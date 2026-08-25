-- ==============================================================================
-- Metric 2: Revenue & ARPU by Subscription Plan Tier
-- Definition:
--   Aggregates total completed revenue, distinct paying subscribers, total
--   transaction count, and Average Revenue Per User (ARPU = Total Revenue /
--   Distinct Paying Subscribers) grouped by subscription plan tier.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewers (v) JOIN subscription_events (e)
-- ==============================================================================

SELECT
    v.plan_tier,
    COUNT(DISTINCT v.viewer_id) AS paying_subscribers,
    COUNT(e.event_id) AS total_transactions,
    ROUND(SUM(e.payment_amount), 2) AS total_revenue,
    ROUND(SUM(e.payment_amount) * 1.0 / COUNT(DISTINCT v.viewer_id), 2) AS arpu,
    ROUND(AVG(e.payment_amount), 2) AS avg_transaction_amount
FROM
    viewers v
INNER JOIN
    subscription_events e ON v.viewer_id = e.viewer_id
WHERE
    e.payment_status = 'Completed'
GROUP BY
    v.plan_tier
ORDER BY
    total_revenue DESC;
