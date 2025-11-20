'use client';

import { useState, useEffect } from 'react';
import { X, Loader2, ExternalLink, Building, Info, DollarSign } from 'lucide-react';
import { getFranchiseDetail } from '@/app/actions';

interface MatchDetailModalProps {
  franchiseId: number | null;
  onClose: () => void;
}

export function MatchDetailModal({ franchiseId, onClose }: MatchDetailModalProps) {
  const [data, setData] = useState<any>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (franchiseId) {
      loadDetail(franchiseId);
    } else {
        setData(null);
    }
  }, [franchiseId]);

  async function loadDetail(id: number) {
    setLoading(true);
    try {
      const detail = await getFranchiseDetail(id);
      setData(detail);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  if (!franchiseId) return null;

  // Helper to safely parse description if it's JSON
  const getDescription = (text: string) => {
    try {
        // Remove outer quotes if double encoded
        if (text.startsWith('"') && text.endsWith('"')) {
             text = JSON.parse(text);
        }
        // If it looks like a JSON array/object
        if (text.startsWith('[') || text.startsWith('{')) {
             // It might be a list of paragraphs?
             const parsed = JSON.parse(text);
             if (Array.isArray(parsed)) return parsed.join('\n\n');
             return JSON.stringify(parsed);
        }
        return text;
    } catch {
        return text;
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between bg-slate-50">
          <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
             <Building className="w-5 h-5 text-indigo-600" />
             {loading ? 'Loading...' : data?.franchise_name}
          </h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors p-1 hover:bg-slate-200 rounded-full">
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 bg-white">
          {loading ? (
            <div className="flex flex-col items-center justify-center h-64 text-slate-500">
              <Loader2 className="w-8 h-8 animate-spin mb-2 text-indigo-500" />
              <p>Loading FDD details...</p>
            </div>
          ) : data ? (
            <div className="space-y-8">
              {/* Overview */}
              <section>
                <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                   <Info className="w-4 h-4 text-slate-400" />
                   Overview
                </h3>
                <p className="text-slate-600 leading-relaxed whitespace-pre-line text-sm">
                  {data.description_text ? getDescription(data.description_text) : "No description available."}
                </p>
                {data.website_url && (
                  <a href={data.website_url} target="_blank" rel="noopener noreferrer" className="inline-flex items-center gap-1 text-indigo-600 hover:underline mt-3 text-sm font-medium">
                    Visit Website <ExternalLink className="w-3 h-3" />
                  </a>
                )}
              </section>

              {/* Stats Grid */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                 <div className="bg-slate-50 p-3 rounded border border-slate-100">
                    <div className="text-xs text-slate-500 uppercase mb-1">Founded</div>
                    <div className="font-semibold text-slate-900 text-sm">{data.founded_year || 'N/A'}</div>
                 </div>
                 <div className="bg-slate-50 p-3 rounded border border-slate-100">
                    <div className="text-xs text-slate-500 uppercase mb-1">Franchised</div>
                    <div className="font-semibold text-slate-900 text-sm">{data.franchised_year || 'N/A'}</div>
                 </div>
                 <div className="bg-slate-50 p-3 rounded border border-slate-100">
                    <div className="text-xs text-slate-500 uppercase mb-1">Model</div>
                    <div className="font-semibold text-slate-900 text-sm">{data.business_model_type || 'N/A'}</div>
                 </div>
                 <div className="bg-slate-50 p-3 rounded border border-slate-100">
                    <div className="text-xs text-slate-500 uppercase mb-1">Category</div>
                    <div className="font-semibold text-slate-900 text-sm truncate" title={data.primary_category}>
                        {Array.isArray(data.primary_category) ? data.primary_category[0] : data.primary_category}
                    </div>
                 </div>
              </div>

              {/* Financials */}
              <section>
                 <h3 className="text-xs font-bold text-slate-900 uppercase tracking-wider mb-3 flex items-center gap-2">
                   <DollarSign className="w-4 h-4 text-slate-400" />
                   Investment & Fees
                </h3>
                <div className="bg-white border border-slate-200 rounded-lg overflow-hidden">
                    <div className="grid grid-cols-2 border-b border-slate-200">
                         <div className="p-4 border-r border-slate-200">
                             <div className="text-xs text-slate-500 mb-1">Total Investment</div>
                             <div className="text-lg font-bold text-slate-900">
                                ${data.total_investment_min_usd?.toLocaleString()} - ${data.total_investment_max_usd?.toLocaleString()}
                             </div>
                         </div>
                         <div className="p-4">
                             <div className="text-xs text-slate-500 mb-1">Liquid Capital Req.</div>
                             <div className="text-lg font-bold text-emerald-700">
                                ${data.required_cash_investment_usd?.toLocaleString()}
                             </div>
                         </div>
                    </div>
                    <div className="p-4 bg-slate-50">
                        <div className="text-xs text-slate-500 mb-1">Royalties</div>
                        <div className="text-sm text-slate-700 font-medium">
                            {data.royalty_details_text || 'Contact for details'}
                        </div>
                    </div>
                </div>
              </section>

              {/* Tags */}
              <div className="flex flex-wrap gap-2 pt-2">
                  {data.is_home_based && (
                      <span className="px-2.5 py-1 bg-blue-50 text-blue-700 text-xs font-medium rounded-full border border-blue-100">Home Based</span>
                  )}
                  {data.allows_semi_absentee && (
                      <span className="px-2.5 py-1 bg-purple-50 text-purple-700 text-xs font-medium rounded-full border border-purple-100">Semi-Absentee</span>
                  )}
                   {data.allows_absentee && (
                      <span className="px-2.5 py-1 bg-indigo-50 text-indigo-700 text-xs font-medium rounded-full border border-indigo-100">Absentee</span>
                  )}
              </div>

            </div>
          ) : (
             <div className="text-center text-red-500">Failed to load details</div>
          )}
        </div>
        
        {/* Footer */}
        <div className="p-4 border-t border-slate-100 bg-slate-50 flex justify-end">
            <button onClick={onClose} className="px-4 py-2 bg-white border border-slate-300 text-slate-700 font-medium rounded hover:bg-slate-50 transition-colors text-sm">
                Close Detail
            </button>
        </div>
      </div>
    </div>
  );
}

