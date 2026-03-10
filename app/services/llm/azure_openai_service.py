"""Azure OpenAI-backed document QA service."""

from __future__ import annotations

import logging
from typing import Any

from openai import AsyncAzureOpenAI

from app.core.config import Settings, get_settings
from app.services.llm.base import LLMServiceBase
from app.services.llm.prompt_builder import (
    build_claim_extraction_prompt,
    build_document_qa_prompt,
    build_evidence_review_prompt,
)
from app.services.llm.response_parser import parse_claim_extraction_json, parse_qa_result_json

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

    async def _run_json_completion(self, system_prompt: str, user_prompt: str) -> str:
        client = self._build_client()
        completion = await client.chat.completions.create(
            model=self.settings.azure_openai_deployment,
            temperature=0.1,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            response_format={"type": "json_object"},
        )

        content = completion.choices[0].message.content if completion.choices else ""
        if not content:
            raise ValueError("LLM returned an empty response.")
        return content

    async def extract_claims(
        self,
        document_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = build_claim_extraction_prompt(document_text=document_text, metadata=metadata)

        try:
            content = await self._run_json_completion(
                system_prompt="You extract evidence-backed claims from compensation letters and return strict JSON.",
                user_prompt=prompt,
            )
            return parse_claim_extraction_json(content)
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Azure OpenAI extract_claims failed")
            raise RuntimeError(f"Azure OpenAI claim extraction failed: {exc}") from exc

    async def analyze_document(
        self,
        instruction: str,
        document_text: str,
        metadata: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = build_document_qa_prompt(instruction=instruction, document_text=document_text, metadata=metadata)

        try:
            content = await self._run_json_completion(
                system_prompt="You perform deterministic document QA and return strict JSON.",
                user_prompt=prompt,
            )
            return parse_qa_result_json(content)

        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Azure OpenAI analyze_document failed")
            raise RuntimeError(f"Azure OpenAI call failed: {exc}") from exc

    async def review_letter_package(
        self,
        instruction: str,
        document_text: str,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        prompt = build_evidence_review_prompt(
            instruction=instruction,
            document_text=document_text,
            context=context,
        )

        try:
            content = await self._run_json_completion(
                system_prompt="You review compensation letters using supplied evidence and return strict JSON.",
                user_prompt=prompt,
            )
            return parse_qa_result_json(content)
        except ValueError:
            raise
        except Exception as exc:
            logger.exception("Azure OpenAI review_letter_package failed")
            raise RuntimeError(f"Azure OpenAI evidence review failed: {exc}") from exc
