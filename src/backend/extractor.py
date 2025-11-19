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
    
    You need to extract/generate the following:
    1. liquidity: The specific amount of liquid capital (cash) they have available to invest. Return as an integer (USD).
    2. investment_cap: The maximum total investment budget they stated (e.g. "Max $200k"). Return as an integer (USD).
    3. location: The preferred location or territory. Return as a string.
    4. semantic_query: A synthesized, natural language search query that captures the essence of what the lead is looking for. This will be used for vector search against franchise descriptions. Include their background, interests, preferred business model (e.g. semi-absentee, owner-operator), and industry preferences if available. Make it descriptive.
    
    If a value is not explicitly stated or cannot be reasonably inferred, return null.
    
    Output must be valid JSON matching the specified schema.
    """

    # Define the JSON schema for structured output
    schema = {
        "type": "OBJECT",
        "properties": {
            "liquidity": {"type": "INTEGER", "nullable": True},
            "investment_cap": {"type": "INTEGER", "nullable": True},
            "location": {"type": "STRING", "nullable": True},
            "semantic_query": {"type": "STRING"},
        },
        "required": ["semantic_query"]
    }

    generate_content_config = types.GenerateContentConfig(
        temperature=0.1, # Low temperature for extraction
        top_p=0.95,
        max_output_tokens=1024,
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
            logger.info(f"Extracted profile data: {data}")
            
            return LeadProfile(**data)
            
        except Exception as e:
            error_msg = str(e) or repr(e)
            logger.error(f"Error extracting profile with Gemini (Attempt {attempt+1}): {error_msg}")
            
            # Retry on Overload, Timeout, or Empty Response
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
