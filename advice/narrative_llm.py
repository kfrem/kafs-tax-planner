"""LLM narrative drafter — richer client-facing prose, grounded in the verified
advice record.

Critically, this is NOT a new source of truth. The draft it returns is passed
through the SAME ``validate_narrative`` guardrail as every other drafter
(advice/narrative.py §8): any number or citation the LLM invents that is not in
the advice record causes the whole draft to be REJECTED. So the model supplies
the *writing*; the engine supplies the *numbers and law*. That is the answer to
"why not just let an LLM write the advice" — because an ungrounded LLM number is
a liability, and here it cannot survive.

Activation: set ``ANTHROPIC_API_KEY`` in the environment (Render dashboard). With
no key, ``llm_available()`` is False and the app falls back to the deterministic
drafter — no hard dependency, nothing to break. Uses the standard library only
(no extra package) so deployment is unchanged.
"""

from __future__ import annotations

import json
import os
import urllib.request

API_URL = "https://api.anthropic.com/v1/messages"
DEFAULT_MODEL = "claude-haiku-4-5-20251001"


def llm_available() -> bool:
    return bool(os.environ.get("ANTHROPIC_API_KEY"))


def _facts_for_prompt(record) -> str:
    """The verified material the model may write from — figures, explanations
    and citations that already exist in the record. The model is told to use
    ONLY these; the validator enforces it afterwards."""
    lines = [f"Client: {record.client.name}", f"Tax year: {record.tax_year}", "", "Strategies:"]
    for r in record.results:
        lines.append(f"- {r['strategy_name']} (risk: {r['risk_status']})")
        lines.append(f"  Explanation: {r['explanation']}")
        lines.append(f"  Figures: {json.dumps(r['quantification'])}")
        cites = "; ".join(a["citation"] for a in r["authorities"])
        if cites:
            lines.append(f"  Authorities: {cites}")
    return "\n".join(lines)


SYSTEM_PROMPT = (
    "You are a UK tax adviser drafting a warm, clear client letter for the "
    "accountant to review and edit. Absolute rules: use ONLY the figures, "
    "percentages, dates and legal citations given in the advice data. Never "
    "invent, estimate, round differently, or introduce any number or citation "
    "that is not in the data. Do not give a definitive recommendation to act — "
    "frame everything as options to discuss. Plain English, no jargon without a "
    "one-line explanation. Start 'Dear [client name],' and keep it under 400 words."
)


def llm_draft(record) -> str:
    """Draft the narrative with the LLM. Raises RuntimeError if no key is set —
    callers should check ``llm_available()`` first and fall back."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set; LLM drafting is unavailable.")

    payload = {
        "model": os.environ.get("ANTHROPIC_MODEL", DEFAULT_MODEL),
        "max_tokens": 900,
        "system": SYSTEM_PROMPT,
        "messages": [{
            "role": "user",
            "content": "Draft the client letter from this verified advice data:\n\n"
                       + _facts_for_prompt(record),
        }],
    }
    req = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    # Messages API returns content as a list of blocks; concatenate the text.
    return "".join(block.get("text", "") for block in body.get("content", [])).strip()
