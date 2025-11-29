/**
 * Geographic utility functions for loading and processing GeoJSON boundary data.
 * Used by the Territory Availability Map component.
 */

import type { Feature, FeatureCollection, Geometry } from 'geojson';

// State code to FIPS code mapping for Census API
const STATE_FIPS: Record<string, string> = {
  'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
  'CO': '08', 'CT': '09', 'DE': '10', 'DC': '11', 'FL': '12',
  'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
  'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23',
  'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
  'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33',
  'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38',
  'OH': '39', 'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44',
  'SC': '45', 'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49',
  'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 'WY': '56'
};

// State code to full name mapping
export const STATE_NAMES: Record<string, string> = {
  'AL': 'Alabama', 'AK': 'Alaska', 'AZ': 'Arizona', 'AR': 'Arkansas', 'CA': 'California',
  'CO': 'Colorado', 'CT': 'Connecticut', 'DE': 'Delaware', 'DC': 'District of Columbia', 'FL': 'Florida',
  'GA': 'Georgia', 'HI': 'Hawaii', 'ID': 'Idaho', 'IL': 'Illinois', 'IN': 'Indiana',
  'IA': 'Iowa', 'KS': 'Kansas', 'KY': 'Kentucky', 'LA': 'Louisiana', 'ME': 'Maine',
  'MD': 'Maryland', 'MA': 'Massachusetts', 'MI': 'Michigan', 'MN': 'Minnesota', 'MS': 'Mississippi',
  'MO': 'Missouri', 'MT': 'Montana', 'NE': 'Nebraska', 'NV': 'Nevada', 'NH': 'New Hampshire',
  'NJ': 'New Jersey', 'NM': 'New Mexico', 'NY': 'New York', 'NC': 'North Carolina', 'ND': 'North Dakota',
  'OH': 'Ohio', 'OK': 'Oklahoma', 'OR': 'Oregon', 'PA': 'Pennsylvania', 'RI': 'Rhode Island',
  'SC': 'South Carolina', 'SD': 'South Dakota', 'TN': 'Tennessee', 'TX': 'Texas', 'UT': 'Utah',
  'VT': 'Vermont', 'VA': 'Virginia', 'WA': 'Washington', 'WV': 'West Virginia', 'WI': 'Wisconsin', 'WY': 'Wyoming'
};

// Cache for loaded GeoJSON data
const geoCache: Map<string, FeatureCollection> = new Map();

/**
 * Load US States boundaries GeoJSON from local file
 */
export async function fetchStatesBoundaries(): Promise<FeatureCollection> {
  const cacheKey = 'us-states';
  if (geoCache.has(cacheKey)) {
    return geoCache.get(cacheKey)!;
  }

  try {
    const response = await fetch('/geo/us-states.geojson');
    if (!response.ok) {
      throw new Error(`Failed to load states GeoJSON: ${response.status}`);
    }
    const data = await response.json() as FeatureCollection;
    geoCache.set(cacheKey, data);
    return data;
  } catch (error) {
    console.error('Error loading states boundaries:', error);
    throw error;
  }
}

/**
 * Fetch county boundaries for a specific state.
 * Priority: 1) Local files, 2) Census TIGER API, 3) GitHub TopoJSON fallback
 */
export async function fetchCountyBoundaries(stateCode: string): Promise<FeatureCollection> {
  const upperStateCode = stateCode.toUpperCase();
  const fips = STATE_FIPS[upperStateCode];
  if (!fips) {
    throw new Error(`Invalid state code: ${stateCode}`);
  }

  const cacheKey = `counties-${upperStateCode}`;
  if (geoCache.has(cacheKey)) {
    return geoCache.get(cacheKey)!;
  }

  // Priority 1: Try local GeoJSON files (most reliable, no network issues)
  try {
    const localUrl = `/geo/counties/${upperStateCode}.geojson`;
    console.log(`Loading county boundaries for ${upperStateCode} from local file...`);
    const response = await fetch(localUrl);
    
    if (response.ok) {
      const data = await response.json() as FeatureCollection;
      if (data.features && data.features.length > 0) {
        console.log(`Loaded ${data.features.length} counties for ${upperStateCode} from local file`);
        geoCache.set(cacheKey, data);
        return data;
      }
    }
    console.warn(`Local county file not found for ${upperStateCode}, trying TIGER API...`);
  } catch (error) {
    console.warn(`Failed to load local county file for ${upperStateCode}:`, error);
  }

  // Priority 2: Try Census TIGER Web API
  try {
    const tigerUrl = `https://tigerweb.geo.census.gov/arcgis/rest/services/TIGERweb/State_County/MapServer/1/query?` + 
      `where=STATE='${fips}'&` +
      `outFields=NAME,STATE,COUNTY,GEOID,CENTLAT,CENTLON&` +
      `outSR=4326&` +
      `f=geojson`;
    
    console.log(`Fetching county boundaries for ${upperStateCode} from Census TIGER API...`);
    const response = await fetch(tigerUrl);
    
    if (response.ok) {
      const data = await response.json() as FeatureCollection;
      
      if (data.features && data.features.length > 0) {
        // Normalize county names in properties for easier matching
        const normalizedData: FeatureCollection = {
          type: 'FeatureCollection',
          features: data.features.map(f => ({
            ...f,
            properties: {
              ...f.properties,
              NAME: f.properties?.NAME || f.properties?.name || 'Unknown',
              STATE: upperStateCode,
              GEOID: f.properties?.GEOID,
              CENTLAT: f.properties?.CENTLAT,
              CENTLON: f.properties?.CENTLON
            }
          }))
        };

        console.log(`Loaded ${normalizedData.features.length} counties for ${upperStateCode} from TIGER API`);
        geoCache.set(cacheKey, normalizedData);
        return normalizedData;
      }
    }
    console.warn(`Census TIGER API failed for ${upperStateCode}, trying GitHub fallback...`);
  } catch (error) {
    console.warn(`TIGER API error for ${upperStateCode}:`, error);
  }

  // Priority 3: Fall back to GitHub TopoJSON
  return await fetchCountyBoundariesFallback(upperStateCode);
}

