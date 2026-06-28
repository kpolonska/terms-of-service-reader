import sys
import os
from pathlib import Path

_project_root = Path(__file__).resolve().parent.parent.parent
if str(_project_root / "ai_pipeline") not in sys.path:
    sys.path.insert(0, str(_project_root / "ai_pipeline"))
if not os.environ.get("DATABASE_PATH") or os.environ["DATABASE_PATH"] == "analyses.db":
    os.environ["DATABASE_PATH"] = str(_project_root / "ai_pipeline" / "analyses.db")

from cache import get_two_latest_for_domain

SEVERITY_RANK = {"low": 1, "medium": 2, "high": 3}


def _max_severity_by_category(clauses: list[dict]) -> dict[str, str]:
    result: dict[str, str] = {}
    for clause in clauses:
        cat = clause.get("category", "")
        sev = clause.get("severity", "low")
        if cat and (cat not in result or SEVERITY_RANK.get(sev, 0) > SEVERITY_RANK.get(result[cat], 0)):
            result[cat] = sev
    return result


def compute_diff(domain: str) -> dict | None:
    versions = get_two_latest_for_domain(domain)
    if len(versions) < 2:
        return None

    current_result = versions[0]["result"]
    previous_result = versions[1]["result"]
    previous_at = versions[1]["analyzed_at"]

    current_cats = _max_severity_by_category(current_result.get("clauses", []))
    previous_cats = _max_severity_by_category(previous_result.get("clauses", []))

    changed: list[dict] = []
    all_cats = set(current_cats) | set(previous_cats)

    for cat in sorted(all_cats):
        if cat in current_cats and cat in previous_cats:
            cur_rank = SEVERITY_RANK.get(current_cats[cat], 0)
            prev_rank = SEVERITY_RANK.get(previous_cats[cat], 0)
            if cur_rank != prev_rank:
                changed.append({
                    "category": cat,
                    "direction": "worse" if cur_rank > prev_rank else "better",
                    "previous_severity": previous_cats[cat],
                    "current_severity": current_cats[cat],
                })
        elif cat in current_cats:
            changed.append({
                "category": cat,
                "direction": "new",
                "previous_severity": None,
                "current_severity": current_cats[cat],
            })
        else:
            changed.append({
                "category": cat,
                "direction": "removed",
                "previous_severity": previous_cats[cat],
                "current_severity": None,
            })

    return {
        "previous_analyzed_at": previous_at,
        "changed_clauses": changed,
        "has_changes": len(changed) > 0,
    }
