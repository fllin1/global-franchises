import { FranchiseMatch } from '@/types';
import { Building2, DollarSign, TrendingUp } from 'lucide-react';

interface MatchCardProps {
  match: FranchiseMatch;
}

export function MatchCard({ match }: MatchCardProps) {
  const isHighMatch = match.match_score >= 90;
  const isMediumMatch = match.match_score >= 80 && match.match_score < 90;
  
  const scoreColor = isHighMatch
    ? 'bg-green-100 text-green-800'
    : isMediumMatch
    ? 'bg-yellow-100 text-yellow-800'
    : 'bg-slate-100 text-slate-800';

  return (
    <div className="bg-white rounded-lg border border-slate-200 shadow-sm p-5 mb-4 hover:shadow-md transition-shadow">
      <div className="flex justify-between items-start mb-3">
        <div>
          <h3 className="text-lg font-semibold text-slate-900 flex items-center gap-2">
            <Building2 className="w-5 h-5 text-indigo-600" />
            {match.name}
          </h3>
          <p className="text-sm text-slate-500 mt-1 line-clamp-1">{match.description}</p>
        </div>
        <div className={`px-3 py-1 rounded-full text-sm font-bold ${scoreColor}`}>
          {match.match_score}% Match
        </div>
      </div>

      <div className="flex items-center gap-2 text-sm text-slate-600 mb-4">
        <div className="flex items-center gap-1 bg-slate-50 px-2 py-1 rounded">
          <DollarSign className="w-4 h-4 text-slate-400" />
          <span>Min Investment: </span>
          <span className="font-medium text-slate-900">
            ${match.investment_min.toLocaleString()}
          </span>
        </div>
      </div>

      <div className="bg-slate-50 p-4 rounded-md border border-slate-100">
        <h4 className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2 flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          Why this match?
        </h4>
        <p className="text-sm text-slate-700 leading-relaxed">
          {match.why_narrative}
        </p>
      </div>
    </div>
  );
}

