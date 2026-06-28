import json
import re
from pydantic import ValidationError
from tos_models import AnalysisResult


def parse_response(raw: str) -> dict:
    parsed = _extract_json(raw)
    try:
        result = AnalysisResult(**parsed)
    except ValidationError as e:
        raise ValueError(f"AI response failed schema validation: {e}") from e
    return result.model_dump()


def _extract_json(raw: str) -> dict:
    raw = raw.strip()

    # Try direct parse first
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        pass

    # Claude sometimes wraps JSON in ```json ... ``` blocks
    match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass

    # Last resort: find the first { ... } block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(0))
        except json.JSONDecodeError:
            pass

    raise ValueError(f"Could not extract valid JSON from AI response. Raw response:\n{raw[:500]}")
