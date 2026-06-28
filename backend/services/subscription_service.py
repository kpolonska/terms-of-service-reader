import sys
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root / "ai_pipeline") not in sys.path:
    sys.path.insert(0, str(_project_root / "ai_pipeline"))
if not os.environ.get("DATABASE_PATH") or os.environ["DATABASE_PATH"] == "analyses.db":
    os.environ["DATABASE_PATH"] = str(_project_root / "ai_pipeline" / "analyses.db")

from cache import subscribe, unsubscribe, get_subscriptions, is_subscribed

__all__ = ["subscribe", "unsubscribe", "get_subscriptions", "is_subscribed"]
