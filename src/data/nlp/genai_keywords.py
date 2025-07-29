# -*- coding: utf-8 -*-
"""
Functions to extract keywords from franchise data using Gemini API.
"""

import ast
from datetime import datetime
import json
from typing import Any, Dict, List

from google import genai
from google.genai import types
from loguru import logger
import pandas as pd

from src.api.config.genai_gemini_config import (
    CLIENT,
    MODEL_FLASH,
    MODEL_FLASH_LITE,
    get_generate_content_config_keywords,
    get_thinking_config,
    get_tools,
)
from src.api.genai_gemini import generate
from src.config import CONFIG_DIR, RAW_DATA_DIR

# --- Step 1: Create the Summary from Structured Data ---


def create_summary_for_keyword_extraction(franchise_data: Dict[str, Any]) -> str:
    """
    Creates a clean, text-based summary from the structured franchise data
    to be used as input for keyword extraction.

    Args:
        franchise_data: The dictionary of data extracted by the first LLM call.

    Returns:
        A single string summarizing the franchise.
    """
    summary_parts = []

    # Helper to add a field to the summary if it exists
    def add_to_summary(key: str, label: str):
        value = franchise_data.get(key)
        if value:
            # If value is a list (like from JSON), join it
            if isinstance(value, list):
                value_str = ", ".join(value)
                summary_parts.append(f"{label}: {value_str}")
            else:
                summary_parts.append(f"{label}: {value}")

    add_to_summary("franchise_name", "Franchise Name")
    add_to_summary("description_text", "Description")
    add_to_summary("why_franchise_summary", "Key Benefits")
    add_to_summary("ideal_candidate_profile_text", "Ideal Candidate")

    # NOTE : Investment details should belong to hard filters
    # # Create a composite investment summary
    # min_inv = franchise_data.get("total_investment_min_usd")
    # max_inv = franchise_data.get("total_investment_max_usd")
    # if min_inv and max_inv:
    #     summary_parts.append(f"Total Investment: ${min_inv:,} - ${max_inv:,}")

    # Create a composite ownership model summary
    ownership_model = []
    if franchise_data.get("is_home_based"):
        ownership_model.append("Home-Based")
    if franchise_data.get("allows_absentee"):
        ownership_model.append("Absentee Ownership")
    elif franchise_data.get("allows_semi_absentee"):
        ownership_model.append("Semi-Absentee Ownership")
    if franchise_data.get("e2_visa_friendly"):
        ownership_model.append("E2 Visa Friendly")

    if ownership_model:
        summary_parts.append(f"Business Model: {', '.join(ownership_model)}")

    return "\n".join(summary_parts)


# --- Step 2: Call the LLM and Extract Keywords ---


def extract_keywords(
    client: genai.Client,
    model: str,
    prompt: str,
    franchise_summary: str,
    source_id: int,
) -> List[str] | None:
    """
    Calls the Gemini API to extract keywords from a franchise summary.

    Args:
        client: The initialized genai.Client.
        model: The name of the model to use (e.g., 'gemini-1.5-pro-latest').
        prompt: The keyword extraction prompt.
        franchise_summary: The text summary of the franchise.

    Returns:
        A list of keywords, or None if an error occurs.
    """
    parts = [
        types.Part(text=prompt),
        types.Part(text="\n--- FRANCHISE SUMMARY ---\n"),
        types.Part(text=franchise_summary),
    ]

    # NOTE: gemini config parameters
    generate_content_config = get_generate_content_config_keywords(
        # thinking_config=get_thinking_config(thinking_budget=-1),
        # tools=get_tools(google_search=True, url_context=True),
    )

    response = generate(
        client=client,
        model=model,
        parts=parts,
        generate_content_config=generate_content_config,
    )

    # Print token usage for cost estimation
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        input_tokens = response.usage_metadata.prompt_token_count
        thoughts_token_count = response.usage_metadata.thoughts_token_count
        output_tokens = response.usage_metadata.candidates_token_count
        logger.info(
            f"Token usage - Input: {input_tokens}, "
            f"Thought: {thoughts_token_count}, "
            f"Output: {output_tokens}"
        )
    else:
        logger.warning("Token usage information not available in response")

    try:
        log_dir = RAW_DATA_DIR / "keywords"
        log_dir.mkdir(parents=True, exist_ok=True)
        with open(
            log_dir / f"keywords_{source_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
            "w",
            encoding="utf-8",
        ) as file:
            json.dump(response.to_json_dict(), file, indent=4)
    except FileNotFoundError:
        logger.error("Failed to save response to file json")

    keywords = ast.literal_eval(response.text)

    if isinstance(keywords, list):
        return keywords

    logger.error(f"Received: {response.text}")
    raise ValueError("Error: LLM response did not contain a valid list of keywords.")


def extract_keywords_with_retry(
    client: genai.Client,
    model: str,
    prompt: str,
    franchise_summary: str,
    source_id: int,
) -> List[str] | None:
    """
    Extract keywords from a franchise summary with retry logic.
    """
    max_retries = 3

    for attempt in range(max_retries):
        try:
            return extract_keywords(client, model, prompt, franchise_summary, source_id)
        except (ValueError, SyntaxError) as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            continue

    logger.error("All attempts failed")
    return None


def main():
    """
    Main function to run the keyword extraction pipeline with upsert support.
    """
    output_path = RAW_DATA_DIR / "keywords.csv"

    # Define schema: you can add more fields later!
    columns = ["source_id", "keywords"]

    # Read existing data
    if output_path.exists():
        df_existing = pd.read_csv(output_path)
    else:
        df_existing = pd.DataFrame(columns=columns)

    # Load prompt
    prompt_path = CONFIG_DIR / "franserve" / "keywords_prompt.txt"
    with open(prompt_path, "r", encoding="utf-8") as file:
        prompt_keywords = file.read()

    # Process each franchise
    franchise_data_paths = list((RAW_DATA_DIR / "franserve").glob("*.json"))
    logger.info(f"Found {len(franchise_data_paths)} franchises files.")

    for franchise_data_path in franchise_data_paths:
        logger.debug(f"Processing {franchise_data_path.name}")

        with open(franchise_data_path, "r", encoding="utf-8") as file:
            raw_data = json.load(file)
        franchise_data = raw_data["franchise_data"]
        source_id = int(raw_data.get("source_id"))

        # Generate inputs
        franchise_summary = create_summary_for_keyword_extraction(franchise_data)
        keywords = extract_keywords_with_retry(
            client=CLIENT,
            # model=MODEL_FLASH,
            model=MODEL_FLASH_LITE,
            prompt=prompt_keywords,
            franchise_summary=franchise_summary,
            source_id=source_id,
        )
        if len(keywords) == 0:
            logger.warning(f"No keywords found for {source_id}")
            continue
        if len(keywords) > 10:
            logger.warning(f"Too many keywords found for {source_id}")
            keywords = keywords[:10]

        # Create new row (easy to extend with more fields!)
        new_row: Dict[str, Any] = {
            "source_id": source_id,
            "keywords": ", ".join(keywords),
        }

        # UPSERT: Remove any existing row with this source_id
        df_existing = df_existing[df_existing["source_id"] != source_id]

        # Append new data
        df_new_row = pd.DataFrame([new_row])
        df_existing = pd.concat([df_existing, df_new_row], ignore_index=True)

        logger.success(f"Processed {source_id}")
        break

    df_to_save = df_existing.copy()
    df_to_save.to_csv(output_path, index=False)
    logger.info(f"Saved {len(df_to_save)} franchises to {output_path}")


if __name__ == "__main__":
    main()
