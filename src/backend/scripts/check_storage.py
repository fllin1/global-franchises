#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to check Supabase Storage for scraped HTML files.
"""

from loguru import logger
from src.data.storage.storage_client import StorageClient
from src.data.functions.extract import Extractor
from datetime import datetime


def main():
    logger.info("Checking Supabase Storage for scraped files...")
    
    # Get today's prefix
    extractor = Extractor()
    prefix = extractor.today_str
    logger.info(f"Checking storage prefix: {prefix}")
    
    try:
        storage_client = StorageClient()
        files = storage_client.list_files(prefix)
        
        # Filter for HTML files
        html_files = [f for f in files if f.get("name", "").endswith(".html")]
        
        logger.info(f"\n=== Storage Check Results ===")
        logger.info(f"Total files found in '{prefix}': {len(files)}")
        logger.info(f"HTML files found: {len(html_files)}")
        
        if html_files:
            logger.success(f"✓ Found {len(html_files)} HTML files in storage!")
            logger.info("\nFirst 20 files:")
            for i, file_obj in enumerate(html_files[:20]):
                size_kb = file_obj.get('metadata', {}).get('size', 0) / 1024
                logger.info(f"  {i+1}. {file_obj.get('name')} ({size_kb:.2f} KB)")
            
            if len(html_files) > 20:
                logger.info(f"  ... and {len(html_files) - 20} more files")
            
            # Try to download and verify one file
            logger.info("\n=== Verifying Sample File ===")
            sample_file = html_files[0].get("name")
            sample_path = f"{prefix}/{sample_file}"
            try:
                content = storage_client.download_html(sample_path)
                logger.success(f"✓ Successfully downloaded: {sample_file}")
                logger.info(f"  Content length: {len(content)} characters")
                logger.info(f"  First 200 chars: {content[:200]}...")
            except Exception as e:
                logger.error(f"✗ Failed to download sample file: {e}")
        else:
            logger.warning(f"✗ No HTML files found in storage prefix '{prefix}'")
            logger.info("This could mean:")
            logger.info("  1. The scraper hasn't run yet")
            logger.info("  2. The scraper failed before uploading files")
            logger.info("  3. Files are stored under a different date prefix")
            
            # Check for other prefixes
            logger.info("\nChecking root directory for other date prefixes...")
            root_files = storage_client.list_files("")
            date_prefixes = set()
            for f in root_files:
                name = f.get("name", "")
                if "/" in name:
                    date_prefix = name.split("/")[0]
                    if date_prefix.startswith("202"):
                        date_prefixes.add(date_prefix)
            
            if date_prefixes:
                logger.info(f"Found {len(date_prefixes)} date prefixes: {sorted(date_prefixes)}")
            else:
                logger.info("No date-prefixed folders found in root")
                
    except Exception as e:
        logger.error(f"Failed to check storage: {e}")
        raise


if __name__ == "__main__":
    main()
























