import pytest
from unittest.mock import Mock, patch
import json
from backend.word_selector import WordSelector

@pytest.fixture
def word_selector():
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        return WordSelector()

def test_validate_hint():
    """Test the hint validation rules."""
    selector = WordSelector()
    word = "house"
    previous_hints = ["This is used for shelter"]
    
    # Test cases that should fail validation
    invalid_hints = [
        "A house is a building",  # Contains the word as a whole word
        "It starts with h",  # Letter-based hint
        "This has 5 letters",  # Letter count hint
        "This contains the letter o",  # Letter content hint
        "This is used for shelter",  # Duplicate hint
        "This is a very long hint that goes on and on and contains way too many words to be considered concise and would definitely exceed our twenty word limit for hints in the game"  # Too long
    ]
    
    for hint in invalid_hints:
        assert not selector._validate_hint(hint, word, previous_hints), f"Should reject: {hint}"
    
    # Test cases that should pass validation
    valid_hints = [
        "This provides shelter",
        "People live inside",
        "A building for living",
        "A place for families",
        "This structure provides shelter",  # Contains 'house' as part of another word
        "The household uses this space"  # Contains 'house' as part of another word
    ]
    
    for hint in valid_hints:
        assert selector._validate_hint(hint, word, previous_hints), f"Should accept: {hint}"

@pytest.mark.api
def test_api_hint_generation():
    """Test API-based hint generation."""
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        selector = WordSelector()
        
        # Mock API response
        mock_response = {
            "choices": [{
                "message": {
                    "content": "This provides shelter and protection"
                }
            }]
        }
        
        with patch.object(selector, '_make_api_request', return_value=mock_response):
            hint = selector.get_semantic_hint("house", "Places", [])
            assert hint == "This provides shelter and protection"
            
            # Test with previous hints
            previous_hints = ["This provides shelter and protection"]
            with patch.object(selector, '_make_api_request', return_value={
                "choices": [{
                    "message": {
                        "content": "Families gather in this structure"
                    }
                }]
            }):
                hint = selector.get_semantic_hint("house", "Places", previous_hints)
                assert hint == "Families gather in this structure"

@pytest.mark.api
def test_api_hint_validation_failure():
    """Test fallback when API generates invalid hints."""
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        selector = WordSelector()
        
        # Mock API returning invalid hints
        invalid_responses = [
            {"choices": [{"message": {"content": "It starts with h"}}]},  # Letter-based hint
            {"choices": [{"message": {"content": "A house is big"}}]},  # Contains the word
            {"choices": [{"message": {"content": "It has 5 letters"}}]}  # Letter count
        ]
        
        for response in invalid_responses:
            with patch.object(selector, '_make_api_request', return_value=response):
                hint = selector.get_semantic_hint("house", "Places", [])
                # Should fall back to category-specific hints
                assert hint in selector._get_fallback_semantic_hint("house", "places")

def test_fallback_hints():
    """Test fallback hint generation."""
    selector = WordSelector()
    
    # Test each category
    categories = {
        "animals": ["creature", "animal", "species"],
        "food": ["ingredient", "taste", "preparation"],
        "places": ["location", "space", "place"],
        "science": ["research", "process", "experiment"],
        "tech": ["computing", "digital", "technology"]
    }
    
    for category, keywords in categories.items():
        hint = selector._get_fallback_semantic_hint("test", category, [])
        # Hint should contain at least one of the category's keywords
        assert any(keyword.lower() in hint.lower() for keyword in keywords), f"Invalid hint for {category}: {hint}"

def test_progressive_hints():
    """Test that multiple hints are progressive and unique."""
    selector = WordSelector()
    word = "house"
    subject = "places"
    hints = []
    
    # Get 5 hints
    for _ in range(5):
        hint = selector.get_semantic_hint(word, subject, hints)
        assert hint not in hints, "Hint should be unique"
        hints.append(hint)
    
    # Verify maximum hints
    hint = selector.get_semantic_hint(word, subject, hints)
    assert hint == "Maximum hints reached!", "Should stop after 5 hints"

@pytest.mark.api
def test_api_error_handling():
    """Test API error handling and fallback."""
    with patch.dict('os.environ', {'OPENROUTER_API_KEY': 'test_key'}):
        selector = WordSelector()
        
        # Test API failure
        with patch.object(selector, '_make_api_request', side_effect=Exception("API Error")):
            hint = selector.get_semantic_hint("house", "Places", [])
            # Should fall back to category-specific hints
            assert hint in selector._get_fallback_semantic_hint("house", "places") 