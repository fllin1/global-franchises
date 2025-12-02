# -*- coding: utf-8 -*-
"""
Backfill logo URLs for existing franchises.

This script extracts logo URLs from HTML files stored in Supabase Storage
and updates the franchises table with the extracted URLs.
"""

import re
from typing import Optional

from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from src.api.config.supabase_config import supabase_client
from src.data.storage.storage_client import StorageClient


FRANSERVE_BASE_URL = "https://franservesupport.com/"


def extract_logo_url_from_html(html_content: str) -> Optional[str]:
    """
    Extract the logo URL from franchise HTML content.
    
    Args:
        html_content: Raw HTML content of the franchise page
        
    Returns:
        Full URL to the logo image, or None if not found
    """
    soup = BeautifulSoup(html_content, "html.parser")
    
    # Look for logo images in the images/logos/ directory
    logo_img = soup.find("img", src=re.compile(r"images/logos/"))
    if logo_img:
        logo_src = logo_img.get("src", "")
        if logo_src and not logo_src.startswith("http"):
            return f"{FRANSERVE_BASE_URL}{logo_src}"
        elif logo_src:
            return logo_src
    
    return None


def get_franchises_without_logo() -> list[dict]:
    """
    Get all franchises that don't have a logo_url set.
    
    Returns:
        List of franchise records with id, source_id, and franchise_name
    """
    client = supabase_client()
    response = (
        client.table("franchises")
        .select("id, source_id, franchise_name")
        .is_("logo_url", "null")
        .execute()
    )
    return response.data


def get_html_from_storage(storage_client: StorageClient, source_id: int) -> Optional[str]:
    """
    Try to retrieve HTML content for a franchise from Supabase Storage.
    
    Searches in the most recent scraping run folder first, then falls back
    to looking in all date-prefixed folders.
    
    Args:
        storage_client: StorageClient instance
        source_id: The franchise source_id (FranID)
        
    Returns:
        HTML content as string, or None if not found
    """
    file_name = f"FranID_{source_id}.html"
    
    try:
        # List folders in the bucket (root level)
        folders = storage_client.list_files("")
        
        # Filter for date-prefixed folders and sort by date (most recent first)
        date_folders = sorted(
            [f["name"] for f in folders if f.get("name") and f["name"][0].isdigit()],
            reverse=True
        )
        
        # Try each folder until we find the file
        for folder in date_folders:
            file_path = f"{folder}/{file_name}"
            try:
                content = storage_client.download_html(file_path)
                if content:
                    return content
            except Exception:
                continue  # File not in this folder, try next
                
    except Exception as e:
        logger.warning(f"Error accessing storage for source_id {source_id}: {e}")
    
    return None


def update_franchise_logo(franchise_id: int, logo_url: str) -> bool:
    """
    Update the logo_url for a franchise.
    
    Args:
        franchise_id: Database ID of the franchise
        logo_url: URL to the logo image
        
    Returns:
        True if update was successful, False otherwise
    """
    try:
        client = supabase_client()
        client.table("franchises").update({"logo_url": logo_url}).eq("id", franchise_id).execute()
        return True
    except Exception as e:
        logger.error(f"Error updating franchise {franchise_id}: {e}")
        return False


def backfill_logos(dry_run: bool = False) -> dict:
    """
    Main function to backfill logo URLs for all franchises.
    
    Args:
        dry_run: If True, don't actually update the database
        
    Returns:
        Dictionary with statistics about the backfill operation
    """
    stats = {
        "total": 0,
        "found": 0,
        "updated": 0,
        "not_found": 0,
        "errors": 0,
    }
    
    logger.info("Starting logo URL backfill...")
    
    # Get franchises without logos
    franchises = get_franchises_without_logo()
    stats["total"] = len(franchises)
    
    if not franchises:
        logger.info("No franchises need logo URL backfill")
        return stats
    
    logger.info(f"Found {len(franchises)} franchises without logo URLs")
    
    # Initialize storage client
    storage_client = StorageClient()
    
    # Process each franchise
    for franchise in tqdm(franchises, desc="Backfilling logos"):
        source_id = franchise.get("source_id")
        franchise_id = franchise.get("id")
        franchise_name = franchise.get("franchise_name", "Unknown")
        
        if not source_id:
            logger.warning(f"Franchise {franchise_id} ({franchise_name}) has no source_id")
            stats["errors"] += 1
            continue
        
        # Get HTML from storage
        html_content = get_html_from_storage(storage_client, source_id)
        
        if not html_content:
            logger.debug(f"No HTML found for {franchise_name} (source_id: {source_id})")
            stats["not_found"] += 1
            continue
        
        # Extract logo URL
        logo_url = extract_logo_url_from_html(html_content)
        
        if not logo_url:
            logger.debug(f"No logo found in HTML for {franchise_name}")
            stats["not_found"] += 1
            continue
        
        stats["found"] += 1
        
        # Update database
        if dry_run:
            logger.info(f"[DRY RUN] Would update {franchise_name}: {logo_url}")
        else:
            if update_franchise_logo(franchise_id, logo_url):
                stats["updated"] += 1
            else:
                stats["errors"] += 1
    
    # Log summary
    logger.info("=" * 50)
    logger.info("Backfill Summary:")
    logger.info(f"  Total franchises processed: {stats['total']}")
    logger.info(f"  Logos found: {stats['found']}")
    logger.info(f"  Successfully updated: {stats['updated']}")
    logger.info(f"  Not found (no HTML or no logo): {stats['not_found']}")
    logger.info(f"  Errors: {stats['errors']}")
    logger.info("=" * 50)
    
    return stats


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Backfill logo URLs for franchises")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without actually updating the database"
    )
    args = parser.parse_args()
    
    backfill_logos(dry_run=args.dry_run)

