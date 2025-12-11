# -*- coding: utf-8 -*-
"""
Fix numeric city values in territory_checks table.

This script identifies records where the city field contains only numeric characters
and attempts to fix them by:
1. Extracting city name from location_raw using LLM parsing
2. Looking up city from zip_code using pgeocode
3. Setting city to NULL if neither method works (will display as "Unspecified Area")

Usage:
    python -m src.backend.scripts.fix_numeric_cities [--dry-run] [--limit=100]
"""

import argparse
import asyncio
import re
from typing import Dict, List, Any, Optional

from loguru import logger
import pgeocode

from src.api.config.supabase_config import supabase_client
from src.backend.scripts.parse_territory_locations import parse_location_with_llm


def is_numeric_city(city: str) -> bool:
    """Check if city value is purely numeric."""
    if not city:
        return False
    return bool(re.match(r'^[0-9]+$', str(city).strip()))


def lookup_city_from_zip(zip_code: str) -> Optional[str]:
    """Look up city name from zip code using pgeocode."""
    if not zip_code:
        return None
    
    try:
        nomi = pgeocode.Nominatim('us')
        geo = nomi.query_postal_code(zip_code)
        
        if geo.empty or str(geo.latitude) == 'nan':
            return None
        
        city = geo.place_name if hasattr(geo, 'place_name') else None
        if city and str(city) != 'nan':
            return str(city).strip()
        return None
    except Exception as e:
        logger.debug(f"pgeocode lookup failed for zip {zip_code}: {e}")
        return None


def extract_city_from_location_raw(location_raw: str) -> Optional[str]:
    """
    Try to extract city name from location_raw using simple regex patterns.
    
    This is a fallback before using LLM parsing.
    """
    if not location_raw:
        return None
    
    # Pattern 1: "City, State" format
    match = re.match(r'^([A-Za-z\s\.\-\']+),\s*[A-Z]{2}', location_raw.strip())
    if match:
        city = match.group(1).strip()
        # Reject if it's numeric
        if not is_numeric_city(city) and len(city) > 1:
            return city
    
    # Pattern 2: "City State" format (without comma)
    match = re.match(r'^([A-Za-z\s\.\-\']+)\s+([A-Z]{2})', location_raw.strip())
    if match:
        city = match.group(1).strip()
        if not is_numeric_city(city) and len(city) > 1:
            return city
    
    return None


async def fix_numeric_city_record(
    record: Dict[str, Any],
    dry_run: bool = False,
) -> Dict[str, Any]:
    """
    Attempt to fix a single record with numeric city value.
    
    Returns:
        Dictionary with fix result: {'fixed': bool, 'new_city': str|None, 'method': str}
    """
    record_id = record['id']
    current_city = record.get('city')
    location_raw = record.get('location_raw')
    zip_code = record.get('zip_code')
    state_code = record.get('state_code')
    
    logger.info(f"Fixing record {record_id}: current city='{current_city}', "
               f"location_raw='{location_raw[:50] if location_raw else None}...', "
               f"zip_code={zip_code}")
    
    new_city = None
    method = None
    
    # Method 1: Try extracting from location_raw using regex
    if location_raw:
        extracted = extract_city_from_location_raw(location_raw)
        if extracted and not is_numeric_city(extracted):
            new_city = extracted
            method = "regex_extraction"
            logger.info(f"  → Extracted city '{new_city}' from location_raw using regex")
    
    # Method 2: Try LLM parsing if regex didn't work
    if not new_city and location_raw:
        try:
            parsed_locations = await parse_location_with_llm(location_raw, state_code)
            if parsed_locations:
                # Take the first location's city
                first_loc = parsed_locations[0]
                llm_city = first_loc.get('city')
                if llm_city and not is_numeric_city(llm_city):
                    new_city = llm_city
                    method = "llm_parsing"
                    logger.info(f"  → Extracted city '{new_city}' from location_raw using LLM")
        except Exception as e:
            logger.warning(f"  → LLM parsing failed: {e}")
    
    # Method 3: Try looking up from zip_code
    if not new_city and zip_code:
        zip_city = lookup_city_from_zip(zip_code)
        if zip_city and not is_numeric_city(zip_city):
            new_city = zip_city
            method = "zip_lookup"
            logger.info(f"  → Found city '{new_city}' from zip_code lookup")
    
    # If we couldn't find a valid city, set to None (will display as "Unspecified Area")
    if not new_city:
        new_city = None
        method = "set_to_null"
        logger.info(f"  → Could not determine city, setting to NULL")
    
    # Update database
    if not dry_run:
        try:
            supabase = supabase_client()
            update_data = {"city": new_city}
            supabase.table("territory_checks") \
                .update(update_data) \
                .eq("id", record_id) \
                .execute()
            logger.success(f"  ✓ Updated record {record_id}: city='{new_city}'")
        except Exception as e:
            logger.error(f"  ✗ Failed to update record {record_id}: {e}")
            return {'fixed': False, 'new_city': None, 'method': None, 'error': str(e)}
    else:
        logger.info(f"  [DRY RUN] Would update record {record_id}: city='{new_city}'")
    
    return {
        'fixed': True,
        'new_city': new_city,
        'method': method,
    }


