-- Create GHL Conversations table
CREATE TABLE IF NOT EXISTS ghl_conversations (
    id VARCHAR(255) PRIMARY KEY,
    location_id VARCHAR(255) NOT NULL,
    contact_id VARCHAR(255) NOT NULL,
    full_name TEXT,
    company_name TEXT,
    email VARCHAR(255),
    phone VARCHAR(50),
    date_added TIMESTAMPTZ,
    date_updated TIMESTAMPTZ,
    last_message_date TIMESTAMPTZ,
    last_message_type VARCHAR(100),
    last_message_direction VARCHAR(50),
    unread_count INTEGER DEFAULT 0,
    tags TEXT,
    type VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create GHL Messages table
CREATE TABLE IF NOT EXISTS ghl_messages (
    id VARCHAR(255) PRIMARY KEY,
    conversation_id VARCHAR(255) NOT NULL,
    contact_id VARCHAR(255) NOT NULL,
    location_id VARCHAR(255) NOT NULL,
    date_added TIMESTAMPTZ,
    message_type VARCHAR(100),
    source VARCHAR(100),
    type VARCHAR(100),
    direction VARCHAR(50),
    subject TEXT,
    body_length INTEGER DEFAULT 0,
    body_clean_length INTEGER DEFAULT 0,
    body_clean TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    FOREIGN KEY (conversation_id) REFERENCES ghl_conversations(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_ghl_conversations_contact_id ON ghl_conversations(contact_id);
CREATE INDEX IF NOT EXISTS idx_ghl_conversations_location_id ON ghl_conversations(location_id);
CREATE INDEX IF NOT EXISTS idx_ghl_conversations_date_added ON ghl_conversations(date_added);
CREATE INDEX IF NOT EXISTS idx_ghl_conversations_last_message_date ON ghl_conversations(last_message_date);
CREATE INDEX IF NOT EXISTS idx_ghl_conversations_email ON ghl_conversations(email);

CREATE INDEX IF NOT EXISTS idx_ghl_messages_conversation_id ON ghl_messages(conversation_id);
CREATE INDEX IF NOT EXISTS idx_ghl_messages_contact_id ON ghl_messages(contact_id);
CREATE INDEX IF NOT EXISTS idx_ghl_messages_location_id ON ghl_messages(location_id);
CREATE INDEX IF NOT EXISTS idx_ghl_messages_date_added ON ghl_messages(date_added);
CREATE INDEX IF NOT EXISTS idx_ghl_messages_message_type ON ghl_messages(message_type);

-- Create updated_at trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create triggers for updated_at
CREATE TRIGGER update_ghl_conversations_updated_at 
    BEFORE UPDATE ON ghl_conversations 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_ghl_messages_updated_at 
    BEFORE UPDATE ON ghl_messages 
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Add comments for documentation
COMMENT ON TABLE ghl_conversations IS 'GHL (Go High Level) conversations data exported from API';
COMMENT ON TABLE ghl_messages IS 'GHL (Go High Level) messages data exported from API';

COMMENT ON COLUMN ghl_conversations.id IS 'Unique conversation ID from GHL';
COMMENT ON COLUMN ghl_conversations.location_id IS 'GHL location ID';
COMMENT ON COLUMN ghl_conversations.contact_id IS 'GHL contact ID';
COMMENT ON COLUMN ghl_conversations.full_name IS 'Contact full name';
COMMENT ON COLUMN ghl_conversations.company_name IS 'Company name';
COMMENT ON COLUMN ghl_conversations.email IS 'Contact email address';
COMMENT ON COLUMN ghl_conversations.phone IS 'Contact phone number';
COMMENT ON COLUMN ghl_conversations.date_added IS 'When conversation was added (ISO 8601)';
COMMENT ON COLUMN ghl_conversations.date_updated IS 'When conversation was last updated (ISO 8601)';
COMMENT ON COLUMN ghl_conversations.last_message_date IS 'Date of last message (ISO 8601)';
COMMENT ON COLUMN ghl_conversations.last_message_type IS 'Type of last message (e.g., TYPE_EMAIL, TYPE_CAMPAIGN_EMAIL)';
COMMENT ON COLUMN ghl_conversations.last_message_direction IS 'Direction of last message (inbound/outbound)';
COMMENT ON COLUMN ghl_conversations.unread_count IS 'Number of unread messages';
COMMENT ON COLUMN ghl_conversations.tags IS 'Comma-separated list of tags';
COMMENT ON COLUMN ghl_conversations.type IS 'Conversation type (e.g., TYPE_PHONE)';

COMMENT ON COLUMN ghl_messages.id IS 'Unique message ID from GHL';
COMMENT ON COLUMN ghl_messages.conversation_id IS 'Foreign key to ghl_conversations.id';
COMMENT ON COLUMN ghl_messages.contact_id IS 'GHL contact ID';
COMMENT ON COLUMN ghl_messages.location_id IS 'GHL location ID';
COMMENT ON COLUMN ghl_messages.date_added IS 'When message was added (ISO 8601)';
COMMENT ON COLUMN ghl_messages.message_type IS 'Type of message (e.g., TYPE_EMAIL)';
COMMENT ON COLUMN ghl_messages.source IS 'Source of message (e.g., bulk_actions)';
COMMENT ON COLUMN ghl_messages.type IS 'Message type';
COMMENT ON COLUMN ghl_messages.direction IS 'Message direction';
COMMENT ON COLUMN ghl_messages.subject IS 'Email subject (if applicable)';
COMMENT ON COLUMN ghl_messages.body_length IS 'Length of raw message body';
COMMENT ON COLUMN ghl_messages.body_clean_length IS 'Length of cleaned message body';
COMMENT ON COLUMN ghl_messages.body_clean IS 'Cleaned message body content (HTML removed for emails)';
