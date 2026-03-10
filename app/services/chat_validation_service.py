"""Deterministic validation assembly for chat-oriented document QA results."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from app.agents.data_validation_agent import validate_generated_letter_against_employee
from app.agents.logo_agent import validate_logo_for_letter
from app.agents.template_agent import review_generated_letter_against_prototype
from app.services.chat_llm_service import ChatLLMService
from app.services.mapping_service import get_document_type_label


def _collect_issues(
    data_validation_result: dict[str, Any],
    template_result: dict[str, Any],
    logo_result: dict[str, Any],
) -> list[str]:
    issues: list[str] = []
    for result in [data_validation_result, template_result, logo_result]:
        result_issues = result.get("issues", [])
        if isinstance(result_issues, list):
            issues.extend(str(item) for item in result_issues if item)
    missing_sections = template_result.get("missing_sections", [])
    if isinstance(missing_sections, list):
        issues.extend(f"Missing prototype section: {section}" for section in missing_sections[:5])
    unexpected_sections = template_result.get("unexpected_sections", [])
    if isinstance(unexpected_sections, list):
        issues.extend(f"Unexpected section detected: {section}" for section in unexpected_sections[:5])
    return issues


def _resolve_status(*statuses: str) -> str:
    lowered = [status.lower() for status in statuses]
    if "fail" in lowered:
        return "failed"
    if "needs_review" in lowered:
        return "needs_review"
    return "passed"


def validate_document_record(
    record: dict[str, Any],
    prototype_extraction_dir: str,
    llm_service: ChatLLMService,
) -> dict[str, Any]:
    data_validation_result = validate_generated_letter_against_employee(
        file_name=str(record.get("file_name", "")),
        extraction_json_path=str(record.get("generated_extraction_json_path", "")),
        employee_csv_path="sample_data/employees/employees.csv",
    )
    template_result = review_generated_letter_against_prototype(
        file_name=str(record.get("file_name", "")),
        generated_extraction_json_path=str(record.get("generated_extraction_json_path", "")),
        prototype_extraction_dir=prototype_extraction_dir,
    )
    logo_result = validate_logo_for_letter(
        generated_extraction_json_path=str(record.get("generated_extraction_json_path", "")),
        logo_dir="sample_data/logos",
        data_validation_result=data_validation_result,
    )
    issues = _collect_issues(data_validation_result, template_result, logo_result)
    status = _resolve_status(
        str(data_validation_result.get("status", "needs_review")),
        str(template_result.get("status", "needs_review")),
        str(logo_result.get("status", "needs_review")),
    )

    result = {
        "employee_name": record.get("employee_name", ""),
        "employee_id": record.get("employee_id", ""),
        "department": record.get("department", ""),
        "document_type": record.get("document_type", ""),
        "document_type_label": get_document_type_label(str(record.get("document_type", ""))),
        "generated_document": record.get("generated_document", ""),
        "prototype_used": record.get("prototype_file", ""),
        "logo_used": record.get("expected_logo", ""),
        "status": status,
        "issues": issues,
        "data_validation_result": data_validation_result,
        "template_result": template_result,
        "logo_result": logo_result,
    }

    explanation = llm_service.explain_validation_result(result)
    if explanation:
        result["explanation"] = explanation

    return result


def build_listing_result(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "employee_name": record.get("employee_name", ""),
        "employee_id": record.get("employee_id", ""),
        "department": record.get("department", ""),
        "document_type": record.get("document_type", ""),
        "generated_document": record.get("generated_document", ""),
        "prototype_used": record.get("prototype_file", ""),
        "logo_used": record.get("expected_logo", ""),
        "status": "listed",
        "issues": [],
    }
