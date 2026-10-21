---
type: method
domain: cross-cutting
topic: timestep
aliases: [analyze-results, results-analysis, post-processing]
tags: [powerworld, analysis, post-processing, csv, solar, wind, renewables]
---

# Method: Writing code to analyze timestep-simulation results

## Abstract

How to write code that reads and analyzes the solar/wind generation CSVs produced by the timestep simulation. Covers the two-CSV-per-run naming convention, the 8-row metadata header layout (ISO, fuel type, PFW model string, max MW, state, utility, lat, lon), why the pipeline's UTC labels run early (PowerWorld's raw export is already UTC), and typical pandas reductions for fleet profiles, capacity factors, and regional totals. This is step 4 of this reading sequence; to plot the results see [visualize-renewable-output](visualize-renewable-output.md).

## Connections

- **Up:** [Home](../index.md) · [timestep-simulation](../concepts/timestep-simulation.md)
- **Across:** step 4 of this reading sequence — prev: [pww-data](../concepts/pww-data.md) · next: [visualize-renewable-output](visualize-renewable-output.md) · start: [esapp-overview](esapp-overview.md) · [timestep-simulation-setup](timestep-simulation-setup.md)

## Content

**Step 4 (final) of this reading sequence.** ← prev: [pww-data](../concepts/pww-data.md) · start over:
[esapp-overview](esapp-overview.md).

You've written the simulation ([timestep-simulation-setup](timestep-simulation-setup.md)) and produced the output
CSVs — this page is how those CSVs are structured and how to write code that reads
and reduces them. The analysis target here is the **solar/wind generation files**,
not a network/contingency report.

### What the simulation produces
Each run writes **two CSVs**: one solar, one wind. Naming:

| Run type | Solar file | Wind file |
|---|---|---|
| Historical (a full year of quarter files) | `Historical_2025_solar.csv` | `Historical_2025_wind.csv` |
| Forecast (a single `.pww`) | `Forecast_..._solar.csv` | `Forecast_..._wind.csv` |

### File layout (8 metadata rows, then hourly data)
`process_results(gen, df)` in the results post-processor's module builds each CSV. The first column is
`DateTimeUTCExcelFormat`; every other column is one renewable generator. The file
opens with **8 metadata header rows**, then the hourly time series. The header rows,
in order, come from these generator fields:

| Header row | Source field |
|---|---|
| `ISO` | `CustomString:2` (assigned by the ISO-assignment step) |
| `PV / Wind` | `GenFuelType` (`SUN` / `WND`) |
| `PV / Wind Types` | `TSPFWModelString` (the PFW model on the unit) |
| `Gen Max MW` | `GenMWMax` |
| `State` | `ZoneName` |
| `Utility` | `AreaName` |
| `Latitude` | `Latitude` |
| `Longitude` | `Longitude` |

Below the header rows, each data row is one UTC hour and each cell is that
generator's MW for that hour. The conversion has already happened by this point —
this file is post-conversion. Its labels are marked UTC but run early, so read
*Timestamps* below before joining this CSV to anything on time.

### How the values get there
- **Timestamps:** PowerWorld's **raw** export (`TimeStepSaveResultsByTypeCSV`) writes
  column 0, `DateTimeUTCExcelFormat`, as Excel-serial days in **UTC**, not Central time.
  Measured 2026-10-20 on Simulator build 2026-09-25: over a loaded `05:00Z`–`04:00Z`
  window the column matched `Timepoint.TimeDomainDateTimeUTC` row for row, and solar
  output started at 13:00Z. `Timepoint.TimeDomainDateHour` is the field that carries the
  case's local clock. Not yet shown: other builds, and cases set to a time zone other
  than Central.
  `time_utils.convert_to_utc` treats the column as CST: it subtracts 6 h, then 1 h more
  inside US DST (second Sunday in March → first Sunday in November), rounds to the hour,
  and writes ISO-8601 strings marked `Z`. On a UTC input that files every value **7 h
  early in summer and 6 h early in winter** (7 h measured 2026-10-14; the winter figure
  is read from the code). The MW values are right; only their hour labels are wrong.
  Before joining these CSVs on time, re-label them from `Timepoint.TimeDomainDateTimeUTC`
  after checking the row counts match, or add 7 h inside DST and 6 h outside.
- **Solar vs wind split:** columns are matched to generators whose `GenFuelType`
  contains `SUN` (solar file) or `WND` (wind file), keyed by `'BusNum' 'GenID'`.

> **Note on forecast pre-processing:** `interpolate_to_hourly` exists in
> `time_utils.py` for forecast pre-processing but is NOT invoked by the current run
> path (the results post-processor's module / `process_results` / the pipeline's CLI entry script).

### Reading / analyzing the CSVs
Because the first 8 rows are metadata, load with pandas accordingly, e.g.:

```python
import pandas as pd
raw = pd.read_csv("Historical_2025_solar.csv")
meta = raw.iloc[:8]            # the 8 description rows (ISO, type, max MW, lat/lon...)
data = raw.iloc[8:].copy()     # hourly time series
data["DateTimeUTCExcelFormat"] = pd.to_datetime(data["DateTimeUTCExcelFormat"])
data.iloc[:, 1:] = data.iloc[:, 1:].astype(float)
```

Typical reductions once loaded: sum across generator columns for a fleet
solar/wind profile; group columns by the `ISO` / `State` / `Utility` metadata rows
for regional totals; divide by `Gen Max MW` for capacity factors; find peak/trough
hours for extreme-scenario screening.

To write matplotlib code that plots these reductions → [visualize-renewable-output](visualize-renewable-output.md).

### When the run also feeds a loading or N-1 study
Report the **intact (no outage) per-hour branch loading first**: the worst hour and its
percent, read as `max(LinePercent, LinePercent:1)` ([reading-violationctg](reading-violationctg.md)).
Then any N-1 results. A 2026-10-20 run that reported only post-contingency rows missed an
intact 141% overload.

### File the answer back
A good analysis is a knowledge-base asset, not chat exhaust. Per [AGENTS](../AGENTS.md), save notable
comparisons or charts as a new `concept`/`method` page, and link it from
[timestep-simulation](../concepts/timestep-simulation.md) and [index](../index.md).

### Next

Plot the results → [visualize-renewable-output](visualize-renewable-output.md)

### Trail complete
[esapp-overview](esapp-overview.md) → [timestep-simulation-setup](timestep-simulation-setup.md) → [pww-data](../concepts/pww-data.md) →
**how-to-analyze-results** → [visualize-renewable-output](visualize-renewable-output.md) ✅
