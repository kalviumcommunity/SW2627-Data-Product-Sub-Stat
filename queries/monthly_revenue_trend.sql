-- ==============================================================================
-- Metric 4: Monthly Revenue Trend & Transaction Volume
-- Definition:
--   Aggregates realized recurring revenue, total successful transactions, and
--   average transaction ticket size grouped chronologically by month (YYYY-MM).
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: subscription_events
-- ==============================================================================

SELECT
    strftime('%Y-%m', event_date) AS revenue_month,
    COUNT(event_id) AS total_transactions,
    ROUND(SUM(payment_amount), 2) AS monthly_revenue,
    ROUND(AVG(payment_amount), 2) AS avg_transaction_amount,
    ROUND(MIN(payment_amount), 2) AS min_transaction_amount,
    ROUND(MAX(payment_amount), 2) AS max_transaction_amount
FROM
    subscription_events
WHERE
    payment_status = 'Completed'
    AND event_date IS NOT NULL
GROUP BY
    strftime('%Y-%m', event_date)
ORDER BY
    revenue_month ASC;
