from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Request

from synaptix.core.permissions import require_reviewer
from synaptix.schemas.auth import UserRead
from synaptix.schemas.upload import SubmissionUploadRead


router = APIRouter(
    prefix="/reviews",
    tags=["Reviews"],
)


@router.get(
    "/queue",
    response_model=list[SubmissionUploadRead],
)
def read_review_queue(
    request: Request,
    user: Annotated[UserRead, Depends(require_reviewer)],
    faculty: str | None = None,
    department: str | None = None,
) -> list[SubmissionUploadRead]:
    """Return the current development upload queue."""

    service = getattr(
        request.app.state,
        "upload_service",
        None,
    )

    if service is None:
        raise HTTPException(
            status_code=503,
            detail="The upload service is not configured.",
        )

    return service.list_for_reviewer(
        reviewer_id=user.user_id,
        faculty=faculty,
        department=department,
    )