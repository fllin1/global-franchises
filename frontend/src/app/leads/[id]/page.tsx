'use client';

import { useState, useEffect, use } from 'react';
import { getLead, getLeadMatches } from '@/app/actions';
import { Lead, FranchiseMatch } from '@/types';
import { MatchCard } from '@/components/MatchCard';
import { CoachingCard } from '@/components/CoachingCard';
import { MatchDetailModal } from '@/components/MatchDetailModal';
import { Wallet, MapPin, BrainCircuit } from 'lucide-react';

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const leadId = parseInt(id);
  
  const [lead, setLead] = useState<Lead | null>(null);
  const [matches, setMatches] = useState<FranchiseMatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFranchiseId, setSelectedFranchiseId] = useState<number | null>(null);

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

  if (isLoading) return <div className="flex items-center justify-center h-screen text-slate-500">Loading lead details...</div>;
  if (!lead) return <div className="p-10 text-center">Lead not found</div>;

  const isTier2 = lead.qualification_status === 'tier_2';
  const profile = lead.profile_data;
  
  // Calculate Completeness
  const hasFinancials = profile.liquidity !== null;
  const hasLocation = profile.location !== null;
  const completeness = (hasFinancials ? 50 : 0) + (hasLocation ? 50 : 0);

  return (
    <div className="flex flex-col h-[calc(100vh-0px)] md:flex-row overflow-hidden">
        {/* Left Panel: Profile Inspector (40%) */}
        <div className="w-full md:w-[40%] bg-white border-r border-slate-200 overflow-y-auto p-6">
            <div className="mb-6 border-b border-slate-100 pb-6">
                <h1 className="text-2xl font-bold text-slate-900 mb-1">{lead.candidate_name || `Lead #${lead.id}`}</h1>
                <p className="text-sm text-slate-500">Created on {new Date(lead.created_at).toLocaleDateString()}</p>
                
                {/* Completeness Bar */}
                <div className="mt-4">
                    <div className="flex justify-between text-xs mb-1">
                        <span className="font-medium text-slate-700">Profile Completeness</span>
                        <span className={completeness === 100 ? "text-emerald-600" : "text-amber-600"}>{completeness}%</span>
                    </div>
                    <div className="w-full bg-slate-100 rounded-full h-2">
                        <div 
                            className={`h-2 rounded-full transition-all ${completeness === 100 ? 'bg-emerald-500' : 'bg-amber-500'}`} 
                            style={{ width: `${completeness}%` }}
                        />
                    </div>
                </div>
            </div>

            {/* Extracted Data / Editor */}
            <div className="space-y-6">
                <section>
                    <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <Wallet className="w-4 h-4 text-slate-400" />
                        Financial Qualification
                    </h3>
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-100 space-y-3">
                        <div>
                            <label className="text-xs text-slate-500 block mb-1">Liquid Capital</label>
                            <div className="font-medium text-slate-900">
                                {profile.liquidity ? `$${profile.liquidity.toLocaleString()}` : <span className="text-red-500 italic">Missing</span>}
                            </div>
                        </div>
                        <div>
                            <label className="text-xs text-slate-500 block mb-1">Investment Cap</label>
                            <div className="font-medium text-slate-900">
                                {profile.investment_cap ? `$${profile.investment_cap.toLocaleString()}` : <span className="text-slate-400 italic">Not specified</span>}
                            </div>
                        </div>
                    </div>
                </section>

                <section>
                    <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <MapPin className="w-4 h-4 text-slate-400" />
                        Location Preferences
                    </h3>
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                         <div className="font-medium text-slate-900">
                            {profile.location || <span className="text-red-500 italic">Missing Location</span>}
                         </div>
                         {profile.state_code && (
                            <div className="mt-1 inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-indigo-50 text-indigo-700">
                                {profile.state_code}
                            </div>
                         )}
                    </div>
                </section>

                <section>
                    <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                        <BrainCircuit className="w-4 h-4 text-slate-400" />
                        AI Analysis
                    </h3>
                    <div className="bg-slate-50 p-4 rounded-lg border border-slate-100">
                        <p className="text-sm text-slate-700 italic leading-relaxed">
                            "{profile.semantic_query}"
                        </p>
                    </div>
                </section>
                
                <section>
                     <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider mb-3">Original Notes</h3>
                     <div className="text-xs text-slate-500 bg-slate-50 p-3 rounded border border-slate-100 whitespace-pre-wrap">
                         {lead.notes}
                     </div>
                </section>
            </div>
        </div>

        {/* Right Panel: Match Board (60%) */}
        <div className="w-full md:w-[60%] bg-slate-50 overflow-y-auto p-6">
            {isTier2 && (
                <div className="mb-6">
                     <CoachingCard 
                        missingFields={!profile.liquidity ? ['Liquidity'] : []}
                        questions={[
                            "What is your timeline for starting a business?",
                            "How will you finance this investment?", 
                            "Have you explored SBA loans?"
                        ]}
                     />
                </div>
            )}

            <h2 className="text-xl font-bold text-slate-900 mb-4 flex items-center justify-between">
                <span>Franchise Matches</span>
                <span className="text-sm font-normal text-slate-500">{matches.length} results</span>
            </h2>
            
            <div className="space-y-4 pb-10">
                {matches.map(match => (
                    <MatchCard 
                        key={match.id} 
                        match={match} 
                        targetState={profile.state_code}
                        onClick={() => setSelectedFranchiseId(parseInt(match.id))}
                    />
                ))}
            </div>
        </div>

        <MatchDetailModal 
            franchiseId={selectedFranchiseId} 
            onClose={() => setSelectedFranchiseId(null)} 
        />
    </div>
  );
}
