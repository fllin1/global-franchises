'use client';

import { useState, useEffect, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import ComparisonTable from '@/components/ComparisonTable';
import { ComparisonResponse, Lead } from '@/types';
import { Loader2 } from 'lucide-react';
import { getLeadComparisonAnalysis } from '@/app/actions';

export default function ComparisonPage() {
  return (
    <Suspense fallback={<div className="flex justify-center p-10"><Loader2 className="animate-spin" /></div>}>
      <ComparisonContent />
    </Suspense>
  );
}

function ComparisonContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const [data, setData] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [leads, setLeads] = useState<Lead[]>([]);

  const idsParam = searchParams.get('ids');
  const leadIdParam = searchParams.get('leadId');

  useEffect(() => {
    // Load leads for selector
    fetch('http://localhost:8000/api/leads/?limit=50')
      .then(res => res.json())
      .then(setLeads)
      .catch(console.error);
  }, []);

  useEffect(() => {
    const fetchComparison = async () => {
      setLoading(true);
      try {
        let comparisonData = null;

        // 1. Try to load saved analysis if leadId is present
        if (leadIdParam) {
            const savedAnalysis = await getLeadComparisonAnalysis(parseInt(leadIdParam));
            if (savedAnalysis) {
                // If we have saved analysis, use it.
                // But wait, what if the user changed the selection?
                // For now, let's say if we have idsParam matching the saved one, or if no idsParam...
                // Actually the requirement is "I still have my comparison killer sheet".
                // So if we have saved analysis, we should probably prefer it unless the user explicitly requested different IDs.
                // But the user enters this page usually via the "Compare" button which passes IDs.
                
                // Let's adopt this logic:
                // If idsParam matches the IDs in saved analysis, use saved analysis (faster, preserved edits if any).
                // If idsParam is different, regenerate.
                // If no idsParam, try to use saved analysis.
                
                const savedIds = savedAnalysis.items.map((i: any) => i.franchise_id).sort().join(',');
                const paramIds = idsParam ? idsParam.split(',').map(n => parseInt(n)).sort().join(',') : '';

                if (!idsParam || savedIds === paramIds) {
                    comparisonData = savedAnalysis;
                }
            }
        }

        // 2. If no valid saved analysis, generate fresh
        if (!comparisonData) {
            if (!idsParam) {
                setError('No franchises selected for comparison.');
                setLoading(false);
                return;
            }

            const franchiseIds = idsParam.split(',').map(id => parseInt(id)).filter(n => !isNaN(n));
            
            if (franchiseIds.length === 0) {
              setError('Invalid franchise IDs.');
              setLoading(false);
              return;
            }

            // Fetch lead profile if leadId is present for personalization
            let leadProfile = null;
            if (leadIdParam) {
              const leadRes = await fetch(`http://localhost:8000/api/leads/${leadIdParam}`);
              if (leadRes.ok) {
                const leadData = await leadRes.json();
                leadProfile = leadData.profile_data;
              }
            }

            const res = await fetch('http://localhost:8000/api/franchises/compare', {
              method: 'POST',
              headers: { 'Content-Type': 'application/json' },
              body: JSON.stringify({ 
                franchise_ids: franchiseIds,
                lead_profile: leadProfile 
              })
            });

            if (!res.ok) throw new Error('Failed to generate comparison');
            comparisonData = await res.json();
        }

        setData(comparisonData);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    fetchComparison();
  }, [idsParam, leadIdParam]);

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50">
        <div className="text-center">
          <Loader2 className="w-10 h-10 text-indigo-600 animate-spin mx-auto mb-4" />
          <h2 className="text-xl font-semibold text-slate-900">Generating "Kill Sheet" Analysis...</h2>
          <p className="text-slate-500">Analyzing financials, territory, and fit.</p>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-slate-50 p-4">
        <div className="bg-white p-8 rounded-xl shadow-lg max-w-md text-center">
          <h2 className="text-red-600 font-bold text-xl mb-2">Error</h2>
          <p className="text-slate-600 mb-6">{error}</p>
          <button 
            onClick={() => router.back()}
            className="px-4 py-2 bg-slate-100 text-slate-700 rounded-md hover:bg-slate-200"
          >
            Go Back
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-slate-50">
        {data && (
            <ComparisonTable 
                data={data} 
                leads={leads}
                initialLeadId={leadIdParam ? parseInt(leadIdParam) : undefined}
                onClose={() => router.back()} 
            />
        )}
    </div>
  );
}
