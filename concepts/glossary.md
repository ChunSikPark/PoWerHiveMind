---
type: concept
domain: tooling
topic: scripting
aliases: [glossary, terminology, acronyms, definitions, jargon]
tags: [glossary, terminology, powerworld, esapp, reference]
---

# Concept: Glossary

## Abstract

Every acronym and piece of jargon this knowledge base uses, defined once. Read the
**Pairs that get confused** section even if you skip the rest — `PWW` versus `PFW` alone
has cost people entire afternoons, and mixing them produces results that look right.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) · [pww-data](pww-data.md)

## Content

### Pairs that get confused

These are near-identical names for different things. Confusing them produces
plausible-looking wrong answers, not errors.

| These two | Are not the same |
|---|---|
| **PWW** vs **PFW** | `PWW` is a **weather data file** — measurements at stations over time. `PFW` (Power Flow Weather) is a **model string embedded in a generator** that converts weather into MW for that unit. You load a PWW; a PFW is already inside the case. One letter apart, unrelated |
| **`esapp`** vs **`esa`** | Two different Python packages wrapping the same SimAuto server. This kit assumes `esapp`. Do not mix them |
| **`PowerWorld`** vs **`SAW`** | `PowerWorld` is esapp's high-level entry point. `SAW` is the raw SimAuto wrapper beneath it, reached as `pw.esa`. `pw.RunScriptCommand(...)` does not exist; `pw.esa.RunScriptCommand(...)` does |
| **TimeStep** vs **Transient Stability** | *TimeStep* solves a sequence of independent steady-state points across a weather series — a production study. *Transient stability* (the `TS*` actions) simulates sub-second dynamics. Different machinery |
| **`Simulator`** vs **`SimAuto`** | Simulator is the program. SimAuto is its automation interface, **licensed separately**. Having one does not mean having the other |
| **`LimViolPct`** on thermal vs voltage rows | The polarity differs between the two. Never rank the two kinds of violation on this field directly; see [reading-violationctg](../methods/reading-violationctg.md) |
| **`.pwb`** vs **`.aux`** | `.pwb` is the binary case file. `.aux` is a text file of data and/or SCRIPT actions that is **merged into** an open case |

### Alphabetical

| Term | Meaning |
|---|---|
| **AC** | Alternating current. An "AC solve" solves the full nonlinear power flow, unlike a DC approximation |
| **ACSR** | Aluminium Conductor Steel Reinforced — the common transmission conductor type |
| **AGC** | Automatic Generation Control — how generation follows load in real time |
| **`.aux`** | PowerWorld Auxiliary file. Text format carrying object data and/or `SCRIPT` action blocks. `LoadAux` **merges** it into the open case rather than replacing anything |
| **Branch** | A transmission line or transformer. Keyed by its two bus numbers plus a circuit identifier |
| **`BusNum`** | A bus's primary key. `BusNum:1` denotes the far end of a branch |
| **CIM** | Common Information Model — a utility data-exchange standard |
| **COM** | Component Object Model, the Windows mechanism SimAuto is built on. A `com_error` is a Windows-level failure, usually meaning SimAuto is unregistered or unlicensed |
| **Contingency / CTG** | A modelled outage. `CTGLabel` is its key. PowerWorld **trims whitespace from `CTGLabel` on load**, so the label you wrote is not always the one you get back |
| **DC solve** | The linearized power-flow approximation. Fast, ignores voltage and reactive power, and **always reports zero mismatch** — it cannot tell you a generation schedule is short |
| **DHI / DNI / GHI** | Diffuse Horizontal, Direct Normal, and Global Horizontal Irradiance. Three different solar measurements; models usually want a specific one |
| **EDIT mode / RUN mode** | PowerWorld's two operating modes. Many data writes are rejected outside EDIT. Switch with `EnterMode` |
| **ERA5** | ECMWF's hourly reanalysis dataset, roughly 0.25° resolution. Good for long historical records |
| **`esapp`** | ESA++, the Python package this kit uses to drive PowerWorld. Provides `PowerWorld`, a bracket interface returning DataFrames, and `SAW` underneath |
| **GIC** | Geomagnetically Induced Current — quasi-DC current driven through the grid by geomagnetic disturbance |
| **HRRR** | NOAA's High-Resolution Rapid Refresh, ~3 km and sub-hourly. Use it to refine a specific window, not to scan a year |
| **Injection group** | A named collection of injections treated as one source or sink in transfer studies |
| **Interface** | A named set of branches whose combined flow is monitored against a limit |
| **Key field** | The column(s) identifying an object: `BusNum` for a bus, `BusNum` + `GenID` for a generator. **Omit them from a DataFrame you write back and the write silently does nothing** |
| **kcmil** | Thousand circular mils — a conductor size unit |
| **LODF** | Line Outage Distribution Factor. How flow redistributes onto other branches when one branch is outaged |
| **Mismatch** | Residual power imbalance at a bus after solving. Near zero means converged — but see *DC solve* |
| **MVA / MW / MVAR** | Apparent, real, and reactive power. Branch limits are usually MVA; dispatch is in MW |
| **N-1** | The reliability criterion that the system must survive the loss of any single element |
| **OPF / SCOPF** | Optimal Power Flow, and its Security-Constrained form which additionally respects contingency limits |
| **`.pwb`** | PowerWorld Binary case file — the case itself |
| **PFW** | Power Flow Weather. The model **inside a generator** converting weather to MW. Not a file |
| **Per unit (pu)** | Values normalized to a base. Voltage near 1.0 pu is nominal. Changing the system base re-derives these — see [per-unit-basis-discipline](per-unit-basis-discipline.md) |
| **PTDF** | Power Transfer Distribution Factor. How a transfer between two points distributes across branches |
| **PV / QV study** | Nose-curve and reactive-margin voltage stability analyses. This kit tells you which action runs them, not what they mean |
| **PWW** | PowerWorld Weather file. Station measurements over time — the input to TimeStep |
| **`SAW`** | The SimAuto wrapper object inside esapp, reached as `pw.esa`. Where `RunScriptCommand` lives |
| **SCRIPT action** | A named PowerWorld command such as `SolvePowerFlow` or `SaveCase`, runnable from an `.aux` file or via `RunScriptCommand`. Catalogue: [aux-script-commands](../references/aux-script-commands.md) |
| **Shift factor** | Sensitivity of a branch's flow to a change in injection |
| **SimAuto** | PowerWorld's COM automation server. **Licensed separately from Simulator** |
| **Slack bus** | The bus absorbing system imbalance. It will silently absorb an enormous shortfall and report success, which is why a DC mismatch of zero proves nothing |
| **Super bus** | A group of buses merged by topology processing into one electrical node |
| **TimeStep** | PowerWorld's feature for solving a series of steady-state points across a weather time series. Not dynamics |
| **TS** | Transient Stability. The `TS*` script actions. Genuinely dynamics |
| **UTC** | Coordinated Universal Time. Weather data is usually UTC while case data may be local — check before joining them |

### Terms this kit deliberately does not define

Contingency analysis fundamentals, OPF formulation, PV/QV curve theory, transient
stability theory, and weather science such as dynamic line ratings. This kit is about
**operating PowerWorld**, not teaching power systems. When a task needs that theory, say
so rather than improvising.
