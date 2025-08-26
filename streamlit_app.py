from dotenv import load_dotenv
import os
# Updated 07/28
# Always use the absolute path to your .env in the current project directory
load_dotenv(dotenv_path=os.path.join(os.getcwd(), ".env"))
import random
import string
import streamlit as st
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import json
import os
import uuid
import datetime
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib.category').setLevel(logging.WARNING)

USERS_FILE = os.environ.get("USERS_FILE", "users.json")
BIO_MAX_CHARS = int(os.environ.get("BIO_MAX_CHARS", "10000"))
PROFILE_BIO_KEY = "profile_bio"

# Global counters file (users count, total game time, total sessions, live sessions)
GLOBAL_COUNTERS_PATH = os.environ.get('GLOBAL_COUNTERS_PATH', 'game_data/global_counters.json')
LIVE_SESSIONS_PATH = os.environ.get('LIVE_SESSIONS_PATH', 'game_data/live_sessions.json')

def _ensure_global_counters_file() -> None:
    try:
        os.makedirs(os.path.dirname(GLOBAL_COUNTERS_PATH) or '.', exist_ok=True)
        if not os.path.exists(GLOBAL_COUNTERS_PATH):
            with open(GLOBAL_COUNTERS_PATH, 'w', encoding='utf-8') as f:
                json.dump({
                    'users_count': 0,
                    'total_game_time_seconds': 0,
                    'total_sessions': 0,
                    'live_sessions': 0
                }, f, indent=2)
    except Exception:
        pass

def _ensure_live_sessions_file() -> None:
    try:
        os.makedirs(os.path.dirname(LIVE_SESSIONS_PATH) or '.', exist_ok=True)
        if not os.path.exists(LIVE_SESSIONS_PATH):
            with open(LIVE_SESSIONS_PATH, 'w', encoding='utf-8') as f:
                json.dump({}, f)
    except Exception:
        pass

def _load_global_counters() -> dict:
    _ensure_global_counters_file()
    try:
        with open(GLOBAL_COUNTERS_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # Backfill missing keys for older files
            if 'live_sessions' not in data:
                data['live_sessions'] = 0
            if 'total_sessions' not in data:
                data['total_sessions'] = 0
            if 'total_game_time_seconds' not in data:
                data['total_game_time_seconds'] = 0
            if 'users_count' not in data:
                data['users_count'] = 0
            return data
    except Exception:
        return {'users_count': 0, 'total_game_time_seconds': 0, 'total_sessions': 0}

def _save_global_counters(counters: dict) -> None:
    try:
        with open(GLOBAL_COUNTERS_PATH, 'w', encoding='utf-8') as f:
            json.dump(counters, f, indent=2)
    except Exception:
        pass

def _read_live_sessions() -> dict:
    _ensure_live_sessions_file()
    try:
        with open(LIVE_SESSIONS_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {}

def _write_live_sessions(data: dict) -> None:
    try:
        with open(LIVE_SESSIONS_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f)
    except Exception:
        pass

def heartbeat_live_session(session_id: str, username: str) -> None:
    """Record/refresh a heartbeat for a live Beat session."""
    try:
        import time as _t
        data = _read_live_sessions()
        data[session_id] = {
            'username': str(username).lower(),
            'ts': int(_t.time())
        }
        _write_live_sessions(data)
    except Exception:
        pass

def count_active_live_sessions(window_seconds: int = 120) -> int:
    """Count sessions with a heartbeat within the given window (default 2 minutes)."""
    try:
        import time as _t
        now = int(_t.time())
        data = _read_live_sessions()
        active = 0
        pruned = False
        for sid, info in list(data.items()):
            ts = int(info.get('ts', 0))
            if (now - ts) <= window_seconds:
                active += 1
            else:
                # prune stale
                data.pop(sid, None)
                pruned = True
        if pruned:
            _write_live_sessions(data)
        return active
    except Exception:
        return 0

def end_live_session(session_id: str) -> None:
    """Remove a live session entry immediately (called on game over)."""
    try:
        data = _read_live_sessions()
        if session_id in data:
            data.pop(session_id, None)
            _write_live_sessions(data)
    except Exception:
        pass

def update_global_counters(users_delta: int = 0, time_seconds_delta: int = 0, sessions_delta: int = 0, live_sessions_delta: int = 0) -> None:
    counters = _load_global_counters()
    counters['users_count'] = max(0, counters.get('users_count', 0) + users_delta)
    counters['total_game_time_seconds'] = max(0, counters.get('total_game_time_seconds', 0) + int(time_seconds_delta))
    counters['total_sessions'] = max(0, counters.get('total_sessions', 0) + sessions_delta)
    counters['live_sessions'] = max(0, counters.get('live_sessions', 0) + live_sessions_delta)
    _save_global_counters(counters)

def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)
def send_reset_email(to_email, reset_code):
    # Configure your SMTP server here
    SMTP_SERVER = os.environ.get("SMTP_HOST")
    SMTP_PORT = 587
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASS")  # Use an app password, not your real password!

    subject = "Your Password Reset Code"
    body = f"Your password reset code is: {reset_code}"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = SMTP_USER
    msg["To"] = to_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False

def send_email_with_attachment(to_emails, subject, body, attachment_path=None, cc_emails=None) -> bool:
    SMTP_SERVER = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASS")

    if isinstance(to_emails, str):
        to_emails = [to_emails]
    cc_emails = cc_emails or []

    try:
        msg = MIMEMultipart()
        msg["From"] = SMTP_USER or ""
        msg["To"] = ", ".join([e for e in to_emails if e])
        if cc_emails:
            msg["Cc"] = ", ".join([e for e in cc_emails if e])
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))

        if attachment_path and os.path.exists(attachment_path):
            with open(attachment_path, "rb") as f:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(f.read())
            encoders.encode_base64(part)
            filename = os.path.basename(attachment_path)
            part.add_header('Content-Disposition', f'attachment; filename="{filename}"')
            msg.attach(part)

        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            recipients = [e for e in to_emails if e] + [e for e in (cc_emails or []) if e]
            server.sendmail(SMTP_USER, recipients, msg.as_string())
        return True
    except Exception as e:
        print(f"Failed to send email with attachment: {e}")
        return False
# Initialize user store for demo (replace with real DB in production)
if 'users' not in st.session_state:
    st.session_state['users'] = load_users()
    # One-time backfill of games_count from existing game_results.json
    try:
        existing = st.session_state['users'] if isinstance(st.session_state.get('users'), dict) else {}
        # Lazy import to avoid forward reference
        from streamlit_app import get_all_game_results as _get_all_game_results  # type: ignore
        all_games = _get_all_game_results()
        counts = {}
        for g in all_games:
            uname = str(g.get('nickname', '')).lower()
            if uname:
                counts[uname] = counts.get(uname, 0) + 1
        changed = False
        for uname, u in list(existing.items()):
            if isinstance(u, dict):
                if not isinstance(u.get('games_count'), int):
                    u['games_count'] = counts.get(str(uname).lower(), 0)
                    changed = True
        if changed:
            save_users(existing)
    except Exception:
        pass
    # Run once-per-day miss-you email check
    try:
        from streamlit_app import run_daily_miss_you_check as _miss_you  # type: ignore
        _miss_you()
    except Exception:
        pass
# Configure Streamlit page with custom theme
st.set_page_config(
    page_title="WizWord - Word Guessing Game",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# WizWord - Word Guessing Game\nTest your deduction skills against AI!"
    }
)

# st.write("🚨 [DEBUG] THIS IS THE REAL streamlit_app.py - TEST MARKER")
from backend.game_logic import GameLogic
import os
import streamlit as st
import json
import re
import time
import random
from backend.monitoring import logger  # Add monitoring logger
from pathlib import Path
from backend.game_logic import GameLogic
from backend.word_selector import WordSelector
from backend.session_manager import SessionManager
from backend.share_card import create_share_card
from backend.share_utils import ShareUtils
from backend.user_auth import register_user, login_user, load_user_profile
import requests
import time as _time
import string
import streamlit.components.v1 as components
import sys



BEAT_MODE_TIMEOUT_SECONDS = int(os.getenv("BEAT_MODE_TIME", 300))
# print(f"[DEBUG] BEAT_MODE_TIMEOUT_SECONDS = {BEAT_MODE_TIMEOUT_SECONDS}")
RECENT_WORDS_LIMIT = 50



# Inject click sound JS (static directory)
st.markdown("""
<audio id=\"click-sound\" src=\"static/clicksound.mp3\"></audio>
<script>
document.addEventListener('click', function(e) {
    var audio = document.getElementById('click-sound');
    if(audio) {
        audio.currentTime = 0;
        audio.play();
    }
}, true);
</script>
""", unsafe_allow_html=True)

# Initialize ShareUtils
share_utils = ShareUtils()

