# -*- coding: utf-8 -*-
"""
Field Mapper for Franchise Data.

This module handles transformations between the LLM structured output format
and the database schema format.
"""

import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import pgeocode

# Initialize pgeocode for US zip lookups
_nomi = None

def _get_nomi():
    """Lazy initialization of pgeocode Nominatim."""
    global _nomi
    if _nomi is None:
        _nomi = pgeocode.Nominatim('us')
    return _nomi


def parse_date_mdy_to_ymd(date_str: Optional[str]) -> Optional[str]:
    """
    Convert date from MM/DD/YYYY format to YYYY-MM-DD format.
    
    Args:
        date_str: Date string in MM/DD/YYYY format (e.g., "11/22/2025")
        
    Returns:
        Date string in YYYY-MM-DD format or None if parsing fails
    """
    if not date_str:
        return None
    
    try:
        # Try MM/DD/YYYY format
        parsed = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    try:
        # Try M/D/YYYY format (single digits)
        parsed = datetime.strptime(date_str.strip(), "%m/%d/%Y")
        return parsed.strftime("%Y-%m-%d")
    except ValueError:
        pass
    
    # Return None if we can't parse it
    return None


def array_to_text(arr: Optional[List[str]], separator: str = "\n- ") -> Optional[str]:
    """
    Convert an array of strings to a single text string.
    
    Args:
        arr: List of strings
        separator: Separator between items (default: newline with bullet)
        
    Returns:
        Joined string or None if array is empty/None
    """
    if not arr or not isinstance(arr, list):
        return None
    
    # Filter out None/empty values
    filtered = [str(item).strip() for item in arr if item]
    
    if not filtered:
        return None
    
    if separator == "\n- ":
        # Format as bullet list
        return "- " + separator.join(filtered)
    
    return separator.join(filtered)


def generate_slug(name: Optional[str]) -> Optional[str]:
    """
    Generate a URL-friendly slug from a franchise name.
    
    Args:
        name: Franchise name
        
    Returns:
        URL-friendly slug
    """
    if not name:
        return None
    
    # Convert to lowercase, replace non-alphanumeric with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', name.lower())
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    return slug


def extract_source_id_from_filename(filename: str) -> Optional[int]:
    """
    Extract source_id from filename like 'FranID_1003.md' or 'FranID_1003.html'.
    
    Args:
        filename: Filename to extract from
        
    Returns:
        Integer source_id or None
    """
    if not filename:
        return None
    
    # Match FranID_XXXX pattern
    match = re.search(r'FranID_(\d+)', filename)
    if match:
        return int(match.group(1))
    
    return None


def build_source_url(source_id: Optional[int]) -> Optional[str]:
    """
    Build the source URL from the source_id.
    
    Args:
        source_id: The FranID
        
    Returns:
        Full FranServe URL
    """
    if not source_id:
        return None
    
    return f"https://franservesupport.com/franchisedetails.asp?FranID={source_id}&ClientID="


