import os
from openai import OpenAI

from prompt import build_prompt
from parser import parse_response
from cache import compute_hash, get_cached, store_result


def analyze_tos(text: str, domain: str | None = None) -> dict:
    text_hash = compute_hash(text)

    cached = get_cached(text_hash)
    if cached:
        return {**cached, "cached": True}

    system_prompt, user_message = build_prompt(text)
    raw_response = _call_llm(system_prompt, user_message)
    result = parse_response(raw_response)

    store_result(text_hash, domain, result)
    return {**result, "cached": False}


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
