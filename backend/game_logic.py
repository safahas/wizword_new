from typing import Dict, List, Tuple, Optional
from .word_selector import WordSelector
from .game_stats import GameStats
import time
import re

class GameLogic:
    def __init__(self, word_length: int, subject: str, mode: str, nickname: str = "", initial_score: int = 0):
        self.word_selector = WordSelector()
        self.stats_manager = GameStats()
        self.word_length = word_length
        self.subject = subject
        self.mode = mode  # "Fun" or "Challenge"
        self.nickname = nickname
        self.score = initial_score  # Initialize with provided score
        self.total_points = 0  # Track total points for the game
        self.questions_asked = []  # Initialize questions list
        self.hints_given = []  # Track hints given
        self.start_time = time.time()
        self.end_time = None
        self.selected_word = None
        self.game_over = False
        self.guesses_made = 0  # Track number of guesses
        
        # Initialize the game by selecting a word
        self.selected_word = self.word_selector.select_word(word_length, subject)

    def ask_question(self, question: str) -> Tuple[bool, str, int]:
        """
        Ask a question about the word.
        Returns: (is_valid, answer, points_added)
        """
        if self.game_over:
            return False, "Game is already over!", 0
            
        if not question.strip():
            return False, "Question cannot be empty!", 0
            
        # Normalize the question by removing punctuation and extra spaces
        normalized_question = re.sub(r'[^\w\s]', '', question.lower()).strip()
        normalized_question = ' '.join(normalized_question.split())  # Remove extra spaces
        
        # Extract key terms from the question
        key_terms = set(normalized_question.split())
        
        # Check if this question was already asked (using normalized form)
        for q in self.questions_asked:
            normalized_prev = re.sub(r'[^\w\s]', '', q["question"].lower()).strip()
            normalized_prev = ' '.join(normalized_prev.split())
            prev_terms = set(normalized_prev.split())
            
            # Check for exact matches
            if normalized_question == normalized_prev:
                return False, "You already asked this question!", 0
            
            # Check for questions with the same key terms
            if key_terms == prev_terms:
                return False, "You already asked this question in a different way!", 0
            
            # Check for questions that are subsets of each other
            if key_terms.issubset(prev_terms) or prev_terms.issubset(key_terms):
                return False, "You already asked a similar question!", 0
        
        # Get answer from word selector
        is_valid, answer = self.word_selector.answer_question(self.selected_word, question)
        
        points_added = 0
        if is_valid:
            # In Challenge mode, deduct points for questions
            if self.mode == "Challenge":
                points_added = -1  # Deduct 1 point per question in Challenge mode
                self.score += points_added
                self.total_points += points_added
            
            # Record the question and answer
            self.questions_asked.append({
                "question": question,
                "normalized_question": normalized_question,  # Store normalized form
                "key_terms": list(key_terms),  # Store key terms for better comparison
                "answer": answer,
                "points_added": points_added if self.mode == "Challenge" else 0  # Only show points in Challenge mode
            })
            
        return is_valid, answer, points_added if self.mode == "Challenge" else 0  # Only return points in Challenge mode

    def make_guess(self, guess: str) -> Tuple[bool, str, int]:
        """
        Make a final guess for the word.
        Returns: (is_correct, message, points_added)
        """
        if self.game_over:
            return False, "Game is already over!", 0
            
        if not guess.strip():
            return False, "Guess cannot be empty!", 0
            
        if len(guess) != self.word_length:
            return False, f"Guess must be {self.word_length} letters long!", 0
            
        if not guess.isalpha():
            return False, "Guess must contain only letters!", 0
        
        self.guesses_made += 1
        is_correct = self.word_selector.verify_guess(self.selected_word, guess)
        
        points_added = 0
        if self.mode == "Challenge":
            if is_correct:
                # Award points based on word length and questions asked
                base_points = (self.word_length * 20)  # Base points for word length bonus
                question_penalty = len(self.questions_asked) * 1  # Penalty for questions asked (1 point each)
                # The final score should be the base points minus penalties
                points_added = max(base_points - question_penalty, 10)  # Minimum 10 points for correct guess
                self.score += points_added  # Add points to the score
                self.total_points += points_added  # Add points to total points instead of setting
            else:
                # Deduct points for wrong guesses
                points_added = -10  # Deduct 10 points per wrong guess
                self.score += points_added
                self.total_points += points_added
        
        self.game_over = is_correct  # Only set game_over if guess is correct
        if is_correct:
            self.end_time = time.time()
            # Record game statistics when game is won
            self.stats_manager.record_game(self.get_game_summary())
        
        # Update message to show points change for wrong guesses
        if is_correct:
            message = f"Correct! You won! Final score: {self.score}"
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
            return "Game is already over!", 0
            
        if len(self.hints_given) >= 5:
            return "Maximum hints reached!", 0
            
        # Get semantic hint
        hint = self.word_selector.get_semantic_hint(
            self.selected_word,
            self.subject,
            self.hints_given
        )
        
        points_deducted = 0
        if self.mode == "Challenge":
            points_deducted = -10  # Deduct 10 points per hint in Challenge mode
            self.score += points_deducted
            self.total_points += points_deducted
            
        # Record the hint
        self.hints_given.append(hint)
        
        return hint, points_deducted if self.mode == "Challenge" else 0

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
            "guesses_made": self.guesses_made,
            "start_time": self.start_time,
            "end_time": end_time,
            "duration": duration,
            "time_taken": duration,  # Add time_taken field for compatibility
            "game_over": self.game_over,
            "nickname": self.nickname
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