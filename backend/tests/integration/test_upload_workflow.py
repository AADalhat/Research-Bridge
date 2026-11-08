import hashlib
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from synaptix.core.config import Settings
from synaptix.dependencies import get_current_user
from synaptix.main import create_app
from synaptix.schemas.auth import UserRead


# This is deliberately NOT a complete, structurally valid PDF.
# It tests only the preliminary header check currently implemented.
PDF_LIKE_BYTES = b"%PDF-1.7\nResearch Bridge test fixture\n"


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Create an isolated application for each test."""

    settings = Settings(
        _env_file=None,
        app_environment="test",
        enable_demo_auth=True,
    )

    app = create_app(settings)

    with TestClient(app) as test_client:
        yield test_client


def login_headers(
    client: TestClient,
    *,
    reviewer: bool = False,
) -> dict[str, str]:
    """Log in and return an Authorization header."""

    if reviewer:
        credentials = {
            "registration_number": "DEMO/STAFF/001",
            "password": "ResearchBridgeReviewer",
        }
    else:
        credentials = {
            "registration_number": "DEMO/PG/001",
            "password": "ResearchBridgeDemo",
        }

    response = client.post(
        "/api/v1/auth/login",
        json=credentials,
    )

    assert response.status_code == 200, response.text

    token = response.json()["access_token"]

    return {"Authorization": f"Bearer {token}"}


def send_upload(
    client: TestClient,
    *,
    headers: dict[str, str] | None = None,
    filename: str = "sample.pdf",
    content: bytes = PDF_LIKE_BYTES,
):
    """Send a multipart upload with the required intake fields."""

    return client.post(
        "/api/v1/submissions",
        headers=headers,
        data={
            "author_name": "Amina Yusuf",
            "faculty": "Engineering",
            "department": "Computer Engineering",
            "language": "English",
        },
        files={
            "file": (
                filename,
                content,
                "application/pdf",
            ),
        },
    )


def test_student_upload_completes_basic_verification(
    client: TestClient,
) -> None:
    """Check intake, ownership-linked lookup and checksum output."""

    headers = login_headers(client)

    upload = send_upload(
        client,
        headers=headers,
    )

    assert upload.status_code == 202, upload.text

    submission_id = upload.json()["submission_id"]

    result = client.get(
        f"/api/v1/submissions/{submission_id}",
        headers=headers,
    )

    assert result.status_code == 200, result.text

    body = result.json()

    assert body["status"] == "UPLOADED"
    assert body["verification_status"] == "completed"
    assert body["author_name"] == "Amina Yusuf"
    assert body["language"] == "English"
    assert body["size_bytes"] == len(PDF_LIKE_BYTES)

    assert body["checks"]["pdf_header_detected"] is True
    assert body["checks"]["size_within_limit"] is True
    assert body["checks"]["sha256"] == hashlib.sha256(
        PDF_LIKE_BYTES
    ).hexdigest()


def test_upload_requires_authentication(
    client: TestClient,
) -> None:
    """An anonymous request must not create an upload."""

    response = send_upload(client)

    assert response.status_code == 401


def test_reviewer_cannot_use_student_upload_endpoint(
    client: TestClient,
) -> None:
    """A valid reviewer session does not grant student actions."""

    headers = login_headers(
        client,
        reviewer=True,
    )

    response = send_upload(
        client,
        headers=headers,
    )

    assert response.status_code == 403


def test_empty_upload_is_rejected(
    client: TestClient,
) -> None:
    """A filename alone is not a usable upload."""

    headers = login_headers(client)

    response = send_upload(
        client,
        headers=headers,
        content=b"",
    )

    assert response.status_code == 400


def test_non_pdf_filename_is_rejected(
    client: TestClient,
) -> None:
    """The current intake contract accepts PDF filenames only."""

    headers = login_headers(client)

    response = send_upload(
        client,
        headers=headers,
        filename="notes.txt",
        content=b"Plain text",
    )

    assert response.status_code == 400


def test_renamed_text_file_fails_verification(
    client: TestClient,
) -> None:
    """A .pdf extension must not bypass the PDF-header check."""

    headers = login_headers(client)

    upload = send_upload(
        client,
        headers=headers,
        filename="pretend.pdf",
        content=b"This is not a PDF.",
    )

    assert upload.status_code == 202, upload.text

    submission_id = upload.json()["submission_id"]

    result = client.get(
        f"/api/v1/submissions/{submission_id}",
        headers=headers,
    )

    assert result.status_code == 200

    body = result.json()

    assert body["verification_status"] == "failed"
    assert body["checks"]["pdf_header_detected"] is False


def test_upload_over_configured_limit_is_rejected(
    client: TestClient,
) -> None:
    """Exercise the size boundary without sending a huge test file."""

    headers = login_headers(client)

    # Lower the limit only on this test's isolated service.
    client.app.state.upload_service.MAX_FILE_BYTES = 16

    response = send_upload(
        client,
        headers=headers,
        content=b"%PDF-" + b"x" * 20,
    )

    assert response.status_code == 400


def test_other_student_cannot_read_submission(
    client: TestClient,
) -> None:
    """Check ownership without adding another public demo account."""

    headers = login_headers(client)

    upload = send_upload(
        client,
        headers=headers,
    )

    assert upload.status_code == 202

    submission_id = upload.json()["submission_id"]

    different_student = UserRead(
        user_id="another-test-student",
        full_name="Another Student",
        registration_number="TEST/PG/002",
        role="student",
    )

    # Override identity for this request to exercise ownership checks.
    # This override is test-only and is never enabled by an API caller.
    client.app.dependency_overrides[get_current_user] = (
        lambda: different_student
    )

    try:
        response = client.get(
            f"/api/v1/submissions/{submission_id}",
            headers=headers,
        )
    finally:
        client.app.dependency_overrides.clear()

    assert response.status_code == 404