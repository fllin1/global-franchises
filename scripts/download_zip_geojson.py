#!/usr/bin/env python3
"""
Download US ZIP Code (ZCTA) boundary GeoJSON data per state.

This script downloads ZIP Code Tabulation Area (ZCTA) boundary data from the 
Census Bureau's TIGERweb API and saves them as individual state files
for efficient loading in the frontend.

Data source: Census Bureau TIGERweb - ZCTA (ZIP Code Tabulation Areas)

Note: ZCTAs are statistical representations of USPS ZIP Codes. They may not
perfectly match ZIP Code boundaries but are the best publicly available option.
"""

import json
import os
import sys
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# State FIPS codes to state abbreviations
STATE_FIPS = {
    'AL': '01', 'AK': '02', 'AZ': '04', 'AR': '05', 'CA': '06',
    'CO': '08', 'CT': '09', 'DE': '10', 'DC': '11', 'FL': '12',
    'GA': '13', 'HI': '15', 'ID': '16', 'IL': '17', 'IN': '18',
    'IA': '19', 'KS': '20', 'KY': '21', 'LA': '22', 'ME': '23',
    'MD': '24', 'MA': '25', 'MI': '26', 'MN': '27', 'MS': '28',
    'MO': '29', 'MT': '30', 'NE': '31', 'NV': '32', 'NH': '33',
    'NJ': '34', 'NM': '35', 'NY': '36', 'NC': '37', 'ND': '38',
    'OH': '39', 'OK': '40', 'OR': '41', 'PA': '42', 'RI': '44',
    'SC': '45', 'SD': '46', 'TN': '47', 'TX': '48', 'UT': '49',
    'VT': '50', 'VA': '51', 'WA': '53', 'WV': '54', 'WI': '55', 
    'WY': '56', 'PR': '72'
}

# State bounding boxes for filtering ZCTAs (lon_min, lat_min, lon_max, lat_max)
# Used to query ZCTAs that intersect with each state
STATE_BBOXES = {
    'AL': (-88.5, 30.1, -84.9, 35.0),
    'AK': (-180.0, 51.2, -130.0, 71.5),
    'AZ': (-114.8, 31.3, -109.0, 37.0),
    'AR': (-94.6, 33.0, -89.6, 36.5),
    'CA': (-124.4, 32.5, -114.1, 42.0),
    'CO': (-109.1, 36.9, -102.0, 41.0),
    'CT': (-73.7, 40.9, -71.8, 42.1),
    'DE': (-75.8, 38.4, -75.0, 39.8),
    'DC': (-77.1, 38.8, -76.9, 39.0),
    'FL': (-87.6, 24.5, -80.0, 31.0),
    'GA': (-85.6, 30.4, -80.8, 35.0),
    'HI': (-160.3, 18.9, -154.8, 22.2),
    'ID': (-117.2, 42.0, -111.0, 49.0),
    'IL': (-91.5, 37.0, -87.0, 42.5),
    'IN': (-88.1, 37.8, -84.8, 41.8),
    'IA': (-96.6, 40.4, -90.1, 43.5),
    'KS': (-102.1, 37.0, -94.6, 40.0),
    'KY': (-89.6, 36.5, -82.0, 39.1),
    'LA': (-94.0, 29.0, -89.0, 33.0),
    'ME': (-71.1, 43.1, -66.9, 47.5),
    'MD': (-79.5, 37.9, -75.0, 39.7),
    'MA': (-73.5, 41.2, -69.9, 42.9),
    'MI': (-90.4, 41.7, -82.4, 48.2),
    'MN': (-97.2, 43.5, -89.5, 49.4),
    'MS': (-91.7, 30.2, -88.1, 35.0),
    'MO': (-95.8, 36.0, -89.1, 40.6),
    'MT': (-116.0, 45.0, -104.0, 49.0),
    'NE': (-104.1, 40.0, -95.3, 43.0),
    'NV': (-120.0, 35.0, -114.0, 42.0),
    'NH': (-72.6, 42.7, -70.7, 45.3),
    'NJ': (-75.6, 38.9, -73.9, 41.4),
    'NM': (-109.1, 31.3, -103.0, 37.0),
    'NY': (-79.8, 40.5, -71.9, 45.0),
    'NC': (-84.3, 33.8, -75.5, 36.6),
    'ND': (-104.1, 45.9, -96.6, 49.0),
    'OH': (-84.8, 38.4, -80.5, 42.0),
    'OK': (-103.0, 33.6, -94.4, 37.0),
    'OR': (-124.6, 42.0, -116.5, 46.3),
    'PA': (-80.5, 39.7, -74.7, 42.3),
    'RI': (-71.9, 41.1, -71.1, 42.0),
    'SC': (-83.4, 32.0, -78.5, 35.2),
    'SD': (-104.1, 42.5, -96.4, 46.0),
    'TN': (-90.3, 35.0, -81.6, 36.7),
    'TX': (-106.7, 25.8, -93.5, 36.5),
    'UT': (-114.1, 37.0, -109.0, 42.0),
    'VT': (-73.4, 42.7, -71.5, 45.0),
    'VA': (-83.7, 36.5, -75.2, 39.5),
    'WA': (-124.8, 45.5, -116.9, 49.0),
    'WV': (-82.6, 37.2, -77.7, 40.6),
    'WI': (-92.9, 42.5, -86.8, 47.1),
    'WY': (-111.1, 41.0, -104.1, 45.0),
    'PR': (-67.3, 17.9, -65.6, 18.5),
}

