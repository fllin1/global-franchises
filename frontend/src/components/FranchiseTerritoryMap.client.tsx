'use client';

import { useState, useMemo, useEffect } from 'react';
import { MapPin, Navigation, ListFilter, Loader2 } from 'lucide-react';

interface TerritoryCheck {
    id: number;
    location_raw: string;
    state_code: string;
    city: string | null;
    zip_code: string | null;
    latitude: number | null;
    longitude: number | null;
    availability_status: string;
    radius_miles: number | null;
}

interface TerritoryData {
    franchise_id: number;
    territory_count: number;
    states: Record<string, Record<string, TerritoryCheck[]>>;
}

export default function FranchiseTerritoryMap({ data }: { data: TerritoryData }) {
    const [selectedState, setSelectedState] = useState<string | null>(null);
    const [selectedCity, setSelectedCity] = useState<string | null>(null);
    const [LeafletComponents, setLeafletComponents] = useState<any>(null);

    useEffect(() => {
        // Dynamic import to prevent SSR "window is not defined" error
        Promise.all([
            import('react-leaflet'),
            import('leaflet'),
            import('leaflet/dist/leaflet.css' as any) // Cast to any to avoid TS error if css module types missing
        ]).then(([RL, L]) => {
            // Fix Leaflet default icon issue
            // @ts-ignore
            delete L.Icon.Default.prototype._getIconUrl;
            L.Icon.Default.mergeOptions({
                iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
            });
            setLeafletComponents({ RL, L });
        }).catch(err => console.error("Failed to load map components", err));
    }, []);

    // Flatten data for map markers
    const markers = useMemo(() => {
        const list: TerritoryCheck[] = [];
        Object.values(data.states).forEach(cities => {
            Object.values(cities).forEach(checks => {
                checks.forEach(check => {
                    if (check.latitude && check.longitude) {
                        list.push(check);
                    }
                });
            });
        });
        return list;
    }, [data]);

    // Calculate center
    const mapCenter: [number, number] = useMemo(() => {
        return markers.length > 0 
            ? [markers[0].latitude!, markers[0].longitude!] 
            : [39.8283, -98.5795]; // US center fallback
    }, [markers]);

    // Filter visible list based on selection
    const filteredList = useMemo(() => {
        if (selectedCity && selectedState) {
            return data.states[selectedState]?.[selectedCity] || [];
        }
        if (selectedState) {
            const allInState: TerritoryCheck[] = [];
            Object.values(data.states[selectedState] || {}).forEach(arr => allInState.push(...arr));
            return allInState;
        }
        return [];
    }, [selectedState, selectedCity, data]);

    // Calculate dynamic center based on selection
    const currentCenter: [number, number] = useMemo(() => {
        if (filteredList.length > 0) {
            const firstValid = filteredList.find(m => m.latitude && m.longitude);
            if (firstValid) {
                return [firstValid.latitude!, firstValid.longitude!];
            }
        }
        return mapCenter;
    }, [filteredList, mapCenter]);

    if (!LeafletComponents) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-50 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Loading Map...
            </div>
        );
    }

    const { MapContainer, TileLayer, Marker, Popup, Circle, useMap } = LeafletComponents.RL;

    // Component to auto-center map - must be defined here to access useMap from the loaded module
    function MapUpdater({ center, zoom }: { center: [number, number]; zoom: number }) {
      const map = useMap();
      useEffect(() => {
          map.setView(center, zoom);
      }, [map, center, zoom]);
      return null;
    }

    return (
        <div className="flex h-full">
            {/* Sidebar List */}
            <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
                <div className="p-4 border-b border-slate-200 bg-slate-50">
                    <h3 className="font-bold text-slate-800 flex items-center gap-2">
                        <ListFilter className="w-4 h-4" />
                        {selectedCity ? selectedCity : (selectedState ? `All ${selectedState}` : 'All States')}
                    </h3>
                    {selectedState && (
                        <button 
                            onClick={() => { setSelectedState(null); setSelectedCity(null); }}
                            className="text-xs text-indigo-600 hover:underline mt-1"
                        >
                            Reset View
                        </button>
                    )}
                </div>
                
                <div className="flex-1 overflow-y-auto">
                    {!selectedState ? (
                        // Level 0: State List
                        Object.keys(data.states).sort().map(state => (
                            <button
                                key={state}
                                onClick={() => setSelectedState(state)}
                                className="w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 flex justify-between items-center group"
                            >
                                <span className="font-medium text-slate-700">{state}</span>
                                <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                                    {Object.values(data.states[state]).reduce((acc, val) => acc + val.length, 0)} checks
                                </span>
                            </button>
                        ))
                    ) : (
                        // Level 1/2: Territory Details
                        <div className="divide-y divide-slate-100">
                            {filteredList.map((item) => (
                                <div key={item.id} className="p-4 hover:bg-slate-50 transition-colors">
                                    <div className="flex items-start gap-3">
                                        <div className={`mt-1 w-2 h-2 rounded-full shrink-0 ${
                                            item.availability_status === 'Available' ? 'bg-emerald-500' : 'bg-slate-300'
                                        }`} />
                                        <div>
                                            <div className="text-sm font-medium text-slate-900">
                                                {item.city || item.location_raw}
                                            </div>
                                            {item.zip_code && (
                                                <div className="text-xs text-slate-500 font-mono mt-0.5">
                                                    Zip: {item.zip_code}
                                                </div>
                                            )}
                                            <div className="text-xs text-slate-400 mt-1">
                                                {item.availability_status}
                                            </div>
                                        </div>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {/* Map */}
            <div className="flex-1 relative bg-slate-100">
                 <MapContainer 
                    center={mapCenter} 
                    zoom={4} 
                    style={{ height: '100%', width: '100%' }}
                    scrollWheelZoom={true}
                >
                    <TileLayer
                        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
                        url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
                    />
                    
                    <MapUpdater 
                        center={currentCenter} 
                        zoom={selectedCity ? 10 : (selectedState ? 7 : 4)} 
                    />

                    {markers.map((marker) => (
                        <div key={marker.id}>
                            <Marker 
                                position={[marker.latitude!, marker.longitude!]}
                                eventHandlers={{
                                    click: () => {
                                        setSelectedState(marker.state_code);
                                        if (marker.city) setSelectedCity(marker.city);
                                    },
                                }}
                            >
                                <Popup>
                                    <div className="p-1">
                                        <strong className="block mb-1">{marker.city}, {marker.state_code}</strong>
                                        <div className="text-sm text-slate-600">{marker.availability_status}</div>
                                        {marker.zip_code && <div className="text-xs text-slate-400">Zip: {marker.zip_code}</div>}
                                    </div>
                                </Popup>
                            </Marker>
                            
                            {/* Radius Circle if applicable */}
                            {marker.radius_miles && (
                                <Circle
                                    center={[marker.latitude!, marker.longitude!]}
                                    radius={marker.radius_miles * 1609.34} // Miles to Meters
                                    pathOptions={{ 
                                        fillColor: marker.availability_status === 'Available' ? '#10b981' : '#94a3b8', 
                                        color: marker.availability_status === 'Available' ? '#059669' : '#64748b',
                                        weight: 1,
                                        opacity: 0.5,
                                        fillOpacity: 0.2
                                    }}
                                />
                            )}
                        </div>
                    ))}
                </MapContainer>
                
                {/* Floating Legend */}
                <div className="absolute bottom-6 right-6 bg-white p-3 rounded-lg shadow-lg z-[1000] text-xs">
                    <div className="flex items-center gap-2 mb-1">
                        <div className="w-3 h-3 rounded-full bg-emerald-500"></div>
                        <span>Available</span>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="w-3 h-3 rounded-full bg-slate-300"></div>
                        <span>Taken/Pending</span>
                    </div>
                </div>
            </div>
        </div>
    );
}
