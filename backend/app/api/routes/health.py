import time
from fastapi import APIRouter
from pydantic import BaseModel
from app.core.config import settings

router = APIRouter(tags=["Health"])

START_TIME = time.time()


class HealthResponse(BaseModel):
    status: str
    app: str
    environment: str
    uptime_seconds: float


@router.get("/health", response_model=HealthResponse)
async def get_health():
    return HealthResponse(
        status="ok",
        app=settings.APP_NAME,
        environment=settings.APP_ENV,
        uptime_seconds=round(time.time() - START_TIME, 2),
    )
