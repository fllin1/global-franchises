'use client';

import { useState, useEffect, use } from 'react';
import { useRouter } from 'next/navigation';
import { getLead, getLeadMatches, updateLeadProfile, getLeadComparisonAnalysis, updateLeadWorkflowStatus, refreshLeadMatches, saveLeadRecommendations } from '@/app/actions';
import { Lead, FranchiseMatch, LeadProfile } from '@/types';
import { MatchCard } from '@/components/MatchCard';
import { CoachingCard } from '@/components/CoachingCard';
import { LeadProfileForm } from '@/components/LeadProfileForm';
import { MatchDetailModal } from '@/components/MatchDetailModal';
import { AddFranchiseModal } from '@/components/AddFranchiseModal';
import { Wallet, MapPin, BrainCircuit, FileBarChart, Loader2, RefreshCw, ChevronDown, ArrowLeft, X, Plus } from 'lucide-react';
import { useComparison } from '@/contexts/ComparisonContext';
import Link from 'next/link';

// Workflow status configuration
const WORKFLOW_STATUSES = {
  new: { label: 'New', color: 'bg-slate-100 text-slate-700 border-slate-200 dark:bg-slate-800 dark:text-slate-300 dark:border-slate-700' },
  contacted: { label: 'Contacted', color: 'bg-blue-50 text-blue-700 border-blue-100 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800' },
  qualified: { label: 'Qualified', color: 'bg-purple-50 text-purple-700 border-purple-100 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800' },
  presented: { label: 'Presented', color: 'bg-indigo-50 text-indigo-700 border-indigo-100 dark:bg-indigo-900/30 dark:text-indigo-300 dark:border-indigo-800' },
  closed_won: { label: 'Closed Won', color: 'bg-emerald-50 text-emerald-700 border-emerald-100 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800' },
  closed_lost: { label: 'Closed Lost', color: 'bg-red-50 text-red-700 border-red-100 dark:bg-red-900/30 dark:text-red-300 dark:border-red-800' },
} as const;

type WorkflowStatus = keyof typeof WORKFLOW_STATUSES;

