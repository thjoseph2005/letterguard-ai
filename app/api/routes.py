"""API routes for LetterGuard AI."""

from fastapi import APIRouter

from app.models.letter import LetterValidationRequest, LetterValidationResponse
from app.workflows.letter_review_graph import run_letter_review

router = APIRouter(tags=["letterguard"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "LetterGuard API is running"}


@router.post("/validate", response_model=LetterValidationResponse)
def validate_letter(payload: LetterValidationRequest) -> LetterValidationResponse:
    """Route request through LangGraph workflow skeleton."""
    return run_letter_review(payload)
