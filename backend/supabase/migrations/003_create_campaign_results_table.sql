-- Migration: Create campaign_results table
-- Description: Stores individual tweets collected per campaign

CREATE TABLE IF NOT EXISTS campaign_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    tweet_id VARCHAR(255) NOT NULL,
    tweet_url TEXT NOT NULL,
    author VARCHAR(255) NOT NULL,
    text TEXT NOT NULL,
    likes INTEGER DEFAULT 0,
    reposts INTEGER DEFAULT 0,
    replies INTEGER DEFAULT 0,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indexes for common queries
CREATE INDEX IF NOT EXISTS idx_campaign_results_campaign_id ON campaign_results(campaign_id);
CREATE INDEX IF NOT EXISTS idx_campaign_results_tweet_id ON campaign_results(tweet_id);
CREATE INDEX IF NOT EXISTS idx_campaign_results_timestamp ON campaign_results(timestamp DESC);

-- Composite index for fetching a campaign's results ordered by timestamp
CREATE INDEX IF NOT EXISTS idx_campaign_results_campaign_timestamp
    ON campaign_results(campaign_id, timestamp DESC);
