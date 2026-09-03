-- ==============================================================================
-- Relational Join 1: INNER JOIN (Viewers & Subscription Events)
-- Definition:
--   Returns only records where a viewer_id exists in BOTH viewers and
--   subscription_events. Excludes inactive viewers with no payments and orphan
--   events with no master viewer record.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewers (v) INNER JOIN subscription_events (e)
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
INNER JOIN
    subscription_events e ON v.viewer_id = e.viewer_id
ORDER BY
    v.viewer_id ASC,
    e.event_date ASC;
