from typing import Protocol

from synaptix.schemas.auth import LoginResponse, UserRead


class AuthService(Protocol):
    def login(
        self,
        registration_number: str,
        password: str,
    ) -> LoginResponse | None:
        ...

    def get_user(self, token: str) -> UserRead | None:
        ...

    def logout(self, token: str) -> None:
        ...