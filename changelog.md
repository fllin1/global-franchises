# Changelog

All notable changes to this project will be documented in this file.

## [Unreleased]

## [2025-11-20] - Territory Extraction System

### Added
- **Database**:
  - Added `processed`, `has_attachment_mention`, and `is_out_of_office` columns to `ghl_messages` table (`docs/database/add_ghl_messages_processing_columns.sql`).

## [2025-11-20] - Data Lake Implementation

### Added
- **Data Lake Architecture**:
  - Implemented Supabase Storage integration for storing raw HTML (`src/data/storage/storage_client.py`).
  - Created `scraping_runs` table to track scraping history (`docs/database/create_scraping_runs_table.sql`).
  - Added `migrate_local_to_storage.py` script to move local files to the cloud.
- **Testing**:
  - Added `tests/test_storage_client.py` and `tests/extract/test_extractor_storage.py` to verify storage operations.

### Changed
- **Scraping Pipeline**:
  - Updated `src/data/franserve/scrapper.py` to upload HTML to Supabase Storage instead of local disk.
  - Updated `src/data/functions/extract.py` to scrape to Storage and parse from Storage.
  - Updated `src/data/nlp/genai_data_batch.py` to process files directly from Storage.
- **File Management**:
  - Deprecated local file storage for scraping.
  - Added `StorageClient` to handle cloud file operations.
- **Documentation**:
  - Updated `docs/database/README.md` to reflect the new Data Lake architecture.
  - Updated `README.md` with new pipeline execution steps.

### Fixed
- Decoupled scraping and parsing steps, allowing independent scaling and re-processing.
- Removed dependency on local file system for data processing.

## [2025-11-20] - Database Cleanup

### Removed
- **Unused Tables**: Dropped the unused `Leads` table (capital L) to avoid confusion with the active `leads` table.

### Changed
- **Database Schema**:
  - Renamed `Contacts` table to `contacts` to match standard naming conventions.
  - Normalized `primary_category` in `franchises` table (converted JSON strings to plain text).
  - Populated missing `slug` values for all franchises using `franchise_name`.
- **Backend Code**:
  - Updated `src/data/upsert_supabase.py` to reference the renamed `contacts` table.

## [2025-11-20] - Database Schema Refactor

### Changed
- **Database Schema**:
  - Refactored database schema to standard naming conventions (`refactor_schema_v2.sql`).
  - Renamed `Franchises` table to `franchises`.
  - Normalized categories into `categories` and `franchise_categories` tables.
  - Added `lead_matches` table for robust match tracking.
  - Added metadata columns (`slug`, `source_url`, `last_scraped_at`, `is_active`) to `franchises`.
- **Backend Logic**:
  - Updated `LeadProfile` and added `Franchise` / `Category` Pydantic models in `src/backend/models.py`.
  - Updated `upsert_supabase.py` to handle new schema and insert categories relationally.
  - Enhanced `html_formatter.py` to extract `primary_category` and generate `slug` for franchises.
  - Updated `match_franchises_hybrid` and `get_franchises_by_state` SQL functions to use new table structure.

## [2025-11-20] - Broker Dashboard Evolution

### Added
- **Persistent Lead Management**:
  - Implemented `leads` table schema for storing profiles and notes (`docs/database/create_leads_table.sql`).
  - Created Leads CRUD API (`src/backend/leads.py`).
  - Added `Lead` and `LeadCreate` models to backend.
- **Franchise Deep Dive**:
  - Added `GET /api/franchises/{id}` endpoint for full FDD data (`src/backend/franchises.py`).
  - Implemented `MatchDetailModal` in frontend to display deep insights.
