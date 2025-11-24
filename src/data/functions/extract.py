# -*- coding: utf-8 -*-
"""
Data Extraction.

This module has 2 main functions:
- `scraping`: Scrapes franchise data from FranServe and saves it to HTML files.
- `extract`: Extracts data from the saved HTML files and converts it to JSON format.
"""

import json
import re
from datetime import datetime
from pathlib import Path
from urllib.parse import quote, parse_qs, urlparse

from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from src.config import CONFIG_DIR, EXTERNAL_DATA_DIR, RAW_DATA_DIR
from src.data.franserve.html_formatter import process_franchise_html
from src.data.franserve.html_to_markdown import convert_html_to_markdown
from src.data.franserve.html_to_prompt import (
    create_gemini_parts,
    format_html_for_llm,
)
from src.api.config.supabase_config import supabase_client
from src.data.franserve.scrapper import (
    ScrapeConfig,
    get_all_pages_franchise_urls,
    get_franchise_data,
    save_franchise_data,
    session_login,
    upload_franchise_html,
)
from src.data.storage.storage_client import StorageClient
from src.data.functions.file_manager import ExtractFileManager
from src.data.nlp.genai_data import (
    PROMPT_FRANSERVE_DATA,
    generate_franchise_data_with_retry,
)

PROMPT_MARKDOWN_DATA = (CONFIG_DIR / "franserve" / "markdown_prompt.txt").read_text()


