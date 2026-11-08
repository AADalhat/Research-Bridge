from typing import Annotated

from fastapi import Depends, HTTPException

from synaptix.dependencies import get_current_user
from synaptix.schemas.auth import UserRead


def require_student(
    user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """Allow student-only actions."""

    if user.role != "student":
        raise HTTPException(
            status_code=403,
            detail="Student access is required.",
        )

    return user


def require_reviewer(
    user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """Allow reviewer-only actions."""

    if user.role != "reviewer":
        raise HTTPException(
            status_code=403,
            detail="Reviewer access is required.",
        )

    return user