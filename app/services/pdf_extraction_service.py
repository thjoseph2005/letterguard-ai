"""Local PDF text and metadata extraction using PyMuPDF."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import fitz

from app.services.file_service import create_directory_if_not_exists


def extract_pdf_text(pdf_path: str) -> dict[str, Any]:
    path = Path(pdf_path)
    pages: list[dict[str, Any]] = []
    page_texts: list[str] = []

    with fitz.open(path) as document:
        for page_index in range(document.page_count):
            page_number = page_index + 1
            page = document.load_page(page_index)

            try:
                text = page.get_text("text") or ""
            except Exception:
                text = ""

            try:
                raw_blocks = page.get_text("blocks") or []
            except Exception:
                raw_blocks = []

            blocks: list[dict[str, Any]] = []
            for block in raw_blocks:
                blocks.append(
                    {
                        "bbox": [block[0], block[1], block[2], block[3]],
                        "text": block[4] if len(block) > 4 and isinstance(block[4], str) else "",
                        "block_no": block[5] if len(block) > 5 else None,
                        "block_type": block[6] if len(block) > 6 else None,
                    }
                )

            pages.append({"page_number": page_number, "text": text, "blocks": blocks})
            page_texts.append(text)

        return {
            "file_name": path.name,
            "page_count": document.page_count,
            "full_text": "\n".join(page_texts).strip(),
            "pages": pages,
        }


def save_extraction_result(result: dict[str, Any], output_path: str) -> str:
    output = Path(output_path)
    create_directory_if_not_exists(str(output.parent))
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    return str(output)


def extract_pdf_metadata(pdf_path: str) -> dict[str, Any]:
    path = Path(pdf_path)
    with fitz.open(path) as document:
        return {
            "file_name": path.name,
            "page_count": document.page_count,
            "metadata": document.metadata or {},
        }
