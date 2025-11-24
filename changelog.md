# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
