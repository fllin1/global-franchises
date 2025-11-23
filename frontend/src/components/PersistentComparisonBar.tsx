'use client';

import { useComparison } from '@/contexts/ComparisonContext';
import { useRouter } from 'next/navigation';
import { ArrowRightLeft, XCircle, UserPlus, FileBarChart, Save } from 'lucide-react';
import { useState, useEffect } from 'react';
import { Lead } from '@/types';
import { saveLeadComparisonAnalysis, getLeads } from '@/app/actions';

export default function PersistentComparisonBar() {
  const { selectedIds, clearComparison, count, leadId: contextLeadId, setLeadContext } = useComparison();
  const router = useRouter();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [selectedLeadId, setSelectedLeadId] = useState<string>("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    // Sync with context if present
    if (contextLeadId) {
        setSelectedLeadId(String(contextLeadId));
    }
  }, [contextLeadId]);

  useEffect(() => {
    // Only fetch leads if we have selected items, to save resources
    // And if not already attached to a lead via context
    if (count > 0 && !contextLeadId) {
      getLeads()
        .then(setLeads)
        .catch(console.error);
    }
  }, [count, contextLeadId]);

  const handleCompare = () => {
    if (count === 0) return;
    const idsParam = selectedIds.join(',');
    const leadParam = selectedLeadId ? `&leadId=${selectedLeadId}` : '';
    router.push(`/franchises/compare?ids=${idsParam}${leadParam}`);
  };

  const handleLeadChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
      const val = e.target.value;
      setSelectedLeadId(val);
      if (val) {
          // If we select a lead, we might want to switch context?
          // Or just attach for this comparison session.
          // For now, let's just keep it as an attachment parameter.
      }
  };

  if (count === 0) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-40 bg-white border-t border-slate-200 shadow-[0_-4px_6px_-1px_rgba(0,0,0,0.1)] p-4 animate-in slide-in-from-bottom duration-300">
      <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
        
        {/* Status Info */}
        <div className="flex items-center gap-4">
          <div className="bg-indigo-100 p-2 rounded-lg">
            <FileBarChart className="w-5 h-5 text-indigo-600" />
          </div>
          <div>
            <div className="text-sm font-bold text-slate-900">
              <span className="text-indigo-600">{count}</span> Franchise{count !== 1 ? 's' : ''} Selected
            </div>
            <p className="text-xs text-slate-500">Ready for side-by-side comparison</p>
          </div>
        </div>

        {/* Action Controls */}
        <div className="flex items-center gap-3 w-full sm:w-auto">
          {/* Lead Attachment */}
          {contextLeadId ? (
              <div className="px-4 py-2 bg-slate-100 rounded-lg text-sm text-slate-700 font-medium flex items-center gap-2">
                  <UserPlus className="w-4 h-4 text-indigo-500" />
                  Attached to Lead #{contextLeadId}
              </div>
          ) : (
            <div className="relative flex-1 sm:w-64">
                <select
                    value={selectedLeadId}
                    onChange={handleLeadChange}
                    className="w-full pl-9 pr-4 py-2 bg-slate-50 border border-slate-300 rounded-lg text-sm focus:ring-2 focus:ring-indigo-500 outline-none appearance-none cursor-pointer"
                >
                    <option value="">Attach to Lead (Optional)...</option>
                    {leads.map(lead => (
                        <option key={lead.id} value={lead.id}>
                            {lead.candidate_name || `Lead #${lead.id}`}
                        </option>
                    ))}
                </select>
                <UserPlus className="w-4 h-4 text-slate-400 absolute left-3 top-2.5 pointer-events-none" />
            </div>
          )}

          <button
            onClick={handleCompare}
            className="flex-shrink-0 inline-flex items-center gap-2 bg-indigo-600 text-white px-6 py-2 rounded-lg text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm shadow-indigo-200"
          >
            <ArrowRightLeft className="w-4 h-4" />
            Compare Now
          </button>
          
          <button 
            onClick={clearComparison}
            className="flex-shrink-0 text-slate-400 hover:text-red-500 p-2 hover:bg-red-50 rounded-lg transition-colors"
            title="Clear all"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
