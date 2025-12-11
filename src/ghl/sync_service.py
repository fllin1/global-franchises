# src/ghl/sync_service.py
"""
GHL Sync Service for two-way lead synchronization.

Handles syncing leads to GoHighLevel as contacts with pipeline opportunities,
and pulling opportunity stage changes back to update workflow_status.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from loguru import logger

from src.api.config.supabase_config import supabase_client
from src.ghl.api_client import (
    find_contact_by_email_or_phone,
    create_contact,
    update_contact,
    get_contact,
    get_or_create_lead_nurturing_pipeline,
    find_opportunity_for_contact,
    create_opportunity,
    update_opportunity,
    get_opportunity,
    get_stage_id_for_workflow_status,
    get_workflow_status_for_stage,
    get_or_create_custom_field,
    WORKFLOW_TO_STAGE,
)


# ---------- Custom Field Mappings ----------

# Map profile_data fields to GHL custom field definitions
# Format: profile_key -> (GHL field name, GHL data type)
CUSTOM_FIELD_MAPPINGS: Dict[str, Tuple[str, str]] = {
    # Financials (The Money)
    "liquidity": ("FG Liquidity", "MONETARY"),
    "investment_cap": ("FG Investment Cap", "MONETARY"),
    "net_worth": ("FG Net Worth", "MONETARY"),
    "investment_source": ("FG Investment Source", "SINGLE_LINE_TEXT"),
    
    # Location/Territory
    "location": ("FG Location", "SINGLE_LINE_TEXT"),
    "state_code": ("FG State", "SINGLE_LINE_TEXT"),
    "territories": ("FG Territories", "MULTI_LINE_TEXT"),
    
    # Profile/Intent (The Interest)
    "semantic_query": ("FG Search Intent", "MULTI_LINE_TEXT"),
    "role_preference": ("FG Role Preference", "SINGLE_LINE_TEXT"),
    "business_model_preference": ("FG Business Model", "SINGLE_LINE_TEXT"),
    "staff_preference": ("FG Staff Preference", "SINGLE_LINE_TEXT"),
    "franchise_categories": ("FG Categories", "MULTI_LINE_TEXT"),
    "home_based_preference": ("FG Home Based", "SINGLE_LINE_TEXT"),
    "absentee_preference": ("FG Absentee", "SINGLE_LINE_TEXT"),
    "semi_absentee_preference": ("FG Semi-Absentee", "SINGLE_LINE_TEXT"),
    "multi_unit_preference": ("FG Multi-Unit", "SINGLE_LINE_TEXT"),
    
    # Motives
    "trigger_event": ("FG Trigger Event", "SINGLE_LINE_TEXT"),
    "current_status": ("FG Current Status", "SINGLE_LINE_TEXT"),
    "experience_level": ("FG Experience", "SINGLE_LINE_TEXT"),
    "goals": ("FG Goals", "MULTI_LINE_TEXT"),
    "timeline": ("FG Timeline", "SINGLE_LINE_TEXT"),
}

# Lead-level fields (not from profile_data)
LEAD_FIELD_MAPPINGS: Dict[str, Tuple[str, str]] = {
    "qualification_status": ("FG Qualification Tier", "SINGLE_LINE_TEXT"),
}


# Cache for pipeline data to avoid repeated API calls
_pipeline_cache: Optional[Dict] = None


def _get_pipeline() -> Dict:
    """Get the Lead Nurturing pipeline, using cache if available."""
    global _pipeline_cache
    if _pipeline_cache is None:
        _pipeline_cache = get_or_create_lead_nurturing_pipeline()
    return _pipeline_cache


def _clear_pipeline_cache():
    """Clear the pipeline cache (useful for testing)."""
    global _pipeline_cache
    _pipeline_cache = None


def _format_custom_field_value(value: Any, data_type: str) -> Optional[str]:
    """
    Format a value for GHL custom field.
    
    - Booleans become "Yes"/"No"
    - Lists become newline-separated strings
    - Dicts (territories) are formatted as text
    - Numbers stay as numbers for MONETARY type
    """
    if value is None:
        return None
    
    if isinstance(value, bool):
        return "Yes" if value else "No"
    
    if isinstance(value, list):
        if not value:
            return None
        # Handle list of dicts (territories)
        if isinstance(value[0], dict):
            formatted_items = []
            for item in value:
                if isinstance(item, dict):
                    loc = item.get("location", "")
                    state = item.get("state_code", "")
                    formatted_items.append(f"{loc}, {state}" if state else loc)
                else:
                    formatted_items.append(str(item))
            return "\n".join(formatted_items)
        # Simple list of strings
        return "\n".join(str(item) for item in value)
    
    if isinstance(value, (int, float)) and data_type == "MONETARY":
        return value  # Keep as number for monetary
    
    return str(value)


def _build_custom_fields(profile_data: Dict, lead: Dict) -> List[Dict]:
    """
    Build GHL custom fields array from profile_data and lead.
    
    Returns list of {"id": field_id, "value": field_value} dicts.
    """
    custom_fields = []
    
    # Process profile_data fields
    for key, (field_name, data_type) in CUSTOM_FIELD_MAPPINGS.items():
        value = profile_data.get(key)
        formatted_value = _format_custom_field_value(value, data_type)
        
        if formatted_value is not None:
            field_id = get_or_create_custom_field(
                name=field_name,
                data_type=data_type,
                model="contact"
            )
            custom_fields.append({
                "id": field_id,
                "value": formatted_value,
            })
    
    # Process lead-level fields
    for key, (field_name, data_type) in LEAD_FIELD_MAPPINGS.items():
        value = lead.get(key)
        formatted_value = _format_custom_field_value(value, data_type)
        
        if formatted_value is not None:
            field_id = get_or_create_custom_field(
                name=field_name,
                data_type=data_type,
                model="contact"
            )
            custom_fields.append({
                "id": field_id,
                "value": formatted_value,
            })
    
    return custom_fields


def _get_opportunity_status(workflow_status: str) -> str:
    """
    Map workflow_status to GHL opportunity status.
    
    Returns "won", "lost", or "open".
    """
    if workflow_status == "closed_won":
        return "won"
    elif workflow_status == "disqualified":
        return "lost"
    else:
        return "open"


def _parse_location(location: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Parse a location string into city and state.
    
    Handles formats like:
    - "Austin, TX"
    - "Austin, Texas"
    - "TX"
    - "Austin"
    """
    if not location:
        return None, None
    
    location = location.strip()
    
    if "," in location:
        parts = location.split(",", 1)
        city = parts[0].strip()
        state = parts[1].strip() if len(parts) > 1 else None
        return city, state
    
    # Check if it's just a state code (2 letters)
    if len(location) == 2 and location.isalpha():
        return None, location.upper()
    
    # Assume it's a city
    return location, None


