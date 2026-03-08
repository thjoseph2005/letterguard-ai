from pathlib import Path

from app.services.employee_data_service import (
    find_employee_fields_in_text,
    load_employee_csv,
    parse_currency_from_text,
)


def test_load_employee_csv(tmp_path: Path) -> None:
    csv_path = tmp_path / "employees.csv"
    csv_path.write_text(
        "employee_id,name,department,title,base_pay,annual_incentive\n"
        "E001,John Smith,Wealth Management,Advisor,120000,20000\n",
        encoding="utf-8",
    )

    employees = load_employee_csv(str(csv_path))
    assert len(employees) == 1
    assert employees[0]["employee_id"] == "E001"
    assert employees[0]["name"] == "John Smith"


def test_find_employee_fields_in_text_exact_match() -> None:
    employee = {
        "employee_id": "E001",
        "name": "John Smith",
        "department": "Wealth Management",
        "title": "Advisor",
        "base_pay": "120000",
        "annual_incentive": "20000",
    }
    text = (
        "Employee Letter\n"
        "Employee ID: E001\n"
        "Name: John Smith\n"
        "Department: Wealth Management\n"
        "Title: Advisor\n"
        "Base Pay: $120,000\n"
        "Annual Incentive: $20,000\n"
    )
    field_results = find_employee_fields_in_text(text, employee)
    assert all(result["found"] for result in field_results.values())
    assert 120000.0 in parse_currency_from_text(text)
