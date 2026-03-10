"""Local document discovery and extraction helpers for chat orchestration."""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from app.services.document_context_service import load_document_context
from app.services.employee_data_service import get_employee_by_id, load_employee_csv, normalize_text
from app.services.file_service import create_directory_if_not_exists
from app.services.mapping_service import get_logo_mapping, get_prototype_mapping, normalize_document_type
from app.services.pdf_extraction_service import extract_pdf_metadata, extract_pdf_text, save_extraction_result
from app.services.prototype_comparison_service import classify_letter_type_from_text


SAMPLE_DATA_DIR = Path("sample_data")
EMPLOYEE_CSV_PATH = SAMPLE_DATA_DIR / "employees" / "employees.csv"
PROTOTYPE_DIR = SAMPLE_DATA_DIR / "prototypes"
GENERATED_DIR = SAMPLE_DATA_DIR / "generated_letters"
PROTOTYPE_EXTRACTION_DIR = SAMPLE_DATA_DIR / "extracted" / "prototypes"
GENERATED_EXTRACTION_DIR = SAMPLE_DATA_DIR / "extracted" / "generated_letters"


def _safe_json_path(pdf_path: Path, extraction_dir: Path) -> Path:
    return extraction_dir / f"{pdf_path.name}.json"


def ensure_extraction_json(pdf_path: Path, extraction_dir: Path) -> Path:
    create_directory_if_not_exists(str(extraction_dir))
    output_path = _safe_json_path(pdf_path, extraction_dir)
    if output_path.exists():
        return output_path

    extracted = extract_pdf_text(str(pdf_path))
    metadata = extract_pdf_metadata(str(pdf_path))
    save_extraction_result({"metadata": metadata, "extraction": extracted}, str(output_path))
    return output_path


def ensure_all_reference_extractions() -> dict[str, str]:
    prototype_map: dict[str, str] = {}
    for pdf_path in sorted(PROTOTYPE_DIR.glob("*.pdf")):
        json_path = ensure_extraction_json(pdf_path, PROTOTYPE_EXTRACTION_DIR)
        prototype_map[pdf_path.name] = str(json_path)
    return prototype_map


def _employee_match_from_text(document_text: str, employees: list[dict[str, str]]) -> dict[str, str] | None:
    normalized_document = normalize_text(document_text)
    for employee in employees:
        name = employee.get("name", "")
        if name and normalize_text(name) in normalized_document:
            return employee
    return None


def _match_employee(file_name: str, document_text: str, employees: list[dict[str, str]]) -> dict[str, str] | None:
    file_match = re.search(r"\b(E\d{3})\b", file_name, flags=re.IGNORECASE)
    if file_match:
        employee = get_employee_by_id(file_match.group(1), employees)
        if employee:
            return employee
    text_match = re.search(r"\b(E\d{3})\b", document_text, flags=re.IGNORECASE)
    if text_match:
        employee = get_employee_by_id(text_match.group(1), employees)
        if employee:
            return employee
    return _employee_match_from_text(document_text, employees)


def load_reference_data() -> dict[str, Any]:
    employees = load_employee_csv(str(EMPLOYEE_CSV_PATH)) if EMPLOYEE_CSV_PATH.exists() else []
    prototype_mapping = get_prototype_mapping()
    logo_mapping = get_logo_mapping()
    prototype_extractions = ensure_all_reference_extractions()
    return {
        "employees": employees,
        "prototype_mapping": prototype_mapping,
        "logo_mapping": logo_mapping,
        "prototype_extractions": prototype_extractions,
    }


def locate_generated_documents(
    document_type: str,
    employees: list[dict[str, str]],
    prototype_mapping: dict[str, str],
    logo_mapping: dict[str, str],
) -> list[dict[str, Any]]:
    normalized_document_type = normalize_document_type(document_type)
    records: list[dict[str, Any]] = []

    for pdf_path in sorted(GENERATED_DIR.glob("*.pdf")):
        extraction_json_path = ensure_extraction_json(pdf_path, GENERATED_EXTRACTION_DIR)
        context = load_document_context(str(extraction_json_path))
        document_text = str(context.get("document_text", ""))
        classification = classify_letter_type_from_text(document_text)
        detected_type = normalize_document_type(str(classification.get("letter_type", "unknown")))
        if normalized_document_type != "all" and detected_type != normalized_document_type:
            continue

        employee = _match_employee(pdf_path.name, document_text, employees) or {}
        department = str(employee.get("department", "")).strip()
        expected_logo = logo_mapping.get(department.lower(), "") if department else ""
        prototype_json = prototype_mapping.get(detected_type, "")
        prototype_pdf = prototype_json.removesuffix(".json") if prototype_json else ""

        records.append(
            {
                "file_name": pdf_path.name,
                "generated_document": pdf_path.name,
                "generated_pdf_path": str(pdf_path),
                "generated_extraction_json_path": str(extraction_json_path),
                "document_text": document_text,
                "document_type": detected_type,
                "classification_confidence": classification.get("confidence", 0.0),
                "matched_keywords": classification.get("matched_keywords", []),
                "employee_id": str(employee.get("employee_id", "")),
                "employee_name": str(employee.get("name", "")),
                "department": department,
                "title": str(employee.get("title", "")),
                "prototype_file": prototype_pdf,
                "prototype_json_file": prototype_json,
                "expected_logo": expected_logo,
            }
        )

    return records
