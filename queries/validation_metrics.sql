-- ==============================================================================
-- Module 5: Cross-Engine Metric Validation Queries
-- Definition:
--   Calculates platform business metrics in pure SQL to be independently
--   compared and validated against Python Pandas calculations.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: subscription_events, viewers, viewer_activity
-- ==============================================================================

-- 1. Total Completed Revenue & Transaction Volume
SELECT
    'total_completed_revenue' AS metric_key,
    ROUND(SUM(payment_amount), 4) AS metric_value
FROM
    subscription_events
WHERE
    payment_status = 'Completed';

-- 2. Average Transaction Amount (Completed)
SELECT
    'avg_completed_transaction_amount' AS metric_key,
    ROUND(AVG(payment_amount), 4) AS metric_value
FROM
    subscription_events
WHERE
    payment_status = 'Completed';

-- 3. Overall Payment Success Rate Percentage
SELECT
    'payment_success_rate_pct' AS metric_key,
    ROUND(100.0 * SUM(CASE WHEN payment_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(*), 4) AS metric_value
FROM
    subscription_events;

-- 4. Total Platform Watch Duration Minutes
SELECT
    'total_watch_duration_mins' AS metric_key,
    ROUND(SUM(watch_duration_mins), 4) AS metric_value
FROM
    viewer_activity
WHERE
    watch_duration_mins IS NOT NULL;

-- 5. Distinct Active Viewers with Activity
SELECT
    'active_viewers_count' AS metric_key,
    CAST(COUNT(DISTINCT viewer_id) AS REAL) AS metric_value
FROM
    viewer_activity;
