import pytest
import os
import json
import boto3
from unittest.mock import Mock, patch
from moto import mock_aws
from backend.session_manager import SessionManager
from cryptography.fernet import Fernet

@pytest.fixture
def sample_game_data():
    return {
        "session_id": "test_123",
        "nickname": "tester",
        "timestamp": "2024-03-20T10:00:00",
        "word_length": 5,
        "subject": "Animals",
        "mode": "Challenge",
        "score": 20,
        "questions_asked": [
            {"question": "Is it a mammal?", "answer": "yes", "points_added": 0},
            {"question": "Does it fly?", "answer": "no", "points_added": 10}
        ],
        "time_taken": 45.2,
        "game_over": True,
        "word": "mouse"
    }

@pytest.fixture
def local_session_manager():
    with patch.dict('os.environ', {
        'USE_CLOUD_STORAGE': 'false',
        'WORD_ENCRYPTION_KEY': Fernet.generate_key().decode()
    }):
        manager = SessionManager()
        # Ensure test directory exists
        os.makedirs('game_data', exist_ok=True)
        yield manager
        # Cleanup test files
        for f in os.listdir('game_data'):
            if f.startswith('test_'):
                os.remove(os.path.join('game_data', f))

@pytest.fixture
def aws_credentials():
    """Mocked AWS Credentials for moto."""
    os.environ["AWS_ACCESS_KEY_ID"] = "testing"
    os.environ["AWS_SECRET_ACCESS_KEY"] = "testing"
    os.environ["AWS_SECURITY_TOKEN"] = "testing"
    os.environ["AWS_SESSION_TOKEN"] = "testing"
    os.environ["AWS_DEFAULT_REGION"] = "us-east-1"

@pytest.fixture
def dynamodb_table(aws_credentials):
    with mock_aws():
        dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
        table = dynamodb.create_table(
            TableName='word_guess_games',
            KeySchema=[{'AttributeName': 'session_id', 'KeyType': 'HASH'}],
            AttributeDefinitions=[{'AttributeName': 'session_id', 'AttributeType': 'S'}],
            ProvisionedThroughput={'ReadCapacityUnits': 5, 'WriteCapacityUnits': 5}
        )
        yield table

@pytest.mark.local
def test_local_save_load(local_session_manager, sample_game_data):
    # Save game
    local_session_manager.save_game(sample_game_data)
    
    # Verify file exists
    filename = f"game_data/test_123.json"
    assert os.path.exists(filename)
    
    # Load and verify data
    loaded_data = local_session_manager.load_game("test_123")
    assert loaded_data["session_id"] == sample_game_data["session_id"]
    assert loaded_data["word"] == sample_game_data["word"]
    assert loaded_data["score"] == sample_game_data["score"]

@pytest.mark.local
def test_local_encryption(local_session_manager, sample_game_data):
    # Save game with encryption
    unfinished_game = sample_game_data.copy()
    unfinished_game["game_over"] = False
    local_session_manager.save_game(unfinished_game)
    
    # Read raw file content
    with open(f"game_data/test_123.json", 'r') as f:
        raw_data = json.load(f)
    
    # Verify word is encrypted
    assert raw_data["word"] != unfinished_game["word"]
    
    # Load through manager and verify decryption
    loaded_data = local_session_manager.load_game("test_123")
    assert loaded_data["word"] == raw_data["word"]  # Still encrypted since game not over

@pytest.mark.cloud
def test_cloud_save_load(dynamodb_table, sample_game_data):
    with patch.dict('os.environ', {
        'USE_CLOUD_STORAGE': 'true',
        'AWS_ACCESS_KEY_ID': 'test',
        'AWS_SECRET_ACCESS_KEY': 'test',
        'AWS_REGION': 'us-east-1',
        'WORD_ENCRYPTION_KEY': Fernet.generate_key().decode()
    }):
        manager = SessionManager(use_cloud=True)
        
        # Save game
        manager.save_game(sample_game_data)
        
        # Load and verify
        loaded_data = manager.load_game("test_123")
        assert loaded_data["session_id"] == sample_game_data["session_id"]
        assert loaded_data["word"] == sample_game_data["word"]
        assert loaded_data["score"] == sample_game_data["score"]

@pytest.mark.cloud
def test_cloud_encryption(dynamodb_table, sample_game_data):
    with patch.dict('os.environ', {
        'USE_CLOUD_STORAGE': 'true',
        'AWS_ACCESS_KEY_ID': 'test',
        'AWS_SECRET_ACCESS_KEY': 'test',
        'AWS_REGION': 'us-east-1',
        'WORD_ENCRYPTION_KEY': Fernet.generate_key().decode()
    }):
        manager = SessionManager(use_cloud=True)
        
        # Save game with encryption
        unfinished_game = sample_game_data.copy()
        unfinished_game["game_over"] = False
        manager.save_game(unfinished_game)
        
        # Get raw item from DynamoDB
        raw_item = dynamodb_table.get_item(
            Key={'session_id': 'test_123'}
        )['Item']
        
        # Verify word is encrypted
        assert raw_item["word"] != unfinished_game["word"]
        
        # Load through manager and verify decryption
        loaded_data = manager.load_game("test_123")
        assert loaded_data["word"] == raw_item["word"]  # Still encrypted since game not over

@pytest.mark.integration
def test_fallback_to_local(sample_game_data):
    with patch.dict('os.environ', {
        'USE_CLOUD_STORAGE': 'true',
        'AWS_ACCESS_KEY_ID': 'invalid',
        'AWS_SECRET_ACCESS_KEY': 'invalid',
        'WORD_ENCRYPTION_KEY': Fernet.generate_key().decode()
    }):
        manager = SessionManager(use_cloud=True)
        
        # Save should fall back to local
        manager.save_game(sample_game_data)
        
        # Verify saved locally
        assert os.path.exists(f"game_data/test_123.json")
        
        # Load should work
        loaded_data = manager.load_game("test_123")
        assert loaded_data["session_id"] == sample_game_data["session_id"]

@pytest.mark.unit
def test_leaderboard(local_session_manager):
    games = [
        {"session_id": "test_1", "score": 10, "mode": "Challenge", "game_over": True, "word": "mouse"},
        {"session_id": "test_2", "score": 20, "mode": "Challenge", "game_over": True, "word": "horse"},
        {"session_id": "test_3", "score": 5, "mode": "Challenge", "game_over": True, "word": "koala"},
    ]
    
    for game in games:
        local_session_manager.save_game(game)
    
    leaderboard = local_session_manager.get_leaderboard()
    assert len(leaderboard) == 3
    assert leaderboard[0]["score"] == 5  # Best score in Challenge mode is lowest
    assert leaderboard[-1]["score"] == 20 