#!/usr/bin/env python3
"""
Download US city/place boundary GeoJSON data per state.

This script downloads city/place boundary data from the Census Bureau's
TIGERweb API (Places layer) and saves them as individual state files
for efficient loading in the frontend.

Data source: Census Bureau TIGERweb - Places (Incorporated Places + CDPs)
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

# TIGERweb API endpoints for Places
# Layer 4 = Incorporated Places (actual cities/towns)
# Layer 5 = Census Designated Places (CDPs - unincorporated communities)
TIGERWEB_INCORPORATED_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/4/query"
)
TIGERWEB_CDP_URL = (
    "https://tigerweb.geo.census.gov/arcgis/rest/services/"
    "TIGERweb/Places_CouSub_ConCity_SubMCD/MapServer/5/query"
)


def download_from_tigerweb(url: str, state_code: str, fips: str, layer_name: str) -> dict:
    """Download place boundaries from a TIGERweb layer."""
    
    # Query parameters for the ArcGIS REST API
    params = {
        'where': f"STATE='{fips}'",
        'outFields': 'NAME,GEOID,STATE,PLACE,LSADC,CENTLAT,CENTLON,AREALAND',
        'outSR': '4326',  # WGS84 coordinate system
        'f': 'geojson',
        'returnGeometry': 'true',
    }
    
    query_string = '&'.join(f"{k}={v}" for k, v in params.items())
    full_url = f"{url}?{query_string}"
    
    print(f"    Downloading {layer_name}...")
    
    request = Request(
        full_url,
        headers={
            'User-Agent': 'Mozilla/5.0 (city-geojson-downloader)',
            'Accept': 'application/json',
        }
    )
    
    try:
        with urlopen(request, timeout=180) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except HTTPError as e:
        print(f"      HTTP Error {e.code}: {e.reason}")
        raise
    except URLError as e:
        print(f"      URL Error: {e.reason}")
        raise


def download_state_cities(state_code: str, fips: str) -> dict:
    """Download city/place boundaries for a single state from TIGERweb.
    
    Downloads from both Incorporated Places and Census Designated Places layers
    and merges them into a single GeoJSON.
    """
    print(f"  Downloading {state_code} cities from TIGERweb...")
    
    all_features = []
    
    # Download Incorporated Places (actual cities/towns)
    try:
        inc_data = download_from_tigerweb(
            TIGERWEB_INCORPORATED_URL, state_code, fips, "Incorporated Places"
        )
        inc_features = inc_data.get('features', [])
        print(f"      Found {len(inc_features)} incorporated places")
        all_features.extend(inc_features)
    except Exception as e:
        print(f"      Incorporated Places failed: {e}")
    
    # Download Census Designated Places (CDPs)
    try:
        cdp_data = download_from_tigerweb(
            TIGERWEB_CDP_URL, state_code, fips, "Census Designated Places"
        )
        cdp_features = cdp_data.get('features', [])
        print(f"      Found {len(cdp_features)} CDPs")
        all_features.extend(cdp_features)
    except Exception as e:
        print(f"      CDPs failed: {e}")
    
    return {
        'type': 'FeatureCollection',
        'features': all_features
    }


def simplify_coordinates(coords, tolerance=0.001):
    """
    Simple Douglas-Peucker-like simplification to reduce coordinate count.
    tolerance is in degrees (~0.001 = ~100m at equator)
    """
    if not coords or len(coords) < 3:
        return coords
    
    # For very long coordinate lists, reduce by keeping every Nth point
    if len(coords) > 100:
        step = max(1, len(coords) // 50)
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
        # Polygon: [[ring1], [ring2], ...]
        simplified_coords = [simplify_coordinates(ring) for ring in coords]
        return {'type': 'Polygon', 'coordinates': simplified_coords}
    
    elif geom_type == 'MultiPolygon':
        # MultiPolygon: [[[ring1], [ring2]], [[ring1]], ...]
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
        
        # Extract city name - remove suffix like "city", "town", etc.
        name = props.get('NAME', 'Unknown')
        
        normalized = {
            'type': 'Feature',
            'properties': {
                'NAME': name,
                'GEOID': props.get('GEOID', ''),
                'STATE': state_code,
                'PLACE': props.get('PLACE', ''),
                'LSADC': props.get('LSADC', ''),  # Legal/Statistical Area Description Code
                'CENTLAT': props.get('CENTLAT'),
                'CENTLON': props.get('CENTLON'),
                'AREALAND': props.get('AREALAND'),  # Land area in sq meters
            },
            'geometry': simplified_geom,
        }
        features.append(normalized)
    
    return features


def save_state_file(state_code: str, features: list, output_dir: Path):
    """Save a state's city boundaries to a GeoJSON file."""
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
        print(f"Downloading cities for specific states: {specific_states}")
    
    # Determine output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'frontend' / 'public' / 'geo' / 'cities'
    
    print(f"Output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    print()
    
    # Determine which states to download
    states_to_download = specific_states if specific_states else list(STATE_FIPS.keys())
    
    total_cities = 0
    total_size = 0
    failed_states = []
    
    for state_code in states_to_download:
        fips = STATE_FIPS.get(state_code)
        if not fips:
            print(f"Unknown state code: {state_code}")
            continue
        
        # Check if file already exists
        output_file = output_dir / f"{state_code}.geojson"
        if output_file.exists() and not specific_states:
            print(f"  {state_code}: Already exists, skipping...")
            total_size += output_file.stat().st_size / 1024
            continue
        
        try:
            # Download from TIGERweb
            geojson = download_state_cities(state_code, fips)
            
            # Normalize and simplify
            features = normalize_features(geojson, state_code)
            
            if not features:
                print(f"    {state_code}: No city features found")
                continue
            
            # Save to file
            file_size = save_state_file(state_code, features, output_dir)
            
            print(f"    {state_code}: {len(features)} cities ({file_size:.1f} KB)")
            total_cities += len(features)
            total_size += file_size
            
            # Be nice to the Census API - add delay between requests
            time.sleep(0.5)
            
        except Exception as e:
            print(f"    {state_code}: Failed - {e}")
            failed_states.append(state_code)
            continue
    
    print()
    print(f"Done!")
    print(f"  Total cities: {total_cities}")
    print(f"  Total size: {total_size / 1024:.2f} MB")
    print(f"  Files saved to: {output_dir}")
    
    if failed_states:
        print(f"  Failed states: {failed_states}")
        print(f"  Re-run with: python {sys.argv[0]} {' '.join(failed_states)}")


if __name__ == '__main__':
    main()

