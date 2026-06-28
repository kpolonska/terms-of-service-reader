from fastapi import APIRouter, HTTPException
from models.schemas import ExplainRequest, ExplainResponse
from services.explain_service import explain
from services.ai_service import RateLimitError

router = APIRouter()


@router.post("/explain", response_model=ExplainResponse)
async def explain_clause(request: ExplainRequest):
    try:
        result = explain(request.quote, request.category, request.profile)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RateLimitError as e:
        raise HTTPException(status_code=429, detail=str(e))
    except TimeoutError:
        raise HTTPException(status_code=503, detail="AI service timed out.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Explain failed: {str(e)}")

    return ExplainResponse(**result)
