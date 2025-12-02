# -*- coding: utf-8 -*-
"""
LLM-based location parser for territory checks.

Parses raw location strings into structured geographic data:
- city, state, county, zip_code
- radius_miles (if specified)
- is_resale (if mentioned)
- country (US by default, CA for Canada, etc.)

Handles multi-location entries by splitting them into separate records.
Uses Gemini with structured output for reliable parsing.
"""

import asyncio
import argparse
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime

import pgeocode
from loguru import logger
from google.genai import types

from src.api.config.supabase_config import supabase_client
from src.api.config.genai_gemini_config import CLIENT, MODEL_FLASH
from src.api.genai_gemini import generate


# Initialize pgeocode for US zip lookups
_nomi_us = None
_nomi_ca = None


def _get_nomi_us():
    """Lazy initialization of pgeocode for US."""
    global _nomi_us
    if _nomi_us is None:
        _nomi_us = pgeocode.Nominatim('us')
    return _nomi_us


def _get_nomi_ca():
    """Lazy initialization of pgeocode for Canada."""
    global _nomi_ca
    if _nomi_ca is None:
        _nomi_ca = pgeocode.Nominatim('ca')
    return _nomi_ca


# Canadian province codes (set for validation)
CANADIAN_PROVINCE_CODES = {
    "AB", "BC", "MB", "NB", "NL", "NS", "NT", "NU", "ON", "PE", "QC", "SK", "YT",
}

# Full province names mapped to codes
CANADIAN_PROVINCE_NAMES = {
    "ALBERTA": "AB", "BRITISH COLUMBIA": "BC", "MANITOBA": "MB",
    "NEW BRUNSWICK": "NB", "NEWFOUNDLAND": "NL", "NOVA SCOTIA": "NS",
    "NORTHWEST TERRITORIES": "NT", "NUNAVUT": "NU", "ONTARIO": "ON",
    "PRINCE EDWARD ISLAND": "PE", "QUEBEC": "QC", "SASKATCHEWAN": "SK", "YUKON": "YT",
}

# US State codes for validation
US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC", "PR", "VI", "GU", "AS", "MP",
}


# JSON schema for LLM structured output
LOCATION_PARSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "locations": {
            "type": "ARRAY",
            "description": "List of parsed locations. Multiple entries if input contains multiple locations.",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "country": {
                        "type": "STRING",
                        "description": "ISO 3166-1 alpha-2 country code. 'US' for USA, 'CA' for Canada.",
                        "enum": ["US", "CA", "MX", "OTHER"],
                    },
                    "state_code": {
                        "type": "STRING",
                        "description": "2-letter state/province code (e.g., TX, CA, ON).",
                        "nullable": True,
                    },
                    "county": {
                        "type": "STRING",
                        "description": "County name without 'County' suffix. Null for Canada.",
                        "nullable": True,
                    },
                    "city": {
                        "type": "STRING",
                        "description": "City name. Null if only county/state specified.",
                        "nullable": True,
                    },
                    "zip_code": {
                        "type": "STRING",
                        "description": "ZIP/postal code. US: 5-digit. Canada: A1A1A1 format.",
                        "nullable": True,
                    },
                    "radius_miles": {
                        "type": "NUMBER",
                        "description": "Radius in miles if specified (e.g., '25 miles', '+ 50 Miles').",
                        "nullable": True,
                    },
                    "is_resale": {
                        "type": "BOOLEAN",
                        "description": "True if 'resale' is mentioned in the location.",
                    },
                },
                "required": ["country", "is_resale"],
            },
        },
    },
    "required": ["locations"],
}


def get_parse_location_config() -> types.GenerateContentConfig:
    """Get the Gemini config for location parsing."""
    return types.GenerateContentConfig(
        temperature=0.1,  # Low temperature for consistent parsing
        top_p=0.95,
        response_mime_type="application/json",
        response_schema=LOCATION_PARSE_SCHEMA,
    )


