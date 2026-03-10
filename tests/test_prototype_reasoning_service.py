from app.services.prototype_reasoning_service import reason_about_prototype_match


class StubLLMService:
    def compare_prototype_documents(self, **kwargs):
        return kwargs["fallback_result"]


def test_reason_about_prototype_match_fallback() -> None:
    result = reason_about_prototype_match(
        document_record={
            "document_text": "Congratulations on your promotion. Effective Date: March 10, 2026.",
            "prototype_text": "Congratulations on your promotion.",
        },
        validation_result={
            "template_result": {
                "missing_sections": ["effective date section"],
                "unexpected_sections": [],
            }
        },
        llm_service=StubLLMService(),
    )

    assert result["status"] == "needs_review"
    assert result["issues"]
