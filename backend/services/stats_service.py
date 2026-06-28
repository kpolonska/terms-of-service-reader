import json
import os
import sqlite3
from pathlib import Path
from dotenv import load_dotenv

_project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(_project_root / ".env")

from services.scoring_service import compute_score

_DB_PATH = os.environ.get("DATABASE_PATH", str(_project_root / "ai_pipeline" / "analyses.db"))


def get_stats() -> dict:
    if not os.path.exists(_DB_PATH):
        return _empty_stats()

    with sqlite3.connect(_DB_PATH) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT domain, result_json, analyzed_at FROM analyses ORDER BY analyzed_at DESC"
        ).fetchall()

    if not rows:
        return _empty_stats()

    category_dist: dict[str, int] = {}
    concept_dist: dict[str, int] = {}
    severity_dist = {"high": 0, "medium": 0, "low": 0}
    domain_scores: list[dict] = []
    all_scores: list[int] = []

    for row in rows:
        result = json.loads(row["result_json"])
        clauses = result.get("clauses", [])
        risk = compute_score(clauses)
        all_scores.append(risk["score"])

        if row["domain"]:
            domain_scores.append({
                "domain": row["domain"],
                "score": risk["score"],
                "label": risk["label"],
                "analyzed_at": row["analyzed_at"],
            })

        for clause in clauses:
            cat = clause.get("category", "unknown")
            concept = clause.get("concept", "unknown")
            sev = clause.get("severity", "low")
            category_dist[cat] = category_dist.get(cat, 0) + 1
            concept_dist[concept] = concept_dist.get(concept, 0) + 1
            if sev in severity_dist:
                severity_dist[sev] += 1

    # Deduplicate domains — keep highest score per domain
    seen: dict[str, dict] = {}
    for d in domain_scores:
        if d["domain"] not in seen or d["score"] > seen[d["domain"]]["score"]:
            seen[d["domain"]] = d

    top_domains = sorted(seen.values(), key=lambda x: x["score"], reverse=True)[:10]
    avg_score = round(sum(all_scores) / len(all_scores), 1) if all_scores else 0

    return {
        "total_analyzed": len(rows),
        "average_score": avg_score,
        "most_dangerous_domains": top_domains,
        "category_distribution": dict(sorted(category_dist.items(), key=lambda x: x[1], reverse=True)),
        "concept_distribution": dict(sorted(concept_dist.items(), key=lambda x: x[1], reverse=True)),
        "severity_distribution": severity_dist,
    }


def _empty_stats() -> dict:
    return {
        "total_analyzed": 0,
        "average_score": 0,
        "most_dangerous_domains": [],
        "category_distribution": {},
        "concept_distribution": {},
        "severity_distribution": {"high": 0, "medium": 0, "low": 0},
    }
