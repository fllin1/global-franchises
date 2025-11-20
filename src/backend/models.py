from typing import Optional, List, Dict, Any
from datetime import datetime
from pydantic import BaseModel, Field, computed_field

class Category(BaseModel):
    id: int
    name: str
    slug: str
    created_at: datetime

class Franchise(BaseModel):
    id: int
    franchise_name: str
    primary_category: str
    description_text: Optional[str]
    total_investment_min_usd: Optional[int]
    image_url: Optional[str]
    source_url: Optional[str]
    last_scraped_at: Optional[datetime]
    slug: Optional[str]
    is_active: bool = True
    
    # Relational data
    # In DB these are separate tables, but API might return them nested
    categories: Optional[List[Category]] = []
    
    # JSONB legacy support (optional)
    sub_categories: Optional[List[str]] = []
    unavailable_states: Optional[List[str]] = []

class LeadProfile(BaseModel):
    candidate_name: Optional[str] = Field(
        None,
        description="The name of the candidate extracted from the notes."
    )
    liquidity: Optional[int] = Field(
        None, 
        description="The extracted liquid capital amount in USD. If missing, the lead is considered Tier 2."
    )
    investment_cap: Optional[int] = Field(
        None, 
        description="The maximum total investment the lead is willing to make. Used as a proxy for liquidity if liquidity is missing."
    )
    location: Optional[str] = Field(
        None, 
        description="The preferred location or territory for the franchise."
    )
    state_code: Optional[str] = Field(
        None,
        description="The 2-letter state code derived from the location (e.g., 'TX', 'NY')."
    )
    semantic_query: str = Field(
        ..., 
        description="A synthesized search query describing the lead's intent, preferences, and background for vector search."
    )

    @computed_field
    def is_tier_2(self) -> bool:
        """
        A lead is Tier 2 if they are missing location OR (liquidity AND investment_cap).
        """
        missing_financials = self.liquidity is None and self.investment_cap is None
        missing_location = self.location is None
        return missing_financials or missing_location
    
    @property
    def effective_budget(self) -> Optional[int]:
        """
        Returns the budget to use for filtering. 
        Prefers investment_cap, falls back to liquidity.
        """
        return self.investment_cap if self.investment_cap is not None else self.liquidity

class Lead(BaseModel):
    id: int
    candidate_name: Optional[str]
    notes: str
    profile_data: LeadProfile
    matches: Optional[list] = []
    qualification_status: str
    workflow_status: str
    created_at: datetime
    updated_at: datetime

class LeadCreate(BaseModel):
    notes: str

class LeadUpdate(BaseModel):
    candidate_name: Optional[str] = None
    notes: Optional[str] = None
    profile_data: Optional[LeadProfile] = None
    qualification_status: Optional[str] = None
    workflow_status: Optional[str] = None
