from typing import Dict, List
from pydantic import BaseModel, Field, validator
import re


class HintsResponse(BaseModel):
    """word -> [hints...] mapping returned by the LLM pipeline.

    Count is validated against FLASHCARD_HINTS_PER_WORD (default 3).
    """

    hints: Dict[str, List[str]] = Field(..., description="word -> [hint1, hint2, ...]")

    @validator("hints")
    def validate_hints(cls, v):
        import os
        pat = re.compile(r"^[A-Za-z]{3,13}$")
        try:
            target = int(os.getenv("FLASHCARD_HINTS_PER_WORD", "3"))
        except Exception:
            target = 3
        for k, arr in v.items():
            if not pat.match(k or ""):
                raise ValueError(f"Invalid word key: {k}")
            if not isinstance(arr, list) or len(arr) != int(target):
                raise ValueError(f"Each word must have exactly {target} hints: {k}")
            for h in arr:
                if not isinstance(h, str) or not h.strip():
                    raise ValueError(f"Empty hint for word: {k}")
                if re.search(re.escape(k), h, re.IGNORECASE):
                    raise ValueError(f"Hint mentions the word itself: {k}")
        return v


