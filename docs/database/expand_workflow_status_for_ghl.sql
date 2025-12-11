-- Migration: Expand workflow_status for GHL Lead Nurturing pipeline sync
-- Date: 2024-12-11
-- Purpose: Expand workflow_status to match all 12 stages in the GHL "Lead Nurturing" pipeline
--          for full two-way sync between FranchisesGlobal and GoHighLevel

-- Step 1: Migrate existing data BEFORE dropping constraint
-- (Do this first while old values are still valid)
UPDATE leads SET workflow_status = 'new_lead' WHERE workflow_status = 'new';
UPDATE leads SET workflow_status = 'initial_sms_sent' WHERE workflow_status = 'contacted';
UPDATE leads SET workflow_status = 'qualified_post_deeper_dive' WHERE workflow_status = 'qualified';
UPDATE leads SET workflow_status = 'franchises_presented' WHERE workflow_status = 'presented';
UPDATE leads SET workflow_status = 'disqualified' WHERE workflow_status = 'closed_lost';
-- closed_won stays as closed_won

-- Step 2: Drop existing CHECK constraint
ALTER TABLE leads DROP CONSTRAINT IF EXISTS leads_workflow_status_check;

-- Step 3: Add new CHECK constraint with all 12 GHL "Lead Nurturing" pipeline stages
-- Mapping:
--   new_lead                    -> "New Lead"
--   initial_sms_sent            -> "Initial SMS Sent"
--   sms_engaged_scheduling      -> "SMS Engaged - Scheduling"
--   deeper_dive_scheduled       -> "Deeper Dive Scheduled"
--   needs_manual_followup       -> "Needs Manual Follow-up"
--   qualified_post_deeper_dive  -> "Qualified - Post Deeper Dive"
--   franchises_presented        -> "Franchise(s) Presented"
--   funding_intro_made          -> "Funding Intro Made"
--   franchisor_intro_made       -> "Franchisor Intro Made"
--   closed_won                  -> "Closed - Won"
--   disqualified                -> "Disqualified"
--   nurturing_long_term         -> "Nurturing - Long Term"

ALTER TABLE leads ADD CONSTRAINT leads_workflow_status_check 
CHECK (workflow_status::text = ANY (ARRAY[
  'new_lead'::character varying,
  'initial_sms_sent'::character varying,
  'sms_engaged_scheduling'::character varying,
  'deeper_dive_scheduled'::character varying,
  'needs_manual_followup'::character varying,
  'qualified_post_deeper_dive'::character varying,
  'franchises_presented'::character varying,
  'funding_intro_made'::character varying,
  'franchisor_intro_made'::character varying,
  'closed_won'::character varying,
  'disqualified'::character varying,
  'nurturing_long_term'::character varying
]::text[]));

-- Add comment for documentation
COMMENT ON COLUMN leads.workflow_status IS 'Lead workflow status matching GHL "Lead Nurturing" pipeline stages. Values: new_lead, initial_sms_sent, sms_engaged_scheduling, deeper_dive_scheduled, needs_manual_followup, qualified_post_deeper_dive, franchises_presented, funding_intro_made, franchisor_intro_made, closed_won, disqualified, nurturing_long_term';
