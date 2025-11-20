# Database & Data Pipeline

## Overview

This codebase implements a data pipeline for collecting and storing franchise information from FranServe and managing leads.

### Data Pipeline (Data Lake Architecture)
- **Scraping**: Logs into FranServe, retrieves franchise page URLs, scrapes detailed HTML data, and uploads it to **Supabase Storage** (`raw-franchise-html` bucket).
- **Data Lake**: Raw HTML files are stored in Supabase Storage with a date-based prefix (e.g., `YYYY-MM-DD/filename.html`).
- **Parsing**: Parses the HTML files directly from Supabase Storage to extract structured franchise and contact data into JSON format.
- **Uploading**: Connects to Supabase, upserts parsed data to the database.
- **Tracking**: `scraping_runs` table tracks each scraping session, including status, file counts, and storage locations.

### Database Schema (V2)

The database has been refactored (see `refactor_schema_v2.sql`) to follow standard naming conventions and normalization.

#### Core Tables
- **`franchises`**: The main table for franchise data.
  - `id`, `source_id`, `franchise_name`, `primary_category`
  - `slug`, `source_url`, `last_scraped_at`, `is_active`
  - `franchise_embedding` (Vector)
- **`categories`**: Normalized categories.
  - `id`, `name`, `slug`
- **`franchise_categories`**: Join table for Many-to-Many relationship between franchises and categories.
- **`contacts`**: Contact information for franchises.
- **`territory_checks`**: Log of availability checks for specific states/territories.

#### Metadata
- **`scraping_runs`**: Tracks history of scraping jobs, including date, status, and storage paths.

#### Leads & Matching
- **`leads`**: Stores lead profiles and notes.
- **`lead_matches`**: Stores computed matches between leads and franchises with scores and reasoning.

### Key Scripts
- **`src/data/storage/storage_client.py`**: Handles interactions with Supabase Storage.
- **`src/data/franserve/scrapper.py`**: Handles authentication, URL collection, data scraping.
- **`src/data/functions/extract.py`**: Orchestrates scraping (to Storage) and parsing (from Storage).
- **`src/data/franserve/html_formatter.py`**: Parses raw HTML into structured JSON.
- **`src/data/upsert_supabase.py`**: Uploads JSON data to Supabase (`franchises`, `categories`, `contacts`).

### Functions
- **`match_franchises_hybrid`**: Performs hybrid search (Vector similarity + Filters for Budget/Location/Availability).
- **`get_franchises_by_state`**: Retrieves available franchises for a given state code.