def build_parse_prompt(location_raw: str, state_context: Optional[str] = None) -> str:
    """Build the prompt for parsing a location string."""
    return f"""You are a geographic data extraction specialist. Parse the following territory location string into structured data.

INPUT: "{location_raw}"
STATE CONTEXT (if provided): "{state_context or 'None'}"

RULES:
1. **Multi-location detection**: If the input contains "or", "and", "&", or commas separating distinct locations, split into multiple location objects.
   - "Dallas or Amarillo, TX" → 2 locations: Dallas, TX and Amarillo, TX
   - "San Jose, CA and Dallas, TX" → 2 locations
   - "Summit & Cuyahoga County OH" → 2 counties

2. **Country detection**:
   - Default to "US" unless Canada is mentioned or province codes (ON, BC, AB, etc.) are used
   - Canadian postal codes have format like "L6H4N8" or "L6H 4N8"
   - "Ontario", "Canada" → country: "CA"

3. **State/Province inference**:
   - Use the state_context if the input lacks an explicit state
   - For zip-code-only inputs, infer state from zip
   - "33174" is FL, "94551" is CA, etc.

4. **County extraction**:
   - "Orange County CA" → county: "Orange", city: null
   - "Marin County" → county: "Marin"
   - Remove "County" suffix from the county name
   - For Canada, set county to null

5. **ZIP/Postal code**:
   - US: 5 digits (e.g., "33174", "94551")
   - Canada: 6 alphanumeric (e.g., "L6H4N8")
   - Format "-" separated zips like "29412" from "SC-29412"

6. **Radius extraction**:
   - "25 miles", "+ 50 Miles", "and 25 miles" → radius_miles: 25 or 50
   - "surrounding area" does NOT have a specific radius (set null)

7. **Resale detection**:
   - "resale", "RESALE", "Resale" anywhere → is_resale: true
   - Otherwise → is_resale: false

8. **City cleanup**:
   - Fix obvious typos: "MUrrieta" → "Murrieta"
   - Normalize capitalization: "salisbury" → "Salisbury"

EXAMPLES:

Input: "Oakland, CA"
Output: {{"locations": [{{"country": "US", "state_code": "CA", "county": null, "city": "Oakland", "zip_code": null, "radius_miles": null, "is_resale": false}}]}}

Input: "33174"
Output: {{"locations": [{{"country": "US", "state_code": "FL", "county": null, "city": "Miami", "zip_code": "33174", "radius_miles": null, "is_resale": false}}]}}

Input: "Livermore CA 94551 and 25 miles"
Output: {{"locations": [{{"country": "US", "state_code": "CA", "county": null, "city": "Livermore", "zip_code": "94551", "radius_miles": 25, "is_resale": false}}]}}

Input: "Dallas or Amarillo, TX"
Output: {{"locations": [{{"country": "US", "state_code": "TX", "county": null, "city": "Dallas", "zip_code": null, "radius_miles": null, "is_resale": false}}, {{"country": "US", "state_code": "TX", "county": null, "city": "Amarillo", "zip_code": null, "radius_miles": null, "is_resale": false}}]}}

Input: "Amarillo TX resale"
Output: {{"locations": [{{"country": "US", "state_code": "TX", "county": null, "city": "Amarillo", "zip_code": null, "radius_miles": null, "is_resale": true}}]}}

Input: "Oakville Ontario L6H4N8"
Output: {{"locations": [{{"country": "CA", "state_code": "ON", "county": null, "city": "Oakville", "zip_code": "L6H4N8", "radius_miles": null, "is_resale": false}}]}}

Input: "Orange County CA"
Output: {{"locations": [{{"country": "US", "state_code": "CA", "county": "Orange", "city": null, "zip_code": null, "radius_miles": null, "is_resale": false}}]}}

Return ONLY the JSON object with the locations array.
"""


