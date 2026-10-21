---
type: method
domain: cross-cutting
topic: timestep
aliases: [viz-renewable, plot-solar-wind, visualize-timestep-output]
tags: [powerworld, analysis, visualization, matplotlib, solar, wind, renewables, pandas]
---

# Method: Writing code to visualize renewable output

## Abstract

How to write matplotlib code that visualizes the solar/wind CSVs produced by the timestep simulation. Covers loading the 8-row metadata + hourly data structure, parsing timestamps, and the four key plot patterns: fleet total solar+wind stacked over time, per-ISO or per-State totals, capacity factor curves, and peak/trough hour identification. This is step 5 (final) of this reading sequence.

## Connections

- **Up:** [Home](../index.md) · [timestep-simulation](../concepts/timestep-simulation.md)
- **Across:** prev in flow: [how-to-analyze-results](how-to-analyze-results.md) · [pww-data](../concepts/pww-data.md) · start: [esapp-overview](esapp-overview.md)

## Content

**Step 5 (final) of this reading sequence.** ← prev: [how-to-analyze-results](how-to-analyze-results.md).

This page teaches you to write visualization code for the CSVs that come out of the timestep simulation. The data format is described fully in [how-to-analyze-results](how-to-analyze-results.md); this page focuses on the plotting patterns.

## 1. Load the CSV

The first 8 rows are metadata, everything below is hourly MW data.

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

raw = pd.read_csv("Historical_2025_solar.csv")

# Split metadata from time series
meta = raw.iloc[:8]          # rows: ISO / PV-Wind / Types / Gen Max MW /
                             #        State / Utility / Latitude / Longitude
data = raw.iloc[8:].copy()

# Parse timestamp and cast generation columns to float
data["DateTimeUTCExcelFormat"] = pd.to_datetime(data["DateTimeUTCExcelFormat"])
data = data.set_index("DateTimeUTCExcelFormat")
data = data.astype(float)
```

`meta.columns` gives the generator names (same order as `data.columns`). Pull any
metadata row by its position:

```python
iso_row    = meta.iloc[0]   # ISO assignment per generator
type_row   = meta.iloc[1]   # SUN / WND
maxmw_row  = meta.iloc[3].astype(float)  # Gen Max MW
state_row  = meta.iloc[4]
```

## 2. Fleet total — solar + wind stacked

Load both CSVs and sum across all generator columns for each:

```python
raw_s = pd.read_csv("Historical_2025_solar.csv")
raw_w = pd.read_csv("Historical_2025_wind.csv")

def load_series(raw):
    d = raw.iloc[8:].copy()
    d["DateTimeUTCExcelFormat"] = pd.to_datetime(d["DateTimeUTCExcelFormat"])
    d = d.set_index("DateTimeUTCExcelFormat").astype(float)
    return d.sum(axis=1)   # fleet total MW

solar_total = load_series(raw_s)
wind_total  = load_series(raw_w)

fig, ax = plt.subplots(figsize=(14, 4))
ax.stackplot(solar_total.index, solar_total, wind_total,
             labels=["Solar", "Wind"], colors=["#f4a261", "#457b9d"], alpha=0.85)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylabel("Generation (MW)")
ax.set_title("Fleet Solar + Wind — 2025")
ax.legend(loc="upper left")
plt.tight_layout()
```

## 3. Per-ISO or per-State totals

Group generator columns by a metadata row value, then sum within each group:

```python
def group_by_meta(data, meta_row):
    """Sum generator columns by the value in meta_row (e.g. ISO or State)."""
    groups = {}
    for gen_col in data.columns:
        key = meta_row[gen_col]
        groups.setdefault(key, []).append(gen_col)
    return {k: data[cols].sum(axis=1) for k, cols in groups.items()}

iso_totals = group_by_meta(data, iso_row)    # dict: ISO → hourly MW Series

fig, ax = plt.subplots(figsize=(14, 4))
for iso, series in iso_totals.items():
    ax.plot(series.index, series, label=iso, linewidth=0.8)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylabel("Solar MW")
ax.set_title("Solar by ISO — 2025")
ax.legend(fontsize=7)
plt.tight_layout()
```

Replace `iso_row` with `state_row` to group by state instead.

## 4. Capacity factor

Divide hourly MW by the `Gen Max MW` metadata row (row index 3):

```python
cf = data.div(maxmw_row, axis=1)   # per-generator capacity factor (0–1)
fleet_cf = cf.mean(axis=1)         # fleet-average capacity factor

fig, ax = plt.subplots(figsize=(14, 3))
ax.plot(fleet_cf.index, fleet_cf, linewidth=0.7, color="#2a9d8f")
ax.set_ylim(0, 1)
ax.set_ylabel("Capacity Factor")
ax.set_title("Fleet Solar Capacity Factor — 2025")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
plt.tight_layout()
```

## 5. Peak and trough hours

Useful for extreme-scenario screening:

```python
fleet_mw = data.sum(axis=1)

peak_hour  = fleet_mw.idxmax()
trough_hour = fleet_mw[fleet_mw > 0].idxmin()   # exclude zero (nighttime)

print(f"Peak:   {peak_hour}  →  {fleet_mw[peak_hour]:.0f} MW")
print(f"Trough: {trough_hour}  →  {fleet_mw[trough_hour]:.0f} MW")

# Mark on the fleet total plot
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(fleet_mw.index, fleet_mw, linewidth=0.7, color="#457b9d")
ax.axvline(peak_hour,   color="red",   linestyle="--", label=f"Peak {peak_hour:%Y-%m-%d %H:%M}")
ax.axvline(trough_hour, color="orange",linestyle="--", label=f"Trough {trough_hour:%Y-%m-%d %H:%M}")
ax.legend()
plt.tight_layout()
```

## Trail complete

[esapp-overview](esapp-overview.md) → [timestep-simulation-setup](timestep-simulation-setup.md) → [pww-data](../concepts/pww-data.md) →
[how-to-analyze-results](how-to-analyze-results.md) → **visualize-renewable-output** ✅
