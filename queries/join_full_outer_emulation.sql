-- ==============================================================================
-- Relational Join 3: FULL OUTER JOIN Emulation (SQLite Compatible)
-- Definition:
--   Emulates FULL OUTER JOIN in SQLite by combining a LEFT JOIN (all viewers +
--   matching events) with unmatched right records (subscription_events without
--   a master viewer) using UNION ALL.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewers (v) FULL OUTER JOIN subscription_events (e)
-- ==============================================================================

-- Part 1: All viewers with matched events or NULL events (Left Join)
SELECT
    v.viewer_id AS viewer_master_id,
    v.plan_tier,
    v.country,
    e.event_id,
    e.viewer_id AS event_viewer_id,
    e.payment_amount,
    e.payment_status,
    CASE
        WHEN e.event_id IS NULL THEN 'Master Viewer Only (No Events)'
        ELSE 'Matched'
    END AS match_category
FROM
    viewers v
LEFT JOIN
    subscription_events e ON v.viewer_id = e.viewer_id

UNION ALL

-- Part 2: Orphan subscription events with no matching viewer in master table
SELECT
    NULL AS viewer_master_id,
    NULL AS plan_tier,
    NULL AS country,
    e.event_id,
    e.viewer_id AS event_viewer_id,
    e.payment_amount,
    e.payment_status,
    'Orphan Event Only (No Viewer Record)' AS match_category
FROM
    subscription_events e
WHERE
    e.viewer_id NOT IN (SELECT viewer_id FROM viewers WHERE viewer_id IS NOT NULL);
