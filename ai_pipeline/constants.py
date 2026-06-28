from pydantic import BaseModel, field_validator
from typing import Literal

CATEGORIES = [
    "data_collection",
    "data_sharing_third_parties",
    "behavioral_analysis",
    "algorithmic_decision",
    "rights_modification",
    "content_ownership",
    "account_termination",
    "legal_jurisdiction",
]

CONCEPTS = [
    "Surveillance Capitalism (Zuboff)",
    "Datafication (Van Dijck)",
    "Platformization (Srnicek)",
    "Algorithmic Opacity (Pasquale)",
    "General Power Asymmetry",
]

SEVERITY_LEVELS = ["low", "medium", "high"]


class Clause(BaseModel):
    quote: str
    plain_english: str
    category: str
    severity: Literal["low", "medium", "high"]
    concept: str

    @field_validator("category")
    @classmethod
    def validate_category(cls, v: str) -> str:
        if v not in CATEGORIES:
            raise ValueError(f"Invalid category: {v}. Must be one of {CATEGORIES}")
        return v

    @field_validator("concept")
    @classmethod
    def validate_concept(cls, v: str) -> str:
        if v not in CONCEPTS:
            raise ValueError(f"Invalid concept: {v}. Must be one of {CONCEPTS}")
        return v


class AnalysisResult(BaseModel):
    tldr: str
    clauses: list[Clause]
