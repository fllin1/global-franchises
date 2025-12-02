from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from loguru import logger
from src.api.config.supabase_config import supabase_client
from src.backend.search import search_franchises_by_state

router = APIRouter(prefix="/api/franchises", tags=["franchises"])
family_brands_router = APIRouter(prefix="/api/family-brands", tags=["family-brands"])

@router.get("/search")
async def search_franchises(q: Optional[str] = Query(None, min_length=0)):
    """
    Fuzzy search for franchises by name.
    If no query provided, returns a default list of franchises.
    """
    try:
        logger.info(f"Searching franchises for query: {q}")
        
        query_builder = supabase_client().table("franchises") \
            .select("id, franchise_name, primary_category, description_text, total_investment_min_usd, slug, logo_url")
            
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
    Returns hierarchy: State -> County -> City -> Territory Check details.
    
    The hierarchy is flexible - if county is not available, "Unspecified County" is used.
    
    Availability logic (bottom-up aggregation):
    - State level: unavailable if ALL counties are unavailable OR state is in unavailable_states
    - County level: unavailable if ALL cities are unavailable
    - City level: unavailable if ALL zips are unavailable
    - Zip level: unavailable if ALL checks are unavailable
    """
    try:
        logger.info(f"Fetching territory checks for Franchise ID: {franchise_id}")
        
        # Fetch franchise-level unavailable_states
        franchise_response = supabase_client().table("franchises") \
            .select("unavailable_states") \
            .eq("id", franchise_id) \
            .execute()
        
        unavailable_states = []
        if franchise_response.data and franchise_response.data[0]:
            unavailable_states = franchise_response.data[0].get("unavailable_states") or []
        
        # Fetch all territory checks for this franchise
        response = supabase_client().table("territory_checks") \
            .select("*") \
            .eq("franchise_id", franchise_id) \
            .execute()
            
        raw_data = response.data
        
        # Organize into 4-level hierarchy: State -> County -> City -> TerritoryCheck[]
        hierarchy: Dict[str, Dict[str, Dict[str, List[Any]]]] = {}
        
        for item in raw_data:
            state = item.get('state_code') or "Unknown"
            county = item.get('county') or "Unspecified County"
            city = item.get('city') or "Unspecified Area"
            
            # Initialize nested dictionaries as needed
            if state not in hierarchy:
                hierarchy[state] = {}
            
            if county not in hierarchy[state]:
                hierarchy[state][county] = {}
            
            if city not in hierarchy[state][county]:
                hierarchy[state][county][city] = []
            
            # Transform field names for frontend compatibility
            # DB may have location_raw already, or raw_text as legacy
            # DB has availability_status already from new inserts
            transformed_item = {
                **item,
                # Ensure location_raw exists (handle legacy raw_text field)
                "location_raw": item.get("location_raw") or item.get("raw_text", ""),
                # Ensure availability_status exists (handle legacy is_available field)
                "availability_status": item.get("availability_status") or (
                    "Available" if item.get("is_available") else "Not Available"
                ),
                # Include county in the item for frontend access
                "county": county if county != "Unspecified County" else None,
            }
            hierarchy[state][county][city].append(transformed_item)
            
        return {
            "franchise_id": franchise_id,
            "territory_count": len(raw_data),
            "states": hierarchy,
            "unavailable_states": unavailable_states,
        }
        
    except Exception as e:
        logger.error(f"Error fetching territories for {franchise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{franchise_id}")
async def get_franchise_detail(franchise_id: int):
    """
    Get full details for a specific franchise.
    Includes family brand info and sibling franchises if the franchise belongs to one.
    """
    try:
        logger.info(f"Fetching franchise details for ID: {franchise_id}")
        
        # Use the view that includes family brand info
        response = supabase_client().table("franchises_with_family").select("*").eq("id", franchise_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Franchise not found")
        
        franchise = response.data[0]
        
        # If franchise has a parent family brand, fetch the full family brand details and sibling franchises
        if franchise.get("parent_family_brand_id"):
            family_response = supabase_client().table("family_of_brands") \
                .select("id, name, source_id, website_url, logo_url") \
                .eq("id", franchise["parent_family_brand_id"]) \
                .execute()
            
            if family_response.data:
                franchise["family_brand"] = family_response.data[0]
            
            # Fetch sibling franchises (other franchises from the same family, excluding current)
            siblings_response = supabase_client().table("franchises") \
                .select("id, franchise_name, primary_category, total_investment_min_usd, logo_url, slug") \
                .eq("parent_family_brand_id", franchise["parent_family_brand_id"]) \
                .neq("id", franchise_id) \
                .order("franchise_name") \
                .limit(6) \
                .execute()
            
            franchise["sibling_franchises"] = siblings_response.data or []
            
        return franchise
    except Exception as e:
        logger.error(f"Error fetching franchise {franchise_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ============================================
# Family Brands Endpoints
# ============================================

@family_brands_router.get("/")
async def get_family_brands(q: Optional[str] = Query(None, min_length=0)):
    """
    Get all family brands with franchise counts.
    Optional search by name.
    """
    try:
        logger.info(f"Fetching family brands, query: {q}")
        
        # Get family brands
        query_builder = supabase_client().table("family_of_brands") \
            .select("id, name, source_id, website_url, contact_name, contact_phone, contact_email, logo_url, created_at")
        
        if q and len(q.strip()) > 0:
            query_builder = query_builder.ilike("name", f"%{q}%")
        
        query_builder = query_builder.order("name")
        response = query_builder.execute()
        
        family_brands = response.data or []
        
        # Get franchise counts for each family brand
        if family_brands:
            # Get all franchises with parent_family_brand_id in one query
            franchises_response = supabase_client().table("franchises") \
                .select("parent_family_brand_id") \
                .not_.is_("parent_family_brand_id", "null") \
                .execute()
            
            # Count franchises per family brand
            counts: Dict[int, int] = {}
            for f in (franchises_response.data or []):
                fb_id = f.get("parent_family_brand_id")
                if fb_id:
                    counts[fb_id] = counts.get(fb_id, 0) + 1
            
            # Attach counts to family brands
            for fb in family_brands:
                fb["franchise_count"] = counts.get(fb["id"], 0)
        
        return family_brands
    except Exception as e:
        logger.error(f"Error fetching family brands: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@family_brands_router.get("/{family_brand_id}")
async def get_family_brand_detail(family_brand_id: int):
    """
    Get detailed info for a specific family brand including all representing franchises.
    """
    try:
        logger.info(f"Fetching family brand details for ID: {family_brand_id}")
        
        # Get family brand details
        response = supabase_client().table("family_of_brands") \
            .select("*") \
            .eq("id", family_brand_id) \
            .execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Family brand not found")
        
        family_brand = response.data[0]
        
        # Get all franchises belonging to this family brand
        franchises_response = supabase_client().table("franchises") \
            .select("id, franchise_name, primary_category, description_text, total_investment_min_usd, slug") \
            .eq("parent_family_brand_id", family_brand_id) \
            .order("franchise_name") \
            .execute()
        
        family_brand["franchises"] = franchises_response.data or []
        family_brand["franchise_count"] = len(family_brand["franchises"])
        
        return family_brand
    except Exception as e:
        logger.error(f"Error fetching family brand {family_brand_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
