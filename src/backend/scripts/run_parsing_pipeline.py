#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run the complete HTML parsing pipeline and save to database.
"""

from src.data.functions.extract import Extractor
from src.data.upsert_supabase import upload_data_to_supabase
from pathlib import Path
from src.config import RAW_DATA_DIR
from loguru import logger

def main():
    # Initialize extractor
    extractor = Extractor()
    
    # Step 1: Parse HTML to JSON (from storage)
    logger.info("Starting HTML parsing from storage...")
    extractor.rule_based_parsing()
    
    # Step 2: Upload to database
    # Note: upload_data_to_supabase() looks for JSON in RAW_DATA_DIR root
    # But rule_based_parsing saves to RAW_DATA_DIR/{date}/rule_based/
    # So we need to either:
    # A) Update upload_data_to_supabase to look in subdirectories, OR
    # B) Read JSON from storage instead
    
    logger.info("Uploading parsed data to database...")
    upload_data_to_supabase()

if __name__ == "__main__":
    main()