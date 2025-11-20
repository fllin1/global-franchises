from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any
from loguru import logger
from src.api.config.supabase_config import supabase_client
from src.backend.search import search_franchises_by_state

router = APIRouter(prefix="/api/franchises", tags=["franchises"])

@router.get("/by-location")
async def get_franchises_by_location(state_code: str = Query(..., min_length=2, max_length=2)):
    """
    Returns franchises available in a specific state.
    """
    try:
        logger.info(f"Fetching franchises for state: {state_code}")
        results = await search_franchises_by_state(state_code)
        return results
    except Exception as e:
        logger.error(f"Error in get_franchises_by_location: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{franchise_id}")
async def get_franchise_detail(franchise_id: int):
    """
    Get full details for a specific franchise.
    """
    try:
        logger.info(f"Fetching franchise details for ID: {franchise_id}")
        response = supabase_client().table("Franchises").select("*").eq("id", franchise_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Franchise not found")
            
        return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching franchise {franchise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

