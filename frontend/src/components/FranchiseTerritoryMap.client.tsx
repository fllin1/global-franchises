'use client';

import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { ListFilter, Loader2, ChevronRight, Home, Map as MapIcon, Building2, MapPin } from 'lucide-react';
import { fetchStatesBoundaries, fetchCountyBoundaries, getStateCodeFromFeature, getFeatureBounds, STATE_NAMES } from '@/lib/geo';
import type { Feature, FeatureCollection } from 'geojson';

interface TerritoryCheck {
    id: number;
    location_raw: string;
    state_code: string;
    county: string | null;
    city: string | null;
    zip_code: string | null;
    latitude: number | null;
    longitude: number | null;
    availability_status: string;
    radius_miles: number | null;
}

// 4-level hierarchy: State -> County -> City -> TerritoryCheck[]
interface TerritoryData {
    franchise_id: number;
    territory_count: number;
    states: Record<string, Record<string, Record<string, TerritoryCheck[]>>>;
}

interface BreadcrumbItem {
    label: string;
    type: 'all' | 'state' | 'county' | 'city' | 'zip';
    value?: string;
}

type ViewLevel = 'states' | 'counties' | 'cities' | 'zips';

// Availability status type
type AvailabilityStatus = 'available' | 'unavailable' | 'mixed' | 'neutral';

const UNSPECIFIED_COUNTY = "Unspecified County";

// Colors for availability status
const AVAILABILITY_COLORS: Record<AvailabilityStatus, { fill: string; stroke: string; hover: string }> = {
    available: { fill: '#10b981', stroke: '#059669', hover: '#34d399' },
    unavailable: { fill: '#f43f5e', stroke: '#e11d48', hover: '#fb7185' },
    mixed: { fill: '#f59e0b', stroke: '#d97706', hover: '#fbbf24' },
    neutral: { fill: '#94a3b8', stroke: '#64748b', hover: '#cbd5e1' },
};

