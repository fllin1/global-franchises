from typing import List, Dict, Any, Optional
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
    location_filter = profile.state_code
    logger.info(f"Executing hybrid search in Supabase. Max budget: {max_budget}, Location: {location_filter}, match_count: {match_count}")
    
    params = {
        "query_embedding": query_embedding,
        "match_threshold": 0.3, # Threshold can be tuned
        "match_count": match_count,
        "max_budget": max_budget, # Can be None
        "location_filter": location_filter # Can be None
    }
    
    try:
        response = supabase_client().rpc("match_franchises_hybrid", params).execute()
        results = response.data
        logger.info(f"Hybrid search returned {len(results)} results (requested {match_count})")
        return results
    except Exception as e:
        logger.error(f"Supabase search failed: {e}")
        raise e

async def search_franchises_by_state(state_code: str, limit: int = 200) -> List[Dict[str, Any]]:
    """
    Searches for franchises available in a specific state.
    
    Args:
        state_code (str): The 2-letter state code (e.g., 'TX', 'NY').
        limit (int): Maximum number of results to return.
        
    Returns:
        List[Dict[str, Any]]: List of available franchises.
    """
    logger.info(f"Searching for franchises in state: {state_code}")
    
    try:
        # RPC function expects 'filter_state_code', not 'state_code_input'
        # And it doesn't take 'limit_count' in the provided definition, but if we want to be safe 
        # we can try to pass it if the SQL function was updated, otherwise just pass filter_state_code.
        # Based on the SQL file provided:
        # create or replace function get_franchises_by_state (
        #   filter_state_code text
        # )
        
        params = {
            "filter_state_code": state_code
        }
        
        response = supabase_client().rpc("get_franchises_by_state", params).execute()
        results = response.data
        
        # The SQL function doesn't have a limit, so we slice it here if needed
        if results and len(results) > limit:
            results = results[:limit]
            
        logger.info(f"State search returned {len(results)} results for {state_code}")
        return results
    except Exception as e:
        logger.error(f"Supabase state search failed: {e}")
        # Fallback or re-raise?
        # If the RPC doesn't exist, we should probably create it.
        # For now, let's assume we can create the RPC.
        raise e
