#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Single Markdown File Extraction Script.

This script processes ONE unprocessed markdown file from Supabase Storage:
1. Lists markdown files in storage for a given date prefix
2. Queries database to find which source_ids already exist
3. Picks ONE unprocessed markdown file
4. Downloads markdown content from storage
5. Extracts source_id from filename (FranID_X.md)
6. Sends to Gemini LLM with markdown prompt
7. Applies field transformations
8. Upserts franchise data to database
9. Upserts contacts to database

Usage:
    python -m src.backend.scripts.run_single_md_extraction
    python -m src.backend.scripts.run_single_md_extraction --prefix 2025-11-24
    python -m src.backend.scripts.run_single_md_extraction --fran-id 1003
"""

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from google.genai import types
from loguru import logger

from src.api.config.genai_gemini_config import (
    CLIENT,
    MODEL_FLASH_LITE,
    get_generate_content_config_franserve_data,
)
from src.api.config.supabase_config import supabase_client
from src.api.genai_gemini import generate
from src.config import CONFIG_DIR
from src.data.functions.field_mapper import (
    extract_contacts_data,
    extract_source_id_from_filename,
    extract_territory_checks_data,
    map_llm_output_to_db_schema,
)
from src.data.franserve.html_to_prompt import create_gemini_parts
from src.data.storage.storage_client import StorageClient


# Load the markdown prompt
PROMPT_MARKDOWN_DATA = (CONFIG_DIR / "franserve" / "markdown_prompt.txt").read_text()


def get_llm_processed_source_ids() -> set:
    """
    Query the database to get source_ids already processed by LLM.
    
    Returns:
        Set of source_ids where llm_processed_at IS NOT NULL.
    """
    supabase = supabase_client()
    
    try:
        # Query source_ids where llm_processed_at is set
        response = (
            supabase.table("franchises")
            .select("source_id")
            .not_.is_("source_id", "null")
            .not_.is_("llm_processed_at", "null")
            .execute()
        )
        
        if response.data:
            return {row["source_id"] for row in response.data}
        
        return set()
    except Exception as e:
        logger.error(f"Failed to query LLM-processed source_ids: {e}")
        return set()


def list_unprocessed_markdown_files(
    storage_client: StorageClient,
    prefix: str,
    existing_source_ids: set,
) -> list:
    """
    List markdown files that haven't been processed yet.
    
    Args:
        storage_client: StorageClient instance
        prefix: Date prefix in storage (e.g., "2025-11-24")
        existing_source_ids: Set of source_ids already in database
        
    Returns:
        List of unprocessed markdown file objects
    """
    files = storage_client.list_files(prefix)
    
    # Filter for markdown files
    md_files = [f for f in files if f.get("name", "").endswith(".md")]
    
    # Filter out files whose source_id already exists in database
    unprocessed = []
    for file_obj in md_files:
        filename = file_obj.get("name", "")
        source_id = extract_source_id_from_filename(filename)
        
        if source_id and source_id not in existing_source_ids:
            unprocessed.append(file_obj)
    
    return unprocessed


def call_gemini_for_extraction(markdown_content: str) -> Optional[dict]:
    """
    Call Gemini LLM to extract structured data from markdown content.
    
    Args:
        markdown_content: The markdown content to parse
        
    Returns:
        Parsed JSON response or None if failed
    """
    # Create parts for the Gemini API
    parts = create_gemini_parts(
        prompt=PROMPT_MARKDOWN_DATA,
        formatted_html=markdown_content,  # Parameter name is misleading but reuses existing function
    )
    
    # Call Gemini with retry logic
    max_retries = 3
    for attempt in range(max_retries):
        try:
            seed = 0 if attempt == 0 else attempt * 12345
            
            response = generate(
                client=CLIENT,
                model=MODEL_FLASH_LITE,
                parts=parts,
                generate_content_config=get_generate_content_config_franserve_data(seed),
            )
            
            # Log token usage
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}")
            
            # Parse JSON response
            response_text = response.text.replace("```json", "").replace("```", "")
            response_json = json.loads(response_text)
            logger.success(f"Successfully parsed LLM response on attempt {attempt + 1}")
            return response_json
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Failed to parse JSON after {max_retries} attempts")
                return None
        except Exception as e:
            logger.error(f"Error calling Gemini on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                return None
    
    return None


def upsert_franchise_to_db(franchise_data: dict) -> Optional[int]:
    """
    Upsert franchise data to the database.
    
    Args:
        franchise_data: Dictionary ready for database upsert
        
    Returns:
        The franchise database ID or None if failed
    """
    supabase = supabase_client()
    
    try:
        response = (
            supabase.table("franchises")
            .upsert(franchise_data, on_conflict="source_id")
            .execute()
        )
        
        if response.data:
            franchise_id = response.data[0]["id"]
            logger.success(f"Upserted franchise with ID: {franchise_id}")
            return franchise_id
        else:
            logger.error("Upsert returned no data")
            return None
            
    except Exception as e:
        logger.error(f"Failed to upsert franchise: {e}")
        return None


def upsert_contacts_to_db(contacts: list, franchise_id: int) -> bool:
    """
    Upsert contacts data to the database.
    
    Strategy: 
    - Contacts WITH email: Check if exists, update if so, insert if not
    - Contacts WITHOUT email: Delete old ones, insert new ones (can't deduplicate)
    
    Args:
        contacts: List of contact dictionaries
        franchise_id: The database ID of the franchise
        
    Returns:
        True if successful, False otherwise
    """
    if not contacts:
        logger.info("No contacts to upsert")
        return True
    
    supabase = supabase_client()
    
    try:
        # Add franchise_id to each contact
        for contact in contacts:
            contact["franchise_id"] = franchise_id
        
        # Split contacts into those with email (can upsert) and without (insert only)
        contacts_with_email = [c for c in contacts if c.get("email")]
        contacts_without_email = [c for c in contacts if not c.get("email")]
        
        upserted_count = 0
        inserted_count = 0
        
        # Handle contacts with email - find and update or insert
        for contact in contacts_with_email:
            email = contact.get("email")
            # Check if contact exists
            existing = (
                supabase.table("contacts")
                .select("id")
                .eq("franchise_id", franchise_id)
                .eq("email", email)
                .execute()
            )
            
            if existing.data:
                # Update existing contact
                contact_id = existing.data[0]["id"]
                supabase.table("contacts").update(contact).eq("id", contact_id).execute()
                upserted_count += 1
            else:
                # Insert new contact
                supabase.table("contacts").insert(contact).execute()
                inserted_count += 1
        
        # Delete old contacts without email for this franchise, then insert new ones
        if contacts_without_email:
            # Delete existing contacts without email
            supabase.table("contacts").delete().eq("franchise_id", franchise_id).is_("email", "null").execute()
            # Insert new contacts without email
            supabase.table("contacts").insert(contacts_without_email).execute()
            inserted_count += len(contacts_without_email)
        
        logger.success(f"Contacts for franchise {franchise_id}: {upserted_count} updated, {inserted_count} inserted")
        return True
        
    except Exception as e:
        logger.error(f"Failed to upsert contacts: {e}")
        return False


def handle_category_relation(franchise_id: int, primary_category: Optional[str]) -> None:
    """
    Handle the many-to-many relationship between franchises and categories.
    
    Args:
        franchise_id: The database ID of the franchise
        primary_category: The primary category name
    """
    if not primary_category:
        return
    
    supabase = supabase_client()
    
    try:
        # Create slug from category name
        cat_slug = re.sub(r'[^a-z0-9]+', '-', primary_category.lower()).strip('-')
        
        # Upsert category and get the result
        cat_payload = {"name": primary_category, "slug": cat_slug}
        cat_response = (
            supabase.table("categories")
            .upsert(cat_payload, on_conflict="name")
            .execute()
        )
        
        if cat_response.data:
            category_id = cat_response.data[0]["id"]
            
            # Link franchise to category
            fc_payload = {"franchise_id": franchise_id, "category_id": category_id}
            supabase.table("franchise_categories").upsert(fc_payload).execute()
            logger.info(f"Linked franchise {franchise_id} to category '{primary_category}'")
            
    except Exception as e:
        logger.warning(f"Failed to handle category relation: {e}")


def insert_territory_checks_to_db(territory_checks: list, franchise_id: int) -> bool:
    """
    Insert territory checks into the territory_checks table.
    
    Strategy: Insert new territory checks. Uses location_raw + franchise_id + check_date
    to avoid exact duplicates (though we don't have a unique constraint on this).
    
    Args:
        territory_checks: List of parsed territory check dictionaries
        franchise_id: The database ID of the franchise
        
    Returns:
        True if successful, False otherwise
    """
    if not territory_checks:
        logger.info("No territory checks to insert")
        return True
    
    supabase = supabase_client()
    
    try:
        # Insert territory checks in batch
        # Each check already has franchise_id set by the parser
        supabase.table("territory_checks").insert(territory_checks).execute()
        logger.success(f"Inserted {len(territory_checks)} territory checks for franchise {franchise_id}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to insert territory checks: {e}")
        return False


def process_single_markdown_file(
    storage_client: StorageClient,
    prefix: str,
    filename: str,
) -> bool:
    """
    Process a single markdown file through the complete pipeline.
    
    Args:
        storage_client: StorageClient instance
        prefix: Date prefix in storage
        filename: Name of the markdown file
        
    Returns:
        True if successful, False otherwise
    """
    file_path = f"{prefix}/{filename}"
    logger.info(f"Processing: {file_path}")
    
    # 1. Extract source_id from filename
    source_id = extract_source_id_from_filename(filename)
    if not source_id:
        logger.error(f"Could not extract source_id from filename: {filename}")
        return False
    
    logger.info(f"Extracted source_id: {source_id}")
    
    # 2. Download markdown content
    try:
        markdown_content = storage_client.download_markdown(file_path)
        logger.info(f"Downloaded markdown ({len(markdown_content)} chars)")
    except Exception as e:
        logger.error(f"Failed to download markdown: {e}")
        return False
    
    # 3. Call Gemini LLM for extraction
    logger.info("Calling Gemini LLM for extraction...")
    llm_output = call_gemini_for_extraction(markdown_content)
    
    if not llm_output:
        logger.error("LLM extraction failed")
        return False
    
    # 4. Map LLM output to database schema
    franchise_data = map_llm_output_to_db_schema(llm_output, source_id)
    
    logger.info(f"Mapped franchise: {franchise_data.get('franchise_name')}")
    
    # 5. Upsert franchise to database
    franchise_id = upsert_franchise_to_db(franchise_data)
    
    if not franchise_id:
        return False
    
    # 6. Handle category relationship
    handle_category_relation(franchise_id, franchise_data.get("primary_category"))
    
    # 7. Extract and upsert contacts
    contacts = extract_contacts_data(llm_output)
    upsert_contacts_to_db(contacts, franchise_id)
    
    # 8. Extract and insert territory checks
    territory_checks = extract_territory_checks_data(llm_output, franchise_id)
    insert_territory_checks_to_db(territory_checks, franchise_id)
    
    logger.success(f"Successfully processed {filename} -> franchise ID {franchise_id}")
    return True


def main(prefix: Optional[str] = None, fran_id: Optional[int] = None):
    """
    Main function to process a single markdown file.
    
    Args:
        prefix: Date prefix in storage (default: today)
        fran_id: Specific FranID to process (optional)
    """
    # Default to today's prefix
    if not prefix:
        prefix = date.today().isoformat()
    
    logger.info(f"Starting single markdown extraction")
    logger.info(f"Storage prefix: {prefix}")
    
    # Initialize storage client
    storage_client = StorageClient()
    
    if fran_id:
        # Process a specific FranID
        filename = f"FranID_{fran_id}.md"
        logger.info(f"Processing specific file: {filename}")
        success = process_single_markdown_file(storage_client, prefix, filename)
        
        if success:
            logger.success("Extraction completed successfully!")
        else:
            logger.error("Extraction failed!")
            sys.exit(1)
    else:
        # Find an unprocessed file
        logger.info("Querying LLM-processed source_ids from database...")
        processed_ids = get_llm_processed_source_ids()
        logger.info(f"Found {len(processed_ids)} already LLM-processed franchises")
        
        # List unprocessed markdown files (not yet LLM-processed)
        logger.info("Listing markdown files not yet LLM-processed...")
        unprocessed = list_unprocessed_markdown_files(storage_client, prefix, processed_ids)
        
        if not unprocessed:
            logger.warning("No unprocessed markdown files found!")
            logger.info("Either all files have been processed, or no markdown files exist in storage.")
            return
        
        logger.info(f"Found {len(unprocessed)} unprocessed markdown files")
        
        # Pick the first unprocessed file
        first_file = unprocessed[0]
        filename = first_file.get("name")
        
        logger.info(f"Selected file: {filename}")
        success = process_single_markdown_file(storage_client, prefix, filename)
        
        if success:
            logger.success("Extraction completed successfully!")
        else:
            logger.error("Extraction failed!")
            sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process a single markdown file from Supabase Storage"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Date prefix in storage (e.g., 2025-11-24). Default: today",
    )
    parser.add_argument(
        "--fran-id",
        type=int,
        default=None,
        help="Specific FranID to process (e.g., 1003)",
    )
    
    args = parser.parse_args()
    main(prefix=args.prefix, fran_id=args.fran_id)

