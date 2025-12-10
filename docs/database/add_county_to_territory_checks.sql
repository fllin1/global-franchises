-- Migration: Add county column to territory_checks table
-- Date: 2025-11-29
-- Description: Adds county-level granularity to territory checks for 4-level hierarchy
--              (State -> County -> City -> Zip)

-- Add county column
ALTER TABLE territory_checks 
ADD COLUMN IF NOT EXISTS county TEXT;

-- Add index for county-based queries
CREATE INDEX IF NOT EXISTS idx_territory_checks_county ON territory_checks(county);

-- Comment for documentation
COMMENT ON COLUMN territory_checks.county IS 'County name for territory check location (e.g., Harris County, Essex County)';















