import json
import asyncio
from typing import Optional
from google.genai import types
from loguru import logger

from src.api.config.genai_gemini_config import CLIENT, MODEL_PRO
from src.api.genai_gemini import generate
from src.backend.models import LeadProfile

async def extract_profile_from_notes(notes: str) -> LeadProfile:
    """
    Extracts structured LeadProfile data from raw broker notes using Gemini.
    
    Args:
        notes (str): The raw notes text from the broker.
        
    Returns:
        LeadProfile: The extracted and synthesized profile.
    """
    
    prompt = f"""
    You are an expert Franchise Broker Assistant. Your task is to extract structured data from the following broker notes about a potential franchisee lead.
    
    Raw Notes:
    "{notes}"
    
    You need to extract/generate the following categories of information. If a value is not explicitly stated or reasonably inferred, return null.

    1. **General:**
       - candidate_name: Name of the candidate.
       - semantic_query: A synthesized natural language search query capturing intent, background, and preferences.

    2. **Money:**
       - liquidity: Liquid capital (cash) available (USD integer).
       - net_worth: Total net worth (USD integer).
       - investment_cap: Max investment budget (USD integer).
       - investment_source: Source of funds (e.g., "401k rollover", "SBA loan", "HELOC").
       - interest: Any specific financial notes or credit score info (string).

    3. **Territories:**
       - territories: List of preferred territories. Each item should have 'location' (e.g. "Austin, TX") and 'state_code' (e.g. "TX").
       - location: Primary location string (legacy support).
       - state_code: Primary state code (legacy support).

    4. **Interest & Preferences:**
       - home_based_preference: Boolean, prefers home-based?
       - absentee_preference: Boolean, prefers absentee?
       - semi_absentee_preference: Boolean, prefers semi-absentee?
       - role_preference: e.g. "Owner-Operator", "Semi-Absentee", "Absentee", "Executive".
       - business_model_preference: e.g. "B2B", "B2C".
       - staff_preference: e.g. "No Staff", "Small Staff", "Manager Run".
       - franchise_categories: Array of strings, specific industries of interest (e.g. "Fitness", "Senior Care").
       - multi_unit_preference: Boolean, interested in owning multiple units?

    5. **Motives & Goals:**
       - trigger_event: Why are they looking now? (e.g. "Layoff", "Retirement").
       - current_status: Current employment status (e.g. "Employed", "Unemployed").
       - experience_level: e.g. "First-time", "Serial Entrepreneur", "Investor".
       - goals: Array of strings, key objectives (e.g. "Wealth Building", "Legacy", "Time Freedom").
       - timeline: When they want to start (e.g. "ASAP", "3-6 months").
    
    Output must be valid JSON matching the specified schema.
    """

    # Define the JSON schema for structured output
    schema = {
        "type": "OBJECT",
        "properties": {
            # General
            "candidate_name": {"type": "STRING", "nullable": True},
            "semantic_query": {"type": "STRING"},
            
            # Money
            "liquidity": {"type": "INTEGER", "nullable": True},
            "net_worth": {"type": "INTEGER", "nullable": True},
            "investment_cap": {"type": "INTEGER", "nullable": True},
            "investment_source": {"type": "STRING", "nullable": True},
            "interest": {"type": "STRING", "nullable": True},

            # Territories
            "location": {"type": "STRING", "nullable": True},
            "state_code": {"type": "STRING", "nullable": True},
            "territories": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "location": {"type": "STRING"},
                        "state_code": {"type": "STRING", "nullable": True}
                    }
                },
                "nullable": True
            },

            # Interest
            "home_based_preference": {"type": "BOOLEAN", "nullable": True},
            "absentee_preference": {"type": "BOOLEAN", "nullable": True},
            "semi_absentee_preference": {"type": "BOOLEAN", "nullable": True},
            "role_preference": {"type": "STRING", "nullable": True},
            "business_model_preference": {"type": "STRING", "nullable": True},
            "staff_preference": {"type": "STRING", "nullable": True},
            "franchise_categories": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "nullable": True
            },
            "multi_unit_preference": {"type": "BOOLEAN", "nullable": True},

            # Motives
            "trigger_event": {"type": "STRING", "nullable": True},
            "current_status": {"type": "STRING", "nullable": True},
            "experience_level": {"type": "STRING", "nullable": True},
            "goals": {
                "type": "ARRAY",
                "items": {"type": "STRING"},
                "nullable": True
            },
            "timeline": {"type": "STRING", "nullable": True}
        },
        "required": ["semantic_query"]
    }

    generate_content_config = types.GenerateContentConfig(
        temperature=0.1, 
        top_p=0.95,
        max_output_tokens=2048, # Increased for larger JSON
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
                logger.error("Gemini returned empty response")
                raise ValueError("Failed to extract profile: Empty response from LLM")
                
            data = json.loads(response.text)

            # Fallback logic for state_code if missing but location exists
            if not data.get('state_code') and data.get('location'):
                loc_lower = data['location'].lower()
                state_map = {
                    "california": "CA", "texas": "TX", "florida": "FL", "new york": "NY",
                    "illinois": "IL", "pennsylvania": "PA", "ohio": "OH", "georgia": "GA",
                    "north carolina": "NC", "michigan": "MI", "new jersey": "NJ", "virginia": "VA",
                    "washington": "WA", "arizona": "AZ", "massachusetts": "MA", "tennessee": "TN",
                    "indiana": "IN", "missouri": "MO", "maryland": "MD", "wisconsin": "WI",
                    "colorado": "CO", "minnesota": "MN", "south carolina": "SC", "alabama": "AL",
                    "louisiana": "LA", "kentucky": "KY", "oregon": "OR", "oklahoma": "OK"
                }
                for state_name, code in state_map.items():
                    if state_name in loc_lower:
                        data['state_code'] = code
                        break
            
            # Fallback: populate legacy location fields if territories exist but top-level is empty
            if not data.get('location') and data.get('territories'):
                first_terr = data['territories'][0]
                data['location'] = first_terr.get('location')
                if not data.get('state_code'):
                    data['state_code'] = first_terr.get('state_code')

            logger.info(f"Extracted profile data: {data}")
            
            return LeadProfile(**data)
            
        except Exception as e:
            error_msg = str(e) or repr(e)
            logger.error(f"Error extracting profile with Gemini (Attempt {attempt+1}): {error_msg}")
            
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
                if not is_transient or attempt == retries - 1:
                    raise e
    
    raise Exception("Failed to extract profile after retries")
