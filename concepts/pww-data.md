---
type: dataset
domain: weather
topic: timestep
aliases: [pww, pww-file, powerworld-weather, powerworld-weather-data]
tags: [pww, weather, dataset, binary-format, era5, hrrr, noaa]
---

# PWW data (PowerWorld Weather)

## Abstract

PWW (PowerWorld Weather) is a custom byte-packed binary format, produced by a weather pipeline and consumed by PowerWorld Simulator's TimeStep Simulation engine. It encodes gridded weather variables as uint8 values (0–254) per timestep and grid point, with 255 as the NaN sentinel. This page covers the VERSION 2 binary spec, variable encoding formulas, per-source production pipelines (ERA5, HRRR, GFS, WRF), and verification procedures. Drill deeper when writing or debugging a PWW file, or tracing weather data into a timestep study.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) (downloading PWW files) · [timestep-simulation](timestep-simulation.md) · [copper-plate](copper-plate.md) · step 3 of this reading sequence: prev [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · next [how-to-analyze-results](../methods/how-to-analyze-results.md)

## Content

**Step 3 of this reading sequence.** ← prev: [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · next: [how-to-analyze-results](../methods/how-to-analyze-results.md).

> **Firewall: PWW ≠ PFW.** PWW = weather *data* files (this page). PFW = the PowerFlow Weather *model* used in [copper-plate](copper-plate.md) studies. Never cross-link their aliases.

PWW stores gridded weather variables at discrete timesteps as uint8 values, one byte per variable per grid point per timestep.

### Binary Format (VERSION 2)

All values are **little-endian**. Types: `h`=int16, `i`=int32, `d`=float64, `u8`=uint8.

```
Offset  Type    Field
──────  ──────  ───────────────────────────────────────────────────────────
0       h       KEY1 = 2001
2       h       KEY2 = 8066  (8065 = VERSION 1; 8066 signals VERSION 2)
4       h       VERSION = 2
6       d       date_min  (OLE automation date — days since 1899-12-30)
14      d       date_max
22      d       lat_min / lat_max / lon_min / lon_max   (4 × d = 32 bytes)
54      h       META_STRINGS  (≥ 1 for VERSION 2)
56      cstr[]  meta_strings[META_STRINGS]  — "PowerWorld Timestep Simulation Weather\0"
─       i       COUNT       (number of timesteps)
─       i       SAMPLE_seconds  (3600=hourly, 900=15-min subh, 0=irregular)
─       i       LOC         (number of stations / grid points)
─       h       LOC_FC = 0
─       h       VARCOUNT
─       h[]     var_codes[VARCOUNT]
─       h       BYTECOUNT = VARCOUNT  (always VARCOUNT when all vars are uint8)
─       i[]     valid_counts[VARCOUNT]   ← VERSION 2 only — non-255 count per variable
─               station_records[LOC]   lat(d), lon(d), elev(h), who(cstr), country(cstr), region(cstr)
─       u8[]    data_array[COUNT × VARCOUNT × n_lat × n_lon]  — C order, 255 = NaN sentinel
```

**Grid dimensions** are derived from header bounds (ERA5 grid is 0.25°):
```python
n_lat = round((lat_max - lat_min) / 0.25) + 1
n_lon = round((lon_max - lon_min) / 0.25) + 1
```

**Longitude convention:** descending east→west (e.g. −60 → −130 for CONUS). Lat is ascending south→north.

**OLE epoch:** 1899-12-30. Timestamps before this date encode as negative and PowerWorld rejects the file. Pre-1900 data must be re-based forward (e.g. 1899 shifted to 1999, +100 years, preserving month/day/hour).

### VERSION 2 Traps (undocumented; the spec doc only covers VERSION 1)

Three requirements are missing from the format doc, and PowerWorld needs all of them to parse the file:

1. **KEY2 = 8066** (not 8065; this magic number signals VERSION 2 to the loader)
2. **META_STRINGS ≥ 1** with at least one description string
3. **VARCOUNT × int32 valid_count block** between BYTECOUNT and station data, counting non-255 values per variable

Without all three, PowerWorld misaligns the byte stream: station block bytes are read as valid counts, producing nonsense `ValidPercent*` values (e.g. 1267%, 990%) and shifted variable readings (temperature showing cloud cover bytes, etc.).

### Variable Codes and Encoding

All values stored as **uint8 (0–254)**; **255 = NaN sentinel** (excluded from valid counts).

| Code | Variable | Encoding formula | Unit stored |
|------|----------|-----------------|-------------|
| 102 | tempF | `round(°F + 115)` | °F+115 offset |
| 104 | DewPointF | `round(°F + 115)` | °F+115 offset |
| 106 | WindSpeedmph | `round(m/s × 2.236936)` | mph (10 m) |
| 107 | WindDirection | `round(degrees / 5)` — division INSIDE round() | ×5 to decode |
| 119 | CloudCoverPerc | `round(fraction × 100)` — GFS/ERA5 tcc is 0.0–1.0, must ×100 | % |
| 110 | WindSpeed100mph | `round(m/s × 2.236936)` | mph (100 m) — ERA5, GFS |
| 112 | WindSpeed80mph | `round(m/s × 2.236936)` | mph (80 m) — HRRR only |
| 120 | GHI | `round(W/m² / 5)` | ×5 to decode |
| 121 | DHI | `round(W/m² / 5)` | ×5 to decode |
| 136 | WindGust | `round(m/s × 2.236936)` | mph |
| 151 | PrecipitationRate | `round(kg/m²/s × 3600)` | mm/hr |
| 150 | PercentFrozenPrecip | direct percent byte | % — HRRR only |
| 122 | VerticallyIntegratedSmoke | `round(40 × log10(colmd × 1e6))` | dBZ-equiv — HRRR only |

**Wind direction encoding trap:** the division MUST be inside `round()`: `round(degrees / 5)`, never `round(degrees) / 5`. The latter truncates (not rounds) on uint8 cast, causing up to 4° systematic error.

**Code-112 (suspected PowerWorld bug):** PowerWorld's TimeStep loader throws an access violation on code 112 (no loadable 80 m wind field in PowerWorld). HRRR pipelines deliberately keep 112 because their wind is genuinely 80 m; this is a suspected PowerWorld bug, not yet verified (glitch `2026-10-21-pww-code112-av`). Do NOT remap 112→110.

### How PWW Is Produced

The weather pipeline runs four Docker pipelines, each writing a different PWW flavor:

| Pipeline | SAMPLE_sec | Variables | Output naming |
|----------|-----------|-----------|---------------|
| ERA5/CDS | 3600 (hourly) | 9 (no precip/smoke) | `{Region}{YYYY}_Q{Q}.pww` |
| NOAA/GFS forecast | 3600 | 8 (no DHI — written as 255) | `Forecast_{Region}_Run{YYYY-MM-DD}T{HH}Z.pww` |
| HRRR Forecast | 3600 | 10 | `{YYYY-MM-DD}T{HH}Z_sfc_48_CONUS.pww` |
| HRRR History (15-min) | 900 | 10 | `{YYYY-MM-DD}_Q{1..4}_subh_15min_CONUS.pww` |
| HRRR History (hourly) | 3600 | 10 | `{YYYY-MM-DD}_hourly_CONUS.pww` |
| WRF reanalysis | varies | 9 (no precip) | `WRF_{period}_{Region}.pww` |

ERA5 also emits a human-readable `.parquet` alongside the PWW.

### Who Consumes PWW

- dynamic line rating: weather around each line for IEEE 738 thermal rating
- hottest- and coldest-hour studies: finding the temperature-extreme scenarios
- [copper-plate](copper-plate.md) studies: weather inputs for the PFW model on renewables
- Any [timestep-simulation](timestep-simulation.md) study needing time-varying weather driving

### Using PWW in a Study

1. Pick spatial/temporal crop (via [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md), which crops by region and time window)
2. Map weather to case elements (lines, renewable units, load zones)
3. Feed per-timestep into the run; see [timestep-simulation-setup](../methods/timestep-simulation-setup.md)
4. Analyze → [how-to-analyze-results](../methods/how-to-analyze-results.md)

### Verifying a PWW (do both before trusting a new file)

1. **Structural + positional round-trip** (offline): parse header, assert KEY2=8066, VERSION=2, ≥1 meta string, valid_count block length == VARCOUNT, data size == COUNT × VARCOUNT × LOC. Then pick a few stations and confirm decoded bytes match the source grid cell at that (lat, lon).
2. **PowerWorld load test:** `TimeStepLoadPWW(file, "Weather Only")` via ESA/SimAuto; exit 0 = file loads cleanly. Pass absolute paths (PowerWorld resolves relative paths against its own working dir). Keep the smoke test as a small standalone script next to the converter that wrote the file.
   **On Simulator 25 (builds dated 2026-09-20 and 2026-09-25) this test fails for every file**: plain `TimeStepLoadPWW` raises `Error With Loading PWWFile` (suspected PowerWorld issue, not yet confirmed: glitch `2026-10-20-timestep-loadpww-plain`). `TimeStepLoadPWWRange(file, start, end, "Weather Only")` over the file's full span loads the same files (72 and 2,064 timepoints on two files, reproduced 2026-09-24). On those builds, run the smoke test with the Range form and assert the timepoint count. A failure of the plain form says nothing about the file.

### Does the file cover the units? (the case auditor's footprint check)

A renewable whose nearest station in the file is far away still runs: it takes that station's
weather, and the time step gives no warning. The case auditor (`ts.pww_footprint`) reads only the
file's header station list and flags every located renewable whose nearest station is more than
**25 miles** away. That number has no source: it is a proposed default in
`skills/case-audit/engine/thresholds.py` (`PWW_MAX_STATION_MILES`), chosen because a 0.25-degree
grid puts every point inside its footprint within about 12 miles of a station, so 25 miles leaves
margin and still catches a unit outside the grid.

### Related

- [Home](../index.md)
