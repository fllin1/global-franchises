# Database Features and Data Scripts

## Implemented Features

This codebase implements a data pipeline for collecting and storing franchise information from FranServe:

- **Scraping**: Logs into FranServe, retrieves franchise page URLs, scrapes detailed HTML data for each franchise, and saves it locally.
- **Parsing**: Parses the scraped HTML to extract structured franchise and contact data into JSON format.
- **Uploading**: Connects to Supabase, upserts franchise data (insert or update based on source_id), manages associated contacts by deleting old ones and inserting new, ensuring data integrity.

The pipeline handles errors gracefully, uses logging, and provides progress tracking.

## Scripts in src/data/

- **franserve/scrapper.py**: Handles authentication, URL collection, data scraping, and saving raw HTML files.
- **franserve/html_formatter.py**: Parses raw HTML into structured JSON with franchise details and contacts.
- **upsert_supabase.py**: Loads JSON data, initializes Supabase client, and performs upsert operations for franchises and contacts.
