# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2025-12-02] - Related Brands Section for Franchise Family

### Added
- **"More from [Family Name]" Section** on franchise detail page:
  - Displays sibling franchises from the same family brand
  - Shows up to 6 related franchises with logo, name, category, and investment range
  - Links to individual franchise pages and family brand overview
  - Gradient violet/indigo styling to visually distinguish from other sections
  - Only appears when franchise belongs to a family brand with other franchises

### Changed
- **Backend API** (`src/backend/franchises.py`):
  - Extended `GET /api/franchises/{id}` to return `sibling_franchises` array when franchise belongs to a family
  - Fetches up to 6 sibling franchises (excluding current), ordered alphabetically

- **Frontend Types** (`frontend/src/types/index.ts`):
  - Added `SiblingFranchise` interface for sibling franchise data
  - Added `sibling_franchises` field to `FranchiseDetail` interface

- **Franchise Detail Page** (`frontend/src/app/franchises/[id]/page.tsx`):
  - Added `RelatedBrandsCard` component at the bottom of the overview tab
  - Component renders responsive grid (1/2/3 columns) of sibling franchise cards

---

## [2025-12-02] - Franchise Directory Table Redesign

### Changed
- **Franchise Directory Page Redesign** (`frontend/src/app/franchises/page.tsx`):
  - Converted from card grid layout to clean table layout matching the Family Brands page aesthetic
  - Added header icon badge with Building icon in indigo background
  - Added stats bar showing total franchise count and selected count for comparison
  - Added table columns: Select (checkbox), Franchise (logo + name), Category, Min Investment, Action
  - Added full dark mode support with proper color variants
  - Added logo display in franchise column using Next.js Image component with fallback icon on error
  - Left-aligned search bar (previously centered)
  - Increased max width from 5xl to 6xl for better table display
  - Preserved comparison checkbox functionality (moved to first table column)
  - Added "Compare" button in stats bar when franchises are selected

- **Frontend Types** (`frontend/src/types/index.ts`):
  - Added `logo_url?: string` field to `FranchiseMatch` interface

- **Search Franchises Action** (`frontend/src/app/franchises/actions.ts`):
  - Now maps `logo_url` from API response to support logo display in directory

- **Backend API** (`src/backend/franchises.py`):
  - Added `logo_url` to the select statement in `/api/franchises/search` endpoint to return logo URLs in search results

---

## [2025-12-02] - Franchise Logo URL Support

### Added
- **Database Schema**: Added `logo_url` column to `franchises` table for storing franchise brand logos
- **Database View**: Updated `franchises_with_family` view to include `logo_url` column
- **LLM Extraction Schema**: Updated `config/franserve/structured_output.json` to extract logo URLs from franchise pages
- **HTML Formatter**: Updated `src/data/franserve/html_formatter.py` to parse logo images from `images/logos/` path
- **Backfill Script**: Created `src/backend/scripts/backfill_logo_urls.py` to populate logo URLs for existing franchises
- **Frontend Types**: Added `logo_url` to `FranchiseDetail` type in `frontend/src/types/index.ts`
- **Frontend Display**: Updated franchise detail page header to display logo alongside franchise name

### Technical Details
- Logo URLs are extracted from `<img src='images/logos/...'>` tags in franchise HTML pages
- Full URLs are constructed by prepending `https://franservesupport.com/` to relative paths
- Backfill script reads HTML from Supabase Storage and updates franchises missing logo_url
- Run backfill with: `python -m src.backend.scripts.backfill_logo_urls` (use `--dry-run` for testing)
- Logo displayed in 80x80px container with white background and subtle border
- 754 out of 810 franchises now have logos populated

---

## [2025-12-02] - Family of Brands Frontend Feature

### Added
- **Family Brands Frontend Pages**:
  - Created `/family-brands` list page with search/filter functionality
  - Created `/family-brands/[id]` detail page showing family brand info and all representing franchises
  - Table/list view with logo, name, franchise count, website link, and action buttons

- **Backend API Endpoints** (`src/backend/franchises.py`):
  - `GET /api/family-brands/` - List all family brands with franchise counts
  - `GET /api/family-brands/{id}` - Get family brand details with all representing franchises
  - Updated `GET /api/franchises/{id}` to include family brand info via `franchises_with_family` view

- **Frontend Types** (`frontend/src/types/index.ts`):
  - Added `FamilyBrand` interface for list views
  - Added `FamilyBrandFranchise` interface for representing brands
  - Added `FamilyBrandDetail` interface extending `FamilyBrand` with franchises array
  - Extended `FranchiseDetail` with `parent_family_brand_id` and `family_brand` properties

- **Frontend Actions** (`frontend/src/app/franchises/actions.ts`):
  - Added `getFamilyBrands(query?)` - Fetch all family brands with optional search
  - Added `getFamilyBrandDetail(id)` - Fetch single family brand with franchises

- **Franchise Detail Page Enhancement**:
  - Added "Part of [Family Brand]" badge in header for franchises belonging to a family
  - Badge links directly to the family brand detail page
  - Uses violet color scheme to distinguish from other badges

- **Sidebar Navigation** (`frontend/src/components/Sidebar.tsx`):
  - Added "Family Brands" nav item with Network icon
  - Positioned between "Franchises" and "Territory Map"

### Technical Details
- Family brands list supports real-time search with 300ms debounce
- Stats bar shows total family brands and total linked franchises
- Detail page displays contact info (name, phone, email) when available
- Franchise cards in family brand detail show category, description, and min investment
- Full dark mode support across all new pages

### Fixed
- Removed reliance on non-existent RPC function `count_franchises_per_family_brand`
- Franchise counts now calculated efficiently by fetching all linked franchises in a single query

---

## [2025-12-02] - Family of Brands Feature

### Added
- **Family of Brands Database Schema**:
  - Created `family_of_brands` table to store parent brand entities (e.g., Driven Brands, Neighborly, Authority Brands)
  - Added `parent_family_brand_id` foreign key to `franchises` table to link franchises to their parent family brands
  - Created `franchises_with_family` view for convenient querying
  - Migration: `docs/database/add_family_of_brands_tables.sql`

- **Family of Brands Scraper** (`src/data/franserve/family_brands_scraper.py`):
  - `get_family_brands_list()`: Fetches all family brands from AJAX endpoint
  - `scrape_family_brand_page()`: Scrapes individual family brand detail pages
  - `parse_family_brand_html()`: Parses HTML to extract family brand data
  - `extract_representing_brands()`: Extracts list of franchise brands in each family
  - `save_family_brand_to_db()`: Upserts family brand records
  - `link_franchises_to_family_brand()`: Links franchises to their parent family brand

- **CLI Script** (`src/backend/scripts/run_family_brands_scraper.py`):
  - `--list-only`: Lists all family brands without scraping details
  - `--single FRAN_ID`: Scrapes a single family brand by FranID
  - `--stats`: Shows database statistics for family brands
  - Default: Full scrape of all family brands

### Results
- Successfully scraped 33 family brands
- Linked 154 franchises (19% of total) to their parent family brands
- Top family brands by franchise count: Neighborly (18), Authority Brands (14), Belfor Franchise Group (11)

## [2025-12-01] - Enhanced Hierarchical Territory Availability Logic

### Added
- **Hierarchical Override System for Territory Availability**:
  - Implemented a new availability calculation system where `unavailable_states` from franchise data provides the **default** state-level availability.
  - Territory checks can now **override** this default to create "mixed" (yellow) status:
    - If a state is in `unavailable_states` but has ANY "Available" territory check → shows as "mixed"
    - If a state is NOT in `unavailable_states` but has ANY "Not Available" territory check → shows as "mixed"
  - Sub-regions (counties, cities) without explicit territory checks now **inherit** from the parent state's default status.

- **New Helper Functions** (`FranchiseTerritoryMap.client.tsx`):
  - `isStateDefaultUnavailable(stateCode)`: Checks if state is in franchise's `unavailable_states` array
  - `getAllChecksInState(stateCode)`: Flattens territory check hierarchy to get all checks for a state
  - `stateHasAnyAvailableCheck(stateCode)`: Checks if state has any "Available" territory check
  - `stateHasAnyUnavailableCheck(stateCode)`: Checks if state has any "Not Available" territory check

- **Documentation**:
  - Created `docs/TERRITORY_AVAILABILITY_LOGIC.md` with comprehensive documentation of the availability system
  - Includes visual diagrams, logic flowcharts, and testing scenarios

### Changed
- **State Availability Logic** (`getStateAvailability`):
  - Now uses default + override pattern instead of simple aggregation
  - States in `unavailable_states` remain red UNLESS they have an Available check (then mixed)
  - States NOT in `unavailable_states` remain green UNLESS they have an Unavailable check (then mixed)

- **County Availability Logic** (`getCountyAvailability`):
  - Counties with territory checks use existing aggregation logic
  - Counties WITHOUT territory checks now inherit from state's default status
  - Previously defaulted to "available" regardless of parent state

- **City Availability Logic** (`getCityAvailability`):
  - Cities with territory checks use existing aggregation logic
  - Cities WITHOUT territory checks now inherit from state's default status
  - Previously defaulted to "available" regardless of parent state

### Fixed
- **Illinois (Franchise 626) Now Shows Correctly**:
  - IL is in `unavailable_states` (default: red)
  - IL has Naperville (Available) and Chicago (Not Available) checks
  - IL now shows as yellow/mixed instead of all red
  - When drilling into IL, counties without checks show as red (inherit default)

