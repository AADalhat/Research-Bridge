from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone

class CandidateMetadata(BaseModel):
    """
    Validated 3-field metadata extracted from research PDF.
    Must contain strictly title, subject_keywords, and abstract.
    """
    title: str = Field(..., description="Non-empty research document title")
    subject_keywords: List[str] = Field(..., description="List of non-empty subject keywords")
    abstract: str = Field(..., description="Non-empty research abstract text")

    @field_validator("title", "abstract")
    @classmethod
    def validate_non_empty_string(cls, v: str) -> str:
        s = v.strip()
        if not s:
            raise ValueError("Field cannot be empty or purely whitespace")
        return s

    @field_validator("subject_keywords")
    @classmethod
    def validate_keywords(cls, v: List[str]) -> List[str]:
        if not v:
            raise ValueError("subject_keywords must contain at least one keyword")
        cleaned = [k.strip() for k in v if k and k.strip()]
        if not cleaned:
            raise ValueError("subject_keywords must contain valid non-empty strings")
        return cleaned

class EvidenceItem(BaseModel):
    """Single evidence span referencing a specific 1-based page number and exact source excerpt."""
    page_number: int = Field(..., ge=1, description="1-based page number")
    source_text: str = Field(..., min_length=1, description="Exact text excerpt found in PDF")

class EvidenceFields(BaseModel):
    title: List[EvidenceItem] = Field(default_factory=list)
    subject_keywords: List[EvidenceItem] = Field(default_factory=list)
    abstract: List[EvidenceItem] = Field(default_factory=list)

class EvidenceData(BaseModel):
    """
    Supporting evidence data adhering strictly to Schema Version 1.
    """
    schema_version: int = Field(1, description="Always 1 for Version 1.2 database schema")
    fields: EvidenceFields

class PageExtraction(BaseModel):
    """Represents text extracted from a single PDF page."""
    page_number: int
    text: str
    confidence: Optional[float] = None  # None for digital; float 0.0 - 1.0 for OCR

class DocumentText(BaseModel):
    """Aggregate extracted text across pages (capped at first 15 pages)."""
    file_path: str
    doc_type: str  # "digital" or "scanned"
    total_pages_in_doc: int
    pages_processed: int
    pages: List[PageExtraction]

    @property
    def full_text(self) -> str:
        chunks = []
        for p in self.pages:
            chunks.append(f"--- PAGE {p.page_number} ---\n{p.text}")
        return "\n\n".join(chunks)

class ExtractionJobResult(BaseModel):
    """
    Complete outcome of an extraction task, compatible with both local JSON logging
    and future PostgreSQL schema mapping (processing_jobs, metadata_extractions, submissions_metadata).
    """
    job_id: str
    file_path: str
    classification: str
    pages_processed: int
    total_pages_in_doc: int
    status: str  # "completed", "failed", "EXTRACTION_STALLED"
    candidate_metadata_raw: Optional[str] = None
    candidate_metadata: Optional[Dict[str, Any]] = None
    evidence_data: Optional[Dict[str, Any]] = None
    output_file: Optional[str] = None
    error_message: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    completed_at: Optional[str] = None

