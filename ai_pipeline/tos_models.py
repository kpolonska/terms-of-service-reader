from pydantic import BaseModel, Field, field_validator
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

# English fallbacks used when the AI omits a translated label.
CATEGORY_LABELS_EN = {
    "data_collection": "Data Collection",
    "data_sharing_third_parties": "Data Sharing (Third Parties)",
    "behavioral_analysis": "Behavioral Analysis",
    "algorithmic_decision": "Algorithmic Decision",
    "rights_modification": "Rights Modification",
    "content_ownership": "Content Ownership",
    "account_termination": "Account Termination",
    "legal_jurisdiction": "Legal Jurisdiction",
}

SEVERITY_LABELS_EN = {"low": "Low", "medium": "Medium", "high": "High"}

RISK_LABELS_EN = {"safe": "Safe", "caution": "Caution", "risky": "Risky", "dangerous": "Dangerous"}


class Clause(BaseModel):
    quote: str
    plain_english: str
    category: str
    category_label: str = Field(default="", validate_default=True)
    severity: Literal["low", "medium", "high"]
    severity_label: str = Field(default="", validate_default=True)
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
        if v in CONCEPTS:
            return v
        # Accept short names without author suffix (AI often omits it)
        for full in CONCEPTS:
            if full.startswith(v) or v.startswith(full.split(" (")[0]):
                return full
        raise ValueError(f"Invalid concept: {v}. Must be one of {CONCEPTS}")

    @field_validator("category_label", mode="after")
    @classmethod
    def default_category_label(cls, v: str, info) -> str:
        if v.strip():
            return v
        category = info.data.get("category", "")
        return CATEGORY_LABELS_EN.get(category, category.replace("_", " ").title())

    @field_validator("severity_label", mode="after")
    @classmethod
    def default_severity_label(cls, v: str, info) -> str:
        if v.strip():
            return v
        severity = info.data.get("severity", "low")
        return SEVERITY_LABELS_EN.get(severity, severity.title())


class AnalysisResult(BaseModel):
    tldr: str
    language: str = Field(default="en", validate_default=True)
    risk_labels: dict[str, str] = Field(default_factory=dict, validate_default=True)
    clauses: list[Clause]

    @field_validator("language", mode="after")
    @classmethod
    def normalize_language(cls, v: str) -> str:
        v = (v or "").strip().lower()
        return v if v else "en"

    @field_validator("risk_labels", mode="after")
    @classmethod
    def fill_risk_labels(cls, v: dict[str, str]) -> dict[str, str]:
        filled = dict(RISK_LABELS_EN)
        for key, label in (v or {}).items():
            if label and label.strip():
                filled[key.lower()] = label.strip()
        return filled
