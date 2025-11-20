# -*- coding: utf-8 -*-
"""
Data Extraction.

This module has 2 main functions:
- `scraping`: Scrapes franchise data from FranServe and saves it to HTML files.
- `extract`: Extracts data from the saved HTML files and converts it to JSON format.
"""

import json
from pathlib import Path
from urllib.parse import quote

from bs4 import BeautifulSoup
from tqdm import tqdm

from src.config import EXTERNAL_DATA_DIR, RAW_DATA_DIR
from src.data.franserve.html_formatter import process_franchise_html
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

        # Upload to Storage
        for url in tqdm(franchise_urls, total=len(franchise_urls), desc="Scraping franchise data"):
            try:
                data = get_franchise_data(session, url)
                file_name = quote(url.split("/")[-1], safe="") + ".html"
                file_path = f"{today_prefix}/{file_name}"
                
                # Upload to Supabase Storage
                upload_franchise_html(data, file_path, storage_client)
                successful_uploads += 1
            except Exception as e:
                print(f"Error processing {url}: {e}")
                failed_uploads += 1
        
        # Update Run Status
        if run_id:
            try:
                status = "completed" if failed_uploads == 0 else "partial"
                if successful_uploads == 0 and failed_uploads > 0:
                    status = "failed"
                
                supabase.table("scraping_runs").update({
                    "status": status,
                    "successful_uploads": successful_uploads,
                    "failed_uploads": failed_uploads
                }).eq("id", run_id).execute()
            except Exception as e:
                print(f"Failed to update scraping run record: {e}")

    def rule_based_parsing(self) -> None:
        """
        Run the rule-based parsing of the HTML files saved in Supabase Storage.
        This will convert the HTML files to JSON files.
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
                
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
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
