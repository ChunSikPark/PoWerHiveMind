---
type: concept
domain: tooling
topic: contingency
aliases: [agc-participation-factors, participation-factors, contingency-make-up-power, GenParFac,
  SetParticipationFactors, who-covers-lost-mw, UseAreaPartsMakeUpPower]
tags: [powerworld, agc, contingency, n-1, gotcha, synthetic-grid]
---

# AGC flags and participation factors: who covers lost MW in a contingency

## Abstract

When an outage drops generation, PowerWorld's contingency solve must find the MW somewhere. Three
settings decide who supplies it: the AGC flag, the participation factor, and the make-up power
option. **AGC on with every factor at 0 changes nothing, so the slack still takes everything.**
The common convention is AGC on for dispatchable synchronous units only, factors from
`MAXMWRAT`, and make-up power `Gen Part Factors`. Setting them leaves the base case untouched;
only contingency solves move. Read before any N-1 run on a case that loses generation.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [opf-preconditions](opf-preconditions.md) (the same AGC flag, needed for an OPF) ·
  [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md)
  (the swing taking all make-up power, playbook step 4) ·
  [reading-violationctg](../methods/reading-violationctg.md) (reading what the contingency solve
  then reports)
- **Deeper:** [powerworld-option-objects-v25](../references/powerworld-option-objects-v25.md) ·
  [powerworld-study-commands](../references/powerworld-study-commands.md)

## Content

### The three settings

| Setting | Field | What it does |
|---|---|---|
| AGC flag | `Gen.GenAGCAble` = `YES` / `NO` | whether a unit may be moved to cover a change in MW |
| Participation factor | `Gen.GenParFac` | the unit's share; a unit with twice the factor picks up twice the MW |
| Make-up power | `CTG_Options.UseAreaPartsMakeUpPower` | `Area Part Factors`, `Gen Part Factors`, or `Same as Power Flow`; PowerWorld's field note recommends `Gen Part Factors` ([powerworld-option-objects-v25](../references/powerworld-option-objects-v25.md)) |

The area's own AGC status (`Area.AreaAGCStatus`, `None` on every public case surveyed below) is a
separate switch; with `Gen Part Factors` the make-up goes straight by each unit's factor.

### Setting the factors

`SetParticipationFactors(Method, ConstantValue, Object);`
([powerworld-study-commands](../references/powerworld-study-commands.md)):

- `MAXMWRAT`: factor from each unit's maximum MW. It does not go stale when the dispatch changes.
  The usual choice.
- `RESERVE`: factor from headroom, MWMax minus present MW. Better physics, but it must be rerun
  after any dispatch change.
- `CONSTANT`: every unit the same `ConstantValue`.
- `Object`: `SYSTEM`, `[Area n]`, `[Zone n]`, `AREAZONE`, or `DISPLAYFILTERS`. It sets factors on
  every generator in scope; only units with `GenAGCAble = YES` take part.

### Traps

- **AGC flags with zero factors do nothing.** Measured 2026-10-18 on a ~9k-bus synthetic case: AGC
  switched on for several hundred units, every factor 0, and the solution did not move. Lost MW
  still lands on the slack, which on that case was one unit that could not cover a large plant.
- **`MAXMWRAT` stores per unit on the 100 MVA base.** A 150 MW unit gets 1.5, not 150. A check for
  "factor equals MWMax" fails on a correct case; check that factor / MWMax is constant across the
  AGC units. Some public cases store the factor in MW instead; only the ratios matter.
- **A battery on the slack bus shares the slack's swing.** The slack's change is split among that
  bus's units, so the battery charges or discharges whenever the slack moves, regardless of its
  scheduled MW.
- **The base case does not change.** With the area AGC status at `None`, setting factors and
  make-up power left every bus voltage identical (max change 0.0). Only contingency solves are
  affected.
- **Writing a unit's MW may switch its AGC flag off.** Suspected, not confirmed (seen 2026-10-18,
  reproduced on Synth40 on 2026-10-20, Simulator build 2026-09-25): writing a *changed* `GenMW`
  read back `GenAGCAble = NO` for that unit, while writing the same MW or another field did not.
  Workaround: write `GenAGCAble = YES` in the same call as the MW, or set the AGC flags after the
  dispatch write, and read them back either way.

### What public synthetic grids use

Surveyed read-only on 2026-10-18:

| Case | AGC on for | Factor | Make-up power |
|---|---|---|---|
| Synth2k series 25 summer peak | every unit, renewables and batteries included | = MWMax | Area Part Factors |
| Synth2k series 24, 2016 summer peak | thermal and hydro | = MWMax | Gen Part Factors |
| Synth2k series 24, 2024 high renewables | thermal and hydro | = MWMax | Gen Part Factors |
| a public 10k-bus synthetic case | thermal and hydro | = MWMax | Gen Part Factors |
| Synth40 | every unit | all 0 | Area Part Factors |

The common convention is AGC on for dispatchable synchronous units only (not wind, solar,
batteries, or condensers with no MW range), factors from `MAXMWRAT`, make-up `Gen Part Factors`.

### Checking it

Read back on a cold reopen, not in the session that set it: the AGC units each have a factor above
0 with factor / MWMax constant, renewables and batteries keep `GenAGCAble = NO`, and
`UseAreaPartsMakeUpPower` reads `Gen Part Factors`.
