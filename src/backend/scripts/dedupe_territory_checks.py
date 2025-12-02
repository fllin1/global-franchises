# -*- coding: utf-8 -*-
"""
Deduplication script for territory_checks table.

Implements geographic hierarchy-based deduplication:
- Geographic hierarchy: Zip ⊂ City ⊂ County ⊂ State
- If status = "Not Available": Keep BROADER scope (more restrictive)
- If status = "Available": Keep SPECIFIC scope (more informative)
- Mixed status: Newer check_date always wins
- Exact duplicates: Keep record with most recent check_date

Usage:
    python -m src.backend.scripts.dedupe_territory_checks [--dry-run] [--franchise-id=50]
"""

import argparse
import asyncio
from collections import defaultdict
from datetime import datetime
from typing import Dict, Any, List, Optional, Set, Tuple

import pgeocode
from loguru import logger

from src.api.config.supabase_config import supabase_client


# Scope levels (lower = more specific)
SCOPE_ZIP = 1
SCOPE_CITY = 2
SCOPE_COUNTY = 3
SCOPE_STATE = 4

# Initialize pgeocode for zip lookups
_nomi_us = None


def _get_nomi_us():
    """Lazy initialization of pgeocode for US."""
    global _nomi_us
    if _nomi_us is None:
        _nomi_us = pgeocode.Nominatim('us')
    return _nomi_us


def get_scope_level(record: Dict[str, Any]) -> int:
    """
    Get the geographic scope level of a record.
    Lower number = more specific scope.
    
    Returns:
        1 = zip_code present (most specific)
        2 = city present, no zip
        3 = county present, no city
        4 = state only (broadest)
    """
    if record.get("zip_code"):
        return SCOPE_ZIP
    if record.get("city"):
        return SCOPE_CITY
    if record.get("county"):
        return SCOPE_COUNTY
    return SCOPE_STATE


def get_location_key(record: Dict[str, Any]) -> Tuple[str, ...]:
    """
    Generate a hierarchical location key for grouping.
    
    Returns tuple: (state_code, county, city, zip_code)
    Normalized to lowercase for comparison.
    """
    state = (record.get("state_code") or "").upper()
    county = (record.get("county") or "").lower().replace(" county", "")
    city = (record.get("city") or "").lower()
    zip_code = (record.get("zip_code") or "").strip()
    
    return (state, county, city, zip_code)


def is_location_contained_in(
    specific: Dict[str, Any], 
    broader: Dict[str, Any],
) -> bool:
    """
    Check if the specific location is geographically contained in the broader location.
    
    Examples:
    - zip 46077 is contained in city Indianapolis
    - city Indianapolis is contained in county Marion
    - county Marion is contained in state IN
    
    Args:
        specific: Record with more specific scope (zip or city)
        broader: Record with broader scope (city, county, or state)
        
    Returns:
        True if specific is contained within broader
    """
    specific_scope = get_scope_level(specific)
    broader_scope = get_scope_level(broader)
    
    # Specific must be more specific (lower scope level)
    if specific_scope >= broader_scope:
        return False
    
    # Must be in the same state
    if specific.get("state_code") != broader.get("state_code"):
        return False
    
    # Check containment based on scope levels
    if broader_scope == SCOPE_STATE:
        # Everything in the state is contained in state-level
        return True
    
    if broader_scope == SCOPE_COUNTY:
        # Check if specific is in the same county
        specific_county = (specific.get("county") or "").lower()
        broader_county = (broader.get("county") or "").lower()
        
        # If specific has county, compare directly
        if specific_county:
            return specific_county == broader_county
        
        # If specific only has zip, look up county
        if specific.get("zip_code"):
            zip_county = lookup_county_for_zip(specific["zip_code"])
            if zip_county:
                return zip_county.lower() == broader_county
        
        return False
    
    if broader_scope == SCOPE_CITY:
        # Check if specific (zip) is in the same city
        specific_city = (specific.get("city") or "").lower()
        broader_city = (broader.get("city") or "").lower()
        
        # If specific has city, compare directly
        if specific_city:
            return specific_city == broader_city
        
        # If specific only has zip, look up city
        if specific.get("zip_code"):
            zip_city = lookup_city_for_zip(specific["zip_code"])
            if zip_city:
                return zip_city.lower() == broader_city
        
        return False
    
    return False


def lookup_county_for_zip(zip_code: str) -> Optional[str]:
    """Look up county name for a US zip code."""
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


def lookup_city_for_zip(zip_code: str) -> Optional[str]:
    """Look up city name for a US zip code."""
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


def parse_check_date(date_val: Any) -> Optional[datetime]:
    """Parse a check_date value into a datetime object."""
    if date_val is None:
        return None
    
    if isinstance(date_val, datetime):
        return date_val
    
    if isinstance(date_val, str):
        # Try ISO format first
        try:
            return datetime.fromisoformat(date_val.replace('Z', '+00:00'))
        except ValueError:
            pass
        
        # Try common formats
        for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%Y-%m-%dT%H:%M:%S"]:
            try:
                return datetime.strptime(date_val.split('+')[0].split('.')[0], fmt)
            except ValueError:
                continue
    
    return None


