from fastapi import APIRouter

from app.retrieval.indexer import build_index


router = APIRouter(prefix="/retrieval", tags=["retrieval"])


@router.post("/reindex")
async def reindex_repository_context():
    result = build_index(".")
    return {
        "status": "completed",
        **result,
    }
