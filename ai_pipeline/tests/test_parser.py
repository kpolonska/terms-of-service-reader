import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from parser import parse_response


VALID_JSON = """
{
  "tldr": "This service collects your data and shares it with third parties.",
  "clauses": [
    {
      "quote": "We may share your information with our partners.",
      "plain_english": "The company can give your data to other businesses.",
      "category": "data_sharing_third_parties",
      "severity": "high",
      "concept": "Surveillance Capitalism (Zuboff)"
    }
  ]
}
"""

MARKDOWN_WRAPPED = f"```json\n{VALID_JSON.strip()}\n```"

PROSE_BEFORE = f"Sure, here is the analysis:\n{VALID_JSON}"


def test_parse_clean_json():
    result = parse_response(VALID_JSON)
    assert result["tldr"] != ""
    assert len(result["clauses"]) == 1
    assert result["clauses"][0]["severity"] == "high"


def test_parse_markdown_wrapped():
    result = parse_response(MARKDOWN_WRAPPED)
    assert len(result["clauses"]) == 1


def test_parse_json_with_prose():
    result = parse_response(PROSE_BEFORE)
    assert result["tldr"] != ""


def test_parse_invalid_raises():
    try:
        parse_response("This is not JSON at all.")
        assert False, "Should have raised"
    except ValueError:
        pass