- **Data Structure Handling**:
  - Fixed `getAllChecksInState` to handle both 3-level and 4-level data structures
  - Handles cases where API returns checks directly under city keys vs nested under county keys

### Example
For Franchise 626:
| State | In unavailable_states? | Has Available Check? | Result |
|-------|----------------------|---------------------|--------|
| IL | Yes | Yes (Naperville) | Mixed 🟡 |
| VA | Yes | No | Unavailable 🔴 |
| TX | No | - | Available 🟢 |
| NC | No | - | Available 🟢 |

## [2025-12-01] - Fix Numeric City Values in Territory Checks

### Fixed
- **Territory Map Displaying Numbers Instead of City Names**:
  - Fixed issue where territory map UI was displaying numbers (0, 1, 2, 3, 4) instead of city names.
  - Root cause: Some records in `territory_checks` table had numeric strings stored in the `city` field instead of actual city names.
  - Solutions implemented:
    1. Created diagnostic script (`src/backend/scripts/diagnose_numeric_cities.py`) to identify affected records
    2. Created cleanup script (`src/backend/scripts/fix_numeric_cities.py`) to fix existing records by:
       - Extracting city names from `location_raw` using regex patterns
       - Using LLM parsing to extract city from `location_raw` if regex fails
       - Looking up city from `zip_code` using pgeocode
       - Setting city to NULL if none of the above methods work (displays as "Unspecified Area")
    3. Added validation to prevent future issues:
       - `is_valid_city_name()` function added to reject numeric-only city values
       - Validation added to `parse_territory_check()` in `field_mapper.py`
       - Validation added to `enrich_with_geocode()`, `update_record_with_parsed_data()`, and `insert_split_record()` in `parse_territory_locations.py`
       - Validation added to `process_batch()` in `normalize_territories.py`
    4. Added frontend filtering in `FranchiseTerritoryMap.client.tsx` to filter out numeric city values as a safety measure
  - Modified files:
    - `src/backend/scripts/diagnose_numeric_cities.py` (new)
    - `src/backend/scripts/fix_numeric_cities.py` (new)
    - `src/data/functions/field_mapper.py` - Added validation
    - `src/backend/scripts/parse_territory_locations.py` - Added validation
    - `src/backend/scripts/normalize_territories.py` - Added validation
    - `frontend/src/components/FranchiseTerritoryMap.client.tsx` - Added filtering

## [2025-12-01] - Fix Territory Map Unavailable States Display

### Fixed
- **Territory Map Now Correctly Shows Unavailable States**:
  - Fixed bug where states in the franchise's `unavailable_states` array (e.g., CA, CT, HI, IL, IN, MD, MN, NY, RI, UT, VA, WA) were shown as green/available on the map.
  - Root causes identified and fixed:
    1. The map rendering logic only called `getStateAvailability()` for states with territory check data
    2. The production territories API does not return `unavailable_states` in the response
  - Solutions applied:
    1. Always call `getStateAvailability()` for all states regardless of territory check data
    2. Pass `unavailable_states` from franchise data as fallback when territories API doesn't include it
  - Modified files:
    - `frontend/src/components/FranchiseTerritoryMap.client.tsx` - Always call availability function
    - `frontend/src/app/franchises/[id]/page.tsx` - Merge `unavailable_states` from franchise data into territory data
  - The Territory Overview card and map header already displayed unavailable states correctly; now the map visualization matches.

## [2025-12-01] - Territory Map Full Geographic Lists

### Added
- **Show All States, Counties, and Cities in Territory Map**:
  - The sidebar now displays ALL 50+ US states, not just those with territory check data.
  - States are sorted with data-having states first (by check count), then alphabetically.
  - Counties are now loaded from GeoJSON files (`/geo/counties/{STATE}.geojson`) and merged with territory data.
  - Cities are loaded from GeoJSON files (CA, FL, NJ, NY, TX only) when available, merged with territory data.
  - All geographic areas (states/counties/cities) are now navigable regardless of whether they have territory checks.

- **New Helper Functions** (`FranchiseTerritoryMap.client.tsx`):
  - `allStates`: Returns all states from `STATE_NAMES`, sorted with data states first.
  - Updated `getCountiesInState()`: Extracts counties from loaded county GeoJSON, merges with territory data.
  - Updated `getCitiesInCounty()`: Extracts cities from city GeoJSON when available, merges with territory data.

### Changed
- **Click Handlers Allow Navigation Without Data**:
  - All states are now clickable on the map, even those without territory checks.
  - All counties are now clickable, navigating to city view even without checks.
  - All cities are now clickable, navigating to ZIP view even without checks.
  
- **Sidebar Display Updates**:
  - Items without territory data show "0 checks" with a lighter styling.
  - Subtitle now shows "52 states (X with data)" instead of just "X states with data".
  - Counties and cities without data display with muted badge styling.

- **Availability Logic**:
  - Areas without territory data now show as "available" (green) instead of "neutral" (gray).
  - This follows the principle that "no data = available" for territory checks.

### Removed
- Removed empty state check - map now renders even when no territory data exists.
- Removed `hasData` guards that prevented clicking on states without territory checks.

## [2025-12-01] - Territory Map Hover Zoom Fix

### Fixed
- **Territory Map Zoom Reset on Hover**:
  - Fixed issue where hovering over map zones (states, counties, cities, ZIPs) would reset the map to base zoom level.
  - Root cause: `hoveredItem` was included in the dependency arrays of the layer-rendering `useEffect` hooks, causing them to re-run and call `fitBounds()`/`setView()` on every hover.
  - Solution: Removed `hoveredItem` from layer-rendering effect dependencies in `FranchiseTerritoryMap.client.tsx`.
  - Changed initial polygon style to always use `isHovered = false` since the dedicated hover effect (lines 1050-1092) handles hover style updates.
  - Map now only resets zoom when navigating via sidebar selections (state/county/city), not when hovering on the map.

## [2025-11-30] - Territory Normalization & Deduplication Pipeline

### Added
- **Schema Migration**:
  - Added `country` column to `territory_checks` table (defaults to 'US', supports 'CA' for Canada)
  - Added `is_resale` boolean column to track resale opportunities
  - Created migration `docs/database/add_territory_normalization_fields.sql`
  - Applied migration via `mcp_supabase_apply_migration`

- **LLM Location Parser** (`src/backend/scripts/parse_territory_locations.py`):
  - Parses `location_raw` into structured fields: city, state, county, zip_code, radius_miles
  - Uses Gemini Flash with structured JSON output schema
  - Handles edge cases:
    - City/State: "Oakland, CA" → city=Oakland, state=CA, county=Alameda
    - ZIP only: "33174" → zip=33174, city=Miami, state=FL, county=Miami-Dade
    - ZIP + radius: "Livermore CA 94551 and 25 miles" → zip=94551, radius_miles=25
    - County-only: "Orange County CA" → county=Orange, city=null
    - Resale detection: "Amarillo TX resale" → is_resale=true
    - International (Canada): "Oakville Ontario L6H4N8" → country=CA, state=ON
  - **Multi-location splitting**: "Dallas or Amarillo, TX" creates 2 separate records
  - Uses pgeocode for US/Canada zip code enrichment (city, county, lat/lon)

- **Deduplication Script** (`src/backend/scripts/dedupe_territory_checks.py`):
  - Implements geographic hierarchy rules: Zip ⊂ City ⊂ County ⊂ State
  - **Dedup rules**:
    - Status = "Not Available": Keep BROADER scope (city-level supersedes zip-level)
    - Status = "Available": Keep SPECIFIC scope (zip-level more informative)
    - Mixed status: Newer check_date always wins
    - Exact duplicates: Keep record with most recent check_date
  - Processes per-franchise to apply containment logic correctly
  - Supports `--dry-run` for preview mode

- **Backfill Orchestrator** (`src/backend/scripts/backfill_territory_normalization.py`):
  - Combines migration check, parser, and deduplication into single pipeline
  - Supports `--dry-run`, `--limit`, `--skip-parse`, `--skip-dedup`, `--franchise-id` options
  - Reports: records parsed, split (multi-location), deduplicated
  - Example: Franchise 50 reduced from 50 to 17 records (33 duplicates removed)

- **Tests**:
  - Created `tests/territory/test_location_parser.py` with comprehensive test cases
  - Created `tests/territory/test_dedup_logic.py` for hierarchy-based dedup rules

### Changed
- **Territory Check Count**:
  - Franchise 50 now shows 17 unique territory checks instead of 50 duplicates
  - Total records: 26,140 → 26,150 (net +10 from splits minus dedup)
  - Unparsed records: 9,810 → 9,744 (66 records parsed in initial batch)

## [2025-11-29] - City and ZIP Boundary Polygons for Territory Map

### Added
- **City Boundary Download Script** (`scripts/download_city_geojson.py`):
  - Downloads city/place boundaries from Census Bureau TIGERweb API.
  - Fetches both Incorporated Places (Layer 4) and Census Designated Places (Layer 5).
  - Saves to `frontend/public/geo/cities/{STATE}.geojson`.
  - Includes geometry simplification to reduce file sizes.
  - Supports downloading specific states via CLI arguments.

- **ZIP Code Boundary Download Script** (`scripts/download_zip_geojson.py`):
  - Downloads ZIP Code Tabulation Area (ZCTA) boundaries from Census Bureau TIGERweb API.
  - Uses state bounding boxes for spatial filtering (ZCTAs cross state lines).
  - Implements pagination for large states (500 records per request).
  - Saves to `frontend/public/geo/zips/{STATE}.geojson`.
  - Includes geometry simplification to reduce file sizes.

