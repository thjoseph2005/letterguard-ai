"""Factory functions for constructing Azure service adapters."""

from app.services.azure_blob_service import AzureBlobService
from app.services.azure_openai_service import AzureOpenAIService


def get_openai_service() -> AzureOpenAIService:
    return AzureOpenAIService()


def get_blob_service() -> AzureBlobService:
    return AzureBlobService()
