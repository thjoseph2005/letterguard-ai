"""Response parsing and validation for LLM QA outputs."""

from __future__ import annotations

import json
import re
from typing import Any

from pydantic import ValidationError

from app.models.qa_models import QAResult


def _strip_code_fences(raw: str) -> str:
    cleaned = raw.strip()
    cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
    cleaned = re.sub(r"```$", "", cleaned).strip()
    return cleaned


def parse_qa_result_json(raw_content: str) -> dict[str, Any]:
    cleaned = _strip_code_fences(raw_content)
    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError(f"LLM response is not valid JSON: {exc}") from exc

    try:
        model = QAResult.model_validate(parsed)
    except ValidationError as exc:
        raise ValueError(f"LLM response does not match QAResult schema: {exc}") from exc

    return model.model_dump()
