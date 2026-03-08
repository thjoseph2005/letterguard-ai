"""Review router agent for NEEDS_REVIEW cases."""

from __future__ import annotations

from typing import Any


def build_review_summary(decision_result: dict[str, Any] | None) -> dict[str, Any] | None:
    decision_result = decision_result or {}
    if decision_result.get("final_status") != "NEEDS_REVIEW":
        return None

    reasons = decision_result.get("reasons", [])
    reason_text = "; ".join(str(item) for item in reasons[:3]) if reasons else "No reasons provided."
    return {
        "status": "needs_review",
        "summary": f"Manual review requested: {reason_text}",
    }
