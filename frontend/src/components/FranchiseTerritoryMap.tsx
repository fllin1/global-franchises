'use client';

import dynamic from 'next/dynamic';
import { Loader2 } from 'lucide-react';

const FranchiseTerritoryMapClient = dynamic(
  () => import('./FranchiseTerritoryMap.client'),
  { 
    ssr: false,
    loading: () => (
      <div className="flex items-center justify-center h-full bg-slate-50 text-slate-400">
        <Loader2 className="w-6 h-6 animate-spin mr-2" />
        Loading Map...
      </div>
    )
  }
);

export default function FranchiseTerritoryMap(props: any) {
  return <FranchiseTerritoryMapClient {...props} />;
}
