# WizWord — Product Pitch & Demo Guide

A fast, fun, and AI‑assisted word guessing game that boosts vocabulary and reasoning while delivering a delightful, share‑worthy experience.

## 1) Problem & Opportunity
- Casual word games are either too simple or too slow; most don’t feel smart, personal, or shareable.
- Educators and families want quick sessions that are actually meaningful, with gentle challenge and trackable progress.

## 2) What WizWord Does
- AI‑assisted yes/no answering and hinting to keep play flowing.
- Dynamic scoring and a 4‑minute “Beat” sprint to make every session exciting.
- Beautiful share cards with QR links for instant brag‑worthy moments.
- Optional Personal mode to tailor hints to a user’s profile (privacy‑aware).

## 3) Who It’s For
- Learners of all ages, families, teachers, and word‑game fans who want quick, meaningful play on any device.

---

## How to Play (Brief)
- Choose mode: Fun, Wiz, or Beat (4‑minute sprint)
- Pick a category or "Any"
- Interact: ask yes/no (−1), hints (−10, up to 3), guess anytime (correct +20 × word length; wrong −10), skip (−10)
- SEI efficiency score powers leaderboards and achievements
- Optional Personal: profile‑aware hints (may need a brief load)

---

## 4) Demo Flow (Suggested Script)
1. Login screen
   - Show quick access to Create Account, Try as Guest, and Account Options.
   - Highlight Delete/Reactivate account safety (token‑based, hidden input cleared).

   ![Account Options](../assets/ui/account_options.png)

2. How to Play
   - Open the in‑app “How to Play” with concise rules, scoring, and tips.

   ![How to Play](../assets/ui/how_to_play.png)

3. Start a Beat game (4 minutes)
   - Pick a category (or “any”), click Start.
   - Ask a yes/no letter question; request a hint; make a guess.
   - Show skip behavior and explain point trade‑offs.

4. Game Over screen
   - Show score summary, SEI chart, and per‑category leaderboard.
   - Generate a share card with QR and download/share it.

   Score trend and distribution examples:

   ![Score Trend](../score_trend.png)

   ![Score Distribution](../score_distribution.png)

   Share card template example:

   ![Share Card Template](../assets/share_card_template.png)

---

## 5) Key Features (Why We Win)
- Fast, approachable play on web and mobile
- AI‑assisted yes/no responses and hints for momentum
- 4‑minute Beat mode for high‑energy sessions
- SEI (Scoring Efficiency Index) to reward speed + accuracy
- Share cards with QR for social, classroom, or family use
- Personal mode (optional): profile‑aware hints with privacy guardrails
- Robust offline fallback (no API key required)

## 6) Differentiators (Under the Hood)
- Rate‑limit and quota monitoring via OpenRouter headers with email alerts
- Offline word engine with category/length coverage; instant responses
- Encryption (Fernet w/ PBKDF2‑derived key) for sensitive data at rest
- Account lifecycle: Delete (archival to deleted store) + email token Reactivate
- Per‑minute and per‑hour rate limiting; cooldowns to prevent abuse
- Streamlit UI, mobile‑friendly layout, modern visuals, and QR workflows

## 7) Architecture (High Level)
- UI: Streamlit (`streamlit_app.py`)
- Game Core: `backend/game_logic.py`, `backend/word_selector.py`
- Sessions & Stats: `backend/session_manager.py`, `backend/game_stats.py`
- Sharing: `backend/share_card.py`, `backend/share_utils.py`
- Auth & Email: `backend/user_auth.py` (SMTP), in‑app password reset
- Storage: local JSON by default; optional AWS (DynamoDB) when enabled

## 8) Privacy & Safety
- Sensitive data encrypted with Fernet; keys derived via PBKDF2
- Personal hints rely on Bio only; easy to disable via env (`ENABLE_PERSONAL_CATEGORY=false`)
- Deletion moves user to an archive file; bios and game logs are purged; confirmation email includes site URL from env

## 9) Setup (1‑minute)
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
pip install -r requirements.txt
streamlit run streamlit_app.py
```

Environment essentials in `.env`:
- `WIZWORD_SITE=https://your-site.example.com` (used in emails)
- `OPENROUTER_API_KEY` (optional; offline fallback is automatic)
- `SMTP_HOST/PORT/USER/PASS` for emails
- `ENABLE_PERSONAL_CATEGORY=true|false`

## 10) Call to Action
- Try a 2‑minute Beat run and share your card.
- Enable Personal to see tailored hints.
- Invite a friend with the QR share link.

## 11) Roadmap Preview
- Templates and themes for share cards
- Lightweight multiplayer & co‑op modes
- Classroom mode with teacher dashboards
- Native mobile packaging

---

### Notes for Presenters
- If screenshots are missing, capture them while running the app and save to:
  - `assets/ui/account_options.png`
  - `assets/ui/how_to_play.png`
- The gallery in this document will render them automatically.
