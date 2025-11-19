'use client';

import React, { memo } from 'react';
import { ComposableMap, Geographies, Geography } from 'react-simple-maps';
import { Loader2 } from 'lucide-react';

// US Map TopoJSON URL
const GEO_URL = "https://cdn.jsdelivr.net/npm/us-atlas@3/states-10m.json";

interface TerritoryMapProps {
  selectedState: string | null;
  onStateClick: (stateCode: string) => void;
  isLoading?: boolean;
}

// Mapping of state names to codes could be done here or in parent,
// but TopoJSON has state names. We need a map of Name -> Code or ID -> Code.
// US Atlas uses FIPS codes or names.
// We can use a lookup or just rely on the name if backend accepts name, but backend expects Code.
// Let's use a dictionary for Name -> Code.

const STATE_NAME_TO_CODE: Record<string, string> = {
  "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR", "California": "CA",
  "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE", "Florida": "FL", "Georgia": "GA",
  "Hawaii": "HI", "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
  "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME", "Maryland": "MD",
  "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN", "Mississippi": "MS", "Missouri": "MO",
  "Montana": "MT", "Nebraska": "NE", "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ",
  "New Mexico": "NM", "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
  "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI", "South Carolina": "SC",
  "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX", "Utah": "UT", "Vermont": "VT",
  "Virginia": "VA", "Washington": "WA", "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
};

const TerritoryMap = ({ selectedState, onStateClick, isLoading }: TerritoryMapProps) => {
  return (
    <div className="w-full h-full bg-slate-50 rounded-xl overflow-hidden relative shadow-inner border border-slate-200">
      {isLoading && (
        <div className="absolute inset-0 bg-white/50 backdrop-blur-[1px] z-10 flex items-center justify-center">
          <Loader2 className="w-8 h-8 text-indigo-600 animate-spin" />
        </div>
      )}
      
      <ComposableMap 
        projection="geoAlbersUsa" 
        projectionConfig={{ scale: 1000 }} // Adjust scale for better fit
        className="w-full h-full"
      >
        <Geographies geography={GEO_URL}>
          {({ geographies }) =>
            geographies.map((geo) => {
              const stateName = geo.properties.name;
              const stateCode = STATE_NAME_TO_CODE[stateName];
              const isSelected = selectedState === stateCode;

              return (
                <Geography
                  key={geo.rsmKey}
                  geography={geo}
                  onClick={() => stateCode && onStateClick(stateCode)}
                  style={{
                    default: {
                      fill: isSelected ? "#6366f1" : "#e2e8f0", // indigo-500 vs slate-200
                      stroke: "#fff",
                      strokeWidth: 0.75,
                      outline: "none",
                      transition: "all 0.3s ease"
                    },
                    hover: {
                      fill: isSelected ? "#4f46e5" : "#cbd5e1", // indigo-600 vs slate-300
                      stroke: "#fff",
                      strokeWidth: 0.75,
                      outline: "none",
                      cursor: "pointer"
                    },
                    pressed: {
                      fill: "#4338ca", // indigo-700
                      stroke: "#fff",
                      outline: "none"
                    }
                  }}
                />
              );
            })
          }
        </Geographies>
      </ComposableMap>

      {/* Legend / Instructions overlay */}
      <div className="absolute bottom-4 left-4 bg-white/90 backdrop-blur p-3 rounded-lg shadow-sm border border-slate-100 text-xs text-slate-500">
        <p className="font-medium text-slate-700 mb-1">Interactive Map</p>
        <div className="flex items-center gap-2 mb-1">
          <div className="w-3 h-3 bg-indigo-500 rounded-sm"></div>
          <span>Selected</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 bg-slate-200 rounded-sm"></div>
          <span>Available</span>
        </div>
      </div>
    </div>
  );
};

export default memo(TerritoryMap);
