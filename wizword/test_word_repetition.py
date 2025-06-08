import logging
from backend.word_selector import WordSelector
from backend.fallback_words import FALLBACK_WORDS
from collections import Counter

def test_word_repetition():
    # Configure logging
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Initialize WordSelector
    selector = WordSelector()
    
    # First, analyze the available word pool
    word_length = 5  # We're testing 5-letter words
    subjects = ["general", "animals", "food", "places", "science"]
    
    logger.info("\nAnalyzing available word pool:")
    total_words = 0
    for subject in subjects:
        words = FALLBACK_WORDS[subject][word_length]
        total_words += len(words)
        logger.info(f"Subject '{subject}' has {len(words)} {word_length}-letter words: {', '.join(words)}")
    
    logger.info(f"\nTotal unique {word_length}-letter words across all categories: {total_words}")
    
    # Track selected words
    selected_words = []
    
    # Select 501 words
    total_selections = 501
    logger.info(f"\nStarting word selection test for {total_selections} words...")
    
    for i in range(total_selections):
        # Cycle through different subjects
        subject = subjects[i % len(subjects)]
        
        word = selector.select_word(word_length=word_length, subject=subject)
        selected_words.append(word)
        
        if (i + 1) % 50 == 0:
            logger.info(f"Selected {i + 1} words...")
    
    # Analyze results
    word_counts = Counter(selected_words)
    repeated_words = {word: count for word, count in word_counts.items() if count > 1}
    
    logger.info("\nTest Results:")
    logger.info(f"Total words selected: {len(selected_words)}")
    logger.info(f"Unique words: {len(word_counts)}")
    logger.info(f"Number of repeated words: {len(repeated_words)}")
    
    if repeated_words:
        logger.info("\nRepeated words and their counts:")
        for word, count in sorted(repeated_words.items(), key=lambda x: (-x[1], x[0])):
            logger.info(f"'{word}': {count} times")
    else:
        logger.info("\nNo words were repeated!")
    
    # Save results to a file
    with open("word_selection_results.txt", "w") as f:
        f.write("Word Selection Test Results\n")
        f.write("=========================\n\n")
        f.write(f"Total words selected: {len(selected_words)}\n")
        f.write(f"Unique words: {len(word_counts)}\n")
        f.write(f"Number of repeated words: {len(repeated_words)}\n\n")
        
        if repeated_words:
            f.write("Repeated words and their counts:\n")
            for word, count in sorted(repeated_words.items(), key=lambda x: (-x[1], x[0])):
                f.write(f"'{word}': {count} times\n")
        else:
            f.write("No words were repeated!\n")
        
        f.write("\nAll selected words in order:\n")
        for i, word in enumerate(selected_words, 1):
            f.write(f"{i}. {word}\n")

if __name__ == "__main__":
    test_word_repetition()