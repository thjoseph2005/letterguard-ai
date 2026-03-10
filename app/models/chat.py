"""Models for chat command requests/responses."""

from typing import Any

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: str


class ChatAskResponse(BaseModel):
    answer: str
    results: list[dict[str, Any]] = Field(default_factory=list)
    status: str = "completed"


class ChatResponse(BaseModel):
    status: str
    message: str
    intent: str
    data: dict
