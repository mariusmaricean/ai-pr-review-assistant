from fastapi import APIRouter, Depends

from app.core.auth import verify_admin_token
from app.metrics.service import get_review_metrics


router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/reviews", dependencies=[Depends(verify_admin_token)])
async def review_metrics():
    return get_review_metrics()
