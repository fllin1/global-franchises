# Database Schema Documentation

This document provides a comprehensive overview of the FranchisesGlobal database schema structure, including tables, relationships, functions, and storage buckets.

## Database Platform

- **Platform**: Supabase (PostgreSQL)
- **Connection**: Managed via `src/api/config/supabase_config.py`

---

## Tables

### Core Franchise Tables

#### `franchises`
Main table storing franchise information and metadata.

**Core Identity Fields:**
| Column | Type | Description |
|--------|------|-------------|
| `id` | `bigint` | Primary key (auto-increment) |
| `created_at` | `timestamp with time zone` | Creation timestamp (default: `now()`) |
| `franchise_name` | `text` | Official name of the franchise (required) |
| `source_id` | `integer` | Unique identifier from source system (used for upserts) |
| `source_url` | `text` | Original source URL (e.g., Franserve) |
| `slug` | `text` | URL-friendly slug generated from franchise_name |
| `primary_category` | `text` | Primary business category (normalized from JSON) |
| `sub_categories` | `jsonb` | Array of sub-categories (legacy support) |
| `business_model_type` | `text` | Business model classification |
| `keywords` | `text` | Extracted keywords for search |

**Financial Fields (The Money):**
| Column | Type | Description |
|--------|------|-------------|
| `franchise_fee_usd` | `integer` | Initial franchise fee in USD |
| `required_cash_investment_usd` | `integer` | Required liquid capital (cash) in USD |
| `required_net_worth_usd` | `integer` | Required total net worth in USD |
| `total_investment_min_usd` | `integer` | Minimum total investment required in USD |
| `total_investment_max_usd` | `integer` | Maximum total investment required in USD |
| `royalty_details_text` | `text` | Royalty structure description (e.g., "8%", "3% Sliding Scale", "$3000 per zone per month") |
| `sba_approved` | `boolean` | Whether franchise is SBA loan pre-approved (default: `false`) |
| `sba_registered` | `boolean` | Whether franchise is registered with the SBA (separate from sba_approved) |
| `providing_earnings_guidance_item19` | `boolean` | Providing earnings guidance in Item 19 in FDD |
| `additional_fees` | `text` | Additional fees beyond franchise fee and royalties |
| `financial_assistance_details` | `text` | Details about financial assistance available (e.g., "Yes, SBA") |
| `commission_structure` | `jsonb` | Commission structure for brokers (single_unit, multi_unit, resales, area_master_developer) |
| `franchise_packages` | `jsonb` | Array of franchise packages with name, franchise_fee, total_investment_min/max, territories_count, description |

**Operational/Lifestyle Fields (The Interest):**
| Column | Type | Description |
|--------|------|-------------|
| `is_home_based` | `boolean` | Can be operated from home (default: `false`) |
| `allows_semi_absentee` | `boolean` | Allows semi-absentee ownership (default: `false`) |
| `allows_absentee` | `boolean` | Allows fully absentee ownership (default: `false`) |
| `e2_visa_friendly` | `boolean` | Qualifies for E2 visa program (default: `false`) |
| `master_franchise_opportunity` | `boolean` | Offers master franchise/area developer opportunities (default: `false`) |
| `vetfran_member` | `boolean` | Member of VetFran program (default: `false`) |
| `vetfran_discount_details` | `text` | Details of veteran discount program |

**Narrative Fields (The Motives):**
| Column | Type | Description |
|--------|------|-------------|
| `description_text` | `text` | Full description/introduction of the franchise |
| `why_franchise_summary` | `text` | Bullet points explaining why to choose this franchise |
| `ideal_candidate_profile_text` | `text` | Description of the ideal franchisee candidate (legacy field) |
| `ideal_candidate_profile` | `jsonb` | Structured ideal candidate profile (skills array, personality_traits array, role_of_owner text) |
| `market_growth_statistics` | `jsonb` | Market growth data (demographics, market_size, cagr, growth_period, recession_resistance) |

**Territory/Availability Fields:**
| Column | Type | Description |
|--------|------|-------------|
| `unavailable_states` | `jsonb` | Array of 2-letter state codes where franchise is unavailable |
| `recent_territory_checks` | `jsonb` | Array of structured territory checks with date, location, is_available, notes |
| `hot_regions` | `jsonb` | Array of hot/desirable markets (state codes or regions) |
| `canadian_referrals` | `boolean` | Accepts Canadian referrals |
| `international_referrals` | `boolean` | Accepts international referrals |
| `corporate_address` | `text` | Corporate headquarters address |

