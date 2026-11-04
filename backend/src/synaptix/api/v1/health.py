from fastapi import APIRouter

router = APIRouter(
    prefix="/health",
    tags=["Health"],
)


@router.get("")
def health_check() -> dict[str, str]:
    """Confirm that the API is running."""
    return {
        "status": "ok",
        "service": "research-bridge-api",
    }