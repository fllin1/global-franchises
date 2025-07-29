# -*- coding: utf-8 -*-
"""
Generate franchise data from HTML using Gemini API.
"""

import json
import random
import sys

from google.genai import types
from loguru import logger

from src.api.config.genai_gemini_config import (
    CLIENT,
    MODEL_FLASH_LITE,
    get_generate_content_config_franserve_data,
)
from src.api.genai_gemini import generate
from src.config import CONFIG_DIR

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
                sys.exit()
            logger.error(
                f"Failed to convert response to JSON after {max_retries} attempts: {str(e)}"
            )
    return None
