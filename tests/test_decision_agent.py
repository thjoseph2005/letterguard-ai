from app.agents.decision_agent import make_final_decision


def test_decision_agent_all_pass() -> None:
    result = make_final_decision(
        file_name="E001_letter.pdf",
        planner_result={"status": "pass", "summary": "Planner ok."},
        data_validation_result={"status": "pass", "summary": "Data validation ok."},
        template_result={"status": "pass", "summary": "Template ok."},
        logo_result={"status": "pass", "summary": "Logo ok."},
    )
    assert result["final_status"] == "PASS"


def test_decision_agent_one_failure() -> None:
    result = make_final_decision(
        file_name="E001_letter.pdf",
        planner_result={"status": "pass", "summary": "Planner ok."},
        data_validation_result={"status": "fail", "summary": "Data mismatch."},
        template_result={"status": "pass", "summary": "Template ok."},
        logo_result={"status": "pass", "summary": "Logo ok."},
    )
    assert result["final_status"] == "FAIL"


def test_decision_agent_needs_review() -> None:
    result = make_final_decision(
        file_name="E001_letter.pdf",
        planner_result={"status": "needs_review", "summary": "Missing optional input."},
        data_validation_result={"status": "pass", "summary": "Data validation ok."},
        template_result={"status": "pass", "summary": "Template ok."},
        logo_result={"status": "pass", "summary": "Logo ok."},
    )
    assert result["final_status"] == "NEEDS_REVIEW"
