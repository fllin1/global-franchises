import json
import asyncio
from typing import List, Dict, Any
from loguru import logger
from google.genai import types

from src.api.config.genai_gemini_config import CLIENT, MODEL_PRO
from src.api.genai_gemini import generate
from src.backend.models import LeadProfile

async def generate_match_narratives(profile: LeadProfile, matches: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Generates a personalized 'why this fits' narrative for a list of franchise matches
    based on the lead's profile.
    
    Args:
        profile (LeadProfile): The candidate's extracted profile.
        matches (List[Dict]): The list of franchise dictionaries from the hybrid search.
        
    Returns:
        Dict[int, str]: A dictionary mapping franchise ID to its narrative string.
    """
    if not matches:
        return {}

    # Prepare a simplified list of matches for the prompt to save tokens
    candidates_summary = []
    for m in matches:
        candidates_summary.append({
            "id": m['id'],
            "name": m['franchise_name'],
            "category": m.get('primary_category'),
            "description": m.get('description_text', '')[:200] + "..." # Truncate description
        })

    prompt = f"""
    You are an expert Franchise Consultant. 
    
    Candidate Profile:
    - Search Intent: {profile.semantic_query}
    - Location: {profile.location or 'Flexible'}
    - Budget/Liquidity: {profile.effective_budget or 'Unknown'}
    
    Here are {len(candidates_summary)} franchise recommendations I found for them. 
    For EACH franchise, write a short, persuasive 1-2 sentence "Match Narrative" explaining SPECIFICALLY why this brand fits this candidate's profile.
    
    Focus on connecting the candidate's intent (keywords, interests) to the franchise's offering.
    
    Franchise Candidates:
    {json.dumps(candidates_summary, indent=2)}
    
    Output must be a JSON object with a "narratives" array, containing objects with "franchise_id" and "narrative".
    """

    schema = {
        "type": "OBJECT",
        "properties": {
            "narratives": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "franchise_id": {"type": "INTEGER"},
                        "narrative": {"type": "STRING"}
                    },
                    "required": ["franchise_id", "narrative"]
                }
            }
        },
        "required": ["narratives"]
    }

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7, # Slightly creative for sales copy
        top_p=0.95,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=schema,
    )

    retries = 3
    for attempt in range(retries):
        try:
            logger.info(f"Generating narratives (Attempt {attempt+1}/{retries})...")
            response = generate(
                client=CLIENT,
                model=MODEL_PRO,
                parts=[types.Part(text=prompt)],
                generate_content_config=generate_content_config
            )
            
            # Check if response has text (generate() asserts this, but we catch it)
            if not response.text:
                logger.warning(f"Gemini returned empty response text. Finish reason: {response.candidates[0].finish_reason if response.candidates else 'Unknown'}")
                raise ValueError("Empty response from Gemini")

            # Parse JSON response
            data = json.loads(response.text)
            narratives_list = data.get("narratives", [])
            narratives = {item["franchise_id"]: item["narrative"] for item in narratives_list}
            
            return narratives

        except Exception as e:
            error_msg = str(e) or repr(e)
            logger.error(f"Error generating narratives (Attempt {attempt+1}): {error_msg}")
            
            # Retry on Overload, Timeout, or Empty Response (AssertionError/ValueError)
            is_transient = (
                "503" in error_msg or 
                "overloaded" in error_msg.lower() or 
                "deadline" in error_msg.lower() or
                "AssertionError" in error_msg or
                "Empty response" in error_msg
            )
            
            if is_transient and attempt < retries - 1:
                wait_time = 2 ** attempt
                logger.warning(f"Transient error detected, retrying in {wait_time} seconds...")
                await asyncio.sleep(wait_time)
            else:
                if not is_transient:
                     break # Don't retry on permanent errors (like Bad Request)
    
    return {} # Fail gracefully
