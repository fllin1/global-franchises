-- ==========================================
-- Database Cleanup & Normalization V2.1
-- Goal: Remove unused tables, standardize names, populate missing slugs, fix categories
-- ==========================================

-- 1. Drop unused tables
-- ==========================================
-- The "Leads" table (capital L, UUID pk) is a relic and not used by the codebase.
-- The "leads" table (lowercase, BIGINT pk) is the active one.
DROP TABLE IF EXISTS "Leads";


-- 2. Rename "Contacts" to "contacts"
-- ==========================================
DO $$
BEGIN
    IF EXISTS (SELECT FROM pg_tables WHERE tablename = 'Contacts') THEN
        ALTER TABLE "Contacts" RENAME TO contacts;
    END IF;
END
$$;


-- 3. Populate missing slugs
-- ==========================================
-- Generate slugs from franchise_name for all rows where slug is NULL
UPDATE franchises
SET slug = lower(regexp_replace(franchise_name, '[^a-zA-Z0-9]+', '-', 'g'))
WHERE slug IS NULL AND franchise_name IS NOT NULL;

-- Trim potential trailing dashes
UPDATE franchises
SET slug = trim(both '-' from slug)
WHERE slug IS NOT NULL;


-- 4. Normalize primary_category
-- ==========================================
-- Extract plain text from JSON-like string: "['Repair & Restoration']" -> "Repair & Restoration"

-- Create a temporary function to extract category name
CREATE OR REPLACE FUNCTION extract_category_name(raw_text text)
RETURNS text AS $$
DECLARE
    cleaned_text text;
BEGIN
    -- If it's null, return null
    IF raw_text IS NULL THEN
        RETURN NULL;
    END IF;

    -- If it looks like a JSON array string "['Value']" or '["Value"]'
    IF raw_text ~* '^\[''.*''\]$' OR raw_text ~* '^\[".*"\]$' THEN
        -- Remove brackets and quotes
        cleaned_text := regexp_replace(raw_text, '^[\["''\s]+|[\]"''\s]+$', '', 'g');
        RETURN cleaned_text;
    END IF;

    -- If it's already plain text, return as is
    RETURN raw_text;
END;
$$ LANGUAGE plpgsql;

-- Update the column
UPDATE franchises
SET primary_category = extract_category_name(primary_category)
WHERE primary_category LIKE '[%';

-- Drop the helper function
DROP FUNCTION extract_category_name;

