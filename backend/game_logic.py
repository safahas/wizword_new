from typing import Dict, List, Tuple, Optional
from .word_selector import WordSelector
from .game_stats import GameStats
import time
import re
import logging
import json
import os
import random
from backend.fallback_words import get_fallback_word

logger = logging.getLogger(__name__)

# Safe logging for non-ASCII content on Windows terminals
def _log_info_safe(prefix: str, text: str) -> None:
    # Always sanitize to ASCII with backslash escapes to avoid Windows console encoding errors
    try:
        combined = f"{prefix}{text}"
    except Exception:
        combined = str(prefix)
    try:
        sanitized = combined.encode('ascii', errors='backslashreplace').decode('ascii', errors='ignore')
    except Exception:
        sanitized = str(prefix).encode('ascii', errors='backslashreplace').decode('ascii', errors='ignore')
    try:
        logger.info(sanitized)
    except Exception:
        pass

class GameLogic:
    def __init__(self, word_length: int = None, subject: str = "general", mode: str = "Fun", nickname: str = "", initial_score: int = 0, difficulty: str = "Medium"):
        
        # Persist WordSelector across all GameLogic instances
        if not hasattr(GameLogic, 'word_selector'):
            GameLogic.word_selector = WordSelector()
        self.word_selector = GameLogic.word_selector
        self.stats_manager = GameStats(nickname=nickname)
        # Ignore word_length for word selection; keep for legacy only
        if subject == "any":
            subject = random.choice(["general", "animals", "food", "places", "science", "tech", "sports"])
        self.subject = subject
        self.original_subject = subject
        self.mode = mode
        self.nickname = nickname
        # Derive account username from Streamlit session if available
        self.account_username = None
        try:
            import streamlit as st  # type: ignore
            self.account_username = (st.session_state.get('user') or {}).get('username') or None
        except Exception:
            self.account_username = None

        def _pool_username() -> str:
            return (self.account_username or self.nickname or "global")
        self._pool_username = _pool_username
        self.score = initial_score
        self.difficulty = difficulty
        self.difficulty_settings = {
            "Easy": {"max_hints": 10, "hint_interval": 45, "question_penalty": -1, "hint_penalty": -5, "guess_penalty": -5, "base_points_multiplier": 25},
            "Medium": {"max_hints": 7, "hint_interval": 30, "question_penalty": -1, "hint_penalty": -10, "guess_penalty": -10, "base_points_multiplier": 20},
            "Hard": {"max_hints": 5, "hint_interval": 20, "question_penalty": -2, "hint_penalty": -15, "guess_penalty": -15, "base_points_multiplier": 15}
        }
        self.current_settings = self.difficulty_settings[self.difficulty]
        # For Beat mode, always limit hints to 3
        if self.mode == "Beat":
            self.current_settings["max_hints"] = 3
        # If Personal or FlashCard category, limit to 1 hint per word
        if str(self.subject).lower() in ('personal', 'flashcard'):
            self.current_settings["max_hints"] = 1
        self.total_points = 0
        # New: track only penalty points (sum of absolute negative deductions)
        self.total_penalty_points = 0
        self.questions_asked = []
        self.hints_given = []
        self.available_hints = []
        self.start_time = time.time()
        self.end_time = None
        self.selected_word = None
        self.game_over = False
        self.guesses_made = 0
        self.show_word_penalty_applied = False
        # Lightweight lazy-init for FlashCard on pre-game screens to avoid login delay
        try:
            subj_lower_lazy = str(self.subject).lower()
            lazy_env = str(os.getenv('FLASHCARD_LAZY_INIT', 'true')).strip().lower() in ('1','true','yes','on')
            pregame = False
            try:
                import streamlit as _st  # type: ignore
                pregame = not bool(_st.session_state.get('beat_started', False))
            except Exception:
                pregame = True
            if lazy_env and subj_lower_lazy == 'flashcard' and pregame:
                # Defer heavy selection until the user actually starts the Beat run
                self.selected_word = ''
                self.available_hints = []
                logger.info("[LAZY_INIT] Skipping FlashCard word selection at init; will select at start.")
                return
        except Exception:
            pass
        try:
            # Use account username if available for per-user tracking, else nickname, else 'global'
            username = self._pool_username()
            
            self.selected_word = self.word_selector.select_word(word_length, subject, username=username)
            
            if not self.selected_word:
                raise ValueError("Failed to select a word")
            all_hints = []
            # For 'Personal' and 'FlashCard' categories, skip hints.json lookup
            if str(self.original_subject).lower() not in ('personal', 'flashcard'):
                try:
                    # Prefer GameLogic helper if present; else use WordSelector's resolver
                    resolver = getattr(self, '_get_hints_file_for_user', None)
                    if callable(resolver):
                        hints_file = resolver(self._pool_username())
                    else:
                        hints_file = getattr(self.word_selector, '_get_hints_file_for_user', lambda _: os.path.join('backend','data','hints.json'))(self._pool_username())
                    logger.info(f"[HINTS_FILE_GAMELOGIC] user='{self._pool_username()}' subject='{subject}' file='{hints_file}'")
                    with open(hints_file, 'r', encoding='utf-8') as f:
                        hints_data = json.load(f)
                        # Try the original subject first (case-insensitive against hints.json keys)
                        lookup_subject = subject
                        templates = hints_data.get("templates", {})
                        ci_key_map = {k.lower(): k for k in templates.keys()}
                        subject_key = ci_key_map.get(str(lookup_subject).lower())
                        general_key = ci_key_map.get("general") if "general" in ci_key_map else "general"
                        if subject_key and self.selected_word in templates.get(subject_key, {}):
                            logger.info(f"Found hints in hints.json for '{self.selected_word}' in category '{subject_key}'")
                            all_hints = templates[subject_key][self.selected_word]
                            logger.info(f"Using {len(all_hints)} hints from hints.json")
                        elif general_key and self.selected_word in templates.get(general_key, {}):
                            logger.info(f"Falling back to 'general' for hints for '{self.selected_word}'")
                            all_hints = templates[general_key][self.selected_word]
                            logger.info(f"Using {len(all_hints)} hints from hints.json (general)")
                        else:
                            try:
                                cats = list((hints_data or {}).get('templates', {}).keys())
                            except Exception:
                                cats = []
                            logger.warning(f"Word '{self.selected_word}' not found in hints file '{hints_file}' for category '{lookup_subject}'. Available categories={cats[:10]}")
                except FileNotFoundError:
                    logger.warning(f"Hints file not found at {hints_file}")
                except json.JSONDecodeError:
                    logger.warning("Error decoding hints file")
                except Exception as e:
                    logger.warning(f"Error reading hints file: {e}")
            if not all_hints:
                # Use API-generated hints if available, otherwise fallback
                api_hints = getattr(self.word_selector, "_last_api_hints", None)
                if api_hints:
                    logger.info("[HINT REQUEST] Using cached API hints from WordSelector")
                    self.word_selector._last_api_hints = None
                else:
                    subj_lower = str(self.original_subject).lower()
                    if subj_lower == 'personal':
                        # Try user-specific pool first (one hint)
                        pool = self.word_selector.get_user_personal_pool(self._pool_username())
                        hint_from_pool = None
                        try:
                            if pool:
                                matched = next((it for it in pool if str(it.get('word','')).lower() == str(self.selected_word or '').lower()), None)
                                if matched and matched.get('hint'):
                                    hint_from_pool = matched['hint']
                                elif pool[0].get('hint'):
                                    hint_from_pool = pool[0]['hint']
                        except Exception:
                            hint_from_pool = None
                        if hint_from_pool:
                            all_hints = [hint_from_pool]
                        else:
                            api_hints = self.word_selector.get_api_hints_force(self.selected_word, 'personal', n=1)
                    elif subj_lower == 'flashcard':
                        # Prefer pre-generated flash_pool hint first
                        try:
                            from backend.bio_store import get_active_flash_set_name, get_flash_set_pool, get_flash_pool
                            _uname = self._pool_username()
                            _active_name = get_active_flash_set_name(_uname) or 'flashcard'
                            pool_fc = get_flash_set_pool(_uname, _active_name) or []
                            if not isinstance(pool_fc, list) or not pool_fc:
                                pool_fc = get_flash_pool(_uname) or []
                        except Exception:
                            pool_fc = []
                        if isinstance(pool_fc, list) and pool_fc:
                            try:
                                w_lc = str(self.selected_word or '').strip().lower()
                                # Build map once for robust lookup
                                pool_map = { str(it.get('word','')).strip().lower(): str(it.get('hint','')) for it in pool_fc if isinstance(it, dict) }
                                if w_lc in pool_map and pool_map[w_lc]:
                                    all_hints = [pool_map[w_lc]]
                                else:
                                    import logging as _lg
                                    _lg.getLogger(__name__).info(f"[FLASH_HINT] Pool hint not found for '{w_lc}'. Active set: {_active_name}. Pool keys sample: {list(pool_map.keys())[:5]}")
                            except Exception:
                                pass
                        # Do NOT call API for FlashCard during gameplay; use local/doc-grounded fallback
                        if not all_hints and not api_hints:
                            try:
                                from backend.bio_store import get_flash_text
                                flash_text = get_flash_text(self._pool_username())
                            except Exception:
                                flash_text = ''
                            try:
                                hint_local = self.word_selector._make_flash_hint(self.selected_word, flash_text)
                            except Exception:
                                hint_local = None
                            if hint_local:
                                all_hints = [hint_local] * self.current_settings["max_hints"]
                    else:
                        api_hints = self.word_selector.get_api_hints(self.selected_word, subject, n=self.current_settings["max_hints"])
                if api_hints:
                    all_hints = api_hints
                    logger.info(f"[HINT REQUEST] Using {len(all_hints)} API-generated hints for '{self.selected_word}'")
                    # Persist first hint into user's pools for future runs (Personal/FlashCard)
                    try:
                        first_hint = str(all_hints[0]) if isinstance(all_hints, list) and all_hints else None
                        subj_lower2 = str(self.original_subject).lower()
                        if first_hint and subj_lower2 == 'personal':
                            self.word_selector.add_or_update_personal_hint(self._pool_username(), self.selected_word, first_hint)
                        elif first_hint and subj_lower2 == 'flashcard':
                            try:
                                from backend.bio_store import get_flash_pool, set_flash_pool
                                uname = self._pool_username()
                                pool_fc = get_flash_pool(uname) or []
                                updated = False
                                for it in pool_fc:
                                    if str(it.get('word','')).lower() == str(self.selected_word or '').lower():
                                        it['hint'] = first_hint
                                        updated = True
                                        break
                                if not updated:
                                    pool_fc.append({'word': self.selected_word, 'hint': first_hint})
                                set_flash_pool(uname, pool_fc)
                            except Exception:
                                pass
                    except Exception:
                        pass
                if not all_hints:
                    fallback_hint = (
                        f"This {subject} term has specific characteristics"
                        if str(self.original_subject).lower() != 'personal'
                        else "This Personal term has specific characteristics"
                    )
                    all_hints = [fallback_hint] * self.current_settings["max_hints"]
                    logger.warning(f"[HINT REQUEST] Using fallback hints for '{self.selected_word}'")
            # Sanitize and de-duplicate hints (do not reveal the word itself)
            def _mask_word_in_hint(h: str, word: str) -> str:
                try:
                    if not h or not word:
                        return h
                    letters = ''.join([c for c in (word or '') if c.isalpha()])
                    if not letters:
                        return h
                    import re as _re
                    pat = _re.compile(rf"\b{_re.escape(letters)}\b", _re.IGNORECASE)
                    if pat.search(h):
                        return pat.sub('[redacted]', h)
                    return h
                except Exception:
                    return h
            safe_hints = []
            for h in (all_hints or []):
                m = _mask_word_in_hint(str(h), str(self.selected_word or ''))
                if m and m not in safe_hints:
                    safe_hints.append(m)
            all_hints = safe_hints
            logger.info(f"Generated {len(all_hints)} total hints for word '{self.selected_word}'")
            self.available_hints = all_hints[:self.current_settings["max_hints"]]
            logger.info(f"Using {len(self.available_hints)} hints for '{self.selected_word}'")
        except Exception as e:
            logger.error(f"Error initializing game: {e}")
            # Ensure word_length is always an int for fallback
            fallback_length = word_length if isinstance(word_length, int) and 3 <= word_length <= 10 else 5
            
            self.selected_word = get_fallback_word(fallback_length, subject)
            self.available_hints = [f"This {subject} term has specific characteristics"] * self.current_settings["max_hints"]
            logger.warning(f"Using {len(self.available_hints)} fallback hints due to initialization error")

    def ask_question(self, question: str) -> Tuple[bool, str, int]:
        """Ask a question about the word."""
        if self.game_over:
            return False, "Game is already over!", 0

        if not question.strip():
            return False, "Question cannot be empty!", 0

        # Normalize the question by removing punctuation and extra spaces
        normalized_question = re.sub(r'[^\w\s]', '', question.lower()).strip()
        normalized_question = ' '.join(normalized_question.split())

        # Extract key terms from the question
        key_terms = set(normalized_question.split())

        # Check if this question was already asked
        for q in self.questions_asked:
            normalized_prev = re.sub(r'[^\w\s]', '', q["question"].lower()).strip()
            normalized_prev = ' '.join(normalized_prev.split())
            prev_terms = set(normalized_prev.split())

            if normalized_question == normalized_prev:
                return False, "You already asked this question!", 0

            if key_terms == prev_terms:
                return False, "You already asked this question in a different way!", 0

            if key_terms.issubset(prev_terms) or prev_terms.issubset(key_terms):
                return False, "You already asked a similar question!", 0

        # Get answer from word selector
        
        answer = self.word_selector.answer_question(self.selected_word, question, self.subject)

        points_added = 0
        if self.mode in ("Wiz", "Beat"):
            points_added = self.current_settings["question_penalty"]
            self.score += points_added
            self.total_points += points_added
            if points_added < 0:
                self.total_penalty_points += abs(points_added)
            

        # Record the question and answer
        self.questions_asked.append({
            "question": question,
            "normalized_question": normalized_question,
            "key_terms": list(key_terms),
            "answer": answer,
            "points_added": points_added if self.mode in ("Wiz", "Beat") else 0
        })

        return True, answer, points_added

    def make_guess(self, guess: str) -> Tuple[bool, str, int]:
        """Make a final guess for the word."""
        if self.game_over:
            return False, "Game is already over!", 0
        
        # Remove only leading and trailing spaces from the guess for validation
        guess = guess.strip()
        
        if not guess:
            return False, "Guess cannot be empty!", 0
        
        # Use the actual selected word's length for validation
        expected_length = len(self.selected_word) if self.selected_word else 0
        if len(guess) != expected_length:
            return False, f"Guess must be {expected_length} letters long!", 0
        
        if not guess.isalpha():
            return False, "Guess must contain only letters!", 0
        
        self.guesses_made += 1
        is_correct = self.word_selector.verify_guess(self.selected_word, guess)
        
        points_added = 0
        if self.mode in ("Wiz", "Beat"):
            if is_correct:
                # Always award 100 points per correct word, regardless of word length or difficulty
                points_added = 100
            else:
                points_added = self.current_settings["guess_penalty"]
            
            self.score += points_added
            self.total_points += points_added
            if points_added < 0:
                self.total_penalty_points += abs(points_added)
        
        # Add debug print for wrong/correct guess
        
        
        self.game_over = is_correct
        if is_correct:
            self.end_time = time.time()
        
        if is_correct:
            message = f"Correct! You guessed the word '{self.selected_word}'. Current score: {self.score}"
            # Only mark as played on correct guess (not on Skip)
            try:
                username = self._pool_username()
                self.word_selector.mark_word_played(self.selected_word, username, self.subject)
            except Exception:
                pass
        else:
            point_text = f" (-{abs(points_added)} points)" if points_added < 0 else ""
            message = f"Wrong! Try again. Current score: {self.score}{point_text}"
        
        return is_correct, message, points_added

    def get_hint(self) -> Tuple[str, int]:
        """
        Get a semantic hint about the word.
        Returns: (hint, points_deducted)
        """
        # Defensive: if lazy init deferred selection (e.g., FlashCard pre-game), select now on first hint request
        if not self.selected_word:
            try:
                username = self._pool_username()
                # Use a reasonable default length for selection; actual length comes from the selector
                self.selected_word = self.word_selector.select_word(5, self.original_subject, username=username)
            except Exception:
                self.selected_word = None
        if not self.selected_word:
            logger.info("[HINT REQUEST] No word selected yet; hint unavailable until word is ready.")
            return "Preparing word… please try again in a moment.", 0
        if self.game_over:
            logger.info("[HINT REQUEST] Game is already over, no hint provided")
            return "Game is already over!", 0
        
        max_hints = self.current_settings["max_hints"]
        if len(self.hints_given) >= max_hints:
            logger.info(f"[HINT REQUEST] Maximum hints ({max_hints}) reached")
            return f"Maximum hints ({max_hints}) reached!", 0
        
        # Get next available hint
        hint = None
        if self.available_hints:
            available = [h for h in self.available_hints if h not in self.hints_given]
            if available:
                hint = available[0]
                _log_info_safe("[HINT REQUEST] Using pre-generated hint: ", str(hint))
        
        # If no pre-generated hints available, try FlashCard pool (lazy-init path), then get a new one
        if not hint:
            subj_lower = str(self.original_subject).lower()
            if subj_lower == 'flashcard':
                try:
                    from backend.bio_store import get_active_flash_set_name, get_flash_set_pool, get_flash_pool
                    _uname = self._pool_username()
                    _active_name = get_active_flash_set_name(_uname) or 'flashcard'
                    pool_fc = get_flash_set_pool(_uname, _active_name) or []
                    if not isinstance(pool_fc, list) or not pool_fc:
                        pool_fc = get_flash_pool(_uname) or []
                except Exception:
                    pool_fc = []
                if isinstance(pool_fc, list) and pool_fc:
                    try:
                        w_lc = str(self.selected_word or '').strip().lower()
                        pool_map = { str(it.get('word','')).strip().lower(): str(it.get('hint','')) for it in pool_fc if isinstance(it, dict) }
                        if w_lc in pool_map and pool_map[w_lc]:
                            hint = pool_map[w_lc]
                            logger.info(f"[HINT REQUEST] Using pool hint for FlashCard word '{self.selected_word}': {hint}")
                        else:
                            import logging as _lg
                            _lg.getLogger(__name__).info(f"[FLASH_HINT] Pool hint not found (lazy) for '{w_lc}'. Active set: {_active_name}. Pool keys sample: {list(pool_map.keys())[:5]}")
                    except Exception:
                        pass
            if not hint:
                logger.info("[HINT REQUEST] No pre-generated hints available, getting new hint")
                # Always use the original subject for hint retrieval
                hint = self.word_selector.get_semantic_hint(
                    self.selected_word,
                    self.original_subject,
                    self.hints_given,
                    max_hints=self.current_settings["max_hints"]
                )
                logger.info(f"[HINT REQUEST] Generated new hint: {hint}")
        
        points_deducted = 0
        if self.mode == "Beat":
            # First hint is free, 2nd and 3rd cost points
            if len(self.hints_given) >= 1:
                points_deducted = self.current_settings["hint_penalty"]
                self.score += points_deducted
                self.total_points += points_deducted
                if points_deducted < 0:
                    self.total_penalty_points += abs(points_deducted)
                logger.info(f"[HINT REQUEST] Applied point deduction: {points_deducted}")
        elif self.mode == "Wiz":
            points_deducted = self.current_settings["hint_penalty"]
            self.score += points_deducted
            self.total_points += points_deducted
            if points_deducted < 0:
                self.total_penalty_points += abs(points_deducted)
        
        # Record the hint
        self.hints_given.append(hint)
        remaining = max(0, self.current_settings["max_hints"] - len(self.hints_given))
        logger.info(f"[HINT REQUEST] Total hints given: {len(self.hints_given)}/{self.current_settings['max_hints']}")
        
        return hint, points_deducted

    def get_game_summary(self) -> Dict:
        """Get a summary of the game state."""
        # If end_time is not set but we need a summary, use current time
        current_time = time.time()
        end_time = self.end_time if self.end_time is not None else current_time
        if self.mode == "Beat":
            beat_mode_time = int(os.getenv("BEAT_MODE_TIME", 300))
            duration = beat_mode_time  # Use env var for Beat mode round time
        else:
            duration = round(end_time - self.start_time)
        actual_length = len(self.selected_word) if self.selected_word else 0
        return {
            "word": self.selected_word,
            "selected_word": self.selected_word,  # Add selected_word field for compatibility
            "subject": self.subject,
            "mode": self.mode,
            "word_length": actual_length,
            "score": self.score,
            "total_points": self.total_points,
            "questions_asked": self.questions_asked,
            "hints_given": self.hints_given,
            "available_hints": self.available_hints,  # Add all available hints
            "guesses_made": self.guesses_made,
            "start_time": self.start_time,
            "end_time": end_time,
            "duration": duration,
            "time_taken": duration,  # Add time_taken field for compatibility
            "game_over": self.game_over,
            "nickname": self.nickname,
            "difficulty": self.difficulty
        }

    def get_recently_used_words(self) -> list:
        """Get the list of recently used words."""
        return self.word_selector.get_recently_used_words()

    def apply_show_word_penalty(self) -> int:
        """
        Apply penalty for showing the word.
        Returns: points_deducted
        """
        penalty = 0
        if self.mode in ("Wiz", "Fun", "Beat"):
            if self.selected_word:
                penalty = -100  # Always -100 points
            else:
                penalty = -50  # fallback if word is missing
            if not getattr(self, 'show_word_penalty_applied', False):
                self.score += penalty  # penalty is negative
                self.total_points += penalty
                # Track penalty separately
                if penalty < 0:
                    self.total_penalty_points += abs(penalty)
                self.show_word_penalty_applied = True
                # Do NOT mark Show Word as played to avoid blocking repeats after reveal/skip
            else:
                penalty = 0  # No penalty if already applied
        return penalty

    def is_game_over(self) -> bool:
        """Check if the game is over."""
        return self.game_over

    def get_player_stats(self) -> Dict:
        """Get statistics for the current player."""
        return self.stats_manager.get_player_stats(self.nickname) if self.nickname else {}

    def get_leaderboard(self, mode: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        """Get the leaderboard, optionally filtered by mode and category."""
        return self.stats_manager.get_leaderboard(mode, category)

    def get_daily_stats(self) -> Dict:
        """Get daily statistics."""
        return self.stats_manager.get_daily_challenge_stats()

    def generate_performance_graphs(self) -> Dict[str, str]:
        """Generate performance graphs."""
        return self.stats_manager.generate_performance_graphs() 