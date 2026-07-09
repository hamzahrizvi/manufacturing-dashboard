-- downtime.sql
-- Identifies discrete downtime EVENTS (not just down minutes) using a
-- gaps-and-islands pattern, then summarises them for a Pareto view.

DROP VIEW IF EXISTS v_downtime_events;
DROP VIEW IF EXISTS v_downtime_summary;

-- Each contiguous run of DOWN minutes = one event.
CREATE VIEW v_downtime_events AS
WITH flagged AS (
    SELECT
        machine_id,
        timestamp,
        status,
        ROW_NUMBER() OVER (PARTITION BY machine_id ORDER BY timestamp)
          - ROW_NUMBER() OVER (PARTITION BY machine_id, status ORDER BY timestamp)
          AS grp
    FROM sensor_data
)
SELECT
    machine_id,
    MIN(timestamp)              AS start_time,
    MAX(timestamp)              AS end_time,
    COUNT(*)                    AS duration_min
FROM flagged
WHERE status = 'DOWN'
GROUP BY machine_id, grp
ORDER BY machine_id, start_time;

-- Roll events up per machine: total lost minutes + number of stoppages.
CREATE VIEW v_downtime_summary AS
SELECT
    machine_id,
    COUNT(*)                    AS stoppages,
    SUM(duration_min)           AS total_downtime_min,
    ROUND(AVG(duration_min), 1) AS avg_stoppage_min,
    MAX(duration_min)           AS longest_stoppage_min
FROM v_downtime_events
GROUP BY machine_id
ORDER BY total_downtime_min DESC;
