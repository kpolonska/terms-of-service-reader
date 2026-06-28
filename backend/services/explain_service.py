import sys
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root / "ai_pipeline"))

from pipeline import explain_clause
import openai

from services.ai_service import RateLimitError


def explain(quote: str, category: str, profile: str = "general") -> dict:
    try:
        return explain_clause(quote, category, profile)
    except openai.RateLimitError as e:
        raise RateLimitError("Too many requests. Please wait and try again.") from e
    except (openai.APIConnectionError, openai.APITimeoutError) as e:
        raise TimeoutError("AI service is unreachable.") from e
