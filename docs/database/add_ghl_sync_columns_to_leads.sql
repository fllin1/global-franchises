-- Migration: Add GHL sync columns to leads table
-- Date: 2024-12-11
-- Purpose: Enable two-way sync between leads and GoHighLevel contacts/opportunities

-- Add GHL contact ID column
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghl_contact_id TEXT;

-- Add GHL opportunity ID column
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghl_opportunity_id TEXT;

-- Add last synced timestamp
ALTER TABLE leads ADD COLUMN IF NOT EXISTS ghl_last_synced_at TIMESTAMPTZ;

-- Add indexes for efficient lookups
CREATE INDEX IF NOT EXISTS idx_leads_ghl_contact_id ON leads(ghl_contact_id) WHERE ghl_contact_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_leads_ghl_opportunity_id ON leads(ghl_opportunity_id) WHERE ghl_opportunity_id IS NOT NULL;

-- Add comments for documentation
COMMENT ON COLUMN leads.ghl_contact_id IS 'GoHighLevel contact ID for two-way sync';
COMMENT ON COLUMN leads.ghl_opportunity_id IS 'GoHighLevel opportunity ID for pipeline tracking';
COMMENT ON COLUMN leads.ghl_last_synced_at IS 'Timestamp of last successful sync with GHL';
