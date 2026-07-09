"""
run_all.py
----------
Runs the full pipeline end to end:
    generate -> load -> analytics -> dashboard

Usage:
    python run_all.py
"""

import sys
sys.path.insert(0, "src")

import generate_data
import load_database
import analytics
import dashboard


def main():
    print("=" * 55)
    print(" STEP 1/4  Simulating production line data")
    print("=" * 55)
    generate_data.generate()

    print("\n" + "=" * 55)
    print(" STEP 2/4  Building SQLite database + views")
    print("=" * 55)
    load_database.build()

    print("\n" + "=" * 55)
    print(" STEP 3/4  Running analytics + exporting for Power BI")
    print("=" * 55)
    analytics.run()

    print("\n" + "=" * 55)
    print(" STEP 4/4  Rendering dashboard PNG")
    print("=" * 55)
    dashboard.build()

    print("\nDone. See docs/dashboard.png and the exports/ folder.")


if __name__ == "__main__":
    main()
