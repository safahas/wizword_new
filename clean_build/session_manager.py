import json
import boto3
import os
import base64
from typing import Dict, List, Optional
from datetime import datetime
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class SessionManager:
    def __init__(self, use_cloud: bool = False):
        self.use_cloud = use_cloud
        self.local_storage_path = Path("game_data")
        self.local_storage_path.mkdir(exist_ok=True)
        
        # Initialize encryption
        self._init_encryption()
        
        if use_cloud:
            self.dynamodb = boto3.resource('dynamodb')
            self.table = self.dynamodb.Table('word_guess_games')

    def _init_encryption(self):
        """Initialize encryption key using environment variable or generate a new one."""
        key = os.getenv('WORD_ENCRYPTION_KEY')
        if not key:
            # Generate a new key if not provided
            salt = b'word_guess_game'  # Fixed salt for development
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
            )
            key = base64.urlsafe_b64encode(kdf.derive(b'default_key'))
            os.environ['WORD_ENCRYPTION_KEY'] = key.decode()
        else:
            key = key.encode()
            
        self.fernet = Fernet(key)

    def _encrypt_word(self, word: str) -> str:
        """Encrypt the hidden word."""
        if not word:
            return ""
        return self.fernet.encrypt(word.encode()).decode()

    def _decrypt_word(self, encrypted_word: str) -> str:
        """Decrypt the hidden word."""
        if not encrypted_word:
            return ""
        try:
            return self.fernet.decrypt(encrypted_word.encode()).decode()
        except Exception as e:
            print(f"Failed to decrypt word: {e}")
            return ""

    def save_game(self, game_data: Dict) -> str:
        """
        Save a game session either locally or to DynamoDB.
        Returns the session ID.
        """
        session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        if game_data.get("nickname"):
            session_id = f"{game_data['nickname']}_{session_id}"
            
        game_data["session_id"] = session_id
        game_data["timestamp"] = datetime.now().isoformat()
        
        # Encrypt the word if present and game is not over
        if "word" in game_data and not game_data.get("game_over", False):
            game_data["word"] = self._encrypt_word(game_data["word"])
        
        if self.use_cloud:
            try:
                self.table.put_item(Item=game_data)
            except Exception as e:
                print(f"Failed to save to DynamoDB: {e}")
                self._save_local(session_id, game_data)
        else:
            self._save_local(session_id, game_data)
            
        return session_id

    def _save_local(self, session_id: str, game_data: Dict) -> None:
        """Save game data to a local JSON file."""
        file_path = self.local_storage_path / f"{session_id}.json"
        with open(file_path, 'w') as f:
            json.dump(game_data, f, indent=2)

    def load_game(self, session_id: str) -> Optional[Dict]:
        """Load a game session by ID."""
        game_data = None
        
        if self.use_cloud:
            try:
                response = self.table.get_item(Key={'session_id': session_id})
                game_data = response.get('Item')
            except Exception as e:
                print(f"Failed to load from DynamoDB: {e}")
                game_data = self._load_local(session_id)
        else:
            game_data = self._load_local(session_id)
            
        if game_data:
            # Decrypt the word if game is over
            if game_data.get("game_over", False) and "word" in game_data:
                game_data["word"] = self._decrypt_word(game_data["word"])
                
        return game_data

    def _load_local(self, session_id: str) -> Optional[Dict]:
        """Load game data from a local JSON file."""
        file_path = self.local_storage_path / f"{session_id}.json"
        if file_path.exists():
            with open(file_path) as f:
                return json.load(f)
        return None

    def get_leaderboard(self, limit: int = 10) -> List[Dict]:
        """Get the top scores from completed games."""
        if self.use_cloud:
            try:
                response = self.table.scan()
                games = response.get('Items', [])
            except Exception as e:
                print(f"Failed to get leaderboard from DynamoDB: {e}")
                games = self._get_local_games()
        else:
            games = self._get_local_games()
            
        # Filter completed games and sort by score (lower is better)
        completed_games = []
        for game in games:
            if game.get('game_over', False):
                # Decrypt word for completed games
                if "word" in game:
                    game["word"] = self._decrypt_word(game["word"])
                completed_games.append(game)
        
        sorted_games = sorted(
            completed_games,
            key=lambda x: (x.get('score', 0), x.get('time_taken', float('inf')))
        )
        
        return sorted_games[:limit]

    def _get_local_games(self) -> List[Dict]:
        """Get all locally stored games."""
        games = []
        for file_path in self.local_storage_path.glob("*.json"):
            try:
                with open(file_path) as f:
                    games.append(json.load(f))
            except Exception as e:
                print(f"Failed to load {file_path}: {e}")
        return games

    def get_user_history(self, nickname: str) -> List[Dict]:
        """Get game history for a specific user."""
        if self.use_cloud:
            try:
                response = self.table.scan(
                    FilterExpression='nickname = :nick',
                    ExpressionAttributeValues={':nick': nickname}
                )
                games = response.get('Items', [])
            except Exception as e:
                print(f"Failed to get user history from DynamoDB: {e}")
                games = self._get_local_games()
        else:
            games = self._get_local_games()
            
        # Filter games by nickname and sort by timestamp
        user_games = []
        for game in games:
            if game.get('nickname', '').lower() == nickname.lower():
                # Decrypt word only for completed games
                if game.get('game_over', False) and "word" in game:
                    game["word"] = self._decrypt_word(game["word"])
                user_games.append(game)
        
        return sorted(
            user_games,
            key=lambda x: x.get('timestamp', ''),
            reverse=True
        ) 