import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(env_path)

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set")

# API Configuration
BASE_URL = "https://openrouter.ai/api/v1/chat/completions"
MODEL = "google/gemini-pro"  # Using Gemini Pro for better performance

# Headers for API requests
HEADERS = {
    "Authorization": f"Bearer {OPENROUTER_API_KEY}",
    "Content-Type": "application/json",
    "HTTP-Referer": "https://github.com/cursor",  # Replace with actual game URL
    "X-Title": "Word Guess Contest AI"
}

# Game Configuration
DEFAULT_WORD_LENGTH = 5
DEFAULT_SUBJECT = "General"
AVAILABLE_SUBJECTS = [
    "General",
    "Animals",
    "Food",
    "Places",
    "Science",
    "History",
    "Tech",
    "Movies",
    "Music",
    "Brands",
    "Random"
]

# Scoring Configuration
CHALLENGE_MODE_PENALTY = 10  # Points added for wrong answers in Challenge mode 