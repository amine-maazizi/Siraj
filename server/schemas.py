from typing import List
from pydantic import BaseModel, Field

class IngestResponse(BaseModel):
    doc_id: str
    title: str
    pages: int
    chunks: int

class SummarizeRequest(BaseModel):
    doc_id: str = Field(..., description="Document ID returned by /ingest")

class SummarySection(BaseModel):
    title: str
    bullets: List[str]

class SummarizeResponse(BaseModel):
    summary_sections: List[SummarySection]
