import os
import logging
from backend.word_selector import WordSelector

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_word_selection():
    """Test word selection with Mistral model"""
    selector = WordSelector()
    
    # Test different categories and word lengths
    test_cases = [
        (5, "Animals"),
        (6, "Food"),
        (4, "Tech"),
        (5, "Science")
    ]
    
    print("\nTesting word selection with Mistral model:")
    print("=" * 50)
    
    for word_length, category in test_cases:
        try:
            print(f"\nTesting {category} category with {word_length}-letter words:")
            word = selector.select_word(word_length, category)
            print(f"Selected word: {word}")
            
            # Get a semantic hint
            hint = selector.get_semantic_hint(word, category)
            print(f"Semantic hint: {hint}")
            
            # Test a question
            question = "Is it related to technology?"
            valid, answer = selector.answer_question(word, question)
            print(f"Question: {question}")
            print(f"Answer: {answer}")
            
        except Exception as e:
            print(f"Error testing {category}: {e}")

if __name__ == "__main__":
    test_word_selection() 