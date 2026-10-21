---
type: tool
domain: tooling
topic: scripting
aliases: [simauto, simauto-com, powerworld-com, saw]
tags: [powerworld, simauto, com, tool]
---

# PowerWorld SimAuto

## Abstract

SimAuto is PowerWorld Simulator's COM Automation Server — the Windows-only layer that all PowerWorld Python scripts ultimately talk to. In esapp it is wrapped by the `SAW` class (assembled via ~20 mixins) and reached through `pw.esa`. This page covers the SAW mixin architecture, verified raw COM method signatures for data, scripting, solving, and state management, and the exception hierarchy. Use it when the high-level `pw[...]` bracket API isn't sufficient and you need to call `pw.esa` directly.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [esapp-overview](../methods/esapp-overview.md) · [aux-script-commands](../references/aux-script-commands.md) · [esapp-script-command-wrappers](esapp-script-command-wrappers.md) (named wrapper over `RunScriptCommand`, the house rule)

## Content

**SimAuto** is PowerWorld Simulator's COM **Automation Server** — it exposes the
running simulator to external scripts (open cases, read/write objects, solve
power flow, run script commands, switch EDIT/RUN modes). It is the layer
*underneath* [esapp](esapp.md). In esapp it is wrapped by the **`SAW` (SimAuto Wrapper)**
class and reached through `pw.esa`. Because it is a COM server, everything here
is **Windows-only** (esapp talks to it via `pywin32`).

## SAW — the wrapper esapp puts on top

`SAW` lives in `esapp/saw/saw.py` and is assembled by the **mixin pattern**:
`SAWBase` (`saw/base.py`, core COM interface + case management + generic data
retrieval) plus ~20 capability mixins — `DataMixin`, `PowerflowMixin`,
`MatrixMixin`, `ContingencyMixin`, `TransientMixin`, `SensitivityMixin`,
`GICMixin`, `OPFMixin`, `PVMixin`, `QVMixin`, `ATCMixin`, `FaultMixin`,
`TopologyMixin`, `RegionsMixin`, `ModifyMixin`, `GeneralMixin`,
`CaseActionsMixin`, `ScheduledActionsMixin`, `TimeStepMixin`, `WeatherMixin`.

You rarely instantiate `SAW` directly — `PowerWorld.open()` does
`SAW(fname, CreateIfNotFound=True, early_bind=True)` and stores it on `pw.esa`.

## Raw calls (when the bracket interface isn't enough)

Real method names, verified in `esapp/saw/`:

```python
# Generic read/write (esapp/saw/data.py)
pw.esa.GetParametersMultipleElement("Bus", ["BusNum", "BusPUVolt"])
pw.esa.GetParamsRectTyped("Bus", ["BusNum", "BusPUVolt"])          # typed DataFrame; backs pw[...]
pw.esa.ChangeParametersSingleElement("Gen", ["BusNum","GenID","GenMW"], ["1","1","100"])
pw.esa.ChangeParametersMultipleElement("Gen", cols, values)
pw.esa.ChangeParametersMultipleElementRect("Bus", cols, df)        # backs pw[Type] = df

# Mode + scripting (saw/general.py, saw/base.py)
pw.esa.EnterMode("EDIT"); pw.esa.EnterMode("RUN")                  # or PowerWorldMode.EDIT/.RUN
pw.esa.SolvePowerFlow()          # call the NAMED wrapper, not RunScriptCommand: 310
                                 # SCRIPT commands are wrapped, and the wrapper gives you a
                                 # typed signature plus correct argument-string building.
                                 # The real win is ONE PATCH POINT — a hand-written string
                                 # is a call site the esapp maintainer can never reach when
                                 # PowerWorld changes a command's syntax. esapp does NOT
                                 # introspect PowerWorld's command table or check the
                                 # Simulator version; this is an upgrade path, not a
                                 # runtime check.

# Solve / matrices / TS (saw/powerflow.py, matrices.py, transient.py)
pw.esa.SolvePowerFlow(SolverMethod.RECTNEWT)
pw.esa.get_ybus(); pw.esa.get_jacobian()
pw.esa.TSInitialize(); pw.esa.TSSolve(ctg); pw.esa.TSGetResults(...)

# State save/restore (used by pw.snapshot())
pw.esa.SaveState(); pw.esa.LoadState()
```

`EnterMode` accepts the `PowerWorldMode` enum or the raw strings `"EDIT"` /
`"RUN"`. Object creation through the bracket interface needs **EDIT mode** plus
`CreateIfNotFound=True` on the SAW.

## Why it matters here

Everything in this knowledge base that touches a `.pwb` case ultimately goes through
SimAuto. esapp wraps it so you almost always use `pw[...]` and `pw.pflow()`
instead of raw COM, but the raw calls remain available on `pw.esa` for anything
the high-level API doesn't cover (time-step runs via `TimeStepMixin`, weather
via `WeatherMixin`, OPF/PV/QV, fault analysis, etc.).

## Exceptions

SAW raises a typed hierarchy rooted at `PowerWorldError` (`saw/_exceptions.py`):
`COMError`, `CommandNotRespectedError`, `SimAutoFeatureError`,
`PowerWorldPrerequisiteError`, `PowerWorldAddonError`. The bracket-write path
keys off `PowerWorldPrerequisiteError` ("not found") to decide whether to create
new objects.

## Related

- Wrapped by [esapp](esapp.md)
- How-to: [esapp-overview](../methods/esapp-overview.md)
