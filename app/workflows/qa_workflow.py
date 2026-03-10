"""LangGraph workflow for full LetterGuard QA orchestration."""

from __future__ import annotations

from typing import Any, Literal, cast

from langgraph.graph import END, START, StateGraph

from app.agents.claim_extraction_agent import extract_claims_from_letter
from app.agents.data_validation_agent import validate_generated_letter_against_employee
from app.agents.decision_agent import make_final_decision
from app.agents.logo_agent import validate_logo_for_letter
from app.agents.planner_agent import build_plan
from app.agents.review_router_agent import build_review_summary
from app.agents.template_agent import review_generated_letter_against_prototype
from app.services.llm.azure_openai_service import AzureOpenAIService
from app.workflows.nodes.document_context_node import document_context_node
from app.workflows.nodes.evidence_review_node import evidence_review_node
from app.workflows.nodes.llm_review_node import llm_review_node
from app.workflows.state import QAWorkflowState


def planner_node(state: QAWorkflowState) -> QAWorkflowState:
    plan = build_plan(state.get("file_name", ""), dict(state))
    return cast(
        QAWorkflowState,
        {
            **state,
            "planner_result": plan,
            "generated_extraction_json_path": plan["paths"]["generated_extraction_json_path"],
            "employee_csv_path": plan["paths"]["employee_csv_path"],
            "prototype_extraction_dir": plan["paths"]["prototype_extraction_dir"],
            "logo_dir": plan["paths"]["logo_dir"],
            "errors": state.get("errors", []),
        },
    )


def data_validation_node(state: QAWorkflowState) -> QAWorkflowState:
    planner_status = str(state.get("planner_result", {}).get("status", "needs_review")).lower()
    if planner_status != "pass":
        return cast(
            QAWorkflowState,
            {
                **state,
                "data_validation_result": {
                    "status": "needs_review",
                    "summary": "Planner failed; data validation skipped.",
                },
            },
        )

    result = validate_generated_letter_against_employee(
        file_name=state.get("file_name", ""),
        extraction_json_path=state.get("generated_extraction_json_path", ""),
        employee_csv_path=state.get("employee_csv_path", ""),
    )
    return cast(QAWorkflowState, {**state, "data_validation_result": result})


def claim_extraction_node(state: QAWorkflowState) -> QAWorkflowState:
    planner_status = str(state.get("planner_result", {}).get("status", "needs_review")).lower()
    if planner_status != "pass":
        return cast(
            QAWorkflowState,
            {
                **state,
                "claim_extraction_result": {
                    "status": "skipped",
                    "summary": "Planner did not pass; claim extraction skipped.",
                    "claims": [],
                    "unresolved_questions": [],
                    "confidence": 0.0,
                },
            },
        )

    result = extract_claims_from_letter(
        document_text=str(state.get("document_text", "")),
        metadata=state.get("metadata", {}),
        llm_service=AzureOpenAIService(),
    )
    return cast(QAWorkflowState, {**state, "claim_extraction_result": result})


def template_node(state: QAWorkflowState) -> QAWorkflowState:
    planner_status = str(state.get("planner_result", {}).get("status", "needs_review")).lower()
    if planner_status != "pass":
        return cast(
            QAWorkflowState,
            {
                **state,
                "template_result": {
                    "status": "needs_review",
                    "summary": "Planner did not pass; template comparison skipped.",
                },
            },
        )

    result = review_generated_letter_against_prototype(
        file_name=state.get("file_name", ""),
        generated_extraction_json_path=state.get("generated_extraction_json_path", ""),
        prototype_extraction_dir=state.get("prototype_extraction_dir", ""),
    )
    return cast(QAWorkflowState, {**state, "template_result": result})


def logo_node(state: QAWorkflowState) -> QAWorkflowState:
    planner_status = str(state.get("planner_result", {}).get("status", "needs_review")).lower()
    if planner_status != "pass":
        return cast(
            QAWorkflowState,
            {
                **state,
                "logo_result": {
                    "status": "needs_review",
                    "summary": "Planner did not pass; logo validation skipped.",
                    "issues": [],
                    "expected_logo": "",
                },
            },
        )

    result = validate_logo_for_letter(
        generated_extraction_json_path=state.get("generated_extraction_json_path", ""),
        logo_dir=state.get("logo_dir", "sample_data/logos"),
        data_validation_result=state.get("data_validation_result", {}),
    )
    return cast(QAWorkflowState, {**state, "logo_result": result})


def decision_node(state: QAWorkflowState) -> QAWorkflowState:
    result = make_final_decision(
        file_name=state.get("file_name", ""),
        planner_result=state.get("planner_result", {}),
        claim_extraction_result=state.get("claim_extraction_result", {}),
        data_validation_result=state.get("data_validation_result", {}),
        template_result=state.get("template_result", {}),
        logo_result=state.get("logo_result", {}),
        evidence_review_result=state.get("evidence_review_result", {}),
    )
    return cast(QAWorkflowState, {**state, "decision_result": result})


def review_router_condition(state: QAWorkflowState) -> Literal["review", "end"]:
    final_status = str(state.get("decision_result", {}).get("final_status", "NEEDS_REVIEW")).upper()
    return "review" if final_status == "NEEDS_REVIEW" else "end"


def review_node(state: QAWorkflowState) -> QAWorkflowState:
    review = build_review_summary(state.get("decision_result", {}))
    return cast(QAWorkflowState, {**state, "review_result": review})


def build_qa_graph():
    graph = StateGraph(QAWorkflowState)
    graph.add_node("planner", planner_node)
    graph.add_node("document_context", document_context_node)
    graph.add_node("llm_review", llm_review_node)
    graph.add_node("claim_extraction", claim_extraction_node)
    graph.add_node("data_validation", data_validation_node)
    graph.add_node("template", template_node)
    graph.add_node("logo", logo_node)
    graph.add_node("evidence_review", evidence_review_node)
    graph.add_node("decision", decision_node)
    graph.add_node("review", review_node)

    graph.add_edge(START, "planner")
    graph.add_edge("planner", "document_context")
    graph.add_edge("document_context", "llm_review")
    graph.add_edge("llm_review", "claim_extraction")
    graph.add_edge("claim_extraction", "data_validation")
    graph.add_edge("data_validation", "template")
    graph.add_edge("template", "logo")
    graph.add_edge("logo", "evidence_review")
    graph.add_edge("evidence_review", "decision")
    graph.add_conditional_edges("decision", review_router_condition, {"review": "review", "end": END})
    graph.add_edge("review", END)

    return graph.compile()


qa_compiled_graph = build_qa_graph()


def run_qa_workflow(file_name: str, overrides: dict[str, Any] | None = None) -> QAWorkflowState:
    overrides = overrides or {}
    initial_state: QAWorkflowState = {
        "file_name": file_name,
        "generated_extraction_json_path": overrides.get("generated_extraction_json_path", ""),
        "employee_csv_path": overrides.get("employee_csv_path", ""),
        "prototype_extraction_dir": overrides.get("prototype_extraction_dir", ""),
        "logo_dir": overrides.get("logo_dir", ""),
        "instruction": overrides.get("instruction", ""),
        "document_text": overrides.get("document_text", ""),
        "metadata": overrides.get("metadata", {}),
        "document_context": overrides.get("document_context", {}),
        "errors": [],
    }
    return qa_compiled_graph.invoke(initial_state)
