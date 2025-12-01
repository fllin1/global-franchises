-- Migration: Add territory normalization fields
-- Date: 2025-11-30
-- Description: Adds 'country' and 'is_resale' columns to territory_checks table
--              for international support and resale tracking

-- Add country column (default 'US' for existing records)
ALTER TABLE territory_checks 
ADD COLUMN IF NOT EXISTS country TEXT DEFAULT 'US';

-- Add is_resale boolean column (default false for existing records)
ALTER TABLE territory_checks 
ADD COLUMN IF NOT EXISTS is_resale BOOLEAN DEFAULT FALSE;

-- Add index for country-based queries (useful for filtering US vs international)
CREATE INDEX IF NOT EXISTS idx_territory_checks_country ON territory_checks(country);

-- Add index for resale filtering
CREATE INDEX IF NOT EXISTS idx_territory_checks_is_resale ON territory_checks(is_resale) WHERE is_resale = TRUE;

-- Comments for documentation
COMMENT ON COLUMN territory_checks.country IS 'ISO 3166-1 alpha-2 country code (e.g., US, CA for Canada). Defaults to US.';
COMMENT ON COLUMN territory_checks.is_resale IS 'Whether this territory check is for a resale opportunity';



