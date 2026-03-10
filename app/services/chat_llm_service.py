"""Provider-aware LLM service for chat intent parsing and summary generation."""

from __future__ import annotations

import json
import logging
import re
from typing import Any

from openai import AzureOpenAI, OpenAI

from app.core.config import Settings, get_settings

logger = logging.getLogger(__name__)


class ChatLLMService:
    def __init__(self, settings: Settings | None = None) -> None:
        self.settings = settings or get_settings()

    def _is_real_llm_available(self) -> bool:
        provider = self.settings.letterguard_llm_provider.lower()
        try:
            if provider == "openai":
                self.settings.validate_openai()
                return True
            if provider == "azure":
                self.settings.validate_azure_openai()
                return True
        except ValueError:
            return False
        return False

    def _get_model_name(self) -> str:
        provider = self.settings.letterguard_llm_provider.lower()
        if provider == "azure":
            return self.settings.azure_openai_model or self.settings.azure_openai_deployment
        return self.settings.openai_model

    def _build_openai_client(self) -> OpenAI:
        self.settings.validate_openai()
        kwargs: dict[str, Any] = {"api_key": self.settings.openai_api_key, "timeout": 20.0}
        if self.settings.openai_base_url:
            kwargs["base_url"] = self.settings.openai_base_url
        return OpenAI(**kwargs)

    def _build_azure_client(self) -> AzureOpenAI:
        self.settings.validate_azure_openai()
        endpoint = self.settings.azure_openai_base_url or self.settings.azure_openai_endpoint
        return AzureOpenAI(
            api_key=self.settings.azure_openai_api_key,
            azure_endpoint=endpoint,
            api_version=self.settings.azure_openai_api_version,
            timeout=20.0,
        )

    @staticmethod
    def _coerce_json(raw_text: str) -> dict[str, Any]:
        cleaned = raw_text.strip()
        cleaned = re.sub(r"^```(?:json)?", "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"```$", "", cleaned).strip()
        parsed = json.loads(cleaned)
        if not isinstance(parsed, dict):
            raise ValueError("LLM response must be a JSON object.")
        return parsed

    def _complete_json(self, *, system_prompt: str, user_prompt: str) -> dict[str, Any]:
        provider = self.settings.letterguard_llm_provider.lower()
        model = self._get_model_name()
        if provider == "azure":
            client = self._build_azure_client()
            completion = client.chat.completions.create(
                model=model,
                temperature=0.1,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
            )
            content = completion.choices[0].message.content if completion.choices else ""
            if not content:
                raise ValueError("LLM returned an empty response.")
            return self._coerce_json(content)

        client = self._build_openai_client()
        response = client.responses.create(
            model=model,
            input=[
                {"role": "system", "content": [{"type": "text", "text": system_prompt}]},
                {"role": "user", "content": [{"type": "text", "text": user_prompt}]},
            ],
            temperature=0.1,
        )
        return self._coerce_json(response.output_text)

    @staticmethod
    def _fallback_parse_intent(message: str) -> dict[str, Any]:
        lowered = message.lower()

        if any(marker in lowered for marker in ["promotion", "promoted"]):
            document_type = "promotion"
        elif any(marker in lowered for marker in ["salary", "base pay", "pay increase"]):
            document_type = "base_pay_increase"
        elif any(marker in lowered for marker in ["bonus", "incentive"]):
            document_type = "annual_incentive_award"
        else:
            document_type = "all"

        list_markers = ["list", "show", "give me", "which", "who received", "who got", "all employees", "all users"]
        validate_markers = [
            "validate",
            "validation",
            "check whether",
            "check",
            "match",
            "compare",
            "verify",
            "prototype",
            "logo",
        ]

        wants_list = any(marker in lowered for marker in list_markers)
        wants_validate = any(marker in lowered for marker in validate_markers)

        if wants_list and wants_validate:
            request_type = "list_and_validate"
        elif wants_validate:
            request_type = "validate_only"
        else:
            request_type = "list_only"

        return {
            "request_type": request_type,
            "document_type": document_type,
            "target_scope": "all_generated_letters",
            "wants_logo_validation": "logo" in lowered or wants_validate,
            "wants_prototype_validation": any(marker in lowered for marker in ["prototype", "match", "compare"]) or wants_validate,
            "notes": ["Intent parsed with deterministic fallback."],
        }

    @classmethod
    def _merge_with_fallback_intent(cls, message: str, parsed: dict[str, Any]) -> dict[str, Any]:
        fallback = cls._fallback_parse_intent(message)
        merged = {**fallback, **parsed}

        request_type = str(merged.get("request_type", "")).strip()
        if request_type not in {"list_only", "validate_only", "list_and_validate"}:
            merged["request_type"] = fallback["request_type"]

        document_type = str(merged.get("document_type", "")).strip().lower()
        if document_type not in {"promotion", "base_pay_increase", "annual_incentive_award", "all"}:
            merged["document_type"] = fallback["document_type"]

        notes = []
        if isinstance(fallback.get("notes"), list):
            notes.extend(str(item) for item in fallback["notes"])
        if isinstance(parsed.get("notes"), list):
            notes.extend(str(item) for item in parsed["notes"])
        merged["notes"] = notes
        return merged

    def parse_intent(self, message: str) -> dict[str, Any]:
        prompt = f"""
Return strict JSON only.

Interpret the user request for a local document QA system.
Schema:
{{
  "request_type": "list_only|validate_only|list_and_validate",
  "document_type": "promotion|base_pay_increase|annual_incentive_award|all",
  "target_scope": "all_generated_letters",
  "wants_logo_validation": true,
  "wants_prototype_validation": true,
  "notes": ["short note"]
}}

User request:
{message}
""".strip()

        if self.settings.is_mock_llm_enabled():
            return self._fallback_parse_intent(message)

        if not self._is_real_llm_available():
            return self._fallback_parse_intent(message)

        try:
            parsed = self._complete_json(
                system_prompt="You convert document QA chat requests into compact routing JSON.",
                user_prompt=prompt,
            )
            parsed.setdefault("notes", [])
            return self._merge_with_fallback_intent(message, parsed)
        except Exception as exc:
            logger.warning("Falling back to deterministic intent parsing: %s", exc)
            return self._fallback_parse_intent(message)

    @staticmethod
    def _fallback_issue_explanation(result: dict[str, Any]) -> str:
        issues = [str(issue) for issue in result.get("issues", []) if issue]
        if not issues:
            return ""
        if result.get("status") == "passed":
            return "The document matched the expected checks."
        return f"Main issue: {issues[0]}."

    def explain_validation_result(self, result: dict[str, Any]) -> str:
        prompt = f"""
Return strict JSON only.

Summarize this document QA result in one business-friendly sentence.
Schema:
{{
  "explanation": "..."
}}

Validation result:
{json.dumps(result, ensure_ascii=False)}
""".strip()

        if self.settings.is_mock_llm_enabled() or not self._is_real_llm_available():
            return self._fallback_issue_explanation(result)

        try:
            parsed = self._complete_json(
                system_prompt="You explain document QA mismatches clearly and concisely.",
                user_prompt=prompt,
            )
            explanation = parsed.get("explanation")
            return str(explanation) if explanation else self._fallback_issue_explanation(result)
        except Exception as exc:
            logger.warning("Falling back to deterministic mismatch explanation: %s", exc)
            return self._fallback_issue_explanation(result)

    @staticmethod
    def _fallback_summary(summary_input: dict[str, Any]) -> str:
        total = int(summary_input.get("total", 0))
        passed = int(summary_input.get("passed", 0))
        failed = int(summary_input.get("failed", 0))
        needs_review = int(summary_input.get("needs_review", 0))
        document_type = str(summary_input.get("document_type_label", "documents"))
        request_type = str(summary_input.get("request_type", "list_only"))
        preview_names = [str(item) for item in summary_input.get("preview_names", []) if item]
        status_preview = [str(item) for item in summary_input.get("status_preview", []) if item]

        if total == 0:
            return f"I could not find any matching {document_type} in the local sample data."
        if request_type == "list_only":
            if preview_names:
                names = ", ".join(preview_names[:3])
                suffix = " and others" if total > 3 else ""
                return f"I found {total} matching {document_type} in the local sample data, including {names}{suffix}."
            return f"I found {total} matching {document_type} in the local sample data."
        if status_preview:
            preview = "; ".join(status_preview[:2])
            return (
                f"I found {total} matching {document_type}. "
                f"{passed} passed, {failed} failed, and {needs_review} need review. "
                f"For example: {preview}."
            )
        return (
            f"I found {total} matching {document_type}. "
            f"{passed} passed, {failed} failed, and {needs_review} need review."
        )

    def summarize_chat_result(self, summary_input: dict[str, Any]) -> str:
        prompt = f"""
Return strict JSON only.

Summarize this document QA workflow result for a chat response.
Schema:
{{
  "answer": "..."
}}

Workflow summary:
{json.dumps(summary_input, ensure_ascii=False)}
""".strip()

        if self.settings.is_mock_llm_enabled() or not self._is_real_llm_available():
            return self._fallback_summary(summary_input)

        try:
            parsed = self._complete_json(
                system_prompt="You summarize document QA workflow outcomes in concise business language.",
                user_prompt=prompt,
            )
            answer = parsed.get("answer")
            return str(answer) if answer else self._fallback_summary(summary_input)
        except Exception as exc:
            logger.warning("Falling back to deterministic summary: %s", exc)
            return self._fallback_summary(summary_input)
