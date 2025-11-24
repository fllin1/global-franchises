#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to run the scraper and display results from Supabase Storage.
"""

from loguru import logger

from src.api.config.supabase_config import supabase_client
from src.data.functions.extract import Extractor
from src.data.storage.storage_client import StorageClient


def main():
    logger.info("Starting scraper run script...")

    # 1. Run Scraper
    extractor = Extractor()
    logger.info(f"Initialized Extractor. Today's prefix: {extractor.today_str}")

    try:
        logger.info("Executing scraper...")
        extractor.scrape()
        logger.success("Scraping execution finished.")
    except Exception as e:
        logger.error(f"Scraping failed: {e}")
        # We continue to try to show results even if it failed, 
        # as partial results might be available.

    # 2. Display Results

    # A. Statistics from Database
    logger.info("\n--- Scraping Run Statistics ---")
    try:
        supabase = supabase_client()
        # Get the most recent run
        response = (
            supabase.table("scraping_runs")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if response.data:
            run_data = response.data[0]
            print(f"Run ID: {run_data.get('id')}")
            print(f"Status: {run_data.get('status')}")
            print(f"Storage Prefix: {run_data.get('storage_path_prefix')}")
            print(f"Total Franchises Expected: {run_data.get('total_franchises')}")
            print(f"Successful Uploads: {run_data.get('successful_uploads')}")
            print(f"Failed Uploads: {run_data.get('failed_uploads')}")
            print(f"Created At: {run_data.get('created_at')}")
            
            # Show processed URLs from metadata if available
            metadata = run_data.get('metadata')
            if metadata and isinstance(metadata, dict):
                processed_count = metadata.get('processed_urls_count', 0)
                sample_urls = metadata.get('sample_urls', [])
                if processed_count > 0:
                    print(f"\nProcessed URLs: {processed_count} total")
                    if sample_urls:
                        print(f"Sample URLs (showing last {len(sample_urls)}):")
                        for url in sample_urls[-10:]:  # Show last 10
                            print(f"  - {url}")
        else:
            logger.warning("No scraping run record found.")

    except Exception as e:
        logger.error(f"Failed to retrieve run statistics: {e}")

    # B. File Listing from Storage
    html_files = []
    logger.info("\n--- Storage File Listing ---")
    try:
        storage_client = StorageClient()
        prefix = extractor.today_str
        files = storage_client.list_files(prefix)
        
        # Filter for HTML files just in case
        html_files = [f for f in files if f.get("name", "").endswith(".html")]
        
        print(f"Total HTML files found in storage '{prefix}': {len(html_files)}")
        
        if html_files:
            print("\nFirst 10 files:")
            for i, file_obj in enumerate(html_files[:10]):
                size_kb = file_obj.get('metadata', {}).get('size', 0) / 1024
                print(f"{i+1}. {file_obj.get('name')} ({size_kb:.2f} KB)")
            
            if len(html_files) > 10:
                print(f"... and {len(html_files) - 10} more files.")
        else:
            logger.warning(f"No HTML files found in prefix '{prefix}'.")

    except Exception as e:
        logger.error(f"Failed to list files from storage: {e}")

    # C. Sample HTML Display
    if html_files:
        logger.info("\n--- Sample HTML Content ---")
        try:
            # Pick the first file
            sample_file_name = html_files[0].get("name")
            sample_path = f"{prefix}/{sample_file_name}"
            
            print(f"Downloading sample file: {sample_path}")
            content = storage_client.download_html(sample_path)
            
            print(f"\nContent Preview (first 500 chars):")
            print("-" * 50)
            print(content[:500])
            print("...")
            print("-" * 50)
            print(f"Total content length: {len(content)} characters")
            
        except Exception as e:
            logger.error(f"Failed to download/display sample file: {e}")


if __name__ == "__main__":
    main()
