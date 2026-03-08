"""Pydantic models for letter validation flows."""

from pydantic import BaseModel, Field


class LetterValidationRequest(BaseModel):
    letter_text: str = Field(..., description="Raw compensation letter text")
    employee_id: str | None = Field(default=None, description="Optional employee ID")


class LetterValidationResponse(BaseModel):
    status: str
    issues: list[str]
    summary: str
