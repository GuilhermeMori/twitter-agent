-- Migration: Create configurations table
-- Description: Stores encrypted user credentials for API tokens and SMTP

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_email VARCHAR(255) NOT NULL,
    apify_token_encrypted TEXT NOT NULL,
    openai_token_encrypted TEXT NOT NULL,
    smtp_password_encrypted TEXT NOT NULL,
    twitter_auth_token_encrypted TEXT,
    twitter_ct0_encrypted TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookup (single-user MVP, prepared for multi-user)
CREATE INDEX IF NOT EXISTS idx_configurations_user_email ON configurations(user_email);

-- Trigger to auto-update updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_configurations_updated_at
    BEFORE UPDATE ON configurations
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();
