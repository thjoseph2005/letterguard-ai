import json
from pathlib import Path

from app.workflows.qa_workflow import run_qa_workflow


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_qa_workflow_smoke(tmp_path: Path) -> None:
    generated_json = tmp_path / "generated" / "E001_letter.pdf.json"
    prototype_dir = tmp_path / "prototypes"
    csv_path = tmp_path / "employees.csv"
    logo_dir = tmp_path / "logos"

    csv_path.write_text(
        "employee_id,name,department,title,base_pay,annual_incentive\n"
        "E001,John Smith,Wealth Management,Advisor,120000,20000\n",
        encoding="utf-8",
    )

    _write_json(
        generated_json,
        {
            "extraction": {
                "full_text": (
                    "Employee ID: E001\n"
                    "Name: John Smith\n"
                    "Department: Wealth Management\n"
                    "Title: Advisor\n"
                    "Base Pay: $120000\n"
                    "Annual Incentive: $20000\n"
                    "Congratulations on your promotion to a new role."
                )
            }
        },
    )

    _write_json(
        prototype_dir / "promotion_prototype.pdf.json",
        {"extraction": {"full_text": "Promotion Letter Template. Congratulations on your promotion."}},
    )

    logo_dir.mkdir(parents=True, exist_ok=True)
    (logo_dir / "wealth.png").write_bytes(b"fakepng")

    state = run_qa_workflow(
        file_name="E001_letter.pdf",
        overrides={
            "generated_extraction_json_path": str(generated_json),
            "employee_csv_path": str(csv_path),
            "prototype_extraction_dir": str(prototype_dir),
            "logo_dir": str(logo_dir),
        },
    )

    assert state.get("planner_result", {}).get("status") == "pass"
    assert state.get("document_text")
    assert state.get("claim_extraction_result", {}).get("status") in {"success", "needs_review", "skipped"}
    assert state.get("decision_result", {}).get("final_status") in {"PASS", "FAIL", "NEEDS_REVIEW"}
    assert "decision_result" in state
