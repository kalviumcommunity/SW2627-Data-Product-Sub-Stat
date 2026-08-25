-- ==============================================================================
-- Relational Join 2: LEFT JOIN (Viewers & Subscription Events)
-- Definition:
--   Preserves ALL records from the left table (viewers). If a viewer has no
--   associated subscription_events, event columns are populated with NULL.
--   Enables detection of registered subscribers with zero billing activity.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewers (v) LEFT JOIN subscription_events (e)
-- ==============================================================================

SELECT
    v.viewer_id,
    v.plan_tier,
    v.country,
    v.device_type,
    e.event_id,
    e.event_date,
    e.payment_amount,
    e.payment_status
FROM
    viewers v
LEFT JOIN
    subscription_events e ON v.viewer_id = e.viewer_id
ORDER BY
    v.viewer_id ASC,
    e.event_date ASC;
