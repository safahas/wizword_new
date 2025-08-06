# WizWord 🎯

WizWord is an AI-powered word guessing game where players try to guess a hidden word by asking yes/no questions. The game uses advanced AI models to select words and answer questions intelligently.

## Features

- Multiple difficulty levels and word categories
- AI-powered word selection and question answering
- Fun and Challenge modes with strategic scoring system
- Optional nickname-based leaderboard
- Local and cloud storage support
- Mobile and desktop friendly UI

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

   ### Challenge Mode
   - Strategic scoring system:
     - Each question: -5 points
     - Wrong guess: -10 points
     - Correct guess: 100 points per word
     - Question penalty: Number of questions × 5
     - Final points = max(Base points - Question penalty, 10)
   - Higher scores are better!
   - Be strategic with your questions to minimize penalties

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
   - In Challenge mode:
     - Wrong guesses cost 10 points
     - Correct guesses always earn 100 points per word
     - Try to minimize questions to maximize your score!

## Score Efficiency Index (SEI)
SEI is a performance metric that combines your average score per word and your average time per word:

    SEI = (Average Score per Word) / (Average Time per Word in seconds)

- A higher SEI means you are both fast and accurate.
- The global leaderboard ranks users by their highest SEI in any single game.
- SEI is shown on your share card and in your statistics graphs.

## Game Statistics & Performance Graphs

After each game, WizWord provides detailed performance statistics and visualizations:

### 1. Score & Time Trend Graph
- **Graph Title:** Avg Score/Word & Avg Time/Word Trend (Last 12 Months)
- **X-Axis:**
  - Nonlinear: First 11 months are compressed (one point per month, averaged), last month is expanded (each game in the last month is shown as an individual point, labeled by date).
- **Left Y-Axis:** Average Score per Word (total score divided by number of words for each game)
- **Right Y-Axis:** Average Time per Word (seconds)
  - For Beat mode: time for the game divided by number of words solved
  - For other modes: time for the game
  - Scale: 0–300 seconds
- **Legend:** Both lines are shown with different colors and a shared legend.
- **Details:**
  - The graph visually emphasizes recent performance by expanding the last month’s results.
  - Each game in the last month is labeled with its actual date (YYYY-MM-DD).

### 2. Avg Time per Word vs. Cumulative Time
- **X-Axis:** Cumulative time (seconds) across all games/words played
- **Y-Axis:** Average time per word (seconds)
- **Purpose:** Shows how your speed per word changes as you play more games.

### 3. Beat Mode Aggregation
- In Beat mode, statistics are aggregated for the entire session:
  - **Total Points:** Sum of all points earned across all words in the session
  - **Guesses Made:** Total number of guesses across all words in the session
  - **Words Played:** List of all words solved in the session
  - **Session Duration:** Total time spent in the session

### 4. Leaderboard & Historical Stats
- The leaderboard and your historical stats are based on these aggregated and per-game statistics.

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
├── config/
│   └── openrouter_config.py          # API configuration
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