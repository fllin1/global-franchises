import asyncio
import re
import json
from typing import List, Dict, Any
from datetime import datetime
from loguru import logger
from src.api.config.supabase_config import supabase_client

# --- Regex Patterns for Extraction ---
# Updated Pattern to match: "El Paso, TX - Available" or "7/21/2025 ... - Available"
# The previous pattern expected a date at the start, but some entries don't have it.
# We need to handle both cases.

# Case 1: With Date "7/21/2025 1:23:56 PM - Hillsborough, NJ 08844 - Available"
PATTERN_WITH_DATE = r"(\d{1,2}/\d{1,2}/\d{4}).*?\s-\s(.*?)\s-\s(Available|Not Available.*|.*Available.*)"

# Case 2: No Date "El Paso, TX - Available"
PATTERN_NO_DATE = r"(.*?)\s-\s(Available|Not Available.*|.*Available.*)"

# Map for State Codes (US + Canada + some Intl if needed)
STATE_MAP = {
    "AL": "AL", "AK": "AK", "AZ": "AZ", "AR": "AR", "CA": "CA", "CO": "CO", "CT": "CT", "DE": "DE", "FL": "FL", "GA": "GA",
    "HI": "HI", "ID": "ID", "IL": "IL", "IN": "IN", "IA": "IA", "KS": "KS", "KY": "KY", "LA": "LA", "ME": "ME", "MD": "MD",
    "MA": "MA", "MI": "MI", "MN": "MN", "MS": "MS", "MO": "MO", "MT": "MT", "NE": "NE", "NV": "NV", "NH": "NH", "NJ": "NJ",
    "NM": "NM", "NY": "NY", "NC": "NC", "ND": "ND", "OH": "OH", "OK": "OK", "OR": "OR", "PA": "PA", "RI": "RI", "SC": "SC",
    "SD": "SD", "TN": "TN", "TX": "TX", "UT": "UT", "VT": "VT", "VA": "VA", "WA": "WA", "WV": "WV", "WI": "WI", "WY": "WY",
    "DC": "DC", "PR": "PR"
}

def extract_state_code(location_text: str) -> str | None:
    """
    Attempts to extract a 2-letter state code from a location string.
    Heuristic: Look for 2 uppercase letters that match a known state code.
    """
    # Normalize slightly
    text = location_text.replace(",", " ").replace(".", " ")
    
    # Look for matches of keys in STATE_MAP
    # Using regex to find word boundaries for state codes
    for state in STATE_MAP:
        # Check for " FL " or " FL" at end or "FL " at start
        if re.search(rf"\b{state}\b", text, re.IGNORECASE):
            return STATE_MAP[state]
    
    return None

def parse_check_string(check_str: str) -> Dict[str, Any] | None:
    """
    Parses a single check string into structured data.
    """
    check_str = check_str.strip()
    date_str = None
    location_raw = None
    status_raw = None

    # Try matching with date first
    match_date = re.match(PATTERN_WITH_DATE, check_str)
    if match_date:
        date_str, location_raw, status_raw = match_date.groups()
    else:
        # Try matching without date
        match_no_date = re.match(PATTERN_NO_DATE, check_str)
        if match_no_date:
            location_raw, status_raw = match_no_date.groups()
            date_str = None # No date available
        else:
            # Failed to parse
            # logger.warning(f"Failed to parse check string: {check_str}")
            return None

    # Normalize status
    if "Not Available" in status_raw:
        status = "Not Available"
    elif "Available" in status_raw:
        status = "Available"
    else:
        status = "Pending"

    state_code = extract_state_code(location_raw)

    return {
        "check_date": date_str, 
        "location_raw": location_raw.strip(),
        "state_code": state_code,
        "availability_status": status
    }

async def migrate_territory_checks():
    """
    Main migration function.
    """
    logger.info("Starting territory checks migration...")
    
    # 1. Fetch Franchises with checks
    try:
        response = supabase_client().table("Franchises").select("id, franchise_name, recent_territory_checks").not_.is_("recent_territory_checks", "null").execute()
        franchises = response.data
        logger.info(f"Found {len(franchises)} franchises with territory checks.")
    except Exception as e:
        logger.error(f"Failed to fetch franchises: {e}")
        return

    total_checks = 0
    inserted_checks = 0
    
    batch_size = 100
    checks_batch = []

    # First clear existing data to avoid duplicates if re-running?
    # Or assume empty table for now.
    # supabase_client().table("territory_checks").delete().neq("id", 0).execute()

    for fran in franchises:
        fran_id = fran['id']
        checks_json_str = fran['recent_territory_checks']
        
        # Python's json.loads might fail if it's single quotes in string representation from Python list str
        # The DB output showed "['El Paso...']" which is NOT valid JSON (single quotes).
        # We need to fix this.
        try:
            # Try standard JSON first
            checks_list = json.loads(checks_json_str)
        except json.JSONDecodeError:
            try:
                # Fallback: Replace single quotes with double quotes? 
                # Danger: What if content has single quotes? e.g. "Founder's check"
                # Better: Use ast.literal_eval if it's a python string representation
                import ast
                checks_list = ast.literal_eval(checks_json_str)
            except Exception as e:
                logger.warning(f"Failed to parse JSON/List for franchise {fran_id}: {e}")
                continue

        if not isinstance(checks_list, list):
            continue
            
        for check_str in checks_list:
            total_checks += 1
            parsed = parse_check_string(check_str)
            
            if parsed:
                # Convert date string to datetime object for Supabase
                if parsed['check_date']:
                    try:
                         dt = datetime.strptime(parsed['check_date'], "%m/%d/%Y")
                         parsed['check_date'] = dt.isoformat()
                    except ValueError:
                        parsed['check_date'] = None # Invalid date format
                
                checks_batch.append({
                    "franchise_id": fran_id,
                    "check_date": parsed['check_date'],
                    "location_raw": parsed['location_raw'],
                    "state_code": parsed['state_code'],
                    "availability_status": parsed['availability_status']
                })
                
                if len(checks_batch) >= batch_size:
                    # Insert batch
                    try:
                        supabase_client().table("territory_checks").insert(checks_batch).execute()
                        inserted_checks += len(checks_batch)
                        checks_batch = []
                    except Exception as e:
                        logger.error(f"Error inserting batch: {e}")
                        checks_batch = [] 

    # Insert remaining
    if checks_batch:
        try:
            supabase_client().table("territory_checks").insert(checks_batch).execute()
            inserted_checks += len(checks_batch)
        except Exception as e:
            logger.error(f"Error inserting final batch: {e}")

    logger.info(f"Migration complete. Processed {total_checks} checks. Inserted {inserted_checks} structured records.")

if __name__ == "__main__":
    asyncio.run(migrate_territory_checks())
