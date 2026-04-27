-- Migration: Add persona_id to campaigns table
-- Description: Adds persona_id column to campaigns table to link campaigns with personas
-- Date: 2026-04-21

-- Add persona_id column to campaigns table
ALTER TABLE campaigns 
ADD COLUMN IF NOT EXISTS persona_id UUID REFERENCES personas(id) ON DELETE SET NULL;

-- Create index for better performance
CREATE INDEX IF NOT EXISTS idx_campaigns_persona_id ON campaigns(persona_id);

-- Add comment for documentation
COMMENT ON COLUMN campaigns.persona_id IS 'UUID of the persona used for generating comments in this campaign';