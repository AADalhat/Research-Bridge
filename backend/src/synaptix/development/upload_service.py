import hashlib
import logging
import tempfile

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock
from typing import BinaryIO
from uuid import uuid4

from synaptix.schemas.upload import (
    SubmissionUploadRead,
    VerificationChecks,
)


logger = logging.getLogger(__name__)


class UploadRejected(ValueError):
    """An upload does not meet the basic intake rules."""


@dataclass
class StoredUpload:
    """Internal record; never returned directly to the frontend."""

    owner_id: str
    temporary_path: Path
    result: SubmissionUploadRead


class DevelopmentUploadService:
    """Local-only upload records and basic verification."""

    MAX_FILE_BYTES = 20 * 1024 * 1024
    CHUNK_BYTES = 1024 * 1024

    def __init__(self) -> None:
        self._records: dict[str, StoredUpload] = {}
        self._lock = Lock()

    def create(
        self,
        *,
        owner_id: str,
        source: BinaryIO,
        original_filename: str,
        author_name: str,
        faculty: str,
        department: str,
        language: str,
    ) -> SubmissionUploadRead:
        """Save a completed upload and register pending verification."""

        # Treat the provided filename as a label, never a storage path.
        display_name = original_filename.replace("\\", "/").split("/")[-1]

        if not display_name.lower().endswith(".pdf"):
            raise UploadRejected("Only PDF files are accepted.")

        fields = {
            "author_name": author_name.strip(),
            "faculty": faculty.strip(),
            "department": department.strip(),
            "language": language.strip(),
        }

        if any(not value for value in fields.values()):
            raise UploadRejected(
                "Author name, faculty, department and language are required."
            )

        temporary_path: Path | None = None
        size_bytes = 0

        try:
            with tempfile.NamedTemporaryFile(
                prefix="research-bridge-",
                suffix=".pdf",
                delete=False,
            ) as destination:
                temporary_path = Path(destination.name)

                while chunk := source.read(self.CHUNK_BYTES):
                    size_bytes += len(chunk)

                    if size_bytes > self.MAX_FILE_BYTES:
                        raise UploadRejected(
                            "The PDF exceeds the 20 MiB development limit."
                        )

                    destination.write(chunk)

            if size_bytes == 0:
                raise UploadRejected("The uploaded file is empty.")

            result = SubmissionUploadRead(
                submission_id=str(uuid4()),
                **fields,
                original_filename=display_name,
                size_bytes=size_bytes,
                created_at=datetime.now(timezone.utc),
                message=(
                    "Upload received. Basic file verification is pending."
                ),
            )

            with self._lock:
                self._records[result.submission_id] = StoredUpload(
                    owner_id=owner_id,
                    temporary_path=temporary_path,
                    result=result,
                )

            return result.model_copy(deep=True)

        except Exception:
            if temporary_path is not None:
                temporary_path.unlink(missing_ok=True)
            raise

    def get_for_owner(
        self,
        submission_id: str,
        owner_id: str,
    ) -> SubmissionUploadRead | None:
        """Return a snapshot only when the submission belongs to the user."""

        with self._lock:
            record = self._records.get(submission_id)

            if record is None or record.owner_id != owner_id:
                return None

            return record.result.model_copy(deep=True)

    def verify(self, submission_id: str) -> None:
        """Perform basic checks, preserving a frontend-readable outcome."""

        with self._lock:
            record = self._records.get(submission_id)

            if record is None:
                return

            # Prevent repeated execution from reprocessing this record.
            if record.result.verification_status != "pending":
                return

            record.result.verification_status = "running"
            record.result.message = "Running basic PDF checks."

            path = record.temporary_path

        try:
            digest = hashlib.sha256()

            with path.open("rb") as file:
                header = file.read(5)
                digest.update(header)

                while chunk := file.read(self.CHUNK_BYTES):
                    digest.update(chunk)

            header_detected = header == b"%PDF-"

            checks = VerificationChecks(
                size_within_limit=True,
                pdf_header_detected=header_detected,
                sha256=digest.hexdigest(),
            )

            with self._lock:
                record.result.checks = checks

                if header_detected:
                    record.result.verification_status = "completed"
                    record.result.message = (
                        "Basic file checks completed. "
                        "Metadata extraction and academic review "
                        "have not been performed."
                    )
                else:
                    record.result.verification_status = "failed"
                    record.result.message = (
                        "The file does not start with the expected PDF header. "
                        "Please select a valid PDF."
                    )

        except Exception:
            logger.exception(
                "Basic verification failed for submission %s",
                submission_id,
            )

            with self._lock:
                record.result.verification_status = "failed"
                record.result.message = (
                    "Basic verification could not be completed. "
                    "Please try uploading again."
                )

        finally:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.exception(
                    "Could not remove temporary upload for submission %s",
                    submission_id,
                )
    def list_for_reviewer(
        self,
        *,
        reviewer_id: str,
        faculty: str | None = None,
        department: str | None = None,
    ) -> list[SubmissionUploadRead]:
        """List verified development uploads, excluding self-review."""

        faculty_filter = faculty.strip().casefold() if faculty else None
        department_filter = (
            department.strip().casefold() if department else None
        )

        with self._lock:
            results = []

            for record in self._records.values():
                if record.owner_id == reviewer_id:
                    continue

                result = record.result

                if result.verification_status != "completed":
                    continue

                if (
                    faculty_filter
                    and result.faculty.casefold() != faculty_filter
                ):
                    continue

                if (
                    department_filter
                    and result.department.casefold() != department_filter
                ):
                    continue

                results.append(result.model_copy(deep=True))

        return sorted(
            results,
            key=lambda result: result.created_at,
            reverse=True,
        )