async def fix_numeric_cities(
    dry_run: bool = False,
    limit: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Find and fix all records with numeric city values.
    
    Args:
        dry_run: If True, don't modify database
        limit: Maximum number of records to process (None for all)
        
    Returns:
        Statistics dictionary
    """
    supabase = supabase_client()
    
    logger.info("Fetching records with numeric city values...")
    
    # Fetch all records with city field populated
    response = supabase.table("territory_checks") \
        .select("id, franchise_id, city, county, state_code, zip_code, location_raw") \
        .not_.is_("city", "null") \
        .execute()
    
    all_records = response.data
    
    # Filter for numeric cities
    numeric_records = [
        record for record in all_records
        if is_numeric_city(record.get('city', ''))
    ]
    
    if limit:
        numeric_records = numeric_records[:limit]
    
    logger.info(f"Found {len(numeric_records)} records with numeric city values")
    
    if not numeric_records:
        logger.info("No records to fix!")
        return {
            'total_found': 0,
            'processed': 0,
            'fixed': 0,
            'failed': 0,
        }
    
    # Process records
    stats = {
        'total_found': len(numeric_records),
        'processed': 0,
        'fixed': 0,
        'failed': 0,
        'by_method': {
            'regex_extraction': 0,
            'llm_parsing': 0,
            'zip_lookup': 0,
            'set_to_null': 0,
        },
    }
    
    logger.info("=" * 60)
    logger.info(f"Processing {len(numeric_records)} records...")
    logger.info("=" * 60)
    
    for i, record in enumerate(numeric_records, 1):
        logger.info(f"\n[{i}/{len(numeric_records)}] Processing record {record['id']}...")
        
        try:
            result = await fix_numeric_city_record(record, dry_run=dry_run)
            
            stats['processed'] += 1
            if result.get('fixed'):
                stats['fixed'] += 1
                method = result.get('method')
                if method in stats['by_method']:
                    stats['by_method'][method] += 1
            else:
                stats['failed'] += 1
            
            # Small delay to avoid rate limits
            await asyncio.sleep(0.5)
            
        except Exception as e:
            logger.error(f"Error processing record {record['id']}: {e}")
            stats['failed'] += 1
    
    logger.info("\n" + "=" * 60)
    logger.info("FIX COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Total found: {stats['total_found']}")
    logger.info(f"Processed: {stats['processed']}")
    logger.info(f"Fixed: {stats['fixed']}")
    logger.info(f"Failed: {stats['failed']}")
    logger.info("\nFix methods:")
    for method, count in stats['by_method'].items():
        logger.info(f"  {method}: {count}")
    logger.info("=" * 60)
    
    return stats


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Fix numeric city values in territory_checks table"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without modifying database"
    )
    parser.add_argument(
        "--limit", type=int,
        help="Maximum number of records to process (default: all)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No changes will be made to the database")
        logger.info("=" * 60)
    
    try:
        stats = await fix_numeric_cities(
            dry_run=args.dry_run,
            limit=args.limit,
        )
        return stats
    except Exception as e:
        logger.error(f"Fix failed: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())














