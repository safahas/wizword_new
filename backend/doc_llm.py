import os
import json
import httpx
import logging
from dotenv import load_dotenv, find_dotenv

# Load shared .env (prefer project root) without overriding existing env
_ENV_PATH = find_dotenv(usecwd=True)
if _ENV_PATH:
    load_dotenv(_ENV_PATH, override=False)
try:
    logging.getLogger(__name__).info(f"[DocLLM] Loaded .env from: {_ENV_PATH or '[none]'}; MODEL={os.getenv('OPENROUTER_MODEL','')}")
except Exception:
    pass

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = os.getenv("OPENROUTER_MODEL", "gpt-4o")


def _build_prompt(doc_text: str, count: int) -> dict:
    system = (
        "You are a helpful assistant that extracts key vocabulary from a document and "
        "returns EXACT JSON—no code fences, no commentary."
    )
    user = f"""You are powering a word/hint generator for a vocabulary game.

INPUT DOCUMENT (sanitized, truncated):
---
{doc_text}
---

TASK:
1) Choose exactly {count} important words that best test comprehension of the above text.
2) Constraints for words:
   - 3–10 letters, A–Z only (no spaces, digits, apostrophes, or hyphens)
   - Avoid overly obscure terms; prefer high-signal content words
3) For each selected word, produce EXACTLY three short, simple hints:
   - Do NOT include the word itself in any hint
   - Hints must be diverse and grounded in the document context
   - Keep them age-appropriate and clear
4) Output STRICT JSON as an object mapping words to arrays of three strings.

OUTPUT FORMAT EXAMPLE (structure only; not actual content):
{{
  "WordOne": ["hint1", "hint2", "hint3"],
  "WordTwo": ["hint1", "hint2", "hint3"]
}}
"""
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


