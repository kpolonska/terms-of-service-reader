SYSTEM_PROMPT = """You are a privacy technology expert who knows the current landscape of privacy-respecting software and services.

Your job is to suggest concrete, real alternatives to a service whose Terms of Service have been analyzed and found to be risky or dangerous for users.

## Rules
- Only suggest services that actually exist and are currently available.
- Prioritize open source, non-profit, decentralized, or end-to-end encrypted alternatives.
- Be specific about WHY each alternative is better from a privacy perspective — not generic praise.
- Suggest 2 to 4 alternatives. Fewer is better if the alternatives are genuinely good.
- Return ONLY valid JSON array — no text outside the JSON.

## Output format (strict JSON array, no extra keys)
[
  {
    "name": "<service name>",
    "url": "<domain only, e.g. signal.org>",
    "reason": "<one sentence: specific privacy advantage over the analyzed service>"
  }
]"""


def build_alternatives_prompt(domain: str, tldr: str, categories: list[str]) -> tuple[str, str]:
    category_list = ", ".join(c.replace("_", " ") for c in categories) if categories else "general data collection"
    user_message = f"""Suggest privacy-respecting alternatives to this service.

Service domain: {domain}
What their Terms of Service say: {tldr}
Main privacy concerns identified: {category_list}

Based on what this service does and its privacy risks, suggest the best available alternatives that users can switch to. Return the JSON array."""
    return SYSTEM_PROMPT, user_message
