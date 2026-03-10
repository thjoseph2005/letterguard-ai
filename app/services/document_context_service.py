"""Helpers for loading structured document context from extraction JSON."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_extraction_payload(extraction_json_path: str) -> dict[str, Any]:
    path = Path(extraction_json_path)
    return json.loads(path.read_text(encoding="utf-8"))


def load_document_context(extraction_json_path: str) -> dict[str, Any]:
    payload = load_extraction_payload(extraction_json_path)
    extraction = payload.get("extraction", {})
    metadata = payload.get("metadata", {})

    if isinstance(extraction, dict):
        document_text = extraction.get("full_text", "")
        page_count = extraction.get("page_count", 0)
        pages = extraction.get("pages", [])
    else:
        document_text = payload.get("full_text", "")
        page_count = payload.get("page_count", 0)
        pages = payload.get("pages", [])

    return {
        "file_name": Path(extraction_json_path).name.removesuffix(".json"),
        "document_text": document_text if isinstance(document_text, str) else "",
        "metadata": metadata if isinstance(metadata, dict) else {},
        "page_count": page_count if isinstance(page_count, int) else 0,
        "pages": pages if isinstance(pages, list) else [],
    }
