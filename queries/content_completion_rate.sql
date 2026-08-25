-- ==============================================================================
-- Metric 5: Content Completion Rate & Engagement by Genre
-- Definition:
--   Computes viewing session completion percentage, total viewing events,
--   and average watch time per content genre.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewer_activity (a) JOIN content_catalog (c)
-- ==============================================================================

SELECT
    COALESCE(c.genre, 'Direct Stream / General') AS genre,
    COUNT(DISTINCT a.content_id) AS distinct_titles,
    COUNT(a.session_timestamp) AS total_viewing_sessions,
    SUM(CASE WHEN a.completion_status = 'Completed' THEN 1 ELSE 0 END) AS completed_sessions,
    ROUND(
        100.0 * SUM(CASE WHEN a.completion_status = 'Completed' THEN 1 ELSE 0 END) / COUNT(a.session_timestamp),
        2
    ) AS completion_rate_pct,
    ROUND(AVG(a.watch_duration_mins), 2) AS avg_duration_mins
FROM
    viewer_activity a
LEFT JOIN
    content_catalog c ON a.content_id = c.content_id
GROUP BY
    COALESCE(c.genre, 'Direct Stream / General')
ORDER BY
    completion_rate_pct DESC,
    total_viewing_sessions DESC;
