# -*- coding: utf-8 -*-
"""
Functions to generate embeddings using the OpenAI API.
"""

from typing import List

from openai import types

from src.api.config.openai_text_embedding_3_small_config import EMBEDDING_MODEL, openai_client


def generate_text_embedding_3_small(
    texts: List[str], embedding_model: str = EMBEDDING_MODEL
) -> types.CreateEmbeddingResponse:
    """
    Generate embeddings for a text using the OpenAI API.

    Args:
        texts: The text to generate embeddings for.
        embedding_model: The model to use for generating embeddings.

    Returns:
        types.CreateEmbeddingResponse : The embeddings for the text.
    """
    embedding_response = openai_client().embeddings.create(input=texts, model=embedding_model)

    assert embedding_response.data[0].embedding is not None

    return embedding_response
