#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Batch Markdown File Extraction Script.

This script processes multiple markdown files from Supabase Storage in batch:
1. Lists all markdown files in storage for a given date prefix
2. Queries database to find which source_ids already exist
3. Processes N unprocessed markdown files (configurable)
4. For each file:
   - Downloads markdown content from storage
   - Extracts source_id from filename
   - Sends to Gemini LLM with markdown prompt
   - Applies field transformations
   - Upserts franchise and contacts data to database
5. Tracks progress and allows resume on failure

Usage:
    python -m src.backend.scripts.run_batch_md_extraction
    python -m src.backend.scripts.run_batch_md_extraction --prefix 2025-11-24 --batch-size 50
    python -m src.backend.scripts.run_batch_md_extraction --prefix 2025-11-24 --batch-size 10 --delay 2
"""

import argparse
import json
import re
import sys
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set

from google.genai import types
from loguru import logger
from tqdm import tqdm

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


class BatchExtractionResult:
    """Class to track batch extraction results."""
    
    def __init__(self):
        self.successful: List[str] = []
        self.failed: List[Dict[str, str]] = []
        self.skipped: List[str] = []
        self.start_time: datetime = datetime.now()
        self.end_time: Optional[datetime] = None
        
    def add_success(self, filename: str):
        self.successful.append(filename)
        
    def add_failure(self, filename: str, error: str):
        self.failed.append({"filename": filename, "error": error})
        
    def add_skipped(self, filename: str):
        self.skipped.append(filename)
        
    def complete(self):
        self.end_time = datetime.now()
        
    @property
    def duration_seconds(self) -> float:
        end = self.end_time or datetime.now()
        return (end - self.start_time).total_seconds()
        
    def summary(self) -> str:
        lines = [
            "\n" + "=" * 60,
            "BATCH EXTRACTION SUMMARY",
            "=" * 60,
            f"Total processed: {len(self.successful) + len(self.failed)}",
            f"Successful: {len(self.successful)}",
            f"Failed: {len(self.failed)}",
            f"Skipped (already processed): {len(self.skipped)}",
            f"Duration: {self.duration_seconds:.1f} seconds",
            "=" * 60,
        ]
        
        if self.failed:
            lines.append("\nFailed files:")
            for item in self.failed:
                lines.append(f"  - {item['filename']}: {item['error']}")
        
        return "\n".join(lines)


def get_llm_processed_source_ids() -> Set[int]:
    """
    Query the database to get source_ids that have ALREADY been processed by LLM.
    
    Returns:
        Set of source_ids where llm_processed_at IS NOT NULL.
    """
    supabase = supabase_client()
    
    try:
        # Query source_ids where llm_processed_at is set (already processed by LLM)
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


def list_all_markdown_files(
    storage_client: StorageClient,
    prefix: str,
) -> List[Dict]:
    """
    List all markdown files in storage.
    
    Args:
        storage_client: StorageClient instance
        prefix: Date prefix in storage (e.g., "2025-11-24")
        
    Returns:
        List of markdown file objects
    """
    files = storage_client.list_files(prefix)
    
    # Filter for markdown files
    md_files = [f for f in files if f.get("name", "").endswith(".md")]
    
    return md_files


def categorize_files(
    md_files: List[Dict],
    existing_source_ids: Set[int],
) -> tuple:
    """
    Categorize markdown files into unprocessed and already processed.
    
    Args:
        md_files: List of markdown file objects
        existing_source_ids: Set of source_ids already in database
        
    Returns:
        Tuple of (unprocessed_files, already_processed_files)
    """
    unprocessed = []
    already_processed = []
    
    for file_obj in md_files:
        filename = file_obj.get("name", "")
        source_id = extract_source_id_from_filename(filename)
        
        if source_id and source_id in existing_source_ids:
            already_processed.append(file_obj)
        else:
            unprocessed.append(file_obj)
    
    return unprocessed, already_processed


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
        formatted_html=markdown_content,
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
            
            # Parse JSON response
            response_text = response.text.replace("```json", "").replace("```", "")
            response_json = json.loads(response_text)
            return response_json
            
        except json.JSONDecodeError as e:
            logger.warning(f"JSON decode error on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise
        except Exception as e:
            logger.error(f"Error calling Gemini on attempt {attempt + 1}: {e}")
            if attempt == max_retries - 1:
                raise
    
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
    
    response = (
        supabase.table("franchises")
        .upsert(franchise_data, on_conflict="source_id")
        .execute()
    )
    
    if response.data:
        return response.data[0]["id"]
    
    return None


def upsert_contacts_to_db(contacts: list, franchise_id: int) -> None:
    """
    Upsert contacts data to the database.
    
    Strategy: 
    - Contacts WITH email: Check if exists, update if so, insert if not
    - Contacts WITHOUT email: Delete old ones, insert new ones (can't deduplicate)
    
    Args:
        contacts: List of contact dictionaries
        franchise_id: The database ID of the franchise
    """
    if not contacts:
        return
    
    supabase = supabase_client()
    
    # Add franchise_id to each contact
    for contact in contacts:
        contact["franchise_id"] = franchise_id
    
    # Split contacts into those with email (can upsert) and without (insert only)
    contacts_with_email = [c for c in contacts if c.get("email")]
    contacts_without_email = [c for c in contacts if not c.get("email")]
    
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
        else:
            # Insert new contact
            supabase.table("contacts").insert(contact).execute()
    
    # Delete old contacts without email for this franchise, then insert new ones
    if contacts_without_email:
        # Delete existing contacts without email
        supabase.table("contacts").delete().eq("franchise_id", franchise_id).is_("email", "null").execute()
        # Insert new contacts without email
        supabase.table("contacts").insert(contacts_without_email).execute()


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
        
        # Upsert category
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
            
    except Exception as e:
        logger.warning(f"Failed to handle category relation: {e}")


def insert_territory_checks_to_db(territory_checks: list, franchise_id: int) -> None:
    """
    Insert territory checks into the territory_checks table.
    
    Args:
        territory_checks: List of parsed territory check dictionaries
        franchise_id: The database ID of the franchise
    """
    if not territory_checks:
        return
    
    supabase = supabase_client()
    
    # Insert territory checks in batch
    supabase.table("territory_checks").insert(territory_checks).execute()


def process_single_file(
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
    
    # 1. Extract source_id from filename
    source_id = extract_source_id_from_filename(filename)
    if not source_id:
        raise ValueError(f"Could not extract source_id from filename: {filename}")
    
    # 2. Download markdown content
    markdown_content = storage_client.download_markdown(file_path)
    
    # 3. Call Gemini LLM for extraction
    llm_output = call_gemini_for_extraction(markdown_content)
    
    if not llm_output:
        raise ValueError("LLM extraction returned empty result")
    
    # 4. Map LLM output to database schema
    franchise_data = map_llm_output_to_db_schema(llm_output, source_id)
    
    # 5. Upsert franchise to database
    franchise_id = upsert_franchise_to_db(franchise_data)
    
    if not franchise_id:
        raise ValueError("Failed to upsert franchise - no ID returned")
    
    # 6. Handle category relationship
    handle_category_relation(franchise_id, franchise_data.get("primary_category"))
    
    # 7. Extract and upsert contacts
    contacts = extract_contacts_data(llm_output)
    upsert_contacts_to_db(contacts, franchise_id)
    
    # 8. Extract and insert territory checks
    territory_checks = extract_territory_checks_data(llm_output, franchise_id)
    insert_territory_checks_to_db(territory_checks, franchise_id)
    
    return True


def run_batch_extraction(
    prefix: str,
    batch_size: int = 50,
    delay_seconds: float = 1.0,
    force_reprocess: bool = False,
) -> BatchExtractionResult:
    """
    Run batch extraction on markdown files.
    
    Args:
        prefix: Date prefix in storage (e.g., "2025-11-24")
        batch_size: Maximum number of files to process
        delay_seconds: Delay between API calls to avoid rate limits
        force_reprocess: If True, reprocess files even if they exist in DB
        
    Returns:
        BatchExtractionResult with statistics
    """
    result = BatchExtractionResult()
    
    logger.info(f"Starting batch extraction")
    logger.info(f"Storage prefix: {prefix}")
    logger.info(f"Batch size: {batch_size}")
    logger.info(f"Delay between requests: {delay_seconds}s")
    
    # Initialize storage client
    storage_client = StorageClient()
    
    # Get already LLM-processed source_ids (unless force reprocess)
    if force_reprocess:
        processed_ids = set()
        logger.info("Force reprocess enabled - will reprocess all files")
    else:
        logger.info("Querying LLM-processed source_ids from database...")
        processed_ids = get_llm_processed_source_ids()
        logger.info(f"Found {len(processed_ids)} already LLM-processed franchises")
    
    # List all markdown files
    logger.info("Listing markdown files in storage...")
    all_md_files = list_all_markdown_files(storage_client, prefix)
    logger.info(f"Found {len(all_md_files)} total markdown files in storage")
    
    if not all_md_files:
        logger.warning("No markdown files found in storage")
        result.complete()
        return result
    
    # Categorize files based on LLM processing status
    unprocessed, already_processed = categorize_files(all_md_files, processed_ids)
    
    logger.info(f"Files to process (not yet LLM-processed): {len(unprocessed)}")
    logger.info(f"Already LLM-processed (will skip): {len(already_processed)}")
    
    # Track skipped files
    for file_obj in already_processed:
        result.add_skipped(file_obj.get("name", ""))
    
    if not unprocessed:
        logger.info("No unprocessed files to process")
        result.complete()
        return result
    
    # Limit to batch size
    files_to_process = unprocessed[:batch_size]
    
    logger.info(f"Processing {len(files_to_process)} files...")
    
    # Process each file with progress bar
    for i, file_obj in enumerate(tqdm(files_to_process, desc="Processing files")):
        filename = file_obj.get("name", "")
        
        try:
            success = process_single_file(storage_client, prefix, filename)
            
            if success:
                result.add_success(filename)
                logger.debug(f"Successfully processed: {filename}")
            else:
                result.add_failure(filename, "Unknown error")
                
        except Exception as e:
            error_msg = str(e)
            result.add_failure(filename, error_msg)
            logger.error(f"Failed to process {filename}: {error_msg}")
        
        # Add delay between requests (except for last one)
        if i < len(files_to_process) - 1 and delay_seconds > 0:
            time.sleep(delay_seconds)
    
    result.complete()
    return result


def update_scraping_run_status(
    prefix: str,
    result: BatchExtractionResult,
) -> None:
    """
    Update the scraping_runs table with LLM parsing status.
    
    Args:
        prefix: Storage prefix (used to find the run)
        result: BatchExtractionResult with statistics
    """
    supabase = supabase_client()
    
    try:
        # Find the scraping run for this prefix
        run_response = (
            supabase.table("scraping_runs")
            .select("id, metadata")
            .eq("storage_path_prefix", prefix)
            .order("created_at", desc=True)
            .limit(1)
            .execute()
        )
        
        if not run_response.data:
            logger.warning(f"No scraping run found for prefix: {prefix}")
            return
        
        run_id = run_response.data[0]["id"]
        existing_metadata = run_response.data[0].get("metadata") or {}
        
        # Determine status
        if len(result.failed) == 0 and len(result.successful) > 0:
            status = "completed"
        elif len(result.successful) > 0:
            status = "partial"
        elif len(result.failed) > 0:
            status = "failed"
        else:
            status = "no_files"
        
        # Update metadata
        new_metadata = {
            **existing_metadata,
            "llm_parsing_completed_files": len(result.successful),
            "llm_parsing_failed_files": len(result.failed),
            "llm_parsing_skipped_files": len(result.skipped),
            "llm_parsing_duration_seconds": result.duration_seconds,
            "llm_parsing_completed_at": datetime.now(timezone.utc).isoformat(),
        }
        
        # Update the run record
        supabase.table("scraping_runs").update({
            "llm_parsing_status": status,
            "metadata": new_metadata,
        }).eq("id", run_id).execute()
        
        logger.info(f"Updated scraping run {run_id} with LLM parsing status: {status}")
        
    except Exception as e:
        logger.warning(f"Failed to update scraping run status: {e}")


def main(
    prefix: Optional[str] = None,
    batch_size: int = 50,
    delay: float = 1.0,
    force_reprocess: bool = False,
):
    """
    Main function to run batch extraction.
    
    Args:
        prefix: Date prefix in storage (default: today)
        batch_size: Maximum number of files to process
        delay: Delay between API calls in seconds
        force_reprocess: If True, reprocess files even if they exist in DB
    """
    # Default to today's prefix
    if not prefix:
        prefix = date.today().isoformat()
    
    # Run batch extraction
    result = run_batch_extraction(
        prefix=prefix,
        batch_size=batch_size,
        delay_seconds=delay,
        force_reprocess=force_reprocess,
    )
    
    # Print summary
    print(result.summary())
    
    # Update scraping run status
    update_scraping_run_status(prefix, result)
    
    # Exit with error code if there were failures
    if result.failed:
        logger.warning(f"Batch completed with {len(result.failed)} failures")
        sys.exit(1)
    else:
        logger.success(f"Batch completed successfully: {len(result.successful)} files processed")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Process multiple markdown files from Supabase Storage in batch"
    )
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Date prefix in storage (e.g., 2025-11-24). Default: today",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=50,
        help="Maximum number of files to process. Default: 50",
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.0,
        help="Delay between API calls in seconds. Default: 1.0",
    )
    parser.add_argument(
        "--force-reprocess",
        action="store_true",
        help="Reprocess files even if they already exist in database",
    )
    
    args = parser.parse_args()
    main(
        prefix=args.prefix,
        batch_size=args.batch_size,
        delay=args.delay,
        force_reprocess=args.force_reprocess,
    )

