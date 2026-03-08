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

## Next Build Steps
- Replace stubs in `app/services/` with Azure SDK clients.
- Add policy/rule checks in `app/agents/letter_review_agent.py`.
- Expand LangGraph with multi-step review + remediation nodes.
- Add integration tests for API and service adapters.