# TIGERweb API endpoint for ZCTA (ZIP Code Tabulation Areas)
# Layer 1 = 2020 Census ZIP Code Tabulation Areas
TIGERWEB_ZCTA_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/PUMA_TAD_TAZ_UGA_ZCTA/MapServer/1/query"
)


def download_state_zips(state_code: str, bbox: tuple) -> dict:
    """Download ZCTA boundaries for a state using bounding box from TIGERweb.
    
    Uses pagination to handle large result sets.
    """
    
    lon_min, lat_min, lon_max, lat_max = bbox
    
    print(f"  Downloading {state_code} ZIPs from TIGERweb (bbox: {bbox})...")
    
    all_features = []
    offset = 0
    batch_size = 500  # Max records per request
    
    while True:
        # Query parameters for the ArcGIS REST API
        params = {
            'where': '1=1',
            'geometry': f'{lon_min},{lat_min},{lon_max},{lat_max}',
            'geometryType': 'esriGeometryEnvelope',
            'inSR': '4326',
            'spatialRel': 'esriSpatialRelIntersects',
            'outFields': 'ZCTA5,GEOID,CENTLAT,CENTLON,AREALAND,AREAWATER',
            'outSR': '4326',
            'f': 'geojson',
            'returnGeometry': 'true',
            'resultOffset': str(offset),
            'resultRecordCount': str(batch_size),
        }
        
        query_string = '&'.join(f"{k}={v}" for k, v in params.items())
        url = f"{TIGERWEB_ZCTA_URL}?{query_string}"
        
        request = Request(
            url,
            headers={
                'User-Agent': 'Mozilla/5.0 (zip-geojson-downloader)',
                'Accept': 'application/json',
            }
        )
        
        try:
            with urlopen(request, timeout=300) as response:
                data = json.loads(response.read().decode('utf-8'))
                features = data.get('features', [])
                
                if not features:
                    break
                
                all_features.extend(features)
                print(f"    Fetched {len(features)} ZCTAs (total: {len(all_features)})...")
                
                # Check if we've got all records
                if len(features) < batch_size:
                    break
                    
                offset += batch_size
                time.sleep(0.3)  # Small delay between pagination requests
                
        except HTTPError as e:
            print(f"    HTTP Error {e.code}: {e.reason}")
            raise
        except URLError as e:
            print(f"    URL Error: {e.reason}")
            raise
    
    return {
        'type': 'FeatureCollection',
        'features': all_features
    }