async def parse_location_with_llm(
    location_raw: str, 
    state_context: Optional[str] = None,
    retries: int = 3,
) -> List[Dict[str, Any]]:
    """
    Parse a location string using Gemini LLM.
    
    Args:
        location_raw: The raw location string to parse
        state_context: Optional 2-letter state code for context
        retries: Number of retry attempts on failure
        
    Returns:
        List of parsed location dictionaries
    """
    if not location_raw or len(location_raw.strip()) < 2:
        return []
    
    if CLIENT is None:
        logger.error("Gemini client not initialized")
        return []
    
    prompt = build_parse_prompt(location_raw, state_context)
    config = get_parse_location_config()
    
    for attempt in range(retries):
        try:
            response = generate(
                client=CLIENT,
                model=MODEL_FLASH,
                parts=[types.Part(text=prompt)],
                generate_content_config=config,
            )
            
            if not response.text:
                logger.warning(f"Empty response for '{location_raw}'")
                continue
            
            result = json.loads(response.text)
            locations = result.get("locations", [])
            
            # Post-process: enrich with pgeocode data
            enriched = []
            for loc in locations:
                enriched.append(enrich_with_geocode(loc))
            
            return enriched
            
        except Exception as e:
            logger.warning(f"Parse attempt {attempt + 1}/{retries} failed for '{location_raw}': {e}")
            if "429" in str(e):
                logger.info("Rate limit hit, sleeping 30s...")
                await asyncio.sleep(30)
            elif attempt < retries - 1:
                await asyncio.sleep(1 * (attempt + 1))
    
    logger.error(f"Failed to parse '{location_raw}' after {retries} attempts")
    return []


def is_valid_city_name(city: Optional[str]) -> bool:
    """
    Validate that a city name is not purely numeric.
    
    Args:
        city: City name to validate
        
    Returns:
        True if city is valid (not None and not purely numeric)
    """
    if not city:
        return False
    # Reject if city contains only digits
    return not bool(re.match(r'^[0-9]+$', str(city).strip()))


