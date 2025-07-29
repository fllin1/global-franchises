# -*- coding: utf-8 -*-
"""
Generate franchise data from HTML using Gemini API.
"""

import json
import random

from bs4 import BeautifulSoup
from google.genai import types
from loguru import logger

from src.api.config.genai_gemini_config import (
    CLIENT,
    MODEL_FLASH_LITE,
    get_generate_content_config_franserve_data,
)
from src.api.genai_gemini import generate
from src.config import CONFIG_DIR, EXTERNAL_DATA_DIR, RAW_DATA_DIR
from src.data.franserve.html_to_prompt import (
    create_gemini_parts,
    format_html_for_llm,
)

PROMPT_FRANSERVE_DATA = (CONFIG_DIR / "franserve" / "data_prompt.txt").read_text()


def generate_franchise_data_with_retry(
    parts: list[types.Part], max_retries: int = 3
) -> dict | None:
    """
    Generate franchise data from HTML parts with retry logic.

    Args:
        parts: The parts to send to the Gemini API.
        max_retries: Maximum number of retry attempts.

    Returns:
        Parsed JSON response or None if all attempts fail.
    """
    for attempt in range(max_retries):
        try:
            if attempt == 0:
                seed = 0
            else:
                seed = random.randint(0, 1000000)
            response = generate(
                client=CLIENT,
                model=MODEL_FLASH_LITE,
                parts=parts,
                generate_content_config=get_generate_content_config_franserve_data(seed),
            )

            # Log token usage for cost estimation
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                input_tokens = response.usage_metadata.prompt_token_count
                output_tokens = response.usage_metadata.candidates_token_count
                logger.info(f"Token usage - Input: {input_tokens}, Output: {output_tokens}")
            else:
                logger.warning("Token usage information not available in response")

            # Try to parse JSON response
            response_text = response.text.replace("```json", "").replace("```", "")
            response_json = json.loads(response_text)
            logger.debug(f"Successfully generated and parsed response on attempt {attempt + 1}")
            return response_json

        except json.decoder.JSONDecodeError as e:
            if attempt < max_retries - 1:
                logger.warning(
                    f"JSON decode error on attempt {attempt + 1}/"
                    f"{max_retries}: {str(e)}. Retrying..."
                )
                exit()
            else:
                logger.error(
                    f"Failed to convert response to JSON after {max_retries} attempts: {str(e)}"
                )
    return None


def main():
    """
    Main function to run the html formatter to prompt.
    """
    html_files = list(EXTERNAL_DATA_DIR.glob("*.html"))

    logger.info(f"Found {len(html_files)} HTML files to process.")
    failed_files = []

    for i, file_path in enumerate(html_files):
        logger.debug(f"Processing {file_path.name}")
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
        logger.success(f"Processed ({i + 1}/{len(html_files)})")
        print("\n")

    logger.warning(f"Failed to process {len(failed_files)} files out of {len(html_files)}.")
    logger.info(f"Failed files: {failed_files}")


if __name__ == "__main__":
    main()
