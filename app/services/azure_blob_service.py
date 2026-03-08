"""Azure Blob Storage service stub."""

from app.services.azure_config import AzureSettings


class AzureBlobService:
    def __init__(self, settings: AzureSettings | None = None) -> None:
        self.settings = settings or AzureSettings()

    def upload_letter(self, blob_name: str, content: bytes) -> str:
        """Stub for uploading raw letter artifacts to Azure Blob Storage."""
        _ = content
        # TODO: Implement BlobServiceClient upload logic.
        return f"[stub] uploaded://{self.settings.blob_container_name}/{blob_name}"
