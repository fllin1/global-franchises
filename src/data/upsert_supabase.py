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
            # same 'source_id' (our on_conflict column) already exists.
            franchise_response = (
                supabase.table("Franchises")
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

            # --- Upsert Contacts Data ---
            if contacts_info:
                # First, add the foreign key 'franchise_id' to each contact record
                for contact in contacts_info:
                    contact["franchise_id"] = franchise_db_id

                # A safe way to handle contacts is to delete existing ones for the franchise
                # and then insert the new list. This handles removed contacts correctly.
                supabase.table("Contacts").delete().eq("franchise_id", franchise_db_id).execute()

                # Insert the new list of contacts
                supabase.table("Contacts").insert(contacts_info).execute()

        except Exception as e:  # pylint: disable=broad-exception-caught
            logger.error(f"\n--- ERROR processing {file_path.name} ---")
            logger.error(f"Franchise: {franchise_info.get('franchise_name')}")
            logger.error(f"Error details: {e}\n")

    logger.success("Upload process completed.")


if __name__ == "__main__":
    upload_data_to_supabase()
