# Word Guess Contest AI - Technical Documentation

## Architecture Overview

### Components

1. **Frontend (Streamlit)**
   - `streamlit_app.py`: Main UI interface
   - Features:
     - Responsive design for mobile/PC
     - Real-time game state updates
     - Interactive question/answer interface
     - Score tracking and leaderboard display
     - Share card generation and social sharing

2. **Backend**
   - `backend/word_selector.py`:
     - Integrates with OpenRouter API for Gemini Pro access
     - Implements retry logic with exponential backoff
     - Provides local fallback dictionary
     - Handles word selection based on category/length
     - Processes yes/no questions
     - Validates responses and guesses
   
   - `backend/fallback_words.py`:
     - Local dictionary of words by category and length
     - Provides offline fallback support
     - Includes category aliases for flexibility
   
   - `backend/game_logic.py`:
     - Manages game state and rules
     - Implements scoring system
     - Tracks question history
     - Handles game progression
   
   - `backend/session_manager.py`:
     - Provides local/cloud storage abstraction
     - Manages game sessions and persistence
     - Handles leaderboard and user history
     - Encrypts hidden words during storage
     - Decrypts words only for completed games

   - `backend/share_card.py`:
     - Generates shareable game summary cards
     - Uses Pillow for image generation
     - Supports custom fonts and colors
     - Includes gradient backgrounds
     - Handles score color coding
     - Integrates QR codes for game links
     - Provides social media sharing options

   - `backend/share_utils.py`:
     - Manages share URL generation
     - Handles QR code creation
     - Formats social media share text
     - Generates unique share IDs
     - Manages output directories

3. **Configuration**
   - `config/openrouter_config.py`:
     - API configuration and credentials
     - Game settings and constants
     - Environment variable management

### Data Flow

1. **Game Initialization**
   ```mermaid
   sequenceDiagram
       participant User
       participant UI
       participant GameLogic
       participant WordSelector
       participant Gemini
       participant Fallback
       
       User->>UI: Start New Game
       UI->>GameLogic: Initialize(settings)
       GameLogic->>WordSelector: select_word()
       WordSelector->>Gemini: Generate Word
       alt API Success
           Gemini-->>WordSelector: Word
       else API Failure (3 retries)
           WordSelector->>Fallback: get_fallback_word()
           Fallback-->>WordSelector: Word
       end
       WordSelector-->>GameLogic: Word
       GameLogic-->>UI: Ready
   ```

2. **Question Flow**
   ```mermaid
   sequenceDiagram
       participant User
       participant UI
       participant GameLogic
       participant WordSelector
       participant Gemini
       participant Fallback
       
       User->>UI: Ask Question
       UI->>GameLogic: ask_question()
       GameLogic->>WordSelector: answer_question()
       WordSelector->>Gemini: Process Question
       alt API Success
           Gemini-->>WordSelector: Yes/No/Invalid
       else API Failure (3 retries)
           WordSelector->>Fallback: Simple Logic
           Fallback-->>WordSelector: Yes/No/Invalid
       end
       WordSelector-->>GameLogic: Response
       GameLogic-->>UI: Update Score
   ```

## API Integration

### OpenRouter/Gemini Pro

1. **Retry Logic**
   ```python
   def _make_api_request(self, data: dict, retry_count: int = 0) -> dict:
       try:
           response = requests.post(url, headers=headers, json=data, timeout=10)
           response.raise_for_status()
           return response.json()
       except Exception as e:
           if retry_count >= self.max_retries:
               raise
           backoff = self.initial_backoff * (2 ** retry_count)
           jitter = random.uniform(0, 0.1 * backoff)
           time.sleep(backoff + jitter)
           return self._make_api_request(data, retry_count + 1)
   ```

2. **Word Selection Prompt**
   ```python
   prompt = f"""
   Choose a {word_length}-letter English word under the subject '{subject}'.
   Only respond with 'yes' or 'no' to questions about the word. 
   Mark vague or irrelevant questions as 'no'.
   Do not reveal the word unless explicitly asked for final verification.
   """
   ```

3. **Question Handling**
   ```python
   prompt = f"""
   The word is '{word}'.
   Question: {question}
   Respond with ONLY 'yes' or 'no'. If the question is vague, irrelevant, 
   or would directly reveal the word, respond with 'invalid'.
   """
   ```

### Fallback System

1. **Word Selection**
   ```python
   try:
       # Try API with retries
       word = api.select_word(length, subject)
   except Exception:
       # Fall back to local dictionary
       word = get_fallback_word(length, subject)
   ```

2. **Question Answering**
   ```python
   try:
       # Try API with retries
       answer = api.answer_question(word, question)
   except Exception:
       # Use simple fallback logic
       answer = fallback_answer_question(word, question)
   ```

3. **Category Mapping**
   ```python
   CATEGORY_ALIASES = {
       "Tech": "Science",
       "Movies": "General",
       "Music": "General",
       "Brands": "General",
       "History": "General",
       "Random": "General"
   }
   ```

### AWS Integration

