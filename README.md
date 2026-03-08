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

## Employee Data Validation (Milestone 4)
- Validation is deterministic and local-only.
- Inputs:
  - Employee CSV: `sample_data/employees/employees.csv`
  - Generated-letter extraction JSON: `sample_data/extracted/generated_letters/*.json`
- No Azure or LLM calls are used in this milestone.

### Matching Logic
1. Read `full_text` from extracted generated-letter JSON.
2. Try to match employee by `employee_id` (`E###`) from file name or text.
3. If no ID match, try employee name match from CSV.
4. Validate required fields:
   - `employee_id`
   - `name`
   - `department`
   - `title`
   - `base_pay`
   - `annual_incentive`

Decision outcomes:
- `pass`: all required fields found
- `fail`: employee matched, but one or more fields missing/mismatched
- `needs_review`: no confident employee match

### Validation Endpoints
- `GET /api/validate/generated-letter/{file_name}`
- `GET /api/validate/generated-letters`

Example single-file response:
```json
{
  "status": "pass",
  "file_name": "E001_letter.pdf",
  "employee_id": "E001",
  "matched_employee_name": "John Smith",
  "field_results": {
    "name": {"expected": "John Smith", "found": true},
    "department": {"expected": "Wealth Management", "found": true},
    "title": {"expected": "Advisor", "found": true},
    "base_pay": {"expected": 120000, "found": true},
    "annual_incentive": {"expected": 20000, "found": true}
  },
  "issues": [],
  "summary": "All expected employee fields matched."
}
```

### Test Milestone 4
```bash
pytest tests/test_employee_data_service.py tests/test_data_validation_agent.py -q
```

## Letter Type Classification + Prototype Comparison (Milestone 5)
- Deterministic, local-only logic.
- Inputs:
  - Extracted generated-letter JSON: `sample_data/extracted/generated_letters/*.json`
  - Extracted prototype JSON: `sample_data/extracted/prototypes/*.json`
- No Azure and no LLM calls in this milestone.

### Classification Rules
Keyword matching only:
- `promotion`: `promotion`, `new role`, `new title`, `congratulations on your promotion`
- `base_pay_increase`: `base pay`, `salary increase`, `annual base salary`, `increase in your base pay`
- `annual_incentive_award`: `annual incentive`, `bonus`, `incentive award`, `awarded`

If no clear keyword signal exists, letter type is `unknown` with low confidence.

### Prototype Comparison
1. Classify generated letter from extracted `full_text`.
2. Map letter type to a prototype extraction file:
   - `promotion -> promotion_prototype.pdf.json`
   - `base_pay_increase -> salary_increase_prototype.pdf.json`
   - `annual_incentive_award -> bonus_prototype.pdf.json`
3. Compare generated text with prototype expected sections.
4. Ignore variable content patterns where possible (employee IDs, dollar amounts, common date formats).
5. Return `pass`, `fail`, or `needs_review`.

### Milestone 5 Endpoints
- `GET /api/classify/generated-letter/{file_name}`
- `GET /api/compare/generated-letter/{file_name}`
- `GET /api/compare/generated-letters`

Example classify response:
```json
{
  "file_name": "E001_letter.pdf",
  "letter_type": "promotion",
  "confidence": 0.5,
  "matched_keywords": ["promotion", "new role"]
}
```

Example compare response:
```json
{
  "status": "pass",
  "file_name": "E001_letter.pdf",
  "detected_letter_type": "promotion",
  "prototype_file": "promotion_prototype.pdf.json",
  "missing_sections": [],
  "unexpected_sections": [],
  "summary": "Prototype comparison passed."
}
```

### Test Milestone 5
```bash
pytest tests/test_prototype_comparison_service.py tests/test_template_agent.py -q
```
