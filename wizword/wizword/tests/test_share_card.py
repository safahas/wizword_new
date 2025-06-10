import os
import pytest
from PIL import Image
from backend.share_card import ShareCardGenerator, create_share_card

@pytest.fixture
def share_card_generator():
    return ShareCardGenerator()

@pytest.fixture
def sample_game_summary():
    return {
        "word": "mouse",
        "subject": "Animals",
        "score": 10,
        "time_taken": 65.5,
        "mode": "Challenge"
    }

@pytest.fixture
def cleanup_share_cards():
    # Ensure directory exists
    os.makedirs('game_data/share_cards', exist_ok=True)
    yield
    # Cleanup generated share cards after tests
    share_cards_dir = 'game_data/share_cards'
    if os.path.exists(share_cards_dir):
        for file in os.listdir(share_cards_dir):
            if file.startswith('share_card_') or file == 'custom_card.png':
                os.remove(os.path.join(share_cards_dir, file))

@pytest.mark.unit
def test_share_card_generator_initialization(share_card_generator):
    assert os.path.exists(share_card_generator.template_path)
    assert share_card_generator.title_size == 48
    assert share_card_generator.subtitle_size == 36
    assert share_card_generator.text_size == 24

@pytest.mark.unit
def test_format_duration(share_card_generator):
    assert share_card_generator._format_duration(65.5) == "1m 5s"
    assert share_card_generator._format_duration(3600) == "60m 0s"
    assert share_card_generator._format_duration(45) == "0m 45s"

@pytest.mark.integration
def test_generate_share_card(share_card_generator, cleanup_share_cards):
    output_path = share_card_generator.generate_share_card(
        word="mouse",
        category="Animals",
        score=10,
        duration=65.5,
        mode="Challenge"
    )
    
    assert os.path.exists(output_path)
    assert output_path.endswith('share_card_mouse.png')
    
    # Verify image properties
    with Image.open(output_path) as img:
        assert img.mode == "RGB"
        assert img.size == (800, 400)

@pytest.mark.integration
def test_create_share_card_from_summary(sample_game_summary, cleanup_share_cards):
    output_path = create_share_card(sample_game_summary)
    
    assert os.path.exists(output_path)
    assert output_path.endswith('share_card_mouse.png')
    
    # Verify image was created correctly
    with Image.open(output_path) as img:
        assert img.mode == "RGB"
        assert img.size == (800, 400)

@pytest.mark.unit
def test_custom_output_path(share_card_generator, cleanup_share_cards):
    custom_path = "game_data/share_cards/custom_card.png"
    output_path = share_card_generator.generate_share_card(
        word="mouse",
        category="Animals",
        score=10,
        duration=65.5,
        mode="Challenge",
        output_path=custom_path
    )
    
    assert output_path == custom_path
    assert os.path.exists(custom_path)

@pytest.mark.unit
def test_font_fallback(share_card_generator):
    # Test with non-existent font paths
    share_card_generator.font_path = "nonexistent.ttf"
    share_card_generator.font_bold_path = "nonexistent_bold.ttf"
    
    fonts = share_card_generator._load_fonts()
    assert all(font is not None for font in fonts.values()) 