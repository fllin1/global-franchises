from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock
import pytest
from src.backend.main import app
from src.backend.models import LeadProfile

client = TestClient(app)

# Mock data
mock_profile_data = {
    "liquidity": 100000,
    "investment_cap": 200000,
    "location": "Austin, TX",
    "state_code": "TX",
    "semantic_query": "fitness franchise in Austin"
}

mock_matches = [
    {
        "id": 1,
        "franchise_name": "FitBody Boot Camp",
        "primary_category": "Fitness",
        "description_text": "Group personal training.",
        "similarity": 0.9,
        "total_investment_min_usd": 150000
    }
]

mock_narratives = {
    1: "Great fit for your budget and interest in fitness."
}

@patch("src.backend.main.extract_profile_from_notes", new_callable=AsyncMock)
@patch("src.backend.main.hybrid_search", new_callable=AsyncMock)
@patch("src.backend.main.generate_match_narratives", new_callable=AsyncMock)
def test_analyze_lead_endpoint(mock_gen_narratives, mock_search, mock_extract):
    # Setup mocks
    mock_extract.return_value = LeadProfile(**mock_profile_data)
    mock_search.return_value = mock_matches
    mock_gen_narratives.return_value = mock_narratives
    
    response = client.post("/analyze-lead", json={"notes": "I want a fitness gym in Austin with 100k cash."})
    
    assert response.status_code == 200
    data = response.json()
    
    assert data["status"] == "complete"
    assert data["profile"]["semantic_query"] == "fitness franchise in Austin"
    assert len(data["matches"]) == 1
    assert data["matches"][0]["why_narrative"] == "Great fit for your budget and interest in fitness."
    assert "coaching_questions" in data

@patch("src.backend.main.search_franchises_by_state", new_callable=AsyncMock)
def test_get_franchises_by_location_endpoint(mock_search_state):
    mock_search_state.return_value = mock_matches
    
    response = client.get("/api/franchises/by-location?state_code=TX")
    
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["franchise_name"] == "FitBody Boot Camp"




