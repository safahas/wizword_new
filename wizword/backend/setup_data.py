# backend/setup_data.py
import os
import json
from typing import Dict, List

# Create data directory if it doesn't exist
data_dir = os.path.join(os.path.dirname(__file__), 'data')
os.makedirs(data_dir, exist_ok=True)

words_json_path = os.path.join(data_dir, 'words.json')
hints_json_path = os.path.join(data_dir, 'hints.json')

# Load words.json
with open(words_json_path, 'r', encoding='utf-8') as f:
    words_data = json.load(f)

# Load existing hints.json if it exists, otherwise start fresh
if os.path.exists(hints_json_path):
    with open(hints_json_path, 'r', encoding='utf-8') as f:
        hints_data = json.load(f)
else:
    hints_data = {"templates": {}, "categories": {}}

# Define specific word templates from word_selector.py
specific_word_templates = {
    "general": {
        "table": [
            "This furniture piece typically measures 30 inches in height and supports 250 pounds of weight",
            "Modern versions cost between $200-$800 and last approximately 15 years",
            "Found in 98% of dining rooms and used exactly 3 times daily for meals",
            "Occupies approximately 15-20 square feet of floor space in average homes",
            "Production requires precisely 2.5 hours of assembly time in factories",
            "Available in over 1000 different styles and materials",
            "Average weight ranges from 25 to 75 pounds",
            "Standard dimensions include 30-inch height and 36-inch width",
            "Typically requires 4-6 chairs for complete dining set",
            "Lifespan extends to 20+ years with proper maintenance"
        ],
        "peace": [
            "Requires $500 billion in annual global initiatives to maintain",
            "Monitored by 100,000 international observers across 195 countries",
            "Reduces conflict-related costs by 75% in affected regions",
            "Diplomatic missions operate in 5,000 locations worldwide",
            "Saves approximately $350 billion yearly in military spending"
        ]
    }
}

def generate_hints(word: str, category: str) -> List[str]:
    """Generate 10 meaningful hints for a word based on its category."""
    # First check if we have specific templates for this word
    if category in specific_word_templates and word in specific_word_templates[category]:
        return specific_word_templates[category][word]
    
    # Initialize hints list
    hints = []
    
    # Generate generic hints based on category
    if category == "animals":
        hints = [
            f"This is a {len(word)}-letter animal",
            f"This creature belongs to the animal kingdom",
            f"This animal starts with the letter '{word[0]}'",
            "This is a living creature",
            f"The last letter of this animal is '{word[-1]}'",
            "This is a member of the fauna",
            f"This word describes a beast",
            "This is a term for a living organism",
            f"This is a name for a creature",
            "This word refers to an animal species"
        ]
    elif category == "food":
        hints = [
            f"This is a {len(word)}-letter food item",
            f"This is something you can eat",
            f"This food starts with '{word[0]}'",
            "This is edible",
            f"This food item ends with '{word[-1]}'",
            "This is something you might find in a kitchen",
            "This is a type of nourishment",
            "This is something consumable",
            "This is a form of sustenance",
            "This is a kind of food"
        ]
    elif category == "places":
        hints = [
            f"This is a {len(word)}-letter location",
            f"This is a place you might visit",
            f"This place starts with '{word[0]}'",
            "This is a physical location",
            f"This place ends with '{word[-1]}'",
            "This is somewhere you could go",
            "This is a type of venue",
            "This is a kind of location",
            "This is a destination",
            "This is a specific place"
        ]
    elif category == "science":
        hints = [
            f"This is a {len(word)}-letter scientific term",
            f"This is related to science",
            f"This scientific term starts with '{word[0]}'",
            "This is a scientific concept",
            f"This term ends with '{word[-1]}'",
            "This is used in scientific contexts",
            "This is a scientific word",
            "This relates to scientific study",
            "This is a term used in research",
            "This is a scientific expression"
        ]
    elif category == "tech":
        hints = [
            f"This is a {len(word)}-letter technology term",
            f"This is related to technology",
            f"This tech term starts with '{word[0]}'",
            "This is a technical concept",
            f"This term ends with '{word[-1]}'",
            "This is used in computing",
            "This is a technical word",
            "This relates to digital technology",
            "This is used in IT",
            "This is a tech-related term"
        ]
    elif category == "sports":
        hints = [
            f"This is a {len(word)}-letter sports term",
            f"This is related to athletics",
            f"This sports term starts with '{word[0]}'",
            "This is related to physical activity",
            f"This term ends with '{word[-1]}'",
            "This is used in sports",
            "This is an athletic term",
            "This relates to competition",
            "This is used in games",
            "This is a sports-related word"
        ]
    elif category == "movies":
        hints = [
            f"This is a {len(word)}-letter movie-related term",
            f"This is connected to cinema",
            f"This term starts with '{word[0]}'",
            "This is related to filmmaking",
            f"This word ends with '{word[-1]}'",
            "This is used in the film industry",
            "This is a movie industry term",
            "This relates to cinema",
            "This is used in film production",
            "This is a movie-related word"
        ]
    elif category == "music":
        hints = [
            f"This is a {len(word)}-letter musical term",
            f"This is related to music",
            f"This musical term starts with '{word[0]}'",
            "This is connected to sound and rhythm",
            f"This term ends with '{word[-1]}'",
            "This is used in musical contexts",
            "This is a musical word",
            "This relates to melody and harmony",
            "This is used in music production",
            "This is a music-related term"
        ]
    elif category == "brands":
        hints = [
            f"This is a {len(word)}-letter brand name",
            f"This is a company or product name",
            f"This brand starts with '{word[0]}'",
            "This is a commercial name",
            f"This brand ends with '{word[-1]}'",
            "This is a business name",
            "This is a market brand",
            "This is a known trademark",
            "This is a company identifier",
            "This is a branded term"
        ]
    elif category == "history":
        hints = [
            f"This is a {len(word)}-letter historical term",
            f"This relates to past events",
            f"This historical term starts with '{word[0]}'",
            "This is connected to history",
            f"This term ends with '{word[-1]}'",
            "This is from the past",
            "This is a historical word",
            "This relates to human history",
            "This is used in historical contexts",
            "This is a term from the past"
        ]
    else:  # general, random, and any other category
        hints = [
            f"This is a {len(word)}-letter word",
            f"This word starts with '{word[0]}'",
            f"This is a common term",
            f"This word ends with '{word[-1]}'",
            f"This has {len(word)} characters",
            "This is a noun",
            "This is a common word",
            "This is a familiar term",
            "This is a standard word",
            "This is a regular term"
        ]
    
    return hints

# Ensure templates and categories sections exist
if "templates" not in hints_data:
    hints_data["templates"] = {}
if "categories" not in hints_data:
    hints_data["categories"] = {}

# Only add missing hints
for category, length_dict in words_data.items():
    if category not in hints_data["categories"]:
        hints_data["categories"][category] = {}
    for length, words in length_dict.items():
        if length not in hints_data["categories"][category]:
            hints_data["categories"][category][length] = {}
        for word in words:
            if word not in hints_data["categories"][category][length]:
                hints_data["categories"][category][length][word] = generate_hints(word, category)

# Save the updated hints.json
with open(hints_json_path, 'w', encoding='utf-8') as f:
    json.dump(hints_data, f, indent=2)

print("Hints updated: only missing words were added.")
