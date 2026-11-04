from fastapi import FastAPI

from synaptix.api.router import api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Research Bridge API",
        version="0.1.0",
        description="Research submission, review and repository preparation.",
    )

    application.include_router(api_router)

    return application


app = create_app()