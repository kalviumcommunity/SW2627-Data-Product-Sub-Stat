-- ==============================================================================
-- WHERE Clause Demonstration: Pre-Aggregation Row Filtering
-- Definition:
--   Filters individual raw row records before any aggregation or grouping.
--   Selects only completed transactions with payment amounts >= $10.00.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: subscription_events
-- ==============================================================================

SELECT
    event_id,
    viewer_id,
    event_date,
    payment_amount,
    payment_status,
    auto_renew
FROM
    subscription_events
WHERE
    payment_status = 'Completed'
    AND payment_amount >= 10.00
ORDER BY
    payment_amount DESC,
    event_date DESC;
