import os
import streamlit as st
import json
import re
import time
import random
from backend.monitoring import logger  # Add monitoring logger
print("📝 OPENROUTER_API_KEY =", os.getenv("OPENROUTER_API_KEY"))
from pathlib import Path
from backend.game_logic import GameLogic
from backend.word_selector import WordSelector
from backend.session_manager import SessionManager
from backend.share_card import create_share_card
from backend.share_utils import ShareUtils

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

# Initialize ShareUtils
share_utils = ShareUtils()

# Custom CSS for better UI
st.markdown("""
    <style>
            
     /* New styles for the split layout */
    /* New styles for the split layout */
    [data-testid="column"] {
        background: rgba(255, 255, 255, 0.05);
        padding: 20px;
        border-radius: 15px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        margin: 10px;
    }
    
    /* Style for the instructions section */
    [data-testid="column"]:first-child {
        background: rgba(255, 255, 255, 0.08);
    }
    
    /* Style for the game settings section */
    [data-testid="column"]:last-child {
        background: rgba(255, 255, 255, 0.12);
    }
    
    /* Enhanced text styling for instructions */
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
    @import url('https://fonts.googleapis.com/css2?family=Press+Start+2P&display=swap');
    
    .game-title {
        font-family: 'Press Start 2P', cursive;
        font-size: 2.8em;
        font-weight: bold;
        background: linear-gradient(45deg, #FF6B6B, #4ECDC4);
        color: white;
        text-align: center;
        padding: 30px 60px;
        margin: 20px auto;
        text-shadow: 3px 3px 0px rgba(0, 0, 0, 0.2),
                     6px 6px 0px rgba(0, 0, 0, 0.1);
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1),
                    inset 0 -8px 0px rgba(0, 0, 0, 0.1),
                    0 -2px 0px rgba(255, 255, 255, 0.2);
        position: relative;
        max-width: 800px;
        display: flex;
        justify-content: center;
        align-items: center;
        gap: 20px;
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
    </style>
    """, unsafe_allow_html=True)

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
                       "movies", "music", "brands", "history", "random"]
    subject = subject.lower()  # Convert to lowercase for comparison
    if subject not in valid_categories:
        return False, f"Invalid subject. Must be one of: {', '.join(valid_categories)}"
    return True, ""

def validate_nickname(nickname: str) -> tuple[bool, str]:
    """Validate nickname with detailed feedback."""
    if not nickname:
        return True, ""  # Nickname is optional
    if len(nickname) > 20:
        return False, "Nickname cannot exceed 20 characters"
    if not re.match(r'^[a-zA-Z0-9_-]+$', nickname):
        return False, "Nickname can only contain letters, numbers, underscores, and hyphens"
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

def main():
    """Main application entry point."""
    print('[DEBUG] Top of main(), st.session_state:', dict(st.session_state))
    # Initialize session state
    if "game" not in st.session_state:
        st.session_state.game = None
    if "game_over" not in st.session_state:
        st.session_state.game_over = False
    if "game_summary" not in st.session_state:
        st.session_state.game_summary = None
    print('[DEBUG] Before play_again check, st.session_state:', dict(st.session_state))
    if st.session_state.get('play_again', False):
        print('[DEBUG] Creating new game for Play Again')
        prev_game = st.session_state.game
        st.session_state.game = GameLogic(
            word_length=prev_game.word_length,
            subject=prev_game.subject,
            mode=prev_game.mode,
            nickname=prev_game.nickname,
            difficulty=prev_game.difficulty
        )
        st.session_state.game_over = False
        st.session_state.game_summary = None
        st.session_state['play_again'] = False
    print('[DEBUG] After play_again check, st.session_state:', dict(st.session_state))
    
    # Display welcome screen if no game is active
    if not st.session_state.game:
        display_welcome()
        return
        
    # Display game over screen if game is finished
    if st.session_state.game_over and st.session_state.game_summary:
        display_game_over(st.session_state.game_summary)
        return
        
    # Display active game
    display_game()

