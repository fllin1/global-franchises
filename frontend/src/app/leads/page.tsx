'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Plus, Trash2, Search, Filter } from 'lucide-react';
import { getLeads, deleteLead } from '@/app/actions';
import { Lead } from '@/types';

export default function LeadsPage() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState('all'); // all, tier_1, tier_2

  useEffect(() => {
    loadLeads();
  }, []);

  async function loadLeads() {
    try {
      setIsLoading(true);
      const data = await getLeads();
      setLeads(data);
    } catch (error) {
      console.error(error);
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

  const filteredLeads = leads.filter(lead => {
    if (filter === 'all') return true;
    return lead.qualification_status === filter;
  });

  return (
    <div className="p-6 md:p-10 max-w-7xl mx-auto">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-8 gap-4">
        <div>
            <h1 className="text-2xl font-bold text-slate-900">My Leads</h1>
            <p className="text-slate-500 mt-1">Manage your pipeline and franchise matches</p>
        </div>
        <Link href="/leads/new" className="bg-indigo-600 hover:bg-indigo-700 text-white px-4 py-2 rounded-lg flex items-center gap-2 font-medium shadow-sm transition-colors">
            <Plus className="w-4 h-4" />
            New Lead
        </Link>
      </div>

      {/* Filters */}
      <div className="flex items-center gap-2 mb-6 bg-white p-2 rounded-lg border border-slate-200 w-fit">
        <Filter className="w-4 h-4 text-slate-400 ml-2" />
        <select 
            value={filter}
            onChange={(e) => setFilter(e.target.value)}
            className="bg-transparent border-none text-sm text-slate-700 focus:ring-0 cursor-pointer pr-8"
        >
            <option value="all">All Statuses</option>
            <option value="tier_1">Tier 1 (Ready)</option>
            <option value="tier_2">Tier 2 (Incomplete)</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-20 text-slate-400">Loading leads...</div>
      ) : filteredLeads.length === 0 ? (
        <div className="text-center py-20 bg-white rounded-xl border border-slate-200 border-dashed">
            <div className="mx-auto w-12 h-12 bg-slate-50 rounded-full flex items-center justify-center mb-3">
                <Search className="w-6 h-6 text-slate-300" />
            </div>
            <h3 className="text-slate-900 font-medium mb-1">No leads found</h3>
            <p className="text-slate-500 text-sm mb-4">Get started by adding your first lead note.</p>
            <Link href="/leads/new" className="text-indigo-600 hover:text-indigo-700 text-sm font-medium">
                Add New Lead
            </Link>
        </div>
      ) : (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
            <table className="w-full text-left">
                <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Candidate</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Status</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Location</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Liquidity</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider">Date</th>
                        <th className="px-6 py-4 text-xs font-semibold text-slate-500 uppercase tracking-wider text-right">Actions</th>
                    </tr>
                </thead>
                <tbody className="divide-y divide-slate-100">
                    {filteredLeads.map((lead) => (
                        <tr key={lead.id} className="hover:bg-slate-50 transition-colors group">
                            <td className="px-6 py-4">
                                <Link href={`/leads/${lead.id}`} className="block">
                                    <div className="font-medium text-slate-900">
                                        {lead.candidate_name || lead.profile_data?.candidate_name || `Lead #${lead.id}`}
                                    </div>
                                    <div className="text-xs text-slate-500 line-clamp-1 max-w-[200px]">
                                        {lead.notes.substring(0, 50)}...
                                    </div>
                                </Link>
                            </td>
                            <td className="px-6 py-4">
                                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${
                                    lead.qualification_status === 'tier_1' 
                                    ? 'bg-emerald-50 text-emerald-700 border-emerald-100' 
                                    : 'bg-amber-50 text-amber-700 border-amber-100'
                                }`}>
                                    {lead.qualification_status === 'tier_1' ? 'Tier 1' : 'Tier 2'}
                                </span>
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-600">
                                {lead.profile_data?.location || '-'}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-600">
                                {lead.profile_data?.liquidity ? `$${lead.profile_data.liquidity.toLocaleString()}` : '-'}
                            </td>
                            <td className="px-6 py-4 text-sm text-slate-500">
                                {new Date(lead.created_at).toLocaleDateString()}
                            </td>
                            <td className="px-6 py-4 text-right">
                                <button 
                                    onClick={(e) => {
                                        e.stopPropagation();
                                        handleDelete(lead.id);
                                    }}
                                    className="text-slate-400 hover:text-red-600 transition-colors p-2 opacity-0 group-hover:opacity-100"
                                >
                                    <Trash2 className="w-4 h-4" />
                                </button>
                            </td>
                        </tr>
                    ))}
                </tbody>
            </table>
        </div>
      )}
    </div>
  );
}

