"""Base agent abstraction for LetterGuard agents."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAgent(ABC):
    name: str = "base-agent"

    @abstractmethod
    def run(self, state: dict[str, Any]) -> dict[str, Any]:
        """Execute agent logic and return updated state."""
        raise NotImplementedError
