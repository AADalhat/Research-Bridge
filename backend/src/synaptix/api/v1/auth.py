from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response

from synaptix.dependencies import (
    get_access_token,
    get_auth_service,
    get_current_user,
)
from synaptix.schemas.auth import (
    LoginRequest,
    LoginResponse,
    UserRead,
)
from synaptix.services.auth_service import AuthService


router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/login", response_model=LoginResponse)
def login(
    payload: LoginRequest,
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> LoginResponse:
    result = auth.login(
        registration_number=payload.registration_number,
        password=payload.password.get_secret_value(),
    )

    if result is None:
        raise HTTPException(
            status_code=401,
            detail="Incorrect registration number or password.",
        )

    return result


@router.get("/me", response_model=UserRead)
def read_current_user(
    user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    return user


@router.post("/logout", status_code=204)
def logout(
    token: Annotated[str, Depends(get_access_token)],
    auth: Annotated[AuthService, Depends(get_auth_service)],
) -> Response:
    auth.logout(token)
    return Response(status_code=204)