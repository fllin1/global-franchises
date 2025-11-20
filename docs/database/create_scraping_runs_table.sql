-- Create scraping_runs table
CREATE TABLE IF NOT EXISTS scraping_runs (
    id BIGSERIAL PRIMARY KEY,
    run_date TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    total_franchises INT DEFAULT 0,
    successful_uploads INT DEFAULT 0,
    failed_uploads INT DEFAULT 0,
    status TEXT CHECK (status IN ('completed', 'failed', 'partial', 'in_progress')),
    storage_path_prefix TEXT, -- e.g., 'raw-franchise-html/2025-01-20/'
    metadata JSONB, -- Additional run metadata
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Add index on run_date
CREATE INDEX IF NOT EXISTS idx_scraping_runs_date ON scraping_runs(run_date);