def dedupe_records_for_franchise(
    records: List[Dict[str, Any]],
) -> Tuple[List[int], List[int]]:
    """
    Apply deduplication rules to records for a single franchise.
    
    Dedup Rules:
    1. Exact duplicates (same location_raw): keep newest check_date
    2. Not Available + broader scope newer: keep broader (supersedes specific)
    3. Available + specific scope: keep specific (more informative)
    4. Mixed status: newer check_date wins
    
    Args:
        records: List of territory_check records for one franchise
        
    Returns:
        Tuple of (keep_ids, delete_ids)
    """
    if len(records) <= 1:
        return ([r["id"] for r in records], [])
    
    keep_ids: Set[int] = set()
    delete_ids: Set[int] = set()
    
    # Sort by check_date descending (newest first)
    sorted_records = sorted(
        records,
        key=lambda r: parse_check_date(r.get("check_date")) or datetime.min,
        reverse=True,
    )
    
    # Step 1: Handle exact duplicates (same location_raw)
    location_raw_groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in sorted_records:
        loc_raw = (record.get("location_raw") or "").strip().lower()
        location_raw_groups[loc_raw].append(record)
    
    # For each group of exact duplicates, keep only the newest
    deduplicated_records = []
    for loc_raw, group in location_raw_groups.items():
        if len(group) > 1:
            # Keep the first (newest due to sorting)
            keep_ids.add(group[0]["id"])
            for r in group[1:]:
                delete_ids.add(r["id"])
            deduplicated_records.append(group[0])
        else:
            deduplicated_records.append(group[0])
    
    # Step 2: Apply geographic hierarchy rules
    # Group by normalized location for hierarchy comparisons
    # Compare each pair of remaining records
    
    processed_pairs: Set[Tuple[int, int]] = set()
    
    for i, rec_a in enumerate(deduplicated_records):
        if rec_a["id"] in delete_ids:
            continue
            
        for j, rec_b in enumerate(deduplicated_records):
            if i >= j:  # Skip self and already-processed pairs
                continue
            if rec_b["id"] in delete_ids:
                continue
            
            pair_key = tuple(sorted([rec_a["id"], rec_b["id"]]))
            if pair_key in processed_pairs:
                continue
            processed_pairs.add(pair_key)
            
            # Check if one contains the other
            a_scope = get_scope_level(rec_a)
            b_scope = get_scope_level(rec_b)
            
            # Determine which is more specific vs broader
            if a_scope < b_scope:
                specific, broader = rec_a, rec_b
            elif b_scope < a_scope:
                specific, broader = rec_b, rec_a
            else:
                # Same scope level - compare by date if statuses match
                status_a = rec_a.get("availability_status", "")
                status_b = rec_b.get("availability_status", "")
                
                if status_a == status_b:
                    # Same status, same scope - keep newest (already sorted)
                    date_a = parse_check_date(rec_a.get("check_date"))
                    date_b = parse_check_date(rec_b.get("check_date"))
                    
                    # Check if they're the same location
                    if get_location_key(rec_a) == get_location_key(rec_b):
                        if date_a and date_b:
                            if date_a >= date_b:
                                delete_ids.add(rec_b["id"])
                            else:
                                delete_ids.add(rec_a["id"])
                continue
            
            # Check containment
            if not is_location_contained_in(specific, broader):
                continue
            
            # Apply hierarchy rules based on status
            specific_status = specific.get("availability_status", "")
            broader_status = broader.get("availability_status", "")
            
            specific_date = parse_check_date(specific.get("check_date"))
            broader_date = parse_check_date(broader.get("check_date"))
            
            # Rule 4: Mixed status - newer wins
            if specific_status != broader_status:
                if broader_date and specific_date:
                    if broader_date > specific_date:
                        # Broader is newer - status changed, delete specific
                        delete_ids.add(specific["id"])
                        logger.debug(
                            f"Mixed status: Keeping {broader['id']} (newer {broader_status}), "
                            f"deleting {specific['id']} ({specific_status})"
                        )
                    else:
                        # Specific is newer - status changed, keep specific
                        # Don't delete broader as it might apply to other areas
                        pass
                continue
            
            # Same status - apply hierarchy rules
            if "Not Available" in specific_status:
                # Rule 2: Not Available - keep broader scope (more restrictive)
                if broader_date and specific_date and broader_date >= specific_date:
                    delete_ids.add(specific["id"])
                    logger.debug(
                        f"Not Available: Keeping broader {broader['id']}, "
                        f"deleting specific {specific['id']}"
                    )
            elif "Available" in specific_status:
                # Rule 3: Available - keep specific scope (more informative)
                # Don't delete broader as it provides general info
                # But if broader is older, it's redundant
                if specific_date and broader_date and specific_date >= broader_date:
                    delete_ids.add(broader["id"])
                    logger.debug(
                        f"Available: Keeping specific {specific['id']}, "
                        f"deleting broader {broader['id']}"
                    )
    
    # Calculate final keep list
    all_ids = {r["id"] for r in records}
    keep_ids = all_ids - delete_ids
    
    return (list(keep_ids), list(delete_ids))


