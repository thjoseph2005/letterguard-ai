"""LangGraph workflow for chat-driven local document QA."""

from __future__ import annotations

from typing import Literal, cast

from langgraph.graph import END, START, StateGraph

from app.services.chat_llm_service import ChatLLMService
from app.services.prototype_reasoning_service import reason_about_prototype_match
from app.services.chat_validation_service import build_listing_result, validate_document_record
from app.services.document_context_service import load_document_context
from app.services.document_resolver_service import load_reference_data, locate_generated_documents
from app.services.mapping_service import get_document_type_label, normalize_document_type
from app.workflows.state import ChatWorkflowState


llm_service = ChatLLMService()


def parse_intent_node(state: ChatWorkflowState) -> ChatWorkflowState:
    try:
        intent = llm_service.parse_intent(str(state.get("user_message", "")))
        return cast(
            ChatWorkflowState,
            {
                **state,
                "intent": intent,
                "status": "in_progress",
                "notes": list(intent.get("notes", [])) if isinstance(intent.get("notes"), list) else [],
            },
        )
    except Exception as exc:
        return cast(
            ChatWorkflowState,
            {
                **state,
                "intent": {},
                "status": "error",
                "error": f"Unable to parse request: {exc}",
                "notes": list(state.get("notes", [])),
            },
        )


def resolve_scope_node(state: ChatWorkflowState) -> ChatWorkflowState:
    intent = state.get("intent", {})
    request_type = str(intent.get("request_type", "list_only"))
    if request_type not in {"list_only", "validate_only", "list_and_validate"}:
        request_type = "list_only"

    document_type = normalize_document_type(str(intent.get("document_type", "all")))

    return cast(
        ChatWorkflowState,
        {
            **state,
            "request_type": request_type,
            "document_type": document_type,
        },
    )


def load_reference_data_node(state: ChatWorkflowState) -> ChatWorkflowState:
    try:
        reference_data = load_reference_data()
        return cast(
            ChatWorkflowState,
            {
                **state,
                "reference_data": reference_data,
                "employees": reference_data.get("employees", []),
                "prototype_mapping": reference_data.get("prototype_mapping", {}),
                "logo_mappings": reference_data.get("logo_mapping", {}),
            },
        )
    except Exception as exc:
        return cast(
            ChatWorkflowState,
            {
                **state,
                "status": "error",
                "error": f"Unable to load local reference data: {exc}",
            },
        )


def locate_generated_documents_node(state: ChatWorkflowState) -> ChatWorkflowState:
    try:
        documents = locate_generated_documents(
            document_type=str(state.get("document_type", "all")),
            employees=state.get("employees", []),
            prototype_mapping=state.get("prototype_mapping", {}),
            logo_mapping=state.get("logo_mappings", {}),
        )
        matched_employees = [
            {"employee_id": doc.get("employee_id", ""), "name": doc.get("employee_name", ""), "department": doc.get("department", "")}
            for doc in documents
            if doc.get("employee_id")
        ]
        return cast(
            ChatWorkflowState,
            {
                **state,
                "documents": documents,
                "matched_employees": matched_employees,
            },
        )
    except Exception as exc:
        return cast(
            ChatWorkflowState,
            {
                **state,
                "status": "error",
                "error": f"Unable to locate generated documents: {exc}",
                "documents": [],
            },
        )


def extract_document_content_node(state: ChatWorkflowState) -> ChatWorkflowState:
    enriched_documents: list[dict] = []
    prototype_extractions = state.get("reference_data", {}).get("prototype_extractions", {})

    for document in state.get("documents", []):
        prototype_pdf = str(document.get("prototype_file", ""))
        prototype_json_path = ""
        prototype_text = ""
        if prototype_pdf:
            prototype_json_path = str(prototype_extractions.get(prototype_pdf, ""))
            if prototype_json_path:
                prototype_text = str(load_document_context(prototype_json_path).get("document_text", ""))

        enriched_documents.append(
            {
                **document,
                "prototype_extraction_json_path": prototype_json_path,
                "prototype_text": prototype_text,
            }
        )

    return cast(ChatWorkflowState, {**state, "documents": enriched_documents})


def validate_documents_node(state: ChatWorkflowState) -> ChatWorkflowState:
    results = [
        validate_document_record(
            record=document,
            prototype_extraction_dir="sample_data/extracted/prototypes",
            llm_service=llm_service,
        )
        for document in state.get("documents", [])
    ]
    return cast(ChatWorkflowState, {**state, "validation_results": results, "results": results})


def prototype_reasoning_node(state: ChatWorkflowState) -> ChatWorkflowState:
    documents = state.get("documents", [])
    validation_results = state.get("validation_results", [])
    document_by_name = {str(item.get("generated_document", "")): item for item in documents}

    enriched_results: list[dict[str, Any]] = []
    prototype_reasoning_results: list[dict[str, Any]] = []

    for result in validation_results:
        document_name = str(result.get("generated_document", ""))
        document_record = document_by_name.get(document_name, {})
        reasoning = reason_about_prototype_match(
            document_record=document_record,
            validation_result=result,
            llm_service=llm_service,
        )
        enriched = {**result, "prototype_reasoning": reasoning}
        if reasoning.get("issues"):
            enriched["issues"] = list(result.get("issues", [])) + [str(item) for item in reasoning.get("issues", []) if item]
            enriched["top_semantic_mismatch"] = str(reasoning.get("issues", [])[0])
        if reasoning.get("summary"):
            enriched["prototype_reasoning_summary"] = str(reasoning.get("summary"))
            enriched["semantic_comparison_summary"] = str(reasoning.get("summary"))
        if reasoning.get("status") == "misaligned" and enriched.get("status") == "passed":
            enriched["status"] = "failed"
        elif reasoning.get("status") == "needs_review" and enriched.get("status") == "passed":
            enriched["status"] = "needs_review"

        enriched_results.append(enriched)
        prototype_reasoning_results.append(
            {
                "generated_document": document_name,
                "employee_name": result.get("employee_name", ""),
                **reasoning,
            }
        )

    return cast(
        ChatWorkflowState,
        {
            **state,
            "validation_results": enriched_results,
            "prototype_reasoning_results": prototype_reasoning_results,
            "results": enriched_results,
        },
    )


