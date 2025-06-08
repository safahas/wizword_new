import os
import json
import time
import random
import requests
import logging
import smtplib
from email.mime.text import MIMEText
from typing import Tuple, Optional, Dict, List
from pathlib import Path
from dotenv import load_dotenv
from .fallback_words import get_fallback_word
from .openrouter_monitor import (
    update_quota_from_response,
    check_rate_limits,
    get_quota_warning,
    get_quota_status
)
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
env_path = Path(__file__).parent.parent / '.env'
logger.info(f"Looking for .env file at: {env_path.absolute()}")
load_dotenv(env_path)

# Add this before the WordSelector class
category_templates = {
    "general": {
        "table": [
            "This furniture piece typically measures 30 inches in height and supports 250 pounds of weight",
            "Modern versions cost between $200-$800 and last approximately 15 years",
            "Found in 98% of dining rooms and used exactly 3 times daily for meals",
            "Occupies approximately 15-20 square feet of floor space in average homes",
            "Production requires precisely 2.5 hours of assembly time in factories"
        ],
        "music": [
            "Vibrates at frequencies between 20 and 20,000 hertz for human hearing",
            "Traditionally divided into 12 semitones per octave in Western culture",
            "Recorded digitally at 44.1 kHz for CD-quality sound",
            "Travels through air at approximately 343 meters per second",
            "Requires at least 65 decibels for clear audibility in concert halls"
        ],
        "phone": [
            "Modern versions process data at 2.5 gigahertz and store 128GB of data",
            "Battery lasts exactly 12-15 hours and charges in 90 minutes",
            "Screen measures 6.1 inches diagonally with 460 pixels per inch",
            "Weighs precisely 174 grams and measures 5.78 inches in height",
            "Camera captures images at 48 megapixels with f/1.8 aperture"
        ],
        "light": [
            "Travels at precisely 299,792,458 meters per second in vacuum",
            "Visible spectrum ranges from 380 to 700 nanometers wavelength",
            "Solar version delivers approximately 1000 watts per square meter at noon",
            "LED versions last up to 50,000 hours of continuous operation",
            "Modern sensors detect as little as 0.00001 lux in darkness"
        ]
    },
    "animals": {
        "tiger": [
            "Adult males weigh exactly 420 pounds and measure 11 feet in length",
            "Runs at precisely 40 mph and jumps 20 feet horizontally",
            "Requires 15 pounds of meat daily and drinks 1 gallon of water",
            "Patrols territory of 40 square miles in natural habitat",
            "Lives between 20-25 years and sleeps 18 hours daily"
        ],
        "eagle": [
            "Spots prey from over 2 miles away with 20/4 vision acuity",
            "Dives at speeds exceeding 150 miles per hour during hunting",
            "Builds nests measuring up to 6 feet wide and 4 feet deep",
            "Wingspan typically ranges between 6 and 7.5 feet when fully grown",
            "Lives up to 30 years in natural habitats at elevations up to 10,000 feet"
        ],
        "shark": [
            "Swims continuously at 5 mph to push water through gills",
            "Detects blood in 1 part per million concentration from 0.25 miles",
            "Replaces 50,000 teeth in a lifetime spanning 70 years",
            "Dives to exactly 3,700 feet depth at 8 atmospheres pressure",
            "Maintains body temperature precisely 7°F above ambient water"
        ]
    },
    "food": {
        "pasta": [
            "Cooks for exactly 8-12 minutes in water at 212°F",
            "Contains 200 calories per 2-ounce serving and 42g carbohydrates",
            "Production exceeds 14.5 million tons annually worldwide",
            "Requires 4-6 quarts of water per pound for cooking",
            "Stores for 24 months at 70°F in airtight containers"
        ],
        "curry": [
            "Contains between 10 and 15 distinct spices in traditional recipes",
            "Preparation typically takes 45-60 minutes for authentic flavor",
            "Heat levels range from 500 to 50,000 Scoville units",
            "Originated over 4,000 years ago in South Asian cuisine",
            "Requires slow cooking at precisely 185°F for best results"
        ],
        "bread": [
            "Requires exactly 3 hours and 15 minutes for proper rising at 85°F",
            "Contains 150 calories per 2-ounce serving with 32g carbohydrates",
            "Bakes at precisely 375°F for 35 minutes until golden brown",
            "Uses 65% hydration ratio with 3% salt by flour weight",
            "Stays fresh for 48 hours when stored at 68°F"
        ]
    },
    "places": {
        "paris": [
            "Covers exactly 105.4 square kilometers with population density of 20,000 per km²",
            "Receives approximately 30 million tourists annually spending $21 billion",
            "Maintains average temperature of 15.5°C across 4 distinct seasons",
            "Houses precisely 296 metro stations spanning 214 kilometers of track",
            "Hosts 20,000 historic monuments dating back to 300 BCE"
        ],
        "tokyo": [
            "Spans precisely 2,194 square kilometers housing 37 million residents",
            "Processes 8.5 million commuters daily through 882 train stations",
            "Experiences 1,500 measurable earthquakes annually above 3.0 magnitude",
            "Maintains 36% green space across 11,000 hectares of urban area",
            "Operates transit system moving 40 million passengers per day"
        ]
    },
    "science": {
        "laser": [
            "Operates at precisely 1064 nanometers wavelength in industrial use",
            "Produces beam divergence of 0.5 milliradians at 100 meters",
            "Requires exactly 1.5 kilowatts power for continuous operation",
            "Achieves spot size of 25 microns for precise cutting",
            "Processes 1000 surface points per second in 3D scanning"
        ],
        "quark": [
            "Exists at temperatures above 2 trillion degrees Celsius",
            "Measures exactly 10^-18 meters in theoretical diameter",
            "Requires precisely 200 GeV of energy for separation",
            "Discovered in 1968 using 30 GeV particle accelerators",
            "Occurs in exactly 6 distinct types with specific charges"
        ],
        "atoms": [
            "Measures exactly 100 picometers in typical diameter",
            "Contains precisely 6.022 × 10^23 particles per mole",
            "Vibrates at frequencies of 10^13 hertz at room temperature",
            "Bonds at angles of 104.5 degrees in water molecules",
            "Requires 13.6 electron volts to ionize hydrogen"
        ],
        "force": [
            "Measures exactly 9.81 meters per second squared at sea level",
            "Generates 1000 newtons per square meter of pressure",
            "Requires 10 joules of energy for basic mechanical work",
            "Operates across distances of 10^-15 to 10^15 meters",
            "Produces acceleration of 3.27 meters per second squared"
        ],
        "light": [
            "Travels at exactly 299,792,458 meters per second in vacuum",
            "Wavelengths range from 380 to 700 nanometers precisely",
            "Requires 1.23 electron volts for visible photon energy",
            "Diffracts at angles of 0.5 degrees through 500nm slits",
            "Reflects at precisely equal angles from smooth surfaces"
        ],
        "cells": [
            "Divides every 24 hours under optimal conditions",
            "Maintains pH between 7.35-7.45 for proper function",
            "Contains exactly 37.2 trillion in human adult body",
            "Processes 1 billion ATP molecules per second",
            "Requires 0.1 millimeters minimum size for visibility"
        ],
        "brain": [
            "Processes information at 1016 operations per second",
            "Contains exactly 86 billion neurons in adult humans",
            "Requires 20% of body's oxygen at 15.4 liters per hour",
            "Maintains temperature at precisely 37.2°C normally",
            "Generates 10-23 watts of power during active thinking"
        ],
        "physics": [
            "Measures forces at precisely 9.81 m/s² on Earth",
            "Operates at temperatures of absolute zero (-273.15°C)",
            "Involves particles moving at 299,792,458 meters per second",
            "Generates magnetic fields of 2.5 tesla strength",
            "Requires precision to 0.000001 millimeters"
        ],
        "chemistry": [
            "Reactions occur at exactly 298.15 Kelvin standard temperature",
            "Solutions maintain pH between 6.5-7.5 precisely",
            "Molecules bind at angles of 104.5 degrees",
            "Requires exactly 6.022 × 10²³ particles per mole",
            "Achieves 99.9999% purity in laboratory conditions"
        ],
        "biology": [
            "Cells divide every 24 hours under optimal conditions",
            "Organisms maintain body temperature at exactly 37°C",
            "DNA contains precisely 3.2 billion base pairs",
            "Neurons fire at 200 times per second",
            "Requires exactly 20 different amino acids"
        ],
        "astronomy": [
            "Objects orbit at 7.67 kilometers per second",
            "Observes phenomena from 13.8 billion light-years away",
            "Detects radiation at wavelengths of 0.01 nanometers",
            "Measures stellar temperatures of 5,778 Kelvin",
            "Tracks objects moving at 2.1 million kilometers per hour"
        ],
        "research": [
            "Studies require exactly 1,000 test subjects",
            "Experiments run for precisely 36 months",
            "Data collection occurs every 15 minutes",
            "Analysis involves 50 terabytes of information",
            "Results achieve 95% confidence intervals"
        ]
    },
    "movies": {
        "drama": [
            "Generates approximately $15 billion in annual box office revenue",
            "Requires exactly 120 pages for standard screenplay format",
            "Films at 24 frames per second using 35mm digital equivalent",
            "Processes 4K resolution at 3840 x 2160 pixels per frame",
            "Records audio at precisely 48 kHz sample rate"
        ],
        "actor": [
            "Memorizes 850 words of dialogue per hour of content",
            "Performs under 5600K lighting at 100 foot-candles",
            "Requires 12-14 hours on set for 3-4 minutes of usable footage",
            "Maintains precise positions within 2 inch markers on set",
            "Syncs dialogue within 0.03 seconds for perfect lip sync"
        ]
    },
    "music": {
        "tempo": [
            "Measures precisely 120 beats per minute in common time",
            "Oscillates between 20 Hz and 20 kHz in audible range",
            "Records at exactly 44.1 kHz digital sampling rate",
            "Processes 32-bit floating point audio at 192 kHz",
            "Maintains timing accuracy within 0.5 milliseconds"
        ],
        "sound": [
            "Travels exactly 343 meters per second at sea level",
            "Requires minimum 60 dB for clear vocal reproduction",
            "Generates frequencies between 27.5 Hz and 4186 Hz on piano",
            "Processes 1,411,200 bits of data per second in CD quality",
            "Reflects off surfaces at precisely equal angles"
        ]
    }
}

