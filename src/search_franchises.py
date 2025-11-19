# -*- coding: utf-8 -*-
"""
Script to verify franchise matching logic using vector search.
"""

import argparse
import sys
from typing import List, Dict

from loguru import logger

from src.api.config.supabase_config import supabase_client
from src.api.openai_text_embedding_3_small import generate_text_embedding_3_small


def search_franchises(query: str, match_count: int = 10) -> List[Dict]:
    """
    Searches for franchises matching the query using vector similarity.
    """
    # 1. Generate embedding for the query
    logger.info(f"Generating embedding for query: '{query}'")
    embedding_response = generate_text_embedding_3_small([query])
    query_embedding = embedding_response.data[0].embedding

    # 2. Call Supabase RPC
    logger.info("Executing vector search in Supabase...")
    supabase = supabase_client()
    
    params = {
        "query_embedding": query_embedding,
        "match_threshold": 0.3, # Adjust threshold as needed
        "match_count": match_count
    }
    
    response = supabase.rpc("match_franchises", params).execute()
    
    return response.data


def main():
    parser = argparse.ArgumentParser(description="Search for franchises using AI embeddings.")
    parser.add_argument("query", type=str, help="The natural language search query")
    parser.add_argument("--limit", type=int, default=10, help="Number of results to return")
    
    if len(sys.argv) == 1:
        parser.print_help(sys.stderr)
        sys.exit(1)
        
    args = parser.parse_args()
    
    try:
        results = search_franchises(args.query, args.limit)
        
        if not results:
            print("\nNo matches found.")
            return

        print(f"\nTop {len(results)} Matches for '{args.query}':\n")
        print("-" * 80)
        
        for i, result in enumerate(results, 1):
            print(f"{i}. {result['franchise_name']} (Similarity: {result['similarity']:.4f})")
            print(f"   ID: {result['id']}")
            # Handle sub_categories which might be JSON/list or string
            cats = result.get('primary_category') or "N/A"
            sub_cats = result.get('sub_categories')
            if sub_cats:
                if isinstance(sub_cats, list):
                    cats += f" - {', '.join(str(x) for x in sub_cats)}"
                else:
                    cats += f" - {sub_cats}"
            
            print(f"   Category: {cats}")
            print(f"   Description: {result.get('description_text', '')[:200]}...")
            print("-" * 80)
            
    except Exception as e:
        logger.error(f"Search failed: {e}")


if __name__ == "__main__":
    main()

