import pytest

from app.services.llm.response_parser import parse_claim_extraction_json, parse_qa_result_json


def test_parse_qa_result_json_success() -> None:
    raw = '{"overall_status":"pass","summary":"ok","issues":[],"recommendations":[],"confidence":0.9}'
    parsed = parse_qa_result_json(raw)
    assert parsed["overall_status"] == "pass"


def test_parse_qa_result_json_invalid() -> None:
    with pytest.raises(ValueError):
        parse_qa_result_json('not-json')


def test_parse_claim_extraction_json_success() -> None:
    raw = (
        '{"status":"success","summary":"ok","claims":[{"field_name":"employee_id","value":"E001",'
        '"confidence":0.9,"evidence":[{"source":"document","quote":"Employee ID: E001","location":"line 1"}]}],'
        '"unresolved_questions":[],"confidence":0.8}'
    )
    parsed = parse_claim_extraction_json(raw)
    assert parsed["status"] == "success"
    assert parsed["claims"][0]["field_name"] == "employee_id"


def test_parse_claim_extraction_json_invalid() -> None:
    with pytest.raises(ValueError):
        parse_claim_extraction_json('{"status":"success"}')