**Contact & Web Fields:**
| Column | Type | Description |
|--------|------|-------------|
| `website_url` | `text` | Official franchise website URL |
| `schedule_call_url` | `text` | Calendar booking URL for scheduling a call |

**Historical Fields:**
| Column | Type | Description |
|--------|------|-------------|
| `founded_year` | `smallint` | Year the business was founded |
| `franchised_year` | `smallint` | Year franchising began |
| `last_updated_from_source` | `date` | Last update date from source system |
| `last_scraped_at` | `timestamp with time zone` | Last time franchise data was scraped |

**Search & Metadata Fields:**
| Column | Type | Description |
|--------|------|-------------|
| `franchise_embedding` | `vector(1536)` | Vector embedding for semantic search (OpenAI text-embedding-3-small) |
| `is_active` | `boolean` | Whether the franchise is currently active (default: `true`) |
| `franchises_data` | `jsonb` | Raw/unmapped data backup (background, markets, support, financials) |
| `industry_awards` | `jsonb` | Array of industry awards with source, year, and award_name |
| `documents` | `jsonb` | Documents and resources (regular, client_focused, recent_emails, magazine_articles) |
| `resales_available` | `boolean` | Whether resales are available for this franchise |
| `resales_list` | `jsonb` | List of available resales |
| `rating` | `numeric(3,2)` | Star rating (1-5) if available |
| `support_training_details` | `jsonb` | Structured training info (program_description, cost_included, cost_details, lodging_airfare_included, site_selection_assistance, lease_negotiation_assistance, mentor_available, mentoring_length) |

**Family Brand Relationship:**
| Column | Type | Description |
|--------|------|-------------|
| `parent_family_brand_id` | `bigint` | Foreign key to `family_of_brands` table. Links franchise to its parent family brand (nullable) |

**Indexes:**
- Primary key on `id`
- Unique constraint on `source_id`
- Index on `franchise_name` for ILIKE searches
- Index on `franchise_embedding` for vector similarity search
- Indexes on boolean fields: `resales_available`, `canadian_referrals`, `international_referrals`, `sba_registered`, `providing_earnings_guidance_item19`
- GIN indexes on JSONB fields: `commission_structure`, `industry_awards`, `documents`, `franchise_packages`, `hot_regions`

**Relationships:**
- One-to-many with `franchise_categories`
- One-to-many with `contacts`
- One-to-many with `territory_checks`
- Many-to-one with `family_of_brands` (via `parent_family_brand_id`)

---

#### `family_of_brands`
Parent brand entities that contain multiple franchise brands (e.g., Driven Brands, Neighborly, Authority Brands).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `bigint` | Primary key (auto-increment) |
| `name` | `text` | Name of the family brand (e.g., "Driven Brands") |
| `source_id` | `integer` | FranID from FranServe URL (unique) |
| `website_url` | `text` | Family brand website URL |
| `contact_name` | `text` | Primary contact name |
| `contact_phone` | `text` | Contact phone number |
| `contact_email` | `text` | Contact email address |
| `logo_url` | `text` | URL to the family brand logo |
| `last_updated_from_source` | `date` | Last update date from source |
| `created_at` | `timestamptz` | Record creation timestamp |
| `updated_at` | `timestamptz` | Record update timestamp (auto-updated via trigger) |

**Indexes:**
- Primary key on `id`
- Unique constraint on `source_id`
- Index on `name` for search

**Relationships:**
- One-to-many with `franchises` (via `franchises.parent_family_brand_id`)

---

#### `categories`
Category definitions for franchise classification.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (auto-increment) |
| `name` | `text` | Category name (unique) |
| `slug` | `text` | URL-friendly slug |
| `created_at` | `timestamp` | Creation timestamp |

**Indexes:**
- Primary key on `id`
- Unique constraint on `name`

**Relationships:**
- Many-to-many with `franchises` via `franchise_categories`

---

#### `franchise_categories`
Junction table for many-to-many relationship between franchises and categories.

| Column | Type | Description |
|--------|------|-------------|
| `franchise_id` | `integer` | Foreign key to `franchises.id` |
| `category_id` | `integer` | Foreign key to `categories.id` |

**Indexes:**
- Composite primary key on (`franchise_id`, `category_id`)
- Foreign key constraints on both columns

---

#### `contacts`
Contact information for franchises (sales representatives, brokers, etc.).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (auto-increment) |
| `franchise_id` | `integer` | Foreign key to `franchises.id` |
| `name` | `text` | Contact person name |
| `title` | `text` | Job title (if available) |
| `email` | `text` | Email address |
| `phone` | `text` | Phone number |
| `other_fields` | `jsonb` | Additional contact metadata |

