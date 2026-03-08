from app.services.prototype_comparison_service import (
    classify_letter_type_from_text,
    compare_generated_text_to_prototype,
    get_prototype_file_for_letter_type,
)


def test_classification_smoke() -> None:
    result = classify_letter_type_from_text("Congratulations on your promotion to a new role.")
    assert result["letter_type"] == "promotion"
    assert result["confidence"] > 0
    assert "promotion" in result["matched_keywords"]


def test_unknown_classification() -> None:
    result = classify_letter_type_from_text("This memo contains generic updates and logistics.")
    assert result["letter_type"] == "unknown"


def test_prototype_mapping() -> None:
    assert get_prototype_file_for_letter_type("promotion") == "promotion_prototype.pdf.json"
    assert get_prototype_file_for_letter_type("unknown") is None


def test_successful_comparison() -> None:
    prototype_text = "Promotion Letter Template. Congratulations on your promotion."
    generated_text = "Congratulations on your promotion in your new role."
    result = compare_generated_text_to_prototype(generated_text, prototype_text, "promotion")
    assert result["status"] == "pass"
    assert result["missing_sections"] == []


def test_missing_section_detection() -> None:
    prototype_text = "Salary Increase Letter Template. Your base pay has been increased."
    generated_text = "Employee Letter with no compensation details."
    result = compare_generated_text_to_prototype(generated_text, prototype_text, "base_pay_increase")
    assert result["status"] == "fail"
    assert len(result["missing_sections"]) >= 1
