"""Prompt templates for deterministic document QA analysis."""

from __future__ import annotations

import json
from typing import Any


def build_document_qa_prompt(
    instruction: str,
    document_text: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    metadata_text = json.dumps(metadata or {}, ensure_ascii=False)

    return f"""
You are a document quality assurance analyst.

Analyze only the provided document content and instruction.
Do not use outside knowledge. Do not hallucinate missing facts.
If information is not present, mark it as missing or needs_review.

Evaluate:
1) Completeness
2) Consistency
3) Missing sections
4) Contradictions
5) Clarity
6) Compliance with user instruction

Return STRICT JSON only, with this exact schema:
{{
  "overall_status": "pass|fail|needs_review",
  "summary": "short summary",
  "issues": [
    {{
      "category": "completeness|consistency|missing_sections|contradictions|clarity|instruction_compliance",
      "severity": "low|medium|high",
      "description": "...",
      "evidence": "..."
    }}
  ],
  "recommendations": ["..."],
  "confidence": 0.0
}}

Instruction:
{instruction}

Metadata (optional):
{metadata_text}

Document text:
{document_text}
""".strip()
