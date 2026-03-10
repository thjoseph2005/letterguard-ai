"""Deterministic mappings for local document QA workflow."""

from __future__ import annotations

from typing import Any

from app.agents.logo_agent import DEPARTMENT_LOGO_MAP
from app.services.prototype_comparison_service import PROTOTYPE_MAP


DOCUMENT_TYPE_ALIASES = {
    "promotion": "promotion",
    "promotion_letter": "promotion",
    "promoted": "promotion",
    "base_pay_increase": "base_pay_increase",
    "salary_increase": "base_pay_increase",
    "salary": "base_pay_increase",
    "base pay": "base_pay_increase",
    "annual_incentive_award": "annual_incentive_award",
    "bonus": "annual_incentive_award",
    "annual incentive": "annual_incentive_award",
    "all": "all",
}


def normalize_document_type(document_type: str) -> str:
    normalized = (document_type or "").strip().lower().replace("-", "_")
    return DOCUMENT_TYPE_ALIASES.get(normalized, normalized or "all")


def get_prototype_mapping() -> dict[str, str]:
    return dict(PROTOTYPE_MAP)


def get_logo_mapping() -> dict[str, str]:
    return dict(DEPARTMENT_LOGO_MAP)


def get_document_type_label(document_type: str) -> str:
    normalized = normalize_document_type(document_type)
    labels = {
        "promotion": "promotion letters",
        "base_pay_increase": "base pay increase letters",
        "annual_incentive_award": "annual incentive award letters",
        "all": "generated letters",
    }
    return labels.get(normalized, f"{normalized} letters")


def build_reference_snapshot() -> dict[str, Any]:
    return {
        "prototype_mapping": get_prototype_mapping(),
        "logo_mapping": get_logo_mapping(),
    }
