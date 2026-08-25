-- ==============================================================================
-- ORDER BY & LIMIT Demonstration: Ranking and Top-N Selection
-- Definition:
--   Ranks viewers by total watch duration and completed sessions in
--   descending order, retrieving the Top-5 most engaged viewers.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewer_activity
-- ==============================================================================

SELECT
    viewer_id,
    COUNT(*) AS total_sessions,
    SUM(CASE WHEN completion_status = 'Completed' THEN 1 ELSE 0 END) AS completed_sessions,
    ROUND(SUM(watch_duration_mins), 2) AS total_watch_mins,
    ROUND(AVG(watch_duration_mins), 2) AS avg_watch_mins,
    ROUND(MAX(watch_duration_mins), 2) AS max_session_watch_mins
FROM
    viewer_activity
GROUP BY
    viewer_id
ORDER BY
    total_watch_mins DESC,
    completed_sessions DESC
LIMIT 5;