def map_llm_output_to_db_schema(
    llm_output: Dict[str, Any],
    source_id: int,
) -> Dict[str, Any]:
    """
    Map the LLM structured output to database schema format.
    
    Handles:
    - Array to text conversions
    - Date format conversions
    - Adding source_id, source_url, slug, last_scraped_at
    
    Args:
        llm_output: The raw JSON output from Gemini LLM
        source_id: The FranID extracted from filename
        
    Returns:
        Dictionary ready for database upsert
    """
    franchise_data = llm_output.get("franchise_data", {})
    
    # Start with a clean dictionary
    db_record = {}
    
    # --- Identity Fields ---
    db_record["source_id"] = source_id
    db_record["source_url"] = build_source_url(source_id)
    db_record["franchise_name"] = franchise_data.get("franchise_name")
    db_record["slug"] = generate_slug(franchise_data.get("franchise_name"))
    db_record["last_scraped_at"] = datetime.now(timezone.utc).isoformat()
    db_record["llm_processed_at"] = datetime.now(timezone.utc).isoformat()  # Track LLM processing
    
    # --- Category Fields ---
    # primary_category: array → text (join with ", ")
    primary_cat = franchise_data.get("primary_category")
    if isinstance(primary_cat, list):
        db_record["primary_category"] = ", ".join(primary_cat) if primary_cat else None
    else:
        db_record["primary_category"] = primary_cat
    
    # sub_categories stays as JSONB array
    db_record["sub_categories"] = franchise_data.get("sub_categories")
    
    # --- Business Fields ---
    db_record["business_model_type"] = franchise_data.get("business_model_type")
    db_record["corporate_address"] = franchise_data.get("corporate_address")
    db_record["website_url"] = franchise_data.get("website_url")
    
    # --- Historical Fields ---
    db_record["founded_year"] = franchise_data.get("founded_year")
    db_record["franchised_year"] = franchise_data.get("franchised_year")
    
    # last_updated_from_source: MM/DD/YYYY → YYYY-MM-DD
    last_updated = franchise_data.get("last_updated_from_source")
    db_record["last_updated_from_source"] = parse_date_mdy_to_ymd(last_updated)
    
    # --- Financial Fields ---
    db_record["franchise_fee_usd"] = franchise_data.get("franchise_fee_usd")
    db_record["required_cash_investment_usd"] = franchise_data.get("required_cash_investment_usd")
    db_record["total_investment_min_usd"] = franchise_data.get("total_investment_min_usd")
    db_record["total_investment_max_usd"] = franchise_data.get("total_investment_max_usd")
    db_record["required_net_worth_usd"] = franchise_data.get("required_net_worth_usd")
    db_record["royalty_details_text"] = franchise_data.get("royalty_details_text")
    db_record["additional_fees"] = franchise_data.get("additional_fees")
    db_record["financial_assistance_details"] = franchise_data.get("financial_assistance_details")
    
    # --- Boolean Flags ---
    db_record["sba_approved"] = franchise_data.get("sba_approved")
    db_record["sba_registered"] = franchise_data.get("sba_registered")
    db_record["providing_earnings_guidance_item19"] = franchise_data.get("providing_earnings_guidance_item19")
    db_record["vetfran_member"] = franchise_data.get("vetfran_member")
    db_record["vetfran_discount_details"] = franchise_data.get("vetfran_discount_details")
    db_record["is_home_based"] = franchise_data.get("is_home_based")
    db_record["allows_semi_absentee"] = franchise_data.get("allows_semi_absentee")
    db_record["allows_absentee"] = franchise_data.get("allows_absentee")
    db_record["e2_visa_friendly"] = franchise_data.get("e2_visa_friendly")
    db_record["master_franchise_opportunity"] = franchise_data.get("master_franchise_opportunity")
    db_record["canadian_referrals"] = franchise_data.get("canadian_referrals")
    db_record["international_referrals"] = franchise_data.get("international_referrals")
    db_record["resales_available"] = franchise_data.get("resales_available")
    
    # --- Narrative Fields (arrays → text) ---
    db_record["description_text"] = franchise_data.get("description_text")
    
    # why_franchise_summary: array → text
    why_summary = franchise_data.get("why_franchise_summary")
    if isinstance(why_summary, list):
        db_record["why_franchise_summary"] = array_to_text(why_summary)
    else:
        db_record["why_franchise_summary"] = why_summary
    
    # ideal_candidate_profile_text: array → text
    ideal_text = franchise_data.get("ideal_candidate_profile_text")
    if isinstance(ideal_text, list):
        db_record["ideal_candidate_profile_text"] = array_to_text(ideal_text)
    else:
        db_record["ideal_candidate_profile_text"] = ideal_text
    
    # --- JSONB Fields (keep as objects/arrays) ---
    db_record["ideal_candidate_profile"] = franchise_data.get("ideal_candidate_profile")
    db_record["unavailable_states"] = franchise_data.get("unavailable_states")
    db_record["hot_regions"] = franchise_data.get("hot_regions")
    db_record["recent_territory_checks"] = franchise_data.get("recent_territory_checks")
    db_record["commission_structure"] = franchise_data.get("commission_structure")
    db_record["industry_awards"] = franchise_data.get("industry_awards")
    db_record["documents"] = franchise_data.get("documents")
    db_record["resales_list"] = franchise_data.get("resales_list")
    db_record["franchise_packages"] = franchise_data.get("franchise_packages")
    db_record["support_training_details"] = franchise_data.get("support_training_details")
    db_record["market_growth_statistics"] = franchise_data.get("market_growth_statistics")
    db_record["franchises_data"] = franchise_data.get("franchises_data")
    
    # --- Other Fields ---
    db_record["rating"] = franchise_data.get("rating")
    db_record["schedule_call_url"] = franchise_data.get("schedule_call_url")
    
    # --- Clean up None values ---
    # Remove keys with None values to avoid overwriting existing data
    db_record = {k: v for k, v in db_record.items() if v is not None}
    
    return db_record


