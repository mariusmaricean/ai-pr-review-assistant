from fastapi import APIRouter, Depends

from app.core.auth import verify_admin_token
from app.retrieval.indexer import build_index


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/reindex", dependencies=[Depends(verify_admin_token)])
async def reindex_repository_context():
    result = build_index(".")
    return {
        "status": "completed",
        **result,
    }