def display_welcome():
    """Display the welcome screen and game setup."""
    st.markdown("<h1 class='game-title'>WizWord 🎯</h1>", unsafe_allow_html=True)
    
    # Create two columns
    left_col, right_col = st.columns([1, 1])  # Equal width columns
    
    # Left column - Instructions
    with left_col:
        # Quick start guide always visible
        st.markdown("""
        ### Quick Start 🚀
        1. Select game mode and difficulty
        2. Choose word category and length
        3. Click 'Start Game' to begin!
        """)
        
        # Detailed instructions in expandable sections
        with st.expander("📖 How to Play", expanded=False):
            st.markdown("""
            ### Game Instructions:
            1. Choose your game settings
            2. Ask questions or request hints to help you guess the word
            3. Make your best guess at any time
            4. In Challenge mode, manage your score carefully!
            """)
            
        with st.expander("💡 Hints System", expanded=False):
            st.markdown("""
            - Easy Mode: Up to 10 hints available (-5 points each)
            - Medium Mode: Up to 7 hints available (-10 points each)
            - Hard Mode: Up to 5 hints available (-15 points each)
            """)
            
        with st.expander("🎯 Difficulty & Scoring", expanded=False):
            st.markdown("""
            ### Easy Mode
            - 10 hints available
            - Questions: -0.5 points
            - Hints: -5 points
            - Wrong guesses: -5 points
            - Base points multiplier: 25x word length

            ### Medium Mode
            - 7 hints available
            - Questions: -1 point
            - Hints: -10 points
            - Wrong guesses: -10 points
            - Base points multiplier: 20x word length

            ### Hard Mode
            - 5 hints available
            - Questions: -2 points
            - Hints: -15 points
            - Wrong guesses: -15 points
            - Base points multiplier: 15x word length
            - Time bonus: +50 points (under 1 min), +25 points (under 2 mins)
            """)
            
        with st.expander("💭 Tips & Strategy", expanded=False):
            st.markdown("""
            - Use hints strategically - they cost more points than questions
            - In Hard mode, try to solve quickly for time bonus
            - Keep track of your score before making guesses
            - Questions are cheaper than wrong guesses
            """)
    
    # Right column - Game Settings
    with right_col:
        st.markdown("### ⚙️ Game Settings")
        
        # Game setup form
        with st.form("game_setup", clear_on_submit=False):
            # Create two columns for game mode and difficulty
            mode_col, diff_col = st.columns(2)
            
            # Game mode selection
            with mode_col:
                mode = st.selectbox(
                    "Game Mode",
                    options=["Fun", "Challenge"],
                    help="Challenge mode includes scoring and leaderboards",
                    index=0,
                    key="game_mode"
                )
            
            # Difficulty selection
            with diff_col:
                difficulty = st.selectbox(
                    "Difficulty",
                    options=["Easy", "Medium", "Hard"],
                    index=1,
                    help="Affects hints and scoring"
                )
            
            # Create two columns for category and length
            cat_col, len_col = st.columns(2)
            
            # Word category selection
            with cat_col:
                subject = st.selectbox(
                    "Category",
                    options=["any"] + ["general", "animals", "food", "places", "science", "tech", "sports"],
                    index=0,  # Default to "any"
                    help="Word category (select 'any' for random category)"
                )
                
                # Convert subject to a random category if "any" is selected
                if subject == "any":
                    subject = random.choice(["general", "animals", "food", "places", "science", "tech", "sports"])
            
            # Word length selection
            with len_col:
                word_length = st.selectbox(
                    "Length",
                    options=["any"] + list(range(3, 11)),
                    index=0,  # Default to "any"
                    help="Word length (select 'any' for random length)"
                )
                
                # Convert word_length to int if not "any"
                if word_length != "any":
                    word_length = int(word_length)
                else:
                    # Random length between 3 and 10
                    word_length = random.randint(3, 10)
            
            st.markdown("---")
            
            # Create two columns for nickname and start button
            if mode == "Challenge":
                nick_col, start_col = st.columns([2, 1])  # Make nickname column wider
                with nick_col:
                    nickname = st.text_input(
                        "Nickname",
                        help="Required for Challenge mode",
                        placeholder="Enter nickname",
                        key="nickname_input"
                    ).strip()
                with start_col:
                    # Add some vertical spacing to align button with input
                    st.markdown("<br>", unsafe_allow_html=True)
                    start_pressed = st.form_submit_button("🎯 Start!", use_container_width=True)
            else:
                # For Fun mode, just show the start button centered
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    start_pressed = st.form_submit_button("🎯 Start Game!", use_container_width=True)
                nickname = ""
            
            if start_pressed:
                if mode == "Challenge" and not nickname:
                    st.error("Please enter a nickname for Challenge mode!")
                    return
                    
                # Create new game instance with difficulty
                st.session_state.game = GameLogic(
                    word_length=word_length,
                    subject=subject,
                    mode=mode,
                    nickname=nickname,
                    difficulty=difficulty
                )
                st.rerun()

