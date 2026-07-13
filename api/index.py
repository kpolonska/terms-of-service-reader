"""Vercel Functions entry point.

Vercel auto-detects this file, installs api/requirements.txt, and mounts the
exported FastAPI `app` as an ASGI handler for all HTTP requests routed here
via vercel.json.

Locally, developers keep using `uvicorn main:app --reload` from backend/ or
`docker-compose up`; this file is only exercised on Vercel.
"""

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "backend"))
sys.path.insert(0, str(_ROOT / "ai_pipeline"))

from main import app  # noqa: E402  (backend/main.py — the existing FastAPI app)
