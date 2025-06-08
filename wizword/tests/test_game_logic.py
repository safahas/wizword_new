import pytest
import os
from unittest.mock import Mock, patch
from backend.game_logic import GameLogic

@pytest.fixture
def mock_word_selector():
    selector = Mock()
    selector.select_word.return_value = "mouse"
    selector.answer_question.return_value = (True, "yes")
    selector.verify_guess.side_effect = lambda word, guess: word.lower() == guess.lower()
    return selector

@pytest.fixture
def game():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        with patch('backend.game_logic.WordSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector.select_word.return_value = "mouse"
            mock_selector.answer_question.return_value = (True, "yes")
            mock_selector.verify_guess.side_effect = lambda word, guess: word.lower() == guess.lower()
            mock_selector_class.return_value = mock_selector
            
            game = GameLogic(word_length=5, subject="Animals", mode="Challenge")
            game.word_selector = mock_selector
            return game

@pytest.mark.unit
def test_game_initialization(game):
    assert game.word_length == 5
    assert game.subject == "Animals"
    assert game.mode == "Challenge"
    assert game.score == 0
    assert not game.game_over
    assert len(game.questions_asked) == 0

@pytest.mark.unit
def test_ask_question_challenge_mode(game):
    # Correct answer - no points
    is_valid, answer, points = game.ask_question("Is it a mammal?")
    assert is_valid is True
    assert answer == "yes"
    assert points == 0
    assert game.score == 0
    
    # Mock wrong answer - add points
    game.word_selector.answer_question.return_value = (True, "no")
    is_valid, answer, points = game.ask_question("Does it fly?")
    assert is_valid is True
    assert answer == "no"
    assert points == 10
    assert game.score == 10

@pytest.mark.unit
def test_ask_question_fun_mode():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        with patch('backend.game_logic.WordSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector.select_word.return_value = "mouse"
            mock_selector.answer_question.return_value = (True, "no")
            mock_selector_class.return_value = mock_selector
            
            game = GameLogic(word_length=5, subject="Animals", mode="Fun")
            game.word_selector = mock_selector
            is_valid, answer, points = game.ask_question("Does it fly?")
            assert is_valid is True
            assert answer == "no"
            assert points == 0
            assert game.score == 0

@pytest.mark.unit
def test_make_guess(game):
    # Wrong guess
    success, message, points = game.make_guess("horse")
    assert not success
    assert "Wrong" in message
    assert points == 10
    assert game.score == 10
    assert game.game_over
    
    # Correct guess (new game)
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        with patch('backend.game_logic.WordSelector') as mock_selector_class:
            mock_selector = Mock()
            mock_selector.select_word.return_value = "mouse"
            mock_selector.answer_question.return_value = (True, "yes")
            mock_selector.verify_guess.side_effect = lambda word, guess: word.lower() == guess.lower()
            mock_selector_class.return_value = mock_selector
            
            game = GameLogic(word_length=5, subject="Animals", mode="Challenge")
            game.word_selector = mock_selector
            success, message, points = game.make_guess("mouse")
            assert success
            assert "Correct" in message
            assert points == 0
            assert game.score == 0
            assert game.game_over

@pytest.mark.unit
def test_get_game_summary(game):
    game.ask_question("Is it a mammal?")
    game.ask_question("Does it fly?")
    game.make_guess("horse")
    
    summary = game.get_game_summary()
    assert summary["word_length"] == 5
    assert summary["subject"] == "Animals"
    assert summary["mode"] == "Challenge"
    assert summary["score"] == game.score
    assert len(summary["questions_asked"]) == 2
    assert summary["game_over"] is True
    assert summary["word"] == "mouse"

@pytest.mark.unit
def test_invalid_questions(game):
    game.word_selector.answer_question.return_value = (False, "invalid")
    is_valid, answer, points = game.ask_question("How many letters?")
    assert not is_valid
    assert answer == "invalid"
    assert points == 0
    assert game.score == 0
    assert len(game.questions_asked) == 0

@pytest.mark.unit
def test_game_state_tracking(game):
    # Track questions
    game.ask_question("Is it a mammal?")
    assert len(game.questions_asked) == 1
    assert game.questions_asked[0]["question"] == "Is it a mammal?"
    assert game.questions_asked[0]["answer"] == "yes"
    
    # Track time
    assert game.start_time is not None
    summary = game.get_game_summary()
    assert "time_taken" in summary
    assert isinstance(summary["time_taken"], float)

@pytest.mark.integration
def test_share_card_integration(game):
    # Play a game
    game.ask_question("Is it a mammal?")
    game.ask_question("Does it fly?")
    game.make_guess("horse")
    
    # Get game summary
    summary = game.get_game_summary()
    
    # Verify summary has all required fields for share card
    required_fields = ["word", "subject", "score", "time_taken", "mode"]
    for field in required_fields:
        assert field in summary
        assert summary[field] is not None
    
    # Verify field types
    assert isinstance(summary["word"], str)
    assert isinstance(summary["subject"], str)
    assert isinstance(summary["score"], int)
    assert isinstance(summary["time_taken"], float)
    assert isinstance(summary["mode"], str) 