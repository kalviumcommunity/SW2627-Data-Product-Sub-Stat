-- ==============================================================================
-- Relational Join 4: 3-Way Multi-Table Analysis
-- Definition:
--   Connects viewers -> viewer_activity -> content_catalog.
--   Enables multi-table relational analysis linking viewer profile attributes
--   with session viewing duration, completion state, and content genre metadata.
-- Database: SQLite (Compatible with standard SQL)
-- Source Tables: viewers (v) INNER JOIN viewer_activity (a) LEFT JOIN content_catalog (c)
-- ==============================================================================

SELECT
    v.viewer_id,
    v.plan_tier,
    v.country,
    v.device_type,
    a.session_timestamp,
    a.watch_duration_mins,
    a.completion_status,
    COALESCE(c.title, 'Direct Stream / Unlisted') AS content_title,
    COALESCE(c.genre, 'General') AS content_genre,
    c.total_duration_mins AS catalog_duration_mins
FROM
    viewers v
INNER JOIN
    viewer_activity a ON v.viewer_id = a.viewer_id
LEFT JOIN
    content_catalog c ON a.content_id = c.content_id
ORDER BY
    v.viewer_id ASC,
    a.session_timestamp ASC;
