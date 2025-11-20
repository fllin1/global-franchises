import json
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from google.genai import types

from src.api.config.genai_gemini_config import CLIENT, MODEL_PRO
from src.api.genai_gemini import generate

async def extract_territories(body_clean: str) -> List[Dict[str, Any]]:
    """
    Extracts territory availability information from a message body.
    
    Args:
        body_clean: The cleaned message body text
        
    Returns:
        List of territory dictionaries matching the territory_checks schema:
        [
            {
                "location_raw": "El Paso, TX",
                "state_code": "TX",
                "availability_status": "Available" | "Not Available" | "Pending",
                "check_date": "YYYY-MM-DD" (optional)
            },
            ...
        ]
    """
    if not body_clean or len(body_clean.strip()) < 10:
        return []

    prompt = f"""
    You are a data extraction assistant. Extract territory availability information from the following franchise inquiry reply.
    
    The sender is replying to a request about available territories.
    Extract every mentioned territory/location and its availability status.
    
    Rules:
    1. location_raw: The full location string as written (e.g., "Austin, TX", "Miami area", "All of New Jersey").
    2. state_code: The 2-letter US state code if identifiable (e.g., "TX", "FL", "NJ"). If multiple states, use the first one. If none, null.
    3. availability_status: Must be one of: "Available", "Not Available", "Pending".
       - "Available": Explicitly stated as open, available, needing a franchisee.
       - "Not Available": Stated as sold, taken, reserved, unavailable.
       - "Pending": Stated as under contract, in discussion, reserved but not finalized.
    4. check_date: If a date is mentioned in relation to the check (e.g. "As of 10/25..."), extract as YYYY-MM-DD. Otherwise null.
    
    Message Body:
    "{body_clean}"
    
    Output JSON object with a "territories" list.
    """
    
    schema = {
        "type": "OBJECT",
        "properties": {
            "territories": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "location_raw": {"type": "STRING"},
                        "state_code": {"type": "STRING", "nullable": True},
                        "availability_status": {
                            "type": "STRING",
                            "enum": ["Available", "Not Available", "Pending"]
                        },
                        "check_date": {"type": "STRING", "nullable": True}
                    },
                    "required": ["location_raw", "availability_status"]
                }
            }
        },
        "required": ["territories"]
    }
    
    generate_content_config = types.GenerateContentConfig(
        temperature=0.1,
        top_p=0.95,
        response_mime_type="application/json",
        response_schema=schema,
    )
    
    retries = 3
    for attempt in range(retries):
        try:
            response = generate(
                client=CLIENT,
                model=MODEL_PRO,
                parts=[types.Part(text=prompt)],
                generate_content_config=generate_content_config
            )
            
            if not response.text:
                logger.warning("Empty response from Gemini territory extractor")
                raise ValueError("Empty response")
                
            result = json.loads(response.text)
            return result.get("territories", [])
            
        except Exception as e:
            logger.warning(f"Error extracting territories (Attempt {attempt+1}/{retries}): {e}")
            if attempt < retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
            else:
                logger.error(f"Failed to extract territories after {retries} attempts")
                return []
