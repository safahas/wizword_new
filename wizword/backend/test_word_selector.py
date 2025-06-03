# backend/test_word_selector.py
from word_selector import WordSelector
import os
import logging

# Configure logging with a more visible format
logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)

def test_word_selector():
    print("Starting WordSelector tests...\n")
    
    # Initialize WordSelector
    selector = WordSelector()
    
    # Check if we're in API or fallback mode
    api_mode = selector.validate_api_key()
    print(f"Running in {'API' if api_mode else 'Fallback'} mode\n")

    # Test 1: Word Selection
    print("=== Test 1: Word Selection ===")
    categories = ["animals", "food", "science", "general"]
    lengths = [3, 4, 5]
    
    for category in categories:
        for length in lengths:
            word = selector.select_word(length, category)
            print(f"Selected {length}-letter {category} word: {word}")
        print()

    # Test 2: Hint Generation
    print("\n=== Test 2: Hint Generation ===")
    test_words = [
        ("tiger", "animals"),
        ("pasta", "food"),
        ("laser", "science"),
        ("peace", "general")
    ]
    
    for word, category in test_words:
        print(f"\nTesting hints for '{word}' ({category}):")
        
        # Test regular hint generation (will use API if available)
        try:
            hint = selector.get_semantic_hint(word, category)
            print(f"API/Smart hint: {hint}")
        except Exception as e:
            print(f"API hint failed: {e}")
        
        # Test fallback hint generation
        fallback_hint = selector._get_fallback_semantic_hint(word, category)
        print(f"Fallback hint: {fallback_hint}")

    # Test 3: Question Answering
    print("\n=== Test 3: Question Answering ===")
    test_questions = [
        ("cat", "Does it contain the letter 'a'?"),
        ("dog", "Is it a 3-letter word?"),
        ("fish", "Does it start with 'f'?"),
        ("bird", "Does it end with 'd'?")
    ]
    
    for word, question in test_questions:
        print(f"\nTesting word: '{word}'")
        print(f"Question: {question}")
        
        # Test regular answer (will use API if available)
        try:
            api_answer = selector.answer_question(word, question)
            print(f"API/Smart answer: {api_answer}")
        except Exception as e:
            print(f"API answer failed: {e}")
        
        # Test fallback answer
        fallback_answer = selector._answer_question_fallback(word, question)
        print(f"Fallback answer: {fallback_answer}")

if __name__ == "__main__":
    test_word_selector()