**Indexes:**
- Primary key on `id`
- Foreign key on `franchise_id`
- Index on `franchise_id` for efficient lookups

---

### Lead Management Tables

#### `leads`
Stores lead information, extracted profiles, and franchise matches.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (auto-increment) |
| `candidate_name` | `text` | Name of the candidate (extracted from notes) |
| `notes` | `text` | Original unstructured notes/description |
| `profile_data` | `jsonb` | Structured `LeadProfile` data (see below) |
| `matches` | `jsonb` | Array of matched franchises with narratives |
| `qualification_status` | `text` | Qualification tier: `"tier_1"` or `"tier_2"` |
| `workflow_status` | `text` | Workflow status: `"new"`, `"contacted"`, `"qualified"`, etc. |
| `created_at` | `timestamp` | Creation timestamp |
| `updated_at` | `timestamp` | Last update timestamp |

**Profile Data Structure (`profile_data` JSONB):**
```json
{
  "candidate_name": "John Doe",
  "liquidity": 500000,
  "investment_cap": 750000,
  "location": "Austin, TX",
  "state_code": "TX",
  "semantic_query": "Looking for a B2B franchise opportunity..."
}
```

**Indexes:**
- Primary key on `id`
- Index on `qualification_status`
- Index on `workflow_status`
- Index on `created_at` for sorting

**Relationships:**
- One-to-many with `lead_matches` (if implemented)

---

#### `lead_matches`
Tracks franchise matches for leads (for robust match tracking).

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (auto-increment) |
| `lead_id` | `integer` | Foreign key to `leads.id` |
| `franchise_id` | `integer` | Foreign key to `franchises.id` |
| `match_score` | `float` | Similarity/match score |
| `why_narrative` | `text` | Generated explanation for the match |
| `created_at` | `timestamp` | Creation timestamp |

**Indexes:**
- Primary key on `id`
- Foreign keys on `lead_id` and `franchise_id`
- Index on `lead_id` for efficient lookups

**Note:** Currently, matches are stored as JSONB in `leads.matches`, but `lead_matches` table exists for future normalization.

---

### Territory Management Tables

#### `territory_checks`
Tracks franchise territory availability by location with 4-level hierarchy: State -> County -> City -> Zip.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (auto-increment) |
| `franchise_id` | `integer` | Foreign key to `franchises.id` |
| `state_code` | `text` | 2-letter state code (e.g., "TX", "NY") |
| `county` | `text` | County name (e.g., "Harris County", "Essex County") |
| `city` | `text` | City name |
| `zip_code` | `text` | ZIP code |
| `covered_zips` | `text[]` | Array of ZIP codes covered by this territory |
| `latitude` | `float` | Latitude coordinate |
| `longitude` | `float` | Longitude coordinate |
| `radius_miles` | `float` | Radius of coverage in miles |
| `raw_text` | `text` | Original territory description text |
| `is_available` | `boolean` | Whether territory is available |
| `created_at` | `timestamp` | Creation timestamp |
| `updated_at` | `timestamp` | Last update timestamp |

**Indexes:**
- Primary key on `id`
- Foreign key on `franchise_id`
- Index on `franchise_id` for efficient lookups
- Index on `state_code` for state-based queries
- Index on `county` for county-based queries
- Index on `zip_code` for geospatial queries
- Index on `city` for city-based queries

**Relationships:**
- Many-to-one with `franchises`

---

### GHL (GoHighLevel) Integration Tables

#### `ghl_conversations`
Stores GHL conversation metadata.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `text` | Primary key (GHL conversation ID) |
| `location_id` | `text` | GHL location ID |
| `contact_id` | `text` | GHL contact ID |
| `full_name` | `text` | Contact full name |
| `company_name` | `text` | Company name (used to match franchises) |
| `email` | `text` | Contact email |
| `phone` | `text` | Contact phone |
| `date_added` | `timestamp` | When conversation was added |
| `date_updated` | `timestamp` | Last update timestamp |
| `last_message_date` | `timestamp` | Date of last message |
| `last_message_type` | `text` | Type of last message |
| `last_message_direction` | `text` | Direction: `"inbound"` or `"outbound"` |
| `unread_count` | `integer` | Number of unread messages |
| `tags` | `text` | Conversation tags |
| `type` | `text` | Conversation type |

