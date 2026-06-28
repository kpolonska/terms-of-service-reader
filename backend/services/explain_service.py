import sys
import os
from pathlib import Path
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env", override=True)

if not os.environ.get("DATABASE_PATH") or os.environ["DATABASE_PATH"] == "analyses.db":
    os.environ["DATABASE_PATH"] = str(_project_root / "ai_pipeline" / "analyses.db")

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
