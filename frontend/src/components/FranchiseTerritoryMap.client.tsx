'use client';

import { useState, useMemo, useEffect, useCallback, useRef } from 'react';
import { ListFilter, Loader2, ChevronRight, Home, Map as MapIcon, Building2, MapPin } from 'lucide-react';
import { 
    fetchStatesBoundaries, 
    fetchCountyBoundaries, 
    fetchCityBoundaries,
    fetchZipBoundaries,
    getStateCodeFromFeature, 
    getFeatureBounds, 
    findCountyFeature,
    findCityFeature,
    STATE_NAMES 
} from '@/lib/geo';
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
// Availability is calculated bottom-up:
// - Zip level: ALL checks must be unavailable for the zip to be unavailable
// - City level: ALL zips must be unavailable for the city to be unavailable
// - County level: ALL cities must be unavailable for the county to be unavailable
// - State level: ALL counties must be unavailable OR state is in unavailable_states
interface TerritoryData {
    franchise_id: number;
    territory_count: number;
    states: Record<string, Record<string, Record<string, TerritoryCheck[]>>>;
    /** Array of state codes that are explicitly marked as unavailable at the franchise level */
    unavailable_states?: string[];
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
    const [citiesGeo, setCitiesGeo] = useState<FeatureCollection | null>(null);
    const [zipsGeo, setZipsGeo] = useState<FeatureCollection | null>(null);
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

    // Load city GeoJSON when county is selected
    useEffect(() => {
        if (selectedState && selectedCounty && !selectedCity) {
            setGeoLoading(true);
            fetchCityBoundaries(selectedState)
                .then(setCitiesGeo)
                .catch(err => console.error(`Failed to load cities for ${selectedState}:`, err))
                .finally(() => setGeoLoading(false));
        } else if (!selectedCounty) {
            setCitiesGeo(null);
        }
    }, [selectedState, selectedCounty, selectedCity]);

    // Load ZIP GeoJSON when city is selected
    useEffect(() => {
        if (selectedState && selectedCity && !selectedZip) {
            setGeoLoading(true);
            fetchZipBoundaries(selectedState)
                .then(setZipsGeo)
                .catch(err => console.error(`Failed to load ZIPs for ${selectedState}:`, err))
                .finally(() => setGeoLoading(false));
        } else if (!selectedCity) {
            setZipsGeo(null);
        }
    }, [selectedState, selectedCity, selectedZip]);

    // ==========================================
    // Bottom-Up Availability Calculation
    // ==========================================
    // The hierarchy is: State -> County -> City -> Zip -> TerritoryCheck
    // 
    // KEY PRINCIPLE: "No data" = "Available" (shown as green on map)
    // 
    // Rules:
    // - A level is "unavailable" ONLY if EXPLICITLY marked unavailable
    //   (e.g., state in unavailable_states, or state-level territory check)
    // - When aggregating from partial data (we don't have data for all sub-areas):
    //   - If ALL data is "available" → "available"
    //   - If ANY data is "unavailable" → "mixed" (because areas without data = available)
    //   - This ensures visual consistency: unavailable areas (red) + no-data areas (green) = mixed
    // ==========================================

    /**
     * Calculate availability for a specific zip code within a city.
     * A zip is unavailable only if ALL checks for that zip are unavailable.
     * Note: At zip level, we have actual check data, so we can determine true availability.
     */
    const getZipAvailability = useCallback((checks: TerritoryCheck[]): AvailabilityStatus => {
        if (!checks || checks.length === 0) return 'available';
        
        const availableCount = checks.filter(c => c.availability_status === 'Available').length;
        const unavailableCount = checks.length - availableCount;
        
        if (unavailableCount === checks.length) return 'unavailable';
        if (availableCount === checks.length) return 'available';
        return 'mixed';
    }, []);

