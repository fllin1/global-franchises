'use server';

import { AnalysisResponse, FranchiseMatch, TierStatus, LeadProfile, TerritoryFranchise, Lead } from '@/types';

// Types matching the ACTUAL Backend Response
interface BackendLeadProfile {
  candidate_name: string | null;
  liquidity: number | null;
  investment_cap: number | null;
  location: string | null;
  state_code: string | null;
  semantic_query: string;
}

interface BackendMatch {
  id: number;
  franchise_name: string;
  primary_category: string | null;
  description_text: string | null;
  similarity: number;
  total_investment_min_usd: number | null;
  why_narrative?: string;
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
      candidate_name: rawData.profile.candidate_name,
      liquidity: rawData.profile.liquidity,
      location: rawData.profile.location,
      state_code: rawData.profile.state_code,
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
      // Use backend narrative if available, otherwise fallback
      why_narrative: m.why_narrative || `Matched based on semantic relevance to "${rawData.profile.semantic_query}" and investment criteria.`
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

export async function searchFranchisesByLocation(stateCode: string): Promise<TerritoryFranchise[]> {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/franchises/by-location?state_code=${stateCode}`, {
      method: 'GET',
      cache: 'no-store',
    });

    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`API Error ${response.status}: ${errorText}`);
    }

    const data = await response.json();
    return data as TerritoryFranchise[];
  } catch (error) {
    console.error('Error fetching franchises by location:', error);
    throw error;
  }
}

// --- NEW ACTIONS for Leads CRUD ---

export async function getLeads(): Promise<Lead[]> {
  try {
    const response = await fetch('http://127.0.0.1:8000/api/leads/', { cache: 'no-store' });
    if (!response.ok) throw new Error('Failed to fetch leads');
    return await response.json();
  } catch (error) {
    console.error('Error fetching leads:', error);
    throw error;
  }
}

export async function createLead(formData: FormData): Promise<Lead> {
  const notes = formData.get('notes');
  if (!notes || typeof notes !== 'string') throw new Error('Invalid notes');

  try {
    const response = await fetch('http://127.0.0.1:8000/api/leads/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ notes }),
    });
    
    if (!response.ok) {
        const error = await response.text();
        throw new Error(`Failed to create lead: ${error}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error creating lead:', error);
    throw error;
  }
}

export async function getLead(id: number): Promise<Lead> {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/leads/${id}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('Failed to fetch lead');
        return await response.json();
    } catch (error) {
        console.error(`Error fetching lead ${id}:`, error);
        throw error;
    }
}

export async function deleteLead(id: number): Promise<void> {
  try {
    const response = await fetch(`http://127.0.0.1:8000/api/leads/${id}`, {
      method: 'DELETE',
    });
    if (!response.ok) throw new Error('Failed to delete lead');
  } catch (error) {
    console.error(`Error deleting lead ${id}:`, error);
    throw error;
  }
}

export async function getFranchiseDetail(id: number): Promise<any> {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/franchises/${id}`, { cache: 'no-store' });
        if (!response.ok) throw new Error('Failed to fetch franchise');
        return await response.json();
    } catch (error) {
        console.error(`Error fetching franchise ${id}:`, error);
        throw error;
    }
}

export async function getLeadMatches(id: number): Promise<FranchiseMatch[]> {
    try {
        const response = await fetch(`http://127.0.0.1:8000/api/leads/${id}/matches`, { cache: 'no-store' });
        if (!response.ok) throw new Error('Failed to fetch matches');
        const data = await response.json();
        
        // Map to FranchiseMatch interface
        return data.map((m: any) => ({
            id: String(m.id),
            name: m.franchise_name,
            description: m.description_text || 'No description available',
            investment_min: m.total_investment_min_usd || 0,
            match_score: Math.round(m.similarity * 100),
            why_narrative: m.why_narrative
        }));
    } catch (error) {
        console.error(`Error fetching matches for lead ${id}:`, error);
        throw error;
    }
}
