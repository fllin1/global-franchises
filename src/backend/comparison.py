from typing import List, Optional
import json
import ast
from fastapi import APIRouter, HTTPException, Body
from loguru import logger

from src.api.config.supabase_config import supabase_client
from src.backend.models import (
    ComparisonResponse, 
    ComparisonItem, 
    LeadProfile, 
    OverviewAttributes,
    MoneyAttributes,
    MotivesAttributes,
    InterestAttributes,
    TerritoryAttributes,
    ValueAttributes
)
from src.backend.narrator import generate_comparison_analysis

router = APIRouter(prefix="/api/franchises/compare", tags=["comparison"])

@router.post("", response_model=ComparisonResponse)
async def compare_franchises(
    franchise_ids: List[int] = Body(..., min_items=1, max_items=10),
    lead_profile: Optional[LeadProfile] = Body(None)
):
    """
    Compare multiple franchises against a lead profile using the 
    "Money, Motives, Interest, Territories" framework.
    """
    try:
        logger.info(f"Comparing franchises: {franchise_ids}")
        
        # 1. Fetch Franchise Data
        response = supabase_client().table("franchises") \
            .select("*") \
            .in_("id", franchise_ids) \
            .execute()
            
        franchises = response.data
        if not franchises:
            raise HTTPException(status_code=404, detail="No franchises found")
            
        # Sort franchises to match input order (UX consistency)
        franchise_map = {f['id']: f for f in franchises}
        ordered_franchises = [franchise_map[fid] for fid in franchise_ids if fid in franchise_map]
        
        # 2. Fetch Territory Availability (Simplified Check)
        # For now, we'll check if there are any recent territory checks or unavailable states
        # In a real scenario, we might run a live check if we had a specific zip code
        
        # 3. Generate AI Analysis
        ai_analysis = await generate_comparison_analysis(lead_profile, ordered_franchises)
        
        # 4. Construct Response
        items = []
        for f in ordered_franchises:
            fid = f['id']
            analysis = ai_analysis.get(fid, {})
            
            # Parse franchises_data JSONB field
            f_data = f.get('franchises_data', {})
            if isinstance(f_data, str):
                try:
                    f_data = json.loads(f_data)
                except:
                    f_data = {}
            background = f_data.get('background', {}) if f_data else {}
            
            # --- Overview Attributes ---
            operating_franchises = None
            if background:
                total_franchisees = background.get('total_franchisees')
                if total_franchisees:
                    operating_franchises = str(total_franchisees)
            
            overview = OverviewAttributes(
                industry=f.get('primary_category') or 'Uncategorized',
                year_started=f.get('founded_year'),
                year_franchised=f.get('franchised_year'),
                operating_franchises=operating_franchises
            )
            
            # --- Money Attributes ---
            # Fallback values if AI fails or returns partial data
            money = analysis.get("money", {
                "financial_model": "Standard Franchise Agreement",
                "overhead_level": "Standard",
                "traffic_light": "yellow"
            })
            
            # Enhance Money attributes with real data if available
            min_inv = f.get('total_investment_min_usd')
            max_inv = f.get('total_investment_max_usd')
            inv_range = "Undisclosed"
            if min_inv and max_inv:
                inv_range = f"${min_inv:,.0f} - ${max_inv:,.0f}"
            elif min_inv:
                inv_range = f"Min ${min_inv:,.0f}"
                
            money["investment_range"] = inv_range
            money["liquidity_req"] = f.get('required_cash_investment_usd')
            money["net_worth_req"] = f.get('required_net_worth_usd')
            money["royalty"] = f.get('royalty_details_text')
            money["sba_registered"] = f.get('sba_registered') or False
            money["in_house_financing"] = f.get('financial_assistance_details')
            
            # Traffic Light Logic for Money (Budget Check)
            if lead_profile and lead_profile.effective_budget and min_inv:
                if min_inv > lead_profile.effective_budget:
                    money["traffic_light"] = "red"
                elif min_inv <= lead_profile.effective_budget:
                    money["traffic_light"] = "green"
            
            motives = analysis.get("motives", {
                "recession_resistance": "Unknown",
                "scalability": "Unknown",
                "market_demand": "Unknown",
                "passive_income_potential": "Unknown"
            })
            
            interest = analysis.get("interest", {
                "role": "Unknown",
                "sales_requirement": "Unknown",
                "inventory_level": "Unknown",
                "employees_count": "Unknown",
                "traffic_light": "yellow"
            })
            
            # --- Territory Attributes ---
            unavailable_raw = f.get('unavailable_states') or []
            # Handle case where unavailable_states might be a string representation of a list
            if isinstance(unavailable_raw, str):
                try:
                    unavailable = ast.literal_eval(unavailable_raw)
                except (ValueError, SyntaxError):
                    unavailable = []
            else:
                unavailable = unavailable_raw if isinstance(unavailable_raw, list) else []
            avail_status = "Check Required"
            
            if lead_profile and lead_profile.state_code:
                if lead_profile.state_code in unavailable:
                    avail_status = "Sold Out in State"
                else:
                    avail_status = "Likely Available"
            
            territories = TerritoryAttributes(
                availability_status=avail_status,
                territory_notes=f"Unavailable in: {', '.join(unavailable[:5])}" if unavailable else None,
                unavailable_states=unavailable if unavailable else None
            )
            
            # --- Value Attributes ---
            # Truncate description_text to reasonable length for display
            description = f.get('description_text') or ''
            if len(description) > 300:
                description = description[:300].rsplit(' ', 1)[0] + '...'
            
            value = ValueAttributes(
                why_franchise=f.get('why_franchise_summary'),
                value_proposition=description if description else None
            )
            
            item = ComparisonItem(
                franchise_id=fid,
                franchise_name=f['franchise_name'],
                image_url=f.get('image_url'),
                verdict=analysis.get("verdict", "A potential match based on your criteria."),
                overview=overview,
                money=MoneyAttributes(**money),
                motives=MotivesAttributes(**motives),
                interest=InterestAttributes(**interest),
                territories=territories,
                value=value
            )
            items.append(item)
            
        return ComparisonResponse(items=items)

    except Exception as e:
        logger.error(f"Error in compare_franchises: {e}")
        raise HTTPException(status_code=500, detail=str(e))

