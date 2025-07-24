from typing import Dict, List, Optional
import json
import time
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime, timedelta

class GameStats:
    def __init__(self, stats_file: str = "game_data/stats.json", nickname: str = None):
        self.stats_file = Path(stats_file)
        self.stats_file.parent.mkdir(parents=True, exist_ok=True)
        self.nickname = nickname
        self._load_stats()

    def _load_stats(self) -> None:
        """Load statistics from file or initialize if not exists."""
        if self.stats_file.exists():
            with open(self.stats_file, 'r') as f:
                self.stats = json.load(f)
        else:
            self.stats = {}
            self._save_stats()
        # Ensure current user has a stats entry
        if self.nickname and self.nickname not in self.stats:
            self.stats[self.nickname] = self._empty_user_stats()

    def _save_stats(self) -> None:
        """Save statistics to file."""
        with open(self.stats_file, 'w') as f:
            json.dump(self.stats, f, indent=2)

    def _empty_user_stats(self):
        return {
            "games": [],
            "categories": {},
            "word_lengths": {},
            "daily_stats": {},
            "leaderboard": []
        }

    def record_game(self, game_summary: Dict) -> None:
        """Record a completed game's statistics for the current user only."""
        if not self.nickname:
            raise ValueError("Nickname must be set for per-user statistics.")
        timestamp = datetime.now().isoformat()
        duration = game_summary.get("duration") or game_summary.get("time_taken", 0)
        word = game_summary.get("word") or game_summary.get("selected_word", "")
        game_record = {
            "timestamp": timestamp,
            "word_length": game_summary["word_length"],
            "subject": game_summary["subject"],
            "mode": game_summary["mode"],
            "nickname": self.nickname,
            "score": game_summary["score"],
            "total_points": game_summary["total_points"],
            "questions_count": len(game_summary["questions_asked"]),
            "guesses_made": game_summary["guesses_made"],
            "duration": duration,
            "time_taken": duration,
            "word": word,
            "selected_word": word
        }
        # Ensure user stats exist
        if self.nickname not in self.stats:
            self.stats[self.nickname] = self._empty_user_stats()
        user_stats = self.stats[self.nickname]
        user_stats["games"].append(game_record)
        # Update category stats
        if game_summary["subject"] not in user_stats["categories"]:
            user_stats["categories"][game_summary["subject"]] = {
                "games_played": 0,
                "avg_score": 0,
                "best_score": float('-inf'),
                "worst_score": float('inf'),
                "total_time": 0
            }
        cat_stats = user_stats["categories"][game_summary["subject"]]
        cat_stats["games_played"] += 1
        cat_stats["avg_score"] = (cat_stats["avg_score"] * (cat_stats["games_played"] - 1) + game_summary["score"]) / cat_stats["games_played"]
        cat_stats["best_score"] = max(cat_stats["best_score"], game_summary["score"])
        cat_stats["worst_score"] = min(cat_stats["worst_score"], game_summary["score"])
        cat_stats["total_time"] += duration
        # Update word length stats
        length_key = str(game_summary["word_length"])
        if length_key not in user_stats["word_lengths"]:
            user_stats["word_lengths"][length_key] = {
                "games_played": 0,
                "avg_time": 0,
                "best_time": float('inf'),
                "worst_time": float('-inf')
            }
        len_stats = user_stats["word_lengths"][length_key]
        len_stats["games_played"] += 1
        len_stats["avg_time"] = (len_stats["avg_time"] * (len_stats["games_played"] - 1) + duration) / len_stats["games_played"]
        len_stats["best_time"] = min(len_stats["best_time"], duration)
        len_stats["worst_time"] = max(len_stats["worst_time"], duration)
        # Update daily stats
        date_key = datetime.now().strftime("%Y-%m-%d")
        if date_key not in user_stats["daily_stats"]:
            user_stats["daily_stats"][date_key] = {
                "games_played": 0,
                "total_score": 0,
                "avg_time": 0
            }
        daily_stats = user_stats["daily_stats"][date_key]
        daily_stats["games_played"] += 1
        daily_stats["total_score"] += game_summary["score"]
        daily_stats["avg_time"] = (daily_stats["avg_time"] * (daily_stats["games_played"] - 1) + duration) / daily_stats["games_played"]
        # Update leaderboard for this user only
        self._update_leaderboard(game_record)
        self._save_stats()

    def _update_leaderboard(self, game_record: Dict) -> None:
        user_stats = self.stats[self.nickname]
        user_stats["leaderboard"].append({
            "nickname": self.nickname,
            "score": game_record["score"],
            "mode": game_record["mode"],
            "subject": game_record["subject"],
            "timestamp": game_record["timestamp"]
        })
        user_stats["leaderboard"].sort(key=lambda x: x["score"], reverse=True)
        user_stats["leaderboard"] = user_stats["leaderboard"][:100]

    def get_player_stats(self) -> Dict:
        user_stats = self.stats.get(self.nickname, self._empty_user_stats())
        player_games = user_stats["games"]
        if not player_games:
            return {}
        return {
            "total_games": len(player_games),
            "avg_score": sum(g["score"] for g in player_games) / len(player_games),
            "best_score": max(g["score"] for g in player_games),
            "favorite_category": max(
                set(g["subject"] for g in player_games),
                key=lambda x: len([g for g in player_games if g["subject"] == x])
            ),
            "total_time": sum(g["time_taken"] for g in player_games),
            "recent_games": sorted(player_games, key=lambda x: x["timestamp"], reverse=True)[:5]
        }

    def generate_performance_graphs(self, save_dir: str = "game_data/graphs") -> Dict[str, str]:
        user_stats = self.stats.get(self.nickname, self._empty_user_stats())
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        graphs = {}
        plt.style.use('seaborn-v0_8')
        # 1. Score distribution by category
        plt.figure(figsize=(10, 6))
        cat_scores = {cat: [] for cat in user_stats["categories"]}
        for game in user_stats["games"]:
            cat_scores[game["subject"]].append(game["score"])
        # Filter out empty lists and their labels
        filtered = [(label, scores) for label, scores in cat_scores.items() if scores]
        if not filtered:
            plt.close()
            graphs["score_distribution"] = None
        else:
            labels, data = zip(*filtered)
            plt.boxplot(data, labels=labels)
            plt.title("Score Distribution by Category")
            plt.ylabel("Score")
            plt.xticks(rotation=45)
            plt.tight_layout()
            score_dist_path = save_path / f"score_distribution_{self.nickname}.png"
            plt.savefig(score_dist_path)
            plt.close()
            graphs["score_distribution"] = str(score_dist_path)
        # 2. Time trend
        plt.figure(figsize=(10, 6))
        dates = [datetime.fromisoformat(g["timestamp"]).date() for g in user_stats["games"]]
        scores = [g["score"] for g in user_stats["games"]]
        df = pd.DataFrame({"date": dates, "score": scores})
        df = df.groupby("date").mean().reset_index()
        plt.plot(df["date"], df["score"], marker='o')
        plt.title("Average Score Trend")
        plt.ylabel("Score")
        plt.xlabel("Date")
        plt.xticks(rotation=45)
        plt.tight_layout()
        trend_path = save_path / f"score_trend_{self.nickname}.png"
        plt.savefig(trend_path)
        plt.close()
        graphs["score_trend"] = str(trend_path)
        return graphs

    def get_leaderboard(self, mode: Optional[str] = None, category: Optional[str] = None) -> List[Dict]:
        user_stats = self.stats.get(self.nickname, self._empty_user_stats())
        filtered = user_stats["leaderboard"]
        if mode:
            filtered = [entry for entry in filtered if entry["mode"] == mode]
        if category:
            filtered = [entry for entry in filtered if entry["subject"] == category]
        return filtered

    def get_daily_challenge_stats(self) -> Dict:
        """Get statistics for daily challenges."""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        user_stats = self.stats.get(self.nickname, self._empty_user_stats())
        if "daily_stats" not in user_stats:
            user_stats["daily_stats"] = {}
        return {
            "today": user_stats["daily_stats"].get(today, {
                "games_played": 0,
                "total_score": 0,
                "avg_time": 0
            }),
            "yesterday": user_stats["daily_stats"].get(yesterday, {
                "games_played": 0,
                "total_score": 0,
                "avg_time": 0
            })
        }

    def get_highest_score_game_this_month(self) -> Optional[Dict]:
        """Return the game record with the highest score for the current user in the current month."""
        user_stats = self.stats.get(self.nickname, self._empty_user_stats())
        games = user_stats["games"]
        if not games:
            return None
        now = datetime.now()
        current_month = now.strftime("%Y-%m")
        games_this_month = [g for g in games if g["timestamp"].startswith(current_month)]
        if not games_this_month:
            return None
        return max(games_this_month, key=lambda g: g["score"]) 