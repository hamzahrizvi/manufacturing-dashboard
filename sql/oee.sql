-- oee.sql
-- Overall Equipment Effectiveness per machine per day.
--   OEE = Availability x Performance x Quality
--
--   Availability = running time / planned production time
--   Performance  = (ideal cycle time * total units) / running time
--   Quality      = good units / total units
--
-- One sensor row == one minute, so minute counts map directly to time.

DROP VIEW IF EXISTS v_oee_daily;

CREATE VIEW v_oee_daily AS
WITH base AS (
    SELECT
        machine_id,
        substr(timestamp, 1, 10)                         AS day,
        SUM(CASE WHEN status = 'RUNNING' THEN 1 END)     AS running_min,
        SUM(planned)                                     AS planned_min,
        SUM(units_produced)                              AS total_units,
        SUM(good_units)                                  AS good_units,
        -- ideal cycle time is constant per machine
        MAX(ideal_cycle_time_sec)                        AS ideal_cycle
    FROM sensor_data
    GROUP BY machine_id, day
)
SELECT
    machine_id,
    day,
    running_min,
    planned_min,
    total_units,
    good_units,
    -- availability
    ROUND(1.0 * running_min / NULLIF(planned_min, 0), 4)           AS availability,
    -- performance  (ideal seconds of work / actual running seconds)
    ROUND((ideal_cycle * total_units) / NULLIF(running_min * 60.0, 0), 4)
                                                                   AS performance,
    -- quality
    ROUND(1.0 * good_units / NULLIF(total_units, 0), 4)            AS quality,
    -- OEE
    ROUND(
        (1.0 * running_min / NULLIF(planned_min, 0)) *
        ((ideal_cycle * total_units) / NULLIF(running_min * 60.0, 0)) *
        (1.0 * good_units / NULLIF(total_units, 0)), 4)            AS oee
FROM base
ORDER BY machine_id, day;
