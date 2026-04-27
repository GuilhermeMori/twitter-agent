-- Migration: Create tweet_comments table
-- Description: Creates the tweet_comments table for storing AI-generated comments for tweets
-- Date: 2026-04-21

-- Create tweet_comments table
CREATE TABLE IF NOT EXISTS tweet_comments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    campaign_id UUID NOT NULL REFERENCES campaigns(id) ON DELETE CASCADE,
    tweet_id VARCHAR(255) NOT NULL,
    persona_id UUID NOT NULL REFERENCES personas(id) ON DELETE RESTRICT,
    comment_text TEXT NOT NULL,
    char_count INTEGER NOT NULL CHECK (char_count > 0),
    generation_attempt INTEGER NOT NULL DEFAULT 1 CHECK (generation_attempt BETWEEN 1 AND 3),
    validation_status VARCHAR(20) NOT NULL CHECK (validation_status IN ('valid', 'failed', 'regenerated')),
    validation_errors JSONB DEFAULT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_tweet_comments_campaign_id ON tweet_comments(campaign_id);
CREATE INDEX IF NOT EXISTS idx_tweet_comments_tweet_id ON tweet_comments(tweet_id);
CREATE INDEX IF NOT EXISTS idx_tweet_comments_persona_id ON tweet_comments(persona_id);
CREATE INDEX IF NOT EXISTS idx_tweet_comments_validation_status ON tweet_comments(validation_status);
CREATE INDEX IF NOT EXISTS idx_tweet_comments_created_at ON tweet_comments(created_at DESC);

-- Composite index for fetching comments by campaign and tweet
CREATE INDEX IF NOT EXISTS idx_tweet_comments_campaign_tweet 
ON tweet_comments(campaign_id, tweet_id);

-- Composite index for fetching valid comments by campaign
CREATE INDEX IF NOT EXISTS idx_tweet_comments_campaign_valid 
ON tweet_comments(campaign_id, validation_status) WHERE validation_status = 'valid';

-- Unique constraint to ensure only one valid comment per tweet per campaign
CREATE UNIQUE INDEX IF NOT EXISTS idx_tweet_comments_unique_valid 
ON tweet_comments(campaign_id, tweet_id) 
WHERE validation_status = 'valid';

-- Add comments for documentation
COMMENT ON TABLE tweet_comments IS 'AI-generated comments for tweets using specific personas';
COMMENT ON COLUMN tweet_comments.campaign_id IS 'Reference to the campaign that collected this tweet';
COMMENT ON COLUMN tweet_comments.tweet_id IS 'Twitter tweet ID (string format)';
COMMENT ON COLUMN tweet_comments.persona_id IS 'Reference to the persona used to generate this comment';
COMMENT ON COLUMN tweet_comments.comment_text IS 'The generated comment text (max 280 characters)';
COMMENT ON COLUMN tweet_comments.char_count IS 'Character count of the comment text';
COMMENT ON COLUMN tweet_comments.generation_attempt IS 'Attempt number (1-3) for generating this comment';
COMMENT ON COLUMN tweet_comments.validation_status IS 'Status: valid, failed, or regenerated';
COMMENT ON COLUMN tweet_comments.validation_errors IS 'JSON array of validation error messages if failed';