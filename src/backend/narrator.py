import json
import asyncio
from typing import List, Dict, Any, Optional
from loguru import logger
from google.genai import types

from src.api.config.genai_gemini_config import CLIENT, MODEL_PRO
from src.api.genai_gemini import generate
from src.backend.models import LeadProfile, ComparisonResponse, ComparisonItem

async def generate_match_narratives(profile: LeadProfile, matches: List[Dict[str, Any]]) -> Dict[int, str]:
    """
    Generates a personalized 'why this fits' narrative for a list of franchise matches
    based on the lead's profile.
    """
    if not matches:
        return {}

    candidates_summary = []
    for m in matches:
        candidates_summary.append({
            "id": m['id'],
            "name": m['franchise_name'],
            "category": m.get('primary_category'),
            "description": m.get('description_text', '')[:200] + "..."
        })

    # Construct detailed profile context
    profile_context = f"""
    - Search Intent: {profile.semantic_query}
    - Location: {profile.location or 'Flexible'}
    - Budget/Liquidity: {profile.effective_budget or 'Unknown'}
    """
    
    if profile.role_preference:
        profile_context += f"\n    - Role Preference: {profile.role_preference}"
    if profile.franchise_categories:
        profile_context += f"\n    - Interest Categories: {', '.join(profile.franchise_categories)}"
    if profile.motives:
        # Assuming motives is accessible if it was a dict, but it's fields on profile now
        pass # Add specific fields below
        
    if profile.trigger_event:
        profile_context += f"\n    - Trigger/Motivation: {profile.trigger_event}"
    if profile.goals:
        profile_context += f"\n    - Goals: {', '.join(profile.goals) if profile.goals else 'None'}"

    prompt = f"""
    You are an expert Franchise Consultant. 
    
    Candidate Profile:
    {profile_context}
    
    Here are {len(candidates_summary)} franchise recommendations.
    For EACH franchise, write a short, persuasive 1-2 sentence "Match Narrative" explaining SPECIFICALLY why this brand fits this candidate's profile.
    
    Franchise Candidates:
    {json.dumps(candidates_summary, indent=2)}
    
    Output must be a JSON object with a "narratives" array, containing objects with "franchise_id" and "narrative".
    """

    schema = {
        "type": "OBJECT",
        "properties": {
            "narratives": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "franchise_id": {"type": "INTEGER"},
                        "narrative": {"type": "STRING"}
                    },
                    "required": ["franchise_id", "narrative"]
                }
            }
        },
        "required": ["narratives"]
    }

    generate_content_config = types.GenerateContentConfig(
        temperature=0.7,
        top_p=0.95,
        max_output_tokens=8192,
        response_mime_type="application/json",
        response_schema=schema,
    )

    retries = 3
    for attempt in range(retries):
        try:
            logger.info(f"Generating narratives (Attempt {attempt+1}/{retries})...")
            response = generate(
                client=CLIENT,
                model=MODEL_PRO,
                parts=[types.Part(text=prompt)],
                generate_content_config=generate_content_config
            )
            
            if not response.text:
                raise ValueError("Empty response from Gemini")

            data = json.loads(response.text)
            narratives_list = data.get("narratives", [])
            narratives = {item["franchise_id"]: item["narrative"] for item in narratives_list}
            return narratives

        except Exception as e:
            logger.error(f"Error generating narratives: {e}")
            is_transient = "503" in str(e) or "overloaded" in str(e).lower()
            if is_transient and attempt < retries - 1:
                await asyncio.sleep(2 ** attempt)
            else:
                if not is_transient: break
    
    return {}


