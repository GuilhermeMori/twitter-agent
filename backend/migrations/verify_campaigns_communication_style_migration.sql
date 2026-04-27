-- Verification Script: Verify campaigns communication_style_id migration
-- Description: Verifies that the campaigns table has been correctly updated to reference
--              communication_styles instead of personas
-- Date: 2026-04-25
-- Task: 3. Database: Atualizar referências em campaigns

-- Check 1: Verify column exists and has correct name
SELECT 
    'Column Check' as test_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'campaigns' 
            AND column_name = 'communication_style_id'
        ) THEN '✓ PASS: communication_style_id column exists'
        ELSE '✗ FAIL: communication_style_id column does not exist'
    END as result;

-- Check 2: Verify old column does not exist
SELECT 
    'Old Column Check' as test_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'campaigns' 
            AND column_name = 'persona_id'
        ) THEN '✓ PASS: persona_id column removed'
        ELSE '✗ FAIL: persona_id column still exists'
    END as result;

-- Check 3: Verify foreign key constraint exists
SELECT 
    'Foreign Key Check' as test_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.table_constraints 
            WHERE table_name = 'campaigns' 
            AND constraint_name = 'campaigns_communication_style_id_fkey'
            AND constraint_type = 'FOREIGN KEY'
        ) THEN '✓ PASS: Foreign key constraint exists'
        ELSE '✗ FAIL: Foreign key constraint does not exist'
    END as result;

-- Check 4: Verify old foreign key constraint does not exist
SELECT 
    'Old Foreign Key Check' as test_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM information_schema.table_constraints 
            WHERE table_name = 'campaigns' 
            AND constraint_name = 'campaigns_persona_id_fkey'
        ) THEN '✓ PASS: Old foreign key constraint removed'
        ELSE '✗ FAIL: Old foreign key constraint still exists'
    END as result;

-- Check 5: Verify foreign key references communication_styles table
SELECT 
    'Foreign Key Target Check' as test_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.referential_constraints rc
            JOIN information_schema.key_column_usage kcu 
                ON rc.constraint_name = kcu.constraint_name
            WHERE rc.constraint_name = 'campaigns_communication_style_id_fkey'
            AND kcu.table_name = 'campaigns'
            AND kcu.column_name = 'communication_style_id'
            AND rc.unique_constraint_schema = current_schema()
        ) THEN '✓ PASS: Foreign key references communication_styles'
        ELSE '✗ FAIL: Foreign key does not reference communication_styles correctly'
    END as result;

-- Check 6: Verify ON DELETE RESTRICT is configured
SELECT 
    'ON DELETE RESTRICT Check' as test_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM information_schema.referential_constraints 
            WHERE constraint_name = 'campaigns_communication_style_id_fkey'
            AND delete_rule = 'RESTRICT'
        ) THEN '✓ PASS: ON DELETE RESTRICT configured'
        ELSE '✗ FAIL: ON DELETE RESTRICT not configured'
    END as result;

-- Check 7: Verify index exists with correct name
SELECT 
    'Index Check' as test_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM pg_indexes 
            WHERE tablename = 'campaigns' 
            AND indexname = 'idx_campaigns_communication_style_id'
        ) THEN '✓ PASS: Index idx_campaigns_communication_style_id exists'
        ELSE '✗ FAIL: Index idx_campaigns_communication_style_id does not exist'
    END as result;

-- Check 8: Verify old index does not exist
SELECT 
    'Old Index Check' as test_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM pg_indexes 
            WHERE tablename = 'campaigns' 
            AND indexname = 'idx_campaigns_persona_id'
        ) THEN '✓ PASS: Old index idx_campaigns_persona_id removed'
        ELSE '✗ FAIL: Old index idx_campaigns_persona_id still exists'
    END as result;

-- Check 9: Verify data integrity - all communication_style_id values reference valid styles
SELECT 
    'Data Integrity Check' as test_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM campaigns c
            WHERE c.communication_style_id IS NOT NULL
            AND NOT EXISTS (
                SELECT 1 
                FROM communication_styles cs 
                WHERE cs.id = c.communication_style_id
            )
        ) THEN '✓ PASS: All communication_style_id values reference valid styles'
        ELSE '✗ FAIL: Some communication_style_id values reference non-existent styles'
    END as result;

-- Summary: Count campaigns by communication style
SELECT 
    'Campaign Count Summary' as info,
    COUNT(*) as total_campaigns,
    COUNT(communication_style_id) as campaigns_with_style,
    COUNT(*) - COUNT(communication_style_id) as campaigns_without_style
FROM campaigns;
