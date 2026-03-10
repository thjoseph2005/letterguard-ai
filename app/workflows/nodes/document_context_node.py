"""Workflow node for loading document context from extraction JSON."""

from __future__ import annotations

from pathlib import Path

from app.services.document_context_service import load_document_context
from app.workflows.state import QAWorkflowState


def document_context_node(state: QAWorkflowState) -> QAWorkflowState:
    extraction_path = str(state.get("generated_extraction_json_path", "")).strip()
    if not extraction_path or not Path(extraction_path).exists():
        errors = list(state.get("errors", []))
        errors.append(f"Document context could not be loaded: missing extraction path {extraction_path!r}")
        return {
            **state,
            "document_context": {},
            "document_text": "",
            "metadata": state.get("metadata", {}),
            "errors": errors,
        }

    context = load_document_context(extraction_path)
    return {
        **state,
        "document_context": context,
        "document_text": str(context.get("document_text", "")),
        "metadata": context.get("metadata", {}) if isinstance(context.get("metadata"), dict) else {},
    }