- **Dashboard UI**:
  - Created `DashboardLayout` with persistent `Sidebar` navigation.
  - Implemented `LeadsPage` (List View) with status filtering (`frontend/src/app/leads/page.tsx`).
  - Implemented `LeadDetailPage` (Workbench) with Profile Editor and Match Analysis (`frontend/src/app/leads/[id]/page.tsx`).
  - Created "New Lead" ingestion flow (`frontend/src/app/leads/new/page.tsx`).
  - Updated `DashboardHome` with high-level metrics and quick actions.

### Changed
- **Backend Architecture**:
  - Refactored `main.py` to use modular routers (`leads_router`, `franchises_router`).
  - Updated `LeadProfile` model to include `candidate_name`.
  - Enhanced `extractor.py` to extract candidate names from notes.
- **Frontend**:
  - Updated `MatchCard` to support click interactions.
  - Refactored `actions.ts` to support persistent lead operations (`getLeads`, `createLead`, `deleteLead`).

## [2025-11-20] - Changelog Documentation & Cursor Rules

### Added
- Comprehensive changelog documenting all project features, enhancements, and fixes.
- Created `.cursorrules` file with mandatory changelog maintenance rules to ensure all changes are properly documented in the correct format.
- Updated `README.md` to include documentation for the new Web Application (Dashboard, Map, API) and setup instructions.

## [2025-11-19] - Territory Explorer, Lead Analysis & Search Enhancements

### Added
- **Territory Explorer**:
  - Implemented interactive map interface for searching franchises by state (`frontend/src/app/territory/page.tsx`).
  - Added `/api/franchises/by-location` endpoint to backend for fetching franchises by state code.
  - Created `TerritoryMap`, `TerritorySearch`, and `TerritoryFranchiseList` components for enhanced UX.
  - Added `get_franchises_by_state` database function for efficient state-based franchise queries.

- **Lead Analysis & Narratives**:
  - Added `/analyze-lead` endpoint to analyze lead notes and return matches with personalized narratives.
  - Implemented `generate_match_narratives` in `src/backend/narrator.py` using Gemini to generate "why this fits" explanations for each match.
  - Created `extract_profile_from_notes` to parse unstructured lead data into a structured `LeadProfile`.
  - Enhanced lead analysis response to include optional backend narrative for matches.

- **Database Enhancements**:
  - Added `territory_checks` table for tracking franchise availability by territory.
  - Added `match_franchises_hybrid` function for cosine similarity search combined with keyword matching.
  - Added `match_franchises_by_cosine_similarity` function for enhanced search capabilities.
  - Created migration scripts for territory checks and franchise state search (`docs/database/`).

- **Frontend**:
  - Initial Next.js frontend setup with TypeScript, Tailwind CSS, and ESLint.
  - Created `MatchCard` and `CoachingCard` components for displaying franchise matches.
  - Implemented lead analysis UI with franchise matching display.

### Changed
- **Search Logic**:
  - Enhanced `hybrid_search` to support improved matching criteria.
  - Updated default `match_count` to 10 in hybrid search functions and related queries for improved search results.
  - Refactored extraction logic for better modularity and testing.

### Fixed
- Fixed HTML cleaning function to handle footer noise better in email content.
- Resolved issues in feature extraction tests.
- Updated `.gitignore` to exclude documentation references and unnecessary files.
- Improved Jupyter notebook execution counts and output structures for better data handling.

## [2025-08-16] - Bug Fixes

### Fixed
- Fixed mail message parsing issue with `None` parent in GHL message cleaning pipeline.
- Enhanced `clean_messages_body.py` to better handle edge cases in message parsing.

## [2025-08-13] - GHL Integration Merge

### Changed
- Merged `feature/etl` branch into `master` with complete GHL integration.

## [2025-08-10] - GoHighLevel (GHL) Integration

### Added
- **GHL Conversation Pipeline**:
  - Implemented GHL conversation and message extraction pipeline (`src/ghl/get_messages.py`).
  - Added HTML cleaning and formatting utilities for GHL message bodies (`src/ghl/utils/clean_messages_body.py`).
  - Created Jupyter notebook for GHL conversation analysis (`notebooks/2.1-ghl-conversations.ipynb`).

