"""Agent for deterministic generated-letter vs prototype review."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.prototype_comparison_service import (
    classify_letter_type_from_text,
    compare_generated_text_to_prototype,
    get_prototype_file_for_letter_type,
)


def _load_full_text_from_extraction_json(json_path: Path) -> str:
    payload = json.loads(json_path.read_text(encoding="utf-8"))
    extraction = payload.get("extraction", {})
    if isinstance(extraction, dict) and isinstance(extraction.get("full_text"), str):
        return extraction["full_text"]
    if isinstance(payload.get("full_text"), str):
        return payload["full_text"]
    return ""


def review_generated_letter_against_prototype(
    file_name: str,
    generated_extraction_json_path: str,
    prototype_extraction_dir: str,
) -> dict[str, Any]:
    generated_path = Path(generated_extraction_json_path)
    if not generated_path.exists():
        return {
            "status": "needs_review",
            "file_name": file_name,
            "detected_letter_type": "unknown",
            "prototype_file": "",
            "missing_sections": [],
            "unexpected_sections": [],
            "summary": f"Generated extraction file not found: {generated_path}",
        }

    generated_text = _load_full_text_from_extraction_json(generated_path)
    classification = classify_letter_type_from_text(generated_text)
    letter_type = str(classification.get("letter_type", "unknown"))

    prototype_file = get_prototype_file_for_letter_type(letter_type)
    if not prototype_file:
        return {
            "status": "needs_review",
            "file_name": file_name,
            "detected_letter_type": letter_type,
            "prototype_file": "",
            "missing_sections": [],
            "unexpected_sections": [],
            "summary": "Could not map detected letter type to a prototype.",
        }

    prototype_json_path = Path(prototype_extraction_dir) / prototype_file
    if not prototype_json_path.exists():
        return {
            "status": "needs_review",
            "file_name": file_name,
            "detected_letter_type": letter_type,
            "prototype_file": prototype_file,
            "missing_sections": [],
            "unexpected_sections": [],
            "summary": f"Prototype extraction JSON not found: {prototype_json_path}",
        }

    prototype_text = _load_full_text_from_extraction_json(prototype_json_path)
    comparison = compare_generated_text_to_prototype(generated_text, prototype_text, letter_type)

    return {
        "status": comparison.get("status", "needs_review"),
        "file_name": file_name,
        "detected_letter_type": letter_type,
        "prototype_file": prototype_file,
        "missing_sections": comparison.get("missing_sections", []),
        "unexpected_sections": comparison.get("unexpected_sections", []),
        "summary": comparison.get("summary", "Prototype comparison completed."),
    }