def display_game():
    """Display the active game interface."""
    if "game" not in st.session_state:
        st.error("No active game found. Please start a new game.")
        return

    game = st.session_state.game
    max_hints = game.current_settings["max_hints"]
    
    # Create main two-column layout
    left_col, right_col = st.columns([1, 3])  # 1:3 ratio to make right side wider
    
    # Left column - Game Controls
    with left_col:
        # Move Guess section to the top
        st.markdown("### 🎯 Make a Guess")
        with st.form(key="guess_form"):
            guess = st.text_input(
                "Enter your guess:",
                placeholder=f"Enter a {game.word_length}-letter word",
                help=f"Must be exactly {game.word_length} letters",
                key="guess_input"
            )
            submit_guess = st.form_submit_button("Submit Guess")
        if submit_guess:
            if not guess:
                st.error("Please enter a guess!")
            else:
                is_correct, message, points = game.make_guess(guess)
                if is_correct:
                    st.balloons()
                    st.success(message)
                    st.session_state.game_over = True
                    st.session_state.game_summary = game.get_game_summary()
                    st.rerun()
                else:
                    st.error(message)
        # Show Word button at the top
        if st.button("👀 Show Word", use_container_width=True, key="show_word_btn"):
            if game.mode == "Challenge":
                points_deducted = game.apply_show_word_penalty()
                st.warning(f"⚠️ {points_deducted:+d} points!", icon="⚠️")
            st.info(f"Word: **{game.selected_word}**", icon="🤫")
        
        # Game stats in the middle
        st.markdown("### Stats")
        st.metric("Mode", game.mode)
        if game.mode == "Challenge":
            st.metric("Score", game.score)
        st.metric("Guesses", game.guesses_made)
        st.metric("Hints", f"{max_hints - len(game.hints_given)}/{max_hints}")
        
        # Add some space before the Restart button
        st.markdown("<br>" * 2, unsafe_allow_html=True)
        
        # Restart button at the bottom
        if st.button("🔄 Restart Game", use_container_width=True, key="restart_btn"):
            reset_game()
            st.rerun()
    
    # Right column - Game Operations
    with right_col:
        # Hint section with combined button
        with st.container():
            hints_remaining = max_hints - len(game.hints_given)
            if st.button(f"💡 Get Hint ({hints_remaining}/{max_hints})", 
                        disabled=len(game.hints_given) >= max_hints,
                        use_container_width=True,
                        key="hint-button"):
                hint, points = game.get_hint()
                
                if points != 0:
                    st.warning(f"{points:+d} points", icon="⚠️")
                
                if hint in ["Game is already over!", f"Maximum hints ({max_hints}) reached!"]:
                    st.warning(hint)
                else:
                    st.markdown(f'<div data-testid="hint-text">💡 Hint #{len(game.hints_given)}: {hint}</div>', unsafe_allow_html=True)
            
            # Display previous hints
            if game.hints_given:
                with st.expander("Previous Hints", expanded=False):
                    for i, hint in enumerate(game.hints_given, 1):
                        st.markdown(f'{i}. {hint}')
        
        # Question input - directly in the interface
        # Check if we're in API mode or fallback mode
        is_fallback = game.word_selector.use_fallback
        
        if is_fallback:
            question_placeholder = "Example: Is the first letter 'A'? (Press Enter to ask)"
            help_text = "In fallback mode, you can only ask about first or last letter"
        else:
            question_placeholder = "Example: Is it used in everyday life? (Press Enter to ask)"
            help_text = "Ask about the word's meaning or properties"
        
        # Create a container for the question section
        with st.container():
            # Create the text input widget
            question = st.text_input(
                "Ask a yes/no question about the word:",
                placeholder=question_placeholder,
                help=help_text,
                key="question_input"
            )
            
            # Process question when Enter is pressed
            if question:
                # Check rate limit before allowing submission
                rate_limit_ok, message = check_rate_limit()
                
                if not rate_limit_ok:
                    st.warning(message)
                else:
                    # Update last question time
                    st.session_state.game_state["last_question_time"] = time.time()
                    
                    # Process the question
                    is_valid, answer, points = game.ask_question(question)
                    
                    if not is_valid:
                        st.warning(answer)
                    else:
                        if points != 0:
                            st.warning(f"{points:+d} points", icon="⚠️")
                        st.success(answer)
                        
                        # Check for rate limit warnings
                        display_rate_limit_warning()
                        
                        # Instead of trying to clear the input, we'll just show the answer
                        # The user can type a new question to override the old one
        
        # Enhancement: Show all previous questions button under the question field
        if st.button("🕑 Show All Previous Questions", key="show-history-btn-main"):
            st.session_state.show_history = True
        
        if st.session_state.get("show_history", False):
            st.markdown("## 📝 All Previous Questions")
            if game.questions_asked:
                for i, qa in enumerate(game.questions_asked, 1):
                    st.write(f"Q{i}: {qa['question']}")
                    st.write(f"A: {qa['answer']}")
                    if game.mode == "Challenge" and qa['points_added'] != 0:
                        st.write(f"Points: {qa['points_added']}")
                    st.divider()
            else:
                st.info("No questions have been asked yet.")
            if st.button("Close History", key="close-history-btn-main"):
                st.session_state.show_history = False
        
        st.markdown("---")  # Add separator between question and guess sections

