"""State definitions for LangGraph workflows."""

from typing import Any, TypedDict


class LetterReviewState(TypedDict, total=False):
    letter_text: str
    employee_id: str
    issues: list[str]
    summary: str
    status: str


class QAWorkflowState(TypedDict, total=False):
    file_name: str
    generated_extraction_json_path: str
    employee_csv_path: str
    prototype_extraction_dir: str
    logo_dir: str
    instruction: str
    document_text: str
    metadata: dict[str, Any]
    planner_result: dict[str, Any]
    qa_result: dict[str, Any]
    data_validation_result: dict[str, Any]
    template_result: dict[str, Any]
    logo_result: dict[str, Any]
    decision_result: dict[str, Any]
    review_result: dict[str, Any] | None
    errors: list[str]
