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
import json
import os
import uuid
import datetime
import logging
logging.getLogger('matplotlib.font_manager').setLevel(logging.WARNING)
logging.getLogger('matplotlib.category').setLevel(logging.WARNING)

USERS_FILE = "users.json"

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
# Initialize user store for demo (replace with real DB in production)
if 'users' not in st.session_state:
    st.session_state['users'] = load_users()
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
    /* Style for hint text */
    [data-testid="hint-text"] {
        font-size: 1.1em;
        font-weight: 600;
        color: #000000;
        background: rgba(255, 255, 255, 0.9);
        padding: 10px;
        border-radius: 8px;
        margin: 5px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
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
                       "movies", "music", "brands", "history", "random", "4th_grade"]
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
        font-size: 2em;                       /* Reduced from 3.8em */
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
    </style>
    """, unsafe_allow_html=True)

    # --- Custom Expander Header Style for Welcome and How to Play ---
    st.markdown("""
    <style>
    /* Improved: Target both expander header and parent for background and border */
    div[role="button"]:has(.streamlit-expanderHeader:has-text('Welcome to WizWord!')),
    div[role="button"]:has(.streamlit-expanderHeader:has-text('How to Play')) {
        background: rgba(255,255,255,0.18) !important;
        border: 1.5px solid #FFD93D !important;
        box-shadow: 0 2px 8px rgba(255,217,61,0.10), 0 1px 4px rgba(0,0,0,0.07) !important;
    }
    div[role="button"]:has(.streamlit-expanderHeader:has-text('Welcome to WizWord!')) .streamlit-expanderHeader,
    div[role="button"]:has(.streamlit-expanderHeader:has-text('How to Play')) .streamlit-expanderHeader,
    div[role="button"]:has(.st-expanderHeader:has-text('Welcome to WizWord!')) .st-expanderHeader,
    div[role="button"]:has(.st-expanderHeader:has-text('How to Play')) .st-expanderHeader {
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
    # --- Introductory Section ---
    with st.expander("👋 Welcome to WizWord!", expanded=False):
        st.markdown("""
        <div style='max-width: 700px; margin: 0 auto 2em auto; background: rgba(255,255,255,0.40); border-radius: 1.2em; padding: 1.5em 2em; box-shadow: 0 1px 8px rgba(255,255,255,0.08);'>
            <h2 style="text-align:center; color:#FF6B6B; margin-bottom:0.5em; font-size:3.8em;">Welcome to WizWord!</h2>
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

    # --- How to Play as collapsible section ---
    
    with st.expander("📖 How to Play", expanded=False):
        st.markdown("""
        ### Gameplay
        - Ask yes/no questions (costs 1 point each) or request hints (see below).
        - Enter your guess at any time—type up to the full word. Each correct letter is revealed and earns points.
        - Each wrong guess costs 10 points.
        - Use the "Show Word" button to reveal the answer (with a point penalty).
        - In Beat mode, use "Skip" to move to a new word, or "Change Category" to switch topics.

        ### Hints (Beat Mode)
        - **First hint is free** (no penalty)
        - 2nd and 3rd hints cost **-10 points each** (max 3 per word)
        - In other modes, all hints cost points as usual

        ### Scoring
        - **Questions:** -1 point each
        - **Hints:** See above
        - **Wrong guesses:** -10 points
        - **Correct guess:** +20 × word length
        - **Show Word:** Point penalty applied
        - **Beat Mode:** Solve as many words as possible in 5 minutes! The timer starts when you click the Start button.

        ### User Profile
        - Access your profile from the menu (☰ > User Profile)
        - Edit your **education**, **occupation**, **address**, and **birthday** (from 1900 onward)
        - Choose from common options or enter your own for education/occupation

        ### Statistics & Leaderboards
        - After each game, view your performance graphs: score trend, category breakdown, and time per game.
        - See your all-time stats and recent games.
        - Compete on the global leaderboard—filter by mode and category.

        ### Sharing
        - Generate a share card for your achievement.
        - Download, copy, or share your results on social media.
        - Email your share card to yourself.
        - Show and share your highest score card for the current month.

        ### Account
        - Register and log in to save your stats.
        - Reset your password via email if needed.
        """)



    # State for which form to show
    if 'auth_mode' not in st.session_state:
        st.session_state['auth_mode'] = 'login'

    # --- LOGIN FORM ---
    if st.session_state['auth_mode'] == 'login':
        st.markdown("## Login")
        # Show error if present (ALWAYS before the form)
        if st.session_state.get('login_error'):
            st.error(st.session_state['login_error'])
        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("Username", key="login_username")
            password = st.text_input("Password", type="password", key="login_password")
            login_btn = st.form_submit_button("Login", use_container_width=True)
            col1, col2 = st.columns(2)
            with col1:
                if st.form_submit_button("Register"):
                    st.session_state['auth_mode'] = 'register'
                    st.session_state['login_error'] = ""
                    st.rerun()
            with col2:
                if st.form_submit_button("Forgot Password?"):
                    st.session_state['auth_mode'] = 'forgot'
                    st.session_state['login_error'] = ""
                    st.rerun()
            if login_btn:
                users = st.session_state['users']
                username_lower = username.lower()
                if username_lower in users and users[username_lower]['password'] == password:
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
        new_password = st.text_input("Choose a password", type="password", key="register_password")
        register_btn = st.button("Register", key="register_btn")
        if st.button("Back to Login", key="back_to_login_from_register"):
            st.session_state['auth_mode'] = 'login'
            st.rerun()
        if register_btn:
            users = st.session_state['users']
            new_username_lower = new_username.lower()
            if not new_username or not new_password or not new_email:
                st.error("Please enter username, email, and password.")
            elif new_username_lower in users:
                st.error("Username already exists.")
            elif any(u['email'] == new_email for u in users.values()):
                st.error("Email already registered.")
            else:
                users[new_username_lower] = {
                    'password': new_password,
                    'email': new_email
                }
                st.session_state['users'] = users
                save_users(users)
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
    # Show login page if not logged in
    if not st.session_state.get('logged_in', False):
        display_login()
        return
# --- Admin-only: Display all user profiles ---
    if st.session_state.get('user', {}).get('username', '').lower() == 'admin':
        st.sidebar.markdown('---')
        if st.sidebar.button('Display All User Profiles', key='admin_show_users'):
            users = st.session_state.get('users', {})
            st.markdown('## All User Profiles')
            import pandas as pd
            df = pd.DataFrame.from_dict(users, orient='index').reset_index().rename(columns={'index': 'username'})
            st.dataframe(df)

    if 'game' not in st.session_state or not st.session_state.game or getattr(st.session_state.game, 'mode', None) != 'Beat':
        random_length = random.randint(3, 10)
        user_profile = st.session_state.get('user', {})
        default_category = user_profile.get('default_category', 'general')
        subject = default_category if default_category else 'general'
        print(f"[DEBUG][main] Starting Beat mode with subject: {subject}")
        st.session_state.game = GameLogic(
            word_length=random_length,  # Use random length between 3 and 10
            subject=subject,
            mode='Beat',
            nickname=st.session_state.user['username'],
            difficulty='Medium'
        )
        st.session_state.game_over = False
        st.session_state.game_summary = None
        st.session_state.beat_word_count = 0
        st.session_state.beat_time_left = 0
        st.session_state['game_saved'] = False
    # Always go directly to the game page
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
                subject = st.selectbox(
                    "Category",
                    options=["any", "4th_grade", "general", "animals", "food", "places", "science", "tech", "sports", "brands", "cities", "medicines", "anatomy"],
                    index=2,  # Set default to 'general'
                    help="Word category (select 'any' for random category)"
                )
                st.session_state['original_category_choice'] = subject
                resolved_subject = random.choice(["general", "animals", "food", "places", "science", "tech", "sports", "brands", "4th_grade", "cities", "medicines", "anatomy"]) if subject == "any" else subject
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
            st.markdown("""
            ### Game Instructions:
            - Choose your game mode:
                - **Fun**: Unlimited play, no timer, just for fun.
                - **Wiz**: Classic mode with stats and leaderboards.
                - **Beat**: Timed challenge—solve as many words as possible before time runs out.
            - Select a word category, or pick 'any' for a random challenge.
            - Ask yes/no questions or request hints to help you guess the word.
            - Enter your guess at any time.
            **Beat Mode Details:**
            - You have 5 minutes to play.
            - For each word, you can:
                - **Guess the word:**
                    - Correct: **+20 × word length**
                    - Wrong: **-10**
                - **Ask yes/no questions:** **-1** each
                - **Request hints:** **-10** each (max 3 per word)
                - **Skip the word:** **-10** (new word loaded)
            - Try to solve as many words as possible and maximize your score before time runs out!
            - Only Medium difficulty is available for all modes.
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
    import time
    from streamlit_app import save_game_to_user_profile
    # Ensure beat_total_points is always initialized for Beat mode
    if 'beat_total_points' not in st.session_state:
        st.session_state['beat_total_points'] = 0

    # If game is not initialized, always use user's default_category for Beat mode
    if 'game' not in st.session_state or not st.session_state.game:
        user_profile = st.session_state.get('user', {})
        default_category = user_profile.get('default_category', 'general')
        subject = default_category if default_category else 'general'
        random_length = random.randint(3, 10)
        print(f"[DEBUG][display_game] Initializing Beat mode with subject: {subject}")
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
            # Remove Skip button for Beat mode from menu
            if not (game.mode == 'Beat'):
                if st.button('Skip', key='skip_word_btn_menu'):
                    game = st.session_state.game
                    st.session_state['last_mode'] = st.session_state.game.mode
                    st.session_state['game_over'] = True
                    st.session_state['game_summary'] = game.get_game_summary()
                    st.rerun()
            if st.button('View Rules / How to Play', key='view_rules_btn_menu'):
                st.session_state['show_rules'] = not st.session_state.get('show_rules', False)
            if st.button('User Profile', key='user_profile_btn_menu'):
                st.session_state['show_user_profile'] = not st.session_state.get('show_user_profile', False)
            if st.button('Toggle Sound/Music', key='toggle_sound_btn'):
                st.session_state['sound_on'] = not st.session_state.get('sound_on', True)
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
        min_birthday = datetime.date(1900, 1, 1)
        birthday = st.date_input('Birthday', value=user.get('birthday') if user.get('birthday') else None, min_value=min_birthday)
        if st.button('Save Profile', key='save_profile_btn'):
            username = user.get('username')
            final_education = education_other if education == 'Other' else education
            final_occupation = occupation_other if occupation == 'Other' else occupation
            if username and 'users' in st.session_state and username in st.session_state['users']:
                st.session_state['users'][username]['education'] = final_education
                st.session_state['users'][username]['address'] = address
                st.session_state['users'][username]['birthday'] = str(birthday)
                st.session_state['users'][username]['occupation'] = final_occupation
                st.session_state['user']['education'] = final_education
                st.session_state['user']['address'] = address
                st.session_state['user']['birthday'] = str(birthday)
                st.session_state['user']['occupation'] = final_occupation
                save_users(st.session_state['users'])
                st.success('Profile updated!')

    # Show rules if toggled
    if st.session_state.get('show_rules', False):
        st.info("""
        **How to Play:**\n- Guess the word by revealing letters.\n- Use hints or ask yes/no questions.\n- In Beat mode, solve as many words as possible before time runs out!\n- Use the menu to skip, reveal, or change category.\n        """)

    # Handle change category
    if st.session_state.get('change_category', False):
        categories = ["any", "anatomy", "animals", "brands", "cities", "food", "general", "medicines", "places", "science", "sports", "tech", "4th_grade"]
        new_category = st.selectbox("Select a new category:", categories, format_func=lambda x: x.replace('_', ' ').title() if x != 'any' else 'Any', key='category_select_box')
        if st.button("Confirm Category Change", key='change_category_btn'):
            game = st.session_state.game
            st.session_state.game = GameLogic(
                word_length=5,
                subject=new_category,
                mode=game.mode,
                nickname=game.nickname,
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
                <span class='wizword-stat'><b>🎮</b> Beat</span>
                <span class='wizword-stat wizword-beat-category'><b>📚</b> {game.subject.replace('_', ' ').title()}</span>
                <span class='wizword-stat wizword-beat-timer'><b>⏰</b> --s</span>
                <span class='wizword-stat wizword-beat-score'><b>🏆</b> {game.score}</span>
                <span class='wizword-stat'><b>🔢</b> {st.session_state.get('beat_word_count', 0)}</span>
                <span class='wizword-stat' style='padding:0;margin:0;'>{{START_BUTTON}}</span>
              </div>
            </div>
            <style>/* ... existing styles ... */</style>
            """
            # Render the banner without the button first
            st.markdown(stats_html.replace('{START_BUTTON}', ''), unsafe_allow_html=True)
            # Now render the Start button in the same row, styled to match
            start_btn_html = """
            <style>
            .beat-start-btn button {
                background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 50%, #4ECDC4 100%) !important;
                color: #222 !important;
                font-weight: 700 !important;
                font-size: 1.1em !important;
                border-radius: 8px !important;
                border: none !important;
                padding: 0.4em 1.2em !important;
                margin: 0 0.2em !important;
                box-shadow: 0 2px 8px rgba(0,0,0,0.10);
                transition: background 0.2s, color 0.2s;
            }
            .beat-start-btn button:hover {
                background: linear-gradient(90deg, #FFD93D 0%, #4ECDC4 100%) !important;
                color: #fff !important;
            }
            </style>
            <div class='beat-start-btn' style='display:inline-block;'>
            </div>
            """
            st.markdown(start_btn_html, unsafe_allow_html=True)
            if st.button('Start', key='beat_start_btn'):
                st.session_state['beat_started'] = True
                st.session_state['beat_start_time'] = _time.time()
                st.rerun()
            # Show Change Category button before starting
            if st.button('Change Category', key='change_category_btn_beat_start'):
                st.session_state['change_category'] = True
                st.rerun()
            st.stop()
        # Normal banner and timer logic follows as before
        stats_html = f"""
        <div class='wizword-banner'>
          <div class='wizword-banner-title'>WizWord</div>
          <div class='wizword-banner-stats'>
            <span class='wizword-stat'><b>🎮</b> Beat</span>
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
            margin: 10px 0 18px 0;
            border-radius: 16px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.10),
                        inset 0 -2px 0px rgba(0, 0, 0, 0.07);
            -webkit-text-stroke: 1px #222;
            text-stroke: 1px #222;
            text-shadow: 1px 1px 4px rgba(0,0,0,0.13),
                         0 1px 4px rgba(0,0,0,0.08);
            transition: box-shadow 0.2s, background 0.2s;
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
    # --- Automatically show the first hint for Beat mode when a new word is loaded ---
    if game.mode == 'Beat' and len(game.hints_given) == 0:
        first_hint, _ = game.get_hint()
        st.info(f"💡 First Hint (free): {first_hint}")

    display_hint_section(game)

    # --- Letter boxes and input ---
    revealed_letters = st.session_state.get('revealed_letters', set())
    word = game.selected_word if hasattr(game, 'selected_word') else ''
    if not word:
        st.error('No word was selected for this round. Please restart the game or contact support.')
        return
    boxes = []
    for i, letter in enumerate(word):
        is_revealed = letter.lower() in revealed_letters
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
    # Letter input below the container
    if 'clear_guess_field' not in st.session_state:
        st.session_state['clear_guess_field'] = False
    if st.session_state['clear_guess_field']:
        st.session_state['letter_guess_input'] = ''
        st.session_state['clear_guess_field'] = False
    # Disable input if showing final word
    input_disabled = st.session_state.get('show_final_word', False)
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
            st.session_state['feedback'] = '  |  '.join(feedback)
            st.session_state['clear_guess_field'] = True
            st.rerun()

    # --- Ask Yes/No Question section (now below letter boxes) ---
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
        print(f"[DEBUG] Game mode before asking question: {game.mode}")
        prev_score = game.score
        success, answer, points = game.ask_question(question)
        print(f"[DEBUG] Score before question: {prev_score}")
        print(f"[DEBUG] Points for this question: {points}")
        print(f"[DEBUG] Score after question: {game.score}")
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

    # --- Show Word button at the bottom ---
    if st.button('Show Word', key='show_word_btn_bottom'):
        game = st.session_state.game
        penalty = game.apply_show_word_penalty()  # <-- Apply the penalty!
        st.session_state['feedback'] = (
            f"The word is: {getattr(game, 'selected_word', '???').upper()}"
            + (f"  \n(-{abs(penalty)} points)" if penalty else "")
        )
        st.session_state['feedback_time'] = time.time()
        st.session_state['show_word'] = True  # <-- Always set this!
        st.session_state['show_word_round_id'] = st.session_state.get('current_round_id')
        st.session_state['feedback_round_id'] = st.session_state.get('current_round_id')
        st.session_state['show_prev_questions'] = False
        st.rerun()

    # --- Skip button for Beat mode, directly below Show Word ---
    if game.mode == 'Beat':
        if st.button('Skip', key='skip_word_btn_main'):
            st.session_state['beat_total_points'] += game.total_points
            # st.session_state.beat_word_count += 1  # <-- REMOVE THIS LINE
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
            st.session_state['show_prev_questions'] = False  # <-- Clear previous questions
            feedback = st.session_state.get('feedback', '')
            feedback_time = st.session_state.get('feedback_time', 0)
            is_show_word = feedback.startswith("The word is:")
            import time
            if not (is_show_word and (time.time() - feedback_time < 4)):
                st.session_state['feedback'] = ''
                st.session_state['feedback_time'] = 0
            st.session_state['revealed_letters'] = set()
            st.session_state['used_letters'] = set()
            st.session_state['show_word'] = False  # <-- Clear show_word for new word
            st.session_state['show_word_round_id'] = None  # <-- Clear show_word_round_id for new word
            st.rerun()
        # --- Remove Change Category button for Beat mode after timer starts ---
        # (Button is now only shown on the Beat start page)

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
    # Debug print for beat_word_count and full session state
    #print(f"[DEBUG] display_game_over: beat_word_count = {st.session_state.get('beat_word_count', 'MISSING')}")
    #print(f"[DEBUG] display_game_over: session_state = {dict(st.session_state)}")
    log_beat_word_count_event("GAME_OVER", st.session_state.get('beat_word_count', 'MISSING'))
    # --- FIX: Always inject correct words_solved for Beat mode ---
    if mode == "Beat":
        game_summary["words_solved"] = st.session_state.get("beat_word_count", 0)
    # --- NEW: Save game result to user profile only once ---
    if not st.session_state.get('game_saved', False):
        save_game_to_user_profile(game_summary)
        # import logging
        # logging.info(f"[PROOF] Beat mode: game_results.json updated for user '{game_summary.get('nickname', '?')}' with game: {game_summary}")
        st.session_state['game_saved'] = True
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
    st.markdown("## 🎉 Game Over!")
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
        # Game summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Score", score)
        # Remove Questions Asked metric
        # with col2:
        #     st.metric("Questions Asked", len(game_summary["questions_asked"]))
        with col2:
            st.metric("Time Taken", format_duration(game_summary.get("duration") or game_summary.get("time_taken", 0)))
        with col3:
            st.metric("Total Points", st.session_state.get('total_points', 0))
        
        if mode == "Beat":
            print(f"[DEBUG] summary_tab: words_solved = {game_summary.get('words_solved', 'MISSING')}")
            # (Removed: last word display above words solved)
            st.markdown(f"**Words solved:** {game_summary.get('words_solved', 0)}")
        else:
            st.markdown(f"**The word was:** {(game_summary.get('selected_word') or game_summary.get('word', '')).upper()}")
        # Remove Questions Asked section
        # if game_summary["questions_asked"]:
        #     st.markdown("### Questions Asked")
        #     for q in game_summary["questions_asked"]:
        #         st.markdown(f"- Q: {q['question']}\n  A: {q['answer']}")
    
    with stats_tab:
        # Performance graphs
        st.markdown("### Your Performance")
        username = game_summary.get('nickname', '').lower()
        all_games = get_all_game_results()
        user_games = [g for g in all_games if g.get('nickname', '').lower() == username]
        if user_games:
            import matplotlib.pyplot as plt
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
            game_dates = []
            total_score = 0
            total_time = 0
            total_words = 0
            for g in user_games:
                score = g.get('score', 0)
                words = g.get('words_solved', 1) if g.get('mode') == 'Beat' else 1
                time_taken = g.get('time_taken', g.get('duration', None))
                date = g.get('timestamp')
                if time_taken is not None and words > 0 and date:
                    total_score += score
                    total_time += time_taken
                    total_words += words
                    avg_score = total_score / total_words if total_words > 0 else 0
                    avg_time = total_time / total_words if total_words > 0 else 0
                    avg_scores.append(avg_score)
                    avg_times.append(avg_time)
                    # Use only the date part for x-axis
                    if isinstance(date, str):
                        date = date.split('T')[0]
                    game_dates.append(date)
            if avg_scores and avg_times and game_dates:
                fig, ax = plt.subplots(figsize=(6, 3))
                color1 = 'tab:blue'
                color2 = 'tab:orange'
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
                ax.set_title('Running Avg Score/Word & Time/Word vs. Game Date')
                fig.tight_layout()
                st.pyplot(fig)
        # (Removed: recent games/results list from this tab)
    
    with share_tab:
        st.markdown("### 🔗 Share Your Achievement!")
        # Generate share card for this game
        if st.button("Generate Share Card"):
            with st.spinner("Generating share card..."):
                game_summary_for_card = dict(game_summary)
                if mode == "Beat":
                    game_summary_for_card["score"] = st.session_state.get('beat_score', 0)
                    game_summary_for_card["word"] = "--"
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
                st.markdown(f"- {g.get('subject','?').title()} | {g.get('mode','?')} | Score: {g.get('score',0)} | {date_str}")
        else:
            st.info("No games played yet.")
        st.markdown("---")
        st.markdown("## 🏆 Global Leaderboard (Top 10)")
        mode = st.selectbox("Game Mode", ["All", "Fun", "Wiz", "Beat"], key="global_leaderboard_mode")
        category = st.selectbox("Category", ["All"] + [cat.title() for cat in WordSelector.CATEGORIES], key="global_leaderboard_category")
        leaderboard = get_global_leaderboard(top_n=10, mode=mode if mode != "All" else None, category=category if category != "All" else None)
        if leaderboard:
            # Banner with top 3 results
            top3 = leaderboard[:3]
            banner_html = "<div style='background:linear-gradient(90deg,#FFD93D,#FF6B6B,#4ECDC4);padding:1.2em 1em;border-radius:1.2em;margin-bottom:1em;box-shadow:0 2px 12px rgba(0,0,0,0.10);display:flex;justify-content:center;align-items:center;gap:2em;'>"
            for i, entry in enumerate(top3, 1):
                date_str = entry.get('timestamp')
                if date_str:
                    try:
                        if isinstance(date_str, (float, int)):
                            from datetime import datetime
                            date_str = datetime.fromtimestamp(date_str).strftime('%Y-%m-%d')
                        else:
                            date_str = str(date_str)[:10]
                    except Exception:
                        date_str = str(date_str)[:10]
                banner_html += f"<span style='font-size:1.2em;font-weight:700;color:#222;'>🏅 {i}. {entry['nickname']} - {entry.get('score',0)} pts | {entry.get('mode','?')} | {entry.get('subject','?').title()} | {date_str}</span>"
            banner_html += "</div>"
            st.markdown(banner_html, unsafe_allow_html=True)
            # Use Streamlit expander for the full leaderboard
            with st.expander("Show Full Leaderboard"):
                for i, entry in enumerate(leaderboard, 1):
                    date_str = entry.get('timestamp')
                    if date_str:
                        try:
                            if isinstance(date_str, (float, int)):
                                from datetime import datetime
                                date_str = datetime.fromtimestamp(date_str).strftime('%Y-%m-%d')
                            else:
                                date_str = str(date_str)[:10]
                        except Exception:
                            date_str = str(date_str)[:10]
                    st.markdown(f"{i}. {entry['nickname']} - {entry.get('score',0)} pts | {entry.get('mode','?')} | {entry.get('subject','?').title()} | {date_str}")
        else:
            st.info("No leaderboard data available.")

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
                new_subject = default_category if default_category else 'general'
                print(f"[DEBUG][Another Beat] Restarting Beat mode with subject: {new_subject}")
                st.session_state.beat_word_count = 0
                st.session_state.beat_score = 0
                st.session_state.beat_time_left = BEAT_MODE_TIMEOUT_SECONDS
                st.session_state.beat_start_time = time.time()
                st.session_state['beat_started'] = False
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
        if st.button('🧹 Restart Game', key='restart-game-btn'):
            # Removed debug print
            log_beat_word_count_event("RESET_RESTART", st.session_state.get('beat_word_count', 'MISSING'))
            user = st.session_state.get('user')
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            if user:
                st.session_state['user'] = user
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
    max_hints = game.current_settings["max_hints"]
    hints_remaining = max_hints - len(game.hints_given)

    # Header row: "Get a Hint" and "Hints Left" on the same line
    st.markdown(
        f"""
        <div style='display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.2em;'>
            <span style='font-size: 1.6em; font-weight: 700; color: #222; letter-spacing: 0.01em;'>Get a Hint</span>
            <span style='font-size: 1.1em; color: #7c3aed; font-weight:700;'>
                Hints Left: <span style='background:#FFD93D; color:#222; border-radius:0.6em; padding:0.2em 0.8em;'>{hints_remaining}</span>
            </span>
        </div>
        """,
        unsafe_allow_html=True
    )

    # --- Two buttons side by side, each half width ---
    col1, col2 = st.columns(2)
    show_prev = st.session_state.get("show_prev_hints", False)

    with col1:
        # Only show "Show Hint" if not showing previous hints
        if not show_prev:
            if st.button("Next Hint", 
                        disabled=len(game.hints_given) >= max_hints,
                        help=f"{hints_remaining} hints remaining",
                        use_container_width=True,
                        key="hint-button"):
                hint, points = game.get_hint()
#                if points < 0:
#                    st.warning(f"Got hint but lost {abs(points)} points!")

    with col2:
        # Toggle show previous hints
        if st.button(
            "Show Previous Hints" if not show_prev else "Hide Previous Hints",
            use_container_width=True,
            key="prev-hints-btn"
        ):
            st.session_state["show_prev_hints"] = not show_prev
            st.rerun()

    # --- Show only previous hints if toggled ---
    if show_prev:
        if game.hints_given:
            styled_hints = [highlight_letters_in_hint(h) for h in game.hints_given]
            st.markdown(
                "<br>".join([f"<b>{i+1}.</b> {h}" for i, h in enumerate(styled_hints)]),
                unsafe_allow_html=True
            )
        else:
            st.info("No previous hints yet.", icon="💡")
    # --- Otherwise, show only the last hint if available ---
    elif game.hints_given:
        last_hint = game.hints_given[-1]
        styled_hint = highlight_letters_in_hint(last_hint)
        st.markdown(f"""
            <div style='width:100%; display:flex; justify-content:center;'>
              <div style='
                  display: inline-block;
                  max-width: 420px;
                  background: linear-gradient(90deg, #FFD93D 0%, #FF6B6B 50%, #4ECDC4 100%);
                  color: #111; font-size: 2em; font-weight: bold; 
                  border-radius: 1em; padding: 0.5em 0.5em; margin: 0.5em 0; 
                  box-shadow: 0 2px 12px rgba(0,0,0,0.13); text-align: center;'>
                💡 {styled_hint}
              </div>
            </div>
        """, unsafe_allow_html=True)

def log_beat_word_count_event(event, value):
    with open("beat_word_count_debug.log", "a", encoding="utf-8") as f:
        f.write(f"{event}: beat_word_count = {value}\n")

GAME_RESULTS_PATH = os.environ.get('GAME_RESULTS_PATH', 'game_results.json')

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

if __name__ == "__main__":
    main() 