# Default templates for categories without specific words
default_templates = {
    "general": [
        "Found in exactly 92.5% of modern households globally",
        "Weighs precisely between 2.5 and 10.2 pounds for standard use",
        "Lasts approximately 7.3 years with proper maintenance",
        "Used by 3.2 billion people daily across 195 countries",
        "Developed through 50 years of engineering improvements"
    ],
    "animals": [
        "Maintains body temperature between 35-42°C for optimal function",
        "Consumes exactly 12% of body weight in food daily",
        "Inhabits territories ranging from 2,500-4,000 feet elevation",
        "Travels precisely 22.5 miles daily for resources",
        "Produces sounds audible up to 1.2 miles in natural habitat"
    ],
    "food": [
        "Contains exactly 150 calories per 100-gram serving",
        "Requires precisely 45 minutes preparation time at 350°F",
        "Stores for 72 hours at 40°F in proper conditions",
        "Provides 15% daily value of essential nutrients",
        "Costs $3.50 per pound in standard markets"
    ],
    "places": [
        "Experiences average temperature of 22.5°C year-round",
        "Receives precisely 2.5 million visitors annually",
        "Covers exactly 150 square kilometers of land area",
        "Houses 500,000 residents with 95% occupancy rate",
        "Maintains 35% green space in urban planning"
    ],
    "science": [
        "Operates at exactly 1064 nanometers wavelength",
        "Processes 1000 data points per millisecond",
        "Requires precisely 2.5 kilowatts power input",
        "Achieves 99.99% accuracy in measurements",
        "Maintains temperature at -196°C using liquid nitrogen"
    ],
    "tech": [
        "Processes data at 3.2 gigahertz clock speed",
        "Stores exactly 1 terabyte of information",
        "Consumes 65 watts of power during operation",
        "Transfers data at 10 gigabits per second",
        "Updates every 2.5 milliseconds in real-time"
    ],
    "movies": [
        "Generates $500 million in global box office revenue",
        "Runs exactly 120 minutes in theatrical release",
        "Films using 8K cameras at 60 frames per second",
        "Employs 2500 visual effects artists for production",
        "Reaches 100 million viewers in first month"
    ],
    "music": [
        "Plays at precisely 120 beats per minute tempo",
        "Records at 192 kilohertz sample rate",
        "Reaches frequency range of 20-20,000 hertz",
        "Performs in venues seating 15,000 people",
        "Streams to 50 million listeners monthly"
    ],
    "brands": [
        "Values at precisely $100 billion market cap",
        "Serves 500 million customers annually",
        "Operates in exactly 150 countries worldwide",
        "Employs 250,000 people globally",
        "Generates $50 billion yearly revenue"
    ],
    "history": [
        "Occurred exactly 100 years ago in 1924",
        "Involved precisely 1 million participants",
        "Lasted exactly 5 years and 3 months",
        "Covered territory of 500,000 square miles",
        "Impacted 25% of global population"
    ]
}