1. **DynamoDB Schema**
   ```json
   {
     "session_id": "string (Primary Key)",
     "nickname": "string (Optional)",
     "timestamp": "string (ISO format)",
     "word_length": "number",
     "subject": "string",
     "mode": "string",
     "score": "number",
     "questions_asked": "list",
     "time_taken": "number",
     "game_over": "boolean",
     "word": "string (encrypted until game over)"
   }
   ```

### Word Encryption

1. **Key Generation**
   ```python
   # Generate encryption key using PBKDF2
   salt = b'word_guess_game'
   kdf = PBKDF2HMAC(
       algorithm=hashes.SHA256(),
       length=32,
       salt=salt,
       iterations=100000,
   )
   key = base64.urlsafe_b64encode(kdf.derive(b'default_key'))
   ```

2. **Storage Flow**
   ```mermaid
   sequenceDiagram
       participant Game
       participant SessionManager
       participant Storage
       
       Game->>SessionManager: save_game(data)
       SessionManager->>SessionManager: encrypt_word()
       SessionManager->>Storage: store_encrypted_data()
       
       Game->>SessionManager: load_game(id)
       SessionManager->>Storage: load_encrypted_data()
       alt game is over
           SessionManager->>SessionManager: decrypt_word()
       end
       SessionManager->>Game: return data
   ```

## Game Logic

### Scoring System

1. **Challenge Mode**
   - Wrong question answer: +10 points
   - Wrong final guess: +10 points
   - Goal: Minimize score

2. **Fun Mode**
   - No scoring penalties
   - Track only question count and time

### Session Management

1. **Local Storage**
   - JSON files in `game_data/` directory
   - One file per game session
   - Filename format: `{nickname}_{timestamp}.json`
   - Words encrypted using Fernet symmetric encryption

2. **Cloud Storage**
   - DynamoDB table: `word_guess_games`
   - Automatic fallback to local storage on errors
   - Real-time leaderboard updates
   - Words encrypted before storage
   - Decryption only on game completion

## Example Game Session

```python
# Initialize game
game = GameLogic(word_length=5, subject="Animals", mode="Challenge")

# Ask questions
game.ask_question("Is it a mammal?")  # (True, "yes", 0)
game.ask_question("Does it fly?")      # (True, "no", 10)
game.ask_question("Is it a pet?")      # (True, "yes", 0)

# Make guess
result = game.make_guess("horse")      # (False, "Wrong! The word was 'mouse'", 10)

# Get summary
summary = game.get_game_summary()
"""
{
    "word_length": 5,
    "subject": "Animals",
    "mode": "Challenge",
    "score": 20,
    "questions_asked": [
        {"question": "Is it a mammal?", "answer": "yes", "points_added": 0},
        {"question": "Does it fly?", "answer": "no", "points_added": 10},
        {"question": "Is it a pet?", "answer": "yes", "points_added": 0}
    ],
    "time_taken": 45.2,
    "game_over": true,
    "word": "mouse"  # Decrypted after game over
}
"""
```

## Deployment Notes

### Local Development
1. Set up Python virtual environment
2. Install dependencies from `requirements.txt`
3. Create `.env` file with required credentials
4. Run with `streamlit run streamlit_app.py`

### Cloud Deployment (AWS)
1. Create DynamoDB table
2. Configure AWS credentials
3. Deploy frontend to Streamlit Cloud:
   ```bash
   streamlit deploy streamlit_app.py
   ```

### Environment Variables
```env
OPENROUTER_API_KEY=required
AWS_ACCESS_KEY_ID=optional
AWS_SECRET_ACCESS_KEY=optional
AWS_REGION=optional
USE_CLOUD_STORAGE=optional
WORD_ENCRYPTION_KEY=optional  # Auto-generated if not provided
```

## Future Enhancements

1. **Multiplayer Mode**
   - Real-time competition
   - Shared word between players
   - Race to guess first

2. **Advanced AI Features**
   - Word difficulty prediction
   - Question suggestion system
   - Learning from player strategies

3. **Enhanced UI**
   - Word category icons
   - Progress visualization
   - Animated celebrations
   - Social sharing cards

4. **Analytics**
   - Player performance tracking
   - Question effectiveness analysis
   - Category difficulty ratings 

## Testing

### Test Structure

The project uses pytest for testing, with the following test categories:
- Unit tests (`@pytest.mark.unit`): Test individual components in isolation
- Integration tests (`@pytest.mark.integration`): Test component interactions
- API tests (`@pytest.mark.api`): Test external API interactions
- Local storage tests (`@pytest.mark.local`): Test local file operations
- Cloud storage tests (`@pytest.mark.cloud`): Test AWS DynamoDB operations

### Test Files

1. `tests/test_word_selector.py`:
   - Tests word selection logic
   - Mocks OpenRouter API calls
   - Tests fallback dictionary usage
   - Tests question answering logic
   - Tests retry mechanism

2. `tests/test_game_logic.py`:
   - Tests game initialization
   - Tests scoring system
   - Tests game state management
   - Tests question tracking
   - Tests game modes (Challenge/Fun)

