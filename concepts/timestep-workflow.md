---
type: concept
domain: cross-cutting
topic: timestep
aliases: [timestep-workflow, time-step-simulation, timestep-engine, weather-to-mw]
tags: [timestep, simulation, powerworld, weather, renewables, pww, parallel]
---

# Concept: The weather-to-MW timestep workflow

## Abstract

The end-to-end chain that turns a weather file into hourly solar and wind output for
every renewable generator in a case: open the case, load a `.pww`, select the renewable
units, tell PowerWorld which fields to save, run its built-in TimeStep simulation, and
export per-generator CSVs. PowerWorld does the weather-to-MW conversion itself using
each unit's embedded PFW model. This is a quasi-static production study, **not** a
transient stability run.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation](timestep-simulation.md) · [pww-data](pww-data.md) · [copper-plate](copper-plate.md) · [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md)
- **Next:** [timestep-simulation-setup](../methods/timestep-simulation-setup.md) to write the code, then [how-to-analyze-results](../methods/how-to-analyze-results.md)
- **Deeper:** [time-step-simulation-backend](../references/time-step-simulation-backend.md)

## Content

### What it is, and what it is not

PowerWorld's TimeStep feature solves a sequence of independent steady-state points, one
per timestamp. It is a production-cost-style study, not dynamics: there is no swing
equation, no machine model, no sub-second behaviour. If you want transient stability,
that is the `TS*` family of script actions and a completely different setup.

The name collision causes real confusion. "Timestep simulation" here means hourly
snapshots across a weather series.

### The chain

1. **Copy the case to a temporary `.pwb`.** The run mutates the case; work on a copy so
   a failed run does not leave your original in a strange state.
2. **Open it** with `esapp`.
3. **Load weather** with `TimeStepLoadPWWRange` over the file's full time span, or
   `TimeStepLoadPWWRangeLatLon` to also crop to a lat/lon box at load time. Append further
   files with `TimeStepAppendPWW`, then assert the timepoint count. **Do not use plain
   `TimeStepLoadPWW` on Simulator 25:** on builds dated 2026-09-20 and 2026-09-25 it fails on
   every file with `Error With Loading PWWFile`, while `TimeStepLoadPWWRange` loads the same
   files. A failure of the plain form says nothing about the file.
4. **Select the renewable generators** — typically those whose fuel type contains `WND`
   or `SUN`. Only selected units produce output.
5. **Declare the fields to save** with `TimeStepSaveFieldsSet(GEN, ...)`. Fields not
   declared here are simply absent from the results, with no warning.
6. **Run** with `TimeStepDoRun()`. Debug a broken setup with
   `TimeStepDoSinglePoint()` first — it solves one timestamp and fails in seconds
   rather than after a long run.
7. **Export** with `TimeStepSaveResultsByTypeCSV`.

**Running contingencies hour by hour?** Set each hour with `TimeStepDoSinglePoint(...)`, then
call `CTGSetAsReference()` before `CTGSolveAll()`. Without it every hour is solved against an
older stored reference and returns the same results. Measured 2026-10-20 on build 2026-09-25:
three hours with about 2.7 GW to 7.6 GW of renewables gave identical answers until the
reference was reset. See [reading-violationctg](../methods/reading-violationctg.md) (Trap 3b).

### PowerWorld does the conversion

You do not compute power curves. Each renewable unit carries an embedded **PFW** (Power
Flow Weather) model string, and PowerWorld applies it to convert weather into MW for
that specific unit. Your job is to supply weather and select units; the physics is
already in the case.

If a unit produces nothing, the usual cause is that it has no PFW model rather than
anything wrong with your weather.

**PWW and PFW are different things.** PWW is the weather data file; PFW is the
generator's weather-to-power model. The names are one letter apart and confusing them
wastes an afternoon. See [pww-data](pww-data.md).

### Reading the output

The exported CSVs are not plain tables. Expect **eight metadata header rows** before the
data begins — read past them or every column parses as text. Timestamps commonly need
a timezone conversion, and the natural final step is splitting the table into a solar
file and a wind file.

Details in [how-to-analyze-results](../methods/how-to-analyze-results.md).

### Series and parallel

A series runner processes timestamps one at a time: slow, but its errors are legible.
A parallel runner using a process pool is dramatically faster because each timestamp is
independent, which makes this an unusually clean parallel problem.

Develop against the series runner and switch to parallel for production. Debugging a
process pool that is failing on one timestamp out of eight thousand is a bad way to
spend a day.

### Copper-plate cases

These studies often run on a copper-plate version of the case — transmission constraints
removed — because the question is usually "what could these renewables have produced?"
rather than "what could have been delivered?" See [copper-plate](copper-plate.md).

Deciding which question you are asking, before the run rather than after, saves
rerunning it.

### Granularity

The workflow is generator-level. Aggregating to area or substation is a post-processing
step on the exported CSVs, not something to ask PowerWorld for during the run.
