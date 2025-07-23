"""
Utilities for handling share URLs and QR codes for the Word Guess Contest game.
"""

import os
import qrcode
import json
import base64
import urllib.parse
from typing import Dict, Optional
from datetime import datetime, timezone
from PIL.Image import Image
import hashlib

class ShareUtils:
    def __init__(self):
        self.base_url = "https://word-guess-contest.streamlit.app"
        os.makedirs('game_data/qr_codes', exist_ok=True)
    
    def generate_share_text(self, game_summary: Dict) -> str:
        """Generate text for sharing game results."""
        text = [
            "�� Word Guess Contest"
        ]
        mode = game_summary.get("mode", "")
        if mode == "Beat":
            words_solved = game_summary.get("words_solved", 0)
            text.append(f"Words Solved: {words_solved}")
        else:
            text.append(f"Word: {game_summary['word'].upper()}")
        text.append(f"Category: {game_summary['subject']}")
        text.append(f"Score: {game_summary['score']} ({game_summary['mode']} mode)")
        text.append(f"Time: {self._format_duration(game_summary['time_taken'])}")
        
        # Add player stats if available
        if game_summary.get("player_stats"):
            stats = game_summary["player_stats"]
            text.extend([
                "",
                "📊 My Stats:",
                f"Total Games: {stats['total_games']}",
                f"Best Score: {int(stats['best_score'])}",
                f"Average Score: {round(stats['avg_score'], 1)}"
            ])
        
        # Add hashtags
        text.extend([
            "",
            "#WordGuessContest #WordGame"
        ])
        
        return "\n".join(text)

    def generate_share_url(self, game_summary: Dict) -> str:
        """Generate URL for sharing game results."""
        params = {
            "word": game_summary["word"],
            "category": game_summary["subject"],
            "score": game_summary["score"],
            "mode": game_summary["mode"],
            "time": game_summary["time_taken"]
        }
        
        # Add player stats if available
        if game_summary.get("player_stats"):
            stats = game_summary["player_stats"]
            params.update({
                "total_games": stats["total_games"],
                "best_score": int(stats["best_score"]),
                "avg_score": round(stats["avg_score"], 1)
            })
        
        # Encode parameters
        encoded_params = urllib.parse.urlencode(params)
        return f"{self.base_url}?{encoded_params}"

    def generate_qr_code(self, word: str, category: str, score: int, duration: float, mode: str) -> Optional[Image]:
        """Generate QR code for sharing game results.

        Args:
            word (str): The word that was guessed
            category (str): The category of the word
            score (int): The final score
            duration (float): Time taken to guess
            mode (str): Game mode

        Returns:
            Optional[PIL.Image.Image]: QR code image if successful, None if failed
        """
        try:
            # Create QR code data
            data = {
                "word": word,
                "category": category,
                "score": score,
                "duration": duration,
                "mode": mode
            }
            
            # Generate QR code
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4
            )
            qr.add_data(json.dumps(data))
            qr.make(fit=True)
            
            return qr.make_image(fill_color="black", back_color="white")
            
        except Exception as e:
            print(f"Failed to generate QR code: {e}")
            return None

    def _format_duration(self, seconds: float) -> str:
        """Format duration in seconds to readable time."""
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}m {seconds}s"

    def generate_share_id(self, game_summary: Dict) -> str:
        """
        Generate a unique share ID for a game session.
        
        Args:
            game_summary: Dictionary containing game summary data
            
        Returns:
            str: Unique share ID
        """
        # Create a unique string from game data
        unique_str = (
            f"{game_summary['word']}"
            f"{game_summary['category']}"
            f"{game_summary['score']}"
            f"{game_summary['duration']}"
            f"{datetime.now(timezone.utc).isoformat()}"
        )
        
        # Generate hash and encode in base64
        hash_obj = hashlib.sha256(unique_str.encode())
        share_id = base64.urlsafe_b64encode(hash_obj.digest()[:9]).decode().rstrip('=')
        
        return share_id
    
    def create_share_url(self, game_summary: Dict, include_params: bool = True) -> str:
        """
        Create a shareable URL for the game results.
        
        Args:
            game_summary: Dictionary containing game summary data
            include_params: Whether to include game parameters in URL (default: True)
            
        Returns:
            str: Shareable URL
        """
        share_id = self.generate_share_id(game_summary)
        base_share_url = f"{self.base_url}/share/{share_id}"
        
        if not include_params:
            return base_share_url
        
        # Add game parameters
        params = {
            'w': game_summary['word'],
            'c': game_summary['category'],
            's': str(game_summary['score']),
            'm': game_summary['mode'],
            't': str(int(game_summary['duration']))
        }
        
        if game_summary.get('nickname'):
            params['n'] = game_summary['nickname']
        
        return f"{base_share_url}?{urllib.parse.urlencode(params)}"
    
    def get_social_share_text(self, game_summary: Dict) -> str:
        """
        Generate text for social media sharing.
        
        Args:
            game_summary: Dictionary containing game summary data
            
        Returns:
            str: Formatted share text
        """
        share_url = self.create_share_url(game_summary, include_params=False)
        
        text = (
            f"I just guessed '{game_summary['word'].upper()}' "
            f"with a score of {game_summary['score']} "
            f"in Word Guess Contest AI! 🎯\n\n"
            f"Category: {game_summary['category']}\n"
            f"Mode: {game_summary['mode']}\n"
            f"Can you beat my score?\n\n"
            f"{share_url}"
        )
        
        return text 