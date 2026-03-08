"""State definitions for LangGraph workflows."""

from typing import TypedDict


class LetterReviewState(TypedDict, total=False):
    letter_text: str
    employee_id: str
    issues: list[str]
    summary: str
    status: str
