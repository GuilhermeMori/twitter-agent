-- Rollback Script: Revert assistants and communication_styles refactoring
-- Description: This script reverts all database changes made in Tasks 1, 2, and 3 of the
--              assistants-communication-styles-refactor spec. It restores the database to
--              its original state before the refactoring.
-- Date: 2026-04-25
-- Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6
--
-- Changes to Revert:
-- - Task 3: Rename communication_style_id back to persona_id in campaigns table
-- - Task 2: Rename communication_styles table back to personas
-- - Task 1: Drop assistants table
--
-- IMPORTANT: All operations are executed in a single transaction. If any operation fails,
--            the entire rollback will be automatically rolled back.

BEGIN;

-- ============================================================================
-- STEP 1: Revert Task 3 - Update campaigns table references
-- ============================================================================

-- Rename column from communication_style_id back to persona_id
ALTER TABLE campaigns RENAME COLUMN communication_style_id TO persona_id;

-- Drop the new foreign key constraint
ALTER TABLE campaigns DROP CONSTRAINT IF EXISTS campaigns_communication_style_id_fkey;

-- Add back the original foreign key constraint
-- Note: We reference communication_styles here because we haven't renamed it yet
ALTER TABLE campaigns ADD CONSTRAINT campaigns_persona_id_fkey 
    FOREIGN KEY (persona_id) 
    REFERENCES communication_styles(id) 
    ON DELETE RESTRICT;

-- Rename index back to original name
ALTER INDEX IF EXISTS idx_campaigns_communication_style_id RENAME TO idx_campaigns_persona_id;

-- Update column comment back to original
COMMENT ON COLUMN campaigns.persona_id IS 'UUID of the persona used for generating comments in this campaign';

-- ============================================================================
-- STEP 2: Revert Task 2 - Rename communication_styles back to personas
-- ============================================================================

-- Rename all indexes back to original names
ALTER INDEX IF EXISTS idx_communication_styles_is_default RENAME TO idx_personas_is_default;
ALTER INDEX IF EXISTS idx_communication_styles_language RENAME TO idx_personas_language;
ALTER INDEX IF EXISTS idx_communication_styles_created_at RENAME TO idx_personas_created_at;
ALTER INDEX IF EXISTS idx_communication_styles_name RENAME TO idx_personas_name;
ALTER INDEX IF EXISTS idx_communication_styles_unique_default RENAME TO idx_personas_unique_default;

-- Rename table back to personas
ALTER TABLE communication_styles RENAME TO personas;

-- Update table comment back to original
COMMENT ON TABLE personas IS 'AI personas for generating tweet comments';

-- Update column comments back to original
COMMENT ON COLUMN personas.name IS 'Display name of the persona (e.g., "Cadu Copy")';
COMMENT ON COLUMN personas.title IS 'Job title or role of the persona (e.g., "Social Media Copywriter")';
COMMENT ON COLUMN personas.description IS 'Detailed description of the persona role and identity';
COMMENT ON COLUMN personas.tone_of_voice IS 'Instructions on how the persona communicates';
COMMENT ON COLUMN personas.principles IS 'JSON array of principles the persona follows';
COMMENT ON COLUMN personas.vocabulary_allowed IS 'JSON array of words/phrases the persona should use';
COMMENT ON COLUMN personas.vocabulary_prohibited IS 'JSON array of words/phrases the persona should avoid';
COMMENT ON COLUMN personas.formatting_rules IS 'JSON array of formatting rules (e.g., "No emojis", "Max 280 chars")';
COMMENT ON COLUMN personas.language IS 'Language code for comments (en, pt, es, etc.)';
COMMENT ON COLUMN personas.system_prompt IS 'Complete prompt for the LLM to generate comments';
COMMENT ON COLUMN personas.is_default IS 'Whether this is the default persona for new campaigns';

-- ============================================================================
-- STEP 3: Revert Task 1 - Drop assistants table
-- ============================================================================

-- Drop the assistants table and all its dependencies
DROP TABLE IF EXISTS assistants CASCADE;

-- Note: CASCADE will automatically drop:
-- - All indexes on the assistants table (idx_assistants_role, idx_assistants_name, idx_assistants_unique_role)
-- - All comments on the table and columns
-- - Any foreign key constraints referencing this table (if any)

-- ============================================================================
-- VERIFICATION QUERIES (commented out - uncomment to verify rollback)
-- ============================================================================

-- Verify assistants table no longer exists
-- SELECT EXISTS (
--     SELECT FROM information_schema.tables 
--     WHERE table_schema = 'public' 
--     AND table_name = 'assistants'
-- ) AS assistants_table_exists;

-- Verify personas table exists
-- SELECT EXISTS (
--     SELECT FROM information_schema.tables 
--     WHERE table_schema = 'public' 
--     AND table_name = 'personas'
-- ) AS personas_table_exists;

-- Verify communication_styles table no longer exists
-- SELECT EXISTS (
--     SELECT FROM information_schema.tables 
--     WHERE table_schema = 'public' 
--     AND table_name = 'communication_styles'
-- ) AS communication_styles_table_exists;

-- Verify campaigns.persona_id column exists
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'campaigns' 
-- AND column_name = 'persona_id';

-- Verify campaigns.communication_style_id column no longer exists
-- SELECT column_name, data_type 
-- FROM information_schema.columns 
-- WHERE table_name = 'campaigns' 
-- AND column_name = 'communication_style_id';

-- Verify foreign key constraint is correct
-- SELECT
--     tc.constraint_name,
--     tc.table_name,
--     kcu.column_name,
--     ccu.table_name AS foreign_table_name,
--     ccu.column_name AS foreign_column_name
-- FROM information_schema.table_constraints AS tc
-- JOIN information_schema.key_column_usage AS kcu
--     ON tc.constraint_name = kcu.constraint_name
--     AND tc.table_schema = kcu.table_schema
-- JOIN information_schema.constraint_column_usage AS ccu
--     ON ccu.constraint_name = tc.constraint_name
--     AND ccu.table_schema = tc.table_schema
-- WHERE tc.constraint_type = 'FOREIGN KEY'
--     AND tc.table_name = 'campaigns'
--     AND kcu.column_name = 'persona_id';

COMMIT;

-- ============================================================================
-- ROLLBACK COMPLETE
-- ============================================================================
-- The database has been restored to its state before the refactoring:
-- ✓ assistants table has been dropped
-- ✓ communication_styles table has been renamed back to personas
-- ✓ campaigns.communication_style_id has been renamed back to persona_id
-- ✓ All indexes and constraints have been restored to their original names
-- ✓ All comments have been restored to their original text
--
-- If you need to re-apply the refactoring, run the migration scripts in order:
-- 1. create_assistants_table.sql
-- 2. rename_personas_to_communication_styles.sql
-- 3. update_campaigns_communication_style_references.sql
-- ============================================================================
