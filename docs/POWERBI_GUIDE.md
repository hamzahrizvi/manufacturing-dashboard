# Building the Power BI Report

The Python pipeline exports clean CSV feeds to `exports/`. This guide turns them
into an interactive Power BI report. No SQLite ODBC driver needed — Power BI
reads the CSVs directly.

## 1. Load the data

`Home → Get Data → Text/CSV` and import each file from `exports/`:

- `sensor_data.csv` — raw readings (the fact table)
- `oee_daily.csv` — OEE per machine per day
- `downtime_summary.csv` — downtime per machine
- `downtime_events.csv` — individual stoppages
- `cycle_time.csv` — hourly cycle time
- `spc_temperature.csv` — SPC series with control limits
- `alerts.csv` — spec + SPC alerts

Set data types: `timestamp` / `day` / `hour` → Date/Time, numeric columns →
Decimal or Whole Number.

## 2. Data model

Create a **Date** table and a **Machine** table, then relate the fact tables to
them (single-direction, one-to-many):

```
Date[Date]        1 --- *  sensor_data[timestamp]
Date[Date]        1 --- *  oee_daily[day]
Machine[machine]  1 --- *  oee_daily[machine_id]
Machine[machine]  1 --- *  downtime_summary[machine_id]
Machine[machine]  1 --- *  sensor_data[machine_id]
```

Quick Date table (New Table):

```DAX
Date =
ADDCOLUMNS(
    CALENDAR ( MIN(sensor_data[timestamp]), MAX(sensor_data[timestamp]) ),
    "Day", FORMAT([Date], "MMM DD"),
    "Weekday", FORMAT([Date], "ddd")
)
```

## 3. Core DAX measures

```DAX
Avg OEE          = AVERAGE ( oee_daily[oee] )
Avg Availability = AVERAGE ( oee_daily[availability] )
Avg Performance  = AVERAGE ( oee_daily[performance] )
Avg Quality      = AVERAGE ( oee_daily[quality] )

Total Units      = SUM ( oee_daily[total_units] )
Total Downtime (h) = DIVIDE ( SUM ( downtime_summary[total_downtime_min] ), 60 )
Open Alerts      = COUNTROWS ( alerts )

OEE % = FORMAT ( [Avg OEE], "0.0%" )
```

## 4. Report visuals

| # | Visual | Fields |
|---|---|---|
| 1 | **KPI cards** (row across top) | `Avg OEE`, `Avg Availability`, `Total Downtime (h)`, `Total Units` |
| 2 | **Line chart – OEE trend** | Axis `day`, Values `oee`, Legend `machine_id`; add a constant line at 0.85 |
| 3 | **Clustered column – OEE components** | Axis `machine_id`, Values `Avg Availability` / `Avg Performance` / `Avg Quality` |
| 4 | **Pareto** | Bar of `total_downtime_min` by machine + a line for cumulative % |
| 5 | **SPC chart** | Line chart from `spc_temperature`: `temperature`, `ucl`, `lcl`, `center_line` on the y-axis, `timestamp` on the x-axis |
| 6 | **Alerts table** | `alerts` fields; conditional-format `severity` (HIGH = red) |

Add **slicers** for `machine_id` and `day` so every visual cross-filters.

## 5. SPC chart tip

Power BI has no native control chart. The `ucl`, `lcl` and `center_line`
columns are already computed in the SQL view, so plotting them as extra lines on
a standard line chart produces a correct-looking SPC chart. To highlight
violations, add `out_of_control` as a second value or filter the alerts table to
`type = "SPC_OUT_OF_CONTROL"`.

## 6. Save

Save as `dashboard.pbix` in this folder and export a screenshot to
`docs/dashboard.png` (or keep the Python-rendered one). Publish to Power BI
Service if you want a shareable link for your CV.
