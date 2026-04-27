-- Verification Script: Verify rollback of assistants and communication_styles refactoring
-- Description: Verifies that the rollback script successfully restored the database to its
--              original state before the refactoring.
-- Date: 2026-04-25
-- Usage: Run this after executing rollback_assistants_communication_styles_refactor.sql

-- ============================================================================
-- CHECK 1: Verify assistants table no longer exists
-- ============================================================================
SELECT 
    'assistants table removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = 'assistants'
        ) THEN '✅ PASS: assistants table has been dropped'
        ELSE '❌ FAIL: assistants table still exists'
    END AS status;

-- ============================================================================
-- CHECK 2: Verify personas table exists
-- ============================================================================
SELECT 
    'personas table restored' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = 'personas'
        ) THEN '✅ PASS: personas table exists'
        ELSE '❌ FAIL: personas table does not exist'
    END AS status;

-- ============================================================================
-- CHECK 3: Verify communication_styles table no longer exists
-- ============================================================================
SELECT 
    'communication_styles table removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_schema = 'public'
            AND table_name = 'communication_styles'
        ) THEN '✅ PASS: communication_styles table has been renamed back to personas'
        ELSE '❌ FAIL: communication_styles table still exists'
    END AS status;

-- ============================================================================
-- CHECK 4: Verify campaigns.persona_id column exists
-- ============================================================================
SELECT 
    'campaigns.persona_id column restored' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'campaigns' 
            AND column_name = 'persona_id'
        ) THEN '✅ PASS: persona_id column exists in campaigns table'
        ELSE '❌ FAIL: persona_id column does not exist in campaigns table'
    END AS status;

-- ============================================================================
-- CHECK 5: Verify campaigns.communication_style_id column no longer exists
-- ============================================================================
SELECT 
    'campaigns.communication_style_id column removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM information_schema.columns 
            WHERE table_schema = 'public'
            AND table_name = 'campaigns' 
            AND column_name = 'communication_style_id'
        ) THEN '✅ PASS: communication_style_id column has been renamed back to persona_id'
        ELSE '❌ FAIL: communication_style_id column still exists'
    END AS status;

-- ============================================================================
-- CHECK 6: Verify foreign key constraint is correct
-- ============================================================================
SELECT 
    'campaigns foreign key constraint restored' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
                ON tc.constraint_name = kcu.constraint_name
                AND tc.table_schema = kcu.table_schema
            JOIN information_schema.constraint_column_usage ccu
                ON ccu.constraint_name = tc.constraint_name
                AND ccu.table_schema = tc.table_schema
            WHERE tc.constraint_type = 'FOREIGN KEY'
                AND tc.table_schema = 'public'
                AND tc.table_name = 'campaigns'
                AND kcu.column_name = 'persona_id'
                AND ccu.table_name = 'personas'
                AND ccu.column_name = 'id'
        ) THEN '✅ PASS: campaigns.persona_id references personas(id)'
        ELSE '❌ FAIL: foreign key constraint is incorrect'
    END AS status;

-- ============================================================================
-- CHECK 7: Verify old foreign key constraint no longer exists
-- ============================================================================
SELECT 
    'old foreign key constraint removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1
            FROM information_schema.table_constraints
            WHERE table_schema = 'public'
            AND table_name = 'campaigns'
            AND constraint_name = 'campaigns_communication_style_id_fkey'
        ) THEN '✅ PASS: old constraint campaigns_communication_style_id_fkey removed'
        ELSE '❌ FAIL: old constraint campaigns_communication_style_id_fkey still exists'
    END AS status;

-- ============================================================================
-- CHECK 8: Verify personas indexes are restored
-- ============================================================================
SELECT 
    'personas indexes restored' AS check_name,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename = 'personas'
            AND indexname LIKE 'idx_personas_%'
        ) >= 5 THEN '✅ PASS: personas indexes restored (' || 
            (SELECT COUNT(*) FROM pg_indexes WHERE tablename = 'personas') || ' total)'
        ELSE '❌ FAIL: personas indexes not fully restored'
    END AS status;

