import pytest
import json
from unittest.mock import patch, Mock
from backend.word_selector import WordSelector
from backend.fallback_words import FALLBACK_WORDS

@pytest.fixture
def word_selector():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        return WordSelector()

@pytest.fixture
def mock_api_response():
    return {
        "choices": [{
            "message": {
                "content": '{"selected_word": "mouse"}'
            }
        }]
    }

@pytest.mark.unit
def test_word_selector_initialization():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        selector = WordSelector()
        assert selector.api_key == 'test_key'
        assert selector.model == 'google/gemini-pro'

@pytest.mark.unit
def test_build_prompt():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        selector = WordSelector()
        prompt = selector._build_prompt(5, "Animals")
        assert "5-letter" in prompt
        assert "Animals" in prompt
        assert "JSON format" in prompt

@pytest.mark.api
def test_select_word_api_success(word_selector, mock_api_response):
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_api_response
        mock_post.return_value.raise_for_status = Mock()
        
        word = word_selector.select_word(5, "Animals")
        assert word == "mouse"
        mock_post.assert_called_once()

@pytest.mark.api
def test_select_word_api_failure_fallback(word_selector):
    with patch('requests.post') as mock_post:
        mock_post.side_effect = Exception("API Error")
        
        word = word_selector.select_word(5, "Animals")
        assert word in FALLBACK_WORDS["Animals"][5]
        assert len(word) == 5

@pytest.mark.api
def test_answer_question(word_selector):
    test_word = "mouse"
    test_question = "Is it a mammal?"
    mock_response = {
        "choices": [{
            "message": {
                "content": "yes"
            }
        }]
    }
    
    with patch('requests.post') as mock_post:
        mock_post.return_value.json.return_value = mock_response
        mock_post.return_value.raise_for_status = Mock()
        
        is_valid, answer = word_selector.answer_question(test_word, test_question)
        assert is_valid is True
        assert answer == "yes"

@pytest.mark.unit
def test_verify_guess():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        selector = WordSelector()
        assert selector.verify_guess("mouse", "mouse") is True
        assert selector.verify_guess("Mouse", "mouse") is True
        assert selector.verify_guess("mouse", "house") is False

@pytest.mark.api
def test_api_retry_logic(word_selector, mock_api_response):
    with patch('requests.post') as mock_post:
        # First two calls fail, third succeeds
        mock_post.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            Mock(
                json=lambda: mock_api_response,
                raise_for_status=Mock()
            )
        ]
        
        word = word_selector.select_word(5, "Animals")
        assert word == "mouse"
        assert mock_post.call_count == 3 