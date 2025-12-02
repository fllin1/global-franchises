'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';
import Image from 'next/image';
import { Search, Network, Building, ArrowRight, Loader2, ExternalLink, Globe } from 'lucide-react';
import { getFamilyBrands } from '@/app/franchises/actions';
import { FamilyBrand } from '@/types';

export default function FamilyBrandsPage() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<FamilyBrand[]>([]);
  const [loading, setLoading] = useState(true);
  const [searched, setSearched] = useState(false);

  // Initial load and Debounce search
  useEffect(() => {
    const fetchFamilyBrands = async () => {
      setLoading(true);
      try {
        const data = await getFamilyBrands(query);
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
      fetchFamilyBrands();
    }, 300);

    return () => clearTimeout(timer);
  }, [query]);

  // Calculate stats
  const totalBrands = results.length;
  const totalFranchises = results.reduce((sum, fb) => sum + (fb.franchise_count || 0), 0);

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-900 p-8 pb-32">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-3 mb-4">
            <div className="p-2 bg-violet-100 dark:bg-violet-900/30 rounded-lg">
              <Network className="w-6 h-6 text-violet-600 dark:text-violet-400" />
            </div>
            <h1 className="text-3xl font-bold text-slate-900 dark:text-white">Family of Brands</h1>
          </div>
          <p className="text-slate-500 dark:text-slate-400 max-w-2xl">
            Parent brand entities that own and operate multiple franchise brands. 
            Explore the portfolio of each family to discover related franchise opportunities.
          </p>
          
          {/* Stats Bar */}
          <div className="mt-6 flex gap-6 text-sm">
            <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <Network className="w-4 h-4 text-violet-500" />
              <span className="text-slate-600 dark:text-slate-300">
                <span className="font-semibold text-slate-900 dark:text-white">{totalBrands}</span> Family Brands
              </span>
            </div>
            <div className="flex items-center gap-2 px-4 py-2 bg-white dark:bg-slate-800 rounded-lg border border-slate-200 dark:border-slate-700">
              <Building className="w-4 h-4 text-indigo-500" />
              <span className="text-slate-600 dark:text-slate-300">
                <span className="font-semibold text-slate-900 dark:text-white">{totalFranchises}</span> Linked Franchises
              </span>
            </div>
          </div>
        </div>

        {/* Search Bar */}
        <div className="relative max-w-2xl mb-8">
          <div className="absolute inset-y-0 left-0 pl-4 flex items-center pointer-events-none">
            <Search className={`w-5 h-5 ${loading ? 'text-violet-500' : 'text-slate-400 dark:text-slate-500'}`} />
          </div>
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="Search family brands..."
            className="block w-full pl-11 pr-4 py-3 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-violet-500 focus:border-transparent shadow-sm transition-all"
          />
          {loading && (
            <div className="absolute inset-y-0 right-0 pr-4 flex items-center">
              <Loader2 className="w-5 h-5 text-violet-500 animate-spin" />
            </div>
          )}
        </div>

        {/* Results Table */}
        {results.length > 0 ? (
          <div className="bg-white dark:bg-slate-800 rounded-xl border border-slate-200 dark:border-slate-700 shadow-sm overflow-hidden">
            <table className="min-w-full divide-y divide-slate-200 dark:divide-slate-700">
              <thead className="bg-slate-50 dark:bg-slate-800/50">
                <tr>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Family Brand
                  </th>
                  <th scope="col" className="px-6 py-4 text-center text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Franchises
                  </th>
                  <th scope="col" className="px-6 py-4 text-left text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Website
                  </th>
                  <th scope="col" className="px-6 py-4 text-right text-xs font-semibold text-slate-500 dark:text-slate-400 uppercase tracking-wider">
                    Action
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 dark:divide-slate-700">
                {results.map((familyBrand) => (
                  <tr 
                    key={familyBrand.id} 
                    className="hover:bg-slate-50 dark:hover:bg-slate-700/50 transition-colors"
                  >
                    <td className="px-6 py-4 whitespace-nowrap">
                      <Link href={`/family-brands/${familyBrand.id}`} className="flex items-center gap-4 group">
                        <div className="flex-shrink-0 w-12 h-12 bg-slate-100 dark:bg-slate-700 rounded-lg overflow-hidden flex items-center justify-center">
                          {familyBrand.logo_url ? (
                            <Image
                              src={familyBrand.logo_url}
                              alt={familyBrand.name}
                              width={48}
                              height={48}
                              className="object-contain"
                              onError={(e) => {
                                // Hide broken image and show fallback
                                (e.target as HTMLImageElement).style.display = 'none';
                              }}
                            />
                          ) : (
                            <Network className="w-6 h-6 text-slate-400 dark:text-slate-500" />
                          )}
                        </div>
                        <div>
                          <div className="font-semibold text-slate-900 dark:text-white group-hover:text-violet-600 dark:group-hover:text-violet-400 transition-colors">
                            {familyBrand.name}
                          </div>
                          {familyBrand.contact_name && (
                            <div className="text-xs text-slate-500 dark:text-slate-400">
                              Contact: {familyBrand.contact_name}
                            </div>
                          )}
                        </div>
                      </Link>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-center">
                      <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-sm font-medium bg-indigo-50 dark:bg-indigo-900/30 text-indigo-700 dark:text-indigo-300">
                        <Building className="w-3.5 h-3.5" />
                        {familyBrand.franchise_count || 0}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      {familyBrand.website_url ? (
                        <a
                          href={familyBrand.website_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1.5 text-sm text-slate-600 dark:text-slate-400 hover:text-violet-600 dark:hover:text-violet-400 transition-colors"
                        >
                          <Globe className="w-4 h-4" />
                          <span className="max-w-[180px] truncate">
                            {familyBrand.website_url.replace(/^https?:\/\//, '').replace(/\/$/, '')}
                          </span>
                          <ExternalLink className="w-3 h-3" />
                        </a>
                      ) : (
                        <span className="text-sm text-slate-400 dark:text-slate-500">—</span>
                      )}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right">
                      <Link
                        href={`/family-brands/${familyBrand.id}`}
                        className="inline-flex items-center gap-1.5 px-4 py-2 text-sm font-medium text-violet-600 dark:text-violet-400 hover:text-violet-700 dark:hover:text-violet-300 hover:bg-violet-50 dark:hover:bg-violet-900/20 rounded-lg transition-colors"
                      >
                        View Brands
                        <ArrowRight className="w-4 h-4" />
                      </Link>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          searched && !loading && (
            <div className="text-center py-12 bg-white dark:bg-slate-800 rounded-xl border border-slate-100 dark:border-slate-700 border-dashed">
              <Network className="w-12 h-12 text-slate-300 dark:text-slate-600 mx-auto mb-4" />
              <p className="text-slate-500 dark:text-slate-400">No family brands found.</p>
            </div>
          )
        )}
        
        {!searched && loading && (
          <div className="flex justify-center py-20">
            <Loader2 className="w-10 h-10 text-violet-500 animate-spin" />
          </div>
        )}
      </div>
    </div>
  );
}