    /**
     * Calculate availability for a city by aggregating from its zip codes.
     * 
     * IMPORTANT: We only have data for SOME zips in a city. Other zips without data
     * would display as "available" on the map. So:
     * - If all zips WITH data are unavailable → "mixed" (because other zips = available)
     * - If all zips WITH data are available → "available"
     * - If mixed data → "mixed"
     */
    const getCityAvailability = useCallback((stateCode: string, county: string, city: string): AvailabilityStatus => {
        const cityChecks = data?.states?.[stateCode]?.[county]?.[city];
        if (!cityChecks || !Array.isArray(cityChecks) || cityChecks.length === 0) return 'available';
        
        // Group checks by zip code
        const zipGroups = new Map<string | null, TerritoryCheck[]>();
        cityChecks.forEach(check => {
            const zip = check.zip_code;
            if (!zipGroups.has(zip)) {
                zipGroups.set(zip, []);
            }
            zipGroups.get(zip)!.push(check);
        });
        
        // Calculate availability for each zip
        const zipStatuses: AvailabilityStatus[] = [];
        zipGroups.forEach(checks => {
            zipStatuses.push(getZipAvailability(checks));
        });
        
        // Aggregate from zips
        const allAvailable = zipStatuses.every(s => s === 'available');
        const hasAnyUnavailable = zipStatuses.some(s => s === 'unavailable' || s === 'mixed');
        
        // If all data is available, city is available
        if (allAvailable) return 'available';
        
        // If any data shows unavailable/mixed, city is mixed
        // (because there could be other zips without data that would show as available)
        if (hasAnyUnavailable) return 'mixed';
        
        return 'available';
    }, [data, getZipAvailability]);

    /**
     * Calculate availability for a county by aggregating from its cities.
     * 
     * IMPORTANT: We only have data for SOME cities in a county. Other cities without data
     * would display as "available" on the map. So:
     * - If all cities WITH data are unavailable → "mixed" (because other cities = available)
     * - If all cities WITH data are available → "available"
     * - If mixed data → "mixed"
     */
    const getCountyAvailability = useCallback((stateCode: string, county: string): AvailabilityStatus => {
        const countyData = data?.states?.[stateCode]?.[county];
        if (!countyData || typeof countyData !== 'object') return 'available';
        
        const cities = Object.keys(countyData);
        if (cities.length === 0) return 'available';
        
        // Calculate availability for each city
        const cityStatuses: AvailabilityStatus[] = cities.map(city => 
            getCityAvailability(stateCode, county, city)
        );
        
        // Aggregate from cities
        const allAvailable = cityStatuses.every(s => s === 'available');
        const hasAnyUnavailable = cityStatuses.some(s => s === 'unavailable' || s === 'mixed');
        
        // If all data is available, county is available
        if (allAvailable) return 'available';
        
        // If any data shows unavailable/mixed, county is mixed
        // (because there could be other cities without data that would show as available)
        if (hasAnyUnavailable) return 'mixed';
        
        return 'available';
    }, [data, getCityAvailability]);

    /**
     * Calculate availability for a state by aggregating from its counties.
     * 
     * A state is "unavailable" ONLY if:
     * 1. It's EXPLICITLY in the franchise's unavailable_states array, OR
     * 2. There's a state-level territory check (no county/city) marking it unavailable
     * 
     * For aggregated data from counties:
     * - If all counties WITH data are unavailable → "mixed" (other counties = available)
     * - If all counties WITH data are available → "available"
     * - If mixed data → "mixed"
     */
    const getStateAvailability = useCallback((stateCode: string): AvailabilityStatus => {
        // Check if state is EXPLICITLY marked as unavailable at franchise level
        if (data?.unavailable_states?.includes(stateCode)) {
            return 'unavailable';
        }
        
        const stateData = data?.states?.[stateCode];
        if (!stateData || typeof stateData !== 'object') return 'available';
        
        const counties = Object.keys(stateData);
        if (counties.length === 0) return 'available';
        
        // Check for state-level territory check (county is "Unspecified County" with no real cities)
        // This handles cases where a territory check EXPLICITLY marks the whole state as unavailable
        if (counties.length === 1 && counties[0] === UNSPECIFIED_COUNTY) {
            const unspecifiedCountyData = stateData[UNSPECIFIED_COUNTY];
            const cities = Object.keys(unspecifiedCountyData);
            if (cities.length === 1 && cities[0] === 'Unspecified Area') {
                const checks = unspecifiedCountyData['Unspecified Area'];
                if (Array.isArray(checks) && checks.length > 0) {
                    // This is an explicit state-level check - use actual status
                    const allUnavailable = checks.every(c => c.availability_status !== 'Available');
                    if (allUnavailable) return 'unavailable';
                    const allAvailable = checks.every(c => c.availability_status === 'Available');
                    if (allAvailable) return 'available';
                    return 'mixed';
                }
            }
        }
        
        // Calculate availability for each county
        const countyStatuses: AvailabilityStatus[] = counties.map(county => 
            getCountyAvailability(stateCode, county)
        );
        
        // Aggregate from counties
        const allAvailable = countyStatuses.every(s => s === 'available');
        const hasAnyUnavailable = countyStatuses.some(s => s === 'unavailable' || s === 'mixed');
        
        // If all data is available, state is available
        if (allAvailable) return 'available';
        
        // If any data shows unavailable/mixed, state is mixed
        // (because there are other counties without data that would show as available)
        if (hasAnyUnavailable) return 'mixed';
        
        return 'available';
    }, [data, getCountyAvailability]);

