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


INVALID_CATEGORY = """
{
  "tldr": "Test summary.",
  "clauses": [
    {
      "quote": "We collect data.",
      "plain_english": "They collect your data.",
      "category": "data_extraction",
      "severity": "high",
      "concept": "Surveillance Capitalism (Zuboff)"
    }
  ]
}
"""

INVALID_SEVERITY = """
{
  "tldr": "Test summary.",
  "clauses": [
    {
      "quote": "We collect data.",
      "plain_english": "They collect your data.",
      "category": "data_collection",
      "severity": "critical",
      "concept": "Surveillance Capitalism (Zuboff)"
    }
  ]
}
"""

INVALID_CONCEPT = """
{
  "tldr": "Test summary.",
  "clauses": [
    {
      "quote": "We collect data.",
      "plain_english": "They collect your data.",
      "category": "data_collection",
      "severity": "high",
      "concept": "Made Up Concept (Nobody)"
    }
  ]
}
"""

MISSING_TLDR = """
{
  "clauses": []
}
"""


def test_parse_invalid_category_raises_value_error():
    try:
        parse_response(INVALID_CATEGORY)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_parse_invalid_severity_raises_value_error():
    try:
        parse_response(INVALID_SEVERITY)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_parse_invalid_concept_raises_value_error():
    try:
        parse_response(INVALID_CONCEPT)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass


def test_parse_missing_tldr_raises_value_error():
    try:
        parse_response(MISSING_TLDR)
        assert False, "Should have raised ValueError"
    except ValueError:
        pass