# Custom CSS for better UI
st.markdown(
    """
    <link href="https://fonts.googleapis.com/css2?family=Baloo+2:wght@700&family=Poppins:wght@700&display=swap" rel="stylesheet">
    <style>
    /* Make all text more visible and bold */
    body, .stApp, .stMarkdown, .stMetricValue, .stMetricLabel, .stTextInput>div>div>input, .stSelectbox>div>div, .stForm, .stButton>button, .stAlert, .streamlit-expanderHeader, .stRadio>div, .stExpander, .stText, .stDataFrame, .stTable, .stCode, .stMetric, h1, h2, h3, h4, h5, h6 {
        font-weight: 700 !important;
        color: #222 !important;
        text-shadow: 0 1px 4px rgba(255,255,255,0.15), 0 1px 1px rgba(0,0,0,0.08);
        letter-spacing: 0.01em;
    }
    /* New styles for the split layout */
    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 10px;
    }
    [data-testid="column"]:first-child {
        background: rgba(255, 255, 255, 0.08);
    }
    [data-testid="column"]:last-child {
        background: rgba(255, 255, 255, 0.12);
    }
    .instructions h1 {
        color: #ffffff;
        font-size: 2em;
        margin-bottom: 1em;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
    }
    .instructions h3 {
        color: #ffffff;
        font-size: 1.3em;
        margin-top: 1.5em;
        margin-bottom: 0.8em;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    .instructions ul {
        margin-left: 1.5em;
        margin-bottom: 1.5em;
    }
    .instructions li {
        margin-bottom: 0.5em;
        color: #ffffff;
    }
    /* Main background with sky gradient */
    .stApp {
        background: linear-gradient(135deg, #B5E3FF 0%, #7CB9E8 100%);
        color: white;
    }
    /* Style for all buttons */
    .stButton>button {
        width: 100%;
        border-radius: 10px;
        height: 3em;
        background: rgba(255, 255, 255, 0.25);
        border: 1px solid rgba(255, 255, 255, 0.35);
        color: white;
        transition: all 0.3s ease;
        font-weight: bold;
        font-size: 1.1em;
    }
    /* Special styling for Start New Game button */
    .stButton>button:first-child {
        background: linear-gradient(135deg, #6FDFBF 0%, #A8D8F0 100%);
        border: none;
        color: white;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 20px;
        height: 4em;
        font-size: 1.2em;
    }
    .stButton>button:hover {
        background: rgba(255, 255, 255, 0.3);
        border: 1px solid rgba(255, 255, 255, 0.4);
        transform: translateY(-2px);
        box-shadow: 0 5px 15px rgba(0,0,0,0.2);
    }
    /* Special hover for Start New Game button */
    .stButton>button:first-child:hover {
        background: linear-gradient(135deg, #5ddfb0 0%, #9ed3f0 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0,0,0,0.15);
    }
    /* Style for text inputs */
    .stTextInput>div>div>input {
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.9);
        border: 1px solid rgba(255, 255, 255, 0.3);
        color: #000000;
        padding: 1em;
        font-weight: 500;
    }
    .stTextInput>div>div>input::placeholder {
        color: rgba(0, 0, 0, 0.5);
    }
    /* Style for alerts and info boxes */
    .stAlert {
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.3);
    }
    /* Style for expanders */
    .streamlit-expanderHeader {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    /* Style for metrics */
    [data-testid="stMetricValue"] {
        color: #ffffff;
        font-weight: bold;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    /* Style for headers */
    h1, h2, h3, h4, h5, h6 {
        color: #ffffff;
        margin-bottom: 1em;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    /* Style for markdown text */
    .stMarkdown {
        color: #ffffff;
    }
    /* Style for forms */
    .stForm {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* Style for selectbox */
    .stSelectbox>div>div {
        background: rgba(255, 255, 255, 0.9) !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        border-radius: 10px;
        color: #000000 !important;
    }
    /* Style for selectbox dropdown */
    .stSelectbox>div>div>div {
        background: white !important;
        color: #000000 !important;
    }
    /* Style for selectbox options */
    .stSelectbox>div>div>div>div>div {
        color: #000000 !important;
    }
    /* Style for selectbox label */
    .stSelectbox label {
        color: white !important;
    }
    /* Style for radio buttons */
    .stRadio>div {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    /* Special styling for hint button */
    .stButton>button[data-testid="hint-button"] {
        background: linear-gradient(135deg, #FFD700 0%, #FFA500 100%);
        border: none;
        color: white;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.2);
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        margin-bottom: 10px;
    }
    .stButton>button[data-testid="hint-button"]:hover {
        background: linear-gradient(135deg, #FFE44D 0%, #FFB347 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 15px rgba(0,0,0,0.15);
    }
    /* Style for hint section */
    [data-testid="hint-section"] {
        background: rgba(255, 255, 255, 0.2);
        padding: 20px;
        border-radius: 10px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        margin-bottom: 20px;
    }
    /* Style for hint history */
    [data-testid="hint-history"] {
        background: rgba(255, 255, 255, 0.15);
        padding: 15px;
        border-radius: 8px;
        margin-top: 10px;
    }
    /* Style for hint text (compact, high-clarity) */
    [data-testid="hint-text"] {
        font-size: 0.9em;
        line-height: 1.35;
        font-weight: 600;
        color: #111111;
        background: #fffdf5;
        padding: 5px 8px;
        border-radius: 6px;
        border: 1px solid rgba(0,0,0,0.08);
        margin: 3px 0;
        box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    }
    /* Timer styles */
    .timer {
        font-size: 1.5em;
        font-weight: bold;
        color: white;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.2);
        padding: 10px;
        border-radius: 10px;
        background: rgba(255, 255, 255, 0.1);
        text-align: center;
        margin: 10px 0;
    }
    /* Progress bar styles */
    .progress-bar {
        width: 100%;
        height: 10px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 5px;
        overflow: hidden;
        margin: 10px 0;
    }
    .progress-bar-fill {
        height: 100%;
        background: linear-gradient(90deg, #6FDFBF 0%, #A8D8F0 100%);
        transition: width 0.3s ease;
    }
    /* Animation for correct answer */
    @keyframes correct-answer {
        0% { transform: scale(1); }
        50% { transform: scale(1.1); }
        100% { transform: scale(1); }
    }
    .correct-answer {
        animation: correct-answer 0.5s ease;
    }
    /* Animation for wrong answer */
    @keyframes wrong-answer {
        0% { transform: translateX(0); }
        25% { transform: translateX(-5px); }
        75% { transform: translateX(5px); }
        100% { transform: translateX(0); }
    }
    .wrong-answer {
        animation: wrong-answer 0.5s ease;
    }
    /* Difficulty selector styles */
    .difficulty-selector {
        margin: 20px 0;
        padding: 15px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    /* Timer color variations */
    .timer-normal {
        color: #ffffff;
    }
    .timer-warning {
        color: #FFD700;
    }
    .timer-danger {
        color: #FF6B6B;
    }
    /* Add custom title styling */
    .game-title {
        font-family: 'Baloo 2', 'Poppins', 'Arial Black', Arial, sans-serif !important;
        font-size: 2.7em;
        font-weight: 700;
        letter-spacing: 0.08em;
        background: linear-gradient(90deg, #FF6B6B 0%, #FFD93D 50%, #4ECDC4 100%);
        color: #fff;
        text-align: center;
        padding: 28px 48px;
        margin: 28px auto 20px auto;
        border-radius: 28px;
        box-shadow: 0 10px 36px rgba(0, 0, 0, 0.16),
                    inset 0 -10px 0px rgba(0, 0, 0, 0.10);
        -webkit-text-stroke: 2px #222;
        text-stroke: 2px #222;
        text-shadow: 3px 3px 12px rgba(0,0,0,0.22),
                     0 3px 12px rgba(0,0,0,0.13);
        transition: box-shadow 0.2s, background 0.2s;
    }
    .game-title:hover {
        box-shadow: 0 16px 48px rgba(0,0,0,0.22),
                    0 2px 8px rgba(0,0,0,0.10);
        background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 50%, #4ECDC4 100%);
    }
    .game-title::before {
        content: "⬅️";
        font-size: 0.8em;
        position: static;
        transform: none;
    }
    .game-title::after {
        content: "➡️";
        font-size: 0.8em;
        position: static;
        transform: none;
    }
    @media (max-width: 768px) {
        .game-title {
            font-size: 2em;
            padding: 20px 30px;
            gap: 10px;
        }
        .game-title::before,
        .game-title::after {
            font-size: 0.6em;
        }
    }
    @media (max-width: 600px) {
        .stApp {
            padding: 0 !important;
            margin: 0 !important;
            width: 100vw !important;
            max-width: 100vw !important;
            overflow-x: auto !important;
        }
        [data-testid="column"] {
            padding: 4px !important;
            margin: 1px !important;
        }
        .wizword-banner {
            flex-direction: column !important;
            align-items: flex-start !important;
            padding: 8px 6px 8px 6px !important;
            margin: 6px 0 10px 0 !important;
        }
        .wizword-banner-title {
            font-size: 1.1em !important;
            margin-right: 0 !important;
            margin-bottom: 4px !important;
        }
        .wizword-banner-stats {
            gap: 7px !important;
            font-size: 0.95em !important;
        }
        .wizword-stat {
            min-width: 36px !important;
            padding: 2px 6px !important;
            font-size: 0.95em !important;
        }
        .stButton>button {
            font-size: 0.82em !important;
            padding: 0.22em 0.12em !important;
            min-width: 4.5em !important;
            max-width: 10em !important;
            height: 1.8em !important;
            margin: 0.03em !important;
            width: auto !important;
            display: inline-block !important;
            white-space: nowrap !important;
            text-overflow: ellipsis !important;
            overflow: hidden !important;
        }
        .letter-box-row {
            display: flex !important;
            flex-wrap: wrap !important;
            justify-content: center !important;
            gap: 0.08em !important;
            margin-bottom: 0.7em !important;
        }
        .letter-box {
            width: 1.7em !important;
            height: 1.7em !important;
            font-size: 1.2em !important;
            line-height: 1.7em !important;
            border-radius: 0.25em !important;
            margin: 0.04em !important;
            display: inline-flex !important;
            align-items: center !important;
            justify-content: center !important;
        }
        .wizword-banner-subtitle {
            font-size: 1em; /* Reduced from 1.45em */
            color: #fff;
            opacity: 0.98;
            letter-spacing: 0.07em;
            margin-top: 3px;
            padding: 0.15em 0.7em;
            border-radius: 0.7em;
            background: rgba(255,255,255,0.13);
            box-shadow: 0 1px 4px rgba(255,255,255,0.06);
            text-shadow: 0 1px 4px #FFD93D88, 0 1px 2px rgba(0,0,0,0.07);
            text-align: center;
            display: flex;
            justify-content: center;
            align-items: center;
        }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# Initialize session state with default values
if "game_state" not in st.session_state:
    st.session_state.game_state = {
        "word_length": 5,
        "subject": "general",  # Changed to lowercase to match WordSelector.CATEGORIES
        "mode": "Fun",
        "nickname": "",
        "score": 0,
        "total_points": 0,
        "questions_asked": [],
        "guesses_made": 0,
        "is_game_active": False,
        "game_instance": None,
        "rate_limit_warning": None,
        "is_loading": False,
        "victory_animation": False,
        "error_count": 0,  # Track consecutive errors
        "last_question_time": 0,  # Rate limiting
        "game_over": False,
        "final_guess_made": False,  # New flag to track if final guess was made
        "final_guess_result": None,  # Store the result of final guess
        "show_game_over": False,  # New flag to control game over screen
        "hint_count": 0,  # Track number of hints given
        "previous_hints": []
    }

def is_yes_no_question(question: str) -> tuple[bool, str]:
    """
    Validate if the question is a proper yes/no question.
    Returns (is_valid, error_message)
    """
    if not question:
        return False, "Question cannot be empty!"
    
    # Clean and lowercase the question
    question = question.strip().lower()
    
    # Check length
    if len(question) < 5:
        return False, "Question is too short. Please be more specific."
    
    if len(question) > 200:
        return False, "Question is too long. Please be more concise."
    
    # Check if it ends with a question mark
    if not question.endswith('?'):
        return False, "Question must end with a question mark (?)"
    
    # Common yes/no question starters
    starters = [
        r"^(is|are|does|do|can|could|will|would|has|have|had|should|must|may)",
        r"^(did|was|were)",
    ]
    
    # Check if it starts with yes/no question words
    if not any(re.match(pattern, question) for pattern in starters):
        return False, "Question must start with: Is, Are, Does, Do, Can, etc."
    
    return True, ""

def validate_word_length(length: int) -> tuple[bool, str]:
    """Validate word length with detailed feedback."""
    if not isinstance(length, int):
        return False, "Word length must be a number"
    # Our dictionary only supports 3-10 letter words
    if length < 3:
        return False, "Word length must be at least 3 letters"
    if length > 10:
        return False, "⚠️ Word length cannot exceed 10 letters in the current dictionary"
    return True, ""

def validate_subject(subject: str) -> tuple[bool, str]:
    """Validate the selected subject."""
    valid_categories = ["general", "animals", "food", "places", "science", "tech", "sports",
                       "movies", "music", "brands", "history", "random", "4th_grade", "8th_grade"]
    subject = subject.lower()  # Convert to lowercase for comparison
    if subject not in valid_categories:
        return False, f"Invalid subject. Must be one of: {', '.join(valid_categories)}"
    return True, ""

def check_rate_limit() -> tuple[bool, str]:
    """Check if user is asking questions too quickly."""
    current_time = time.time()
    last_question_time = st.session_state.game_state["last_question_time"]
    
    if current_time - last_question_time < 2:  # 2 seconds cooldown
        return False, "Please wait a moment before asking another question"
    return True, ""

def display_rate_limit_warning():
    """Display rate limit warning with enhanced UI."""
    warning = st.session_state.game_state.get("rate_limit_warning")
    if warning:
        if warning["level"] == "error":
            st.error(f"🚫 {warning['message']}")
        else:
            st.warning(f"⚠️ {warning['message']}")

def handle_api_response(response: dict) -> dict:
    """Handle API response and extract rate limit warnings."""
    if "_rate_limit_warning" in response:
        st.session_state.game_state["rate_limit_warning"] = response["_rate_limit_warning"]
        del response["_rate_limit_warning"]
    return response

def display_player_stats():
    """Display player statistics in the sidebar."""
    if st.session_state.game_state["game_instance"] and st.session_state.game_state["nickname"]:
        st.sidebar.markdown("---")
        st.sidebar.header("📊 Your Stats")
        
        player_stats = st.session_state.game_state["game_instance"].get_player_stats()
        if player_stats:
            col1, col2 = st.sidebar.columns(2)
            with col1:
                st.metric("Total Games", player_stats["total_games"])
                st.metric("Best Score", int(player_stats["best_score"]))
            with col2:
                st.metric("Avg Score", round(player_stats["avg_score"], 1))
                st.metric("Total Time", format_duration(player_stats["total_time"]))
            
            st.sidebar.markdown(f"**Favorite Category:** {player_stats['favorite_category']}")
            
            # Recent games
            if player_stats["recent_games"]:
                st.sidebar.markdown("**Recent Games**")
                for game in player_stats["recent_games"]:
                    st.sidebar.markdown(
                        f"- {game['subject']} ({game['word_length']} letters): "
                        f"Score {game['score']} ({format_duration(game['time_taken'])})"
                    )

def display_login():
    # --- Modern, Centered, Animated WizWord Banner ---
    st.markdown("""
    <div class='wizword-banner'>
      <div class='wizword-banner-title'>
        <span class="wizword-animated-text">WizWord</span>
      </div>
      <div class='wizword-banner-subtitle'>AI powered word guess game</div>
    </div>
    <style>
    @keyframes gradient-move {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pop {
        0% { transform: scale(1); }
        20% { transform: scale(1.12); }
        40% { transform: scale(0.98); }
        60% { transform: scale(1.06); }
        80% { transform: scale(0.99); }
        100% { transform: scale(1); }
    }
    .wizword-banner {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: linear-gradient(270deg, #FFD93D, #FF6B6B, #4ECDC4, #FFD93D);
        background-size: 600% 600%;
        animation: gradient-move 8s ease infinite;
        color: #fff;
        padding: 18px 8px 10px 8px;           /* Reduced padding */
        margin-bottom: 16px;                  /* Reduced margin */
        border-radius: 18px;                  /* Slightly smaller radius */
        border: 2px solid #fff7c2;            /* Thinner border */
        box-shadow: 0 3px 16px 0 rgba(255, 217, 61, 0.13), 0 1px 4px rgba(0,0,0,0.09);
        font-weight: 700;
        text-shadow: 0 1px 4px rgba(0,0,0,0.13), 0 1px 2px rgba(0,0,0,0.07);
        position: relative;
        overflow: hidden;
    }
    .wizword-banner-title {
        width: 100%;
        display: flex;
        justify-content: center;
        align-items: center;
        margin-bottom: 4px;                   /* Reduced margin */
    }
    .wizword-animated-text {
        font-family: 'Baloo 2', 'Poppins', 'Arial Black', Arial, sans-serif !important;
        font-size: 1.4em;                       /* 30% smaller */
        font-weight: 900;
        letter-spacing: 0.10em;
        background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 40%, #4ECDC4 80%, #FFD93D 100%);
        background-size: 200% auto;
        background-clip: text;
        -webkit-background-clip: text;
        color: transparent;
        -webkit-text-fill-color: transparent;
        filter: drop-shadow(0 0 8px #FFD93D88) drop-shadow(0 0 6px #4ECDC488);
        text-shadow: 0 0 12px #FFD93D, 0 0 16px #FF6B6B, 0 0 6px #4ECDC4, 1px 1px 6px rgba(0,0,0,0.13);
        animation: gradient-move 4s linear infinite, pop 2.5s cubic-bezier(.36,1.56,.64,1) infinite;
        text-align: center;
        margin: 0 auto;
        padding: 0 0.05em;
    }
    .wizword-banner-subtitle {
        font-size: 0.7em; /* 30% smaller */
        color: #fff;
        opacity: 0.98;
        letter-spacing: 0.07em;
        margin-top: 3px;
        padding: 0.15em 0.7em;
        border-radius: 0.7em;
        background: rgba(255,255,255,0.13);
        box-shadow: 0 1px 4px rgba(255,255,255,0.06);
        text-shadow: 0 1px 4px #FFD93D88, 0 1px 2px rgba(0,0,0,0.07);
        text-align: center;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    </style>
    """, unsafe_allow_html=True)

    # --- Custom Expander Header Style for Welcome and How to Play ---
    st.markdown("""
    <style>
    /* Improved: Target both expander header and parent for background and border */
    div[role="button"]:has(.streamlit-expanderHeader:has-text('Welcome to WizWord!')),
    div[role="button"]:has(.streamlit-expanderHeader:has-text('How to Play')),
    div[role="button"]:has(.streamlit-expanderHeader:has-text('📖 How to Play')),
    div[role="button"]:has(.st-expanderHeader:has-text('📖 How to Play')) {
        background: linear-gradient(135deg, #ffffff 0%, #e8f0ff 100%) !important;
        border: 1.5px solid #3b82f6 !important; /* blue border to differentiate */
        box-shadow: 0 3px 10px rgba(59,130,246,0.18), 0 1px 5px rgba(0,0,0,0.08) !important;
    }
    div[role="button"]:has(.streamlit-expanderHeader:has-text('Welcome to WizWord!')) .streamlit-expanderHeader,
    div[role="button"]:has(.streamlit-expanderHeader:has-text('How to Play')) .streamlit-expanderHeader,
    div[role="button"]:has(.streamlit-expanderHeader:has-text('📖 How to Play')) .streamlit-expanderHeader,
    div[role="button"]:has(.st-expanderHeader:has-text('Welcome to WizWord!')) .st-expanderHeader,
    div[role="button"]:has(.st-expanderHeader:has-text('How to Play')) .st-expanderHeader,
    div[role="button"]:has(.st-expanderHeader:has-text('📖 How to Play')) .st-expanderHeader {
        font-size: 1em !important;
        font-weight: 700 !important;
        color: #fff !important;
        opacity: 0.98 !important;
        letter-spacing: 0.07em !important;
        padding: 0.6em 1.2em !important;
        text-shadow: 0 1px 4px #FFD93D88, 0 1px 2px rgba(0,0,0,0.07) !important;
        background: transparent !important;
    }
    </style>
    """, unsafe_allow_html=True)
    # --- Top Menu (three-bar style) for login page ---
    if 'login_show_welcome' not in st.session_state:
        st.session_state['login_show_welcome'] = False
    if 'login_show_howto' not in st.session_state:
        st.session_state['login_show_howto'] = False
    with st.expander("☰ Menu", expanded=False):
        c1, c2 = st.columns(2)
        with c1:
            if st.button("Welcome to WizWord!", key="login_menu_welcome"):
                st.session_state['login_show_welcome'] = not st.session_state['login_show_welcome']
                st.rerun()
        with c2:
            if st.button("How to Play", key="login_menu_howto"):
                st.session_state['login_show_howto'] = not st.session_state['login_show_howto']
                st.rerun()

    # --- Introductory Section (conditional) ---
    if st.session_state['login_show_welcome']:
        st.markdown("""
        <div style='max-width: 700px; margin: 0 auto 2em auto; background: rgba(255,255,255,0.40); border-radius: 1.2em; padding: 1.5em 2em; box-shadow: 0 1px 8px rgba(255,255,255,0.08);'>
            <h2 style="text-align:center; color:#FF6B6B; margin-bottom:0.5em; font-size:1.8em;">Welcome to WizWord!</h2>
            <p style="text-align:center; color:#333; font-size:1.45em;">
                <b>WizWord</b> is a modern, AI-powered word guessing game that challenges your deduction skills and vocabulary. 
                Compete under different categories, ask clever questions, use hints, and race against the clock in Beat mode!
            </p>
            <ul style="margin-top:1em; font-size:1.25em;">
                <li><b>Wiz Mode:</b> Classic mode with stats and leaderboards.</li>
                <li><b>Beat Mode:</b> Timed challenge—solve as many words as possible before time runs out.</li>
            </ul>
            <p style="margin-top:1em; color:#444; font-size:1.5em;">
                 🧠 Train Your Brain the Fun Way!
                  Step into the magical world of WizWord, where every guess sharpens your mind, boosts your knowledge, and challenges your memory and logic — all while having fun!
         
        Whether you're a curious student, a word game enthusiast, or just looking to stretch your brain muscles, WizWord is your perfect companion for:
        
        ✅ Improving Vocabulary:
        Explore new words across themes like science, nature, geography, and more.
        
        ✅ Boosting Memory & Recall:
        Challenge your ability to remember spelling patterns and word associations with each round.
        
        ✅ Sharpening Analytical Thinking:
        Ask smart yes/no questions, analyze clues, eliminate possibilities — and outsmart the clock.
        
        ✅ Fun for All Ages:
        From quick 3-letter sprints to full 10-letter puzzles, WizWord adapts to every player.
        
        🧙‍♂️ With a magical theme, interactive animations, and a friendly wizard mascot, WizWord turns learning into an adventure!
        
        🎮 Play solo to test yourself — or challenge friends and beat the clock in "Beat Mode."
        🎯 Track your progress and celebrate your growing mastery with every word guessed.
        
        Ready to boost your brainpower — one word at a time?
        Let the game begin! ✨
            </p>
        </div>
        """, unsafe_allow_html=True)

    # --- How to Play (conditional) ---
    if st.session_state['login_show_howto']:
        st.markdown(f"""
        ### Game Instructions:
        - Choose your game mode:
        
            - **Wiz**: Classic mode with stats and leaderboards.
            - **Beat**: Default mode. Timed challenge—solve as many words as possible before time runs out.
        - Click Start to begin  or change word category , pick 'any' for a random challenge.
        - Ask yes/no questions or request hints to help you guess the word.
        - Enter your guess at any time.
        **Beat Mode Details:**
        - You have {int(os.getenv('BEAT_MODE_TIME', 300))} seconds to play.
        - For each word, you can:
            - **Guess the word:**
                - Correct: **+100**
                - Wrong: **-10**
            - **Ask yes/no questions:** **-1** each
            - **Request hints:** **-10** each (max 3 per word)
            - Skip: reveals the word for 2 seconds, then loads the next word (no additional penalty)
        - Try to solve as many words as possible and maximize your score before time runs out!
        - Only Medium difficulty is available for all modes.
            - Note: Some categories (e.g., Movies, Music, Aviation) may include alphanumeric titles like "Se7en" or "Rio2". Only letters count toward vowel/uniqueness checks.
        
        #### Personal Category (Profile‑aware)
        - When you choose **Personal**, the game uses your profile (Bio, Occupation, Education) to ask the LLM for a single, personally relevant noun and a set of tailored hints.
        - The UI blocks with “Generating personal hints…” until at least 3 hints are available. If not enough hints are ready in time, you’ll see a clear warning and a **Retry generating hints** button.
        
        #### Top SEI Achievements
        - Achieve (or tie) the highest SEI in a category (with SEI > 0) to unlock:
          - An emailed congratulations card (with trophy, your username, category, SEI, and UTC timestamp)
          - An in-app celebration: a flying trophy, rising banner, and balloons that auto‑dismiss

          #### Game Over Page
          - Summary: Final score, time taken, and total penalty points.
          - Statistics: Running Avg Score/Word and Time/Word vs game date; SEI line graph; includes the current game's point.
          - Leaderboard: Global Top 10 by SEI (with dates) for the current category; header shows your SEI.
          - Share: Generate and download a share card (with QR) and share to social networks.
          - My Stats & Leaderboard: Personal historical stats and per‑category leaderboard.
        """)

    # State for which form to show
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'

    # --- LOGIN FORM ---
    if st.session_state['auth_mode'] == 'login':
        # Quick access Create Account button above the login card
        c_top = st.columns([1,1,1])
        with c_top[1]:
            if st.button("Create Account", key="create_account_top"):
                st.session_state['auth_mode'] = 'register'
                st.session_state['login_error'] = ""
                st.rerun()
        # Tighten spacing below the top button
        st.markdown("""
        <style>
        /* Pull the login form up further */
        div[data-testid=\"stForm\"] { margin-top: -58px !important; }
        </style>
        """, unsafe_allow_html=True)
        # Modern login card UI
        st.markdown("""
        <style>
        .auth-card {
            max-width: 430px;
            margin: 2px auto 4px auto;
            background: rgba(15,17,25,0.92);
            backdrop-filter: blur(6px);
            -webkit-backdrop-filter: blur(6px);
            border-radius: 16px;
            border: 1px solid rgba(255,255,255,0.35);
            box-shadow: 0 10px 26px rgba(0,0,0,0.12), 0 2px 6px rgba(0,0,0,0.08);
            padding: 8px 10px 8px 10px;
        }
        .auth-title {
            font-family: 'Poppins', 'Baloo 2', system-ui, -apple-system, Segoe UI, Roboto, sans-serif;
            font-size: 1.35em;
            font-weight: 800;
            letter-spacing: 0.04em;
            background: linear-gradient(90deg, #FF6B6B 0%, #FFD93D 50%, #4ECDC4 100%);
            -webkit-background-clip: text; background-clip: text;
            -webkit-text-fill-color: transparent; color: transparent;
            text-align: center;
            margin: 2px 0 6px 0;
        }
        .auth-subtitle {
            text-align: center; color: #333; opacity: 0.85;
            font-size: 0.92em; margin-bottom: 8px;
        }
        .auth-sep { height: 4px; }
        .auth-muted { text-align:center; font-size:0.86em; color:#333; opacity:0.8; }
        .auth-link { color:#1c64f2; text-decoration: none; font-weight:700; }
        .auth-actions { display:flex; gap:8px; }
        .auth-actions .stButton>button { height: 2.4em; }
        .auth-primary .stButton>button {
            background: linear-gradient(90deg, #6FDFBF 0%, #A8D8F0 100%) !important;
            color: #222 !important; border: none !important; font-weight: 800 !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.10) !important;
        }
        .auth-secondary .stButton>button {
            background: rgba(0,0,0,0.06) !important; color:#222 !important; border: 1px solid rgba(0,0,0,0.12) !important;
        }
        .auth-card .stTextInput>div>div>input { padding: 0.45em 0.55em; margin-top: -2px; }
        .auth-spacer { height: 6px; }
        </style>
        """, unsafe_allow_html=True)

        # Teal gradient styling for primary Sign In button; lighter style for secondary actions
        st.markdown(
            """
            <style>
            /* Primary Sign In: first button inside the login form */
            div[data-testid="stForm"] form button:first-of-type {
              background: linear-gradient(135deg, #06b6d4 0%, #22d3ee 50%, #34d399 100%) !important;
              color: #0b1220 !important;
              font-weight: 800 !important;
              border: none !important;
              border-radius: 10px !important;
              box-shadow: 0 8px 18px rgba(34, 211, 238, 0.25) !important;
            }
            div[data-testid="stForm"] form button:first-of-type:hover {
              filter: brightness(1.05);
              transform: translateY(-1px);
              box-shadow: 0 10px 22px rgba(34, 211, 238, 0.32) !important;
            }
            /* Secondary buttons: all other form buttons */
            div[data-testid="stForm"] form button:not(:first-of-type) {
              background: rgba(255,255,255,0.06) !important;
              color: #e6e6e6 !important;
              border: 1px solid rgba(255,255,255,0.16) !important;
              font-weight: 700 !important;
              border-radius: 10px !important;
              box-shadow: none !important;
            }
            div[data-testid="stForm"] form button:not(:first-of-type):hover {
              background: rgba(255,255,255,0.10) !important;
            }
            </style>
            """,
            unsafe_allow_html=True,
        )

        # Show error if present (ALWAYS before the form)
        if st.session_state.get('login_error'):
            st.error(st.session_state['login_error'])
        with st.form("login_form", clear_on_submit=False):
            # Inputs inside the card
            with st.container():
                st.markdown("<div class='auth-spacer'></div>", unsafe_allow_html=True)
                username = st.text_input(" ", key="login_username", placeholder="Username")
                password = st.text_input(" ", type="password", key="login_password", placeholder="Password")
                st.markdown("<div class='auth-spacer'></div>", unsafe_allow_html=True)
                # Primary action
                with st.container():
                    with st.container():
                        login_btn = st.form_submit_button("Sign In", use_container_width=True)
                                # Secondary actions
                st.markdown("<div class='auth-sep'></div>", unsafe_allow_html=True)
                c1, c2 = st.columns(2)
                with c1:
                    if st.form_submit_button("Create account", use_container_width=True):
                        st.session_state['auth_mode'] = 'register'
                        st.session_state['login_error'] = ""
                        st.rerun()
                with c2:
                    if st.form_submit_button("Forgot password?", use_container_width=True):
                        st.session_state['auth_mode'] = 'forgot'
                        st.session_state['login_error'] = ""
                        st.rerun()
            if login_btn:
                users = st.session_state['users']
                username_lower = (username or "").strip().lower()
                if username_lower in users and users[username_lower]['password'] == (password or '').strip():
                    st.session_state.user = dict(users[username_lower])
                    st.session_state.user['username'] = username_lower
                    st.session_state.logged_in = True
                    st.session_state['login_error'] = ""
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.session_state['login_error'] = "Invalid username or password."
                    st.session_state['login_failed'] = True
                    st.rerun()
            # Reset the login_failed flag after displaying the error
            if st.session_state.get('login_failed', False):
                st.session_state['login_failed'] = False

    # --- REGISTER FORM ---
    elif st.session_state['auth_mode'] == 'register':
        st.markdown("## Register")
        new_username = st.text_input("Choose a username", key="register_username")
        new_email = st.text_input("Email", key="register_email")
        # Live email format feedback
        _entered_email = (new_email or "").strip()
        if _entered_email:
            import re as _re
            if not _re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", _entered_email):
                st.warning("Please enter a valid email address (e.g., name@example.com).")
        new_password = st.text_input("Choose a password", type="password", key="register_password")
        # Add compulsory birthday and education fields
        import datetime
        min_birthday = datetime.date(1900, 1, 1)
        birthday = st.date_input("Birthday (required)", value=datetime.date(2000, 1, 1), min_value=min_birthday, key="register_birthday")
        education_options = [
            'Student', 'High School', 'Bachelor', 'Master', 'PhD', 'Other'
        ]
        education = st.selectbox('Education (required)', education_options, key="register_education")
        bio = st.text_area(
            f"Bio (optional – up to {BIO_MAX_CHARS} characters)",
            key="register_bio_v2",
            help="Tell others a little about yourself; interests, background, etc.",
            max_chars=BIO_MAX_CHARS,
            placeholder=f"Up to {BIO_MAX_CHARS} characters"
        )
        _bio_len = len(bio or "")
        st.caption(f"{_bio_len}/{BIO_MAX_CHARS} characters")
        if _bio_len > BIO_MAX_CHARS:
            st.warning(f"Bio exceeds {BIO_MAX_CHARS} characters; please shorten it.")
        elif _bio_len >= BIO_MAX_CHARS:
            st.warning(f"Bio reached the {BIO_MAX_CHARS}-character limit.")
        elif _bio_len >= int(BIO_MAX_CHARS * 0.9):
            st.info("Approaching the 90% character limit.")
        register_btn = st.button("Register", key="register_btn")
        if st.button("Back to Login", key="back_to_login_from_register"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
        if register_btn:
            users = st.session_state['users']
            # Strip whitespace
            u_name = (new_username or "").strip()
            u_email = (new_email or "").strip()
            u_pass = (new_password or "").strip()
            u_edu = (education or "").strip()
            u_bio = (bio or "").strip()
            new_username_lower = u_name.lower()
            # Per-field validation
            missing = []
            if not u_name: missing.append("username")
            if not u_email: missing.append("email")
            if not u_pass: missing.append("password")
            if not birthday: missing.append("birthday")
            if not u_edu: missing.append("education")
            if missing:
                st.error("Please enter: " + ", ".join(missing) + ".")
            else:
                # Basic email format validation
                import re as _re
                email_ok = bool(_re.match(r"^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$", u_email))
                if not email_ok:
                    st.error("Please enter a valid email address (e.g., name@example.com).")
                elif new_username_lower in users:
                    st.error("Username already exists.")
                elif any((u.get('email') or '').lower() == u_email.lower() for u in users.values()):
                    st.error("Email already registered.")
                else:
                    users[new_username_lower] = {
                        'password': u_pass,
                        'email': u_email,
                        'birthday': str(birthday),
                        'education': u_edu,
                        'bio': u_bio
                    }
                    st.session_state['users'] = users
                    save_users(users)
                    # Increment users_count on successful registration
                    update_global_counters(users_delta=1)
                    st.success("Registration successful! Please log in.")
                    st.session_state['auth_mode'] = 'login'
                    save_users(st.session_state['users'])
                    st.rerun()

    # --- FORGOT PASSWORD FORM ---

    elif st.session_state['auth_mode'] == 'forgot':
        st.markdown("## Forgot Password")
        forgot_username = st.text_input("Enter your username", key="forgot_username")
        if st.button("Back to Login", key="back_to_login_from_forgot"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
        if st.button("Reset Password", key="reset_password_btn"):
            users = st.session_state['users']
            forgot_username_lower = forgot_username.lower()
            if forgot_username_lower in users:
                # Only generate and store the code if not already set for this user
                if st.session_state.get('reset_user') != forgot_username_lower:
                    reset_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))
                    st.session_state['reset_code'] = reset_code
                    st.session_state['reset_user'] = forgot_username_lower
                    send_reset_email(users[forgot_username_lower]['email'], reset_code)
                st.success(f"Password reset code sent to {users[forgot_username_lower]['email']}. Please check your email.")
                st.session_state['auth_mode'] = 'reset'
                st.rerun()
            else:
                st.error("Username not found.")

    elif st.session_state['auth_mode'] == 'reset':
        st.markdown("## Reset Password")
        code_entered = st.text_input("Enter the reset code sent to your email", key="reset_code_input")
        new_password = st.text_input("Enter your new password", type="password", key="new_password_input")
        # Debug print
        # st.write(f"DEBUG: Expected code: {st.session_state.get('reset_code')}, Entered: {code_entered}")
        if st.button("Set New Password", key="set_new_password_btn"):
            user = st.session_state.get('reset_user')
            if code_entered == st.session_state.get('reset_code'):
                if user and user in st.session_state['users']:
                    st.session_state['users'][user]['password'] = new_password
                    save_users(st.session_state['users'])
                    st.success("Password reset successful! Please log in.")
                    # Clean up reset state
                    st.session_state['auth_mode'] = 'login'
                    st.session_state.pop('reset_code', None)
                    st.session_state.pop('reset_user', None)
                    st.rerun()
                else:
                    st.error("User not found.")
            else:
                st.error("Invalid reset code.")
        if st.button("Back to Login", key="back_to_login_from_reset"):
            st.session_state['auth_mode'] = 'login'
            st.session_state.pop('reset_code', None)
            st.session_state.pop('reset_user', None)
            st.rerun()

def main():
    """Main application entry point."""
    # Bootstrap aggregates on first run
    try:
        ensure_aggregates_bootstrap()
    except Exception:
        pass
    # Show login page if not logged in
    if not st.session_state.get('logged_in', False):
        display_login()
        return
# --- Admin-only: Display all user profiles ---
    if st.session_state.get('user', {}).get('username', '').lower() == 'admin':
        st.sidebar.markdown('---')
        # Admin dashboard counters (sidebar)
        counters = _load_global_counters()
        st.sidebar.markdown("### Admin Stats")
        # Show the actual number of registered accounts from users.json (authoritative)
        actual_users = len(st.session_state.get('users', {}))
        if counters.get('users_count') != actual_users:
            counters['users_count'] = actual_users
            _save_global_counters(counters)
        st.sidebar.metric("Users", actual_users)
        # Live sessions = active sessions by heartbeat in last 2 minutes
        try:
            _live = count_active_live_sessions(window_seconds=120)
        except Exception:
            _live = 0
        st.sidebar.metric("Live Sessions", _live)
        # Optional auto-refresh for admin stats
        auto_refresh = st.sidebar.checkbox("Auto-refresh stats", value=True, key="admin_auto_refresh")
        if auto_refresh:
            try:
                import time as _t
                last = float(st.session_state.get('_admin_refresh_ts', 0))
                now = _t.time()
                if now - last >= 5:
                    st.session_state['_admin_refresh_ts'] = now
                    st.experimental_rerun()
            except Exception:
                pass
        total_secs = counters.get('total_game_time_seconds', 0)
        hours = total_secs // 3600
        minutes = (total_secs % 3600) // 60
        st.sidebar.metric("Global Game Time", f"{hours}h {minutes}m")
        st.sidebar.metric("Total Sessions", counters.get('total_sessions', 0))
        # Make sidebar metric values clearly visible in red
        st.sidebar.markdown(
            """
            <style>
            section[data-testid="stSidebar"] [data-testid="stMetricValue"] {
              color: #ff3b30 !important; /* vivid red */
              text-shadow: 0 1px 2px rgba(0,0,0,0.15);
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Toggle profiles at bottom of Beat start page
        if 'show_all_users_profiles' not in st.session_state:
            st.session_state['show_all_users_profiles'] = False
        if st.sidebar.button('Display All User Profiles', key='admin_show_users'):
            st.session_state['show_all_users_profiles'] = not st.session_state['show_all_users_profiles']

    if 'game' not in st.session_state or not st.session_state.game or getattr(st.session_state.game, 'mode', None) != 'Beat':
        random_length = random.randint(3, 10)
        user_profile = st.session_state.get('user', {})
        default_category = user_profile.get('default_category', 'general')
        # Enforce env gate here, too (start page auto-initialization)
        _enable_personal_gate = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
        if not _enable_personal_gate and str(default_category).lower() == 'personal':
            default_category = 'general'
            try:
                if 'user' in st.session_state and st.session_state['user']:
                    st.session_state['user']['default_category'] = 'general'
                users_db = st.session_state.get('users', {})
                uname = (st.session_state.get('user', {}) or {}).get('username') or ''
                if uname in users_db:
                    users_db[uname]['default_category'] = 'general'
                    save_users(users_db)
                elif uname.lower() in users_db:
                    users_db[uname.lower()]['default_category'] = 'general'
                    save_users(users_db)
            except Exception:
                pass
        subject = default_category if default_category else 'general'
        
        st.session_state.game = GameLogic(
            word_length=random_length,  # Use random length between 3 and 10
            subject=subject,
            mode='Beat',
            nickname=st.session_state.user['username'],
            difficulty='Medium'
        )
        # Increment total sessions (lifetime) and current live sessions
        update_global_counters(sessions_delta=1, live_sessions_delta=1)
        # Create a stable live session id for heartbeats
        try:
            import uuid as _uuid
            st.session_state['live_session_id'] = st.session_state.get('live_session_id') or str(_uuid.uuid4())
        except Exception:
            pass
        st.session_state.game_over = False
        st.session_state.game_summary = None
        st.session_state.beat_word_count = 0
        st.session_state.beat_time_left = 0
        st.session_state['game_saved'] = False
        # Reset Beat session accumulators for a fresh run
        st.session_state['beat_total_points'] = 0
        st.session_state['beat_total_penalty'] = 0
    # Always go directly to the game page
    # Heartbeat for live session tracking (throttled ~10s); skip admin
    try:
        import time as _t
        sid = st.session_state.get('live_session_id') or st.session_state.get('current_round_id')
        if not sid:
            import uuid as _uuid
            sid = str(_uuid.uuid4())
            st.session_state['live_session_id'] = sid
        if st.session_state.get('user', {}).get('username', '').lower() != 'admin':
            last_hb = st.session_state.get('_last_live_hb', 0)
            if _t.time() - float(last_hb) >= 10:
                heartbeat_live_session(session_id=sid, username=st.session_state.user['username'])
                st.session_state['_last_live_hb'] = _t.time()
    except Exception:
        pass
    display_game()

def display_welcome():
        # If the game is over, show only the game over page
    if st.session_state.get('game_over', False):
        display_game_over(st.session_state.get('game_summary', {}))
        return

    ensure_beat_mode_state()
    if "game" not in st.session_state:
        st.error("No active game found. Please start a new game.")
        return
    if st.session_state.get('game_over', False):
        display_game_over(st.session_state.get('game_summary', {}))
        return
    """Display the welcome screen and game setup."""
    if st.session_state.get('game'):
        # Even if a game is active, show a compact Top 10 SEI for the current category
        try:
            current_cat = getattr(st.session_state.game, 'subject', None)
            if current_cat:
                all_games = get_all_game_results()
                user_highest_sei = {}
                for g in all_games:
                    if (g.get('subject', '') or '').lower() != str(current_cat).lower():
                        continue
                    score = g.get('score', 0)
                    time_taken = g.get('time_taken', g.get('duration', 0))
                    words = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
                    denom = max(int(words or 0), 1)
                    avg_score = score / denom
                    avg_time = time_taken / denom
                    sei = avg_score / avg_time if avg_time > 0 else None
                    if sei is None:
                        continue
                    user = (g.get('nickname', '') or '').lower()
                    if user not in user_highest_sei or sei > user_highest_sei[user]:
                        user_highest_sei[user] = sei
                top3 = sorted(user_highest_sei.items(), key=lambda x: x[1], reverse=True)[:3]
                nice_cat = str(current_cat).replace('_',' ').title()
                st.markdown(f"""
                <div style='font-size:1.0em; font-weight:700; color:#fff; margin:0.5em 0 0.25em 0;'>
                    🏆 Global Top 3 by SEI — {nice_cat}
                </div>
                """, unsafe_allow_html=True)
                if top3:
                    st.table([{ 'User': u, 'Highest SEI': round(v, 2) } for u, v in top3])
                else:
                    st.info("No games available yet for this category.")
        except Exception:
            pass
        return  # Defensive: never show settings if a game is active
    if not st.session_state.get('user'):
        # Show WizWord banner with only the title (no high score message)
        st.markdown("""
        <div class='wizword-banner'>
          <div class='wizword-banner-title'>WizWord</div>
        </div>
        <style>
        .wizword-banner {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            background: linear-gradient(90deg, #4ECDC4 0%, #FFD93D 100%);
            color: #222;
            padding: 14px 10px 10px 10px;
            margin-bottom: 18px;
            border-radius: 16px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
            font-weight: 700;
        }
        .wizword-banner-title {
            font-family: 'Baloo 2', 'Poppins', 'Arial Black', Arial, sans-serif !important;
            font-size: 2em;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin-bottom: 4px;
        }
        </style>
        """, unsafe_allow_html=True)
        return
    # If logged in, show welcome and high score
    st.markdown(f"<div style='text-align:center; margin-bottom:10px;'><b>Welcome, {st.session_state.user['username']}!</b></div>", unsafe_allow_html=True)
    session_manager = SessionManager()

    #st.markdown(high_score_html, unsafe_allow_html=True)
    # --- End WizWord Banner with Global High Score ---
    if st.session_state.get('game'):
        return  # Defensive: never show settings if a game is active
    # Remove the second welcome message here
    st.markdown("<div class='game-title'>WizWord</div>", unsafe_allow_html=True)
    st.markdown("""
    <div style='text-align:center; margin-top:-18px; margin-bottom:18px;'>
        <span style='font-size:1.1em; color:#fff; opacity:0.85; letter-spacing:0.04em;'>AI powered word guess game</span>
    </div>
    """, unsafe_allow_html=True)
    # Create two columns
    left_col, right_col = st.columns([1, 1])  # Equal width columns
    # Left column - Game Settings
    with left_col:
        st.markdown("### ⚙️ Game Settings")
        with st.form("game_setup", clear_on_submit=False):
            start_col = st.columns([1])[0]
            start_pressed = start_col.form_submit_button(
                "🎯 Start!" if st.session_state.get('game_mode', 'Fun') == "Wiz" else "🎯 Start Game!",
                use_container_width=True
            )
            cols = st.columns([2, 2])  # [Game Mode, Category]
            with cols[0]:
                mode = st.selectbox(
                    "Game Mode",
                    options=["Fun", "Wiz", "Beat"],
                    help="Wiz mode includes scoring and leaderboards",
                    index=0,
                    key="game_mode"
                )
            difficulty = "Medium"
            with cols[1]:
                enable_personal = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
                category_options = [
                    "any", "4th_grade", "8th_grade", "anatomy", "animals", "brands", "cities", "food",
                    "general", "gre", "medicines", "places", "psat", "sat", "science", "sports", "tech"
                ]
                if enable_personal:
                    category_options.insert(1, "Personal")
                subject = st.selectbox(
                    "Category",
                    options=category_options,
                    index=category_options.index("general"),  # default to 'general'
                    help="Word category (select 'any' for random category)",
                    format_func=lambda x: (
                        'Any' if x == 'any' else (
                            'Personal' if x == 'Personal' else (
                                'SAT' if x == 'sat' else (
                                    'PSAT' if x == 'psat' else (
                                        'GRE' if x == 'gre' else (
                                            '4th Grade' if x == '4th_grade' else (
                                                '8th Grade' if x == '8th_grade' else x.replace('_', ' ').title()
                                            )
                                        )
                                    )
                                )
                            )
                        )
                    )
                )
                st.session_state['original_category_choice'] = subject
                # Enforce env gate in case subject came from stale state (do this BEFORE resolving)
                _enable_personal_login = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
                if not _enable_personal_login and str(subject).lower() == 'personal':
                    subject = 'general'
                    st.session_state['original_category_choice'] = subject
                # Now resolve the effective subject for this run
                resolved_subject = random.choice(["general", "animals", "food", "places", "science", "tech", "sports", "brands", "4th_grade", "8th_grade", "cities", "medicines", "anatomy", "psat", "sat", "gre"]) if subject == "any" else subject
                # --- Global Top 3 by SEI for chosen category (start page) ---
                try:
                    all_games = get_all_game_results()
                    chosen_cat = subject.lower()
                    # Build per-user highest SEI in this category (or all if 'any')
                    user_highest_sei = {}
                    for g in all_games:
                        game_cat = (g.get('subject', '') or '').lower()
                        if chosen_cat != 'any' and game_cat != chosen_cat:
                            continue
                        score = g.get('score', 0)
                        time_taken = g.get('time_taken', g.get('duration', 0))
                        words = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
                        denom = max(int(words or 0), 1)
                        avg_score = score / denom
                        avg_time = time_taken / denom
                        sei = avg_score / avg_time if avg_time > 0 else None
                        if sei is None:
                            continue
                        user = (g.get('nickname', '') or '').lower()
                        if user not in user_highest_sei or sei > user_highest_sei[user]:
                            user_highest_sei[user] = sei
                    # Sort and present top 3
                    top3 = sorted(user_highest_sei.items(), key=lambda x: x[1], reverse=True)[:3]
                    nice_cat = ('All Categories' if chosen_cat == 'any' else subject.replace('_',' ').title())
                    st.markdown(f"""
                    <div style='font-size:1.0em; font-weight:700; color:#fff; margin:0.5em 0 0.25em 0;'>
                        🏆 Global Top 3 by SEI — {nice_cat}
                    </div>
                    """, unsafe_allow_html=True)
                    if top3:
                        st.table([{ 'User': u, 'Highest SEI': round(v, 2) } for u, v in top3])
                    else:
                        st.info("No games available yet for this category.")
                except Exception:
                    pass
            word_length = "any"
            st.session_state['original_word_length_choice'] = word_length
            if start_pressed:
                selected_mode = st.session_state.get("game_mode", mode)
                st.session_state.game = GameLogic(
                    word_length=word_length,
                    subject=resolved_subject,
                    mode=selected_mode,
                    nickname=st.session_state.user['username'],
                    difficulty=difficulty
                )
                st.markdown("""
                    <script>
                        window.parent.scrollTo({top: 0, behavior: 'smooth'});
                    </script>
                """, unsafe_allow_html=True)
                st.rerun()
        # End of form block

        # --- Global Top 3 by SEI for chosen category (outside form for visibility) ---
        try:
            # Use user's default category for Top 3 (fallback to 'any' and then running category)
            user_profile = st.session_state.get('user', {})
            chosen_cat = (user_profile.get('default_category') or 'any').lower()
            top3_rows = get_top10_from_aggregates(chosen_cat)[:3]
            if (not top3_rows) and chosen_cat != 'any':
                top3_rows = get_top10_from_aggregates('any')[:3]
            if (not top3_rows) and 'game' in st.session_state and st.session_state.game:
                top3_rows = get_top10_from_aggregates(getattr(st.session_state.game, 'subject', 'any')).copy()[:3]
            # Final fallback: pick a populated category from aggregates
            if not top3_rows:
                try:
                    agg = _load_aggregates()
                    cat_map = agg.get('category_user_highest', {})
                    for cat_key, users in cat_map.items():
                        if users:
                            cand = get_top10_from_aggregates(cat_key)[:3]
                            if cand:
                                chosen_cat = cat_key
                                top3_rows = cand
                                break
                except Exception:
                    pass
            # Debug output for diagnosing empty tables
            try:
                import os, logging
                _dbg = os.getenv('DEBUG_TOP3', '').strip().lower() in ('1','true','yes','on')
                cats = []
                try:
                    _agg = _load_aggregates()
                    cats = list((_agg.get('category_user_highest') or {}).keys())
                except Exception:
                    pass
                if _dbg and not st.session_state.get('top3_debug_done'):
                    _agg_exists = os.path.exists(AGGREGATES_PATH)
                    _agg_size = os.path.getsize(AGGREGATES_PATH) if _agg_exists else 0
                    _msg = f"[TOP3] chosen_cat={chosen_cat}, cats={cats}, rows={len(top3_rows)} AGG_PATH={AGGREGATES_PATH} exists={_agg_exists} size={_agg_size}"
                    logging.info(_msg)
                    st.caption(f"DEBUG TOP3: chosen_cat={chosen_cat}, cats={cats}, rows={len(top3_rows)}")
                    st.caption(f"DEBUG TOP3: AGG_PATH={AGGREGATES_PATH}, exists={_agg_exists}, size={_agg_size}")
                    if not top3_rows:
                        st.caption("DEBUG TOP3: No rows found after fallbacks")
                    else:
                        st.caption(f"DEBUG TOP3: First row sample: {top3_rows[0]}")
                    st.session_state['top3_debug_done'] = True
            except Exception:
                pass
            nice_cat = (chosen_cat.replace('_',' ').title())
            st.markdown(f"""
            <div style='font-size:1.0em; font-weight:700; color:#fff; margin:0.5em 0 0.25em 0;'>
                🏆 Global Leaderboard (Top 3 by SEI) - {nice_cat}
            </div>
            """, unsafe_allow_html=True)
            if top3_rows:
                st.table(top3_rows)
            else:
                st.info("No games available yet for this category.")
        except Exception as e:
            
            st.info("Unable to render Top 10 at the moment. Check logs for details.")

        # Toggleable High Score Monthly History
        if "show_high_score_history" not in st.session_state:
            st.session_state.show_high_score_history = False

        if st.button("🏆 High Score Monthly History", key="show_high_score_history_btn"):
            st.session_state.show_high_score_history = not st.session_state.show_high_score_history

        if st.session_state.show_high_score_history:
            with st.expander("Global Monthly Highest Score History", expanded=True):
                # Show previous months' high scores for ALL modes and ALL categories
                from datetime import datetime
                session_manager = SessionManager()
                all_games = session_manager._get_local_games()
                year = datetime.now().strftime('%Y')
                monthly_scores = {}
                for g in all_games:
                    ts = g.get('timestamp', '')
                    if g.get('game_over', False) and ts.startswith(year):
                        month = ts[:7]  # YYYY-MM
                        if month not in monthly_scores or g['score'] > monthly_scores[month]['score']:
                            monthly_scores[month] = {
                                'score': g['score'],
                                'nickname': g.get('nickname', ''),
                                'mode': g.get('mode', ''),
                                'subject': g.get('subject', ''),
                            }
                for month in sorted(monthly_scores.keys(), reverse=True):
                    entry = monthly_scores[month]
                    st.markdown(
                        f"**{month}**: 🌍 Global Highest Score ({entry['mode']}, {entry['subject'].title()}): "
                        f"<span style='color:#FF6B6B;'>{entry['score']}</span> by "
                        f"<span style='color:#222;'>{entry['nickname']}</span>",
                        unsafe_allow_html=True
                    )
        # Add Exit button below the form
        if st.button("🚪 Exit", key="exit_btn"):
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()
    # Right column - Instructions
    with right_col:
        st.markdown("""
        ### Quick Start 🚀
        1. Select your game mode (Fun, Wiz, or Beat)
        2. Choose a word category (or pick 'any' for random)
        3. Click 'Start Game' to begin!
        """)
        with st.expander("📖 How to Play", expanded=False):
            st.markdown(f"""
            ### Game Instructions:
            - Choose your game mode:
                - **Fun**: Unlimited play, no timer, just for fun.
                - **Wiz**: Classic mode with stats and leaderboards.
                - **Beat**: The default  mode. Timed challenge—solve as many words as possible before time runs out.
            - Select a word category, or pick 'any' for a random challenge.
            - Ask yes/no questions or request hints to help you guess the word.
            - Enter your guess at any time.
            **Beat Mode Details:**
            - You have {int(os.getenv('BEAT_MODE_TIME', 300))} seconds to play.
            - For each word, you can:
                - **Guess the word:**
                    - Correct: **+100**
                    - Wrong: **-10**
                - **Ask yes/no questions:** **-1** each
                - **Request hints:** **-10** each (max 3 per word)
                - Skip: reveals the word for 2 seconds, then loads the next word (no additional penalty)
            - Try to solve as many words as possible and maximize your score before time runs out!
            - Only Medium difficulty is available for all modes.
            - Note: Some categories (e.g., Movies, Music, Aviation) may include alphanumeric titles like "Se7en" or "Rio2". Only letters count toward vowel/uniqueness checks.

            #### Personal Category (Profile‑aware)
            - When you choose **Personal**, the game uses your profile (Bio, Occupation, Education) to ask the LLM for a single, personally relevant noun and a set of tailored hints.
            - The UI blocks with “Generating personal hints…” until at least 3 hints are available. If not enough hints are ready in time, you’ll see a clear warning and a **Retry generating hints** button.
            
            #### Top SEI Achievements
            - Achieve (or tie) the highest SEI in a category (with SEI > 0) to unlock:
              - An emailed congratulations card (with trophy, your username, category, SEI, and UTC timestamp)
                        - An in-app celebration: a flying trophy, rising banner, and balloons that auto‑dismiss

        #### Game Over Page
        - Summary: Final score, time taken, and total penalty points.
        - Statistics: Running Avg Score/Word and Time/Word vs game date; SEI line graph; includes the current game's point.
        - Leaderboard: Global Top 10 by SEI (with dates) for the current category; header shows your SEI.
        - Share: Generate and download a share card (with QR) and share to social networks.
        - My Stats & Leaderboard: Personal historical stats and per‑category leaderboard.
        """)
        with st.expander("💡 Hints System", expanded=False):
            st.markdown("""
            - Easy Mode: Up to 10 hints available (-5 points each)
            - Medium Mode: Up to 7 hints available (-10 points each)
            - Hard Mode: Up to 5 hints available (-15 points each)
            - **Beat Mode:** Up to 3 hints available (-10 points each)
            """)
        with st.expander("🎯 Scoring", expanded=False):
            st.markdown("""
            ### Medium Difficulty (Only Option)
            - 3 hints available per word in Beat mode
            - Questions: **-1** point each
            - Hints: **-10** points each
            - Wrong guesses: **-10** points
            - Skip word: **-10** points (loads a new word)
            - Correct guess: **+20 × word length**
            - 5 minutes to solve as many words as possible in Beat mode
            - Try to maximize your score before time runs out!
            """)
        with st.expander("💭 Tips & Strategy", expanded=False):
            st.markdown("""
            - Use hints strategically—they cost more points than questions
            - In Beat mode, time is limited—work quickly and don't get stuck on one word
            - Keep track of your score before making guesses
            - Questions are cheaper than wrong guesses
            """)


def display_game():
    # Early debug: confirm we entered display_game and show Beat state
    try:
        import logging, os
        # Gate debug output via env var and log only on state change
        _dbg_enabled = os.getenv('DEBUG_DISPLAY_GAME', '').strip().lower() in ('1', 'true', 'yes', 'on')
        _bs = st.session_state.get('beat_started', None)
        _md = st.session_state.game.mode if ('game' in st.session_state and st.session_state.game) else None
        _msg = f"[DBG] display_game entered: mode={_md}, beat_started={_bs}"
        if _dbg_enabled:
            _prev = st.session_state.get('_dbg_prev_state', {})
            if _prev.get('mode') != _md or _prev.get('beat_started') != _bs or not st.session_state.get('_dbg_logged_once'):
                logging.info(_msg)
                st.session_state['_dbg_logged_once'] = True
            st.session_state['_dbg_prev_state'] = {'mode': _md, 'beat_started': _bs}
    except Exception:
        pass
    # Ensure per-render guard for Skip button (defensive against duplicate blocks)
    st.session_state['_skip_btn_rendered'] = False
    
    import time
    from streamlit_app import save_game_to_user_profile
    # Ensure beat_total_points is always initialized for Beat mode
    if 'beat_total_points' not in st.session_state:
        st.session_state['beat_total_points'] = 0
    # New: accumulator for total penalties across Beat session
    if 'beat_total_penalty' not in st.session_state:
        st.session_state['beat_total_penalty'] = 0

    # If game is not initialized, always use user's default_category for Beat mode
    if 'game' not in st.session_state or not st.session_state.game:
        user_profile = st.session_state.get('user', {})
        default_category = user_profile.get('default_category', 'general')
        # Enforce env gate: if Personal is disabled, do not allow default_category to be Personal
        enable_personal = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
        if not enable_personal and str(default_category).lower() == 'personal':
            default_category = 'general'
            # Persist the correction to both in-memory user and users database if available
            try:
                if 'user' in st.session_state and st.session_state['user']:
                    st.session_state['user']['default_category'] = 'general'
                users_db = st.session_state.get('users', {})
                uname = (st.session_state.get('user', {}) or {}).get('username') or ''
                if uname in users_db:
                    users_db[uname]['default_category'] = 'general'
                    save_users(users_db)
                elif uname.lower() in users_db:
                    users_db[uname.lower()]['default_category'] = 'general'
                    save_users(users_db)
            except Exception:
                pass
        subject = default_category if default_category else 'general'
        random_length = random.randint(3, 10)
        
        st.session_state.game = GameLogic(
            word_length=random_length,
            subject=subject,
            mode='Beat',
            nickname=st.session_state.user['username'],
            difficulty='Medium'
        )
        st.session_state.game_over = False
        st.session_state.game_summary = None
        st.session_state.beat_word_count = 0
        st.session_state.beat_time_left = 0
    # --- Always clear show_word if the word has changed (new round) and update round id ---
    if 'last_displayed_word' not in st.session_state:
        st.session_state['last_displayed_word'] = None
    game = st.session_state.get('game', None)
    current_word = getattr(game, 'selected_word', None) if game else None
    if st.session_state['last_displayed_word'] != current_word:
        st.session_state['show_word'] = False
        st.session_state['show_word_round_id'] = None
        st.session_state['current_round_id'] = str(uuid.uuid4())
        st.session_state['last_displayed_word'] = current_word
        st.session_state['show_prev_questions'] = False
        # Reset any reveal/guess state to avoid leaking letters into the new round
        st.session_state['revealed_letters'] = set()
        st.session_state['used_letters'] = set()
        st.session_state['letter_guess_input'] = ''
        st.session_state['clear_guess_field'] = True
        if game and hasattr(game, 'questions_asked'):
            game.questions_asked.clear()
        st.rerun()
        return  # Prevent further execution after rerun
    # ABSOLUTE FIRST: If the game is over, show only the game over page
    if st.session_state.get('game_over', False):
        display_game_over(st.session_state.get('game_summary', {}))
        return

    # --- Hamburger menu now at the bottom of the game page ---
    with st.container():
        with st.expander('☰ Menu', expanded=False):
            # Skip button removed from menu to avoid duplication; use the main Skip on the game page
            if st.button('View Rules / How to Play', key='view_rules_btn_menu'):
                st.session_state['show_rules'] = not st.session_state.get('show_rules', False)
            if st.button('User Profile', key='user_profile_btn_menu'):
                st.session_state['show_user_profile'] = not st.session_state.get('show_user_profile', False)
            if st.button('Toggle Sound/Music', key='toggle_sound_btn'):
                st.session_state['sound_on'] = not st.session_state.get('sound_on', True)
            # Support button under menu tab
            if 'show_support' not in st.session_state:
                st.session_state['show_support'] = False
            if st.button('Contact Support', key='contact_support_btn_menu'):
                st.session_state['show_support'] = not st.session_state['show_support']
            if st.session_state.get('show_support'):
                with st.form('support_form_menu', clear_on_submit=True):
                    support_subject = st.text_input('Subject', key='support_subject_input_menu')
                    support_message = st.text_area('Message', key='support_message_input_menu')
                    submitted = st.form_submit_button('Send Support Message')
                    if submitted:
                        admin_email = os.getenv('ADMIN_EMAIL') or os.getenv('SMTP_USER')
                        if not admin_email:
                            st.error('Support email not configured. Set ADMIN_EMAIL or SMTP_USER.')
                        else:
                            user = st.session_state.get('user', {})
                            sender = (user.get('username') or 'unknown')
                            sender_email = user.get('email') or ''
                            category = getattr(st.session_state.get('game'), 'subject', '') or ''
                            body = f"From: {sender} <{sender_email}>\nCategory: {category}\n\n{support_message}"
                            ok = send_email_with_attachment(admin_email, support_subject or '(no subject)', body)
                            if ok:
                                st.success('Support request sent!')
                            else:
                                st.error('Failed to send. Please try again later.')
            if st.button('Log Out', key='logout_btn'):
                # Only remove session/user/game state, NOT the users database
                keys_to_keep = ['users']
                for key in list(st.session_state.keys()):
                    if key != 'users':
                        del st.session_state[key]
                st.rerun()

    # Show user profile form if toggled
    if st.session_state.get('show_user_profile', False):
        st.markdown('## User Profile')
        user = st.session_state.get('user', {})
        # Education dropdown
        education_options = [
            'High School', 'Associate Degree', 'Bachelor\'s Degree', 'Master\'s Degree', 'PhD', 'Other'
        ]
        education = st.selectbox('Education', education_options, index=education_options.index(user.get('education', '')) if user.get('education', '') in education_options else len(education_options)-1)
        education_other = ''
        if education == 'Other':
            education_other = st.text_input('Please specify your education', value=user.get('education', '') if user.get('education', '') not in education_options else '')
        # Occupation dropdown
        occupation_options = [
            'Student', 'Teacher', 'Engineer', 'Doctor', 'Researcher', 'Artist', 'Business', 'Retired', 'Other'
        ]
        occupation = st.selectbox('Occupation', occupation_options, index=occupation_options.index(user.get('occupation', '')) if user.get('occupation', '') in occupation_options else len(occupation_options)-1)
        occupation_other = ''
        if occupation == 'Other':
            occupation_other = st.text_input('Please specify your occupation', value=user.get('occupation', '') if user.get('occupation', '') not in occupation_options else '')
        address = st.text_input('Address', value=user.get('address', ''))
        bio_value = st.text_area(f"Bio (optional – up to {BIO_MAX_CHARS} characters)", value=user.get('bio', ''), max_chars=BIO_MAX_CHARS, key=PROFILE_BIO_KEY)
        _bio_len = len(bio_value or "")
        st.caption(f"{_bio_len}/{BIO_MAX_CHARS} characters")
        if _bio_len > BIO_MAX_CHARS:
            st.warning(f"Bio exceeds {BIO_MAX_CHARS} characters; please shorten it.")
        elif _bio_len >= BIO_MAX_CHARS:
            st.warning(f"Bio reached the {BIO_MAX_CHARS}-character limit.")
        elif _bio_len >= int(BIO_MAX_CHARS * 0.9):
            st.info("Approaching the 90% character limit.")
        min_birthday = datetime.date(1900, 1, 1)
        raw_birthday = user.get('birthday', None)
        birthday_value = None  # Always define before use
        
        if isinstance(raw_birthday, datetime.date):
            birthday_value = raw_birthday
        elif isinstance(raw_birthday, datetime.datetime):
            birthday_value = raw_birthday.date()
        elif isinstance(raw_birthday, str) and raw_birthday:
            try:
                birthday_value = datetime.date.fromisoformat(raw_birthday)
            except Exception:
                try:
                    birthday_value = datetime.datetime.fromisoformat(raw_birthday).date()
                except Exception:
                    birthday_value = None
        if not birthday_value:
            birthday_value = datetime.date.today()
        birthday = st.date_input('Birthday', value=birthday_value, min_value=min_birthday)
        # Debug: show current username and users dict keys (first 10)
        st.caption(f"Debug: current username={user.get('username')}, lower={(user.get('username') or '').lower()}")
        st.caption(f"Debug: users keys={list(st.session_state.get('users', {}).keys())[:10]}")
        # One-time normalization: if users dict has a mixed-case key for this user, migrate it to lowercase
        _users_dict = st.session_state.get('users', {})
        _username = user.get('username') or ''
        _username_lower = _username.lower()
        if _username in _users_dict and _username != _username_lower:
            _users_dict[_username_lower] = _users_dict.pop(_username)
            save_users(_users_dict)
        # Confirm guard will pass
        _ok_guard = bool(_username_lower and 'users' in st.session_state and _username_lower in st.session_state['users'])
        st.caption(f"Debug: save guard ok={_ok_guard}")
        st.caption(f"Debug: bio_in_state={st.session_state.get(PROFILE_BIO_KEY, None) is not None}")
        if st.button('Save Profile', key='save_profile_btn'):
            username = user.get('username')
            final_education = education_other if education == 'Other' else education
            final_occupation = occupation_other if occupation == 'Other' else occupation
            username_lower = (username or '').lower()
            bio_to_save = st.session_state.get(PROFILE_BIO_KEY, None)
            if bio_to_save is None:
                bio_to_save = st.session_state.get('profile_bio_v6', user.get('bio', ''))
            if username_lower and 'users' in st.session_state and username_lower in st.session_state['users']:
                st.session_state['users'][username_lower]['education'] = final_education
                st.session_state['users'][username_lower]['address'] = address
                st.session_state['users'][username_lower]['bio'] = bio_to_save
                st.session_state['users'][username_lower]['birthday'] = str(birthday)
                st.session_state['users'][username_lower]['occupation'] = final_occupation
                st.session_state['user']['education'] = final_education
                st.session_state['user']['address'] = address
                st.session_state['user']['bio'] = bio_to_save
                st.session_state['user']['birthday'] = str(birthday)
                st.session_state['user']['occupation'] = final_occupation
                save_users(st.session_state['users'])
                st.success('Profile updated!')
                st.rerun()

    # Show rules if toggled
    if st.session_state.get('show_rules', False):
        st.info("""
        **How to Play:**\n- Guess the word by revealing letters.\n- Use hints or ask yes/no questions.\n- In Beat mode, solve as many words as possible before time runs out!\n- Use the menu to skip, reveal, or change category.\n- Personal: profile‑aware category that may show “Generating personal hints…” and a Retry button until 3+ hints are ready.\n        """)

    # Handle change category
    if st.session_state.get('change_category', False):
        enable_personal = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1', 'true', 'yes', 'on')
        categories = ["any", "anatomy", "animals", "aviation", "brands", "cities", "food", "general", "gre", "history", "medicines", "movies", "music", "places", "psat", "sat", "science", "sports", "tech", "4th_grade", "8th_grade"]
        if enable_personal:
            categories.insert(1, "Personal")
        new_category = st.selectbox("Select a new category:", categories, format_func=lambda x: ('Any' if x=='any' else ('GRE' if x=='gre' else ('SAT' if x=='sat' else ('PSAT' if x=='psat' else x.replace('_',' ').title())))), key='category_select_box')
        if st.button("Confirm Category Change", key='change_category_btn'):
            # Enforce env gate: if Personal is disabled, do not allow selection of Personal
            _enable_personal = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
            if not _enable_personal and str(new_category).lower() == 'personal':
                st.warning("Personal category is currently disabled by admin settings. Using 'general' instead.")
                new_category = 'general'
            game = st.session_state.game
            st.session_state.game = GameLogic(
                word_length=5,
                subject=new_category,
                mode=game.mode,
                nickname=st.session_state.user['username'],
                difficulty=game.difficulty
            )
            # --- Update user profile default_category ---
            if 'user' in st.session_state and st.session_state['user']:
                st.session_state['user']['default_category'] = new_category
                # Also update in users dict and save
                username = st.session_state['user']['username']
                if 'users' in st.session_state and username in st.session_state['users']:
                    st.session_state['users'][username]['default_category'] = new_category
                    save_users(st.session_state['users'])
            st.session_state['change_category'] = False
            st.session_state['revealed_letters'] = set()
            st.session_state['used_letters'] = set()
            st.session_state['feedback'] = ''
            st.session_state['show_prev_questions'] = False  # <-- Clear previous questions
            st.session_state['show_word'] = False  # <-- Clear show_word for new word
            st.session_state['show_word_round_id'] = None  # <-- Clear show_word_round_id for new word
            st.rerun()
        st.stop()

    ensure_beat_mode_state()

    if "game" not in st.session_state:
        st.error("No active game found. Please start a new game.")
        return
    game = st.session_state.game
    user_name = st.session_state.user['username'] if st.session_state.get('user') else ''
    max_hints = game.current_settings["max_hints"]

    # --- Banner and stats ---
    import time as _time
    if game.mode == 'Beat':
        # Timer logic
        if 'beat_start_time' not in st.session_state:
            st.session_state['beat_start_time'] = _time.time()
        elapsed = int(_time.time() - st.session_state['beat_start_time'])
        time_left = max(0, BEAT_MODE_TIMEOUT_SECONDS - elapsed)
        st.session_state['beat_time_left'] = time_left
        # End game if time is up
        if time_left <= 0 and not st.session_state.get('game_over', False):
            # --- FIX: If the current word was just solved, increment beat_word_count ---
            # If all letters are revealed, count as solved
            word = game.selected_word if hasattr(game, 'selected_word') else ''
            revealed_letters = st.session_state.get('revealed_letters', set())
            if word and set(letter.lower() for letter in word) == revealed_letters:
                st.session_state.beat_word_count += 1
            st.session_state['last_mode'] = st.session_state.game.mode
            st.session_state['game_over'] = True
            st.session_state['game_summary'] = game.get_game_summary()
            st.session_state['show_word'] = False  # <-- Clear show_word for new word
            st.session_state['show_word_round_id'] = None  # <-- Clear show_word_round_id for new word
            st.rerun()
        # --- Banner with timer and score (MATCH GAME OVER STYLE) ---
        if game.mode == 'Beat' and 'beat_started' not in st.session_state:
            st.session_state['beat_started'] = False
        if game.mode == 'Beat' and not st.session_state['beat_started']:
            stats_html = f"""
            <div class='wizword-banner'>
              <div class='wizword-banner-title'>WizWord</div>
              <div class='wizword-banner-stats' style='display:flex;align-items:center;gap:18px;'>
                <span class='wizword-stat wizword-beat-category'><b>📚</b> {game.subject.replace('_', ' ').title()}</span>
                <span class='wizword-stat wizword-beat-timer'><b>⏰</b> --s</span>
                <span class='wizword-stat wizword-beat-score'><b>🏆</b> {game.score}</span>
                <span class='wizword-stat'><b>🔢</b> {st.session_state.get('beat_word_count', 0)}</span>
                <span class='wizword-stat' style='padding:0;margin:0;'>
                  <div class='beat-start-btn' style='display:inline-block;'></div>
                </span>
              </div>
            </div>
            <style>/* ... existing styles ... */</style>
            """
            # Render the banner (contains a marker div where the button sits)
            st.markdown(stats_html, unsafe_allow_html=True)
            # Now render the Start button which follows the marker div (styled via sibling selector)
            start_btn_html = """
            <style>
            @keyframes flash-pulse {
                0% { transform: scale(1); filter: brightness(1); }
                50% { transform: scale(1.06); filter: brightness(1.25); }
                100% { transform: scale(1); filter: brightness(1); }
            }
            .beat-start-btn + div button {
                background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 35%, #4ECDC4 70%, #8EC5FF 100%) !important;
                color: #222 !important;
                font-weight: 900 !important;
                font-size: 2.4em !important; /* 100% larger */
                border-radius: 9999px !important;
                border: none !important;
                padding: 1.2em 3.2em !important; /* 100% larger */
                margin: 0 0.2em !important;
                box-shadow: 0 14px 30px rgba(0,0,0,0.22) !important;
                animation: flash-pulse 1.3s ease-in-out infinite;
                transition: transform 0.15s ease, filter 0.15s ease, box-shadow 0.15s ease;
            }
            .beat-start-btn + div button:hover {
                background: linear-gradient(90deg, #FFED8A 0%, #FF8A8A 35%, #70E6CD 70%, #A6D5FF 100%) !important;
                color: #fff !important;
                box-shadow: 0 12px 28px rgba(0,0,0,0.24) !important;
            }
            /* Smaller, white Change Category button */
            .beat-change-cat button {
                background: #ffffff !important;
                color: #333 !important;
                font-weight: 600 !important;
                font-size: 0.45em !important; /* 50% smaller */
                border-radius: 6px !important;
                border: 1px solid #e5e7eb !important; /* light gray */
                padding: 0.125em 0.4em !important; /* halved padding */
                margin-left: 0.2em !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.08);
                transform: scale(1); /* ensure no inherited scaling */
            }
            .beat-change-cat button:hover {
                background: #f9fafb !important;
                color: #111 !important;
                border-color: #d1d5db !important;
            }
            </style>
            <div class='beat-start-btn' style='display:inline-block;'></div>
            """
            st.markdown(start_btn_html, unsafe_allow_html=True)
            _uname = (
                (st.session_state.get('user') or {}).get('username')
                or st.session_state.get('nickname')
                or 'Player'
            )
            _start_label = f"{_uname} .. Click to Start Game"
            if st.button(_start_label, key='beat_start_btn'):
                st.session_state['beat_started'] = True
                st.session_state['beat_start_time'] = _time.time()
                st.rerun()
            # Bottom-of-start-page Global Leaderboard (Top 10 by SEI) for user's default category
            try:
                # Use the running category shown in the banner
                chosen_cat = (game.subject or 'any').lower()
                # Pull Top 3 from aggregates with simple per-category cache to avoid recomputation
                _cache = st.session_state.get('_top3_start_cache', {})
                if _cache.get('cat') == chosen_cat and 'rows' in _cache:
                    top3_rows = _cache.get('rows', [])
                else:
                    top3_rows = get_top10_from_aggregates(chosen_cat)[:3]
                if (not top3_rows) and chosen_cat != 'any':
                    top3_rows = get_top10_from_aggregates('any')[:3]
                if not top3_rows:
                    try:
                        _agg = _load_aggregates()
                        for cat_key, users in (_agg.get('category_user_highest') or {}).items():
                            if users:
                                cand = get_top10_from_aggregates(cat_key)[:3]
                                if cand:
                                    chosen_cat = cat_key
                                    top3_rows = cand
                                    break
                    except Exception:
                        pass
                    st.session_state['_top3_start_cache'] = {'cat': chosen_cat, 'rows': top3_rows}
                # Optional debug for start page block
                import logging, os
                _dbg = os.getenv('DEBUG_TOP3', '').strip().lower() in ('1','true','yes','on')
                if _dbg and not st.session_state.get('top3_start_debug_done'):
                    _exists = os.path.exists(AGGREGATES_PATH)
                    _size = os.path.getsize(AGGREGATES_PATH) if _exists else 0
                    _cats = []
                    try:
                        _a = _load_aggregates()
                        _cats = list((_a.get('category_user_highest') or {}).keys())
                    except Exception:
                        pass
                    _msg = f"[TOP3:START] chosen_cat={chosen_cat}, cats={_cats}, rows={len(top3_rows)} AGG_PATH={AGGREGATES_PATH} exists={_exists} size={_size}"
                    logging.info(_msg)
                    st.caption(f"DEBUG TOP3 START: chosen_cat={chosen_cat}, cats={_cats}, rows={len(top3_rows)}")
                    st.caption(f"DEBUG TOP3 START: AGG_PATH={AGGREGATES_PATH}, exists={_exists}, size={_size}")
                    if not top3_rows:
                        st.caption("DEBUG TOP3 START: No rows found after fallbacks")
                    else:
                        st.caption(f"DEBUG TOP3 START: First row sample: {top3_rows[0]}")
                    st.session_state['top3_start_debug_done'] = True
                nice_cat = chosen_cat.replace('_',' ').title()
                st.markdown(f"""
                <div style='font-size:1.0em; font-weight:700; color:#fff; margin:1em 0 0.25em 0;'>
                    🏆 Global Leaderboard (Top 3 by SEI) - {nice_cat}
                </div>
                """, unsafe_allow_html=True)
                if top3_rows:
                    st.table(top3_rows)
                else:
                    st.info("No games available yet for this category.")
                # Change Category under Top 10
                st.markdown("<div class='beat-change-cat' style='display:inline-block;margin-top:8px;'>", unsafe_allow_html=True)
                if st.button('Change Category', key='change_category_btn_beat_start'):
                    st.session_state['change_category'] = True
                    # Clear the cached Top 3 so it refreshes for the new category
                    st.session_state.pop('_top3_start_cache', None)
                    st.rerun()
                st.markdown("</div>", unsafe_allow_html=True)
                # Admin-only: render all user profiles when toggled in the sidebar
                try:
                    if st.session_state.get('show_all_users_profiles'):
                        st.markdown("### All User Profiles")
                        users_obj = load_all_users()
                        # Build per-user game counts and last timestamps from game_results.json (authoritative)
                        try:
                            all_games_flat = get_all_game_results()
                        except Exception:
                            all_games_flat = []
                        games_by_user = {}
                        last_time_by_user = {}
                        for gg in all_games_flat:
                            uname = str(gg.get('nickname', '')).lower()
                            if uname:
                                games_by_user[uname] = games_by_user.get(uname, 0) + 1
                                ts = gg.get('timestamp')
                                if ts:
                                    try:
                                        # Keep the max timestamp
                                        prev = last_time_by_user.get(uname)
                                        if (prev is None) or (str(ts) > str(prev)):
                                            last_time_by_user[uname] = str(ts)
                                    except Exception:
                                        pass
                        # Also read games_count directly from users.json if present
                        try:
                            users_map = load_all_users()
                        except Exception:
                            users_map = {}
                        rows = []
                        # Support both dict-based and list-based user stores
                        if isinstance(users_obj, dict):
                            for username, u in users_obj.items():
                                if isinstance(u, dict):
                                    uname_l = str(username).lower()
                                    games_count = u.get('games_count') if isinstance(u, dict) else None
                                    if not isinstance(games_count, int):
                                        games_count = games_by_user.get(uname_l, 0)
                                    # Last game date preference: users.json last_game_time, fallback to derived last_time_by_user
                                    last_ts = (u.get('last_game_time') if isinstance(u, dict) else None) or last_time_by_user.get(uname_l)
                                    if isinstance(last_ts, str) and 'T' in last_ts:
                                        last_ts = last_ts.split('T')[0]
                                    rows.append({
                                        'Username': username,
                                        'Email': u.get('email', ''),
                                        'Games': games_count,
                                        'Last Game': last_ts or ''
                                    })
                                else:
                                    rows.append({'Username': str(username), 'Email': '', 'Games': 0})
                        elif isinstance(users_obj, list):
                            for u in users_obj:
                                _uname = (u.get('username') if isinstance(u, dict) else '')
                                rows.append({
                                    'Username': _uname,
                                    'Email': (u.get('email') if isinstance(u, dict) else ''),
                                    'Games': (u.get('games_count') if isinstance(u, dict) and isinstance(u.get('games_count'), int) else games_by_user.get(str(_uname).lower(), 0)),
                                    'Last Game': (
                                        ((u.get('last_game_time') or '') if isinstance(u, dict) else '')
                                        or (last_time_by_user.get(str(_uname).lower()) or '')
                                    ).split('T')[0] if (
                                        (isinstance(u, dict) and isinstance(u.get('last_game_time'), str)) or isinstance(last_time_by_user.get(str(_uname).lower()), str)
                                    ) else ''
                                })
                        if rows:
                            st.table(rows)
                        else:
                            st.info('No user profiles found.')
                except Exception:
                    st.info('Unable to load user profiles.')
            except Exception as e:
                # Surface an error line so it is visible in console if this block fails
                import logging
                logging.error(f"[TOP3:START] failed: {e}")
                pass
        # Determine banner stickiness from environment
        _sticky_env = os.getenv('WIZWORD_STICKY_BANNER', 'true').strip().lower()
        _is_sticky_banner = _sticky_env in ('1', 'true', 'yes', 'on')
        _banner_position_css = (
            "position: fixed; top: 56px; left: 0; right: 0; width: 100vw; z-index: 10000; backdrop-filter: blur(2px);"
            if _is_sticky_banner else
            "position: static;"
        )
        # Normal banner and timer logic follows as before
        stats_html = f"""
        <div class='wizword-banner'>
          <div class='wizword-banner-title'>WizWord <span style="font-size:0.6em; padding:0.25em 0.6em; margin-left:0.4em; border-radius:0.6em; background:rgba(255,255,255,0.18); box-shadow: inset 0 0 0 1px rgba(255,255,255,0.25);">Beat</span></div>
          <div class='wizword-banner-stats'>
            <span class='wizword-stat wizword-beat-category'><b>📚</b> {game.subject.replace('_', ' ').title()}</span>
            <span class='wizword-stat wizword-beat-timer'><b>⏰</b> {time_left}s</span>
            <span class='wizword-stat wizword-beat-score'><b>🏆</b> {game.score}</span>
            <span class='wizword-stat'><b>🔢</b> {st.session_state.get('beat_word_count', 0)}</span>
          </div>
        </div>
        <style>
        .wizword-banner {{
            display: flex;
            flex-direction: row;
            align-items: center;
            justify-content: space-between;
            background: linear-gradient(90deg, #FF6B6B 0%, #FFD93D 50%, #4ECDC4 100%);
            color: #fff;
            padding: 10px 24px 10px 24px;
            margin: 0 0 0 0;
            border-radius: 0;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.10),
                        inset 0 -2px 0px rgba(0, 0, 0, 0.07);
            -webkit-text-stroke: 1px #222;
            text-stroke: 1px #222;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.13),
                         0 1px 4px rgba(0,0,0,0.08);
            transition: box-shadow 0.2s, background 0.2s;
            {_banner_position_css}
        }}
        .wizword-banner-title {{
            font-family: 'Baloo 2', 'Poppins', 'Arial Black', Arial, sans-serif !important;
            font-size: 1.5em;
            font-weight: 700;
            letter-spacing: 0.08em;
            margin-right: 24px;
            flex: 0 0 auto;
        }}
        .wizword-banner-stats {{
            display: flex;
            flex-direction: row;
            gap: 18px;
            font-size: 1.1em;
            font-weight: 600;
            align-items: center;
        }}
        .wizword-stat {{
            background: rgba(0,0,0,0.13);
            border-radius: 8px;
            padding: 4px 12px;
            margin-left: 0;
            margin-right: 0;
            min-width: 60px;
            text-align: center;
            box-shadow: 0 1px 2px rgba(0,0,0,0.07);
        }}
        @keyframes pulse-beat-score {{
            0% {{ background: #fffbe6; color: #ff6b6b; box-shadow: 0 0 0 0 #FFD93D55; }}
            50% {{ background: #FFD93D; color: #fff; box-shadow: 0 0 16px 8px #FFD93D55; }}
            100% {{ background: #fffbe6; color: #ff6b6b; box-shadow: 0 0 0 0 #FFD93D55; }}
        }}
        .wizword-beat-score {{
            font-size: 2.1em !important;
            font-weight: 900 !important;
            color: #ff6b6b !important;
            background: #fffbe6 !important;
            border: 2.5px solid #FFD93D !important;
            box-shadow: 0 2px 12px #FFD93D33, 0 1px 4px #FF6B6B22 !important;
            animation: pulse-beat-score 1.2s infinite;
            transition: background 0.2s, color 0.2s, box-shadow 0.2s;
        }}
        @keyframes pulse-beat-timer {{
            0% {{
                background: #e6f7ff;
                color: #1e90ff;
                box-shadow: 0 0 0 0 #1e90ff33, 0 0 0 0 #00e0ff44;
                border-color: #1e90ff;
                transform: scale(1);
            }}
            40% {{
                background: #1e90ff;
                color: #fff;
                box-shadow: 0 0 32px 16px #00e0ff99, 0 0 12px 4px #1e90ff88;
                border-color: #00e0ff;
                transform: scale(1.13);
            }}
            60% {{
                background: #00e0ff;
                color: #fff;
                box-shadow: 0 0 48px 24px #00e0ffcc, 0 0 16px 8px #1e90ffcc;
                border-color: #fff;
                transform: scale(1.18);
            }}
            100% {{
                background: #e6f7ff;
                color: #1e90ff;
                box-shadow: 0 0 0 0 #1e90ff33, 0 0 0 0 #00e0ff44;
                border-color: #1e90ff;
                transform: scale(1);
            }}
        }}
        .wizword-beat-timer {{
            font-size: 2.2em !important;
            font-weight: 900 !important;
            color: #1e90ff !important;
            background: #e6f7ff !important;
            border: 3px solid #1e90ff !important;
            box-shadow: 0 2px 18px #1e90ff55, 0 1px 8px #00e0ff44 !important;
            animation: pulse-beat-timer 2s infinite;
            transition: background 0.2s, color 0.2s, box-shadow 0.2s, border-color 0.2s, transform 0.2s;
            will-change: background, color, box-shadow, border-color, transform;
        }}
        </style>
        """
        st.markdown(stats_html, unsafe_allow_html=True)
        # Override styles to reduce banner height
        st.markdown(
            """
            <style>
            .wizword-banner { padding: 4px 12px !important; }
            .wizword-banner-title { font-size: 1.2em !important; white-space: nowrap !important; }
            .wizword-banner-stats { gap: 8px !important; font-size: 0.95em !important; flex-wrap: wrap !important; }
            .wizword-stat { padding: 2px 8px !important; min-width: auto !important; max-width: 44vw !important; }
            .wizword-beat-timer { font-size: 1.5em !important; border-width: 2px !important; }
            .wizword-beat-score { font-size: 1.5em !important; border-width: 2px !important; }
            @media (max-width: 420px) {
              .wizword-banner { padding: 4px 8px !important; }
              .wizword-banner-title { font-size: 1.05em !important; }
              .wizword-banner-stats { gap: 6px !important; font-size: 0.9em !important; }
              .wizword-stat { padding: 2px 6px !important; max-width: 46vw !important; }
            }
            </style>
            """,
            unsafe_allow_html=True,
        )
        # Add a spacer to prevent content from hiding under the fixed banner
        st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)
    else:
        stats_html = f"""
        <div class='wizword-banner'>
          <div class='wizword-banner-title'>WizWord</div>
          <div class='wizword-banner-stats'>
        """
        stats_html += f"<span class='wizword-stat'><b>🎮</b> {game.mode}</span>"
        stats_html += f"<span class='wizword-stat'><b>��</b> {game.score}</span>"
        stats_html += f"<span class='wizword-stat'><b>🎯</b> {game.guesses_made}</span>"
        stats_html += f"<span class='wizword-stat'><b>💡</b> {max_hints - len(game.hints_given)}/{max_hints}</span>"
        stats_html += "</div></div>"
        st.markdown(stats_html, unsafe_allow_html=True)

    # --- Hints and questions section (now above letter boxes) ---
    # --- Prevent rendering gameplay UI until Beat has started ---
    if game.mode == 'Beat' and not st.session_state.get('beat_started', False):
        return

    display_hint_section(game)

    # --- Early Skip handling to avoid rendering stale letter boxes/input ---
    if game.mode == 'Beat':
        try:
            import time as _t
            # Default overlay flag to False each run
            st.session_state['skip_overlay_active'] = False
            if st.session_state.get('skip_pending'):
                _now = _t.time()
                _until = st.session_state.get('skip_show_until', 0)
                _word_to_show = (st.session_state.get('skip_word', '') or '')
                # Abort showing if round changed or current word differs
                if st.session_state.get('skip_round_id') != st.session_state.get('current_round_id') or (getattr(game, 'selected_word', '') and getattr(game, 'selected_word', '') != st.session_state.get('skip_word', '')):
                    st.session_state['skip_pending'] = False
                    st.session_state['skip_show_until'] = 0
                    st.session_state['skip_word'] = ''
                    st.session_state.pop('skip_round_id', None)
                elif _now < _until and _word_to_show:
                    # Mark overlay active and ensure input is cleared/disabled downstream
                    st.session_state['skip_overlay_active'] = True
                    st.session_state['clear_guess_field'] = True
                else:
                    # Time elapsed: load next word and clear flags BEFORE rendering boxes
                    try:
                        username = game.nickname if hasattr(game, 'nickname') and game.nickname else 'global'
                        if hasattr(game, 'selected_word') and game.selected_word:
                            game.word_selector.mark_word_played(game.selected_word, username, game.subject)
                    except Exception:
                        pass
                    new_word_length = 5
                    new_subject = game.subject
                    st.session_state.game = GameLogic(
                        word_length=new_word_length,
                        subject=new_subject,
                        mode=game.mode,
                        nickname=game.nickname,
                        difficulty=game.difficulty,
                        initial_score=game.score
                    )
                    # Clear UI/session for new round
                    st.session_state['show_prev_questions'] = False
                    st.session_state['feedback'] = ''
                    st.session_state['feedback_time'] = 0
                    st.session_state['revealed_letters'] = set()
                    st.session_state['used_letters'] = set()
                    st.session_state['show_word'] = False
                    st.session_state['show_word_round_id'] = None
                    st.session_state['show_final_word'] = False
                    st.session_state['final_word_time'] = 0
                    st.session_state['current_round_id'] = str(uuid.uuid4())
                    st.session_state['last_displayed_word'] = getattr(st.session_state.game, 'selected_word', None)
                    st.session_state['clear_guess_field'] = True
                    # Clear skip flags and rerun
                    st.session_state['skip_pending'] = False
                    st.session_state['skip_show_until'] = 0
                    st.session_state['skip_word'] = ''
                    st.session_state.pop('skip_round_id', None)
                    st.rerun()
                    return
        except Exception:
            pass

    # --- Letter boxes and input ---
    # Reserve a fixed container just above the Skip area (unused now; we show skipped word in boxes)
    skip_word_display_container = st.empty()
    revealed_letters = st.session_state.get('revealed_letters', set())
    word = game.selected_word if hasattr(game, 'selected_word') else ''
    overlay_active = bool(st.session_state.get('skip_overlay_active') and st.session_state.get('skip_word'))
    # Defensive clamp only when not showing skip overlay
    if not overlay_active:
        try:
            used_letters = set((l or '').lower() for l in st.session_state.get('used_letters', set()))
            word_letters = set((word or '').lower())
            allowed_reveals = used_letters.intersection(word_letters)
            if allowed_reveals != set(revealed_letters):
                revealed_letters = allowed_reveals
                st.session_state['revealed_letters'] = allowed_reveals
        except Exception:
            pass
    render_word = (st.session_state.get('skip_word', '') if overlay_active else word) or ''
    if not render_word:
        st.error('No word was selected for this round. Please restart the game or contact support.')
        return
    boxes = []
    for i, letter in enumerate(render_word):
        is_revealed = overlay_active or (letter.lower() in revealed_letters)
        style = (
            "display:inline-block;width:2.5em;height:2.5em;margin:0 0.2em;"
            "font-size:2em;text-align:center;line-height:2.5em;"
            "border-radius:0.4em;box-shadow:0 2px 8px rgba(0,0,0,0.10);"
            "transition:background 0.3s, color 0.3s, transform 0.4s;"
            f"background:{'#7c3aed' if is_revealed else '#f3e8ff'};"
            f"color:{'#fff' if is_revealed else '#b39ddb'};"
            f"font-weight:{'700' if is_revealed else '400'};"
            f"transform:{'scale(1.1)' if is_revealed else 'none'};"
            "border:2px solid #7c3aed;"
        )
        content = letter.upper() if is_revealed else "_"
        boxes.append(f"<span style='{style}'>{content}</span>")
    st.markdown(f"<div style='display:flex;flex-direction:row;justify-content:center;gap:0.2em;margin-bottom:1.2em;'>{''.join(boxes)}</div>", unsafe_allow_html=True)
    # If Personal category and not enough hints yet, block and fetch
    try:
        game = st.session_state.game
        if str(getattr(game, 'original_subject', game.subject)).lower() == 'personal':
            needed = 3
            have = len(getattr(game, 'available_hints', []) or [])
            if have < needed:
                with st.spinner('Generating personal hints…'):
                    import time as _t
                    deadline = _t.time() + 15  # allow up to 15s of retries
                    while have < needed and _t.time() < deadline:
                        try:
                            api_hints = game.word_selector.get_api_hints_force(game.selected_word, 'personal', n=needed)
                            api_hints = list(dict.fromkeys((api_hints or [])[:needed]))
                            if api_hints:
                                # Merge into available_hints
                                merged = list(dict.fromkeys((getattr(game, 'available_hints', []) or []) + api_hints))
                                game.available_hints = merged[:max(needed, len(merged))]
                                have = len(game.available_hints)
                                if have >= needed:
                                    break
                        except Exception:
                            pass
                        _t.sleep(1.0)
                have = len(getattr(game, 'available_hints', []) or [])
                if have < needed:
                    st.warning('Could not generate enough personal hints. You can retry.')
                    if st.button('Retry generating hints', key='retry_personal_hints'):
                        st.session_state['retry_personal_hints'] = True
                        st.rerun()
            elif st.session_state.pop('retry_personal_hints', False):
                # Clear flag if hints are now sufficient
                pass
    except Exception:
        pass
    # Ensure no separate skipped word text is shown below Skip button
    skip_word_display_container.empty()

    # Letter input below the container
    if 'clear_guess_field' not in st.session_state:
        st.session_state['clear_guess_field'] = False
    if st.session_state['clear_guess_field']:
        st.session_state['letter_guess_input'] = ''
        st.session_state['clear_guess_field'] = False
    # Disable input if showing final word
    input_disabled = st.session_state.get('show_final_word', False) or st.session_state.get('skip_overlay_active', False)
    guess = st.text_input(f'Type up to {len(word)} letters and press Enter:', max_chars=len(word), key='letter_guess_input', disabled=input_disabled)
    # --- Show final word before win logic ---
    if st.session_state.get('show_final_word', False):
        st.markdown(f"<div style='text-align:center; margin:1.5em 0 0.5em 0;'><span style=\"display:inline-block;font-size:2.4em;font-family:'Baloo 2','Poppins','Arial Black',sans-serif;font-weight:900;letter-spacing:0.18em;background:linear-gradient(90deg,#FFD93D 0%,#FF6B6B 50%,#4ECDC4 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:2px 2px 8px rgba(0,0,0,0.13);padding:0.18em 0.7em;border-radius:0.4em;box-shadow:0 2px 8px rgba(0,0,0,0.10);\">{word.upper()}</span></div>", unsafe_allow_html=True)
        st.success("🎉 You revealed the full word!")
        # Custom big, long-lasting balloon animation
        st.markdown("""
        <style>
        @keyframes big-balloons {
            0% { transform: translateY(100vh) scale(1.2); opacity: 0.7; }
            10% { opacity: 1; }
            80% { opacity: 1; }
            100% { transform: translateY(-120vh) scale(1.2); opacity: 0; }
        }
        .custom-balloons {
            position: fixed;
            left: 0; right: 0; bottom: 0;
            width: 100vw; height: 100vh;
            pointer-events: none;
            z-index: 99999;
        }
        .custom-balloon {
            position: absolute;
            bottom: 0;
            width: 90px; height: 120px;
            border-radius: 50% 50% 50% 50% / 60% 60% 40% 40%;
            opacity: 0.85;
            animation: big-balloons 5.5s cubic-bezier(.17,.67,.83,.67) forwards;
        }
        .custom-balloon1 { left: 12vw; background: linear-gradient(120deg,#FFD93D,#FF6B6B); }
        .custom-balloon2 { left: 32vw; background: linear-gradient(120deg,#4ECDC4,#FFD93D); }
        .custom-balloon3 { left: 52vw; background: linear-gradient(120deg,#FF6B6B,#4ECDC4); }
        .custom-balloon4 { left: 72vw; background: linear-gradient(120deg,#FFD93D,#4ECDC4); }
        .custom-balloon5 { left: 22vw; background: linear-gradient(120deg,#FF6B6B,#FFD93D); }
        .custom-balloon6 { left: 62vw; background: linear-gradient(120deg,#4ECDC4,#FF6B6B); }
        </style>
        <div class='custom-balloons'>
            <div class='custom-balloon custom-balloon1'></div>
            <div class='custom-balloon custom-balloon2'></div>
            <div class='custom-balloon custom-balloon3'></div>
            <div class='custom-balloon custom-balloon4'></div>
            <div class='custom-balloon custom-balloon5'></div>
            <div class='custom-balloon custom-balloon6'></div>
        </div>
        <script>
        setTimeout(function() {
            var el = document.querySelector('.custom-balloons');
            if (el) el.remove();
        }, 5400);
        </script>
        """, unsafe_allow_html=True)
        import time as _wait_time
        if 'final_word_time' not in st.session_state:
            st.session_state['final_word_time'] = time.time()
        elif time.time() - st.session_state['final_word_time'] > 3.0:
            st.session_state['show_final_word'] = False
            st.session_state['final_word_time'] = 0
            # Now proceed to win logic
            is_correct, message, points = game.make_guess(game.selected_word)
            # Sync penalties to session after final scoring
            try:
                if hasattr(game, 'total_penalty_points'):
                    st.session_state['beat_total_points'] = int(getattr(game, 'total_penalty_points', 0))
                # If points were negative on last action, accumulate
                if isinstance(points, (int, float)) and points < 0:
                    st.session_state['beat_total_penalty'] = int(st.session_state.get('beat_total_penalty', 0)) + abs(points)
            except Exception:
                pass
            st.session_state['feedback'] = message
            if game.mode == 'Beat':
                # Clear show_word and feedback before loading new word
                st.session_state['show_word'] = False
                st.session_state['feedback'] = ''
                st.session_state.beat_word_count += 1
                orig_length = st.session_state.get('original_word_length_choice', None)
                orig_category = st.session_state.get('original_category_choice', game.subject)
                # Always ensure word_length is an int between 3 and 10
                if orig_length == "any" or orig_length is None:
                    new_word_length = random.randint(3, 10)
                else:
                    try:
                        new_word_length = int(orig_length)
                        if new_word_length < 3 or new_word_length > 10:
                            new_word_length = 5
                    except Exception:
                        new_word_length = 5
                categories = ["general", "animals", "food", "places", "science", "tech", "sports", "brands", "4th_grade", "cities", "medicines", "anatomy"]
                new_subject = random.choice(categories) if orig_category == "any" else game.subject
                # Enforce env gate when rolling next word too
                _enable_personal_round = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
                if not _enable_personal_round and str(new_subject).lower() == 'personal':
                    new_subject = 'general'

                st.session_state.game = GameLogic(
                    word_length=new_word_length,
                    subject=new_subject,
                    mode=game.mode,
                    nickname=game.nickname,
                    difficulty=game.difficulty,
                    initial_score=game.score
                )
                st.session_state['current_round_id'] = str(uuid.uuid4())
                st.session_state['feedback'] = ''
                st.session_state['show_word'] = False
                st.session_state['show_word_round_id'] = None
                st.session_state['show_prev_questions'] = False
                st.session_state['yes_no_question_input'] = ''
                if hasattr(st.session_state.game, 'questions_asked'):
                    st.session_state.game.questions_asked.clear()
                st.session_state['revealed_letters'] = set()
                st.session_state['used_letters'] = set()
                st.session_state['clear_guess_field'] = True
                st.rerun()
            else:
                st.session_state['last_mode'] = st.session_state.game.mode
                st.session_state['game_over'] = True
                st.session_state['game_summary'] = game.get_game_summary()
                save_game_to_user_profile(st.session_state['game_summary'])
                st.session_state['clear_guess_field'] = True
                st.rerun()
        else:
            import time as _wait_time
            _wait_time.sleep(0.1)
            st.rerun()
    elif guess:
        guess = guess.lower()
        used_letters = st.session_state.get('used_letters', set())
        feedback = []
        # Reveal any matching letters, regardless of position
        for g in guess:
            if g in word.lower():
                if g not in revealed_letters:
                    revealed_letters.add(g)
                feedback.append(f"✅ {g.upper()} is in the word!")
            else:
                feedback.append(f"❌ {g.upper()} is not in the word.")
        st.session_state['revealed_letters'] = revealed_letters
        st.session_state['used_letters'] = used_letters.union(set(guess))
        # If all letters are revealed, set flag and rerun (do NOT trigger win logic yet)
        if set(letter.lower() for letter in word) == revealed_letters:
            st.session_state['show_final_word'] = True
            st.session_state['final_word_time'] = time.time()
            st.rerun()
        else:
            # Apply -10 point penalty for each wrong attempt
            game.score -= 10
            game.total_points -= 10
            # Update total penalty tracker
            try:
                if hasattr(game, 'total_penalty_points'):
                    game.total_penalty_points += 10
                else:
                    game.total_penalty_points = 10
                st.session_state['beat_total_penalty'] = int(st.session_state.get('beat_total_penalty', 0)) + 10
            except Exception:
                pass
            st.session_state['feedback'] = '  |  '.join(feedback)
            st.session_state['clear_guess_field'] = True
            st.rerun()

    # --- Skip button for Beat mode (moved above the question section) ---
    if game.mode == 'Beat':
        col_a, col_b, col_c = st.columns([1,2,1])
        with col_b:
            if (not st.session_state.get('_skip_btn_rendered', False)) and st.button('Skip', key='skip_word_btn_main', use_container_width=True):
                import time as _t
                st.session_state['skip_pending'] = True
                st.session_state['skip_word'] = getattr(game, 'selected_word', '')
                st.session_state['skip_show_until'] = _t.time() + 2.0  # show word for 2 seconds
                # Track the round we initiated skip on, so we can stop showing after the round changes
                st.session_state['skip_round_id'] = st.session_state.get('current_round_id')
                st.session_state['_skip_btn_rendered'] = True
                st.rerun()

    # --- Ask Yes/No Question section (now below letter boxes and Skip) ---
    clear_field = st.session_state.get('clear_question_field', False)
    if clear_field:
        st.session_state['yes_no_question_input'] = ""
    question = st.text_input(
        "Type your yes/no question:",
        key="yes_no_question_input",
        value=st.session_state.get('yes_no_question_input', "")
    )
    if clear_field:
        st.session_state['clear_question_field'] = False
    if question != st.session_state.get('yes_no_question_input', ""):
        st.session_state['yes_no_question_input'] = question
    if question.strip():
        # Debug prints to confirm score update
        
        prev_score = game.score
        success, answer, points = game.ask_question(question)
        # Sync penalties to session after a question penalty is applied
        try:
            if hasattr(game, 'total_penalty_points'):
                st.session_state['beat_total_points'] = int(getattr(game, 'total_penalty_points', 0))
                st.session_state['beat_total_penalty'] = int(st.session_state.get('beat_total_penalty', 0)) + (abs(points) if points < 0 else 0)
        except Exception:
            pass
        
        if success:
            st.session_state['feedback'] = f"Q: {question}  \nA: {answer}"
            st.session_state['feedback_round_id'] = st.session_state.get('current_round_id')
        else:
            st.session_state['feedback'] = answer
            st.session_state['feedback_round_id'] = st.session_state.get('current_round_id')
        st.session_state['feedback_time'] = time.time()
        st.session_state['clear_question_field'] = True  # Set flag to clear on next rerun
        st.rerun()

    # --- Previous Asked Questions section (toggleable) ---
    prev_questions_container = st.empty()
    if 'show_prev_questions' not in st.session_state:
        st.session_state['show_prev_questions'] = False

    # Display the answer to the most recent question above the banner
    if hasattr(game, 'questions_asked') and game.questions_asked and st.session_state.get('feedback_round_id') == st.session_state.get('current_round_id'):
        last_q = game.questions_asked[-1]
        st.markdown(f"""
            <div style='background: linear-gradient(90deg, #FFD93D 0%, #4ECDC4 100%); color: #111; font-size: 1.3em; font-weight: bold; border-radius: 0.7em; padding: 0.4em 1em; margin: 0.5em 0 0.2em 0; box-shadow: 0 2px 8px rgba(0,0,0,0.10); text-align: center;'>
                <span style='font-size:1.1em;'>🗨️ <b>Last Answer:</b> {last_q['answer']}</span>
            </div>
        """, unsafe_allow_html=True)

    if st.button("Show Previous Asked Questions" if not st.session_state['show_prev_questions'] else "Hide Previous Asked Questions", key="toggle_prev_questions_btn"):
        st.session_state['show_prev_questions'] = not st.session_state['show_prev_questions']
    if st.session_state['show_prev_questions'] and hasattr(game, 'questions_asked') and game.questions_asked and st.session_state.get('feedback_round_id') == st.session_state.get('current_round_id'):
        with prev_questions_container:
            st.markdown("**Previous Asked Questions**")
            for q in reversed(game.questions_asked):
                st.markdown(f"- **Q:** {q['question']}<br>  **A:** {q['answer']}", unsafe_allow_html=True)
    else:
        prev_questions_container.empty()

    # --- Show the word below the Ask Question section if requested ---
    show_word_container = st.empty()
    if st.session_state.get('show_word', False) and st.session_state.get('show_word_round_id') == st.session_state.get('current_round_id'):
        current_word = game.selected_word.upper() if hasattr(game, 'selected_word') else ''
        if current_word:
            with show_word_container:
                st.markdown(f"""
                    <div style='margin:1em 0;font-size:2em;color:#7c3aed;font-weight:700;text-align:center;'>
                        {current_word}
                    </div>
                """, unsafe_allow_html=True)
    else:
        show_word_container.empty()

    # --- Game Over Page ---
    if st.session_state.get('game_over', False):
        display_game_over(st.session_state['game_summary'])
        return

    # --- Feedback/status area ---
    feedback = st.session_state.get('feedback', '')
    feedback_time = st.session_state.get('feedback_time', 0)
    is_show_word = feedback.startswith("The word is:")
    # Only show feedback if it matches the current round
    if st.session_state.get('feedback_round_id') == st.session_state.get('current_round_id'):
        if feedback and ((is_show_word and (time.time() - feedback_time < 4)) or (not is_show_word)):
            st.markdown(f"<div style='margin:1em 0;font-size:1.2em;color:#7c3aed;font-weight:600;'>{feedback}</div>", unsafe_allow_html=True)
            # Only clear if show word and expired
            if is_show_word and (time.time() - feedback_time >= 4):
                st.session_state['feedback'] = ''
                st.session_state['feedback_time'] = 0
        elif feedback:
            st.session_state['feedback'] = ''
            st.session_state['feedback_time'] = 0


    # --- Timer auto-refresh for Beat mode ---
    if game.mode == 'Beat' and not st.session_state.get('game_over', False):
        import time as _time
        _time.sleep(1)
        st.rerun()

    # --- Fixed bottom bar for Restart Game button ---
    st.markdown("""
        <style>
        .bottom-restart-bar {
            position: fixed;
            left: 0;
            bottom: 0;
            width: 100vw;
            background: linear-gradient(90deg, #FF6B6B 0%, #FFD93D 50%, #4ECDC4 100%);
            padding: 1.1em 0 1.1em 0;
            z-index: 9999;
            box-shadow: 0 -2px 16px rgba(0,0,0,0.08);
            display: flex;
            justify-content: center;
        }
        </style>
        <div class="bottom-restart-bar">
    """, unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

def display_game_over(game_summary):
    """Display game over screen with statistics and sharing options."""
    # Use the current game mode from session state if available, then last_mode, then game_summary
    mode = (
        getattr(st.session_state.game, 'mode', None)
        or st.session_state.get('last_mode', None)
        or game_summary.get('mode', 'Fun')
    )
    # If achieved category top SEI, fly a trophy and show congrats banner
    try:
        score_cur = game_summary.get('score', 0)
        time_cur = game_summary.get('time_taken', game_summary.get('duration', 0))
        words_cur = game_summary.get('words_solved', 1) if game_summary.get('mode') == 'Beat' else 1
        denom_cur = max(int(words_cur or 0), 1)
        avg_score_cur = score_cur / denom_cur
        avg_time_cur = (time_cur / denom_cur) if time_cur else 0
        sei_cur = (avg_score_cur / avg_time_cur) if avg_time_cur > 0 else None
        category = (game_summary.get('subject') or '').lower()
        games = get_all_game_results()
        highest = None
        for g in games:
            if (g.get('subject','') or '').lower() != category:
                continue
            # Exclude the current game result (already saved) from comparison
            try:
                _cur_ts = game_summary.get('timestamp')
                if _cur_ts and g.get('timestamp') == _cur_ts:
                    continue
            except Exception:
                pass
            s = g.get('score', 0)
            t = g.get('time_taken', g.get('duration', 0))
            w = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
            d = max(int(w or 0), 1)
            asw = s / d
            atw = (t / d) if t else 0
            val = (asw / atw) if atw > 0 else None
            if val is not None and (highest is None or val > highest):
                highest = val
        is_top = False
        if sei_cur is not None and sei_cur > 0:
            # Trigger if current SEI is a new high or ties the previous high (with small tolerance)
            if highest is None or (sei_cur > (highest + 1e-9)):
                is_top = True
        # Debug override to force the animation without requiring top SEI
        if os.getenv('DEBUG_FORCE_TROPHY', '').strip().lower() in ('1', 'true', 'yes', 'on'):
            is_top = True
        if is_top:
            
            st.markdown(
                f"""
                <style>
                @keyframes flyTrophy {{
                  0% {{ transform: translate(0, 0) scale(1); opacity: 0; }}
                  10% {{ opacity: 1; }}
                  90% {{ transform: translate(-50vw, -30vh) scale(1.2); opacity: 1; }}
                  100% {{ transform: translate(-52vw, -32vh) scale(1.2); opacity: 0; }}
                }}
                .trophy-fly {{
                  position: fixed;
                  right: 16px;
                  bottom: 16px;
                  font-size: 48px;
                  z-index: 999999;
                  animation: flyTrophy 2.6s ease-in-out forwards;
                  pointer-events: none;
                }}
                /* Rising congratulations banner */
                @keyframes riseBanner {{
                  0% {{ transform: translate(-50%, 120%); opacity: 0; }}
                  10% {{ opacity: 1; }}
                  100% {{ transform: translate(-50%, -10vh); opacity: 1; }}
                }}
                .banner-fly {{
                  position: fixed;
                  left: 50%;
                  bottom: -80px;
                  transform: translate(-50%, 120%);
                  z-index: 999998;
                  background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 100%);
                  color: #222; font-weight: 800; border-radius: 12px; padding: 12px 18px; margin: 0;
                  box-shadow: 0 4px 14px rgba(0,0,0,0.18);
                  animation: riseBanner 1.8s ease-out forwards;
                  pointer-events: none;
                  white-space: nowrap;
                }}
                /* Floating balloons */
                @keyframes floatBalloon {{
                  0% {{ transform: translateY(0) translateX(0); opacity: 0; }}
                  10% {{ opacity: 1; }}
                  100% {{ transform: translateY(-60vh) translateX(-10px); opacity: 1; }}
                }}
                .balloon {{
                  position: fixed;
                  bottom: -24px;
                  font-size: 32px;
                  z-index: 999997;
                  animation: floatBalloon 3s ease-in forwards;
                  pointer-events: none;
                }}
                </style>
                <div class="trophy-fly">🏆</div>
                <div class="banner-fly">🎉 Congratulations! Global Top SEI — <b>{game_summary.get('subject','').title()}</b> 🎉</div>
                <span class="balloon" style="left:20%; animation-delay: .0s;">🎈</span>
                <span class="balloon" style="left:35%; animation-delay: .2s;">🎈</span>
                <span class="balloon" style="left:50%; animation-delay: .4s;">🎈</span>
                <span class="balloon" style="left:65%; animation-delay: .1s;">🎈</span>
                <span class="balloon" style="left:80%; animation-delay: .3s;">🎈</span>
                <script>
                setTimeout(function(){{
                  var t = document.querySelector('.trophy-fly'); if(t) t.remove();
                }}, 1900);
                setTimeout(function(){{
                  var b = document.querySelector('.banner-fly'); if(b) b.remove();
                }}, 2200);
                setTimeout(function(){{
                  document.querySelectorAll('.balloon').forEach(function(el){{ el.remove(); }});
                }}, 4000);
                </script>
                """,
                unsafe_allow_html=True,
            )
    except Exception:
        pass
    # Update total game time seconds when saving a game
    try:
        _duration = int(game_summary.get('time_taken') or game_summary.get('duration') or 0)
        update_global_counters(time_seconds_delta=_duration)
    except Exception:
        pass

    # Debug print for beat_word_count and full session state
    #print(f"[DEBUG] display_game_over: beat_word_count = {st.session_state.get('beat_word_count', 'MISSING')}")
    #print(f"[DEBUG] display_game_over: session_state = {dict(st.session_state)}")
    log_beat_word_count_event("GAME_OVER", st.session_state.get('beat_word_count', 'MISSING'))
    # --- FIX: Always inject correct words_solved for Beat mode ---
    if mode == "Beat":
        game_summary["words_solved"] = st.session_state.get("beat_word_count", 0)
        # Sync total penalty from current game if available
        try:
            _cg = st.session_state.get('game') if 'game' in st.session_state else None
            if _cg is not None and hasattr(_cg, 'total_penalty_points'):
                st.session_state['beat_total_points'] = int(getattr(_cg, 'total_penalty_points', 0))
                game_summary['total_penalty_points'] = int(getattr(_cg, 'total_penalty_points', 0))
        except Exception:
            pass
    else:
        # For non-Beat, if current game has penalties, carry them to summary
        try:
            _cg = st.session_state.get('game') if 'game' in st.session_state else None
            if _cg is not None and hasattr(_cg, 'total_penalty_points'):
                game_summary['total_penalty_points'] = int(getattr(_cg, 'total_penalty_points', 0))
        except Exception:
            pass

    # End the heartbeat session immediately on game over to avoid lingering counts
    try:
        sid = st.session_state.get('live_session_id') or st.session_state.get('current_round_id')
        if sid:
            end_live_session(sid)
    except Exception:
        pass
    # --- NEW: Save game result to user profile only once ---
    if not st.session_state.get('game_saved', False):
        save_game_to_user_profile(game_summary)
        st.session_state['game_saved'] = True
    # --- NEW: Update aggregates once per game over ---
    try:
        if not st.session_state.get('aggregates_updated', False):
            # Ensure timestamp exists for date bucketing
            if 'timestamp' not in game_summary or not game_summary.get('timestamp'):
                from datetime import datetime
                game_summary['timestamp'] = datetime.utcnow().isoformat()
            update_aggregates_with_game(game_summary)
            st.session_state['aggregates_updated'] = True
    except Exception as e:
        import logging
        logging.error(f"[AGGREGATES] update failed: {e}")
    # Add WizWord banner at the top
    stats_html = """
    <div class='wizword-banner'>
      <div class='wizword-banner-title'>WizWord</div>
      <div class='wizword-banner-stats'>
    """
    # Use live Beat score from session state if in Beat mode
    if mode == "Beat":
        # Use the live score from the GameLogic object if available
        if 'game' in st.session_state and st.session_state.game:
            score = st.session_state.game.score
            st.session_state['beat_score'] = score
        else:
            score = st.session_state.get('beat_score', 0)
    else:
        score = game_summary.get('score', 0)
    guesses = game_summary.get('guesses_made', len(game_summary.get('questions_asked', [])))
    hints = game_summary.get('max_hints', 7)
    hints_used = len(game_summary.get('hints_given', []))
    stats_html += f"<span class='wizword-stat'><b>🎮</b> {mode}</span>"
    # Add category/subject stat
    if 'subject' in game_summary:
        stats_html += f"<span class='wizword-stat wizword-beat-category'><b>📚</b> {game_summary['subject'].replace('_', ' ').title()}</span>"
    if mode == "Wiz":
        stats_html += f"<span class='wizword-stat'><b>🏆</b> {score}</span>"
        stats_html += f"<span class='wizword-stat'><b>🎯</b> {guesses}</span>"
    else:
        stats_html += f"<span class='wizword-stat'><b>🎯</b> {guesses}</span>"
    stats_html += "</div></div>"
    stats_html += """
    <style>
    .wizword-banner {
        display: flex;
        flex-direction: row;
        align-items: center;
        justify-content: space-between;
        background: linear-gradient(90deg, #FF6B6B 0%, #FFD93D 50%, #4ECDC4 100%);
        color: #fff;
        padding: 10px 24px 10px 24px;
        margin: 10px 0 18px 0;
        border-radius: 16px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.10),
                    inset 0 -2px 0px rgba(0, 0, 0, 0.07);
        -webkit-text-stroke: 1px #222;
        text-stroke: 1px #222;
        text-shadow: 1px 1px 4px rgba(0,0,0,0.13),
                     0 1px 4px rgba(0,0,0,0.08);
        transition: box-shadow 0.2s, background 0.2s;
        position: sticky;
        top: 0;
        z-index: 1000;
        backdrop-filter: blur(2px);
    }
    .wizword-banner-title {
        font-family: 'Baloo 2', 'Poppins', 'Arial Black', Arial, sans-serif !important;
        font-size: 1.5em;
        font-weight: 700;
        letter-spacing: 0.08em;
        margin-right: 24px;
        flex: 0 0 auto;
    }
    .wizword-banner-stats {
        display: flex;
        flex-direction: row;
        gap: 18px;
        font-size: 1.1em;
        font-weight: 600;
        align-items: center;
    }
    .wizword-stat {
        background: rgba(0,0,0,0.13);
        border-radius: 8px;
        padding: 4px 12px;
        margin-left: 0;
        margin-right: 0;
        min-width: 60px;
        text-align: center;
        box-shadow: 0 1px 2px rgba(0,0,0,0.07);
    }
    </style>
    """
    st.markdown(stats_html, unsafe_allow_html=True)
    # --- END FLEX BANNER ---
    _uname_go = (
        (st.session_state.get('user') or {}).get('username')
        or game_summary.get('nickname')
        or 'Player'
    )
    st.markdown(f"## 🎉 Game Over .. {_uname_go}")
    # (Block displaying last_word at the top for Beat mode has been deleted)

    # Show last chosen word in Beat mode
    if mode == "Beat":
        last_word = game_summary.get('selected_word') or game_summary.get('word', '')
        if last_word:
            st.markdown(f"""
                <div style='text-align:center; margin:1.5em 0 0.5em 0;'>
                    <span style="display:inline-block;font-size:2.4em;font-family:'Baloo 2','Poppins','Arial Black',sans-serif;font-weight:900;letter-spacing:0.18em;background:linear-gradient(90deg,#FFD93D 0%,#FF6B6B 50%,#4ECDC4 100%);-webkit-background-clip:text;-webkit-text-fill-color:transparent;text-shadow:2px 2px 8px rgba(0,0,0,0.13);padding:0.18em 0.7em;border-radius:0.4em;box-shadow:0 2px 8px rgba(0,0,0,0.10);\">{last_word.upper()}</span>
                </div>
            """, unsafe_allow_html=True)
    
    # Create tabs for different sections
    summary_tab, stats_tab, share_tab, stats_leader_tab = st.tabs(["Summary", "Statistics", "Share", "📈 My Stats & Leaderboard"])
    
    with summary_tab:
        # Remove duplicated top metrics row; consolidated strip is shown below the banner
        
        if mode == "Beat":
            
            # Compute SEI for this game
            words = game_summary.get('words_solved', 1)
            time_taken = game_summary.get('duration') or game_summary.get('time_taken', 0)
            try:
                denom = max(int(words or 0), 1)
                avg_score = (score / denom)
                avg_time = (time_taken / denom) if time_taken is not None else 0
                sei_val = (avg_score / avg_time) if avg_time > 0 else 0
            except Exception:
                sei_val = 0
            # (Removed: duplicate SEI box and words solved line; SEI is already shown in header and badges)
        else:
            st.markdown(f"**The word was:** {(game_summary.get('selected_word') or game_summary.get('word', '')).upper()}")
        # Remove Questions Asked section
        # if game_summary["questions_asked"]:
        #     st.markdown("### Questions Asked")
        #     for q in game_summary["questions_asked"]:
        #         st.markdown(f"- Q: {q['question']}\n  A: {q['answer']}")
    
    with stats_tab:
        # Performance graphs
        _uname_stats = (
            (st.session_state.get('user') or {}).get('username')
            or game_summary.get('nickname')
            or 'Player'
        )
        st.markdown(f"### {_uname_stats} performance")
        username = game_summary.get('nickname', '').lower()
        all_games = get_all_game_results()
        user_games = [g for g in all_games if g.get('nickname', '').lower() == username]
        # Filter user_games to only include games from the running category
        running_category = None
        if 'game' in st.session_state and st.session_state.game:
            running_category = getattr(st.session_state.game, 'subject', None)
        if not running_category:
            running_category = game_summary.get('subject', None)
        if running_category:
            user_games = [g for g in user_games if g.get('subject', '').lower() == running_category.lower()]
        if user_games:
            import matplotlib.pyplot as plt
            # ...
            import seaborn as sns
            import numpy as np
            import pandas as pd
            from datetime import datetime, timedelta
            plt.style.use('seaborn-v0_8')
            sns.set_palette("husl")
            # --- Running Average Score/Word & Time/Word vs. Game Date ---
            # Prepare data
            avg_scores = []
            avg_times = []
            sei_values = []
            game_dates = []
            total_score = 0
            total_time = 0
            total_words = 0
            for g in user_games:
                score = g.get('score', 0)
                words = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
                time_taken = g.get('time_taken', g.get('duration', None))
                date = g.get('timestamp')
                if time_taken is not None and date:
                    total_score += score
                    total_time += time_taken
                    total_words += words
                    denom = max(int(total_words or 0), 1)
                    avg_score = total_score / denom
                    avg_time = total_time / denom
                    sei = avg_score / avg_time if avg_time > 0 else 0
                    avg_scores.append(avg_score)
                    avg_times.append(avg_time)
                    sei_values.append(sei)
                    # Use only the date part for x-axis
                    if isinstance(date, str):
                        date = date.split('T')[0]
                    game_dates.append(date)
            if avg_scores and avg_times and sei_values and game_dates:
                # Append current game's SEI point to the graph if in Beat mode
                try:
                    if game_summary.get('mode') == 'Beat':
                        cur_date = (game_summary.get('timestamp') or '')[:10]
                        if cur_date:
                            game_dates.append(cur_date)
                            # Use current avg values computed above for consistency
                            _words = game_summary.get('words_solved', 1)
                            _time = game_summary.get('duration') or game_summary.get('time_taken', 0)
                            _den = max(int(_words or 0), 1)
                            avg_scores.append((score / _den) if (score := game_summary.get('score', 0)) or True else 0)
                            avg_times.append((_time / _den) if _time else 0)
                            _sei_val = (avg_scores[-1] / avg_times[-1]) if avg_times[-1] > 0 else 0
                            sei_values.append(_sei_val)
                except Exception:
                    pass
                fig, ax = plt.subplots(figsize=(6, 3))
                color1 = 'tab:blue'
                color2 = 'tab:orange'
                color3 = 'tab:green'
                ax.plot(game_dates, avg_scores, marker='o', linewidth=2, markersize=6, color=color1, label='Running Avg Score/Word')
                ax.set_xlabel('Game Date')
                ax.set_ylabel('Running Avg Score/Word', color=color1)
                ax.tick_params(axis='y', labelcolor=color1)
                ax.set_xticks(game_dates)
                ax.set_xticklabels(game_dates, rotation=45, ha='right', fontsize=8)
                ax2 = ax.twinx()
                ax2.plot(game_dates, avg_times, marker='s', linewidth=2, markersize=6, color=color2, label='Running Avg Time/Word (s)')
                ax2.set_ylabel('Running Avg Time per Word (sec)', color=color2)
                ax2.set_ylim(0, 300)
                ax2.tick_params(axis='y', labelcolor=color2)
                lines, labels = ax.get_legend_handles_labels()
                lines2, labels2 = ax2.get_legend_handles_labels()
                ax2.legend(lines + lines2, labels + labels2, loc='upper left')
                category_label = (game_summary.get('subject') or getattr(st.session_state.game, 'subject', None) or 'All Categories')
                ax.set_title(f"{category_label.title()} — Running Avg Score/Word & Time/Word vs. Game Date")
                fig.tight_layout()
                st.pyplot(fig)
                # Add a separate SEI line graph
                fig_sei, ax_sei = plt.subplots(figsize=(6, 3))
                ax_sei.plot(game_dates, sei_values, marker='^', linewidth=2, markersize=6, color=color3, label='SEI (Score/Time Index)')
                ax_sei.set_xlabel('Game Date')
                ax_sei.set_ylabel('SEI (Score/Time Index)', color=color3)
                category_label = (game_summary.get('subject') or getattr(st.session_state.game, 'subject', None) or 'All Categories')
                ax_sei.set_title(f"{category_label.title()} — Score Efficiency Index (SEI) per Game")
                # Match x-axis label styling to the main stats graph
                ax_sei.set_xticks(game_dates)
                ax_sei.set_xticklabels(game_dates, rotation=45, ha='right', fontsize=8)
                ax_sei.legend(loc='upper left')
                fig_sei.tight_layout()
                st.pyplot(fig_sei)
        # (Removed: recent games/results list from this tab)
    
    with share_tab:
        st.markdown("### 🔗 Share Your Achievement!")
        # Generate share card for this game
        if st.button("Generate Share Card"):
            with st.spinner("Generating share card..."):
                # In display_game_over, before calling create_share_card
                # Calculate total average score and time per word across all games for the user
                all_games = get_all_game_results()
                username = game_summary.get('nickname', '').lower()
                user_games = [g for g in all_games if g.get('nickname', '').lower() == username]
                total_score = sum(g.get('score', 0) for g in user_games)
                total_time = sum(g.get('time_taken', g.get('duration', 0)) for g in user_games)
                total_words = sum(g.get('words_solved', 1) for g in user_games)
                if int(total_words or 0) <= 0:
                    avg_score_per_word = 0
                    avg_time_per_word = 0
                else:
                    avg_score_per_word = round(total_score / total_words, 2)
                    avg_time_per_word = round(total_time / total_words, 2)
                sei = round(avg_score_per_word / avg_time_per_word, 2) if avg_time_per_word > 0 else 0
                # When calling create_share_card, pass avg_time_per_word as 'time_taken', avg_score_per_word as 'score', and sei as 'sei' in game_summary
                game_summary_for_card = dict(game_summary)
                game_summary_for_card['time_taken'] = avg_time_per_word
                game_summary_for_card['score'] = avg_score_per_word
                game_summary_for_card['sei'] = sei
                share_card_path = create_share_card(game_summary_for_card)
                if share_card_path:
                    st.session_state['share_card_path'] = share_card_path
                    st.image(share_card_path, caption="Your Share Card")
                    st.download_button(
                        "Download Share Card",
                        open(share_card_path, "rb"),
                        file_name="word_guess_share.png",
                        mime="image/png"
                    )
                # Display SEI in the share card tab
                st.markdown(f"**Score Efficiency Index (SEI):** {sei} points/sec")
        # --- New: Send by Email ---
        if st.session_state.get('share_card_path') and st.session_state.get('user') and st.session_state.user.get('email'):
            unique_id = f"{mode}_{game_summary.get('word','')}"
            game_summary_for_text = dict(game_summary)
            if mode == "Beat":
                game_summary_for_text["word"] = "--"
            share_text = share_utils.generate_share_text(game_summary_for_text)
            share_url = share_utils.generate_share_url(game_summary_for_text)
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                if st.button("Share on Twitter", key=f"share_twitter_btn_sharetab_{unique_id}"):
                    twitter_url = f"https://twitter.com/intent/tweet?text={share_text}&url={share_url}"
                    st.markdown(f"[Click to Tweet]({twitter_url})")
            with col2:
                if st.button("Share on Facebook", key=f"share_facebook_btn_sharetab_{unique_id}"):
                    fb_url = f"https://www.facebook.com/sharer/sharer.php?u={share_url}"
                    st.markdown(f"[Share on Facebook]({fb_url})")
            with col3:
                if st.button("Copy Link", key=f"share_copy_btn_sharetab_{unique_id}"):
                    st.code(share_url)
                    st.success("Link copied to clipboard!")
            with col4:
                email_to = st.session_state.user['email']
                email_subject = "Your WizWord Share Card"
                email_body = "Congratulations! Here is your WizWord share card."
                if st.button("Send Share Card by Email", key=f"share_email_btn_sharetab_{unique_id}"):
                    from backend.user_auth import send_share_card_email
                    with st.spinner("Sending email..."):
                        sent = send_share_card_email(email_to, email_subject, email_body, st.session_state['share_card_path'])
                        if sent:
                            st.success(f"Share card sent to {email_to}!")
                        else:
                            st.error("Failed to send share card by email. Please try again later.")
        # --- NEW: Generate and display highest score share card for this month ---
        from backend.share_card import create_monthly_high_score_share_card
        stats_manager = None
        if hasattr(st.session_state.game, 'stats_manager'):
            stats_manager = st.session_state.game.stats_manager
        if stats_manager and st.button("Show My Highest Score This Month Card"):
            with st.spinner("Generating monthly high score share card..."):
                high_score_card_path = create_monthly_high_score_share_card(stats_manager)
                if not high_score_card_path:
                    # Fallback: use current game_summary if it belongs to current month
                    from datetime import datetime, timezone
                    try:
                        ts = game_summary.get('timestamp') or game_summary.get('end_time')
                        if not ts:
                            raise ValueError('no timestamp')
                        if isinstance(ts, (int, float)):
                            cur_month = datetime.fromtimestamp(ts, tz=timezone.utc).strftime('%Y-%m')
                        else:
                            cur_month = str(ts)[:7]
                        now_month = datetime.now(timezone.utc).strftime('%Y-%m')
                        if cur_month == now_month and stats_manager:
                            # Temporarily inject the current game as the "highest" for this month
                            # by creating a share card directly from game_summary aggregates
                            gs = dict(game_summary)
                            gs['sei'] = None  # let the card compute from provided averages if any
                            # Compute per-word averages if missing
                            score = gs.get('score', 0)
                            time_taken = gs.get('time_taken', gs.get('duration', 0))
                            words = gs.get('words_solved', 1) if gs.get('mode') == 'Beat' else 1
                            denom = max(int(words or 0), 1)
                            gs['time_taken'] = round((time_taken/denom) if time_taken else 0, 2)
                            gs['score'] = round((score/denom), 2)
                            high_score_card_path = create_share_card(gs, is_monthly=True)
                    except Exception:
                        pass
                if high_score_card_path:
                    st.session_state['monthly_high_score_card_path'] = high_score_card_path
                    st.image(high_score_card_path, caption="Your Highest Score This Month")
                    st.download_button(
                        "Download Monthly High Score Card",
                        open(high_score_card_path, "rb"),
                        file_name="monthly_high_score_card.png",
                        mime="image/png"
                    )
                else:
                    st.info("No high score card available for this month.")
        # --- Always show email button if card exists ---
        if st.session_state.get('monthly_high_score_card_path') and st.session_state.get('user') and st.session_state.user.get('email'):
            email_to = st.session_state.user['email']
            email_subject = "Your WizWord Monthly High Score Card"
            email_body = "Congratulations! Here is your WizWord monthly high score card."
            if st.button("Send Monthly High Score Card by Email", key=f"share_email_btn_monthly_{email_to}"):
                from backend.user_auth import send_share_card_email
                with st.spinner("Sending email..."):
                    sent = send_share_card_email(email_to, email_subject, email_body, st.session_state['monthly_high_score_card_path'])
                    if sent:
                        st.success(f"Monthly high score card sent to {email_to}!")
                    else:
                        st.error("Failed to send monthly high score card by email. Please try again later.")
        
        # Share buttons
        share_text = share_utils.generate_share_text(game_summary)
        share_url = share_utils.generate_share_url(game_summary)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Share on Twitter", key="share_twitter_btn_sharetab"):
                twitter_url = f"https://twitter.com/intent/tweet?text={share_text}&url={share_url}"
                st.markdown(f"[Click to Tweet]({twitter_url})")
        with col2:
            if st.button("Share on Facebook", key="share_facebook_btn_sharetab"):
                fb_url = f"https://www.facebook.com/sharer/sharer.php?u={share_url}"
                st.markdown(f"[Share on Facebook]({fb_url})")
        with col3:
            if st.button("Copy Link", key="share_copy_btn_sharetab"):
                st.code(share_url)
                st.success("Link copied to clipboard!")
    
    with stats_leader_tab:
        st.markdown("## 📈 My Historical Stats")
        username = game_summary.get('nickname', '').lower()
        all_games = get_all_game_results()
        user_games = [g for g in all_games if g.get('nickname', '').lower() == username]
        if user_games:
            col1, col2, col3 = st.columns(3)
            total_games = len(user_games)
            best_score = max((g.get('score', 0) for g in user_games), default=0)
            avg_score = sum(g.get('score', 0) for g in user_games) / total_games if total_games else 0
            total_time = sum(g.get('time_taken', 0) for g in user_games)
            favorite_category = max(
                set(g.get('subject') for g in user_games),
                key=lambda cat: sum(1 for g in user_games if g.get('subject') == cat),
                default=None
            )
            with col1:
                st.metric("Total Games", total_games)
                st.metric("Best Score", best_score)
            with col2:
                st.metric("Avg Score", round(avg_score, 1))
                st.metric("Total Time", format_duration(total_time))
            with col3:
                st.metric("Favorite Category", favorite_category or "-")
            # Average SEI across all user games
            try:
                total_words_all = sum((g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1) for g in user_games)
                denom_all = max(int(total_words_all or 0), 1)
                avg_score_per_word_all = (sum(g.get('score', 0) for g in user_games) / denom_all)
                avg_time_per_word_all = (sum(g.get('time_taken', g.get('duration', 0)) for g in user_games) / denom_all)
                avg_sei_all = (avg_score_per_word_all / avg_time_per_word_all) if avg_time_per_word_all > 0 else 0
            except Exception:
                avg_sei_all = 0
            st.markdown(
                f"""
                <div style="display:flex; gap:18px; margin: 6px 0 12px 0;">
                    <div style="background: rgba(255,255,255,0.04); border: 1px solid rgba(255,255,255,0.08); border-radius: 10px; padding: 8px 12px;">
                        <div style="font-size: 0.82em; color: #9CA3AF; font-weight: 600;">Average SEI (Score/Time Index)</div>
                        <div style="font-size: 1.35em; color: #ff3b30; font-weight: 800;">{avg_sei_all:.2f}</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            st.markdown("**Recent Games:**")
            for g in user_games[-5:][::-1]:
                date_str = g.get('end_time') or g.get('timestamp')
                if date_str:
                    try:
                        if isinstance(date_str, (float, int)):
                            from datetime import datetime
                            date_str = datetime.fromtimestamp(date_str).strftime('%Y-%m-%d')
                        else:
                            date_str = str(date_str)[:10]
                    except Exception:
                        date_str = str(date_str)[:10]
                # Compute SEI per game
                score_g = g.get('score', 0)
                time_taken_g = g.get('time_taken', g.get('duration', 0))
                words_g = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
                denom_g = max(int(words_g or 0), 1)
                avg_score_g = (score_g / denom_g)
                avg_time_g = (time_taken_g / denom_g)
                sei_g = (avg_score_g / avg_time_g) if avg_time_g > 0 else 0
                st.markdown(f"- {g.get('subject','?').title()} | {g.get('mode','?')} | SEI: {sei_g:.2f} | {date_str}")
        else:
            st.info("No games played yet.")
        st.markdown("---")
    # Default leaderboard category to current session's category
    leaderboard_category = None
    if 'game' in st.session_state and st.session_state.game:
        leaderboard_category = getattr(st.session_state.game, 'subject', None)
    if not leaderboard_category:
        leaderboard_category = game_summary.get('subject', None)
    if not leaderboard_category:
        leaderboard_category = 'All Categories'
    # Show current game's SEI alongside the leaderboard header
    try:
        _score_cur = game_summary.get('score', 0)
        _time_cur = game_summary.get('time_taken', game_summary.get('duration', 0))
        _words_cur = game_summary.get('words_solved', 1) if game_summary.get('mode') == 'Beat' else 1
        _denom_cur = max(int(_words_cur or 0), 1)
        _avg_score_cur = _score_cur / _denom_cur
        _avg_time_cur = (_time_cur / _denom_cur) if _time_cur else 0
        _sei_cur_display = (_avg_score_cur / _avg_time_cur) if _avg_time_cur > 0 else None
    except Exception:
        _sei_cur_display = None
    # Show "Your SEI" at the top of the Summary section
    _your_sei_value = (_sei_cur_display if _sei_cur_display is not None else 0)
    st.markdown(
        f"<div style='font-size:1.2em; font-weight:900; color:#ff3b30; margin: 6px 0 6px 0; text-align:center;'>Your SEI : {_your_sei_value:.2f}</div>",
        unsafe_allow_html=True,
    )
    # Pill badges: Final Score, Words Solved, Total Penalty (moved above Global Leaderboard)
    try:
        _final_score = int(game_summary.get('score', 0))
        _penalty = int(game_summary.get('total_penalty_points', 0))
        _words_solved = int(game_summary.get('words_solved', 0))
        st.markdown(
            f"""
            <div style='display:flex; gap:14px; align-items:center; justify-content:center; margin:8px 0 10px 0;'>
                <span style='background:#FFEDD5;color:#9A3412;font-weight:900;border-radius:10px;padding:6px 12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);'>Final Score: {_final_score}</span>
                <span style='background:#DCFCE7;color:#065F46;font-weight:900;border-radius:10px;padding:6px 12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);'>Words Solved: {_words_solved}</span>
                <span style='background:#FEE2E2;color:#991B1B;font-weight:900;border-radius:10px;padding:6px 12px;box-shadow:0 1px 3px rgba(0,0,0,0.08);'>Total Penalty: {_penalty}</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    except Exception:
        pass
    # Global Leaderboard header without the inline Your SEI
    st.markdown(f"""
    <div style='font-size:1.1em; font-weight:700; color:#fff; margin-bottom:0.5em;'>
        🏆 Global Leaderboard (Top 3 by SEI) - {leaderboard_category.title() if leaderboard_category != 'All Categories' else 'All Categories'}
    </div>
    """, unsafe_allow_html=True)
    user_sei = {}
    for g in all_games:
        user = g.get('nickname', '').lower()
        game_category = g.get('subject', '').lower()
        if leaderboard_category and leaderboard_category.lower() != 'all categories' and game_category != leaderboard_category.lower():
            continue

        score = g.get('score', 0)
        time_taken = g.get('time_taken', g.get('duration', 0))
        words = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
        denom = max(int(words or 0), 1)
        avg_score = score / denom
        avg_time = time_taken / denom
        sei = avg_score / avg_time if avg_time > 0 else 0
        # Only keep the highest SEI for each user in this category
        if user not in user_sei or sei > user_sei[user]:
            user_sei[user] = sei
    # Email congrats when current game achieves highest SEI in this leaderboard category
    try:
        current_user = (game_summary.get('nickname', '') or '').lower()
        current_category = (leaderboard_category or game_summary.get('subject', '') or '').lower()
        score_cur = game_summary.get('score', 0)
        time_cur = game_summary.get('time_taken', game_summary.get('duration', 0))
        words_cur = game_summary.get('words_solved', 1) if game_summary.get('mode') == 'Beat' else 1
        denom_cur = max(int(words_cur or 0), 1)
        avg_score_cur = score_cur / denom_cur
        avg_time_cur = (time_cur / denom_cur) if time_cur else 0
        sei_cur = (avg_score_cur / avg_time_cur) if avg_time_cur > 0 else None
        if sei_cur is not None:
            if leaderboard_category and leaderboard_category.lower() != 'all categories':
                highest_sei_in_cat = max(user_sei.values()) if user_sei else None
            else:
                highest_sei_in_cat = None
                for g in all_games:
                    if g.get('subject', '').lower() == current_category:
                        # Exclude current game if already saved
                        try:
                            _cur_ts = game_summary.get('timestamp')
                            if _cur_ts and g.get('timestamp') == _cur_ts:
                                continue
                        except Exception:
                            pass
                        s = g.get('score', 0)
                        t = g.get('time_taken', g.get('duration', 0))
                        w = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
                        d = max(int(w or 0), 1)
                        asw = s / d
                        atw = (t / d) if t else 0
                        sei_val = (asw / atw) if atw > 0 else None
                        if sei_val is not None and (highest_sei_in_cat is None or sei_val > highest_sei_in_cat):
                            highest_sei_in_cat = sei_val
            # Skip sending if current SEI is exactly zero
            zero_sei = isinstance(sei_cur, (int, float)) and abs(sei_cur) < 1e-12
            is_new_high = (not zero_sei) and ((highest_sei_in_cat is None) or (sei_cur > (highest_sei_in_cat + 1e-9)))
            users = st.session_state.get('users', {}) if isinstance(st.session_state.get('users'), dict) else {}
            recipient = users.get(current_user, {}).get('email')
            admin_email = os.getenv('ADMIN_EMAIL') or os.getenv('SMTP_USER')
            has_smtp = bool(os.getenv('SMTP_HOST') and os.getenv('SMTP_USER') and os.getenv('SMTP_PASS'))
            
            if is_new_high and recipient and has_smtp:
                try:
                    from backend.share_card import create_congrats_sei_card
                    share_card_path = create_congrats_sei_card(current_user, current_category, sei_cur)
                except Exception:
                    share_card_path = None
                subject = f"🎉 Congratulations — Global Top SEI in {current_category.title()}!"
                body = (
                    f"Congratulations {current_user}! You just achieved the global top SEI (Score/Time Index) in "
                    f"the {current_category.title()} category. Keep it up!"
                )
                
                try:
                    sent_ok = send_email_with_attachment([recipient], subject, body, attachment_path=share_card_path, cc_emails=[admin_email] if admin_email else None)
                    
                    # Show celebration animation immediately on Game Over after achieving top SEI
                    cat_title = current_category.title()
                    st.markdown(
                        f"""
                        <style>
                        @keyframes flyTrophy {{
                          0% {{ transform: translate(0, 0) scale(1); opacity: 0; }}
                          10% {{ opacity: 1; }}
                          90% {{ transform: translate(-50vw, -30vh) scale(1.2); opacity: 1; }}
                          100% {{ transform: translate(-52vw, -32vh) scale(1.2); opacity: 0; }}
                        }}
                        .trophy-fly {{
                          position: fixed; right: 16px; bottom: 16px; font-size: 48px; z-index: 999999;
                          animation: flyTrophy 2.6s ease-in-out forwards; pointer-events: none;
                        }}
                        @keyframes riseBanner {{
                          0% {{ transform: translate(-50%, 120%); opacity: 0; }}
                          10% {{ opacity: 1; }}
                          100% {{ transform: translate(-50%, -10vh); opacity: 1; }}
                        }}
                        .banner-fly {{
                          position: fixed; left: 50%; bottom: -80px; transform: translate(-50%, 120%);
                          z-index: 999998; background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 100%);
                          color: #222; font-weight: 800; border-radius: 12px; padding: 12px 18px; margin: 0;
                          box-shadow: 0 4px 14px rgba(0,0,0,0.18); animation: riseBanner 1.8s ease-out forwards;
                          pointer-events: none; white-space: nowrap;
                        }}
                        @keyframes floatBalloon {{
                          0% {{ transform: translateY(0) translateX(0); opacity: 0; }}
                          10% {{ opacity: 1; }}
                          100% {{ transform: translateY(-60vh) translateX(-10px); opacity: 1; }}
                        }}
                        .balloon {{ position: fixed; bottom: -24px; font-size: 32px; z-index: 999997; animation: floatBalloon 3s ease-in forwards; pointer-events: none; }}
                        </style>
                        <div class=\"trophy-fly\">🏆</div>
                        <div class=\"banner-fly\">🎉 Congratulations! Global Top SEI — <b>{cat_title}</b> 🎉</div>
                        <span class=\"balloon\" style=\"left:20%; animation-delay: .0s;\">🎈</span>
                        <span class=\"balloon\" style=\"left:35%; animation-delay: .2s;\">🎈</span>
                        <span class=\"balloon\" style=\"left:50%; animation-delay: .4s;\">🎈</span>
                        <span class=\"balloon\" style=\"left:65%; animation-delay: .1s;\">🎈</span>
                        <span class=\"balloon\" style=\"left:80%; animation-delay: .3s;\">🎈</span>
                        <script>
                        setTimeout(function(){{ var t = document.querySelector('.trophy-fly'); if(t) t.remove(); }}, 1900);
                        setTimeout(function(){{ var b = document.querySelector('.banner-fly'); if(b) b.remove(); }}, 2200);
                        setTimeout(function(){{ document.querySelectorAll('.balloon').forEach(function(el){{ el.remove(); }}); }}, 4000);
                        </script>
                        """,
                        unsafe_allow_html=True,
                    )
                except Exception as e:
                    pass
            else:
                # Log reasons for not sending
                if zero_sei:
                    pass
                if not is_new_high and not zero_sei:
                    pass
                if not recipient:
                    pass
                if not has_smtp:
                    print("[DEBUG][SEI_EMAIL] Not sending: SMTP env vars missing (SMTP_HOST/SMTP_USER/SMTP_PASS).")
    except Exception as e:
        print(f"[DEBUG][SEI_EMAIL] Exception in email logic: {e}")
    # (Removed duplicate consolidated summary strip here; badges are shown above the leaderboard)

    # Sort users by highest SEI
    top_users = sorted(user_sei.items(), key=lambda x: x[1], reverse=True)[:3]
    rows = []
    for u, v in top_users:
        dates = []
        for gg in all_games:
            if leaderboard_category and leaderboard_category.lower() != 'all categories' and (gg.get('subject','') or '').lower() != leaderboard_category.lower():
                continue
            if (gg.get('nickname','') or '').lower() != u:
                continue
            sc = gg.get('score', 0); tt = gg.get('time_taken', gg.get('duration', 0))
            wd = gg.get('words_solved', 1) if gg.get('mode') == 'Beat' else 1
            dn = max(int(wd or 0), 1)
            avs = sc / dn; avt = tt / dn if tt else 0
            sei_u = avs / avt if avt > 0 else None
            if sei_u is not None and abs(sei_u - v) < 1e-9:
                dates.append(str(gg.get('timestamp') or gg.get('end_time') or '')[:10])
        last = sorted([d for d in dates if d], reverse=True)[0] if dates else ''
        rows.append({'User': u, 'Highest SEI': round(v,2), 'Date': last})
    st.table(rows)
    # After all tabs (summary_tab, stats_tab, share_tab, stats_leader_tab), restore the play again and restart buttons
    col1, col2 = st.columns(2)
    with col1:
        current_mode = getattr(st.session_state.game, 'mode', None)
        another_label = '🔄 Another Beat' if current_mode == 'Beat' else '🔄 Another Word'
        if st.button(another_label, key='play-again-btn'):
            log_beat_word_count_event("RESET_PLAY_AGAIN", st.session_state.get('beat_word_count', 'MISSING'))
            st.session_state['restart_game'] = False
            if current_mode == 'Beat':
                import random
                new_word_length = random.randint(3, 10)
                user_profile = st.session_state.get('user', {})
                default_category = user_profile.get('default_category', 'general')
                _enable_personal_again = os.getenv('ENABLE_PERSONAL_CATEGORY', 'true').strip().lower() in ('1','true','yes','on')
                if not _enable_personal_again and str(default_category).lower() == 'personal':
                    default_category = 'general'
                    try:
                        if 'user' in st.session_state and st.session_state['user']:
                            st.session_state['user']['default_category'] = 'general'
                        users_db = st.session_state.get('users', {})
                        uname = (st.session_state.get('user', {}) or {}).get('username') or ''
                        if uname in users_db:
                            users_db[uname]['default_category'] = 'general'
                            save_users(users_db)
                        elif uname.lower() in users_db:
                            users_db[uname.lower()]['default_category'] = 'general'
                            save_users(users_db)
                    except Exception:
                        pass
                new_subject = default_category if default_category else 'general'
                print(f"[DEBUG][Another Beat] Restarting Beat mode with subject: {new_subject}")
                st.session_state.beat_word_count = 0
                st.session_state.beat_score = 0
                st.session_state.beat_time_left = BEAT_MODE_TIMEOUT_SECONDS
                st.session_state.beat_start_time = time.time()
                st.session_state['beat_started'] = False
                # Reset Beat penalty/session accumulators
                st.session_state['beat_total_points'] = 0
                st.session_state['beat_total_penalty'] = 0
                st.session_state.game = GameLogic(
                    word_length=new_word_length,
                    subject=new_subject,
                    mode='Beat',
                    nickname=st.session_state.user['username'],
                    difficulty=st.session_state.game.difficulty if hasattr(st.session_state.game, 'difficulty') else 'Medium'
                )
                st.session_state.game_over = False
                st.session_state.game_summary = None
                st.session_state['play_again'] = False
                st.session_state['just_finished_game'] = False
                st.rerun()
            else:
                st.session_state['play_again'] = True
                st.rerun()
    with col2:
        if st.button('🚪 Log Out', key='logout-after-game-btn'):
            # Log and clear entire session to log out
            log_beat_word_count_event("LOGOUT_AFTER_GAME", st.session_state.get('beat_word_count', 'MISSING'))
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

def reset_game():
    # Clear Beat mode stats
    for key in [
        "beat_word_count", "beat_score", "beat_time_left", "beat_start_time",
        "last_beat_hint", "clear_guess_field", "beat_questions", "beat_hints",
        "beat_guesses", "_last_beat_word_count", "show_word_for_count", "show_word_until", "show_word",
        "show_history"  # <-- add this line
    ]:
        if key in st.session_state:
            del st.session_state[key]
    st.session_state['game'] = None
    if "game_over" in st.session_state:
        del st.session_state.game_over
    if "game_summary" in st.session_state:
        del st.session_state.game_summary

def format_duration(seconds):
    """Format duration in seconds to readable time."""
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    if minutes == 0:
        return f"{seconds}s"
    return f"{minutes}m {seconds}s"

def display_game_stats(game):
    """Display game statistics."""
    st.markdown("### Game Stats")
    
    # Create columns for stats
    cols = st.columns(5)  # Changed to 5 columns to include difficulty
    
    with cols[0]:
        st.metric("Score", game.score)
    with cols[1]:
        st.metric("Questions Asked", len(game.questions_asked))
    with cols[2]:
        st.metric("Guesses Made", game.guesses_made)
    with cols[3]:
        st.metric("Hints Used", len(game.hints_given))
    with cols[4]:
        st.metric("Difficulty", game.difficulty)
        
    # Display available hints and their status
    st.markdown("### Available Hints")
    max_hints = game.current_settings["max_hints"]  # Get max hints from settings
    for i, hint in enumerate(game.available_hints, 1):
        if i <= max_hints:  # Only show hints up to the difficulty limit
            hint_used = hint in game.hints_given
            status = "✓" if hint_used else "○"
            st.markdown(f"{status} Hint {i}: " + ("*[Used]* " if hint_used else "") + hint)


def ensure_beat_mode_state():
    if "beat_word_count" not in st.session_state:
        st.session_state.beat_word_count = 0
    if "beat_score" not in st.session_state:
        st.session_state.beat_score = 0
    if "beat_time_left" not in st.session_state:
        st.session_state.beat_time_left = BEAT_MODE_TIMEOUT_SECONDS
    if "beat_start_time" not in st.session_state:
        st.session_state.beat_start_time = time.time()
    if "last_beat_hint" not in st.session_state:
        st.session_state.last_beat_hint = ""
    if "clear_guess_field" not in st.session_state:
        st.session_state.clear_guess_field = False

def highlight_letters_in_hint(hint):
    # Highlight single letters in quotes or patterns like 'The first letter is 'A''
    # Use a pill-shaped background, larger font, bold, and more spacing
    def replacer(match):
        letter = match.group(1)
        return (
            "<span style='display:inline-block; background:#FF6B6B; color:#fff; "
            "font-weight:bold; font-size:1.5em; padding:0.15em 0.7em; margin:0 0.15em; "
            "border-radius:1em; box-shadow:0 1px 4px rgba(0,0,0,0.10); letter-spacing:0.1em;'>"
            f"{letter.upper()}"
            "</span>"
        )
    # Replace patterns like 'letter is 'A'' or 'letter is "A"'
    hint = re.sub(r"letter is ['\"]([a-zA-Z])['\"]", replacer, hint)
    # Replace patterns like 'letter 'A'' or 'letter "A"'
    hint = re.sub(r"letter ['\"]([a-zA-Z])['\"]", replacer, hint)
    # Replace patterns like 'starts with 'A'' or 'ends with 'Z''
    hint = re.sub(r"with ['\"]([a-zA-Z])['\"]", replacer, hint)
    return hint

# In display_hint_section and display_game_stats, use st.markdown with unsafe_allow_html=True for hints

def display_game_stats(game):
    st.markdown("### Game Stats")
    cols = st.columns(5)
    with cols[0]:
        st.metric("Score", game.score)
    with cols[1]:
        st.metric("Questions Asked", len(game.questions_asked))
    with cols[2]:
        st.metric("Guesses Made", game.guesses_made)
    with cols[3]:
        st.metric("Hints Used", len(game.hints_given))
    with cols[4]:
        st.metric("Difficulty", game.difficulty)
    st.markdown("### Available Hints")
    max_hints = game.current_settings["max_hints"]
    for i, hint in enumerate(game.available_hints, 1):
        if i <= max_hints:
            hint_used = hint in game.hints_given
            status = "✓" if hint_used else "○"
            styled_hint = highlight_letters_in_hint(hint)
            st.markdown(f"{status} Hint {i}: " + ("*[Used]* " if hint_used else "") + styled_hint, unsafe_allow_html=True)



def display_hint_section(game):
    # Auto-show first hint per round for free
    try:
        cur_round = st.session_state.get('current_round_id')
        if (len(game.hints_given) == 0) and (st.session_state.get('first_hint_round_id') != cur_round):
            hint, points = game.get_hint()
            # Refund penalty if any so first hint is free
            try:
                if isinstance(points, (int, float)) and points < 0:
                    refund = abs(points)
                    game.score += refund
                    if hasattr(game, 'total_points'):
                        game.total_points += refund
                    if hasattr(game, 'total_penalty_points'):
                        game.total_penalty_points = max(0, int(game.total_penalty_points) - refund)
                    st.session_state['beat_total_points'] = int(getattr(game, 'total_penalty_points', 0)) if hasattr(game, 'total_penalty_points') else st.session_state.get('beat_total_points', 0)
            except Exception:
                pass
            st.session_state['first_hint_round_id'] = cur_round
    except Exception:
        pass

    # Allow up to 2 extra hints (each -10)
    max_extra = 2
    extra_used = max(len(game.hints_given) - 1, 0)
    remaining = max(0, max_extra - extra_used)

    # Build the current hint text (last hint or placeholder)
    if game.hints_given:
        current_text = highlight_letters_in_hint(game.hints_given[-1])
    else:
        current_text = "Tap for a hint"

    # Render a visual card with a full-size invisible overlay button (preferred visual card approach)
    st.markdown(
        """
        <style>
        .hint-card-wrap { position: relative; width: 100% !important; }
        .hint-card-visual {
            background: linear-gradient(90deg, #FFEA00 0%, #FF8A80 45%, #80F7D3 100%);
            border-radius: 18px; border: 3px solid rgba(255,255,255,0.55);
            box-shadow: 0 10px 28px rgba(0,0,0,0.22), 0 0 0 6px rgba(255,255,255,0.08) inset;
            color: #0b1220; font-weight: 900; letter-spacing: 0.01em;
            padding: 0.8em 1em; margin: 0.4em 0 0.2em 0; text-align: center;
            width: 100%; max-width: 100%;
            font-size: clamp(1.26em, 4.32vw, 2.34em);
            line-height: 1.35; word-break: break-word; overflow-wrap: anywhere; white-space: normal;
            text-shadow: 0 2px 6px rgba(0,0,0,0.18);
        }
        .hint-card-cta { display:none; }
        .hint-card-wrap .stButton>button {
            position: absolute; inset: 0; width: 100%; height: 100%; opacity: 0;
            background: transparent !important; border: none !important; box-shadow: none !important;
            cursor: pointer;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div class='hint-card-wrap'>", unsafe_allow_html=True)
    st.markdown(f"<div class='hint-card-visual'>💡 {current_text}</div>", unsafe_allow_html=True)
    _hint_btn_label = ("Click for next hint" if remaining > 0 else "No more hints")
    clicked = st.button(_hint_btn_label, key="hint_card_click", help=("Tap for next hint" if remaining > 0 else "No more hints available"), use_container_width=True, disabled=(remaining == 0))
    st.markdown("</div>", unsafe_allow_html=True)
    if clicked and remaining > 0:
                hint, points = game.get_hint()
                try:
                    if hasattr(game, 'total_penalty_points'):
                        st.session_state['beat_total_points'] = int(getattr(game, 'total_penalty_points', 0))
                    if isinstance(points, (int, float)) and points < 0:
                        st.session_state['beat_total_penalty'] = int(st.session_state.get('beat_total_penalty', 0)) + abs(points)
                except Exception:
                    pass
                st.rerun()

def log_beat_word_count_event(event, value):
    with open("beat_word_count_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{event}: beat_word_count = {value}\n")

GAME_RESULTS_PATH = os.environ.get('GAME_RESULTS_PATH', 'game_results.json')
AGGREGATES_PATH = os.environ.get('AGGREGATES_PATH', 'game_data/aggregates.json')

def save_game_to_user_profile(game_summary):
    import os, json
    game_file = GAME_RESULTS_PATH
    # Ensure timestamp exists
    if 'timestamp' not in game_summary:
        from datetime import datetime
        game_summary['timestamp'] = datetime.utcnow().isoformat()
    # Ensure nickname exists
    if 'nickname' not in game_summary or not game_summary['nickname']:
        import streamlit as st
        game_summary['nickname'] = st.session_state.get('nickname', 'unknown').lower()
    # Remove hint-related fields
    for key in ['hints_given', 'max_hints', 'questions_asked', 'available_hints']:
        if key in game_summary:
            del game_summary[key]
    # Load or initialize grouped results
    if os.path.exists(game_file):
        with open(game_file, "r", encoding="utf-8") as f:
            all_games = json.load(f)
    else:
        all_games = {}
    user = game_summary['nickname']
    if user not in all_games:
        all_games[user] = []
    all_games[user].append(dict(game_summary))
    with open(game_file, "w", encoding="utf-8") as f:
        json.dump(all_games, f, indent=2)
        abs_path = os.path.abspath(game_file)
        try:
            mtime = os.path.getmtime(game_file)
            import datetime
            mtime_str = datetime.datetime.fromtimestamp(mtime).isoformat()
        except Exception as e:
            mtime_str = f"(could not get mtime: {e})"
        import logging
        logging.info(f"[DEBUG] game_results.json path: {abs_path}, last modified: {mtime_str}")
        print(f"[DEBUG] game_results.json path: {abs_path}, last modified: {mtime_str}")

    # Also persist per-user games count in users.json for admin scalability
    try:
        users_path = USERS_FILE
        users_data = {}
        if os.path.exists(users_path):
            with open(users_path, 'r', encoding='utf-8') as uf:
                users_data = json.load(uf)
        username = str(game_summary.get('nickname', '')).lower()
        if username:
            if username not in users_data:
                users_data[username] = { 'username': username }
            # Initialize and increment games_count
            current = users_data[username].get('games_count', 0)
            users_data[username]['games_count'] = int(current) + 1
            # Keep only the last game timestamp (do not store all dates to avoid file bloat)
            last_ts = game_summary.get('timestamp')
            users_data[username]['last_game_time'] = last_ts
            # If an old array exists from earlier versions, collapse it to last item
            if isinstance(users_data[username].get('recent_game_times'), list):
                hist = users_data[username]['recent_game_times']
                users_data[username]['last_game_time'] = hist[-1] if hist else last_ts
                users_data[username].pop('recent_game_times', None)
            with open(users_path, 'w', encoding='utf-8') as uf:
                json.dump(users_data, uf, indent=2)
            # Sync in-memory session users map so admin view reflects immediately
            try:
                if 'users' in st.session_state and isinstance(st.session_state['users'], dict):
                    if username not in st.session_state['users']:
                        st.session_state['users'][username] = {}
                    st.session_state['users'][username]['games_count'] = users_data[username]['games_count']
                    st.session_state['users'][username]['last_game_time'] = users_data[username].get('last_game_time')
            except Exception:
                pass
    except Exception as e:
        import logging
        logging.warning(f"[USERS.GAMES_COUNT] failed to update users.json: {e}")

def load_all_users():
    with open("users.json", "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_game_results():
    import os, json
    game_file = GAME_RESULTS_PATH
    if not os.path.exists(game_file):
        return []
    with open(game_file, "r", encoding="utf-8") as f:
        all_games = json.load(f)
    # Flatten to a list of games with user info
    results = []
    for user, games in all_games.items():
        for game in games:
            game = dict(game)
            game['nickname'] = user
            results.append(game)
    return results

def get_global_leaderboard(top_n=10, mode=None, category=None):
    games = get_all_game_results()
    if mode and mode != "All":
        games = [g for g in games if g.get("mode") == mode]
    if category and category != "All":
        games = [g for g in games if g.get("subject") == category]
    games.sort(key=lambda g: g.get("score", 0), reverse=True)
    return games[:top_n]

def get_user_stats(username):
    users = load_all_users()
    user = users.get(username.lower())
    if not user or "games" not in user:
        return {}
    games = user["games"]
    total_games = len(games)
    best_score = max((g.get("score", 0) for g in games), default=0)
    avg_score = sum(g.get("score", 0) for g in games) / total_games if total_games else 0
    total_time = sum(g.get("time_taken", 0) for g in games)
    favorite_category = max(
        set(g.get("subject") for g in games),
        key=lambda cat: sum(1 for g in games if g.get("subject") == cat),
        default=None
    )
    return {
        "total_games": total_games,
        "best_score": best_score,
        "avg_score": avg_score,
        "total_time": total_time,
        "favorite_category": favorite_category,
        "recent_games": games[-5:][::-1],  # Last 5 games, most recent first
    }

def format_duration(seconds):
    minutes = int(seconds // 60)
    seconds = int(seconds % 60)
    if minutes == 0:
        return f"{seconds}s"
    return f"{minutes}m {seconds}s"

def _ensure_aggregates_file() -> None:
    try:
        os.makedirs(os.path.dirname(AGGREGATES_PATH) or '.', exist_ok=True)
        if not os.path.exists(AGGREGATES_PATH):
            with open(AGGREGATES_PATH, 'w', encoding='utf-8') as f:
                json.dump({'category_user_highest': {}, 'user_time_series': {}}, f, indent=2)
    except Exception:
        pass

def _load_aggregates() -> dict:
    _ensure_aggregates_file()
    try:
        with open(AGGREGATES_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {'category_user_highest': {}, 'user_time_series': {}}

def _save_aggregates(data: dict) -> None:
    try:
        with open(AGGREGATES_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass

def update_aggregates_with_game(game_summary: dict) -> None:
    try:
        # Compute per-word metrics and SEI
        score = game_summary.get('score', 0)
        time_taken = game_summary.get('time_taken', game_summary.get('duration', 0))
        words = game_summary.get('words_solved', 1) if game_summary.get('mode') == 'Beat' else 1
        denom = max(int(words or 0), 1)
        avg_score = (score / denom)
        avg_time = (time_taken / denom) if time_taken else 0
        sei = (avg_score / avg_time) if avg_time > 0 else 0
        user = (game_summary.get('nickname', '') or '').lower()
        category = (game_summary.get('subject', '') or '').lower()
        date_str = (game_summary.get('timestamp') or game_summary.get('end_time') or '')[:10]
        agg = _load_aggregates()
        # Update category_user_highest
        cat_map = agg.setdefault('category_user_highest', {})
        user_map = cat_map.setdefault(category, {})
        prev = user_map.get(user)
        if (prev is None) or (sei > float(prev.get('sei', 0))):
            user_map[user] = {'sei': float(sei), 'date': date_str}
        # Update user_time_series
        uts = agg.setdefault('user_time_series', {})
        series_key = user
        series = uts.setdefault(series_key, [])
        series.append({'date': date_str, 'category': category, 'avg_score_per_word': avg_score, 'avg_time_per_word': avg_time, 'sei': sei})
        # Keep last 500 points per user to cap size
        if len(series) > 500:
            uts[series_key] = series[-500:]
        _save_aggregates(agg)
    except Exception:
        pass

def get_top10_from_aggregates(category: str) -> list[dict]:
    """Return list of rows: {User, Highest SEI, Date} for a category; if category == 'any', combine all categories and pick per-user max."""
    try:
        agg = _load_aggregates()
        cat_map = agg.get('category_user_highest', {})
        rows = []
        if category and category != 'any':
            data = cat_map.get(category.lower(), {})
            for u, rec in data.items():
                rows.append({'User': u, 'Highest SEI': round(float(rec.get('sei', 0)), 2), 'Date': rec.get('date', '')})
            rows.sort(key=lambda r: r['Highest SEI'], reverse=True)
            return rows[:10]
        # any: take best across all categories per user
        best = {}
        for cat, users in cat_map.items():
            for u, rec in users.items():
                v = float(rec.get('sei', 0))
                d = rec.get('date', '')
                if (u not in best) or (v > best[u]['Highest SEI']):
                    best[u] = {'User': u, 'Highest SEI': round(v, 2), 'Date': d}
        out = list(best.values())
        out.sort(key=lambda r: r['Highest SEI'], reverse=True)
        return out[:10]
    except Exception:
        return []

def get_user_series_from_aggregates(user: str, category: str | None = None) -> list[dict]:
    try:
        agg = _load_aggregates()
        series = agg.get('user_time_series', {}).get((user or '').lower(), [])
        if category and category.lower() != 'any':
            series = [p for p in series if (p.get('category') or '').lower() == category.lower()]
        return series
    except Exception:
        return []

def ensure_aggregates_bootstrap() -> None:
    try:
        # If aggregates exists and non-empty, skip
        if os.path.exists(AGGREGATES_PATH) and os.path.getsize(AGGREGATES_PATH) > 2:
            return
        # Build from existing game_results.json
        games = get_all_game_results()
        for g in games:
            update_aggregates_with_game(g)
    except Exception:
        pass

def send_miss_you_email(to_email: str, username: str) -> bool:
    SMTP_SERVER = os.environ.get("SMTP_HOST")
    SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
    SMTP_USER = os.environ.get("SMTP_USER")
    SMTP_PASSWORD = os.environ.get("SMTP_PASS")
    if not (SMTP_SERVER and SMTP_USER and SMTP_PASSWORD and to_email):
        return False
    subject = "We miss you at WizWord!"
    body = f"Hi {username},\n\nIt's been a while since your last game. Come back and beat your best SEI!\n\nPlay now: https://wizword.example\n\n— WizWord Team"
    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = SMTP_USER
        msg["To"] = to_email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASSWORD)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
        return True
    except Exception:
        return False

def run_daily_miss_you_check() -> None:
    # Run once per day using a stamp file
    try:
        stamp_path = os.path.join("game_data", "last_miss_you_check.json")
        os.makedirs("game_data", exist_ok=True)
        today_str = datetime.date.today().isoformat()
        last_run = None
        if os.path.exists(stamp_path):
            try:
                with open(stamp_path, "r", encoding="utf-8") as f:
                    last_run = (json.load(f) or {}).get("last_run")
            except Exception:
                last_run = None
        if last_run == today_str:
            return
        # Threshold: 7 days without a game
        threshold_days = int(os.getenv("MISS_YOU_THRESHOLD_DAYS", "7"))
        now = datetime.datetime.now(datetime.UTC)
        # Load from users.json each day to ensure we use on-disk data
        users = load_users()
        for uname, u in (users or {}).items():
            try:
                email = (u or {}).get("email")
                last_game = (u or {}).get("last_game_time")
                if not (email and last_game):
                    continue
                # Parse last_game_time (ISO)
                last_dt = None
                try:
                    last_dt = datetime.datetime.fromisoformat(str(last_game))
                    if last_dt.tzinfo is None:
                        last_dt = last_dt.replace(tzinfo=datetime.UTC)
                except Exception:
                    continue
                days = (now - last_dt).days
                if days >= threshold_days:
                    send_miss_you_email(email, uname)
            except Exception:
                continue
        with open(stamp_path, "w", encoding="utf-8") as f:
            json.dump({"last_run": today_str}, f)
    except Exception:
        pass

if __name__ == "__main__":
    main() 