**Indexes:**
- Primary key on `id`
- Index on `company_name` for franchise matching
- Index on `contact_id` for contact lookups

**Relationships:**
- One-to-many with `ghl_messages`

---

#### `ghl_messages`
Stores individual GHL messages.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `text` | Primary key (GHL message ID) |
| `conversation_id` | `text` | Foreign key to `ghl_conversations.id` |
| `contact_id` | `text` | GHL contact ID |
| `location_id` | `text` | GHL location ID |
| `date_added` | `timestamp` | When message was sent/received |
| `message_type` | `text` | Message type (e.g., "sms", "email") |
| `source` | `text` | Message source |
| `type` | `text` | Message type |
| `direction` | `text` | Direction: `"inbound"` or `"outbound"` |
| `subject` | `text` | Email subject (if applicable) |
| `body_length` | `integer` | Length of original body |
| `body_clean_length` | `integer` | Length of cleaned body |
| `body_clean` | `text` | Cleaned message body (HTML removed) |
| `processed` | `boolean` | Whether message has been processed for territory extraction (default: `false`) |
| `has_attachment_mention` | `boolean` | Whether message mentions attachments |
| `is_out_of_office` | `boolean` | Whether message is an out-of-office reply |

**Indexes:**
- Primary key on `id`
- Foreign key on `conversation_id`
- Index on `conversation_id` for efficient lookups
- Index on `processed` for filtering unprocessed messages
- Index on `direction` for filtering inbound/outbound

**Relationships:**
- Many-to-one with `ghl_conversations`

---

### Data Pipeline Tables

#### `scraping_runs`
Tracks scraping runs for data collection pipeline.

| Column | Type | Description |
|--------|------|-------------|
| `id` | `integer` | Primary key (auto-increment) |
| `run_date` | `date` | Date of the scraping run |
| `storage_path_prefix` | `text` | Prefix path in Supabase Storage |
| `status` | `text` | Status: `"pending"`, `"in_progress"`, `"completed"`, `"failed"` |
| `franchises_scraped` | `integer` | Number of franchises scraped |
| `franchises_parsed` | `integer` | Number of franchises parsed |
| `franchises_uploaded` | `integer` | Number of franchises uploaded to DB |
| `started_at` | `timestamp` | When scraping started |
| `completed_at` | `timestamp` | When scraping completed |
| `error_message` | `text` | Error message if status is `"failed"` |
| `llm_parsing_status` | `text` | LLM parsing status: `"pending"`, `"in_progress"`, `"completed"`, `"partial"`, `"failed"`, `"no_files"` |
| `llm_parsing_started_at` | `timestamp with time zone` | When LLM parsing started |
| `llm_parsing_completed_at` | `timestamp with time zone` | When LLM parsing completed |
| `metadata` | `jsonb` | Additional metadata including LLM parsing statistics |

**Indexes:**
- Primary key on `id`
- Index on `run_date` for chronological queries
- Index on `status` for filtering active runs

---

## Database Functions

### `match_franchises_hybrid`
Performs hybrid search combining vector similarity and SQL filters.

**Parameters:**
- `query_embedding` (`vector(1536)`) - Vector embedding of the search query
- `match_threshold` (`float`) - Minimum similarity threshold (default: 0.3)
- `match_count` (`integer`) - Maximum number of results to return
- `max_budget` (`integer`, optional) - Maximum investment budget filter
- `location_filter` (`text`, optional) - State code filter (e.g., "TX")

**Returns:** Array of franchise records with similarity scores

**Usage:**
```sql
SELECT * FROM match_franchises_hybrid(
  query_embedding := '[0.1, 0.2, ...]'::vector(1536),
  match_threshold := 0.3,
  match_count := 10,
  max_budget := 500000,
  location_filter := 'TX'
);
```

**Implementation:** Combines cosine similarity search on `franchise_embedding` with budget and location filters.

---

### `get_franchises_by_state`
Returns franchises available in a specific state.

**Parameters:**
- `filter_state_code` (`text`) - 2-letter state code (e.g., "TX")

**Returns:** Array of franchise records available in the specified state

**Usage:**
```sql
SELECT * FROM get_franchises_by_state('TX');
```

**Implementation:** Queries `territory_checks` table to find franchises with available territories in the specified state.

---

### `match_franchises_by_cosine_similarity`
Performs pure vector similarity search (legacy function).

**Parameters:**
- `query_embedding` (`vector(1536)`) - Vector embedding of the search query
- `match_threshold` (`float`) - Minimum similarity threshold
- `match_count` (`integer`) - Maximum number of results

