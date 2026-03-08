"""Deterministic chat command parsing and execution for LetterGuard AI."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from app.services.employee_data_service import load_employee_csv
from app.services.qa_orchestration_service import (
    run_letterguard_workflow_for_all_generated_letters,
    run_letterguard_workflow_for_file,
)
from app.services.result_explainer_service import explain_qa_result


EMPLOYEE_CSV_PATH = Path("sample_data/employees/employees.csv")
QA_RESULTS_DIR = Path("sample_data/qa_results")


def _extract_file_name(message: str) -> str:
    match = re.search(r"\b([A-Za-z0-9_-]+\.pdf)\b", message, flags=re.IGNORECASE)
    if not match:
        return ""
    return Path(match.group(1)).name


def _extract_employee_name_candidate(message: str) -> str:
    patterns = [
        r"check\s+(.+?)'?s\s+letter",
        r"run qa for\s+(.+?)'?s\s+letter",
        r"run quality check for\s+(.+?)'?s\s+letter",
        r"check\s+(.+?)\s+letter",
        r"run qa for\s+(.+?)\s+letter",
    ]
    lowered = message.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            return " ".join(part.capitalize() for part in match.group(1).strip().split())
    return ""


def parse_chat_instruction(message: str) -> dict[str, str]:
    lowered = message.strip().lower()
    file_name = _extract_file_name(message)
    employee_name = ""

    explain_markers = ["why did", "explain", "explain result"]
    if any(marker in lowered for marker in explain_markers):
        intent = "explain_result"
        if not file_name:
            employee_name = _extract_employee_name_candidate(message)
            if employee_name:
                file_name = resolve_employee_name_to_file(employee_name) or ""
        return {
            "intent": intent,
            "file_name": file_name,
            "employee_name": employee_name,
            "raw_message": message,
        }

    run_all_markers = ["all generated letters", "all letters", "run qa for all", "check all letters", "validate all"]
    if any(marker in lowered for marker in run_all_markers):
        return {"intent": "run_all", "file_name": "", "employee_name": "", "raw_message": message}

    single_markers = ["run quality check", "run qa", "check "]
    if any(marker in lowered for marker in single_markers):
        if not file_name:
            employee_name = _extract_employee_name_candidate(message)
            if employee_name:
                file_name = resolve_employee_name_to_file(employee_name) or ""
        return {
            "intent": "run_single",
            "file_name": file_name,
            "employee_name": employee_name,
            "raw_message": message,
        }

    return {"intent": "unknown", "file_name": "", "employee_name": "", "raw_message": message}


def resolve_employee_name_to_file(employee_name: str) -> str | None:
    if not EMPLOYEE_CSV_PATH.exists():
        return None

    employees = load_employee_csv(str(EMPLOYEE_CSV_PATH))
    target = employee_name.strip().lower()
    for employee in employees:
        name = str(employee.get("name", "")).strip().lower()
        if name == target:
            employee_id = str(employee.get("employee_id", "")).strip()
            if employee_id:
                return f"{employee_id}_letter.pdf"
    return None


def _load_saved_result(file_name: str) -> dict[str, Any] | None:
    result_path = QA_RESULTS_DIR / f"{Path(file_name).name}.result.json"
    if not result_path.exists():
        return None
    return json.loads(result_path.read_text(encoding="utf-8"))


def execute_chat_command(command: dict[str, str]) -> dict[str, Any]:
    intent = command.get("intent", "unknown")
    file_name = command.get("file_name", "")

    if intent == "run_single":
        if not file_name:
            return {
                "status": "error",
                "message": "I could not determine which file to check. Try: Run quality check for E001_letter.pdf",
                "intent": intent,
                "data": {},
            }
        result = run_letterguard_workflow_for_file(file_name)
        return {
            "status": "success",
            "message": f"QA completed for {file_name}: {result.get('final_status', 'NEEDS_REVIEW')}.",
            "intent": intent,
            "data": result,
        }

    if intent == "run_all":
        result = run_letterguard_workflow_for_all_generated_letters()
        return {
            "status": "success",
            "message": (
                f"QA run complete for {result.get('total', 0)} letters "
                f"(PASS={result.get('PASS', 0)}, FAIL={result.get('FAIL', 0)}, "
                f"NEEDS_REVIEW={result.get('NEEDS_REVIEW', 0)})."
            ),
            "intent": intent,
            "data": result,
        }

    if intent == "explain_result":
        if not file_name:
            return {
                "status": "error",
                "message": "Please provide a file name to explain, for example: Explain result for E001_letter.pdf",
                "intent": intent,
                "data": {},
            }
        result = _load_saved_result(file_name)
        if not result:
            return {
                "status": "error",
                "message": (
                    f"No saved QA result found for {file_name}. "
                    "Run a quality check first using: Run quality check for <file_name>."
                ),
                "intent": intent,
                "data": {},
            }
        return {
            "status": "success",
            "message": explain_qa_result(result),
            "intent": intent,
            "data": result,
        }

    return {
        "status": "error",
        "message": (
            "I can help with: 'Run quality check for E001_letter.pdf', "
            "'Run QA for all generated letters', "
            "'Check John Smith\\'s letter', "
            "'Explain result for E001_letter.pdf'."
        ),
        "intent": "unknown",
        "data": {},
    }
