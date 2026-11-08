from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class VerificationChecks(BaseModel):
    """Results of basic technical file checks."""

    size_within_limit: bool
    pdf_header_detected: bool
    sha256: str


class SubmissionUploadRead(BaseModel):
    """Public response for the temporary upload workflow."""

    submission_id: str
    author_name: str
    faculty: str
    department: str
    language: str

    original_filename: str
    size_bytes: int
    created_at: datetime

    status: Literal["UPLOADED"] = "UPLOADED"

    verification_status: Literal[
        "pending",
        "running",
        "completed",
        "failed",
    ] = "pending"

    message: str
    checks: VerificationChecks | None = None