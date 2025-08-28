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

# Feature flags
# Controls visibility and usage of the profile‑aware Personal category
ENABLE_PERSONAL_CATEGORY=true  # set false to hide Personal and force General instead
```

5. Run the game:
```bash
streamlit run streamlit_app.py
```

## How to Play
### Personal Category (profile‑aware)

- When you choose **Personal**, the game uses your profile Bio (bio‑only, not other fields) from `users_bio.json` to request personally relevant words and hints.
- If API calls fail or are disabled, Personal falls back to a deterministic offline generator that samples from your Bio with allow/deny lists and relevance scoring.
- With `BYPASS_API_WORD_SELECTION=true`, all other categories use the local dictionary; Personal still attempts the API and falls back offline as needed.
- Hint experience for Personal:
  - Personal words show only 1 hint per word.
  - If a contextual hint isn’t available, a helpful fallback like “Starts with ‘X’” is used.
  - The UI blocks with “Generating personal hints…” and retries until at least 3 hints exist for the current non‑Personal words (general hint system). If it can’t, a warning and a Retry button are shown.

Note on admin control:
- You can disable the Personal category across the app by setting `ENABLE_PERSONAL_CATEGORY=false` in `.env` and restarting the app.
- When disabled:
  - “Personal” is removed from category pickers.
  - Any existing or default “Personal” category is normalized to `general` at runtime.
  - The “How to Play” sections hide the Personal subsection.
  - Accepted values: `true/1/yes/on` to enable, `false/0/no/off` to disable.


1. Configure your game:
   - Choose word length (3-15 letters)
   - Select a category (General, Animals, Food, Personal, etc.)
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

### New Hint Experience (Mobile‑friendly)

- Single, colorful hint card replaces the old two buttons.
- The card displays the latest hint text in a large, high‑contrast banner.
- Click/tap the hint card to request the next hint.
- First hint each round is shown automatically for free (no penalty).
- Up to two additional hints are available per word with the same penalty (‑10 points each).
- Designed for phones: fluid text sizing and proper wrapping prevent truncation; the card uses full width and breaks long lines gracefully.

Implementation notes (for developers):
- The visual card is rendered as a gradient banner; a full‑size overlay button captures clicks while keeping the visual intact.
- Styles use CSS clamp() and wrapping rules (overflow‑wrap/word‑break/white‑space) to ensure readability on small screens.

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

## Aggregates and Performance

To avoid rescanning `game_results.json` on every render, the app maintains a compact aggregates store:

- Location: `game_data/aggregates.json` (override with `AGGREGATES_PATH`)
- Bootstrap: On first run, if the file is missing/empty, it auto-imports all existing games from `GAME_RESULTS_PATH` and builds aggregates
- Incremental updates: On each Game Over, new results are appended to the aggregates
- Consumers: Leaderboards, SEI tables, and stats line graphs read from the aggregates for O(Top N) reads

Environment variables:
- `GAME_RESULTS_PATH` (default: `game_results.json`) — full games log (append-only)
- `AGGREGATES_PATH` (default: `game_data/aggregates.json`) — derived data for fast UI queries

Docker/AWS paths (WORKDIR=/app):
- `/app/game_data/aggregates.json` (mount this directory for persistence)

Maintenance:
- To rebuild from scratch, delete the aggregates file and restart; it will bootstrap from `GAME_RESULTS_PATH` on next run

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

## Personal Pool (Bio‑only)

- Storage: `users_bio.json` (see Data Files). The file is auto‑created on first access if missing.
- Source: Only tokens from the user’s Bio are considered. Occupation/Education/Address are not used for pool selection.
- Size and top‑ups:
  - Target size is configurable via `.env` (`PERSONAL_POOL_MAX`, default 60).
  - When entering Personal, the app auto‑tops up in batches until the pool reaches the target size, avoiding duplicates.
  - Batch size and API attempt limits are configurable.
- API vs Offline:
  - API is attempted first (unless no/invalid key), with robust JSON repair.
  - If API returns fewer than requested items, partial results are kept and only the remainder is requested on subsequent retries.
  - If still short, the offline generator fills the remainder.
- Biasing and filtering:
  - Deny‑lists remove generic tokens (e.g., “have”, “since”, numbers, common verbs like “watch”).
  - Name‑to‑role mapping requires proper capitalization in Bio (e.g., “Zina”).
  - Location terms from the Bio (e.g., “San Jose”, “Almaden”) map to “Related to where you live.”
- Hints:
  - Contextual one‑liners are generated from Bio; otherwise fallback to first‑letter hints.
  - Generic “Related to your profile” hints are avoided and cleaned via a migration.

### Environment Variables (Personal Pool)

Add these to `.env` as needed:

```env
# Personal pool knobs
PERSONAL_POOL_MAX=60              # Max items per user pool
PERSONAL_POOL_BATCH_SIZE=10       # Items requested per top‑up
PERSONAL_POOL_API_ATTEMPTS=3      # Consecutive API retries per top‑up

# Enable/disable Personal in UI and logic
ENABLE_PERSONAL_CATEGORY=true

# Optional: bypass API for non‑Personal categories
BYPASS_API_WORD_SELECTION=true

# Paths
USERS_BIO_FILE=users_bio.json
```

## Data Files

- `users.json`: authentication and non‑bio profile basics (e.g., username, email, counters).
- `users_bio.json`: stores per‑user `bio` and `personal_pool` only. Auto‑created on first access.
- `game_results.json`: append‑only game logs.
- `game_data/aggregates.json`: derived stats for UI.

## Migrations

- Split bio/pool out of users.json:
  - `python backend/migrations/split_users_bio.py`
  - Moves `bio` and `personal_pool` to `users_bio.json` and strips them from `users.json`.
- Rewrite generic personal hints to clearer ones:
  - `python backend/migrations/rewrite_personal_hints.py`
  - Rewrites “From your bio”/generic hints to contextual or first‑letter hints; also removes generic tokens.

Notes:
- Fresh deployments: `users_bio.json` is created automatically when first accessed.
- Personal pool capacity guard prevents API calls once the pool reaches `PERSONAL_POOL_MAX`.

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