-- ============================================================================
-- CHECK 9: Verify communication_styles indexes no longer exist
-- ============================================================================
SELECT 
    'communication_styles indexes removed' AS check_name,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND indexname LIKE 'idx_communication_styles_%'
        ) = 0 THEN '✅ PASS: all communication_styles indexes removed'
        ELSE '❌ FAIL: some communication_styles indexes still exist'
    END AS status;

-- ============================================================================
-- CHECK 10: Verify campaigns index is restored
-- ============================================================================
SELECT 
    'campaigns.persona_id index restored' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename = 'campaigns'
            AND indexname = 'idx_campaigns_persona_id'
        ) THEN '✅ PASS: idx_campaigns_persona_id index exists'
        ELSE '❌ FAIL: idx_campaigns_persona_id index does not exist'
    END AS status;

-- ============================================================================
-- CHECK 11: Verify old campaigns index no longer exists
-- ============================================================================
SELECT 
    'old campaigns index removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM pg_indexes 
            WHERE schemaname = 'public'
            AND tablename = 'campaigns'
            AND indexname = 'idx_campaigns_communication_style_id'
        ) THEN '✅ PASS: idx_campaigns_communication_style_id index removed'
        ELSE '❌ FAIL: idx_campaigns_communication_style_id index still exists'
    END AS status;

-- ============================================================================
-- CHECK 12: Verify data integrity - personas table has data
-- ============================================================================
SELECT 
    'personas data preserved' AS check_name,
    CASE 
        WHEN (SELECT COUNT(*) FROM personas) > 0 
        THEN '✅ PASS: personas table has ' || (SELECT COUNT(*) FROM personas) || ' records'
        ELSE '❌ FAIL: personas table has no records'
    END AS status;

-- ============================================================================
-- CHECK 13: Verify data integrity - campaigns references are valid
-- ============================================================================
SELECT 
    'campaigns references valid' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 
            FROM campaigns c
            LEFT JOIN personas p ON c.persona_id = p.id
            WHERE c.persona_id IS NOT NULL 
            AND p.id IS NULL
        ) THEN '✅ PASS: all campaigns.persona_id references are valid'
        ELSE '❌ FAIL: some campaigns have invalid persona_id references'
    END AS status;

-- ============================================================================
-- SUMMARY: Display current state
-- ============================================================================

SELECT '============================================================================' AS separator;
SELECT 'ROLLBACK VERIFICATION SUMMARY' AS title;
SELECT '============================================================================' AS separator;

-- Display personas table info
SELECT 
    '--- Personas Table ---' AS info,
    '' AS details
UNION ALL
SELECT 
    'Total records' AS info,
    CAST(COUNT(*) AS TEXT) AS details
FROM personas
UNION ALL
SELECT 
    'Sample record' AS info,
    name || ' (' || language || ')' AS details
FROM personas
LIMIT 1;

-- Display personas indexes
SELECT 
    '--- Personas Indexes ---' AS info,
    '' AS details
UNION ALL
SELECT 
    indexname AS info,
    'on ' || tablename AS details
FROM pg_indexes 
WHERE schemaname = 'public'
AND tablename = 'personas'
ORDER BY indexname;

-- Display campaigns foreign key
SELECT 
    '--- Campaigns Foreign Keys ---' AS info,
    '' AS details
UNION ALL
SELECT 
    tc.constraint_name AS info,
    kcu.column_name || ' -> ' || ccu.table_name || '(' || ccu.column_name || ')' AS details
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
    AND tc.table_schema = kcu.table_schema
JOIN information_schema.constraint_column_usage ccu
    ON ccu.constraint_name = tc.constraint_name
    AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY'
    AND tc.table_schema = 'public'
    AND tc.table_name = 'campaigns'
    AND kcu.column_name = 'persona_id';

SELECT '============================================================================' AS separator;
SELECT 'END OF VERIFICATION' AS title;
SELECT '============================================================================' AS separator;

