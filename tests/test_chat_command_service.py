from pathlib import Path

from app.services import chat_command_service as service


def test_parse_single_file_command() -> None:
    command = service.parse_chat_instruction("Run quality check for E001_letter.pdf")
    assert command["intent"] == "run_single"
    assert command["file_name"] == "E001_letter.pdf"


def test_parse_run_all_command() -> None:
    command = service.parse_chat_instruction("Run QA for all generated letters")
    assert command["intent"] == "run_all"


def test_parse_explain_result_command() -> None:
    command = service.parse_chat_instruction("Why did E003_letter.pdf fail?")
    assert command["intent"] == "explain_result"
    assert command["file_name"] == "E003_letter.pdf"


def test_parse_unknown_command() -> None:
    command = service.parse_chat_instruction("Tell me a joke")
    assert command["intent"] == "unknown"


def test_employee_name_lookup(monkeypatch, tmp_path: Path) -> None:
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "employee_id,name,department,title,base_pay,annual_incentive\n"
        "E010,Karen Jackson,Wealth Management,Client Associate,80000,8000\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(service, "EMPLOYEE_CSV_PATH", csv_path)
    file_name = service.resolve_employee_name_to_file("Karen Jackson")
    assert file_name == "E010_letter.pdf"
