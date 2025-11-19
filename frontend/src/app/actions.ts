'use server';

import { AnalysisResponse, FranchiseMatch, TierStatus, LeadProfile } from '@/types';

// Types matching the ACTUAL Backend Response
interface BackendLeadProfile {
  liquidity: number | null;
  investment_cap: number | null;
  location: string | null;
  semantic_query: string;
}

interface BackendMatch {
  id: number;
  franchise_name: string;
  primary_category: string | null;
  description_text: string | null;
  similarity: number;
  total_investment_min_usd: number | null;
}

interface BackendResponse {
  status: string; // "complete" | "incomplete"
  profile: BackendLeadProfile;
  matches: BackendMatch[];
  coaching_questions: string[];
}

export async function analyzeLead(formData: FormData): Promise<AnalysisResponse> {
  const notes = formData.get('notes');

  if (!notes || typeof notes !== 'string') {
    throw new Error('Invalid notes provided');
  }

  try {
    const response = await fetch('http://127.0.0.1:8000/analyze-lead', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ notes }),
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    const rawData: BackendResponse = await response.json();
    
    // --- ADAPTER LAYER ---
    // Transform Backend Response to Frontend Contract

    // 1. Map Status
    const status: TierStatus = rawData.status === 'complete' ? 'tier_1' : 'tier_2';

    // 2. Map Profile
    // We inferred extracted tags if investment_cap is present
    const extracted_tags: string[] = [];
    if (rawData.profile.investment_cap) {
      extracted_tags.push(`Max Budget: $${rawData.profile.investment_cap.toLocaleString()}`);
    }

    const profile: LeadProfile = {
      liquidity: rawData.profile.liquidity,
      location: rawData.profile.location,
      semantic_query: rawData.profile.semantic_query,
      extracted_tags
    };

    // 3. Map Matches (if any)
    const matches: FranchiseMatch[] = rawData.matches.map((m) => ({
      id: String(m.id),
      name: m.franchise_name,
      description: m.description_text || 'No description available',
      investment_min: m.total_investment_min_usd || 0,
      match_score: Math.round(m.similarity * 100), // Convert float 0.85 -> 85
      // Fallback narrative since backend doesn't provide it yet
      why_narrative: `Matched based on semantic relevance to "${rawData.profile.semantic_query}" and investment criteria.`
    }));

    return {
      status,
      profile,
      coaching_questions: rawData.coaching_questions,
      // Populate missing fields if incomplete (backend doesn't strictly return this list separately, 
      // but we can infer if liquidity is missing for Tier 2)
      missing_fields: status === 'tier_2' && !rawData.profile.liquidity ? ['Liquidity / Budget'] : [],
      matches
    };

  } catch (error) {
    console.error('Error analyzing lead:', error);
    throw error; 
  }
}

