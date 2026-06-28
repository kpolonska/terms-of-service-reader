from tos_models import CATEGORIES, CONCEPTS, SEVERITY_LEVELS

_BASE_SYSTEM_PROMPT = f"""You are an expert legal analyst and privacy rights advocate specializing in Terms of Service documents.
Your job is to help ordinary users understand what they are agreeing to — in plain language, without legal jargon.

You will be given a Terms of Service text. Identify 5 to 10 of the most important clauses
and return a structured JSON analysis. You must return ONLY valid JSON — no prose, no markdown,
no explanation outside the JSON object.

## Quoting rules (strict)
- Every "quote" MUST appear VERBATIM in the document text. Copy the wording exactly, character for character.
- Do NOT paraphrase, summarize, rewrite, or invent text in the "quote" field.
- Keep quotes under 200 characters — pick the single most revealing short sentence or phrase.
- If you cannot find a verbatim excerpt for a concern, do not include that clause.

## Categories
Each clause must be assigned one of these categories:
{chr(10).join(f'- {c}' for c in CATEGORIES)}

## Severity levels
- low: Minor or standard clause with little impact on the user
- medium: Noticeable restriction of user rights or privacy
- high: Serious risk, significant data extraction, or rights loss

## Concepts (map each clause to one)
You MUST use the EXACT string below, including the parentheses and author name.
Do NOT shorten "Surveillance Capitalism (Zuboff)" to "Surveillance Capitalism".
Do NOT shorten "Datafication (Van Dijck)" to "Datafication". Same for all others.
Allowed values (copy verbatim):
{chr(10).join(f'- "{c}"' for c in CONCEPTS)}

## Output format (strict JSON, no extra keys)
{{
  "tldr": "<2-3 sentence plain-English summary of the whole document>",
  "clauses": [
    {{
      "quote": "<verbatim excerpt from the ToS, max 200 chars>",
      "plain_english": "<one sentence explanation a teenager would understand>",
      "category": "<one of the categories above>",
      "severity": "<low | medium | high>",
      "concept": "<one of the concepts above>"
    }}
  ]
}}
"""

PROFILE_ADDITIONS = {
    "journalist": (
        "\n## EXTREME IMPORTANCE: User is a JOURNALIST/INVESTIGATIVE REPORTER analyzing for SOURCE PROTECTION\n"
        "COMPLETELY REANALYZE this document through the lens of protecting journalistic sources and avoiding government surveillance.\n"
        "YOU MUST do the following OR YOUR ANALYSIS FAILS:\n"
        "1. ONLY look for and ONLY include clauses about: \n"
        "   - Government/law enforcement data requests, court orders, subpoenas\n"
        "   - Data retention policies that could expose source identity\n"
        "   - Account termination without warning (eliminates source access)\n"
        "   - IP logging, metadata collection, user identification\n"
        "   - Terms allowing data sharing with authorities\n"
        "   - Anonymity guarantees (or lack thereof)\n"
        "2. IGNORE all other clauses (data selling, ads, standard business terms).\n"
        "3. Mark EVERY clause about government data access as HIGH severity.\n"
        "4. Your TLDR MUST focus ONLY on government surveillance risks and source protection.\n"
        "5. This analysis MUST be COMPLETELY DIFFERENT from a 'general' analysis."
    ),
    "activist": (
        "\n## EXTREME IMPORTANCE: User is an ACTIVIST/ORGANIZER analyzing for PERSONAL SAFETY\n"
        "COMPLETELY REANALYZE this document through the lens of surveillance, account control, and personal safety during activism.\n"
        "YOU MUST do the following OR YOUR ANALYSIS FAILS:\n"
        "1. ONLY look for and ONLY include clauses about:\n"
        "   - Surveillance capabilities (behavioral tracking, profiling, geolocation)\n"
        "   - Account suspension/termination policies (removes organizing platform)\n"
        "   - Content removal authority and moderation\n"
        "   - Data sharing with law enforcement or governments\n"
        "   - IP tracking, device fingerprinting, location tracking\n"
        "   - Right to know who has your data\n"
        "2. IGNORE clauses about intellectual property, business terms, data monetization.\n"
        "3. Mark surveillance and law enforcement sharing as HIGH severity.\n"
        "4. Your TLDR MUST focus ONLY on surveillance risks and account safety.\n"
        "5. This analysis MUST be COMPLETELY DIFFERENT from a 'general' analysis."
    ),
    "business": (
        "\n## EXTREME IMPORTANCE: User is a BUSINESS PROFESSIONAL analyzing for LEGAL/FINANCIAL RISK\n"
        "COMPLETELY REANALYZE this document through the lens of business liability, IP ownership, and contract risk.\n"
        "YOU MUST do the following OR YOUR ANALYSIS FAILS:\n"
        "1. ONLY look for and ONLY include clauses about:\n"
        "   - Content ownership and IP rights (who owns what you create)\n"
        "   - Liability disclaimers and indemnification\n"
        "   - Commercial use restrictions or prohibitions\n"
        "   - Service termination terms (loss of business access)\n"
        "   - Data export and account deletion policies\n"
        "   - Payment disputes, refund policies, price changes\n"
        "2. IGNORE clauses about personal privacy, government surveillance, data selling.\n"
        "3. Mark IP loss and liability limits as HIGH severity.\n"
        "4. Your TLDR MUST focus ONLY on business liability and financial/legal exposure.\n"
        "5. This analysis MUST be COMPLETELY DIFFERENT from a 'general' analysis."
    ),
    "general": "",
}


def build_prompt(tos_text: str, profile: str = "general") -> tuple[str, str]:
    profile_addition = PROFILE_ADDITIONS.get(profile, "")
    system_prompt = _BASE_SYSTEM_PROMPT + profile_addition

    user_message = f"""Analyze this Terms of Service document and return the JSON analysis.

--- BEGIN DOCUMENT ---
{tos_text}
--- END DOCUMENT ---
"""
    return system_prompt, user_message