def extract_contacts_data(
    llm_output: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Extract contacts data from LLM output.
    
    Args:
        llm_output: The raw JSON output from Gemini LLM
        
    Returns:
        List of contact dictionaries ready for database insert
    """
    contacts = llm_output.get("contacts_data", [])
    
    if not contacts or not isinstance(contacts, list):
        return []
    
    cleaned_contacts = []
    for contact in contacts:
        if not contact or not contact.get("name"):
            continue
        
        cleaned = {
            "name": contact.get("name"),
            "title": contact.get("title"),
            "phone": contact.get("phone"),
            "email": contact.get("email"),
        }
        
        # Remove None values
        cleaned = {k: v for k, v in cleaned.items() if v is not None}
        
        if cleaned.get("name"):
            cleaned_contacts.append(cleaned)
    
    return cleaned_contacts


# =============================================================================
# Territory Check Parsing Functions
# =============================================================================

# List of valid 2-letter US state codes
US_STATE_CODES = {
    'AL', 'AK', 'AZ', 'AR', 'CA', 'CO', 'CT', 'DE', 'FL', 'GA',
    'HI', 'ID', 'IL', 'IN', 'IA', 'KS', 'KY', 'LA', 'ME', 'MD',
    'MA', 'MI', 'MN', 'MS', 'MO', 'MT', 'NE', 'NV', 'NH', 'NJ',
    'NM', 'NY', 'NC', 'ND', 'OH', 'OK', 'OR', 'PA', 'RI', 'SC',
    'SD', 'TN', 'TX', 'UT', 'VT', 'VA', 'WA', 'WV', 'WI', 'WY', 'DC'
}


def extract_state_code(location_text: str) -> Optional[str]:
    """
    Extract 2-letter US state code from location text.
    
    Args:
        location_text: Raw location string (e.g., "Austin, TX 78701")
        
    Returns:
        2-letter state code or None
    """
    if not location_text:
        return None
    
    # Pattern 1: Look for 2-letter state codes (must be standalone or before zip)
    # Match patterns like "TX", "TX 78701", ", TX", "TX,"
    state_pattern = r'\b([A-Z]{2})\b'
    matches = re.findall(state_pattern, location_text.upper())
    
    for match in matches:
        if match in US_STATE_CODES:
            return match
    
    return None


def extract_zip_code(location_text: str) -> Optional[str]:
    """
    Extract 5-digit US zip code from location text.
    
    Args:
        location_text: Raw location string
        
    Returns:
        5-digit zip code or None
    """
    if not location_text:
        return None
    
    # Match 5-digit zip codes
    zip_match = re.search(r'\b(\d{5})\b', location_text)
    if zip_match:
        return zip_match.group(1)
    
    return None


def extract_radius_miles(location_text: str) -> Optional[float]:
    """
    Extract radius in miles from location text.
    
    Patterns matched:
    - "30 miles around"
    - "within 30 miles"
    - "30 mile radius"
    - "up to 30 miles"
    
    Args:
        location_text: Raw location string
        
    Returns:
        Radius in miles as float, or None
    """
    if not location_text:
        return None
    
    # Pattern for miles
    patterns = [
        r'(\d+(?:\.\d+)?)\s*miles?\s*(?:around|radius|from|of|away)',
        r'(?:within|up\s*to)\s*(\d+(?:\.\d+)?)\s*miles?',
        r'(\d+(?:\.\d+)?)\s*mile\s*radius',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, location_text, re.IGNORECASE)
        if match:
            return float(match.group(1))
    
    return None


def lookup_zip_with_pgeocode(zip_code: str) -> Tuple[Optional[str], Optional[str], Optional[float], Optional[float]]:
    """
    Look up zip code using pgeocode to get city, state, lat, lon.
    
    Args:
        zip_code: 5-digit US zip code
        
    Returns:
        Tuple of (city, state_code, latitude, longitude)
    """
    if not zip_code:
        return None, None, None, None
    
    try:
        nomi = _get_nomi()
        geo = nomi.query_postal_code(zip_code)
        
        if geo.empty or str(geo.latitude) == 'nan':
            return None, None, None, None
        
        city = geo.place_name if hasattr(geo, 'place_name') else None
        state = geo.state_code if hasattr(geo, 'state_code') else None
        lat = float(geo.latitude) if str(geo.latitude) != 'nan' else None
        lon = float(geo.longitude) if str(geo.longitude) != 'nan' else None
        
        return city, state, lat, lon
    except Exception:
        return None, None, None, None


def parse_territory_check(
    check: Dict[str, Any],
    franchise_id: int,
) -> Optional[Dict[str, Any]]:
    """
    Parse a single territory check from LLM output into database format.
    
    Extracts:
    - state_code from location text
    - zip_code from location text
    - city, latitude, longitude from pgeocode lookup
    - radius_miles from location text
    - Converts is_available to availability_status
    - Converts date from MM/DD/YYYY to timestamp
    
    Args:
        check: Territory check dict from LLM output with keys:
               date, location, is_available, notes
        franchise_id: The database ID of the franchise
        
    Returns:
        Dictionary ready for territory_checks table insert, or None if invalid
    """
    if not check or not check.get("location"):
        return None
    
    location_raw = check.get("location", "")
    
    # Extract components from location text
    state_code = extract_state_code(location_raw)
    zip_code = extract_zip_code(location_raw)
    radius_miles = extract_radius_miles(location_raw)
    
    # Look up zip code for city and coordinates
    city = None
    latitude = None
    longitude = None
    
    if zip_code:
        pgeo_city, pgeo_state, latitude, longitude = lookup_zip_with_pgeocode(zip_code)
        if pgeo_city:
            city = pgeo_city
        # If we didn't extract state from text but got it from pgeocode, use that
        if not state_code and pgeo_state:
            state_code = pgeo_state
    
    # Convert availability boolean to status text
    is_available = check.get("is_available")
    if is_available is True:
        availability_status = "Available"
    elif is_available is False:
        availability_status = "Not Available"
    else:
        availability_status = "Pending"
    
    # Parse date from MM/DD/YYYY to ISO timestamp
    check_date = None
    date_str = check.get("date")
    if date_str:
        try:
            parsed_date = datetime.strptime(date_str.strip(), "%m/%d/%Y")
            check_date = parsed_date.isoformat()
        except ValueError:
            pass
    
    # Build the record
    record = {
        "franchise_id": franchise_id,
        "check_date": check_date,
        "location_raw": location_raw,
        "state_code": state_code,
        "availability_status": availability_status,
        "city": city,
        "zip_code": zip_code,
        "latitude": latitude,
        "longitude": longitude,
        "radius_miles": radius_miles,
    }
    
    # Remove None values to avoid overwriting existing data
    record = {k: v for k, v in record.items() if v is not None}
    
    # Ensure we have at least franchise_id and location_raw
    if "franchise_id" in record and "location_raw" in record:
        return record
    
    return None


def extract_territory_checks_data(
    llm_output: Dict[str, Any],
    franchise_id: int,
) -> List[Dict[str, Any]]:
    """
    Extract and parse all territory checks from LLM output.
    
    Args:
        llm_output: The raw JSON output from Gemini LLM
        franchise_id: The database ID of the franchise
        
    Returns:
        List of territory check dictionaries ready for database insert
    """
    franchise_data = llm_output.get("franchise_data", {})
    territory_checks = franchise_data.get("recent_territory_checks", [])
    
    if not territory_checks or not isinstance(territory_checks, list):
        return []
    
    parsed_checks = []
    for check in territory_checks:
        parsed = parse_territory_check(check, franchise_id)
        if parsed:
            parsed_checks.append(parsed)
    
    return parsed_checks

