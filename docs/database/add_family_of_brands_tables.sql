-- Migration: Add Family of Brands tables
-- Description: Creates family_of_brands table and links franchises to their parent family brands
-- Date: 2025-12-02

-- ============================================
-- 1. Create family_of_brands table
-- ============================================
CREATE TABLE IF NOT EXISTS family_of_brands (
    id BIGSERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    source_id INTEGER UNIQUE,  -- FranID from URL (e.g., 2353 for Driven Brands)
    website_url TEXT,
    contact_name TEXT,
    contact_phone TEXT,
    contact_email TEXT,
    logo_url TEXT,  -- URL to the family brand logo
    last_updated_from_source DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add comments for documentation
COMMENT ON TABLE family_of_brands IS 'Parent brand families that contain multiple franchise brands (e.g., Driven Brands contains 1-800 Radiator, Maaco, Meineke)';
COMMENT ON COLUMN family_of_brands.source_id IS 'FranID from FranServe URL (frandevcompany_details.asp?FranID=XXXX)';
COMMENT ON COLUMN family_of_brands.name IS 'Name of the family brand (e.g., Driven Brands, Alliance Franchise Brands)';

-- Create index on source_id for fast lookups
CREATE INDEX IF NOT EXISTS idx_family_of_brands_source_id ON family_of_brands(source_id);

-- Create index on name for search
CREATE INDEX IF NOT EXISTS idx_family_of_brands_name ON family_of_brands(name);

-- ============================================
-- 2. Add parent_family_brand_id to franchises table
-- ============================================
ALTER TABLE franchises 
ADD COLUMN IF NOT EXISTS parent_family_brand_id BIGINT REFERENCES family_of_brands(id) ON DELETE SET NULL;

COMMENT ON COLUMN franchises.parent_family_brand_id IS 'Foreign key to family_of_brands table. Links franchise to its parent family brand (nullable - not all franchises belong to a family)';

-- Create index for efficient joins
CREATE INDEX IF NOT EXISTS idx_franchises_parent_family_brand ON franchises(parent_family_brand_id);

-- ============================================
-- 3. Create updated_at trigger for family_of_brands
-- ============================================
-- First, create the trigger function if it doesn't exist
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger for family_of_brands
DROP TRIGGER IF EXISTS update_family_of_brands_updated_at ON family_of_brands;
CREATE TRIGGER update_family_of_brands_updated_at
    BEFORE UPDATE ON family_of_brands
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================
-- 4. Create helper view for franchise-family relationships
-- ============================================
CREATE OR REPLACE VIEW franchises_with_family AS
SELECT 
    f.*,
    fb.name AS family_brand_name,
    fb.source_id AS family_brand_source_id,
    fb.website_url AS family_brand_website
FROM franchises f
LEFT JOIN family_of_brands fb ON f.parent_family_brand_id = fb.id;

COMMENT ON VIEW franchises_with_family IS 'Convenience view joining franchises with their parent family brand information';