- **Geographic Library Enhancements** (`frontend/src/lib/geo.ts`):
  - Added `fetchCityBoundaries(stateCode)` function to load city GeoJSON from local files.
  - Added `fetchZipBoundaries(stateCode)` function to load ZIP GeoJSON from local files.
  - Added `findCityFeature(collection, cityName)` helper function.
  - Added `findZipFeature(collection, zipCode)` helper function.
  - Added `filterCitiesByNames(collection, cityNames)` utility function.
  - Added `filterZipsByCode(collection, zipCodes)` utility function.

- **City Polygon Rendering** (`FranchiseTerritoryMap.client.tsx`):
  - When a county is selected, cities are now rendered as GeoJSON polygons instead of point markers.
  - City boundaries are colored by availability status (green/red/mixed).
  - Proper zoom to county bounds when drilling down.
  - Fallback to point markers if city GeoJSON is not available.

- **ZIP Polygon Rendering** (`FranchiseTerritoryMap.client.tsx`):
  - When a city is selected, ZIPs with data are rendered as GeoJSON polygons.
  - ZIP boundaries are colored by availability status.
  - Point markers overlay ZIPs for precise location indication.
  - Proper zoom to city/ZIP area bounds.

### Changed
- **Territory Map Component** (`FranchiseTerritoryMap.client.tsx`):
  - Added state for `citiesGeo` and `zipsGeo` GeoJSON data.
  - Added useEffects to load city/ZIP boundaries on navigation.
  - Updated hover effect to handle city and ZIP polygon layers.
  - Improved zoom behavior using polygon bounds instead of marker bounds.

### Notes
- City/ZIP boundary files are large (~2-10MB per state). Download only needed states using:
  - `python scripts/download_city_geojson.py TX FL CA` (cities)
  - `python scripts/download_zip_geojson.py TX FL CA` (ZIPs)
- Currently downloaded: TX, FL, CA, NY, NJ, CT cities and CT, FL ZIPs.
- Remaining states can be downloaded as needed.

## [2025-11-29] - Hierarchical Territory Availability Logic

### Changed
- **Bottom-Up Availability Aggregation with Partial Data Handling**:
  - Completely rewrote territory availability calculation in `FranchiseTerritoryMap.client.tsx` to use hierarchical bottom-up aggregation.
  - **Key Principle**: "No data" = "Available" (shown as green on map). Areas without territory checks are implicitly available.
  - **New Rules**:
    - **Zip Level**: A zip is "unavailable" only if ALL territory checks for that zip are unavailable.
    - **City Level**: If any zip WITH data is unavailable, city shows as "mixed" (because other zips without data = available).
    - **County Level**: If any city WITH data is unavailable/mixed, county shows as "mixed" (because other cities without data = available).
    - **State Level**: "unavailable" ONLY if explicitly marked in `unavailable_states` array OR via state-level territory check. Otherwise, if any county WITH data is unavailable/mixed, state shows as "mixed".
  - **Rationale**: Since we only have partial territory check coverage, we can't assume an area is fully unavailable just because all our data says so. Other sub-areas without data would display as available, making the parent "mixed".
  - Added `getZipAvailability()` function for base-level aggregation.
  - Added `getCityAvailability()` function that aggregates from zips with partial data awareness.
  - Refactored `getCountyAvailability()` to aggregate from cities with partial data awareness.
  - Refactored `getStateAvailability()` to check explicit unavailability and aggregate from counties.
  - Updated sidebar rendering to use the new `getCityAvailability()` and `getZipAvailability()` functions for consistent coloring.

### Added
- **Explicit Unavailable States Support**:
  - Added `unavailable_states` field to `TerritoryData` interface in `frontend/src/types/index.ts`.
  - Updated `/api/franchises/{id}/territories` endpoint in `src/backend/franchises.py` to fetch and return the franchise's `unavailable_states` array from the database.
  - State availability now respects the franchise-level `unavailable_states` JSONB field.

## [2025-11-29] - Default Territory Availability to Available

### Changed
- **Territory Map Default Availability**:
  - Changed default territory availability status from "neutral" (gray/No Data) to "available" (green) when no territory check data exists for a state, county, or city.
  - States, counties, and cities without explicit territory checks now display as "Available" by default.
  - Updated `getStateAvailability()` and `getCountyAvailability()` functions in `FranchiseTerritoryMap.client.tsx` to return `'available'` instead of `'neutral'` when no data exists.
  - Updated rendering logic for states, counties, and cities to use `'available'` as default status.
  - Removed "No Data" entry from the map legend since all territories now default to available.

## [2025-11-29] - Local County GeoJSON Hosting

### Added
- **Local County Boundary Files**:
  - Created `scripts/download_county_geojson.py` Python script to download and split US county boundaries by state.
  - Downloaded 3,221 county polygons from Plotly datasets (Census Bureau source).
  - Split into 52 state/territory files in `frontend/public/geo/counties/` (total 2.78 MB).
  - Each file contains GeoJSON FeatureCollection with normalized properties: `NAME`, `GEOID`, `STATE`, `STATEFP`, `COUNTYFP`.

### Changed
- **Geographic Data Loading Priority** (`frontend/src/lib/geo.ts`):
  - Updated `fetchCountyBoundaries()` to use 3-tier fallback strategy:
    1. **Local files first** (most reliable, no CORS): `/geo/counties/${stateCode}.geojson`
    2. **Census TIGER API** (fallback if local missing): Live API call
    3. **GitHub TopoJSON** (last resort): Community-hosted files
  - This eliminates CORS issues and network dependencies for county boundary rendering.
  - Added caching to GitHub fallback function for consistency.

### Notes
- Local county files are pre-simplified for web display (~36KB average per state).
- County boundaries will render when drilling down from state to county view on territory maps.

## [2025-11-29] - Territory Map Data Linking Fix

### Fixed
- **Territory Map "0 checks" Bug**:
  - Fixed critical bug where Territory Availability Map showed total count in header (e.g., "25 checks") but "0 checks" for all states in the sidebar.
  - **Root Cause**: The production backend was returning a 2-level hierarchy (`state → city → array`) instead of the correct 3-level hierarchy (`state → county → city → array`).
  - **Investigation**: Used console debugging and API testing to identify structure mismatch between local and production backends.
  - The local backend (`src/backend/franchises.py`) correctly builds the 4-level hierarchy, but the production deployment had an older version.
  
### Changed
- **Frontend Development Environment**:
  - Updated `frontend/.env.local` to use local backend (`http://127.0.0.1:8000`) for development testing.
  - This allows testing against the latest backend code before production deployment.

### Notes
- **Deployment Required**: The backend changes in `src/backend/franchises.py` need to be deployed to production (Railway) to fix the bug in production.
- The fix involves the county-level hierarchy that was added in a previous update but not yet deployed.

## [2025-11-29] - Territory Map Enhancement with Polygon Rendering

### Added
- **US States GeoJSON Data**:
  - Added `frontend/public/geo/us-states.geojson` for state boundary polygon rendering.
  - States are now displayed as colored polygons on the map instead of just point markers.

- **Geographic Utilities** (`frontend/src/lib/geo.ts`):
  - `fetchStatesBoundaries()`: Loads states GeoJSON from local file.
  - `fetchCountyBoundaries(stateCode)`: Fetches county boundaries on-demand from external API.
  - `fetchZipBoundaries()`: Placeholder for ZIP code boundary fetching.
  - `getStateCodeFromFeature()`: Extracts state code from GeoJSON feature properties.
  - `getFeatureBounds()`: Calculates bounding box for map zoom.
  - `STATE_NAMES` and `STATE_FIPS` mapping constants.

- **Availability-Based Coloring**:
  - States/counties colored based on territory check status:
    - Green (`#10b981`): Available checks exist
    - Red (`#f43f5e`): Unavailable checks exist
    - Orange/Amber (`#f59e0b`): Mixed availability
    - Gray (`#94a3b8`): No territory data (neutral)
  - Updated legend to show all availability states.

- **Bidirectional Hover Synchronization**:
  - Hovering on sidebar list items highlights corresponding map polygon/marker.
  - Hovering on map features highlights corresponding sidebar item.
  - Visual feedback with increased opacity and border weight on hover.

- **Sorted Lists by Check Count**:
  - States list sorted by territory check count (descending).
  - Counties sorted by check count within selected state.
  - Cities sorted by check count within selected county.

### Changed
- **Complete FranchiseTerritoryMap.client.tsx Rewrite**:
  - Replaced point-marker-only approach with polygon-based rendering.
  - Added `viewLevel` state tracking: states → counties → cities → zips.
  - Implemented zoom-to-bounds when selecting state/county/city.
  - Added loading states for GeoJSON data fetching.
  - Counties fallback to city markers when GeoJSON not available.

### Fixed
- **"NaN checks" Display Bug**:
  - Fixed counting functions (`getStateCheckCount`, `getCountyCheckCount`, `getCityCheckCount`) with defensive type checking.
  - Added `Array.isArray()` guards to prevent NaN from malformed data.
  - Added try-catch blocks for error recovery.

## [2025-11-29] - County-Level Territory Granularity

### Added
- **County Field to Territory System**:
  - Added `county` column to `territory_checks` database table with index (`docs/database/add_county_to_territory_checks.sql`).
  - Migration applied to Supabase database via `mcp_supabase_apply_migration`.
  
- **LLM County Extraction**:
  - Updated `config/franserve/structured_output.json` to include `county` field in `recent_territory_checks` items.
  - LLM now extracts county names when explicitly mentioned in territory check text (e.g., "Union County, NJ").

