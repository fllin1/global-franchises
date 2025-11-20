# -*- coding: utf-8 -*-
"""
Migration script to move local HTML files to Supabase Storage.
"""

import os
from pathlib import Path
import re
from typing import List

from loguru import logger
from tqdm import tqdm

from src.api.config.supabase_config import supabase_client
from src.config import EXTERNAL_DATA_DIR
from src.data.storage.storage_client import StorageClient

DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def migrate_local_to_storage():
    """
    Migrate local HTML files to Supabase Storage and create scraping run records.
    """
    storage_client = StorageClient()
    supabase = supabase_client()

    # 1. Identify dated folders
    if not EXTERNAL_DATA_DIR.exists():
        logger.warning(f"{EXTERNAL_DATA_DIR} does not exist. Skipping migration.")
        return

    dated_folders = [
        d for d in EXTERNAL_DATA_DIR.iterdir() 
        if d.is_dir() and DATE_RE.match(d.name)
    ]
    
    logger.info(f"Found {len(dated_folders)} dated folders to migrate.")
    
    for folder in sorted(dated_folders, key=lambda d: d.name):
        run_date = folder.name
        logger.info(f"Processing folder: {run_date}")
        
        html_files = list(folder.glob("*.html"))
        if not html_files:
            logger.warning(f"No HTML files in {folder}")
            continue
            
        # Check if run already exists
        existing_run = supabase.table("scraping_runs").select("id").eq("storage_path_prefix", run_date).execute()
        
        run_id = None
        if not existing_run.data:
            # Create scraping run record
            try:
                run_data = {
                    "run_date": f"{run_date} 12:00:00+00", # Approximate time
                    "status": "in_progress",
                    "storage_path_prefix": run_date,
                    "total_franchises": len(html_files),
                    "metadata": {"migration": "migrated_from_local"}
                }
                res = supabase.table("scraping_runs").insert(run_data).execute()
                if res.data:
                    run_id = res.data[0]["id"]
            except Exception as e:
                logger.error(f"Failed to create run record for {run_date}: {e}")
        else:
            run_id = existing_run.data[0]["id"]
            logger.info(f"Run record already exists for {run_date} (ID: {run_id})")

        successful_uploads = 0
        failed_uploads = 0
        
        # Upload files
        for file_path in tqdm(html_files, desc=f"Uploading {run_date}"):
            file_name = file_path.name
            storage_path = f"{run_date}/{file_name}"
            
            # Check if exists (optional optimization, or just rely on upsert=True)
            # StorageClient upload uses upsert=True
            
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                
                storage_client.upload_html(content, storage_path)
                successful_uploads += 1
            except Exception as e:
                logger.error(f"Failed to upload {file_name}: {e}")
                failed_uploads += 1

        # Update run status
        if run_id:
            status = "completed" if failed_uploads == 0 else "partial"
            try:
                supabase.table("scraping_runs").update({
                    "status": status,
                    "successful_uploads": successful_uploads,
                    "failed_uploads": failed_uploads
                }).eq("id", run_id).execute()
            except Exception as e:
                logger.error(f"Failed to update run {run_id}: {e}")

    logger.success("Migration completed.")

if __name__ == "__main__":
    migrate_local_to_storage()

