from fastapi import APIRouter

from synaptix.api.v1.auth import router as auth_router
from synaptix.api.v1.health import router as health_router
from synaptix.api.v1.submissions import (
    router as submissions_router,
)


router = APIRouter()

router.include_router(health_router)
router.include_router(auth_router)
router.include_router(submissions_router)