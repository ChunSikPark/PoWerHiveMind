---
type: reference
domain: tooling
topic: scripting
aliases: [powerworld-study-options, study-options, solution-options, ctg-options, opf-options, scopf-options, object-fields, case-object-fields, sim-solution-options]
tags: [powerworld, esapp, options, power-flow, contingency, opf, scopf, schema, reference]
---

# Reference: steady-state study options, and the PowerWorld object-field export

## Abstract

The entry point for changing how any PowerWorld study runs ("200 iterations", "report islands",
"more SCOPF loops", "DC"): per study, which option object and command control it, with each
key field tagged verified, documented or schema-only. The exhaustive field and command lists
live on two companion pages; the Simulator 25 field export sits beside this page.

## Connections

- **Up:** [Home](../index.md)
- **Deeper:** [powerworld-option-objects-v25](powerworld-option-objects-v25.md) (all 32 option objects, 1,079 fields, generated from
  the export) · [powerworld-study-commands](powerworld-study-commands.md) (every study SCRIPT command with parameters and
  defaults, plus 29 silent behaviours, from the aux-file-format document)
- **Across:** [esapp-schema-reference](esapp-schema-reference.md) (key fields and SAW methods, read from esapp source — the
  complement to this page's option fields) · [opf-preconditions](../concepts/opf-preconditions.md) (the three OPF walls) ·
  [reading-violationctg](../methods/reading-violationctg.md) (reading what a contingency run reports) ·
  [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (why the distributed-CTG switch below is not used)
- **Used by:** [reducing-a-contingency-set](../methods/reducing-a-contingency-set.md) · [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) ·
  [powerworld-limitset-setdata](../methods/powerworld-limitset-setdata.md)

## Content

### The field export

`references/powerworld-object-fields-v25.xlsx` is PowerWorld's own case-object field list,
exported from **Simulator 25 (beta)** on 2026-09-12. One sheet, `ObjectFields`: **1,026 object
types and about 101,000 fields**. It is a schema, not case data. The field list changes between
Simulator versions; re-export rather than trust it on another build.

An object's header row carries the name in column A; its fields follow on rows with column A
blank. Columns:

| column | meaning |
|---|---|
| Key/Required Fields | `*1*`, `*2*`… primary key parts in order; `*A*` alternate key; `**` required to create the object. Suffixes (`*2B*`) and a bare `<` also appear; the export does not define them |
| Variable Name | the name esapp `pw[...]`, `GetParametersMultipleElement` and aux `SetData` use. A `:N` suffix is a separate field (`MaxItr:1`), spelled `MaxItr__1` as a Python attribute |
| Concise Variable Name | a second name for the same field — `DCPFMode` and `DCApprox` are one field |
| Available Field List | the GUI path, e.g. `Inner Power Flow Loop\Max Iterations` — search this to go from a dialog label to a field |
| Enterable | `Yes` = writable; `AUX/Paste` = writable only through an aux file or paste; blank = read-only |

Look a field up without opening Excel:

```python
import pandas as pd
df = pd.read_excel("powerworld-object-fields-v25.xlsx")
df["Object Type"] = df["Object Type"].ffill()
f = df[df["Variable Name"].notna()]
f[f["Object Type"].eq("Shunt") & f["Key/Required Fields"].notna()]   # keys + required
f[f["Description"].str.contains("island", case=False, na=False)]     # search by meaning
```

**Worked example of why the export matters.** "Add a shunt to an area": `Shunt` is keyed
`BusNum` (`*1*`) + `ShuntID` (`*2B*`) and requires `SSCMode`, `SSNMVR`, `SSStatus` (`**`). It
carries **two** area fields: `AreaNum` ("Area\Num of Shunt", writable — the shunt's own area
assignment, which may differ from its bus's) and `AreaNum:1` ("Area\Num of Bus", read-only).
Writing `AreaNum` changes which area the shunt is accounted to, not where it connects. To put a
shunt electrically inside an area, create it at a bus in that area.

### How to set any option object

Option objects (`Sim_Solution_Options`, `CTG_Options`, `OPF_Options`, `Distributed_Options`,
`Limit_Monitoring_Options`, `CTG_AutoInsert_Options`) are single-record and keyless.

- esapp: `pw.esa.SetData("CTG_Options", ["Field"], ["Value"])`, or the indexable
  `pw[Sim_Solution_Options, "Field"] = value`.
- aux / script: `SetData(CTG_Options, [Field], [Value]);`
- **Read the value back after every write.** `SetData` reports success on writes that change
  nothing ([opf-preconditions](../concepts/opf-preconditions.md)).
- Every option object has a `<Obj>_Value` twin (`VariableName` / `ValueField`), a name/value table
  form. Schema only; nothing here uses it.

- **The aux document never says how to address a keyless object.** It states that `SetData` with
  no filter needs key fields "to identify the one object", and `ALL` means every object. In
  practice keyless `SetData(Sim_Solution_Options, [f], [v]);` with no filter is used across these
  pages; the read-back is what proves each write, not the call returning.
- Field names: the aux parser accepts the variable name or the concise name.

**Precedence** (aux-file-format document, p.183): a contingency reads its solution options from
(1) its own `Contingency` record, then (2) `CTG_Options`, then (3) global `Sim_Solution_Options` —
global ranks **last**. Levels 1 and 2 are written in aux as a two-line
`<SUBDATA Sim_Solution_Options>` block (field names, then values) inside the record, or as the
`CTGSolutionOptions` string, which is enterable only via AUX/Paste.

### Every study at a glance

Commands with full parameters are on [powerworld-study-commands](powerworld-study-commands.md); every field of every option
object is on [powerworld-option-objects-v25](powerworld-option-objects-v25.md).

| study | option object(s) | run / control with |
|---|---|---|
| AC power flow | `Sim_Solution_Options`, `Limit_Monitoring_Options` | `SolvePowerFlow(RECTNEWT\|POLARNEWTON\|GAUSSSEIDEL\|FASTDEC\|ROBUST, okAux, failAux)`, `ResetToFlatStart`, `StoreState` / `RestoreState(USER\|BEFOREFAILED\|LASTSUCCESSFUL)` |
| DC power flow | `Sim_Solution_Options` (`DCPFModelType`) | `SolvePowerFlow(DC)` — the case **stays** DC until an AC method is used |
| contingency (N-1) | `CTG_Options`, `CTG_AutoInsert_Options`, `LimitSet`, `Distributed_Options` | `CTGAutoInsert`, `CTGSolveAll(DoDistributed, ClearAllResults)`, `CTGSetAsReference`, `CTGWriteResultsAndOptions` |
| N-1-1 / combo | `CTGPrimary_Options` | `CTGPrimaryAutoInsert`, `CTGComboSolveAll` |
| OPF | `OPF_Options`, plus `Area.BGAGC`, `Gen.GenAGCAble`, cost data | `InitializePrimalLP`, `SolvePrimalLP`, `SolveSinglePrimalLPOuterLoop` |
| SCOPF | `OPF_Options` (`SCOPF*`), `CTG_Options` | `SolveFullSCOPF(POWERFLOW\|OPF, …)` |
| unit commitment | `UC_Options` | options only; the aux document never mentions unit commitment |
| PTDF / LODF / shift factors | `PTDF_Options`, `LODF_Options`, `TLR_Options` | `CalculatePTDF`, `CalculateLODF`, `CalculateLODFMatrix`, `CalculateLODFScreening`, `CalculateShiftFactors` — LODF is DC/DCPS only |
| voltage and loss sensitivity | — | `CalculateVoltSense`, `CalculateVoltSelfSense`, `CalculateTapSense`, `CalculateLossSense` |
| ATC | `ATC_Options` | `ATCDetermine`, `ATCDetermineMultipleDirections` (opposite `DoMultipleScenarios` defaults) |
| PV / QV curves | `PVCurve_Options`, `QVCurve_Options` | `PVSetSourceAndSink`, `PVRun`, `QVRun` |
| scaling load or generation | `Scale_Options` | `Scale(LOAD\|GEN\|INJECTIONGROUP\|BUSSHUNT, MW\|FACTOR, [..], BUS\|AREA\|ZONE\|OWNER)` — only objects whose marker has `Scale = YES` |
| islands and topology | — | `DetermineBranchesThatCreateIslands`, `FindRadialBusPaths`, `DeterminePathDistance` |
| equivalencing | `Equiv_Options` | `Equivalence` (buses flagged `Equiv`) |
| fault | `Fault_Options` | `Fault`, `FaultAutoInsert` |
| time step | `Time_Step_Simulation_Options` | `TimeStepLoadPWW` (deletes existing timepoints; suspected glitch 2026-10-20-timestep-loadpww-plain: on builds dated 2026-09-20 and 2026-09-25 plain `TimeStepLoadPWW` failed with `Error With Loading PWWFile` while `TimeStepLoadPWWRange` loaded the same files; see [timestep-workflow](../concepts/timestep-workflow.md)), `TimeStepDoRun` |
| weather | `Weather_Options` | `WeatherPWWLoadForDateTimeUTC`, `WeatherPFWModelsSetInputsAndApply`, `TemperatureLimitsBranchUpdate` |
| scheduled actions | `ScheduledActions_Options` | `ApplyScheduledActionsAt`, `SetScheduleWindow` |

**Silent behaviours that break automation** (full list of 29 on [powerworld-study-commands](powerworld-study-commands.md)):

- `SetData` with no filter edits **one** object found by key fields; use `ALL` for every object.
  `Delete` with no filter deletes **every** object of the type.
- `CTGSolveAll` clears results of **skipped** contingencies too (`ClearAllResults` defaults YES).
- `CTGSolve` leaves the case in the post-contingency state; call `CTGRestoreReference`.
- `ResetToFlatStart` with defaults also sets **generator voltage setpoints** to 1.0 pu.
- `RestoreState(BEFOREFAILED)` vanishes after any later successful solve.
- `CTGAutoInsert`, `FaultAutoInsert`, `Equivalence` take no parameters: stale option values from
  an earlier session silently drive them.
- Contingencies run in creation order, not name order (`CTGSort` first).
- Most Save commands **append** by default.
- `CalculateShiftFactors` defaults to `AbortOnError = YES`, which stops the rest of the aux file.

**Provenance tags below:** **V** = a page records it confirmed on a live case · **D** = a page
states it, not live-tested · **S** = the field exists in the export with PowerWorld's
description; behaviour not tested here.

### A. Power flow — `Sim_Solution_Options`

| want | field | tag |
|---|---|---|
| more Newton iterations | `MaxItr` (inner loop) · `MaxItr:1` (voltage-control loop) | S |
| tolerance | `ConvergenceTol` (**per unit**: 0.1 MVA at 100 MVA base = 0.001) · `ConvergenceTol:2` (MVA) | S |
| controls on/off | `ChkTaps`, `ChkShunts`, `ChkShunts:1` (SVC), `ChkPhaseShifters`, `ChkVars` / `ChkVars:1` (gen Mvar check / back-off), `DisableGenMVRCheck`, `EnforceGenMWLimits` | S |
| stop oscillating controls | `PreventOscillations` | S |
| islands | `AllowMultIslands` (auto slack per island) · `EvalSolutionIsland` / `:1` | S |
| load model at low voltage | `MinVoltSLoad` / `MinVoltILoad` — **hides voltage collapse** by shedding load | V 2026-09-23 |
| flat start | `FlatStart` is **ignored by script solves** (PowerWorld's own description). Call `ResetToFlatStart` | S + D |
| DC power flow | script `SolvePowerFlow(DC)`, then check every `BusPUVolt == 1.0` | V |

⚠️ **`DCPFMode` (concise name `DCApprox`) is one field, and writing it is not enough.** Measured
2026-09-23 on a live case: `DCApprox = YES` did **not** make
`SolvePowerFlow()` run DC. Only `SolvePowerFlow(DC)` is verified. Any DC-contingency or DC-SCOPF
sequence that relies on the flag alone may have run an AC base case.

### B. Contingency — `CTG_Options`, `LimitSet`, `Area`

| want | object.field | tag |
|---|---|---|
| AC or DC contingency | `CTG_Options.CTG_CalculationMethod` = `AC` / `DC` / `DCPS`. In DC power-flow mode only `AC` is offered and contingencies are evaluated by sensitivities, not applied | S, used live |
| base-case violations | `CTG_WhatToDoWithBC`: 0 don't report · 1 report all · 2 change-from-base | V (Synth2k) |
| voltage band post-CTG | `LimitSet.LSCtgPULow` / `LSCtgPUHigh` — `SetData` needs the full row | V |
| rate set | `LimitSet.LSLineRateSet` (normal) / `LSLineRateSet:1` (CTG) | V 2026-08-17 |
| which areas are monitored | `Area.BGReportLimits`. `CTG_ReportMonitoredAreas` is a **decoy** (text report only) | V 2026-08-17 |
| report disconnected buses | `CTG_BCDiscBusReporting` | S |
| ignore radial elements | `Limit_Monitoring_Options.LMS_IgnoreRadial` | S |
| **report islanding** | `CTG_Options.Include` (concise `IslandViolations`) = YES; filters `BGLoadMW` (min island load) and `IslandTotalBus` (min buses). Needs `Sim_Solution_Options.EvalSolutionIsland = YES` | D, fires live |
| solver settings during CTG | `CTG_Options.CTGSolutionOptions` = `"MaxItr = 200, ChkShunts = NO"` (Sim_Solution_Options names) + `CTGUseSolutionOptions = YES`. **Enterable only via AUX/Paste** | S |
| same, one contingency | `Contingency.CTGSolutionOptions` (AUX/Paste) + `Contingency.CTGUseSolutionOptions`; `CTGIgnoreSolutionOptions` overrides both | S |
| make-up power | `CTG_Options.UseAreaPartsMakeUpPower` | S |
| DC pre-screen before AC | `ScreenAllow` (NO / YES / OnlyScreen), `ScreenMethod` (DC / DCPS), `ScreenNum` … `:3` | S |
| aux before/after each CTG | `CtgFileName:1` / `CtgFileName:2` | S |
| results persist in .pwb | `CTGSaveInPWB` — they do persist; clear before a fresh run | V (trap) |
| PowerWorld distributed CTG | `Distributed_Options.CTGUseDistributedComputing`, `CTGNumberPerProcess` — silently degrades to serial without a DS server; see [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) | D |

**Islands: no single check covers them all** (measured 2026-09-28, regional synthetic planning
model). `Contingency.LoadMW` / `GenMW` catch islands PowerWorld **drops**; `CTG_Options.Include`
fires "Island Solved" rows for self-sustaining pockets it keeps **energized**; the script
`DetermineBranchesThatCreateIslands` catches both plus 0-MW pockets. Gate an island check on MW
only when the pocket carries MW. `Contingency.LoadMW:2` is load lost to the `MinVoltSLoad` model,
not to islanding — read it separately.

**Building the set** — `CTG_AutoInsert_Options`: `ElementType` is `BRANCH` or `GENERATOR`, never
`GEN` (silently ignored; suspected, possibly by design: glitch `2026-10-20-ctgautoinsert-gen-ignored`). On the
Simulator 25 beta build used 2026-09-28, `CTGAutoInsert` inserted **zero** contingencies with no error (suspected,
glitch `2026-10-20-ctgautoinsert-zero-insert`): always count the result against lines plus
two-winding transformers.

### C. OPF

| want | object.field / command | tag |
|---|---|---|
| area under OPF | `Area.BGAGC = "OPF"` (values: Off AGC, Part. AGC, ED, Area Slack, IG Slack, OPF) | V 2026-09-11 |
| super area under OPF | `SuperArea.BGAGC` — value vocabulary not in the export | S |
| movable gens | `Gen.GenAGCAble = "YES"`; writing a changed `GenMW` has been seen to turn it off (suspected, glitch `2026-10-20-genmw-write-clears-agc`), so set it after MW writes | V |
| cost data | `Gen.GenCostModel` ≠ None with `GenCostCurvePoints > 0` or `GenMCost > 0` (a cost above 0 at today's output; see the 2026-10-01 note in `concepts/opf-preconditions.md`) — **data, never fabricated** | V |
| run LP OPF | `InitializePrimalLP("", STOP); SolvePrimalLP("", STOP);` | V 2026-09-24 (AC, public 40-bus) |
| DC OPF | DC mode first (`SolvePowerFlow(DC)`), then `SolvePrimalLP` | D |
| LP iterations | `OPF_Options.OPF_MaxLPIterations`; `OPFValidSolutionOnMaxITR` accepts the answer at the cap | S |
| drop constraint classes | `OPF_DisLineEnforce`, `OPF_DisIntEnforce`, `OPFDisBusEnforce`, `OPF_DisDCLineMW`, `OPF_DisAreaTrans` | S |
| soft-limit penalties | `OPF_LineMaxViolCost`, `OPF_IntMaxViolCost`, `OPF_LineCorrectTol` | S |
| results | `OPFSolutionSummary` (`LPOPFCostFunction:1` is final cost; bare is initial) · `Branch.LineLPUnenforceableMVA` | S / V |

### D. SCOPF

| want | object.field / command | tag |
|---|---|---|
| run | `SolveFullSCOPF(POWERFLOW, "", STOP)` or `(OPF, …)` | D (public 40-bus, undated) |
| more outer loops | `OPF_Options.SCOPFMaxOuterLoopItr` (re-dispatch, re-find binding contingencies; 3 in the reference sequence) | D + S |
| base case start | `SCOPFBaseCaseMethod`: 0 = power flow, 1 = OPF | S |
| constraints per CTG | `SCOPFMaxElementCTGViol` | S |
| radial-load CTG violations | `SCOPFRadialLoad`: 0 flag · 1 ignore · 2 include | S |
| warm start | `SCOPFUseMustInclude`, `OPFUseLastTableau` | S |
| keep result as CTG reference | `SCOPFSetSolutionCARef` | S |
| reuse LODFs | `CTG_Options.CTGStoreLODFS` (0 none, 1 memory) | S |
| DC SCOPF | `CTG_CalculationMethod = DC` **and** the case genuinely in DC mode (`SolvePowerFlow(DC)`, see the ⚠️ in A) | not verified |

**There is no SCOPF "inner loop" count.** The export has `SCOPFMaxOuterLoopItr` and the per-LP
`OPF_MaxLPIterations`, nothing else. `SCOPFOuterLoopType` exists but its values are undocumented.

### E. After the run

- Read violations with an explicit field list — `pw[ViolationCTG, fields]`, never bare. Watch
  `LimViolCat` (`Unsolved` is not a violation) and `AreaNum = 0` on tie lines
  ([reading-violationctg](../methods/reading-violationctg.md)).
- Rank devices by how far past the limit their outages push things
  ([ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md)).
- Shrink the set: `CTGSkip` only partitions; `Delete(Contingency, "CTGViol = 0")` reduces. Back
  up with `CTGWriteAuxUsingOptions` first ([reducing-a-contingency-set](../methods/reducing-a-contingency-set.md)).
- Screen fast with LODFs before a full AC run ([lodf](../concepts/lodf.md)).

### Gaps — nothing here documents these

- Value vocabularies for `SCOPFOuterLoopType`, `OPF_GenCostModel`, `OPF_LoadControlPFOption`,
  `SuperArea.BGAGC` — the export's description is only the field name.
- An AC or DC SCOPF verified end to end, with a date.
- Post-contingency governor response, load throw-over and switched-shunt behaviour beyond
  `UseAreaPartsMakeUpPower`.
- OPF reserve requirement and bid fields beyond `OPFIncludeReserveRequirements`.
- The meaning of the `<` marker and key suffixes like `*2B*` in the export.