- **County Parsing Functions** (`src/data/functions/field_mapper.py`):
  - Added `extract_county()` function with regex patterns to extract county names from location text.
  - Updated `lookup_zip_with_pgeocode()` to return county information from pgeocode lookups (5-tuple instead of 4-tuple).
  - Updated `parse_territory_check()` to include county in output using three-tier priority:
    1. LLM-extracted county from check dict
    2. Regex extraction from location text
    3. pgeocode lookup fallback from zip code

- **Backend 4-Level Hierarchy**:
  - Updated `get_franchise_territories()` endpoint in `src/backend/franchises.py` to return 4-level hierarchy: State -> County -> City -> TerritoryCheck[].
  - When county is not available, "Unspecified County" is used as placeholder for flexible navigation.

- **Frontend County Support**:
  - Updated `TerritoryCheck` interface in `frontend/src/types/index.ts` with `county` field.
  - Updated `TerritoryData` interface to support 4-level nested structure: `Record<string, Record<string, Record<string, TerritoryCheck[]>>>`.
  - Rewrote `FranchiseTerritoryMap.client.tsx` with full 4-level navigation support:
    - Added `selectedCounty` state for county-level selection.
    - Updated breadcrumbs: All States -> State -> County (if not Unspecified) -> City -> Zip.
    - Added county icon (Building2) in navigation.
    - Smart auto-selection: when state has only "Unspecified County", automatically skip to city selection.
    - County check counts displayed in sidebar.
    - Map popup now shows county information when available.
    - Marker click handler navigates to correct county -> city -> zip path.

- **Backfill Script**:
  - Created `src/backend/scripts/backfill_territory_counties.py` for populating county data on existing records.
  - Uses pgeocode to look up county from zip codes for records missing county.
  - Supports `--dry-run` mode for preview and `--batch-size` for performance tuning.
  - Progress tracking and comprehensive summary report.

### Changed
- **Territory Hierarchy**:
  - Changed from 3-level (State -> City -> Zip) to 4-level (State -> County -> City -> Zip) hierarchy.
  - Flexible navigation allows skipping county level when it's "Unspecified County".

## [2025-11-29] - Franchise Detail Page Enhancement & Territory Tab Fix

### Added
- **Enhanced FDD Overview**:
  - **Franchise Packages Card**: Displays multiple franchise packages with fee, investment range, territories count, and descriptions (`frontend/src/app/franchises/[id]/page.tsx`).
  - **Commission Structure Card**: Shows broker commission info for single unit, multi-unit, resales, and area developer opportunities.
  - **Market Insights Card**: Displays market size, CAGR, growth period, demographics, and recession resistance from `market_growth_statistics` field.
  - **Industry Awards Card**: Shows franchise awards and recognition with source, year, and award name badges.
  - **Territory Quick View Card**: Displays hot regions, Canadian/international referral acceptance, and resales availability badges.
  - **Documents & Resources Card**: Lists regular documents, client-focused resources, recent emails, and magazine articles with clickable links.
  - **Schedule Call CTA**: Added prominent "Schedule a Call" button in header when `schedule_call_url` is available.

- **Enhanced Financial Dashboard**:
  - Added SBA Registered badge (separate from SBA Approved).
  - Added Item 19 Earnings Guidance badge for franchises providing financial performance data.
  - Added Additional Fees section showing extra costs beyond franchise fee.
  - Added Financial Assistance Details section.

- **Enhanced Ideal Candidate Card**:
  - Now uses structured `ideal_candidate_profile` JSON when available (skills, personality traits, role of owner).
  - Falls back to legacy `ideal_candidate_profile_text` if structured data unavailable.
  - Skills and traits displayed as tags for better visual presentation.

- **Enhanced Support & Training Card**:
  - Now uses structured `support_training_details` JSON when available.
  - Displays training cost inclusion, lodging/airfare, site selection help, lease negotiation help, mentor availability as visual badges.
  - Shows mentoring duration and cost details.
  - Falls back to legacy `franchises_data.support_and_training` if structured data unavailable.

- **TypeScript Type Definitions**:
  - Added comprehensive interfaces to `frontend/src/types/index.ts`:
    - `TerritoryCheck`, `TerritoryData` for territory map
    - `MarketGrowthStatistics`, `IdealCandidateProfile`, `SupportTrainingDetails`
    - `IndustryAward`, `FranchiseDocuments`, `CommissionStructure`, `FranchisePackage`
    - `FranchiseDetail` comprehensive interface for franchise data

### Fixed
- **Territory Availability Tab**:
  - Fixed rendering error caused by field name mismatch between database and frontend.
  - Backend now transforms `raw_text` → `location_raw` and `is_available` → `availability_status` string (`src/backend/franchises.py`).
  - Added null safety checks in `FranchiseTerritoryMap.client.tsx` to handle missing/empty data gracefully.
  - Component now shows empty state with helpful message when no territory data exists.

- **Territory Map Component Rewrite**:
  - Rewrote `frontend/src/components/FranchiseTerritoryMap.client.tsx` with full functionality.
  - Added breadcrumb navigation showing: All States > State > City > ZIP.
  - Clicking breadcrumb items navigates back up the hierarchy.
  - Added proper drill-down from states → cities → zip codes.
  - Improved visual indicators for available (green) vs not available (red) territories.
  - Added territory count badges at each level.

- **Leaflet "Map container already initialized" Error** (Final Fix):
  - Fixed persistent runtime error when clicking Territory Availability tab.
  - **Root cause**: react-leaflet's lifecycle management doesn't properly handle Next.js tab switching and component remounting.
  - **Solution**: Completely rewrote `frontend/src/components/FranchiseTerritoryMap.client.tsx` using **imperative Leaflet API** instead of react-leaflet.
  - Key changes:
    1. Removed all react-leaflet components (`MapContainer`, `TileLayer`, `Marker`, `Popup`, `Circle`).
    2. Use native Leaflet API: `L.map()`, `L.tileLayer()`, `L.marker()`, `L.circle()`, `L.layerGroup()`.
    3. Map instance managed entirely via `mapRef` ref with full manual lifecycle control.
    4. Markers managed via `markersLayerRef` layer group for easy clearing/updating.
    5. Explicit cleanup in useEffect: checks for existing `_leaflet_id`, clears container children, calls `map.remove()`.
    6. Map view updates via `map.setView()` in separate useEffect.
    7. Markers update reactively by clearing and recreating the layer group contents.

### Changed
- **Territory Data Backend**:
  - Updated `/api/franchises/{id}/territories` endpoint to transform data for frontend compatibility (`src/backend/franchises.py`).

## [2025-11-25] - PDF Export Rewrite with jsPDF

### Added
- **Programmatic PDF Export with jsPDF + AutoTable**:
  - Replaced `html2pdf.js` (HTML screenshot approach) with `jsPDF` + `jspdf-autotable` for proper PDF generation.
  - Added `jspdf` and `jspdf-autotable` to frontend dependencies (`frontend/package.json`).
  - PDF now generates proper tables instead of cropped HTML screenshots.

- **PDF Cover Page**:
  - Title: "Franchise Comparison Matrix" with subtitle.
  - Lead profile section showing candidate name, location, liquidity, and net worth (if selected).
  - Summary table listing all compared franchises with industry, investment range, and fit assessment.
  - Export timestamp.

- **Franchise Detail Pages (One Per Franchise)**:
  - Each franchise gets a dedicated page with professional layout.
  - Color-coded header with franchise name and industry.
  - Verdict box with AI-generated pitch.
  - **Overview Table**: Year Started, Year Franchised, Operating Franchises.
  - **Financials Table**: Investment range, liquidity, net worth, royalty, SBA status, financing, financial model, overhead (with fit indicator badge).
  - **Motives Table**: Recession resistance, scalability, market demand, passive income potential.
  - **Operations Table**: Role type, sales model, employees, inventory (with role fit indicator badge).
  - **Territory Table**: Availability status, unavailable states list.
  - **Value Proposition Section**: "Why This Franchise" bullet points, franchise description.

- **Page Numbers**: Footer on all pages showing "Page X of Y".

### Changed
- **PDF Export Function Complete Rewrite**:
  - Replaced `handleExportPDF` function in `frontend/src/components/ComparisonTable.tsx`.
  - Removed all html2canvas/html2pdf related code and CSS workarounds.
  - New function uses jsPDF's native table generation for clean, properly paginated output.

### Removed
- Removed `html2pdf.js` dependency from `frontend/package.json`.
- Deleted `frontend/src/types/html2pdf.d.ts` type declaration file.
- Removed HTML cloning and CSS override workarounds for html2canvas compatibility.

## [2025-11-25] - Comparison Table Display & PDF Export Fix

### Added
- **ContentList Shared Component**:
  - Created `frontend/src/components/ContentList.tsx` as a reusable component.
  - Handles parsing of various content formats: JSON arrays, Python-style arrays, and plain text.
  - Supports customizable bullet colors (`bulletClassName`), text colors (`textClassName`), and compact mode.
  - Normalizes inconsistent data formats into consistent bullet-point lists.

### Fixed
- **"Why This Franchise" Display Inconsistency**:
  - Fixed issue where "Why This Franchise" content displayed inconsistently in the Comparison Matrix.
  - Some franchises showed raw array format like `['item1', 'item2']` instead of bullet points.
  - Updated `ComparisonTable.tsx` to use the new `ContentList` component for proper rendering.
  - All franchise entries now display with consistent bullet-point formatting.

