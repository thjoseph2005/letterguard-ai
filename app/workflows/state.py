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
    document_context: dict[str, Any]
    planner_result: dict[str, Any]
    qa_result: dict[str, Any]
    claim_extraction_result: dict[str, Any]
    data_validation_result: dict[str, Any]
    template_result: dict[str, Any]
    logo_result: dict[str, Any]
    evidence_review_result: dict[str, Any]
    decision_result: dict[str, Any]
    review_result: dict[str, Any] | None
    errors: list[str]


class ChatWorkflowState(TypedDict, total=False):
    user_message: str
    intent: dict[str, Any]
    request_type: str
    document_type: str
    reference_data: dict[str, Any]
    employees: list[dict[str, str]]
    documents: list[dict[str, Any]]
    matched_employees: list[dict[str, str]]
    prototype_mapping: dict[str, str]
    logo_mappings: dict[str, str]
    validation_results: list[dict[str, Any]]
    prototype_reasoning_results: list[dict[str, Any]]
    answer: str
    results: list[dict[str, Any]]
    status: str
    error: str
    notes: list[str]
