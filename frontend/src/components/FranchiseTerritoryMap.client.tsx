'use client';

import { useState, useMemo, useEffect, useCallback } from 'react';
import { ListFilter, Loader2, ChevronRight, Home, Map as MapIcon } from 'lucide-react';

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

interface BreadcrumbItem {
    label: string;
    type: 'all' | 'state' | 'city' | 'zip';
    value?: string;
}

export default function FranchiseTerritoryMapClient({ data }: { data: TerritoryData | null }) {
    const [selectedState, setSelectedState] = useState<string | null>(null);
    const [selectedCity, setSelectedCity] = useState<string | null>(null);
    const [selectedZip, setSelectedZip] = useState<string | null>(null);
    const [LeafletComponents, setLeafletComponents] = useState<any>(null);
    const [mapKey, setMapKey] = useState(0);

    useEffect(() => {
        Promise.all([
            import('react-leaflet'),
            import('leaflet'),
            import('leaflet/dist/leaflet.css' as any)
        ]).then(([RL, L]) => {
            // @ts-ignore
            delete L.Icon.Default.prototype._getIconUrl;
            L.Icon.Default.mergeOptions({
                iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
            });
            setLeafletComponents({ RL, L });
            setMapKey(prev => prev + 1);
        }).catch(err => console.error("Failed to load map components", err));
    }, []);

    const breadcrumbs: BreadcrumbItem[] = useMemo(() => {
        const items: BreadcrumbItem[] = [{ label: 'All States', type: 'all' }];
        if (selectedState) items.push({ label: selectedState, type: 'state', value: selectedState });
        if (selectedCity) items.push({ label: selectedCity, type: 'city', value: selectedCity });
        if (selectedZip) items.push({ label: 'ZIP: ' + selectedZip, type: 'zip', value: selectedZip });
        return items;
    }, [selectedState, selectedCity, selectedZip]);

    const handleBreadcrumbClick = useCallback((item: BreadcrumbItem) => {
        switch (item.type) {
            case 'all':
                setSelectedState(null);
                setSelectedCity(null);
                setSelectedZip(null);
                break;
            case 'state':
                setSelectedCity(null);
                setSelectedZip(null);
                break;
            case 'city':
                setSelectedZip(null);
                break;
        }
    }, []);

    const markers = useMemo(() => {
        if (!data?.states) return [];
        const list: TerritoryCheck[] = [];
        try {
            Object.values(data.states).forEach(cities => {
                if (cities && typeof cities === 'object') {
                    Object.values(cities).forEach(checks => {
                        if (Array.isArray(checks)) {
                            checks.forEach(check => {
                                if (check?.latitude && check?.longitude) list.push(check);
                            });
                        }
                    });
                }
            });
        } catch (e) { console.error('Error processing territory markers:', e); }
        return list;
    }, [data]);

    const mapCenter: [number, number] = useMemo(() => {
        return markers.length > 0 ? [markers[0].latitude!, markers[0].longitude!] : [39.8283, -98.5795];
    }, [markers]);

    const filteredList = useMemo(() => {
        if (!data?.states) return [];
        if (selectedZip && selectedCity && selectedState) {
            return (data.states[selectedState]?.[selectedCity] || []).filter(c => c.zip_code === selectedZip);
        }
        if (selectedCity && selectedState) return data.states[selectedState]?.[selectedCity] || [];
        if (selectedState) {
            const allInState: TerritoryCheck[] = [];
            const stateCities = data.states[selectedState];
            if (stateCities) Object.values(stateCities).forEach(arr => { if (Array.isArray(arr)) allInState.push(...arr); });
            return allInState;
        }
        return [];
    }, [selectedState, selectedCity, selectedZip, data]);

    const availableZips = useMemo(() => {
        if (!selectedCity || !selectedState || !data?.states) return [];
        const cityChecks = data.states[selectedState]?.[selectedCity] || [];
        const zips = new Set(cityChecks.map(c => c.zip_code).filter(Boolean));
        return Array.from(zips) as string[];
    }, [selectedCity, selectedState, data]);

    const currentCenter: [number, number] = useMemo(() => {
        if (filteredList.length > 0) {
            const firstValid = filteredList.find(m => m.latitude && m.longitude);
            if (firstValid) return [firstValid.latitude!, firstValid.longitude!];
        }
        return mapCenter;
    }, [filteredList, mapCenter]);

    if (!data?.states || Object.keys(data.states).length === 0) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-50 text-slate-500">
                <div className="text-center">
                    <MapIcon className="w-12 h-12 mx-auto mb-3 text-slate-300" />
                    <p className="font-medium">No territory data available</p>
                    <p className="text-sm text-slate-400 mt-1">Territory checks will appear here once added</p>
                </div>
            </div>
        );
    }

    if (!LeafletComponents) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-50 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Loading Map...
            </div>
        );
    }

    const { MapContainer, TileLayer, Marker, Popup, Circle, useMap } = LeafletComponents.RL;

    function MapUpdater({ center, zoom }: { center: [number, number]; zoom: number }) {
        const map = useMap();
        useEffect(() => { map.setView(center, zoom); }, [map, center, zoom]);
        return null;
    }

    const currentZoom = selectedZip ? 12 : (selectedCity ? 10 : (selectedState ? 7 : 4));

    return (
        <div className="flex h-full flex-col">
            <div className="bg-white border-b border-slate-200 px-4 py-2">
                <nav className="flex items-center text-sm">
                    {breadcrumbs.map((crumb, idx) => (
                        <div key={idx} className="flex items-center">
                            {idx > 0 && <ChevronRight className="w-4 h-4 mx-1 text-slate-300" />}
                            <button
                                onClick={() => handleBreadcrumbClick(crumb)}
                                className={'flex items-center gap-1 px-2 py-1 rounded transition-colors ' + (idx === breadcrumbs.length - 1 ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100')}
                            >
                                {idx === 0 && <Home className="w-3.5 h-3.5" />}
                                {crumb.label}
                            </button>
                        </div>
                    ))}
                </nav>
            </div>

            <div className="flex flex-1 min-h-0">
                <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
                    <div className="p-4 border-b border-slate-200 bg-slate-50">
                        <h3 className="font-bold text-slate-800 flex items-center gap-2">
                            <ListFilter className="w-4 h-4" />
                            {selectedZip ? 'ZIP: ' + selectedZip : selectedCity ? selectedCity : (selectedState ? 'All ' + selectedState : 'Select a State')}
                        </h3>
                        <p className="text-xs text-slate-500 mt-1">
                            {selectedState ? filteredList.length + ' territory check' + (filteredList.length !== 1 ? 's' : '') : Object.keys(data.states).length + ' states with data'}
                        </p>
                    </div>
                    
                    <div className="flex-1 overflow-y-auto">
                        {!selectedState ? (
                            Object.keys(data.states).sort().map(state => (
                                <button key={state} onClick={() => setSelectedState(state)} className="w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 flex justify-between items-center group">
                                    <span className="font-medium text-slate-700">{state}</span>
                                    <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                                        {Object.values(data.states[state]).reduce((acc, val) => acc + val.length, 0)} checks
                                    </span>
                                </button>
                            ))
                        ) : !selectedCity ? (
                            Object.keys(data.states[selectedState] || {}).sort().map(city => (
                                <button key={city} onClick={() => setSelectedCity(city)} className="w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 flex justify-between items-center group">
                                    <span className="font-medium text-slate-700">{city}</span>
                                    <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                                        {data.states[selectedState][city].length} checks
                                    </span>
                                </button>
                            ))
                        ) : availableZips.length > 1 && !selectedZip ? (
                            <>
                                <button onClick={() => setSelectedZip(null)} className="w-full text-left px-4 py-3 border-b border-slate-200 bg-slate-50 hover:bg-slate-100 flex justify-between items-center">
                                    <span className="font-medium text-indigo-600">View All {selectedCity}</span>
                                    <span className="text-xs bg-indigo-100 text-indigo-600 px-2 py-1 rounded-full">{filteredList.length} checks</span>
                                </button>
                                {availableZips.sort().map(zip => (
                                    <button key={zip} onClick={() => setSelectedZip(zip)} className="w-full text-left px-4 py-3 border-b border-slate-100 hover:bg-slate-50 flex justify-between items-center group">
                                        <span className="font-medium text-slate-700 font-mono">{zip}</span>
                                        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                                            {filteredList.filter(c => c.zip_code === zip).length} checks
                                        </span>
                                    </button>
                                ))}
                            </>
                        ) : (
                            <div className="divide-y divide-slate-100">
                                {filteredList.map((item) => (
                                    <div key={item.id} className="p-4 hover:bg-slate-50 transition-colors">
                                        <div className="flex items-start gap-3">
                                            <div className={'mt-1 w-2.5 h-2.5 rounded-full shrink-0 ' + (item.availability_status === 'Available' ? 'bg-emerald-500' : 'bg-rose-400')} />
                                            <div className="flex-1 min-w-0">
                                                <div className="text-sm font-medium text-slate-900">{item.city || item.location_raw || 'Unknown Location'}</div>
                                                {item.zip_code && <div className="text-xs text-slate-500 font-mono mt-0.5">ZIP: {item.zip_code}</div>}
                                                <div className={'text-xs mt-1 font-medium ' + (item.availability_status === 'Available' ? 'text-emerald-600' : 'text-rose-500')}>{item.availability_status}</div>
                                                {item.radius_miles && <div className="text-xs text-slate-400 mt-1">{item.radius_miles} mile radius</div>}
                                            </div>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>

                <div className="flex-1 relative bg-slate-100">
                    <MapContainer key={mapKey} center={mapCenter} zoom={4} style={{ height: '100%', width: '100%' }} scrollWheelZoom={true}>
                        <TileLayer attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors' url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
                        <MapUpdater center={currentCenter} zoom={currentZoom} />
                        {markers.map((marker) => (
                            <div key={marker.id}>
                                <Marker position={[marker.latitude!, marker.longitude!]} eventHandlers={{ click: () => { setSelectedState(marker.state_code); if (marker.city) setSelectedCity(marker.city); if (marker.zip_code) setSelectedZip(marker.zip_code); } }}>
                                    <Popup>
                                        <div className="p-1">
                                            <strong className="block mb-1">{marker.city || 'Unknown'}, {marker.state_code}</strong>
                                            <div className={'text-sm font-medium ' + (marker.availability_status === 'Available' ? 'text-emerald-600' : 'text-rose-500')}>{marker.availability_status}</div>
                                            {marker.zip_code && <div className="text-xs text-slate-500 mt-1">ZIP: {marker.zip_code}</div>}
                                        </div>
                                    </Popup>
                                </Marker>
                                {marker.radius_miles && <Circle center={[marker.latitude!, marker.longitude!]} radius={marker.radius_miles * 1609.34} pathOptions={{ fillColor: marker.availability_status === 'Available' ? '#10b981' : '#f43f5e', color: marker.availability_status === 'Available' ? '#059669' : '#e11d48', weight: 1, opacity: 0.5, fillOpacity: 0.2 }} />}
                            </div>
                        ))}
                    </MapContainer>
                    <div className="absolute bottom-6 right-6 bg-white p-3 rounded-lg shadow-lg z-[1000] text-xs">
                        <div className="font-semibold text-slate-700 mb-2">Territory Status</div>
                        <div className="flex items-center gap-2 mb-1.5"><div className="w-3 h-3 rounded-full bg-emerald-500"></div><span>Available</span></div>
                        <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-rose-400"></div><span>Not Available</span></div>
                    </div>
                </div>
            </div>
        </div>
    );
}
