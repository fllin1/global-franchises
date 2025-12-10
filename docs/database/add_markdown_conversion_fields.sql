-- Add markdown conversion tracking fields to scraping_runs table

ALTER TABLE scraping_runs
ADD COLUMN IF NOT EXISTS markdown_conversions_completed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS markdown_conversions_failed INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS markdown_conversions_skipped INTEGER DEFAULT 0,
ADD COLUMN IF NOT EXISTS markdown_conversion_status TEXT DEFAULT NULL,
ADD COLUMN IF NOT EXISTS markdown_conversion_started_at TIMESTAMP WITH TIME ZONE DEFAULT NULL,
ADD COLUMN IF NOT EXISTS markdown_conversion_completed_at TIMESTAMP WITH TIME ZONE DEFAULT NULL;

-- Add index on markdown_conversion_status for filtering
CREATE INDEX IF NOT EXISTS idx_scraping_runs_markdown_conversion_status 
ON scraping_runs(markdown_conversion_status);

-- Add comment to document the status values
COMMENT ON COLUMN scraping_runs.markdown_conversion_status IS 
'Status of markdown conversion: pending, in_progress, completed, failed, partial';






















