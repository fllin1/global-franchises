# -*- coding: utf-8 -*-
"""
Config for Supabase.
"""

import os
import sys

from dotenv import load_dotenv
from loguru import logger
from supabase import Client, create_client

# --- Tables ---
FRANCHISE_TABLE = "Franchises"
CONTACTS_TABLE = "Contacts"

# --- Storage ---
RAW_FRANCHISE_BUCKET = "raw-franchise-html"


def supabase_client():
    """
    Initialize the Supabase client.
    """
    # Load environment variables from .env and .env.local files
    # .env.local takes precedence over .env
    load_dotenv()  # Load .env first
    load_dotenv(".env.local")  # Then load .env.local (overrides .env if exists)

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        error_msg = "SUPABASE_URL and SUPABASE_KEY must be set as environment variables."
        logger.error(error_msg)
        # Raise exception instead of sys.exit to allow FastAPI to handle it gracefully
        raise ValueError(error_msg)

    logger.info("Initializing Supabase client...")
    try:
        supabase: Client = create_client(supabase_url, supabase_key)
        logger.info("Supabase client initialized successfully")
        return supabase
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {e}")
        raise
