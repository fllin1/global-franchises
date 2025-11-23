'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { getLeadComparisonSelections, saveLeadComparisonSelections } from '@/app/actions';

interface ComparisonContextType {
  selectedIds: string[];
  addToComparison: (id: string) => void;
  removeFromComparison: (id: string) => void;
  clearComparison: () => void;
  isInComparison: (id: string) => boolean;
  toggleComparison: (id: string) => void;
  count: number;
  leadId: number | null;
  setLeadContext: (id: number | null) => void;
  loadLeadSelections: (id: number) => Promise<void>;
  saveLeadSelections: (id: number) => Promise<void>;
}

const ComparisonContext = createContext<ComparisonContextType | undefined>(undefined);

export function ComparisonProvider({ children }: { children: React.ReactNode }) {
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [isInitialized, setIsInitialized] = useState(false);
  const [leadId, setLeadId] = useState<number | null>(null);

  // Initialize from localStorage (Global context)
  useEffect(() => {
    if (typeof window !== 'undefined' && !leadId) {
      const stored = localStorage.getItem('franchise_comparison');
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          if (Array.isArray(parsed)) {
            setSelectedIds(parsed);
          }
        } catch (e) {
          console.error('Failed to parse comparison state', e);
        }
      }
      setIsInitialized(true);
    }
  }, [leadId]);

  // Sync to localStorage (Global context)
  useEffect(() => {
    if (isInitialized && typeof window !== 'undefined' && !leadId) {
      localStorage.setItem('franchise_comparison', JSON.stringify(selectedIds));
    }
  }, [selectedIds, isInitialized, leadId]);

  const loadLeadSelections = async (id: number) => {
    try {
        const selections = await getLeadComparisonSelections(id);
        setSelectedIds(selections.map(String));
        setIsInitialized(true);
    } catch (e) {
        console.error('Failed to load lead selections', e);
    }
  };

  const saveLeadSelections = async (id: number) => {
      if (selectedIds.length === 0) return;
      try {
          await saveLeadComparisonSelections(id, selectedIds.map(Number));
      } catch (e) {
          console.error('Failed to save lead selections', e);
      }
  };

  const setLeadContext = (id: number | null) => {
      setLeadId(id);
      if (id === null) {
          // Revert to global storage logic (handled by useEffect)
          setIsInitialized(false); // Trigger re-read from localStorage
      } else {
          // Lead context is handled by loadLeadSelections call in the page component
          setSelectedIds([]); 
      }
  };

  const addToComparison = (id: string) => {
    setSelectedIds(prev => {
      if (prev.includes(id)) return prev;
      if (prev.length >= 10) return prev; // Limit to 10
      return [...prev, id];
    });
  };

  const removeFromComparison = (id: string) => {
    setSelectedIds(prev => prev.filter(pid => pid !== id));
  };

  const clearComparison = () => {
    setSelectedIds([]);
  };

  const isInComparison = (id: string) => {
    return selectedIds.includes(id);
  };

  const toggleComparison = (id: string) => {
    if (selectedIds.includes(id)) {
      removeFromComparison(id);
    } else {
      addToComparison(id);
    }
  };

  // Auto-save when in lead context and selections change
  useEffect(() => {
      if (leadId && isInitialized) {
          const timer = setTimeout(() => {
              saveLeadSelections(leadId);
          }, 1000); // Debounce save
          return () => clearTimeout(timer);
      }
  }, [selectedIds, leadId, isInitialized]);

  return (
    <ComparisonContext.Provider value={{
      selectedIds,
      addToComparison,
      removeFromComparison,
      clearComparison,
      isInComparison,
      toggleComparison,
      count: selectedIds.length,
      leadId,
      setLeadContext,
      loadLeadSelections,
      saveLeadSelections
    }}>
      {children}
    </ComparisonContext.Provider>
  );
}

export function useComparison() {
  const context = useContext(ComparisonContext);
  if (context === undefined) {
    throw new Error('useComparison must be used within a ComparisonProvider');
  }
  return context;
}
