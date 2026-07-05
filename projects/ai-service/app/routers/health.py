from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict[str, object]:
    return {
        "status": "ok",
        "service": "ai-service",
        "time": datetime.now(timezone.utc).isoformat(),
    }
