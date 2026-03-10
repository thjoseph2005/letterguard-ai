"""Hybrid claim extraction agent with deterministic fallback."""

from __future__ import annotations

import asyncio
import re
from typing import Any

from app.services.llm.azure_openai_service import AzureOpenAIService
from app.services.prototype_comparison_service import classify_letter_type_from_text


def _find_line_with_pattern(document_text: str, pattern: str) -> tuple[str, str | None]:
    regex = re.compile(pattern, flags=re.IGNORECASE)
    for line_number, line in enumerate(document_text.splitlines(), start=1):
        if regex.search(line):
            return line.strip(), f"line {line_number}"
    match = regex.search(document_text)
    if match:
        snippet = document_text[max(0, match.start() - 40) : match.end() + 40].strip()
        return snippet, None
    return "", None


def _append_claim(
    claims: list[dict[str, Any]],
    field_name: str,
    value: str,
    evidence_quote: str,
    location: str | None,
    confidence: float = 0.7,
) -> None:
    if not value.strip():
        return
    claims.append(
        {
            "field_name": field_name,
            "value": value.strip(),
            "confidence": confidence,
            "evidence": [{"source": "document", "quote": evidence_quote or value.strip(), "location": location}],
        }
    )


def _deterministic_extract_claims(document_text: str) -> dict[str, Any]:
    claims: list[dict[str, Any]] = []

    employee_id_match = re.search(r"\bE\d{3}\b", document_text, flags=re.IGNORECASE)
    if employee_id_match:
        quote, location = _find_line_with_pattern(document_text, re.escape(employee_id_match.group(0)))
        _append_claim(claims, "employee_id", employee_id_match.group(0).upper(), quote, location, 0.95)

    labeled_patterns = {
        "employee_name": r"(?:name|employee)\s*:\s*([A-Z][A-Za-z' -]+)",
        "department": r"department\s*:\s*([A-Za-z&' -]+)",
        "title": r"title\s*:\s*([A-Za-z&,'/ -]+)",
        "effective_date": r"(?:effective date|effective)\s*:\s*([A-Za-z0-9, /-]+)",
    }
    for field_name, pattern in labeled_patterns.items():
        match = re.search(pattern, document_text, flags=re.IGNORECASE)
        if not match:
            continue
        quote, location = _find_line_with_pattern(document_text, pattern)
        _append_claim(claims, field_name, match.group(1), quote, location, 0.8)

    for field_name, label in [("base_pay", "base pay"), ("annual_incentive", "annual incentive")]:
        match = re.search(rf"{label}\s*:\s*\$?\s*([\d,]+(?:\.\d+)?)", document_text, flags=re.IGNORECASE)
        if not match:
            continue
        quote, location = _find_line_with_pattern(document_text, rf"{label}\s*:\s*\$?\s*([\d,]+(?:\.\d+)?)")
        _append_claim(claims, field_name, match.group(1).replace(",", ""), quote, location, 0.9)

    letter_type = classify_letter_type_from_text(document_text)
    if letter_type.get("letter_type") != "unknown":
        keyword = ", ".join(letter_type.get("matched_keywords", [])[:2]) or str(letter_type.get("letter_type", ""))
        quote, location = _find_line_with_pattern(document_text, re.escape(keyword.split(",")[0])) if keyword else ("", None)
        _append_claim(
            claims,
            "letter_type",
            str(letter_type.get("letter_type", "")),
            quote or keyword,
            location,
            float(letter_type.get("confidence", 0.5)),
        )

    unresolved_questions = []
    core_fields = {"employee_id", "employee_name", "department", "title"}
    extracted_fields = {claim["field_name"] for claim in claims}
    for field_name in sorted(core_fields - extracted_fields):
        unresolved_questions.append(f"Document did not clearly state {field_name}.")

    status = "success" if claims else "needs_review"
    if not document_text.strip():
        status = "skipped"

    return {
        "status": status,
        "summary": "Extracted evidence-backed claims from document text." if claims else "Could not extract enough structured claims.",
        "claims": claims,
        "unresolved_questions": unresolved_questions,
        "confidence": 0.8 if claims else 0.2,
    }


def extract_claims_from_letter(
    document_text: str,
    metadata: dict[str, Any] | None = None,
    llm_service: AzureOpenAIService | None = None,
) -> dict[str, Any]:
    if not document_text.strip():
        return {
            "status": "skipped",
            "summary": "Claim extraction skipped because no document text was available.",
            "claims": [],
            "unresolved_questions": ["No document text was provided."],
            "confidence": 0.0,
        }

    service = llm_service
    if service is not None:
        try:
            return asyncio.run(service.extract_claims(document_text=document_text, metadata=metadata))
        except Exception:
            pass

    return _deterministic_extract_claims(document_text)
