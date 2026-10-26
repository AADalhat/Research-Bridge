from fastapi import FastAPI

from synaptix.api.router import api_router


def create_app() -> FastAPI:
    application = FastAPI(
        title="Synaptix API",
        version="0.1.0",
        description=(
            "AI-assisted research submission, tracking "
            "and metadata processing."
        ),
    )

    application.include_router(api_router)

    return application


app = create_app()