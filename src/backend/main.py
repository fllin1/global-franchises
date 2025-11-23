from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from loguru import logger

from src.backend.models import LeadProfile
from src.backend.extractor import extract_profile_from_notes
from src.backend.search import hybrid_search, search_franchises_by_state
from src.backend.narrator import generate_match_narratives

from src.backend.leads import router as leads_router
from src.backend.franchises import router as franchises_router
from src.backend.comparison import router as comparison_router

app = FastAPI(title="Franchise Matcher API")

# Include Routers
app.include_router(leads_router)
app.include_router(franchises_router)
app.include_router(comparison_router)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeLeadRequest(BaseModel):
    notes: str

@app.get("/")
async def health_check():
    return {"status": "ok", "service": "franchise-matcher-backend"}

@app.post("/analyze-lead")
async def analyze_lead(request: AnalyzeLeadRequest):
    """
    Analyzes lead notes, extracts profile, and finds matching franchises.
    """
    try:
        logger.info(f"Analyzing lead with notes length: {len(request.notes)}")
        
        # 1. Extract Profile
        profile = await extract_profile_from_notes(request.notes)
        
        # 2. Search for Matches
        matches = await hybrid_search(profile, match_count=6)
        
        # 3. Generate Narratives
        narratives = await generate_match_narratives(profile, matches)
        
        # 4. Construct Response
        # Add narratives to matches
        enriched_matches = []
        for m in matches:
            m_id = m.get('id')
            m['why_narrative'] = narratives.get(m_id, "Matched based on profile criteria.")
            enriched_matches.append(m)
            
        # Determine status
        # Note: frontend expects "complete" or "incomplete" (mapped to tier_1/tier_2)
        # logic in actions.ts: rawData.status === 'complete' ? 'tier_1' : 'tier_2'
        status = "incomplete" if profile.is_tier_2 else "complete"
        
        # Placeholder for coaching questions (could be another LLM call)
        coaching_questions = [
            "What is your timeline for starting a business?",
            "Have you ever owned a business before?",
            "How will you finance this investment?"
        ]

        return {
            "status": status,
            "profile": profile.model_dump(),
            "matches": enriched_matches,
            "coaching_questions": coaching_questions
        }

    except Exception as e:
        logger.error(f"Error in analyze_lead: {e}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("src.backend.main:app", host="0.0.0.0", port=8000, reload=True)
