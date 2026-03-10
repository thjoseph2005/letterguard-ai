"""Workflow node for evidence-based QA review using optional LLM support."""

from __future__ import annotations

import asyncio
from typing import Any

from app.services.llm.azure_openai_service import AzureOpenAIService
from app.workflows.state import QAWorkflowState


DEFAULT_QA_INSTRUCTION = (
    "Review this compensation letter for employee data accuracy, template adherence, "
    "branding risks, contradictions, and any missing evidence that requires manual review."
)


def _build_review_context(state: QAWorkflowState) -> dict[str, Any]:
    return {
        "document_context": state.get("document_context", {}),
        "claim_extraction_result": state.get("claim_extraction_result", {}),
        "data_validation_result": state.get("data_validation_result", {}),
        "template_result": state.get("template_result", {}),
        "logo_result": state.get("logo_result", {}),
    }


def evidence_review_node(state: QAWorkflowState) -> QAWorkflowState:
    document_text = str(state.get("document_text", "")).strip()
    if not document_text:
        return {
            **state,
            "evidence_review_result": {
                "status": "skipped",
                "summary": "Evidence review skipped because no document text was available.",
                "issues": [],
                "recommendations": [],
                "confidence": 0.0,
            },
        }

    instruction = str(state.get("instruction", "")).strip() or DEFAULT_QA_INSTRUCTION
    context = _build_review_context(state)

    try:
        service = AzureOpenAIService()
        result = asyncio.run(
            service.review_letter_package(
                instruction=instruction,
                document_text=document_text,
                context=context,
            )
        )
        return {
            **state,
            "evidence_review_result": {
                "status": result.get("overall_status", "needs_review"),
                **result,
            },
        }
    except Exception as exc:
        return {
            **state,
            "evidence_review_result": {
                "status": "skipped",
                "summary": f"Evidence review skipped because Azure OpenAI was unavailable: {exc}",
                "issues": [],
                "recommendations": [],
                "confidence": 0.0,
            },
        }
