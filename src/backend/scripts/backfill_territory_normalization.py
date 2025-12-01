# -*- coding: utf-8 -*-
"""
Backfill orchestrator for territory normalization.

Pipeline:
1. Apply migration (add 'country' and 'is_resale' columns)
2. Run LLM parser on unparsed records
3. Run deduplication per franchise
4. Report statistics

Usage:
    python -m src.backend.scripts.backfill_territory_normalization [--dry-run] [--limit=1000]
"""

import argparse
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

from loguru import logger

from src.api.config.supabase_config import supabase_client


async def check_columns_exist() -> Dict[str, bool]:
    """Check if the new columns already exist in territory_checks."""
    supabase = supabase_client()
    
    result = {"country": False, "is_resale": False}
    
    # Try a simple query to see which columns exist
    try:
        test = supabase.table("territory_checks") \
            .select("id, country, is_resale") \
            .limit(1) \
            .execute()
        result["country"] = True
        result["is_resale"] = True
    except Exception as e:
        error_str = str(e)
        # Check which column is missing
        if "country" not in error_str:
            result["country"] = True
        if "is_resale" not in error_str:
            result["is_resale"] = True
    
    return result


async def apply_migration(dry_run: bool = False) -> bool:
    """
    Apply the migration to add new columns.
    
    Note: This requires manual execution via Supabase dashboard or CLI
    for DDL operations. This function logs the SQL to run.
    """
    migration_sql = """
-- Migration: Add territory normalization fields
-- Run this in Supabase SQL Editor

ALTER TABLE territory_checks 
ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'US';

ALTER TABLE territory_checks 
ADD COLUMN IF NOT EXISTS is_resale BOOLEAN DEFAULT FALSE;

CREATE INDEX IF NOT EXISTS idx_territory_checks_country ON territory_checks(country);
CREATE INDEX IF NOT EXISTS idx_territory_checks_is_resale ON territory_checks(is_resale) WHERE is_resale = TRUE;

COMMENT ON COLUMN territory_checks.country IS 'ISO 3166-1 alpha-2 country code (e.g., US, CA for Canada). Defaults to US.';
COMMENT ON COLUMN territory_checks.is_resale IS 'Whether this territory check is for a resale opportunity';
"""
    
    logger.info("Migration SQL (run in Supabase SQL Editor if not already applied):")
    logger.info(migration_sql)
    
    # Check if columns already exist
    columns_exist = await check_columns_exist()
    
    if columns_exist.get("country") and columns_exist.get("is_resale"):
        logger.success("Migration already applied - columns exist")
        return True
    
    if dry_run:
        logger.info("[DRY RUN] Would apply migration - please run SQL manually")
        return True
    
    # Try to execute via RPC (may fail if no permissions)
    try:
        supabase = supabase_client()
        supabase.rpc("exec_sql", {"sql": migration_sql}).execute()
        logger.success("Migration applied successfully")
        return True
    except Exception as e:
        logger.warning(f"Could not apply migration via API: {e}")
        logger.warning("Please run the migration SQL manually in Supabase dashboard")
        return False


async def get_unparsed_count() -> int:
    """Get count of records needing parsing."""
    supabase = supabase_client()
    
    response = supabase.table("territory_checks") \
        .select("id", count="exact") \
        .is_("city", "null") \
        .is_("county", "null") \
        .not_.is_("location_raw", "null") \
        .execute()
    
    return response.count or 0


async def get_total_count() -> int:
    """Get total count of territory_checks."""
    supabase = supabase_client()
    
    response = supabase.table("territory_checks") \
        .select("id", count="exact") \
        .execute()
    
    return response.count or 0


async def run_parser(
    limit: int = 1000,
    dry_run: bool = False,
    delay: float = 0.5,
) -> Dict[str, int]:
    """
    Run the location parser on unparsed records.
    
    Args:
        limit: Maximum records to process
        dry_run: If True, don't modify database
        delay: Delay between LLM calls
        
    Returns:
        Stats from parser
    """
    from src.backend.scripts.parse_territory_locations import process_batch
    
    total_stats = {
        "processed": 0,
        "updated": 0,
        "split": 0,
        "skipped": 0,
        "errors": 0,
    }
    
    batch_size = 100
    processed_total = 0
    
    while processed_total < limit:
        current_limit = min(batch_size, limit - processed_total)
        
        stats = await process_batch(
            limit=current_limit,
            dry_run=dry_run,
            delay_seconds=delay,
        )
        
        # Aggregate stats
        for key in total_stats:
            total_stats[key] += stats.get(key, 0)
        
        processed_total += stats.get("processed", 0)
        
        # Stop if no more records to process
        if stats.get("processed", 0) == 0:
            break
        
        logger.info(f"Parser progress: {processed_total}/{limit} processed")
    
    return total_stats


async def run_dedup(
    dry_run: bool = False,
    franchise_id: int | None = None,
) -> Dict[str, int]:
    """
    Run deduplication.
    
    Args:
        dry_run: If True, don't delete records
        franchise_id: If provided, only dedupe this franchise
        
    Returns:
        Stats from dedup
    """
    from src.backend.scripts.dedupe_territory_checks import dedupe_all
    
    stats = await dedupe_all(
        dry_run=dry_run,
        franchise_id=franchise_id,
    )
    
    return stats