# Fallback hints for specific words
WORD_HINTS = {
    "otter": [
        "This mammal is known for its exceptional swimming abilities in rivers and coastal waters",
        "This animal uses tools like rocks to crack open shellfish while floating on its back",
        "This playful creature has thick, water-resistant fur and spends most of its time in or near water",
        "This semi-aquatic predator hunts fish and is known for its agile underwater movements",
        "This marine mammal forms close family groups and often holds hands while sleeping to avoid drifting apart"
    ],
}

class WordSelector:
    # Define available categories
    CATEGORIES = [
        "general",
        "animals",
        "food",
        "places",
        "science",
        "tech",
        "sports",
        "movies",
        "music",
        "brands",
        "history",
        "random"
    ]

    # Class-level set to track recently used words across all instances
    _recently_used_words = set()
    _max_recent_words = 50  # Maximum number of words to remember

    def __init__(self):
        """Initialize the word selector."""
        # Load environment variables
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.use_fallback = not bool(self.api_key)
        
        if self.use_fallback:
            logger.warning("OpenRouter API key not set. Using fallback mode with local dictionary.")
        else:
            logger.info("OpenRouter API key found. Using API mode.")
            
        self.model = "openai/gpt-4"  # Default model
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.max_retries = 3
        self.initial_backoff = 1  # seconds
        
        # Email configuration
        self.admin_email = os.getenv("ADMIN_EMAIL")
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER")
        self.smtp_pass = os.getenv("SMTP_PASS")

    def get_recently_used_words(self) -> list:
        """Get the list of recently used words."""
        return list(self._recently_used_words)

    def clear_recent_words(self):
        """Clear the list of recently used words."""
        self._recently_used_words.clear()
        logger.info("Cleared recently used words list")

    def _send_email_alert(self, subject: str, body: str) -> None:
        """Send email alert to admin."""
        if not all([self.admin_email, self.smtp_user, self.smtp_pass]):
            logger.warning("Email configuration incomplete. Skipping email alert.")
            return
            
        try:
            msg = MIMEText(body)
            msg['Subject'] = subject
            msg['From'] = self.smtp_user
            msg['To'] = self.admin_email
            
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_pass)
                server.send_message(msg)
                
            logger.info(f"Rate limit warning email sent to {self.admin_email}")
        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _make_api_request(self, data: dict, retry_count: int = 0) -> dict:
        """Make API request with exponential backoff retry and rate limit monitoring."""
        if self.use_fallback:
            raise requests.exceptions.RequestException("API key not set. Using fallback mode.")
            
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/cursor",
            "X-Title": "Word Guess Contest AI"
        }
        
        # Check rate limits before making request
        is_allowed, error_msg = check_rate_limits()
        if not is_allowed:
            raise requests.exceptions.RequestException(error_msg)
        
        # Add required OpenRouter parameters
        data.update({
            "model": self.model,
            "temperature": 0.7,
            "max_tokens": 50,
            "top_p": 0.95,
            "frequency_penalty": 0,
            "presence_penalty": 0,
            "stream": False,
            "messages": data.get("messages", [])
        })
        
        try:
            logger.info(f"Making API request with data: {json.dumps(data)}")
            response = requests.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=10  # Add timeout
            )
            response.raise_for_status()
            
            # Update quota information from response headers
            update_quota_from_response(response.headers)
            
            # Get current quota warning if any
            warning = get_quota_warning()
            
            # If critical quota warning, send email alert
            if warning and warning["level"] == "error":
                quota_status = get_quota_status()
                self._send_email_alert(
                    "Word Guess Game - Critical API Quota Warning",
                    f"Critical: API quota is critically low!\n\n"
                    f"Status: {json.dumps(quota_status, indent=2)}\n\n"
                    f"Action required: Please check the API quota and usage patterns."
                )
            
            # Add warning to response if present
            response_data = response.json()
            if warning:
                response_data["_rate_limit_warning"] = warning
            
            return response_data
            
        except (requests.exceptions.RequestException, json.JSONDecodeError) as e:
            if retry_count >= self.max_retries:
                logger.error(f"Max retries ({self.max_retries}) reached. Error: {e}")
                raise
                
            # Calculate exponential backoff with jitter
            backoff = self.initial_backoff * (2 ** retry_count)
            jitter = random.uniform(0, 0.1 * backoff)
            wait_time = backoff + jitter
            
            logger.warning(f"API request failed. Retrying in {wait_time:.2f} seconds... (Attempt {retry_count + 1}/{self.max_retries})")
            time.sleep(wait_time)
            
            return self._make_api_request(data, retry_count + 1)

    def _build_prompt(self, word_length: int, subject: str) -> dict:
        """Build the prompt for word selection with strict JSON formatting."""
        return {
            "messages": [
                {
                    "role": "system",
                    "content": 'You are a word guessing game assistant. You MUST respond with ONLY a JSON object using double quotes, in this exact format: {"selected_word": "WORD"}'
                },
                {
                    "role": "user",
                    "content": f'Choose a {word_length}-letter English word under the subject "{subject}". Respond with ONLY the JSON object using double quotes.'
                }
            ]
        }

    def select_word(self, word_length: int, subject: str) -> str:
        """
        Select a word using the API with fallback to local dictionary.
        Ensures the same word is not selected repeatedly.
        """
        # First check if the word length is supported in our dictionary
        supported_lengths = list(range(3, 11))  # Our dictionary supports 3-10 letter words
        if word_length not in supported_lengths:
            raise ValueError(
                f"Word length {word_length} is not supported. "
                f"Please choose a word length between {min(supported_lengths)} and {max(supported_lengths)} letters."
            )

        max_attempts = 10  # Maximum attempts to find a new word
        selected_word = None

        # Log current state of recently used words
        logger.info(f"Currently tracking {len(self._recently_used_words)} recently used words")
        logger.debug(f"Recent words: {self._recently_used_words}")

        # If we've used too many words, clear the oldest ones
        if len(self._recently_used_words) >= self._max_recent_words * 0.8:  # Lower threshold to 80%
            num_to_remove = int(self._max_recent_words * 0.5)  # Remove 50% of words
            old_words = list(self._recently_used_words)[:num_to_remove]
            for word in old_words:
                self._recently_used_words.remove(word)
            logger.info(f"Cleared {num_to_remove} old words from recently used list")

        for attempt in range(max_attempts):
            logger.debug(f"Word selection attempt {attempt + 1}")
            
            if self.use_fallback:
                # Get multiple fallback words and try to find one not recently used
                fallback_words = []
                for _ in range(10):  # Try more words
                    word = get_fallback_word(word_length, subject)
                    if word and word not in self._recently_used_words:
                        fallback_words.append(word)
                
                if fallback_words:
                    selected_word = random.choice(fallback_words)
                    logger.info(f"Selected new word '{selected_word}' from {len(fallback_words)} available words")
                else:
                    # If all words are used, clear half the recent words and try again
                    num_to_remove = len(self._recently_used_words) // 2
                    old_words = list(self._recently_used_words)[:num_to_remove]
                    for word in old_words:
                        self._recently_used_words.remove(word)
                    logger.info(f"Cleared {num_to_remove} old words from recently used list")
                    selected_word = get_fallback_word(word_length, subject)
            else:
                try:
                    # Try API with retries, asking for a different word each time
                    recent_words_list = list(self._recently_used_words)
                    prompt_data = {
                        "messages": [
                            {
                                "role": "system",
                                "content": f'You are a word guessing game assistant. You MUST respond with ONLY a JSON object using double quotes, in this exact format: {{"selected_word": "WORD"}}. IMPORTANT: DO NOT use any of these words: {recent_words_list}. Choose a completely different word.'
                            },
                            {
                                "role": "user",
                                "content": f'Choose a {word_length}-letter English word under the subject "{subject}". The word MUST NOT be any of these: {recent_words_list}. Respond with ONLY the JSON object using double quotes.'
                            }
                        ]
                    }
                    response = self._make_api_request(prompt_data)
                    content = response["choices"][0]["message"]["content"]
                    
                    try:
                        word_data = json.loads(content)
                        selected_word = word_data["selected_word"].lower()
                        
                        # Validate the word
                        if len(selected_word) != word_length:
                            logger.warning(f"API returned word '{selected_word}' with wrong length")
                            continue
                        if not selected_word.isalpha():
                            logger.warning(f"API returned non-alphabetic word '{selected_word}'")
                            continue
                        if selected_word in self._recently_used_words:
                            logger.warning(f"API returned recently used word '{selected_word}', trying again")
                            continue
                            
                    except (json.JSONDecodeError, KeyError, ValueError) as e:
                        logger.error(f"Failed to parse word from API response: {e}")
                        continue
                        
                except Exception as e:
                    # Fall back to local dictionary
                    logger.warning(f"API selection failed: {e}. Falling back to local dictionary.")
                    selected_word = get_fallback_word(word_length, subject)

            # Check if word was recently used
            if selected_word and selected_word not in self._recently_used_words:
                # Add word to recently used set
                self._recently_used_words.add(selected_word)
                logger.info(f"Selected word: {selected_word} (attempt {attempt + 1})")
                return selected_word

        # If we've tried max_attempts times and still haven't found a new word,
        # clear half of the recently used words and try one final time
        logger.warning("Max attempts reached without finding unused word, clearing half of recent words")
        num_to_remove = len(self._recently_used_words) // 2
        old_words = list(self._recently_used_words)[:num_to_remove]
        for word in old_words:
            self._recently_used_words.remove(word)
        logger.info(f"Cleared {num_to_remove} old words after max attempts")

        if self.use_fallback:
            selected_word = get_fallback_word(word_length, subject)
        else:
            try:
                prompt_data = {
                    "messages": [
                        {
                            "role": "system",
                            "content": 'You are a word guessing game assistant. You MUST respond with ONLY a JSON object using double quotes, in this exact format: {"selected_word": "WORD"}.'
                        },
                        {
                            "role": "user",
                            "content": f'Choose a {word_length}-letter English word under the subject "{subject}". Respond with ONLY the JSON object using double quotes.'
                        }
                    ]
                }
                response = self._make_api_request(prompt_data)
                word_data = json.loads(response["choices"][0]["message"]["content"])
                selected_word = word_data["selected_word"].lower()
                
                # Validate the word one last time
                if len(selected_word) != word_length or not selected_word.isalpha():
                    selected_word = get_fallback_word(word_length, subject)
                
            except Exception:
                selected_word = get_fallback_word(word_length, subject)

        # Add the final selected word to recently used words
        if selected_word not in self._recently_used_words:
            self._recently_used_words.add(selected_word)
            logger.info(f"Selected word (after clearing half of recent words): {selected_word}")
        return selected_word

    def _validate_hint(self, hint: str, word: str, previous_hints: List[str]) -> bool:
        """Validate that a hint follows all rules and is specific enough."""
        # Convert to lowercase for comparisons
        hint_lower = hint.lower().strip()
        word_lower = word.lower()
        
        # Debug logging
        logger.debug(f"Validating hint: '{hint_lower}'")
        
        # Check for previous hints
        if hint in previous_hints:
            logger.debug("Hint rejected: duplicate hint")
            return False
            
        # Check length (keep hints concise but informative)
        words = hint.split()
        if len(words) < 5 or len(words) > 25:
            logger.debug("Hint rejected: too short or too long")
            return False
            
        # Check for word mention
        if word_lower in hint_lower:
            logger.debug("Hint rejected: contains the word")
            return False
            
        # Check for letter counts
        letter_patterns = [
            r"\b\d+\s*letters?\b",
            r"\b\w+\s*letters?\b",
            r"\bletter\s*count\b",
            r"\bcharacters?\b"
        ]
        for pattern in letter_patterns:
            if re.search(pattern, hint_lower):
                logger.debug("Hint rejected: mentions letter count")
                return False
            
        # Check for specific measurements (must have at least one)
        measurement_patterns = [
            r"\d+(?:\.\d+)?\s*(?:degrees?|°[CF]|K)",  # Temperature
            r"\d+(?:\.\d+)?\s*(?:meters?|m|km|miles?|feet|ft)",  # Distance
            r"\d+(?:\.\d+)?\s*(?:seconds?|minutes?|hours?|days?|years?)",  # Time
            r"\d+(?:\.\d+)?\s*(?:Hz|hertz|MHz|GHz)",  # Frequency
            r"\d+(?:\.\d+)?\s*(?:watts?|W|kW|MW)",  # Power
            r"\d+(?:\.\d+)?\s*(?:dollars?|\$|€|£)",  # Money
            r"\d+(?:\.\d+)?\s*(?:percent|%)",  # Percentage
            r"\d+(?:\.\d+)?\s*(?:kg|g|pounds?|lbs)",  # Weight
            r"\d+(?:\.\d+)?\s*(?:liters?|L|gallons?|gal)",  # Volume
            r"\d+(?:\.\d+)?\s*(?:square\s*(?:meters?|feet|km|miles?))",  # Area
            r"\d+(?:\.\d+)?\s*(?:volts?|V|amperes?|A)",  # Electrical
            r"\d+(?:\.\d+)?\s*(?:pixels?|px|MP|megapixels?)",  # Digital
            r"\d+(?:\.\d+)?\s*(?:bits?|bytes?|KB|MB|GB|TB)"  # Data
        ]
        
        has_measurement = False
        for pattern in measurement_patterns:
            if re.search(pattern, hint_lower):
                has_measurement = True
                break
            
        if not has_measurement:
            logger.debug("Hint rejected: no specific measurements")
            return False
        
        return True

    def get_semantic_hint(self, word: str, subject: str, previous_hints: List[str] = None) -> str:
        """Get a semantic hint about the word, either from API or fallback."""
        if previous_hints is None:
            previous_hints = []
            
        if self.use_fallback:
            return self._get_fallback_semantic_hint(word, subject, previous_hints)
            
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a hint generator for a word guessing game.
                    Rules for generating hints:
                    1. NEVER mention the word itself or any part of it
                    2. NEVER mention letter counts or specific letters
                    3. MUST include at least one precise measurement with units from this list:
                       - Temperature (°C, °F, K)
                       - Distance (meters, km, miles, feet)
                       - Time (seconds, minutes, hours, years)
                       - Frequency (Hz, MHz, GHz)
                       - Power (watts, kW, MW)
                       - Money ($, €, £)
                       - Percentage (%)
                       - Weight (kg, g, pounds)
                       - Volume (liters, gallons)
                       - Area (square meters/feet/km/miles)
                       - Electrical (volts, amperes)
                       - Digital (pixels, MP, bits, bytes)
                    4. Make hints specific and detailed:
                       - Use concrete examples with exact numbers
                       - Reference well-known facts with measurements
                       - Include distinctive features with precise values
                       - Avoid generic descriptions
                    5. Keep hints concise (1-2 sentences)
                    6. Make each hint unique and different from previous ones
                    7. Use active voice and present tense
                    8. Include category-specific knowledge
                    9. Make hints progressively more helpful"""
                },
                {
                    "role": "user",
                    "content": f"""
                    Word: {word}
                    Category: {subject}
                    Previous hints: {previous_hints}
                    
                    Generate a semantic hint that helps guess the word.
                    The hint must follow ALL the rules strictly.
                    Respond with ONLY the hint text.
                    Make this hint different from and more specific than previous hints.
                    Focus on unique and distinctive features that help identify this specific word.
                    """
                }
            ]
        }
        
        try:
            response = self._make_api_request(data)
            hint = response["choices"][0]["message"]["content"].strip()
            
            # Validate the hint
            if self._validate_hint(hint, word, previous_hints):
                return hint
            else:
                logger.warning(f"API hint '{hint}' failed validation, using fallback")
                return self._get_fallback_semantic_hint(word, subject, previous_hints)
                
        except Exception as e:
            logger.error(f"Failed to get semantic hint from API: {e}")
            return self._get_fallback_semantic_hint(word, subject, previous_hints)

    def _generate_hint_from_template(self, template: str, word: str, subject: str) -> str:
        """Generate a specific hint from a template based on word and category."""
        # Category-specific hint parameters
        hint_params = {
            "animals": {
                "habitat": ["forests", "oceans", "grasslands", "mountains", "deserts", "wetlands", "urban areas"],
                "feature": ["fur", "scales", "feathers", "claws", "beak", "tail", "wings"],
                "behavior": ["hunting", "grazing", "swimming", "flying", "climbing", "digging", "nesting"],
                "family": ["mammal", "reptile", "bird", "fish", "amphibian", "insect"],
                "characteristic": ["size", "color", "pattern", "shape", "movement", "sound"],
                "ability": ["run", "swim", "fly", "climb", "jump", "hide", "hunt"],
                "location": ["wild", "farms", "homes", "zoos", "parks", "nature reserves"],
                "similar": ["domestic pets", "wild animals", "farm animals", "exotic creatures"],
                "difference": ["size", "habitat", "behavior", "diet", "appearance"],
                "time": ["day", "night", "dawn", "dusk", "seasonal"],
                "interaction": ["companionship", "work", "entertainment", "assistance"]
            },
            "food": {
                "cuisine": ["Italian", "Chinese", "Mexican", "Indian", "French", "Japanese", "Mediterranean"],
                "flavor": ["sweet", "savory", "spicy", "sour", "bitter", "umami"],
                "method": ["baking", "grilling", "frying", "boiling", "steaming", "roasting"],
                "accompaniment": ["rice", "pasta", "bread", "vegetables", "sauce", "spices"],
                "texture": ["crispy", "soft", "crunchy", "smooth", "creamy", "chewy"],
                "occasion": ["breakfast", "lunch", "dinner", "celebrations", "holidays"],
                "ingredient": ["vegetables", "fruits", "grains", "meat", "dairy", "spices"],
                "type": ["casual", "fine dining", "fast food", "street food", "home-style"],
                "category": ["appetizer", "main course", "dessert", "snack", "beverage"],
                "time": ["morning", "afternoon", "evening", "special occasions"]
            },
            "places": {
                "activity": ["work", "shop", "eat", "learn", "exercise", "relax", "socialize"],
                "atmosphere": ["busy", "quiet", "formal", "casual", "energetic", "peaceful"],
                "area": ["cities", "suburbs", "rural areas", "nature", "indoors", "outdoors"],
                "purpose": ["business", "leisure", "education", "healthcare", "entertainment"],
                "features": ["buildings", "spaces", "facilities", "amenities", "services"],
                "time": ["day", "night", "weekends", "seasons", "holidays"],
                "association": ["work", "fun", "learning", "health", "culture"],
                "function": ["gathering", "working", "shopping", "dining", "recreation"],
                "characteristic": ["size", "location", "accessibility", "popularity"],
                "reason": ["necessity", "entertainment", "education", "relaxation"]
            },
            "science": {
                "field": ["physics", "chemistry", "biology", "astronomy", "geology"],
                "subject": ["matter", "energy", "life", "space", "earth"],
                "phenomenon": ["natural", "physical", "chemical", "biological"],
                "context": ["laboratories", "research", "industry", "nature", "space"],
                "concept": ["theories", "laws", "principles", "models", "hypotheses"],
                "topic": ["universe", "matter", "life", "energy", "systems"],
                "discovery": ["observation", "experimentation", "analysis", "research"],
                "measurement": ["instruments", "tools", "methods", "techniques"],
                "principle": ["fundamental laws", "theories", "relationships", "processes"],
                "application": ["technology", "medicine", "industry", "research"]
            },
            "tech": {
                "system": ["computer", "network", "software", "hardware", "digital"],
                "function": ["processing", "storage", "communication", "control"],
                "component": ["hardware", "software", "network", "interface"],
                "task": ["automation", "analysis", "communication", "storage"],
                "device": ["computers", "phones", "tablets", "servers"],
                "connection": ["internet", "networks", "wireless", "cloud"],
                "data_type": ["text", "images", "audio", "video"],
                "control": ["systems", "processes", "devices", "networks"],
                "management": ["resources", "data", "systems", "networks"],
                "capability": ["processing", "storage", "communication", "analysis"]
            },
            "sports": {
                "sport": [
                    "Requires exactly 90 minutes of regulation play time",
                    "Played professionally in 195 countries worldwide",
                    "Involves precisely 11 players per team on the field",
                    "Competitions occur at exactly 211 national associations",
                    "Generates approximately $28 billion in annual revenue"
                ],
                "action": [
                    "Athletes burn 600-800 calories per hour during competition",
                    "Requires reaction times under 0.15 seconds",
                    "Involves movements at speeds up to 35 mph",
                    "Generates forces up to 8 times body weight",
                    "Requires maintaining heart rates between 160-180 bpm"
                ],
                "strategy": [
                    "Success rate increases 45% with proper technique",
                    "Involves analyzing 12-15 different play patterns",
                    "Requires coordinating exactly 5 key movement phases",
                    "Uses 3-dimensional space calculations within 0.1 seconds",
                    "Implements 8 fundamental tactical principles"
                ],
                "venue": [
                    "Facilities typically cover 85,000 square feet",
                    "Maintains temperature at precisely 72°F year-round",
                    "Accommodates exactly 50,000 spectators at capacity",
                    "Requires 250 staff members for full operation",
                    "Uses 1.2 million watts of lighting power"
                ],
                "performance": [
                    "Elite athletes train exactly 35 hours weekly",
                    "Performance peaks between ages 25-28 statistically",
                    "Requires maintaining 12% body fat for optimal results",
                    "Athletes consume 3,500-4,000 calories daily",
                    "Recovery takes precisely 48 hours between events"
                ]
            },
            "movies": {
                "genre": ["action", "drama", "comedy", "thriller", "romance"],
                "element": ["plot", "characters", "setting", "dialogue"],
                "production": ["filming", "editing", "effects", "sound"],
                "role": ["acting", "directing", "producing", "writing"],
                "aspect": ["visual", "narrative", "technical", "artistic"],
                "experience": ["entertainment", "emotion", "thought", "excitement"],
                "technique": ["cinematography", "editing", "sound", "effects"],
                "quality": ["storytelling", "performance", "visuals", "sound"],
                "impact": ["emotional", "cultural", "social", "artistic"],
                "feature": ["story", "cast", "effects", "music"]
            },
            "music": {
                "style": ["classical", "rock", "jazz", "pop", "folk"],
                "element": ["melody", "rhythm", "harmony", "lyrics"],
                "instrument": ["strings", "percussion", "wind", "electronic"],
                "performance": ["live", "recorded", "solo", "ensemble"],
                "quality": ["tone", "tempo", "dynamics", "expression"],
                "aspect": ["composition", "arrangement", "production"],
                "effect": ["emotional", "physical", "mental", "social"],
                "technique": ["playing", "singing", "composing", "arranging"],
                "feature": ["sound", "rhythm", "melody", "harmony"],
                "context": ["concerts", "recordings", "practice", "performance"]
            },
            "general": {
                "concept": ["everyday life", "common experiences", "basic needs", "human activities"],
                "usage": ["daily activities", "communication", "interaction", "organization"],
                "description": ["physical objects", "abstract ideas", "human experiences", "natural phenomena"],
                "relation": ["human activities", "natural world", "social interactions", "personal experiences"],
                "context": ["daily life", "social settings", "personal space", "public places"],
                "association": ["common activities", "shared experiences", "cultural elements", "social norms"],
                "expression": ["thoughts", "feelings", "ideas", "needs"],
                "reference": ["common objects", "shared concepts", "universal experiences", "basic needs"],
                "representation": ["physical items", "abstract concepts", "human needs", "social elements"],
                "connection": ["daily activities", "human experiences", "social interactions", "basic needs"],
                "ocean": [
                    "A vast expanse of blue that covers most of Earth's surface",
                    "Home to countless marine creatures and underwater ecosystems",
                    "Where waves meet the horizon in an endless dance",
                    "Salty waters that connect continents",
                    "A deep blue realm of mystery and wonder"
                ],
                "default": [
                    "This {length}-letter word represents something common in daily life",
                    "A word often used to describe basic concepts or objects",
                    "Something you might encounter in everyday situations",
                    "A fundamental term in the English language",
                    "A word that describes a common element of human experience",
                    "Something that most people are familiar with",
                    "A basic concept that's part of our regular vocabulary",
                    "A term used to describe everyday things or ideas",
                    "Something that's part of common knowledge",
                    "A word that represents a universal concept"
                ]
            }
        }

        try:
            # Get category-specific parameters
            params = hint_params.get(subject, hint_params["general"])
            
            # Select random values for each parameter in the template
            for param_name, param_values in params.items():
                if "{" + param_name + "}" in template:
                    template = template.replace(
                        "{" + param_name + "}", 
                        random.choice(param_values)
                    )
            
            return template
            
        except Exception as e:
            logger.error(f"Error generating hint from template: {e}")
            return f"This {subject} term is something special"

    def _get_fallback_semantic_hint(self, word: str, subject: str, previous_hints: List[str] = None) -> str:
        """Get a fallback semantic hint when API is not available."""
        if previous_hints is None:
            previous_hints = []
        
        # Normalize subject to match template categories
        subject = subject.lower()
        if subject == "tech":
            subject = "technology"
            
        # Define a global default template if nothing else matches
        global_default = [
            "This term has specific uses and meanings",
            "Found in everyday situations and contexts",
            "Serves particular functions or purposes",
            "Has distinctive characteristics or features",
            "Used in specific ways by people"
        ]
        
        try:
            # Try word-specific hints first
            if word in category_templates.get(subject, {}):
                word_hints = category_templates[subject][word]
                available_hints = [hint for hint in word_hints if hint not in previous_hints]
                if available_hints:
                    return random.choice(available_hints)
            
            # Try category defaults
            if subject in category_templates:
                category_defaults = category_templates[subject].get("default", [])
                available_hints = [hint for hint in category_defaults if hint not in previous_hints]
                if available_hints:
                    return random.choice(available_hints)
            
            # Try general category defaults
            general_defaults = category_templates.get("general", {}).get("default", [])
            available_hints = [hint for hint in general_defaults if hint not in previous_hints]
            if available_hints:
                return random.choice(available_hints)
            
            # If all else fails, use global default
            available_hints = [hint for hint in global_default if hint not in previous_hints]
            if available_hints:
                return random.choice(available_hints)
            else:
                # If all hints have been used, cycle through global defaults
                return random.choice(global_default)
                
        except Exception as e:
            logger.error(f"Error getting fallback hint: {e}")
            return "This has specific characteristics and uses"

    def answer_question(self, word: str, question: str) -> Tuple[bool, str]:
        """
        Ask the LLM a yes/no question about the word with retries and fallback.
        Returns a tuple of (is_valid_question: bool, answer: str)
        """
        # First check if this is a word guess
        question = question.lower().strip()
        word_guess_patterns = [
            r"^is (?:the )?(?:word )?['\"]?(\w+)['\"]?\??$",
            r"^(?:is it|could it be) ['\"]?(\w+)['\"]?\??$",
            r"^(?:the )?word is ['\"]?(\w+)['\"]?\??$",
            r"^(?:does )?it say ['\"]?(\w+)['\"]?\??$",
            r"^(?:is )?['\"]?(\w+)['\"]? (?:the word|correct)\??$",
            r"^['\"]?(\w+)['\"]?\??$"  # Just the word itself
        ]
        
        for pattern in word_guess_patterns:
            match = re.search(pattern, question)
            if match:
                return False, "Please use the 'Submit Guess' button to make your final guess."

        # Check if this is a letter question for positions other than first or last
        letter_pattern = r"(?:is|does|has|contains?).*(?:letter|character).*(?:second|third|middle|2nd|3rd|fourth|4th|fifth|5th)"
        if re.search(letter_pattern, question):
            return False, "Only questions about the first and last letters are allowed. Try guessing the word using the 'Submit Guess' button."

        if self.use_fallback:
            return self._answer_question_fallback(word, question)
            
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are helping with a word guessing game. The player is trying to guess a word by asking questions.
                    Guidelines for answering:
                    1. ONLY answer questions about the first and last letters - reject all other letter position questions
                    2. For non-letter questions, give clear yes/no answers with brief explanations
                    3. If you can't understand the question, ask for clarification
                    4. NEVER reveal or confirm the word - direct players to use the 'Submit Guess' button
                    5. If the player tries to guess the word, respond with: Please use the 'Submit Guess' button to make your final guess.
                    6. For questions about letters in positions other than first or last, respond with: Only questions about the first and last letters are allowed."""
                },
                {
                    "role": "user",
                    "content": f"""
                    The word is: {word}
                    Player's question: {question}
                    
                    Answer the question helpfully. Only answer questions about first and last letters.
                    For other questions, answer with yes/no and a brief explanation if relevant.
                    Remember: NEVER reveal or confirm the word.
                    """
                }
            ]
        }
        
        try:
            response = self._make_api_request(data)
            answer = response["choices"][0]["message"]["content"].strip()
            
            # Double check that the answer doesn't reveal the word
            if word.lower() in answer.lower():
                return False, "Please use the 'Submit Guess' button to make your final guess."
                
            return True, answer
            
        except Exception as e:
            logger.error(f"Failed to get answer from API: {e}")
            return self._answer_question_fallback(word, question)

    def _answer_question_fallback(self, word: str, question: str) -> Tuple[bool, str]:
        """
        Fallback question answering system when API is not available.
        Uses pattern matching and word-specific knowledge to provide answers.
        """
        # Normalize question and word
        question = question.lower().strip()
        word = word.lower()
        
        # Check if this is a word guess - expanded patterns to catch more cases
        word_guess_patterns = [
            r"^is (?:the )?(?:word )?['\"]?(\w+)['\"]?\??$",
            r"^(?:is it|could it be) ['\"]?(\w+)['\"]?\??$",
            r"^(?:the )?word is ['\"]?(\w+)['\"]?\??$",
            r"^(?:does )?it say ['\"]?(\w+)['\"]?\??$",
            r"^(?:is )?['\"]?(\w+)['\"]? (?:the word|correct)\??$",
            r"^['\"]?(\w+)['\"]?\??$"  # Just the word itself
        ]
        
        for pattern in word_guess_patterns:
            match = re.search(pattern, question)
            if match:
                return False, "Please use the 'Submit Guess' button to make your final guess."

        # Check if this is a letter question for positions other than first or last
        letter_pattern = r"(?:is|does|has|contains?).*(?:letter|character).*(?:second|third|middle|2nd|3rd|fourth|4th|fifth|5th)"
        if re.search(letter_pattern, question):
            return False, "Only questions about the first and last letters are allowed. Try guessing the word using the 'Submit Guess' button."

        # Handle first letter questions
        first_letter_pattern = r"(?:is|does|has|contains?).*(?:first|1st|start|begin).*(?:letter|character).*['\"]?(\w)['\"]?"
        match = re.search(first_letter_pattern, question)
        if match:
            letter = match.group(1).lower()
            return True, f"Yes, the first letter is '{word[0]}'" if word[0] == letter else f"No, the first letter is not '{letter}'"

        # Handle last letter questions
        last_letter_pattern = r"(?:is|does|has|contains?).*(?:last|final|end).*(?:letter|character).*['\"]?(\w)['\"]?"
        match = re.search(last_letter_pattern, question)
        if match:
            letter = match.group(1).lower()
            return True, f"Yes, the last letter is '{word[-1]}'" if word[-1] == letter else f"No, the last letter is not '{letter}'"

        # For any other letter position questions, reject them
        if re.search(r"(?:letter|character|spell)", question):
            return False, "Only questions about the first and last letters are allowed. Try guessing the word using the 'Submit Guess' button."

        # For non-letter questions, give a generic response
        return True, "No, that's not correct. Try asking about the first or last letter, or make a guess using the 'Submit Guess' button."

    def verify_guess(self, word: str, guess: str) -> bool:
        """Verify if the guessed word matches the actual word."""
        return word.lower() == guess.lower() 