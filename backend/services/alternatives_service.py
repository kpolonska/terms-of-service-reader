import sys
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_project_root / "ai_pipeline"))

from pipeline import generate_alternatives

SHOW_THRESHOLD = 7  # only suggest alternatives when risk score >= 7 (RISKY or DANGEROUS)


def get_alternatives(domain: str | None, risk_score: int, tldr: str, categories: list[str]) -> list[dict]:
    if not domain or risk_score < SHOW_THRESHOLD:
        return []
    return generate_alternatives(domain, tldr, categories)
