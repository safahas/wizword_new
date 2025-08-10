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

class GameLogic:
    def __init__(self, word_length: int = None, subject: str = "general", mode: str = "Fun", nickname: str = "", initial_score: int = 0, difficulty: str = "Medium"):
        print(f"[DEBUG][GameLogic.__init__] word_length: {word_length} (type: {type(word_length)}), subject: {subject} (type: {type(subject)})")
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
        try:
            # Instead of selecting a word without username, always use nickname for recent word tracking
            username = self.nickname if self.nickname else "global"
            print(f"[DEBUG][GameLogic.__init__] Calling select_word with word_length={word_length}, subject={subject}, username={username}")
            self.selected_word = self.word_selector.select_word(word_length, subject, username=username)
            print(f"[DEBUG] selected_word set to: {repr(self.selected_word)}")
            if not self.selected_word:
                raise ValueError("Failed to select a word")
            all_hints = []
            try:
                hints_file = os.path.join('backend', 'data', 'hints.json')
                logger.info(f"Looking for hints in: {hints_file}")
                # Remove forced mapping of tech/movies/music/brands/history to general for hint lookup
                # if subject in ["tech", "movies", "music", "brands", "history"]:
                #     subject = "general"
                with open(hints_file, 'r', encoding='utf-8') as f:
                    hints_data = json.load(f)
                    # Try the original subject first
                    lookup_subject = subject
                    if "templates" in hints_data and lookup_subject in hints_data["templates"] and self.selected_word in hints_data["templates"][lookup_subject]:
                        logger.info(f"Found hints in hints.json for '{self.selected_word}' in category '{lookup_subject}'")
                        all_hints = hints_data["templates"][lookup_subject][self.selected_word]
                        logger.info(f"Using {len(all_hints)} hints from hints.json")
                    # If not found, fall back to 'general'
                    elif "templates" in hints_data and "general" in hints_data["templates"] and self.selected_word in hints_data["templates"]["general"]:
                        logger.info(f"Falling back to 'general' for hints for '{self.selected_word}'")
                        all_hints = hints_data["templates"]["general"][self.selected_word]
                        logger.info(f"Using {len(all_hints)} hints from hints.json (general)")
                    else:
                        logger.warning(f"Word '{self.selected_word}' not found in hints.json templates for category '{lookup_subject}' or 'general'")
            except FileNotFoundError:
                logger.warning(f"hints.json file not found at {hints_file}")
            except json.JSONDecodeError:
                logger.warning("Error decoding hints.json")
            except Exception as e:
                logger.warning(f"Error reading hints.json: {e}")
            if not all_hints:
                # Use API-generated hints if available, otherwise fallback
                api_hints = self.word_selector.get_api_hints(self.selected_word, subject, n=self.current_settings["max_hints"])
                if api_hints:
                    all_hints = api_hints
                    logger.info(f"[HINT REQUEST] Using {len(all_hints)} API-generated hints for '{self.selected_word}'")
                else:
                    all_hints = [f"This {subject} term has specific characteristics"] * self.current_settings["max_hints"]
                    logger.warning(f"[HINT REQUEST] Using fallback hints for '{self.selected_word}'")
            logger.info(f"Generated {len(all_hints)} total hints for word '{self.selected_word}'")
            # Deduplicate all_hints
            all_hints = list(dict.fromkeys(all_hints))
            self.available_hints = all_hints[:self.current_settings["max_hints"]]
            logger.info(f"Using {len(self.available_hints)} hints for '{self.selected_word}'")
        except Exception as e:
            logger.error(f"Error initializing game: {e}")
            # Ensure word_length is always an int for fallback
            fallback_length = word_length if isinstance(word_length, int) and 3 <= word_length <= 10 else 5
            print(f"[DEBUG][GameLogic.__init__] Fallback: using fallback_length={fallback_length}, subject={subject}")
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
        print(f"[DEBUG] Passing word to answer_question: {repr(self.selected_word)}")
        answer = self.word_selector.answer_question(self.selected_word, question, self.subject)

        points_added = 0
        if self.mode in ("Wiz", "Beat"):
            points_added = self.current_settings["question_penalty"]
            self.score += points_added
            self.total_points += points_added
            if points_added < 0:
                self.total_penalty_points += abs(points_added)
            print(f"[DEBUG] Penalty applied in ask_question: {points_added}, new score: {self.score}")  # <-- Debug print

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
        print(f"[DEBUG] make_guess: is_correct={is_correct}, points_added={points_added}, guess_penalty={self.current_settings['guess_penalty']}")
        
        self.game_over = is_correct
        if is_correct:
            self.end_time = time.time()
        
        if is_correct:
            message = f"Correct! You guessed the word '{self.selected_word}'. Current score: {self.score}"
        else:
            point_text = f" (-{abs(points_added)} points)" if points_added < 0 else ""
            message = f"Wrong! Try again. Current score: {self.score}{point_text}"
        
        return is_correct, message, points_added

    def get_hint(self) -> Tuple[str, int]:
        """
        Get a semantic hint about the word.
        Returns: (hint, points_deducted)
        """
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
                logger.info(f"[HINT REQUEST] Using pre-generated hint: {hint}")
        
        # If no pre-generated hints available, get a new one
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
                # Mark the word as played (add to recent list)
                username = self.nickname if self.nickname else "global"
                self.word_selector.mark_word_played(self.selected_word, username, self.subject)
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