- **PDF Export CSS Compatibility**:
  - Enhanced PDF export function in `ComparisonTable.tsx` to handle modern CSS color functions.
  - Added comprehensive inline style overrides for Tailwind color classes (`bg-*`, `text-*`, `border-*`).
  - Implemented recursive color override function that detects and replaces `lab()`, `oklch()`, and `color()` functions.
  - Removed dark mode classes and attributes from cloned elements before rendering.
  - PDF export now works reliably without triggering CSS parsing errors in html2canvas.

### Changed
- **Franchise Detail Page Refactor**:
  - Updated `frontend/src/app/franchises/[id]/page.tsx` to import shared `ContentList` component.
  - Removed duplicate local `ContentList` function definition.
  - Both Comparison Matrix and Franchise Detail pages now share the same parsing logic.

## [2025-11-25] - Comparison Matrix Enhancement & PDF Export

### Added
- **PDF Export Feature**:
  - Implemented client-side PDF export for the Comparison Matrix using `html2pdf.js` (`frontend/src/components/ComparisonTable.tsx`).
  - Added "Export PDF" button to the toolbar next to "Save Analysis" button.
  - PDF exports in landscape format with proper scaling and formatting.
  - Filename includes lead name and date (e.g., `John_Doe_Franchise_Matrix_2025-11-25.pdf`).
  - Added `html2pdf.js` package to frontend dependencies (`frontend/package.json`).
  - Created TypeScript declaration file for `html2pdf.js` (`frontend/src/types/html2pdf.d.ts`).

- **New Comparison Matrix Fields**:
  - **Overview Section** (new):
    - Industry (`primary_category`)
    - Year Started (`founded_year`)
    - Year Franchised (`franchised_year`)
    - Operating Franchises (from `franchises_data.background`)
  - **Wallet Section** (enhanced):
    - Net Worth Requirement (`required_net_worth_usd`)
    - Royalty (`royalty_details_text`)
    - SBA Registered (`sba_registered`)
    - In-House Financing (`financial_assistance_details`)
  - **Territory Section** (enhanced):
    - Unavailable States list with visual badges
  - **Value Proposition Section** (new):
    - Why This Franchise (`why_franchise_summary`)
    - Description/Value Proposition (`description_text` - truncated to 300 chars)

- **Backend Model Updates**:
  - Added `OverviewAttributes` model to `src/backend/models.py` (industry, year_started, year_franchised, operating_franchises).
  - Added `ValueAttributes` model to `src/backend/models.py` (why_franchise, value_proposition).
  - Enhanced `MoneyAttributes` model with `royalty`, `sba_registered`, `in_house_financing` fields.
  - Enhanced `TerritoryAttributes` model with `unavailable_states` array.
  - Updated `ComparisonItem` model to include `overview` and `value` sections.

- **Frontend Type Updates**:
  - Added `OverviewAttributes` interface to `frontend/src/types/index.ts`.
  - Added `ValueAttributes` interface to `frontend/src/types/index.ts`.
  - Enhanced `MoneyAttributes` interface with new financial fields.
  - Enhanced `TerritoryAttributes` interface with `unavailable_states` array.
  - Updated `ComparisonItem` interface with new sections.

### Fixed
- **Sticky Section Headers**:
  - Fixed horizontal scroll issue where section headers ("Wallet", "Motives", "Life", "Empire") would scroll out of view.
  - Converted section header rows from full-width `colSpan` to having the title in the sticky left column.
  - Section titles now remain visible when scrolling horizontally through franchise columns.

- **Comparison Matrix N/A Values**:
  - Fixed issue where "Why This Franchise" and "Description" fields displayed "N/A" due to stale cached analysis data.
  - Added completeness check in `frontend/src/app/franchises/compare/page.tsx` to detect incomplete saved analyses.
  - Page now regenerates fresh data from API if saved analysis is missing `value` section (why_franchise, value_proposition).
  - Note: Full fix requires deploying updated `comparison.py` to production backend (currently frontend points to production API).

- **PDF Export Crash**:
  - Fixed runtime error that caused page crash when clicking "Export PDF" (`frontend/src/components/ComparisonTable.tsx`).
  - Root cause: `html2canvas` doesn't support modern CSS color functions (`lab()`, `oklch()`) used by Tailwind CSS v4.
  - Added defensive error handling to prevent page crash.
  - Added fallback prompt to use browser's native print dialog when html2pdf export fails.
  - Clone element now wrapped with light mode style overrides to reduce color parsing issues.

- **Backend Comparison API Validation Error**:
  - Fixed Pydantic validation error in `src/backend/comparison.py` where `unavailable_states` was passed as a string instead of a list.
  - Error: `Input should be a valid list [type=list_type, input_value="['Florida', 'Alabama']", input_type=str]`
  - Added type checking and `ast.literal_eval()` parsing to handle string representations of lists from database.

### Changed
- **Comparison Endpoint**:
  - Updated `/api/franchises/compare` endpoint (`src/backend/comparison.py`) to populate all new fields.
  - Added extraction of `operating_franchises` from `franchises_data.background` JSONB field.
  - Added truncation logic for `description_text` (max 300 chars with word boundary).
  - Enhanced territory notes to show up to 5 unavailable states.

## [2025-11-24] - Markdown to Database Extraction Pipeline

### Added (Later Update)
- **LLM Processing Tracking**:
  - Added `llm_processed_at` column to `franchises` table (`docs/database/add_llm_processed_at.sql`)
  - Tracks when each franchise was processed by LLM extraction pipeline
  - Enables batch processing to resume without reprocessing already-done files
  - Skip logic now checks `llm_processed_at IS NOT NULL` instead of just source_id existence

### Changed (Later Update)
- **Batch Extraction Skip Logic**:
  - Changed from skipping based on `source_id` existence to skipping based on `llm_processed_at`
  - Renamed `get_existing_source_ids()` to `get_llm_processed_source_ids()` in both scripts
  - This allows updating existing franchises that haven't been LLM-processed yet

### Added
- **Field Mapper Utility**:
  - Created `src/data/functions/field_mapper.py` with transformations between LLM output and database schema
  - `parse_date_mdy_to_ymd()`: Converts dates from MM/DD/YYYY to YYYY-MM-DD format
  - `array_to_text()`: Converts arrays to formatted text strings
  - `generate_slug()`: Creates URL-friendly slugs from franchise names
  - `extract_source_id_from_filename()`: Extracts FranID from filenames like `FranID_1003.md`
  - `build_source_url()`: Constructs source URLs from FranIDs
  - `map_llm_output_to_db_schema()`: Complete mapping function handling all field transformations
  - `extract_contacts_data()`: Extracts and cleans contacts from LLM output

- **Territory Check Parsing Functions** (`src/data/functions/field_mapper.py`):
  - `extract_state_code()`: Extracts 2-letter US state code from location text
  - `extract_zip_code()`: Extracts 5-digit zip code from location text
  - `extract_radius_miles()`: Extracts radius from patterns like "30 miles around"
  - `lookup_zip_with_pgeocode()`: Gets city, state, lat, lon from zip using pgeocode
  - `parse_territory_check()`: Parses single territory check with full extraction
  - `extract_territory_checks_data()`: Extracts all territory checks from LLM output

- **Single Record Extraction Script**:
  - Created `src/backend/scripts/run_single_md_extraction.py` for testing single file extraction
  - Downloads markdown from Supabase Storage
  - Extracts source_id from filename (FranID_X.md format)
  - Calls Gemini LLM with markdown prompt for structured extraction
  - Applies field transformations via mapper
  - Upserts franchise data to `franchises` table using `on_conflict="source_id"`
  - Upserts contacts to `contacts` table using email-based deduplication
  - Inserts territory checks to `territory_checks` table with parsed location data
  - Handles category relationships in `franchise_categories` table
  - CLI arguments: `--prefix` (date), `--fran-id` (specific franchise)

- **Batch Extraction Script**:
  - Created `src/backend/scripts/run_batch_md_extraction.py` for processing multiple files
  - Queries existing source_ids to identify unprocessed files
  - Sequential processing with configurable delay between API calls
  - Progress tracking with tqdm progress bar
  - Detailed summary report (successful, failed, skipped counts)
  - Updates `scraping_runs` table with LLM parsing status
  - CLI arguments: `--prefix`, `--batch-size` (default 50), `--delay` (default 1.0s), `--force-reprocess`

- **LLM Parsing Status Tracking**:
  - Added migration `docs/database/add_llm_parsing_fields.sql`
  - New columns in `scraping_runs` table:
    - `llm_parsing_status`: pending/in_progress/completed/partial/failed/no_files
    - `llm_parsing_started_at`: Timestamp when parsing started
    - `llm_parsing_completed_at`: Timestamp when parsing completed
  - Metadata JSONB stores: `llm_parsing_completed_files`, `llm_parsing_failed_files`, `llm_parsing_skipped_files`, `llm_parsing_duration_seconds`

- **Contacts Email Constraint**:
  - Added migration `docs/database/add_contacts_email_constraint.sql`
  - Created partial unique index on `contacts(franchise_id, email)` for non-null emails
  - Enables email-based deduplication for contacts

### Changed
- **Contacts Upsert Strategy**:
  - Changed from delete+insert to email-based upsert in both extraction scripts
  - Contacts WITH email: Find existing by (franchise_id, email), update if exists, insert if not
  - Contacts WITHOUT email: Delete old null-email contacts, insert new ones

- **Database Schema Documentation**:
  - Updated `docs/database/SCHEMA.md` with new `scraping_runs` fields for LLM parsing tracking

