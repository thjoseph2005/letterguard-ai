"""Azure OpenAI service stub."""

from app.services.azure_config import AzureSettings


class AzureOpenAIService:
    def __init__(self, settings: AzureSettings | None = None) -> None:
        self.settings = settings or AzureSettings()

    def generate(self, prompt: str) -> str:
        """Stubbed completion method for future LLM integration."""
        _ = prompt
        # TODO: Implement Azure OpenAI SDK call.
        return "[stub] Azure OpenAI response"
