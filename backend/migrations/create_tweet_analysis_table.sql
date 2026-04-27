-- Migration: Create tweet_analysis table
-- Description: Creates the tweet_analysis table for storing AI analysis of tweets with 5 scoring criteria
-- Date: 2026-04-21

-- Create tweet_analysis table
CREATE TABLE IF NOT EXISTS tweet_analysis (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    tweet_id VARCHAR(255) NOT NULL,
    lead_relevance_score INTEGER NOT NULL CHECK (lead_relevance_score BETWEEN 0 AND 10),
    tone_of_voice_score INTEGER NOT NULL CHECK (tone_of_voice_score BETWEEN 0 AND 10),
    insight_strength_score INTEGER NOT NULL CHECK (insight_strength_score BETWEEN 0 AND 10),
    engagement_potential_score INTEGER NOT NULL CHECK (engagement_potential_score BETWEEN 0 AND 10),
    brand_safety_score INTEGER NOT NULL CHECK (brand_safety_score BETWEEN 0 AND 10),
    average_score DECIMAL(3,1) NOT NULL CHECK (average_score BETWEEN 0.0 AND 10.0),
    verdict VARCHAR(20) NOT NULL CHECK (verdict IN ('APPROVED', 'REJECTED')),
    notes TEXT,
    is_top_3 BOOLEAN NOT NULL DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_campaign_id ON tweet_analysis(campaign_id);
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_tweet_id ON tweet_analysis(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_average_score ON tweet_analysis(average_score DESC);
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_is_top_3 ON tweet_analysis(is_top_3);
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_verdict ON tweet_analysis(verdict);

-- Composite index for fetching top tweets by campaign
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_campaign_score 
ON tweet_analysis(campaign_id, average_score DESC);

-- Composite index for fetching top 3 tweets by campaign
CREATE INDEX IF NOT EXISTS idx_tweet_analysis_campaign_top3 
ON tweet_analysis(campaign_id, is_top_3) WHERE is_top_3 = TRUE;

-- Unique constraint to prevent duplicate analysis for same tweet in same campaign
CREATE UNIQUE INDEX IF NOT EXISTS idx_tweet_analysis_unique_campaign_tweet 
ON tweet_analysis(campaign_id, tweet_id);

-- Add comments for documentation
COMMENT ON TABLE tweet_analysis IS 'AI analysis results for tweets with 5 scoring criteria and verdict';
COMMENT ON COLUMN tweet_analysis.campaign_id IS 'Reference to the campaign that collected this tweet';
COMMENT ON COLUMN tweet_analysis.tweet_id IS 'Twitter tweet ID (string format)';
COMMENT ON COLUMN tweet_analysis.lead_relevance_score IS 'Score 0-10: Is the author a relevant decision-maker?';
COMMENT ON COLUMN tweet_analysis.tone_of_voice_score IS 'Score 0-10: Is the tone professional and consultative?';
COMMENT ON COLUMN tweet_analysis.insight_strength_score IS 'Score 0-10: Does the tweet provide valuable insights?';
COMMENT ON COLUMN tweet_analysis.engagement_potential_score IS 'Score 0-10: Does it invite meaningful conversation?';
COMMENT ON COLUMN tweet_analysis.brand_safety_score IS 'Score 0-10: Is it safe for brand engagement?';
COMMENT ON COLUMN tweet_analysis.average_score IS 'Average of all 5 scores (calculated)';
COMMENT ON COLUMN tweet_analysis.verdict IS 'APPROVED (avg >= 8.0) or REJECTED (avg < 8.0)';
COMMENT ON COLUMN tweet_analysis.notes IS 'AI-generated explanatory notes about the analysis';
COMMENT ON COLUMN tweet_analysis.is_top_3 IS 'Whether this tweet is in the top 3 for the campaign';