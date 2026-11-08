from typing import Annotated

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
)

from synaptix.core.permissions import require_student
from synaptix.development.upload_service import (
    DevelopmentUploadService,
    UploadRejected,
)
from synaptix.schemas.auth import UserRead
from synaptix.schemas.upload import SubmissionUploadRead


router = APIRouter(
    prefix="/submissions",
    tags=["Submissions"],
)


def get_upload_service(request: Request) -> DevelopmentUploadService:
    """Resolve the local development upload implementation."""

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

    return service


@router.post(
    "",
    response_model=SubmissionUploadRead,
    status_code=202,
)
def upload_submission(
    background_tasks: BackgroundTasks,
    user: Annotated[UserRead, Depends(require_student)],
    service: Annotated[
        DevelopmentUploadService,
        Depends(get_upload_service),
    ],
    file: Annotated[UploadFile, File()],
    author_name: Annotated[
        str,
        Form(min_length=1, max_length=255),
    ],
    faculty: Annotated[
        str,
        Form(min_length=1, max_length=150),
    ],
    department: Annotated[
        str,
        Form(min_length=1, max_length=150),
    ],
    language: Annotated[
        str,
        Form(min_length=1, max_length=50),
    ],
) -> SubmissionUploadRead:
    """Receive the PDF and schedule basic verification."""

    try:
        result = service.create(
            owner_id=user.user_id,
            source=file.file,
            original_filename=file.filename or "",
            author_name=author_name,
            faculty=faculty,
            department=department,
            language=language,
        )
    except UploadRejected as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc
    finally:
        file.file.close()

    background_tasks.add_task(
        service.verify,
        result.submission_id,
    )

    return result


@router.get(
    "/{submission_id}",
    response_model=SubmissionUploadRead,
)
def read_submission(
    submission_id: str,
    user: Annotated[UserRead, Depends(require_student)],
    service: Annotated[
        DevelopmentUploadService,
        Depends(get_upload_service),
    ],
) -> SubmissionUploadRead:
    """Read verification status for the student's own submission."""

    result = service.get_for_owner(
        submission_id=submission_id,
        owner_id=user.user_id,
    )

    if result is None:
        raise HTTPException(
            status_code=404,
            detail="Submission not found.",
        )

    return result