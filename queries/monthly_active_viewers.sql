-- ==============================================================================
-- Metric 1: Monthly Active Viewers (MAV) & Session Frequency
-- Definition:
--   Calculates the number of unique viewers who engaged in at least one viewing
--   session per calendar month, along with total session volume and average
--   session watch duration (in minutes).
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewer_activity
-- ==============================================================================

SELECT
    strftime('%Y-%m', session_timestamp) AS activity_month,
    COUNT(DISTINCT viewer_id) AS active_viewers,
    COUNT(*) AS total_sessions,
    ROUND(AVG(watch_duration_mins), 2) AS avg_watch_duration_mins,
    ROUND(SUM(watch_duration_mins), 2) AS total_watch_duration_mins
FROM
    viewer_activity
WHERE
    session_timestamp IS NOT NULL
GROUP BY
    strftime('%Y-%m', session_timestamp)
ORDER BY
    activity_month ASC;
