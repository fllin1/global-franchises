# -*- coding: utf-8 -*-
"""
Diagnostic script to identify territory_checks records with numeric city values.

Finds all records where the city field contains only numeric characters (0-9),
which should be actual city names instead.

Usage:
    python -m src.backend.scripts.diagnose_numeric_cities
"""

import re
import json
from collections import defaultdict
from typing import Dict, List, Any

from loguru import logger

from src.api.config.supabase_config import supabase_client


def is_numeric_city(city: str) -> bool:
    """Check if city value is purely numeric."""
    if not city:
        return False
    # Match strings that contain only digits (0-9)
    return bool(re.match(r'^[0-9]+$', str(city).strip()))


async def diagnose_numeric_cities() -> Dict[str, Any]:
    """
    Query database and identify records with numeric city values.
    
    Returns:
        Dictionary with statistics and affected records
    """
    supabase = supabase_client()
    
    logger.info("Fetching all territory_checks records...")
    
    # Fetch all records with city field populated
    # We'll filter in Python since Supabase doesn't support regex queries directly
    response = supabase.table("territory_checks") \
        .select("id, franchise_id, city, county, state_code, zip_code, location_raw") \
        .not_.is_("city", "null") \
        .execute()
    
    all_records = response.data
    logger.info(f"Found {len(all_records)} records with city values")
    
    # Filter for numeric cities
    numeric_records = []
    for record in all_records:
        city = record.get("city")
        if is_numeric_city(city):
            numeric_records.append(record)
    
    logger.info(f"Found {len(numeric_records)} records with numeric city values")
    
    # Group by franchise_id for statistics
    by_franchise = defaultdict(list)
    for record in numeric_records:
        franchise_id = record.get("franchise_id")
        by_franchise[franchise_id].append(record)
    
    # Statistics
    stats = {
        "total_records_with_city": len(all_records),
        "numeric_city_count": len(numeric_records),
        "affected_franchises": len(by_franchise),
        "franchise_breakdown": {
            franchise_id: len(records)
            for franchise_id, records in by_franchise.items()
        },
        "sample_records": numeric_records[:10],  # First 10 for inspection
    }
    
    # Log summary
    logger.info("=" * 60)
    logger.info("DIAGNOSTIC RESULTS")
    logger.info("=" * 60)
    logger.info(f"Total records with city: {stats['total_records_with_city']}")
    logger.info(f"Records with numeric city: {stats['numeric_city_count']}")
    logger.info(f"Affected franchises: {stats['affected_franchises']}")
    logger.info("")
    logger.info("Breakdown by franchise:")
    for franchise_id, count in sorted(stats['franchise_breakdown'].items()):
        logger.info(f"  Franchise {franchise_id}: {count} records")
    logger.info("")
    
    if numeric_records:
        logger.info("Sample records with numeric cities:")
        for record in stats['sample_records']:
            logger.info(f"  ID {record['id']}: city='{record['city']}', "
                       f"location_raw='{record.get('location_raw', 'N/A')[:50]}...', "
                       f"zip_code={record.get('zip_code', 'N/A')}")
    
    logger.info("=" * 60)
    
    return {
        "stats": stats,
        "all_numeric_records": numeric_records,
    }


async def main():
    """Main entry point."""
    try:
        results = await diagnose_numeric_cities()
        
        # Output JSON for further processing
        logger.debug(f"\nFull results:\n{json.dumps(results['stats'], indent=2)}")
        
        return results
    except Exception as e:
        logger.error(f"Diagnostic failed: {e}")
        raise


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())



