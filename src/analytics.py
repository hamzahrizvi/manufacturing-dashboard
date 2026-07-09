"""
analytics.py
------------
Reads from the SQLite views and produces:
  1. An ALERTS table  - spec breaches + SPC out-of-control points.
  2. Flat CSV exports  - one per view, ready to import into Power BI /
     Excel without needing an ODBC driver for SQLite.

Run after load_database.py.
"""

import os
import sqlite3

import pandas as pd

import config as cfg


def _spec_alerts(conn) -> pd.DataFrame:
    """One alert row per sensor reading that breaches a spec limit."""
    df = pd.read_sql("SELECT * FROM sensor_data WHERE status='RUNNING'", conn)
    alerts = []
    for sensor, lim in cfg.SPEC_LIMITS.items():
        breach = df[(df[sensor] < lim["low"]) | (df[sensor] > lim["high"])]
        for _, r in breach.iterrows():
            alerts.append({
                "timestamp": r["timestamp"],
                "machine_id": r["machine_id"],
                "type": "SPEC_BREACH",
                "sensor": sensor,
                "value": r[sensor],
                "limit_low": lim["low"],
                "limit_high": lim["high"],
                "severity": "HIGH",
            })
    return pd.DataFrame(alerts)


def _spc_alerts(conn) -> pd.DataFrame:
    """Out-of-control points flagged by the SPC view."""
    df = pd.read_sql(
        "SELECT * FROM v_spc_temperature WHERE out_of_control = 1", conn)
    if df.empty:
        return pd.DataFrame()
    return pd.DataFrame({
        "timestamp": df["timestamp"],
        "machine_id": df["machine_id"],
        "type": "SPC_OUT_OF_CONTROL",
        "sensor": "temperature",
        "value": df["temperature"],
        "limit_low": df["lcl"],
        "limit_high": df["ucl"],
        "severity": "MEDIUM",
    })


def build_alerts(conn) -> pd.DataFrame:
    parts = [_spec_alerts(conn), _spc_alerts(conn)]
    parts = [p for p in parts if not p.empty]
    if not parts:
        return pd.DataFrame()
    alerts = pd.concat(parts, ignore_index=True)
    alerts = alerts.sort_values("timestamp").reset_index(drop=True)
    return alerts


def export_for_powerbi(conn):
    """Dump every view + the alerts table to CSV for Power BI / Excel."""
    os.makedirs(cfg.EXPORT_DIR, exist_ok=True)

    exports = {
        "oee_daily":        "SELECT * FROM v_oee_daily",
        "downtime_events":  "SELECT * FROM v_downtime_events",
        "downtime_summary": "SELECT * FROM v_downtime_summary",
        "cycle_time":       "SELECT * FROM v_cycle_time_hourly",
        "spc_temperature":  "SELECT * FROM v_spc_temperature",
        "sensor_data":      "SELECT * FROM sensor_data",
    }
    for name, q in exports.items():
        df = pd.read_sql(q, conn)
        path = os.path.join(cfg.EXPORT_DIR, f"{name}.csv")
        df.to_csv(path, index=False)
        print(f"  exported {name}.csv ({len(df):,} rows)")

    alerts = build_alerts(conn)
    alerts.to_csv(os.path.join(cfg.EXPORT_DIR, "alerts.csv"), index=False)
    print(f"  exported alerts.csv ({len(alerts):,} rows)")
    return alerts


def print_summary(conn):
    oee = pd.read_sql("SELECT * FROM v_oee_daily", conn)
    dt = pd.read_sql("SELECT * FROM v_downtime_summary", conn)

    print("\n================ PLANT SUMMARY ================")
    by_machine = oee.groupby("machine_id")[
        ["availability", "performance", "quality", "oee"]].mean().round(3)
    print("\nAverage OEE components by machine:")
    print(by_machine.to_string())

    print("\nDowntime summary:")
    print(dt.to_string(index=False))
    print("===============================================")


def run():
    conn = sqlite3.connect(cfg.DB_PATH)
    print("Exporting analytical tables for Power BI / Excel...")
    export_for_powerbi(conn)
    print_summary(conn)
    conn.close()


if __name__ == "__main__":
    run()