export default function FranchiseTerritoryMapClient({ data }: { data: TerritoryData | null }) {
    const [selectedState, setSelectedState] = useState<string | null>(null);
    const [selectedCounty, setSelectedCounty] = useState<string | null>(null);
    const [selectedCity, setSelectedCity] = useState<string | null>(null);
    const [selectedZip, setSelectedZip] = useState<string | null>(null);
    const [leafletLoaded, setLeafletLoaded] = useState(false);
    const [L, setL] = useState<any>(null);
    const [hoveredItem, setHoveredItem] = useState<string | null>(null);
    
    // GeoJSON data
    const [statesGeo, setStatesGeo] = useState<FeatureCollection | null>(null);
    const [countiesGeo, setCountiesGeo] = useState<FeatureCollection | null>(null);
    const [geoLoading, setGeoLoading] = useState(false);
    
    // Refs for imperative map management
    const mapContainerRef = useRef<HTMLDivElement>(null);
    const mapRef = useRef<any>(null);
    const geoLayerRef = useRef<any>(null);
    const markersLayerRef = useRef<any>(null);
    const featureLayersRef = useRef<Map<string, any>>(new Map());
    const sidebarRef = useRef<HTMLDivElement>(null);

    // Load Leaflet library dynamically
    useEffect(() => {
        let isMounted = true;
        
        Promise.all([
            import('leaflet'),
            import('leaflet/dist/leaflet.css' as any)
        ]).then(([LeafletModule]) => {
            if (!isMounted) return;
            
            const Leaflet = LeafletModule.default || LeafletModule;
            
            // Fix default marker icons
            // @ts-ignore
            delete Leaflet.Icon.Default.prototype._getIconUrl;
            Leaflet.Icon.Default.mergeOptions({
                iconUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon.png',
                iconRetinaUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-icon-2x.png',
                shadowUrl: 'https://unpkg.com/leaflet@1.7.1/dist/images/marker-shadow.png',
            });
            
            setL(Leaflet);
            setLeafletLoaded(true);
        }).catch(err => console.error("Failed to load Leaflet", err));

        return () => {
            isMounted = false;
        };
    }, []);

    // Load states GeoJSON on mount
    useEffect(() => {
        fetchStatesBoundaries()
            .then(setStatesGeo)
            .catch(err => console.error("Failed to load states GeoJSON:", err));
    }, []);

    // Load county GeoJSON when state is selected
    useEffect(() => {
        if (selectedState && !selectedCounty) {
            setGeoLoading(true);
            fetchCountyBoundaries(selectedState)
                .then(setCountiesGeo)
                .catch(err => console.error(`Failed to load counties for ${selectedState}:`, err))
                .finally(() => setGeoLoading(false));
        } else if (!selectedState) {
            setCountiesGeo(null);
        }
    }, [selectedState, selectedCounty]);

    // Calculate availability status for a state
    const getStateAvailability = useCallback((stateCode: string): AvailabilityStatus => {
        if (!data?.states?.[stateCode]) return 'neutral';
        
        let hasAvailable = false;
        let hasUnavailable = false;
        
        try {
            const stateData = data.states[stateCode];
            Object.values(stateData).forEach(countyData => {
                if (typeof countyData !== 'object' || countyData === null) return;
                Object.values(countyData).forEach(cityChecks => {
                    if (!Array.isArray(cityChecks)) return;
                    cityChecks.forEach(check => {
                        if (check.availability_status === 'Available') hasAvailable = true;
                        else hasUnavailable = true;
                    });
                });
            });
        } catch (e) {
            return 'neutral';
        }
        
        if (hasAvailable && hasUnavailable) return 'mixed';
        if (hasAvailable) return 'available';
        if (hasUnavailable) return 'unavailable';
        return 'neutral';
    }, [data]);

    // Calculate availability status for a county
    const getCountyAvailability = useCallback((stateCode: string, county: string): AvailabilityStatus => {
        if (!data?.states?.[stateCode]?.[county]) return 'neutral';
        
        let hasAvailable = false;
        let hasUnavailable = false;
        
        try {
            const countyData = data.states[stateCode][county];
            Object.values(countyData).forEach(cityChecks => {
                if (!Array.isArray(cityChecks)) return;
                cityChecks.forEach(check => {
                    if (check.availability_status === 'Available') hasAvailable = true;
                    else hasUnavailable = true;
                });
            });
        } catch (e) {
            return 'neutral';
        }
        
        if (hasAvailable && hasUnavailable) return 'mixed';
        if (hasAvailable) return 'available';
        if (hasUnavailable) return 'unavailable';
        return 'neutral';
    }, [data]);

    // Count checks in a state (defensive - handles malformed data)
    const getStateCheckCount = useCallback((state: string): number => {
        if (!data?.states?.[state]) return 0;
        let count = 0;
        try {
            const stateData = data.states[state];
            if (typeof stateData !== 'object' || stateData === null) return 0;
            
            Object.values(stateData).forEach(countyData => {
                if (typeof countyData !== 'object' || countyData === null) return;
                Object.values(countyData).forEach(cityChecks => {
                    if (Array.isArray(cityChecks)) {
                        count += cityChecks.length;
                    }
                });
            });
        } catch (e) {
            console.error('Error counting state checks:', e);
            return 0;
        }
        return count;
    }, [data]);

    // Count checks in a county (defensive - handles malformed data)
    const getCountyCheckCount = useCallback((state: string, county: string): number => {
        if (!data?.states?.[state]?.[county]) return 0;
        let count = 0;
        try {
            const countyData = data.states[state][county];
            if (typeof countyData !== 'object' || countyData === null) return 0;
            
            Object.values(countyData).forEach(cityChecks => {
                if (Array.isArray(cityChecks)) {
                    count += cityChecks.length;
                }
            });
        } catch (e) {
            console.error('Error counting county checks:', e);
            return 0;
        }
        return count;
    }, [data]);

    // Count checks in a city (defensive - handles malformed data)
    const getCityCheckCount = useCallback((state: string, county: string, city: string): number => {
        try {
            const cityChecks = data?.states?.[state]?.[county]?.[city];
            return Array.isArray(cityChecks) ? cityChecks.length : 0;
        } catch (e) {
            console.error('Error counting city checks:', e);
            return 0;
        }
    }, [data]);

    // Get all states with territory checks (sorted by check count descending)
    const statesWithData = useMemo(() => {
        if (!data?.states) return [];
        return Object.keys(data.states)
            .sort((a, b) => getStateCheckCount(b) - getStateCheckCount(a));
    }, [data, getStateCheckCount]);

    // Get all counties in a state (sorted by check count descending)
    const getCountiesInState = useCallback((state: string): string[] => {
        if (!data?.states?.[state]) return [];
        return Object.keys(data.states[state])
            .sort((a, b) => {
                // Put Unspecified County last
                if (a === UNSPECIFIED_COUNTY) return 1;
                if (b === UNSPECIFIED_COUNTY) return -1;
                // Then sort by check count
                return getCountyCheckCount(state, b) - getCountyCheckCount(state, a);
            });
    }, [data, getCountyCheckCount]);

    // Get all cities in a county (sorted by check count descending)
    const getCitiesInCounty = useCallback((state: string, county: string): string[] => {
        if (!data?.states?.[state]?.[county]) return [];
        return Object.keys(data.states[state][county])
            .sort((a, b) => getCityCheckCount(state, county, b) - getCityCheckCount(state, county, a));
    }, [data, getCityCheckCount]);

    // Check if a state has only "Unspecified County"
    const hasOnlyUnspecifiedCounty = useCallback((state: string): boolean => {
        if (!data?.states?.[state]) return true;
        const counties = Object.keys(data.states[state]);
        return counties.length === 1 && counties[0] === UNSPECIFIED_COUNTY;
    }, [data]);

    // Breadcrumbs
    const breadcrumbs: BreadcrumbItem[] = useMemo(() => {
        const items: BreadcrumbItem[] = [{ label: 'All States', type: 'all' }];
        if (selectedState) items.push({ label: STATE_NAMES[selectedState] || selectedState, type: 'state', value: selectedState });
        if (selectedCounty && selectedCounty !== UNSPECIFIED_COUNTY) {
            items.push({ label: selectedCounty, type: 'county', value: selectedCounty });
        }
        if (selectedCity) items.push({ label: selectedCity, type: 'city', value: selectedCity });
        if (selectedZip) items.push({ label: 'ZIP: ' + selectedZip, type: 'zip', value: selectedZip });
        return items;
    }, [selectedState, selectedCounty, selectedCity, selectedZip]);

    const handleBreadcrumbClick = useCallback((item: BreadcrumbItem) => {
        switch (item.type) {
            case 'all':
                setSelectedState(null);
                setSelectedCounty(null);
                setSelectedCity(null);
                setSelectedZip(null);
                break;
            case 'state':
                setSelectedCounty(null);
                setSelectedCity(null);
                setSelectedZip(null);
                break;
            case 'county':
                setSelectedCity(null);
                setSelectedZip(null);
                break;
            case 'city':
                setSelectedZip(null);
                break;
        }
    }, []);

    // Handle state selection
    const handleStateSelect = useCallback((state: string) => {
        setSelectedState(state);
        setSelectedCounty(null);
        setSelectedCity(null);
        setSelectedZip(null);
        setHoveredItem(null);
        
        // Auto-select county if there's only Unspecified County
        if (hasOnlyUnspecifiedCounty(state)) {
            setSelectedCounty(UNSPECIFIED_COUNTY);
        }
    }, [hasOnlyUnspecifiedCounty]);

    // Handle county selection
    const handleCountySelect = useCallback((county: string) => {
        setSelectedCounty(county);
        setSelectedCity(null);
        setSelectedZip(null);
        setHoveredItem(null);
    }, []);

    // Handle city selection
    const handleCitySelect = useCallback((city: string) => {
        setSelectedCity(city);
        setSelectedZip(null);
        setHoveredItem(null);
    }, []);

    // Filtered list based on current selection
    const filteredList = useMemo(() => {
        if (!data?.states) return [];
        
        // If zip is selected
        if (selectedZip && selectedCity && selectedCounty && selectedState) {
            const cityChecks = data.states[selectedState]?.[selectedCounty]?.[selectedCity] || [];
            return cityChecks.filter(c => c.zip_code === selectedZip);
        }
        
        // If city is selected
        if (selectedCity && selectedCounty && selectedState) {
            return data.states[selectedState]?.[selectedCounty]?.[selectedCity] || [];
        }
        
        // If county is selected
        if (selectedCounty && selectedState) {
            const allInCounty: TerritoryCheck[] = [];
            const countyCities = data.states[selectedState]?.[selectedCounty];
            if (countyCities) {
                Object.values(countyCities).forEach(arr => {
                    if (Array.isArray(arr)) allInCounty.push(...arr);
                });
            }
            return allInCounty;
        }
        
        // If only state is selected
        if (selectedState) {
            const allInState: TerritoryCheck[] = [];
            const stateCounties = data.states[selectedState];
            if (stateCounties) {
                Object.values(stateCounties).forEach(counties => {
                    if (counties && typeof counties === 'object') {
                        Object.values(counties).forEach(arr => {
                            if (Array.isArray(arr)) allInState.push(...arr);
                        });
                    }
                });
            }
            return allInState;
        }
        
        return [];
    }, [selectedState, selectedCounty, selectedCity, selectedZip, data]);

    // Available zips in current city
    const availableZips = useMemo(() => {
        if (!selectedCity || !selectedCounty || !selectedState || !data?.states) return [];
        const cityChecks = data.states[selectedState]?.[selectedCounty]?.[selectedCity] || [];
        const zips = new Set(cityChecks.map(c => c.zip_code).filter(Boolean));
        return Array.from(zips) as string[];
    }, [selectedCity, selectedCounty, selectedState, data]);

    // Current view level
    const viewLevel: ViewLevel = useMemo(() => {
        if (selectedCity) return 'zips';
        if (selectedCounty) return 'cities';
        if (selectedState) return 'counties';
        return 'states';
    }, [selectedState, selectedCounty, selectedCity]);

    // Get polygon style
    const getPolygonStyle = useCallback((status: AvailabilityStatus, isHovered: boolean) => {
        const colors = AVAILABILITY_COLORS[status];
        return {
            fillColor: isHovered ? colors.hover : colors.fill,
            color: colors.stroke,
            weight: isHovered ? 2 : 1,
            opacity: 0.8,
            fillOpacity: isHovered ? 0.6 : 0.4,
        };
    }, []);

    // Initialize map
    useEffect(() => {
        if (!leafletLoaded || !L || !mapContainerRef.current) return;
        
        const container = mapContainerRef.current;
        if ((container as any)._leaflet_id) {
            if (mapRef.current) {
                try {
                    mapRef.current.remove();
                } catch (e) { }
            }
            delete (container as any)._leaflet_id;
            while (container.firstChild) {
                container.removeChild(container.firstChild);
            }
        }
        
        const map = L.map(container, {
            center: [39.8283, -98.5795],
            zoom: 4,
            scrollWheelZoom: true,
        });
        
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        }).addTo(map);
        
        // Use featureGroup instead of layerGroup to support getBounds()
        const geoLayer = L.featureGroup().addTo(map);
        const markersLayer = L.featureGroup().addTo(map);
        
        mapRef.current = map;
        geoLayerRef.current = geoLayer;
        markersLayerRef.current = markersLayer;
        featureLayersRef.current = new Map();
        
        return () => {
            featureLayersRef.current.clear();
            if (geoLayerRef.current) {
                geoLayerRef.current.clearLayers();
                geoLayerRef.current = null;
            }
            if (markersLayerRef.current) {
                markersLayerRef.current.clearLayers();
                markersLayerRef.current = null;
            }
            if (mapRef.current) {
                try {
                    mapRef.current.remove();
                } catch (e) { }
                mapRef.current = null;
            }
            if (container && (container as any)._leaflet_id) {
                delete (container as any)._leaflet_id;
            }
        };
    }, [leafletLoaded, L]);

    // Render states polygons
    useEffect(() => {
        if (!mapRef.current || !geoLayerRef.current || !L || !statesGeo) return;
        if (viewLevel !== 'states') return;
        
        geoLayerRef.current.clearLayers();
        markersLayerRef.current?.clearLayers();
        featureLayersRef.current.clear();
        
        statesGeo.features.forEach(feature => {
            const stateCode = getStateCodeFromFeature(feature);
            if (!stateCode) return;
            
            const hasData = statesWithData.includes(stateCode);
            const availability = hasData ? getStateAvailability(stateCode) : 'neutral';
            const isHovered = hoveredItem === stateCode;
            
            const layer = L.geoJSON(feature, {
                style: getPolygonStyle(availability, isHovered),
                onEachFeature: (_feat: Feature, lyr: any) => {
                    const checkCount = getStateCheckCount(stateCode);
                    lyr.bindTooltip(`<strong>${STATE_NAMES[stateCode] || stateCode}</strong><br/>${checkCount} checks`, {
                        sticky: true,
                        className: 'leaflet-tooltip-custom'
                    });
                    
                    lyr.on('mouseover', () => {
                        setHoveredItem(stateCode);
                        lyr.setStyle(getPolygonStyle(availability, true));
                    });
                    
                    lyr.on('mouseout', () => {
                        setHoveredItem(null);
                        lyr.setStyle(getPolygonStyle(availability, false));
                    });
                    
                    lyr.on('click', () => {
                        if (hasData) {
                            handleStateSelect(stateCode);
                        }
                    });
                }
            });
            
            featureLayersRef.current.set(stateCode, layer);
            geoLayerRef.current.addLayer(layer);
        });
        
        // Fit bounds to continental US
        mapRef.current.setView([39.8283, -98.5795], 4);
    }, [viewLevel, statesGeo, L, statesWithData, getStateAvailability, getPolygonStyle, hoveredItem, handleStateSelect, getStateCheckCount]);

    // Render counties polygons or city markers
    useEffect(() => {
        if (!mapRef.current || !geoLayerRef.current || !markersLayerRef.current || !L) return;
        if (viewLevel !== 'counties') return;
        if (!selectedState) return;
        
        geoLayerRef.current.clearLayers();
        markersLayerRef.current.clearLayers();
        featureLayersRef.current.clear();
        
        const counties = getCountiesInState(selectedState);
        
        // If we have county GeoJSON, render polygons
        if (countiesGeo && countiesGeo.features.length > 0) {
            countiesGeo.features.forEach(feature => {
                const countyName = feature.properties?.NAME || feature.properties?.name || 'Unknown';
                const matchingCounty = counties.find(c => 
                    c.toLowerCase().replace(/\s+county$/i, '').trim() === 
                    countyName.toLowerCase().replace(/\s+county$/i, '').trim()
                );
                
                const availability = matchingCounty ? getCountyAvailability(selectedState, matchingCounty) : 'neutral';
                const isHovered = hoveredItem === countyName;
                
                const layer = L.geoJSON(feature, {
                    style: getPolygonStyle(availability, isHovered),
                    onEachFeature: (_feat: Feature, lyr: any) => {
                        const checkCount = matchingCounty ? getCountyCheckCount(selectedState, matchingCounty) : 0;
                        lyr.bindTooltip(`<strong>${countyName}</strong><br/>${checkCount} checks`, {
                            sticky: true
                        });
                        
                        lyr.on('mouseover', () => {
                            if (matchingCounty) setHoveredItem(matchingCounty);
                        });
                        
                        lyr.on('mouseout', () => {
                            setHoveredItem(null);
                        });
                        
                        lyr.on('click', () => {
                            if (matchingCounty) {
                                handleCountySelect(matchingCounty);
                            }
                        });
                    }
                });
                
                if (matchingCounty) {
                    featureLayersRef.current.set(matchingCounty, layer);
                }
                geoLayerRef.current.addLayer(layer);
            });
            
            // Fit to state bounds (with safety check)
            try {
                const bounds = geoLayerRef.current.getBounds();
                if (bounds && bounds.isValid()) {
                    mapRef.current.fitBounds(bounds, { padding: [20, 20] });
                }
            } catch (e) {
                console.warn('Could not fit to county bounds:', e);
            }
        } else {
            // Fallback: Show city markers grouped by county
            const allChecks = filteredList.filter(c => c.latitude && c.longitude);
            if (allChecks.length > 0) {
                allChecks.forEach(check => {
                    const isAvailable = check.availability_status === 'Available';
                    const marker = L.circleMarker([check.latitude!, check.longitude!], {
                        radius: 8,
                        fillColor: isAvailable ? '#10b981' : '#f43f5e',
                        color: isAvailable ? '#059669' : '#e11d48',
                        weight: 2,
                        opacity: 1,
                        fillOpacity: 0.7
                    });
                    
                    marker.bindTooltip(`<strong>${check.city || 'Unknown'}</strong><br/>${check.county || ''}<br/>${check.availability_status}`, {
                        sticky: true
                    });
                    
                    marker.on('click', () => {
                        if (check.county) {
                            setSelectedCounty(check.county);
                            if (check.city) {
                                setSelectedCity(check.city);
                            }
                        }
                    });
                    
                    markersLayerRef.current.addLayer(marker);
                });
                
                const bounds = L.latLngBounds(allChecks.map(c => [c.latitude!, c.longitude!]));
                mapRef.current.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [viewLevel, selectedState, countiesGeo, L, getCountiesInState, getCountyAvailability, getPolygonStyle, hoveredItem, handleCountySelect, filteredList, getCountyCheckCount]);

    // Render city markers
    useEffect(() => {
        if (!mapRef.current || !markersLayerRef.current || !L) return;
        if (viewLevel !== 'cities' && viewLevel !== 'zips') return;
        
        geoLayerRef.current?.clearLayers();
        markersLayerRef.current.clearLayers();
        featureLayersRef.current.clear();
        
        const checksWithCoords = filteredList.filter(c => c.latitude && c.longitude);
        
        checksWithCoords.forEach(check => {
            const isAvailable = check.availability_status === 'Available';
            const isHovered = hoveredItem === check.city || hoveredItem === check.zip_code;
            
            const marker = L.circleMarker([check.latitude!, check.longitude!], {
                radius: isHovered ? 12 : 8,
                fillColor: isAvailable ? '#10b981' : '#f43f5e',
                color: isAvailable ? '#059669' : '#e11d48',
                weight: isHovered ? 3 : 2,
                opacity: 1,
                fillOpacity: isHovered ? 0.9 : 0.7
            });
            
            const tooltipContent = `
                <strong>${check.city || 'Unknown'}</strong><br/>
                ${check.county ? `${check.county}<br/>` : ''}
                ${check.zip_code ? `ZIP: ${check.zip_code}<br/>` : ''}
                <span style="color: ${isAvailable ? '#10b981' : '#f43f5e'}">${check.availability_status}</span>
            `;
            marker.bindTooltip(tooltipContent, { sticky: true });
            
            marker.on('mouseover', () => {
                setHoveredItem(check.city || check.zip_code || null);
            });
            
            marker.on('mouseout', () => {
                setHoveredItem(null);
            });
            
            marker.on('click', () => {
                if (check.city && !selectedCity) {
                    handleCitySelect(check.city);
                } else if (check.zip_code) {
                    setSelectedZip(check.zip_code);
                }
            });
            
            // Store by city or zip for hover sync
            if (check.city) {
                featureLayersRef.current.set(check.city, marker);
            }
            if (check.zip_code) {
                featureLayersRef.current.set(check.zip_code, marker);
            }
            
            markersLayerRef.current.addLayer(marker);
            
            // Add radius circle if specified
            if (check.radius_miles) {
                const circle = L.circle([check.latitude!, check.longitude!], {
                    radius: check.radius_miles * 1609.34,
                    fillColor: isAvailable ? '#10b981' : '#f43f5e',
                    color: isAvailable ? '#059669' : '#e11d48',
                    weight: 1,
                    opacity: 0.3,
                    fillOpacity: 0.1
                });
                markersLayerRef.current.addLayer(circle);
            }
        });
        
        // Fit bounds
        if (checksWithCoords.length > 0) {
            const bounds = L.latLngBounds(checksWithCoords.map(c => [c.latitude!, c.longitude!]));
            mapRef.current.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [viewLevel, filteredList, L, hoveredItem, selectedCity, handleCitySelect]);

    // Update hover state on map when sidebar hover changes
    useEffect(() => {
        if (!hoveredItem) return;
        
        const layer = featureLayersRef.current.get(hoveredItem);
        if (layer && layer.setStyle) {
            // For GeoJSON layers
            const status = viewLevel === 'states' 
                ? (statesWithData.includes(hoveredItem) ? getStateAvailability(hoveredItem) : 'neutral')
                : (selectedState ? getCountyAvailability(selectedState, hoveredItem) : 'neutral');
            layer.setStyle(getPolygonStyle(status, true));
        } else if (layer && layer.setRadius) {
            // For circle markers
            layer.setRadius(12);
        }
        
        return () => {
            if (layer && layer.setStyle) {
                const status = viewLevel === 'states' 
                    ? (statesWithData.includes(hoveredItem) ? getStateAvailability(hoveredItem) : 'neutral')
                    : (selectedState ? getCountyAvailability(selectedState, hoveredItem) : 'neutral');
                layer.setStyle(getPolygonStyle(status, false));
            } else if (layer && layer.setRadius) {
                layer.setRadius(8);
            }
        };
    }, [hoveredItem, viewLevel, statesWithData, getStateAvailability, selectedState, getCountyAvailability, getPolygonStyle]);

    // Sidebar title and subtitle
    const getSidebarTitle = () => {
        if (selectedZip) return 'ZIP: ' + selectedZip;
        if (selectedCity) return selectedCity;
        if (selectedCounty && selectedCounty !== UNSPECIFIED_COUNTY) return selectedCounty;
        if (selectedState) return STATE_NAMES[selectedState] || selectedState;
        return 'Select a State';
    };

    const getSidebarSubtitle = () => {
        if (selectedState) {
            return filteredList.length + ' territory check' + (filteredList.length !== 1 ? 's' : '');
        }
        return statesWithData.length + ' states with data';
    };

    // Render sidebar content
    const renderSidebarContent = () => {
        // Level 1: Show all states
        if (!selectedState) {
            return statesWithData.map(state => {
                const availability = getStateAvailability(state);
                const colors = AVAILABILITY_COLORS[availability];
                const isHovered = hoveredItem === state;
                
                return (
                <button 
                    key={state} 
                    onClick={() => handleStateSelect(state)} 
                        onMouseEnter={() => setHoveredItem(state)}
                        onMouseLeave={() => setHoveredItem(null)}
                        className={`w-full text-left px-4 py-3 border-b border-slate-100 flex justify-between items-center group transition-colors ${
                            isHovered ? 'bg-slate-100' : 'hover:bg-slate-50'
                        }`}
                    >
                        <div className="flex items-center gap-3">
                            <div 
                                className="w-3 h-3 rounded-full" 
                                style={{ backgroundColor: colors.fill }}
                            />
                            <span className="font-medium text-slate-700">
                                {STATE_NAMES[state] || state}
                            </span>
                        </div>
                    <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                        {getStateCheckCount(state)} checks
                    </span>
                </button>
                );
            });
        }

        // Level 2: Show counties in state
        if (!selectedCounty) {
            const counties = getCountiesInState(selectedState);
            return counties.map(county => {
                const availability = getCountyAvailability(selectedState, county);
                const colors = AVAILABILITY_COLORS[availability];
                const isHovered = hoveredItem === county;
                
                return (
                <button 
                    key={county} 
                    onClick={() => handleCountySelect(county)} 
                        onMouseEnter={() => setHoveredItem(county)}
                        onMouseLeave={() => setHoveredItem(null)}
                        className={`w-full text-left px-4 py-3 border-b border-slate-100 flex justify-between items-center group transition-colors ${
                            isHovered ? 'bg-slate-100' : 'hover:bg-slate-50'
                        }`}
                    >
                        <div className="flex items-center gap-3">
                            <div 
                                className="w-3 h-3 rounded-full" 
                                style={{ backgroundColor: colors.fill }}
                            />
                    <div className="flex items-center gap-2">
                        <Building2 className="w-4 h-4 text-slate-400" />
                        <span className="font-medium text-slate-700">
                            {county === UNSPECIFIED_COUNTY ? <span className="italic text-slate-500">{county}</span> : county}
                        </span>
                            </div>
                    </div>
                    <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                        {getCountyCheckCount(selectedState, county)} checks
                    </span>
                </button>
                );
            });
        }

        // Level 3: Show cities in county
        if (!selectedCity) {
            const cities = getCitiesInCounty(selectedState, selectedCounty);
            return cities.map(city => {
                const cityChecks = data?.states?.[selectedState]?.[selectedCounty]?.[city] || [];
                const hasAvailable = cityChecks.some(c => c.availability_status === 'Available');
                const hasUnavailable = cityChecks.some(c => c.availability_status !== 'Available');
                const status: AvailabilityStatus = hasAvailable && hasUnavailable ? 'mixed' : hasAvailable ? 'available' : hasUnavailable ? 'unavailable' : 'neutral';
                const colors = AVAILABILITY_COLORS[status];
                const isHovered = hoveredItem === city;
                
                return (
                <button 
                    key={city} 
                    onClick={() => handleCitySelect(city)} 
                        onMouseEnter={() => setHoveredItem(city)}
                        onMouseLeave={() => setHoveredItem(null)}
                        className={`w-full text-left px-4 py-3 border-b border-slate-100 flex justify-between items-center group transition-colors ${
                            isHovered ? 'bg-slate-100' : 'hover:bg-slate-50'
                        }`}
                    >
                        <div className="flex items-center gap-3">
                            <div 
                                className="w-3 h-3 rounded-full" 
                                style={{ backgroundColor: colors.fill }}
                            />
                            <div className="flex items-center gap-2">
                                <MapPin className="w-4 h-4 text-slate-400" />
                    <span className="font-medium text-slate-700">{city}</span>
                            </div>
                        </div>
                    <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                        {getCityCheckCount(selectedState, selectedCounty, city)} checks
                    </span>
                </button>
                );
            });
        }

        // Level 4: Show zips in city (if multiple) or territory checks
        if (availableZips.length > 1 && !selectedZip) {
            return (
                <>
                    <button 
                        onClick={() => setSelectedZip(null)} 
                        className="w-full text-left px-4 py-3 border-b border-slate-200 bg-slate-50 hover:bg-slate-100 flex justify-between items-center"
                    >
                        <span className="font-medium text-indigo-600">View All {selectedCity}</span>
                        <span className="text-xs bg-indigo-100 text-indigo-600 px-2 py-1 rounded-full">{filteredList.length} checks</span>
                    </button>
                    {availableZips.sort().map(zip => {
                        const zipChecks = filteredList.filter(c => c.zip_code === zip);
                        const hasAvailable = zipChecks.some(c => c.availability_status === 'Available');
                        const colors = AVAILABILITY_COLORS[hasAvailable ? 'available' : 'unavailable'];
                        const isHovered = hoveredItem === zip;
                        
                        return (
                        <button 
                            key={zip} 
                            onClick={() => setSelectedZip(zip)} 
                                onMouseEnter={() => setHoveredItem(zip)}
                                onMouseLeave={() => setHoveredItem(null)}
                                className={`w-full text-left px-4 py-3 border-b border-slate-100 flex justify-between items-center group transition-colors ${
                                    isHovered ? 'bg-slate-100' : 'hover:bg-slate-50'
                                }`}
                            >
                                <div className="flex items-center gap-3">
                                    <div 
                                        className="w-3 h-3 rounded-full" 
                                        style={{ backgroundColor: colors.fill }}
                                    />
                            <span className="font-medium text-slate-700 font-mono">{zip}</span>
                                </div>
                            <span className="text-xs bg-slate-100 text-slate-500 px-2 py-1 rounded-full group-hover:bg-indigo-100 group-hover:text-indigo-600">
                                    {zipChecks.length} checks
                            </span>
                        </button>
                        );
                    })}
                </>
            );
        }

        // Level 5: Show territory check details
        return (
            <div className="divide-y divide-slate-100">
                {filteredList.map((item) => (
                    <div 
                        key={item.id} 
                        className="p-4 hover:bg-slate-50 transition-colors"
                        onMouseEnter={() => setHoveredItem(item.city || item.zip_code || null)}
                        onMouseLeave={() => setHoveredItem(null)}
                    >
                        <div className="flex items-start gap-3">
                            <div className={'mt-1 w-2.5 h-2.5 rounded-full shrink-0 ' + (item.availability_status === 'Available' ? 'bg-emerald-500' : 'bg-rose-400')} />
                            <div className="flex-1 min-w-0">
                                <div className="text-sm font-medium text-slate-900">{item.city || item.location_raw || 'Unknown Location'}</div>
                                {item.county && item.county !== UNSPECIFIED_COUNTY && (
                                    <div className="text-xs text-slate-400 mt-0.5">{item.county}</div>
                                )}
                                {item.zip_code && <div className="text-xs text-slate-500 font-mono mt-0.5">ZIP: {item.zip_code}</div>}
                                <div className={'text-xs mt-1 font-medium ' + (item.availability_status === 'Available' ? 'text-emerald-600' : 'text-rose-500')}>{item.availability_status}</div>
                                {item.radius_miles && <div className="text-xs text-slate-400 mt-1">{item.radius_miles} mile radius</div>}
                            </div>
                        </div>
                    </div>
                ))}
            </div>
        );
    };

    // Empty state
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

    // Loading state
    if (!leafletLoaded) {
        return (
            <div className="flex items-center justify-center h-full bg-slate-50 text-slate-400">
                <Loader2 className="w-6 h-6 animate-spin mr-2" />
                Loading Map...
            </div>
        );
    }

    return (
        <div className="flex h-full flex-col">
            {/* Breadcrumbs */}
            <div className="bg-white border-b border-slate-200 px-4 py-2">
                <nav className="flex items-center text-sm flex-wrap">
                    {breadcrumbs.map((crumb, idx) => (
                        <div key={idx} className="flex items-center">
                            {idx > 0 && <ChevronRight className="w-4 h-4 mx-1 text-slate-300" />}
                            <button
                                onClick={() => handleBreadcrumbClick(crumb)}
                                className={'flex items-center gap-1 px-2 py-1 rounded transition-colors ' + (idx === breadcrumbs.length - 1 ? 'bg-indigo-50 text-indigo-700 font-medium' : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100')}
                            >
                                {idx === 0 && <Home className="w-3.5 h-3.5" />}
                                {crumb.type === 'county' && <Building2 className="w-3.5 h-3.5" />}
                                {crumb.label}
                            </button>
                        </div>
                    ))}
                </nav>
            </div>

            <div className="flex flex-1 min-h-0">
                {/* Sidebar */}
                <div className="w-80 bg-white border-r border-slate-200 flex flex-col">
                    <div className="p-4 border-b border-slate-200 bg-slate-50">
                        <h3 className="font-bold text-slate-800 flex items-center gap-2">
                            <ListFilter className="w-4 h-4" />
                            {getSidebarTitle()}
                        </h3>
                        <p className="text-xs text-slate-500 mt-1">
                            {getSidebarSubtitle()}
                        </p>
                    </div>
                    
                    <div ref={sidebarRef} className="flex-1 overflow-y-auto">
                        {geoLoading ? (
                            <div className="flex items-center justify-center p-8 text-slate-400">
                                <Loader2 className="w-5 h-5 animate-spin mr-2" />
                                Loading...
                            </div>
                        ) : (
                            renderSidebarContent()
                        )}
                    </div>
                </div>

                {/* Map */}
                <div className="flex-1 relative bg-slate-100">
                    <div 
                        ref={mapContainerRef} 
                        style={{ height: '100%', width: '100%' }}
                    />
                    
                    {/* Legend */}
                    <div className="absolute bottom-6 right-6 bg-white p-3 rounded-lg shadow-lg z-[1000] text-xs">
                        <div className="font-semibold text-slate-700 mb-2">Territory Status</div>
                        <div className="space-y-1.5">
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: AVAILABILITY_COLORS.available.fill }}></div>
                                <span>Available</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: AVAILABILITY_COLORS.unavailable.fill }}></div>
                                <span>Not Available</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: AVAILABILITY_COLORS.mixed.fill }}></div>
                                <span>Mixed</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-3 h-3 rounded-full" style={{ backgroundColor: AVAILABILITY_COLORS.neutral.fill }}></div>
                                <span>No Data</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
