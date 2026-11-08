from typing import Literal

from pydantic import BaseModel, Field, SecretStr


class LoginRequest(BaseModel):
    registration_number: str = Field(
        min_length=1,
        max_length=50,
    )
    password: SecretStr


class UserRead(BaseModel):
    user_id: str
    full_name: str
    registration_number: str
    role: Literal["student", "reviewer", "administrator"]


class LoginResponse(BaseModel):
    access_token: str
    token_type: Literal["bearer"] = "bearer"
    expires_in: int
    user: UserRead