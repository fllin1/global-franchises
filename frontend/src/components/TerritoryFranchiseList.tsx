'use client';

import { TerritoryFranchise } from '@/types';
import { CheckCircle2, AlertCircle, XCircle, DollarSign, Briefcase } from 'lucide-react';

interface TerritoryFranchiseListProps {
  franchises: TerritoryFranchise[];
  isLoading: boolean;
  stateCode: string | null;
}

export default function TerritoryFranchiseList({ franchises, isLoading, stateCode }: TerritoryFranchiseListProps) {
  if (isLoading) {
    return (
      <div className="flex flex-col gap-3">
        {[1, 2, 3, 4, 5, 6].map((i) => (
          <div key={i} className="bg-white rounded-lg p-4 border border-slate-100 shadow-sm animate-pulse">
            <div className="h-5 bg-slate-100 rounded w-3/4 mb-2"></div>
            <div className="flex gap-2 mb-3">
              <div className="h-4 bg-slate-100 rounded-full w-16"></div>
            </div>
            <div className="h-3 bg-slate-100 rounded w-1/2"></div>
          </div>
        ))}
      </div>
    );
  }

  if (!stateCode) {
    return (
      <div className="h-full flex flex-col items-center justify-center text-center p-8 bg-slate-50/50 rounded-xl border border-dashed border-slate-200">
        <div className="w-12 h-12 bg-slate-100 rounded-full flex items-center justify-center mb-3">
          <Briefcase className="w-6 h-6 text-slate-400" />
        </div>
        <h3 className="text-base font-medium text-slate-900 mb-1">Select a Territory</h3>
        <p className="text-sm text-slate-500 max-w-xs">
          Click a state on the map to view opportunities.
        </p>
      </div>
    );
  }

  if (franchises.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center p-8 text-center">
        <XCircle className="w-10 h-10 text-slate-300 mb-3" />
        <h3 className="text-base font-medium text-slate-900">No Franchises Found</h3>
        <p className="text-sm text-slate-500 mt-1">
          No available franchises in {stateCode}.
        </p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3">
      {franchises.map((franchise) => {
        // Parse categories that come as stringified arrays e.g. "['Category']"
        const categories = franchise.primary_category
          ? franchise.primary_category.replace(/[\[\]"']/g, '').split(',').map(s => s.trim()).filter(Boolean)
          : [];

        return (
          <div 
            key={franchise.id} 
            className="group bg-white rounded-lg p-3 border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all duration-200 flex flex-col"
          >
            <div className="flex justify-between items-start mb-2">
              <h3 className="font-semibold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1 text-sm">
                {franchise.franchise_name}
              </h3>
              <AvailabilityBadge status={franchise.availability_status} />
            </div>

            <div className="flex flex-wrap gap-1.5 mb-3">
              {categories.map((cat, idx) => (
                <span key={idx} className="inline-flex items-center px-1.5 py-0.5 rounded-md bg-slate-50 text-[10px] font-medium text-slate-600 border border-slate-100">
                  {cat}
                </span>
              ))}
            </div>

            <div className="mt-auto pt-2 border-t border-slate-50 flex items-center justify-between text-xs">
              <div className="flex items-center gap-1 text-slate-600">
                <DollarSign className="w-3 h-3 text-slate-400" />
                <span>Min: ${franchise.total_investment_min_usd?.toLocaleString() || 'N/A'}</span>
              </div>
            </div>
          </div>
        );
      })}
    </div>
  );
}

function AvailabilityBadge({ status }: { status: TerritoryFranchise['availability_status'] }) {
  switch (status) {
    case 'Available':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-emerald-50 text-emerald-700 text-[10px] font-medium uppercase tracking-wide border border-emerald-100">
          <CheckCircle2 className="w-3 h-3" />
          Available
        </span>
      );
    case 'Limited':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-amber-50 text-amber-700 text-[10px] font-medium uppercase tracking-wide border border-amber-100">
          <AlertCircle className="w-3 h-3" />
          Limited
        </span>
      );
    case 'Not Available':
      return (
        <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full bg-slate-100 text-slate-600 text-[10px] font-medium uppercase tracking-wide border border-slate-200">
          <XCircle className="w-3 h-3" />
          Unavailable
        </span>
      );
    default:
      return null;
  }
}
