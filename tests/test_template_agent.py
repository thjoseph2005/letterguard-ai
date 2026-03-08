import json
from pathlib import Path

from app.agents.template_agent import review_generated_letter_against_prototype


def _write_extraction_json(path: Path, full_text: str) -> None:
    payload = {"metadata": {"file_name": path.name}, "extraction": {"full_text": full_text, "page_count": 1}}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_template_agent_successful_comparison(tmp_path: Path) -> None:
    generated_json = tmp_path / "generated" / "E001_letter.pdf.json"
    prototype_dir = tmp_path / "prototypes"
    prototype_json = prototype_dir / "promotion_prototype.pdf.json"

    _write_extraction_json(generated_json, "Congratulations on your promotion in your new role.")
    _write_extraction_json(prototype_json, "Promotion Letter Template. Congratulations on your promotion.")

    result = review_generated_letter_against_prototype(
        file_name="E001_letter.pdf",
        generated_extraction_json_path=str(generated_json),
        prototype_extraction_dir=str(prototype_dir),
    )

    assert result["status"] == "pass"
    assert result["detected_letter_type"] == "promotion"
    assert result["prototype_file"] == "promotion_prototype.pdf.json"


def test_template_agent_missing_section_fail(tmp_path: Path) -> None:
    generated_json = tmp_path / "generated" / "E002_letter.pdf.json"
    prototype_dir = tmp_path / "prototypes"
    prototype_json = prototype_dir / "salary_increase_prototype.pdf.json"

    _write_extraction_json(generated_json, "General update letter.")
    _write_extraction_json(prototype_json, "Salary Increase Letter Template. Your base pay has been increased.")

    result = review_generated_letter_against_prototype(
        file_name="E002_letter.pdf",
        generated_extraction_json_path=str(generated_json),
        prototype_extraction_dir=str(prototype_dir),
    )

    # Generated text still classifies as unknown and should be flagged for review.
    assert result["status"] in {"fail", "needs_review"}
