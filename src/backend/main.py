from typing import List, Optional, Dict, Any
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from loguru import logger

from src.backend.extractor import extract_profile_from_notes
from src.backend.search import hybrid_search
from src.backend.models import LeadProfile
from src.backend.narrator import generate_match_narratives

app = FastAPI(title="Franchise Broker Co-Pilot API")

class AnalyzeLeadRequest(BaseModel):
    notes: str

class FranchiseMatch(BaseModel):
    id: int
    franchise_name: str
    primary_category: Optional[str]
    description_text: Optional[str]
    similarity: float
    total_investment_min_usd: Optional[int]
    why_narrative: Optional[str] = None # Added field

class AnalyzeLeadResponse(BaseModel):
    status: str # "complete" or "incomplete"
    profile: LeadProfile
    matches: List[FranchiseMatch] = []
    coaching_questions: List[str] = []

@app.post("/analyze-lead", response_model=AnalyzeLeadResponse)
async def analyze_lead(request: AnalyzeLeadRequest):
    """
    Analyzes broker notes to extract a lead profile and either finds matching franchises 
    (if Tier 1) or provides coaching questions (if Tier 2/incomplete).
    """
    try:
        logger.info("Analyzing lead from notes...")
        # 1. Parse notes to get profile
        profile = await extract_profile_from_notes(request.notes)
        
        matches = []
        coaching_questions = []
        status = "complete"

        # 2. Logic Branch
        if profile.is_tier_2:
            logger.info("Lead identified as Tier 2 (Incomplete Profile)")
            status = "incomplete"
            # Generate coaching questions based on missing data
            if profile.liquidity is None and profile.investment_cap is None:
                coaching_questions.append("Could you please provide your available liquid capital (cash) or maximum investment budget?")
            
            coaching_questions.append("Are you open to exploring other franchise opportunities outside of your initial inquiry?")
            
        else:
            logger.info(f"Lead identified as Tier 1. Budget: {profile.effective_budget}")
            # 3. Run Hybrid Search
            raw_matches = await hybrid_search(profile, match_count=10)
            
            # 4. Generate Narratives (Batch)
            narratives = await generate_match_narratives(profile, raw_matches)

            # Convert to Pydantic models
            for m in raw_matches:
                # Get narrative for this ID, or None if generation failed/skipped
                narrative = narratives.get(m['id'])
                
                matches.append(FranchiseMatch(
                    id=m['id'],
                    franchise_name=m['franchise_name'],
                    primary_category=m.get('primary_category'),
                    description_text=m.get('description_text'),
                    similarity=m['similarity'],
                    total_investment_min_usd=m.get('total_investment_min_usd'),
                    why_narrative=narrative
                ))

        return AnalyzeLeadResponse(
            status=status,
            profile=profile,
            matches=matches,
            coaching_questions=coaching_questions
        )

    except Exception as e:
        logger.error(f"Error processing lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
