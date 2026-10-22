---
type: tool
domain: weather
topic: timestep
aliases: [grid-workshop-auto-pfw, auto-pfw, pfw-insertion-script, grid-workshop-pfw, pfw_eia,
  PFW_EIA.py, attach-pfw-models, missing-pfw-models]
tags: [pfw, weather, renewables, wind, solar, timestep, aux, powerworld, tool]
---

# Tool: Grid-Workshop `Auto_PFW` — attaching PFW weather models to renewables

## Abstract

The research group's `OverbyeResearchGroup/Grid-Workshop` repository has an `Auto_PFW` folder
that attaches PFW (power-flow weather) models to a case's wind and solar units, so TimeStep can
turn weather into MW. It is where the kit's case-auditor sends you when renewables lack a PFW
model. Read this before running it: it **silently skips wind units it cannot classify**, so
always re-count PFW coverage on the copy it saves.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation-setup](../methods/timestep-simulation-setup.md) (the per-unit
  prerequisites a PFW model is one of) · [timestep-and-pfw](../demos/timestep-and-pfw.md) (the
  coverage count that decides whether a case can run a time step) ·
  [timestep-workflow](timestep-workflow.md) (the TimeStep chain that consumes PFW models)
- **Checked by:** the case-auditor's `ts.pfw_missing` rule, which names this tool as the handoff
  and counts how many of the missing wind units carry a class it can use

## Content

### What it does

Two scripts, both driving PowerWorld through SimAuto with the older `esa` package (not `esapp`):

| script | how it chooses the model | prompts |
|---|---|---|
| `PFW_EIA.py` | Wind: `GenMWMax_WindClass1` … `4` from `CustomInteger:1` (1–4) **or** `GenUnitType` (W1–W4). Solar: every unit gets `GenMWMax_SolarPVBasic2`. | none |
| `Automation_integrating_PFW_into_PowerWorld.py` | One user-chosen class applied to every wind unit (WindBasic, WindGeneral, WindClass1–4) and/or every solar unit (SolarPVBasic1/2). | wind / solar / both, then the class |

The sequence is the same in both:

1. Open the case, export the generator table (`PW.csv`) with `GenFuelType`, `GenMWMax`,
   `CustomInteger:1`, `GenUnitType`.
2. Select units by fuel type: `WND (Wind)` and `SUN (Solar)`.
3. Write one AUX record per unit attaching the chosen `GenMWMax_*` model object.
4. `LoadAux` the file and save a **copy** as `<case>_PFW.pwb`; the original is not modified.

A PFW model is a per-generator object record ("this unit converts weather to MW with the
WindClass2 curve"). TimeStep reads it together with a `.pww` weather file; without it a unit
produces nothing, and TimeStep still reports success.

### Failure modes

- **Silent skip.** In `PFW_EIA.py`, a wind unit with neither `CustomInteger:1` in 1–4 nor
  `GenUnitType` W1–W4 gets **no record and no warning**. Cases built from EIA-860 carry the class;
  many synthetic cases do not, and then most wind units are skipped. On both public synthetic
  cases probed 2026-09-30, `CustomInteger:1` read blank on every unit.
- **Record shape.** `WindClass1` records carry 10 values for 9 listed fields (an extra value
  before the hub height); classes 2–4 carry 9. Check the PowerWorld message log after the AUX loads.
- **Interactive script input.** The solar answer is lower-cased and then compared with a
  mixed-case name, so only the answer `1` selects SolarPVBasic1; answering `quit` at a class prompt
  raises an `AttributeError`; the WindGeneral field list spells `DefaultWindMSS`.

### Verifying the result

Count, on the saved `_PFW` copy, the renewable units whose PFW model string is empty
(`TSPFWModelString` two characters or fewer). The count should be zero; anything else is the
silent skip above. Also confirm valid coordinates on those units, since this tool sets only the
PFW model. Running the case-auditor with the `timestep` profile on the copy does both counts.

### When to use which

- The case carries a wind class per unit (EIA-derived): `PFW_EIA.py` is sufficient.
- It does not: give the units a class first (from EIA-860 plant data, or your own judgment), or
  accept that unclassified wind units get no model. The interactive script applies one class to
  every unit, which runs but flattens the fleet into one turbine type.

Established 2026-09-28 from the repository's scripts and README; not re-run on a case for this
page.
