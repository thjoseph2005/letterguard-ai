import json
from pathlib import Path

from app.agents.data_validation_agent import validate_generated_letter_against_employee


def _write_csv(path: Path) -> None:
    path.write_text(
        "employee_id,name,department,title,base_pay,annual_incentive\n"
        "E001,John Smith,Wealth Management,Advisor,120000,20000\n",
        encoding="utf-8",
    )


def _write_extraction_json(path: Path, full_text: str) -> None:
    payload = {"metadata": {"file_name": "dummy.pdf"}, "extraction": {"full_text": full_text, "page_count": 1}}
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_validation_exact_match_pass(tmp_path: Path) -> None:
    csv_path = tmp_path / "employees.csv"
    extraction_path = tmp_path / "E001_letter.pdf.json"
    _write_csv(csv_path)
    _write_extraction_json(
        extraction_path,
        (
            "Employee ID: E001\n"
            "Name: John Smith\n"
            "Department: Wealth Management\n"
            "Title: Advisor\n"
            "Base Pay: $120000\n"
            "Annual Incentive: $20000\n"
        ),
    )

    result = validate_generated_letter_against_employee(
        file_name="E001_letter.pdf",
        extraction_json_path=str(extraction_path),
        employee_csv_path=str(csv_path),
    )

    assert result["status"] == "pass"
    assert result["employee_id"] == "E001"
    assert result["issues"] == []


def test_validation_mismatch_fail(tmp_path: Path) -> None:
    csv_path = tmp_path / "employees.csv"
    extraction_path = tmp_path / "E001_letter.pdf.json"
    _write_csv(csv_path)
    _write_extraction_json(
        extraction_path,
        (
            "Employee ID: E001\n"
            "Name: John Smith\n"
            "Department: Wealth Management\n"
            "Title: Analyst\n"
            "Base Pay: $100000\n"
            "Annual Incentive: $5000\n"
        ),
    )

    result = validate_generated_letter_against_employee(
        file_name="E001_letter.pdf",
        extraction_json_path=str(extraction_path),
        employee_csv_path=str(csv_path),
    )

    assert result["status"] == "fail"
    assert len(result["issues"]) >= 1
    assert result["field_results"]["title"]["found"] is False


def test_validation_no_match_needs_review(tmp_path: Path) -> None:
    csv_path = tmp_path / "employees.csv"
    extraction_path = tmp_path / "unknown_letter.pdf.json"
    _write_csv(csv_path)
    _write_extraction_json(
        extraction_path,
        (
            "Employee Letter\n"
            "Name: Unknown Person\n"
            "Department: Unknown\n"
        ),
    )

    result = validate_generated_letter_against_employee(
        file_name="unknown_letter.pdf",
        extraction_json_path=str(extraction_path),
        employee_csv_path=str(csv_path),
    )

    assert result["status"] == "needs_review"
    assert result["field_results"] == {}
