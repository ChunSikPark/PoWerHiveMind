---
type: concept
domain: cross-cutting
topic: timestep
aliases: [timestep-simulation, time-step-simulation-concept, temporal-simulation]
tags: [timestep, simulation, powerworld, weather, renewables, concept]
---

# Timestep simulation (concept)

## Abstract

A timestep simulation (in this project's sense) is PowerWorld's built-in TimeStep feature run over a weather time series: each renewable generator's hourly solar or wind MW output is computed quasi-statically from PWW weather data via its embedded PFW model. This is not a transient-stability study — it has nothing to do with faults or rotor angles. For how to set one up and run it see [timestep-simulation-setup](../methods/timestep-simulation-setup.md); for the code see [time-step-simulation-backend](../references/time-step-simulation-backend.md).

## Connections

- **Up:** [Home](../index.md) · [time-step-simulation-backend](../references/time-step-simulation-backend.md)
- **Across:** [pww-data](pww-data.md) · [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · [how-to-analyze-results](../methods/how-to-analyze-results.md)

## Content

In **this project's** sense, a "timestep simulation" is a run of PowerWorld's
built-in **TimeStep** feature: a power-system case is stepped through a sequence of
weather timestamps so PowerWorld computes, for each renewable generator, how much
**solar** or **wind** MW it would produce at every hour. This is *not* a
transient-stability / dynamics study and has nothing to do with faults or rotor
angles — it is a quasi-static, hour-by-hour weather-to-generation evaluation.

This page is **what it is**; for **how to set one up and run it** see the method
[timestep-simulation-setup](../methods/timestep-simulation-setup.md); for the engine/code see
[time-step-simulation-backend](../references/time-step-simulation-backend.md).

## How it works conceptually
1. A weather time series ([pww-data](pww-data.md)) is loaded into the case
   (`TimeStepLoadPWWRange`; plain `TimeStepLoadPWW` fails on Simulator 25 builds dated
   2026-09-20 and 2026-09-25).
2. Each renewable generator carries an embedded **PFW (PowerFlow Weather) model**
   that maps weather (irradiance, wind speed, etc.) to MW.
3. PowerWorld walks every timestep, applies the weather, and records each
   generator's output (`TimeStepDoRun`).
4. The result is an hourly MW table per generator, split into solar and wind.

## Why it matters
- Converts gridded weather into grid-relevant generation numbers, hour by hour.
- Lets historical years (ERA5 quarter files) and forecast files alike be turned
  into generation profiles for downstream studies.
- Feeds extreme-scenario and renewable-integration analysis.

## Series vs parallel
The timestep simulation pipeline runs it **series** (slow, for testing) and
**parallel** (fast, many sims at once). Output resolution is currently
**generator-level** — area/substation-level aggregation is a noted future extension.

## Related
- [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · [how-to-analyze-results](../methods/how-to-analyze-results.md) · [pww-data](pww-data.md) · [Home](../index.md)
