"""Semantic prototype comparison using LLM reasoning with deterministic fallback."""

from __future__ import annotations

from typing import Any

from app.services.chat_llm_service import ChatLLMService


def _fallback_reasoning(
    generated_text: str,
    prototype_text: str,
    validation_result: dict[str, Any],
) -> dict[str, Any]:
    template_result = validation_result.get("template_result", {})
    missing_sections = template_result.get("missing_sections", []) if isinstance(template_result, dict) else []
    unexpected_sections = template_result.get("unexpected_sections", []) if isinstance(template_result, dict) else []
    issues: list[str] = []

    if missing_sections:
        issues.append(f"Prototype-required content appears missing: {', '.join(str(item) for item in missing_sections[:3])}.")
    if unexpected_sections:
        issues.append(f"Generated letter contains content that does not align with the prototype: {', '.join(str(item) for item in unexpected_sections[:3])}.")
    if not prototype_text.strip():
        issues.append("Prototype text was unavailable for semantic comparison.")
    if not generated_text.strip():
        issues.append("Generated document text was unavailable for semantic comparison.")

    severity = "medium" if issues else "low"
    summary = issues[0] if issues else "The generated document is broadly aligned with the prototype based on deterministic checks."
    return {
        "status": "needs_review" if issues else "aligned",
        "summary": summary,
        "issues": issues,
        "severity": severity,
    }


def reason_about_prototype_match(
    *,
    document_record: dict[str, Any],
    validation_result: dict[str, Any],
    llm_service: ChatLLMService,
) -> dict[str, Any]:
    generated_text = str(document_record.get("document_text", ""))
    prototype_text = str(document_record.get("prototype_text", ""))
    result = _fallback_reasoning(generated_text, prototype_text, validation_result)
    return llm_service.compare_prototype_documents(
        generated_text=generated_text,
        prototype_text=prototype_text,
        validation_context=validation_result,
        fallback_result=result,
    )