def enrich_with_geocode(location: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich a parsed location with data from pgeocode.
    
    Adds:
    - county (if zip_code is present and county is missing)
    - latitude/longitude (if zip_code is present)
    - city (if zip_code is present and city is missing)
    """
    zip_code = location.get("zip_code")
    country = location.get("country", "US")
    
    if not zip_code:
        return location
    
    try:
        if country == "US":
            nomi = _get_nomi_us()
        elif country == "CA":
            nomi = _get_nomi_ca()
        else:
            return location
        
        geo = nomi.query_postal_code(zip_code)
        
        if geo.empty or str(geo.latitude) == 'nan':
            return location
        
        # Enrich missing fields
        if not location.get("county") and country == "US":
            county_name = getattr(geo, 'county_name', None)
            if county_name and str(county_name) != 'nan':
                location["county"] = county_name
        
        if not location.get("city"):
            place_name = getattr(geo, 'place_name', None)
            if place_name and str(place_name) != 'nan' and is_valid_city_name(place_name):
                location["city"] = place_name
        
        if not location.get("state_code"):
            state_code = getattr(geo, 'state_code', None)
            if state_code and str(state_code) != 'nan':
                location["state_code"] = state_code
        
        # Add lat/lon for potential radius calculations
        location["latitude"] = float(geo.latitude)
        location["longitude"] = float(geo.longitude)
        
    except Exception as e:
        logger.debug(f"Geocode enrichment failed for zip {zip_code}: {e}")
    
    return location


def lookup_county_by_zip(zip_code: str) -> Optional[str]:
    """Look up county name from US zip code."""
    try:
        nomi = _get_nomi_us()
        geo = nomi.query_postal_code(zip_code)
        
        if geo.empty:
            return None
        
        county = getattr(geo, 'county_name', None)
        if county and str(county) != 'nan':
            return county
        return None
    except Exception:
        return None


def lookup_city_by_zip(zip_code: str) -> Optional[str]:
    """Look up city name from US zip code."""
    try:
        nomi = _get_nomi_us()
        geo = nomi.query_postal_code(zip_code)
        
        if geo.empty:
            return None
        
        city = getattr(geo, 'place_name', None)
        if city and str(city) != 'nan':
            return city
        return None
    except Exception:
        return None


async def fetch_unparsed_records(limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
    """
    Fetch territory_checks records that need parsing.
    
    Criteria: city IS NULL AND county IS NULL (unprocessed)
    """
    supabase = supabase_client()
    
    response = supabase.table("territory_checks") \
        .select("id, franchise_id, location_raw, state_code, availability_status, check_date") \
        .is_("city", "null") \
        .is_("county", "null") \
        .not_.is_("location_raw", "null") \
        .range(offset, offset + limit - 1) \
        .execute()
    
    return response.data


async def update_record_with_parsed_data(
    record_id: int,
    parsed: Dict[str, Any],
    dry_run: bool = False,
) -> bool:
    """
    Update a territory_checks record with parsed location data.
    
    Args:
        record_id: ID of the record to update
        parsed: Parsed location data
        dry_run: If True, don't actually update
        
    Returns:
        True if successful
    """
    # Validate city before storing (reject numeric-only values)
    city = parsed.get("city")
    if city and not is_valid_city_name(city):
        logger.warning(f"Rejected numeric city value '{city}' for record {record_id}")
        city = None
    
    update_data = {
        "country": parsed.get("country", "US"),
        "state_code": parsed.get("state_code"),
        "county": parsed.get("county"),
        "city": city,
        "zip_code": parsed.get("zip_code"),
        "radius_miles": parsed.get("radius_miles"),
        "is_resale": parsed.get("is_resale", False),
        "latitude": parsed.get("latitude"),
        "longitude": parsed.get("longitude"),
    }
    
    # Remove None values to avoid overwriting with null
    update_data = {k: v for k, v in update_data.items() if v is not None}
    
    if dry_run:
        logger.info(f"[DRY RUN] Would update record {record_id}: {update_data}")
        return True
    
    try:
        supabase = supabase_client()
        supabase.table("territory_checks") \
            .update(update_data) \
            .eq("id", record_id) \
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update record {record_id}: {e}")
        return False


async def insert_split_record(
    original_record: Dict[str, Any],
    parsed: Dict[str, Any],
    dry_run: bool = False,
) -> Optional[int]:
    """
    Insert a new record when splitting multi-location entries.
    
    Args:
        original_record: The original record (for franchise_id, check_date, etc.)
        parsed: Parsed location data for the new record
        dry_run: If True, don't actually insert
        
    Returns:
        ID of the new record, or None if failed
    """
    # Validate city before storing (reject numeric-only values)
    city = parsed.get("city")
    if city and not is_valid_city_name(city):
        logger.warning(f"Rejected numeric city value '{city}' for split record")
        city = None
    
    insert_data = {
        "franchise_id": original_record["franchise_id"],
        "location_raw": f"{city or parsed.get('county') or ''}, {parsed.get('state_code') or ''}".strip(", "),
        "availability_status": original_record.get("availability_status"),
        "check_date": original_record.get("check_date"),
        "country": parsed.get("country", "US"),
        "state_code": parsed.get("state_code"),
        "county": parsed.get("county"),
        "city": city,
        "zip_code": parsed.get("zip_code"),
        "radius_miles": parsed.get("radius_miles"),
        "is_resale": parsed.get("is_resale", False),
        "latitude": parsed.get("latitude"),
        "longitude": parsed.get("longitude"),
    }
    
    # Remove None values
    insert_data = {k: v for k, v in insert_data.items() if v is not None}
    
    if dry_run:
        logger.info(f"[DRY RUN] Would insert split record: {insert_data}")
        return -1  # Placeholder ID
    
    try:
        supabase = supabase_client()
        response = supabase.table("territory_checks") \
            .insert(insert_data) \
            .execute()
        
        if response.data:
            return response.data[0].get("id")
        return None
    except Exception as e:
        logger.error(f"Failed to insert split record: {e}")
        return None


async def process_batch(
    limit: int = 100,
    dry_run: bool = False,
    delay_seconds: float = 0.5,
) -> Dict[str, int]:
    """
    Process a batch of unparsed territory_checks records.
    
    Args:
        limit: Maximum records to process
        dry_run: If True, don't modify database
        delay_seconds: Delay between LLM calls to avoid rate limits
        
    Returns:
        Stats dict with counts
    """
    stats = {
        "processed": 0,
        "updated": 0,
        "split": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    records = await fetch_unparsed_records(limit=limit)
    
    if not records:
        logger.info("No unparsed records found")
        return stats
    
    logger.info(f"Processing {len(records)} records (dry_run={dry_run})")
    
    for record in records:
        stats["processed"] += 1
        record_id = record["id"]
        location_raw = record.get("location_raw", "")
        state_context = record.get("state_code")
        
        try:
            # Parse with LLM
            parsed_locations = await parse_location_with_llm(location_raw, state_context)
            
            if not parsed_locations:
                logger.warning(f"No locations parsed for record {record_id}: '{location_raw}'")
                stats["skipped"] += 1
                continue
            
            # Handle single vs multi-location
            if len(parsed_locations) == 1:
                # Update existing record
                success = await update_record_with_parsed_data(
                    record_id, parsed_locations[0], dry_run
                )
                if success:
                    stats["updated"] += 1
                    logger.debug(f"Updated record {record_id}")
                else:
                    stats["errors"] += 1
            else:
                # Multi-location: update first, insert rest
                success = await update_record_with_parsed_data(
                    record_id, parsed_locations[0], dry_run
                )
                if success:
                    stats["updated"] += 1
                
                # Insert additional locations
                for parsed in parsed_locations[1:]:
                    new_id = await insert_split_record(record, parsed, dry_run)
                    if new_id:
                        stats["split"] += 1
                        logger.debug(f"Inserted split record {new_id} from {record_id}")
                    else:
                        stats["errors"] += 1
            
            # Rate limiting
            await asyncio.sleep(delay_seconds)
            
        except Exception as e:
            logger.error(f"Error processing record {record_id}: {e}")
            stats["errors"] += 1
        
        # Progress log every 50 records
        if stats["processed"] % 50 == 0:
            logger.info(f"Progress: {stats}")
    
    return stats


async def main():
    """Main entry point for the parser script."""
    parser = argparse.ArgumentParser(
        description="Parse territory_checks location_raw into structured fields"
    )
    parser.add_argument(
        "--limit", type=int, default=100,
        help="Maximum number of records to process (default: 100)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without modifying database"
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Delay in seconds between LLM calls (default: 0.5)"
    )
    parser.add_argument(
        "--loop", action="store_true",
        help="Run continuously until all records are processed"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=" * 50)
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info("=" * 50)
    
    total_stats = {
        "processed": 0,
        "updated": 0,
        "split": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    while True:
        stats = await process_batch(
            limit=args.limit,
            dry_run=args.dry_run,
            delay_seconds=args.delay,
        )
        
        # Aggregate stats
        for key in total_stats:
            total_stats[key] += stats[key]
        
        # Check if we should continue
        if not args.loop or stats["processed"] == 0:
            break
        
        logger.info(f"Batch complete. Total so far: {total_stats}")
    
    logger.info("=" * 50)
    logger.info("Location Parsing Complete!")
    logger.info(f"  Total processed: {total_stats['processed']}")
    logger.info(f"  Updated: {total_stats['updated']}")
    logger.info(f"  Split into new records: {total_stats['split']}")
    logger.info(f"  Skipped (no parse): {total_stats['skipped']}")
    logger.info(f"  Errors: {total_stats['errors']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())

