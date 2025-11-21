// types/api.ts

export type TierStatus = "tier_1" | "tier_2";

export interface LeadProfile {
  candidate_name?: string | null;
  liquidity: number | null; // The hard constraint
  location: string | null;  // The location filter
  state_code?: string | null; // The inferred state code
  semantic_query: string;   // The intent for vector search
  extracted_tags?: string[]; // e.g. ["Absentee", "Fitness", "High Budget"]
}

export interface Lead {
  id: number;
  candidate_name?: string | null;
  notes: string;
  profile_data: LeadProfile;
  matches?: FranchiseMatch[];
  qualification_status: TierStatus;
  workflow_status: string;
  created_at: string;
  updated_at: string;
}

export interface FranchiseMatch {
  id: string;
  name: string;
  description: string;
  investment_min: number;
  match_score: number; // 0 to 100
  why_narrative: string; // AI Generated explanation for the broker
  unavailable_states?: string[]; // JSON list of states where this franchise is NOT available
  primary_category?: string;
}

export interface AnalysisResponse {
  status: TierStatus;
  profile: LeadProfile;
  // Present ONLY if status is "tier_2"
  coaching_questions?: string[];
  missing_fields?: string[];
  // Present ONLY if status is "tier_1"
  matches?: FranchiseMatch[];
}

export interface TerritoryFranchise {
  id: number;
  franchise_name: string;
  primary_category: string;
  total_investment_min_usd: number;
  availability_status: 'Available' | 'Limited' | 'Not Available';
  description_text?: string;
}
