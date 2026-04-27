-- Migration: Update campaigns table to reference communication_styles
-- Description: Renames persona_id column to communication_style_id and updates foreign key
--              constraint to reference communication_styles table with ON DELETE RESTRICT.
--              This prevents deletion of communication styles that are in use by campaigns.
-- Date: 2026-04-25
-- Task: 3. Database: Atualizar referências em campaigns
-- Requirements: 3.1, 3.2, 3.3, 3.4, 16.1, 16.2

BEGIN;

-- Rename column from persona_id to communication_style_id
ALTER TABLE campaigns RENAME COLUMN persona_id TO communication_style_id;

-- Drop old foreign key constraint (if exists)
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_persona_id_fkey;

-- Add new foreign key constraint with ON DELETE RESTRICT
-- This prevents deletion of communication styles that are in use by campaigns
ALTER TABLE campaigns ADD CONSTRAINT campaigns_communication_style_id_fkey 
    FOREIGN KEY (communication_style_id) 
    REFERENCES communication_styles(id) 
    ON DELETE RESTRICT;

-- Rename index to match new column name
ALTER INDEX IF EXISTS idx_campaigns_persona_id RENAME TO idx_campaigns_communication_style_id;

-- Update column comment to reflect new naming
COMMENT ON COLUMN campaigns.communication_style_id IS 'UUID of the communication style used for generating comments in this campaign. References communication_styles(id) with ON DELETE RESTRICT to prevent deletion of styles in use.';

COMMIT;
