"""
load_database.py
----------------
Builds the SQLite database:
  1. creates the schema
  2. bulk-loads the generated CSV
  3. applies every analytical view in /sql

Run after generate_data.py.
"""

import glob
import os
import sqlite3

import pandas as pd

import config as cfg

# Views must be created after the table exists. schema.sql first,
# the rest in any order.
VIEW_FILES = ["oee.sql", "downtime.sql", "cycle_time.sql", "spc.sql"]


def _run_sql_file(conn, path):
    with open(path) as f:
        conn.executescript(f.read())
    print(f"  applied {os.path.basename(path)}")


def build():
    os.makedirs("data", exist_ok=True)
    if os.path.exists(cfg.DB_PATH):
        os.remove(cfg.DB_PATH)

    conn = sqlite3.connect(cfg.DB_PATH)

    print("Creating schema...")
    _run_sql_file(conn, "sql/schema.sql")

    print(f"Loading {cfg.RAW_CSV}...")
    df = pd.read_csv(cfg.RAW_CSV)
    df.to_sql("sensor_data", conn, if_exists="append", index=False)
    print(f"  loaded {len(df):,} rows")

    print("Building views...")
    for vf in VIEW_FILES:
        _run_sql_file(conn, os.path.join("sql", vf))

    conn.commit()

    # quick sanity print
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*), COUNT(DISTINCT machine_id) FROM sensor_data")
    n, m = cur.fetchone()
    print(f"\nDatabase ready: {cfg.DB_PATH}  ({n:,} rows, {m} machines)")

    conn.close()


if __name__ == "__main__":
    build()
