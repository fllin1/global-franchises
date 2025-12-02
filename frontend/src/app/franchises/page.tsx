'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Search, Building, DollarSign, ArrowRight, Loader2 } from 'lucide-react';
import { searchFranchises } from './actions';
import { FranchiseMatch } from '@/types';
import { useComparison } from '@/contexts/ComparisonContext';

export default function FranchiseSearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<FranchiseMatch[]>([]);
  const [loading, setLoading] = useState(true);
  const [searched, setSearched] = useState(false);

  // Comparison State
  const { selectedIds, toggleComparison } = useComparison();

  // Initial load and Debounce search
  useEffect(() => {
    const fetchFranchises = async () => {
      setLoading(true);
      try {
        const data = await searchFranchises(query);
        setResults(data);
        setSearched(true);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    // Debounce for search queries
    const timer = setTimeout(() => {
      fetchFranchises();
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Calculate stats
  const totalFranchises = results.length;

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-8 pb-32">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-indigo-100 dark:bg-indigo-900/30 rounded-lg">
              <Building className="w-6 h-6 text-indigo-600 dark:text-indigo-400" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Franchise Directory</h1>
          </div>
          <p className="text-slate-500 dark:text-slate-400 max-w-2xl">
            Browse our complete database of franchise opportunities. Search by name or filter to find the perfect match.
          </p>
          
          {/* Stats Bar */}
          <div className="mt-6 flex gap-6 text-sm">
            <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <Building className="w-4 h-4 text-indigo-500" />
              <span className="text-slate-600 dark:text-slate-300">
                <span className="font-semibold text-slate-900 dark:text-white">{totalFranchises}</span> Franchises
              </span>
            </div>
            {selectedIds.length > 0 && (
              <Link 
                href="/franchises/compare"
                className="flex items-center gap-2 px-4 py-2 bg-indigo-600 hover:bg-indigo-700 text-white rounded-lg transition-colors"
              >
                <span className="font-semibold">{selectedIds.length}</span> Selected — Compare
                <ArrowRight className="w-4 h-4" />
              </Link>
            )}
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-2xl mb-8">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className={`w-5 h-5 ${loading ? 'text-indigo-500' : 'text-slate-400 dark:text-slate-500'}`} />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search franchise name (e.g. 'Smoothie', 'Fitness')..."
            className="block w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm transition-all"
          />
          {loading && (
            <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
              <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
            </div>
          )}
        </div>

        {/* Results Table */}
        {results.length > 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th scope="col" className="w-12 px-4 py-4 text-center">
                    <span className="sr-only">Select</span>
                  </th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Franchise
                  </th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Category
                  </th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Min Investment
                  </th>
                  <th scope="col" className="px-6 py-4 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {results.map((franchise) => {
                  const isSelected = selectedIds.includes(franchise.id);
                  return (
                    <tr 
                      key={franchise.id} 
                      className={`transition-colors ${
                        isSelected 
                          ? 'bg-indigo-50 dark:bg-indigo-900/20' 
                          : 'hover:bg-slate-50 dark:hover:bg-slate-700/50'
                      }`}
                    >
                      {/* Checkbox Column */}
                      <td className="w-12 px-4 py-4 text-center">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={() => toggleComparison(franchise.id)}
                          className="w-5 h-5 text-indigo-600 rounded border-gray-300 dark:border-slate-600 focus:ring-indigo-500 cursor-pointer"
                        />
                      </td>
                      
                      {/* Franchise Column */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link href={`/franchises/${franchise.id}`} className="flex items-center gap-4 group">
                          <div className="flex-shrink-0 w-12 h-12 bg-slate-100 dark:bg-slate-700 rounded-lg overflow-hidden flex items-center justify-center relative">
                            {franchise.logo_url ? (
                              <>
                                <Image
                                  src={franchise.logo_url}
                                  alt={franchise.name}
                                  width={48}
                                  height={48}
                                  className="object-contain z-10 relative"
                                  onError={(e) => {
                                    const img = e.target as HTMLImageElement;
                                    img.style.display = 'none';
                                    // Show fallback icon
                                    const container = img.parentElement;
                                    const fallback = container?.querySelector('.logo-fallback') as HTMLElement;
                                    if (fallback) fallback.style.display = 'flex';
                                  }}
                                />
                                <Building className="w-6 h-6 text-slate-400 dark:text-slate-500 logo-fallback hidden absolute inset-0 items-center justify-center" />
                              </>
                            ) : (
                              <Building className="w-6 h-6 text-slate-400 dark:text-slate-500" />
                            )}
                          </div>
                          <div className="font-semibold text-slate-900 dark:text-white group-hover:text-indigo-600 dark:group-hover:text-indigo-400 transition-colors">
                            {franchise.name}
                          </div>
                        </Link>
                      </td>
                      
                      {/* Category Column */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="text-sm text-slate-600 dark:text-slate-400">
                          {franchise.primary_category || '—'}
                        </span>
                      </td>
                      
                      {/* Min Investment Column */}
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-emerald-50 dark:bg-emerald-900/30 text-emerald-700 dark:text-emerald-300">
                          <DollarSign className="w-3.5 h-3.5" />
                          {franchise.investment_min > 0 
                            ? `${franchise.investment_min.toLocaleString()}`
                            : '—'
                          }
                        </span>
                      </td>
                      
                      {/* Action Column */}
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <Link
                          href={`/franchises/${franchise.id}`}
                          className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-indigo-600 dark:text-indigo-400 hover:text-indigo-700 dark:hover:text-indigo-300 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors"
                        >
                          View Details
                          <ArrowRight className="w-4 h-4" />
                        </Link>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        ) : (
          searched && !loading && (
            <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 border-dashed">
              <Building className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">No franchises found.</p>
            </div>
          )
        )}
        
        {!searched && loading && (
          <div className="flex justify-center py-20">
            <Loader2 className="w-10 h-10 text-indigo-500 animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}
