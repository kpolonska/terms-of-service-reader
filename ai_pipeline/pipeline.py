import os
import re
import json
from openai import OpenAI

from prompt import build_prompt
from parser import parse_response
from cache import compute_hash, get_cached, store_result
from explain_prompt import build_explain_prompt
from alternatives_prompt import build_alternatives_prompt
from cache import get_cached_alternatives, store_alternatives


def analyze_tos(text: str, domain: str | None = None, profile: str = "general") -> dict:
    text_hash = compute_hash(text)

    cached = get_cached(text_hash)
    if cached:
        return {**cached, "cached": True}

    system_prompt, user_message = build_prompt(text, profile)
    raw_response = _call_llm(system_prompt, user_message)
    result = parse_response(raw_response)

    store_result(text_hash, domain, result)
    return {**result, "cached": False}


def generate_alternatives(domain: str, tldr: str, categories: list[str]) -> list[dict]:
    cached = get_cached_alternatives(domain)
    if cached is not None:
        return cached

    system_prompt, user_message = build_alternatives_prompt(domain, tldr, categories)
    raw = _call_llm(system_prompt, user_message)

    try:
        raw = raw.strip()
        if raw.startswith("["):
            alternatives = json.loads(raw)
        else:
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            alternatives = json.loads(match.group(0)) if match else []
    except Exception:
        alternatives = []

    store_alternatives(domain, alternatives)
    return alternatives


def explain_clause(quote: str, category: str, profile: str = "general") -> dict:
    system_prompt, user_message = build_explain_prompt(quote, category, profile)
    raw = _call_llm(system_prompt, user_message)
    try:
        return json.loads(raw.strip())
    except json.JSONDecodeError:
        import re
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        raise ValueError("Could not parse explain response from AI.")


def _call_llm(system_prompt: str, user_message: str) -> str:
    client = OpenAI(
        api_key=os.environ["LLMAPI_KEY"],
        base_url=os.environ.get("LLMAPI_BASE_URL", "https://api.llmapi.ai/v1"),
    )

    response = client.chat.completions.create(
        model="claude-haiku-4-5",
        max_tokens=2048,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    return response.choices[0].message.content
