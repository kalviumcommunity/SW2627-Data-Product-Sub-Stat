-- ==============================================================================
-- GROUP BY & Aggregate Functions Demonstration
-- Definition:
--   Groups records across multiple dimensions (plan_tier and country) to
--   compute aggregate statistics: COUNT, SUM, AVG, MIN, and MAX.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewers (v) INNER JOIN subscription_events (e)
-- ==============================================================================

SELECT
    v.plan_tier,
    v.country,
    COUNT(e.event_id) AS total_events,
    COUNT(DISTINCT v.viewer_id) AS distinct_viewers,
    ROUND(SUM(e.payment_amount), 2) AS total_amount,
    ROUND(AVG(e.payment_amount), 2) AS avg_amount,
    ROUND(MIN(e.payment_amount), 2) AS min_amount,
    ROUND(MAX(e.payment_amount), 2) AS max_amount
FROM
    viewers v
INNER JOIN
    subscription_events e ON v.viewer_id = e.viewer_id
GROUP BY
    v.plan_tier,
    v.country
ORDER BY
    total_amount DESC,
    total_events DESC;
