from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.ai_service import analyze

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_tos(request: AnalyzeRequest):
    try:
        result = analyze(request.text, request.domain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=503, detail="AI service timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    return AnalyzeResponse(
        tldr=result["tldr"],
        clauses=result["clauses"],
        cached=result["cached"],
        analyzed_at=datetime.now(timezone.utc).isoformat(),
    )
