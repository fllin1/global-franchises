#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to sync scraping_runs database record with actual files in storage.
This fixes cases where the scraper was interrupted before updating the database.
"""

from loguru import logger
from src.api.config.supabase_config import supabase_client
from src.data.storage.storage_client import StorageClient
from src.data.functions.extract import Extractor


def main():
    logger.info("Syncing scraping_runs status with actual storage files...")
    
    extractor = Extractor()
    prefix = extractor.today_str
    
    try:
        # Get the most recent scraping run
        supabase = supabase_client()
        response = (
            supabase.table("scraping_runs")
            .select("*")
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if not response.data:
            logger.warning("No scraping run found in database")
            return
        
        run_data = response.data[0]
        run_id = run_data.get("id")
        logger.info(f"Found run ID: {run_id}")
        logger.info(f"Current status: {run_data.get('status')}")
        logger.info(f"Current successful_uploads: {run_data.get('successful_uploads')}")
        
        # Count actual files in storage
        storage_client = StorageClient()
        files = storage_client.list_files(prefix)
        html_files = [f for f in files if f.get("name", "").endswith(".html")]
        actual_count = len(html_files)
        
        logger.info(f"\n=== Storage Check ===")
        logger.info(f"Files found in storage '{prefix}': {actual_count}")
        
        if actual_count > 0:
            logger.success(f"✓ Found {actual_count} HTML files in storage!")
            
            # Update the database record
            logger.info(f"\n=== Updating Database ===")
            update_data = {
                "successful_uploads": actual_count,
                "status": "completed" if actual_count == run_data.get("total_franchises") else "partial"
            }
            
            supabase.table("scraping_runs").update(update_data).eq("id", run_id).execute()
            logger.success(f"✓ Updated run {run_id}:")
            logger.info(f"  Status: {update_data['status']}")
            logger.info(f"  Successful uploads: {actual_count}")
            
            # Show sample files
            logger.info(f"\n=== Sample Files ===")
            for i, file_obj in enumerate(html_files[:10]):
                size_kb = file_obj.get('metadata', {}).get('size', 0) / 1024
                logger.info(f"  {i+1}. {file_obj.get('name')} ({size_kb:.2f} KB)")
            
            if len(html_files) > 10:
                logger.info(f"  ... and {len(html_files) - 10} more files")
        else:
            logger.warning("No files found in storage. Database record may be accurate.")
            
    except Exception as e:
        logger.error(f"Failed to sync status: {e}")
        raise


if __name__ == "__main__":
    main()

