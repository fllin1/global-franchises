# Franchise Matching Platform - Project Plan

This to-do list tracks the progress of building the franchise matching platform, from initial setup to final deployment.

---

## Milestone 1: Foundation & Setup

- [x] **(P0)** Create Database Tables in Supabase
  - **Status:** Completed
  - **Deliverables:** `Franchises.sql`, `Contacts.sql`
- [x] **(P1)** Setup Python Development Environment
  - **Status:** Completed
  - **Notes:** Environment created using `venv`. Key libraries `beautifulsoup4`, `requests`, `supabase`, `python-dotenv`, `tqdm` are installed.

---

## Milestone 2: ETL (Extract, Transform, Load) Pipeline

- [x] **(P0)** Develop Data Scraper/Parser Script
  - **Status:** Completed
  - **Notes:** Scrapes `franservesupport.com` and saves raw HTML content.
- [x] **(P0)** Implement HTML Data Parsing
  - **Status:** Completed
  - **Notes:** Parses the saved HTML files to extract structured data into JSON format.
- [ ] **(P0)** Test Parser with Edge Cases
  - **Status:** In Progress
  - **Action:** Create a test suite that runs the parser on at least 3-5 different HTML files, including those with missing sections, nested tags, and unusual formatting to ensure robustness.
- [x] **(P1)** Develop Database Population Script
  - **Status:** Completed
  - **Notes:** Script reads parsed `.json` files and prepares them for database insertion.
- [ ] **(P0)** Test Database Population Script
  - **Status:** In Progress
  - **Action:** Before running on the full dataset, test the uploader script with a small batch (5-10 files) against a staging/test table in Supabase. Verify `upsert` logic works correctly for both new and existing `source_id`s. Check that contacts are linked to the correct franchise `id`.
- [x] **(P1)** Execute Full Data Population
  - **Status:** Completed
  - **Notes:** The parser and uploader scripts have been run on the entire dataset.
- [x] **(P0)** Develop Embedding Generation Script
  - **Status:** Completed
  - **Notes:** Script will read franchise data (especially `description_text`) from the database, generate embeddings using a chosen model, and save them back to the `franchise_embedding` column.
- [ ] **(P0)** Test Embedding Generation Script
  - **Status:** Not Started
  - **Action:** Run the script on a small sample of franchises. Verify in the Supabase table that the `franchise_embedding` column is populated with vectors of the correct dimension.
- [x] **(P1)** Implement AI Keyword Generation
  - **Status:** Completed
  - **Notes:** Feed the `description_text` to an LLM with a prompt to extract relevant keywords as a JSON array. This can be integrated into the embedding or population script.
- [ ] **(P1)** Test AI Keyword Generation
  - **Status:** Not Started
  - **Action:** Test the keyword generation prompt on 5-10 different franchise descriptions. Review the output JSON for relevance and correct formatting.

---

## Milestone 3: Core Matching Algorithm

- [ ] **(P0)** Develop Analyzer Agent Logic
  - **Status:** In Progress (Owner: `lin.marcel.pro@gmail.com`)
  - **Notes:** Implements the logic to break down a user's lead/profile into structured data points for filtering.
- [ ] **(P0)** Develop Prompt Engineer Agent Logic
  - **Status:** In Progress (Owner: `lin.marcel.pro@gmail.com`)
  - **Notes:** Implements the logic to dynamically create a detailed prompt for the final LLM-based matching stage.
- [ ] **(P0)** Develop Core Matching Algorithm
  - **Status:** Not Started
  - **Notes:** This function will orchestrate the full matching process:
    1.  **Stage 1:** Hard filtering using structured data (e.g., `investment_max`, `unavailable_states`).
    2.  **Stage 2:** Semantic search using vector similarity (cosine distance) on embeddings.
    3.  **Stage 3:** Re-ranking of top candidates using a detailed LLM prompt.
- [ ] **(P0)** Test Matching Algorithm
  - **Status:** Not Started
  - **Action:** Create a testing script that feeds 3-5 mock user profiles into the algorithm. Manually review the results from each stage (hard filtering, vector search, final re-ranking) to ensure they are logical and accurate.
- [ ] **(P1)** Create API Endpoint for Matching
  - **Status:** Not Started
  - **Notes:** Use a framework like Flask or FastAPI to wrap the matching algorithm in a callable API endpoint.
- [ ] **(P1)** Test API Endpoint
  - **Status:** Not Started
  - **Action:** Once deployed locally, use a tool like `curl` or Postman to send requests with mock user profiles to the API endpoint. Verify that you receive a well-formatted JSON response with the franchise matches.

---

## Milestone 4: Dashboard & Analytics

- [ ] **(P2)** Design Dashboard Layout & Metrics
  - **Status:** Not Started
  - **Notes:** Define the Key Performance Indicators (KPIs) and charts needed, such as franchises by category, investment distribution, etc.
- [ ] **(P1)** Develop Bokeh Data Queries
  - **Status:** Not Started
  - **Notes:** Write the backend Python/pandas functions that query the Supabase database to fetch and aggregate data for the dashboard.
- [ ] **(P1)** Build Interactive Bokeh Dashboard
  - **Status:** Not Started
  - **Notes:** Develop the main dashboard application using the data queries.
- [ ] **(P2)** Deploy Bokeh Dashboard
  - **Status:** Not Started
  - **Notes:** Host the dashboard application to make it accessible via a URL.

---

## Milestone 5: Integration & Production

- [ ] **(P1)** Build n8n Workflow for Full Process
  - **Status:** Not Started
  - **Notes:** This workflow will automate the entire lead-to-match process by calling the various API endpoints.
- [ ] **(P0)** Perform End-to-End Testing
  - **Status:** Not Started
  - **Notes:** Test the complete n8n workflow with realistic lead data (e.g., Tier 1 leads) to ensure every step functions correctly in sequence.
- [ ] **(P0)** Deploy to Production
  - **Status:** Not Started
  - **Notes:** Finalize all environment variables, API keys, and deploy all services to a production-ready environment.
