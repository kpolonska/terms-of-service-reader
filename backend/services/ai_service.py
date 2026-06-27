import sys
import os

sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "ai_pipeline"))

from prompt import build_prompt
from parser import parse_response
from cache import get_cached, store_result, compute_hash


def analyze(text: str, domain: str | None = None) -> dict:
    text_hash = compute_hash(text)

    cached = get_cached(text_hash)
    if cached:
        return {**cached, "cached": True}

    # TODO: replace with actual Claude/OpenAI API call
    # raw_response = call_claude(build_prompt(text))
    raw_response = _mock_api_call(text)

    result = parse_response(raw_response)
    store_result(text_hash, domain, result)

    return {**result, "cached": False}


def _mock_api_call(text: str) -> str:
    # Placeholder — remove once ai_pipeline prompt.py + Claude integration is wired up
    return """
    {
      "tldr": "This is a placeholder analysis. Wire up the Claude API to get real results.",
      "clauses": [
        {
          "quote": "We may share your data with third parties.",
          "plain_english": "The company can give your personal data to other companies.",
          "category": "data_sharing_third_parties",
          "severity": "high",
          "concept": "Surveillance Capitalism (Zuboff)"
        }
      ]
    }
    """
