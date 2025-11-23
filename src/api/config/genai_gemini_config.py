# -*- coding: utf-8 -*-
"""
Config to use Gemini models.
"""

import json
import os
from typing import List, Optional

from google import genai
from google.genai import types

from src.config import CONFIG_DIR

try:
    CLIENT = genai.Client(
        api_key=os.environ.get("GEMINI_API_KEY"),
    )
except Exception as e:
    print(f"Warning: Failed to initialize Gemini Client: {e}")
    CLIENT = None

MODEL_PRO = "gemini-2.5-pro"
MODEL_FLASH = "gemini-2.5-flash"
MODEL_FLASH_LITE = "gemini-2.5-flash-lite"


def get_tools(
    google_search: bool = False, url_context: bool = False, code_execution: bool = False
) -> list[types.Tool]:
    """
    Get the tools for the Gemini API.

    Args:
        google_search: Whether to use the Google Search tool.
        url_context: Whether to use the URL Context tool.
        code_execution: Whether to use the Code Execution tool.

    Returns:
        list[types.Tool]: The tools for the Gemini API.
    """
    tools = []
    if google_search:
        tools.append(types.Tool(googleSearch=types.GoogleSearch()))
    if code_execution:
        tools.append(types.Tool(codeExecution=types.ToolCodeExecution()))
    if url_context:
        tools.append(types.Tool(url_context=types.UrlContext()))
    return tools


def get_thinking_config(thinking_budget: Optional[int] = None) -> types.ThinkingConfig:
    """
    Get the thinking config for the Gemini API.

    Args:
        thinking_budget: The thinking budget for the Gemini API.

    Returns:
        types.ThinkingConfig: The thinking config for the Gemini API.
    """
    if thinking_budget:
        return types.ThinkingConfig(
            thinking_budget=thinking_budget,
        )
    return thinking_budget


with open(CONFIG_DIR / "franserve" / "structured_output.json", encoding="utf-8") as file:
    response_schema_franserve_data = json.load(file)


def get_generate_content_config_franserve_data(seed: int = 0) -> types.GenerateContentConfig:
    """
    Get the generate content config for the franserve data.

    Args:
        seed: The seed for the random number generator.

    Returns:
        types.GenerateContentConfig: The generate content config for the franserve data.
    """
    return types.GenerateContentConfig(
        temperature=1,
        top_p=1,
        seed=seed,
        max_output_tokens=65535,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        response_mime_type="application/json",
        response_schema=response_schema_franserve_data,
    )


# NOTE : Structured output is not supported with Google Search Features
# with open(CONFIG_DIR / "franserve" / "keywords_structured_output.json", encoding="utf-8") as file:
#     response_schema_keywords = json.load(file)


def get_generate_content_config_keywords(
    seed: int = 0,
    thinking_config: Optional[types.ThinkingConfig] = None,
    tools: Optional[List[types.Tool]] = None,
) -> types.GenerateContentConfig:
    """
    Get the generate content config for the keywords.

    Args:
        seed: The seed for the random number generator.
        thinking_config: The thinking config for the Gemini API.
        tools: The tools for the Gemini API.

    Returns:
        types.GenerateContentConfig: The generate content config for the keywords.
    """
    return types.GenerateContentConfig(
        temperature=1,
        top_p=1,
        seed=seed,
        max_output_tokens=65535,
        safety_settings=[
            types.SafetySetting(category="HARM_CATEGORY_HATE_SPEECH", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_DANGEROUS_CONTENT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_SEXUALLY_EXPLICIT", threshold="OFF"),
            types.SafetySetting(category="HARM_CATEGORY_HARASSMENT", threshold="OFF"),
        ],
        # NOTE : Structured output is not supported with Google Search Features
        # response_mime_type="application/json",
        # response_schema=response_schema_keywords,
        thinking_config=thinking_config,
        tools=tools,
    )