def simplify_coordinates(coords, tolerance=0.0005):
    """
    Simple coordinate reduction to decrease file size.
    tolerance is in degrees (~0.0005 = ~50m at equator)
    """
    if not coords or len(coords) < 3:
        return coords
    
    # For very long coordinate lists, reduce by keeping every Nth point
    if len(coords) > 50:
        step = max(1, len(coords) // 25)
        simplified = coords[::step]
        # Always include the last point to close polygons
        if coords[-1] != simplified[-1]:
            simplified.append(coords[-1])
        return simplified
    
    return coords


def simplify_geometry(geometry):
    """Simplify a GeoJSON geometry to reduce file size."""
    if not geometry:
        return geometry
    
    geom_type = geometry.get('type')
    coords = geometry.get('coordinates')
    
    if not coords:
        return geometry
    
    if geom_type == 'Polygon':
        simplified_coords = [simplify_coordinates(ring) for ring in coords]
        return {'type': 'Polygon', 'coordinates': simplified_coords}
    
    elif geom_type == 'MultiPolygon':
        simplified_coords = [
            [simplify_coordinates(ring) for ring in polygon]
            for polygon in coords
        ]
        return {'type': 'MultiPolygon', 'coordinates': simplified_coords}
    
    return geometry


def normalize_features(geojson: dict, state_code: str) -> list:
    """Normalize and simplify features for consistent frontend usage."""
    features = []
    
    for feature in geojson.get('features', []):
        props = feature.get('properties', {})
        geometry = feature.get('geometry')
        
        if not geometry:
            continue
        
        # Simplify geometry to reduce file size
        simplified_geom = simplify_geometry(geometry)
        
        # Get ZIP code
        zip_code = props.get('ZCTA5') or props.get('GEOID', '')
        
        if not zip_code:
            continue
        
        normalized = {
            'type': 'Feature',
            'properties': {
                'ZCTA5': zip_code,
                'GEOID': props.get('GEOID', zip_code),
                'STATE': state_code,
                'CENTLAT': props.get('CENTLAT'),
                'CENTLON': props.get('CENTLON'),
                'AREALAND': props.get('AREALAND'),
                'AREAWATER': props.get('AREAWATER'),
            },
            'geometry': simplified_geom,
        }
        features.append(normalized)
    
    return features


def save_state_file(state_code: str, features: list, output_dir: Path):
    """Save a state's ZIP boundaries to a GeoJSON file."""
    geojson = {
        'type': 'FeatureCollection',
        'features': features
    }
    
    output_file = output_dir / f"{state_code}.geojson"
    
    with open(output_file, 'w') as f:
        json.dump(geojson, f, separators=(',', ':'))  # Compact JSON
    
    file_size = output_file.stat().st_size / 1024
    return file_size


def main():
    # Parse command line arguments
    specific_states = None
    if len(sys.argv) > 1:
        specific_states = [s.upper() for s in sys.argv[1:]]
        print(f"Downloading ZIPs for specific states: {specific_states}")
    
    # Determine output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'frontend' / 'public' / 'geo' / 'zips'
    
    print(f"Output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print()
    
    # Determine which states to download
    states_to_download = specific_states if specific_states else list(STATE_FIPS.keys())
    
    total_zips = 0
    total_size = 0
    failed_states = []
    
    for state_code in states_to_download:
        bbox = STATE_BBOXES.get(state_code)
        if not bbox:
            print(f"No bounding box for state: {state_code}")
            continue
        
        # Check if file already exists
        output_file = output_dir / f"{state_code}.geojson"
        if output_file.exists() and not specific_states:
            print(f"  {state_code}: Already exists, skipping...")
            total_size += output_file.stat().st_size / 1024
            continue
        
        try:
            # Download from TIGERweb
            geojson = download_state_zips(state_code, bbox)
            
            # Normalize and simplify
            features = normalize_features(geojson, state_code)
            
            if not features:
                print(f"    {state_code}: No ZIP features found")
                continue
            
            # Save to file
            file_size = save_state_file(state_code, features, output_dir)
            
            print(f"    {state_code}: {len(features)} ZIPs ({file_size:.1f} KB)")
            total_zips += len(features)
            total_size += file_size
            
            # Be nice to the Census API - add delay between requests
            time.sleep(1.0)  # Longer delay for ZCTA queries (larger data)
            
        except Exception as e:
            print(f"    {state_code}: Failed - {e}")
            failed_states.append(state_code)
            continue
    
    print()
    print(f"Done!")
    print(f"  Total ZIPs: {total_zips}")
    print(f"  Total size: {total_size / 1024:.2f} MB")
    print(f"  Files saved to: {output_dir}")
    
    if failed_states:
        print(f"  Failed states: {failed_states}")
        print(f"  Re-run with: python {sys.argv[0]} {' '.join(failed_states)}")


if __name__ == '__main__':
    main()

