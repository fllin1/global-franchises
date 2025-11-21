-- Add structured geographic columns to territory_checks table
ALTER TABLE territory_checks
ADD COLUMN IF NOT EXISTS city TEXT,
ADD COLUMN IF NOT EXISTS zip_code TEXT,
ADD COLUMN IF NOT EXISTS covered_zips TEXT[],
ADD COLUMN IF NOT EXISTS latitude FLOAT,
ADD COLUMN IF NOT EXISTS longitude FLOAT,
ADD COLUMN IF NOT EXISTS radius_miles FLOAT;

-- Create indexes for geospatial queries
CREATE INDEX IF NOT EXISTS idx_territory_checks_zip_code ON territory_checks(zip_code);
CREATE INDEX IF NOT EXISTS idx_territory_checks_city ON territory_checks(city);

