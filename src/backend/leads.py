from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional
from datetime import datetime
from src.backend.models import Lead, LeadCreate, LeadUpdate, LeadProfile
from src.api.config.supabase_config import supabase_client
from src.backend.extractor import extract_profile_from_notes
from loguru import logger

router = APIRouter(prefix="/api/leads", tags=["leads"])

def db_to_lead(row: dict) -> Lead:
    """Convert database row to Lead model"""
    # Ensure profile_data is a dict
    profile_data = row.get('profile_data', {})
    if not isinstance(profile_data, dict):
        profile_data = {} # Handle potential None or bad data

    return Lead(
        id=row['id'],
        candidate_name=row.get('candidate_name'),
        notes=row['notes'],
        profile_data=LeadProfile(**profile_data),
        matches=row.get('matches') or [],
        qualification_status=row['qualification_status'],
        workflow_status=row['workflow_status'],
        created_at=row['created_at'],
        updated_at=row['updated_at']
    )

@router.get("/", response_model=List[Lead])
async def list_leads(limit: int = 100, offset: int = 0):
    """List leads with pagination"""
    try:
        response = supabase_client().table("leads")\
            .select("*")\
            .order("created_at", desc=True)\
            .range(offset, offset + limit - 1)\
            .execute()
        return [db_to_lead(row) for row in response.data]
    except Exception as e:
        logger.error(f"Error listing leads: {e}")
        raise HTTPException(status_code=500, detail=str(e))

from src.backend.search import hybrid_search
from src.backend.narrator import generate_match_narratives

@router.post("/", response_model=Lead)
async def create_lead(lead_in: LeadCreate):
    """Create a new lead by analyzing notes"""
    try:
        logger.info(f"Creating lead from notes length: {len(lead_in.notes)}")
        
        # 1. Extract Profile
        profile = await extract_profile_from_notes(lead_in.notes)
        
        # 2. Determine qualification status
        status = "tier_2" if profile.is_tier_2 else "tier_1"
        
        # 3. Generate Matches & Narratives (Persistent)
        matches = await hybrid_search(profile, match_count=6)
        narratives = await generate_match_narratives(profile, matches)
        
        enriched_matches = []
        for m in matches:
            m_id = m.get('id')
            m['why_narrative'] = narratives.get(m_id, "Matched based on profile criteria.")
            enriched_matches.append(m)

        # 4. Insert into DB
        row_data = {
            "candidate_name": profile.candidate_name,
            "notes": lead_in.notes,
            "profile_data": profile.model_dump(mode='json'),
            "matches": enriched_matches,
            "qualification_status": status,
            "workflow_status": "new"
        }
        
        response = supabase_client().table("leads").insert(row_data).execute()
        if not response.data:
             raise HTTPException(status_code=500, detail="Failed to insert lead")
             
        return db_to_lead(response.data[0])
    except Exception as e:
        logger.error(f"Error creating lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{lead_id}", response_model=Lead)
async def get_lead(lead_id: int):
    """Get a specific lead by ID"""
    try:
        response = supabase_client().table("leads").select("*").eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        return db_to_lead(response.data[0])
    except Exception as e:
        logger.error(f"Error fetching lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.patch("/{lead_id}", response_model=Lead)
async def update_lead(lead_id: int, update: LeadUpdate):
    """Update a lead's details or profile"""
    try:
        # Prepare update data
        data = {}
        if update.candidate_name is not None:
            data['candidate_name'] = update.candidate_name
        if update.notes is not None:
            data['notes'] = update.notes
        if update.profile_data is not None:
            data['profile_data'] = update.profile_data.model_dump(mode='json')
            # Re-evaluate tier status if profile changes
            status = "tier_2" if update.profile_data.is_tier_2 else "tier_1"
            data['qualification_status'] = status
            
        if update.qualification_status is not None:
            data['qualification_status'] = update.qualification_status
        if update.workflow_status is not None:
            data['workflow_status'] = update.workflow_status
            
        if not data:
            # Nothing to update, return current state
            return await get_lead(lead_id)

        response = supabase_client().table("leads").update(data).eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
            
        return db_to_lead(response.data[0])
    except Exception as e:
        logger.error(f"Error updating lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/{lead_id}")
async def delete_lead(lead_id: int):
    """Delete a lead"""
    try:
        response = supabase_client().table("leads").delete().eq("id", lead_id).execute()
        if not response.data:
             raise HTTPException(status_code=404, detail="Lead not found or already deleted")
        return {"message": "Lead deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{lead_id}/matches")
async def get_lead_matches(lead_id: int):
    """Get franchise matches for a specific lead"""
    try:
        # 1. Get Lead
        response = supabase_client().table("leads").select("*").eq("id", lead_id).execute()
        if not response.data:
            raise HTTPException(status_code=404, detail="Lead not found")
        lead_data = response.data[0]
        
        # Check if matches already exist (persisted)
        if lead_data.get('matches') is not None:
            return lead_data['matches']
        
        # Fallback: Generate if missing (Lazy Load)
        logger.info(f"Matches missing for lead {lead_id}, generating now...")
        
        # Parse profile
        profile_data = lead_data.get('profile_data', {})
        profile = LeadProfile(**profile_data)
        
        # 2. Search
        matches = await hybrid_search(profile, match_count=6)
        
        # 3. Narratives
        narratives = await generate_match_narratives(profile, matches)
        
        enriched_matches = []
        for m in matches:
            m_id = m.get('id')
            m['why_narrative'] = narratives.get(m_id, "Matched based on profile criteria.")
            enriched_matches.append(m)
            
        # Save back to DB
        supabase_client().table("leads").update({"matches": enriched_matches}).eq("id", lead_id).execute()
            
        return enriched_matches
    except Exception as e:
        logger.error(f"Error fetching matches for lead {lead_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

