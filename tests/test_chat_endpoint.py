from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def test_chat_endpoint_success(monkeypatch) -> None:
    def fake_parse(message: str) -> dict:
        return {"intent": "run_single", "file_name": "E001_letter.pdf", "employee_name": "", "raw_message": message}

    def fake_execute(command: dict) -> dict:
        return {
            "status": "success",
            "message": "QA completed for E001_letter.pdf: PASS.",
            "intent": "run_single",
            "data": {"final_status": "PASS", "file_name": "E001_letter.pdf"},
        }

    monkeypatch.setattr("app.api.routes.parse_chat_instruction", fake_parse)
    monkeypatch.setattr("app.api.routes.execute_chat_command", fake_execute)

    response = client.post("/api/chat", json={"message": "Run quality check for E001_letter.pdf"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "success"
    assert body["intent"] == "run_single"


def test_chat_endpoint_unknown(monkeypatch) -> None:
    def fake_parse(message: str) -> dict:
        return {"intent": "unknown", "file_name": "", "employee_name": "", "raw_message": message}

    def fake_execute(command: dict) -> dict:
        return {
            "status": "error",
            "message": "Unsupported command.",
            "intent": "unknown",
            "data": {},
        }

    monkeypatch.setattr("app.api.routes.parse_chat_instruction", fake_parse)
    monkeypatch.setattr("app.api.routes.execute_chat_command", fake_execute)

    response = client.post("/api/chat", json={"message": "Hello"})
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "error"
    assert body["intent"] == "unknown"


def test_chat_ask_endpoint(monkeypatch) -> None:
    def fake_run_chat_request(message: str) -> dict:
        return {
            "answer": "I found 1 matching promotion letter and it passed validation.",
            "results": [{"employee_name": "John Smith", "status": "passed"}],
            "status": "completed",
        }

    monkeypatch.setattr("app.api.routes.run_chat_request", fake_run_chat_request)

    response = client.post("/api/chat/ask", json={"message": "List promotion letters"})
    assert response.status_code == 200
    assert response.json() == {
        "answer": "I found 1 matching promotion letter and it passed validation.",
        "results": [{"employee_name": "John Smith", "status": "passed"}],
        "status": "completed",
    }
