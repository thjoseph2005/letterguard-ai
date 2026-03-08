# LetterGuard AI

LetterGuard AI is a modular Python 3.11 project scaffold for validating employee compensation letters with an agentic workflow.

## Stack
- FastAPI backend for API exposure
- LangGraph for workflow orchestration
- Azure service abstraction layer for LLM and storage integrations

## Project Structure

```text
app/
  agents/       # Agent interfaces and domain-specific agent implementations
  api/          # FastAPI route definitions
  services/     # Azure adapters and service factories
  workflows/    # LangGraph states and graph composition
  models/       # Pydantic request/response schemas
  utils/        # Shared helpers (logging, config utilities)
ui/             # Frontend placeholder for capstone demo
prompts/        # Prompt templates and system instructions
tests/          # Backend tests
sample_data/    # Local sample artifacts for demo/testing
```

## Architecture Overview
1. Client sends letter content to the FastAPI endpoint.
2. API route maps request payload to domain models.
3. LangGraph workflow executes one or more agents against shared state.
4. Agents use `services/` adapters to call Azure OpenAI / Blob Storage.
5. Workflow returns structured validation output to the API response.

## Quick Start

```bash
python3.11 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Open API docs at `http://127.0.0.1:8000/docs`.

## Local PDF Extraction (Milestone 3)
- Uses **PyMuPDF** (`fitz`) for local parsing only.
- Prototype PDFs are read from `sample_data/prototypes/`.
- Generated-letter PDFs are read from `sample_data/generated_letters/`.
- Extraction JSON is saved to:
  - `sample_data/extracted/prototypes/`
  - `sample_data/extracted/generated_letters/`

### Extraction Endpoints
- `GET /api/extract/prototype/{file_name}`
- `GET /api/extract/generated-letter/{file_name}`

Both return:
```json
{
  "status": "success",
  "file_name": "sample.pdf",
  "page_count": 2,
  "json_output_path": "sample_data/extracted/generated_letters/sample.pdf.json"
}
```

### How It Works
1. Endpoint loads the requested local PDF file.
2. `pdf_extraction_service` extracts:
   - page text
   - text blocks per page
   - document-level `full_text`
   - basic PDF metadata
3. Combined extraction + metadata JSON is written to the extracted folder.

### Testing Extraction Endpoints
1. Start server:
```bash
uvicorn app.main:app --reload
```
2. Upload or place a PDF in:
   - `sample_data/prototypes/` or
   - `sample_data/generated_letters/`
3. Call endpoint, for example:
```bash
curl "http://127.0.0.1:8000/api/extract/prototype/example.pdf"
```

### Run Tests
```bash
pytest tests/test_pdf_extraction.py -q
```
