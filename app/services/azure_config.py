"""Configuration helpers for Azure-backed services."""

import os


class AzureSettings:
    openai_endpoint: str = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    openai_api_key: str = os.getenv("AZURE_OPENAI_API_KEY", "")
    openai_deployment: str = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")
    blob_connection_string: str = os.getenv("AZURE_STORAGE_CONNECTION_STRING", "")
    blob_container_name: str = os.getenv("AZURE_STORAGE_CONTAINER", "letters")
