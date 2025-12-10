'use client';

import { useState, useEffect } from 'react';
import { X, Search, Loader2, Building, DollarSign, Plus, Check } from 'lucide-react';
import { searchFranchises } from '@/app/franchises/actions';
import { FranchiseMatch } from '@/types';

interface AddFranchiseModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAdd: (franchise: FranchiseMatch) => void;
  existingMatchIds: string[];
}

export function AddFranchiseModal({ isOpen, onClose, onAdd, existingMatchIds }: AddFranchiseModalProps) {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<FranchiseMatch[]>([]);
  const [loading, setLoading] = useState(false);
  const [addingId, setAddingId] = useState<string | null>(null);

  // Debounced search
  useEffect(() => {
    if (!isOpen) return;
    
    const fetchFranchises = async () => {
      setLoading(true);
      try {
        const data = await searchFranchises(query);
        setResults(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };

    const timer = setTimeout(() => {
      fetchFranchises();
    }, 300);

    return () => clearTimeout(timer);
  }, [query, isOpen]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setQuery('');
      setAddingId(null);
    }
  }, [isOpen]);

  const handleAdd = async (franchise: FranchiseMatch) => {
    setAddingId(franchise.id);
    try {
      await onAdd(franchise);
    } finally {
      setAddingId(null);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm p-4 animate-in fade-in duration-200">
      <div className="bg-white dark:bg-slate-900 rounded-xl shadow-2xl w-full max-w-2xl max-h-[80vh] overflow-hidden flex flex-col animate-in zoom-in-95 duration-200">
        {/* Header */}
        <div className="px-6 py-4 border-b border-slate-100 dark:border-slate-800 flex items-center justify-between bg-slate-50 dark:bg-slate-800/50">
          <h2 className="text-lg font-bold text-slate-900 dark:text-white flex items-center gap-2">
            <Building className="w-5 h-5 text-indigo-600 dark:text-indigo-400" />
            Add Franchise to Recommendations
          </h2>
          <button 
            onClick={onClose} 
            className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300 transition-colors p-1 hover:bg-slate-200 dark:hover:bg-slate-700 rounded-full"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Search Bar */}
        <div className="p-4 border-b border-slate-100 dark:border-slate-800">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
              <Search className={`w-5 h-5 ${loading ? 'text-indigo-500' : 'text-slate-400 dark:text-slate-500'}`} />
            </div>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search franchises by name..."
              autoFocus
              className="block w-full pl-10 pr-4 py-2.5 bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg text-slate-900 dark:text-white placeholder-slate-400 dark:placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent text-sm"
            />
            {loading && (
              <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                <Loader2 className="w-5 h-5 text-indigo-500 animate-spin" />
              </div>
            )}
          </div>
        </div>

        {/* Results List */}
        <div className="flex-1 overflow-y-auto p-4 space-y-2">
          {results.length === 0 && !loading ? (
            <div className="text-center py-8 text-slate-500 dark:text-slate-400">
              <Building className="w-10 h-10 mx-auto mb-2 text-slate-300 dark:text-slate-600" />
              <p>No franchises found. Try a different search term.</p>
            </div>
          ) : (
            results.map((franchise) => {
              const isAlreadyAdded = existingMatchIds.includes(franchise.id);
              const isAdding = addingId === franchise.id;
              
              return (
                <div 
                  key={franchise.id}
                  className={`flex items-center gap-4 p-3 rounded-lg border transition-colors ${
                    isAlreadyAdded 
                      ? 'bg-slate-50 dark:bg-slate-800/50 border-slate-200 dark:border-slate-700 opacity-60'
                      : 'bg-white dark:bg-slate-800 border-slate-200 dark:border-slate-700 hover:border-indigo-300 dark:hover:border-indigo-700'
                  }`}
                >
                  {/* Logo placeholder */}
                  <div className="shrink-0 w-10 h-10 bg-slate-100 dark:bg-slate-700 rounded-lg flex items-center justify-center">
                    <Building className="w-5 h-5 text-slate-400 dark:text-slate-500" />
                  </div>
                  
                  {/* Info */}
                  <div className="flex-1 min-w-0">
                    <div className="font-medium text-slate-900 dark:text-white truncate">
                      {franchise.name}
                    </div>
                    <div className="flex items-center gap-3 text-sm text-slate-500 dark:text-slate-400">
                      {franchise.primary_category && (
                        <span>{franchise.primary_category}</span>
                      )}
                      {franchise.investment_min > 0 && (
                        <span className="flex items-center gap-1">
                          <DollarSign className="w-3.5 h-3.5" />
                          {franchise.investment_min.toLocaleString()}
                        </span>
                      )}
                    </div>
                  </div>
                  
                  {/* Add Button */}
                  <button
                    onClick={() => handleAdd(franchise)}
                    disabled={isAlreadyAdded || isAdding}
                    className={`flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors ${
                      isAlreadyAdded
                        ? 'bg-slate-100 dark:bg-slate-700 text-slate-400 dark:text-slate-500 cursor-not-allowed'
                        : isAdding
                        ? 'bg-indigo-100 dark:bg-indigo-900/30 text-indigo-400 cursor-wait'
                        : 'bg-indigo-600 text-white hover:bg-indigo-700'
                    }`}
                  >
                    {isAlreadyAdded ? (
                      <>
                        <Check className="w-4 h-4" />
                        Added
                      </>
                    ) : isAdding ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Adding...
                      </>
                    ) : (
                      <>
                        <Plus className="w-4 h-4" />
                        Add
                      </>
                    )}
                  </button>
                </div>
              );
            })
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-4 border-t border-slate-100 dark:border-slate-800 bg-slate-50 dark:bg-slate-800/50 flex justify-between items-center">
          <span className="text-sm text-slate-500 dark:text-slate-400">
            {results.length} franchise{results.length !== 1 ? 's' : ''} found
          </span>
          <button 
            onClick={onClose}
            className="px-4 py-2 bg-white dark:bg-slate-800 border border-slate-300 dark:border-slate-600 text-slate-700 dark:text-slate-300 font-medium rounded-lg hover:bg-slate-50 dark:hover:bg-slate-700 transition-colors text-sm"
          >
            Close
          </button>
        </div>
      </div>
    </div>
  );
}

