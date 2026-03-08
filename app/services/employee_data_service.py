"""Deterministic helpers for employee CSV lookups and text matching."""

from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Any


REQUIRED_FIELDS = [
    "employee_id",
    "name",
    "department",
    "title",
    "base_pay",
    "annual_incentive",
]


def load_employee_csv(csv_path: str) -> list[dict[str, str]]:
    path = Path(csv_path)
    with path.open("r", newline="", encoding="utf-8") as csv_file:
        return [dict(row) for row in csv.DictReader(csv_file)]


def get_employee_by_id(employee_id: str, employees: list[dict[str, str]]) -> dict[str, str] | None:
    target = normalize_text(employee_id)
    for employee in employees:
        if normalize_text(employee.get("employee_id", "")) == target:
            return employee
    return None


def get_employee_by_name(name: str, employees: list[dict[str, str]]) -> dict[str, str] | None:
    target = normalize_text(name)
    for employee in employees:
        if normalize_text(employee.get("name", "")) == target:
            return employee
    return None


def normalize_text(value: str) -> str:
    normalized = re.sub(r"\s+", " ", value or "").strip().lower()
    return normalized


def parse_currency_from_text(text: str) -> list[str | float]:
    matches = re.findall(r"\$?\s*\d[\d,]*(?:\.\d+)?", text)
    parsed_values: list[str | float] = []
    for match in matches:
        cleaned = match.replace("$", "").replace(",", "").strip()
        try:
            parsed_values.append(float(cleaned))
        except ValueError:
            continue
    return parsed_values


def _parse_expected_number(value: Any) -> float | None:
    if value is None:
        return None
    cleaned = str(value).replace("$", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def find_employee_fields_in_text(text: str, employee: dict[str, str]) -> dict[str, dict[str, Any]]:
    normalized_text = normalize_text(text)
    parsed_currencies = parse_currency_from_text(text)

    field_results: dict[str, dict[str, Any]] = {}

    for field in ["employee_id", "name", "department", "title"]:
        expected = employee.get(field, "")
        field_results[field] = {
            "expected": expected,
            "found": normalize_text(expected) in normalized_text if expected else False,
        }

    for field in ["base_pay", "annual_incentive"]:
        expected_number = _parse_expected_number(employee.get(field))
        found = expected_number in parsed_currencies if expected_number is not None else False
        field_results[field] = {
            "expected": int(expected_number) if expected_number is not None and expected_number.is_integer() else expected_number,
            "found": found,
        }

    return field_results
