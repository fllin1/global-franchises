import { AlertTriangle, CheckCircle2, MessageCircleQuestion } from 'lucide-react';

interface CoachingCardProps {
  missingFields?: string[];
  questions?: string[];
}

export function CoachingCard({ missingFields = [], questions = [] }: CoachingCardProps) {
  const hasMissingFields = missingFields.length > 0;
  const hasQuestions = questions.length > 0;

  if (!hasMissingFields && !hasQuestions) {
    return null;
  }

  return (
    <div className="space-y-6">
      {/* Missing Fields Section */}
      {hasMissingFields && (
        <div className="bg-amber-50 border border-amber-200 rounded-lg p-4">
          <h3 className="text-amber-800 font-medium flex items-center gap-2 mb-3">
            <AlertTriangle className="w-5 h-5" />
            Profile Incomplete - Cannot Match Yet
          </h3>
          <div className="space-y-2">
            <p className="text-sm text-amber-700 mb-2">We need more information about:</p>
            <div className="flex flex-wrap gap-2">
              {missingFields.map((field) => (
                <span
                  key={field}
                  className="bg-white text-amber-800 border border-amber-200 px-3 py-1 rounded-full text-xs font-medium"
                >
                  {field}
                </span>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Coaching Questions Section */}
      {hasQuestions && (
        <div className="bg-white border border-slate-200 rounded-lg shadow-sm overflow-hidden">
          <div className="bg-slate-50 px-4 py-3 border-b border-slate-100">
            <h3 className="font-semibold text-slate-800 flex items-center gap-2">
              <MessageCircleQuestion className="w-5 h-5 text-indigo-600" />
              Next Best Questions
            </h3>
          </div>
          <div className="p-4">
            <ul className="space-y-3">
              {questions.map((question, index) => (
                <li key={index} className="flex items-start gap-3 text-slate-700">
                  <CheckCircle2 className="w-5 h-5 text-slate-300 flex-shrink-0 mt-0.5" />
                  <span className="text-sm leading-relaxed">{question}</span>
                </li>
              ))}
            </ul>
          </div>
        </div>
      )}
    </div>
  );
}