def display_game_over(game_summary):
    """Display game over screen with statistics and sharing options."""
    st.markdown("## 🎉 Game Over!")
    
    # Create tabs for different sections
    summary_tab, stats_tab, share_tab = st.tabs(["Summary", "Statistics", "Share"])
    
    with summary_tab:
        # Game summary
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Final Score", game_summary["score"])
        with col2:
            st.metric("Questions Asked", len(game_summary["questions_asked"]))
        with col3:
            st.metric("Time Taken", format_duration(game_summary.get("duration") or game_summary.get("time_taken", 0)))
            
        st.markdown(f"**The word was:** {(game_summary.get('selected_word') or game_summary.get('word', '')).upper()}")
        
        # Question history
        if game_summary["questions_asked"]:
            st.markdown("### Questions Asked")
            for q in game_summary["questions_asked"]:
                st.markdown(f"- Q: {q['question']}\n  A: {q['answer']}")
    
    with stats_tab:
        # Performance graphs
        st.markdown("### Your Performance")
        if st.session_state.game and hasattr(st.session_state.game, 'generate_performance_graphs'):
            graphs = st.session_state.game.generate_performance_graphs()
            
            if graphs:
                col1, col2 = st.columns(2)
                with col1:
                    st.image(graphs["score_distribution"], caption="Score Distribution by Category")
                with col2:
                    st.image(graphs["score_trend"], caption="Score Trend Over Time")
        else:
            st.info("Performance graphs are not available for this game.")
        
        # Leaderboard
        st.markdown("### 🏆 Leaderboard")
        mode = st.selectbox("Game Mode", ["All", "Fun", "Challenge"], key="leaderboard_mode")
        # Convert categories to title case for display
        display_categories = ["All"] + [cat.title() for cat in WordSelector.CATEGORIES]
        category = st.selectbox("Category", display_categories, key="leaderboard_category")
        
        if st.session_state.game and hasattr(st.session_state.game, 'get_leaderboard'):
            leaderboard = st.session_state.game.get_leaderboard(
                mode if mode != "All" else None,
                category.lower() if category != "All" else None  # Convert back to lowercase for backend
            )
            
            if leaderboard:
                for i, entry in enumerate(leaderboard, 1):
                    st.markdown(
                        f"{i}. **{entry['nickname']}** - {entry['score']} points "
                        f"({entry['subject'].title()}, {entry['mode']} mode)"  # Convert subject to title case for display
                    )
            else:
                st.info("No entries in the leaderboard yet!")
        else:
            st.info("Leaderboard is not available for this game.")
        
        # Daily stats
        st.markdown("### 📅 Daily Challenge Stats")
        if st.session_state.game and hasattr(st.session_state.game, 'get_daily_stats'):
            daily_stats = st.session_state.game.get_daily_stats()
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("**Today**")
                st.metric("Games Played", daily_stats["today"]["games_played"])
                st.metric("Total Score", daily_stats["today"]["total_score"])
                if daily_stats["today"]["games_played"] > 0:
                    st.metric("Avg Time", format_duration(daily_stats["today"]["avg_time"]))
            with col2:
                st.markdown("**Yesterday**")
                st.metric("Games Played", daily_stats["yesterday"]["games_played"])
                st.metric("Total Score", daily_stats["yesterday"]["total_score"])
                if daily_stats["yesterday"]["games_played"] > 0:
                    st.metric("Avg Time", format_duration(daily_stats["yesterday"]["avg_time"]))
        else:
            st.info("Daily statistics are not available for this game.")
    
    with share_tab:
        st.markdown("### 🔗 Share Your Achievement!")
        
        # Generate share card
        if st.button("Generate Share Card"):
            with st.spinner("Generating share card..."):
                share_card_path = create_share_card(game_summary)
                if share_card_path:
                    st.image(share_card_path, caption="Your Share Card")
                    st.download_button(
                        "Download Share Card",
                        open(share_card_path, "rb"),
                        file_name="word_guess_share.png",
                        mime="image/png"
                    )
        
        # Share buttons
        share_text = share_utils.generate_share_text(game_summary)
        share_url = share_utils.generate_share_url(game_summary)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Share on Twitter"):
                twitter_url = f"https://twitter.com/intent/tweet?text={share_text}&url={share_url}"
                st.markdown(f"[Click to Tweet]({twitter_url})")
        with col2:
            if st.button("Share on Facebook"):
                fb_url = f"https://www.facebook.com/sharer/sharer.php?u={share_url}"
                st.markdown(f"[Share on Facebook]({fb_url})")
        with col3:
            if st.button("Copy Link"):
                st.code(share_url)
                st.success("Link copied to clipboard!")
    
    # Play again and restart game buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button('🔄 Another Word', key='play-again-btn'):
            print('[DEBUG] Play Again button pressed')
            st.session_state['restart_game'] = False
            st.session_state['play_again'] = True
            st.rerun()
    with col2:
        if st.button('🧹 Restart Game', key='restart-game-btn'):
            # Start fresh: clear all session state and return to welcome screen
            for key in list(st.session_state.keys()):
                del st.session_state[key]

def reset_game():
    """Reset the game state."""
    if "game" in st.session_state:
        del st.session_state.game
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

def display_hint_section(game):
    """Display the hint section."""
    st.markdown("### Get a Hint")
    col1, col2 = st.columns([3, 1])
    
    max_hints = game.current_settings["max_hints"]  # Get max hints from difficulty settings
    hints_remaining = max_hints - len(game.hints_given)
    
    with col1:
        # Show hint button
        if st.button("Get Hint", 
                    disabled=len(game.hints_given) >= max_hints,  # Use max_hints from settings
                    help=f"{hints_remaining} hints remaining",
                    use_container_width=True,
                    key="hint-button"):
            hint, points = game.get_hint()
            if points < 0:
                st.warning(f"Got hint but lost {abs(points)} points!")
            st.info(f"Hint: {hint}")
    
    with col2:
        st.metric("Hints Left", hints_remaining)  # Use calculated hints remaining
    
    # Display previous hints
    if game.hints_given:
        st.markdown("#### Previous Hints:")
        for i, hint in enumerate(game.hints_given, 1):
            st.markdown(f"{i}. {hint}")

if __name__ == "__main__":
    main() 