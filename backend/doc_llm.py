import os
import json
import httpx
import logging
from dotenv import load_dotenv, find_dotenv

# Load shared .env (prefer project root) without overriding existing env
_ENV_PATH = find_dotenv(usecwd=True)
if _ENV_PATH:
    # Prefer .env values over pre-set env for consistent behavior
    load_dotenv(_ENV_PATH, override=True)
try:
    logging.getLogger(__name__).info(f"[DocLLM] Loaded .env from: {_ENV_PATH or '[none]'}; MODEL={os.getenv('OPENROUTER_MODEL','')}")
except Exception:
    pass

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o")


def _build_prompt(doc_text: str, count: int) -> dict:
    # How many hints per word to request (default 3)
    try:
        hints_per_word = int(os.getenv("FLASHCARD_HINTS_PER_WORD", "3"))
    except Exception:
        hints_per_word = 3

    system = (
        "You are powering a flash‑card generator for a comprehension game. "
        "Always return STRICT JSON only (no markdown, no code fences, no prose)."
    )

    user = (
        "You are powering a flash-card generator for a comprehension game.\n\n"
        "DOCUMENT CONTENT (sanitized, may be truncated):\n---\n"
        f"{doc_text}\n"
        "---\n\n"
        "TASK:\n"
        f"1. Select exactly {count} words that best capture the core meaning of the document.\n"
        "   - Each word MUST appear in the document text itself.\n"
        "   - Each must be 3–13 letters, A–Z only (no digits, spaces, apostrophes, or hyphens).\n"
        "   - Choose significant content words that highlight key themes, actors, or concepts.\n"
        "   - Avoid filler/function words (pronouns, determiners, conjunctions, prepositions, adverbs)\n"
        "     like: the, and, very, with, which, her, she, he, they, it, you, we, this, that, these, those,\n"
        "     a, an, some, many, most, few, more, less, any, all, none, and similar.\n"
        f"2. For each selected word, generate EXACTLY {hints_per_word} short hints grounded in THIS document:\n"
        "   - Do NOT include the word itself (no case-insensitive matches or substrings).\n"
        "   - Hint A: The meaning or role of the word in the context of THIS document.\n"
        "   - Hint B: A direct reference to how it appears or functions in THIS text.\n"
        "   - Hint C: A related idea, effect, or consequence mentioned in the document.\n"
        f"3. Output STRICT JSON ONLY: keys = words, values = arrays of {hints_per_word} hints.\n\n"
        "FORMAT EXAMPLE (structure only; do not copy content):\n"
        "{\n"
        "  \"Equity\": [\n"
        "    \"Fair treatment described as essential in the text.\",\n"
        "    \"Linked to protections ensuring equal opportunity.\",\n"
        "    \"Presented as a guiding principle in the document.\"\n"
        "  ],\n"
        "  \"Harass\": [\n"
        "    \"Unwanted behavior creating an unsafe environment.\",\n"
        "    \"Explicitly prohibited in the workplace section.\",\n"
        "    \"Connected to procedures for reporting and remedies.\"\n"
        "  ]\n"
        "}"
    )

    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.3,
        "response_format": {"type": "json_object"},
    }
    return body


async def generate_hints_from_text(doc_text: str, count: int) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY not set (backend .env not loaded or variable missing)")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": os.environ.get("OPENROUTER_REFERER", "https://example.com"),
        "X-Title": os.environ.get("OPENROUTER_TITLE", "WizWord Hint Generator"),
        "Content-Type": "application/json",
    }
    body = _build_prompt(doc_text, count)
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(OPENROUTER_URL, headers=headers, json=body)
        r.raise_for_status()
        data = r.json()
    content = data["choices"][0]["message"]["content"].strip()
    return json.loads(content)


