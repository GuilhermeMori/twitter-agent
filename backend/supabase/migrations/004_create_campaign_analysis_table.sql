-- Migration: Create campaign_analysis table
-- Description: Stores OpenAI analysis results per campaign

CREATE TABLE IF NOT EXISTS campaign_analysis (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    analysis_text TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Index for fast lookup by campaign
CREATE INDEX IF NOT EXISTS idx_campaign_analysis_campaign_id ON campaign_analysis(campaign_id);
