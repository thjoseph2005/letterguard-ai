"""API routes for LetterGuard AI."""

from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.agents.data_validation_agent import validate_generated_letter_against_employee
from app.agents.template_agent import review_generated_letter_against_prototype
from app.models.chat import ChatAskResponse, ChatRequest, ChatResponse
from app.models.extraction import ExtractionSummaryResponse
from app.models.letter import LetterValidationRequest, LetterValidationResponse
from app.models.qa_models import QAAnalyzeRequest, QAResult
from app.services.chat_orchestration_service import run_chat_request
from app.services.chat_command_service import execute_chat_command, parse_chat_instruction
from app.services.file_service import save_uploaded_file, validate_file_type
from app.services.llm.azure_openai_service import AzureOpenAIService
from app.services.pdf_extraction_service import (
    extract_pdf_metadata,
    extract_pdf_text,
    save_extraction_result,
)
from app.services.prototype_comparison_service import classify_letter_type_from_text
from app.services.qa_orchestration_service import (
    run_letterguard_workflow_for_all_generated_letters,
    run_letterguard_workflow_for_file,
)
from app.workflows.letter_review_graph import run_letter_review

router = APIRouter(tags=["letterguard"])
llm_service = AzureOpenAIService()


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


@router.get("/validate/generated-letter/{file_name}")
def validate_generated_letter(file_name: str) -> dict:
    safe_file_name = Path(file_name).name
    extraction_json_path = Path("sample_data/extracted/generated_letters") / f"{safe_file_name}.json"
    employee_csv_path = Path("sample_data/employees/employees.csv")

    if not extraction_json_path.exists():
        raise HTTPException(
            status_code=404,
            detail=f"Extraction JSON not found for {safe_file_name}. Expected: {extraction_json_path}",
        )
    if not employee_csv_path.exists():
        raise HTTPException(status_code=404, detail="Employee CSV file not found.")

    return validate_generated_letter_against_employee(
        file_name=safe_file_name,
        extraction_json_path=str(extraction_json_path),
        employee_csv_path=str(employee_csv_path),
    )


@router.get("/validate/generated-letters")
def validate_generated_letters() -> dict:
    extraction_dir = Path("sample_data/extracted/generated_letters")
    employee_csv_path = Path("sample_data/employees/employees.csv")

    if not extraction_dir.exists():
        raise HTTPException(status_code=404, detail="Generated letter extraction directory not found.")
    if not employee_csv_path.exists():
        raise HTTPException(status_code=404, detail="Employee CSV file not found.")

    results: list[dict] = []
    for json_file in sorted(extraction_dir.glob("*.json")):
        file_name = json_file.name.removesuffix(".json")
        results.append(
            validate_generated_letter_against_employee(
                file_name=file_name,
                extraction_json_path=str(json_file),
                employee_csv_path=str(employee_csv_path),
            )
        )

    status_counts = {"pass": 0, "fail": 0, "needs_review": 0}
    for result in results:
        status = result.get("status")
        if status in status_counts:
            status_counts[status] += 1

    return {
        "total": len(results),
        "pass": status_counts["pass"],
        "fail": status_counts["fail"],
        "needs_review": status_counts["needs_review"],
        "results": results,
    }


def _load_full_text_from_extraction_json(json_path: Path) -> str:
    import json

    payload = json.loads(json_path.read_text(encoding="utf-8"))
    extraction = payload.get("extraction", {})
    if isinstance(extraction, dict) and isinstance(extraction.get("full_text"), str):
        return extraction["full_text"]
    if isinstance(payload.get("full_text"), str):
        return payload["full_text"]
    return ""


@router.get("/classify/generated-letter/{file_name}")
def classify_generated_letter(file_name: str) -> dict:
    safe_file_name = Path(file_name).name
    extraction_json_path = Path("sample_data/extracted/generated_letters") / f"{safe_file_name}.json"
    if not extraction_json_path.exists():
        raise HTTPException(status_code=404, detail=f"Extraction JSON not found: {extraction_json_path}")

    full_text = _load_full_text_from_extraction_json(extraction_json_path)
    classification = classify_letter_type_from_text(full_text)
    return {"file_name": safe_file_name, **classification}


@router.get("/compare/generated-letter/{file_name}")
def compare_generated_letter(file_name: str) -> dict:
    safe_file_name = Path(file_name).name
    generated_extraction_json_path = Path("sample_data/extracted/generated_letters") / f"{safe_file_name}.json"
    if not generated_extraction_json_path.exists():
        raise HTTPException(status_code=404, detail=f"Extraction JSON not found: {generated_extraction_json_path}")

    return review_generated_letter_against_prototype(
        file_name=safe_file_name,
        generated_extraction_json_path=str(generated_extraction_json_path),
        prototype_extraction_dir="sample_data/extracted/prototypes",
    )


@router.get("/compare/generated-letters")
def compare_generated_letters() -> dict:
    extraction_dir = Path("sample_data/extracted/generated_letters")
    if not extraction_dir.exists():
        raise HTTPException(status_code=404, detail="Generated letter extraction directory not found.")

    results: list[dict] = []
    for json_file in sorted(extraction_dir.glob("*.json")):
        file_name = json_file.name.removesuffix(".json")
        results.append(
            review_generated_letter_against_prototype(
                file_name=file_name,
                generated_extraction_json_path=str(json_file),
                prototype_extraction_dir="sample_data/extracted/prototypes",
            )
        )

    status_counts = {"pass": 0, "fail": 0, "needs_review": 0}
    for result in results:
        status = result.get("status")
        if status in status_counts:
            status_counts[status] += 1

    return {
        "total": len(results),
        "pass": status_counts["pass"],
        "fail": status_counts["fail"],
        "needs_review": status_counts["needs_review"],
        "results": results,
    }


@router.get("/qa/run/{file_name}")
def qa_run_single(file_name: str) -> dict:
    return run_letterguard_workflow_for_file(Path(file_name).name)


@router.get("/qa/run-all")
def qa_run_all() -> dict:
    return run_letterguard_workflow_for_all_generated_letters()


@router.post("/chat", response_model=ChatResponse)
def chat_endpoint(payload: ChatRequest) -> ChatResponse:
    command = parse_chat_instruction(payload.message)
    result = execute_chat_command(command)
    return ChatResponse(**result)


@router.post("/chat/ask", response_model=ChatAskResponse)
def chat_ask_endpoint(payload: ChatRequest) -> ChatAskResponse:
    result = run_chat_request(payload.message)
    return ChatAskResponse(**result)


@router.post("/qa/analyze", response_model=QAResult)
async def qa_analyze(payload: QAAnalyzeRequest) -> QAResult:
    try:
        result = await llm_service.analyze_document(
            instruction=payload.instruction,
            document_text=payload.document_text,
            metadata=payload.metadata,
        )
        return QAResult(**result)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
