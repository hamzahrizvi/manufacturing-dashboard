"""
Central configuration for the manufacturing monitoring project.

Keeping all tunable parameters in one place makes the simulation
reproducible and the analytics logic easy to audit.
"""

# --- Simulation window --------------------------------------------------
SIM_DAYS = 7                 # how many days of data to generate
SAMPLE_INTERVAL_MIN = 1      # one sensor record per machine per minute
RANDOM_SEED = 42             # reproducible output

# --- Production line ----------------------------------------------------
MACHINES = ["CNC-01", "CNC-02", "PRESS-01"]

# Planned production schedule (a machine is only *expected* to run inside
# these hours; time outside is not counted against availability).
SHIFT_START_HOUR = 6         # 06:00
SHIFT_END_HOUR = 22          # 22:00  (two 8h shifts)

# Ideal cycle time = seconds to produce one good unit at full speed.
# Used for the Performance component of OEE.
IDEAL_CYCLE_TIME_SEC = {
    "CNC-01": 4.0,
    "CNC-02": 4.0,
    "PRESS-01": 2.0,
}

# --- Sensor nominal operating points (mean, std) ------------------------
# Values are per-machine so the dashboard shows variety.
SENSOR_PROFILE = {
    "CNC-01":   {"temperature": (62, 3),  "pressure": (5.2, 0.3),
                 "motor_current": (14, 1.2), "flow_rate": (48, 4),
                 "energy": (7.5, 0.6)},
    "CNC-02":   {"temperature": (64, 3),  "pressure": (5.0, 0.3),
                 "motor_current": (15, 1.2), "flow_rate": (46, 4),
                 "energy": (7.8, 0.6)},
    "PRESS-01": {"temperature": (58, 4),  "pressure": (8.1, 0.5),
                 "motor_current": (22, 1.8), "flow_rate": (60, 5),
                 "energy": (11.2, 0.9)},
}

# --- Process spec limits (used for alerts + quality) --------------------
# If a reading crosses these, the unit produced that minute is flagged
# out-of-spec and an alert is raised.
SPEC_LIMITS = {
    "temperature":   {"low": 45, "high": 78},
    "pressure":      {"low": 4.0, "high": 9.5},
    "motor_current": {"low": 8,  "high": 28},
    "flow_rate":     {"low": 30, "high": 72},
    "energy":        {"low": 5,  "high": 14},
}

# --- Fault injection ----------------------------------------------------
# Probability (per machine per minute) of starting an unplanned downtime.
DOWNTIME_PROB = 0.0018
DOWNTIME_MIN_LEN = 5         # minutes
DOWNTIME_MAX_LEN = 45        # minutes

# Probability of entering a "drift" period where a sensor slowly goes
# out of spec (simulates a developing fault -> useful for SPC/alerts).
DRIFT_PROB = 0.0012
DRIFT_MIN_LEN = 20
DRIFT_MAX_LEN = 90

# Baseline defect rate while healthy; multiplied up during drift.
BASE_DEFECT_RATE = 0.012
DRIFT_DEFECT_RATE = 0.09

# --- Paths --------------------------------------------------------------
DB_PATH = "data/factory.db"
RAW_CSV = "data/sensor_data.csv"
EXPORT_DIR = "exports"