async def fetch_franchise_records(franchise_id: int) -> List[Dict[str, Any]]:
    """Fetch all territory_checks for a franchise."""
    supabase = supabase_client()
    
    response = supabase.table("territory_checks") \
        .select("*") \
        .eq("franchise_id", franchise_id) \
        .execute()
    
    return response.data


async def fetch_all_franchise_ids() -> List[int]:
    """Fetch all distinct franchise IDs with territory checks."""
    supabase = supabase_client()
    
    response = supabase.table("territory_checks") \
        .select("franchise_id") \
        .execute()
    
    # Get unique franchise IDs
    franchise_ids = list(set(r["franchise_id"] for r in response.data if r.get("franchise_id")))
    return sorted(franchise_ids)


async def delete_records(record_ids: List[int], dry_run: bool = False) -> int:
    """
    Delete territory_check records by ID.
    
    Args:
        record_ids: List of record IDs to delete
        dry_run: If True, don't actually delete
        
    Returns:
        Number of records deleted
    """
    if not record_ids:
        return 0
    
    if dry_run:
        logger.info(f"[DRY RUN] Would delete {len(record_ids)} records: {record_ids[:10]}...")
        return len(record_ids)
    
    supabase = supabase_client()
    
    # Delete in batches to avoid query limits
    batch_size = 100
    deleted = 0
    
    for i in range(0, len(record_ids), batch_size):
        batch = record_ids[i:i + batch_size]
        try:
            supabase.table("territory_checks") \
                .delete() \
                .in_("id", batch) \
                .execute()
            deleted += len(batch)
        except Exception as e:
            logger.error(f"Failed to delete batch: {e}")
    
    return deleted


async def dedupe_franchise(
    franchise_id: int,
    dry_run: bool = False,
) -> Dict[str, int]:
    """
    Run deduplication for a single franchise.
    
    Args:
        franchise_id: The franchise to dedupe
        dry_run: If True, preview changes without deleting
        
    Returns:
        Stats dict
    """
    stats = {
        "franchise_id": franchise_id,
        "total_records": 0,
        "kept": 0,
        "deleted": 0,
    }
    
    records = await fetch_franchise_records(franchise_id)
    stats["total_records"] = len(records)
    
    if len(records) <= 1:
        stats["kept"] = len(records)
        return stats
    
    keep_ids, delete_ids = dedupe_records_for_franchise(records)
    
    stats["kept"] = len(keep_ids)
    stats["deleted"] = len(delete_ids)
    
    if delete_ids:
        deleted_count = await delete_records(delete_ids, dry_run)
        if not dry_run:
            logger.info(f"Franchise {franchise_id}: Deleted {deleted_count} duplicates")
    
    return stats


async def dedupe_all(
    dry_run: bool = False,
    franchise_id: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Run deduplication for all franchises (or a specific one).
    
    Args:
        dry_run: If True, preview changes
        franchise_id: If provided, only dedupe this franchise
        
    Returns:
        Aggregated stats
    """
    total_stats = {
        "franchises_processed": 0,
        "total_records": 0,
        "total_kept": 0,
        "total_deleted": 0,
    }
    
    if franchise_id:
        franchise_ids = [franchise_id]
    else:
        franchise_ids = await fetch_all_franchise_ids()
    
    logger.info(f"Processing {len(franchise_ids)} franchises (dry_run={dry_run})")
    
    for fid in franchise_ids:
        stats = await dedupe_franchise(fid, dry_run)
        
        total_stats["franchises_processed"] += 1
        total_stats["total_records"] += stats["total_records"]
        total_stats["total_kept"] += stats["kept"]
        total_stats["total_deleted"] += stats["deleted"]
        
        # Progress every 100 franchises
        if total_stats["franchises_processed"] % 100 == 0:
            logger.info(f"Progress: {total_stats}")
    
    return total_stats


async def main():
    """Main entry point for deduplication script."""
    parser = argparse.ArgumentParser(
        description="Deduplicate territory_checks using geographic hierarchy rules"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview deletions without actually deleting"
    )
    parser.add_argument(
        "--franchise-id", type=int,
        help="Process only this franchise (for testing)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=" * 50)
        logger.info("DRY RUN MODE - No records will be deleted")
        logger.info("=" * 50)
    
    stats = await dedupe_all(
        dry_run=args.dry_run,
        franchise_id=args.franchise_id,
    )
    
    logger.info("=" * 50)
    logger.info("Deduplication Complete!")
    logger.info(f"  Franchises processed: {stats['franchises_processed']}")
    logger.info(f"  Total records examined: {stats['total_records']}")
    logger.info(f"  Records kept: {stats['total_kept']}")
    logger.info(f"  Records deleted: {stats['total_deleted']}")
    logger.info("=" * 50)


if __name__ == "__main__":
    asyncio.run(main())





