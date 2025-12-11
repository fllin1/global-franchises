# -*- coding: utf-8 -*-
"""
Backfill county data for existing territory_checks records.

This script populates the 'county' column for territory checks that have 
zip_code but no county. It uses pgeocode for US zip code lookups.

Usage:
    python -m src.backend.scripts.backfill_territory_counties [--dry-run] [--batch-size=100]
"""

import argparse
from typing import Optional, Tuple

import pgeocode
from loguru import logger

from src.api.config.supabase_config import supabase_client

# Initialize pgeocode for US zip lookups
_nomi = None


def _get_nomi():
    """Lazy initialization of pgeocode Nominatim."""
    global _nomi
    if _nomi is None:
        _nomi = pgeocode.Nominatim('us')
    return _nomi


def lookup_county_by_zip(zip_code: str) -> Optional[str]:
    """
    Look up county name from a US zip code using pgeocode.
    
    Args:
        zip_code: 5-digit US zip code
        
    Returns:
        County name or None if lookup fails
    """
    if not zip_code or len(zip_code) != 5:
        return None
    
    try:
        nomi = _get_nomi()
        geo = nomi.query_postal_code(zip_code)
        
        if geo.empty:
            return None
        
        county = geo.county_name if hasattr(geo, 'county_name') and str(geo.county_name) != 'nan' else None
        return county
    except Exception as e:
        logger.warning(f"Failed to lookup county for zip {zip_code}: {e}")
        return None


def fetch_records_without_county(batch_size: int = 100, offset: int = 0):
    """
    Fetch territory_checks records that have zip_code but no county.
    
    Args:
        batch_size: Number of records to fetch
        offset: Offset for pagination
        
    Returns:
        List of records
    """
    supabase = supabase_client()
    
    response = supabase.table("territory_checks") \
        .select("id, zip_code") \
        .is_("county", "null") \
        .not_.is_("zip_code", "null") \
        .neq("zip_code", "") \
        .range(offset, offset + batch_size - 1) \
        .execute()
    
    return response.data


def update_record_county(record_id: int, county: str) -> bool:
    """
    Update a territory_checks record with county.
    
    Args:
        record_id: ID of the record to update
        county: County name to set
        
    Returns:
        True if successful, False otherwise
    """
    supabase = supabase_client()
    
    try:
        supabase.table("territory_checks") \
            .update({"county": county}) \
            .eq("id", record_id) \
            .execute()
        return True
    except Exception as e:
        logger.error(f"Failed to update record {record_id}: {e}")
        return False


def backfill_counties(dry_run: bool = False, batch_size: int = 100) -> Tuple[int, int, int]:
    """
    Backfill county data for all territory_checks with zip_code but no county.
    
    Args:
        dry_run: If True, don't actually update records
        batch_size: Number of records to process at a time
        
    Returns:
        Tuple of (total_processed, updated_count, skipped_count)
    """
    total_processed = 0
    updated_count = 0
    skipped_count = 0
    offset = 0
    
    logger.info(f"Starting county backfill (dry_run={dry_run}, batch_size={batch_size})")
    
    while True:
        records = fetch_records_without_county(batch_size, offset)
        
        if not records:
            logger.info("No more records to process")
            break
        
        logger.info(f"Processing batch of {len(records)} records (offset={offset})")
        
        for record in records:
            total_processed += 1
            record_id = record["id"]
            zip_code = record["zip_code"]
            
            # Look up county
            county = lookup_county_by_zip(zip_code)
            
            if not county:
                logger.debug(f"Record {record_id}: No county found for zip {zip_code}")
                skipped_count += 1
                continue
            
            if dry_run:
                logger.info(f"[DRY RUN] Record {record_id}: Would set county to '{county}' (zip: {zip_code})")
                updated_count += 1
            else:
                success = update_record_county(record_id, county)
                if success:
                    logger.debug(f"Record {record_id}: Updated county to '{county}'")
                    updated_count += 1
                else:
                    skipped_count += 1
        
        offset += batch_size
        
        # Progress update every 500 records
        if total_processed % 500 == 0:
            logger.info(f"Progress: {total_processed} processed, {updated_count} updated, {skipped_count} skipped")
    
    return total_processed, updated_count, skipped_count


def main():
    parser = argparse.ArgumentParser(
        description="Backfill county data for territory_checks records"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview changes without updating the database"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="Number of records to process at a time (default: 100)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=" * 50)
        logger.info("DRY RUN MODE - No changes will be made")
        logger.info("=" * 50)
    
    total, updated, skipped = backfill_counties(
        dry_run=args.dry_run,
        batch_size=args.batch_size
    )
    
    logger.info("=" * 50)
    logger.info("Backfill Complete!")
    logger.info(f"  Total processed: {total}")
    logger.info(f"  Updated: {updated}")
    logger.info(f"  Skipped (no county found): {skipped}")
    logger.info("=" * 50)


if __name__ == "__main__":
    main()
















