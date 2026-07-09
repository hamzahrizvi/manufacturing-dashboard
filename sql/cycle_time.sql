-- cycle_time.sql
-- Actual cycle time = running seconds / units produced, per machine per hour.
-- Compared against the machine's ideal cycle time to expose slow running.

DROP VIEW IF EXISTS v_cycle_time_hourly;

CREATE VIEW v_cycle_time_hourly AS
WITH hourly AS (
    SELECT
        machine_id,
        substr(timestamp, 1, 13) || ':00'          AS hour,   -- 'YYYY-MM-DD HH:00'
        SUM(CASE WHEN status = 'RUNNING' THEN 1 END) AS running_min,
        SUM(units_produced)                          AS units,
        MAX(ideal_cycle_time_sec)                    AS ideal_cycle
    FROM sensor_data
    GROUP BY machine_id, hour
)
SELECT
    machine_id,
    hour,
    units,
    ideal_cycle                                            AS ideal_cycle_sec,
    ROUND(running_min * 60.0 / NULLIF(units, 0), 2)        AS actual_cycle_sec,
    ROUND(
        (running_min * 60.0 / NULLIF(units, 0)) - ideal_cycle, 2)
                                                           AS cycle_loss_sec
FROM hourly
WHERE units > 0
ORDER BY machine_id, hour;