/**
 * Last resort fallback to GitHub-hosted TopoJSON
 */
async function fetchCountyBoundariesFallback(stateCode: string): Promise<FeatureCollection> {
  const cacheKey = `counties-${stateCode}`;
  
  try {
    const stateName = STATE_NAMES[stateCode]?.replace(/\s+/g, '-');
    if (!stateName) {
      console.warn(`No state name mapping for ${stateCode}`);
      return { type: 'FeatureCollection', features: [] };
    }
    
    const url = `https://raw.githubusercontent.com/deldersveld/topojson/master/countries/us-states/${stateName}-counties.json`;
    console.log(`Fetching county boundaries for ${stateCode} from GitHub fallback...`);
    
    const response = await fetch(url);
    
    if (!response.ok) {
      console.warn(`GitHub fallback data not available for ${stateCode}`);
      return { type: 'FeatureCollection', features: [] };
    }

    const topoData = await response.json();
    
    // Convert TopoJSON to GeoJSON if needed
    const geoData = convertTopoJSONToGeoJSON(topoData, stateCode);
    
    if (geoData.features.length > 0) {
      console.log(`Loaded ${geoData.features.length} counties for ${stateCode} from GitHub fallback`);
      geoCache.set(cacheKey, geoData);
    }
    
    return geoData;
  } catch (error) {
    console.error(`All county loading methods failed for ${stateCode}:`, error);
    return { type: 'FeatureCollection', features: [] };
  }
}

/**
 * Fetch ZIP code boundaries for a specific area
 * Note: ZIP code boundaries are large, so we only load on-demand for specific areas
 */
export async function fetchZipBoundaries(stateCode: string, county?: string): Promise<FeatureCollection> {
  const cacheKey = `zips-${stateCode}-${county || 'all'}`;
  if (geoCache.has(cacheKey)) {
    return geoCache.get(cacheKey)!;
  }

  try {
    // ZIP code boundaries are typically very large files
    // For now, we'll return an empty collection and use point markers for ZIPs
    // In production, you'd use a spatial database or tile server
    console.log(`ZIP boundary data would be loaded for ${stateCode}/${county}`);
    
    const emptyCollection: FeatureCollection = {
      type: 'FeatureCollection',
      features: []
    };
    
    geoCache.set(cacheKey, emptyCollection);
    return emptyCollection;
  } catch (error) {
    console.error(`Error loading ZIP boundaries:`, error);
    return { type: 'FeatureCollection', features: [] };
  }
}

/**
 * Convert TopoJSON to GeoJSON (simplified conversion)
 */
function convertTopoJSONToGeoJSON(topoData: any, stateCode: string): FeatureCollection {
  try {
    // Check if it's already GeoJSON
    if (topoData.type === 'FeatureCollection') {
      return topoData;
    }

    // Simple TopoJSON conversion
    if (topoData.type === 'Topology' && topoData.objects) {
      const objectKey = Object.keys(topoData.objects)[0];
      const geometries = topoData.objects[objectKey]?.geometries || [];
      
      const features: Feature[] = geometries.map((geo: any) => ({
        type: 'Feature' as const,
        properties: {
          ...geo.properties,
          STATE: stateCode,
          COUNTY: geo.properties?.NAME || geo.properties?.name || 'Unknown'
        },
        geometry: decodeTopoJSONGeometry(geo, topoData.arcs, topoData.transform)
      }));

      return {
        type: 'FeatureCollection',
        features
      };
    }

    return { type: 'FeatureCollection', features: [] };
  } catch (e) {
    console.error('TopoJSON conversion error:', e);
    return { type: 'FeatureCollection', features: [] };
  }
}

