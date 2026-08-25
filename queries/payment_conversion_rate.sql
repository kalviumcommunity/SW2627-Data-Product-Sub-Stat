-- ==============================================================================
-- Metric 3: Payment Conversion & Transaction Success Rate
-- Definition:
--   Measures transaction success rate as the percentage of billing attempts
--   resulting in 'Completed' status versus total billing attempts, broken down
--   by subscription plan tier.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: subscription_events (e) LEFT JOIN viewers (v)
-- ==============================================================================

SELECT
    COALESCE(v.plan_tier, 'Unknown') AS plan_tier,
    COUNT(e.event_id) AS total_payment_attempts,
    SUM(CASE WHEN e.payment_status = 'Completed' THEN 1 ELSE 0 END) AS successful_transactions,
    SUM(CASE WHEN e.payment_status != 'Completed' THEN 1 ELSE 0 END) AS failed_transactions,
    ROUND(
        100.0 * SUM(CASE WHEN e.payment_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(e.event_id),
        2
    ) AS success_rate_pct,
    ROUND(
        SUM(CASE WHEN e.payment_status = 'Completed' THEN e.payment_amount ELSE 0 END),
        2
    ) AS realized_revenue
FROM
    subscription_events e
LEFT JOIN
    viewers v ON e.viewer_id = v.viewer_id
GROUP BY
    COALESCE(v.plan_tier, 'Unknown')
ORDER BY
    success_rate_pct DESC;
