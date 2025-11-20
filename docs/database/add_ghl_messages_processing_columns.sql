-- Add processing status columns to ghl_messages table
ALTER TABLE ghl_messages 
ADD COLUMN IF NOT EXISTS processed BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS has_attachment_mention BOOLEAN DEFAULT FALSE,
ADD COLUMN IF NOT EXISTS is_out_of_office BOOLEAN DEFAULT FALSE;

-- Create index on processed column for faster querying of pending messages
CREATE INDEX IF NOT EXISTS idx_ghl_messages_processed ON ghl_messages(processed);

