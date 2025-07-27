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


def supabase_client():
    """
    Initialize the Supabase client.
    """
    load_dotenv()  # Load environment variables from .env file

    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_KEY")

    if not supabase_url or not supabase_key:
        logger.error("Error: SUPABASE_URL and SUPABASE_KEY must be set in your .env file.")
        sys.exit(1)

    logger.info("Initializing Supabase client...")
    supabase: Client = create_client(supabase_url, supabase_key)

    return supabase
