-- Migration to add 'matches' column to existing 'leads' table
ALTER TABLE leads
ADD COLUMN IF NOT EXISTS matches JSONB;

-- Add index for matches if needed (optional, but good for searching within JSONB later if required)
-- CREATE INDEX IF NOT EXISTS idx_leads_matches ON leads USING gin (matches);