def summarize_results_node(state: ChatWorkflowState) -> ChatWorkflowState:
    if state.get("status") == "error":
        answer = state.get("error", "An unknown error occurred while processing the request.")
        return cast(ChatWorkflowState, {**state, "answer": answer, "results": [], "status": "error"})

    documents = state.get("documents", [])
    request_type = str(state.get("request_type", "list_only"))
    if request_type == "list_only":
        results = [build_listing_result(document) for document in documents]
    else:
        results = state.get("validation_results", [])

    passed = sum(1 for item in results if item.get("status") == "passed")
    failed = sum(1 for item in results if item.get("status") == "failed")
    needs_review = sum(1 for item in results if item.get("status") == "needs_review")
    document_type = str(state.get("document_type", "all"))
    summary_input = {
        "request_type": request_type,
        "document_type": document_type,
        "document_type_label": get_document_type_label(document_type),
        "total": len(results) if results else len(documents),
        "passed": passed,
        "failed": failed,
        "needs_review": needs_review,
        "preview_names": [item.get("employee_name", "") for item in results[:5]],
        "status_preview": [
            f"{item.get('employee_name', 'Unknown')} ({item.get('generated_document', 'unknown document')}): {item.get('status', 'unknown')}"
            for item in results[:5]
        ],
        "notes": state.get("notes", []),
        "prototype_reasoning_preview": [
            str(item.get("summary", "")) for item in state.get("prototype_reasoning_results", [])[:3] if item.get("summary")
        ],
        "logo_validation_note": (
            "Logo validation currently resolves the expected department logo file and checks local availability; "
            "it does not perform true visual logo comparison."
        ),
    }
    answer = llm_service.summarize_chat_result(summary_input)
    if not documents:
        results = []

    return cast(ChatWorkflowState, {**state, "answer": answer, "results": results, "status": "completed"})


def route_after_locate(state: ChatWorkflowState) -> Literal["extract_document_content", "summarize_results"]:
    if state.get("status") == "error":
        return "summarize_results"
    if not state.get("documents"):
        return "summarize_results"
    return "extract_document_content"


def route_after_extract(state: ChatWorkflowState) -> Literal["validate_documents", "summarize_results"]:
    if str(state.get("request_type", "list_only")) == "list_only":
        return "summarize_results"
    return "validate_documents"


def route_after_validate(state: ChatWorkflowState) -> Literal["prototype_reasoning", "summarize_results"]:
    if not state.get("validation_results"):
        return "summarize_results"
    return "prototype_reasoning"


def build_chat_graph():
    graph = StateGraph(ChatWorkflowState)
    graph.add_node("parse_intent", parse_intent_node)
    graph.add_node("resolve_scope", resolve_scope_node)
    graph.add_node("load_reference_data", load_reference_data_node)
    graph.add_node("locate_generated_documents", locate_generated_documents_node)
    graph.add_node("extract_document_content", extract_document_content_node)
    graph.add_node("validate_documents", validate_documents_node)
    graph.add_node("prototype_reasoning", prototype_reasoning_node)
    graph.add_node("summarize_results", summarize_results_node)

    graph.add_edge(START, "parse_intent")
    graph.add_edge("parse_intent", "resolve_scope")
    graph.add_edge("resolve_scope", "load_reference_data")
    graph.add_edge("load_reference_data", "locate_generated_documents")
    graph.add_conditional_edges(
        "locate_generated_documents",
        route_after_locate,
        {"extract_document_content": "extract_document_content", "summarize_results": "summarize_results"},
    )
    graph.add_conditional_edges(
        "extract_document_content",
        route_after_extract,
        {"validate_documents": "validate_documents", "summarize_results": "summarize_results"},
    )
    graph.add_conditional_edges(
        "validate_documents",
        route_after_validate,
        {"prototype_reasoning": "prototype_reasoning", "summarize_results": "summarize_results"},
    )
    graph.add_edge("prototype_reasoning", "summarize_results")
    graph.add_edge("summarize_results", END)
    return graph.compile()


compiled_chat_graph = build_chat_graph()


def run_chat_workflow(user_message: str) -> ChatWorkflowState:
    initial_state: ChatWorkflowState = {
        "user_message": user_message,
        "intent": {},
        "request_type": "",
        "document_type": "",
        "reference_data": {},
        "employees": [],
        "documents": [],
        "matched_employees": [],
        "prototype_mapping": {},
        "logo_mappings": {},
        "validation_results": [],
        "prototype_reasoning_results": [],
        "answer": "",
        "results": [],
        "status": "pending",
        "error": "",
        "notes": [],
    }
    return compiled_chat_graph.invoke(initial_state)
