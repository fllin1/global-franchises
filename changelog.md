# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
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
- **Railway Deployment**:
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
