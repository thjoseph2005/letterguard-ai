"""Service wrapper for LangGraph-backed chat orchestration."""

from __future__ import annotations

from typing import Any

from app.workflows.chat_workflow import run_chat_workflow


def run_chat_request(message: str) -> dict[str, Any]:
    state = run_chat_workflow(message)
    return {
        "answer": str(state.get("answer", "")),
        "results": state.get("results", []),
        "status": str(state.get("status", "completed")),
    }
