"""Models for LLM-driven QA analysis."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class IssueItem(BaseModel):
    category: str
    severity: Literal["low", "medium", "high"] = "medium"
    description: str
    evidence: str | None = None


class QAResult(BaseModel):
    overall_status: Literal["pass", "fail", "needs_review"]
    summary: str
    issues: list[IssueItem] = Field(default_factory=list)
    recommendations: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)


class QAAnalyzeRequest(BaseModel):
    instruction: str = Field(min_length=3)
    document_text: str = Field(min_length=1)
    metadata: dict[str, Any] | None = None
