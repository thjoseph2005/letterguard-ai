"""Local deterministic logo validation placeholder agent."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

DEPARTMENT_LOGO_MAP = {
    "wealth management": "wealth.png",
    "investment banking": "investment.png",
    "asset management": "asset.png",
}


def _extract_full_text(json_path: Path) -> str:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    extraction = payload.get("extraction", {})
    if isinstance(extraction, dict) and isinstance(extraction.get("full_text"), str):
        return extraction["full_text"]
    if isinstance(payload.get("full_text"), str):
        return payload["full_text"]
    return ""


def validate_logo_for_letter(
    generated_extraction_json_path: str,
    logo_dir: str,
    data_validation_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    data_validation_result = data_validation_result or {}
    department = ""

    field_results = data_validation_result.get("field_results", {})
    if isinstance(field_results, dict):
        department = str(field_results.get("department", {}).get("expected", "")).strip().lower()

    if not department:
        return {
            "status": "needs_review",
            "expected_logo": "",
            "issues": ["Unable to infer department for logo validation."],
            "summary": "Department not available from data validation result.",
        }

    expected_logo = DEPARTMENT_LOGO_MAP.get(department, "")
    if not expected_logo:
        return {
            "status": "needs_review",
            "expected_logo": "",
            "issues": [f"No logo mapping found for department: {department}"],
            "summary": "Department-to-logo mapping is missing.",
        }

    logo_path = Path(logo_dir) / expected_logo
    issues: list[str] = []
    status = "pass"

    if not logo_path.exists():
        status = "fail"
        issues.append(f"Expected logo file not found: {logo_path}")

    extraction_path = Path(generated_extraction_json_path)
    if extraction_path.exists():
        full_text = _extract_full_text(extraction_path).lower()
        department_signal = department in full_text
        if not department_signal:
            issues.append("Department name not found in generated letter text (weak signal).")
            if status == "pass":
                status = "needs_review"

    summary = "Logo validation passed." if status == "pass" else "Logo validation found issues."
    return {
        "status": status,
        "expected_logo": expected_logo,
        "issues": issues,
        "summary": summary,
    }
