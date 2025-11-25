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

    # --- Extended Money Fields ---
    net_worth: Optional[int] = Field(None, description="Total net worth in USD")
    investment_source: Optional[str] = Field(None, description="Source of investment (e.g., 'Personal', 'SBA', '401K')")
    interest: Optional[str] = Field(None, description="Additional financial interest details")

    # --- Extended Territories Fields ---
    territories: Optional[List[Dict[str, str]]] = Field(
        None, 
        description="Array of territory objects: [{'location': 'Orange County, CA', 'state_code': 'CA'}]"
    )

    # --- Extended Interest Fields ---
    home_based_preference: Optional[bool] = Field(None, description="Prefers home-based operations")
    absentee_preference: Optional[bool] = Field(None, description="Prefers absentee ownership")
    semi_absentee_preference: Optional[bool] = Field(None, description="Prefers semi-absentee ownership")
    role_preference: Optional[str] = Field(None, description="e.g., 'Owner-Operator', 'Semi-Absentee'")
    business_model_preference: Optional[str] = Field(None, description="e.g., 'B2B', 'B2C'")
    staff_preference: Optional[str] = Field(None, description="e.g., 'No staff', 'Small staff'")
    franchise_categories: Optional[List[str]] = Field(None, description="Interested franchise categories")
    multi_unit_preference: Optional[bool] = Field(None, description="Interested in multi-unit opportunities")

    # --- Extended Motives Fields ---
    trigger_event: Optional[str] = Field(None, description="What triggered the search")
    current_status: Optional[str] = Field(None, description="Current employment/status")
    experience_level: Optional[str] = Field(None, description="e.g. 'First-time', 'Serial entrepreneur'")
    goals: Optional[List[str]] = Field(None, description="Goals e.g. 'Wealth building'")
    timeline: Optional[str] = Field(None, description="Timeline to start")

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
    comparison_selections: Optional[List[int]] = None
    comparison_analysis: Optional[Dict[str, Any]] = None
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

# --- Comparison Models ---

class OverviewAttributes(BaseModel):
    """Overview section with basic franchise info"""
    industry: str = Field(..., description="Primary business category")
    year_started: Optional[int] = Field(None, description="Year the business was founded")
    year_franchised: Optional[int] = Field(None, description="Year franchising began")
    operating_franchises: Optional[str] = Field(None, description="Number of operating franchises")

class MoneyAttributes(BaseModel):
    investment_range: str
    liquidity_req: Optional[int] = None
    net_worth_req: Optional[int] = None
    financial_model: str = Field(..., description="e.g. 'All Cash', 'In-House Financing', 'SBA Approved'")
    overhead_level: str = Field(..., description="e.g. 'Low - Home Based', 'High - Retail Buildout'")
    royalty: Optional[str] = Field(None, description="Royalty structure (e.g., '8%', '3% Sliding Scale')")
    sba_registered: bool = Field(False, description="Whether franchise is SBA registered")
    in_house_financing: Optional[str] = Field(None, description="In-house financing details")
    traffic_light: str = Field("green", description="green, yellow, red based on fit")

class MotivesAttributes(BaseModel):
    recession_resistance: str = Field(..., description="Yes/No/Partial with explanation")
    scalability: str = Field(..., description="e.g. 'Multi-Unit', 'Add Crews', 'Area Developer'")
    market_demand: str = Field(..., description="Description of market need/size")
    passive_income_potential: str = Field(..., description="Low/Medium/High")

class InterestAttributes(BaseModel):
    role: str = Field(..., description="e.g. 'Owner-Operator', 'Semi-Absentee', 'Executive'")
    sales_requirement: str = Field(..., description="e.g. 'Inbound Leads', 'Direct Sales', 'B2B'")
    inventory_level: str = Field(..., description="e.g. 'None - Service', 'Low', 'High - Retail'")
    employees_count: str = Field(..., description="e.g. '1-2', '5-10', '15+'")
    traffic_light: str = Field("green", description="green, yellow, red based on role fit")

class TerritoryAttributes(BaseModel):
    availability_status: str = Field(..., description="e.g. 'Available', 'Sold Out', 'Check Required'")
    territory_notes: Optional[str] = None
    unavailable_states: Optional[List[str]] = Field(None, description="List of states where franchise is unavailable")

class ValueAttributes(BaseModel):
    """Value proposition section"""
    why_franchise: Optional[str] = Field(None, description="Why choose this franchise - summary bullets")
    value_proposition: Optional[str] = Field(None, description="Franchise description/value proposition")

class ComparisonItem(BaseModel):
    franchise_id: int
    franchise_name: str
    image_url: Optional[str] = None
    verdict: str = Field(..., description="1-2 sentence AI-generated summary for this lead")
    overview: OverviewAttributes
    money: MoneyAttributes
    motives: MotivesAttributes
    interest: InterestAttributes
    territories: TerritoryAttributes
    value: ValueAttributes

class ComparisonResponse(BaseModel):
    items: List[ComparisonItem]
