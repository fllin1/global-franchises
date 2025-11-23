import { FranchiseMatch } from '@/types';
import { Building2, DollarSign, TrendingUp, CheckCircle2 } from 'lucide-react';

interface MatchCardProps {
  match: FranchiseMatch;
  targetState?: string | null;
  onClick?: () => void;
  onViewDetails?: () => void;
}

export function MatchCard({ match, targetState, onClick, onViewDetails }: MatchCardProps) {
  const isHighMatch = match.match_score >= 90;
  const isMediumMatch = match.match_score >= 80 && match.match_score < 90;
  
  const handleClick = onClick || onViewDetails;

  const scoreColor = isHighMatch
    ? 'bg-green-100 text-green-800 border-green-200'
    : isMediumMatch
    ? 'bg-yellow-100 text-yellow-800 border-yellow-200'
    : 'bg-slate-100 text-slate-800 border-slate-200';

  // Conditional checks
  // We want to show investment if it's a number. Even if 0, it might be better to show "N/A" or something 
  // if we want it explicitly, but usually 0 means missing data in this context.
  // Let's make sure we have a fallback for display.
  const investmentValue = match.investment_min;
  const hasInvestment = typeof investmentValue === 'number' && investmentValue > 0;
  
  const showMatchScore = typeof match.match_score === 'number' && !isNaN(match.match_score);
  const showDescription = match.description && match.description !== 'No description available';

  return (
    <div 
        onClick={handleClick}
        className={`bg-white rounded-lg border border-slate-200 shadow-sm hover:shadow-md hover:border-indigo-200 transition-all p-3 ${
            handleClick ? 'cursor-pointer' : ''
        }`}
    >
      {/* Row 1: Header Info */}
      <div className="flex items-center justify-between gap-3 mb-2">
        <div className="flex items-center gap-2 min-w-0">
          <Building2 className="w-4 h-4 text-indigo-600 shrink-0" />
          <h3 className="text-sm font-semibold text-slate-900 truncate">
            {match.name || 'Unknown Franchise'}
          </h3>
          {showDescription && (
             <span className="text-xs text-slate-400 truncate hidden sm:inline border-l border-slate-200 pl-2">
               {match.description}
             </span>
          )}
        </div>

        <div className="flex items-center gap-2 shrink-0">
           {/* Investment Badge - Always show if we have data, or maybe a placeholder? 
               The user complained they don't see it. If it's 0, we might want to show "Info N/A" */}
           {hasInvestment ? (
            <div className="flex items-center gap-1 text-xs text-slate-600 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
              <DollarSign className="w-3 h-3 text-slate-400" />
              <span className="font-medium">${investmentValue.toLocaleString()}</span>
            </div>
           ) : (
            <div className="flex items-center gap-1 text-xs text-slate-400 bg-slate-50 px-2 py-0.5 rounded border border-slate-100">
              <DollarSign className="w-3 h-3 text-slate-400" />
              <span className="font-medium">Inv. TBD</span>
            </div>
           )}

           {/* Match Score Badge */}
           {showMatchScore && (
             <div className={`px-2 py-0.5 rounded text-xs font-bold border ${scoreColor}`}>
               {match.match_score}%
             </div>
           )}
        </div>
      </div>

      {/* Row 2: Narrative */}
      <div className="flex gap-2 items-start">
         <div className="mt-0.5 shrink-0">
            <TrendingUp className="w-3.5 h-3.5 text-indigo-400" />
         </div>
         <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">
           {match.why_narrative || match.description || 'No details available.'}
         </p>
      </div>

      {/* Optional: Availability Tag (if passed) */}
      {targetState && (
        <div className="mt-2 flex justify-end">
           <div className="flex items-center gap-1 text-[10px] font-medium text-emerald-700 bg-emerald-50 px-1.5 py-0.5 rounded border border-emerald-100">
             <CheckCircle2 className="w-3 h-3" />
             Available in {targetState}
           </div>
        </div>
      )}
    </div>
  );
}
