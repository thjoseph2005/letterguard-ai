from app.agents.claim_extraction_agent import extract_claims_from_letter


def test_extract_claims_from_letter_deterministic() -> None:
    result = extract_claims_from_letter(
        (
            "Employee ID: E001\n"
            "Name: John Smith\n"
            "Department: Wealth Management\n"
            "Title: Advisor\n"
            "Base Pay: $120,000\n"
            "Annual Incentive: $20,000\n"
            "Congratulations on your promotion to a new role.\n"
        )
    )

    field_names = {claim["field_name"] for claim in result["claims"]}
    assert result["status"] == "success"
    assert "employee_id" in field_names
    assert "department" in field_names
    assert "letter_type" in field_names


def test_extract_claims_from_letter_skipped_for_empty_text() -> None:
    result = extract_claims_from_letter("")
    assert result["status"] == "skipped"
