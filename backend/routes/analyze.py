from fastapi import APIRouter, HTTPException
from datetime import datetime, timezone

from models.schemas import AnalyzeRequest, AnalyzeResponse
from services.ai_service import analyze, RateLimitError
from services.scoring_service import compute_score
from services.alternatives_service import get_alternatives

router = APIRouter()


@router.post("/analyze", response_model=AnalyzeResponse)
async def analyze_tos(request: AnalyzeRequest):
    try:
        result = analyze(request.text, request.domain)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=503, detail="AI service timed out. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    risk = compute_score(result["clauses"])
    categories = [c.get("category", "") for c in result["clauses"]]
    alternatives = get_alternatives(request.domain, risk["score"], result.get("tldr", ""), categories)

    return AnalyzeResponse(
        tldr=result["tldr"],
        clauses=result["clauses"],
        cached=result.get("cached", False),
        analyzed_at=datetime.now(timezone.utc).isoformat(),
        risk=risk,
        alternatives=alternatives,
    )
