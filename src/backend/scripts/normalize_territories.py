
import asyncio
import json
import re
import time
from typing import List, Dict, Any, Optional
from loguru import logger
import pgeocode
from google import genai
from google.genai import types

from src.api.config.supabase_config import supabase_client
from src.api.genai_gemini import generate
from src.api.config.genai_gemini_config import CLIENT, MODEL_FLASH, get_generate_content_config_keywords

# Initialize pgeocode for US
nomi = pgeocode.Nominatim('us')
dist = pgeocode.GeoDistance('us')

async def fetch_unprocessed_territories(limit: int = 50):
    """Fetch territory checks that haven't been normalized (missing zip_code AND city)."""
    # Only fetch rows where BOTH city and zip_code are null (unprocessed)
    # This ensures we skip rows that were already processed, even if zip_code wasn't found
    response = supabase_client().table("territory_checks") \
        .select("id, location_raw, state_code") \
        .is_("zip_code", "null") \
        .is_("city", "null") \
        .limit(limit) \
        .execute()
    return response.data

async def extract_location_details(location_raw: str, state_context: str) -> Dict[str, Any]:
    """Use LLM to extract structured location data from raw text."""
    
    prompt = f"""
    You are a location extraction specialist. Extract structured geographic data from the following territory description.
    The context is checking franchise availability in the US.
    
    Input Text: "{location_raw}"
    State Context: "{state_context}"
    
    Return a JSON object with these fields:
    - city: (string) The primary city mentioned.
    - state_code: (string) 2-letter US state code (e.g., TX, SC). If missing, infer from context.
    - zip_code: (string) The primary zip code if explicitly stated, otherwise null.
    - radius_miles: (number) If a radius is mentioned (e.g., "30 miles around"), extract the number. Otherwise null.
    - is_entire_state: (boolean) True if it refers to the whole state.
    
    Example 1: "Taylor's SC 29687 and up to 30 miles"
    Output: {{ "city": "Taylors", "state_code": "SC", "zip_code": "29687", "radius_miles": 30, "is_entire_state": false }}

    Example 2: "Charlotte area"
    Output: {{ "city": "Charlotte", "state_code": "NC", "zip_code": null, "radius_miles": 25, "is_entire_state": false }} 
    (Note: Default small radius for "area" if vague, or leave null if strictly city)

    Example 3: "All of New Jersey"
    Output: {{ "city": null, "state_code": "NJ", "zip_code": null, "radius_miles": null, "is_entire_state": true }}

    Return ONLY the valid JSON object.
    """
    
    try:
        parts = [types.Part(text=prompt)]
        config = get_generate_content_config_keywords()
        
        # Add delay for rate limits (Gemini free tier is ~15 RPM)
        await asyncio.sleep(4) 
        
        response = generate(
            client=CLIENT,
            model=MODEL_FLASH,
            parts=parts,
            generate_content_config=config
        )
        
        text = response.text
        # Clean up potential markdown formatting
        clean_json = text.replace('```json', '').replace('```', '').strip()
        return json.loads(clean_json)
    except Exception as e:
        # If we hit rate limit, log it but don't crash the whole batch
        logger.error(f"LLM Extraction failed for '{location_raw}': {e}")
        if "429" in str(e):
            logger.warning("Rate limit hit. Sleeping for 30 seconds...")
            await asyncio.sleep(30)
        return {}

# Improved Geocoding Strategy using pgeocode properly
def get_lat_lon_from_zip(zip_code: str):
    geo = nomi.query_postal_code(zip_code)
    if not geo.empty and str(geo.latitude) != 'nan':
        return float(geo.latitude), float(geo.longitude), geo.place_name, geo.state_code
    return None, None, None, None

def is_valid_city_name(city: str) -> bool:
    """Validate that a city name is not purely numeric."""
    if not city:
        return False
    return not bool(re.match(r'^[0-9]+$', str(city).strip()))


async def process_batch():
    items = await fetch_unprocessed_territories(limit=50)
    if not items:
        logger.info("No unprocessed items found.")
        return

    logger.info(f"Processing {len(items)} locations...")
    
    for item in items:
        raw = item['location_raw']
        ctx_state = item['state_code']
        
        # 1. LLM Extract
        extracted = await extract_location_details(raw, ctx_state)
        
        if not extracted:
            continue

        zip_code = extracted.get('zip_code')
        city = extracted.get('city')
        state = extracted.get('state_code')
        radius = extracted.get('radius_miles')
        
        lat, lon = None, None
        
        # 2. Geocode
        # If we have a zip, use it
        if zip_code:
            lat, lon, place_name, state_res = get_lat_lon_from_zip(zip_code)
            if not city and place_name and is_valid_city_name(place_name):
                city = place_name
        
        # Validate city before storing (reject numeric-only values)
        if city and not is_valid_city_name(city):
            logger.warning(f"Rejected numeric city value '{city}' for location '{raw}'")
            city = None
        
        # If no zip but we have city/state, we need a zip to get lat/lon via pgeocode
        # We can't easily do City -> Zip with pgeocode alone.
        # IMPROVEMENT: Ask LLM to provide a "central zip" for the city in the first step.
        
        # 3. Update DB
        update_data = {
            "city": city,
            "zip_code": zip_code,
            "latitude": lat,
            "longitude": lon,
            "radius_miles": radius
            # "covered_zips": [] # Omitted for now as calculation is heavy
        }
        
        try:
            supabase_client().table("territory_checks") \
                .update(update_data) \
                .eq("id", item['id']) \
                .execute()
            logger.success(f"Updated {item['id']}: {city}, {state} ({zip_code})")
        except Exception as e:
            logger.error(f"DB Update failed for {item['id']}: {e}")

if __name__ == "__main__":
    import pandas as pd # pgeocode dependency
    asyncio.run(process_batch())
