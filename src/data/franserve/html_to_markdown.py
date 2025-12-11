# -*- coding: utf-8 -*-
"""
Functions to convert HTML to Markdown format.
"""

from bs4 import BeautifulSoup
from markdownify import markdownify as md

from loguru import logger


def convert_html_to_markdown(html_content: str | BeautifulSoup) -> str:
    """
    Converts HTML content to Markdown format.

    Args:
        html_content: Either a string containing HTML or a BeautifulSoup object.

    Returns:
        A string containing the Markdown representation of the HTML.
    """
    # Convert BeautifulSoup to string if needed
    if isinstance(html_content, BeautifulSoup):
        html_string = str(html_content)
    else:
        html_string = html_content

    # Use markdownify to convert HTML to Markdown
    # Configure markdownify to preserve structure
    markdown_content = md(
        html_string,
        heading_style="ATX",  # Use # style headings
        bullets="-",  # Use - for bullet points
        strip=["script", "style"],  # Strip script and style tags
    )

    return markdown_content























