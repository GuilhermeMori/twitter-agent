-- Verification Script: Check communication_styles migration
-- Description: Verifies that the personas table was successfully renamed to communication_styles
-- Usage: Run this after executing rename_personas_to_communication_styles.sql

-- Check 1: Verify communication_styles table exists
SELECT 
    'communication_styles table exists' AS check_name,
    CASE 
        WHEN EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'communication_styles'
        ) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status;

-- Check 2: Verify personas table no longer exists
SELECT 
    'personas table removed' AS check_name,
    CASE 
        WHEN NOT EXISTS (
            SELECT 1 FROM information_schema.tables 
            WHERE table_name = 'personas'
        ) THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status;

-- Check 3: Verify all indexes were renamed
SELECT 
    'all indexes renamed' AS check_name,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE tablename = 'communication_styles'
            AND indexname LIKE 'idx_communication_styles_%'
        ) = 5 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status;

-- Check 4: Verify no old indexes remain
SELECT 
    'no old indexes remain' AS check_name,
    CASE 
        WHEN (
            SELECT COUNT(*) 
            FROM pg_indexes 
            WHERE indexname LIKE 'idx_personas_%'
        ) = 0 THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status;

-- Check 5: Verify data was preserved
SELECT 
    'data preserved' AS check_name,
    CASE 
        WHEN (SELECT COUNT(*) FROM communication_styles) > 0 
        THEN '✅ PASS (' || (SELECT COUNT(*) FROM communication_styles) || ' records)'
        ELSE '❌ FAIL (no records found)'
    END AS status;

-- Check 6: Verify table comment was updated
SELECT 
    'table comment updated' AS check_name,
    CASE 
        WHEN obj_description('communication_styles'::regclass) LIKE '%Communication styles%'
        THEN '✅ PASS'
        ELSE '❌ FAIL'
    END AS status;

-- Display all indexes for communication_styles table
SELECT 
    '--- List of indexes ---' AS info,
    '' AS details
UNION ALL
SELECT 
    indexname AS info,
    indexdef AS details
FROM pg_indexes 
WHERE tablename = 'communication_styles'
ORDER BY indexname;

-- Display sample data from communication_styles
SELECT 
    '--- Sample data ---' AS info,
    '' AS details
UNION ALL
SELECT 
    'Record ' || ROW_NUMBER() OVER (ORDER BY created_at) AS info,
    name || ' (' || language || ')' AS details
FROM communication_styles
LIMIT 5;

-- Display table structure
SELECT 
    '--- Table structure ---' AS info,
    '' AS details
UNION ALL
SELECT 
    column_name AS info,
    data_type || COALESCE(' (' || character_maximum_length || ')', '') AS details
FROM information_schema.columns
WHERE table_name = 'communication_styles'
ORDER BY ordinal_position;
