'use client';

import { useState, useTransition, useMemo } from 'react';
import { Loader2, Sparkles, MapPin, Wallet } from 'lucide-react';
import { analyzeLead } from './actions';
import { MatchCard } from '@/components/MatchCard';
import { CoachingCard } from '@/components/CoachingCard';
import TerritoryMap from '@/components/TerritoryMap';
import { AnalysisResponse } from '@/types';

import Link from 'next/link';

const US_STATES = [
  "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
  "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
  "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
  "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
  "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY"
];

export default function Dashboard() {
  const [isPending, startTransition] = useTransition();
  const [response, setResponse] = useState<AnalysisResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [notes, setNotes] = useState<string>('');

  async function handleSubmit(formData: FormData) {
    setError(null);
    startTransition(async () => {
      try {
        const result = await analyzeLead(formData);
        setResponse(result);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'An unexpected error occurred');
      }
    });
  }

  const coverageStates = useMemo(() => {
    if (!response?.matches || response.matches.length === 0) return [];
    
    const covered = new Set<string>();
    
    response.matches.forEach(match => {
        // If unavailable_states is null/undefined, it's available everywhere
        if (!match.unavailable_states) {
            US_STATES.forEach(s => covered.add(s));
            return;
        }
        
        const unavailable = new Set(match.unavailable_states);
        US_STATES.forEach(state => {
            if (!unavailable.has(state)) {
                covered.add(state);
            }
        });
    });
    
    return Array.from(covered);
  }, [response]);

  return (
    <main className="min-h-screen bg-slate-50 flex flex-col md:flex-row">
      {/* Left Panel: Input (35%) */}
      <section className="w-full md:w-[35%] bg-white border-r border-slate-200 p-6 flex flex-col h-screen sticky top-0">
        <div className="mb-6">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-bold text-slate-900 flex items-center gap-2">
              <Sparkles className="w-5 h-5 text-indigo-600" />
              Broker Co-Pilot
            </h1>
          </div>
          <p className="text-sm text-slate-500 mt-1 mb-4">AI-Powered Lead Matching</p>
          
          <Link 
            href="/territory" 
            className="w-full flex items-center justify-center gap-2 px-4 py-2 bg-slate-50 text-slate-700 text-sm font-medium rounded-lg border border-slate-200 hover:bg-slate-100 hover:border-slate-300 transition-all mb-2"
          >
            <MapPin className="w-4 h-4 text-slate-500" />
            Explore Territories
          </Link>
        </div>

        <form action={handleSubmit} className="flex-1 flex flex-col">
          <div className="flex-1 flex flex-col mb-4">
            <label htmlFor="notes" className="text-sm font-medium text-slate-700 mb-2">
              Lead Notes
            </label>
            <textarea
              id="notes"
              name="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Paste call notes, email text, or resume details here..."
              className="flex-1 w-full p-4 rounded-lg border border-slate-200 bg-slate-50 focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none text-sm leading-relaxed text-slate-900 placeholder:text-slate-400 transition-all"
              required
            />
          </div>

          {error && (
            <div className="mb-4 p-3 text-sm text-red-600 bg-red-50 rounded-md border border-red-100">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={isPending}
            className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-medium rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm"
          >
            {isPending ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" />
                Analyzing Lead...
              </>
            ) : (
              <>
                Analyze Lead
              </>
            )}
          </button>
        </form>
      </section>

      {/* Right Panel: Intelligence (65%) */}
      <section className="w-full md:w-[65%] p-6 md:p-8 overflow-y-auto h-screen">
        
        {!response ? (
          // State A: Idle
          <div className="h-full flex flex-col items-center justify-center text-center text-slate-400"> 
            <div className="w-16 h-16 bg-slate-100 rounded-full flex items-center justify-center mb-4">
              <Sparkles className="w-8 h-8 text-slate-300" />
            </div>
            <h2 className="text-lg font-medium text-slate-600">Ready to Analyze</h2>
            <p className="max-w-sm mt-2">Paste your lead notes on the left to generate franchise matches and coaching insights.</p>
          </div>
        ) : (
          <div className="max-w-3xl mx-auto animate-in fade-in slide-in-from-bottom-4 duration-500">
            
            {/* Map Visualization - Only Visible when response exists */}
            <TerritoryMap 
                targetState={response?.profile?.state_code}
                coverageStates={coverageStates}
                isLoading={isPending}
            />

            {/* Header Stats */}
            <div className="flex flex-wrap gap-3 mb-8">
              {response.profile.liquidity !== null && (
                <div className="bg-white border border-slate-200 px-3 py-1.5 rounded-full flex items-center gap-2 text-sm shadow-sm">
                  <Wallet className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-500">Liquidity:</span>
                  <span className="font-medium text-slate-900">
                    ${response.profile.liquidity.toLocaleString()}
                  </span>
                </div>
              )}
              {response.profile.location && (
                <div className="bg-white border border-slate-200 px-3 py-1.5 rounded-full flex items-center gap-2 text-sm shadow-sm">
                  <MapPin className="w-4 h-4 text-slate-400" />
                  <span className="text-slate-500">Location:</span>
                  <span className="font-medium text-slate-900">
                    {response.profile.location}
                  </span>
                </div>
              )}
              {response.profile.extracted_tags?.map(tag => (
                 <div key={tag} className="bg-indigo-50 text-indigo-700 px-3 py-1.5 rounded-full text-sm font-medium">
                   {tag}
                 </div>
              ))}
            </div>

            {/* Content based on Status */}
            {response.status === 'tier_2' && (
              <CoachingCard 
                missingFields={response.missing_fields || []} 
                questions={response.coaching_questions || []} 
              />
            )}

            {response.status === 'tier_1' && (
              <div>
                <div className="flex items-center justify-between mb-6">
                  <h2 className="text-2xl font-bold text-slate-900">Top Franchise Matches</h2>
                  <span className="text-sm text-slate-500">Based on your notes</span>
                </div>
                <div className="space-y-4">
                  {response.matches?.map((match) => (
                    <MatchCard 
                      key={match.id} 
                      match={match}
                      targetState={response.profile.state_code}
                    />
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </section>
    </main>
  );
}
