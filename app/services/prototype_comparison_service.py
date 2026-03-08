"""Deterministic classification and prototype comparison helpers."""

from __future__ import annotations

import re
from typing import Any


LETTER_TYPE_KEYWORDS: dict[str, list[str]] = {
    "promotion": [
        "promotion",
        "new role",
        "new title",
        "congratulations on your promotion",
    ],
    "base_pay_increase": [
        "base pay",
        "salary increase",
        "annual base salary",
        "increase in your base pay",
    ],
    "annual_incentive_award": [
        "annual incentive",
        "bonus",
        "incentive award",
        "awarded",
    ],
}

PROTOTYPE_MAP: dict[str, str] = {
    "promotion": "promotion_prototype.pdf.json",
    "base_pay_increase": "salary_increase_prototype.pdf.json",
    "annual_incentive_award": "bonus_prototype.pdf.json",
}

STRONG_CROSS_TYPE_KEYWORDS: dict[str, list[str]] = {
    "promotion": ["congratulations on your promotion", "new role", "new title"],
    "base_pay_increase": ["salary increase", "annual base salary", "increase in your base pay"],
    "annual_incentive_award": ["incentive award", "awarded a bonus"],
}


def _normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip().lower())


def _sanitize_variable_content(text: str) -> str:
    sanitized = text or ""
    sanitized = re.sub(r"\bE\d{3}\b", " employee_id ", sanitized, flags=re.IGNORECASE)
    sanitized = re.sub(r"\$?\s*\d[\d,]*(?:\.\d+)?", " amount ", sanitized)
    sanitized = re.sub(
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2},?\s+\d{2,4}\b",
        " date ",
        sanitized,
        flags=re.IGNORECASE,
    )
    sanitized = re.sub(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b", " date ", sanitized)
    return _normalize_text(sanitized)


def classify_letter_type_from_text(text: str) -> dict[str, Any]:
    normalized = _sanitize_variable_content(text)
    scores: dict[str, int] = {}
    matched_by_type: dict[str, list[str]] = {}

    for letter_type, keywords in LETTER_TYPE_KEYWORDS.items():
        matched = [keyword for keyword in keywords if keyword in normalized]
        matched_by_type[letter_type] = matched
        scores[letter_type] = len(matched)

    best_type = max(scores, key=scores.get)
    best_score = scores[best_type]

    if best_score == 0:
        return {"letter_type": "unknown", "confidence": 0.1, "matched_keywords": []}

    confidence = round(best_score / max(1, len(LETTER_TYPE_KEYWORDS[best_type])), 2)
    return {
        "letter_type": best_type,
        "confidence": confidence,
        "matched_keywords": matched_by_type[best_type],
    }


def get_prototype_file_for_letter_type(letter_type: str) -> str | None:
    return PROTOTYPE_MAP.get(letter_type)


def extract_required_sections_from_prototype(prototype_text: str) -> list[str]:
    normalized = _sanitize_variable_content(prototype_text)
    sections: list[str] = []
    skip_markers = ["template", "employee letter"]

    for sentence in re.split(r"[.\n]+", normalized):
        cleaned = sentence.strip()
        if len(cleaned) < 8:
            continue
        if any(marker in cleaned for marker in skip_markers):
            continue
        if cleaned:
            sections.append(cleaned)

    for keywords in LETTER_TYPE_KEYWORDS.values():
        for keyword in keywords:
            if keyword in normalized and keyword not in sections:
                sections.append(keyword)

    deduped: list[str] = []
    seen: set[str] = set()
    for section in sections:
        if section not in seen:
            seen.add(section)
            deduped.append(section)
    return deduped


def compare_generated_text_to_prototype(
    generated_text: str,
    prototype_text: str,
    letter_type: str,
) -> dict[str, Any]:
    normalized_generated = _sanitize_variable_content(generated_text)
    required_sections = extract_required_sections_from_prototype(prototype_text)

    prototype_file = get_prototype_file_for_letter_type(letter_type)
    if letter_type == "unknown" or not prototype_file:
        return {
            "status": "needs_review",
            "letter_type": letter_type,
            "prototype_file": prototype_file or "",
            "missing_sections": [],
            "unexpected_sections": [],
            "similarity_notes": ["Could not map unknown letter type to a prototype."],
            "summary": "Unable to determine prototype for comparison.",
        }

    missing_sections = [section for section in required_sections if section not in normalized_generated]

    unexpected_sections: list[str] = []
    for other_type, keywords in STRONG_CROSS_TYPE_KEYWORDS.items():
        if other_type == letter_type:
            continue
        for keyword in keywords:
            if keyword in normalized_generated:
                unexpected_sections.append(keyword)

    unexpected_sections = sorted(set(unexpected_sections))
    similarity_notes = [
        f"Required sections found: {len(required_sections) - len(missing_sections)}/{len(required_sections)}",
    ]
    if unexpected_sections:
        similarity_notes.append("Detected keywords from other letter types.")

    if not required_sections:
        status = "needs_review"
        summary = "Prototype sections were empty; manual review required."
    elif missing_sections or unexpected_sections:
        status = "fail"
        summary = "Prototype comparison found missing or unexpected content."
    else:
        status = "pass"
        summary = "Prototype comparison passed."

    return {
        "status": status,
        "letter_type": letter_type,
        "prototype_file": prototype_file,
        "missing_sections": missing_sections,
        "unexpected_sections": unexpected_sections,
        "similarity_notes": similarity_notes,
        "summary": summary,
    }
