"""Prompt templates for deterministic and agentic document QA analysis."""

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


def build_claim_extraction_prompt(
    document_text: str,
    metadata: dict[str, Any] | None = None,
) -> str:
    metadata_text = json.dumps(metadata or {}, ensure_ascii=False)

    return f"""
You are an evidence-based compensation letter extraction agent.

Extract only claims that are explicitly supported by the document.
Do not infer missing values.
Each claim must include a short evidence quote copied from the document.
If key facts are missing, add them to unresolved_questions.

Return STRICT JSON only, with this exact schema:
{{
  "status": "success|needs_review|skipped",
  "summary": "short summary",
  "claims": [
    {{
      "field_name": "employee_id|employee_name|department|title|base_pay|annual_incentive|letter_type|effective_date|other",
      "value": "extracted value",
      "confidence": 0.0,
      "evidence": [
        {{
          "source": "document",
          "quote": "short exact quote",
          "location": "optional location"
        }}
      ]
    }}
  ],
  "unresolved_questions": ["..."],
  "confidence": 0.0
}}

Metadata (optional):
{metadata_text}

Document text:
{document_text}
""".strip()


def build_evidence_review_prompt(
    instruction: str,
    document_text: str,
    context: dict[str, Any] | None = None,
) -> str:
    context_text = json.dumps(context or {}, ensure_ascii=False)

    return f"""
You are an evidence-based QA reviewer for compensation letters.

Use only the supplied document and structured QA context.
Every issue must be grounded in document evidence or explicit missing evidence.
If evidence is insufficient, return needs_review.

Evaluate:
1) employee data accuracy
2) template and section adherence
3) branding or logo concerns
4) contradictions across checks
5) unresolved risks that still need human review

Return STRICT JSON only, with this exact schema:
{{
  "overall_status": "pass|fail|needs_review",
  "summary": "short summary",
  "issues": [
    {{
      "category": "employee_data|template|branding|contradiction|missing_evidence|instruction_compliance",
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

Structured QA context:
{context_text}

Document text:
{document_text}
""".strip()
