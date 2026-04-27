-- Migration: Rename personas table to communication_styles
-- Description: Renames the personas table to communication_styles to better reflect its purpose
--              of storing tone of voice configurations. Updates all related indexes and comments.
-- Date: 2026-04-25
-- Task: 2. Database: Renomear tabela personas para communication_styles

BEGIN;

-- Rename table
ALTER TABLE personas RENAME TO communication_styles;

-- Rename indexes
ALTER INDEX idx_personas_is_default RENAME TO idx_communication_styles_is_default;
ALTER INDEX idx_personas_language RENAME TO idx_communication_styles_language;
ALTER INDEX idx_personas_created_at RENAME TO idx_communication_styles_created_at;
ALTER INDEX idx_personas_name RENAME TO idx_communication_styles_name;
ALTER INDEX idx_personas_unique_default RENAME TO idx_communication_styles_unique_default;

-- Update table comment
COMMENT ON TABLE communication_styles IS 'Communication styles for generating tweet comments with specific tone and voice';

-- Update column comments to reflect new table name
COMMENT ON COLUMN communication_styles.name IS 'Display name of the communication style (e.g., "Strategic Partner")';
COMMENT ON COLUMN communication_styles.title IS 'Job title or role of the communication style (e.g., "Social Media Copywriter")';
COMMENT ON COLUMN communication_styles.description IS 'Detailed description of the communication style role and identity';
COMMENT ON COLUMN communication_styles.tone_of_voice IS 'Instructions on how the communication style communicates';
COMMENT ON COLUMN communication_styles.principles IS 'JSON array of principles the communication style follows';
COMMENT ON COLUMN communication_styles.vocabulary_allowed IS 'JSON array of words/phrases the communication style should use';
COMMENT ON COLUMN communication_styles.vocabulary_prohibited IS 'JSON array of words/phrases the communication style should avoid';
COMMENT ON COLUMN communication_styles.formatting_rules IS 'JSON array of formatting rules (e.g., "No emojis", "Max 280 chars")';
COMMENT ON COLUMN communication_styles.language IS 'Language code for comments (en, pt, es, etc.)';
COMMENT ON COLUMN communication_styles.system_prompt IS 'Complete prompt for the LLM to generate comments';
COMMENT ON COLUMN communication_styles.is_default IS 'Whether this is the default communication style for new campaigns';

COMMIT;
