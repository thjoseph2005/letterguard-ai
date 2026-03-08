"""Models for chat command requests/responses."""

from pydantic import BaseModel


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    status: str
    message: str
    intent: str
    data: dict