### Fixed
- **Category Relation Handling**:
  - Fixed `handle_category_relation()` to use correct Supabase upsert syntax (removed `.select()` chaining)

## [2025-01-28] - Enhanced Markdown to JSON Extraction

### Added
- **Basic Franchise Information Extraction**:
  - Added explicit section (Section 0) in prompt for extracting franchise_name, primary_category, sub_categories, website_url, and corporate_address
  - Enhanced schema descriptions for categories, subcategories, website, and corporate_address with extraction guidance
  - Emphasized that these fields appear early in markdown and must be extracted first
- **Comprehensive Pattern Extraction**:
  - Enhanced `markdown_prompt.txt` (`config/franserve/markdown_prompt.txt`) with explicit instructions for all information patterns found in franchise markdown files.
  - Added structured extraction requirements for territory checks, commission structures, awards, documents, market availability, and more.
  - Added examples and detailed guidance for complex patterns like multiple franchise packages and structured territory checks.

- **Enhanced Structured Output Schema**:
  - Updated `structured_output.json` (`config/franserve/structured_output.json`) with comprehensive new fields:
    - `commission_structure`: Structured commission data (single_unit, multi_unit, resales, area_master_developer)
    - `industry_awards`: Array of awards with source, year, and award_name
    - `documents`: Organized documents (regular, client_focused, recent_emails, magazine_articles)
    - `resales_available` and `resales_list`: Resale availability information
    - `rating`: Star rating (1-5)
    - `schedule_call_url`: Calendar booking URL
    - `hot_regions`: Array of hot/desirable markets
    - `canadian_referrals` and `international_referrals`: Referral acceptance booleans
    - `franchise_packages`: Array of franchise packages with detailed information
    - `support_training_details`: Structured training and support information
    - `market_growth_statistics`: Extracted market growth data from WHY section
    - `ideal_candidate_profile`: Structured profile (skills, personality_traits, role_of_owner)
    - Enhanced `recent_territory_checks`: Changed from string array to structured objects with date, location, is_available, notes
    - Enhanced `franchises_data`: Added launching_units and total_franchisees fields
    - Added `title` field to `contacts_data` schema

- **Database Schema Enhancements**:
  - Created migration script `add_enhanced_franchise_fields.sql` (`docs/database/add_enhanced_franchise_fields.sql`):
    - Added `commission_structure` (JSONB) to `franchises` table
    - Added `industry_awards` (JSONB) to `franchises` table
    - Added `documents` (JSONB) to `franchises` table
    - Added `resales_available` (boolean) and `resales_list` (JSONB) to `franchises` table
    - Added `rating` (numeric) to `franchises` table
    - Added `schedule_call_url` (text) to `franchises` table
    - Added `hot_regions` (JSONB) to `franchises` table
    - Added `canadian_referrals` and `international_referrals` (boolean) to `franchises` table
    - Added `franchise_packages` (JSONB) to `franchises` table
    - Added `support_training_details` (JSONB) to `franchises` table
    - Added `market_growth_statistics` (JSONB) to `franchises` table
    - Added `ideal_candidate_profile` (JSONB) to `franchises` table
    - Added `sba_registered` (boolean) to `franchises` table
    - Added `providing_earnings_guidance_item19` (boolean) to `franchises` table
    - Added `additional_fees` (text) to `franchises` table
    - Added `financial_assistance_details` (text) to `franchises` table
    - Added `title` (text) to `contacts` table
    - Added indexes for new boolean fields and GIN indexes for JSONB fields

### Changed
- **Prompt Enhancement**:
  - Completely rewrote `markdown_prompt.txt` to be more explicit and comprehensive:
    - Added Section 0 for basic franchise information (name, categories, subcategories, website, corporate address) that appears early in markdown
    - Added 15 critical extraction requirements with detailed examples (now 16 sections total)
    - Enhanced BACKGROUND section extraction with comprehensive field-by-field instructions
    - Emphasized structured extraction for territory checks (with dates, locations, availability, notes)
    - Added instructions for handling multiple franchise fee packages
    - Added instructions for extracting market statistics from WHY section
    - Added instructions for structured extraction of ideal franchisee profile
    - Enhanced guidance for commission structures, awards, documents, and market availability
    - Added explicit instructions for extracting all background fields (founded_year, franchised_year, units operating, etc.)

- **Schema Updates**:
  - Enhanced `recent_territory_checks` from simple string array to structured array of objects
  - Enhanced `royalty_details_text` description to handle both percentage and fixed amount formats
  - Enhanced `franchise_fee_usd` description to handle multiple packages
  - Added structured `ideal_candidate_profile` object alongside legacy `ideal_candidate_profile_text` array

- **Documentation**:
  - Updated `SCHEMA.md` (`docs/database/SCHEMA.md`) with all new fields:
    - Added new fields to Financial Fields section
    - Added new fields to Narrative Fields section
    - Enhanced Territory/Availability Fields section
    - Enhanced Contact & Web Fields section
    - Enhanced Search & Metadata Fields section
    - Updated indexes documentation
    - Added comprehensive JSONB structure documentation for all new fields
    - Updated `recent_territory_checks` structure documentation
    - Updated `contacts` table documentation with `title` field

### Fixed
- **Data Extraction Completeness**:
  - Fixed missing extraction of commission structures from markdown files
  - Fixed missing extraction of industry awards and rankings
  - Fixed missing extraction of documents and resources
  - Fixed missing extraction of market availability details (hot regions, Canadian/international referrals)
  - Fixed missing extraction of franchise packages when multiple packages exist
  - Fixed missing extraction of structured support and training details
  - Fixed missing extraction of market growth statistics from WHY section
  - Fixed missing extraction of structured ideal franchisee profile (skills, traits, role)
  - Fixed territory checks being stored as simple strings instead of structured objects with dates and availability
  - Fixed missing contact title field extraction

## [2025-01-27] - Tailwind CSS v4 Dark Mode Configuration

### Fixed
- **Theme Toggle Dark Mode**:
  - Fixed theme toggle button not applying visual changes by adding Tailwind CSS v4 dark mode variant configuration (`frontend/src/app/globals.css`).
  - Added `@variant dark (&:where(.dark, .dark *));` directive to enable class-based dark mode in Tailwind CSS v4.
  - Theme toggle button now properly switches between light and dark themes visually.

## [2025-11-24] - Dark Mode Theme Toggle Fixes

### Fixed
- **Theme Toggle Implementation**:
  - Fixed sidebar hardcoded dark styles in `frontend/src/components/Sidebar.tsx` to support light mode (now uses white background in light mode).
  - Fixed theme toggle logic to explicitly override system preference when user clicks toggle button (`frontend/src/components/Sidebar.tsx`).
  - Added `storageKey="theme"` prop to `ThemeProvider` in `frontend/src/app/layout.tsx` to ensure theme preference persists in localStorage.
  - Improved toggle button handler with better error handling, DOM fallback checks, and debugging logs.
  - Added `type="button"` and `cursor-pointer` to toggle button to ensure proper click handling.
  - Toggle now sets theme to 'light' or 'dark' explicitly, preventing system preference from overriding manual selections.
  - Added missing `next-themes` dependency to `frontend/package.json`.
  - Updated `Sidebar` navigation links and icons to have proper contrast in both light and dark modes.
  - Updated `LeadDetailPage` (`frontend/src/app/leads/[id]/page.tsx`) to support dark mode with proper background and text colors.
  - Ensured `MatchCard` and other components render correctly in both modes.

## [2025-11-24] - Dark Mode & UI Fixes

### Added
- **Dark Mode Support**:
  - Implemented manual light/dark mode switching via `next-themes`.
  - Added theme toggle button to the `Sidebar` header, placing it next to the "BrokerAI" title for better accessibility and to avoid conflict with the persistent comparison bar.
  - Configured `ThemeProvider` with class-based strategy to work seamlessly with Tailwind CSS dark variants.
  - Implemented comprehensive dark mode support across key frontend components using Tailwind CSS `dark:` variants.
  - Added dark mode styles to `DashboardLayout` (`frontend/src/components/DashboardLayout.tsx`).
  - Added dark mode styles to `LeadProfileForm` (`frontend/src/components/LeadProfileForm.tsx`).
  - Added dark mode styles to `ComparisonTable` (`frontend/src/components/ComparisonTable.tsx`).
  - Added dark mode styles to `MatchCard` (`frontend/src/components/MatchCard.tsx`).
  - Added dark mode styles to `PersistentComparisonBar` (`frontend/src/components/PersistentComparisonBar.tsx`).
  - Added dark mode styles to `NewLeadPage` (`frontend/src/app/leads/new/page.tsx`).

### Fixed
- **Lead Profile Form Input**:
  - Fixed "Motives & Goals" textarea input issue where spaces were being trimmed immediately preventing multi-word entry (`frontend/src/components/LeadProfileForm.tsx`).
  - Implemented local state `goalsInput` to preserve raw user input before processing into the tag array.
- **UI Consistency**:
  - Standardized color palette usage across components for both light and dark modes (Slate/Indigo/Red/Green/Yellow).

## [2025-11-24] - Scraper Run Script & Filename Fix

### Fixed
- **HTML to Markdown Conversion Pagination**:
  - Fixed issue where only 100 files were processed when 765+ HTML files existed (`src/data/storage/storage_client.py`).
  - Implemented pagination support in `list_files()` method to fetch all files across multiple pages.
  - Added pagination loop with offset/limit to retrieve all files from Supabase Storage.
  - Now correctly processes all HTML files, not just the first page.
