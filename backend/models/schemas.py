from pydantic import BaseModel, field_validator
from typing import Literal

VALID_CATEGORIES = {
    "data_collection",
    "data_sharing_third_parties",
    "behavioral_analysis",
    "algorithmic_decision",
    "rights_modification",
    "content_ownership",
    "account_termination",
    "legal_jurisdiction",
}

VALID_SEVERITY: set[str] = {"low", "medium", "high"}

VALID_CONCEPTS = {
    "Surveillance Capitalism (Zuboff)",
    "Datafication (Van Dijck)",
    "Platformization (Srnicek)",
    "Algorithmic Opacity (Pasquale)",
    "General Power Asymmetry",
}


class AnalyzeRequest(BaseModel):
    text: str
    domain: str | None = None

    @field_validator("text")
    @classmethod
    def text_must_be_nonempty(cls, v: str) -> str:
        v = v.strip()
        if len(v) < 100:
            raise ValueError("Text is too short to be a Terms of Service document.")
        if len(v) > 20000:
            raise ValueError("Text exceeds maximum allowed length of 20,000 characters.")
        return v


class Clause(BaseModel):
    quote: str
    plain_english: str
    category: str
    severity: Literal["low", "medium", "high"]
    concept: str


class Alternative(BaseModel):
    name: str
    url: str
    reason: str


class ExplainRequest(BaseModel):
    quote: str
    category: str
    profile: str = "general"

    @field_validator("profile")
    @classmethod
    def validate_profile(cls, v: str) -> str:
        if v not in {"general", "journalist", "activist", "business"}:
            raise ValueError("Invalid profile.")
        return v


class ExplainResponse(BaseModel):
    detailed_explanation: str
    real_world_example: str
    what_you_can_do: str


class RiskScore(BaseModel):
    score: int   # 1–10, higher = more dangerous
    label: str   # "SAFE" | "CAUTION" | "RISKY" | "DANGEROUS"


class AnalyzeResponse(BaseModel):
    tldr: str
    clauses: list[Clause]
    cached: bool
    analyzed_at: str
    risk: RiskScore
    alternatives: list[Alternative] = []