async def run_backfill(
    dry_run: bool = False,
    limit: int = 1000,
    skip_parse: bool = False,
    skip_dedup: bool = False,
    franchise_id: int | None = None,
    delay: float = 0.5,
) -> Dict[str, Any]:
    """
    Run the full backfill pipeline.
    
    Args:
        dry_run: If True, preview changes without modifying database
        limit: Maximum records to parse
        skip_parse: Skip the parsing step
        skip_dedup: Skip the deduplication step
        franchise_id: If provided, only dedupe this franchise
        delay: Delay between LLM calls
        
    Returns:
        Combined stats from all steps
    """
    start_time = datetime.now()
    
    results = {
        "started_at": start_time.isoformat(),
        "dry_run": dry_run,
        "migration": {"status": "skipped"},
        "parser": {"status": "skipped"},
        "dedup": {"status": "skipped"},
        "summary": {},
    }
    
    # Pre-stats
    total_before = await get_total_count()
    unparsed_before = await get_unparsed_count()
    
    logger.info("=" * 60)
    logger.info("Territory Normalization Backfill")
    logger.info("=" * 60)
    logger.info(f"Dry Run: {dry_run}")
    logger.info(f"Records before: {total_before} total, {unparsed_before} unparsed")
    logger.info("=" * 60)
    
    # Step 1: Check/Apply Migration
    logger.info("\n[Step 1/3] Checking Migration...")
    migration_ok = await apply_migration(dry_run)
    results["migration"] = {
        "status": "success" if migration_ok else "needs_manual_apply",
    }
    
    # Step 2: Parse Locations
    if not skip_parse:
        logger.info(f"\n[Step 2/3] Parsing locations (limit={limit})...")
        try:
            parser_stats = await run_parser(
                limit=limit,
                dry_run=dry_run,
                delay=delay,
            )
            results["parser"] = {
                "status": "success",
                **parser_stats,
            }
            logger.info(f"Parser results: {parser_stats}")
        except Exception as e:
            logger.error(f"Parser failed: {e}")
            results["parser"] = {"status": "error", "error": str(e)}
    else:
        logger.info("\n[Step 2/3] Skipping parsing (--skip-parse)")
    
    # Step 3: Deduplicate
    if not skip_dedup:
        logger.info("\n[Step 3/3] Running deduplication...")
        try:
            dedup_stats = await run_dedup(
                dry_run=dry_run,
                franchise_id=franchise_id,
            )
            results["dedup"] = {
                "status": "success",
                **dedup_stats,
            }
            logger.info(f"Dedup results: {dedup_stats}")
        except Exception as e:
            logger.error(f"Dedup failed: {e}")
            results["dedup"] = {"status": "error", "error": str(e)}
    else:
        logger.info("\n[Step 3/3] Skipping deduplication (--skip-dedup)")
    
    # Post-stats
    total_after = await get_total_count()
    unparsed_after = await get_unparsed_count()
    
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    results["summary"] = {
        "records_before": total_before,
        "records_after": total_after,
        "unparsed_before": unparsed_before,
        "unparsed_after": unparsed_after,
        "records_added": total_after - total_before + results.get("dedup", {}).get("total_deleted", 0),
        "records_deleted": results.get("dedup", {}).get("total_deleted", 0),
        "duration_seconds": duration,
    }
    results["completed_at"] = end_time.isoformat()
    
    # Final summary
    logger.info("\n" + "=" * 60)
    logger.info("BACKFILL COMPLETE")
    logger.info("=" * 60)
    logger.info(f"Duration: {duration:.1f} seconds")
    logger.info(f"Records: {total_before} → {total_after}")
    logger.info(f"Unparsed: {unparsed_before} → {unparsed_after}")
    if results.get("parser", {}).get("split", 0) > 0:
        logger.info(f"New records from splits: {results['parser']['split']}")
    if results.get("dedup", {}).get("total_deleted", 0) > 0:
        logger.info(f"Duplicates removed: {results['dedup']['total_deleted']}")
    logger.info("=" * 60)
    
    return results


async def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Run territory normalization backfill pipeline"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Preview changes without modifying database"
    )
    parser.add_argument(
        "--limit", type=int, default=1000,
        help="Maximum records to parse (default: 1000)"
    )
    parser.add_argument(
        "--skip-parse", action="store_true",
        help="Skip the location parsing step"
    )
    parser.add_argument(
        "--skip-dedup", action="store_true",
        help="Skip the deduplication step"
    )
    parser.add_argument(
        "--franchise-id", type=int,
        help="Only dedupe this specific franchise (for testing)"
    )
    parser.add_argument(
        "--delay", type=float, default=0.5,
        help="Delay between LLM calls in seconds (default: 0.5)"
    )
    
    args = parser.parse_args()
    
    if args.dry_run:
        logger.info("=" * 60)
        logger.info("DRY RUN MODE - No changes will be made to the database")
        logger.info("=" * 60)
    
    results = await run_backfill(
        dry_run=args.dry_run,
        limit=args.limit,
        skip_parse=args.skip_parse,
        skip_dedup=args.skip_dedup,
        franchise_id=args.franchise_id,
        delay=args.delay,
    )
    
    # Output JSON results for logging/debugging
    import json
    logger.debug(f"Full results:\n{json.dumps(results, indent=2)}")


if __name__ == "__main__":
    asyncio.run(main())