- **HTML to Markdown Conversion Logging**:
  - Enhanced logging in `convert_html_to_markdown_and_upload()` method (`src/data/functions/extract.py`) to show:
    - Total files found in storage
    - Total HTML files to process
    - Files being processed (every 10th file)
    - Files being skipped (first 10, then summary)
    - Progress updates every 50 files
    - Comprehensive summary at completion showing converted/skipped/failed counts
  - Users can now see which files are being processed and track progress accurately.

### Changed
- **Scraper Filename Format**:
  - Changed filename format from URL-based (`franchisedetails.asp?FranID=1016&ClientID=.html`) to clean format (`FranID_1016.html`) (`src/data/functions/extract.py`).
  - Extracts FranID from URL query parameters or HTML content.
  - Eliminates URL encoding issues with special characters (`?`, `&`) in filenames.
  - Makes filenames more readable and easier to work with programmatically.
- **HTML to Markdown Conversion**:
  - Enhanced `convert_html_to_markdown_and_upload()` method (`src/data/functions/extract.py`) to check if Markdown files already exist before converting HTML files.
  - Skips HTML files that already have corresponding `.md` files in storage, preventing redundant processing.
  - Added `skipped_conversions` counter and improved logging to show skipped vs processed files.
  - Final summary now displays: "Converted: X, Skipped: Y, Failed: Z" for better visibility into conversion status.
  - Allows safe re-runs of the conversion process without duplicating work.

### Added
- **Markdown Conversion Run Tracking**:
  - Extended `scraping_runs` table with markdown conversion tracking fields (`docs/database/add_markdown_conversion_fields.sql`):
    - `markdown_conversions_completed`, `markdown_conversions_failed`, `markdown_conversions_skipped` (integer counters)
    - `markdown_conversion_status` (text: "pending", "in_progress", "completed", "failed", "partial")
    - `markdown_conversion_started_at`, `markdown_conversion_completed_at` (timestamps)
    - Index on `markdown_conversion_status` for efficient filtering
  - Enhanced `convert_html_to_markdown_and_upload()` method (`src/data/functions/extract.py`) with run tracking:
    - Creates/updates run records in `scraping_runs` table for each conversion session
    - Tracks converted files in database metadata (`metadata.markdown_converted_files` array)
    - Enables resumption from failures by checking metadata for already-converted files
    - Updates run status and counts throughout the conversion process
    - Periodically updates run record (every 50 files) to prevent data loss on interruption
  - Created `run_html_to_markdown.py` script (`src/backend/scripts/run_html_to_markdown.py`) to execute conversion and display comprehensive results:
    - Shows conversion run statistics (status, counts, timestamps)
    - Displays storage file listing (HTML and Markdown files)
    - Shows conversion ratio and sample converted files
    - Displays sample Markdown content for verification

### Fixed
- **Storage Download Issues**:
  - Fixed download failures caused by special characters (`?`, `&`) in filenames being interpreted as URL query parameters (`src/data/storage/storage_client.py`).
  - Enhanced `download_html()` and `download_markdown()` methods to properly URL-encode filenames when needed.
  - Added better error handling and debug logging for download operations.

### Added
- **Scraper Execution Script**:
  - Created `run_scraper.py` script (`src/backend/scripts/run_scraper.py`) to execute the scraper and display comprehensive results.
  - Script executes `Extractor.scrape()` method which:
    - Logs into FranServe website using credentials from environment variables.
    - Uses BeautifulSoup to extract HTML content from franchise pages.
    - Uploads HTML files to Supabase Storage bucket.
    - Tracks scraping runs in `scraping_runs` database table.
  - Results display includes:
    - **Statistics**: Queries `scraping_runs` table to show run ID, status, total franchises, successful/failed uploads, and storage prefix.
    - **File Listing**: Lists all HTML files stored in Supabase Storage for today's date prefix, showing first 10 files with sizes and total count.
    - **Sample HTML**: Downloads and displays a sample HTML file content (first 500 characters) to verify scraping results.
  - Script handles errors gracefully and continues to show partial results even if scraping fails.

### Added
- **HTML to Markdown Pipeline**:
  - Added `markdownify` dependency to `pyproject.toml` for HTML to Markdown conversion.
  - Extended `StorageClient` class (`src/data/storage/storage_client.py`) with:
    - `upload_json()` method for uploading JSON files to Supabase Storage.
    - `upload_markdown()` method for uploading Markdown files to Supabase Storage.
    - `download_markdown()` method for downloading Markdown files from storage.
  - Created `html_to_markdown.py` module (`src/data/franserve/html_to_markdown.py`) with `convert_html_to_markdown()` function using markdownify library.
  - Created `markdown_prompt.txt` (`config/franserve/markdown_prompt.txt`) with specialized prompt for extracting structured JSON from Markdown format.
  - Enhanced `Extractor` class (`src/data/functions/extract.py`) with:
    - `convert_html_to_markdown_and_upload()` method that downloads HTML from storage, converts to Markdown, and uploads to storage.
    - `markdown_to_json_parsing()` method that uses LLM to convert Markdown files to JSON format.
  - Updated `rule_based_parsing()` method to upload JSON output to Supabase Storage in addition to saving locally.
  - Pipeline now supports three formats in storage: HTML, JSON (rule-based), and Markdown.

### Fixed
- **CORS Configuration**:
  - Fixed CORS origin matching by stripping whitespace and trailing slashes from allowed origins (`src/backend/main.py`).
  - CORS origins are now properly normalized (e.g., `https://app.vercel.app/` becomes `https://app.vercel.app`) to prevent mismatches.
  - Added detailed logging of processed CORS origins for debugging.
  - This resolves CORS errors where origins with trailing slashes were not matching requests from the frontend.
- **Backend Startup & Logging**:
  - Added startup and shutdown event handlers to `main.py` for better visibility into application lifecycle (`src/backend/main.py`).
  - Improved error handling in `supabase_config.py` to raise exceptions instead of calling `sys.exit(1)`, allowing FastAPI to handle errors gracefully (`src/api/config/supabase_config.py`).
  - Enhanced health check endpoint to include Supabase configuration status and removed verbose logging to reduce noise.
  - Improved `start.sh` script with better logging, explicit uvicorn configuration, and `--timeout-keep-alive` for Railway healthchecks.
  - Added detailed logging for environment variable validation and CORS configuration during startup.
  - Optimized Railway healthcheck configuration: reduced timeout to 10s and interval to 30s for faster detection (`railway.json`).
- **Error Handling**:
  - Improved error handling in `LeadsPage` component to display connection errors to users instead of silently failing (`frontend/src/app/leads/page.tsx`).
  - Added error state and retry functionality when backend API connection fails.
  - Users will now see a clear error message if the frontend cannot connect to the backend API.
- **Vercel Deployment**:
  - Fixed TypeScript compilation error for missing type declarations for `react-simple-maps` module (`frontend/src/types/react-simple-maps.d.ts`).
  - Created TypeScript declaration file with proper type definitions for `ComposableMap`, `Geographies`, and `Geography` components used in `TerritoryMap.tsx`.
  - Fixed TypeScript compilation error in `MatchDetailModal` component usage (`frontend/src/app/leads/[id]/page.tsx`).
  - Removed invalid `isOpen` prop that was not defined in `MatchDetailModalProps` interface.
  - Component already handles visibility internally based on `franchiseId` prop (returns `null` when `franchiseId` is null).

### Added
- **Deployment Documentation**:
  - Created comprehensive deployment guide (`docs/DEPLOYMENT.md`) with step-by-step instructions for Railway and Vercel deployment.
- **Deployment Configuration**:
  - Dockerized the backend service:
    - Created `Dockerfile` with Python 3.12-slim base image and Poetry setup.
    - Created `.dockerignore` to exclude frontend, data, and artifacts from the build context.
  - Updated `railway.json` to use `DOCKERFILE` builder strategy instead of Nixpacks for more reliable builds.
  - Created `.python-version` file to specify Python 3.12.0 for Railway deployment (`.python-version`).
  - Created `vercel.json` for Vercel frontend deployment configuration with Next.js framework settings (`frontend/vercel.json`).
  - Created API configuration helper `getApiUrl` function for centralized API URL management (`frontend/src/lib/api.ts`).
  - Created `.env.example` file documenting frontend environment variables (`frontend/.env.example`).

### Fixed
- **Vercel Deployment**:
  - Fixed property name mismatch in `TerritoryFranchiseList.tsx` (`investment_min` -> `total_investment_min_usd`, `category` -> `primary_category`) to match the defined `TerritoryFranchise` interface.
  - Fixed implicit `any` type error in `LeadProfileForm.tsx` by adding type annotations to event handlers.
  - Fixed TypeScript type error in `frontend/src/app/territory/page.tsx` by renaming incorrect `selectedState` prop to `targetState` when using the `TerritoryMap` component.
  - Fixed TypeScript compilation error by updating `target` from `ES2017` to `ES2020` in `frontend/tsconfig.json` to support regex `s` (dotAll) flag used in `franchises/[id]/page.tsx`.
  - Fixed missing `@/lib/api` module error by adding exception to `.gitignore` to allow `frontend/src/lib/` directory to be tracked (`frontend/src/lib/api.ts` is now committed).
  - Added missing `leaflet`, `react-leaflet`, and `@types/leaflet` packages to `frontend/package.json` to resolve build errors in `FranchiseTerritoryMap.client.tsx`.
  - Fixed npm peer dependency conflict between React 19 and `react-simple-maps@3.0.0` by adding `--legacy-peer-deps` flag to the install command in `frontend/vercel.json`.
  - This allows Vercel builds to succeed despite `react-simple-maps` not officially supporting React 19 yet (React 19 is backward compatible).

