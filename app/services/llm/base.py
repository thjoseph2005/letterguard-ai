"""Base abstractions for pluggable LLM services."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMServiceBase(ABC):
    @abstractmethod
    async def extract_claims(
        self,
        document_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError

    @abstractmethod
    async def analyze_document(
        self,
        instruction: str,
        document_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        raise NotImplementedError
