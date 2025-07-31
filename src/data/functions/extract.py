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
from src.data.franserve.scrapper import (
    ScrapeConfig,
    get_all_pages_franchise_urls,
    get_franchise_data,
    save_franchise_data,
    session_login,
)
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
        in the EXTERNAL_DATA_DIR.
        """
        session = session_login(
            ScrapeConfig.LOGIN_ACTION, ScrapeConfig.USERNAME, ScrapeConfig.PASSWORD
        )
        franchise_urls = get_all_pages_franchise_urls(
            session, ScrapeConfig.BASE_URL, ScrapeConfig.CATALOGUE_BASE_URL
        )

        def _create_backup() -> None:
            """Create a backup of the current 'new_' directory by removing 'new_'."""
            for folder in self.external_data_dir.iterdir():
                if folder.is_dir() and folder.name.startswith("new_"):
                    new_name = folder.name[len("new_") :]
                    new_path = folder.parent / new_name
                    folder.rename(new_path)

        _create_backup()

        # Create dated subfolder path
        dated_dir = self.external_data_dir / "new_" + self.today_str
        dated_dir.mkdir(parents=True, exist_ok=True)

        for url in tqdm(franchise_urls, total=len(franchise_urls), desc="Scraping franchise data"):
            data = get_franchise_data(session, url)
            file_name = quote(url.split("/")[-1], safe="") + ".html"
            save_franchise_data(data, file_name, dated_dir)

        self.copy_modified_external_files()

    def rule_based_parsing(self) -> None:
        """
        Run the rule-based parsing of the HTML files saved in the EXTERNAL_DATA_DIR.
        This will convert the HTML files to JSON files.
        """

        html_files = list(self.modified_dir.glob("*.html"))
        for file_path in tqdm(html_files, total=len(html_files), desc="Parsing HTML files"):
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

            data = process_franchise_html(html_content)

            file_name = file_path.name.replace(".html", ".json")
            output_path = self.raw_date_dir / "rule_based" / file_name
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)

    def ai_assisted_parsing(self) -> None:
        """
        Run the AI-assisted parsing of the HTML files saved in the EXTERNAL_DATA_DIR.
        This will convert the HTML files to JSON files.
        """

        modified_files: list = self.read_log_file()
        modified_files = [Path(file) for file in modified_files]
        failed_files = []

        for file_path in modified_files:
            with open(file_path, "r", encoding="utf-8") as f:
                html_content = f.read()

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
                failed_files.append(file_path)

            if response_json:
                file_name = file_path.name.replace(".html", ".json")
                output_path = self.raw_date_dir / file_name
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    json.dump(response_json, f, indent=4)

        print(f"Failed to process {len(failed_files)} files out of {len(modified_files)}.")
        print(f"Failed files: {failed_files}")