    // Count checks in a state (defensive - handles both 3-level and 4-level structures)
    // 3-level: State -> City -> [Checks]  (when county is not present)
    // 4-level: State -> County -> City -> [Checks]
    const getStateCheckCount = useCallback((state: string): number => {
        if (!data?.states?.[state]) return 0;
        let count = 0;
        try {
            const stateData = data.states[state];
            if (typeof stateData !== 'object' || stateData === null) return 0;
            
            Object.values(stateData).forEach(value => {
                if (Array.isArray(value)) {
                    // Direct array of checks (3-level: State -> City -> [Checks])
                    count += value.length;
                } else if (typeof value === 'object' && value !== null) {
                    // Nested object (4-level: State -> County -> City -> [Checks])
                    Object.values(value).forEach(cityChecks => {
                        if (Array.isArray(cityChecks)) {
                            count += cityChecks.length;
                        }
                    });
                }
            });
        } catch (e) {
            console.error('Error counting state checks:', e);
            return 0;
        }
        return count;
    }, [data]);

    // Count checks in a county (defensive - handles both direct arrays and nested city objects)
    const getCountyCheckCount = useCallback((state: string, county: string): number => {
        if (!data?.states?.[state]?.[county]) return 0;
        let count = 0;
        try {
            const countyData = data.states[state][county];
            
            if (Array.isArray(countyData)) {
                // Direct array of checks (3-level structure)
                count = countyData.length;
            } else if (typeof countyData === 'object' && countyData !== null) {
                // Nested city objects (4-level structure)
                Object.values(countyData).forEach(cityChecks => {
                    if (Array.isArray(cityChecks)) {
                        count += cityChecks.length;
                    }
                });
            }
        } catch (e) {
            console.error('Error counting county checks:', e);
            return 0;
        }
        return count;
    }, [data]);

