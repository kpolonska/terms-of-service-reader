import sys
import os
from pathlib import Path
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env", override=True)

if not os.environ.get("DATABASE_PATH") or os.environ["DATABASE_PATH"] == "analyses.db":
    os.environ["DATABASE_PATH"] = str(_project_root / "ai_pipeline" / "analyses.db")

sys.path.insert(0, str(_project_root / "ai_pipeline"))

for _mod in ("tos_models", "prompt", "pipeline", "cache", "parser"):
    sys.modules.pop(_mod, None)

from pipeline import analyze_tos
import openai


class RateLimitError(Exception):
    pass


def analyze(text: str, domain: str | None = None, profile: str = "general") -> dict:
    try:
        return analyze_tos(text, domain, profile)
    except openai.RateLimitError as e:
        raise RateLimitError("Too many requests. Please wait and try again.") from e
    except (openai.APIConnectionError, openai.APITimeoutError) as e:
        print(f"[ai_service] connection/timeout error: {type(e).__name__}: {e}", flush=True)
        raise TimeoutError(f"AI service unreachable: {type(e).__name__}: {e}") from e
    except openai.APIStatusError as e:
        print(f"[ai_service] API status error {e.status_code}: {e.message}", flush=True)
        raise TimeoutError(f"AI service returned error {e.status_code}: {e.message}") from e
    except Exception as e:
        print(f"[ai_service] unexpected error: {type(e).__name__}: {e}", flush=True)
        raise
