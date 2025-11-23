import React from 'react';
import Link from 'next/link';
import { ArrowRight, DollarSign, ExternalLink } from 'lucide-react';
import { TerritoryFranchise, ComparisonResponse } from '@/types';
import { useComparison } from '@/contexts/ComparisonContext';

interface TerritoryFranchiseListProps {
  franchises: TerritoryFranchise[];
  isLoading: boolean;
  stateCode: string | null;
}

export default function TerritoryFranchiseList({ franchises, isLoading, stateCode }: TerritoryFranchiseListProps) {
  const { selectedIds, toggleComparison } = useComparison();

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
      <div className="text-center py-12 px-4">
        <div className="bg-indigo-50 w-16 h-16 rounded-full flex items-center justify-center mx-auto mb-4">
          <DollarSign className="w-8 h-8 text-indigo-600" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900 mb-1">Select a State</h3>
        <p className="text-slate-500 text-sm">Choose a state on the map to view available franchise opportunities.</p>
      </div>
    );
  }

  if (franchises.length === 0) {
    return (
      <div className="text-center py-12 bg-slate-50 rounded-lg border border-dashed border-slate-200">
        <p className="text-slate-500">No franchises found in {stateCode}.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-3 pb-20">
      <div className="flex items-center justify-between mb-2">
         <div className="text-sm text-slate-500">
            Found <span className="font-semibold text-slate-900">{franchises.length}</span> opportunities in {stateCode}
         </div>
      </div>

      {franchises.map((franchise) => {
        const isSelected = selectedIds.includes(String(franchise.id));
        return (
          <div 
            key={franchise.id}
            className={`
              group relative bg-white rounded-lg p-4 border transition-all hover:shadow-md
              ${isSelected ? 'border-indigo-500 ring-1 ring-indigo-500 bg-indigo-50/10' : 'border-slate-200 hover:border-indigo-300'}
            `}
          >
            <div className="absolute top-4 left-3 z-10">
               <input
                    type="checkbox"
                    checked={isSelected}
                    onChange={() => toggleComparison(String(franchise.id))}
                    className="w-4 h-4 text-indigo-600 rounded border-gray-300 focus:ring-indigo-500 cursor-pointer"
                />
            </div>

            <Link href={`/franchises/${franchise.id}`} className="block pl-7">
              <div className="flex justify-between items-start mb-2">
                <h3 className="font-bold text-slate-900 group-hover:text-indigo-600 transition-colors line-clamp-1">
                  {franchise.franchise_name}
                </h3>
                {franchise.total_investment_min_usd > 0 && (
                  <span className="text-xs font-medium text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full whitespace-nowrap">
                    From ${franchise.total_investment_min_usd.toLocaleString()}
                  </span>
                )}
              </div>
              
              <div className="flex flex-wrap gap-2 mb-3">
                <span className="text-xs text-slate-500 bg-slate-100 px-2 py-0.5 rounded">
                   {franchise.primary_category || 'Franchise'}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded ${
                    franchise.availability_status === 'Available' 
                    ? 'bg-green-100 text-green-700' 
                    : 'bg-amber-100 text-amber-700'
                }`}>
                    {franchise.availability_status}
                </span>
              </div>
              
              <div className="flex items-center text-indigo-600 text-xs font-medium group-hover:underline">
                View Details <ArrowRight className="w-3 h-3 ml-1" />
              </div>
            </Link>
          </div>
        );
      })}
    </div>
  );
}
