# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

### Added
- **Territory Explorer**:
  - Implemented a new interactive map interface for searching franchises by state (`frontend/src/app/territory/page.tsx`).
  - Added `/api/franchises/by-location` endpoint to backend for fetching franchises by state code.
  - Integrated `TerritoryMap`, `TerritorySearch`, and `TerritoryFranchiseList` components.

- **Lead Analysis & Narratives**:
  - Added `/analyze-lead` endpoint to analyze lead notes and return matches with personalized narratives.
  - Implemented `generate_match_narratives` in `src/backend/narrator.py` using Gemini to generate "why this fits" explanations for each match.
  - Created `extract_profile_from_notes` to parse unstructured lead data into a structured `LeadProfile`.

- **Database**:
  - Added `territory_checks` table for tracking franchise availability by territory.
  - Added `match_franchises_hybrid` function for cosine similarity search combined with keyword matching.
  - Added migration scripts for territory checks and franchise state search (`docs/database/`).

- **ETL & Integrations**:
  - Implemented GHL (GoHighLevel) conversation and message extraction pipeline.
  - Added HTML cleaning and formatting for better text extraction from franchise data.
  - Added keyword extraction and embedding generation for franchise profiles.

### Changed
- **Search Logic**:
  - Enhanced `hybrid_search` to support improved matching criteria and increased default match count.
  - Refactored extraction logic for better modularity and testing.

### Fixed
- **Bug Fixes**:
  - Fixed HTML cleaning function to handle footer noise better.
  - Resolved issues in feature extraction tests.
  - Updated `.gitignore` to exclude documentation references and unnecessary files.

## [2024-11-19] - Initial Backend & ETL Setup

### Added
- Initial project structure for backend (FastAPI) and frontend (Next.js).
- Basic database schema for franchises and leads.
- Scraper and HTML formatter for Franserve data.

