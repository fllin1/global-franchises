from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from loguru import logger
from src.api.config.supabase_config import supabase_client
from src.backend.search import search_franchises_by_state

router = APIRouter(prefix="/api/franchises", tags=["franchises"])

@router.get("/search")
async def search_franchises(q: Optional[str] = Query(None, min_length=0)):
    """
    Fuzzy search for franchises by name.
    If no query provided, returns a default list of franchises.
    """
    try:
        logger.info(f"Searching franchises for query: {q}")
        
        query_builder = supabase_client().table("franchises") \
            .select("id, franchise_name, primary_category, description_text, total_investment_min_usd, slug")
            
        if q and len(q.strip()) > 0:
            # Perform ILIKE search on franchise_name if query exists
            query_builder = query_builder.ilike("franchise_name", f"%{q}%")
        else:
            # Default sort if no query
            query_builder = query_builder.order("franchise_name")
            
        response = query_builder.limit(50).execute()
            
        return response.data
    except Exception as e:
        logger.error(f"Error searching franchises: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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

@router.get("/{franchise_id}/territories")
async def get_franchise_territories(franchise_id: int):
    """
    Get structured territory availability for a franchise.
    Returns hierarchy: State -> City -> Zip details.
    """
    try:
        logger.info(f"Fetching territory checks for Franchise ID: {franchise_id}")
        
        # Fetch all territory checks for this franchise
        response = supabase_client().table("territory_checks") \
            .select("*") \
            .eq("franchise_id", franchise_id) \
            .execute()
            
        raw_data = response.data
        
        # Organize into hierarchy
        hierarchy = {}
        
        for item in raw_data:
            state = item.get('state_code') or "Unknown"
            city = item.get('city') or "Unspecified Area"
            
            if state not in hierarchy:
                hierarchy[state] = {}
            
            if city not in hierarchy[state]:
                hierarchy[state][city] = []
            
            # Transform field names for frontend compatibility
            # DB has raw_text and is_available, frontend expects location_raw and availability_status
            transformed_item = {
                **item,
                "location_raw": item.get("raw_text", ""),
                "availability_status": "Available" if item.get("is_available") else "Not Available"
            }
            hierarchy[state][city].append(transformed_item)
            
        return {
            "franchise_id": franchise_id,
            "territory_count": len(raw_data),
            "states": hierarchy
        }
        
    except Exception as e:
        logger.error(f"Error fetching territories for {franchise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{franchise_id}")
async def get_franchise_detail(franchise_id: int):
    """
    Get full details for a specific franchise.
    """
    try:
        logger.info(f"Fetching franchise details for ID: {franchise_id}")
        response = supabase_client().table("franchises").select("*").eq("id", franchise_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Franchise not found")
            
        return response.data[0]
    except Exception as e:
        logger.error(f"Error fetching franchise {franchise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
