'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { getLead, getLeadMatches, updateLeadProfile } from '@/app/actions';
import { Lead, FranchiseMatch, LeadProfile } from '@/types';
import { MatchCard } from '@/components/MatchCard';
import { CoachingCard } from '@/components/CoachingCard';
import { LeadProfileForm } from '@/components/LeadProfileForm';
import { MatchDetailModal } from '@/components/MatchDetailModal';
import { Wallet, MapPin, BrainCircuit, CheckSquare, ArrowRightLeft } from 'lucide-react';
import { useComparison } from '@/contexts/ComparisonContext';

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const leadId = parseInt(id);
  const router = useRouter();
  
  const [lead, setLead] = useState<Lead | null>(null);
  const [matches, setMatches] = useState<FranchiseMatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFranchiseId, setSelectedFranchiseId] = useState<number | null>(null);
  
  // Comparison Selection
  const { selectedIds, toggleComparison, setLeadContext, loadLeadSelections } = useComparison();

  useEffect(() => {
    // Initialize Lead Context
    if (leadId) {
        setLeadContext(leadId);
        loadLeadSelections(leadId);
    }
    
    // Cleanup on unmount or id change
    return () => {
        // Optional: revert to global context if leaving? 
        // For now, keep it simple.
    };
  }, [leadId]);

  useEffect(() => {
    loadData();
  }, [leadId]);

  async function loadData() {
    try {
      setIsLoading(true);
      const [leadData, matchesData] = await Promise.all([
        getLead(leadId),
        getLeadMatches(leadId)
      ]);
      setLead(leadData);
      setMatches(matchesData);
    } catch (error) {
      console.error(error);
    } finally {
      setIsLoading(false);
    }
  }

  const handleSaveProfile = async (updatedProfile: LeadProfile) => {
    try {
        const updatedLead = await updateLeadProfile(leadId, updatedProfile);
        setLead(updatedLead);
        // Optionally refresh matches here if we want to re-run matching based on new profile
    } catch (error) {
        console.error("Failed to update profile", error);
        alert("Failed to save profile changes.");
    }
  };

  const handleSelectAll = () => {
      // Logic to select all high matches for comparison?
      // For now, simpler to just let user toggle individual ones
  };

  if (isLoading) return <div className="p-8">Loading...</div>;
  if (!lead) return <div className="p-8">Lead not found</div>;

  // Compute missing fields for CoachingCard
  const missingFields: string[] = [];
  if (lead.qualification_status === 'tier_2') {
    if (!lead.profile_data.liquidity && !lead.profile_data.investment_cap) {
      missingFields.push('Liquidity / Budget');
    }
    if (!lead.profile_data.location && !lead.profile_data.state_code) {
      missingFields.push('Location');
    }
  }

  return (
    <div className="min-h-screen bg-slate-50 pb-24">
      {/* Header */}
      <div className="bg-white border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-slate-900">{lead.candidate_name || 'Unnamed Lead'}</h1>
              <div className="flex items-center gap-4 mt-2 text-slate-500">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {lead.profile_data.state_code || 'No State'}, {lead.profile_data.location || 'No City'}
                </span>
                <span className="flex items-center gap-1">
                  <Wallet className="w-4 h-4" />
                  ${lead.profile_data.liquidity?.toLocaleString() || '0'} Liquid
                </span>
                <span className="bg-emerald-50 text-emerald-700 px-2 py-0.5 rounded text-sm font-medium">
                  {matches.length} Matches Found
                </span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-8 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Main Content */}
        <div className="lg:col-span-3 space-y-6">
          
          {/* Lead Profile Form */}
          <LeadProfileForm 
            initialProfile={lead.profile_data} 
            onSave={handleSaveProfile} 
          />

          <div className="flex items-center justify-between">
            <h2 className="text-xl font-semibold text-slate-900 flex items-center gap-2">
              <BrainCircuit className="w-5 h-5 text-indigo-600" />
              AI Recommendations
            </h2>
            <div className="flex gap-2">
               {/* Optional bulk actions */}
            </div>
          </div>
          
          <div className="space-y-2">
            {matches.map((match) => (
              <div key={match.id} className="flex gap-3">
                 <div className="pt-3">
                    <input 
                        type="checkbox"
                        checked={selectedIds.includes(match.id)}
                        onChange={() => toggleComparison(match.id)}
                        className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 cursor-pointer"
                    />
                 </div>
                 <div className="flex-1">
                    <MatchCard 
                        match={match} 
                        onClick={() => setSelectedFranchiseId(parseInt(match.id))}
                    />
                 </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedFranchiseId && (
        <MatchDetailModal 
          franchiseId={selectedFranchiseId} 
          isOpen={!!selectedFranchiseId}
          onClose={() => setSelectedFranchiseId(null)}
        />
      )}
    </div>
  );
}