class Extractor(ExtractFileManager):
    """
    A class to manage the extraction of data from FranServe HTML files.

    Inherits from ExtractFileManager to utilize file management functionalities.
    """

    def __init__(
        self, external_data_dir: Path = EXTERNAL_DATA_DIR, raw_data_dir: Path = RAW_DATA_DIR
    ):
        """
        Initializes the Extractor with the specified directories.
        Args:
            external_data_dir (Path): The directory where the scraped HTML files are stored.
            raw_data_dir (Path): The directory where the extracted JSON files will be saved.
        """
        # Initialize the parent class with the external data directory
        super().__init__(external_data_dir)

        self.raw_date_dir = raw_data_dir / self.today_str
        self.raw_date_dir.mkdir(parents=True, exist_ok=True)

    def scrape(self) -> None:
        """
        Run the scrapper over all the data on the Franserve catalogue and saves it
        to Supabase Storage.
        """
        session = session_login(
            ScrapeConfig.LOGIN_ACTION, ScrapeConfig.USERNAME, ScrapeConfig.PASSWORD
        )
        franchise_urls = get_all_pages_franchise_urls(
            session, ScrapeConfig.BASE_URL, ScrapeConfig.CATALOGUE_BASE_URL
        )

        storage_client = StorageClient()
        today_prefix = self.today_str

        # Start Scraping Run Tracking
        supabase = supabase_client()
        run_id = None
        try:
            run_data = {
                "status": "in_progress",
                "storage_path_prefix": today_prefix,
                "total_franchises": len(franchise_urls),
            }
            run_response = supabase.table("scraping_runs").insert(run_data).execute()
            if run_response.data:
                run_id = run_response.data[0]["id"]
        except Exception as e:
            print(f"Failed to create scraping run record: {e}")

        successful_uploads = 0
        failed_uploads = 0
        processed_urls = []

        # Upload to Storage
        logger.info(f"Starting to scrape {len(franchise_urls)} franchise URLs...")
        for idx, url in enumerate(tqdm(franchise_urls, total=len(franchise_urls), desc="Scraping franchise data"), 1):
            try:
                logger.debug(f"Processing franchise {idx}/{len(franchise_urls)}: {url}")
                data = get_franchise_data(session, url)
                
                # Extract FranID from URL or HTML
                fran_id = None
                # Try to extract from URL first (faster)
                parsed_url = urlparse(url)
                query_params = parse_qs(parsed_url.query)
                if "FranID" in query_params:
                    fran_id = query_params["FranID"][0]
                else:
                    # Fallback: extract from HTML
                    fran_id_tag = data.find("input", {"name": "ZorID"})
                    if fran_id_tag and fran_id_tag.get("value"):
                        fran_id = fran_id_tag["value"]
                
                if not fran_id:
                    logger.warning(f"Could not extract FranID from {url}, using URL-based filename")
                    # Fallback to old method if FranID not found
                    file_name = quote(url.split("/")[-1], safe="") + ".html"
                else:
                    # Use clean filename format: FranID_{id}.html
                    file_name = f"FranID_{fran_id}.html"
                
                file_path = f"{today_prefix}/{file_name}"
                
                # Upload to Supabase Storage
                upload_franchise_html(data, file_path, storage_client)
                successful_uploads += 1
                processed_urls.append(url)
                
                # Log progress every 50 files
                if successful_uploads % 50 == 0:
                    logger.info(f"Progress: {successful_uploads}/{len(franchise_urls)} franchises scraped successfully")
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                failed_uploads += 1
        
        # Update Run Status
        if run_id:
            try:
                status = "completed" if failed_uploads == 0 else "partial"
                if successful_uploads == 0 and failed_uploads > 0:
                    status = "failed"
                
                # Store processed URLs in metadata (limit to last 100 for storage efficiency)
                metadata = {
                    "processed_urls_count": len(processed_urls),
                    "sample_urls": processed_urls[-100:] if len(processed_urls) > 100 else processed_urls
                }
                
                supabase.table("scraping_runs").update({
                    "status": status,
                    "successful_uploads": successful_uploads,
                    "failed_uploads": failed_uploads,
                    "metadata": metadata
                }).eq("id", run_id).execute()
                
                logger.info(f"Scraping run completed: {successful_uploads} successful, {failed_uploads} failed")
            except Exception as e:
                logger.error(f"Failed to update scraping run record: {e}")

    def rule_based_parsing(self) -> None:
        """
        Run the rule-based parsing of the HTML files saved in Supabase Storage.
        This will convert the HTML files to JSON files and upload JSON to storage.
        """
        storage_client = StorageClient()
        prefix = self.today_str
        files = storage_client.list_files(prefix)

        if not files:
            print(f"No files found in storage for {prefix}")
            return

        # Ensure rule_based directory exists
        (self.raw_date_dir / "rule_based").mkdir(parents=True, exist_ok=True)

        for file_obj in tqdm(files, desc="Parsing HTML files from Storage"):
            file_name = file_obj.get("name")
            # Skip if it's a directory or not html
            if not file_name or not file_name.endswith(".html"):
                continue

            file_path = f"{prefix}/{file_name}"

            try:
                html_content = storage_client.download_html(file_path)
                data = process_franchise_html(html_content)

                output_name = file_name.replace(".html", ".json")
                output_path = self.raw_date_dir / "rule_based" / output_name
                
                # Save locally
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                
                # Upload JSON to storage
                json_file_path = f"{prefix}/{output_name}"
                json_content = json.dumps(data, indent=4)
                storage_client.upload_json(json_content, json_file_path)
            except Exception as e:
                print(f"Error parsing {file_name}: {e}")

    def ai_assisted_parsing(self) -> None:
        """
        Run the AI-assisted parsing of the HTML files saved in Supabase Storage.
        This will convert the HTML files to JSON files.
        """
        storage_client = StorageClient()
        prefix = self.today_str
        files = storage_client.list_files(prefix)
        
        if not files:
            print(f"No files found in storage for {prefix}")
            return

        failed_files = []

        for file_obj in tqdm(files, desc="AI Parsing from Storage"):
            file_name = file_obj.get("name")
            if not file_name or not file_name.endswith(".html"):
                continue
                
            file_path = f"{prefix}/{file_name}"

            try:
                html_content = storage_client.download_html(file_path)
                data = format_html_for_llm(html_content)

                parts = create_gemini_parts(
                    prompt=PROMPT_FRANSERVE_DATA,
                    formatted_html=data,
                )

                # Generate franchise data with automatic retry
                response_json = generate_franchise_data_with_retry(parts)

                if response_json:
                    # Get the source_id directly from the HTML
                    soup = BeautifulSoup(html_content, "html.parser")
                    fran_id_tag = soup.find("input", {"name": "ZorID"})
                    if fran_id_tag and fran_id_tag.get("value"):
                        response_json["source_id"] = int(fran_id_tag["value"])
                else:
                    failed_files.append(file_name)

                if response_json:
                    output_name = file_name.replace(".html", ".json")
                    output_path = self.raw_date_dir / output_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(response_json, f, indent=4)
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                failed_files.append(file_name)

        print(f"Failed to process {len(failed_files)} files out of {len(files)}.")
        print(f"Failed files: {failed_files}")

    def convert_html_to_markdown_and_upload(self) -> None:
        """
        Convert HTML files from Supabase Storage to Markdown format and upload to storage.
        Downloads HTML, converts to Markdown, and uploads Markdown files.
        Skips HTML files that already have corresponding Markdown files in storage.
        Tracks progress in scraping_runs table to enable resumption from failures.
        """
        storage_client = StorageClient()
        prefix = self.today_str
        files = storage_client.list_files(prefix)

        if not files:
            logger.warning(f"No files found in storage for {prefix}")
            return

        # Filter HTML files
        html_files = [
            f for f in files 
            if f.get("name") and f.get("name").endswith(".html")
        ]

        logger.info(f"Found {len(files)} total files in storage prefix '{prefix}'")
        logger.info(f"Found {len(html_files)} HTML files to process")

        if not html_files:
            logger.warning(f"No HTML files found in storage for {prefix}")
            return

        # Start Run Tracking
        supabase = supabase_client()
        run_id = None
        converted_files_set = set()
        existing_metadata = {}
        
        try:
            # Query for existing scraping run with matching storage_path_prefix
            run_response = (
                supabase.table("scraping_runs")
                .select("*")
                .eq("storage_path_prefix", prefix)
                .order("created_at", desc=True)
                .limit(1)
                .execute()
            )
            
            if run_response.data:
                run_data = run_response.data[0]
                run_id = run_data.get("id")
                md_status = run_data.get("markdown_conversion_status")
                existing_metadata = run_data.get("metadata") or {}
                
                # Load already-converted files from metadata if resuming
                if md_status in ("in_progress", "partial"):
                    converted_files_list = existing_metadata.get("markdown_converted_files", [])
                    converted_files_set = set(converted_files_list)
                    logger.info(f"Resuming conversion run {run_id}. Found {len(converted_files_set)} already-converted files in metadata.")
                
                # Update run record to mark as in_progress
                update_data = {
                    "markdown_conversion_status": "in_progress",
                }
                # Only set started_at if it's not already set (for resume case)
                if not run_data.get("markdown_conversion_started_at"):
                    update_data["markdown_conversion_started_at"] = datetime.utcnow().isoformat()
                
                supabase.table("scraping_runs").update(update_data).eq("id", run_id).execute()
                logger.info(f"Updated run {run_id} to in_progress status")
            else:
                # Create new run record if it doesn't exist
                run_data = {
                    "status": "completed",  # Scraping is assumed complete
                    "storage_path_prefix": prefix,
                    "markdown_conversion_status": "in_progress",
                    "markdown_conversion_started_at": datetime.utcnow().isoformat(),
                    "metadata": {"markdown_converted_files": []}
                }
                run_response = supabase.table("scraping_runs").insert(run_data).execute()
                if run_response.data:
                    run_id = run_response.data[0]["id"]
                    logger.info(f"Created new conversion run {run_id} for prefix {prefix}")
        except Exception as e:
            logger.error(f"Failed to create/update scraping run record: {e}")
            # Continue without tracking if DB fails

        successful_conversions = 0
        failed_conversions = 0
        skipped_conversions = 0
        converted_files_list = list(converted_files_set)

        if converted_files_set:
            logger.info(f"Resuming: {len(converted_files_set)} files already converted, {len(html_files) - len(converted_files_set)} remaining to process")

        # Process files
        for file_obj in tqdm(html_files, desc="Converting HTML to Markdown"):
            file_name = file_obj.get("name")
            file_path = f"{prefix}/{file_name}"

            # Check if already converted (from metadata)
            if file_name in converted_files_set:
                if skipped_conversions < 10:  # Log first 10 skipped files
                    logger.info(f"Skipping {file_name} - Already converted (from metadata)")
                elif skipped_conversions == 10:
                    logger.info(f"... (skipping more files already in metadata, will show summary at end)")
                skipped_conversions += 1
                continue

            # Check if Markdown file already exists in storage
            markdown_file_name = file_name.replace(".html", ".md")
            markdown_file_path = f"{prefix}/{markdown_file_name}"
            
            if storage_client.exists(markdown_file_path):
                if skipped_conversions < 10:  # Log first 10 skipped files
                    logger.info(f"Skipping {file_name} - Markdown already exists in storage")
                elif skipped_conversions == 10:
                    logger.info(f"... (skipping more files that already exist, will show summary at end)")
                skipped_conversions += 1
                # Add to converted_files_set to track it
                converted_files_set.add(file_name)
                converted_files_list.append(file_name)
                continue

            try:
                # Log every 10th file being processed for visibility
                if successful_conversions % 10 == 0:
                    logger.info(f"Processing {file_name} ({successful_conversions + 1}/{len(html_files) - skipped_conversions} remaining)")
                
                # Download HTML from storage
                html_content = storage_client.download_html(file_path)

                # Convert HTML to Markdown
                markdown_content = convert_html_to_markdown(html_content)

                # Upload Markdown to storage (same path structure, .md extension)
                storage_client.upload_markdown(markdown_content, markdown_file_path)

                successful_conversions += 1
                converted_files_set.add(file_name)
                converted_files_list.append(file_name)
                
                # Update run record periodically (every 50 files)
                if run_id and successful_conversions % 50 == 0:
                    try:
                        # Limit metadata to last 1000 files for storage efficiency
                        metadata_converted = converted_files_list[-1000:] if len(converted_files_list) > 1000 else converted_files_list
                        supabase.table("scraping_runs").update({
                            "markdown_conversions_completed": successful_conversions,
                            "markdown_conversions_failed": failed_conversions,
                            "markdown_conversions_skipped": skipped_conversions,
                            "metadata": {
                                "markdown_converted_files": metadata_converted,
                                "markdown_converted_files_count": len(converted_files_set)
                            }
                        }).eq("id", run_id).execute()
                        logger.info(f"Progress update: {successful_conversions} converted, {skipped_conversions} skipped, {failed_conversions} failed")
                    except Exception as e:
                        logger.warning(f"Failed to update run progress: {e}")
                        
            except Exception as e:
                logger.error(f"Error converting {file_name} to Markdown: {e}")
                failed_conversions += 1

        # Update Run Status at completion
        if run_id:
            try:
                # Determine final status
                if failed_conversions == 0 and successful_conversions > 0:
                    status = "completed"
                elif successful_conversions > 0:
                    status = "partial"
                elif successful_conversions == 0 and failed_conversions > 0:
                    status = "failed"
                else:
                    status = "completed"  # All skipped case
                
                # Limit metadata to last 1000 files for storage efficiency
                metadata_converted = converted_files_list[-1000:] if len(converted_files_list) > 1000 else converted_files_list
                
                update_data = {
                    "markdown_conversion_status": status,
                    "markdown_conversions_completed": successful_conversions,
                    "markdown_conversions_failed": failed_conversions,
                    "markdown_conversions_skipped": skipped_conversions,
                    "markdown_conversion_completed_at": datetime.utcnow().isoformat(),
                    "metadata": {
                        "markdown_converted_files": metadata_converted,
                        "markdown_converted_files_count": len(converted_files_set)
                    }
                }
                
                # Preserve existing metadata fields if they exist
                if existing_metadata:
                    # Merge with existing metadata, but prioritize our markdown fields
                    for key, value in existing_metadata.items():
                        if key not in ("markdown_converted_files", "markdown_converted_files_count"):
                            update_data["metadata"][key] = value
                
                supabase.table("scraping_runs").update(update_data).eq("id", run_id).execute()
                logger.info(f"Conversion run {run_id} completed: Status={status}, Converted={successful_conversions}, Skipped={skipped_conversions}, Failed={failed_conversions}")
            except Exception as e:
                logger.error(f"Failed to update conversion run record: {e}")

        logger.info(f"\n=== Conversion Summary ===")
        logger.info(f"Total HTML files found: {len(html_files)}")
        logger.info(f"Successfully converted: {successful_conversions}")
        logger.info(f"Skipped (already converted): {skipped_conversions}")
        logger.info(f"Failed: {failed_conversions}")
        logger.info(f"Remaining to process: {len(html_files) - successful_conversions - skipped_conversions - failed_conversions}")

    def markdown_to_json_parsing(self) -> None:
        """
        Run the AI-assisted parsing of Markdown files saved in Supabase Storage.
        This will convert the Markdown files to JSON files using LLM.
        """
        storage_client = StorageClient()
        prefix = self.today_str
        files = storage_client.list_files(prefix)

        if not files:
            print(f"No files found in storage for {prefix}")
            return

        failed_files = []

        for file_obj in tqdm(files, desc="AI Parsing Markdown from Storage"):
            file_name = file_obj.get("name")
            if not file_name or not file_name.endswith(".md"):
                continue

            file_path = f"{prefix}/{file_name}"

            try:
                # Download Markdown from storage
                markdown_content = storage_client.download_markdown(file_path)

                # Create parts for Gemini API
                parts = create_gemini_parts(
                    prompt=PROMPT_MARKDOWN_DATA,
                    formatted_html=markdown_content,
                )

                # Generate franchise data with automatic retry
                response_json = generate_franchise_data_with_retry(parts)

                if response_json:
                    # Try to get source_id from corresponding HTML file
                    html_file_name = file_name.replace(".md", ".html")
                    html_file_path = f"{prefix}/{html_file_name}"
                    try:
                        html_content = storage_client.download_html(html_file_path)
                        soup = BeautifulSoup(html_content, "html.parser")
                        fran_id_tag = soup.find("input", {"name": "ZorID"})
                        if fran_id_tag and fran_id_tag.get("value"):
                            response_json["source_id"] = int(fran_id_tag["value"])
                    except Exception:
                        # If we can't get source_id from HTML, continue without it
                        pass
                else:
                    failed_files.append(file_name)

                if response_json:
                    # Save locally
                    output_name = file_name.replace(".md", "_markdown.json")
                    output_path = self.raw_date_dir / output_name
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    with open(output_path, "w", encoding="utf-8") as f:
                        json.dump(response_json, f, indent=4)
            except Exception as e:
                print(f"Error processing {file_name}: {e}")
                failed_files.append(file_name)

        print(f"Failed to process {len(failed_files)} files out of {len(files)}.")
        if failed_files:
            print(f"Failed files: {failed_files}")
