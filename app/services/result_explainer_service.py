"""Helpers to convert deterministic QA results into user-friendly explanations."""

from __future__ import annotations

from typing import Any


def explain_qa_result(result: dict[str, Any]) -> str:
    final_status = str(result.get("final_status", "NEEDS_REVIEW")).upper()
    reasons = [str(item) for item in result.get("reasons", []) if item]
    issues: list[str] = []

    data_validation = result.get("data_validation_result", {})
    if isinstance(data_validation, dict):
        for issue in data_validation.get("issues", []):
            issues.append(str(issue))

    template = result.get("template_result", {})
    if isinstance(template, dict):
        missing_sections = template.get("missing_sections", [])
        if missing_sections:
            issues.append("template comparison detected missing required sections")

    if final_status == "PASS":
        return "The letter passed all current QA checks."
    if final_status == "FAIL":
        details = issues or reasons
        if details:
            return f"The letter failed because {details[0]}."
        return "The letter failed one or more deterministic QA checks."

    details = reasons or ["the checks were ambiguous or required inputs were missing"]
    return f"The letter needs review because {details[0]}."
