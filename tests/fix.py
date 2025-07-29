# -*- coding: utf-8 -*-
"""
This script fixes the JSON files by adding the source_id to the franchise_data.
"""

import json

from bs4 import BeautifulSoup
from loguru import logger
from tqdm import tqdm

from src.config import EXTERNAL_DATA_DIR, RAW_DATA_DIR

franserve_dir = RAW_DATA_DIR / "franserve"

json_files = list(franserve_dir.glob("*.json"))

logger.info(f"Found {len(json_files)} JSON files to process.")

for json_file in tqdm(json_files, desc="Processing JSON files"):
    with open(json_file, "r", encoding="utf-8") as f:
        response_json = json.load(f)

    html_file = EXTERNAL_DATA_DIR / f"{json_file.name.replace('.json', '.html')}"
    with open(html_file, "r", encoding="utf-8") as f:
        html_content = f.read()

    # Get the source_id directly from the HTML
    soup = BeautifulSoup(html_content, "html.parser")
    fran_id_tag = soup.find("input", {"name": "ZorID"})
    if fran_id_tag and fran_id_tag.get("value"):
        response_json["franchise_data"]["source_id"] = int(fran_id_tag["value"])

    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(response_json, f, indent=4)

logger.success(f"Processed {len(json_files)} JSON files.")
