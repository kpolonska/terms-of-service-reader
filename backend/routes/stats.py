from fastapi import APIRouter, HTTPException
from services.stats_service import get_stats

router = APIRouter()


@router.get("/stats")
async def stats():
    try:
        return get_stats()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats query failed: {str(e)}")
