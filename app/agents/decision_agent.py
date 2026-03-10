"""Decision agent for final QA status aggregation."""

from __future__ import annotations

from typing import Any


MAJOR_COMPONENTS = ["planner", "data_validation", "template_comparison", "logo_validation"]
NEUTRAL_STATUSES = {"skipped", "not_run", "n/a"}


def make_final_decision(
    file_name: str,
    planner_result: dict[str, Any] | None,
    claim_extraction_result: dict[str, Any] | None,
    data_validation_result: dict[str, Any] | None,
    template_result: dict[str, Any] | None,
    logo_result: dict[str, Any] | None,
    evidence_review_result: dict[str, Any] | None,
) -> dict[str, Any]:
    planner_result = planner_result or {}
    claim_extraction_result = claim_extraction_result or {}
    data_validation_result = data_validation_result or {}
    template_result = template_result or {}
    logo_result = logo_result or {}
    evidence_review_result = evidence_review_result or {}

    component_status = {
        "planner": str(planner_result.get("status", "needs_review")),
        "claim_extraction": str(claim_extraction_result.get("status", "needs_review")),
        "data_validation": str(data_validation_result.get("status", "needs_review")),
        "template_comparison": str(template_result.get("status", "needs_review")),
        "logo_validation": str(logo_result.get("status", "needs_review")),
        "evidence_review": str(
            evidence_review_result.get("status", evidence_review_result.get("overall_status", "skipped"))
        ),
    }

    normalized_statuses = {key: value.lower() for key, value in component_status.items()}
    blocking_statuses = {
        key: value for key, value in normalized_statuses.items() if key in MAJOR_COMPONENTS or key == "evidence_review"
    }
    reasons: list[str] = []

    if "fail" in blocking_statuses.values():
        final_status = "FAIL"
    elif "needs_review" in blocking_statuses.values():
        final_status = "NEEDS_REVIEW"
    elif all(normalized_statuses.get(component) == "pass" for component in MAJOR_COMPONENTS):
        final_status = "PASS"
    else:
        final_status = "NEEDS_REVIEW"

    if planner_result.get("summary"):
        reasons.append(str(planner_result["summary"]))
    if claim_extraction_result.get("summary"):
        reasons.append(str(claim_extraction_result["summary"]))
    if data_validation_result.get("summary"):
        reasons.append(str(data_validation_result["summary"]))
    if template_result.get("summary"):
        reasons.append(str(template_result["summary"]))
    if logo_result.get("summary"):
        reasons.append(str(logo_result["summary"]))
    if evidence_review_result.get("summary"):
        reasons.append(str(evidence_review_result["summary"]))

    if normalized_statuses.get("evidence_review") in NEUTRAL_STATUSES and final_status == "PASS":
        summary = "Letter passed deterministic QA checks; LLM evidence review was not run."
    elif final_status == "PASS":
        summary = "Letter passed all current QA checks."
    elif final_status == "FAIL":
        summary = "Letter failed one or more deterministic or evidence-based QA checks."
    else:
        summary = "Letter needs manual review due to missing inputs, ambiguous checks, or unresolved evidence."

    return {
        "final_status": final_status,
        "file_name": file_name,
        "reasons": reasons,
        "component_status": component_status,
        "summary": summary,
    }
