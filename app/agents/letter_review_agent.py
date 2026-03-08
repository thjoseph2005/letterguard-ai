"""Placeholder letter review agent."""

from typing import Any

from app.agents.base_agent import BaseAgent


class LetterReviewAgent(BaseAgent):
    name = "letter-review-agent"

    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        text = state.get("letter_text", "")
        # TODO: Replace with policy + LLM-backed validation checks.
        state["issues"] = [] if text else ["Letter text is empty"]
        state["summary"] = "Validation scaffold executed"
        return state
