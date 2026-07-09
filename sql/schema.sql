-- schema.sql
-- Raw sensor + production fact table, one row per machine per minute.

DROP TABLE IF EXISTS sensor_data;

CREATE TABLE sensor_data (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp            TEXT    NOT NULL,   -- 'YYYY-MM-DD HH:MM:SS'
    machine_id           TEXT    NOT NULL,
    status               TEXT    NOT NULL,   -- RUNNING / IDLE / DOWN
    temperature          REAL,
    pressure             REAL,
    motor_current        REAL,
    flow_rate            REAL,
    energy               REAL,
    units_produced       INTEGER,
    good_units           INTEGER,
    defective_units      INTEGER,
    planned              INTEGER,            -- 1 if inside planned hours
    ideal_cycle_time_sec REAL
);

CREATE INDEX idx_machine_time ON sensor_data (machine_id, timestamp);
CREATE INDEX idx_status       ON sensor_data (status);
