from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from secrets import compare_digest, token_urlsafe
from threading import Lock

from synaptix.schemas.auth import LoginResponse, UserRead


@dataclass(frozen=True)
class DemoAccount:
    user: UserRead
    password: str


@dataclass(frozen=True)
class DemoSession:
    account_id: str
    expires_at: datetime


class DevelopmentAuthService:
    SESSION_SECONDS = 3600

    def __init__(self) -> None:
        self._sessions: dict[str, DemoSession] = {}
        self._lock = Lock()

        student = UserRead(
            user_id="demo-student-001",
            full_name="Amina Yusuf",
            registration_number="DEMO/PG/001",
            role="student",
        )

        reviewer = UserRead(
            user_id="demo-reviewer-001",
            full_name="Dr. Ibrahim Musa",
            registration_number="DEMO/STAFF/001",
            role="reviewer",
        )

        self._accounts: dict[str, DemoAccount] = {
            student.registration_number: DemoAccount(
                user=student,
                password="ResearchBridgeDemo",
            ),
            reviewer.registration_number: DemoAccount(
                user=reviewer,
                password="ResearchBridgeReviewer",
            ),
        }

    def login(
        self,
        registration_number: str,
        password: str,
    ) -> LoginResponse | None:
        account_id = registration_number.strip().upper()
        account = self._accounts.get(account_id)

        if account is None:
            return None

        if not compare_digest(
            password.encode("utf-8"),
            account.password.encode("utf-8"),
        ):
            return None

        token = token_urlsafe(32)
        now = datetime.now(timezone.utc)

        with self._lock:
            self._sessions = {
                key: session
                for key, session in self._sessions.items()
                if session.expires_at > now
            }

            self._sessions[token] = DemoSession(
                account_id=account_id,
                expires_at=now + timedelta(
                    seconds=self.SESSION_SECONDS
                ),
            )

        return LoginResponse(
            access_token=token,
            expires_in=self.SESSION_SECONDS,
            user=account.user.model_copy(),
        )

    def get_user(self, token: str) -> UserRead | None:
        now = datetime.now(timezone.utc)

        with self._lock:
            session = self._sessions.get(token)

            if session is None:
                return None

            if session.expires_at <= now:
                self._sessions.pop(token, None)
                return None

            account = self._accounts.get(session.account_id)

            if account is None:
                return None

            return account.user.model_copy()

    def logout(self, token: str) -> None:
        with self._lock:
            self._sessions.pop(token, None)