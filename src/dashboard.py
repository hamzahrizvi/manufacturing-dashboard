"""
dashboard.py
------------
Generates a single-page PNG dashboard from the SQLite views so the repo
has an immediate visual (and a screenshot for the README) without needing
Power BI installed. Mirrors the visuals you would build in Power BI:

  - OEE trend by machine
  - OEE component breakdown (Availability / Performance / Quality)
  - Downtime Pareto
  - SPC chart (temperature with control limits) for one machine
  - KPI headline cards

Output: docs/dashboard.png
"""

import os
import sqlite3

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

import config as cfg

# --- simple dark dashboard theme ---
plt.rcParams.update({
    "figure.facecolor": "#0f1420",
    "axes.facecolor": "#171d2e",
    "axes.edgecolor": "#2a3350",
    "axes.labelcolor": "#c7d0e0",
    "text.color": "#e6ebf5",
    "xtick.color": "#8b95ad",
    "ytick.color": "#8b95ad",
    "grid.color": "#242c44",
    "font.size": 9,
})
ACCENT = ["#4f9dff", "#28c99a", "#ff8f4f"]


def _card(ax, title, value, sub=""):
    ax.axis("off")
    ax.add_patch(plt.Rectangle((0, 0), 1, 1, transform=ax.transAxes,
                               facecolor="#171d2e", edgecolor="#2a3350",
                               linewidth=1.2))
    ax.text(0.5, 0.66, value, ha="center", va="center", fontsize=22,
            fontweight="bold", color="#4f9dff", transform=ax.transAxes)
    ax.text(0.5, 0.30, title, ha="center", va="center", fontsize=9,
            color="#c7d0e0", transform=ax.transAxes)
    if sub:
        ax.text(0.5, 0.12, sub, ha="center", va="center", fontsize=7.5,
                color="#8b95ad", transform=ax.transAxes)


def build():
    conn = sqlite3.connect(cfg.DB_PATH)
    oee = pd.read_sql("SELECT * FROM v_oee_daily", conn, parse_dates=["day"])
    dt = pd.read_sql("SELECT * FROM v_downtime_summary", conn)
    spc = pd.read_sql("SELECT * FROM v_spc_temperature", conn,
                      parse_dates=["timestamp"])
    alerts = pd.read_sql_query(
        "SELECT COUNT(*) n FROM v_spc_temperature WHERE out_of_control=1", conn)
    conn.close()

    fig = plt.figure(figsize=(15, 9))
    gs = fig.add_gridspec(3, 4, hspace=0.45, wspace=0.3,
                          height_ratios=[0.5, 1, 1])

    fig.suptitle("Digital Process Monitoring Dashboard",
                 fontsize=18, fontweight="bold", x=0.5, y=0.97)
    fig.text(0.5, 0.925, "Simulated production line  |  OEE  ·  Downtime  ·  "
             "Cycle time  ·  SPC  ·  Alerts", ha="center",
             fontsize=10, color="#8b95ad")

    # ---- KPI cards ----
    plant_oee = oee["oee"].mean()
    plant_avail = oee["availability"].mean()
    total_dt = dt["total_downtime_min"].sum()
    total_units = oee["total_units"].sum()

    _card(fig.add_subplot(gs[0, 0]), "PLANT OEE", f"{plant_oee*100:.1f}%")
    _card(fig.add_subplot(gs[0, 1]), "AVAILABILITY", f"{plant_avail*100:.1f}%")
    _card(fig.add_subplot(gs[0, 2]), "DOWNTIME", f"{total_dt/60:.0f} h",
          "across all machines")
    _card(fig.add_subplot(gs[0, 3]), "UNITS PRODUCED", f"{total_units:,.0f}")

    # ---- OEE trend ----
    ax1 = fig.add_subplot(gs[1, :2])
    for i, (mid, g) in enumerate(oee.groupby("machine_id")):
        ax1.plot(g["day"], g["oee"] * 100, marker="o", ms=4,
                 color=ACCENT[i % 3], label=mid, linewidth=1.8)
    ax1.axhline(85, color="#ff5470", ls="--", lw=1, alpha=0.7,
                label="World-class (85%)")
    ax1.set_title("OEE Trend by Machine", loc="left", fontweight="bold")
    ax1.set_ylabel("OEE (%)")
    ax1.legend(fontsize=7, framealpha=0.2, loc="lower left", ncol=2)
    ax1.grid(True, alpha=0.3)
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))

    # ---- OEE component breakdown ----
    ax2 = fig.add_subplot(gs[1, 2:])
    comp = oee.groupby("machine_id")[
        ["availability", "performance", "quality"]].mean() * 100
    x = range(len(comp))
    w = 0.26
    for j, col in enumerate(["availability", "performance", "quality"]):
        ax2.bar([xi + (j - 1) * w for xi in x], comp[col], w,
                label=col.capitalize(), color=ACCENT[j])
    ax2.set_xticks(list(x))
    ax2.set_xticklabels(comp.index, fontsize=8)
    ax2.set_title("OEE Components (avg)", loc="left", fontweight="bold")
    ax2.set_ylabel("%")
    ax2.legend(fontsize=7, framealpha=0.2)
    ax2.grid(True, axis="y", alpha=0.3)

    # ---- Downtime Pareto ----
    ax3 = fig.add_subplot(gs[2, :2])
    dts = dt.sort_values("total_downtime_min", ascending=False)
    ax3.bar(dts["machine_id"], dts["total_downtime_min"], color="#ff8f4f")
    ax3.set_title("Downtime by Machine (Pareto)", loc="left",
                  fontweight="bold")
    ax3.set_ylabel("Downtime (min)")
    cum = dts["total_downtime_min"].cumsum() / dts["total_downtime_min"].sum() * 100
    ax3b = ax3.twinx()
    ax3b.plot(dts["machine_id"], cum, color="#4f9dff", marker="o", ms=5)
    ax3b.set_ylabel("Cumulative %", color="#4f9dff")
    ax3b.set_ylim(0, 105)
    ax3.grid(True, axis="y", alpha=0.3)

    # ---- SPC chart ----
    ax4 = fig.add_subplot(gs[2, 2:])
    mid0 = spc["machine_id"].iloc[0]
    s = spc[spc["machine_id"] == mid0].iloc[::15]  # thin for readability
    ax4.plot(s["timestamp"], s["temperature"], color="#c7d0e0", lw=0.7,
             label="Temperature")
    ax4.plot(s["timestamp"], s["ucl"], color="#ff5470", ls="--", lw=1,
             label="UCL / LCL")
    ax4.plot(s["timestamp"], s["lcl"], color="#ff5470", ls="--", lw=1)
    ax4.plot(s["timestamp"], s["center_line"], color="#28c99a", lw=1,
             label="Center")
    ooc = s[s["out_of_control"] == 1]
    ax4.scatter(ooc["timestamp"], ooc["temperature"], color="#ff5470",
                s=18, zorder=5, label="Out of control")
    ax4.set_title(f"SPC Chart · Temperature · {mid0}", loc="left",
                  fontweight="bold")
    ax4.set_ylabel("°C")
    ax4.legend(fontsize=7, framealpha=0.2, loc="upper right")
    ax4.grid(True, alpha=0.3)
    ax4.xaxis.set_major_formatter(mdates.DateFormatter("%m-%d"))

    os.makedirs("docs", exist_ok=True)
    out = "docs/dashboard.png"
    fig.savefig(out, dpi=120, bbox_inches="tight", facecolor=fig.get_facecolor())
    print(f"Dashboard saved -> {out}")


if __name__ == "__main__":
    build()
