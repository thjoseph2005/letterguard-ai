"""LangGraph workflow skeleton for letter validation."""

from typing import cast

from langgraph.graph import END, START, StateGraph

from app.agents.letter_review_agent import LetterReviewAgent
from app.models.letter import LetterValidationRequest, LetterValidationResponse
from app.workflows.state import LetterReviewState


agent = LetterReviewAgent()


def review_node(state: LetterReviewState) -> LetterReviewState:
    updated = agent.run(dict(state))
    updated["status"] = "ok" if not updated.get("issues") else "flagged"
    return cast(LetterReviewState, updated)


def build_graph():
    graph = StateGraph(LetterReviewState)
    graph.add_node("review", review_node)
    graph.add_edge(START, "review")
    graph.add_edge("review", END)
    return graph.compile()


compiled_graph = build_graph()


def run_letter_review(payload: LetterValidationRequest) -> LetterValidationResponse:
    initial_state: LetterReviewState = {
        "letter_text": payload.letter_text,
        "employee_id": payload.employee_id or "",
    }
    result = compiled_graph.invoke(initial_state)
    return LetterValidationResponse(
        status=result.get("status", "unknown"),
        issues=result.get("issues", []),
        summary=result.get("summary", "No summary generated."),
    )