async def generate_comparison_analysis(
    profile: Optional[LeadProfile], 
    franchises: List[Dict[str, Any]]
) -> Dict[int, Dict[str, Any]]:
    """
    Generates deep comparison attributes for a list of franchises using the
    "Money, Motives, Interest, Territories" framework.
    
    Optimized to use DB fields where possible to minimize AI hallucination/cost.
    """
    if not franchises:
        return {}

    # Prepare context for AI - ONLY essential info for subjective fields
    analysis_context = []
    db_attributes = {} # Store deterministic attributes here

    for f in franchises:
        fid = f['id']
        f_data = f.get('franchises_data', {})
        if isinstance(f_data, str):
            try:
                f_data = json.loads(f_data)
            except:
                f_data = {}
                
        background = f_data.get('background', {})
        # financials = f_data.get('financials_unmapped', {})

        # --- Deterministic Extraction (DB Fields) ---
        
        # Role / Interest
        role_type = "Owner-Operator"
        if f.get('allows_absentee'):
            role_type = "Absentee Available"
        elif f.get('allows_semi_absentee'):
            role_type = "Semi-Absentee Available"
        
        is_home_based = f.get('is_home_based', False)
        inventory_level = "Low/None" if is_home_based else "Standard" # Default, AI can override if needed
        overhead = "Low - Home Based" if is_home_based else "Retail/Office"

        # Stability / Motives
        founded = f.get('founded_year')
        franchised = f.get('franchised_year')
        recession_proof = "Check FDD" # Default
        
        # Very rough heuristic for stability
        if founded and (2024 - founded) > 15:
            recession_proof = "Likely - Established Brand"
        
        # Pre-populate DB attributes to merge later
        db_attributes[fid] = {
            "money": {
                "overhead_level": overhead,
                # financial_model is hard to guess from DB alone, let AI handle it or default
            },
            "interest": {
                "role": role_type,
                "inventory_level": inventory_level
            },
            "motives": {
                # recession_resistance handled by AI for better nuance
            }
        }

        # Context for AI (Focus on subjective parts)
        analysis_context.append({
            "id": fid,
            "name": f['franchise_name'],
            "description": f.get('description_text', '')[:400],
            "ideal_candidate": f.get('ideal_candidate_profile_text', '')[:300],
            "why_summary": f.get('why_franchise_summary', '')[:300]
        })

    # Construct Prompt
    profile_text = "Generic Candidate"
    if profile:
        profile_text = f"""
        - Intent: {profile.semantic_query}
        - Budget: {profile.effective_budget or 'Unknown'}
        - Role Preference: {profile.role_preference or 'Flexible'}
        - Home Based: {'Yes' if profile.home_based_preference else 'No'}
        - Multi-Unit: {'Yes' if profile.multi_unit_preference else 'No'}
        - Goals: {', '.join(profile.goals) if profile.goals else 'Unknown'}
        - Experience: {profile.experience_level or 'Unknown'}
        """

    prompt = f"""
    You are a Franchise Analyst.
    
    Candidate: {profile_text}
    
    Analyze these {len(analysis_context)} franchises.
    
    Output a JSON object with an "analysis" array containing:
    
    1. franchise_id: (int)
    2. verdict: (string) 1 sentence pitch tailored to the candidate.
    3. money_financial_model: (string) e.g. "All Cash", "SBA Approved", "In-House Financing".
    4. motives_recession_resistance: (string) e.g. "Yes - Essential Service", "No - Luxury".
    5. motives_scalability: (string) e.g. "Multi-Unit", "Area Dev".
    6. motives_market_demand: (string) e.g. "High - Senior Care", "Stable".
    7. motives_passive_potential: (string) "Low", "Medium", "High".
    8. interest_sales_req: (string) e.g. "B2B", "Inbound", "Direct".
    9. interest_employees: (string) e.g. "1-2", "5-10", "15+".
    
    Franchises:
    {json.dumps(analysis_context, indent=2)}
    """

    schema = {
        "type": "OBJECT",
        "properties": {
            "analysis": {
                "type": "ARRAY",
                "items": {
                    "type": "OBJECT",
                    "properties": {
                        "franchise_id": {"type": "INTEGER"},
                        "verdict": {"type": "STRING"},
                        "money_financial_model": {"type": "STRING"},
                        "motives_recession_resistance": {"type": "STRING"},
                        "motives_scalability": {"type": "STRING"},
                        "motives_market_demand": {"type": "STRING"},
                        "motives_passive_potential": {"type": "STRING"},
                        "interest_sales_req": {"type": "STRING"},
                        "interest_employees": {"type": "STRING"},
                    },
                    "required": ["franchise_id", "verdict", "money_financial_model", "motives_recession_resistance"]
                }
            }
        }
    }

    generate_content_config = types.GenerateContentConfig(
        temperature=0.4,
        top_p=0.95,
        max_output_tokens=4096,
        response_mime_type="application/json",
        response_schema=schema,
    )

    # Call AI
    ai_results = {}
    try:
        logger.info("Generating lightweight comparison analysis...")
        response = generate(
            client=CLIENT,
            model=MODEL_PRO,
            parts=[types.Part(text=prompt)],
            generate_content_config=generate_content_config
        )
        if response.text:
            data = json.loads(response.text)
            for item in data.get("analysis", []):
                ai_results[item["franchise_id"]] = item
    except Exception as e:
        logger.error(f"AI Comparison Generation failed: {e}")
        # Fallback will handle missing keys

    # Merge DB and AI results
    final_results = {}
    for fid, db_data in db_attributes.items():
        ai_data = ai_results.get(fid, {})
        
        final_results[fid] = {
            "verdict": ai_data.get("verdict", "A potential match."),
            "money": {
                "financial_model": ai_data.get("money_financial_model", "Standard"),
                "overhead_level": db_data["money"]["overhead_level"],
                "traffic_light": "yellow" # Calc in comparison endpoint
            },
            "motives": {
                "recession_resistance": ai_data.get("motives_recession_resistance", "Unknown"),
                "scalability": ai_data.get("motives_scalability", "Standard"),
                "market_demand": ai_data.get("motives_market_demand", "Stable"),
                "passive_income_potential": ai_data.get("motives_passive_potential", "Low")
            },
            "interest": {
                "role": db_data["interest"]["role"],
                "sales_requirement": ai_data.get("interest_sales_req", "Standard"),
                "inventory_level": db_data["interest"]["inventory_level"],
                "employees_count": ai_data.get("interest_employees", "Varies"),
                "traffic_light": "yellow" # Calc in comparison endpoint
            }
        }

    return final_results
