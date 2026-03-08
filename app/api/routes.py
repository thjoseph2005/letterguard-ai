"""API routes for LetterGuard AI."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.models.extraction import ExtractionSummaryResponse
from app.models.letter import LetterValidationRequest, LetterValidationResponse
from app.services.file_service import save_uploaded_file, validate_file_type
from app.services.pdf_extraction_service import (
    extract_pdf_metadata,
    extract_pdf_text,
    save_extraction_result,
)
from app.workflows.letter_review_graph import run_letter_review

router = APIRouter(tags=["letterguard"])


@router.get("/ping")
def ping() -> dict[str, str]:
    return {"message": "LetterGuard API is running"}


@router.post("/validate", response_model=LetterValidationResponse)
def validate_letter(payload: LetterValidationRequest) -> LetterValidationResponse:
    """Route request through LangGraph workflow skeleton."""
    return run_letter_review(payload)


@router.post("/upload/employees")
def upload_employees(file: UploadFile = File(...)) -> dict[str, str]:
    if not validate_file_type(file.filename, [".csv"]):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .csv is allowed.")

    saved_path = save_uploaded_file(file, "sample_data/employees")
    return {"status": "success", "file_name": file.filename, "saved_to": saved_path}


@router.post("/upload/prototype")
def upload_prototype(file: UploadFile = File(...)) -> dict[str, str]:
    if not validate_file_type(file.filename, [".pdf"]):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .pdf is allowed.")

    saved_path = save_uploaded_file(file, "sample_data/prototypes")
    return {"status": "success", "file_name": file.filename, "saved_to": saved_path}


@router.post("/upload/generated-letter")
def upload_generated_letter(file: UploadFile = File(...)) -> dict[str, str]:
    if not validate_file_type(file.filename, [".pdf"]):
        raise HTTPException(status_code=400, detail="Invalid file type. Only .pdf is allowed.")

    saved_path = save_uploaded_file(file, "sample_data/generated_letters")
    return {"status": "success", "file_name": file.filename, "saved_to": saved_path}


@router.post("/upload/logo")
def upload_logo(file: UploadFile = File(...)) -> dict[str, str]:
    if not validate_file_type(file.filename, [".png", ".jpg", ".jpeg"]):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Only .png, .jpg, .jpeg are allowed.",
        )

    saved_path = save_uploaded_file(file, "sample_data/logos")
    return {"status": "success", "file_name": file.filename, "saved_to": saved_path}


def _extract_and_save(pdf_path: Path, output_dir: Path) -> ExtractionSummaryResponse:
    if not pdf_path.exists():
        raise HTTPException(status_code=404, detail=f"File not found: {pdf_path.name}")
    if pdf_path.suffix.lower() != ".pdf":
        raise HTTPException(status_code=400, detail="Only .pdf files are supported for extraction.")

    extracted = extract_pdf_text(str(pdf_path))
    metadata = extract_pdf_metadata(str(pdf_path))
    combined_result = {"metadata": metadata, "extraction": extracted}

    output_path = output_dir / f"{pdf_path.name}.json"
    saved_output = save_extraction_result(combined_result, str(output_path))
    return ExtractionSummaryResponse(
        status="success",
        file_name=pdf_path.name,
        page_count=extracted.get("page_count", 0),
        json_output_path=saved_output,
    )


@router.get("/extract/prototype/{file_name}", response_model=ExtractionSummaryResponse)
def extract_prototype(file_name: str) -> ExtractionSummaryResponse:
    pdf_path = Path("sample_data/prototypes") / Path(file_name).name
    output_dir = Path("sample_data/extracted/prototypes")
    return _extract_and_save(pdf_path, output_dir)


@router.get("/extract/generated-letter/{file_name}", response_model=ExtractionSummaryResponse)
def extract_generated_letter(file_name: str) -> ExtractionSummaryResponse:
    pdf_path = Path("sample_data/generated_letters") / Path(file_name).name
    output_dir = Path("sample_data/extracted/generated_letters")
    return _extract_and_save(pdf_path, output_dir)
