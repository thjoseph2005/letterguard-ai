"""Response models for PDF extraction endpoints."""

from pydantic import BaseModel


class ExtractionSummaryResponse(BaseModel):
    status: str
    file_name: str
    page_count: int
    json_output_path: str
