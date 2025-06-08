import json
import os

data_dir = os.path.join(os.path.dirname(__file__), 'data')
words_json_path = os.path.join(data_dir, 'words.json')
hints_json_path = os.path.join(data_dir, 'hints.json')

# Load words.json
def load_words():
    with open(words_json_path, 'r', encoding='utf-8') as f:
        words_data = json.load(f)
    fourth_grade_words = set()
    if '4th_grade' in words_data:
        for length, words in words_data['4th_grade'].items():
            fourth_grade_words.update(word.lower() for word in words)
    return fourth_grade_words

# Load hints.json
def load_hints():
    with open(hints_json_path, 'r', encoding='utf-8') as f:
        hints_data = json.load(f)
    # Check both main categories and top-level 4th_grade
    hints_words = set()
    # 1. Main categories section
    if 'categories' in hints_data and '4th_grade' in hints_data['categories']:
        for word in hints_data['categories']['4th_grade']:
            hints_words.add(word.lower())
    # 2. Top-level 4th_grade section
    if '4th_grade' in hints_data:
        for word in hints_data['4th_grade']:
            hints_words.add(word.lower())
    return hints_words

def main():
    words_set = load_words()
    hints_set = load_hints()
    print(f"Number of words in 4th_grade (words.json): {len(words_set)}")
    print(f"Number of words in 4th_grade (hints.json): {len(hints_set)}")
    missing = words_set - hints_set
    if missing:
        print("Words in words.json but missing in hints.json:")
        for word in sorted(missing):
            print(f"  - {word}")
    else:
        print("All words in words.json/4th_grade have hints in hints.json.")

if __name__ == "__main__":
    main() 