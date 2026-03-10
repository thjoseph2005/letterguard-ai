"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    letterguard_llm_provider: str = os.getenv("LETTERGUARD_LLM_PROVIDER", "openai")
    letterguard_use_mock_llm: bool = os.getenv("LETTERGUARD_USE_MOCK_LLM", "false").lower() == "true"
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    openai_base_url: str = os.getenv("OPENAI_BASE_URL", "")
    openai_model: str = os.getenv("OPENAI_MODEL", "")
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    azure_openai_base_url: str = os.getenv("AZURE_OPENAI_BASE_URL", "")
    azure_openai_model: str = os.getenv("AZURE_OPENAI_MODEL", "")

    def validate_openai(self) -> None:
        missing = []
        if not self.openai_api_key:
            missing.append("OPENAI_API_KEY")
        if not self.openai_model:
            missing.append("OPENAI_MODEL")
        if missing:
            raise ValueError(f"Missing OpenAI configuration: {', '.join(missing)}")

    def validate_azure_openai(self) -> None:
        missing = []
        endpoint = self.azure_openai_base_url or self.azure_openai_endpoint
        model = self.azure_openai_model or self.azure_openai_deployment
        if not endpoint:
            missing.append("AZURE_OPENAI_BASE_URL or AZURE_OPENAI_ENDPOINT")
        if not self.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not self.azure_openai_api_version:
            missing.append("AZURE_OPENAI_API_VERSION")
        if not model:
            missing.append("AZURE_OPENAI_MODEL or AZURE_OPENAI_DEPLOYMENT")
        if missing:
            raise ValueError(f"Missing Azure OpenAI configuration: {', '.join(missing)}")

    def is_mock_llm_enabled(self) -> bool:
        return self.letterguard_use_mock_llm


def get_settings() -> Settings:
    return Settings()
