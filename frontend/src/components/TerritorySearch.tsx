'use client';

import { Search, X, MapPin } from 'lucide-react';
import { useState, useEffect, useRef } from 'react';

interface TerritorySearchProps {
  selectedState: string | null;
  onStateSelect: (stateCode: string) => void;
  onClear: () => void;
}

const STATES = [
  { name: "Alabama", code: "AL" }, { name: "Alaska", code: "AK" }, { name: "Arizona", code: "AZ" },
  { name: "Arkansas", code: "AR" }, { name: "California", code: "CA" }, { name: "Colorado", code: "CO" },
  { name: "Connecticut", code: "CT" }, { name: "Delaware", code: "DE" }, { name: "Florida", code: "FL" },
  { name: "Georgia", code: "GA" }, { name: "Hawaii", code: "HI" }, { name: "Idaho", code: "ID" },
  { name: "Illinois", code: "IL" }, { name: "Indiana", code: "IN" }, { name: "Iowa", code: "IA" },
  { name: "Kansas", code: "KS" }, { name: "Kentucky", code: "KY" }, { name: "Louisiana", code: "LA" },
  { name: "Maine", code: "ME" }, { name: "Maryland", code: "MD" }, { name: "Massachusetts", code: "MA" },
  { name: "Michigan", code: "MI" }, { name: "Minnesota", code: "MN" }, { name: "Mississippi", code: "MS" },
  { name: "Missouri", code: "MO" }, { name: "Montana", code: "MT" }, { name: "Nebraska", code: "NE" },
  { name: "Nevada", code: "NV" }, { name: "New Hampshire", code: "NH" }, { name: "New Jersey", code: "NJ" },
  { name: "New Mexico", code: "NM" }, { name: "New York", code: "NY" }, { name: "North Carolina", code: "NC" },
  { name: "North Dakota", code: "ND" }, { name: "Ohio", code: "OH" }, { name: "Oklahoma", code: "OK" },
  { name: "Oregon", code: "OR" }, { name: "Pennsylvania", code: "PA" }, { name: "Rhode Island", code: "RI" },
  { name: "South Carolina", code: "SC" }, { name: "South Dakota", code: "SD" }, { name: "Tennessee", code: "TN" },
  { name: "Texas", code: "TX" }, { name: "Utah", code: "UT" }, { name: "Vermont", code: "VT" },
  { name: "Virginia", code: "VA" }, { name: "Washington", code: "WA" }, { name: "West Virginia", code: "WV" },
  { name: "Wisconsin", code: "WI" }, { name: "Wyoming", code: "WY" }
];

export default function TerritorySearch({ selectedState, onStateSelect, onClear }: TerritorySearchProps) {
  const [query, setQuery] = useState("");
  const [isOpen, setIsOpen] = useState(false);
  const wrapperRef = useRef<HTMLDivElement>(null);

  // Sync query with selected state if changed externally (e.g. via map click)
  useEffect(() => {
    if (selectedState) {
      const state = STATES.find(s => s.code === selectedState);
      if (state) setQuery(state.name);
    } else {
      setQuery("");
    }
  }, [selectedState]);

  // Filter states based on query
  const filteredStates = STATES.filter(state => 
    state.name.toLowerCase().includes(query.toLowerCase()) || 
    state.code.toLowerCase().includes(query.toLowerCase())
  );

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (wrapperRef.current && !wrapperRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    }
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (state: { name: string, code: string }) => {
    setQuery(state.name);
    onStateSelect(state.code);
    setIsOpen(false);
  };

  const handleClear = () => {
    setQuery("");
    onClear();
    setIsOpen(false);
  };

  return (
    <div className="relative w-full max-w-md" ref={wrapperRef}>
      <div className="relative">
        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
        <input
          type="text"
          value={query}
          onChange={(e) => {
            setQuery(e.target.value);
            setIsOpen(true);
          }}
          onFocus={() => setIsOpen(true)}
          placeholder="Search by state (e.g. Texas or TX)..."
          className="w-full pl-10 pr-10 py-2.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all shadow-sm"
        />
        {query && (
          <button 
            onClick={handleClear}
            className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Autocomplete Dropdown */}
      {isOpen && filteredStates.length > 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg border border-slate-100 shadow-lg max-h-60 overflow-y-auto z-50 py-1 animate-in fade-in zoom-in-95 duration-100">
          {filteredStates.map((state) => (
            <button
              key={state.code}
              onClick={() => handleSelect(state)}
              className="w-full text-left px-4 py-2.5 text-sm text-slate-700 hover:bg-indigo-50 hover:text-indigo-700 flex items-center justify-between group transition-colors"
            >
              <span className="font-medium">{state.name}</span>
              <span className="text-xs text-slate-400 group-hover:text-indigo-400 font-mono bg-slate-50 group-hover:bg-white px-1.5 py-0.5 rounded">
                {state.code}
              </span>
            </button>
          ))}
        </div>
      )}
      
      {isOpen && query && filteredStates.length === 0 && (
        <div className="absolute top-full left-0 right-0 mt-1 bg-white rounded-lg border border-slate-100 shadow-lg p-4 z-50 text-center text-sm text-slate-500">
          No states found matching "{query}"
        </div>
      )}
    </div>
  );
}
