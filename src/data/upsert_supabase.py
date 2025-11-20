# -*- coding: utf-8 -*-
"""
This module contains the functions to upload the data to Supabase.
"""

import json

from loguru import logger
from tqdm import tqdm

from src.api.config.supabase_config import supabase_client
from src.config import RAW_DATA_DIR


def upload_data_to_supabase():
    """
    Connects to Supabase, reads parsed JSON files, and uploads the data
    to the 'Franchises' and 'Contacts' tables.
    """
    # --- 1. Initialize Supabase Client ---
    supabase = supabase_client()

    # --- 2. Get the list of JSON files to process ---
    json_files = list(RAW_DATA_DIR.glob("*.json"))
    if not json_files:
        logger.error(f"No JSON files found in {RAW_DATA_DIR}. Nothing to upload.")
        return

    logger.debug(f"Found {len(json_files)} files to process.")

    # --- 3. Iterate and Upload ---
    for file_path in tqdm(json_files, desc="Uploading to Supabase"):
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        franchise_info = data.get("franchise_data")
        contacts_info = data.get("contacts_data")

        if not franchise_info or not franchise_info.get("source_id"):
            logger.warning(f"Skipping {file_path.name} due to missing data or source_id.")
            continue

        try:
            # --- Upsert Franchise Data ---
            # Add metadata
            from datetime import datetime
            franchise_info["last_scraped_at"] = datetime.utcnow().isoformat()

            # Remove category from franchise_info if it's not a column in franchises table directly 
            # (Actually primary_category IS a column in franchises based on previous SQL, so we keep it)
            # But we also want to populate the relational tables.
            primary_category = franchise_info.get("primary_category")
            
            # same 'source_id' (our on_conflict column) already exists.
            franchise_response = (
                supabase.table("franchises")
                .upsert(
                    franchise_info,
                    on_conflict="source_id",  # This requires the UNIQUE constraint we set
                )
                .execute()
            )

            if not franchise_response.data:
                raise RuntimeError(f"Failed to upsert franchise: {franchise_response.error}")

            # Get the primary key ('id') of the franchise we just inserted/updated
            franchise_db_id = franchise_response.data[0]["id"]

            # --- Handle Categories Relation ---
            if primary_category:
                # 1. Ensure Category exists
                import re
                cat_slug = re.sub(r'[^a-z0-9]+', '-', primary_category.lower()).strip('-')
                
                cat_payload = {"name": primary_category, "slug": cat_slug}
                cat_res = supabase.table("categories").upsert(cat_payload, on_conflict="name").select().execute()
                
                if cat_res.data:
                    category_id = cat_res.data[0]["id"]
                    
                    # 2. Link in franchise_categories
                    fc_payload = {"franchise_id": franchise_db_id, "category_id": category_id}
                    supabase.table("franchise_categories").upsert(fc_payload).execute()

            # --- Upsert Contacts Data ---
            if contacts_info:
                # First, add the foreign key 'franchise_id' to each contact record
                for contact in contacts_info:
                    contact["franchise_id"] = franchise_db_id

                # A safe way to handle contacts is to delete existing ones for the franchise
                # and then insert the new list. This handles removed contacts correctly.
                supabase.table("contacts").delete().eq("franchise_id", franchise_db_id).execute()

                # Insert the new list of contacts
                supabase.table("contacts").insert(contacts_info).execute()

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"\n--- ERROR processing {file_path.name} ---")
            logger.error(f"Franchise: {franchise_info.get('franchise_name')}")
            logger.error(f"Error details: {e}\n")

    logger.success("Upload process completed.")


if __name__ == "__main__":
    upload_data_to_supabase()
