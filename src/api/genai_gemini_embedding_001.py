# -*- coding: utf-8 -*-
"""
Functions to generate embeddings using the Gemini API.
"""

from typing import List

from google import genai

from src.api.config.genai_gemini_embedding_001_config import get_config_gemini_embedding_001


def generate_gemini_embedding_001(
    texts: List[str], task_type: str = "SEMANTIC_SIMILARITY", output_dimensionality: int = 768
) -> list[float] | None:
    """
    Generate embeddings for a text using the Gemini API.

    Args:
        texts: The text to generate embeddings for.
        task_type: The task type to use.
        output_dimensionality: The output dimensionality to use.

    Returns:
        list[float] | None: The embeddings for the text.
    """
    client = genai.Client()

    result = client.models.embed_content(
        model="gemini-embedding-001",
        contents=texts,
        config=get_config_gemini_embedding_001(task_type, output_dimensionality),
    )

    return result.embeddings
