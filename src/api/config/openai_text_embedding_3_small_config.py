# -*- coding: utf-8 -*-
"""
Config for OpenAI text embeddings.
"""

import os

from dotenv import load_dotenv
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"  # OpenAI's current recommended model


def openai_client():
    """
    Initialize the OpenAI client.
    """
    load_dotenv()

    openai_api_key = os.getenv("OPENAI_API_KEY")
    client = OpenAI(api_key=openai_api_key)

    return client
