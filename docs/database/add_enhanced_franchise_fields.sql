-- Add enhanced franchise data extraction fields to franchises table
-- This migration adds fields to capture all information patterns from markdown files

-- Commission Structure (JSONB)
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS commission_structure JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.commission_structure IS 
'Commission structure for brokers: single_unit, multi_unit, resales, area_master_developer';

-- Industry Awards (JSONB)
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS industry_awards JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.industry_awards IS 
'Array of industry awards with source, year, and award_name';

-- Documents & Resources (JSONB)
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS documents JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.documents IS 
'Documents and resources: regular, client_focused, recent_emails, magazine_articles';

-- Resales Information
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS resales_available BOOLEAN DEFAULT NULL,
ADD COLUMN IF NOT EXISTS resales_list JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.resales_available IS 'Whether resales are available for this franchise';
COMMENT ON COLUMN franchises.resales_list IS 'List of available resales';

-- Rating
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS rating NUMERIC(3,2) DEFAULT NULL;

COMMENT ON COLUMN franchises.rating IS 'Star rating (1-5) if available';

-- Schedule Call URL
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS schedule_call_url TEXT DEFAULT NULL;

COMMENT ON COLUMN franchises.schedule_call_url IS 'Calendar booking URL for scheduling a call';

-- Market Availability Enhancements
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS hot_regions JSONB DEFAULT NULL,
ADD COLUMN IF NOT EXISTS canadian_referrals BOOLEAN DEFAULT NULL,
ADD COLUMN IF NOT EXISTS international_referrals BOOLEAN DEFAULT NULL;

COMMENT ON COLUMN franchises.hot_regions IS 'Array of hot/desirable markets (state codes or regions)';
COMMENT ON COLUMN franchises.canadian_referrals IS 'Accepts Canadian referrals';
COMMENT ON COLUMN franchises.international_referrals IS 'Accepts international referrals';

-- Franchise Packages (JSONB)
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS franchise_packages JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.franchise_packages IS 
'Array of franchise packages with name, franchise_fee, total_investment_min/max, territories_count, description';

-- Support & Training Details (JSONB)
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS support_training_details JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.support_training_details IS 
'Structured training info: program_description, cost_included, cost_details, lodging_airfare_included, site_selection_assistance, lease_negotiation_assistance, mentor_available, mentoring_length';

-- Market Growth Statistics (JSONB)
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS market_growth_statistics JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.market_growth_statistics IS 
'Market growth data: demographics, market_size, cagr, growth_period, recession_resistance';

-- Financial Details Enhancements
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS sba_registered BOOLEAN DEFAULT NULL,
ADD COLUMN IF NOT EXISTS providing_earnings_guidance_item19 BOOLEAN DEFAULT NULL,
ADD COLUMN IF NOT EXISTS additional_fees TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS financial_assistance_details TEXT DEFAULT NULL;

COMMENT ON COLUMN franchises.sba_registered IS 'Is the franchise registered with the SBA? (Separate from sba_approved)';
COMMENT ON COLUMN franchises.providing_earnings_guidance_item19 IS 'Providing earnings guidance in Item 19 in FDD';
COMMENT ON COLUMN franchises.additional_fees IS 'Additional fees beyond franchise fee and royalties';
COMMENT ON COLUMN franchises.financial_assistance_details IS 'Details about financial assistance available';

-- Ideal Candidate Profile (JSONB) - structured version
ALTER TABLE franchises
ADD COLUMN IF NOT EXISTS ideal_candidate_profile JSONB DEFAULT NULL;

COMMENT ON COLUMN franchises.ideal_candidate_profile IS 
'Structured ideal candidate profile: skills (array), personality_traits (array), role_of_owner (text)';

-- Update recent_territory_checks to support structured format
-- Note: This column already exists as JSONB, but we're ensuring it can handle the new structured format
-- The existing data will remain compatible, new extractions will use structured objects

-- Enhance franchises_data JSONB structure
-- Note: franchises_data already exists, but we're documenting the enhanced structure
-- New fields will be added automatically when data is inserted

-- Add indexes for new boolean fields for filtering
CREATE INDEX IF NOT EXISTS idx_franchises_resales_available ON franchises(resales_available) WHERE resales_available IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_canadian_referrals ON franchises(canadian_referrals) WHERE canadian_referrals IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_international_referrals ON franchises(international_referrals) WHERE international_referrals IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_sba_registered ON franchises(sba_registered) WHERE sba_registered IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_providing_earnings_guidance ON franchises(providing_earnings_guidance_item19) WHERE providing_earnings_guidance_item19 IS NOT NULL;

-- Add GIN indexes for JSONB fields that will be queried
CREATE INDEX IF NOT EXISTS idx_franchises_commission_structure ON franchises USING GIN(commission_structure) WHERE commission_structure IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_industry_awards ON franchises USING GIN(industry_awards) WHERE industry_awards IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_documents ON franchises USING GIN(documents) WHERE documents IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_franchise_packages ON franchises USING GIN(franchise_packages) WHERE franchise_packages IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_franchises_hot_regions ON franchises USING GIN(hot_regions) WHERE hot_regions IS NOT NULL;

-- Add title field to contacts table
ALTER TABLE contacts
ADD COLUMN IF NOT EXISTS title TEXT DEFAULT NULL;

COMMENT ON COLUMN contacts.title IS 'Job title of the contact person';

-- Add index for title field
CREATE INDEX IF NOT EXISTS idx_contacts_title ON contacts(title) WHERE title IS NOT NULL;








