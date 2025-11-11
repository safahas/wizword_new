import os
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi import Body
from fastapi.responses import FileResponse
from pydantic import BaseModel

from .tts import synthesize, pick_voice, hash_key  # noqa: F401  (hash_key/pick_voice exposed)

app = FastAPI(title="WizWord Backend")


class TTSRequest(BaseModel):
    text: str
    lang: str | None = "auto"
    voice: str | None = None
    speed: float | None = 1.0


@app.post("/tts")
def tts_generate(req: TTSRequest):
    if not req.text or not req.text.strip():
        raise HTTPException(status_code=400, detail="text is required")
    path = synthesize(req.text.strip(), req.lang or "auto", req.voice, req.speed or 1.0)
    return {"ok": True, "file": f"/tts/{path.stem}.mp3"}


@app.get("/tts/{fname}.mp3")
def tts_get(fname: str):
    audio = Path(os.getenv("TTS_CACHE_DIR", "/mnt/audio")).resolve() / f"{fname}.mp3"
    if not audio.exists():
        raise HTTPException(status_code=404, detail="audio not found")
    return FileResponse(str(audio), media_type="audio/mpeg")


