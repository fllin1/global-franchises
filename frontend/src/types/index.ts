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

// --- Franchise Detail Types ---

export interface TerritoryCheck {
  id: number;
  location_raw: string;
  state_code: string;
  city: string | null;
  zip_code: string | null;
  latitude: number | null;
  longitude: number | null;
  availability_status: string;
  radius_miles: number | null;
}

export interface TerritoryData {
  franchise_id: number;
  territory_count: number;
  states: Record<string, Record<string, TerritoryCheck[]>>;
}

export interface MarketGrowthStatistics {
  demographics?: string;
  market_size?: string;
  cagr?: string;
  growth_period?: string;
  recession_resistance?: string;
}

export interface IdealCandidateProfile {
  skills?: string[];
  personality_traits?: string[];
  role_of_owner?: string;
}

export interface SupportTrainingDetails {
  program_description?: string;
  cost_included?: boolean;
  cost_details?: string;
  lodging_airfare_included?: boolean;
  site_selection_assistance?: boolean;
  lease_negotiation_assistance?: boolean;
  mentor_available?: boolean;
  mentoring_length?: string;
}

export interface IndustryAward {
  source: string;
  year: number;
  award_name?: string;
}

export interface FranchiseDocuments {
  regular?: string[];
  client_focused?: string[];
  recent_emails?: string[];
  magazine_articles?: string[];
}

export interface CommissionStructure {
  single_unit?: {
    amount?: number;
    description: string;
  };
  multi_unit?: {
    percentage?: number;
    max_per_unit?: number;
    description: string;
  };
  resales?: {
    percentage?: number;
    max?: number;
    description: string;
  };
  area_master_developer?: {
    amount?: number | null;
    description: string;
  };
}

export interface FranchisePackage {
  name: string;
  franchise_fee: number;
  total_investment_min?: number;
  total_investment_max?: number;
  territories_count?: number;
  description?: string;
}

export interface FranchiseDetail {
  id: number;
  franchise_name: string;
  slug?: string;
  primary_category?: string;
  sub_categories?: string[];
  business_model_type?: string;
  keywords?: string;
  
  // Financial
  franchise_fee_usd?: number;
  required_cash_investment_usd?: number;
  required_net_worth_usd?: number;
  total_investment_min_usd?: number;
  total_investment_max_usd?: number;
  royalty_details_text?: string;
  sba_approved?: boolean;
  sba_registered?: boolean;
  providing_earnings_guidance_item19?: boolean;
  additional_fees?: string;
  financial_assistance_details?: string;
  commission_structure?: CommissionStructure;
  franchise_packages?: FranchisePackage[];
  
  // Operational
  is_home_based?: boolean;
  allows_semi_absentee?: boolean;
  allows_absentee?: boolean;
  e2_visa_friendly?: boolean;
  master_franchise_opportunity?: boolean;
  vetfran_member?: boolean;
  vetfran_discount_details?: string;
  
  // Narrative
  description_text?: string;
  why_franchise_summary?: string;
  ideal_candidate_profile_text?: string;
  ideal_candidate_profile?: IdealCandidateProfile;
  market_growth_statistics?: MarketGrowthStatistics;
  
  // Territory
  unavailable_states?: string[];
  recent_territory_checks?: any[];
  hot_regions?: string[];
  canadian_referrals?: boolean;
  international_referrals?: boolean;
  corporate_address?: string;
  
  // Contact
  website_url?: string;
  schedule_call_url?: string;
  
  // Historical
  founded_year?: number;
  franchised_year?: number;
  last_updated_from_source?: string;
  last_scraped_at?: string;
  
  // Metadata
  is_active?: boolean;
  franchises_data?: any;
  industry_awards?: IndustryAward[];
  documents?: FranchiseDocuments;
  resales_available?: boolean;
  resales_list?: any[];
  rating?: number;
  support_training_details?: SupportTrainingDetails;
}
