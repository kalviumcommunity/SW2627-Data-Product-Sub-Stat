-- ==============================================================================
-- HAVING Clause Demonstration: Post-Aggregation Group Filtering
-- Definition:
--   Explicitly contrasts WHERE and HAVING:
--   1. WHERE filters individual transaction rows (payment_status = 'Completed')
--      BEFORE aggregation.
--   2. GROUP BY aggregates data at the viewer level.
--   3. HAVING filters out aggregated groups where total completed spend < $30.00
--      or transaction count < 2 AFTER aggregation.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: subscription_events (e) LEFT JOIN viewers (v)
-- ==============================================================================

SELECT
    e.viewer_id,
    COALESCE(v.plan_tier, 'Unknown') AS plan_tier,
    COUNT(e.event_id) AS completed_transactions,
    ROUND(SUM(e.payment_amount), 2) AS total_spent,
    ROUND(AVG(e.payment_amount), 2) AS avg_transaction_amount
FROM
    subscription_events e
LEFT JOIN
    viewers v ON e.viewer_id = v.viewer_id
WHERE
    e.payment_status = 'Completed'     -- Row-level filter BEFORE aggregation
GROUP BY
    e.viewer_id,
    COALESCE(v.plan_tier, 'Unknown')
HAVING
    COUNT(e.event_id) >= 2             -- Group-level filter AFTER aggregation
    AND SUM(e.payment_amount) >= 30.00
ORDER BY
    total_spent DESC;
