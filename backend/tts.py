import os
import hashlib
from pathlib import Path
from typing import Optional

import boto3  # type: ignore


CACHE_DIR = Path(os.getenv("TTS_CACHE_DIR", "/mnt/audio")).resolve()
try:
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
except Exception:
    pass


def hash_key(text: str, lang: str, voice: str, speed: float) -> str:
    key = f"{text}|{lang}|{voice}|{speed:.2f}".encode("utf-8", "ignore")
    return hashlib.sha1(key).hexdigest()


def pick_voice(lang: str) -> str:
    lng = (lang or "auto").strip().lower()
    # Chinese
    if lng in ("zh", "zh-cn", "chinese") or lng.startswith("zh"):
        return os.getenv("POLLY_VOICE_ZH", "Zhiyu")
    # Arabic
    if lng in ("ar", "ar-sa", "arabic") or lng.startswith("ar"):
        return os.getenv("POLLY_VOICE_AR", "Zeina")
    if lng.startswith("es"):
        return os.getenv("POLLY_VOICE_ES", "Lucia")
    if lng.startswith("fr"):
        return os.getenv("POLLY_VOICE_FR", "Celine")
    # default English
    return os.getenv("POLLY_VOICE_EN", "Joanna")


def to_ssml(text: str, lang: str, speed: float) -> str:
    try:
        spd = float(speed or 1.0)
    except Exception:
        spd = 1.0
    spd = max(0.8, min(1.2, spd))
    pct = int(spd * 100)
    # very basic sanitization
    safe = str(text or "").replace("&", "and").replace("<", "").replace(">", "")
    return f'<speak><prosody rate="{pct}%">{safe}</prosody></speak>'


def synthesize(text: str, lang: str = "auto", voice: Optional[str] = None, speed: float = 1.0) -> Path:
    v = voice or pick_voice(lang or "auto")
    h = hash_key(text or "", lang or "auto", v, speed or 1.0)
    out = CACHE_DIR / f"{h}.mp3"
    if out.exists():
        return out
    polly = boto3.client("polly", region_name=os.getenv("AWS_REGION", "us-west-2"))
    ssml = to_ssml(text or "", lang or "auto", speed or 1.0)
    resp = polly.synthesize_speech(
        TextType="ssml",
        Text=ssml,
        VoiceId=v,
        OutputFormat="mp3",
        Engine="neural",
    )
    audio = resp["AudioStream"].read()
    out.write_bytes(audio)
    return out


