import asyncio
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from src.ghl.utils.template_matcher import is_template_message
from src.ghl.utils.message_classifier import classify_message
from src.ghl.utils.territory_extractor import extract_territories

# --- Template Matcher Tests ---
def test_is_template_message_exact():
    msg = "Hi John, Nice seeing you at the convention. Is it possible to mail me available territories and the hot markets to present to my clients please. Thank you Best, Manoj Soans"
    assert is_template_message(msg) is True

def test_is_template_message_variation():
    msg = "Hello Jane,\n\nIs it possible to mail me available territories and the hot markets to present to my clients please.\n\nThank you Best, Manoj Soans"
    assert is_template_message(msg) is True

def test_is_template_message_negative():
    msg = "This is a genuine reply about territory availability in Texas."
    assert is_template_message(msg) is False

def test_is_template_message_empty():
    assert is_template_message("") is False

# --- Message Classifier Tests ---
def test_classify_message_ooo():
    mock_response = MagicMock()
    mock_response.text = '{"is_out_of_office": true, "has_attachment_mention": false}'
    
    async def run_test():
        with patch('src.ghl.utils.message_classifier.generate', return_value=mock_response):
            result = await classify_message("I am out of office until next Monday.")
            assert result["is_out_of_office"] is True
            assert result["has_attachment_mention"] is False
            
    asyncio.run(run_test())

def test_classify_message_attachment():
    mock_response = MagicMock()
    mock_response.text = '{"is_out_of_office": false, "has_attachment_mention": true}'
    
    async def run_test():
        with patch('src.ghl.utils.message_classifier.generate', return_value=mock_response):
            result = await classify_message("Please see the attached PDF for available areas.")
            assert result["is_out_of_office"] is False
            assert result["has_attachment_mention"] is True

    asyncio.run(run_test())

# --- Territory Extractor Tests ---
def test_extract_territories_valid():
    mock_response = MagicMock()
    mock_response.text = '''
    {
        "territories": [
            {
                "location_raw": "Austin, TX",
                "state_code": "TX",
                "availability_status": "Available",
                "check_date": null
            },
            {
                "location_raw": "Dallas",
                "state_code": "TX",
                "availability_status": "Not Available",
                "check_date": "2025-01-01"
            }
        ]
    }
    '''
    
    async def run_test():
        with patch('src.ghl.utils.territory_extractor.generate', return_value=mock_response):
            territories = await extract_territories("Austin is open, but Dallas is taken.")
            assert len(territories) == 2
            assert territories[0]["location_raw"] == "Austin, TX"
            assert territories[1]["availability_status"] == "Not Available"

    asyncio.run(run_test())

def test_extract_territories_empty_response():
    mock_response = MagicMock()
    mock_response.text = '{"territories": []}'
    
    async def run_test():
        with patch('src.ghl.utils.territory_extractor.generate', return_value=mock_response):
            territories = await extract_territories("Just saying hello.")
            assert len(territories) == 0

    asyncio.run(run_test())

