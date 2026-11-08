from typing import Annotated

from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from synaptix.schemas.auth import UserRead
from synaptix.services.auth_service import AuthService


bearer_scheme = HTTPBearer(auto_error=False)


def unauthorized() -> HTTPException:
    return HTTPException(
        status_code=401,
        detail="Invalid or expired authentication credentials.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def get_auth_service(request: Request) -> AuthService:
    service = getattr(
        request.app.state,
        "auth_service",
        None,
    )

    if service is None:
        raise HTTPException(
            status_code=503,
            detail="Authentication is not configured.",
        )

    return service


def get_access_token(
    credentials: Annotated[
        HTTPAuthorizationCredentials | None,
        Depends(bearer_scheme),
    ],
) -> str:
    if credentials is None:
        raise unauthorized()

    return credentials.credentials


def get_current_user(
    token: Annotated[str, Depends(get_access_token)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> UserRead:
    user = auth.get_user(token)

    if user is None:
        raise unauthorized()

    return user