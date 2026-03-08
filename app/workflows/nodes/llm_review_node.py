"""LangGraph node for Azure OpenAI QA review."""

from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Any

from app.services.llm.azure_openai_service import AzureOpenAIService
from app.workflows.state import QAWorkflowState


def _load_full_text_from_extraction(path: str) -> str:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    extraction = payload.get("extraction", {})
    if isinstance(extraction, dict) and isinstance(extraction.get("full_text"), str):
        return extraction["full_text"]
    if isinstance(payload.get("full_text"), str):
        return payload["full_text"]
    return ""


def llm_review_node(state: QAWorkflowState) -> QAWorkflowState:
    instruction = str(state.get("instruction", "")).strip()
    if not instruction:
        return {
            **state,
            "qa_result": {
                "overall_status": "needs_review",
                "summary": "LLM review skipped because no instruction was provided.",
                "issues": [],
                "recommendations": [],
                "confidence": 0.0,
            },
        }

    document_text = str(state.get("document_text", "")).strip()
    if not document_text:
        extraction_path = str(state.get("generated_extraction_json_path", "")).strip()
        if extraction_path and Path(extraction_path).exists():
            document_text = _load_full_text_from_extraction(extraction_path)

    if not document_text:
        return {
            **state,
            "qa_result": {
                "overall_status": "needs_review",
                "summary": "LLM review skipped because no document text was available.",
                "issues": [],
                "recommendations": [],
                "confidence": 0.0,
            },
        }

    service = AzureOpenAIService()
    try:
        qa_result = asyncio.run(
            service.analyze_document(
                instruction=instruction,
                document_text=document_text,
                metadata=state.get("metadata", {}),
            )
        )
        return {**state, "qa_result": qa_result}
    except Exception as exc:
        errors = list(state.get("errors", []))
        errors.append(str(exc))
        return {
            **state,
            "errors": errors,
            "qa_result": {
                "overall_status": "needs_review",
                "summary": f"LLM review failed: {exc}",
                "issues": [],
                "recommendations": [],
                "confidence": 0.0,
            },
        }
