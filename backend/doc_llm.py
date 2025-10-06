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
        f"1) Select exactly {count} distinct words/terms that BEST capture the core ideas of THIS document.\n"
        "   - Each selected term MUST APPEAR in the document (case-insensitive substring is allowed),\n"
        "     but the final key must be a single A–Z token, 3–13 letters.\n"
        "   - Prefer distinctive, subject-specific items: named entities, mechanisms, domain terms, unique phrases\n"
        "     reduced to a single-token form if necessary.\n"
        "   - AVOID generic/academic terms and near-duplicates. Do NOT use any of these as selected words:\n"
        "     batteries, battery, impact, finding, findings, method, methods, condition, conditions, availability,\n"
        "     researcher, researchers, production, community, environment, technology, surface, sample, samples, system,\n"
        "     process, approach, data, model, results, analysis, development, effect, effects, study, studies, paper,\n"
        "     topic, section, work\n"
        "   - Avoid selecting BOTH a noun and its plural (e.g., 'chamber' and 'chambers'); treat morphological variants\n"
        "     as duplicates and keep only one, preferably the singular/base form.\n"
        "   - Avoid filler/function words (pronouns, determiners, prepositions, conjunctions, adverbs).\n"
        "   - Choose words an expert would call core ideas in THIS text (subject-specific over generic).\n"
        f"2) For each selected word, generate EXACTLY {hints_per_word} short hints grounded in THIS document:\n"
        "   - Do NOT include the word itself (no case-insensitive matches or substrings).\n"
        "   - Hint A: Its meaning or role IN THIS DOCUMENT.\n"
        "   - Hint B: A direct reference to how/where it appears in THIS text.\n"
        "   - Hint C: A related idea, effect, or consequence mentioned in THIS document.\n"
        "   - Keep hints specific, concise, and non-generic (avoid dictionary-like phrasing).\n"
        f"3) Output STRICT JSON OBJECT ONLY with this structure (no prose):\n"
        f"   {{ \"TermOne\": [\"h1\", ... up to {hints_per_word}\"], \"TermTwo\": [ ... ] }}\n"
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


