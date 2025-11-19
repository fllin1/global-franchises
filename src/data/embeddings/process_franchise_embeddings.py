# -*- coding: utf-8 -*-
"""
Script to process existing franchises in Supabase, clean their data,
generate embeddings, and update the records.
"""

import ast
import json
import time
from typing import Any, List, Optional

from loguru import logger
from tqdm import tqdm

from src.api.config.supabase_config import supabase_client
from src.api.openai_text_embedding_3_small import generate_text_embedding_3_small


def clean_python_list_string(value: Any) -> str:
    """
    Attempts to parse a string that looks like a Python list or JSON array
    into a clean space-separated string.
    e.g. "['Item 1', 'Item 2']" -> "Item 1 Item 2"
    """
    if not value:
        return ""

    # If it's already a list, just join it
    if isinstance(value, list):
        return " ".join([str(v) for v in value if v])

    # If it's not a string, convert to string
    if not isinstance(value, str):
        return str(value)

    cleaned_value = value.strip()
    
    # Handle double encoded strings if present (e.g. "\"['a']\"")
    if cleaned_value.startswith('"') and cleaned_value.endswith('"'):
        try:
            cleaned_value = json.loads(cleaned_value)
        except json.JSONDecodeError:
            pass
            
    if isinstance(cleaned_value, list):
         return " ".join([str(v) for v in cleaned_value if v])

    # Try parsing as Python literal (list)
    if cleaned_value.startswith("[") and cleaned_value.endswith("]"):
        try:
            parsed = ast.literal_eval(cleaned_value)
            if isinstance(parsed, list):
                return " ".join([str(v) for v in parsed if v])
        except (ValueError, SyntaxError):
            pass

    # Clean up common artifacts if parsing failed but it looks like a list
    if "['" in cleaned_value or "']" in cleaned_value:
        cleaned_value = cleaned_value.replace("['", "").replace("']", "").replace("', '", " ")
    
    return cleaned_value


def create_embedding_text(franchise: dict) -> str:
    """
    Constructs the rich text representation for embedding.
    """
    name = franchise.get("franchise_name", "") or ""
    
    primary_cat = clean_python_list_string(franchise.get("primary_category"))
    sub_cats = clean_python_list_string(franchise.get("sub_categories"))
    
    description = franchise.get("description_text", "") or ""
    summary = clean_python_list_string(franchise.get("why_franchise_summary"))
    ideal_candidate = clean_python_list_string(franchise.get("ideal_candidate_profile_text"))
    
    # Combine into a structured document
    # We weight the name and categories slightly by position, but mainly just concatenating.
    parts = [
        f"Franchise: {name}",
        f"Categories: {primary_cat} {sub_cats}",
        f"Description: {description}",
        f"Why this franchise: {summary}",
        f"Ideal Candidate: {ideal_candidate}"
    ]
    
    return "\n".join(parts)


def process_franchises():
    supabase = supabase_client()
    
    logger.info("Fetching franchises from Supabase...")
    # Fetch all franchises (assuming < 1000 for now, or we paginate)
    # Since we know it's 769, we can fetch all. Supabase API default limit is usually 1000.
    response = supabase.table("Franchises").select("*").execute()
    franchises = response.data
    
    if not franchises:
        logger.warning("No franchises found.")
        return

    logger.info(f"Found {len(franchises)} franchises. Starting processing...")

    updates = []
    
    # Batch processing to respect API limits and optimize network
    BATCH_SIZE = 20
    
    for i in tqdm(range(0, len(franchises), BATCH_SIZE)):
        batch = franchises[i : i + BATCH_SIZE]
        texts_to_embed = []
        ids_in_batch = []
        
        for franchise in batch:
            text = create_embedding_text(franchise)
            texts_to_embed.append(text)
            ids_in_batch.append(franchise["id"])
        
        try:
            # Generate embeddings
            embedding_response = generate_text_embedding_3_small(texts_to_embed)
            embeddings = [item.embedding for item in embedding_response.data]
            
            # Prepare updates
            for j, embedding in enumerate(embeddings):
                # We update individually or we can try upserting if we have all fields. 
                # Updating by ID is safer to not overwrite other fields if we were just patching,
                # but upsert requires all non-nullable fields or default handling.
                # Simplest here is individual updates or a batch upsert if we construct the object right.
                # Let's do individual updates for safety on this tracer bullet.
                
                # Actually, Supabase-py doesn't support bulk update with different values easily without upsert.
                # Let's try to just update the embedding field for the ID.
                
                supabase.table("Franchises").update({"franchise_embedding": embedding}).eq("id", ids_in_batch[j]).execute()
                
            # Rate limit safeguard
            time.sleep(0.1)
            
        except Exception as e:
            logger.error(f"Error processing batch starting at index {i}: {e}")

    logger.success("Finished processing and updating embeddings.")


if __name__ == "__main__":
    process_franchises()

