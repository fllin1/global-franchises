// types/api.ts

export type TierStatus = "tier_1" | "tier_2";

export interface LeadProfile {
  candidate_name?: string | null;
  liquidity: number | null; // The hard constraint
  investment_cap?: number | null;
  location: string | null;  // The location filter
  state_code?: string | null; // The inferred state code
  semantic_query: string;   // The intent for vector search
  extracted_tags?: string[]; // e.g. ["Absentee", "Fitness", "High Budget"]

  // --- Extended Money Fields ---
  net_worth?: number | null;
  investment_source?: string | null;
  interest?: string | null; // Additional financial interest details

  // --- Extended Territories Fields ---
  territories?: Array<{ location: string; state_code?: string }> | null;

  // --- Extended Interest Fields ---
  home_based_preference?: boolean | null;
  absentee_preference?: boolean | null;
  semi_absentee_preference?: boolean | null;
  role_preference?: string | null;
  business_model_preference?: string | null;
  staff_preference?: string | null;
  franchise_categories?: string[] | null;
  multi_unit_preference?: boolean | null;

  // --- Extended Motives Fields ---
  trigger_event?: string | null;
  current_status?: string | null;
  experience_level?: string | null;
  goals?: string[] | null;
  timeline?: string | null;
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

// --- Comparison Feature Types ---

export interface OverviewAttributes {
  industry: string;
  year_started?: number;
  year_franchised?: number;
  operating_franchises?: string;
}

export interface MoneyAttributes {
  investment_range: string;
  liquidity_req?: number;
  net_worth_req?: number;
  financial_model: string;
  overhead_level: string;
  royalty?: string;
  sba_registered: boolean;
  in_house_financing?: string;
  traffic_light: 'green' | 'yellow' | 'red';
}

export interface MotivesAttributes {
  recession_resistance: string;
  scalability: string;
  market_demand: string;
  passive_income_potential: string;
}

export interface InterestAttributes {
  role: string;
  sales_requirement: string;
  inventory_level: string;
  employees_count: string;
  traffic_light: 'green' | 'yellow' | 'red';
}

export interface TerritoryAttributes {
  availability_status: string;
  territory_notes?: string;
  unavailable_states?: string[];
}

export interface ValueAttributes {
  why_franchise?: string;
  value_proposition?: string;
}

export interface ComparisonItem {
  franchise_id: number;
  franchise_name: string;
  image_url?: string;
  verdict: string;
  overview: OverviewAttributes;
  money: MoneyAttributes;
  motives: MotivesAttributes;
  interest: InterestAttributes;
  territories: TerritoryAttributes;
  value: ValueAttributes;
}

export interface ComparisonResponse {
  items: ComparisonItem[];
}
