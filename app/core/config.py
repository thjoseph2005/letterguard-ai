"""Application configuration."""

from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class Settings:
    azure_openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    azure_openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    azure_openai_api_version: str = os.getenv("AZURE_OPENAI_API_VERSION", "")
    azure_openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")

    def validate_azure_openai(self) -> None:
        missing = []
        if not self.azure_openai_endpoint:
            missing.append("AZURE_OPENAI_ENDPOINT")
        if not self.azure_openai_api_key:
            missing.append("AZURE_OPENAI_API_KEY")
        if not self.azure_openai_api_version:
            missing.append("AZURE_OPENAI_API_VERSION")
        if not self.azure_openai_deployment:
            missing.append("AZURE_OPENAI_DEPLOYMENT")
        if missing:
            raise ValueError(f"Missing Azure OpenAI configuration: {', '.join(missing)}")


def get_settings() -> Settings:
    return Settings()
