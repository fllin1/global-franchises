-- Migration: Add LLM parsing status tracking fields to scraping_runs table
-- Date: 2025-11-24
-- Description: Adds fields to track the status of LLM parsing for markdown files

-- Add llm_parsing_status column
ALTER TABLE scraping_runs 
ADD COLUMN IF NOT EXISTS llm_parsing_status TEXT 
CHECK (llm_parsing_status IN ('pending', 'in_progress', 'completed', 'partial', 'failed', 'no_files'));

-- Add llm_parsing_started_at column
ALTER TABLE scraping_runs 
ADD COLUMN IF NOT EXISTS llm_parsing_started_at TIMESTAMP WITH TIME ZONE;

-- Add llm_parsing_completed_at column
ALTER TABLE scraping_runs 
ADD COLUMN IF NOT EXISTS llm_parsing_completed_at TIMESTAMP WITH TIME ZONE;

-- Set default value for new runs
COMMENT ON COLUMN scraping_runs.llm_parsing_status IS 'Status of LLM parsing: pending, in_progress, completed, partial, failed, no_files';
COMMENT ON COLUMN scraping_runs.llm_parsing_started_at IS 'Timestamp when LLM parsing started';
COMMENT ON COLUMN scraping_runs.llm_parsing_completed_at IS 'Timestamp when LLM parsing completed';



