SEVERITY_WEIGHTS = {"high": 10, "medium": 4, "low": 1}

CATEGORY_MULTIPLIERS = {
    "behavioral_analysis": 1.5,
    "data_sharing_third_parties": 1.5,
    "data_collection": 1.2,
    "algorithmic_decision": 1.2,
    "rights_modification": 1.1,
    "content_ownership": 1.0,
    "account_termination": 1.0,
    "legal_jurisdiction": 0.8,
}

# (max_weighted_total, numeric_score, label)
_BREAKPOINTS = [
    (8,  1,  "SAFE"),
    (16, 2,  "SAFE"),
    (24, 3,  "SAFE"),
    (33, 4,  "CAUTION"),
    (43, 5,  "CAUTION"),
    (54, 6,  "RISKY"),
    (66, 7,  "RISKY"),
    (80, 8,  "DANGEROUS"),
    (96, 9,  "DANGEROUS"),
]


def compute_score(clauses: list[dict]) -> dict:
    """Return {'score': 1..10, 'label': 'SAFE'|'CAUTION'|'RISKY'|'DANGEROUS'}."""
    if not clauses:
        return {"score": 1, "label": "SAFE"}

    total = 0.0
    for clause in clauses:
        weight = SEVERITY_WEIGHTS.get(clause.get("severity", "low"), 1)
        multiplier = CATEGORY_MULTIPLIERS.get(clause.get("category", ""), 1.0)
        total += weight * multiplier

    for threshold, numeric, label in _BREAKPOINTS:
        if total <= threshold:
            return {"score": numeric, "label": label}

    return {"score": 10, "label": "DANGEROUS"}
