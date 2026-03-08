"""Decision agent for final QA status aggregation."""

from __future__ import annotations

from typing import Any


MAJOR_COMPONENTS = ["planner", "data_validation", "template_comparison", "logo_validation"]


def make_final_decision(
    file_name: str,
    planner_result: dict[str, Any] | None,
    data_validation_result: dict[str, Any] | None,
    template_result: dict[str, Any] | None,
    logo_result: dict[str, Any] | None,
) -> dict[str, Any]:
    planner_result = planner_result or {}
    data_validation_result = data_validation_result or {}
    template_result = template_result or {}
    logo_result = logo_result or {}

    component_status = {
        "planner": str(planner_result.get("status", "needs_review")),
        "data_validation": str(data_validation_result.get("status", "needs_review")),
        "template_comparison": str(template_result.get("status", "needs_review")),
        "logo_validation": str(logo_result.get("status", "needs_review")),
    }

    normalized_statuses = {key: value.lower() for key, value in component_status.items()}
    reasons: list[str] = []

    if "fail" in normalized_statuses.values():
        final_status = "FAIL"
    elif "needs_review" in normalized_statuses.values():
        final_status = "NEEDS_REVIEW"
    elif all(normalized_statuses.get(component) == "pass" for component in MAJOR_COMPONENTS):
        final_status = "PASS"
    else:
        final_status = "NEEDS_REVIEW"

    if planner_result.get("summary"):
        reasons.append(str(planner_result["summary"]))
    if data_validation_result.get("summary"):
        reasons.append(str(data_validation_result["summary"]))
    if template_result.get("summary"):
        reasons.append(str(template_result["summary"]))
    if logo_result.get("summary"):
        reasons.append(str(logo_result["summary"]))

    if final_status == "PASS":
        summary = "Letter passed all current QA checks."
    elif final_status == "FAIL":
        summary = "Letter failed one or more deterministic QA checks."
    else:
        summary = "Letter needs manual review due to missing inputs or ambiguous checks."

    return {
        "final_status": final_status,
        "file_name": file_name,
        "reasons": reasons,
        "component_status": component_status,
        "summary": summary,
    }
