from pathlib import Path

import fitz
from fastapi.testclient import TestClient

from app.main import app
from app.services.pdf_extraction_service import (
    extract_pdf_metadata,
    extract_pdf_text,
    save_extraction_result,
)


def _create_sample_pdf(path: Path, text: str) -> None:
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((72, 72), text)
    doc.save(path)
    doc.close()


def test_pdf_extraction_service_smoke(tmp_path: Path) -> None:
    pdf_path = tmp_path / "smoke.pdf"
    json_path = tmp_path / "smoke.pdf.json"
    _create_sample_pdf(pdf_path, "LetterGuard extraction smoke test")

    extracted = extract_pdf_text(str(pdf_path))
    metadata = extract_pdf_metadata(str(pdf_path))
    output_path = save_extraction_result({"metadata": metadata, "extraction": extracted}, str(json_path))

    assert extracted["file_name"] == "smoke.pdf"
    assert extracted["page_count"] == 1
    assert "LetterGuard extraction smoke test" in extracted["full_text"]
    assert metadata["page_count"] == 1
    assert output_path.endswith("smoke.pdf.json")
    assert json_path.exists()


def test_extract_prototype_endpoint() -> None:
    sample_pdf = Path("sample_data/prototypes/test_prototype_extract.pdf")
    output_json = Path("sample_data/extracted/prototypes/test_prototype_extract.pdf.json")
    sample_pdf.parent.mkdir(parents=True, exist_ok=True)
    _create_sample_pdf(sample_pdf, "Prototype extraction endpoint test")

    client = TestClient(app)
    response = client.get("/api/extract/prototype/test_prototype_extract.pdf")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["file_name"] == "test_prototype_extract.pdf"
    assert body["page_count"] == 1
    assert body["json_output_path"].endswith("sample_data/extracted/prototypes/test_prototype_extract.pdf.json")
    assert output_json.exists()

    sample_pdf.unlink(missing_ok=True)
    output_json.unlink(missing_ok=True)
