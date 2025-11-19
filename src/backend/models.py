from typing import Optional
from pydantic import BaseModel, Field, computed_field

class LeadProfile(BaseModel):
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
