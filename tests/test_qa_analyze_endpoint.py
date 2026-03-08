from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_qa_analyze_validation_error(monkeypatch) -> None:
    async def fake_analyze_document(instruction: str, document_text: str, metadata=None):
        raise ValueError("Missing Azure OpenAI configuration")

    monkeypatch.setattr("app.api.routes.llm_service.analyze_document", fake_analyze_document)

    response = client.post(
        "/api/qa/analyze",
        json={
            "instruction": "Check completeness",
            "document_text": "Sample text",
            "metadata": {},
        },
    )
    assert response.status_code == 400
    assert "Missing Azure OpenAI configuration" in response.json()["detail"]
