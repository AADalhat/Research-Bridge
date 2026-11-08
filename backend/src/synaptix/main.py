from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from synaptix.api.router import api_router
from synaptix.core.config import Settings


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings if settings is not None else Settings()

    # Prevent public demo credentials from working in staging/production.
    if settings.enable_demo_auth and settings.app_environment not in {
        "development",
        "test",
    }:
        raise RuntimeError(
            "Demo authentication is forbidden outside development/test."
        )

    application = FastAPI(
        title="Research Bridge API",
        version="0.1.0",
        description=(
            "Research submission, review and repository preparation."
        ),
    )

    # Allow requests from the explicitly configured frontend.
    if settings.frontend_origin:
        application.add_middleware(
            CORSMiddleware,
            allow_origins=[settings.frontend_origin],
            allow_credentials=False,
            allow_methods=[
                "GET",
                "POST",
                "PATCH",
                "PUT",
                "DELETE",
                "OPTIONS",
            ],
            allow_headers=[
                "Authorization",
                "Content-Type",
            ],
        )

    application.state.auth_service = None

    if settings.enable_demo_auth:
        from synaptix.development.fake_auth import (
            DevelopmentAuthService,
        )
        from synaptix.development.upload_service import (
            DevelopmentUploadService,
        )

        application.state.auth_service = DevelopmentAuthService()
        application.state.upload_service = DevelopmentUploadService()
        application.include_router(api_router)

    return application


app = create_app()