/**
 * Decode TopoJSON arc-based geometry to GeoJSON coordinates
 */
function decodeTopoJSONGeometry(geometry: any, arcs: number[][][], transform?: any): Geometry {
  if (!geometry || !arcs) {
    return { type: 'Polygon', coordinates: [] };
  }

  const decodeArc = (arcIndex: number): number[][] => {
    const arc = arcs[arcIndex < 0 ? ~arcIndex : arcIndex];
    if (!arc) return [];
    
    let coords = arc.map((point, i) => {
      if (i === 0 || !transform) return point;
      // Apply delta decoding if needed
      return point;
    });
    
    if (arcIndex < 0) coords = coords.slice().reverse();
    return coords;
  };

  const decodeRing = (ring: number[]): number[][] => {
    return ring.flatMap(arcIndex => decodeArc(arcIndex));
  };

  try {
    if (geometry.type === 'Polygon') {
      const coordinates = (geometry.arcs || []).map((ring: number[]) => decodeRing(ring));
      return { type: 'Polygon', coordinates };
    } else if (geometry.type === 'MultiPolygon') {
      const coordinates = (geometry.arcs || []).map((polygon: number[][]) =>
        polygon.map((ring: number[]) => decodeRing(ring))
      );
      return { type: 'MultiPolygon', coordinates };
    }
  } catch (e) {
    console.error('Geometry decode error:', e);
  }

  return { type: 'Polygon', coordinates: [] };
}

/**
 * Get the bounding box for a GeoJSON feature
 */
export function getFeatureBounds(feature: Feature): [[number, number], [number, number]] | null {
  if (!feature.geometry) return null;
  
  const coords = getAllCoordinates(feature.geometry);
  if (coords.length === 0) return null;
  
  let minLat = Infinity, maxLat = -Infinity;
  let minLng = Infinity, maxLng = -Infinity;
  
  coords.forEach(([lng, lat]) => {
    minLat = Math.min(minLat, lat);
    maxLat = Math.max(maxLat, lat);
    minLng = Math.min(minLng, lng);
    maxLng = Math.max(maxLng, lng);
  });
  
  return [[minLat, minLng], [maxLat, maxLng]];
}

/**
 * Extract all coordinates from a geometry
 */
function getAllCoordinates(geometry: Geometry): number[][] {
  const coords: number[][] = [];
  
  function extract(arr: any): void {
    if (Array.isArray(arr)) {
      if (arr.length === 2 && typeof arr[0] === 'number' && typeof arr[1] === 'number') {
        coords.push(arr as number[]);
      } else {
        arr.forEach(extract);
      }
    }
  }
  
  if ('coordinates' in geometry) {
    extract(geometry.coordinates);
  }
  
  return coords;
}

/**
 * Find a feature by state code in a FeatureCollection
 */
export function findStateFeature(collection: FeatureCollection, stateCode: string): Feature | undefined {
  const upperCode = stateCode.toUpperCase();
  const fullName = STATE_NAMES[upperCode];
  
  return collection.features.find(f => {
    const props = f.properties || {};
    // Check various property names that might contain the state identifier
    return props.STUSPS === upperCode || 
           props.STATE === upperCode || 
           props.state === stateCode ||
           props.postal === upperCode ||
           props.name === fullName ||
           props.NAME === fullName;
  });
}

/**
 * Get state code from a GeoJSON feature
 */
export function getStateCodeFromFeature(feature: Feature): string | null {
  const props = feature.properties || {};
  
  // Check for direct state code properties
  if (props.STUSPS) return props.STUSPS;
  if (props.STATE && typeof props.STATE === 'string' && props.STATE.length === 2) return props.STATE;
  if (props.postal) return props.postal;
  
  // Check by full name
  const name = props.name || props.NAME;
  if (name) {
    const entry = Object.entries(STATE_NAMES).find(([, fullName]) => fullName === name);
    if (entry) return entry[0];
  }
  
  // Check by FIPS code (the feature id)
  const fipsCode = feature.id?.toString().padStart(2, '0');
  if (fipsCode) {
    const entry = Object.entries(STATE_FIPS).find(([, fips]) => fips === fipsCode);
    if (entry) return entry[0];
  }
  
  return null;
}

/**
 * Find a feature by county name in a FeatureCollection
 */
export function findCountyFeature(collection: FeatureCollection, countyName: string): Feature | undefined {
  const normalizedName = countyName.toLowerCase().replace(/\s+county$/i, '').trim();
  
  return collection.features.find(f => {
    const props = f.properties || {};
    const featureName = (props.NAME || props.name || props.COUNTY || '').toLowerCase().replace(/\s+county$/i, '').trim();
    return featureName === normalizedName;
  });
}

/**
 * Clear the geo cache (useful for testing or memory management)
 */
export function clearGeoCache(): void {
  geoCache.clear();
}

