"""QA orchestration service for running and persisting LangGraph results."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.services.file_service import create_directory_if_not_exists
from app.workflows.qa_workflow import run_qa_workflow


QA_RESULTS_DIR = Path("sample_data/qa_results")
GENERATED_EXTRACTION_DIR = Path("sample_data/extracted/generated_letters")


def _persist_json(path: Path, payload: dict[str, Any]) -> str:
    create_directory_if_not_exists(str(path.parent))
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return str(path)


def run_letterguard_workflow_for_file(file_name: str) -> dict[str, Any]:
    state = run_qa_workflow(file_name)
    decision = state.get("decision_result", {})

    final_payload = {
        "final_status": decision.get("final_status", "NEEDS_REVIEW"),
        "file_name": file_name,
        "reasons": decision.get("reasons", []),
        "component_status": decision.get(
            "component_status",
            {
                "planner": "needs_review",
                "claim_extraction": "skipped",
                "data_validation": "needs_review",
                "template_comparison": "needs_review",
                "logo_validation": "needs_review",
                "evidence_review": "skipped",
            },
        ),
        "claim_extraction_result": state.get("claim_extraction_result"),
        "data_validation_result": state.get("data_validation_result"),
        "template_result": state.get("template_result"),
        "logo_result": state.get("logo_result"),
        "evidence_review_result": state.get("evidence_review_result"),
        "review": state.get("review_result"),
        "summary": decision.get("summary", "Workflow completed."),
    }

    result_path = QA_RESULTS_DIR / f"{Path(file_name).name}.result.json"
    saved_path = _persist_json(result_path, final_payload)
    final_payload["result_json_path"] = saved_path
    return final_payload


def run_letterguard_workflow_for_all_generated_letters() -> dict[str, Any]:
    create_directory_if_not_exists(str(QA_RESULTS_DIR))

    results: list[dict[str, Any]] = []
    for extraction_json in sorted(GENERATED_EXTRACTION_DIR.glob("*.json")):
        file_name = extraction_json.name.removesuffix(".json")
        results.append(run_letterguard_workflow_for_file(file_name))

    summary = {
        "total": len(results),
        "PASS": sum(1 for item in results if item.get("final_status") == "PASS"),
        "FAIL": sum(1 for item in results if item.get("final_status") == "FAIL"),
        "NEEDS_REVIEW": sum(1 for item in results if item.get("final_status") == "NEEDS_REVIEW"),
        "results": results,
    }

    _persist_json(QA_RESULTS_DIR / "batch_summary.json", summary)
    return summary
