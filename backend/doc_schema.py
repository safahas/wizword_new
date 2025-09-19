from typing import Dict, List
from pydantic import BaseModel, Field, validator
import re


class HintsResponse(BaseModel):
    """word -> [hint1, hint2, hint3] mapping returned by the LLM pipeline."""

    hints: Dict[str, List[str]] = Field(..., description="word -> [hint1, hint2, hint3]")

    @validator("hints")
    def validate_hints(cls, v):
        pat = re.compile(r"^[A-Za-z]{3,10}$")
        for k, arr in v.items():
            if not pat.match(k or ""):
                raise ValueError(f"Invalid word key: {k}")
            if not isinstance(arr, list) or len(arr) != 3:
                raise ValueError(f"Each word must have exactly 3 hints: {k}")
            for h in arr:
                if not isinstance(h, str) or not h.strip():
                    raise ValueError(f"Empty hint for word: {k}")
                if re.search(re.escape(k), h, re.IGNORECASE):
                    raise ValueError(f"Hint mentions the word itself: {k}")
        return v