- **GHL Data Loading**:
  - Implemented GHL data loading to Supabase (`src/ghl/load_ghl_to_supabase.py`).
  - Added database schema for GHL tables (`docs/database/create_ghl_tables.sql`).
  - Created pipeline for loading conversation data into database.

## [2025-07-31] - Extraction Bug Fixes & Tests

### Fixed
- Fixed bugs in feature extraction logic.
- Improved file manager functionality.

### Added
- Added comprehensive tests for file manager (`tests/extract/test_file_manager.py`).
- Enhanced extraction functions with better error handling.

## [2025-07-29] - Data Extraction Reorganization

### Changed
- Reorganized data extraction modules for better structure and maintainability.
- Refactored extraction functions into modular components (`src/data/functions/extract.py`, `src/data/functions/file_manager.py`).
- Updated README with clearer project structure and documentation.
- Moved HTML formatter improvements and keyword extraction logic.

### Removed
- Removed deprecated modeling and plotting modules.
- Cleaned up unused utility functions.

## [2025-07-27] - ETL Pipeline Implementation

### Added
- **Franserve Scraping & Processing**:
  - Implemented web scraper for Franserve franchise data (`src/data/franserve/scrapper.py`).
  - Added HTML formatter with manual and LLM-based formatting (`src/data/franserve/html_formatter.py`).
  - Created HTML to prompt conversion utilities (`src/data/franserve/html_to_prompt.py`).

- **Keyword Extraction & Embeddings**:
  - Implemented keyword extraction using Gemini (`src/data/nlp/genai_keywords.py`).
  - Added batch processing for keyword extraction (`src/data/nlp/genai_keywords_batch.py`).
  - Created embedding generation pipeline (`src/data/embeddings/embeddings.py`).
  - Added support for multiple embedding providers:
    - Google Gemini Embedding 001 (`src/data/embeddings/genai_embeddings.py`)
    - OpenAI Text Embedding 3 Small (`src/data/embeddings/openai_embeddings.py`)

- **AI Integration**:
  - Integrated Google Gemini API for data processing (`src/api/genai_gemini.py`).
  - Added batch processing support for Gemini API (`src/api/genai_gemini_batch.py`).
  - Created configuration management for AI providers (`src/api/config/`).

- **Database & Batch System**:
  - Implemented batch processing system for large-scale data operations (`docs/database/BATCH_SYSTEM.md`).
  - Added Supabase integration for data storage (`src/data/upsert_supabase.py`).
  - Created structured output schemas for LLM responses (`config/franserve/structured_output.json`).

- **Notebooks & Documentation**:
  - Added Jupyter notebook for NLP data processing (`notebooks/1.2-data-nlp.ipynb`).
  - Created comprehensive TODO documentation (`docs/TODO.md`).

## [2025-07-21] - Initial Project Setup

### Added
- **Project Structure**:
  - Initial project structure with Poetry for dependency management.
  - Backend structure with FastAPI framework.
  - Database pipeline and schema design.
  - Basic project documentation and README.

- **Franserve Data Processing**:
  - Initial Franserve scraper implementation (`src/data/franserve/scrapper.py`).
  - HTML formatter for franchise data (`src/data/franserve/html_formatter.py`).
  - Dataset management utilities (`src/dataset.py`).

- **Database**:
  - Database schema documentation (`docs/database/`).
  - Database flow diagrams and documentation.
  - Supabase integration setup.

- **Testing**:
  - Initial test suite for HTML formatter (`tests/test_html_formatter.py`).
  - Tests for scraper functionality (`tests/test_scrapper.py`).
  - Supabase connection tests (`tests/test_supabase.py`).

- **Documentation**:
  - Project README with setup instructions.
  - TODO list for future development (`docs/TODO.md`).
  - Database documentation and flow diagrams.
