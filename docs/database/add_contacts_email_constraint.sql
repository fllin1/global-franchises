-- Migration: Add unique constraint on contacts(franchise_id, email)
-- Date: 2025-11-24
-- Description: Enables upsert on contacts using email as conflict resolution key

-- First, clean up any potential duplicates (keep the most recent one)
-- This is done by deleting older duplicates before adding the constraint
DELETE FROM contacts a
USING contacts b
WHERE a.id < b.id
  AND a.franchise_id = b.franchise_id
  AND a.email = b.email
  AND a.email IS NOT NULL;

-- Add unique constraint on (franchise_id, email) for non-null emails
-- Using a partial unique index to only apply to non-null emails
CREATE UNIQUE INDEX IF NOT EXISTS contacts_franchise_email_unique_idx 
ON contacts (franchise_id, email) 
WHERE email IS NOT NULL;

-- Add comment explaining the constraint
COMMENT ON INDEX contacts_franchise_email_unique_idx IS 'Unique constraint for upsert on contacts by franchise_id and email. Only applies to non-null emails.';























