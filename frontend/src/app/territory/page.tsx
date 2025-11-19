'use client';

import { useState, useEffect, useTransition } from 'react';
import { searchFranchisesByLocation } from '../actions';
import { TerritoryFranchise } from '@/types';
import TerritoryMap from '@/components/TerritoryMap';
import TerritorySearch from '@/components/TerritorySearch';
import TerritoryFranchiseList from '@/components/TerritoryFranchiseList';
import Link from 'next/link';
import { ArrowLeft, Map as MapIcon, LayoutGrid } from 'lucide-react';

export default function TerritoryPage() {
  const [selectedState, setSelectedState] = useState<string | null>(null);
  const [franchises, setFranchises] = useState<TerritoryFranchise[]>([]);
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  const handleStateSelect = (stateCode: string) => {
    if (stateCode === selectedState) return; // Avoid duplicate fetch
    
    setSelectedState(stateCode);
    setError(null);
    
    startTransition(async () => {
      try {
        const results = await searchFranchisesByLocation(stateCode);
        setFranchises(results);
      } catch (e) {
        console.error(e);
        setError('Failed to load franchises for this territory.');
        setFranchises([]);
      }
    });
  };

  const handleClear = () => {
    setSelectedState(null);
    setFranchises([]);
    setError(null);
  };

  return (
    <main className="h-screen w-full overflow-hidden flex flex-col bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shrink-0 z-20">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          
          {/* Left Column: Title & Navigation */}
          <div className="flex-1 flex items-center justify-start">
            <div className="flex items-center gap-4">
              <Link 
                href="/" 
                className="p-2 -ml-2 text-slate-400 hover:text-slate-700 hover:bg-slate-50 rounded-full transition-colors"
                title="Back to Dashboard"
              >
                <ArrowLeft className="w-5 h-5" />
              </Link>
              <div className="flex items-center gap-2">
                <div className="bg-indigo-600 p-1.5 rounded-lg">
                  <MapIcon className="w-5 h-5 text-white" />
                </div>
                <h1 className="text-lg font-bold text-slate-900">Territory Explorer</h1>
              </div>
            </div>
          </div>

          {/* Center Column: Search Bar */}
          <div className="flex items-center justify-center w-full max-w-md mx-4">
            <TerritorySearch 
              selectedState={selectedState}
              onStateSelect={handleStateSelect}
              onClear={handleClear}
            />
          </div>

          {/* Right Column: Empty Spacer for Balance */}
          <div className="flex-1"></div>
          
        </div>
      </header>

      {/* Main Content - Split View Adjusted */}
      <div className="flex-1 min-h-0 flex flex-col lg:flex-row">
        
        {/* Left: Map (65% - Predominant) */}
        <section className="flex-1 lg:flex-[1.8] relative bg-white border-b lg:border-b-0 lg:border-r border-slate-200 z-10">
          <div className="absolute inset-0 flex flex-col p-4 lg:p-6">
            <div className="mb-4 flex justify-between items-center shrink-0">
              <h2 className="font-semibold text-slate-900 flex items-center gap-2">
                <MapIcon className="w-4 h-4 text-slate-400" />
                Interactive Map
              </h2>
              <span className="text-xs text-slate-400">Click a state to filter</span>
            </div>
            {/* Flex-1 ensures map takes all remaining vertical space */}
            <div className="flex-1 min-h-0 relative">
              <TerritoryMap 
                selectedState={selectedState}
                onStateClick={handleStateSelect}
                isLoading={isPending}
              />
            </div>
          </div>
        </section>

        {/* Right: Listings (35%) */}
        <section className="flex-1 lg:flex-[1] bg-slate-50 flex flex-col border-l border-slate-200 shadow-[-4px_0_15px_-3px_rgba(0,0,0,0.05)] min-w-0">
          <div className="p-3 lg:p-4 border-b border-slate-100 bg-slate-50 shrink-0">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900 flex items-center gap-2">
                  {selectedState ? (
                    <>
                      Franchises in <span className="text-indigo-600">{selectedState}</span>
                      <span className="ml-2 bg-indigo-50 text-indigo-700 text-xs px-2 py-0.5 rounded-full font-medium">
                        {franchises.length}
                      </span>
                    </>
                  ) : (
                    'Available Franchises'
                  )}
                </h2>
                <p className="text-xs text-slate-500 mt-0.5">
                  {selectedState 
                    ? `Showing opportunities available in this territory.` 
                    : 'Select a state on the map.'}
                </p>
              </div>
              <div className="hidden md:flex gap-2">
                <button className="p-1.5 bg-white border border-slate-200 rounded-lg text-slate-400 hover:text-slate-600 shadow-sm">
                  <LayoutGrid className="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="flex-1 overflow-y-auto p-3 lg:p-4 min-h-0">
            {error ? (
              <div className="bg-red-50 border border-red-100 text-red-600 p-4 rounded-xl text-sm">
                {error}
              </div>
            ) : (
              // Override grid cols for narrower column
              <div className="territory-list-container">
                 <TerritoryFranchiseList 
                  franchises={franchises} 
                  isLoading={isPending} 
                  stateCode={selectedState}
                />
              </div>
            )}
          </div>
        </section>
      </div>
    </main>
  );
}