3. `tests/test_session_manager.py`:
   - Tests local storage operations
   - Tests cloud storage operations
   - Tests encryption/decryption
   - Tests storage fallback mechanism
   - Tests leaderboard functionality

### Running Tests

1. Install test dependencies:
   ```bash
   pip install -r tests/requirements-test.txt
   ```

2. Run all tests:
   ```bash
   pytest
   ```

3. Run specific test categories:
   ```bash
   pytest -m unit  # Run unit tests only
   pytest -m integration  # Run integration tests only
   pytest -m "not cloud"  # Skip cloud tests
   ```

4. Run with coverage:
   ```bash
   pytest --cov=backend tests/
   ```

### Test Configuration

The `pytest.ini` file configures test discovery and markers:
```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = -v --tb=short
markers =
    unit: Unit tests
    integration: Integration tests
    api: Tests that make API calls
    local: Tests for local storage
    cloud: Tests for cloud storage
```

### Mocking

1. API Calls:
   ```python
   @patch('requests.post')
   def test_api_call(mock_post):
       mock_post.return_value.json.return_value = {"choices": [...]}
   ```

2. AWS Services:
   ```python
   @mock_dynamodb
   def test_aws_operation():
       # moto library handles AWS mocking
   ```

3. Environment Variables:
   ```python
   with patch.dict('os.environ', {'KEY': 'value'}):
       # Test with mocked environment
   ```

### Test Data

Test fixtures provide common test data and setup:
```python
@pytest.fixture
def sample_game_data():
    return {
        "session_id": "test_123",
        "word": "mouse",
        # ... other game data ...
    }
```

### Best Practices

1. Use markers to categorize tests
2. Mock external dependencies
3. Use fixtures for common setup
4. Clean up test data after tests
5. Test both success and failure cases
6. Test edge cases and invalid inputs
7. Keep tests focused and independent
8. Use meaningful test names
9. Add comments for complex test logic
10. Maintain test data separate from production 

## Share Card System

### Share Card Generation

1. **Card Components**
   ```python
   class ShareCardGenerator:
       def __init__(self):
           self.colors = {
               'background': (245, 247, 250),  # Light blue-gray
               'text': (33, 33, 33),          # Dark gray
               'accent': (0, 121, 107),       # Teal
               'score': {
                   'good': (76, 175, 80),     # Green
                   'medium': (255, 152, 0),    # Orange
                   'bad': (244, 67, 54)       # Red
               }
           }
           self.dimensions = {
               'width': 800,
               'height': 400,
               'padding': 40,
               'border_radius': 20
           }
   ```

2. **Share URL Generation**
   ```python
   def create_share_url(self, game_summary: Dict) -> str:
       share_id = self.generate_share_id(game_summary)
       params = {
           'w': game_summary['word'],
           'c': game_summary['category'],
           's': str(game_summary['score']),
           'm': game_summary['mode'],
           't': str(int(game_summary['duration']))
       }
       return f"{self.base_url}/share/{share_id}?{urlencode(params)}"
   ```

3. **QR Code Integration**
   ```python
   def generate_qr_code(self, game_summary: Dict) -> str:
       share_url = self.create_share_url(game_summary)
       qr = qrcode.QRCode(
           version=1,
           error_correction=qrcode.constants.ERROR_CORRECT_L,
           box_size=8,
           border=1
       )
       qr.add_data(share_url)
       qr.make(fit=True)
       return qr.make_image()
   ```

4. **Social Media Integration**
   ```mermaid
   sequenceDiagram
       participant User
       participant UI
       participant ShareCard
       participant ShareUtils
       participant SocialMedia
       
       User->>UI: Click Share
       UI->>ShareCard: Generate Card
       ShareCard->>ShareUtils: Create Share URL
       ShareUtils->>ShareCard: URL + QR Code
       ShareCard-->>UI: Share Card Image
       User->>UI: Click Social Share
       UI->>ShareUtils: Get Share Text
       ShareUtils-->>UI: Formatted Text
       UI->>SocialMedia: Open Share Dialog
   ```

5. **Share Card Flow**
   ```mermaid
   sequenceDiagram
       participant User
       participant UI
       participant ShareCard
       participant Storage
       
       User->>UI: Complete Game
       UI->>ShareCard: Generate Card
       ShareCard->>Storage: Save Image
       Storage-->>UI: Image Path
       UI->>User: Display Preview
       User->>UI: Download/Share
       UI-->>User: Share Options
   ```

### Share Card Features

1. **Visual Elements**
   - Gradient background with rounded corners
   - Game title with shadow effect
   - Word and category display
   - Score with color-coded feedback
   - Game duration and mode
   - Optional player nickname
   - QR code for easy access
   - "Scan to play" call-to-action

2. **Social Sharing**
   - Twitter/X integration
   - Facebook sharing
   - LinkedIn posting
   - Direct link copying
   - Download as PNG

3. **Performance Optimizations**
   - Font caching
   - Image quality settings
   - QR code size optimization
   - Output directory management
   - Error handling and recovery

4. **Security Features**
   - Share ID hashing
   - URL-safe encoding
   - Parameter validation
   - File path sanitization
   - Error logging

// ... rest of existing code ... 