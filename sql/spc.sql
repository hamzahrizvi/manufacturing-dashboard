-- spc.sql
-- Statistical Process Control limits for temperature, per machine.
-- Uses the classic mean +/- 3-sigma control band computed over all
-- healthy RUNNING readings. Power BI (or Python) plots the raw series
-- against UCL / CL / LCL to make an SPC chart.

DROP VIEW IF EXISTS v_spc_temperature;

CREATE VIEW v_spc_temperature AS
WITH stats AS (
    SELECT
        machine_id,
        AVG(temperature)                                        AS cl,
        -- SQLite has no STDDEV: compute population sigma manually
        SQRT(AVG(temperature * temperature) - AVG(temperature) * AVG(temperature))
                                                                AS sigma
    FROM sensor_data
    WHERE status = 'RUNNING'
    GROUP BY machine_id
)
SELECT
    d.machine_id,
    d.timestamp,
    d.temperature,
    ROUND(s.cl, 3)                       AS center_line,
    ROUND(s.cl + 3 * s.sigma, 3)         AS ucl,
    ROUND(s.cl - 3 * s.sigma, 3)         AS lcl,
    CASE
        WHEN d.temperature > s.cl + 3 * s.sigma
          OR d.temperature < s.cl - 3 * s.sigma
        THEN 1 ELSE 0
    END                                  AS out_of_control
FROM sensor_data d
JOIN stats s ON s.machine_id = d.machine_id
WHERE d.status = 'RUNNING'
ORDER BY d.machine_id, d.timestamp;
