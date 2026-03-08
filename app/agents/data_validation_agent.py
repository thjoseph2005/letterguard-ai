"""Agent for deterministic generated-letter validation against employee CSV data."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.employee_data_service import (
    REQUIRED_FIELDS,
    find_employee_fields_in_text,
    get_employee_by_id,
    get_employee_by_name,
    load_employee_csv,
    normalize_text,
)


def _extract_full_text(extraction_payload: dict[str, Any]) -> str:
    extraction = extraction_payload.get("extraction", {})
    if isinstance(extraction, dict):
        full_text = extraction.get("full_text")
        if isinstance(full_text, str):
            return full_text
    full_text = extraction_payload.get("full_text")
    return full_text if isinstance(full_text, str) else ""


def _find_employee_id_candidate(file_name: str, text: str) -> str | None:
    id_pattern = re.compile(r"\bE\d{3}\b", flags=re.IGNORECASE)
    file_match = id_pattern.search(file_name)
    if file_match:
        return file_match.group(0).upper()

    text_match = id_pattern.search(text)
    if text_match:
        return text_match.group(0).upper()
    return None


def _find_employee_by_name_from_text(text: str, employees: list[dict[str, str]]) -> dict[str, str] | None:
    normalized_text = normalize_text(text)
    for employee in employees:
        name = employee.get("name", "")
        if name and normalize_text(name) in normalized_text:
            return get_employee_by_name(name, employees)
    return None


def validate_generated_letter_against_employee(
    file_name: str,
    extraction_json_path: str,
    employee_csv_path: str,
) -> dict[str, Any]:
    employees = load_employee_csv(employee_csv_path)

    extraction_path = Path(extraction_json_path)
    extraction_payload = json.loads(extraction_path.read_text(encoding="utf-8"))
    full_text = _extract_full_text(extraction_payload)

    matched_employee: dict[str, str] | None = None
    employee_id_candidate = _find_employee_id_candidate(file_name, full_text)
    if employee_id_candidate:
        matched_employee = get_employee_by_id(employee_id_candidate, employees)

    if not matched_employee:
        matched_employee = _find_employee_by_name_from_text(full_text, employees)

    if not matched_employee:
        return {
            "status": "needs_review",
            "file_name": file_name,
            "employee_id": employee_id_candidate or "",
            "matched_employee_name": "",
            "field_results": {},
            "issues": ["Unable to confidently match employee from file name or text."],
            "summary": "No employee match found. Manual review required.",
        }

    field_results = find_employee_fields_in_text(full_text, matched_employee)
    issues = [f"Field mismatch or missing: {field}" for field in REQUIRED_FIELDS if not field_results.get(field, {}).get("found")]

    if not issues:
        status = "pass"
        summary = "All expected employee fields matched."
    else:
        status = "fail"
        summary = "One or more required employee fields were not matched."

    return {
        "status": status,
        "file_name": file_name,
        "employee_id": matched_employee.get("employee_id", ""),
        "matched_employee_name": matched_employee.get("name", ""),
        "field_results": field_results,
        "issues": issues,
        "summary": summary,
    }
