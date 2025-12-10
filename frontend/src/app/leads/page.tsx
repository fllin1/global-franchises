'use client';

import { useState, useEffect, useMemo } from 'react';
import Link from 'next/link';
import { Plus, Trash2, Search, Filter, CircleDot } from 'lucide-react';
import { getLeads, deleteLead } from '@/app/actions';
import { Lead } from '@/types';

// Workflow status configuration
const WORKFLOW_STATUSES = {
  new: { label: 'New', color: 'bg-slate-100 text-slate-700 border-slate-200' },
  contacted: { label: 'Contacted', color: 'bg-blue-50 text-blue-700 border-blue-100' },
  qualified: { label: 'Qualified', color: 'bg-purple-50 text-purple-700 border-purple-100' },
  presented: { label: 'Presented', color: 'bg-indigo-50 text-indigo-700 border-indigo-100' },
  closed_won: { label: 'Closed Won', color: 'bg-emerald-50 text-emerald-700 border-emerald-100' },
  closed_lost: { label: 'Closed Lost', color: 'bg-red-50 text-red-700 border-red-100' },
} as const;

type WorkflowStatus = keyof typeof WORKFLOW_STATUSES;

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [tierFilter, setTierFilter] = useState('all'); // all, tier_1, tier_2
  const [workflowFilter, setWorkflowFilter] = useState('all'); // all, new, contacted, etc.
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    loadLeads();
  }, []);

  async function loadLeads() {
    try {
      setIsLoading(true);
      setError(null);
      const data = await getLeads();
      setLeads(data);
    } catch (error) {
      console.error('Error loading leads:', error);
      const errorMessage = error instanceof Error 
        ? error.message 
        : 'Failed to connect to backend API. Please check your connection and try again.';
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  }

  async function handleDelete(id: number) {
    if (!confirm('Are you sure you want to delete this lead?')) return;
    try {
      await deleteLead(id);
      setLeads(leads.filter(l => l.id !== id));
    } catch (error) {
      alert('Failed to delete lead');
    }
  }

  const filteredLeads = useMemo(() => {
    return leads.filter(lead => {
      // Tier filter
      if (tierFilter !== 'all' && lead.qualification_status !== tierFilter) {
        return false;
      }
      
      // Workflow filter
      if (workflowFilter !== 'all' && lead.workflow_status !== workflowFilter) {
        return false;
      }
      
      // Search filter
      if (searchQuery.trim()) {
        const query = searchQuery.toLowerCase();
        const name = (lead.candidate_name || lead.profile_data?.candidate_name || '').toLowerCase();
        const location = (lead.profile_data?.location || '').toLowerCase();
        const notes = (lead.notes || '').toLowerCase();
        
        if (!name.includes(query) && !location.includes(query) && !notes.includes(query)) {
          return false;
        }
      }
      
      return true;
    });
  }, [leads, tierFilter, workflowFilter, searchQuery]);

  // Calculate stats for quick filters
  const stats = useMemo(() => {
    const byWorkflow: Record<string, number> = { all: leads.length };
    leads.forEach(lead => {
      const status = lead.workflow_status || 'new';
      byWorkflow[status] = (byWorkflow[status] || 0) + 1;
    });
    return byWorkflow;
  }, [leads]);

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
            <h1 className="text-2xl font-bold text-slate-900 dark:text-white">My Leads</h1>
            <p className="text-slate-500 dark:text-slate-400 mt-1">Manage your pipeline and franchise matches</p>
        </div>
        <Link href="/leads/new" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium shadow-sm transition-colors">
            <Plus className="w-4 h-4" />
            New Lead
        </Link>
      </div>

      {/* Pipeline Stats */}
      {!isLoading && !error && leads.length > 0 && (
        <div className="flex flex-wrap gap-2 mb-6">
          {Object.entries(WORKFLOW_STATUSES).map(([key, { label, color }]) => {
            const count = stats[key] || 0;
            const isActive = workflowFilter === key;
            return (
              <button
                key={key}
                onClick={() => setWorkflowFilter(isActive ? 'all' : key)}
                className={`
                  inline-flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs font-medium border transition-all
                  ${isActive 
                    ? 'ring-2 ring-indigo-500 ring-offset-1' 
                    : 'hover:shadow-sm'}
                  ${color}
                `}
              >
                <CircleDot className="w-3 h-3" />
                {label}
                <span className="bg-white/50 dark:bg-slate-800/50 px-1.5 py-0.5 rounded text-[10px]">
                  {count}
                </span>
              </button>
            );
          })}
        </div>
      )}

      {/* Filters Row */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3 mb-6">
        {/* Search Input */}
        <div className="relative flex-1 max-w-md">
          <Search className="w-4 h-4 text-slate-400 dark:text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name, location, or notes..."
            className="w-full pl-10 pr-4 py-2 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-sm text-slate-700 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none"
          />
        </div>
        
        {/* Tier Filter */}
        <div className="flex items-center gap-2 bg-white dark:bg-slate-800 p-2 rounded-lg border border-slate-200 dark:border-slate-700">
          <Filter className="w-4 h-4 text-slate-400 dark:text-slate-500 ml-1" />
          <select 
              value={tierFilter}
              onChange={(e) => setTierFilter(e.target.value)}
              className="bg-transparent border-none text-sm text-slate-700 dark:text-white focus:ring-0 cursor-pointer pr-8"
          >
              <option value="all">All Tiers</option>
              <option value="tier_1">Tier 1 (Ready)</option>
              <option value="tier_2">Tier 2 (Incomplete)</option>
          </select>
        </div>

        {/* Clear Filters */}
        {(tierFilter !== 'all' || workflowFilter !== 'all' || searchQuery) && (
          <button
            onClick={() => {
              setTierFilter('all');
              setWorkflowFilter('all');
              setSearchQuery('');
            }}
            className="text-xs text-slate-500 dark:text-slate-400 hover:text-slate-700 dark:hover:text-slate-200 underline"
          >
            Clear filters
          </button>
        )}
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-slate-400 dark:text-slate-500">Loading leads...</div>
      ) : error ? (
        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-xl border border-red-200 dark:border-red-800">
            <div className="mx-auto w-12 h-12 bg-red-50 dark:bg-red-900/30 rounded-full flex items-center justify-center mb-3">
                <Search className="w-6 h-6 text-red-400" />
            </div>
            <h3 className="text-red-900 dark:text-red-300 font-medium mb-1">Connection Error</h3>
            <p className="text-red-600 dark:text-red-400 text-sm mb-4">{error}</p>
            <button 
              onClick={loadLeads}
              className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 text-sm font-medium"
            >
                Retry
            </button>
        </div>
      ) : filteredLeads.length === 0 ? (
        <div className="text-center py-20 bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 border-dashed">
            <div className="mx-auto w-12 h-12 bg-slate-50 dark:bg-slate-800 rounded-full flex items-center justify-center mb-3">
                <Search className="w-6 h-6 text-slate-300 dark:text-slate-600" />
            </div>
            <h3 className="text-slate-900 dark:text-white font-medium mb-1">
              {leads.length > 0 ? 'No leads match your filters' : 'No leads found'}
            </h3>
            <p className="text-slate-500 dark:text-slate-400 text-sm mb-4">
              {leads.length > 0 
                ? 'Try adjusting your search or filter criteria.' 
                : 'Get started by adding your first lead note.'}
            </p>
            {leads.length === 0 && (
              <Link href="/leads/new" className="text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 text-sm font-medium">
                  Add New Lead
              </Link>
            )}
        </div>
      ) : (
        <div className="bg-white dark:bg-slate-900 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
            <table className="w-full text-left">
                <thead className="bg-slate-50 dark:bg-slate-800 border-b border-slate-200 dark:border-slate-700">
                    <tr>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Candidate</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Tier</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Pipeline</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Location</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Liquidity</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">Date</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    {filteredLeads.map((lead) => {
                        const workflowStatus = (lead.workflow_status || 'new') as WorkflowStatus;
                        const statusConfig = WORKFLOW_STATUSES[workflowStatus] || WORKFLOW_STATUSES.new;
                        
                        return (
                          <tr key={lead.id} className="hover:bg-slate-50 dark:hover:bg-slate-800/50 transition-colors group">
                              <td className="px-6 py-4">
                                  <Link href={`/leads/${lead.id}`} className="block">
                                      <div className="font-medium text-slate-900 dark:text-white">
                                          {lead.candidate_name || lead.profile_data?.candidate_name || `Lead #${lead.id}`}
                                      </div>
                                      <div className="text-xs text-slate-500 dark:text-slate-400 line-clamp-1 max-w-[200px]">
                                          {lead.notes.substring(0, 50)}...
                                      </div>
                                  </Link>
                              </td>
                              <td className="px-6 py-4">
                                  <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                                      lead.qualification_status === 'tier_1' 
                                      ? 'bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300 border-emerald-100 dark:border-emerald-800' 
                                      : 'bg-amber-50 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 border-amber-100 dark:border-amber-800'
                                  }`}>
                                      {lead.qualification_status === 'tier_1' ? 'Tier 1' : 'Tier 2'}
                                  </span>
                              </td>
                              <td className="px-6 py-4">
                                  <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-medium border ${statusConfig.color}`}>
                                      <CircleDot className="w-3 h-3" />
                                      {statusConfig.label}
                                  </span>
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                                  {lead.profile_data?.location || '-'}
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-600 dark:text-slate-400">
                                  {lead.profile_data?.liquidity ? `$${lead.profile_data.liquidity.toLocaleString()}` : '-'}
                              </td>
                              <td className="px-6 py-4 text-sm text-slate-500 dark:text-slate-400">
                                  {new Date(lead.created_at).toLocaleDateString()}
                              </td>
                              <td className="px-6 py-4 text-right">
                                  <button 
                                      onClick={(e) => {
                                          e.stopPropagation();
                                          handleDelete(lead.id);
                                      }}
                                      className="text-slate-400 dark:text-slate-500 hover:text-red-600 dark:hover:text-red-400 transition-colors p-2 opacity-0 group-hover:opacity-100"
                                  >
                                      <Trash2 className="w-4 h-4" />
                                  </button>
                              </td>
                          </tr>
                        );
                    })}
                </tbody>
            </table>
        </div>
      )}
    </div>
  );
}
