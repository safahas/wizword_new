import os
import re
from dotenv import load_dotenv

load_dotenv()


def sanitize_text(s: str, max_chars: int) -> str:
    s = re.sub(r"\b[\w\.-]+@[\w\.-]+\.\w+\b", "[redacted-email]", s)
    s = re.sub(r"\b\+?\d[\d\s\-\(\)]{7,}\b", "[redacted-phone]", s)
    s = " ".join(s.split())
    return s[:max_chars]


def get_limits() -> tuple[int, int]:
    """Return (max_file_bytes, flashcard_pool_max). Defaults: 10 KB, 10 words."""
    try:
        max_file_bytes = int(os.getenv("UPLOAD_MAX_BYTES", "10240"))
    except Exception:
        max_file_bytes = 10240
    try:
        flash_max = int(os.getenv("FLASHCARD_POOL_MAX", "10"))
    except Exception:
        flash_max = 10
    return max_file_bytes, flash_max


def sanitize_hints_map(hints: dict, desired_count: int, doc_text: str | None = None) -> dict:
    """Post-process LLM output to satisfy schema:
    - keep only 3–10 letter keys (A–Z)
    - ensure exactly 3 hints per word
    - remove the word (case-insensitive, word boundaries) from its hints
    - trim/pad to desired_count entries
    """
    import re
    if not isinstance(hints, dict):
        return {}
    out: dict[str, list[str]] = {}
    key_pat = re.compile(r"^[A-Za-z]{3,10}$")
    # Build doc token set for grounding check
    doc_tokens: set[str] = set()
    if isinstance(doc_text, str) and doc_text:
        doc_tokens = {t.lower() for t in re.findall(r"[A-Za-z]{3,10}", doc_text)}
    # Broad English stopwords and function words; plus generic/unhelpful terms
    STOPWORDS = {
        "and","the","with","which","that","this","these","those","from","then","than","into","onto","until","within","without","across","through","during","before","after","between","against","among","about","like","just","even","both","either","neither","each","per","via","over","under","very","really","quite","maybe","often","sometimes","usually","always","never","again","still","because","however","therefore","thus","also","into","onto","here","there","where","when","while","every","some","many","most","few","more","less","such","only","own","same","other","another","much","any","all","none","one","two","three","four","five","six","seven","eight","nine","ten","first","second","third","part","central","general","common","live",
    }
    def _clean_hint(word: str, hint: str) -> str:
        # Remove ANY occurrence (substring) of the word, case-insensitive
        try:
            pat = re.compile(re.escape(word), re.IGNORECASE)
            return pat.sub("the term", hint or "").strip()
        except Exception:
            return (hint or "").strip()
    safe_fillers = [
        "Context clue from the passage.",
        "Key idea tied to the document.",
        "Relates to the main topic discussed.",
    ]
    for k, arr in hints.items():
        if not isinstance(k, str) or not key_pat.match(k.strip()):
            continue
        word = k.strip()
        # Grounding and stopword checks
        if (doc_tokens and word.lower() not in doc_tokens) or (word.lower() in STOPWORDS):
            continue
        items = []
        if isinstance(arr, list):
            for h in arr:
                if isinstance(h, str) and h.strip():
                    items.append(_clean_hint(word, h))
        # ensure exactly 3
        items = items[:3]
        while len(items) < 3:
            items.append(_clean_hint(word, safe_fillers[len(items) % len(safe_fillers)]))
        out[word] = items
        if len(out) >= desired_count:
            break
    # If fewer than desired_count, return what we have
    return out


