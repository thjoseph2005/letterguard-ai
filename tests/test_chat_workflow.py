from app.workflows import chat_workflow


def test_run_chat_workflow_list_only(monkeypatch) -> None:
    def fake_parse_intent(message: str) -> dict:
        return {
            "request_type": "list_only",
            "document_type": "promotion",
            "target_scope": "all_generated_letters",
            "wants_logo_validation": False,
            "wants_prototype_validation": False,
            "notes": ["parsed"],
        }

    def fake_load_reference_data() -> dict:
        return {
            "employees": [{"employee_id": "E001", "name": "John Smith", "department": "Wealth Management"}],
            "prototype_mapping": {"promotion": "promotion_prototype.pdf.json"},
            "logo_mapping": {"wealth management": "wealth.png"},
            "prototype_extractions": {},
        }

    def fake_locate_generated_documents(document_type: str, employees: list[dict], prototype_mapping: dict, logo_mapping: dict) -> list[dict]:
        assert document_type == "promotion"
        return [
            {
                "employee_name": "John Smith",
                "employee_id": "E001",
                "department": "Wealth Management",
                "document_type": "promotion",
                "generated_document": "E001_letter.pdf",
                "prototype_file": "promotion_prototype.pdf",
                "expected_logo": "wealth.png",
            }
        ]

    monkeypatch.setattr(chat_workflow.llm_service, "parse_intent", fake_parse_intent)
    monkeypatch.setattr(chat_workflow.llm_service, "summarize_chat_result", lambda summary: "I found 1 matching promotion letter.")
    monkeypatch.setattr(chat_workflow, "load_reference_data", fake_load_reference_data)
    monkeypatch.setattr(chat_workflow, "locate_generated_documents", fake_locate_generated_documents)

    state = chat_workflow.run_chat_workflow("Give me the list of all users who received promotion letter")

    assert state["status"] == "completed"
    assert state["answer"] == "I found 1 matching promotion letter."
    assert state["results"][0]["employee_name"] == "John Smith"
    assert state["results"][0]["status"] == "listed"


def test_run_chat_workflow_validate(monkeypatch) -> None:
    def fake_parse_intent(message: str) -> dict:
        return {
            "request_type": "list_and_validate",
            "document_type": "promotion",
            "target_scope": "all_generated_letters",
            "wants_logo_validation": True,
            "wants_prototype_validation": True,
            "notes": [],
        }

    monkeypatch.setattr(chat_workflow.llm_service, "parse_intent", fake_parse_intent)
    monkeypatch.setattr(
        chat_workflow.llm_service,
        "summarize_chat_result",
        lambda summary: "I found 1 matching promotion letter. 1 passed, 0 failed, and 0 need review.",
    )
    monkeypatch.setattr(
        chat_workflow,
        "load_reference_data",
        lambda: {
            "employees": [],
            "prototype_mapping": {"promotion": "promotion_prototype.pdf.json"},
            "logo_mapping": {"wealth management": "wealth.png"},
            "prototype_extractions": {},
        },
    )
    monkeypatch.setattr(
        chat_workflow,
        "locate_generated_documents",
        lambda **kwargs: [
            {
                "employee_name": "John Smith",
                "employee_id": "E001",
                "department": "Wealth Management",
                "document_type": "promotion",
                "generated_document": "E001_letter.pdf",
                "prototype_file": "promotion_prototype.pdf",
                "expected_logo": "wealth.png",
            }
        ],
    )
    monkeypatch.setattr(
        chat_workflow,
        "validate_document_record",
        lambda **kwargs: {
            "employee_name": "John Smith",
            "department": "Wealth Management",
            "document_type": "promotion",
            "generated_document": "E001_letter.pdf",
            "prototype_used": "promotion_prototype.pdf",
            "logo_used": "wealth.png",
            "status": "passed",
            "issues": [],
        },
    )

    state = chat_workflow.run_chat_workflow(
        "List all employees with promotion letters and check whether their generated letters match the prototype"
    )

    assert state["status"] == "completed"
    assert state["results"][0]["status"] == "passed"
    assert "1 passed" in state["answer"]
