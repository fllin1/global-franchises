# -*- coding: utf-8 -*-
"""
Functions to convert HTML to prompt for Gemini API.
"""

import re
import sys

from bs4 import BeautifulSoup
from google.genai import types
from loguru import logger

# --- Clean HTML ---


def format_html_for_llm(html_content: str) -> str:
    """
    Cleans raw HTML to produce a clean, structured text block for an LLM.

    - Parses the HTML using BeautifulSoup.
    - Extracts text from the main body to avoid script/style tags.
    - Uses newlines as separators to maintain content structure.
    - Removes excessive blank lines.

    Args:
        html_content: A string containing the raw HTML of a franchise page.

    Returns:
        A clean string of the page's textual content.
    """
    soup = BeautifulSoup(html_content, "html.parser")

    # Try to find a main content area, fall back to the whole body
    content_area = soup.find("div", class_="MainFont") or soup.body

    # Get text, using '\n' to preserve separations between tags
    if content_area:
        text = content_area.get_text(separator="\n", strip=True)
    else:
        logger.error("No main content area found in HTML")
        sys.exit(1)

    # Reduce multiple blank lines down to a maximum of two
    clean_text = re.sub(r"\n{3,}", "\n\n", text)

    return clean_text


# --- HTML to Parts ---


def create_gemini_parts(prompt: str, formatted_html: str) -> list[types.Part]:
    """
    Creates the list of parts for the Gemini API call.

    Args:
        prompt: The instructional prompt for the model.
        formatted_html: The cleaned HTML text to be analyzed.

    Returns:
        A list of parts ready for the genai.Content object.
    """
    return [
        types.Part(text=prompt),
        types.Part(text="\n--- FRANCHISE DATA TO PARSE ---\n"),
        types.Part(text=formatted_html),
    ]
