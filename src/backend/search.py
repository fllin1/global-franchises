from typing import List, Dict, Any
from loguru import logger
from src.api.config.supabase_config import supabase_client
from src.api.openai_text_embedding_3_small import generate_text_embedding_3_small
from src.backend.models import LeadProfile

async def hybrid_search(profile: LeadProfile, match_count: int = 10) -> List[Dict[str, Any]]:
    """
    Performs a hybrid search (vector + SQL filter) for franchises matching the lead profile.
    
    Args:
        profile (LeadProfile): The lead profile containing semantic query and liquidity/budget.
        match_count (int): Number of results to return.
        
    Returns:
        List[Dict[str, Any]]: List of matching franchises.
    """
    
    # 1. Generate embedding for the semantic query
    logger.info(f"Generating embedding for query: '{profile.semantic_query}'")
    try:
        # Note: generate_text_embedding_3_small is synchronous in the provided file, 
        # but we are in an async function. It's fine for now, but ideal to make it async if possible.
        # Checking src/api/openai_text_embedding_3_small.py: it uses openai_client().embeddings.create 
        # which is sync unless using AsyncOpenAI. 
        # For this tracer bullet, sync call is acceptable.
        embedding_response = generate_text_embedding_3_small([profile.semantic_query])
        query_embedding = embedding_response.data[0].embedding
    except Exception as e:
        logger.error(f"Failed to generate embedding: {e}")
        raise e

    # 2. Call Supabase RPC match_franchises_hybrid
    # Use effective_budget (investment_cap or liquidity) for the max_budget filter
    max_budget = profile.effective_budget
    logger.info(f"Executing hybrid search in Supabase. Max budget: {max_budget}, match_count: {match_count}")
    
    params = {
        "query_embedding": query_embedding,
        "match_threshold": 0.3, # Threshold can be tuned
        "match_count": match_count,
        "max_budget": max_budget # Can be None
    }
    
    try:
        response = supabase_client().rpc("match_franchises_hybrid", params).execute()
        results = response.data
        logger.info(f"Hybrid search returned {len(results)} results (requested {match_count})")
        return results
    except Exception as e:
        logger.error(f"Supabase search failed: {e}")
        raise e
