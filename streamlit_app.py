import os
import streamlit as st
import json
import re
import time
print("📝 OPENROUTER_API_KEY =", os.getenv("OPENROUTER_API_KEY"))
from pathlib import Path
from backend.game_logic import GameLogic
from backend.word_selector import WordSelector
from backend.session_manager import SessionManager
from backend.share_card import create_share_card
from backend.share_utils import ShareUtils

# Configure Streamlit page with custom theme
st.set_page_config(
    page_title="Word Guess Contest AI",
    page_icon="🎯",
    layout="centered",
    initial_sidebar_state="expanded",
    menu_items={
        'About': "# Word Guess Contest AI\nTest your deduction skills against AI!"
    }
)

# Initialize ShareUtils
share_utils = ShareUtils()

# Custom CSS for better UI
st.markdown("""
    <style>
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
    # Initialize session state
    if "game" not in st.session_state:
        st.session_state.game = None
    if "game_over" not in st.session_state:
        st.session_state.game_over = False
    if "game_summary" not in st.session_state:
        st.session_state.game_summary = None
    
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
    st.title("Word Guess Contest AI 🎯")
    st.markdown("""
    Welcome to Word Guess Contest AI! Test your deduction skills by guessing words with the help of AI-generated hints.
    
    ### How to Play
    1. Choose your game settings below
    2. Watch for automatic hints that appear every 30 seconds
    3. Make your best guess at any time
    4. In Challenge mode, manage your score carefully!
    """)
    
    # Game setup form
    with st.form("game_setup"):
        # Game mode selection
        mode = st.radio(
            "Select Game Mode:",
            ["Fun", "Challenge"],
            help="Challenge mode includes scoring and leaderboards"
        )
        
        # Word category selection
        subject = st.selectbox(
            "Choose Word Category:",
            ["general", "animals", "food", "places", "science", "tech", "sports"],
            help="Select the category of words you want to guess"
        )
        
        # Word length selection
        word_length = st.slider(
            "Choose Word Length:",
            min_value=3,
            max_value=10,
            value=5,
            help="Select how many letters you want in your word"
        )
        
        # Nickname input (optional for Fun mode, required for Challenge mode)
        nickname_help = "Required for Challenge mode, optional for Fun mode"
        nickname = st.text_input(
            "Enter your nickname:",
            help=nickname_help
        ).strip()
        
        # Start game button
        start_pressed = st.form_submit_button("Start Game!")
        
        if start_pressed:
            if mode == "Challenge" and not nickname:
                st.error("Please enter a nickname for Challenge mode!")
                return
                
            # Create new game instance
            st.session_state.game = GameLogic(
                word_length=word_length,
                subject=subject,
                mode=mode,
                nickname=nickname
            )
            st.rerun()

def display_game():
    """Display the active game interface."""
    if "game" not in st.session_state:
        st.error("No active game found. Please start a new game.")
        return

    game = st.session_state.game
    
    # Game stats in a compact row
    cols = st.columns([1, 1, 1, 1])
    with cols[0]:
        st.metric("Mode", game.mode)
    with cols[1]:
        if game.mode == "Challenge":
            st.metric("Score", game.score)
        else:
            st.metric("Questions", len(game.questions_asked))
    with cols[2]:
        st.metric("Guesses", game.guesses_made)
    with cols[3]:
        st.metric("Hints Left", 5 - len(game.hints_given))
    
    # Action buttons row
    col1, col2 = st.columns(2)
    with col1:
        if st.button("👀 Show Word", use_container_width=True):
            if game.mode == "Challenge":
                points_deducted = game.apply_show_word_penalty()  # Use the method
                st.warning(f"⚠️ {points_deducted:+d} points penalty for revealing the word!", icon="⚠️")
            st.info(f"The word is: **{game.selected_word}**", icon="🤫")
    with col2:
        if st.button("🔄 Restart", use_container_width=True):
            reset_game()
            st.rerun()
    
    # Question and Guess tabs
    tab1, tab2 = st.tabs(["❓ Ask", "🎯 Guess"])
    
    with tab1:
        # Hint section at the top
        with st.container():
            st.markdown('<div data-testid="hint-section">', unsafe_allow_html=True)
            st.markdown("#### 💡 Need a hint?")
            
            if st.button("Get Hint", disabled=len(game.hints_given) >= 5, 
                        help=f"{5-len(game.hints_given)} hints remaining", 
                        use_container_width=True,
                        key="hint-button"):
                
                hint, points = game.get_hint()
                
                if points != 0:
                    st.warning(f"{points:+d} points", icon="⚠️")
                
                if hint in ["Game is already over!", "Maximum hints reached!"]:
                    st.warning(hint)
                else:
                    st.markdown(f'<div data-testid="hint-text">💡 Hint #{len(game.hints_given)}: {hint}</div>', unsafe_allow_html=True)
            
            # Display previous hints
            if game.hints_given:
                st.markdown('<div data-testid="hint-history">', unsafe_allow_html=True)
                st.markdown("##### Previous Hints:")
                for i, hint in enumerate(game.hints_given, 1):
                    st.markdown(f'<div data-testid="hint-text">{i}. {hint}</div>', unsafe_allow_html=True)
                st.markdown('</div>', unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)
        
        # Question input
        st.markdown("#### ❓ Ask a Question")
        with st.form("question_form"):
            question = st.text_input(
                "Ask a yes/no question about the word:",
                placeholder="Example: Is it used in everyday life?",
                help="Ask about the word's meaning or properties, not its letters"
            )
            submitted = st.form_submit_button("Ask", use_container_width=True)
            
            if submitted and question:
                is_valid, answer, points = game.ask_question(question)
                if is_valid:
                    if points != 0:
                        st.warning(f"{points:+d} points", icon="⚠️")
                    st.success(f"Answer: {answer}")
                else:
                    st.error(answer)
                    
        # Display question history
        if game.questions_asked:
            st.markdown("##### Question History:")
            for q in reversed(game.questions_asked):
                with st.expander(f"Q: {q['question']}"):
                    st.write(f"A: {q['answer']}")
                    if q['points_added'] != 0:
                        st.write(f"Points: {q['points_added']:+d}")
    
    with tab2:
        with st.form(key="guess_form", clear_on_submit=True):
            guess = st.text_input(f"Your {game.word_length}-letter guess:", key="guess_input")
            submit_button = st.form_submit_button("Submit", use_container_width=True)
            
            if submit_button and guess:
                is_correct, message, points = game.make_guess(guess)
                if is_correct:
                    st.balloons()
                    st.success(message)
                    if points != 0:
                        st.info(f"Points: {points}")
                    st.session_state.game_over = True
                    st.session_state.game_summary = game.get_game_summary()
                    st.rerun()
                else:
                    st.error(message)
                    if points != 0:
                        st.warning(f"Points: {points}")
    
    # History in expander
    if game.questions_asked:
        with st.expander("📝 History", expanded=False):
            for i, qa in enumerate(game.questions_asked, 1):
                st.write(f"Q{i}: {qa['question']}")
                st.write(f"A: {qa['answer']}")
                if game.mode == "Challenge" and qa['points_added'] != 0:
                    st.write(f"Points: {qa['points_added']}")
                st.divider()

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
    
    # Play again button
    if st.button("Play Again", key="play_again"):
        reset_game()
        st.rerun()

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

if __name__ == "__main__":
    main() 