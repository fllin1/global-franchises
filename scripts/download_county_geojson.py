#!/usr/bin/env python3
"""
Download US county boundary GeoJSON data and split by state.

This script downloads county boundary data from the Census Bureau's
cartographic boundary files and splits them into individual state files
for efficient loading in the frontend.

Data source: Census Bureau TIGER/Line Cartographic Boundary Files
Resolution: 20m (simplified for web display)
"""

import json
import os
import sys
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError

# State FIPS codes to state abbreviations
FIPS_TO_STATE = {
    '01': 'AL', '02': 'AK', '04': 'AZ', '05': 'AR', '06': 'CA',
    '08': 'CO', '09': 'CT', '10': 'DE', '11': 'DC', '12': 'FL',
    '13': 'GA', '15': 'HI', '16': 'ID', '17': 'IL', '18': 'IN',
    '19': 'IA', '20': 'KS', '21': 'KY', '22': 'LA', '23': 'ME',
    '24': 'MD', '25': 'MA', '26': 'MI', '27': 'MN', '28': 'MS',
    '29': 'MO', '30': 'MT', '31': 'NE', '32': 'NV', '33': 'NH',
    '34': 'NJ', '35': 'NM', '36': 'NY', '37': 'NC', '38': 'ND',
    '39': 'OH', '40': 'OK', '41': 'OR', '42': 'PA', '44': 'RI',
    '45': 'SC', '46': 'SD', '47': 'TN', '48': 'TX', '49': 'UT',
    '50': 'VT', '51': 'VA', '53': 'WA', '54': 'WV', '55': 'WI', 
    '56': 'WY', '72': 'PR', '78': 'VI'  # Include territories
}

# Data sources (in order of preference)
DATA_SOURCES = [
    # Plotly's pre-processed GeoJSON (includes all US counties with FIPS)
    {
        'name': 'Plotly datasets',
        'url': 'https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json',
        'fips_field': 'id',  # FIPS code is in the feature id
    },
    # Alternative: Census Bureau Cartographic Boundaries (need ogr2ogr conversion)
    # These would require additional processing
]


def download_json(url: str) -> dict:
    """Download JSON from URL with proper headers."""
    print(f"Downloading from: {url}")
    
    request = Request(
        url,
        headers={
            'User-Agent': 'Mozilla/5.0 (county-geojson-downloader)',
            'Accept': 'application/json',
        }
    )
    
    try:
        with urlopen(request, timeout=120) as response:
            data = json.loads(response.read().decode('utf-8'))
            return data
    except HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}")
        raise
    except URLError as e:
        print(f"URL Error: {e.reason}")
        raise


def split_by_state(geojson: dict, fips_field: str = 'id') -> dict[str, dict]:
    """Split a GeoJSON FeatureCollection by state FIPS code."""
    state_features = {}
    
    for feature in geojson.get('features', []):
        # Get FIPS code from feature
        if fips_field == 'id':
            fips = str(feature.get('id', ''))
        else:
            fips = str(feature.get('properties', {}).get(fips_field, ''))
        
        if len(fips) < 2:
            continue
            
        # First 2 digits of county FIPS is state FIPS
        state_fips = fips[:2]
        state_code = FIPS_TO_STATE.get(state_fips)
        
        if not state_code:
            print(f"  Unknown state FIPS: {state_fips}")
            continue
        
        if state_code not in state_features:
            state_features[state_code] = []
        
        # Normalize feature properties for consistency
        props = feature.get('properties', {})
        normalized_feature = {
            'type': 'Feature',
            'properties': {
                'NAME': props.get('NAME') or props.get('name') or props.get('NAMELSAD', 'Unknown'),
                'GEOID': fips,
                'STATE': state_code,
                'STATEFP': state_fips,
                'COUNTYFP': fips[2:] if len(fips) >= 5 else '',
                # Keep centroid if available
                'CENTLAT': props.get('CENTLAT') or props.get('INTPTLAT'),
                'CENTLON': props.get('CENTLON') or props.get('INTPTLON'),
            },
            'geometry': feature.get('geometry'),
        }
        
        # Only keep feature if it has geometry
        if normalized_feature['geometry']:
            state_features[state_code].append(normalized_feature)
    
    return state_features


def save_state_files(state_features: dict[str, list], output_dir: Path):
    """Save each state's counties to a separate GeoJSON file."""
    output_dir.mkdir(parents=True, exist_ok=True)
    
    for state_code, features in state_features.items():
        geojson = {
            'type': 'FeatureCollection',
            'features': features
        }
        
        output_file = output_dir / f"{state_code}.geojson"
        
        with open(output_file, 'w') as f:
            json.dump(geojson, f, separators=(',', ':'))  # Compact JSON
        
        file_size = output_file.stat().st_size / 1024
        print(f"  {state_code}: {len(features)} counties ({file_size:.1f} KB)")


def main():
    # Determine output directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    output_dir = project_root / 'frontend' / 'public' / 'geo' / 'counties'
    
    print(f"Output directory: {output_dir}")
    print()
    
    # Try each data source until one works
    geojson = None
    source_info = None
    
    for source in DATA_SOURCES:
        try:
            print(f"Trying source: {source['name']}")
            geojson = download_json(source['url'])
            source_info = source
            print(f"  Success! Downloaded {len(geojson.get('features', []))} features")
            break
        except Exception as e:
            print(f"  Failed: {e}")
            continue
    
    if not geojson:
        print("Error: Could not download county data from any source")
        sys.exit(1)
    
    print()
    print("Splitting by state...")
    state_features = split_by_state(geojson, source_info.get('fips_field', 'id'))
    
    print()
    print(f"Saving {len(state_features)} state files...")
    save_state_files(state_features, output_dir)
    
    # Calculate total size
    total_size = sum(f.stat().st_size for f in output_dir.glob('*.geojson'))
    print()
    print(f"Done! Total size: {total_size / 1024 / 1024:.2f} MB")
    print(f"Files saved to: {output_dir}")


if __name__ == '__main__':
    main()
















