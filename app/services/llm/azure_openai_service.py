"""Azure OpenAI-backed document QA service."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncAzureOpenAI

from app.core.config import Settings, get_settings
from app.services.llm.base import LLMServiceBase
from app.services.llm.prompt_builder import build_document_qa_prompt
from app.services.llm.response_parser import parse_qa_result_json

logger = logging.getLogger(__name__)


class AzureOpenAIService(LLMServiceBase):
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _build_client(self) -> AsyncAzureOpenAI:
        self.settings.validate_azure_openai()
        return AsyncAzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            azure_endpoint=self.settings.azure_openai_endpoint,
            api_version=self.settings.azure_openai_api_version,
        )

    async def analyze_document(
        self,
        instruction: str,
        document_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = build_document_qa_prompt(instruction=instruction, document_text=document_text, metadata=metadata)

        try:
            client = self._build_client()
            completion = await client.chat.completions.create(
                model=self.settings.azure_openai_deployment,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": "You perform deterministic document QA and return strict JSON."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )

            content = completion.choices[0].message.content if completion.choices else ""
            if not content:
                raise ValueError("LLM returned an empty response.")

            return parse_qa_result_json(content)

        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Azure OpenAI analyze_document failed")
            raise RuntimeError(f"Azure OpenAI call failed: {exc}") from exc
