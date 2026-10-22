---
type: method
domain: cross-cutting
topic: timestep
aliases: [timestep-setup, ts-setup, timestep-simulation-howto]
tags: [powerworld, simauto, timestep, simulation, weather, renewables, pww]
---

# Method: Writing a timestep simulation

## Abstract

How to drive PowerWorld's TimeStep simulation, turning `.pww` weather files into hourly solar/wind generation CSVs. Covers the prerequisites a case must satisfy per renewable generator (`GenFuelType` containing WND or SUN, valid Lat/Lon, a `TSPFWModelString` PFW model), one pipeline's optional ISO-labelling step, and the pipeline's worker-function sequence. This is step 2 of this reading sequence; for the PWW weather files see [pww-data](../concepts/pww-data.md).

> **Writing the backend code?** [time-step-simulation-backend](../references/time-step-simulation-backend.md) has the full worker-function call sequence, the required `TIMESTEPSaveSelectedModifyStart/Finish` wrapper, the `_GEN_PARAM` field list, and the key-field rule.

## Connections

- **Up:** [Home](../index.md) · [timestep-simulation](../concepts/timestep-simulation.md)
- **Deeper (backend code):** [time-step-simulation-backend](../references/time-step-simulation-backend.md) (exact call sequence, field lists, gotchas)
- **Across:** [timestep-simulation](../concepts/timestep-simulation.md) · [auto-pfw-scripts](../concepts/auto-pfw-scripts.md) (attaching the PFW models) · [esapp](../concepts/esapp.md) · step 2 of this reading sequence: prev [esapp-overview](esapp-overview.md) · next: [pww-data](../concepts/pww-data.md) · final: [how-to-analyze-results](how-to-analyze-results.md)

## Content

**Step 2 of this reading sequence.** ← prev: [esapp-overview](esapp-overview.md) · next: [pww-data](../concepts/pww-data.md).
The concept behind it: [timestep-simulation](../concepts/timestep-simulation.md).

TimeStep simulation is *not* a transient-stability study.

> **Library note: prefer `esapp` over `esa`.** Older repos import the standalone `esa` (Easy SimAuto) package. `esapp` (ESA++) is the updated, better-documented version of the same thing, so write esapp. Every `RunScriptCommand` / `TimeStep*` script command is identical via `pw.esa.RunScriptCommand(...)`, and the bracket interface (`pw[Type, fields]`, `pw[Type] = df`) replaces esa's `GetParametersMultipleElement` / `change_parameters_multiple_element_df`. See [esapp-overview](esapp-overview.md).

### 0. Prerequisites

PowerWorld needs, on each renewable generator: a `GenFuelType` that contains `WND`
or `SUN` (the case labels them `WND (Wind)`, `SUN (Solar)`), valid coordinates, and a
PFW model string (`TSPFWModelString` longer than 2 characters). A unit with no PFW model
runs and reads 0 MW for the whole run; attach models with
[auto-pfw-scripts](../concepts/auto-pfw-scripts.md). Coordinates: on both public
synthetic cases probed 2026-09-30 the unit's own `Gen.Latitude` read blank and the substation's
`Gen.Latitude:1` / `Longitude:1` (the field export's "Substation Latitude") were set. That
TimeStep then reads the substation pair is not verified in the kit.

### 1. (Optional, one pipeline's convention) Label units with an ISO region

This is **not** a PowerWorld prerequisite. One time-step pipeline writes an ISO region into
`CustomString:2`, a custom field, so its output CSVs can carry an ISO header row; TimeStep does
not read it. Skip this section unless your post-processing needs the label.

The pipeline's ISO-assignment step does a geopandas spatial join
of every generator's lat/long against ISO-region shapefiles (nearest-neighbor for
units outside any boundary) and writes the ISO assignment back into the case, where it
later appears as the first metadata header row. Run it once per case; skip it if the
case already has ISO assignments.

> The ISO-assignment step writes **only `CustomString:2`**. It does
> **not** touch `TSPFWModelString`. PFW model strings must already be in the case;
> [auto-pfw-scripts](../concepts/auto-pfw-scripts.md) attaches them, and the
> case-auditor's `timestep` profile counts which units still lack one.

### 2. What your code does (the worker function)

`timestep_worker(case, pww_list, result_csv)` is the core function to implement:
1. Copies the case to a temp `.pwb`, opens it with `PowerWorld(tmp_case)` from esapp.
2. Pulls generator metadata (`GetParametersMultipleElement('gen', ...)` / `pw[Gen, fields]`).
3. Loads weather: `TimeStepLoadPWW("...","Weather Only")` then
   `TimeStepAppendPWW(...)` for any additional files. On Simulator 25 (builds dated 2026-09-20
   and 2026-09-25) the plain load fails with `Error With Loading PWWFile` (suspected PowerWorld issue, not yet confirmed: glitch `2026-10-20-timestep-loadpww-plain`); use
   `TimeStepLoadPWWRange` over the file's full span and assert the timepoint count (see
   [pww-data](../concepts/pww-data.md)).
4. Selects renewables (`GenFuelType` contains `WND|SUN`) and marks them
   `TimeDomainSelected`.
5. Picks the saved fields:
   `TimeStepSaveFieldsSet(GEN, [BGGenMWFuelTypeGeneric:10, BGGenMWFuelTypeGeneric:12], SELECTED)`.
6. Runs `TimeStepDoRun()` and exports via `TimeStepSaveResultsByTypeCSV(gen, ...)`.

> The simulation is **generator-level** by construction: `TimeStepSaveFieldsSet`
> targets `GEN`. Area/substation-level output is not covered here.

### 3. Inputs and outputs

- **In:** one case + one or more `.pww` weather files ([pww-data](../concepts/pww-data.md)).
- **Out:** per run, two CSVs (solar + wind). Historical quarter files grouped by
  year are named `Historical_{year}_solar.csv` / `_wind.csv`; a forecast file is
  named after its stem. Resume-safe: a run is skipped if both its CSVs already
  exist (delete them to re-run).

### Next

- Get the weather inputs → [pww-data](../concepts/pww-data.md)
- Analyze the CSVs → [how-to-analyze-results](how-to-analyze-results.md)