    // Count checks in a city (defensive - handles both direct city arrays and nested structures)
    const getCityCheckCount = useCallback((state: string, county: string, city: string): number => {
        try {
            // Try 4-level path first: state -> county -> city -> [checks]
            const cityChecks = data?.states?.[state]?.[county]?.[city];
            if (Array.isArray(cityChecks)) {
                return cityChecks.length;
            }
            
            // Try 3-level path: state -> city -> [checks] (county might be the city in 3-level)
            const directChecks = data?.states?.[state]?.[city];
            if (Array.isArray(directChecks)) {
                return directChecks.length;
            }
            
            return 0;
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
            const availability = hasData ? getStateAvailability(stateCode) : 'available';
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
                
                const availability = matchingCounty ? getCountyAvailability(selectedState, matchingCounty) : 'available';
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

    // Get cities with data in the selected county
    const citiesWithData = useMemo(() => {
        if (!selectedState || !selectedCounty || !data?.states?.[selectedState]?.[selectedCounty]) return [];
        return Object.keys(data.states[selectedState][selectedCounty]);
    }, [selectedState, selectedCounty, data]);

    // Get ZIPs with data in the selected city
    const zipsWithData = useMemo(() => {
        if (!selectedState || !selectedCounty || !selectedCity) return [];
        const cityChecks = data?.states?.[selectedState]?.[selectedCounty]?.[selectedCity] || [];
        return [...new Set(cityChecks.map(c => c.zip_code).filter(Boolean))] as string[];
    }, [selectedState, selectedCounty, selectedCity, data]);

    // Render city polygons when county is selected
    useEffect(() => {
        if (!mapRef.current || !geoLayerRef.current || !L) return;
        if (viewLevel !== 'cities') return;
        if (!selectedState || !selectedCounty) return;
        
        geoLayerRef.current.clearLayers();
        markersLayerRef.current?.clearLayers();
        featureLayersRef.current.clear();
        
        const cities = getCitiesInCounty(selectedState, selectedCounty);
        
        // If we have city GeoJSON, render polygons
        if (citiesGeo && citiesGeo.features.length > 0) {
            // Get selected county bounds for proper zoom
            let countyBounds: any = null;
            if (countiesGeo) {
                const countyFeature = findCountyFeature(countiesGeo, selectedCounty);
                if (countyFeature) {
                    const featureBounds = getFeatureBounds(countyFeature);
                    if (featureBounds) {
                        countyBounds = L.latLngBounds(featureBounds);
                    }
                }
            }
            
            // Render city polygons
            citiesGeo.features.forEach(feature => {
                const cityName = feature.properties?.NAME || feature.properties?.name || 'Unknown';
                const matchingCity = cities.find(c => 
                    c.toLowerCase().trim() === cityName.toLowerCase().trim()
                );
                
                // Only render cities that are in our data OR are within the county bounds
                const hasTerritoryData = matchingCity !== undefined;
                const availability = hasTerritoryData ? getCityAvailability(selectedState, selectedCounty, matchingCity!) : 'available';
                const isHovered = hoveredItem === cityName || hoveredItem === matchingCity;
                
                const layer = L.geoJSON(feature, {
                    style: getPolygonStyle(availability, isHovered),
                    onEachFeature: (_feat: Feature, lyr: any) => {
                        const checkCount = matchingCity ? getCityCheckCount(selectedState, selectedCounty, matchingCity) : 0;
                        lyr.bindTooltip(`<strong>${cityName}</strong><br/>${checkCount} checks`, {
                            sticky: true
                        });
                        
                        lyr.on('mouseover', () => {
                            if (matchingCity) setHoveredItem(matchingCity);
                            else setHoveredItem(cityName);
                        });
                        
                        lyr.on('mouseout', () => {
                            setHoveredItem(null);
                        });
                        
                        lyr.on('click', () => {
                            if (matchingCity) {
                                handleCitySelect(matchingCity);
                            }
                        });
                    }
                });
                
                if (matchingCity) {
                    featureLayersRef.current.set(matchingCity, layer);
                }
                geoLayerRef.current.addLayer(layer);
            });
            
            // Fit to county bounds for better context, or fall back to geo layer bounds
            if (countyBounds && countyBounds.isValid()) {
                mapRef.current.fitBounds(countyBounds, { padding: [30, 30] });
            } else {
                try {
                    const bounds = geoLayerRef.current.getBounds();
                    if (bounds && bounds.isValid()) {
                        mapRef.current.fitBounds(bounds, { padding: [30, 30] });
                    }
                } catch (e) {
                    console.warn('Could not fit to city bounds:', e);
                }
            }
        } else {
            // Fallback: Show city markers if no GeoJSON available
        const checksWithCoords = filteredList.filter(c => c.latitude && c.longitude);
            checksWithCoords.forEach(check => {
                const isAvailable = check.availability_status === 'Available';
                const marker = L.circleMarker([check.latitude!, check.longitude!], {
                    radius: 10,
                    fillColor: isAvailable ? '#10b981' : '#f43f5e',
                    color: isAvailable ? '#059669' : '#e11d48',
                    weight: 2,
                    opacity: 1,
                    fillOpacity: 0.7
                });
                
                marker.bindTooltip(`<strong>${check.city || 'Unknown'}</strong><br/>${check.availability_status}`, {
                    sticky: true
                });
                
                marker.on('click', () => {
                    if (check.city) handleCitySelect(check.city);
                });
                
                markersLayerRef.current.addLayer(marker);
            });
            
            if (checksWithCoords.length > 0) {
                const bounds = L.latLngBounds(checksWithCoords.map(c => [c.latitude!, c.longitude!]));
                mapRef.current.fitBounds(bounds, { padding: [50, 50] });
            }
        }
    }, [viewLevel, selectedState, selectedCounty, citiesGeo, countiesGeo, L, getCitiesInCounty, getCityAvailability, getPolygonStyle, hoveredItem, handleCitySelect, filteredList, getCityCheckCount]);

    // Render ZIP polygons when city is selected
    useEffect(() => {
        if (!mapRef.current || !geoLayerRef.current || !L) return;
        if (viewLevel !== 'zips') return;
        if (!selectedState || !selectedCity) return;
        
        geoLayerRef.current.clearLayers();
        markersLayerRef.current?.clearLayers();
        featureLayersRef.current.clear();
        
        // If we have ZIP GeoJSON, render polygons
        if (zipsGeo && zipsGeo.features.length > 0 && zipsWithData.length > 0) {
            // Get city feature bounds for proper zoom
            let cityBounds: any = null;
            if (citiesGeo) {
                const cityFeature = findCityFeature(citiesGeo, selectedCity);
                if (cityFeature) {
                    const featureBounds = getFeatureBounds(cityFeature);
                    if (featureBounds) {
                        cityBounds = L.latLngBounds(featureBounds);
                    }
                }
            }
            
            // Only render ZIPs that have territory data
            const zipsSet = new Set(zipsWithData);
            let hasRenderedZips = false;
            
            zipsGeo.features.forEach(feature => {
                const zipCode = feature.properties?.ZCTA5 || feature.properties?.GEOID || '';
                
                if (!zipsSet.has(zipCode)) return; // Skip ZIPs without data
                
                hasRenderedZips = true;
                const zipChecks = filteredList.filter(c => c.zip_code === zipCode);
                const availability = getZipAvailability(zipChecks);
                const isHovered = hoveredItem === zipCode;
                
                const layer = L.geoJSON(feature, {
                    style: getPolygonStyle(availability, isHovered),
                    onEachFeature: (_feat: Feature, lyr: any) => {
                        lyr.bindTooltip(`<strong>ZIP ${zipCode}</strong><br/>${zipChecks.length} checks`, {
                            sticky: true
                        });
                        
                        lyr.on('mouseover', () => {
                            setHoveredItem(zipCode);
                        });
                        
                        lyr.on('mouseout', () => {
                            setHoveredItem(null);
                        });
                        
                        lyr.on('click', () => {
                            setSelectedZip(zipCode);
                        });
                    }
                });
                
                featureLayersRef.current.set(zipCode, layer);
                geoLayerRef.current.addLayer(layer);
            });
            
            // Fit bounds
            if (hasRenderedZips) {
                try {
                    const bounds = geoLayerRef.current.getBounds();
                    if (bounds && bounds.isValid()) {
                        mapRef.current.fitBounds(bounds, { padding: [40, 40] });
                    }
                } catch (e) {
                    // Fall back to city bounds
                    if (cityBounds && cityBounds.isValid()) {
                        mapRef.current.fitBounds(cityBounds, { padding: [30, 30] });
                    }
                }
            } else if (cityBounds && cityBounds.isValid()) {
                mapRef.current.fitBounds(cityBounds, { padding: [30, 30] });
            }
        }
        
        // Always add point markers for ZIP checks (even if we have polygons, for precision)
        const checksWithCoords = filteredList.filter(c => c.latitude && c.longitude);
        checksWithCoords.forEach(check => {
            const isAvailable = check.availability_status === 'Available';
            const isHovered = hoveredItem === check.zip_code;
            
            const marker = L.circleMarker([check.latitude!, check.longitude!], {
                radius: isHovered ? 10 : 6,
                fillColor: isAvailable ? '#10b981' : '#f43f5e',
                color: '#ffffff',
                weight: 2,
                opacity: 1,
                fillOpacity: 0.9
            });
            
            const tooltipContent = `
                <strong>${check.city || 'Unknown'}</strong><br/>
                ${check.zip_code ? `ZIP: ${check.zip_code}<br/>` : ''}
                <span style="color: ${isAvailable ? '#10b981' : '#f43f5e'}">${check.availability_status}</span>
            `;
            marker.bindTooltip(tooltipContent, { sticky: true });
            
            marker.on('mouseover', () => {
                setHoveredItem(check.zip_code || null);
            });
            
            marker.on('mouseout', () => {
                setHoveredItem(null);
            });
            
            marker.on('click', () => {
                if (check.zip_code) {
                    setSelectedZip(check.zip_code);
                }
            });
            
            markersLayerRef.current.addLayer(marker);
        });
        
        // If no ZIP polygons rendered, fit to marker bounds
        if ((!zipsGeo || zipsGeo.features.length === 0) && checksWithCoords.length > 0) {
            const bounds = L.latLngBounds(checksWithCoords.map(c => [c.latitude!, c.longitude!]));
            mapRef.current.fitBounds(bounds, { padding: [50, 50] });
        }
    }, [viewLevel, selectedState, selectedCity, zipsGeo, citiesGeo, zipsWithData, L, filteredList, getZipAvailability, getPolygonStyle, hoveredItem]);

    // Update hover state on map when sidebar hover changes
    useEffect(() => {
        if (!hoveredItem) return;
        
        const layer = featureLayersRef.current.get(hoveredItem);
        if (layer && layer.setStyle) {
            // For GeoJSON layers - determine status based on view level
            let status: AvailabilityStatus = 'neutral';
            if (viewLevel === 'states') {
                status = statesWithData.includes(hoveredItem) ? getStateAvailability(hoveredItem) : 'neutral';
            } else if (viewLevel === 'counties' && selectedState) {
                status = getCountyAvailability(selectedState, hoveredItem);
            } else if (viewLevel === 'cities' && selectedState && selectedCounty) {
                status = getCityAvailability(selectedState, selectedCounty, hoveredItem);
            } else if (viewLevel === 'zips') {
                const zipChecks = filteredList.filter(c => c.zip_code === hoveredItem);
                status = getZipAvailability(zipChecks);
            }
            layer.setStyle(getPolygonStyle(status, true));
        } else if (layer && layer.setRadius) {
            // For circle markers
            layer.setRadius(12);
        }
        
        return () => {
            if (layer && layer.setStyle) {
                let status: AvailabilityStatus = 'neutral';
                if (viewLevel === 'states') {
                    status = statesWithData.includes(hoveredItem) ? getStateAvailability(hoveredItem) : 'neutral';
                } else if (viewLevel === 'counties' && selectedState) {
                    status = getCountyAvailability(selectedState, hoveredItem);
                } else if (viewLevel === 'cities' && selectedState && selectedCounty) {
                    status = getCityAvailability(selectedState, selectedCounty, hoveredItem);
                } else if (viewLevel === 'zips') {
                    const zipChecks = filteredList.filter(c => c.zip_code === hoveredItem);
                    status = getZipAvailability(zipChecks);
                }
                layer.setStyle(getPolygonStyle(status, false));
            } else if (layer && layer.setRadius) {
                layer.setRadius(8);
            }
        };
    }, [hoveredItem, viewLevel, statesWithData, getStateAvailability, selectedState, selectedCounty, getCountyAvailability, getCityAvailability, getZipAvailability, filteredList, getPolygonStyle]);

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
                // Use the bottom-up getCityAvailability function
                const status = getCityAvailability(selectedState, selectedCounty, city);
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
                        // Use bottom-up getZipAvailability function
                        const status = getZipAvailability(zipChecks);
                        const colors = AVAILABILITY_COLORS[status];
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
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
