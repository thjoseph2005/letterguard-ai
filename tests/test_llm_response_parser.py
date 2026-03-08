import pytest

from app.services.llm.response_parser import parse_qa_result_json


def test_parse_qa_result_json_success() -> None:
    raw = '{"overall_status":"pass","summary":"ok","issues":[],"recommendations":[],"confidence":0.9}'
    parsed = parse_qa_result_json(raw)
    assert parsed["overall_status"] == "pass"


def test_parse_qa_result_json_invalid() -> None:
    with pytest.raises(ValueError):
        parse_qa_result_json('not-json')
