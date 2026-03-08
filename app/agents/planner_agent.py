"""Planner agent for building deterministic QA execution plans."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def _pick_path(state: dict[str, Any], key: str, default: str) -> str:
    value = state.get(key)
    if isinstance(value, str) and value.strip():
        return value
    return default


def build_plan(file_name: str, state: dict[str, Any] | None = None) -> dict[str, Any]:
    state = state or {}
    safe_file_name = Path(file_name).name

    generated_extraction_json_path = _pick_path(
        state,
        "generated_extraction_json_path",
        str(Path("sample_data/extracted/generated_letters") / f"{safe_file_name}.json"),
    )
    employee_csv_path = _pick_path(state, "employee_csv_path", "sample_data/employees/employees.csv")
    prototype_extraction_dir = _pick_path(state, "prototype_extraction_dir", "sample_data/extracted/prototypes")
    logo_dir = _pick_path(state, "logo_dir", "sample_data/logos")

    required_paths = {
        "generated_extraction_json_path": generated_extraction_json_path,
        "employee_csv_path": employee_csv_path,
        "prototype_extraction_dir": prototype_extraction_dir,
        "logo_dir": logo_dir,
    }

    missing_inputs = [name for name, path in required_paths.items() if not Path(path).exists()]
    status = "pass" if not missing_inputs else "needs_review"
    summary = "All required inputs found." if not missing_inputs else f"Missing required inputs: {', '.join(missing_inputs)}"

    return {
        "status": status,
        "file_name": safe_file_name,
        "paths": required_paths,
        "missing_inputs": missing_inputs,
        "summary": summary,
    }
