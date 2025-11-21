'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import { Search, Building, DollarSign, ArrowRight, Loader2, MapPin } from 'lucide-react';
import { searchFranchises } from './actions';
import { FranchiseMatch } from '@/types';
import { useDebounce } from '@/hooks/useDebounce'; // Assuming hook exists, otherwise I'll implement debounce inline

export default function FranchiseSearchPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<FranchiseMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  // Simple debounce effect
  useEffect(() => {
    const timer = setTimeout(async () => {
      if (query.length >= 2) {
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
      } else if (query.length === 0) {
        setResults([]);
        setSearched(false);
      }
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  return (
    <div className="min-h-screen bg-slate-50 p-8">
      <div className="max-w-5xl mx-auto">
        {/* Header */}
        <div className="mb-10 text-center">
            <h1 className="text-3xl font-bold text-slate-900 mb-4">Franchise Directory</h1>
            <p className="text-slate-500 max-w-lg mx-auto">
                Search for franchise brands to view detailed FDD information and interactive territory availability maps.
            </p>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-2xl mx-auto mb-12">
            <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
                <Search className={`w-5 h-5 ${loading ? 'text-indigo-500' : 'text-slate-400'}`} />
            </div>
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search franchise name (e.g. 'Smoothie', 'Fitness')..."
                className="block w-full pl-11 pr-4 py-4 bg-white border border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent shadow-sm transition-all"
            />
            {loading && (
                <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
                    <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
                </div>
            )}
        </div>

        {/* Results */}
        <div className="space-y-4">
            {results.length > 0 ? (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {results.map((franchise) => (
                        <Link 
                            key={franchise.id} 
                            href={`/franchises/${franchise.id}`}
                            className="block bg-white border border-slate-200 rounded-xl p-5 hover:border-indigo-500 hover:shadow-md transition-all group"
                        >
                            <div className="flex justify-between items-start">
                                <div>
                                    <h3 className="font-bold text-lg text-slate-900 group-hover:text-indigo-600 transition-colors">
                                        {franchise.name}
                                    </h3>
                                    <div className="text-sm text-slate-500 mb-3 flex items-center gap-2">
                                        <Building className="w-3 h-3" />
                                        {/* Using description as category fallback if needed, but API returns primary_category */}
                                        {/* We might need to adjust type definition or cast */}
                                        {franchise.primary_category || 'Franchise'}
                                    </div>
                                </div>
                                <div className="bg-slate-50 p-2 rounded-lg">
                                    <ArrowRight className="w-5 h-5 text-slate-400 group-hover:text-indigo-500" />
                                </div>
                            </div>
                            
                            <div className="mt-4 flex items-center gap-4 text-sm">
                                <div className="flex items-center gap-1.5 text-slate-600">
                                    <DollarSign className="w-4 h-4 text-emerald-600" />
                                    <span className="font-medium">
                                        ${franchise.investment_min.toLocaleString()}
                                    </span>
                                    <span className="text-slate-400">Min Inv.</span>
                                </div>
                                <div className="flex items-center gap-1.5 text-slate-600">
                                    <MapPin className="w-4 h-4 text-blue-500" />
                                    <span className="text-slate-500">View Territories</span>
                                </div>
                            </div>
                        </Link>
                    ))}
                </div>
            ) : (
                searched && !loading && (
                    <div className="text-center py-12 bg-white rounded-xl border border-slate-100 border-dashed">
                        <p className="text-slate-500">No franchises found matching "{query}"</p>
                    </div>
                )
            )}
            
            {!searched && !loading && (
                <div className="text-center mt-20 opacity-50">
                    <Building className="w-16 h-16 mx-auto text-slate-200 mb-4" />
                    <p className="text-slate-400">Start typing to search the database</p>
                </div>
            )}
        </div>

      </div>
    </div>
  );
}

