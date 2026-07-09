"""
generate_data.py
----------------
Simulates a production line of several machines at 1-minute resolution.

For each machine and each minute it produces:
  - sensor readings (temperature, pressure, motor current, flow, energy)
  - a machine status (RUNNING / IDLE / DOWN)
  - units produced that minute, split into good / defective

Realism is created with three layers:
  1. Cyclic base signal + gaussian noise for each sensor.
  2. Random unplanned DOWNTIME blocks (hurts OEE availability).
  3. Random sensor DRIFT periods that push a variable out of spec,
     raising the defect rate (hurts OEE quality and triggers SPC/alerts).

Output: data/sensor_data.csv
"""

import csv
import math
import os
import random
from datetime import datetime, timedelta

import numpy as np

import config as cfg


def _in_shift(ts: datetime) -> bool:
    """True when the timestamp falls inside planned production hours."""
    return cfg.SHIFT_START_HOUR <= ts.hour < cfg.SHIFT_END_HOUR


def _sensor_value(machine: str, sensor: str, minute_of_day: int) -> float:
    """Nominal reading = mean + daily cycle + noise."""
    mean, std = cfg.SENSOR_PROFILE[machine][sensor]
    # gentle daily cycle so trends look natural in the dashboard
    cycle = 0.15 * std * math.sin(2 * math.pi * minute_of_day / 1440)
    return mean + cycle + np.random.normal(0, std)


def generate():
    random.seed(cfg.RANDOM_SEED)
    np.random.seed(cfg.RANDOM_SEED)

    start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    start -= timedelta(days=cfg.SIM_DAYS)
    total_minutes = cfg.SIM_DAYS * 24 * 60

    os.makedirs("data", exist_ok=True)
    rows = []

    for machine in cfg.MACHINES:
        # per-machine fault state
        downtime_left = 0
        drift_left = 0
        drift_sensor = None
        drift_dir = 1

        ideal_cycle = cfg.IDEAL_CYCLE_TIME_SEC[machine]
        ideal_units_per_min = 60.0 / ideal_cycle

        for m in range(total_minutes):
            ts = start + timedelta(minutes=m)
            minute_of_day = ts.hour * 60 + ts.minute

            # ---------- decide status ----------
            if downtime_left > 0:
                status = "DOWN"
                downtime_left -= 1
            elif not _in_shift(ts):
                status = "IDLE"          # outside planned hours
            else:
                # maybe start a new downtime block
                if random.random() < cfg.DOWNTIME_PROB:
                    downtime_left = random.randint(
                        cfg.DOWNTIME_MIN_LEN, cfg.DOWNTIME_MAX_LEN)
                    status = "DOWN"
                    downtime_left -= 1
                else:
                    status = "RUNNING"

            # ---------- maybe start a drift ----------
            if drift_left == 0 and status == "RUNNING":
                if random.random() < cfg.DRIFT_PROB:
                    drift_left = random.randint(
                        cfg.DRIFT_MIN_LEN, cfg.DRIFT_MAX_LEN)
                    drift_sensor = random.choice(
                        ["temperature", "pressure", "motor_current"])
                    drift_dir = random.choice([-1, 1])

            # ---------- sensor readings ----------
            reading = {s: _sensor_value(machine, s, minute_of_day)
                       for s in ["temperature", "pressure",
                                 "motor_current", "flow_rate", "energy"]}

            drift_active = drift_left > 0
            if drift_active:
                # push the drifting sensor progressively out of range
                _, std = cfg.SENSOR_PROFILE[machine][drift_sensor]
                progress = 1 - (drift_left /
                                (cfg.DRIFT_MAX_LEN))  # 0..~1
                reading[drift_sensor] += drift_dir * std * (2 + 4 * progress)
                drift_left -= 1

            # while down/idle, motor + energy fall toward zero
            if status != "RUNNING":
                reading["motor_current"] *= 0.05
                reading["energy"] *= 0.08
                reading["flow_rate"] *= 0.1

            # ---------- production + quality ----------
            if status == "RUNNING":
                # actual speed slightly below ideal, worse during drift
                speed_factor = np.random.uniform(0.82, 0.98)
                if drift_active:
                    speed_factor *= 0.9
                units = max(0, int(round(ideal_units_per_min * speed_factor)))

                defect_rate = (cfg.DRIFT_DEFECT_RATE if drift_active
                               else cfg.BASE_DEFECT_RATE)
                # any hard spec breach this minute worsens quality too
                for s, lim in cfg.SPEC_LIMITS.items():
                    if not (lim["low"] <= reading[s] <= lim["high"]):
                        defect_rate = max(defect_rate, 0.15)
                defective = np.random.binomial(units, min(defect_rate, 1.0))
                good = units - defective
            else:
                units = good = defective = 0

            rows.append({
                "timestamp": ts.strftime("%Y-%m-%d %H:%M:%S"),
                "machine_id": machine,
                "status": status,
                "temperature": round(reading["temperature"], 2),
                "pressure": round(reading["pressure"], 3),
                "motor_current": round(reading["motor_current"], 2),
                "flow_rate": round(reading["flow_rate"], 2),
                "energy": round(reading["energy"], 3),
                "units_produced": units,
                "good_units": good,
                "defective_units": defective,
                "planned": int(_in_shift(ts)),
                "ideal_cycle_time_sec": ideal_cycle,
            })

    # ---------- write CSV ----------
    fieldnames = list(rows[0].keys())
    with open(cfg.RAW_CSV, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Generated {len(rows):,} rows -> {cfg.RAW_CSV}")
    print(f"Machines: {', '.join(cfg.MACHINES)} | "
          f"{cfg.SIM_DAYS} days @ {cfg.SAMPLE_INTERVAL_MIN}-min resolution")


if __name__ == "__main__":
    generate()
