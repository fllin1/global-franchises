'use client';

import { useState, useTransition } from 'react';
import { useRouter } from 'next/navigation';
import { createLead } from '@/app/actions';
import { Loader2, Sparkles } from 'lucide-react';

export default function NewLeadPage() {
  const router = useRouter();
  const [isPending, startTransition] = useTransition();
  const [error, setError] = useState<string | null>(null);

  async function handleSubmit(formData: FormData) {
    setError(null);
    startTransition(async () => {
      try {
        const lead = await createLead(formData);
        router.push(`/leads/${lead.id}`);
      } catch (e) {
        setError(e instanceof Error ? e.message : 'An unexpected error occurred');
      }
    });
  }

  return (
    <div className="max-w-2xl mx-auto p-6 md:p-12">
      <div className="mb-8 text-center">
        <div className="mx-auto w-16 h-16 bg-indigo-50 rounded-full flex items-center justify-center mb-4">
           <Sparkles className="w-8 h-8 text-indigo-600" />
        </div>
        <h1 className="text-3xl font-bold text-slate-900">New Lead Analysis</h1>
        <p className="text-slate-500 mt-2">Paste your raw notes below. AI will extract the profile and find matches.</p>
      </div>

      <form action={handleSubmit} className="space-y-6">
        <div>
          <label htmlFor="notes" className="block text-sm font-medium text-slate-700 mb-2">
            Broker Notes
          </label>
          <textarea
            id="notes"
            name="notes"
            rows={8}
            placeholder="Candidate John Smith, based in Austin TX. Has $150k liquid, interested in fitness..."
            className="w-full p-4 rounded-lg border border-slate-200 focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none shadow-sm text-base"
            required
          />
        </div>

        {error && (
          <div className="p-4 bg-red-50 text-red-700 rounded-lg text-sm">
            {error}
          </div>
        )}

        <button
          type="submit"
          disabled={isPending}
          className="w-full py-3 px-4 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-400 text-white font-bold rounded-lg flex items-center justify-center gap-2 transition-colors shadow-lg"
        >
          {isPending ? (
            <>
              <Loader2 className="w-5 h-5 animate-spin" />
              Analyzing & Creating Lead...
            </>
          ) : (
            'Analyze Lead'
          )}
        </button>
      </form>
    </div>
  );
}