**Returns:** Array of franchise records with similarity scores

**Note:** Prefer `match_franchises_hybrid` for new implementations as it includes filtering capabilities.

---

## Storage Buckets

### `raw-franchise-html`
Supabase Storage bucket for storing raw HTML files from scraping.

**Structure:**
```
raw-franchise-html/
  YYYY-MM-DD/          # Date-based organization
    franchise_123.html  # Individual franchise HTML files
    franchise_456.html
```

**Usage:**
- Scraped HTML files are uploaded here before parsing
- Files are organized by date for easy tracking
- Referenced by `scraping_runs.storage_path_prefix`

**Access:** Managed via `src/data/storage/storage_client.py`

---

## Relationships Diagram

```
franchises
  ├── franchise_categories (many-to-many)
  │     └── categories
  ├── contacts (one-to-many)
  └── territory_checks (one-to-many)

leads
  ├── lead_matches (one-to-many, optional)
  │     └── franchises
  └── matches (JSONB array, current implementation)

ghl_conversations
  └── ghl_messages (one-to-many)

scraping_runs (standalone tracking table)
```

---

## Data Types Reference

### JSONB Structures

**`leads.profile_data`:**
```typescript
{
  candidate_name?: string;
  liquidity?: number;          // USD
  investment_cap?: number;      // USD
  location?: string;
  state_code?: string;          // 2-letter code
  semantic_query: string;       // Required
}
```

**`leads.matches`:**
```typescript
Array<{
  id: number;
  franchise_name: string;
  primary_category: string;
  total_investment_min_usd?: number;
  why_narrative?: string;
  match_score?: number;
  // ... other franchise fields
}>
```

**`franchises.sub_categories`:**
```typescript
string[]  // Array of sub-category names
```

**`franchises.unavailable_states`:**
```typescript
string[]  // Array of 2-letter state codes (e.g., ["CA", "NY"])
```

**`franchises.recent_territory_checks`:**
```typescript
Array<{
  date: string;           // MM/DD/YYYY format
  location: string;       // Location description (city, state, zip, or combinations)
  is_available: boolean;  // Whether territory is available
  notes?: string;         // Additional notes, questions, or special conditions
}>
```

**`franchises.commission_structure`:**
```typescript
{
  single_unit?: {
    amount?: number;
    description: string;
  };
  multi_unit?: {
    percentage?: number;
    max_per_unit?: number;
    description: string;
  };
  resales?: {
    percentage?: number;
    max?: number;
    description: string;
  };
  area_master_developer?: {
    amount?: number | null;
    description: string;
  };
}
```

**`franchises.industry_awards`:**
```typescript
Array<{
  source: string;      // e.g., "FranServe's FRAN-TASTIC BRAND"
  year: number;        // Year the award was received
  award_name?: string; // e.g., "Fran-Tastic Brand Award"
}>
```

**`franchises.documents`:**
```typescript
{
  regular?: string[];           // Regular documents (PDFs, videos, links)
  client_focused?: string[];    // Client-focused documents
  recent_emails?: string[];     // Recent email campaign links
  magazine_articles?: string[]; // Franchise Dictionary Magazine articles
}
```

**`franchises.franchise_packages`:**
```typescript
Array<{
  name: string;              // e.g., "Development Package"
  franchise_fee: number;    // Franchise fee in USD
  total_investment_min?: number;
  total_investment_max?: number;
  territories_count?: number;
  description?: string;
}>
```

**`franchises.support_training_details`:**
```typescript
{
  program_description?: string;
  cost_included?: boolean;
  cost_details?: string;
  lodging_airfare_included?: boolean;
  site_selection_assistance?: boolean;
  lease_negotiation_assistance?: boolean;
  mentor_available?: boolean;
  mentoring_length?: string;  // e.g., "Term of FA", "Ongoing"
}
```

**`franchises.market_growth_statistics`:**
```typescript
{
  demographics?: string;        // Demographic statistics and projections
  market_size?: string;         // e.g., "$1,012 billion"
  cagr?: string;                // e.g., "6.3%"
  growth_period?: string;       // e.g., "2023 to 2030"
  recession_resistance?: string;
}
```

**`franchises.ideal_candidate_profile`:**
```typescript
{
  skills?: string[];            // Array of required skills
  personality_traits?: string[]; // Array of personality traits
  role_of_owner?: string;       // Detailed description of owner role
}
```

