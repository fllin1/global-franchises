#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run the Family of Brands scraper.

This script:
1. Scrapes the Family of Brands listing page
2. Scrapes each family brand detail page
3. Stores HTML files in Supabase Storage
4. Saves family brand data to the database
5. Links franchises to their parent family brands

Usage:
    python -m src.backend.scripts.run_family_brands_scraper
    
    # Or with specific options:
    python -m src.backend.scripts.run_family_brands_scraper --single 2353  # Scrape only Driven Brands
    python -m src.backend.scripts.run_family_brands_scraper --list-only    # Just list family brands
"""

import argparse
from datetime import datetime

from loguru import logger

from src.api.config.supabase_config import supabase_client
from src.data.storage.storage_client import StorageClient
from src.data.franserve.family_brands_scraper import (
    FamilyBrandsConfig,
    FamilyBrandData,
    get_authenticated_session,
    get_family_brands_list,
    scrape_family_brand_page,
    parse_family_brand_html,
    upload_family_brand_html,
    save_family_brand_to_db,
    link_franchises_to_family_brand,
    scrape_all_family_brands,
)


def list_family_brands():
    """List all family brands without scraping details."""
    logger.info("Listing all family brands...")
    
    session = get_authenticated_session()
    logger.success("Authenticated with FranServe")
    family_brands = get_family_brands_list(session)
    
    print(f"\n=== Found {len(family_brands)} Family Brands ===\n")
    for idx, (name, url, source_id) in enumerate(family_brands, 1):
        print(f"{idx:3}. {name} (FranID={source_id})")
    
    return family_brands


def scrape_single_family_brand(source_id: int):
    """
    Scrape a single family brand by its source_id (FranID).
    
    Args:
        source_id: The FranID of the family brand to scrape
    """
    logger.info(f"Scraping single family brand with FranID={source_id}")
    
    # Get authenticated session
    session = get_authenticated_session()
    logger.success("Authenticated with FranServe")
    
    # Initialize clients
    storage_client = StorageClient()
    supabase = supabase_client()
    
    # Build URL
    url = f"{FamilyBrandsConfig.FAMILY_BRAND_DETAIL_URL}{source_id}"
    
    # Get today's date for storage prefix
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    
    try:
        # Scrape the page
        logger.info(f"Scraping: {url}")
        soup = scrape_family_brand_page(session, url)
        
        # Save HTML to storage
        file_path = f"{FamilyBrandsConfig.STORAGE_PREFIX}/{date_prefix}/FranID_{source_id}.html"
        upload_family_brand_html(soup, file_path, storage_client)
        logger.success(f"Saved HTML to storage: {file_path}")
        
        # Parse the HTML
        data = parse_family_brand_html(soup, source_id)
        
        # Display parsed data
        print(f"\n=== Family Brand: {data.name} ===")
        print(f"Source ID: {data.source_id}")
        print(f"Website: {data.website_url}")
        print(f"Contact: {data.contact_name}")
        print(f"Phone: {data.contact_phone}")
        print(f"Email: {data.contact_email}")
        print(f"Logo URL: {data.logo_url}")
        print(f"Last Updated: {data.last_updated_from_source}")
        print(f"\nRepresenting Brands ({len(data.representing_brand_ids)}):")
        for name, fran_id in zip(data.representing_brand_names, data.representing_brand_ids):
            print(f"  - {name} (FranID={fran_id})")
        
        # Save to database
        db_id = save_family_brand_to_db(data, supabase)
        
        if db_id:
            logger.success(f"Saved to database with ID: {db_id}")
            
            # Link franchises
            linked = link_franchises_to_family_brand(
                db_id,
                data.representing_brand_ids,
                supabase
            )
            logger.success(f"Linked {linked} franchises to this family brand")
        else:
            logger.error("Failed to save to database")
        
        return data
        
    except Exception as e:
        logger.error(f"Error scraping family brand {source_id}: {e}")
        raise


def run_full_scrape():
    """Run the full family brands scraper."""
    logger.info("Starting full Family of Brands scraper run...")
    
    # Get authenticated session
    session = get_authenticated_session()
    logger.success("Authenticated with FranServe")
    
    # Initialize clients
    storage_client = StorageClient()
    supabase = supabase_client()
    
    # Get today's date for storage prefix
    date_prefix = datetime.now().strftime("%Y-%m-%d")
    
    # Run the scraper
    stats = scrape_all_family_brands(
        session=session,
        storage_client=storage_client,
        supabase_client=supabase,
        date_prefix=date_prefix
    )
    
    # Display results
    print("\n" + "=" * 50)
    print("FAMILY BRANDS SCRAPER RESULTS")
    print("=" * 50)
    print(f"Total Family Brands Found: {stats['total_found']}")
    print(f"Successfully Scraped: {stats['scraped_success']}")
    print(f"Failed to Scrape: {stats['scraped_failed']}")
    print(f"Saved to Database: {stats['saved_to_db']}")
    print(f"Franchises Linked: {stats['franchises_linked']}")
    print("=" * 50)
    
    return stats


def show_database_stats():
    """Show current family brands statistics from the database."""
    logger.info("Fetching family brands statistics from database...")
    
    supabase = supabase_client()
    
    # Count family brands
    family_brands_result = supabase.table("family_of_brands").select("id", count="exact").execute()
    family_brands_count = family_brands_result.count if family_brands_result.count else 0
    
    # Count franchises with family brand links
    linked_franchises_result = supabase.table("franchises").select(
        "id", count="exact"
    ).not_.is_("parent_family_brand_id", "null").execute()
    linked_count = linked_franchises_result.count if linked_franchises_result.count else 0
    
    # Get total franchises
    total_franchises_result = supabase.table("franchises").select("id", count="exact").execute()
    total_franchises = total_franchises_result.count if total_franchises_result.count else 0
    
    print("\n=== Family Brands Database Statistics ===")
    print(f"Total Family Brands: {family_brands_count}")
    print(f"Franchises with Family Brand Link: {linked_count}")
    print(f"Total Franchises: {total_franchises}")
    if total_franchises > 0:
        print(f"Percentage Linked: {linked_count / total_franchises * 100:.1f}%")
    
    # List family brands with their franchise counts
    if family_brands_count > 0:
        print("\n--- Family Brands ---")
        family_brands = supabase.table("family_of_brands").select("*").execute()
        
        for fb in family_brands.data:
            # Count franchises for this family brand
            count_result = supabase.table("franchises").select(
                "id", count="exact"
            ).eq("parent_family_brand_id", fb["id"]).execute()
            franchise_count = count_result.count if count_result.count else 0
            
            print(f"  {fb['name']} (FranID={fb['source_id']}): {franchise_count} franchises")


def main():
    parser = argparse.ArgumentParser(
        description="Family of Brands Scraper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python -m src.backend.scripts.run_family_brands_scraper              # Full scrape
  python -m src.backend.scripts.run_family_brands_scraper --list-only  # List brands only
  python -m src.backend.scripts.run_family_brands_scraper --single 2353  # Scrape Driven Brands
  python -m src.backend.scripts.run_family_brands_scraper --stats      # Show database stats
        """
    )
    
    parser.add_argument(
        "--list-only",
        action="store_true",
        help="Only list family brands without scraping details"
    )
    
    parser.add_argument(
        "--single",
        type=int,
        metavar="FRAN_ID",
        help="Scrape a single family brand by its FranID"
    )
    
    parser.add_argument(
        "--stats",
        action="store_true",
        help="Show current family brands statistics from database"
    )
    
    args = parser.parse_args()
    
    if args.stats:
        show_database_stats()
    elif args.list_only:
        list_family_brands()
    elif args.single:
        scrape_single_family_brand(args.single)
    else:
        run_full_scrape()


if __name__ == "__main__":
    main()

