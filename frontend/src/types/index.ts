// types/api.ts

export type TierStatus = "tier_1" | "tier_2";

export interface LeadProfile {
  liquidity: number | null; // The hard constraint
  location: string | null;  // The location filter
  semantic_query: string;   // The intent for vector search
  extracted_tags?: string[]; // e.g. ["Absentee", "Fitness", "High Budget"]
}

export interface FranchiseMatch {
  id: string;
  name: string;
  description: string;
  investment_min: number;
  match_score: number; // 0 to 100
  why_narrative: string; // AI Generated explanation for the broker
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