**`franchises.franchises_data`:**
```typescript
{
  background?: {
    year_founded?: string;
    year_franchised?: string;
    home_based?: string;
    semiabsentee_ownership_available?: string;
    absentee_ownership_available?: string;
    e2_visa_friendly?: string;
    launching_units?: string;    // e.g., "15 launching units"
    total_franchisees?: string;  // e.g., "42 total franchisees"
    // ... other background fields
  };
  available_markets?: {
    not_available?: string;
    // ... other market fields
  };
  support_and_training?: {
    // Support and training details
  };
  financials_unmapped?: {
    franchise_fee?: string;
    total_investment_range?: string;
    net_worth_requirement?: string;
    royalty?: string;
    // ... other unmapped financial fields
  };
}
```

**`territory_checks.covered_zips`:**
```typescript
string[]  // Array of ZIP codes
```

---

## Indexes Summary

### Performance-Critical Indexes

1. **`franchises`**
   - `franchise_name` (ILIKE searches)
   - `franchise_embedding` (vector similarity)
   - `source_id` (unique upserts)

2. **`territory_checks`**
   - `franchise_id` (franchise territory lookups)
   - `state_code` (state-based queries)
   - `zip_code` (geospatial queries)
   - `city` (city-based queries)

3. **`leads`**
   - `qualification_status` (filtering)
   - `workflow_status` (filtering)
   - `created_at` (sorting)

4. **`ghl_messages`**
   - `conversation_id` (message lookups)
   - `processed` (processing pipeline)
   - `direction` (filtering inbound/outbound)

---

## Migration Notes

### Schema Evolution

1. **Initial Schema (Legacy)**
   - Tables used PascalCase: `Franchises`, `Contacts`
   - Categories stored as JSONB in `franchises` table

2. **Current Schema (v2)**
   - Tables use lowercase: `franchises`, `contacts`
   - Categories normalized into `categories` and `franchise_categories`
   - Added metadata columns (`slug`, `source_url`, `last_scraped_at`, `is_active`)
   - Added `lead_matches` table for robust match tracking

3. **Recent Additions**
   - Geographic columns added to `territory_checks` (city, zip_code, latitude, longitude, radius_miles)
   - Processing columns added to `ghl_messages` (processed, has_attachment_mention, is_out_of_office)
   - `scraping_runs` table for tracking data pipeline runs
   - Financial columns added to `franchises` (franchise_fee_usd, required_cash_investment_usd, required_net_worth_usd, royalty_details_text)
   - Operational/lifestyle columns added to `franchises` (is_home_based, allows_semi_absentee, allows_absentee, e2_visa_friendly, master_franchise_opportunity, vetfran_member)
   - Narrative columns added to `franchises` (why_franchise_summary, ideal_candidate_profile_text)
   - Contact fields added to `franchises` (corporate_address, website_url)
   - Historical fields added to `franchises` (founded_year, franchised_year, last_updated_from_source)

---

## Common Queries

### Get Franchises by State
```sql
SELECT * FROM get_franchises_by_state('TX');
```

### Search Franchises (Fuzzy)
```sql
SELECT id, franchise_name, primary_category, description_text, total_investment_min_usd, slug
FROM franchises
WHERE franchise_name ILIKE '%query%'
LIMIT 20;
```

### Get Franchise Territories
```sql
SELECT *
FROM territory_checks
WHERE franchise_id = 123
ORDER BY state_code, city;
```

### Get Unprocessed GHL Messages
```sql
SELECT *
FROM ghl_messages
WHERE processed = false
ORDER BY date_added DESC
LIMIT 100;
```

### Hybrid Search (via RPC)
```python
# Python example
response = supabase_client().rpc("match_franchises_hybrid", {
    "query_embedding": embedding_vector,
    "match_threshold": 0.3,
    "match_count": 10,
    "max_budget": 500000,
    "location_filter": "TX"
}).execute()
```

---

## Notes

- All timestamps are stored in UTC
- Vector embeddings use OpenAI's `text-embedding-3-small` model (1536 dimensions)
- The `leads.matches` field currently stores matches as JSONB, but `lead_matches` table exists for future normalization
- Territory data is extracted from GHL messages and normalized using LLM + pgeocode
- Scraping runs are tracked in `scraping_runs` and raw HTML is stored in Supabase Storage

---

## Related Documentation

- **Backend Models**: `src/backend/models.py`
- **API Configuration**: `src/api/config/supabase_config.py`
- **Storage Client**: `src/data/storage/storage_client.py`
- **Changelog**: `changelog.md` (contains migration history)