def sync_lead_to_ghl(lead_id: int) -> Dict:
    """
    Sync a lead to GoHighLevel.
    
    1. Find or create contact by email OR phone
    2. Build and attach custom fields from profile_data
    3. Create or update opportunity in pipeline
    4. Update lead with GHL IDs and sync timestamp
    
    Returns dict with sync results:
    {
        "success": bool,
        "lead_id": int,
        "ghl_contact_id": str or None,
        "ghl_opportunity_id": str or None,
        "action": str (created/updated/skipped),
        "error": str or None
    }
    """
    supabase = supabase_client()
    
    try:
        # 1. Get lead from database
        lead_resp = supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not lead_resp.data:
            return {
                "success": False,
                "lead_id": lead_id,
                "ghl_contact_id": None,
                "ghl_opportunity_id": None,
                "action": "error",
                "error": "Lead not found",
            }
        
        lead = lead_resp.data[0]
        profile_data = lead.get("profile_data", {}) or {}
        
        # Extract contact info from lead
        candidate_name = lead.get("candidate_name") or profile_data.get("candidate_name")
        email = profile_data.get("email")
        phone = profile_data.get("phone")
        location = profile_data.get("location")
        state_code = profile_data.get("state_code")
        liquidity = profile_data.get("liquidity")
        workflow_status = lead.get("workflow_status", "new_lead")
        
        # Parse location into city/state
        city, state = _parse_location(location)
        if not state and state_code:
            state = state_code
        
        # 2. Get or create pipeline
        pipeline = _get_pipeline()
        pipeline_id = pipeline.get("id")
        
        if not pipeline_id:
            return {
                "success": False,
                "lead_id": lead_id,
                "ghl_contact_id": None,
                "ghl_opportunity_id": None,
                "action": "error",
                "error": "Failed to get Lead Nurturing pipeline",
            }
        
        # 3. Build custom fields from profile_data
        custom_fields = _build_custom_fields(profile_data, lead)
        
        # 4. Find or create contact
        existing_ghl_contact_id = lead.get("ghl_contact_id")
        contact = None
        contact_action = "skipped"
        
        if existing_ghl_contact_id:
            # We already have a GHL contact ID - verify it still exists
            contact = get_contact(existing_ghl_contact_id)
            if contact:
                # Update existing contact with custom fields
                contact = update_contact(
                    contact_id=existing_ghl_contact_id,
                    first_name=candidate_name.split()[0] if candidate_name else None,
                    last_name=" ".join(candidate_name.split()[1:]) if candidate_name and len(candidate_name.split()) > 1 else None,
                    city=city,
                    state=state,
                    custom_fields=custom_fields if custom_fields else None,
                )
                contact_action = "updated"
        
        if not contact:
            # Try to find by email or phone
            contact = find_contact_by_email_or_phone(email=email, phone=phone)
            
            if contact:
                contact_action = "found"
                # Update tags and custom fields
                existing_tags = contact.get("tags", []) or []
                updated_tags = list(existing_tags)
                if "FranchisesGlobal Lead" not in existing_tags:
                    updated_tags.append("FranchisesGlobal Lead")
                
                contact = update_contact(
                    contact_id=contact.get("id"),
                    tags=updated_tags,
                    custom_fields=custom_fields if custom_fields else None,
                )
                contact_action = "updated"
            else:
                # Create new contact with distinguishing tags and custom fields
                tags = [
                    "FranchisesGlobal Lead",  # Primary identifier
                    f"Tier: {lead.get('qualification_status', 'unknown')}",
                ]
                
                contact = create_contact(
                    name=candidate_name,
                    email=email,
                    phone=phone,
                    city=city,
                    state=state,
                    tags=tags,
                    custom_fields=custom_fields if custom_fields else None,
                    source="FranchisesGlobal Lead",
                )
                contact_action = "created"
        
        contact_id = contact.get("id")
        if not contact_id:
            return {
                "success": False,
                "lead_id": lead_id,
                "ghl_contact_id": None,
                "ghl_opportunity_id": None,
                "action": "error",
                "error": "Failed to get or create contact",
            }
        
        # 5. Find or create opportunity
        existing_ghl_opportunity_id = lead.get("ghl_opportunity_id")
        opportunity = None
        opportunity_action = "skipped"
        
        # Get stage ID for current workflow status
        stage_id = get_stage_id_for_workflow_status(pipeline, workflow_status)
        if not stage_id:
            # Default to first stage if workflow status not found
            stages = pipeline.get("stages", [])
            if stages:
                stage_id = stages[0].get("id")
        
        # Get opportunity status based on workflow
        opp_status = _get_opportunity_status(workflow_status)
        
        if existing_ghl_opportunity_id:
            # We already have a GHL opportunity ID - verify it still exists
            opportunity = get_opportunity(existing_ghl_opportunity_id)
            if opportunity:
                # Update opportunity stage and status
                current_stage_id = opportunity.get("pipelineStageId")
                current_status = opportunity.get("status")
                
                if current_stage_id != stage_id or current_status != opp_status:
                    opportunity = update_opportunity(
                        opportunity_id=existing_ghl_opportunity_id,
                        stage_id=stage_id,
                        status=opp_status,
                    )
                    opportunity_action = "updated"
                else:
                    opportunity_action = "skipped"
        
        if not opportunity:
            # Try to find existing opportunity for this contact in pipeline
            opportunity = find_opportunity_for_contact(contact_id, pipeline_id)
            
            if opportunity:
                opportunity_action = "found"
                # Update stage and status if different
                current_stage_id = opportunity.get("pipelineStageId")
                current_status = opportunity.get("status")
                
                if current_stage_id != stage_id or current_status != opp_status:
                    opportunity = update_opportunity(
                        opportunity_id=opportunity.get("id"),
                        stage_id=stage_id,
                        status=opp_status,
                    )
                    opportunity_action = "updated"
            else:
                # Create new opportunity
                opportunity_name = f"Franchise Lead: {candidate_name or f'Lead #{lead_id}'}"
                
                # Set monetary value based on liquidity
                monetary_value = liquidity if liquidity else None
                
                opportunity = create_opportunity(
                    contact_id=contact_id,
                    pipeline_id=pipeline_id,
                    stage_id=stage_id,
                    name=opportunity_name,
                    monetary_value=monetary_value,
                    status=opp_status,
                )
                opportunity_action = "created"
        
        opportunity_id = opportunity.get("id")
        if not opportunity_id:
            return {
                "success": False,
                "lead_id": lead_id,
                "ghl_contact_id": contact_id,
                "ghl_opportunity_id": None,
                "action": "error",
                "error": "Failed to get or create opportunity",
            }
        
        # 6. Update lead with GHL IDs and sync timestamp
        now = datetime.now(timezone.utc).isoformat()
        supabase.table("leads").update({
            "ghl_contact_id": contact_id,
            "ghl_opportunity_id": opportunity_id,
            "ghl_last_synced_at": now,
            "updated_at": now,
        }).eq("id", lead_id).execute()
        
        # Determine overall action
        if contact_action == "created" or opportunity_action == "created":
            action = "created"
        elif contact_action == "updated" or opportunity_action == "updated":
            action = "updated"
        else:
            action = "synced"
        
        logger.info(f"Synced lead {lead_id} to GHL: contact={contact_id}, opportunity={opportunity_id}, action={action}")
        
        return {
            "success": True,
            "lead_id": lead_id,
            "ghl_contact_id": contact_id,
            "ghl_opportunity_id": opportunity_id,
            "action": action,
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Error syncing lead {lead_id} to GHL: {e}")
        return {
            "success": False,
            "lead_id": lead_id,
            "ghl_contact_id": None,
            "ghl_opportunity_id": None,
            "action": "error",
            "error": str(e),
        }


def sync_from_ghl(lead_id: int) -> Dict:
    """
    Pull opportunity stage from GHL and update lead workflow_status.
    
    Only updates if the opportunity stage has changed since last sync.
    
    Returns dict with sync results:
    {
        "success": bool,
        "lead_id": int,
        "workflow_status": str or None (new status if changed),
        "changed": bool,
        "error": str or None
    }
    """
    supabase = supabase_client()
    
    try:
        # 1. Get lead from database
        lead_resp = supabase.table("leads").select("*").eq("id", lead_id).execute()
        if not lead_resp.data:
            return {
                "success": False,
                "lead_id": lead_id,
                "workflow_status": None,
                "changed": False,
                "error": "Lead not found",
            }
        
        lead = lead_resp.data[0]
        opportunity_id = lead.get("ghl_opportunity_id")
        current_workflow_status = lead.get("workflow_status", "new_lead")
        
        if not opportunity_id:
            return {
                "success": False,
                "lead_id": lead_id,
                "workflow_status": current_workflow_status,
                "changed": False,
                "error": "Lead not synced to GHL (no opportunity ID)",
            }
        
        # 2. Get opportunity from GHL
        opportunity = get_opportunity(opportunity_id)
        if not opportunity:
            return {
                "success": False,
                "lead_id": lead_id,
                "workflow_status": current_workflow_status,
                "changed": False,
                "error": "Opportunity not found in GHL",
            }
        
        # 3. Get stage and map to workflow status
        pipeline = _get_pipeline()
        stage_id = opportunity.get("pipelineStageId")
        
        new_workflow_status = get_workflow_status_for_stage(pipeline, stage_id)
        
        if not new_workflow_status:
            logger.warning(f"Could not map GHL stage {stage_id} to workflow status for lead {lead_id}")
            return {
                "success": True,
                "lead_id": lead_id,
                "workflow_status": current_workflow_status,
                "changed": False,
                "error": None,
            }
        
        # 4. Update lead if status changed
        if new_workflow_status != current_workflow_status:
            now = datetime.now(timezone.utc).isoformat()
            supabase.table("leads").update({
                "workflow_status": new_workflow_status,
                "ghl_last_synced_at": now,
                "updated_at": now,
            }).eq("id", lead_id).execute()
            
            logger.info(f"Updated lead {lead_id} workflow status: {current_workflow_status} -> {new_workflow_status}")
            
            return {
                "success": True,
                "lead_id": lead_id,
                "workflow_status": new_workflow_status,
                "changed": True,
                "error": None,
            }
        
        return {
            "success": True,
            "lead_id": lead_id,
            "workflow_status": current_workflow_status,
            "changed": False,
            "error": None,
        }
        
    except Exception as e:
        logger.error(f"Error syncing from GHL for lead {lead_id}: {e}")
        return {
            "success": False,
            "lead_id": lead_id,
            "workflow_status": None,
            "changed": False,
            "error": str(e),
        }


def bulk_sync_leads_to_ghl(lead_ids: List[int]) -> Dict:
    """
    Sync multiple leads to GHL.
    
    Returns summary of sync results:
    {
        "total": int,
        "success": int,
        "failed": int,
        "results": List[Dict]
    }
    """
    results = []
    success_count = 0
    failed_count = 0
    
    for lead_id in lead_ids:
        result = sync_lead_to_ghl(lead_id)
        results.append(result)
        
        if result.get("success"):
            success_count += 1
        else:
            failed_count += 1
    
    return {
        "total": len(lead_ids),
        "success": success_count,
        "failed": failed_count,
        "results": results,
    }


def bulk_sync_from_ghl(lead_ids: List[int]) -> Dict:
    """
    Pull updates from GHL for multiple leads.
    
    Returns summary of sync results:
    {
        "total": int,
        "success": int,
        "failed": int,
        "changed": int,
        "results": List[Dict]
    }
    """
    results = []
    success_count = 0
    failed_count = 0
    changed_count = 0
    
    for lead_id in lead_ids:
        result = sync_from_ghl(lead_id)
        results.append(result)
        
        if result.get("success"):
            success_count += 1
            if result.get("changed"):
                changed_count += 1
        else:
            failed_count += 1
    
    return {
        "total": len(lead_ids),
        "success": success_count,
        "failed": failed_count,
        "changed": changed_count,
        "results": results,
    }


def two_way_sync_lead(lead_id: int) -> Dict:
    """
    Perform two-way sync for a lead:
    1. First pull from GHL (if already synced)
    2. Then push to GHL
    
    Returns combined results.
    """
    # First, try to pull from GHL
    pull_result = sync_from_ghl(lead_id)
    
    # Then push to GHL
    push_result = sync_lead_to_ghl(lead_id)
    
    return {
        "lead_id": lead_id,
        "pull": pull_result,
        "push": push_result,
        "success": push_result.get("success", False),
    }

