import os
import logging
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv, find_dotenv

from .doc_utils import get_limits, sanitize_text, sanitize_hints_map
from .doc_schema import HintsResponse
from .doc_llm import generate_hints_from_text

# Load environment from a shared .env (prefer project root), without overriding existing env
_ENV_PATH = find_dotenv(usecwd=True)
if not _ENV_PATH:
    try:
        _ENV_PATH = str((Path(__file__).resolve().parent.parent / ".env"))
    except Exception:
        _ENV_PATH = ""
if _ENV_PATH and os.path.exists(_ENV_PATH):
    # .env should override any pre-set env vars for deterministic config
    load_dotenv(_ENV_PATH, override=True)

logger = logging.getLogger(__name__)
try:
    logger.info(f"[DocAPI] Loaded .env from: {_ENV_PATH or '[none]'}; FLASHCARD_POOL_MAX={os.getenv('FLASHCARD_POOL_MAX','10')}; UPLOAD_MAX_BYTES={os.getenv('UPLOAD_MAX_BYTES','10240')}")
except Exception:
    pass

app = FastAPI(title="WizWord Doc Hint API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True,
    allow_methods=["*"], allow_headers=["*"],
)

@app.get("/env-debug")
def env_debug():
    """Return key environment values and computed limits for quick verification."""
    max_bytes, flash_max = get_limits()
    return {
        "env_path": _ENV_PATH or "",
        "env": {
            "FLASHCARD_POOL_MAX": os.getenv("FLASHCARD_POOL_MAX", "unset"),
            "UPLOAD_MAX_BYTES": os.getenv("UPLOAD_MAX_BYTES", "unset"),
            "OPENROUTER_MODEL": os.getenv("OPENROUTER_MODEL", "unset"),
            "BACKEND_HINTS_URL": os.getenv("BACKEND_HINTS_URL", "unset"),
        },
        "limits": {
            "max_file_bytes": max_bytes,
            "flashcard_pool_max": flash_max,
        },
    }


def _read_upload_bytes(file: UploadFile, max_bytes: int) -> bytes:
    data = file.file.read(max_bytes + 1)
    if not data:
        raise HTTPException(status_code=400, detail="Empty file.")
    if len(data) > max_bytes:
        raise HTTPException(status_code=400, detail=f"File exceeds limit of {max_bytes} bytes.")
    return data


@app.post("/generate-hints", response_model=HintsResponse)
async def generate_hints(file: UploadFile = File(...)):
    max_bytes, flash_max = get_limits()
    raw = _read_upload_bytes(file, max_bytes)
    name = (file.filename or "").lower()
    ext = name.split(".")[-1]
    # Simple text extraction (PDF/DOCX/TXT minimal viable)
    text = ""
    try:
        if ext == "pdf":
            from io import BytesIO
            # Prefer pypdf if available; fall back to PyPDF2 for broader compatibility
            try:
                from pypdf import PdfReader as _PdfReader  # type: ignore
            except Exception:
                try:
                    from PyPDF2 import PdfReader as _PdfReader  # type: ignore
                except Exception as _imp_err:
                    raise RuntimeError(f"PDF parser not available: {_imp_err}")
            reader = _PdfReader(BytesIO(raw))
            try:
                pages = reader.pages
            except Exception:
                # PyPDF2 older API
                pages = getattr(reader, "pages", [])
            text = "\n".join([(getattr(p, "extract_text", lambda: "")() or "") for p in pages])
        elif ext == "docx":
            from io import BytesIO
            from docx import Document
            doc = Document(BytesIO(raw))
            text = "\n".join([p.text for p in doc.paragraphs])
        elif ext == "txt":
            text = raw.decode("utf-8", errors="ignore")
        else:
            raise HTTPException(status_code=400, detail="Unsupported file type. Use PDF, DOCX, or TXT.")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to read file: {e}")

    # Allow larger context via env knob to improve word coverage
    try:
        _doc_max_chars = int(os.getenv("DOC_MAX_CHARS", "8000"))
    except Exception:
        _doc_max_chars = 8000
    text = sanitize_text(text, max_chars=_doc_max_chars)
    # Ensure API key is available (from .env or environment)
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("[DocAPI] OPENROUTER_API_KEY not set; .env path=%s", _ENV_PATH or "[none]")
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY not set (backend .env not loaded or variable missing)")
    try:
        raw_hints = await generate_hints_from_text(text, count=flash_max)
        cleaned = sanitize_hints_map(raw_hints, desired_count=flash_max, doc_text=text)
        resp = HintsResponse(hints=cleaned)
        return resp
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"LLM error: {e}")


