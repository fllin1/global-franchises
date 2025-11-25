-- Migration: Add llm_processed_at to franchises table
-- Date: 2025-11-24
-- Description: Tracks when each franchise was processed by LLM extraction pipeline

-- Add column to track LLM processing timestamp
ALTER TABLE franchises 
ADD COLUMN IF NOT EXISTS llm_processed_at TIMESTAMP WITH TIME ZONE;

-- Add index for efficient querying of unprocessed franchises
CREATE INDEX IF NOT EXISTS idx_franchises_llm_processed_at 
ON franchises (llm_processed_at);

-- Add comment explaining the column
COMMENT ON COLUMN franchises.llm_processed_at IS 'Timestamp when franchise was processed by LLM extraction pipeline. NULL means not yet processed.';