### Changed
- **Backend CORS Configuration**:
  - Made CORS origins configurable via `ALLOWED_ORIGINS` environment variable (comma-separated list) in `src/backend/main.py`.
  - Defaults to `*` for development, but can be restricted to specific domains in production for better security.

### Fixed
- **Railway Deployment**:
  - Resolved `FileNotFoundError: /app/config/franserve/structured_output.json` by copying the `config/` directory into the Docker image.
  - Implemented `start.sh` entrypoint script to reliably handle dynamic port assignment from Railway's `$PORT` environment variable.
  - Resolved `Error: Invalid value for '--port': '$PORT' is not a valid integer` by moving the startup command and port expansion logic into a bash script instead of relying on Dockerfile shell expansion.
  - Updated `Dockerfile` to copy and execute `start.sh`.
  - Fixed Railway healthcheck failure by updating `Dockerfile` CMD to bind to the dynamic `$PORT` environment variable (`CMD uvicorn ... --port ${PORT:-8000}`).
  - Previously, the app was hardcoded to listen on port 8000, while Railway expected it to listen on the dynamically assigned `$PORT`.
  - Increased healthcheck timeout to 300s and interval to 60s in `railway.json` to allow more startup time.
  - Converted `pyproject.toml` from Flit to standard Poetry configuration.
  - Fixed `KeyError: 'name'` during Docker build by adding proper `[tool.poetry]` metadata section.
  - Standardized build backend to `poetry-core`.
  - Resolved persistent "pip: command not found" and "No module named pip" errors by switching from Nixpacks to a custom Dockerfile.
  - The Dockerfile explicitly installs system dependencies, bootstraps Poetry, and installs Python packages in a controlled environment.

### Changed
- **Frontend API Calls**:
  - Updated all hardcoded API URLs to use environment variable-based configuration (`frontend/src/app/actions.ts`, `frontend/src/app/franchises/actions.ts`, `frontend/src/app/franchises/compare/page.tsx`).
  - Replaced `http://127.0.0.1:8000` and `http://localhost:8000` with `getApiUrl()` helper function for production-ready deployment.
  - Frontend now uses `NEXT_PUBLIC_API_URL` environment variable for backend API endpoint configuration.

## [2025-11-23] - Load Comparison Button

### Added
- **Lead Detail Page**:
  - Added "Load Saved Comparison" button to the "AI Recommendations" section header (`frontend/src/app/leads/[id]/page.tsx`).
  - Implemented check for existing saved comparison analysis on page mount.
  - Added navigation to comparison page with pre-loaded lead context.

## [2025-11-22] - Lead Profile Form & Enhanced Data

### Added
- **Lead Profile Management**:
  - Added comprehensive `LeadProfileForm` component with 4 collapsible sections: Money, Interest, Territories, Motives (`frontend/src/components/LeadProfileForm.tsx`).
  - Added `updateLeadProfile` server action for patching lead data (`frontend/src/app/actions.ts`).
  - Added new fields to `LeadProfile` model in backend (`src/backend/models.py`) and frontend (`frontend/src/types/index.ts`).
    - **Money**: `net_worth`, `investment_source`, `interest` (financial notes).
    - **Interest**: `role_preference`, `home_based_preference`, `franchise_categories`, `multi_unit_preference`, `staff_preference`, `business_model_preference`, `absentee_preference`, `semi_absentee_preference`.
    - **Motives**: `trigger_event`, `current_status`, `experience_level`, `goals`, `timeline`.
    - **Territories**: Support for multiple territory objects (`{ location, state_code }`).

### Changed
- **Lead Detail Page**:
  - Integrated `LeadProfileForm` at the top of the page (`frontend/src/app/leads/[id]/page.tsx`).
  - Updated page layout to accommodate the new form.
- **AI Extraction**:
  - Enhanced `extract_profile_from_notes` in `src/backend/extractor.py` to extract all new profile fields from broker notes.
  - Updated Gemini prompt and JSON schema for richer data extraction.
- **Comparison Matrix**:
  - Updated `ComparisonTable` to display new candidate profile fields in the sidebar (`frontend/src/components/ComparisonTable.tsx`).
  - Updated `generate_comparison_analysis` in `src/backend/narrator.py` to use new profile fields (like role preference, multi-unit interest) in the AI analysis prompt.
  - Updated `compare_franchises` in `src/backend/comparison.py` to orchestrate the enhanced analysis.

## [2025-11-22] - Lead Comparison Integration

### Added
- **Comparison Feature**:
  - Implemented per-lead persistence for comparison selections.
  - Added "Save Analysis" feature to `ComparisonTable` to save the full "killer sheet" state to the lead.
  - Added `comparison_selections` and `comparison_analysis` JSONB columns to `leads` table (`docs/database/add_comparison_columns_to_leads.sql`).
  - Added server actions `getLeadComparisonSelections`, `saveLeadComparisonSelections`, `getLeadComparisonAnalysis`, `saveLeadComparisonAnalysis` (`frontend/src/app/actions.ts`).

### Changed
- **Comparison Context**:
  - Enhanced `ComparisonContext` to support lead-specific contexts (`frontend/src/contexts/ComparisonContext.tsx`).
  - Added auto-save functionality for selections when attached to a lead.
- **Lead Detail Page**:
  - Updated `LeadDetailPage` to sync comparison selections with the new context (`frontend/src/app/leads/[id]/page.tsx`).
- **Persistent Comparison Bar**:
  - Added ability to attach comparison session to a specific lead.
  - Added "Save Analysis" button and logic (`frontend/src/components/PersistentComparisonBar.tsx`).
- **Backend API**:
  - Updated `Lead` model to include comparison fields (`src/backend/models.py`).
  - Added API endpoints for managing comparison data (`src/backend/leads.py`).

## [2025-11-22] - Investment Data Fix

### Fixed
- **Investment Data Mapping**:
  - Updated `getLeadMatches` in `frontend/src/app/actions.ts` to prioritize `total_investment_min_usd` (fresh database value) over potentially stale `investment_min` from stored JSONB matches.
  - This ensures "Inv. TBD" is only shown when investment data is genuinely missing, not when it's just missing from the cached match object.

## [2025-11-22] - MatchCard Redesign & Data Fixes

### Changed
- **MatchCard**:
  - Redesigned `MatchCard` component to use a compact horizontal row layout (`frontend/src/components/MatchCard.tsx`).
  - Reduced font sizes to `text-xs`/`text-sm` and padding to `p-3` for a cleaner, smaller footprint.
  - Implemented conditional rendering for Investment, Match Score, and Description fields to hide invalid/missing data (e.g., "NaN% Match", "$0" investment).
  - Added robust fallbacks for missing company names and investment data (shows "Inv. TBD" instead of hiding).
  - Standardized component to accept `onClick` prop while maintaining backward compatibility with `onViewDetails`.
- **Lead Detail Page**:
  - Reduced vertical spacing between match cards to `space-y-2` (`frontend/src/app/leads/[id]/page.tsx`).
  - Adjusted checkbox alignment to match the new compact card layout.
  - Updated to use standardized `onClick` prop for `MatchCard`.
  - Removed sidebar placeholder for cleaner layout (`frontend/src/app/leads/[id]/page.tsx`).

### Fixed
- **Data Mapping & Hydration**:
  - Updated `get_lead_matches` in `src/backend/leads.py` to hydrate stored matches with fresh franchise details from the database.
  - Resolved "Unknown Franchise" issue caused by stale or incomplete data in the stored `matches` JSONB.
  - Updated `getLeadMatches` in `frontend/src/app/actions.ts` to robustly map franchise data from both database (stored matches) and API (fresh matches).
  - Resolved issues where franchise names were missing (showing blank or "Unknown") and match scores were NaN.
  - Standardized field access for `name`/`franchise_name`, `description`/`description_text`, and `investment_min`/`total_investment_min_usd`.

## [2025-11-22] - Comparison Table UI Improvements & Lead Sidebar

### Added
- **Comparison Table**:
  - Added "Highlight Misfits" toggle button to visually flag potential issues (red/yellow traffic lights, sold out territories).
  - Implemented a slide-in sidebar that displays detailed Lead Profile data (Financials, Preferences, Location) when misfit highlighting is active (`frontend/src/components/ComparisonTable.tsx`).

### Changed
- **Comparison Table**:
  - Reduced font sizes to `text-xs` (~12pt equivalent) and minimized padding for a more compact view.
  - Improved visual density to allow easier comparison of multiple franchises.
  - Updated layout to support side-by-side view with the Lead Profile sidebar positioned on the **left** side.

### Fixed
- **Lead Detail Page**:
  - Fixed runtime error in `CoachingCard` by properly computing `missingFields` and passing default `questions` (`frontend/src/app/leads/[id]/page.tsx`).
  - Updated `CoachingCard` to gracefully handle empty or undefined arrays (`frontend/src/components/CoachingCard.tsx`).

## [2025-11-22] - Sticky Comparison Feature

## [2025-11-20] - Scouting & Classification

### Added
- **Scouting System**:
  - Created `scouting/` directory in `data/raw/` for organized data collection.
  - Implemented `batch_cli.py` for managing batch operations.
  - Added `process_batch_results.py` for handling API responses.

### Changed
- **Data Processing**:
  - Refactored `classify_msgs.py` to support batch processing.
  - Updated `main.py` to integrate new scouting workflow.

### Fixed
- Fixed issue with rate limiting in Gemini API calls.
- Resolved path resolution errors in `extractor.py`.
