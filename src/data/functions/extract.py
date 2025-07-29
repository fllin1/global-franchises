# -*- coding: utf-8 -*-
"""
Data Extraction.

This module has 2 main functions:
- `scraping`: Scrapes franchise data from FranServe and saves it to HTML files.
- `extract`: Extracts data from the saved HTML files and converts it to JSON format.
"""

import json
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
from src.data.nlp.genai_data import (
    PROMPT_FRANSERVE_DATA,
    generate_franchise_data_with_retry,
)


def scrape():
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
    for url in tqdm(franchise_urls, total=len(franchise_urls), desc="Scraping franchise data"):
        data = get_franchise_data(session, url)
        file_name = quote(url.split("/")[-1], safe="") + ".html"
        save_franchise_data(data, file_name)


def rule_based_parsing():
    """
    Run the rule-based parsing of the HTML files saved in the EXTERNAL_DATA_DIR.
    This will convert the HTML files to JSON files.
    """

    html_files = list(EXTERNAL_DATA_DIR.glob("*.html"))
    for file_path in tqdm(html_files, total=len(html_files), desc="Parsing HTML files"):
        with open(file_path, "r", encoding="utf-8") as f:
            html_content = f.read()

        data = process_franchise_html(html_content)

        file_name = file_path.name.replace(".html", ".json")
        output_path = RAW_DATA_DIR / "franserve" / "rule_based" / file_name
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)


def ai_assited_parsing():
    """
    Run the AI-assisted parsing of the HTML files saved in the EXTERNAL_DATA_DIR.
    This will convert the HTML files to JSON files.
    """

    html_files = list(EXTERNAL_DATA_DIR.glob("*.html"))
    failed_files = []

    for file_path in html_files:
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
            output_path = RAW_DATA_DIR / "franserve" / file_name
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, "w", encoding="utf-8") as f:
                json.dump(response_json, f, indent=4)

    print(f"Failed to process {len(failed_files)} files out of {len(html_files)}.")
    print(f"Failed files: {failed_files}")
