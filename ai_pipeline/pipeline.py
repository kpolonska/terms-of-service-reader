import os
import anthropic

from prompt import build_prompt
from parser import parse_response
from cache import compute_hash, get_cached, store_result


def analyze_tos(text: str, domain: str | None = None) -> dict:
    text_hash = compute_hash(text)

    cached = get_cached(text_hash)
    if cached:
        return {**cached, "cached": True}

    system_prompt, user_message = build_prompt(text)
    raw_response = _call_claude(system_prompt, user_message)
    result = parse_response(raw_response)

    store_result(text_hash, domain, result)
    return {**result, "cached": False}


def _call_claude(system_prompt: str, user_message: str) -> str:
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2048,
        system=system_prompt,
        messages=[{"role": "user", "content": user_message}],
    )

    return message.content[0].text
