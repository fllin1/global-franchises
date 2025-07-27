# -*- coding: utf-8 -*-
"""
Config for Gemini API.
"""

import os

from google import genai
from google.genai import types

CLIENT = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)


def get_config_gemini_embedding_001(
    task_type: str = "SEMANTIC_SIMILARITY", output_dimensionality: int = 768
) -> types.EmbedContentConfig:
    """
    Get the config for the Gemini API.

    Args:
        task_type (str): The task type to use. Supported values:
            (SEMANTIC_SIMILARITY, CLASSIFICATION, CLUSTERING, RETRIEVAL_DOCUMENT,
            RETRIEVAL_QUERY, CODE_RETRIEVAL_QUERY, QUESTION_ANSWERING, FACT_VERIFICATION)
        output_dimensionality (int): The output dimensionality to use. Supported values:
            (768, 1536, 3072)

    Returns:
        types.EmbedContentConfig: The config for the Gemini API.
    """
    config = types.EmbedContentConfig(
        task_type=task_type, output_dimensionality=output_dimensionality
    )
    return config
