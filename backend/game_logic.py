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
    def __init__(self, word_length: int, subject: str, mode: str, nickname: str = "", initial_score: int = 0, difficulty: str = "Medium"):
        self.word_selector = WordSelector()
        self.stats_manager = GameStats()
        
        # Handle word length
        if word_length == "any":
            word_length = random.randint(3, 10)
        self.word_length = word_length
        
        # Handle subject/category
        if subject == "any":
            subject = random.choice(["general", "animals", "food", "places", "science", "tech", "sports"])
        self.subject = subject
        self.original_subject = subject  # <-- Store the original subject for the round
        
        self.mode = mode  # "Fun" or "Challenge"
        self.nickname = nickname
        self.score = initial_score  # Initialize with provided score
        
        # Set difficulty-based parameters
        self.difficulty = difficulty
        self.difficulty_settings = {
            "Easy": {
                "max_hints": 10,
                "hint_interval": 45,
                "question_penalty": -0.5,
                "hint_penalty": -5,
                "guess_penalty": -5,
                "base_points_multiplier": 25
            },
            "Medium": {
                "max_hints": 7,
                "hint_interval": 30,
                "question_penalty": -1,
                "hint_penalty": -10,
                "guess_penalty": -10,
                "base_points_multiplier": 20
            },
            "Hard": {
                "max_hints": 5,
                "hint_interval": 20,
                "question_penalty": -2,
                "hint_penalty": -15,
                "guess_penalty": -15,
                "base_points_multiplier": 15
            }
        }
        
        # Get settings for current difficulty
        self.current_settings = self.difficulty_settings[self.difficulty]
        
        self.total_points = 0  # Track total points for the game
        self.questions_asked = []  # Initialize questions list
        self.hints_given = []  # Track hints given
        self.available_hints = []  # Store all available hints
        self.start_time = time.time()
        self.end_time = None
        self.selected_word = None
        self.game_over = False
        self.guesses_made = 0  # Track number of guesses
        
        # Select word and initialize hints
        try:
            self.selected_word = get_fallback_word(word_length, subject)
            if not self.selected_word:
                raise ValueError("Failed to select a word")
            
            # Initialize available hints based on difficulty
            all_hints = []
            
            # Try to get hints from hints.json first
            try:
                hints_file = os.path.join('backend', 'data', 'hints.json')
                logger.info(f"Looking for hints in: {hints_file}")
                
                # Map categories to general if needed
                if subject in ["tech", "movies", "music", "brands", "history"]:
                    subject = "general"
                
                with open(hints_file, 'r', encoding='utf-8') as f:
                    hints_data = json.load(f)
                    if "templates" in hints_data and subject in hints_data["templates"] and self.selected_word in hints_data["templates"][subject]:
                        logger.info(f"Found hints in hints.json for '{self.selected_word}' in category '{subject}'")
                        all_hints = hints_data["templates"][subject][self.selected_word]
                        logger.info(f"Using {len(all_hints)} hints from hints.json")
                    else:
                        logger.warning(f"Word '{self.selected_word}' not found in hints.json templates for category '{subject}'")
            except FileNotFoundError:
                logger.warning(f"hints.json file not found at {hints_file}")
            except json.JSONDecodeError:
                logger.warning("Error decoding hints.json")
            except Exception as e:
                logger.warning(f"Error reading hints.json: {e}")
            
            # If no hints from hints.json, get hints from word_selector
            if not all_hints:
                all_hints = self.word_selector.generate_all_hints(self.selected_word, subject)
            
            logger.info(f"Generated {len(all_hints)} total hints for word '{self.selected_word}'")
            
            # Separate static hints (from hints.json or WORD_HINTS) and dynamic hints
            static_hints = []
            dynamic_hints = []
            
            # Check if hints are from hints.json or WORD_HINTS
            for hint in all_hints:
                if hint.startswith("This") and subject.lower() in hint.lower() and "term" in hint:
                    dynamic_hints.append(hint)
                else:
                    static_hints.append(hint)
            
            logger.info(f"Found {len(static_hints)} static hints and {len(dynamic_hints)} dynamic hints")
            
            # Prioritize static hints, then add dynamic hints if needed
            max_hints = self.current_settings["max_hints"]
            if len(static_hints) >= max_hints:
                self.available_hints = static_hints[:max_hints]
                logger.info(f"Using {len(self.available_hints)} static hints")
            else:
                # Use all static hints and generate additional dynamic hints
                self.available_hints = static_hints
                remaining_slots = max_hints - len(static_hints)
                if remaining_slots > 0:
                    # Generate new dynamic hints for the remaining slots
                    for i in range(remaining_slots):
                        new_hint = self.word_selector.get_semantic_hint(
                            self.selected_word,
                            subject,
                            previous_hints=self.available_hints
                        )
                        if new_hint and new_hint not in self.available_hints:
                            self.available_hints.append(new_hint)
                logger.info(f"Using {len(static_hints)} static hints and {len(self.available_hints) - len(static_hints)} dynamic hints")
            
        except Exception as e:
            logger.error(f"Error initializing game: {e}")
            # Ensure we have a word even if something fails
            self.selected_word = get_fallback_word(word_length, subject)
            # Generate fallback hints based on difficulty
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
        if self.mode == "Challenge":
            points_added = self.current_settings["question_penalty"]
            self.score += points_added
            self.total_points += points_added
        
        # Record the question and answer
        self.questions_asked.append({
            "question": question,
            "normalized_question": normalized_question,
            "key_terms": list(key_terms),
            "answer": answer,
            "points_added": points_added if self.mode == "Challenge" else 0
        })
            
        return True, answer, points_added

    def make_guess(self, guess: str) -> Tuple[bool, str, int]:
        """Make a final guess for the word."""
        if self.game_over:
            return False, "Game is already over!", 0
            
        if not guess.strip():
            return False, "Guess cannot be empty!", 0
        
        # Use the actual selected word's length for validation
        expected_length = len(self.selected_word) if self.selected_word else self.word_length
        if len(guess) != expected_length:
            return False, f"Guess must be {expected_length} letters long!", 0
        
        if not guess.isalpha():
            return False, "Guess must contain only letters!", 0
        
        self.guesses_made += 1
        is_correct = self.word_selector.verify_guess(self.selected_word, guess)
        
        points_added = 0
        if self.mode == "Challenge":
            if is_correct:
                # Calculate base points with difficulty multiplier
                base_points = (self.word_length * self.current_settings["base_points_multiplier"])
                
                # Add time bonus for Hard mode
                time_bonus = 0
                if self.difficulty == "Hard":
                    time_taken = time.time() - self.start_time
                    if time_taken < 60:  # Under 1 minute
                        time_bonus = 50
                    elif time_taken < 120:  # Under 2 minutes
                        time_bonus = 25
                        
                # Calculate final points
                question_penalty = len(self.questions_asked) * abs(self.current_settings["question_penalty"])
                points_added = max(base_points + time_bonus - question_penalty, 10)
            else:
                points_added = self.current_settings["guess_penalty"]
            
            self.score += points_added
            self.total_points += points_added
        
        self.game_over = is_correct
        if is_correct:
            self.end_time = time.time()
            self.stats_manager.record_game(self.get_game_summary())
        
        # Update message to show points change
        if is_correct:
            message = f"Correct! You won! Final score: {self.score}"
            if self.difficulty == "Hard" and points_added > base_points:
                message += f" (includes time bonus: +{time_bonus} points)"
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
        if self.mode == "Challenge":
            points_deducted = self.current_settings["hint_penalty"]
            self.score += points_deducted
            self.total_points += points_deducted
            logger.info(f"[HINT REQUEST] Applied point deduction: {points_deducted}")
        
        # Record the hint
        self.hints_given.append(hint)
        logger.info(f"[HINT REQUEST] Total hints given: {len(self.hints_given)}/{max_hints}")
        
        return hint, points_deducted

    def get_game_summary(self) -> Dict:
        """Get a summary of the game state."""
        # If end_time is not set but we need a summary, use current time
        current_time = time.time()
        end_time = self.end_time if self.end_time is not None else current_time
        duration = round(end_time - self.start_time)
        
        return {
            "word": self.selected_word,
            "selected_word": self.selected_word,  # Add selected_word field for compatibility
            "subject": self.subject,
            "mode": self.mode,
            "word_length": self.word_length,
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
        if self.mode == "Challenge":
            points_deducted = -50  # Deduct 50 points for showing word in Challenge mode
            self.score -= 50  # Subtract from score
            self.total_points -= 50  # Subtract from total points
            return points_deducted
        return 0

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