export default function LeadDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const leadId = parseInt(id);
  const router = useRouter();
  
  const [lead, setLead] = useState<Lead | null>(null);
  const [matches, setMatches] = useState<FranchiseMatch[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [selectedFranchiseId, setSelectedFranchiseId] = useState<number | null>(null);
  
  // Workflow status state
  const [isUpdatingStatus, setIsUpdatingStatus] = useState(false);
  const [showStatusDropdown, setShowStatusDropdown] = useState(false);
  
  // Re-run matching state
  const [isRefreshingMatches, setIsRefreshingMatches] = useState(false);
  
  // Remove match state
  const [removingMatchId, setRemovingMatchId] = useState<string | null>(null);
  
  // Add Franchise Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  
  // Saved Comparison State
  const [hasSavedComparison, setHasSavedComparison] = useState(false);
  const [isCheckingComparison, setIsCheckingComparison] = useState(false);
  
  // Comparison Selection
  const { selectedIds, toggleComparison, setLeadContext, loadLeadSelections } = useComparison();

  useEffect(() => {
    // Check for saved comparison on mount
    const checkSavedComparison = async () => {
        if (!leadId) return;
        setIsCheckingComparison(true);
        try {
            const analysis = await getLeadComparisonAnalysis(leadId);
            if (analysis && analysis.items && analysis.items.length > 0) {
                setHasSavedComparison(true);
            }
        } catch (e) {
            console.error("Failed to check saved comparison", e);
        } finally {
            setIsCheckingComparison(false);
        }
    };
    checkSavedComparison();
  }, [leadId]);

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

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = () => setShowStatusDropdown(false);
    if (showStatusDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showStatusDropdown]);

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

  const handleWorkflowStatusChange = async (newStatus: WorkflowStatus) => {
    if (!lead) return;
    
    setIsUpdatingStatus(true);
    setShowStatusDropdown(false);
    
    try {
      const updatedLead = await updateLeadWorkflowStatus(leadId, newStatus);
      setLead(updatedLead);
    } catch (error) {
      console.error("Failed to update workflow status", error);
      alert("Failed to update status.");
    } finally {
      setIsUpdatingStatus(false);
    }
  };

  const handleRefreshMatches = async () => {
    if (!lead) return;
    
    setIsRefreshingMatches(true);
    
    try {
      const newMatches = await refreshLeadMatches(leadId);
      setMatches(newMatches);
    } catch (error) {
      console.error("Failed to refresh matches", error);
      alert("Failed to refresh matches. Please try again.");
    } finally {
      setIsRefreshingMatches(false);
    }
  };

  const handleRemoveMatch = async (matchId: string) => {
    if (!confirm('Are you sure you want to remove this franchise from the recommendations?')) {
      return;
    }
    
    setRemovingMatchId(matchId);
    
    try {
      // Filter out the match to remove
      const updatedMatches = matches.filter(m => m.id !== matchId);
      
      // Convert to backend format for saving
      const matchesToSave = updatedMatches.map(m => ({
        id: parseInt(m.id),
        franchise_name: m.name,
        description_text: m.description,
        total_investment_min_usd: m.investment_min,
        similarity: m.match_score / 100,
        why_narrative: m.why_narrative
      }));
      
      await saveLeadRecommendations(leadId, matchesToSave);
      setMatches(updatedMatches);
    } catch (error) {
      console.error("Failed to remove match", error);
      alert("Failed to remove franchise. Please try again.");
    } finally {
      setRemovingMatchId(null);
    }
  };

  const handleAddFranchise = async (franchise: FranchiseMatch) => {
    // Create the new match with default narrative
    const newMatch: FranchiseMatch = {
      ...franchise,
      match_score: 0, // No AI score for manually added
      why_narrative: 'Manually added by broker'
    };
    
    // Add to current matches
    const updatedMatches = [...matches, newMatch];
    
    // Convert to backend format for saving
    const matchesToSave = updatedMatches.map(m => ({
      id: parseInt(m.id),
      franchise_name: m.name,
      description_text: m.description,
      total_investment_min_usd: m.investment_min,
      similarity: m.match_score / 100,
      why_narrative: m.why_narrative
    }));
    
    await saveLeadRecommendations(leadId, matchesToSave);
    setMatches(updatedMatches);
  };

  if (isLoading) return <div className="p-8 text-slate-600 dark:text-slate-300">Loading...</div>;
  if (!lead) return <div className="p-8 text-slate-600 dark:text-slate-300">Lead not found</div>;

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

  const currentWorkflowStatus = (lead.workflow_status || 'new') as WorkflowStatus;
  const statusConfig = WORKFLOW_STATUSES[currentWorkflowStatus] || WORKFLOW_STATUSES.new;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 pb-24">
      {/* Header */}
      <div className="bg-white dark:bg-slate-900 border-b border-slate-200 dark:border-slate-800 sticky top-0 z-10 transition-colors">
        <div className="max-w-7xl mx-auto px-8 py-6">
          <div className="flex justify-between items-start">
            <div>
              {/* Back link */}
              <Link 
                href="/leads" 
                className="inline-flex items-center gap-1 text-sm text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 mb-2"
              >
                <ArrowLeft className="w-4 h-4" />
                Back to Leads
              </Link>
              
              <div className="flex items-center gap-4">
                <h1 className="text-3xl font-bold text-slate-900 dark:text-white">{lead.candidate_name || 'Unnamed Lead'}</h1>
                
                {/* Workflow Status Dropdown */}
                <div className="relative">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      setShowStatusDropdown(!showStatusDropdown);
                    }}
                    disabled={isUpdatingStatus}
                    className={`
                      inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium border transition-all
                      ${statusConfig.color}
                      ${isUpdatingStatus ? 'opacity-50 cursor-wait' : 'hover:shadow-sm cursor-pointer'}
                    `}
                  >
                    {isUpdatingStatus ? (
                      <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    ) : (
                      <ChevronDown className="w-3.5 h-3.5" />
                    )}
                    {statusConfig.label}
                  </button>
                  
                  {showStatusDropdown && (
                    <div 
                      className="absolute top-full left-0 mt-1 w-48 bg-white dark:bg-slate-800 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 py-1 z-20"
                      onClick={(e) => e.stopPropagation()}
                    >
                      {Object.entries(WORKFLOW_STATUSES).map(([key, { label, color }]) => (
                        <button
                          key={key}
                          onClick={() => handleWorkflowStatusChange(key as WorkflowStatus)}
                          className={`
                            w-full px-4 py-2 text-left text-sm transition-colors
                            ${currentWorkflowStatus === key 
                              ? 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300' 
                              : 'text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700'}
                          `}
                        >
                          <span className={`inline-block w-2 h-2 rounded-full mr-2 ${
                            key === 'new' ? 'bg-slate-400' :
                            key === 'contacted' ? 'bg-blue-500' :
                            key === 'qualified' ? 'bg-purple-500' :
                            key === 'presented' ? 'bg-indigo-500' :
                            key === 'closed_won' ? 'bg-emerald-500' :
                            'bg-red-500'
                          }`}></span>
                          {label}
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </div>
              
              <div className="flex items-center gap-4 mt-2 text-slate-500 dark:text-slate-400">
                <span className="flex items-center gap-1">
                  <MapPin className="w-4 h-4" />
                  {lead.profile_data.state_code || 'No State'}, {lead.profile_data.location || 'No City'}
                </span>
                <span className="flex items-center gap-1">
                  <Wallet className="w-4 h-4" />
                  ${lead.profile_data.liquidity?.toLocaleString() || '0'} Liquid
                </span>
                <span className={`px-2 py-0.5 rounded text-sm font-medium border ${
                  lead.qualification_status === 'tier_1'
                    ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-100 dark:border-emerald-800'
                    : 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-100 dark:border-amber-800'
                }`}>
                  {lead.qualification_status === 'tier_1' ? 'Tier 1' : 'Tier 2'}
                </span>
                <span className="bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-400 px-2 py-0.5 rounded text-sm font-medium border border-slate-200 dark:border-slate-700">
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
          
          {/* Coaching Card for Tier 2 leads */}
          {missingFields.length > 0 && (
            <CoachingCard missingFields={missingFields} />
          )}
          
          {/* Lead Profile Form */}
          <LeadProfileForm 
            initialProfile={lead.profile_data} 
            onSave={handleSaveProfile} 
          />

          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
                <h2 className="text-xl font-semibold text-slate-900 dark:text-white flex items-center gap-2">
                <BrainCircuit className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
                Franchise Recommendations
                </h2>
                
                {/* Load Saved Comparison Button */}
                {(hasSavedComparison || isCheckingComparison) && (
                    <button
                        onClick={() => router.push(`/franchises/compare?leadId=${leadId}`)}
                        disabled={isCheckingComparison || !hasSavedComparison}
                        className={`
                            flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors
                            ${isCheckingComparison 
                                ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-wait' 
                                : 'bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300 hover:bg-indigo-100 dark:hover:bg-indigo-900/50 border border-indigo-200 dark:border-indigo-800'}
                        `}
                    >
                        {isCheckingComparison ? (
                            <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                            <FileBarChart className="w-4 h-4" />
                        )}
                        {isCheckingComparison ? 'Checking...' : 'Load Saved Comparison'}
                    </button>
                )}
            </div>

            <div className="flex gap-2">
               {/* Add Franchise Button */}
               <button
                 onClick={() => setShowAddModal(true)}
                 className="flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors border bg-indigo-600 text-white hover:bg-indigo-700 border-indigo-600"
               >
                 <Plus className="w-4 h-4" />
                 Add Franchise
               </button>
               
               {/* Re-run Matching Button */}
               <button
                 onClick={handleRefreshMatches}
                 disabled={isRefreshingMatches}
                 className={`
                   flex items-center gap-2 px-3 py-1.5 rounded-md text-sm font-medium transition-colors border
                   ${isRefreshingMatches
                     ? 'bg-slate-100 dark:bg-slate-800 text-slate-400 dark:text-slate-500 cursor-wait border-slate-200 dark:border-slate-700'
                     : 'bg-white dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-700 border-slate-200 dark:border-slate-700'}
                 `}
               >
                 <RefreshCw className={`w-4 h-4 ${isRefreshingMatches ? 'animate-spin' : ''}`} />
                 {isRefreshingMatches ? 'Refreshing...' : 'Re-run AI Matching'}
               </button>
            </div>
          </div>
          
          <div className="space-y-2">
            {matches.length === 0 ? (
              <div className="text-center py-12 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 border-dashed">
                <BrainCircuit className="w-10 h-10 text-slate-300 dark:text-slate-600 mx-auto mb-3" />
                <h3 className="text-slate-900 dark:text-white font-medium mb-1">No matches yet</h3>
                <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
                  Complete the profile and click "Re-run AI Matching" to find franchise recommendations.
                </p>
              </div>
            ) : (
              matches.map((match) => (
                <div key={match.id} className="flex gap-3 items-start">
                   <div className="pt-3">
                      <input 
                          type="checkbox"
                          checked={selectedIds.includes(match.id)}
                          onChange={() => toggleComparison(match.id)}
                          className="w-4 h-4 text-indigo-600 rounded border-gray-300 dark:border-slate-600 bg-white dark:bg-slate-800 focus:ring-indigo-500 cursor-pointer"
                      />
                   </div>
                   <div className="flex-1">
                      <MatchCard 
                          match={match} 
                          onClick={() => setSelectedFranchiseId(parseInt(match.id))}
                      />
                   </div>
                   <div className="pt-3">
                      <button
                        onClick={() => handleRemoveMatch(match.id)}
                        disabled={removingMatchId === match.id}
                        className="p-1.5 text-slate-400 hover:text-red-500 dark:text-slate-500 dark:hover:text-red-400 hover:bg-red-50 dark:hover:bg-red-900/20 rounded transition-colors disabled:opacity-50 disabled:cursor-wait"
                        title="Remove from recommendations"
                      >
                        {removingMatchId === match.id ? (
                          <Loader2 className="w-4 h-4 animate-spin" />
                        ) : (
                          <X className="w-4 h-4" />
                        )}
                      </button>
                   </div>
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Detail Modal */}
      {selectedFranchiseId && (
        <MatchDetailModal 
          franchiseId={selectedFranchiseId} 
          onClose={() => setSelectedFranchiseId(null)}
        />
      )}

      {/* Add Franchise Modal */}
      <AddFranchiseModal
        isOpen={showAddModal}
        onClose={() => setShowAddModal(false)}
        onAdd={handleAddFranchise}
        existingMatchIds={matches.map(m => m.id)}
      />
    </div>
  );
}
