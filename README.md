# WizWord 🎯

WizWord is an AI-powered word guessing game where players try to guess a hidden word by asking yes/no questions. The game uses advanced AI models to select words and answer questions intelligently.

## Features

- Multiple difficulty levels and word categories (now supports alphanumeric titles like "Se7en", "Rio2", "Sing2")
- AI-powered word selection and question answering
- Fun and Challenge modes with strategic scoring system
- Optional nickname-based leaderboard
- Local and cloud storage support
- Mobile and desktop friendly UI
- New: Category Top SEI achievements with email + share card + in‑app celebration

## Setup

1. Clone the repository:
```bash
git clone https://github.com/yourusername/wizword.git
cd wizword
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root:
```env
# OpenRouter API Configuration
OPENROUTER_API_KEY=your_api_key_here

# AWS Configuration (Optional - for cloud storage)
AWS_ACCESS_KEY_ID=your_aws_access_key_id
AWS_SECRET_ACCESS_KEY=your_aws_secret_access_key
AWS_REGION=your_aws_region  # e.g., us-east-1

# Game Configuration
USE_CLOUD_STORAGE=false  # Set to true to use AWS DynamoDB instead of local storage

# SMTP for achievement emails
SMTP_HOST=smtp.example.com
SMTP_PORT=587
SMTP_USER=bot@example.com
SMTP_PASS=app_password
ADMIN_EMAIL=admin@example.com  # optional; falls back to SMTP_USER if not set
```

5. Run the game:
```bash
streamlit run streamlit_app.py
```

## How to Play

1. Configure your game:
   - Choose word length (3-15 letters)
   - Select a category (General, Animals, Food, etc.)
   - Pick game mode (Fun or Challenge)
   - Enter an optional nickname

2. Game Modes:
   
   ### Fun Mode
   - No scoring system
   - Ask unlimited questions
   - Make multiple guesses
   - Perfect for learning and practice

   ### Challenge/Beat Mode
   - Strategic scoring system:
     - Each question: -1 point (Beat), -5/-10/-15 depending on difficulty (Wiz)
     - Wrong guess: -10 (Beat/Wiz)
     - Correct guess: 100 points per word (fixed)
     - Show Word: -100 points
   - Higher scores are better!
   - Be strategic with your questions to minimize penalties
   - Category notes: Movies/Music/Aviation may include titles/terms with digits (e.g., "Se7en", "Rio2").

3. Asking Questions:
   - Questions must be yes/no format (start with Is, Are, Does, etc.)
   - Questions must end with a question mark
   - Examples:
     - "Is it a type of food?"
     - "Does it contain the letter 'a'?"
     - "Is it something you can find at home?"
     - "Would you use this daily?"

4. Making Guesses:
    - Type your guess when ready
    - Guesses must match the chosen word length
    - Alphanumeric names are allowed (e.g., Se7en, Rio2, Sing2). Only letters count for vowel/uniqueness checks.
    - In Beat mode:
      - Wrong guesses cost 10 points
      - Correct guesses always earn 100 points per word

## Score Efficiency Index (SEI)
SEI is a performance metric that combines your average score per word and your average time per word:

    SEI = (Average Score per Word) / (Average Time per Word in seconds)

- A higher SEI means you are both fast and accurate.
- The global leaderboard ranks users by their highest SEI in any single game.
- SEI is shown on your share card and in your statistics graphs.

### New: Top SEI Achievements
When you achieve the highest SEI in a category (or tie the high with a non-zero SEI):
- A dedicated “Congratulations” share card is generated and emailed to you (CC admin):
  - CCs the address from ADMIN_EMAIL (fallback: SMTP_USER if ADMIN_EMAIL is unset).
  - Title: Congratulations!
  - Subtitle: Global Top SEI — Category: <your category>
  - UTC timestamp
  - Your SEI value highlighted
  - Trophy artwork with "WizWord" in the cup, your username on the top base tier, and the category on the bottom base tier
- A celebration appears in-app on the Game Over screen:
  - A trophy emoji flies up
  - A rising congratulations banner and floating balloons briefly show, then auto-dismiss

To test the animation without hitting top SEI, you can temporarily set:
```env
DEBUG_FORCE_TROPHY=true
```
(Do not use in production.)

## Favorite Category

Your **Favorite Category** is the word category (such as Tech, Brands, Science, etc.) in which you have played the most games. The app tracks all your games and determines which category you play most frequently.

## Game Statistics & Performance Graphs

- Running average Score/Word and Time/Word per game
- Separate SEI trend per game
- Leaderboard filtered to the active category

## Cloud Deployment

To enable cloud storage with AWS:

1. Create a DynamoDB table named `word_guess_games` with primary key `session_id`
2. Set up AWS credentials in your `.env` file
3. Set `USE_CLOUD_STORAGE=true` in your `.env` file

## Development

The project structure is organized as follows:

```
word_guess_contest_ai/
│
├── streamlit_app.py                  # Main UI interface
├── backend/
│   ├── game_logic.py                 # Game state and scoring
│   ├── word_selector.py              # AI word selection
│   └── session_manager.py            # Session handling
│
├── assets/                           # Static assets
├── game_data/                        # Local storage (if used)
├── requirements.txt                  # Dependencies
└── README.md                         # This file
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details. 

## UI Configuration

- WIZWORD_STICKY_BANNER (default: true)
  - Controls whether the in-game WizWord banner (score/timer strip) stays fixed at the top or scrolls with the page.

## Admin Dashboard Counters

- `game_data/global_counters.json` tracks users count, total game time, and total sessions. 