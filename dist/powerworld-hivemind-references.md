# PowerWorldHiveMind - REFERENCES

# ==== aux-script-commands.md ====

---
type: reference
domain: tooling
topic: scripting
aliases: [aux-script-commands, script-commands, aux-actions, script-action-index, powerworld-script-actions]
tags: [powerworld, aux, script, commands, reference, simauto]
---

# Reference: PowerWorld SCRIPT actions — working subset

## Abstract

A task-organized index of the PowerWorld SCRIPT actions this kit's workflows actually
use, plus their close neighbours — 198 of the ~370 that Simulator defines. Look
here to find *which* command does a job; look in Simulator's own *Auxiliary File Format*
manual for argument lists and exact syntax, which this page deliberately does not
reproduce. To run one from Python, call the esapp method of the same name; use
`pw.esa.RunScriptCommand("ActionName(args)")` only where none exists
([esapp-script-command-wrappers](../concepts/esapp-script-command-wrappers.md)). In an `.aux`
file, put it inside a `SCRIPT { }` block. Start at [esapp-overview](../methods/esapp-overview.md) for the
Python side.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](../concepts/esapp.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [esapp-schema-reference](esapp-schema-reference.md)
- **Deeper:** [esapp-package-backend](esapp-package-backend.md)

## Content

> **Descriptions here are written for this kit, not copied from PowerWorld's
> documentation.** They say what a command is *for* in the context of these workflows.
> For argument order, optional parameters, and filter syntax, consult Simulator's
> *Auxiliary File Format* manual — it ships with the program under Help, and it is the
> authority. Where this page and the manual disagree, the manual is right.

### How a script action is invoked

```python
pw.esa.RunScriptCommand('SolvePowerFlow(RECTNEWT)')
pw.esa.RunScriptCommand('SaveCase("C:\\out\\case.pwb", PWB)')
```

Two rules that cause most first-attempt failures, both documented at
[save-powerworld-case](../methods/save-powerworld-case.md) and [new-device-contingency-aux](../methods/new-device-contingency-aux.md):

- File paths must be **absolute**. A relative path resolves against Simulator's current
  working directory, which is not your script's.
- `LoadAux` **merges** into the open case rather than replacing it. Loading the same aux
  twice duplicates its objects.

---

### Opening, saving, and case lifecycle

| Action | What it is for |
|---|---|
| `OpenCase` | Open a `.pwb` from disk, replacing whatever is loaded |
| `NewCase` | Start from an empty case |
| `AppendCase` | Merge a second case into the open one |
| `SaveCase` | Write the case to disk. **Use this, not the COM `SaveCase`** — see [save-powerworld-case](../methods/save-powerworld-case.md) |
| `EnterMode` | Switch between `RUN` and `EDIT`. Many data writes are rejected outside `EDIT` |
| `Scale` | Scale load, generation, or injection by a factor or to a target total |
| `Equivalence` | Reduce the case to an equivalent of the retained subsystem |
| `DeleteExternalSystem` | Drop everything outside the retained area/zone selection |
| `SaveExternalSystem` | Write the external subsystem out separately |
| `LoadEMS` | Read an EMS-format snapshot |
| `RenumberBuses` | Renumber buses en masse — changes key fields, so re-read any DataFrame you held |
| `RenumberAreas`, `RenumberZones`, `RenumberSubs` | Same, for those container types |
| `RenumberCase` | Apply a renumbering scheme across the whole case |
| `Renumber3WXFormerStarBuses` | Renumber the hidden star buses inside three-winding transformers |
| `CaseDescriptionSet`, `CaseDescriptionClear` | Set or clear the case's description text |

### Reading and writing data

| Action | What it is for |
|---|---|
| `SetData` | Write field values on existing objects. **Requires the entire key-field row** or it errors — see [powerworld-limitset-setdata](../methods/powerworld-limitset-setdata.md) |
| `CreateData` | Create new objects (buses, branches, loads, generators) — see [adding-devices-esapp](../methods/adding-devices-esapp.md) |
| `SetElseCreateData` | Set one object's fields if it exists, else create it from defaults. The aux language's only exists-check — see [aux-only-powerworld](../concepts/aux-only-powerworld.md). Added September 2026; older Simulator 24 builds will not have it |
| `Delete` | Delete objects of a type matching a filter |
| `DeleteDevice` | Delete one specific device |
| `DeleteIncludingContents` | Delete a container and everything inside it |
| `LoadAux` | Read an `.aux` file into the case. Absolute path; **merges** |
| `LoadAuxDirectory` | Load every aux in a directory |
| `LoadCSV`, `LoadData`, `ImportData` | Bulk-import records from CSV or another data source |
| `LoadScript` | Run a named `SCRIPT` block from an aux file |
| `SaveData` | Export a table of objects and chosen fields to file |
| `SaveDataWithExtra` | Same, with additional computed columns |
| `SaveDataUsingBuiltInAUXFormat` | Export as aux using Simulator's own field layout |
| `SaveDataUsingExportFormat` | Export using a named custom format |
| `SaveDataEPC` | Export in EPC format |
| `SaveObjectFields` | Write out which fields exist for an object type |
| `SelectAll`, `UnSelectAll` | Set or clear the `Selected` flag, which many other actions filter on |
| `SendtoExcel` | Push a table to Excel. Note the lowercase `t` — the obvious spelling fails |
| `WriteLimitMonitoringSettings` | Dump the current limit-monitoring configuration |

### Solving power flow

| Action | What it is for |
|---|---|
| `SolvePowerFlow` | Solve. Takes the method: `RECTNEWT`, `POLARNEWTON` (often written `POLARNEWT`; see [powerworld-study-commands](powerworld-study-commands.md)), `GAUSSSEIDEL`, `FASTDEC`, `DC` |
| `ResetToFlatStart` | Reset voltages to 1.0 pu / 0 degrees before a hard solve |
| `EstimateVoltages` | Seed a starting voltage profile when flat start will not converge |
| `ZeroOutMismatches` | Force mismatches to zero — diagnostic, not a fix |
| `UpdateIslandsAndBusStatus` | Recompute island membership and energization after topology edits |
| `VoltageConditioning`, `ConditionVoltagePockets` | Repair local voltage anomalies that block convergence |
| `InitializeGenMvarLimits` | Reset generator reactive limits to their defined values |
| `GenForceLDC_RCC` | Force line-drop / reactive-current compensation behaviour |
| `SaveJacobian` | Write the Jacobian matrix to file |
| `SaveYbusInMatlabFormat` | Write Ybus in MATLAB format |
| `StoreState`, `RestoreState`, `DeleteState` | Snapshot and roll back a solved state. Cheaper than reloading the case between scenarios |
| `ClearPowerFlowSolutionAidValues` | Clear stored solution aids |

**A DC solve always reports zero mismatch.** It cannot tell you that your generation
schedule is short — the slack bus absorbs it silently. Check the schedule against total
load directly. See [applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md).

### Contingency analysis

| Action | What it is for |
|---|---|
| `CTGSolveAll` | Solve every active contingency. The workhorse |
| `CTGSolve` | Solve one named contingency |
| `CTGApply` | Apply a contingency's actions to the case without solving |
| `CTGAutoInsert` | Generate a contingency set automatically from the case topology |
| `CTGPrimaryAutoInsert` | Auto-insert primary contingencies only |
| `CTGRestoreReference` | Return the case to its pre-contingency reference state |
| `CTGSetAsReference` | Mark the current state as the reference base |
| `CTGClearAllResults` | Clear stored results. **Do this first** — results persist stale inside the `.pwb`, see [reading-violationctg](../methods/reading-violationctg.md) |
| `CTGProduceReport` | Write a formatted violation report |
| `CTGSaveViolationMatrices` | Export the violation matrices |
| `CTGWriteResultsAndOptions` | Write results plus the option set that produced them |
| `CTGWriteAuxUsingOptions` | Emit the contingency definitions as an aux file |
| `CTGSort` | Sort the contingency list |
| `CTGCloneOne`, `CTGCloneMany` | Duplicate contingency definitions |
| `CTGDeleteWithIdenticalActions`, `CTGSkipWithIdenticalActions` | Remove or skip duplicates by action set |
| `CTGConvertAllToDeviceCTG`, `CTGConvertToPrimaryCTG` | Convert between contingency representations |
| `CTGCreateStuckBreakerCTGs`, `CTGCreateExpandedBreakerCTGs` | Build breaker-failure contingencies |
| `CTGCreateContingentInterfaces` | Create interfaces defined by contingency outcomes |
| `CTGRelinkUnlinkedElements` | Re-bind contingency elements whose keys stopped resolving |
| `CTGJoinActiveCTGs` | Combine active contingencies into one |
| `CTGComboSolveAll`, `CTGComboDeleteAllResults` | Solve or clear combination contingencies |
| `CTGCalculateOTDF` | Outage transfer distribution factors |
| `CTGCompareTwoListsofContingencyResults` | Diff two result sets |
| `CTGProcessRemedialActionsAndDependencies` | Evaluate remedial action schemes |
| `CTGVerifyIteratedLinearActions` | Validate iterated linear contingency actions |
| `CTGReadFilePTI`, `CTGReadFilePSLF`, `CTGWriteFilePTI` | Exchange contingency sets with PSS/E and PSLF |
| `CTGWriteAllOptions` | Dump every contingency analysis option |
| `DoCTGAction` | Execute a single contingency action directly |

Building a contingency set for a chosen device list is its own procedure with several
silent failure modes (`ElementType=GEN` is ignored; the action string must be quoted;
labels get whitespace-trimmed on load) — see [new-device-contingency-aux](../methods/new-device-contingency-aux.md).

### Timestep simulation and weather

| Action | What it is for |
|---|---|
| `TimeStepLoadPWW` | Load a `.pww` weather file for the simulation. Suspected glitch 2026-10-20-timestep-loadpww-plain: on builds dated 2026-09-20 and 2026-09-25 plain `TimeStepLoadPWW` failed with `Error With Loading PWWFile` while `TimeStepLoadPWWRange` loaded the same files; see [timestep-workflow](../concepts/timestep-workflow.md) |
| `TimeStepLoadPWWRange` | Load a time range from a PWW |
| `TimeStepLoadPWWRangeLatLon` | Load a time range cropped to a lat/lon box — the usual entry point |
| `TimeStepAppendPWW`, `TimeStepAppendPWWRange`, `TimeStepAppendPWWRangeLatLon` | Append further weather to what is already loaded |
| `TimeStepLoadTSB`, `TimeStepLoadB3D` | Load time-series data in TSB or B3D format |
| `TimeStepDoRun` | Run the full time-step simulation |
| `TimeStepDoSinglePoint` | Solve one time point only — use this to debug setup before a long run |
| `TimeStepClearResults`, `TimeStepDeleteAll` | Clear results, or clear the whole time-step definition |
| `WeatherPWWSetDirectory` | Point Simulator at the directory holding PWW files |
| `WeatherPWWLoadForDateTimeUTC` | Load weather for a specific UTC timestamp |
| `WeatherPWWFileCombine2` | Merge two PWW files |
| `WeatherPWWFileGeoReduce` | Crop a PWW geographically — do this before loading, not after |
| `WeatherPWWFileAllMeasValid` | Check that all measurements in a PWW are valid |
| `TemperatureLimitsBranchUpdate` | Update branch thermal limits from temperature — the dynamic line rating hook |
| `WeatherLimitsGenUpdate` | Update generator limits from weather |
| `WeatherPFWModelsSetInputs` | Set inputs on PFW renewable models |
| `WeatherPFWModelsSetInputsAndApply` | Set and apply them in one step |
| `WeatherPFWModelsRestoreDesignValues` | Restore PFW models to design values |

`PWW` (PowerWorld Weather data) and `PFW` (the renewable output model) are different
things with confusingly similar names. See [pww-data](../concepts/pww-data.md).

### Modifying case objects

| Action | What it is for |
|---|---|
| `ChangeSystemMVABase` | Change the system base. Re-derives per-unit quantities — see [per-unit-basis-discipline](../concepts/per-unit-basis-discipline.md) |
| `CalculateRXBGFromLengthConfigCondType` | Derive branch R/X/B/G from length, configuration, and conductor type |
| `CreateLineDeriveExisting` | Create a line by deriving parameters from an existing one |
| `TapTransmissionLine` | Tap a line to insert a new bus |
| `SplitBus`, `MergeBuses` | Split one bus into two, or merge two into one |
| `MergeLineTerminals`, `MergeMSLineSections` | Merge line terminals or multi-section line segments |
| `ClearSmallIslands` | Remove islands below a size threshold |
| `RotateBusAnglesInIsland` | Rotate all angles in an island to a new reference |
| `SetScheduledVoltageForABus` | Set a bus's scheduled voltage setpoint |
| `SetParticipationFactors` | Set generator participation factors for AGC-style dispatch |
| `SetGenPMaxFromReactiveCapabilityCurve` | Derive generator MW max from its capability curve |
| `BranchMVALimitReorder` | Reorder branch MVA limit sets |
| `InjectionGroupCreate`, `InjectionGroupsAutoInsert` | Create injection groups by hand or automatically |
| `InjectionGroupRemoveDuplicates`, `RenameInjectionGroup` | Maintain injection groups |
| `InterfaceCreate`, `InterfacesAutoInsert` | Create interfaces by hand or automatically |
| `InterfaceAddElementsFromContingency` | Build an interface from a contingency's elements |
| `InterfaceFlatten`, `InterfaceFlattenFilter` | Flatten nested interface definitions |
| `InterfaceRemoveDuplicates`, `InterfaceModifyIsolatedElements` | Maintain interfaces |
| `SetInterfaceLimitToMonitoredElementLimitSum` | Set an interface limit from the sum of its elements' limits |
| `DirectionsAutoInsert`, `DirectionsAutoInsertReference` | Auto-create transfer directions |
| `AutoInsertTieLineTransactions` | Auto-create tie-line transactions |
| `SuperAreaAddAreas`, `SuperAreaRemoveAreas` | Manage super-area membership |
| `Remove3WXformerContainer` | Remove a three-winding transformer container |
| `ReassignIDs` | Reassign object IDs |
| `Move` | Move an object to a different container |

Reclassifying a line as a transformer is not done here — `BranchDeviceType` is derived,
so you set `LineXFMR` instead. See [converting-lines-to-transformers](../methods/converting-lines-to-transformers.md).

### Sensitivities

| Action | What it is for |
|---|---|
| `CalculatePTDF` | Power transfer distribution factors for one direction — see [lodf](../concepts/lodf.md) |
| `CalculatePTDFMultipleDirections` | PTDFs for several directions at once |
| `CalculateLODF` | Line outage distribution factors for one outage |
| `CalculateLODFMatrix` | The full LODF matrix |
| `CalculateLODFAdvanced` | LODFs with extended options |
| `CalculateLODFScreening` | LODF-based screening pass — the cheap first cut in critical branch screening |
| `CalculateShiftFactors` | Shift factors for a transfer |
| `CalculateShiftFactorsMultipleElement` | Shift factors across several elements |
| `CalculateFlowSense` | Sensitivity of a flow to injections |
| `CalculateVoltSense`, `CalculateVoltSelfSense` | Sensitivity of voltage to injections |
| `CalculateVoltToTransferSense` | Sensitivity of voltage to a transfer |
| `CalculateLossSense` | Sensitivity of losses to injections |
| `CalculateTapSense` | Sensitivity to transformer tap position |
| `SetSensitivitiesAtOutOfServiceToClosest` | Fill sensitivities at out-of-service elements from the nearest in-service one |
| `LineLoadingReplicatorCalculate`, `LineLoadingReplicatorImplement` | Compute then apply a loading pattern that reproduces target flows |

### Optimal power flow

| Action | What it is for |
|---|---|
| `SolvePrimalLP` | Solve the LP OPF |
| `InitializePrimalLP` | Initialize before solving |
| `SolveSinglePrimalLPOuterLoop` | Run one outer-loop iteration — useful for diagnosing non-convergence |
| `SolveFullSCOPF` | Solve the security-constrained OPF |
| `OPFWriteResultsAndOptions` | Write OPF results and the options used |

### PV and QV analysis

| Action | What it is for |
|---|---|
| `PVSetSourceAndSink` | Define the transfer's source and sink before running |
| `PVRun` | Run the PV (nose curve) study |
| `PVStartOver`, `PVClear`, `PVDestroy` | Restart or tear down a PV study |
| `PVWriteResultsAndOptions`, `PVDataWriteOptionsAndResults` | Write PV results |
| `PVWriteInadequateVoltages` | Report buses whose voltage is inadequate along the curve |
| `PVQVTrackSingleBusPerSuperBus` | Track one representative bus per super bus |
| `QVRun` | Run the QV study |
| `QVSelectSingleBusPerSuperBus` | Select one bus per super bus for QV |
| `QVWriteCurves` | Write the QV curves |
| `QVWriteResultsAndOptions`, `QVDataWriteOptionsAndResults` | Write QV results |
| `QVDeleteAllResults` | Clear QV results |
| `RefineModel` | Refine the model between study passes |

### Transient stability

| Action | What it is for |
|---|---|
| `TSInitialize` | Initialize dynamics from the solved power flow |
| `TSSolve` | Run one transient stability contingency |
| `TSSolveAll` | Run all of them |
| `TSSolveContinue` | Resume a paused contingency from a SnapShot or Restore Time Point. Added December 2025, Simulator 25 |
| `TSRunUntilSpecifiedTime` | Advance the run to a given time, then stop — manual stepping |
| `TSGetResults` | Retrieve results into memory |
| `TSGetVCurveData` | Retrieve V-curve data |
| `TSCalculateCriticalClearTime` | Compute critical clearing time |
| `TSCalculateSMIBEigenValues` | Single-machine-infinite-bus eigenvalues |
| `TSValidate`, `TSAutoCorrect` | Validate dynamic models, and auto-correct what can be fixed |
| `TSClearAllModels`, `TSClearModelsforObjects` | Remove dynamic models |
| `TSClearResultsFromRAM` | Free result memory between runs |
| `TSResultStorageSetAll` | Choose which quantities are stored |
| `TSLoadPTI`, `TSLoadGE`, `TSLoadBPA`, `TSLoadRDB` | Import dynamic models from other formats |
| `TSSavePTI`, `TSSaveGE`, `TSSaveBPA` | Export dynamic models |
| `TSSaveDynamicModels`, `TSWriteModels` | Write the model set out |
| `TSSaveTwoBusEquivalent` | Save a two-bus equivalent |
| `TSTransferStateToPowerFlow` | Push the dynamic state back into the power flow case |
| `TSAutoInsertDistRelay`, `TSAutoInsertZPOTT` | Auto-insert distance and POTT relay models |
| `TSAutoSavePlots`, `TSPlotSeriesAdd` | Manage transient plots |
| `TSRunResultAnalyzer` | Run the result analyzer |
| `TSJoinActiveCTGs` | Join active contingencies for TS |
| `TSDisableMachineModelNonZeroDerivative` | Disable machine models with non-zero initial derivatives |
| `TSSetSelectedForTransientReferences` | Set the selected flag for transient reference objects |
| `TSWriteOptions` | Dump TS options |

### Geomagnetically induced current

| Action | What it is for |
|---|---|
| `GICCalculate` | Run the GIC calculation for a uniform field — see [gic](../concepts/gic.md) |
| `GICClear` | Clear GIC results |
| `GICSensitivitiesCalculate` | Recalculate GIC sensitivities — Line Amp Input or Transformer Ieffective. Added March 2026, Simulator 25 |
| `GICLoad3DEfield` | Load a 3-D electric field |
| `GICTimeVaryingCalculate` | Run GIC over a time-varying field |
| `GICTimeVaryingEFieldCalculate` | Compute the time-varying E-field itself |
| `GICSetupTimeVaryingSeries` | Set up the time series |
| `GICTimeVaryingAddTime` | Add a time point |
| `GICTimeVaryingDeleteAllTimes`, `GICTimeVaryingElectricFieldsDeleteAllTimes` | Clear time points or fields |
| `GICShiftOrStretchInputPoints` | Shift or stretch the input series in time |
| `GICSaveGMatrix` | Save the G matrix |
| `GICReadFilePTI`, `GICReadFilePSLF`, `GICWriteFilePTI`, `GICWriteFilePSLF` | Exchange GIC data with PSS/E and PSLF |
| `GICWriteOptions` | Dump GIC options |

### Case comparison

| Action | What it is for |
|---|---|
| `DiffCaseSetAsBase` | Mark the open case as the comparison base |
| `DiffCaseMode` | Turn difference mode on or off |
| `DiffCaseKeyType` | Choose how objects are matched between cases |
| `DiffCaseRefresh` | Recompute the comparison |
| `DiffCaseShowPresentAndBase` | Show present and base values side by side |
| `DiffCaseClearBase` | Clear the base case |
| `DiffCaseWriteCompleteModel` | Write the full differenced model |
| `DiffCaseWriteNewEPC`, `DiffCaseWriteRemovedEPC`, `DiffCaseWriteBothEPC` | Write added, removed, or both as EPC |

### Program and file housekeeping

| Action | What it is for |
|---|---|
| `SetCurrentDirectory` | Set Simulator's working directory. Prefer absolute paths over relying on this |
| `CopyFile`, `DeleteFile` | Copy or delete a file from inside a script |
| `WriteTextToFile` | Write arbitrary text to a file |
| `LogAdd`, `LogAddDateTime`, `LogClear`, `LogSave`, `LogShow` | Message-log control — `LogSave` is the cheapest way to capture what a long script did |
| `StopAuxFile` | Treat the rest of the aux file as a comment |
| `ExitProgram` | Exit Simulator immediately, without prompting |

### What this page leaves out

Simulator defines roughly 370 SCRIPT actions. Omitted here as outside this kit's scope:
oneline and user-interface actions, fault analysis, ATC, integrated topology processing,
regions, scheduled actions, distributed computing, the trainer, and customer-specific
actions. If you need one of those, the *Auxiliary File Format* manual lists them by the
same category names used above.


---

# ==== esapp-package-backend.md ====

---
type: reference
domain: tooling
topic: scripting
aliases: [esapp-backend, esapp-internals]
tags: [esapp, powerworld, simauto, internals, backend, reference]
---

# ESA++ (esapp) — Package Backend / Internals Reference

## Abstract

Internals reference for the esapp package project, covering bracket-interface mechanics (`Indexable.__getitem__`/`__setitem__`), SAW mixin composition, the component-generation pipeline, GObject schema model, embedded utility apps (`Network`, `GIC`, `BusCat`), descriptors, and the exception hierarchy. This is the heavy/deep layer — read it in full only when writing or regenerating code for esapp package; for the gist, use [esapp](../concepts/esapp.md).

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](../concepts/esapp.md) (API-usage map for callers), [powerworld-simauto](../concepts/powerworld-simauto.md), [aux-script-commands](aux-script-commands.md) (SCRIPT command names)

## Content

**Scope:** how `esapp` works *inside* and how to *extend* it — bracket-interface
mechanics, the SAW mixin assembly, the component-generation pipeline, the GObject
schema model, embedded utility apps, descriptors, and the exception hierarchy. This
is the INTERNALS companion to the API-usage map in [esapp](../concepts/esapp.md); it does not re-document
user-facing call recipes. Hub is
[Home](../index.md).

All file:line citations are against the real source under `C:\path\to\esapp`.

---

## 1. Object graph (who owns whom)

```
PowerWorld(Indexable)            workbench.py:22   — user entry point
 ├── .esa : SAW                  set in Indexable.open() indexable.py:50
 │    └── SAW(SAWBase, *mixins)  saw/saw.py:28      — ~20 mixins composed
 ├── .network : Network(self)    workbench.py:36    — utils/network.py
 ├── .gic     : GIC(self)        workbench.py:37    — utils/gic.py
 └── .buscat  : BusCat(self)     workbench.py:38    — utils/buscat.py
```

`PowerWorld` **subclasses** `Indexable` (so `pw[...]` works directly), and **holds**
a `SAW` instance as `self.esa`. The embedded apps each keep a back-reference to the
`PowerWorld` instance (`self._pw`) and delegate all data access through it — they
never open their own COM connection.

`PowerWorld.__init__` (workbench.py:26–45) instantiates the three apps *first*, then
either opens the case (`self.open()`, inherited from `Indexable`) or leaves
`self.esa = None`. `Indexable.open()` (indexable.py:25–50) absolutizes/validates the
path and constructs `SAW(self.fname, CreateIfNotFound=True, early_bind=True)` — note
**`CreateIfNotFound=True` is hard-wired here**, which is what makes the bracket-write
create path possible (see §3).

---

## 2. `Indexable` — bracket read/write mechanics

File: `esapp/indexable.py`. `Indexable` is a mixin-style base with two declared
attributes (`esa: SAW`, `fname: str`) and the bracket protocol. Both `PowerWorld`
and `SAW` are described as implementing indexable access, but the read/write logic
lives here and is backed by SAW data methods.

### 2.1 `__getitem__` (read) — indexable.py:52–113

Index forms and how they resolve:

| Index | `requested_fields` | Fields fetched |
|---|---|---|
| `pw[Bus]` | `None` | `set(gtype.keys())` only |
| `pw[Bus, :]` | `slice(None)` | keys ∪ `gtype.fields()` (all) |
| `pw[Bus, "BusPUVolt"]` | str | keys ∪ {field} |
| `pw[Bus, ["a","b"]]` | list | keys ∪ {a,b} |
| `pw[Bus, Bus.PUVolt]` | a `GObject` member | uses `field.value[1]` (the PW field string) |

Mechanics (verbatim flow):
1. Unpack `index` into `(gtype, requested_fields)` (tuple) or `(gtype, None)`.
2. `fields_to_get = set(gtype.keys())` — **always starts from primary keys.**
3. A bare `GObject` member in the field list is resolved via `field.value[1]`
   (the field-name string carried in the enum value tuple — see §5).
4. A `slice` other than `[:]` raises `ValueError("Only the full slice [:] is
   supported...")`.
5. Returns `self.esa.GetParamsRectTyped(gtype.TYPE(), sorted(list(fields_to_get)))`.

So **every read is backed by `SAW.GetParamsRectTyped`** (data.py:324–362), which
calls COM `GetParamsRectTyped` with `pythoncom.VT_VARIANT` to preserve native typing,
and returns a `DataFrame(output, columns=ParamList)` or `None`. Fields are passed
**sorted**, so column order in the returned DataFrame is alphabetical, not request
order.

### 2.2 `__setitem__` (write) — indexable.py:115–173

Two dispatch cases:

- **Case 1 — bulk** `pw[GObject] = DataFrame`: `args` is a `type` subclassing
  `GObject` → `_bulk_update_from_df(args, value)`.
- **Case 2 — broadcast** `pw[GObject, field(s)] = value`: `args` is a 2-tuple →
  normalizes `fields` to a list and calls `_broadcast_update_to_fields(gtype, fields, value)`.
- Anything else → `TypeError`.

### 2.3 `_bulk_update_from_df` — indexable.py:148–197 (the create path)

This is the load-bearing method. Flow **as of 0.2.1** (line numbers against the 0.2.1
`indexable.py`; the 0.1.x layout this section used to describe is noted inline):

1. Reject non-DataFrame `value` with `TypeError`.
2. **The write funnel:** `df = self._prepare_write(gtype, df)` (`:212`) — normalizes
   `GObject`-member columns to field-name strings, calls `_warn_unsettable` (`:199`), then
   `_serialize_bools` (`:226`). The caller's DataFrame is never mutated.

   > ⚠️ **This is no longer a gate.** Through 0.1.x it was: a read-only column raised
   > `ValueError("Cannot set read-only field(s)...")` *before* any COM call, so esapp never
   > asked PowerWorld. In 0.2.1 `_warn_unsettable` only emits `warnings.warn` — once for
   > unknown fields, once for read-only ones — and **the write proceeds regardless**, on the
   > stated principle that "PowerWorld is the authority, and the generated schema may lag the
   > installed Simulator version." Consequences: a field-name typo no longer raises, and the
   > read-only warning is a false alarm on ~150 fields (§5).

   `is_settable` = key ∪ secondary ∪ editable (see §5).
3. Fast path: `self._send_rect(gtype, df)` (`:274`) →
   `self.esa.ChangeParametersMultipleElementRect(gtype.TYPE(), df.columns.tolist(), df)` —
   one COM round-trip (data.py:88–121). A `PowerWorldError` here is re-raised through
   `_raise_with_edit_hint` (`:263`), which appends *"field(s) [...] are only enterable in
   EDIT mode — call esa.EnterMode('EDIT') first"* when any touched field carries the
   `EDIT_MODE` flag.
4. **Create fallback keyed off the exception type:** wrapped in
   `except PowerWorldPrerequisiteError as e:` and `if "not found" in str(e).lower():`
   - Check `gtype.key_sets()` — the primary keys first, then any `ALT_KEY_SETS` alternates
     registered for the type. If **no** complete key set is a subset of `df.columns` →
     `ValueError` naming the missing fields and every accepted key set. (0.1.x compared
     against `gtype.keys()` alone; alternate key sets are new.) Secondary keys are *not*
     required.
   - Else fall back to `ChangeParametersMultipleElement(type, cols, values)` (the
     row-by-row variant, data.py:54–86), which **creates** objects when
     `CreateIfNotFound=True` **and** PowerWorld is in **EDIT mode**. A second
     `"not found"` `PowerWorldPrerequisiteError` from this call is **swallowed**
     (expected for freshly created rows); any other message re-raises.
   - Any non-`"not found"` `PowerWorldPrerequisiteError` re-raises immediately.

This is the concrete answer to "where bracket-write keys off `PowerWorldPrerequisiteError`":
indexable.py:233–253. The classification "not found" → `PowerWorldPrerequisiteError`
is decided in `PowerWorldError.from_message` (see §6); the bracket layer then string-matches
`"not found"` again to distinguish the create case from other prerequisite failures.

> Prerequisites for the create path to actually create: `SAW(..., CreateIfNotFound=True)`
> (already forced by `Indexable.open()`, indexable.py:50) **and** `pw.edit_mode()`
> (`esa.EnterMode('EDIT')`, workbench.py:427–429) before assignment.

### 2.4 `_broadcast_update_to_fields` — indexable.py:255–316

For `pw[GObject, fields] = value`. Same settable gate first. Then two sub-paths:

- **Keyless object** (`not gtype.keys()`, e.g. `Sim_Solution_Options`): builds the
  change DataFrame directly from `value` without reading PowerWorld. Single field →
  `{field: [value]}`; multiple fields require `value` to be a list/tuple of equal
  length (else `ValueError`).
- **Keyed object:** reads existing primary keys via `self[gtype, keys]` (a recursive
  `__getitem__`), returns early if empty (nothing to update — **never creates** on
  this path), then assigns `change_df[field] = value` (pandas broadcasts a scalar or
  aligns a list/array). Single field uses the bare name to avoid pandas multi-column
  treatment.

Always finishes with `ChangeParametersMultipleElementRect`. So broadcast writes are
update-only; only the Case-1 DataFrame path can create.

`fexcept` (indexable.py:11) is a small lambda turning `'Three…'` type names into
`'3…'` (e.g. `ThreeWindingTransformer` → `3WindingTransformer`) — Python-identifier
vs PowerWorld-string reconciliation, mirrored in the generator (§4).

---

## 3. SAW mixin composition — `esapp/saw/saw.py`

`SAW` is an **empty class body** (`pass`) whose entire behavior comes from its MRO.
saw.py:28–55:

```python
class SAW(
    SAWBase,           # core COM: __init__, _com_call, RunScriptCommand, exec_aux...
    CaseActionsMixin, DataMixin, ContingencyMixin, GeneralMixin, MatrixMixin,
    ModifyMixin, PowerflowMixin, RegionsMixin, SensitivityMixin, ScheduledActionsMixin,
    TopologyMixin, TransientMixin, FaultMixin, ATCMixin, GICMixin, OPFMixin,
    PVMixin, QVMixin, TimeStepMixin, WeatherMixin,
):
    pass
```

21 bases total (`SAWBase` + 20 functional mixins). Each mixin lives in its own
`esapp/saw/<area>.py` and is imported at the top of saw.py:5–25.

### How a mixin works (the shared contract)

Mixins do **not** declare `__init__` or hold state — they rely on `SAWBase`
providing:
- `self._com_call(func, *args)` — the single COM gateway (base.py:331–401). Wraps
  every SimAuto call, unwraps the `(Error, Result)` tuple, maps RPC failures to
  `COMError`, and raises `PowerWorldError.from_message(...)` when SimAuto returns an
  error string. Returns `output[1]` (single result) or `output[1:]`.
- `self._run_script(command, *args)` — builds a script statement `"Cmd(a, b);"`
  (strips trailing `None`s, stringifies args) and routes through `RunScriptCommand`
  (base.py:202–238). This is how every *script-command* mixin method works.
- `self.log`, `self.decimal_delimiter`, `self._object_fields` (field-list cache),
  `self.pw_order`, etc.

Two concrete patterns to copy when extending:

- **Script-command method** (most analysis verbs) — `PowerflowMixin.SolvePowerFlow`
  (powerflow.py:10–40): normalize an enum/str arg, then
  `return self._run_script("SolvePowerFlow", method)`.
  `TimeStepMixin` (timestep.py) is the cleanest example: nearly every method is a
  one-line `self._run_script("TimeStep…", …)` with filename/time args quoted.
- **Data method** (typed COM data calls) — `DataMixin` (data.py): convert lists/DFs
  to COM variants (`convert_list_to_variant`, `convert_df_to_variant`) and call
  `self._com_call("GetParamsRectTyped", …)`.

### How to add a mixin (extension recipe)

1. Create `esapp/saw/<feature>.py` with `class FeatureMixin:` and methods that use
   `self._run_script(...)` (for script commands) or `self._com_call(...)` (for direct
   SimAuto functions). No `__init__`, no state of your own.
2. Import it in `saw/saw.py` (top, alongside the others) and add it to the `SAW(...)`
   base list. **MRO order matters** only if two mixins define the same method name —
   keep `SAWBase` first and avoid name collisions.
3. If the feature needs new type-safe constants, add them to `saw/_enums.py` and
   export via `saw/__init__.py`'s `__all__`.

No registry/metaclass — composition is purely the explicit base-class tuple, so the
only "wiring" is the import + the line in the tuple.

---

## 4. Component generation pipeline — `esapp/components/`

`grid.py` (~13 MB) and `ts_fields.py` are **auto-generated** from the `PWRaw` TSV
schema export. Do **not** hand-edit them (the file banner says so, and the project
conventions in the esapp repo reiterate it). Regenerate with:

```bash
cd esapp/components && python generate_components.py   # reads ./PWRaw
```

`generate_components.py:490–507` (the `__main__`): builds a `ComponentGenerator('PWRaw')`,
calls `.parse()`, then `.generate_components('grid.py')` and `.generate_ts_fields('ts_fields.py')`.

### Pipeline stages (`ComponentGenerator`)

1. **Row iteration** — `_iter_raw_rows` (337–341) skips the header and joins wrapped
   quoted continuation lines via `_join_continuation_lines` (343–362). A line is a
   field row if it starts with a tab (`_is_field_row`, 369–370); an object header is
   detected by `_is_object_header` (372–380) using the subdata/maintainer columns.
2. **Parse** — `_parse_components` (150–171) walks rows, creating an
   `ObjectTypeDefinition` per header (skipping `EXCLUDE_OBJECTS`, 79–92) and appending
   `FieldDefinition`s (skipping `EXCLUDE_FIELDS` and any var name containing `/`).
   `_parse_field_definition` (382–397) reads columns: var name (col 3), key symbol
   (col 2), concise name (4), data type (5), description (6), enterable (8).
3. **Key-symbol → role** — `_parse_key_symbol` (446–459) maps PWRaw symbols to
   `FieldRole` flags: `*`→PRIMARY_KEY, `*1*/*2*/*3*`→COMPOSITE_KEY_n, `*2B*`→SECONDARY_ID,
   `*4B*`→CIRCUIT_ID, `*A*`→ALTERNATE_KEY, `**`→BASE_VALUE, `<`→STANDARD_FIELD.
   `FieldDefinition.is_primary` (39–45) treats PRIMARY/COMPOSITE_n/SECONDARY_ID/CIRCUIT_ID
   as primary; `is_secondary` (47–51) = ALTERNATE_KEY|BASE_VALUE.
4. **Name sanitizing** — `_sanitize_for_python` (420–426): `:`→`__`, space→`___`,
   leading digit handling (`3…`→`Three…`, else prefix `_`). `_fix_pw_string` (428–436)
   is the inverse used to recover the PowerWorld field string. (This is the same
   `Three…`↔`3…` rule as `fexcept` in indexable.py.)
5. **Emit GObject classes** — `generate_components` (233–262): writes the preamble
   `from .gobject import *`, then per object a `class <Name>(GObject):` with members
   `PyName = ("PWFieldString", <dtype>, <FieldPriority flags>)` plus a docstring, and
   finally `ObjectString = '<full obj name>'`. Fields are sorted by `_get_sort_key`
   (468–477: composite/primary keys first, then alternate, secondary, base value,
   then standard). Priority flags built by `_build_field_priority_flags` (479–487):
   PRIMARY → `FieldPriority.PRIMARY`, secondary → `FieldPriority.SECONDARY`, else
   `FieldPriority.OPTIONAL`; `+ REQUIRED` if base value; `+ EDITABLE` if enterable.

Real generated output (`grid.py:6036–6048`):
```python
class Bus(GObject):
	BusNum = ("BusNum", int, FieldPriority.PRIMARY)
	"""Number"""
	BusName_NomVolt = ("BusName_NomVolt", str, FieldPriority.SECONDARY)
	"""Name_Nominal kV"""
	AreaNum = ("AreaNum", int, FieldPriority.SECONDARY | FieldPriority.REQUIRED | FieldPriority.EDITABLE)
	...
```

6. **TS fields** — `_extract_ts_fields` (173–231) matches var-name prefixes from
   `TS_OBJECT_MAPPING` (128–138: `TSBus`→`Bus`, `TSGen`→`Gen`, `TSACLine`→`Branch`,
   …), strips `:N` index suffixes, dedups per object type, and emits a frozen
   `TSField` dataclass per attribute under nested `class <ObjType>:` inside one `TS`
   class (generate_ts_fields, 264–333). `TSField.__getitem__` (300–302) lets you write
   `TS.Bus.Input[1]` → `TSField("TSBusInput:1")`.

`MANUAL_FIELDS` (101–124) injects fields PWRaw defines poorly (e.g. `Dbd:3` on
`PlantController_REPCA1`), merged in by `_fields_with_manual_fields` (399–411) without
clobbering existing names.

### `components/__init__.py`
Re-exports: `GObject` from `gobject`, `from .grid import *` (all object classes), and
`TS, TSField` from `ts_fields`.

---

## 5. `GObject` schema model — `esapp/components/gobject.py`

`GObject(Enum)` builds a class-level schema at *definition time* via a custom
`__new__` (gobject.py:59–106). Each subclass member is either:
- the **type tag** — a single-arg member (`ObjectString = 'Bus'`) → sets `cls._TYPE`
  and stores an int `_value_`; or
- a **field** — a `(name, dtype, priority)` triple → `_value_` becomes the 4-tuple
  `(int, field_name_str, dtype, priority)`, and the field name is appended to the
  per-class lists `_FIELDS`, plus `_KEYS`/`_SECONDARY`/`_EDITABLE` depending on its
  `FieldPriority` flags (95–104).

This is why `__getitem__` can read `field.value[1]` for a member (indexable.py:102) —
index 1 of the tuple is the PowerWorld field-name string.

`FieldPriority(Flag)` (gobject.py:16–28): `PRIMARY`, `SECONDARY`, `REQUIRED`,
`OPTIONAL`, `EDITABLE`, **`EDIT_MODE`** — combinable. `EDIT_MODE` marks a field only
enterable while Simulator is in EDIT mode and drives the hint in `_raise_with_edit_hint`
(§2.3).

### Classmethod schema accessors (the public extension surface)

| Classmethod | Returns | Source |
|---|---|---|
| `TYPE()` | PW object-type string (e.g. `"Bus"`), or `'NO_OBJECT_NAME'` | 220 |
| `keys()` | primary-key field names (`_KEYS`) | 172 |
| `fields()` | all field names (`_FIELDS`) | 176 |
| `secondary()` | secondary-key field names (`_SECONDARY`) | 180 |
| `editable()` | editable field names (`_EDITABLE`) | 185 |
| `edit_mode_only()` | fields needing EDIT mode (`_EDIT_MODE`) | 189 |
| `is_edit_mode_only(f)` | bool — in `_EDIT_MODE` | 194 |
| `key_sets()` | `[frozenset(keys())]` + `ALT_KEY_SETS[TYPE()]` alternates | 199 |
| `identifiers()` | `set(keys) ∪ set(secondary)` | 210 |
| `settable()` | `identifiers() ∪ set(editable)` | 215 |
| `is_editable(f)` | bool — in `_EDITABLE` | 224 |
| `is_settable(f)` | bool — in `settable()` | 229 |

`keys()` drives the always-included primary keys in reads; `key_sets()` (with the
`ALT_KEY_SETS` table at gobject.py:61) drives the create-path key check in §2.3.

> ⚠️ **`is_settable` is advisory, not a gate, and it is frequently wrong.** Through 0.1.x
> it *was* the gate — both bracket-write paths refused a read-only column. In 0.2.1 it only
> selects the text of a `UserWarning`. Worse, it disagrees with PowerWorld: the generator
> keeps a field as `EDITABLE` only when Simulator reports `enterable` as an unconditional
> `Yes`, and silently drops every **conditional** one. `Branch.LineStatus` is the canonical
> case — PowerWorld says *"Depends: Normally enterable except when field Lockout is YES"*,
> esapp says read-only, and the write succeeds.
>
> Counted against Simulator build 2026-07-22 / esapp 0.2.1 — fields PowerWorld reports as
> enterable but `is_settable()` calls read-only:
>
> | Type | known fields | PW enterable | flagged read-only anyway |
> |---|---|---|---|
> | `Branch` | 809 | 303 | **112** |
> | `Bus` | 581 | 144 | **33** |
> | `Gen` | 598 | 228 | **5** (incl. `GenMVR`) |
> | `Load` | 277 | 119 | **1** |
>
> The authority is PowerWorld: `pw.esa.GetFieldList(<type>)` returns an `enterable` column
> (and a `key_field` column marking keys `*1*`, `*2*`, …). Genuine read-onlys have it blank —
> `Shunt.SSMinMVR` for instance, where the write really does vanish. Never promote this
> warning to an error with `-W error::UserWarning`.

`__str__` returns the PW field string for field members (so a member stringifies to
its PowerWorld name); `__repr__` shows the type or field for debugging (108–120).

---

## 6. Exception hierarchy — `esapp/saw/_exceptions.py`

```
Exception
└── Error                         (base for everything esapp; _exceptions.py:8)
    ├── PowerWorldError           (SimAuto returned an error string; 19)
    │   ├── SimAutoFeatureError           ("cannot be retrieved through simauto"; 77)
    │   ├── PowerWorldPrerequisiteError   (setup/data missing — KEY for writes; 92)
    │   ├── PowerWorldAddonError          ("not registered"; 108)
    │   └── CommandNotRespectedError      (silent no-op; 135)
    ├── COMError                  (COM/RPC layer failure; 121)
    ├── GridObjDNE                (165)
    ├── FieldDataException / AuxParseException / ContainerDeletedException
    ├── PowerFlowException        (180)
    │   ├── BifurcationException / DivergenceException / GeneratorLimitException
    └── GICException              (204)
```

### The classification factory — `PowerWorldError.from_message` (50–74)

`SAWBase._com_call` raises `PowerWorldError.from_message(output[0])` when SimAuto
returns a non-empty, non-"No data" error string (base.py:386–387). The factory
lower-cases the message and returns a **subclass**:
- `"cannot be retrieved through simauto"` → `SimAutoFeatureError`.
- Any of `"no active"`, **`"not found"`**, `"could not be found"`, `"requires setup"`,
  `"is not online"`, `"at least one"`, `"no directions set"`, `"out-of-range"`,
  `"no available participation points"` → `PowerWorldPrerequisiteError`.
- `"not registered"` → `PowerWorldAddonError`.
- else → base `PowerWorldError`.

This is the linchpin for bracket-write: a SimAuto "object not found" comes back as
`PowerWorldPrerequisiteError`, which `_bulk_update_from_df` catches and re-string-matches
on `"not found"` to trigger the create fallback (§2.3). So the create path depends on
**both** the factory's substring list *and* the bracket layer's own `"not found"` check.

`COMError` is different in kind — it wraps a thrown COM exception (RPC server crash /
invalid function), raised in `_com_call`'s `except` (base.py:368–376), not via the
factory.

`__init__` (38–48) splits the message on the first `:` into `source` / `message`,
keeping `raw_message`.

The exception classes consolidated from the old `utils/exceptions.py` (`GridObjDNE`,
`PowerFlowException` & subtypes, `GICException`, etc.) now live in this same file and
are re-exported through `saw/__init__.py` and the top-level `esapp/__init__.py`.

---

## 7. Descriptors — `esapp/_descriptors.py`

Two descriptor classes give Pythonic option access without boilerplate, both built on
the bracket interface:

- **`SolverOption(key, is_bool=True)`** (_descriptors.py:12–34): maps a `PowerWorld`
  attribute to a `Sim_Solution_Options` field. `__get__` does
  `obj[Sim_Solution_Options, key][key].iloc[0]` and coerces to bool via `== YesNo.YES`;
  `__set__` does `obj[Sim_Solution_Options, key] = YesNo.from_bool(value)` (or raw
  value if `is_bool=False`). The ~25 `pw.flat_start`, `pw.max_iterations`, etc. in
  workbench.py:50–93 are instances of this — they read/write through `__setitem__`'s
  keyless broadcast path (§2.4).
- **`GICOption(key, is_bool=True)`** (_descriptors.py:37–68): maps a `GIC` attribute to
  a `GIC_Options_Value` row. `__get__` reads `obj._pw[GIC_Options_Value, "ValueField"]`
  and filters by `VariableName == key`; `__set__` wraps the write in
  `EnterMode("EDIT")` … `SetData('GIC_Options_Value', ['VariableName','ValueField'],
  [key, value])` … `EnterMode("RUN")`. The `pf_include`, `calc_mode`, `efield_mag`, …
  attributes in gic.py:69–96 are instances.

To add a new solver/GIC flag: just declare one more class attribute
`my_opt = SolverOption('PWFieldName')` on `PowerWorld` (or `GICOption(...)` on `GIC`) —
no method needed.

---

## 8. Embedded utility apps — `esapp/utils/`

All three follow the same pattern: `__init__(self, pw=None)` stores `self._pw`, and
every method reaches data via `self._pw[GObject, fields]` or `self._pw.esa.<saw method>`.
They are stateless wrappers over the live case (plus some cached matrices).

- **`Network`** (network.py:62) — topology matrices. `busmap()` (Series BusNum→index),
  `incidence()` (signed branch×bus sparse, HVDC appended, cached in `self._A`),
  `laplacian(weights)` = `A.T @ diags(W) @ A`, plus electrical helpers `lengths`,
  `zmag`, `ybranch`, `yshunt`, `gamma`, `delay`. Pulls `Branch`/`Bus`/`Substation`/
  `DCTransmissionLine` via the bracket interface; `delay()` also calls
  `self._pw.esa.get_ybus()` directly (MatrixMixin). `PowerWorld.busmap/buscoords`
  delegate here (workbench.py:245–275).
- **`GIC`** (gic.py:34) — GIC engine integration. `configure()` sets the `GICOption`
  descriptors; `gmatrix()` forces `pf_include=True` then `self._pw.esa.get_gmatrix()`;
  `storm()` → `esa.GICCalculate(...)`; `model()` (gic.py:250–373) builds the full
  sparse incidence `A`, conductance Laplacian `G`, H-matrix and per-unit `zeta`
  entirely from `GICXFormer`/`Substation`/`Bus`/`Branch`/`Gen` bracket reads. Results
  exposed as read-only properties (`A`, `G`, `H`, `zeta`, `Px`, `eff`).
- **`BusCat`** (buscat.py) — parses the `BusCat` string field into typed bus
  classes/roles using `BusType`/`BusCtrl`/`Role` enums from `saw/_enums.py`; reads
  `Bus` via `self._pw`.

To add another embedded app: write `class Foo: def __init__(self, pw=None): self._pw = pw`
in `utils/`, then add `self.foo = Foo(self)` in `PowerWorld.__init__` (workbench.py:36–38).

---

## 9. Quick "where do I touch X" index

| Want to change… | Edit | Notes |
|---|---|---|
| How `pw[...]` reads/writes | `indexable.py` | backed by `GetParamsRectTyped` / `ChangeParametersMultipleElement[Rect]` |
| Add a new SAW capability | new `saw/<x>.py` mixin + line in `saw/saw.py` | use `_run_script` / `_com_call` |
| Object/field schema | regenerate via `generate_components.py` from `PWRaw` | **never** hand-edit `grid.py`/`ts_fields.py` |
| Key/editable classification | `gobject.py` flags + `_parse_key_symbol` in generator | drives `is_settable` gate |
| New error type | `saw/_exceptions.py` + `from_message` substring list | export in `saw/__init__.py` |
| New solver/GIC flag | one `SolverOption`/`GICOption` attr | `_descriptors.py` |
| New analysis app on `pw` | `utils/<x>.py` + `self.x = X(self)` in `__init__` | delegate via `self._pw` |

---

## See also
- API-usage map (how to *call* esapp): [esapp](../concepts/esapp.md)
- Underlying COM server: [powerworld-simauto](../concepts/powerworld-simauto.md)
- Hub: [Home](../index.md)


---

# ==== esapp-schema-reference.md ====

---
type: reference
domain: tooling
topic: scripting
aliases: [esapp-schema, object-fields, simauto-commands, grid-py-reference]
tags: [esapp, schema, fields, simauto, commands, reference]
---

# Reference: esapp object-field schema + SimAuto command catalog

## Abstract

This is the field-schema + SimAuto-command lookup for **writing esapp code**: read
it when you need an object type's exact **key fields** (so a read-modify-write
round-trips) or the **command/method** for an operation. **Part A** documents the
`GObject` category model (keys / secondary / editable / identifiers / settable) plus
its runtime `@classmethod` accessors and the real per-type key/identifier table pulled
from `grid.py`. **Part B** catalogs the `SAW` mixins and the named SAW methods; the
task-organized SCRIPT-command index lives in [aux-script-commands](aux-script-commands.md). Every field name and method below was read
out of `C:\path\to\esapp` source — cited `file:line`.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](../concepts/esapp.md) · [esapp-overview](../methods/esapp-overview.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [esapp-package-backend](esapp-package-backend.md) · [aux-script-commands](aux-script-commands.md)

## Content

> Source of truth: `C:\path\to\esapp`. Field names + flags were read
> from `components/gobject.py` and `components/grid.py`; methods from `saw/*.py`.
> `grid.py` is auto-generated (~197k lines, 1001 `GObject` classes) — regenerate via
> `components/generate_components.py`, never hand-edit.

---

## Part A — Object field schema

### A.1 The category model (`components/gobject.py`)

Each component is a `GObject` subclass (an `Enum`). Every field is declared as
`Member = ("PWFieldName", dtype, FieldPriority...)`. The `FieldPriority` `Flag`
(`gobject.py:16-27`) drives which category a field lands in:

| Flag | Meaning (`gobject.py:23-27`) |
|---|---|
| `PRIMARY` | Field is part of the **primary key** for the object |
| `SECONDARY` | Field is part of a **secondary key** (a secondary identifier) |
| `REQUIRED` | Required for data retrieval/update |
| `OPTIONAL` | Optional |
| `EDITABLE` | User-modifiable |

At class-construction time `GObject.__new__` (`gobject.py:59-106`) sorts every field
into class-level lists: `_FIELDS` (all), `_KEYS` (has `PRIMARY`), `_SECONDARY`
(has `SECONDARY`), `_EDITABLE` (has `EDITABLE`). Flags combine with `|`
(e.g. `SECONDARY | REQUIRED | EDITABLE`).

### A.2 Runtime accessors (call with `()` — they are `@classmethod`s)

From `gobject.py:122-161`. **They are methods, not properties — `Bus.keys()` not
`Bus.keys`.**

| Accessor | Returns | Source |
|---|---|---|
| `Type.TYPE()` | PowerWorld object-type string (e.g. `"Bus"`) | `gobject.py:149-151` |
| `Type.fields()` | `list` — every defined field name | `gobject.py:126-128` |
| `Type.keys()` | `list` — **primary** key fields only | `gobject.py:122-124` |
| `Type.secondary()` | `list` — secondary identifier fields | `gobject.py:130-133` |
| `Type.editable()` | `list` — editable (user-modifiable) fields | `gobject.py:135-137` |
| `Type.identifiers()` | `set` — **primary ∪ secondary** keys | `gobject.py:139-142` |
| `Type.settable()` | `set` — **identifiers ∪ editable** (everything writable) | `gobject.py:144-147` |
| `Type.is_editable(name)` | `bool` — is this field editable | `gobject.py:153-156` |
| `Type.is_settable(name)` | `bool` — is this field a key or editable | `gobject.py:158-161` |

```python
from esapp.components import Bus, Gen
Bus.TYPE()          # 'Bus'
Bus.keys()          # ['BusNum']
Gen.keys()          # ['BusNum', 'GenID']
Gen.identifiers()   # primary + secondary, e.g. {'BusNum','GenID','GenStatus','GenMWSetPoint', ...}
Gen.is_settable('GenMW')   # True  -> safe to push back
```

### A.3 The KEY-FIELD WRITE-BACK RULE (do not skip)

PowerWorld matches each DataFrame row back to a live object by its **primary key
field(s)**. If a row you write lacks those keys, PowerWorld cannot identify the object
and the change is a **silent no-op** (no error, no change).

- **Bracket path (preferred):** `pw[Gen, "GenMW"]` *automatically* includes the keys
  on read (`indexable.py:84-89` — reads always start with `gtype.keys()`), so a
  read-modify-write keeps them. A bulk write `pw[Gen] = df` **validates that all
  primary keys are present** and raises `ValueError` if any are missing
  (`indexable.py:235-241`). Every column must also pass `gtype.is_settable(...)`
  (`indexable.py:224-225`).
- **Raw `esa`/SAW path:** you must prepend the keys yourself — there is no auto-key on
  `GetParametersMultipleElement` / `ChangeParametersMultipleElementRect`. Build the
  field list as `list(Gen.keys()) + [<your fields>]` and keep the key columns in the
  DataFrame end-to-end.

**Rule of thumb: never strip key columns from a DataFrame you intend to push back.**

### A.4 Per-type key / identifier table (read from `grid.py`)

Keys/secondary verbatim from the `FieldPriority.PRIMARY` / `.SECONDARY` flags in
`grid.py`. `secondary` here lists the most useful identifiers (full list via
`Type.secondary()`); `#flds`/`#edit` are total field and editable-field counts.

| Object type | `TYPE()` | `keys()` (primary) | key secondary / identifiers | #flds | #edit | grid.py line | Description |
|---|---|---|---|---|---|---|---|
| **Bus** | `Bus` | `BusNum` | `BusName`, `BusNomVolt`, `AreaNum`, `ZoneNum`, `BusName_NomVolt` | 588 | 111 | `6036` | **UNVERIFIED:** (no prose definition found; key field is `BusNum` since a bus is uniquely identified by its number). |
| **Gen** | `Gen` | `BusNum`, `GenID` | `GenStatus`, `GenMWSetPoint`, `GenMVRMax/Min`, `GenMWMax/Min`, `GenVoltSet` | 607 | 222 | `61768` | **UNVERIFIED:** (BidCurve subdata = piecewise-linear cost curve; ReactiveCapability subdata = MW vs. Min/Max MVAR limits). |
| **Load** | `Load` | `BusNum`, `LoadID` | `LoadStatus`, `LoadSMW`, `LoadSMVR` | 287 | 118 | `97444` | **UNVERIFIED:** (BidCurve subdata = piecewise-linear benefit curve; costs must be increasing for loads). |
| **Branch** (line) | `Branch` | `BusNum`, `BusNum:1`, `LineCircuit` *(+`BusName_NomVolt:1`)* | `LineR`, `LineX`, `LineAMVA` (rating), `BusName_NomVolt` | 811 | 188 | `4298` | A network element (e.g. transmission line) connecting a from-bus and to-bus with a circuit ID; MW flow direction runs from-bus → to-bus. |
| **Transformer** | `Transformer` | `BusNum`, `BusNum:1`, `LineCircuit` *(+`BusName_NomVolt:1`)* | `LineXFType`, `XFTapMax/Min`, `XFStep`, `XFAuto`, `XFRegMax/Min` | 814 | 193 | `176297` | The `3WXFormer` type — a three-winding transformer modeled internally as a container of two-winding transformer branches joined at a common star bus. |
| **Shunt** (switched) | `Shunt` | `BusNum`, `ShuntID` | `SSStatus`, `SSNMVR`, `SSCMode` | 302 | 154 | `156986` | A switched shunt device (e.g. capacitor bank or reactor) at a bus that injects/absorbs Mvar in discrete steps. |
| **DCTransmissionLine** | `DCTransmissionLine` | `BusNum`, `BusNum:1`, `DCLID` *(+`BusName_NomVolt:1`)* | `DCLMode`, `DCLSetVolt`, `DCLR`, `DCLAlpha`, `DCLGamma` | 324 | 184 | `21018` | **UNVERIFIED:** (no prose found for the plain 2-terminal type; grouped with VSCDCLine/MSLine/3WXFormer/MTDC* as Edit-Mode-only topology objects). |
| **MultiSectionLine** | `MultiSectionLine` | `BusNum`, `BusNum:1`, `LineCircuit` *(+`BusName_NomVolt:1`)* | `BusInt`, `BusInt:1…` (section buses) | 149 | 48 | `127339` | A transmission line (MSLine) modeled as segments joined by intermediate dummy buses, running in order from the From Bus to the To Bus. |
| **Area** | `Area` | `AreaNum` | `AreaName` | 446 | 95 | `1693` | **UNVERIFIED:** (no prose definition found beyond an unrelated SelectByCriteriaSet reference). |
| **Zone** | `Zone` | `ZoneNum` | `ZoneName` | 390 | 57 | `192861` | **UNVERIFIED:** (no prose definition found beyond an unrelated SelectByCriteriaSet reference). |
| **Substation** | `Substation` | `SubNum` | `SubName` | 512 | 90 | `168780` | Groups the equipment/buses at a physical site to support full node-breaker topology modeling (vs. simpler bus-branch representation). |
| **SuperArea** | `SuperArea` | `SAName` | *(none flagged secondary)* | 198 | 32 | `169809` | A named grouping of Areas, each assigned an optional participation factor. |
| **Owner** | `Owner` | `OwnerNum` | `OwnerName` | 126 | 37 | `130894` | An entity holding ownership of buses, loads, generators, and branches; generator ownership is recorded as a percentage fraction. |
| **InjectionGroup** | `InjectionGroup` | `InjGrpName` | *(none flagged secondary)* | 174 | 65 | `87889` | A named collection of participation points (gens, loads, switched shunts, buses, or other injection groups), each with a participation factor, for an aggregate/distributed injection. |
| **Interface** | `Interface` | `FGName` | `IntNum`, `IntMonDir` | 149 | 43 | `88373` | A monitored aggregate power-flow quantity, summing (directional) flow/injection across branches, DC lines, MSLines, gens, loads, injection groups, areas, zones, or other interfaces. |
| **Nomogram** | `Nomogram` | `FGName` | *(none flagged secondary)* | 45 | 25 | `127898` | A safe-operating limit curve relating simultaneous flows on two interfaces, bounded by vertex breakpoints (NomogramBreakPoint). |
| **Contingency** | `Contingency` | `CTGLabel` | *(none flagged secondary)* | 166 | 40 | `10980` | **UNVERIFIED:** (no standalone prose found; only its CTGElement subdata format — an ordered list of actions with optional criteria/status/timing — is documented). |

Notes / gotchas read from source:
- **Branch / Transformer / DCLine / MSLine** are all two-terminal: the `:1` suffix is
  the **to-bus** (`BusNum` = from, `BusNum:1` = to), plus a circuit id
  (`LineCircuit`, or `DCLID` for DC). The generator also flags `BusName_NomVolt:1` as
  `PRIMARY` — it is a composite "BusName_NomVolt" identifier for the to-bus; the
  numeric `BusNum`/`BusNum:1`/`LineCircuit` triple is the one you normally supply.
- **Transformer is a separate `GObject` class** from `Branch` (`grid.py:176297`), but
  in PowerWorld a transformer is still a Branch with `LineXFType` set — the two schemas
  overlap heavily (both expose `LineR`/`LineX`, ratings, `Branch*` fields).
- **`ThreeWXFormer`** (`grid.py:9`) is the 3-winding transformer with a different key
  shape (`BusIdentifier`, `BusIdentifier:1`, `BusIdentifier:2`, `LineCircuit`) — use it
  for 3-winders, not `Transformer`.
- **Substation**: `grid.py` declares `SubNum`/`SubName` **twice** in the class body
  (duplicate enum members). Under Python ≥3.13's stricter `Enum` this raises on import
  (the package targets 3.11, where the dup is treated as an alias). Effective key is
  `SubNum`, secondary `SubName`.
- **` contingencies / interfaces / injection groups / nomograms`** are **string-keyed**
  (`CTGLabel`, `FGName`, `InjGrpName`) — no numeric key.
- Keyless objects exist too (e.g. `Sim_Solution_Options`): `Type.keys()` is empty and
  the bracket setter takes a positional value list instead (`indexable.py:282-296`).

---

## Part B — SAW SimAuto command catalog

`SAW` (`saw/saw.py:28-55`) is assembled by the **mixin pattern**: `SAWBase` plus 19
mixins. Reach it via `pw.esa`. Two call styles inside:
`_com_call(...)` wraps a direct SimAuto COM function; `_run_script("Cmd", *args)`
(`base.py:202`) builds a PowerWorld **script command** string and routes it through
`RunScriptCommand`. So a mixin method named `EnterMode` *is* the script command
`EnterMode(...)` — the Python method name = the PowerWorld aux/script command name.

### B.1 Mixins (what each covers) — `saw/`

| Mixin | File | Covers |
|---|---|---|
| `SAWBase` | `base.py` | COM core: connect/`exit`, `RunScriptCommand`/`RunScriptCommand2`, `ProcessAuxFile`, `exec_aux`, `_run_script`/`_com_call` plumbing, properties (`CreateIfNotFound`, `ProcessID`) |
| `DataMixin` | `data.py` | **The data layer** — Get/Change Parameters (single/multiple/rect/typed), `GetFieldList`, `ListOfDevices` |
| `PowerflowMixin` | `powerflow.py` | `SolvePowerFlow`, flat start, mismatch/tolerance, **`SaveState`/`LoadState`**, diff-case |
| `GeneralMixin` | `general.py` | `EnterMode`, `StoreState`/`RestoreState`/`DeleteState`, aux/CSV load (`LoadAux`, `LoadCSV`, `ImportData`), `SaveData`, `SetData`/`CreateData`, `GetSubData`/`SetSubData`, `Delete`, `SelectAll` |
| `CaseActionsMixin` | `case_actions.py` | `OpenCase`/`OpenCaseType`, `SaveCase`, `CloseCase`, `NewCase`, renumbering, `Scale` |
| `ModifyMixin` | `modify.py` | Topology/model edits: `Move`, `SplitBus`/`MergeBuses`, `TapTransmissionLine`, injection-group/interface create, participation factors |
| `ContingencyMixin` | `contingency.py` | `CTGSolve`/`CTGSolveAll`, `CTGAutoInsert`, `CTGApply`, OTDF, read/write CTG files |
| `TransientMixin` | `transient.py` | Transient stability: `TSSolve`/`TSSolveAll`, `TSInitialize`, `TSGetResults`, result storage, model load/save |
| `SensitivityMixin` | `sensitivity.py` | `CalculatePTDF`, `CalculateLODF`(+matrix/screening), `CalculateShiftFactors`, loss/volt sense |
| `MatrixMixin` | `matrices.py` | `get_ybus`, `get_jacobian`(+ids), `get_gmatrix`, `SaveJacobian` |
| `TopologyMixin` | `topology.py` | Path/island analysis, `CloseWithBreakers`/`OpenWithBreakers`, `ExpandBusTopology`, `SaveConsolidatedCase` |
| `RegionsMixin` | `regions.py` | Area/zone/region operations |
| `ScheduledActionsMixin` | `scheduled.py` | Scheduled-action automation |
| `TimeStepMixin` | `timestep.py` | **TimeStep weather feature** — `TimeStepDoRun`, `TimeStepLoadPWW*`, B3D/TSB load-save, `TimeStepSaveFieldsSet` |
| `WeatherMixin` | `weather.py` | Weather data helpers |
| `GICMixin` | `gic.py` | Geomagnetically-induced-current commands |
| `OPFMixin` / `PVMixin` / `QVMixin` / `ATCMixin` / `FaultMixin` | `opf.py` … `fault.py` | OPF, PV/QV curves, ATC, fault analysis |

### B.2 Most-used methods (the ones agents actually call)

**Reading data** (`saw/data.py`):
- `GetParametersMultipleElement(ObjectType, ParamList, FilterName="")` → `DataFrame`
  (string output, `data.py:284`). The classic ESA read.
- `GetParamsRectTyped(ObjectType, ParamList, FilterName="")` → typed `DataFrame`
  (preserves native variant types; `data.py:324`). **This is what the bracket read
  uses.**
- `GetParametersSingleElement(ObjectType, ParamList, Values)` → `Series` (`data.py:246`).
- `GetFieldList(ObjectType)` → all available fields for a type (`data.py:187`);
  `ListOfDevices(ObjType, FilterName="")` → device keys (`data.py:478`).

**Writing data** (`saw/data.py`):
- `ChangeParametersMultipleElementRect(ObjectType, ParamList, df)` — push a whole
  DataFrame back (`data.py:88`). **Used by the bracket setter.** `ParamList` **must
  lead with the key fields.**
- `ChangeParametersMultipleElement(ObjectType, ParamList, ValueList)` (`data.py:54`).
- `ChangeParametersSingleElement(ObjectType, ParamList, Values)` (`data.py:21`).

**Mode / state / solve**:
- `EnterMode("EDIT" | "RUN")` (`general.py:200`) — must be in EDIT to create/delete
  objects; RUN to solve. Accepts `PowerWorldMode.EDIT/RUN`.
- `SolvePowerFlow(SolMethod=SolverMethod.RECTNEWT)` (`powerflow.py:10`) — also accepts
  `"POLARNEWT"`, `"GAUSS"`, `"DC"`, etc.
- `SaveState()` / `LoadState()` (`powerflow.py:382`/`390`) — the **single** PowerWorld
  power-flow state stack (`pw.snapshot()` context manager wraps these).
- `StoreState(name)` / `RestoreState(name, state_type="USER")` / `DeleteState(name)`
  (`general.py:225`/`246`/`267`) — **named** states (different from Save/LoadState).

**Case actions** (`saw/case_actions.py`): `OpenCase(FileName)` (`33`),
`SaveCase(FileName=None, FileType="PWB", Overwrite=True)` (`127`), `CloseCase()` (`113`),
`NewCase()` (`254`), `Scale(...)` (`458`).

**Aux / script** (`saw/base.py` + `general.py`):
- `RunScriptCommand(Statements)` (`base.py:240`) — run a raw PowerWorld script string.
- `RunScriptCommand2(Statements, StatusMessage)` (`base.py:260`).
- `ProcessAuxFile(FileName)` (`base.py:179`) / `exec_aux(aux, ...)` (`base.py:422`) —
  run an aux file / inline aux text.
- `LoadAux(filename, create_if_not_found=False)` (`general.py:288`),
  `LoadCSV` (`337`), `ImportData` (`311`).

**TimeStep (weather)** (`saw/timestep.py`): `TimeStepDoRun(start, end)` (`10`),
`TimeStepDoSinglePoint(time_point)` (`28`), `TimeStepLoadPWW(filename, solution_type)`
(`146`), `TimeStepLoadPWWRange(...)` (`164`), `TimeStepSaveFieldsSet(object_type,
field_list, filter_name)` (`268`), `TimeStepLoadB3D` (`135`), `TimeStepLoadTSB`/`SaveTSB`
(`307`/`318`). *(This is PowerWorld's TimeStep feature — NOT transient stability; see the
TS disambiguation on [esapp](../concepts/esapp.md).)*

**Contingency** (`saw/contingency.py`): `CTGSolve(ctg_name)` (`11`),
`CTGSolveAll(distributed=False, clear_results=True)` (`33`), `CTGAutoInsert()` (`61`),
`CTGApply(name)` (`136`), `CTGWriteResultsAndOptions(...)` (`79`).

**Transient stability** (`saw/transient.py`): `TSSolve(...)` (`58`), `TSSolveAll()`
(`96`), `TSInitialize()` (`28`), `TSGetResults(...)` (`326`),
`TSResultStorageSetAll(object="ALL", value=True)` (`41`).

**Matrices / sensitivities**: `get_ybus(full=False)` (`matrices.py:15`),
`get_jacobian(full=False, form=JacobianForm.RECTANGULAR)` (`matrices.py:178`),
`CalculatePTDF(seller, buyer, method=LinearMethod.DC)` (`sensitivity.py:36`),
`CalculateLODF(branch, method=LinearMethod.DC)` (`sensitivity.py:65`),
`CalculateShiftFactors(...)` (`sensitivity.py:197`).

### B.3 Common `RunScriptCommand(...)` script commands

Task-organized SCRIPT-command index → [aux-script-commands](aux-script-commands.md).
The named methods above (§B.2) remain the preferred Python entry points; the catalog
is the raw script-command reference for anything unwrapped.

> Preference (per wiki house rules): for **data**, use the bracket interface
> (`pw[Gen, fields]`, `pw[Gen] = df`) over raw `GetParametersMultipleElement` /
> `ChangeParametersMultipleElementRect`; for **script commands**, use the named SAW
> methods (`pw.esa.SolvePowerFlow()`) or `pw.esa.RunScriptCommand("...")` for anything
> not yet wrapped. See [esapp-overview](../methods/esapp-overview.md) for end-to-end recipes and [powerworld-simauto](../concepts/powerworld-simauto.md)
> for the underlying COM server.


---

# ==== powerworld-option-objects-v25.md ====

---
type: reference
domain: tooling
topic: scripting
aliases: [powerworld-option-objects-v25, option-objects, all-powerworld-options, options-catalog, sim-solution-options-fields, ctg-options-fields, opf-options-fields]
tags: [powerworld, options, schema, reference, simulator-25, generated]
---

# Reference: every PowerWorld option object and its fields (Simulator 25)

## Abstract

All 32 PowerWorld `*_Options` objects and their 1,079 fields, generated from the Simulator 25
field export. Use it to find the exact field behind any study setting. For which fields matter per
study, whether each is verified, and the traps, read [powerworld-study-options](powerworld-study-options.md) first.

## Connections

- **Up:** [Home](../index.md)
- **Hub:** [powerworld-study-options](powerworld-study-options.md) (curated: which option to change for which study, provenance-tagged)
- **Across:** [powerworld-study-commands](powerworld-study-commands.md) (the SCRIPT commands that run each study) · [esapp-schema-reference](esapp-schema-reference.md) (key fields for non-option objects)

## Content

Generated 2026-09-28 from `powerworld-object-fields-v25.xlsx` (in this folder), the PowerWorld
Simulator 25 (beta) field export dated 2026-09-12. **Nothing here is hand-written: the descriptions
are PowerWorld's.** Regenerate on a new Simulator build rather than editing rows.

- Per-object boilerplate fields (custom expressions, calculated fields, data checks, `ObjectID`,
  `Selected`) are omitted.
- **enterable**: `Yes` = writable by `SetData`; `AUX/Paste` = writable only from an aux file or a
  paste; `read-only` = cannot be written.
- A `:N` suffix is a distinct field (`MaxItr:1` is not `MaxItr`). **concise** is a second name for
  the same field; the aux parser accepts either.
- Set a field with `SetData(<object>, [field], [value]);` (esapp: `pw.esa.SetData(...)`), then
  **read it back**: a write that changes nothing still reports success.
- Grouped by study area. Transient and GIC come last and are outside steady-state work.

### Power flow and solution

#### `Sim_Solution_Options` (82 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `SEOCloseCBToEnergizeSShunts` | CloseCBToEnergizeShunts | String | Yes | Close Breakers to Energize Switched Shunts | Set to YES to allow switched shunts that are presently not energized to participate in automatic switched shunt control if they can be energized by closing breakers (or load break disconnects). |
| `DCIgnoreXFImpedanceCorrection` | DCXFCorrIgnore | String | Yes | DC Approximation\Ignore Transformer Impedance Correction | Set to YES to ignore the transformer impedance correction in the DC approximation. Normally this should be ignored. |
| `DCPFModelType` | DCModelType | Integer | Yes | DC Approximation\Line Model Type | Set to RIgnore to assume the series resistance (r) is zero. Set to GIgnore to assume the series conductange (g) is zero |
| `DCPFMode` | DCApprox | String | Yes | DC Approximation\Use DC Approximation | Set to YES to assume a DC approximation (the DC power flow) |
| `LossSenseFunc:1` | DCLossComp | String | Yes | DC Approximation\Use User-Defined Loss Sens for DC OPF and ED | Use User-Defined Loss Sens for DC OPF and ED |
| `EnforceConvex` | EconDispEnforceConvex | String | Yes | Economic Dispatch\Enforce Convex Cost Curves? | Enforce Convex Cost Curves in the economic dispatch. If a generator ends up in a part of its cost curve that is not convex then the generator AGC status will be set to NO |
| `IncludePenaltyFactors` | EconDispPenaltyFactors | String | Yes | Economic Dispatch\Include Penalty Factors? | Include Penalty Factors in the economic dispatch to account for losses |
| `ContingentInterfaceEnforcement` | CTGInterfaceEnforcement | Integer | Yes | General\Contingent Interface Inclusion | Contingent Interface Inclusion (Never = never enforce flows; PowerFlow = only enforce in power flow and OPF; 2 : CTG = also enforce in Contingency and SCOPF) |
| `DisableAngleRotation` |  | String | Yes | General\Disable Angle Rotation | Set to YES to disable voltage angle rotation. Normally at the end of a power flow solution angles are brought inside of +/- 160 degrees if possible. |
| `SEODisableAngleSmoothing` | DisableAngleSmoothing | String | Yes | General\Disable Angle Smoothing | Set to YES to disable the angle smoothing that is done as a preprocess to the power flow. Angle smoothing attempts to reduce large angle differences across branches that have been been closed in. Normally this option should NOT be disabled. |
| `RestoreSolution` | DisableRestoreSolution | String | Yes | General\Disable Restore last successful solution | Disable Restore last successful solution |
| `RestoreState` | DisableRestoreState | String | Yes | General\Disable Restore State before failed solution attempt | Disable Restore State before failed solution attempt |
| `SEODisableXFTapControlIfSensWrongSign` | DisableXFTapWrongSign | String | Yes | General\Disable Transformer Tap Control if Sens. Wrong Sign | Set this to YES to disable transformer control when a transformer is regulating one of its own terminal buses and the tap sensitivity is the wrong sign. If regulating the from bus the correct sign is positive and when regulating the to bus the correct sign is negative. This should normally be set to YES. |
| `AllowMultIslands` | DynAssignSlack | String | Yes | General\Dynamically assign slack buses (Allow Multiple Islands) | Set to YES to allow Simulator to determine automatically add or remove a slack buses as system topology changes. Preference is given to the buses chosen by the user to be slack buses while in Edit Mode. Otherwise the generation with the largest maximum MW is given preference. |
| `EvalSolutionIsland` |  | String | Yes | General\Evaluate Solution for Each Island | Set to YES so that the power flow solution only terminates if all viable islands in the case fail to converge. As long as one island continues to converge the solution will continue. Also after completing a power flow solution, if some islands solve while others do not, then the Solved field of each island will be populated to indicate which ones sucessfully converged. |
| `EvalSolutionIsland:1` | EvalSolutionIslandRequireLargest | String | Yes | General\Evaluate Solution Require Largest Island Solved | When EvalSolutionIsland = YES, a solution only terminates if all viable islands in the case fail to converge. Set this option to YES to require that the island with the largest number of buses in it must also converge. If the largest island does not converge then entire solution is reported as unsolved. |
| `LossSenseFunc` |  | String | Yes | General\Loss Sensitivity Function | Loss Sensitivity Function |
| `SBase` | MVABase | String | Yes | General\SBase |  |
| `UsePSLFConverterApproximatePowerFactor` | UsePSLFConvApproxPowerFactor | String | Yes | General\Use Approximate DC Converter Power Factor Equations | Recommended value is NO. Set to YES to use an approximate calculation (to match what PSLF does) for DC converter power factor of cos(Phi) = 1/2*(cos(alpha) + cos(alpha+mu)) instead of the more accurate equations normally used. |
| `UsePSLFConverterIncorrectFixedTap` | UsePSLFConvIncorrectFixedTap | String | Yes | General\Use PSLF treatment of Fixed Tap in DC Converters | NO is recommended value. This only impacts DC converter transformer equations. NO - Uses the correct equation of TotalTap = VariableTap + FixedTap - 1; YES - Uses the incorrect equation of TotalTap = VariableTap*FixedTap (implemented by PSLF). |
| `ConvergenceTol:2` | MVAConvergenceTol | Real | Yes | Inner Power Flow Loop\Convergence Tolerance in MVA | Convergence Tolerance in MVA |
| `ConvergenceTol` | PUConvergenceTol | Real | Yes | Inner Power Flow Loop\Convergence Tolerance in PU | Convergence Tolerance. Note: In the AUX file, this value is written in per unit. Thus if SBase=100, then a 0.1 MVA tolerance should be written as 0.001 |
| `DisableOptMult` |  | String | Yes | Inner Power Flow Loop\Disable Optimal Multiplier | Set to YES to disable the optimal multiplier in the inner power flow loop iterations. Normally this should NOT be done. |
| `DoOneIteration` |  | String | Yes | Inner Power Flow Loop\Do One Iteration | Do only one inner power flow loop iteration |
| `FlatStart` | FlatStartInit | String | Yes | Inner Power Flow Loop\Flat Start | Initialize the system to a flat start at the beginning of each power flow solution. When this option is YES it gets applied when using the Solve Power Flow option from the GUI, using the Auto Solve On Load option, and when Animating in the GUI. This option is not used when solving the power flow using script commands. |
| `SEOZBRMis:5` | InitMis_BranchRateMult | Real | Yes | Inner Power Flow Loop\Initial Mismatch Branch Limit Scalar | Initial mismatches are flagged if the flow on a branch is greater than this value times the branch limit |
| `SEOZBRMis:4` | InitMis_ToleranceMult | Real | Yes | Inner Power Flow Loop\Initial Mismatch Tolerance Multiplier | Initial mismatch errors are only corrected if the mismatch is greater than this value times the solution tolerance |
| `SEOZBRMis:2` | InitMis_ZBR_MultNomHigh | Real | Yes | Inner Power Flow Loop\Initial Mismatch ZBR Multipler at High Nom kV | Initial Mismatch ZBR Multipler at High Nom kV |
| `SEOZBRMis` | InitMis_ZBRMultNomLow | Real | Yes | Inner Power Flow Loop\Initial Mismatch ZBR Multipler at Low Nom kV | Initial Mismatch ZBR Multipler at Low Nom kV |
| `SEOZBRMis:3` | InitMis_ZBR_NomHighKV | Real | Yes | Inner Power Flow Loop\Initial Mismatch ZBR Multipler High Nom kV | Initial Mismatch ZBR Multipler High Nom kV |
| `SEOZBRMis:1` | InitMis_ZBR_NomLowKV | Real | Yes | Inner Power Flow Loop\Initial Mismatch ZBR Multipler Low Nom kV | Initial Mismatch ZBR Multipler Low Nom kV |
| `MaxItr` |  | Integer | Yes | Inner Power Flow Loop\Max Iterations | Maximum number of iterations in the inner power flow loop |
| `MinVoltILoad` |  | Real | Yes | Inner Power Flow Loop\Minimum PU Voltage for Constant Current Loads | Minimum Per Unit Voltage for Constant Current Loads. If the voltage at the terminal bus falls below this value the load will decrease using a cosine function towards a value of zero load at zero voltage. |
| `MinVoltSLoad` |  | Real | Yes | Inner Power Flow Loop\Minimum PU Voltage for Constant Power Loads | Minimum Per Unit Voltage for Constant Power Loads. If the voltage at the terminal bus falls below this value the load will decrease using a cosine function towards a value of zero load at zero voltage. |
| `VarLimitBackoffVtol` |  | Real | Yes | Inner Power Flow Loop\Var Limit Backoff Voltage Tolerance | Tolerance on when to backoff generator Mvar limits based on how far the regulated the bus voltage is beyond the voltage setpoint. This controls the transition from a PQ to a PV bus. |
| `PVCEnforceAGC` | MWAGCIGOnlyAGCAble | String | Yes | Island-Based AGC\Injection Group Enforce Generator AGC | Island-based AGC Injection Group Enforce Generator AGC |
| `PVCEnforceGenMWLimits` | MWAGCIGEnforceGenMWLimits | String | Yes | Island-Based AGC\Injection Group Enforce Generator Limits | Island-based AGC Injection Group Enforce Generator Limits |
| `PVCEnforcePosLoad` | MWAGCIGPositiveLoad | String | Yes | Island-Based AGC\Injection Group Enforce Positive Load | Island-based AGC Injection Group Enforce Positive Load |
| `InjGrpName` | MWAGCIGName | String | Yes | Island-Based AGC\Injection Group Name | Island-based AGC Injection Group |
| `ConvergenceTol:3` | AGCToleranceMVA | Real | Yes | Island-Based AGC\Island AGC Convergence Tolerance in MVA | Island AGC Convergence Tolerance in MVA |
| `ConvergenceTol:1` | AGCTolerance | Real | Yes | Island-Based AGC\Island AGC Convergence Tolerance in PU | Island AGC Convergence Tolerance Note: In the AUX file, this value is written in per unit. Thus if SBase=100, then a 5 MW tolerance should be written as 0.05 |
| `UseAreaPartsMakeUpPower` | MWAGCAreaIsland | String | Yes | Island-Based AGC\Island Based AGC Type | Island Based AGC Type (Choices are U, G, A or I meaning Use Area/SuperArea, Gen, Area, or Injection Group) |
| `PVCQPowerFactMult` | MWAGCIGQMult | Real | Yes | Island-Based AGC\Multiplier for Mvar When Scaling Load | Multiplier for Mvar When Scaling Load for Island-Based AGC |
| `PVCPowerFac` | MWAGCIGPowerFact | Real | Yes | Island-Based AGC\Power Factor used When Scaling Load | Power Factor used When Scaling Load for Island-Based AGC |
| `PVCUseConstantPF` | MWAGCIGUseContantPF | String | Yes | Island-Based AGC\Use Constant Power Factor When Scaling Load | Use Constant Power Factor When Scaling Load for Island-Based AGC |
| `BusIdentifier` | LogID | String | Yes | Message Log\Bus Identifier | Message Log Bus Identifier |
| `LogColorLogging` | LogMWColor | Integer | Yes | Message Log\Color AGC Messages | Color AGC Messages |
| `LogColorLogging:1` | LogMvarColor | Integer | Yes | Message Log\Color Gen MVAR Messages | Color Gen MVAR Messages |
| `LogColorLogging:5` | LogOPFLPColor | Integer | Yes | Message Log\Color LP Variable Messages | Color LP Variable Messages |
| `LogColorLogging:2` | LogLTCColor | Integer | Yes | Message Log\Color LTC Messages | Color LTC Messages |
| `LogColorLogging:3` | LogPhaseColor | Integer | Yes | Message Log\Color Phase Shifter Messages | Color Phase Shifter Messages |
| `LogColorLogging:4` | LogShuntColor | Integer | Yes | Message Log\Color Switched Shunt Messages | Color Switched Shunt Messages |
| `IncludeNomVolt` | LogNomkV | String | Yes | Message Log\Include Nominal Voltage | Set to YES to show nominal voltage, if appropriate for the object, with object identifiers shown in the message log. |
| `Show` | LogShowContainerObjectCreate | String | Yes | Message Log\Show Container Object Create | Set to YES to show messages indicating that a container object has been created when creating a contained object when loading an auxiliary file. As an example, contingency elements can be created using the ContingencyElement data section. If an element is created for a contingency that does not already exist, the Contingency, i.e. the Container, will be created. |
| `LogDisableLogging` | LogMWSuppress | String | Yes | Message Log\Suppress AGC Messages | Suppress AGC Messages |
| `LogDisableLogging:1` | LogMvarSuppress | String | Yes | Message Log\Suppress Gen MVAR Messages | Suppress Gen MVAR Messages |
| `LogDisableLogging:5` | LogOPFLPSuppress | String | Yes | Message Log\Suppress LP Variable Messages | Suppress LP Variable Messages |
| `LogDisableLogging:2` | LogLTCSuppress | String | Yes | Message Log\Suppress LTC Messages | Suppress LTC Messages |
| `LogDisableLogging:3` | LogPhaseSuppress | String | Yes | Message Log\Suppress Phase Shifter Messages | Suppress Phase Shifter Messages |
| `LogDisableLogging:4` | LogShuntSuppress | String | Yes | Message Log\Suppress Switched Shunt Messages | Suppress Switched Shunt Messages |
| `ChkAreaInt` | ChkMWAGC | String | Yes | MW Control Loop\Check Automatic Generation Control (AGC) | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to perform the MW Control Loop to balance load and generation. Normally this is done by Area and/or SuperArea, but Island-Based AGC is also possible. |
| `EnforceGenMWLimits` |  | String | Yes | MW Control Loop\Enforce Generator MW limits | Set to YES to enforce the generator MW limits. Note that for economic modeling such as in the ED or OPF, generators MW limits are always enforced regardless of this option. |
| `UseLossFactorForDCTieLines` |  | String | Yes | MW Control Loop\Use Loss Factor for DC Tielines | Set to YES to use the aLoss factor for two-terminal DC lines when calculating MW metering flows for use in area interchange calculations. |
| `SEOUseConsolidation` | ConsolidationUse | String | Yes | Use Topology Processing Consolidation | Set to YES to automatically perform topology processing at the beginning of solution activities to consolidate branches marked for consolidation. |
| `SEOLTCTapBalance` | LTCTapBalance | String | Yes | Voltage Control Loop\Balance LTC Tap Ratios | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display so that the power flow solution will always try to maintain a balance of tap ratios for transformers that are in parallel with each other. |
| `ChkTaps:1` | ChkDCTaps | String | Yes | Voltage Control Loop\Check DC Transmission Transformer Tap Ratios | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow DC transmission lines to move transformer tap ratio control in the DC system solution. |
| `SEOCheckRegDFACTS` | ChkDFACTS | String | Yes | Voltage Control Loop\Check DFACTS | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow automatic DFACTS control in the voltage control loop. |
| `ChkPhaseShifters` |  | String | Yes | Voltage Control Loop\Check Phase Shifters | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow automatic phase shifter control in the voltage control loop. |
| `ChkShunts:1` | ChkSVCs | String | Yes | Voltage Control Loop\Check SVCs | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow automatic SVC (static var compensator) control in the voltage control loop. |
| `ChkShunts` |  | String | Yes | Voltage Control Loop\Check Switched Shunts | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow automatic switched shunt control in the voltage control loop. |
| `ChkTaps` |  | String | Yes | Voltage Control Loop\Check Transformer Tap Ratios | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow automatic transformer tap ratio control in the voltage control loop. |
| `DisableGenMVRCheck` |  | String | Yes | Voltage Control Loop\Disable Gen MVAR Check? | Set to YES to disable all Generator Mvar limit checking. Setting to YES means that generators can have any value of Mvar output to meet the voltage setpoint. |
| `ChkVars:1` | ChkVarBackoffImmediately | String | Yes | Voltage Control Loop\Generate Mvar Check Backoff Immediately | Set to YES to check whether to backoff generator Mvar limits in the inner power flow loop. This means that hitting a generator Mvar limit will not be evaluated after each inner loop iteration (but will still be handled in the voltage control loop). |
| `ChkVars` | ChkVarImmediately | String | Yes | Voltage Control Loop\Generate Mvar Check Immediately | Set to YES to check generator Mvar limits in the inner power flow loop. This means that both backing off limits and hitting a generator Mvar limit will be evaluated after each inner loop iteration. |
| `MaxItr:1` | MaxItrVoltLoop | Integer | Yes | Voltage Control Loop\Maximum Voltage Control Loop Iterations | Maximum number of Voltage Control Loop Iterations |
| `MinLTCSense` |  | Real | Yes | Voltage Control Loop\Minimum LTC Sensitivity | Transformer Tap ratios with voltage to tap sensitivities smaller than this value will not attempt to control the regulated bus voltage. If the transformer sensitivity later improves the transformer will automatically regain control. |
| `ModelPSDiscrete` |  | String | Yes | Voltage Control Loop\Model phase-shifters as discrete controls | Set to YES to force phase-shifters to have angles at the discrete steps defined. For most modeling, it is recommended the this be set to NO. |
| `PreventOscillations` |  | String | Yes | Voltage Control Loop\Prevent Controller Oscillations | Set to YES to prevent Generator Mvar limit, Transformer Tap Ratio, Phase Shifters, and Switched Shunt controller oscillations. If one of these devices begins to oscillate the control will be turned off. |
| `SEORemoteRegVarAlloc` | MvarSharingAllocation | String | Yes | Voltage Control Loop\Remote Regulation Mvar Allocation Type | Determines how generators regulating the same bus share the Mvars needed to maintain the voltage. Options are RegPerc, MinMaxRange, and SumRegPerc. |
| `SSContPFInnerLoop` | ShuntInner | String | Yes | Voltage Control Loop\Switched Shunts in Inner Power Flow Loop | UNCHECK box in the GUI dialog and set to YES in auxiliary file or case information display to allow continuous switched shunts to be treated as PV buses in the inner power flow loop. |
| `SEOTransformerSteppingMethodology` | TransformerStepping | String | Yes | Voltage Control Loop\Transformer Stepping Methodology | If value is "Coordinated", then transformers switching control will be coordinated between all transformers. If the value is "Self", then each transformer only looks at its own control. |
| `ZBRThreshold` |  | String | Yes | Voltage Control Loop\ZBR Threshold | This is the per unit impedance threshold below which Simulator will automatically determine groupings of buses which are connected by very low impedance branches. This effects the treatment of voltage regulation for devices which regulate a bus in this grouping. |

#### `Limit_Monitoring_Options` (1 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `LMS_IgnoreRadial` |  | String | Yes | Ignore Radial Elements |  |

#### `Sim_Environment_Options` (64 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `AutoSaveBaseCaseOnLoad` | DiffCaseSetBaseOnLoad | String | Yes | Environment\Auto Set Base Case on Load | When set to YES, the difference case Set as Present will be performed each time a case is loaded. |
| `AutoSolveOnLoad` | SolveOnLoad | String | Yes | Environment\Auto Solve after loading a case | When set to YES, a power flow solution will be performed each time a case is loaded |
| `AutoStart` | AnimateOnLoad | String | Yes | Environment\Auto start solution animimation | When set to YES, the animation will be started each time a case is loaded |
| `ShowBlackouts` | DisableShowBlackouts | String | Yes | Environment\Blackouts? | When set to YES, after a failed power flow solution a dialog will appear denoting that a black out has occurred. |
| `ClockStyle` | ShowClock | Integer | Yes | Environment\Clock Style | Clock Style |
| `GenAGCAble` | AGCDisableOnMWChange | String | Yes | Environment\Disable AGC When Manually Changing Gen MW | Normally when manually changing the MW output of a generator, the AGC status of the generator is automatically set to NO. Set this to YES to stop this. |
| `KiloOrMega` |  | Integer | Yes | Environment\Kilo Or Mega? | Kilo Or Mega? |
| `ShowLog` |  | String | Yes | Environment\Show Log | Set to YES to show the message log |
| `MeasurementUnits` |  | Integer | Yes | Environment\Units | Units |
| `SEOArchivePWBFileChecked` | AutoSaveDo | String | Yes | File Management\Archive Case When Save | Archive Case When Save |
| `SEOArchiveFileDelim` | AutoSaveDelim | String | Yes | File Management\Archive File Name Delimiter | Delimiter in Archive File Name |
| `SEAutoSaveFileLocationPath` | AutoSaveDirectory | String | Yes | File Management\Archive File Path Location | Specify a filepath in which the archived PWB file will be saved. If blank, the files will be saved in the current case file location. |
| `SEOMaxArchiveFileNum` | AutoSaveMaxFiles | Integer | Yes | File Management\Archive Maximum Number of Files | Maximum Number of Archive Files |
| `SEAutoLoadPath` | AutoLoadDirectory | String | read-only | File Management\Auto Load File Path Location | Specify a filepath in which files will be automatically loaded. At a user specified Auto Load Interval in seconds, this directory will be checked for new files and if new files are in the directory they will be loaded. |
| `SEAutoLoadInterval` | AutoLoadInterval | Integer | read-only | File Management\Auto Load Files Interval Seconds | Specify a time in seconds between the automatica loading of files in the Auto Load Path |
| `SEOAutoSaveIntervalMinutes` | AutoSaveInterval | Integer | Yes | File Management\Auto Save Interval (minutes) | Auto Save Interval (minutes) |
| `SEOSpecifiedAUXFile` | AutoLoadAUXCasesAll | String | Yes | File Management\Auxiliary File with ANY case | Auxiliary file that will be loaded when ANY case is opened. |
| `SEOAuxiliaryFile` | AutoLoadAUXCase | String | Yes | File Management\Auxiliary File with present case | Auxiliary file that will be loaded when the present case is opened. |
| `SEODoNotAutoLoadAuxilaryFile` | AutoLoadAUXCaseNotUse | String | Yes | File Management\Do Not Load Auxiliary File with Present Case | Set to YES to NOT load the auxiliary file that is loaded when the present case is opened. |
| `SEOCBTyp` | HDBExportCBTyp | String | Yes | File Management\hdbexport CBTyp mapping | String specifying the mapping of CBTyp strings to Simulator Branch Device Types. String should be semicolon delimited. First string is a CBTyp from the hdbexport file, second is the mapping to a Branch Device Type; third is another CBTyp; Fourth is Branch Device Type; and so on. |
| `CtgAutoInsOpenBreakers:1` | HDBExportCTGLRAS | String | Yes | File Management\hdbexport CTGL RAS | Set to Ignore or OPEN to determine how CTGL records with RAS=T are handled. If Ignore, then these CTGL records are ignored. If OPEN, then these CTGL records will be created as OPEN actions |
| `CtgAutoInsOpenBreakers` | HDBExportCTGLREDEF | String | Yes | File Management\hdbexport CTGL REDEF | Set to Ignore or OPEN to determine how CTGL records with REDEF=T are handled. If Ignore, then these CTGL records are ignored. If OPEN, then these CTGL records will be created as OPEN actions even when the CTG.ENREDEF=T (this flag indicates that other CTGL records should be read as OPENCBs actions.) |
| `Delim` | HDBExportDelim | String | Yes | File Management\hdbexport Delim Character | Character used as a delimiter when creating labels for devices when loading an hdbexport CSV file |
| `HDBExportNoDefaultLabels` |  | String | Yes | File Management\hdbexport No Default Labels | Set to YES so that no default labels are created |
| `UnitsType` | HDBExportTempUnits | String | Yes | File Management\hdbexport Temperature Units | Specify either Fahrenheit or Celsius. This determines the units assumed for temperature measurements when reading the RATING and WST records. |
| `HDBExportTranslateDCSystem` | HDBExportTranslateDC | String | Yes | File Management\hdbexport Translate DC System | Specify when to translate the POLE, VSC, DCND, DCCNV, and DCLN record into multi-terminal DC line systems. Choices are Never, Always, and Prompt. Prompt will bring up a dialog asking what to do when loading the file. |
| `SEOUseSpecifiedAUXFile` | AutoLoadAUXCasesAllUse | String | Yes | File Management\Load Auxiliary File with ANY case | Set to YES to load the auxiliary file that is loaded when ANY case is opened. |
| `SEOPromptToSaveChangedOnelines` | OnelinePromptSaveOnChange | String | Yes | File Management\Save Changed Onelines Do Not Prompt | Set to YES to prevent a prompt from appearing asking whether to save a changed oneline. |
| `SaveUnlinked` | UnlinkedElementsSave | String | Yes | File Management\Save Unlinked Elements | This option is stored with the Windows Registry. This option is overridden by the similar option stored with the PWB file. Set to YES to save unlinked elements of contingency, interface, and injection group records in the PWB file. Unlinked elements will be created after reading an auxiliary file with unlinked records or deleting an object being used by an existing contingency. |
| `SaveUnlinked:1` | UnlinkedElementsSaveForce | String | Yes | File Management\Save Unlinked Elements Force | This option is stored with the PWB file and overrides the option stored with the Windows Registry. Set to NO to obey the Window Registry option. Set to YES to save unlinked elements of contingency, interface, and injection group records in the PWB file. |
| `SEOScriptInputOutputDir` | ScriptTransferFileDirectory | String | Yes | FLD::Sim_Environment_Options_SEOScriptInputOutputDir | DSC::Sim_Environment_Options_SEOScriptInputOutputDir |
| `SEOScriptInputOutputDir:1` | ScriptTransferFileEnabled | String | Yes | FLD::Sim_Environment_Options_SEOScriptInputOutputDir:1 | DSC::Sim_Environment_Options_SEOScriptInputOutputDir:1 |
| `SEOScriptInputOutputSingle` | ScriptInputOutputPollSec | Real | Yes | FLD::Sim_Environment_Options_SEOScriptInputOutputSingle | DSC::Sim_Environment_Options_SEOScriptInputOutputSingle |
| `SEORotateOnelinesDelay` | ShortCutRotateOnelinesDelay | Integer | Yes | Keyboard Shortcuts\Oneline Rotation Delay | Oneline Rotation Delay |
| `SEORotateOnelinesEnabled` | ShortCutRotateOnelines | String | Yes | Keyboard Shortcuts\Oneline Rotation Enabled | Oneline Rotation Enabled |
| `MWTRAreaShowAll` | AreaDialogShowAllTransactions | String | Yes | Miscellaneous\Area Dialog Transactions List Show All Areas | Show All Study Areas |
| `SEOAutoUpdateOnelineFind` | FindOnelineAutoUpdate | String | Yes | Miscellaneous\Oneline Find Dialog Auto Update Oneline on Find | Auto Update Oneline on Find |
| `SEOTranslationAUX` | DDLTranslationAUX | Real | Yes | Oneline\Areva/Allstom Translation File | Areva/Allstom Import Xlate AUX |
| `OnelineBrowsingPath` |  | String | Yes | Oneline\Browsing Path | Path used when searching for onelines. |
| `DefaultOnelineFile` | OnelineDefault | String | Yes | Oneline\Default Oneline filename | Default Oneline |
| `UseDefaultOneline` | OnelineDefaultUse | String | Yes | Oneline\Default Oneline Use | Default Oneline? |
| `SEOSpecifiedAUXFile:2` | AutoLoadAXDAnyCase | String | Yes | Oneline\Display AXD File with ANY case | Display AXD file that will be loaded when a oneline is opened with ANY case. |
| `SEOSpecifiedAUXFile:1` | AutoLoadAXDThisCase | String | Yes | Oneline\Display AXD File with present case | Display AXD file that will be loaded when a oneline is opened with the present case. |
| `DisplayUnlinked` | OnelineDisplayUnlinkedRunMode | String | Yes | Oneline\Display Unlinked in Run Mode | Display Unlinked in Run Mode |
| `DisplayOnly` | AnimateNoSolving | String | Yes | Oneline\Do not solve while animating (Display Only) | Display Only? |
| `OOMouseWheelZoom` | OnelineMouseWheelZoom | String | Yes | Oneline\Enable Mouse Wheel Zooming |  |
| `SEOUseSpecifiedAUXFile:2` | AutoLoadAXDAnyCaseUse | String | Yes | Oneline\Load Display AXD File ANY present case | Set to YES to load the specified Display AXD file when a oneline is opened with ANY case. |
| `SEOUseSpecifiedAUXFile:1` | AutoLoadAXDThisCaseUse | String | Yes | Oneline\Load Display AXD File with present case | Set to YES to load the specified Display AXD file when a oneline is opened with the present case. |
| `MainOneLineFile` | OnelineMain | String | Yes | Oneline\Main Oneline filename | Main Oneline |
| `MinMetaFontSize` | OnelineMinPrintCopyFont | Real | Yes | Oneline\Minimum Print and Copy Font | Min Metafile Font |
| `MinScreenFontSize` | OnelineMinScreenFont | Real | Yes | Oneline\Minimum Screen Font | Min Screen Font |
| `DefaultOnelineFile:1` | OnelineSaveOnCaseSave | String | Yes | Oneline\Prompt for Saving Onelines when Saving Case | Prompt for Saving Onelines when Saving Case |
| `SaveContour` | OnelineSaveContour | String | Yes | Oneline\Save Contour with PWD file | Save Contour? |
| `SetGenMWToMinWhenOpenedFromOneline` | OnelineSetGenMWMinOnClose | String | Yes | Oneline\Set generator MW output to min when closed from oneline diagram | Set generator MW output to min when closed from oneline diagram |
| `ShowFull` | OnelineShowFull | String | Yes | Oneline\Show Full automatically when opening any oneline | Set to YES to automatically perform a "Show Full" every time any oneline is opened |
| `ShowHints` | OnelineHints | String | Yes | Oneline\Show Oneline Hints | Show Hints? |
| `ShowXY` | OnelineCoordinates | String | Yes | Oneline\Show X-Y or Lat-Long coordinates | Show XY Loc? |
| `XfmrSymbol` | OnelineXFSymbol | Integer | Yes | Oneline\Transformer Symbol Style | Xfmr Symbol Style |
| `SEOTranslationAUX:1` | DDLTranslationAUXAutoLoad | Real | Yes | Oneline\Use Areva/Allstom Translation File | Use Areva/Allstom Import Xlate Aux |
| `BlinkColor` | OnelineBlinkColor | Integer | Yes | Oneline\Visualize Outaged Blink Color | Blink Color |
| `BlinkInterval` | OnelineBlinkInterval | Integer | Yes | Oneline\Visualize Outaged Blink Interval | Blink Interval |
| `VisualizeOutagedObject:2` | OnelineOutX | String | Yes | Oneline\Visualize Outaged Generators with X | Highlight Offline Generators |
| `VisualizeOutagedObject:1` | OnelineOutBlink | String | Yes | Oneline\Visualize Outaged Objects as Blinking | Show Outaged Objects as blinking |
| `VisualizeOutagedObject` | OnelineOutDashed | String | Yes | Oneline\Visualize Outaged Objects with Dashes | Show Outaged Objects with Dashes |

#### `Sim_Simulation_Options` (19 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `TSBFileAutoLoad` |  | String | Yes | Auto load default *.tsb file |  |
| `TSBAutoRun` |  | String | Yes | Auto Run TSB |  |
| `TSBFileUpdateDefault` |  | String | Yes | Auto update default *.tsb file |  |
| `CostUnservedEnergy` |  | Real | Yes | Cost of Unserved Energy |  |
| `CurrentDay` |  | Integer | Yes | Current Day |  |
| `CurrentTime` |  | Real | Yes | Current Time |  |
| `TSBFileDefault` |  | String | Yes | Default *.tsb file |  |
| `EndDay` |  | Integer | Yes | End Day |  |
| `EndTime` |  | Real | Yes | End Time |  |
| `UseFixedTimeStep` |  | String | Yes | Fixed Time Step |  |
| `FreqModel` |  | Integer | Yes | Freq Model |  |
| `PowerBlockSize` |  | Real | Yes | MW Block Size |  |
| `NeverEnds` |  | String | Yes | Never Ends |  |
| `StartDay` |  | Integer | Yes | Start Day |  |
| `StartTime` |  | Real | Yes | Start Time |  |
| `TapDelay` |  | Real | Yes | Tap Delay |  |
| `TimeSpeedUp` |  | Real | Yes | Time Speed Up |  |
| `TransRampTime` |  | Real | Yes | Trans Ramp Time |  |
| `UseTapDelays` |  | String | Yes | Use Tap Delays? |  |

#### `MessLog_Options` (7 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `LogAutoEnableAuto` | AutoSaveEnable | String | Yes | Autowrite Enable | Set to YES to have the log automatically written to a file |
| `LogAutoWriteEveryXlines` | AutoSaveEveryXLines | Integer | Yes | Autowrite Every X Lines | When autowriting the log, the log will be written to the file after this number of lines |
| `LogAutoWriteEveryXSeconds` | AutoSaveEveryXSeconds | Integer | Yes | Autowrite Every X Seconds | When autowriting the log, the log will be written to the file after this number of seconds |
| `LogAutoFileName` | AutoSaveFileName | String | Yes | Autowrite Filename | When autowriting the log, this is the name of the file to which the log is written |
| `LogDisableLogging` | Disable | String | Yes | Disable Logging | Set to YES to turn off all message log messages |
| `LogMaxEntries` | MaxEntries | Integer | Yes | Maximum Lines in Log | Maximum number of lines of text in the message log |
| `LogUseTimeStamps` | TimeStampShow | Real | Yes | Use Time Stamps | Set to YES to have a time-stamp included on each line in the log which shows the time at which the line was generated |

#### `CaseInfo_Options` (32 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `CaseInfoBackgroundColor` | ColorBackground | Integer | Yes | Color\Background | Background Color |
| `CaseInfoBackgroundColorAlternating` |  | Integer | Yes | Color\Background Alternating | Background Color Alternating |
| `CaseInfoDataFillColor` | ColorDataFill | Integer | Yes | Color\Data Fill | DataFill Color |
| `CaseInfoEnterColor` | ColorEnterable | Integer | Yes | Color\Enterable | Enter Color |
| `CaseInfoHeadingBackgroundColor` | ColorHeadingBackground | Integer | Yes | Color\Heading Background | Heading Background Color |
| `SEOCaseInfoHighlightSelectedColor` | HighlightSelectedColor | Integer | Yes | Color\Highlight Selected | Highlight Selected Color |
| `CaseInfoLimitColor` | ColorLimit | Integer | Yes | Color\Limit Violation | Limit Color |
| `FontColor` |  | Integer | Yes | Color\Normal Font | Font Color |
| `CaseInfoNotUsedColor` | ColorNotUsed | Integer | Yes | Color\Not Used | Not Used Color |
| `CaseInfoSpecialExternalColor` | ColorSpecialExternal | Integer | Yes | Color\Special External Enterable | Special External Color |
| `CaseInfoToggleColor` | ColorToggleable | Integer | Yes | Color\Toggle | Toggle Color |
| `CaseInfoBackgroundAlternating` | ColorBackgroundAlternatingUse | String | Yes | Color\Use Background Alternating | Use Background Alternating |
| `CaseInfoColumnHeadingTypes` | ColumnHeadingType | String | Yes | Column Headings Type | Column Headings Type: Set to either Normal or Variable |
| `CaseInfoCopyIncludeColumnHeadings` | CopyIncludeColumnHeadings | String | Yes | Copy Include Column Options |  |
| `CaseInfoCopyIncludeKeyFields` |  | String | Yes | Copy Include Key Fields |  |
| `CaseInfoCopyIncludeObjectName` | CopyIncludeObjectName | String | Yes | Copy Include Object Name |  |
| `DisableCaseInfoRefresh` | DisableRefresh | String | Yes | Disable Case Info Refresh? |  |
| `FontName` |  | String | Yes | Font Name |  |
| `SOFontSize` | FontSize | Integer | Yes | Font Size |  |
| `FontStyles` |  | String | Yes | Font Styles |  |
| `SEOCaseInfoHighlightSelected` | HighlightSelected | String | Yes | Highlight Selected |  |
| `MetricsIgnoreBlanks` | MetricsBlank | Real | Yes | Ignore Blank Cells | Ignore Blank Cells for Metrics |
| `KeyFieldsToUseInSubdata` | KeyFieldsUse | String | Yes | Key Fields to use in Subdata |  |
| `CaseInfoRowHeight` | RowHeight | Integer | Yes | Row Height |  |
| `ShowCaseInfoHints` | ShowHints | String | Yes | Show Case Info Hints |  |
| `ShowMetricsHints` | MetricsShow | Real | Yes | Show Column Metrics | Show Column Metrics as Hints |
| `CaseInfoShowGridLines` | ShowGridlines | String | Yes | Show Grid Lines |  |
| `MetricsUseAbsolute` | MetricsAbsolute | Real | Yes | Use Absolute Values | Use Absolute Values for Metrics |
| `UseColumnHeadingWordWrap` | ColumnHeadingWordWrap | String | Yes | Use Column Headings Word Wrap |  |
| `UseVariableName` | UseConciseVariableNames | String | Yes | Use Concise Variable Names and Headers | Set to YES to use the concise variable names and also to use the concise header when writing out to an AUX file DATA section. |
| `UseDataMaintainerFiltering` | DataMaintainerFilter | String | Yes | Use Data Maintainer Filtering | Set to YES to enable DataMainainer Filtering on case information displays |
| `UseVariableName:1` | UseDefinedNamesInVariables | String | Yes | Use Defined Names In Variable Names | Set to YES to replace the location number in the variable name with the user-defined name for a field (if one exists). User-defined names can be specified with certain fields including CustomExpression, CustomExpressionStr, CustomFloat, CustomInteger, CustomString, BGCalcField, DataCheck, and DataCheckAggr. A variable name such as CustomExpression:1 would become "CustomExpression:My Expression Name". |

### Contingency analysis

#### `CTG_Options` (95 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `CTGResultStorageFile:1` | HardDriveFilename | String | Yes | Hard Drive Storage\Filename | Specify the name of the file to which to write hard drive results. You must set CTGSaveInHardDrive = YES to use this option |
| `CTGSaveFieldNormalName` | HardDriveUseColHead | String | Yes | Hard Drive Storage\Use Column Headers | Set to YES to store the column header when writing results to hard drive. Set to NO to store the variable name. |
| `CTGSaveInHardDrive` | HardDriveSave | String | Yes | Hard Drive Storage\Write to hard drive | Set to YES to store results to the hard drive when running contingency analysis. You then configure the CTGResultStorage object to indicate which fields to write to the file. |
| `FilterName` | InjSensFilterNameGen | String | Yes | Injection Sensitivities\Filter Name for Generators | Specify if generators should be included as injection points when determining injection sensitivities for a contingency violation. Valid entries are NONE (do not include generators), ONLINE (include only online generators), ALL (include all generators), SELECTED (only generators where Selected = Yes), AREAZONE (generators that meet the area/zone/owner filter), the name of an Advanced Filter, the name of a Device Filter, or a Filter Condition string. |
| `FilterName:1` | InjSensFilterNameLoad | String | Yes | Injection Sensitivities\Filter Name for Loads | Specify if loads should be included as injection points when determining injection sensitivities for a contingency violation. Valid entries are NONE (do not include loads), ONLINE (include only online loads), ALL (include all loads), SELECTED (only loads where Selected = Yes), AREAZONE (loads that meet the area/zone/owner filter), the name of an Advanced Filter, the name of a Device Filter, or a Filter Condition string. |
| `MaxCount:1` | InjSensMaxEffect | Integer | Yes | Injection Sensitivities\Max Count MW Effect | Maximum number of injection sensitivities to keep for a contingency violation when considering how a change in injection at the injection point will decrease the loading on the violation. The sensitivities that are kept are the specified number for both the impact of increasing injection and decreasing injection that have the greatest impact on reducing the loading of the violation. |
| `MaxCount` | InjSensMaxSens | Integer | Yes | Injection Sensitivities\Max Count Sensitivities | Maximum number of injection sensitivities to keep for a contingency violation. The sensitivities that are kept are the specified number of both the largest and smallest injection sensitivities affecting the violation. |
| `CTG_WhatToDoWithBC:2` | AlwaysReport | String | Yes | Limit Monitoring\Change always report violations | Set to YES to always report violations based on a change from the base case |
| `CTG_BCFlows:2` | AlwaysBranchInc | Real | Yes | Limit Monitoring\Change always report violations branch flow increase | Any branch flow change (expressed as a percentage of the post-contingency limit) above this threshold will be reported as a CHANGE contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:2 to YES |
| `CTG_BCHighVolt:2` | AlwaysHighVoltInc | Real | Yes | Limit Monitoring\Change always report violations high voltage increase | Any voltage increase above this threshold will be reported as a CHANGE contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:2 to YES. In AUX files, 5.2% is expressed as 0.052 |
| `CTG_BCInterface:2` | AlwaysInterfaceInc | Real | Yes | Limit Monitoring\Change always report violations interface flow increase | Any interface flow change (expressed as a percentage of the post-contingency limit) above this threshold will be reported as a CHANGE contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:2 to YES |
| `CTG_BCLowVolt:2` | AlwaysLowVoltDec | Real | Yes | Limit Monitoring\Change always report violations low voltage decrease | Any voltage decrease above this threshold will be reported as a CHANGE contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:2 to YES. In AUX files, 5.2% is expressed as 0.052 |
| `CTG_WhatToDoWithBC` | BCViolReport | String | Yes | Limit Monitoring\Change base case violations | Specify what to do with base case violations. 0 = do not report; 1 = report all; 2 = use change from base case criteria |
| `CTG_BCFlows` | BCViolBranchInc | Real | Yes | Limit Monitoring\Change base case violations branch flow increase | A base case branch violation will not be re-reported unless the flow increase is above this threshold. Must be enabled by setting the variable CTG_WHATTODOWITHBC to 2 |
| `CTG_BCHighVolt` | BCViolHighVoltInc | Real | Yes | Limit Monitoring\Change base case violations high voltage increase | A base case high voltage violation will not be re-reported unless the voltage increase is above this threshold. Must be enabled by setting the variable CTG_WHATTODOWITHBC to 2. In AUX files, 5.2% is expressed as 0.052 |
| `CTG_BCInterface` | BCViolInterfaceInc | Real | Yes | Limit Monitoring\Change base case violations interface flow increase | A base case interface violation will not be re-reported unless the flow increase is above this threshold. Must be enabled by setting the variable CTG_WHATTODOWITHBC to 2 |
| `CTG_BCLowVolt` | BCViolLowVoltDec | Real | Yes | Limit Monitoring\Change base case violations low voltage decrease | A base case low voltage violation will not be re-reported unless the voltage decrease is above this threshold. Must be enabled by setting the variable CTG_WHATTODOWITHBC to 2. In AUX files, 5.2% is expressed as 0.052 |
| `CTG_WhatToDoWithBC:1` | NeverReport | String | Yes | Limit Monitoring\Change never report violations | Set to YES to never report violations based on a change from the base case |
| `CTG_BCFlows:1` | NeverBranchInc | Real | Yes | Limit Monitoring\Change never report violations branch flow increase | Any branch flow change (expressed as a percentage of the post-contingency limit) below this threshold will not be reported as a contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:1 to YES |
| `CTG_BCHighVolt:1` | NeverHighVoltInc | Real | Yes | Limit Monitoring\Change never report violations high voltage increase | Any voltage increase below this threshold will be not be reported as a contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:1 to YES. In AUX files, 5.2% is expressed as 0.052 |
| `CTG_BCInterface:1` | NeverInterfaceInc | Real | Yes | Limit Monitoring\Change never report violations interface flow increase | Any interface flow change (expressed as a percentage of the post-contingency limit) below this threshold will be not reported as a contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:1 to YES |
| `CTG_BCLowVolt:1` | NeverLowVoltDec | Real | Yes | Limit Monitoring\Change never report violations low voltage decrease | Any voltage decrease below this threshold will not be reported as a contingency violation. Must be enabled by setting the variable CTG_WHATTODOWITHBC:1 to YES. In AUX files, 5.2% is expressed as 0.052 |
| `CTG_WhatToDoWithBC:3` | VoltChangePercent | String | Yes | Limit Monitoring\Change treat voltages in percentage | Set to YES to treat all voltage change values as a percentage of the pre-contingency voltage. If this value is NO, then 0.052 means a change in per unit voltage of 0.052. If this value is YES, then 0.052 means a change of 5.2% of pre-contingency voltage. |
| `IslandTotalBus` | IslandViolationMinBus | Integer | Yes | Limit Monitoring\Island Minimum Buses | When reporting contingency violations for islands, any island with less buses (or super bus) than this will not be reported. |
| `BGLoadMW` | IslandViolationMinLoadMW | Real | Yes | Limit Monitoring\Island Minimum Load MW | When reporting contingency violations for islands, any island with less load MW than this value will not be reported. |
| `Include` | IslandViolations | String | Yes | Limit Monitoring\Island Report Violations | Set to YES so that contingency violations are reported for islands that do not solve and islands that do not have enough MW reserves. |
| `CTGTPMonitorOnlySuperBus` | MonPrimaryBus | String | Yes | Limit Monitoring\Monitor only Superbus in Integrated Topology Processing | Set to YES to only monitor one bus inside each superbus for a voltage violation |
| `CTG_BCDiscBusReporting` | MonDiscBus | String | Yes | Limit Monitoring\Report disconnected bus | Set to YES to report disconnected buses as a contingency violation |
| `CTG_BCVoltSensThreshold` | MonVoltSensThres | Real | Yes | Limit Monitoring\Voltage sensitivity dV/dQ threshold | Any dV/dQ sensitivity which increases by this multiple will be reported as a contingency violation. Also any dV/dQ which become negative will always be reported as a violation. Must set CTG_BCVOLTSENSEREPORT to YES to enable this. |
| `CTG_BCVoltSensMonitorFilter` | MonVoltSensFilter | String | Yes | Limit Monitoring\Voltage sensitivity monitor filter | An advanced bus filter defining which buses will be monitored for changes in dV/dQ |
| `CTG_BCVoltSensReporting` | MonVoltSens | String | Yes | Limit Monitoring\Voltage sensitivity report | Set to YES to report changes in dV/dQ as a contingency violation. |
| `CTG_AlwaysSaveResults` |  | String | Yes | Miscellaneous\Always save results with the contingency list | Old option used before version 7. Now a dialog always appears asking you what to save when choosing to save an aux file from the contingency list. |
| `WhatActuallyOccuredContingencyDescription` |  | String | Yes | Miscellaneous\Contingency action description in what actually occurred | Specify how contingency action descriptions will appear in GUI and the What Actually Occurred results. Set to any of the following: NUMBER, NAME_KV, LABEL, PTI, PRETTY NAME, PRETTY NUMBER, PRETTY NAME_NUMBER |
| `CTGSaveInPWB` |  | String | Yes | Miscellaneous\Save contingency definitions and results in PWB file | Set to YES to store contingency results and definitions in the PWB file |
| `SaveUnlinked` | SaveUnlinkedElementObject | String | Yes | Miscellaneous\Save Unlinked Actions | Set to YES to save unlinked action objects with ContingencyElement, ContingencyPrimaryElement, and RemedialActionElement objects when writing to auxiliary files. |
| `CTGStoreLODFS` |  | String | Yes | Miscellaneous\SCOPF Storage and Reuse of LODFs | Set whether to store and reusing DC LODFs in the SCOPF calculation. 0 = None; 1 = stored in memory |
| `CTGLabel` | ContingencyActive | String | read-only | Modeling\Active Contingency | This is the contingency that is currently running. |
| `CTGLabel:1` | ContingencyPrimaryActive | String | read-only | Modeling\Active Primary Contingency | When running n-1-1 contingency analysis, this is the currently applied primary contingency. |
| `CTG_CalculationMethod` | CalculationMethod | String | Yes | Modeling\Calculation Method | Contingency Analysis Calculation Method. AC = Full Power Flow; DC = Linearized Lossless DC; DCPS = Linearized Lossless DC with Phase Shifters. When the Power Flow Solution Options are set to use the DC Power Flow, the only option is Full Power Flow. When in DC Power Flow mode, the impact of contingencies is determined using linear sensitivities and contingencies are not actually implemented. |
| `CTGOPT_AltPFCheckHighVolt` | AltPFCheckHighVolt | Real | Yes | Modeling\Check for Alternative Solution High Voltage | If buses are only checked for alternative solutions by voltage level, this is the mimimum high voltage |
| `CTGOPT_AltPFCheckLowVolt` | AltPFCheckLowVolt | Real | Yes | Modeling\Check for Alternative Solution Low Voltage | If buses are only checked for alternative solutions by voltage level, this is the maximum low voltage |
| `CTGOPT_AltPFCheck` | AltPFCheck | Integer | Yes | Modeling\Check for Alternative Solutions | If NO do not check for alternative solutions, otherwise check buses based on either a post-contingency low/high voltage range, or based on pre-contingency bus filters or based on post-contingency bus filters |
| `CTGSolutionOptions` | SolutionOptions | String | AUX/Paste | Modeling\Contingency Solution Options | Comma-delimited list of the form VarName1 = Value1, VarName2 = Value2, etc… Variable names are the same as those used for the SIM_SOLUTION_OPTIONS. Thus to disable shunts, taps, and phase shifters this value would be set to "ChkShunts = NO, ChkTaps = NO, ChkPhaseShifters = NO" |
| `DisableGenDropOverlap` |  | String | Yes | Modeling\Disable Gen Drop Overlap | Set to YES to disable Gen Drop Overlap management when using injection group contingency elements that drop generation in merit order. |
| `OPF_SolutionType` |  | Integer | Yes | Modeling\Do OPF Solution | Set to YES to solve the Optimal Power Flow solution during each contingency. The case must be generally configured to run an OPF solution before choosing this option. |
| `IterateOnActionStatus` |  | String | Yes | Modeling\Iterate On Action Status | Set to YES to model the impacts of actions with statuses other than CHECK in an iterative fashion. Certain model criteria for TOPOLOGYCHECK and POSTCHECK actions will be evaluated as part of a linear contingency state that has been updated due to already applied actions. If set to NO, all actions will be modeled as if they are CHECK actions, which means that they are evaluated under reference case conditions. |
| `AllowAmpLimits` |  | String | Yes | Modeling\Linearized DC Allow Amp Limits | Set to YES to approximate amp limits assuming a constant voltage magnitude when using the Linearized Lossless DC calculation methods. |
| `ReactivePowerModel` |  | String | Yes | Modeling\Linearized DC Reactive Power Model | Specify how to handle reactive power in the linear calculations; Ignore = Ignore reactive power; ConstVolt = assume constant voltage magnitude; ConstMvar = assume reactive power does not change. |
| `ConvergenceTol:2` | AGCToleranceMVA | Real | Yes | Modeling\Make-up power tolerance in MVA | Value specified in MVA. When using make-up power by Area or by Generator participation factors, Simulator ultimately dispatch each island independently with participation factor determining who makes-up changes in MW. A MW tolerance is needed to determine when this calculation is close enough and is specified here. |
| `ConvergenceTol` | AGCTolerance | Real | Yes | Modeling\Make-up power tolerance in per unit | Value specified in per unit. When using make-up power by Area or by Generator participation factors, Simulator ultimately dispatch each island independently with participation factor determining who makes-up changes in MW. A MW tolerance is needed to determine when this calculation is close enough and is specified here. Note: In the AUX file, this value is written in per unit. Thus if SBase=100, then a 5 MW tolerance should be written as 0.05 |
| `UseAreaPartsMakeUpPower` | MakeUpPower | String | Yes | Modeling\Make-up power use area part factors | Specify how to handle make-up power when performing contingency solutions. Choices are "Area Part Factors", "Gen Part Factors", or "Same as Power Flow". Recommended setting is "Gen Part Factors". |
| `CtgFileName:1` | PostCTGAuxFile | String | Yes | Modeling\Post-contingency auxiliary file | Immediately before solving a contingency when using the Full Power Flow Calculation Method, this auxiliary file will be loaded. |
| `CtgFileName:2` | PostCTGSolAuxFile | String | Yes | Modeling\Post-contingency solution auxiliary file | Immediately after solving a contingency this auxiliary file will be loaded. |
| `PreventIslandWithoutEnoughGen` |  | String | Yes | Modeling\Prevent Island Viability without enough generation | Set to YES to prevent a new electrical island from being created if there isn't enough controllable generation in the island. See help documentation for details. |
| `RetryRobustSolutionProcess` | RetryRobust | String | Yes | Modeling\Retry with robust solution | Set to YES to attempt a robust solution process after a solution failure |
| `TSTime` | TSModelMaxDelay | Real | Yes | Modeling\Transient Models Maximum Time Delay | When using transient stability models in contingency analysis, this is the maximum time delay for which a transient model will be treated as though it responds in the power flow contingency solution. Thus if transient relay model has a delay of 1000 seconds, and this value is set to 500 seconds then that transient relay model will not be treated as though it responds during the power flow contingency solution |
| `TSModelClass` | TSModelsTrip | String | Yes | Modeling\Transient Models to Act On | A comma-delimited list of transient model object types which Simulator will model in the simulation of contingency analysis solutions |
| `TSModelClass:1` | TSModelsMonitor | String | Yes | Modeling\Transient Models to Monitor Only | A comma-delimited list of transient model object types which Simulator will monitor in contingency analysis solutions with contingency violations reported as appropriate |
| `CTGUseSolutionOptions` | SolutionOptionsUseSpecific | String | Yes | Modeling\Use Contingency Solution Options | Set to YES if the defined contingency solution options should be used. Set to NO to ignore these options. |
| `RTCTGAnaMode` | UseIncTP | Integer | Yes | Modeling\Use Incremental Topology Processing | Set to YES to use incremental topology processing for contingency analysis. Setting to YES is recommended. |
| `DisableIfTrueInCTGReferenceState` | IgnoreRASIfTrueInRef | String | Yes | Remedial Actions\Disable if True in CTG Ref State | Set to YES to disable any remedial action elements where the Model Criteria evaluates to True in the contingency reference state. |
| `ScreenAllow` |  | String | Yes | Screening\Allow | Specify whether to perform any screening before running the full AC Contingency solutions. Choices are NO, YES, or OnlyScreen |
| `ScreenIncludeVoltage` |  | String | Yes | Screening\Include Voltage | Set to YES to include voltage screening as part of contingency screening. |
| `ScreenMaxItr` | ScreenVoltMaxItr | Integer | Yes | Screening\Max Iterations | Maximum number of inner power flow loop iterations to perform when doing voltage screening. |
| `ScreenMethod` |  | String | Yes | Screening\Method | Specify the method used for performing screening. Choices are DC or DCPS. |
| `ScreenNum` | ScreenNumBranch | Integer | Yes | Screening\Number of Branches | Specify the integer maximum number of branche violations that will force a full a full AC Solution on after performing screening. |
| `ScreenNum:2` | ScreenNumBus | Integer | Yes | Screening\Number of Buses | Specify the integer maximum number of bus voltage violations that will force a full a full AC Solution on after performing screening. |
| `ScreenNum:3` | ScreenNumBusPair | Integer | Yes | Screening\Number of BusPairs | Specify the integer maximum number of buspair violations that will force a full a full AC Solution on after performing screening. |
| `ScreenNum:1` | ScreenNumInterface | Integer | Yes | Screening\Number of Interfaces | Specify the integer maximum number of interface MW violations that will force a full a full AC Solution on after performing screening. |
| `ScreenIncludeVoltage:1` | ScreenVoltStoreViol | String | Yes | Screening\Store Voltage Violations | Set to YES to store voltage limit violations when including voltage as part of contingency screening. |
| `CTG_ReportMaxVioPerType` |  | Integer | Yes | Text File Report Writing\Maximum Violations to Report For Each Type | Options used for Text File Report Writing: Maximum Violations to Report For Each Type |
| `CTG_ReportAll` |  | String | Yes | Text File Report Writing\Report All | Options used for Text File Report Writing: Report All |
| `CTG_ReportBaseCaseOutages` |  | String | Yes | Text File Report Writing\Report Base Case Outages | Options used for Text File Report Writing: Report Base Case Outages |
| `CTG_ReportBranchChangeFlowVio` |  | String | Yes | Text File Report Writing\Report Branch Change Flow Violations | Options used for Text File Report Writing: Report Branch Change Flow Violations |
| `CTG_ReportBusHighVolt` |  | String | Yes | Text File Report Writing\Report Bus High Voltages | Options used for Text File Report Writing: Report Bus High Voltages |
| `CTG_ReportBusLowVolt` |  | String | Yes | Text File Report Writing\Report Bus Low Voltages | Options used for Text File Report Writing: Report Bus Low Voltages |
| `CTG_ReportBusVoltageExtremes` |  | String | Yes | Text File Report Writing\Report Bus Voltage Extremes | Options used for Text File Report Writing: Report Bus Voltage Extremes |
| `CTG_ReportCaseSummary` |  | String | Yes | Text File Report Writing\Report CaseSummary | Options used for Text File Report Writing: Report CaseSummary |
| `CTG_ReportCondense` |  | String | Yes | Text File Report Writing\Report Condense | Options used for Text File Report Writing: Report Condense |
| `CTG_ReportCreateTables` |  | String | Yes | Text File Report Writing\Report Create Tables | Options used for Text File Report Writing: Report Create Tables |
| `CTG_ReportFieldSeparator` |  | String | Yes | Text File Report Writing\Report Field Separator | Options used for Text File Report Writing: Report Field Separator |
| `CTG_ReportIDBusBy` |  | Integer | Yes | Text File Report Writing\Report ID Bus By | Options used for Text File Report Writing: Report ID Bus By |
| `CTG_ReportInactiveViolations` |  | String | Yes | Text File Report Writing\Report Inactive Violations | Options used for Text File Report Writing: Report Inactive Violations |
| `CTG_ReportInterfaceChangeFlowVio` |  | String | Yes | Text File Report Writing\Report Interface Change Flow Violations | Options used for Text File Report Writing: Report Interface Change Flow Violations |
| `CTG_ReportInterfaceFlow` |  | String | Yes | Text File Report Writing\Report Interface Flow Violations | Options used for Text File Report Writing: Report Interface Flow Violations |
| `CTG_ReportLargestBranchFlow` |  | String | Yes | Text File Report Writing\Report Largest Branch Flow | Options used for Text File Report Writing: Report Largest Branch Flow |
| `CTG_ReportLargestInterfaceFlow` |  | String | Yes | Text File Report Writing\Report Largest Inter Flow | Options used for Text File Report Writing: Report Largest Inter Flow |
| `CTG_ReportLineFlow` |  | String | Yes | Text File Report Writing\Report Line Flow Violations | Options used for Text File Report Writing: Report Line Flow Violations |
| `CTG_ReportMonitoredAreas` |  | String | Yes | Text File Report Writing\Report MonitoredAreas | Options used for Text File Report Writing: Report MonitoredAreas |
| `CTG_ReportMonitoredZones` |  | String | Yes | Text File Report Writing\Report MonitoredZones | Options used for Text File Report Writing: Report MonitoredZones |
| `CTG_ReportOnlyNonZero` |  | String | Yes | Text File Report Writing\Report Only Categories with Violations | Options used for Text File Report Writing: Report Only Categories with Violations |
| `CTG_ReportOnlyViolations` |  | String | Yes | Text File Report Writing\Report Only Violations | Options used for Text File Report Writing: Report Only Violations |
| `CTG_ReportOptionSettings` |  | String | Yes | Text File Report Writing\Report OptionSettings | Options used for Text File Report Writing: Report OptionSettings |
| `CTG_ReportVoltDecreaseVio` |  | String | Yes | Text File Report Writing\Report Volt Decrease Violations | Options used for Text File Report Writing: Report Volt Decrease Violations |
| `CTG_ReportVoltIncreaseVio` |  | String | Yes | Text File Report Writing\Report Volt Increase Violations | Options used for Text File Report Writing: Report Volt Increase Violations |

#### `CTG_AutoInsert_Options` (56 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `DOCBranchVoltageTreatment` | kVBranchEnd | String | Yes | Branch Voltage Treatment |  |
| `BusIdentifier` | NameID | String | Yes | Bus Identifier |  |
| `CtgAutoInsCombinationVal:3` | ComboCountBus | Integer | Yes | Combination Value for buses |  |
| `CtgAutoInsCombinationVal:2` | ComboCountGen | Integer | Yes | Combination Value for generators |  |
| `CtgAutoInsCombinationVal` | ComboCountLine | Integer | Yes | Combination Value for lines |  |
| `CtgAutoInsCombinationVal:1` | ComboCountXF | Integer | Yes | Combination Value for transformers |  |
| `CtgAutoInsDeleteExistCtgs` | DeleteExisting | String | Yes | Delete Existing Contingencies |  |
| `Duration` | TSDuration | Real | Yes | Duration |  |
| `CtgAutoInsElementFilter:4` | Filter3WXF | String | Yes | Element Filter for 3 winding transformers |  |
| `CtgAutoInsElementFilter:2` | FilterBus | String | Yes | Element Filter for buses |  |
| `CtgAutoInsElementFilter:1` | FilterGen | String | Yes | Element Filter for generators |  |
| `CtgAutoInsElementFilter:6` | FilterLineShunt | String | Yes | Element Filter for line shunts |  |
| `CtgAutoInsElementFilter` | FilterLine | String | Yes | Element Filter for lines |  |
| `CtgAutoInsElementFilter:7` | FilterLoad | String | Yes | Element Filter for loads |  |
| `CtgAutoInsElementFilter:5` | FilterSubstation | String | Yes | Element Filter for substations |  |
| `CtgAutoInsElementFilter:3` | FilterShunt | String | Yes | Element Filter for switched shunts |  |
| `CtgAutoInsElementType` | ElementType | String | Yes | Element Type |  |
| `FaultLocation` | TSFaultLocation | Real | Yes | Fault Location |  |
| `BranchDeviceType` | FilterOnlyLineXFSeries | String | Yes | Filter Only BranchDeviceType of Line XF or Series Cap |  |
| `Include3WXfifFoundWithXf` | Handle3WXF | String | Yes | Include 3WXf if Found in XF |  |
| `IncludeNomVolt` | NameNomVolt | String | Yes | Include Nominal Voltage |  |
| `DOCMaxkV` | kVMax | Real | Yes | Maximum kV Voltage |  |
| `DOCMinkV` | kVMin | Real | Yes | Minimum kV Voltage |  |
| `MeasType` | IncludeWithinType | String | Yes | MType |  |
| `CtgAutoInsPrefix:5` | NamePrefix3WXF | String | Yes | Numeric Field Prefix for 3 winding transformers |  |
| `CtgAutoInsPrefix:3` | NamePrefixBus | String | Yes | Numeric Field Prefix for buses |  |
| `CtgAutoInsPrefix:2` | NamePrefixGen | String | Yes | Numeric Field Prefix for generators |  |
| `CtgAutoInsPrefix:7` | NamePrefixLineShunt | String | Yes | Numeric Field Prefix for line shunts |  |
| `CtgAutoInsPrefix` | NamePrefixLine | String | Yes | Numeric Field Prefix for lines |  |
| `CtgAutoInsPrefix:8` | NamePrefixLoad | String | Yes | Numeric Field Prefix for loads |  |
| `CtgAutoInsPrefix:6` | NamePrefixSubstation | String | Yes | Numeric Field Prefix for substations |  |
| `CtgAutoInsPrefix:4` | NamePrefixShunt | String | Yes | Numeric Field Prefix for switched shunts |  |
| `CtgAutoInsPrefix:1` | NamePrefixXF | String | Yes | Numeric Field Prefix for transformers |  |
| `CtgAutoInsOnlyIncludeWithin` | IncludeWithin | String | Yes | Only Include Elements |  |
| `CtgAutoInsOnlyIncludeWithinBus` | IncludeWithinBus | Integer | Yes | Only Include Elements Bus |  |
| `CtgAutoInsOnlyIncludeWithinNum` | IncludeWithinCount | Integer | Yes | Only Include Elements Value |  |
| `Side` |  | String | Yes | Open Both Action |  |
| `CtgAutoInsOpenBreakers` | OpenBreakers | String | Yes | Open Breakers |  |
| `CTGAutoParallelCommon` | ParallelCommon | String | Yes | Parallel or Common |  |
| `CtgAutoInsPreventIdenticalBreakers` | PreventIdentical | String | Yes | Prevent Identical Breakers |  |
| `Integer` |  | Integer | Yes | Reclose Attempts |  |
| `Duration:1` |  | Real | Yes | Reclose Interval |  |
| `SelfClear:1` | TSSelfClearOpen | String | Yes | Self Clear Fault Open Devices |  |
| `SelfClear` | TSSelfClear | String | Yes | Self Clearing Fault |  |
| `StartTime` | TSFaultTime | Real | Yes | Start Time |  |
| `DOCUseAllkV` | kVAll | String | Yes | Use All kV Voltages? |  |
| `CtgAutoInsUseAreaZoneFilters` | PrefilterAreaZone | String | Yes | Use Area/Zone Filters |  |
| `CtgAutoInsUseElementFilter:4` | Filter3WXFUse | String | Yes | Use Element Filter for 3 winding transformers |  |
| `CtgAutoInsUseElementFilter:2` | FilterBusUse | String | Yes | Use Element Filter for buses |  |
| `CtgAutoInsUseElementFilter:1` | FilterGenUse | String | Yes | Use Element Filter for generators |  |
| `CtgAutoInsUseElementFilter:6` | FilterLineShuntUse | String | Yes | Use Element Filter for line shunts |  |
| `CtgAutoInsUseElementFilter` | FilterLineUse | String | Yes | Use Element Filter for lines |  |
| `CtgAutoInsUseElementFilter:7` | FilterLoadUse | String | Yes | Use Element Filter for loads |  |
| `CtgAutoInsUseElementFilter:5` | FilterSubstationUse | String | Yes | Use Element Filter for substations |  |
| `CtgAutoInsUseElementFilter:3` | FilterShuntUse | String | Yes | Use Element Filter for switched shunts |  |
| `UseNormalStatus` |  | String | Yes | Use Normal Status of Branches for Bus Groupings |  |

#### `CTGPrimary_Options` (6 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `CTGLabel` |  | String | read-only | Modeling\Active Contingency | This is the contingency that is currently running. |
| `CTG_CalculationMethod` | CalculationMethod | String | Yes | Modeling\Calculation Method | Contingency Analysis Calculation Method. AC = Full Power Flow; DC = Linearized Lossless DC; DCPS = Linearized Lossless DC with Phase Shifters. When the Power Flow Solution Options are set to use the DC Power Flow, the only option is Full Power Flow. When in DC Power Flow mode, the impact of contingencies is determined using linear sensitivities and contingencies are not actually implemented. |
| `CTGSolutionOptions` | SolutionOptions | String | AUX/Paste | Modeling\Contingency Solution Options | Comma-delimited list of the form VarName1 = Value1, VarName2 = Value2, etc… Variable names are the same as those used for the SIM_SOLUTION_OPTIONS. Thus to disable shunts, taps, and phase shifters this value would be set to "ChkShunts = NO, ChkTaps = NO, ChkPhaseShifters = NO" |
| `Reference:1` | RefPostCTGPriLimitMonitoring | String | Yes | Modeling\Post CTG Primary Limit Monitoring Reference | Set to YES to use the system state following the solution of the primary contingency as the reference state for determining limit monitoring violations that compare the contingency state to a base reference state when determining secondary contingency violations. |
| `Reference` | RefPostCTGPriRemedialCTGActions | String | Yes | Modeling\Post CTG Primary Remedial Action Reference | Set to YES to use the system state following the solution of the primary contingency as the reference state for solving remedial actions for secondary contingencies. This reference will also be used for the original value when solving secondary contingency actions that require a change from the reference, e.g., percent MW changes. |
| `CTGUseSolutionOptions` | SolutionOptionsUseSpecific | String | Yes | Modeling\Use Contingency Solution Options | Set to YES if the defined contingency solution options should be used. Set to NO to ignore these options. |

#### `CTGWriteAux_Options` (32 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `String:17` | ConvertBlocksAndGlobalActions | String | Yes | Convert Blocks and Global Actions | Set to YES to convert contingency blocks and global actions before saving any definitions. |
| `String:11` | SaveDefContingency | String | Yes | Definitions\Save Contingency | Set to YES to save contingency definitions. |
| `String:20` | SaveDefContingencyPrimary | String | Yes | Definitions\Save Contingency Primary | Set to YES to save primary contingency definitions. These are used with CTG Combo Analysis. |
| `String:22` | SaveDefCustomFields | String | Yes | Definitions\Save Custom Fields | Set to YES to save calculated fields and custom expressions that are used by other objects being saved. |
| `String:13` | SaveDefCustomMonitor | String | Yes | Definitions\Save Custom Monitor | Set to YES to save custom monitor definitions. |
| `String:4` | SaveDefDataGrid | String | Yes | Definitions\Save Data Grid | Set to YES to save Case Info Customizations (DataGrid object) for contingency related case information displays. |
| `String:15` | SaveDefFilter | String | Yes | Definitions\Save Filter | Set to YES to save advanced filters that are used by other objects being saved. |
| `String:8` | SaveDefInjectionGroup | String | Yes | Definitions\Save Injection Group | Set to YES to save injection group definitions. |
| `String:7` | SaveDefInterface | String | Yes | Definitions\Save Interface | Set to YES to save interface definitions. |
| `String:2` | SaveDefLimitMonitoring | String | Yes | Definitions\Save Limit Monitoring | Set to YES to save Limit Monitoring Settings. |
| `String:16` | SaveDefLimitMonitoringCost | String | Yes | Definitions\Save Limit Monitoring Cost | Set to YES to save limit monitoring cost functions. |
| `String:14` | SaveDefModelCriteria | String | Yes | Definitions\Save Model Criteria | Set to YES to save model condition, model filter, model expression, model plane, and model result override objects. |
| `String:12` | SaveDefRemedialAction | String | Yes | Definitions\Save Remedial Action | Set to YES to save remedial action definitions. |
| `String` | SaveDefContingencyUnlinked | String | Yes | Definitions\Save Unlinked Contingency Actions | Set to YES to save Contingency, Contingency Primary, and Remedial Action elements where the action object is unlinked. |
| `String:18` | SaveDefVoltageControlGroup | String | Yes | Definitions\Save Voltage Control Group | Set to YES to save voltage control group definitions. |
| `String:24` | KeyField | String | Yes | Key Field | Specify the key field to use when saving objects. Options are PRIMARY, SECONDARY, and LABEL. |
| `String:1` | SaveOptionsContingency | String | Yes | Options\Save Contingency | Set to YES to save options for running contingency analysis. |
| `String:19` | SaveOptionsContingencyPrimary | String | Yes | Options\Save Contingency Primary | Set to YES to save options for solving primary contingencies as part of CTG Combo Analysis. |
| `String:9` | SaveOptionsDistributedComputing | String | Yes | Options\Save Distributed Computing | Set to YES to save distributed computing options. |
| `String:3` | SaveOptionsPowerFlow | String | Yes | Options\Save Power Flow | Set to YES to save power flow solution options. |
| `String:10` | SaveOptionsContingencySuppress | String | Yes | Options\Save Suppress Contingency | Set to YES to suppress saving generator and load options when saving options for running contingency analysis. |
| `String:5` | SaveResultsContingency | String | Yes | Results\Save Contingency | Set to YES to save contingency results. |
| `String:21` | SaveResultsCTGCombo | String | Yes | Results\Save CTG Combo | Set to YES to save CTG Combo Analysis results. |
| `String:6` | SaveResultsInactive | String | Yes | Results\Save Inactive | Set to YES to save inactive contingency violations. |
| `String:23` | SaveDependencies | String | Yes | Save Dependencies | Set to YES to save all relevant objects that are needed to define the objects that are selected to be saved. Set to NO to only save the objects that are selected to be saved. |
| `String:31` | UseAreaZoneFilters | String | Yes | Use Area/Zone Filters | Set to YES to save only the information for objects that meet the Area, Zone, Owner filters. This affects objects related to contingency options and limit monitoring settings. |
| `String:26` | UseConcise | String | Yes | Use Concise | Set to YES to use the concise variablenames and headers. |
| `String:30` | UseDataMaintainers | String | Yes | Use Data Maintainers | Set to YES to save only the information belonging to selected data maintainers. |
| `String:25` | UseDATASection | String | Yes | Use DATA Section | Set to YES to use DATA sections instead of SUBDATA sections. |
| `String:27` | UseObjectIDs | String | Yes | Use Object IDs | Set to YES to use the ObjectID field instead of other key fields when identifying objects. This will simplify the auxiliary file by using a single identifying field rather than multiple key fields that change based on the type of object. |
| `String:29` | UseObjectIDs3WXformer | String | Yes | Use Object IDs 3WXformer | Set to YES to write out a three-winding transformer using the buses as the three terminals of the transformer followed by the circuit ID with the first bus listed being the particular winding that is desired. Set to NO to write out a particular winding with its terminal bus, the star bus of the transformer, and the circuit ID of the transformer. For this option to be used the "Use Object IDs" field must also be set to YES. |
| `String:28` | UseObjectIDsMSLine | String | Yes | Use Object IDs MSLine | Set to YES to save lines that are part of a multi-section line by identifying by the from bus, to bus, and circuit ID of the multi-section line followed by the number of the particular section. If set to NO, individual sections will be written based on their from bus, to bus, and circuit ID. For this option to be used the "Use Object IDs" field must also be set to YES. |

#### `Distributed_Options` (12 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `ATCUseDistributedComputing` |  | String | Yes | ATC Use Distributed Computing |  |
| `CTGComboUseDistributedComputing` |  | String | Yes | CTG Combo Use Distributed Computing |  |
| `CTGUseDistributedComputing` |  | String | Yes | CTG Use Distributed Computing |  |
| `DistMasterPasswordHash` |  | String | Yes | Dist Auth Master Password Hash |  |
| `ATCNumberPerProcess` |  | Integer | Yes | Number of ATC Directions Per Process |  |
| `CTGComboNumberPerProcess` |  | String | Yes | Number of Contingencies Per Combo Process |  |
| `CTGNumberPerProcess` |  | Integer | Yes | Number of Contingencies Per Process |  |
| `NumberPerProcess:1` | PVNumberPerProcess | Integer | Yes | PV Number of Contingencies Per Process |  |
| `UseDistributedComputing:1` | PVUseDistributedComputing | String | Yes | PV Use Distributed Computing |  |
| `NumberPerProcess` | QVNumberPerProcess | Integer | Yes | QV Number of Buses or CTGs Per Process |  |
| `UseDistributedComputing` | QVUseDistributedComputing | String | Yes | QV Use Distributed Computing |  |
| `TSUseDistributedComputing` |  | String | Yes | TS Use Distributed Computing |  |

### OPF, SCOPF and unit commitment

#### `OPF_Options` (59 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `OPFGenAllowCommitment` |  | String | Yes | Allow OPF Gen Commitment |  |
| `OPFGenAllowDecommitment` |  | String | Yes | Allow OPF Gen Decommitment |  |
| `OPFBusMaxViolCost` |  | Real | Yes | Bus Angle Max Violation Cost |  |
| `OPFCalculateBusReactiveLMP` |  | String | Yes | Calculate Q Marginal Cost |  |
| `OPFDFACTSCost` |  | Real | Yes | D-FACTS Cost |  |
| `OPF_DisableACE` |  | String | Yes | Disable ACE |  |
| `OPF_DisAreaTrans` |  | String | Yes | Disable Area Transactions |  |
| `OPFDisBusEnforce` |  | String | Yes | Disable Bus Angle |  |
| `OPF_DisDCLineMW` |  | String | Yes | Disable DC Line MW |  |
| `OPFDisDFACTSXinj` |  | String | Yes | Disable DFACTS Control |  |
| `OPF_DisGenMW` |  | String | Yes | Disable Generator MW |  |
| `OPF_DisIntEnforce` |  | String | Yes | Disable Interface Enforcement |  |
| `OPF_DisLineEnforce` |  | String | Yes | Disable Line Enforcement |  |
| `OPF_DisGenMW:1` |  | String | Yes | Disable Load MW |  |
| `OPF_DisPhaseShift` |  | String | Yes | Disable Phase Shifter |  |
| `OPFDisableXFRegPSEnforce` |  | String | Yes | Disable Phase Shifter Regulation Limit Enforcement |  |
| `OPF_GenCostModel` |  | Integer | Yes | Generator Cost Model |  |
| `OPFIncludeReserveRequirements` |  | String | Yes | Include OPF Reserve Requirements |  |
| `OPF_IntCorrectTol` |  | Real | Yes | Interface Correction Tolerance |  |
| `OPF_IntMaxViolCost` |  | Real | Yes | Interface Max Violation Cost |  |
| `OPF_IntMWRelease` |  | Real | Yes | Interface MW Release |  |
| `OPF_LineCorrectTol` |  | Real | Yes | Line Correction Tolerance |  |
| `OPF_LineMaxViolCost` |  | Real | Yes | Line Max Violation Cost |  |
| `OPF_LineMVARelease` |  | Real | Yes | Line MVA Release |  |
| `OPF_LoadControlPFOption` |  | Integer | Yes | Load Power Factor Option |  |
| `OPFPFUpdateGenChange` |  | Real | Yes | LP OPF Min Gen Change | Power Flow Recalculation Gen MW Change Threshold in per unit |
| `OPFPFUpdate` |  | Integer | Yes | LP OPF PF Update | Power Flow Recalculation Criteria |
| `OPF_MaxLPIterations` |  | Integer | Yes | Max LP Iterations |  |
| `SCOPFMaxElementCTGViol` |  | Integer | Yes | Max. SCOPF Element CTG Violations | Maximum number of violations that will be included in the SCOPF constraints for EACH defined contingency. |
| `OPF_MinControlSense` |  | Real | Yes | Min Control Sensitivity |  |
| `OPF_MinPhaseShiftSense` |  | Real | Yes | Min Phase Shifter Sensitivity |  |
| `OPF_MWPerSegment` |  | Integer | Yes | MW per Segment |  |
| `OPF_ObjFunc` |  | Integer | Yes | Objective Function |  |
| `BusObjectOnline` |  | String | Yes | Only Online in Injection Group | Set to YES to only include online devices when calculating marginal costs for injection groups. |
| `OPFAreaInitPFControl` |  | String | Yes | OPF Area Initial PF Control |  |
| `OPFAreaStandAlonePFControl` |  | String | Yes | OPF Area Stand-alone PF Control |  |
| `OPFCyclingMinItr` |  | Integer | Yes | OPF Cycling Minimum Itrs |  |
| `OPFCyclingRowMult` |  | Integer | Yes | OPF Cycling Minimum Row Multiplier |  |
| `OPFGenFastStartTurnOnPercent` |  | String | Yes | OPF Fast Start Turn On Percent |  |
| `OPFSaveTableauInPWB` |  | String | Yes | OPF Save Tableau in PWB |  |
| `OPFUseLastTableau` |  | String | Yes | OPF Start From Last Tableau | Set to Yes will initialize the starting tableau for the SCOPF with binding constraints from the previous SCOPF solution. |
| `OPFBranchUseMW` |  | String | Yes | OPF Use MW Line Limits |  |
| `OPFDCPhaseShifterMaxLimitChange` |  | Integer | Yes | OPFDCPhaseShifterMaxLimitChange |  |
| `OPFGroupOption` |  | String | Yes | OPFGroupOption | Set to YES to distribute change of generators with the same cost |
| `OPF_PhaseShiftCost` |  | Real | Yes | Phase Shifter Cost |  |
| `OPFXFRegPSInRangeCost` |  | Real | Yes | Phase Shifter Inrange Cost |  |
| `OPFXFRegPSMaxViolCost` |  | Real | Yes | Phase Shifter Max Violation Cost |  |
| `OPF_PtsPerCurve` |  | Integer | Yes | Points per Curve |  |
| `OPF_SaveLinCurve` |  | String | Yes | Save Linear Curve |  |
| `SCOPFBaseCaseMethod` |  | String | Yes | SCOPF Basecase Solution Method | Specify whether to use a standard power flow or an optimal power flow solution as the initial solution of the SCOPF calculation. 0 = PF, 1 = OPF. |
| `SCOPFMaxOuterLoopItr` |  | Integer | Yes | SCOPF Max Outer Loop Itr | Maximum number of times the SCOPF algorithm will find a resulting generation dispatch, and then repeat the process to look for new constraints that require additional generation changes. |
| `SCOPFOuterLoopType` |  | Integer | Yes | SCOPF Outer Loop Type |  |
| `SCOPFRadialLoad` |  | Integer | Yes | SCOPF Radial Load | Choose to flag but not include, ignore, or include contingent violations that feed radial loads as SCOPF constraints. 0 = flag, 1 = ignore, 2 = include. |
| `SCOPFUseMustInclude` |  | String | Yes | SCOPF Use Must Include | Set to Yes will include contingent violations that were binding in the last SCOPF solution as part of the constraint set for a new SCOPF calculation. |
| `SCOPFSetSolutionCARef` |  | String | Yes | Set Solution as Contingency Reference | Set to Yes will store the resulting SCOPF solution as the reference state for the contingency analysis. |
| `OPFShowLMPComponents` |  | String | Yes | Show Bus LMP Components |  |
| `LPSolutionTrace` |  | Integer | Yes | Trace LP Solution |  |
| `OPFIncludeUnenforceCost` |  | String | Yes | Treat area MW constraints with Small ACE as Unenforceable | Set to NO means to not treat area (or SuperArea) MW constraints as unenforceable if the ACE value is less than the AGC Tolerance for the Area (or SuperArea) |
| `OPFValidSolutionOnMaxITR` |  | String | Yes | Valid LPOPF Solution on Max ITR |  |

#### `UC_Options` (6 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `UCLambdaTolerance` |  | Real | Yes | Lambda Tolerance ($/MWh |  |
| `UCMaxItr` |  | Integer | Yes | Maximum UC Iterations |  |
| `UCStoreTPGenMW` |  | String | Yes | Store UC Gen MW Output |  |
| `UCStoreTPGenProfit` |  | String | Yes | Store UC Gen Profit |  |
| `TimeStep` |  | Real | Yes | Time Step |  |
| `UCDualityGapTol` |  | Real | Yes | UC Duality Gap Tolerance |  |

### Sensitivities and transfer

#### `PTDF_Options` (2 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `Injector` | InjectionLocation | String | Yes | Assumed Injection Location | Assumed location of injection for the distribution factor calculation. This is used when a bus is the injector for a distribution factor and a generator and/or load at that bus has been outaged due to a contingency or the bus itself has been outaged. The distribution factor will be modified to account for the outaged element(s) based on the following option choices: BUS - assume the injection is at the bus and only modify the distribution factor if the bus is outaged, GEN - assume the injection is at a generator at the bus and only modify if an online generator is outaged, LOAD - assume that the injection is at a load at the bus and only modify if an online load is outaged, GENLOAD - assume that the injection is at a generator or load at the bus and only modify if an online generator or load is outaged. |
| `ATC_LinCalcMethod` | LinearCalcMethod | String | Yes | Linear Calculation Method |  |

#### `LODF_Options` (1 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `ATC_LinCalcMethod` | LinearCalcMethod | String | Yes | Linear Calculation Method |  |

#### `TLR_Options` (7 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `BGAGC` | EnforceAGC | String | Yes | AGC Status |  |
| `TLRCalculationAppend` | AppendCalc | String | Yes | Append Calculation |  |
| `Injector` | InjectionLocation | String | Yes | Assumed Injection Location | Assumed location of injection for the distribution factor calculation. This is used when a bus is the injector for a distribution factor and a generator and/or load at that bus has been outaged due to a contingency or the bus itself has been outaged. The distribution factor will be modified to account for the outaged element(s) based on the following option choices: BUS - assume the injection is at the bus and only modify the distribution factor if the bus is outaged, GEN - assume the injection is at a generator at the bus and only modify if an online generator is outaged, LOAD - assume that the injection is at a load at the bus and only modify if an online load is outaged, GENLOAD - assume that the injection is at a generator or load at the bus and only modify if an online generator or load is outaged. |
| `BranchDeviceType` | CloseBreaker | String | Yes | Close Disconnected Using Breaker | Set to YES if Breakers should be closed to connect a disconnected bus that contains generators or loads. Only Breakers in series with a bus will be closed. If NO, shift factors will be 0 for disconnected buses. |
| `BranchDeviceType:1` | CloseLoadBreakDisconnect | String | Yes | Close Disconnected Using Load Break Disconnect | Set to YES if Load Break Disconnects should be closed to connect a disconnected bus that contains generators or loads. Only Load Break Disconnects in series with a bus will be closed. If NO, shift factors will be 0 for disconnected buses. |
| `ATC_LinCalcMethod` | LinearCalcMethod | String | Yes | Linear Calculation Method |  |
| `BusObjectOnline` | InjGroupOnlyOnline | String | Yes | Only Online in Injection Group | Set to YES to only include online devices when calculating injection group sensitivities for Shift Factor calculations. |

#### `ATC_Options` (33 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `AllowAmpLimits` |  | String | Yes | Allow Amp Limits | Set to YES to allow amp limits in the linear calculations by assuming a constant voltage magnitude |
| `GenEnforceMWLimits:1` | GenLimitEnforce | String | Yes | Allow Generator MW Limit Enforcement in Single Linear Step | When set to YES, generator MW limits will be enforced for areas, zones, and superareas (either as the source or sink) if all criteria for generator MW limit enforcement are met. For injection groups (either as the source or sink) the criteria for Allow Only AGC Units to Vary, Enforce Unit MW Limits, and Do Not Allow Negative Loads will all be checked and enforced if necessary. When set to NO all of the options specified will be treated as FALSE. This option applies when doing the Single Linear Step method either as a standalone method or part of one of the iterated methods. When using the Economic Merit Order Dispatch method with injection groups, these options will always be checked and limits will be enforced if necessary regardless of this option setting. |
| `Injector` | InjectionLocation | String | Yes | Assumed Injection Location | Assumed location of injection for the distribution factor calculation. This is used when a bus is the injector for a distribution factor and a generator and/or load at that bus has been outaged due to a contingency or the bus itself has been outaged. The distribution factor will be modified to account for the outaged element(s) based on the following option choices: BUS - assume the injection is at the bus and only modify the distribution factor if the bus is outaged, GEN - assume the injection is at a generator at the bus and only modify if an online generator is outaged, LOAD - assume that the injection is at a load at the bus and only modify if an online load is outaged, GENLOAD - assume that the injection is at a generator or load at the bus and only modify if an online generator or load is outaged. |
| `ATC_SolMethod` | SolutionMethod | Integer | Yes | ATC Solution Method | Specify an integer specifying which ATC Solution Method to Use: 0 = Single Linear Step; 1 = Iterated Linear Step; 2 = Iterating Linear Step then Full Contingency Solution |
| `ATCTransactor:1` | Buyer | String | AUX/Paste | Buyer | A text string describing the buyer in the ATC tool |
| `ATC_IncludePSPostCont` | PhaseShiftPostCTG | String | Yes | Enable Phase-Shifters Post-Contingency | Set to YES to enforce phase shifter control during post-contingency ATC calculations. If YES this means that the phase shifter angle may change to keep the line flow from changing after the contingency has been applied. |
| `GUIMultipleDirectionsChk` | GUIMultipleDirection | String | Yes | GUI\Multiple Directions Check | This is a GUI only option. When YES the option on the ATC dialog to solve Multiple Directions will be checked when the dialog is opened if multiple directions have been defined. |
| `GUIMultipleScenariosChk` | GUIMultipleScenario | String | Yes | GUI\Multiple Scenarios Check | This is a GUI only option. When YES the option on the ATC dialog to Analyze Multiple Scenarios will be checked when the dialog is opened if multiple directions have been defined. |
| `ATC_ForcePreContRamp` | RampForcePreCTG | String | Yes | Iterated Methods\Force Ramping in Pre-Contingency | When using the Iterated Linear then Full CTG solution method, this option specifies when to solve the contingency. Set to YES to force all transfer ramping to occur in the pre-contingency solution state. |
| `ATCIgnoreLimitersBelow` | IterateIgnoreBelowMW | String | Yes | Iterated Methods\Ignore Limiters Below | When choose which transfer limiters to iterate on, Simulator will not iterate on limiters below this value. |
| `ATCIterateOnFailedContingency` | IterateFailedCTG | String | Yes | Iterated Methods\Iterate on Failed Contingency | When Force Ramping in Pre-Contingency is YES, and a contingency solution fails, then setting this value to YES will force Simulator to search for the transfer level at which the contingency fails to solve. |
| `ATCLimitersToIterateOn` | IterateCount | String | Yes | Iterated Methods\Limiters To Iterate On | Specify the number of limiters on which to iterate |
| `ATC_TransferTol` | ToleranceMW | Real | Yes | Iterated Methods\Transfer Tolerance | When using an iterated method, specify the tolerance to use to stop iterations. |
| `UseMeritOrder:1` | RampMeritOrderTypeSink | String | Yes | Iterated Methods\Use Economic Merit Order Sink | Set to YES to use Economic Merit Order Dispatch for the sink injection group. Any injection group specific options will override this option. |
| `UseMeritOrder` | RampMeritOrderTypeSource | String | Yes | Iterated Methods\Use Economic Merit Order Source | Set to YES to use Economic Merit Order Dispatch for the source injection group. Any injection group specific options will override this option. |
| `ATC_LinCalcMethod` | LinearCalcMethod | String | Yes | Linear Calculation Method | Specify the linear calculation method for the ATC tool as either DC = Lossless DC or DCPS = Lossless DC with Phase Shifters |
| `LinearizeMakeupPower` | LinearizeMakeUpPower | String | Yes | Linearize Makeup Power | Set to YES to calculate the makeup power factors at the beginning of each linear step calculation and not for each contingency. If using this option, generator limits will not be enforced in the makeup power calculation. |
| `VariableName` | ScenarioField | String | Yes | Multiple Scenarios\Field To Show | Variablename of the field that should be displayed in the grid shown on the Results tab when enabling multiple scenarios. By default the Transfer Limit field will be shown. |
| `ATC_MultipleScenarios:1` | ScenarioMonitorLimitsOnly | String | Yes | Multiple Scenarios\Only Monitor Scenarios Limits | Set to YES to only monitor those branches that are defined in either the Line Rating A or Line Rating B lists. |
| `VaryLoadConstantPF` | ScenarioLoadConstantPF | String | Yes | Multiple Scenarios\Zone Vary Load Constant PF | When analyzing ATC Scenarios which include Zone Load scenarios, set this value to YES to assume that the load power factor does not change. If the value is NO, then Mvar loads are not varied. |
| `ReactivePowerModel` |  | String | Yes | Reactive Power Model | Specify how to handle reactive power in the linear calculations; Ignore = Ignore reactive power; ConstVolt = assume constant voltage magnitude; ConstMvar = assume reactive power does not change. |
| `ATCLimiterFERC2023Options` | LimiterFERC2023Options | String | Yes | Reporting\FERC Order 2023 Heatmap Options | Set to YES to use options necessary for producing Transfer Limiter results based on FERC Order 2023 heatmap requirements. This will set defaults for the Max Limter Per CTG, Include Contingencies, and Report Reserve options. Interfaces will not be monitored, ATC Extra Monitors are ignored, and the Single Linear Step solution method is used. |
| `ATC_IgnorePTDFBelow` | LimiterIgnoreBelowOTDF | Real | Yes | Reporting\Ignore Limiters with OTDFs Below | Specify to ignore transfer limiters with an OTDF% smaller than this value. |
| `ATC_IgnorePTDFBelow:1` | LimiterIgnoreBelowPTDF | Real | Yes | Reporting\Ignore Limiters with PTDFs Below | Specify to ignore transfer limiters with an PTDF% smaller than this value. Normally this only applies to limiters for the base case unless the Apply PTDF Cuttoff with Contingency Limiters option is chosen. |
| `ATC_IncBranchCtg` | CTGInclude | String | Yes | Reporting\Include Contingencies | Set to YES to process contingencies. If NO, then only base case transfer limiters will be examined |
| `ATC_MaxLimCtg` | LimiterCountPerCTG | Integer | Yes | Reporting\Maximum Limiters per Contingencies | When multiple transfer limiters for the same limiting contingency are found, only this number will be kept for results. Those with the smallest transfer limitation will be kept. |
| `ATC_MaxLimElements` | LimiterCountPerElement | Integer | Yes | Reporting\Maximum Limiters per Element | When multiple transfer limiters for the same limiting element are found, only this number will be kept for results. Those with the smallest transfer limitation will be kept. |
| `ATC_MaxMWLimit` | LimiterMaxMW | Real | Yes | Reporting\Maximum MW Limitation | Only transfer limiters with a MW limitation smaller than this value will be kept |
| `ATC_LimitersSaved` | LimiterCount | Integer | Yes | Reporting\Maximum total Limiters to Save | Specify an integer giving the maximum number of transfer limiter records to save. Those limiters with the smallest Transfer Limitation will be saved. |
| `ATC_IgnoreBaseLimitations` | LimiterBaseCaseLimits | String | Yes | Reporting\Report Base Case Limitations | Set to YES to specify that transfer limiters related to the base case should be kept in the results. (Note: the variable name for this option is unfortunately confusing, so be careful) |
| `GenEnforceMWLimits` | LimiterGenReserveLimits | String | Yes | Reporting\Report Generation Reserve Limitations | Set to YES to specify that limiters related to the amount of reserve in the Buyer or Seller should be maintained. |
| `CTGSaveInPWB` | StoreResultsInPWB | String | Yes | Save Results in PWB | Set to YES to Save the ATC results in the PWB file |
| `ATCTransactor` | Seller | String | AUX/Paste | Seller | A text string describing the seller in the ATC tool |

#### `IG_AutoInsert_Options` (14 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `PPntUseFixedParFac:1` | AutoCalc | String | Yes | AutoCalc | Set to YES if the auto inserted Participation Point ParFac values should change according to the selected auto calculation method. This will set the AutoCalc field to YES for auto inserted Participation Points. |
| `PPntPFInit` | AutoCalcMethod | String | Yes | AutoCalc Method | This specifies where the initial Participation Factor originates for the Participation Points and the AutoCalc Method for points that should be updated when AutoCalc = YES. Valid entries are SPECIFIED, SPECIFIED VALUE, SPECIFIED PRESENT, SPECIFIED FLOAT, MAX GEN INC, MAX GEN DEC, MAX GEN MW, and LOAD MW. This can also be the name of a Field or Model Expression. |
| `DeleteExisting` |  | String | Yes | Delete Existing | Set to YES to delete existing injection groups before auto inserting new ones. |
| `GroupBy` |  | String | Yes | Group By | Method used for specifying the groups used to create new injection groups. Options are: AREA, ZONE, SUPERAREA, OWNER, and CUSTOMFLOAT. |
| `StartAt` | NumberStart | Integer | Yes | Name Number Start | Value to start at when naming the auto inserted injection groups. Injection groups will be named using the prefix followed by a value (beginning at 0) that is offest by this starting value. |
| `Prefix` | NamePrefix | String | Yes | Name Prefix | Prefix to use when naming the auto inserted injection groups. |
| `BusIdentifier` | IdentifyBy | String | Yes | Object Identifier | Identifier to use when naming the injection groups based on the PointType. Options are: NUMBERS, NAMES, and BOTH. |
| `OnlySelected` | SelectedOnly | String | Yes | Only Selected | Set to YES to only create injection groups for the objects that have their SELECTED field set to YES. |
| `PPntParFac` | PartFact | Real | Yes | ParFac | Participation factor to use for all Participation Points when AutoCalcMethod = SPECIFIED VALUE. |
| `PPntType` | PointType | String | Yes | Point Type | Element type of the object to add as Partiticipation Points. Options are: GEN, LOAD, SHUNT, BUS, and INJECTIONGROUP. |
| `UseField` | GroupByCustomField | Integer | Yes | Use Field for Grouping | This is the the location number of the Custom Floating Point or Custom String field that specifies the groups to use when creating new injection groups. This is used when GroupBy = CUSTOMFLOAT. To specify a Custom Floating Point field use the location number. To specify a Custom String field use: (Location number of Custom String) + (Maximum location number of Custom Floating Point fields) + 1. |
| `UseField:1` | PartFactCustomField | Integer | Yes | Use Field for ParFac Value | This is the location number of the Custom Floating Point field containing the Participation Factor value. This is used when AutoCalcMethod = SPECIFIED FLOAT. |
| `PPntUseFixedParFac` | UseFixedPartFact | String | Yes | Use Fixed ParFac | Set to YES if the auto inserted Participation Point ParFac values should not be changed according to the selected auto calculation method. This will set the AutoCalc field to NO for auto inserted Participation Points. |
| `PPntAutoInsUsePrefixAsName` | UseNamePrefixIfOnlyOne | String | Yes | Use Prefix as Name | When only a single injection group is created, setting this option to YES will use the string specified in the NamePrefix field as the name of the new injection group. |

#### `AutoInsertBorders_Options` (18 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `BordersFilePath` |  | String | Yes | Borders File Path | File in which the border files are contained. If left blank, Simulator assumes it's in a subdirectory named Borders inside the directory in which the pwrworld.exe file is contained. |
| `CanadaOption` |  | String | Yes | Canada Provinces | List of Canadian Provinces to insert |
| `SOColor` |  | Integer | Yes | Color | Color of background lines inserted |
| `UserDefinedBordersFile` |  | String | Yes | Filename for User Defined Borders |  |
| `SOFillColor` |  | Integer | Yes | Fill Color | Fill Color of background lines inserted |
| `BordersImmobileOption` |  | String | Yes | Immobile | Set to YES to make background lines inserted immobile |
| `LinktoSupplementalDataOption` |  | String | Yes | Link to Supplemental Data | Set to YS to Link to Supplemental Data |
| `MapProjection` |  | String | Yes | Map Projection | Either SIMPLE CONIC or MERCATOR |
| `PreDefinedOption` |  | String | Yes | Predefined Option | Predefined Option: Either NORTHAMERICA, USASTATEBORDERS, CANADIANPROVINCEBORDERS, or ENTIREWORLD |
| `RegionForBorders` |  | String | Yes | Region To Insert | Region To Insert: Either PRE-DEFINED, United States, CANADA, or WORLD |
| `SLName` |  | String | Yes | Screen Layer | Layer into which background lines are inserted |
| `StackLevelOption` |  | String | Yes | Stack Level | Stack level in which background lines are inserted. Either BASE, BACKGROUND, MIDDLE, or TOP |
| `SOThickness` |  | Integer | Yes | Thickness | Thickness of background lines inserted |
| `USBorderTypeOption` |  | String | Yes | US Border Type | Either STATE or COUNTY |
| `USOption` |  | String | Yes | US States | List of US States to insert |
| `BackgroundFillColorOption` |  | String | Yes | Use Fill Color | Set to YES to use a fill with background lines. (Fill Color specified the color) |
| `UserDefBorderFileFormat` |  | String | Yes | User Defined Coordinates | User Defined Coordinates. Either X-Y or LAT-LON |
| `WorldOption` |  | String | Yes | World Regions | List of World Regions to insert |

### Voltage stability

#### `PVCurve_Options` (91 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `PVCRunBaseToCompletion` | RunBaseToCompletion | String | Yes | Base Case Run to Completion | Set this to YES to run the PV analysis to completion for the base case scenario even if the specified number of critical scenarios have been found. |
| `PVCDoNotConsiderRadialBuses` | InadequateNoRadial | String | Yes | Inadequate\Do Not Consider Radial Buses | Set to YES to not consider radial buses to have inadequate voltage. This includes buses that become radial due to a contingency. |
| `PVCInterpolateInadequate:1` | InadequateHighInterpolate | String | Yes | Inadequate\High Voltage Interpolate | Set to YES to interpolate inadequate high voltages to determine a closer estimate of the transfer level at which voltages become inadequate. |
| `PVCInadequateVoltLimitSet:1` | InadequateHighRateSet | String | Yes | Inadequate\High Voltage Rate Set | Specify the limit set to use when considering any monitored bus voltage to be inadequate if it is too high. Valid options are A, B, C, or D. |
| `PVCFlagInadequate:1` | InadequateHighStore | String | Yes | Inadequate\High Voltage Store | Set to YES to store inadequate high voltages. |
| `PVCInadequateVoltType:1` | InadequateHighType | String | Yes | Inadequate\High Voltage Type | When considering a bus voltage to be inadequate if it is too high, use this option to specify how to check the adequacy of the voltage. LIMIT means to use the High Voltage Violation Limit for each bus, SET means to use a specific limit set, and VALUE means to use the same specified value for each bus. |
| `PVCInadequateVolt:1` | InadequateHighVolt | Real | Yes | Inadequate\High Voltage Value | Specify the high voltage to use when considering any monitored bus voltage to be inadequate. (Per-unit value.) |
| `PVCInterpolateInadequate` | InadequateLowInterpolate | String | Yes | Inadequate\Low Voltage Interpolate | Set to YES to interpolate inadequate low voltages to determine a closer estimate of the transfer level at which voltages become inadequate. |
| `PVCInadequateVoltLimitSet` | InadequateLowRateSet | String | Yes | Inadequate\Low Voltage Rate Set | Specify the limit set to use when considering any monitored bus voltage to be inadequate if it is too low. Valid options are A, B, C, or D. |
| `PVCFlagInadequate` | InadequateLowStore | String | Yes | Inadequate\Low Voltage Store | Set to YES to store inadequate low voltages. |
| `PVCInadequateVoltType` | InadequateLowType | String | Yes | Inadequate\Low Voltage Type | When considering a bus voltage to be inadequate if it is too low, use this option to specify how to check the adequacy of the voltage. LIMIT means to use the Low Voltage Violation Limit for each bus, SET means to use a specific limit set, and VALUE means to use the same specified value for each bus. |
| `PVCInadequateVolt` | InadequateLowVolt | Real | Yes | Inadequate\Low Voltage Value | Specify the low voltage to use when considering any monitored bus voltage to be inadequate. (Per-unit value.) |
| `FGName` | RampInterfaceX | String | Yes | Interface Ramping\Interface X | Interface X |
| `FGName:1` | RampInterfaceY | String | Yes | Interface Ramping\Interface Y | Interface Y |
| `UseInterface` | RampInterfaceYUse | String | Yes | Interface Ramping\Interface Y Use | Use Interface Y |
| `FGName:2` | RampInterfaceZ | String | Yes | Interface Ramping\Interface Z | Interface Z |
| `MWSetpoint` | RampInterfaceZMW | Real | Yes | Interface Ramping\Interface Z MW Setpoint | Interface Z MW Setpoint |
| `UseInterface:1` | RampInterfaceZUse | String | Yes | Interface Ramping\Interface Z Use | Use Interface Z |
| `Angle` | RampInterfaceAngle | Real | Yes | Interface Ramping\Search Path Angle | Search Path Angle |
| `PVCBuyerPartFact:4` | LoadFracBuyerIMvar | Real | Yes | Load Fraction\Buyer Constant current Mvar | Sink reactive constant current (I MVAR) ZIP proportion. (Value between 0 and 1.) |
| `PVCBuyerPartFact:1` | LoadFracBuyerIMW | Real | Yes | Load Fraction\Buyer Constant current MW | Sink real constant current (I MW) ZIP proportion. (Value between 0 and 1.) |
| `PVCBuyerPartFact:5` | LoadFracBuyerZMvar | Real | Yes | Load Fraction\Buyer Constant impedance Mvar | Sink reactive constant impedance (Z MVAR) ZIP proportion. (Value between 0 and 1.) |
| `PVCBuyerPartFact:2` | LoadFracBuyerZMW | Real | Yes | Load Fraction\Buyer Constant impedance MW | Sink real constant impedance (Z MW) ZIP proportion. (Value between 0 and 1.) |
| `PVCBuyerPartFact:3` | LoadFracBuyerSMvar | Real | Yes | Load Fraction\Buyer Constant power Mvar | Sink reactive constant power (S MVAR) ZIP proportion. (Value between 0 and 1.) |
| `PVCBuyerPartFact` | LoadFracBuyerSMW | Real | Yes | Load Fraction\Buyer Constant power MW | Sink real constant power (S MW) ZIP proportion. (Value between 0 and 1.) |
| `PVCSellerPartFact:4` | LoadFracSellerIMvar | Real | Yes | Load Fraction\Seller Constant current Mvar | Source reactive constant current (I MVAR) ZIP proportion. (Value between 0 and 1.) |
| `PVCSellerPartFact:1` | LoadFracSellerIMW | Real | Yes | Load Fraction\Seller Constant current MW | Source real constant current (I MW) ZIP proportion. (Value between 0 and 1.) |
| `PVCSellerPartFact:5` | LoadFracSellerZMvar | Real | Yes | Load Fraction\Seller Constant impedance Mvar | Source reactive constant impedance (Z MVAR) ZIP proportion. (Value between 0 and 1.) |
| `PVCSellerPartFact:2` | LoadFracSellerZMW | Real | Yes | Load Fraction\Seller Constant impedance MW | Source real constant impedance (Z MW) ZIP proportion. (Value between 0 and 1.) |
| `PVCSellerPartFact:3` | LoadFracSellerSMvar | Real | Yes | Load Fraction\Seller Constant power Mvar | Source reactive constant power (S MVAR) ZIP proportion. (Value between 0 and 1.) |
| `PVCSellerPartFact` | LoadFracSellerSMW | Real | Yes | Load Fraction\Seller Constant power MW | Source real constant power (S MW) ZIP proportion. (Value between 0 and 1.) |
| `PLColor` | PlotColor | Integer | Yes | Plot\Color | When plotting results for multiple PV scenarios on the same chart, this specifies the color of plot series related to this base case scenario |
| `SODashed` | PlotDashed | String | Yes | Plot\Line Dashed | When plotting results for multiple PV scenarios on the same chart, this specifies the Dash property used for a Line Series related to the base case scenario (Solid, Dash, Dot, Dash Dot, Dash Dot Dot, or Default) |
| `PLThickness` | PlotThickness | Integer | Yes | Plot\Line Thickness | When plotting results for multiple PV scenarios on the same chart, this specifies the thickness used for a Line Series related to this base case scenario |
| `IDFormat` | PlotIDFormat | String | Yes | Plot\Plot Object Identifier | Format of the identifier to use for objects in plots. |
| `SymbolType` | PlotSymbol | String | Yes | Plot\Point Symbol | When plotting results for multiple PV scenarios on the same chart, this specifies the symbol used for a points in a Point Series related to the base case scenario (Circle, Cross, DiagCross, Diamond, DownTriangle, Hexigon, LeftTriangle, Nothing, Rectangle, RightTriangle, SmallDot, Stair, Triangle, or Default) |
| `PLVisible` | PlotShowBase | String | Yes | Plot\Show on Base Case Scenario on Plot | When plotting results for multiple PV scenarios on the same chart, this specifies whether the base case scenario is included |
| `PVTrackLimits` | TrackLimitGen | String | Yes | PV Track Limits\Gens | Set to YES to track generator var limits. |
| `PVTrackLimits:1` | TrackLimitGenFilter | String | Yes | PV Track Limits\Gens Filter | Name of filter to use when tracking generator var limits. |
| `PVTrackLimits:8` | TrackLimitInterface | String | Yes | PV Track Limits\Interfaces | Set to YES to track interface thermal limits. |
| `PVTrackLimits:9` | TrackLimitInterfaceFilter | String | Yes | PV Track Limits\Interfaces Filter | Name of filter to use when tracking interface thermal limits. |
| `PVTrackLimits:6` | TrackLimitBranch | String | Yes | PV Track Limits\Lines | Set to YES to track line thermal limits. |
| `PVTrackLimits:7` | TrackLimitBranchFilter | String | Yes | PV Track Limits\Lines Filter | Name of filter to use when tracking line thermal limits. |
| `PVTrackLimits:4` | TrackLimitLTC | String | Yes | PV Track Limits\LTCs | Set to YES to track LTC tranformer tap limits. |
| `PVTrackLimits:5` | TrackLimitLTCFilter | String | Yes | PV Track Limits\LTCs Filter | Name of filter to use when tracking LTC transformer tap limits. |
| `PVTrackLimits:2` | TrackLimitShunt | String | Yes | PV Track Limits\Shunts | Set to YES to track switched shunt var limits. |
| `PVTrackLimits:3` | TrackLimitShuntFilter | String | Yes | PV Track Limits\Shunts Filter | Name of filter to use when tracking switched shunt var limits. |
| `PVCApplyReverseTransfer` | RampReverse | String | Yes | Ramp\Apply Reverse Transfer | Set to YES to attempt the reverse transfer if any contingencies do not solve in the base case. |
| `PVCOIPercent` | COIPDCIRatio | Real | Yes | Ramp\COI/PDCI\COI % | Percentage of the PDCI/COI ratio. (Enter as ratio) |
| `PVCOIPDCIMaxMW` | COIPDCIMWMax | Real | Yes | Ramp\COI/PDCI\Max PDCI MW | Maintain the PDCI/COI ratio up to this limit. (MW value.) |
| `PVDoCOISplit` | COIPDCISplit | String | Yes | Ramp\COI/PDCI\Split Use | Set to YES to do the COI/PDCI split. |
| `PVCEnforceAGC` | RampEnforceAGC | String | Yes | Ramp\Enforce AGC | Set to YES to only include generators whose AGC status = YES in the transfer. |
| `PVCEnforceGenMWLimits` | RampEnforceMWLimits | String | Yes | Ramp\Enforce Gen MW Limits | Set to YES to enforce generator MW limits during the transfer. |
| `PVCEnforcePosLoad` | RampEnforcePosLoad | String | Yes | Ramp\Enforce Positive Load | Set to YES to enforce that loads not become negative during the transfer. |
| `PVCConvTolerance` | RampTolerancepu | Real | Yes | Ramp\Island-based AGC Convergence Tolerance | Convergence tolerance used when adjusting the sink injection group during the transfer. This should be less than the minimum step size and greater than the MVA convergence tolerance. This value will be automatically adjusted by Simulator if these conditions are not met. (Per-unit value on the system MVA base.) |
| `PVCQPowerFactMult` | RampLoadMvarMult | Real | Yes | Ramp\Load\Mvar multiplier | Apply this multiplier to the change in MVAR load when using the option to maintain a constant power factor as MW load changes during the transfer. (Value between 0 and 1.) |
| `PVCPowerFac` | RampLoadMvarPF | Real | Yes | Ramp\Load\Mvar Power Factor | As MW load changes during the transfer, change the MVAR at this power factor. (Value between 0 and 1.) |
| `PVCUseConstantPF` | RampLoadConstantPF | String | Yes | Ramp\Load\Use Constant PF | Set this to YES to use a constant power factor when changing MVAR load as MW load changes as part of the transfer. |
| `PVCUseZIPFactors` | RampLoadZipFactorsUse | String | Yes | Ramp\Load\ZIP Factors Use | Set to YES or SPECIFY to use specified ZIP factors. Set to NO or CONSTPOWER to have all load changes go to the constant power component. Set to EXISTINGRATIOS to scale components in proportion to existing ratios. |
| `PVCUseGenMeritOrder` | RampMeritOrderUse | String | Yes | Ramp\Merit Order\Use | Set to YES to use merit order dispatch for both the source and sink. Set to NO to use merit order dispatch for neither. Set to SOURCE or SINK to just use merit order dispatch for either the source or sink. |
| `PVCUseGenMeritOrder:2` | RampMeritOrderTypeSink | String | Yes | Ramp\Merit Order\Use Economic Sink | Set to YES, NO, or MERITCLOSE. This is only used if the option to use Merit Order for the Sink is configured with another varaible. Set to YES to use Economic Merit Order dispatch for the sink injection group. Set to MERITCLOSE to use merit order but also close in units presently open. Set to NO to use Merit Order. |
| `PVCUseGenMeritOrder:1` | RampMeritOrderTypeSource | String | Yes | Ramp\Merit Order\Use Economic Source | Set to YES, NO, or MERITCLOSE. This is only used if the option to use Merit Order for the Source is configured with another varaible. Set to YES to use Economic Merit Order dispatch for the source injection group. Set to MERITCLOSE to use merit order but also close in units presently open. Set to NO to use Merit Order. |
| `PVCSink` | RampSink | String | Yes | Ramp\Sink | Sink injection group. |
| `PVCSource` | RampSource | String | Yes | Ramp\Source | Source injection group. |
| `PVCIniStep` | RampStepSizeInitpu | Real | Yes | Ramp\Step Size Initial (pu) | Initial transfer step size. (Per-unit value on system MVA base.) |
| `PVCMinStep` | RampStepSizeMinpu | Real | Yes | Ramp\Step Size Minimum (pu) | Minimum allowed step size for the transfer. (Per-unit value on system MVA base.) |
| `PVCReduceFactor` | RampReduceFactor | Real | Yes | Ramp\Step Size Reduce Factor | When the power flow fails to solve for a scenario, reduce the transfer step size by this reduction factor. |
| `RampingMethod` |  | String | Yes | Ramping Method | Ramping method to use during the PV analysis. When choosing INJECTIONGROUP the ramping will occur between source and sink injection groups. When choosing INTERFACE the ramping will occur to meet specified MW flows on selected interfaces. |
| `RestoreSystemState` | RestoreInitialState | String | Yes | Restore Initial State | Set to YES to restore the initial state on completion of run. |
| `PVCArchiveState` | ResultArchiveState | String | Yes | Result\Archive State | CRITICAL BASE to save base case states for each critical contingency, ALL to save all states, or NONE to not archive any states. |
| `PVCArchiveStateFormat` | ResultArchiveFormat | String | Yes | Result\Archive State Format | AUX for auxiliary file, PWB for PowerWorld binary file, AUX_PWB to save as both auxiliary and binary files. |
| `PVCOutFile` | ResultFileName | String | Yes | Result\Output File | Name of the PV results output file. |
| `PVCSaveToFile` | ResultSave | String | Yes | Result\Save to File | Set this to YES to save the PV results to file. |
| `PVCStoreStatesWhere` | ResultArchiveDirectory | String | Yes | Result\State and Plot Storage Directory | Directory where archived state and plot files should be stored. |
| `PVCStateArchivePrefix` | ResultArchivePrefix | String | Yes | Result\State Archive Prefix | Prefix to apply to any files stored as part of the state archiving process. |
| `PVCTranspose` | ResultTranspose | String | Yes | Result\Transpose PV Output File | Set to YES to transpose the PV results file with the transfer levels reported in columns and the tracked quantities reported in rows. |
| `PVCUseSingleHeaderFile` | ResultSingleHeaderFile | String | Yes | Result\Use Single Header File | Set to YES to save the PV output file using only a single field header. |
| `CTGSaveInPWB` | StoreResultsInPWB | String | Yes | Save Results in PWB | Set to YES to Save the PV results in the PWB file |
| `PVCSkipCtg` | CTGSkip | String | Yes | Skip Contingencies | Set this to YES to skip processing contingencies during the PV analysis. |
| `PVCCapped` | StopMaxShift | String | Yes | Stop\Maximum at max Shift | Set to YES to stop the PV analysis when the transfer exceeds the specified value with the PVCMaxShift variable. |
| `PVCMaxShift:1` | StopMaxShiftReverseMW | Real | Yes | Stop\Maximum Reverse Transfer MW | Stop the reverse transfer if the transfer exceeds this value. (MW value.) |
| `PVCMaxShift` | StopMaxShiftpu | Real | Yes | Stop\Maximum Shift MW | Stop the PV analysis if the transfer exceeds this value and the PVCCapped variable is set to YES. (Per-unit value on system MVA base.) |
| `PVCNumLimitCases` | StopNumCritical | Integer | Yes | Stop\Number of Limiting Cases | Stop the analysis when at least this number of critical scenarios is found. |
| `PVCStopWhenInadequate:1` | StopNegativedVdq | String | Yes | Stop\On Negative dV/dQ | Stop On Negative dV/dQ |
| `PVCStopWhenInadequate` | StopInadequate | String | Yes | Stop\When Inadequate | Set to YES to stop the PV analysis when any monitored voltage becomes inadequate. |
| `PVCIncludeATCExtraMonitor` | TrackATCExtraMon | String | Yes | Track ATC Extra Monitors | Set to YES to include ATC Extra Monitors in the quantities to track. |
| `Flag` | ViolationBranchType | String | Yes | Violation\Branch Type | The following options are available: IGNORE - ignore branch violations, LOG - log any branch violations that occur, STOP - stop a scenario and treat it as critical if any branch violations are found, or STOPBASECASE - stop only the base case scenario and treat it as critical if any branch violations are found. |
| `PVCFlagHighVolt` | ViolationVoltHigh | String | Yes | Violation\High Voltage | Set to YES to identify buses with high voltage violations in the results. |
| `Flag:1` | ViolationInterfaceType | String | Yes | Violation\Interface Type | The following options are available: IGNORE - ignore ignore violations, LOG - log any interface violations that occur, STOP - stop a scenario and treat it as critical if any interface violations are found, or STOPBASECASE - stop only the base case scenario and treat it as critical if any interface violations are found. |
| `PVCFlagLowVolt` | ViolationVoltLow | String | Yes | Violation\Low Voltage | Set to YES to identify buses with low voltage violations in the results. |
| `PVCFlagLowVolt:1` | ViolationVoltLowest | String | Yes | Violation\Lowest Voltage Always | Set to YES to always report the lowest voltage when also flagging low voltage violations even if none of the voltages fall below their low voltage limits. |

#### `QVCurve_Options` (22 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `qvAutoIDdVdQ` | AutoNumdVdQ | String | Yes | AutoID dV/dQ | Specify the number of highest dV/dQ buses that should be automatically included in the analysis. |
| `qvAutoIDLimGroup` | AutoLimitSet | String | Yes | AutoID Lim Group | Specify the limit group used for determining which buses are considered when identifying the lowest-voltage or highest dV/dQ buses. |
| `qvAutoIDBusV` | AutoNumVpu | String | Yes | AutoID Voltage | Specify the number of lowest-voltage buses that should be automatically included in the analysis. |
| `qvDoCTGs` | ContingencyDo | String | Yes | Do CTGs | Set to YES to include contingencies as part of the QV analysis. |
| `qvPlot` | Plot | String | Yes | Draw Curves | Set to YES to automatically draw QV curves as they are calculated. |
| `qvFileExt` | OutFileExt | String | read-only | File Extension | File extension of the output file. |
| `qvFilePrefix` | OutFilePrefix | String | read-only | File Prefix | Prefix of the output file. |
| `QVMakeSolvable:1` | MakeBaseCaseSolvable | String | Yes | Make Base Case Solvable | Set to YES to attempt to make the base case solvable if it does not initially solve. |
| `QVMakeSolvable` | MakeSolvable | String | Yes | Make Solvable | Set to YES to attempt to make any contingency scenarios solvable if the contingency does not solve in the base case. |
| `MakeUpPower` | MakeupPower | String | Yes | Make-Up Power | Method to use for make-up power during the power flow solutions when tracing the QV curve. Options are SLACK - use the system slack, or CONTINGENCY - do the same thing as the contingency analysis option for make-up power. |
| `qvMaxVolt` | VpuMax | Real | Yes | MaxVolt | Maximum voltage in pu to consider when tracing the QV curves. |
| `qvMinVolt` | VpuMin | Real | Yes | MinVolt | Minimum voltage in pu to consider when tracing the QV curves. |
| `qvOutputDir` | OutDirectory | String | read-only | Output Directory | Directory of the output file. |
| `QVPlotQAsQSync` | PlotValue | String | Yes | Plot Q as QSync | Specify the Mvar quantity to use when plotting the QV curves. QSYNC or YES - only the synchronous condenser output. QTOTAL or NO- synchronous condenser plus any existing shunt injection. QSYNCRESERVE - synchronous condenser plus any available reserves. QTOTALRESERVE - synchronous condenser plus any existing shunt injection plus any available reserves. |
| `QVOutputFileName` | OutFileName | String | Yes | QV: Output File Name | Directory and name of the QV results output file. |
| `QVSkipBaseCase` | SkipBaseCase | String | Yes | QV: Skip Base Case | Set to YES to skip the base case during the QV analysis. |
| `qvSave:1` | OutSaveQuantitiesToTrack | String | Yes | Save Quantities to Track to File | Set to YES to save the Quantities to Track to file as the run progresses. This is a comma-separated file. This file will be named automatically with "ExtraMonitoring" contained in the name. This file can also be saved after a run has completed using appropriate dialog options and script commands. |
| `CTGSaveInPWB` | StoreResultsInPWB | String | Yes | Save Results in PWB | Set to YES to save all QV analysis related results in PWB files. QV related options will always be stored in PWB files. QV results and options are ONLY stored in Simulator version 22 PWB files and later. |
| `qvSave` | OutSave | String | Yes | Save To File | Set to YES to save the QV results to file. This will save the QV curve points in a file without the Quantities to Track. |
| `SolutionOptionWhen` |  | String | Yes | Solution Options When to Apply | Set to either Before or After: Specifies whether the QV solution options should be applied before or after the contingency or base case power flow solution |
| `qvStepSize` | VpuStepSize | Real | Yes | Stepsize | Voltage stepsize in pu to use when tracing the QV curves. |
| `QVUseInitialVAsVMax` | VmaxVinit | String | Yes | V_max = V_initial? | Set to YES to use the initial bus voltage as the maximum voltage for tracing the QV curve. |

### Scaling, equivalents, faults, scheduled actions

#### `Scale_Options` (10 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `GenAGCAble` | EnforceAGC | String | Yes | AGC |  |
| `BGAGC` | ACEKeepConstant | String | Yes | AGC Status |  |
| `EnforceGenMWLimits` | EnforceMWLimits | String | Yes | Enforce Gen MW |  |
| `IncludeOutOfServiceLoads` | OutLoads | String | Yes | Include Out-of-service Loads |  |
| `ScaleUseModeledMW` | ModeledMW | String | Yes | Scale Modeled MW? |  |
| `ScaleStartingPoint` | StartingPoint | String | Yes | Scale Starting Point |  |
| `GenAGCAble:1` | EnforceAGCIgnorePart | String | Yes | Use AGC Flag for Scale Only | Ignore AGC flag to calculate participation but use AGC flag to scale individual loads or generators |
| `UseMeritOrder:1` | MeritOrderType | String | Yes | Use Economic Merit Order |  |
| `UseMeritOrder` | MeritOrderUse | String | Yes | Use Merit Order |  |
| `VaryLoadConstantPF` | LoadConstantPF | String | Yes | Vary Load Constant PF |  |

#### `Equiv_Options` (13 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `AdjustAreaUnspecifiedInterchange` | AdjustAreaInterchange | String | Yes | Adjust Area Unspecified Interchange |  |
| `EquivConvertShuntsToLoad` | ConvertShuntsToLoad | String | Yes | Convert Shunts to Loads |  |
| `DeleteAllExtGen` | DeleteExternalGen | String | Yes | Delete All External Gen |  |
| `DeleteEmptyBusGroups` | DeleteEmptyAreaZoneSub | String | Yes | Delete Empty Bus Groups |  |
| `EquivLineID` | EquivBranchID | String | Yes | Equivalent Line ID |  |
| `EquivMaxLineImpedance` | LineImpedanceMax | Real | Yes | Max Line Impedance |  |
| `LMS_IgnoreRadial` | RemoveRadial | String | Yes | Remove Radial Systems |  |
| `EquivRetainOther:2` | RetainAreaTie | String | Yes | Retain Area Ties Lines |  |
| `EquivRetainGen` | RetainGenMWMax | Real | Yes | Retain Gens Larger Than |  |
| `EquivRetainRemotelyRegulatedBuses` | RetainRemoteReg | String | Yes | Retain Remotely Regulated Buses |  |
| `EquivRetainOther` | RetainXF | String | Yes | Retain Transformer Terminals |  |
| `EquivRetainOther:1` | RetainZBR | String | Yes | Retain Zero Impedance Ties |  |
| `EquivRetainOther:3` | RetainZoneTie | String | Yes | Retain Zone Ties Lines |  |

#### `Fault_Options` (7 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `FAFaultCurDisplayAmps` | DisplayAmps | String | Yes | Display Fault Current in Amps? |  |
| `FAIECPowerFactor` | IECGenPFAngleRadians | Real | Yes | IEC Power Factor |  |
| `FAIECVolt` | IECVpu | Real | Yes | IEC Voltage |  |
| `FASetLineCharging` | SetLineCharging | String | Yes | Line Charging Set to 0? |  |
| `FAPreFaultProfile` | PreFaultProfile | String | Yes | Pre-Fault Profile |  |
| `FASetShuntElements` | SetShuntElements | String | Yes | Shunt Elements Treated as... |  |
| `FASetTRRatio` | SetXFRatio | String | Yes | XF Turns Rations Set to 1.0? |  |

#### `ScheduledActions_Options` (15 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `SAAnimation` | AnimationValue | Real | Yes | Animation Rate | Hold time between animated increments |
| `SAAnimationUnits` | AnimationUnit | String | Yes | Animation Rate Units | Units of the hold time between animated increments |
| `SAApplyActions` | ApplyActions | String | Yes | Apply Actions | Apply relevant scheduled actions by time. |
| `SAApplyWindow` | ApplyResolution | String | Yes | Apply Window | Apply all actions that are active within Resolution time after the current View Time |
| `SADeleteAddedExtra` | DeleteAddedExtra | String | Yes | Clear Added and Extra Actions | Clear Added and Extra Actions before running Identify Breakers |
| `SAEndTime` | EndTime | String | Yes | End Time | End of time display window. |
| `SAEvaluateManually` | EvaluateManually | String | Yes | Evaluate Manually | Evaluate schedules at View Time only when specified by the user. |
| `SAIdentifyBreakers` | IdentifyBreakers | String | Yes | Identify Breakers Active | Identify Breakers ignores any inactive Actions |
| `IncludeNormallyOpen` | IncludeDisconnectsNormalStatus | String | Yes | Include Normal Status Disconnects | When using the Open Breakers action, Disconnects that are Closed but Normally Open will be opened in addition to Breakers. When using Close Breakers actions, Disconnects that are Open but Normally Closed will be closed in addition to Breakers. |
| `SAResolution` | ResolutionValue | Real | Yes | Resolution | Resolution of time display window |
| `SAResolutionUnits` | ResolutionUnit | String | Yes | Resolution Units | Units of the resolution of time display window |
| `SAStartTime` | StartTime | String | Yes | Start Time | Start of time display window. |
| `SAUseActionFilter` | UseActionFilter | String | Yes | Use Action Filter | When applying actions, use the filter currently applied to the Actions grid of the Scheduled Actions dialog |
| `SAUseNormal` | ApplyUseNormalStatus | String | Yes | Use Normal | When line elements that are referenced by a scheduled action are not being affected by that action, set them to their normal status. |
| `SAViewTime` | ViewTime | String | Yes | View Time | View point in time display window. |

### Time step and weather

#### `Time_Step_Simulation_Options` (50 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `TimeDomainOptionString:10` | ApplyAndSolve | String | Yes | ApplyAndSolve | If Yes then apply and solve; if no just apply the time point data |
| `TimeDomainOptionString:11` | ApplyInputData | String | Yes | ApplyInputData | If Yes then the input data is applied for each time point |
| `TimeDomainOptionString:14` | ApplyPostScriptAfterStoringResults | String | Yes | ApplyPostScriptAfterStoringResults | If Yes then apply the postscript commands after storing the results; otherwise before the store |
| `TimeDomainOptionString:13` | ApplyPreScriptAfterInputData | String | Yes | ApplyPreScriptAfterInputData | If Yes then apply the prescript commands after the input data; otherwise before the input data |
| `TimeDomainOptionString:12` | ApplyScheduleData | String | Yes | ApplyScheduleData | If Yes then the schedule data is applied for each time point |
| `TimeDomainOptionString:17` | AreaZoneIncludeOffLoads | String | Yes | AreaZoneIncludeOffLoads | If Yes then offline loads are included in determining the total load for the area or zone; othewise they are ignored |
| `TimeDomainOptionString:15` | AreaZoneLoadScaling | String | Yes | AreaZoneLoadScaling | If AREA use the area scaling values, if ZONE use the zone ones, if NONE then no scaling |
| `TimeDomainOptionString:16` | AreaZoneReactivePowerConstantPF | String | Yes | AreaZoneReactivePowerConstantPF | If Yes then the area or zone reactive load is scaled to maintain a constant power factor; otherwise the reactive power load is not changed |
| `TimeDomainOptionString:4` | AutoLoadTSB | String | Yes | AutoLoadTSB | Yes to autoload the tsb |
| `TimeDomainOptionString:7` | AutoRunOnTSBLoad | String | Yes | AutoRunOnTSBLoad | Yes to automatically run on a tsb file load |
| `TimeDomainOptionString:3` | AutoSaveTSB | String | Yes | AutoSaveTSB | Yes to autosave after a run |
| `TimeDomainOptionString:5` | AutoUpdateDefaultTSB | String | Yes | AutoUpdateDefaultTSB | Yes to automatically update the default tsb to the current tsb |
| `TimeDomainOptionString` | Continuous | String | Yes | Continuous | If yes then do a continuous simulation; otherwise solve the discrete time points |
| `TimeDomainOptionString:1` | CSVFileIdentifier | String | Yes | CSVFileIdentifier |  |
| `TimeDomainOptionString:2` | CSVOutputPath | String | Yes | CSVOutputPath |  |
| `TimeDomainOptionString:6` | DefaultTSBFile | String | Yes | DefaultTSBFile | Default tsb file |
| `TimeDomainOptionSingle:8` | DisplayUpdateSeconds | Real | Yes | DisplayUpdateSeconds | Specifieds the rate (in seconds) to update the display when doing solutions |
| `TimeDomainOptionString:19` | GenAGCTurnOffOnInputChange | String | Yes | GenAGCTurnOffOnInputChange | If Yes then turn off a generator's AGC if its value is changed by an input value |
| `TimeDomainOptionString:21` | GenHydroPriceAtMarginalCost | String | Yes | GenHydroPriceAtMarginalCost | If Yes then price the hydro at the marginal cost; if no use the input cost values |
| `TimeDomainOptionString:22` | GenHydroPriceReset | String | Yes | GenHydroPriceReset | If Yes then reset the hydro generation price at the end of each time step |
| `TimeDomainOptionSingle:5` | GenSolarAzimuthDeg | Real | Yes | GenSolarAzimuthDeg | For solar generation assumed azimuth angle; only used when there is no tracking |
| `TimeDomainOptionSingle:7` | GenSolarDiffuseFactor | Real | Yes | GenSolarDiffuseFactor | For solar generation assumed diffuse factor |
| `TimeDomainOptionString:25` | GenSolarSetMaxByWeather | String | Yes | GenSolarSetMaxByWeather | If Yes then set the solar generation MaxMW field based on the available sun |
| `TimeDomainOptionSingle:6` | GenSolarTiltOffsetDeg | Real | Yes | GenSolarTiltOffsetDeg | For solar generation assumed tilt angle offset from value based on latitude |
| `TimeDomainOptionString:26` | GenSolarTracking | String | Yes | GenSolarTracking | Tells the default solar tracking: none, singleaxis or dualaxis |
| `TimeDomainOptionSingle:1` | GenWindCutInSpeedMPH | Real | Yes | GenWindCutInSpeedMPH | For wind generation speed in MPH when generation starts |
| `TimeDomainOptionSingle:3` | GenWindCutOutSpeedMPH | Real | Yes | GenWindCutOutSpeedMPH | For wind generation speed in MPH when generation stops |
| `TimeDomainOptionSingle:4` | GenWindHubHeightScalar | Real | Yes | GenWindHubHeightScalar | For wind generation scales the wind to account for winds at the hub height |
| `TimeDomainOptionSingle:2` | GenWindRatedSpeedMPH | Real | Yes | GenWindRatedSpeedMPH | For wind generation speed in MPH when generation reachces its rated value |
| `TimeDomainOptionString:24` | GenWindSetMaxByWeather | String | Yes | GenWindSetMaxByWeather | If Yes then set the wind generation MaxMW field based on the wind speed |
| `TimeDomainOptionString:36` | GICAssumeConstantGridTopology | String | Yes | GICAssumeConstantGridTopology | When doing GIC solutions if Yes then assume the grid topology is fixed, allowing for faster solutions |
| `TimeDomainOptionInteger:1` | GICDelaySeconds | Integer | Yes | GICDelaySeconds | GIC delay in seconds |
| `TimeDomainOptionString:29` | MergeWeatherStationOnLoad | String | Yes | MergeWeatherStationOnLoad | If yes then on a load merge the weather stations; otherise replace existing weather stations |
| `TimeDomainOptionString:23` | OPFSaveBindingConstraints | String | Yes | OPFSaveBindingConstraints | If Yes then save the OPF binding constraints |
| `TimeDomainOptionString:38` | PauseOnError | String | Yes | PauseOnError | Automatically pauses the time step solution if there is an error |
| `TimeDomainOptionString:18` | PauseOnNoSolution | String | Yes | PauseOnNoSolution | If Yes then pause if the time point does not solve |
| `TimeDomainOptionString:31` | PlayBackAllowWithNoStoredStates | String | Yes | PlayBackAllowWithNoStoredStates | If yes then on the Stored Solution Playback Dialog times can be played back with no stored states; useful for weather and GIC electric fields |
| `TimeDomainOptionString:35` | PWWReadDefaultSolutionType | String | Yes | PWWReadDefaultSolutionType | Default solution type to use when reading PWW files |
| `TimeDomainOptionString:34` | PWWReadRetainCustomInputDefinitions | String | Yes | PWWReadRetainCustomInputDefinitions | If yes then when reading a pww file any existing custom input defintions are retained; default is Yes |
| `TimeDomainOptionString:32` | RefreshDisplaysEachTimeStep | String | Yes | RefreshDisplaysEachTimeStep | If yes then then all the displays are refreshed each time step; during simulations in which the solution is fast, having this flag set yes can substantially slow dow the simulation |
| `TimeDomainOptionString:27` | RunTimeBackward | String | Yes | RunTimeBackward | If yes then time results backward in the simulation |
| `TimeDomainOptionString:28` | SaveWeatherStationInTSB | String | Yes | SaveWeatherStationInTSB | If yes then same the weather stations in the tsb; otherwise don't save them |
| `TimeDomainOptionString:30` | ShowTimeMilliSeconds | String | Yes | ShowTimeMilliSeconds | If yes then include milliseconds in the time; this is uncommon, mostly with GIC calculations |
| `TimeDomainOptionString:8` | SimulatorApplyInterpolate | String | Yes | SimulatorApplyInterpolate | If Yes then results are interpolated when running in Simulator |
| `TimeDomainOptionString:9` | SimulatorPauseAtEnd | String | Yes | SimulatorPauseAtEnd | If Yes then the simulation is paused at the end when running in Simulator |
| `TimeDomainOptionString:20` | SolveUnconstrainedCase | String | Yes | SolveUnconstrainedCase | If Yes then before doing an OPF always solve the unconstrained case |
| `TimeDomainOptionInteger` | TimeScaleSecPerHour | Integer | Yes | TimeScaleSecPerHour | Seconds for one hour of simulation time |
| `TimeDomainOptionString:33` | TimezoneisDaylightTime | String | Yes | TimeZone is Daylight Time | If yes then the timezone offset is based on daylight savings time; only used for display |
| `TimeDomainOptionSingle` | TimeZoneHoursOffset | Real | Yes | TimeZoneHoursOffset | Timezone offset in hours from UTC |
| `TimeDomainOptionString:37` | WeatherUpdateDisplaysOnDialogShow | String | Yes | WeatherUpdateDisplaysOnDialogShow | When yes the main weather and all the displays are updated when the weather dialog is showed for a time point |

#### `Weather_Options` (48 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `WeatherOptionString` | DateTimeUseLocal | String | Yes | DateTimeUseLocal |  |
| `WeatherOptionInteger:9` |  | Integer | Yes | DisplayBranchInterpolation | Indicates the approach used for interpolating weather along the branch: 0=closest station, 1=closest two stations |
| `WeatherOptionSingle:8` |  | Real | Yes | DisplayBranchLengthKM | Indicates the distance increment to use along the branch for showing the weather |
| `WeatherOptionString:2` | DisplayUnitsTemperature | String | Yes | DisplayUnitsTemperature |  |
| `WeatherOptionString:3` | DisplayUnitsWindSpeed | String | Yes | DisplayUnitsWindSpeed |  |
| `WeatherOptionInteger:3` | FindHourUTC | Integer | Yes | FindHourUTC | When analyyzing weather this is the UTC hour to check |
| `WeatherOptionString:5` |  | String | Yes | FindIgnoreOceanValues | If yes then ignore the ocean values when doing outlier finds |
| `WeatherOptionString:1` | FindIncludeEntireFootprint | String | Yes | FindIncludeEntireFootprint |  |
| `WeatherOptionSingle:1` | FindLatMax | Real | Yes | FindLatMax |  |
| `WeatherOptionSingle` | FindLatMin | Real | Yes | FindLatMin |  |
| `WeatherOptionSingle:3` | FindLonMax | Real | Yes | FindLonMax |  |
| `WeatherOptionSingle:2` | FindLonMin | Real | Yes | FindLonMin |  |
| `WeatherOptionInteger:6` | FindOutlierConditionMeasType | Integer | Yes | FindOutlierConditionMeasType | When analyzing weather this is the condition measurement type; same types as the FindOutlierMeasType |
| `WeatherOptionInteger:5` | FindOutlierConditionType | Integer | Yes | FindOutlierConditionType | When analyzing weather this is the condition type: 0=none, 1=less than, 2=greater than, 3=in range, 4=out-of-range |
| `WeatherOptionSingle:4` | FindOutlierConditionValue | Real | Yes | FindOutlierConditionValue1 |  |
| `WeatherOptionSingle:7` |  | Real | Yes | FindOutlierConditionValue2 |  |
| `WeatherOptionInteger:2` | FindOutlierMeasType | Integer | Yes | FindOutlierMeasType | When analyzing weather this is the measurement type to check; current 0=temp, 1=dew point, 2=cloud cover percentage, 3=wind speed, 4=wind direction, 5=wind speed 100m, 6=GHI, 7=DHI |
| `WeatherOptionInteger:4` | FindOutlierType | Integer | Yes | FindOutlierType | When analyzing weather this is the type comparison; 0=minimum, 1=maximum |
| `WeatherOptionString:4` | FindSimilarDateTimeISO8601 | String | Yes | FindSimilarDateTimeISO8601 |  |
| `WeatherOptionInteger:1` | FindYearEnd | Integer | Yes | FindYearEnd | When analyzing weather this is the last year to check |
| `WeatherOptionInteger` | FindYearStart | Integer | Yes | FindYearStart | When analyzing weather this is the first year to check |
| `WeatherOptionInteger:10` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:10 | DSC::Weather_Options_WeatherOptionInteger:10 |
| `WeatherOptionInteger:11` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:11 | DSC::Weather_Options_WeatherOptionInteger:11 |
| `WeatherOptionInteger:12` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:12 | DSC::Weather_Options_WeatherOptionInteger:12 |
| `WeatherOptionInteger:13` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:13 | DSC::Weather_Options_WeatherOptionInteger:13 |
| `WeatherOptionInteger:14` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:14 | DSC::Weather_Options_WeatherOptionInteger:14 |
| `WeatherOptionInteger:15` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:15 | DSC::Weather_Options_WeatherOptionInteger:15 |
| `WeatherOptionInteger:16` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:16 | DSC::Weather_Options_WeatherOptionInteger:16 |
| `WeatherOptionInteger:17` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:17 | DSC::Weather_Options_WeatherOptionInteger:17 |
| `WeatherOptionInteger:18` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:18 | DSC::Weather_Options_WeatherOptionInteger:18 |
| `WeatherOptionInteger:19` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:19 | DSC::Weather_Options_WeatherOptionInteger:19 |
| `WeatherOptionInteger:20` |  | Integer | Yes | FLD::Weather_Options_WeatherOptionInteger:20 | DSC::Weather_Options_WeatherOptionInteger:20 |
| `WeatherOptionString:10` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:10 | DSC::Weather_Options_WeatherOptionString:10 |
| `WeatherOptionString:11` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:11 | DSC::Weather_Options_WeatherOptionString:11 |
| `WeatherOptionString:12` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:12 | DSC::Weather_Options_WeatherOptionString:12 |
| `WeatherOptionString:13` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:13 | DSC::Weather_Options_WeatherOptionString:13 |
| `WeatherOptionString:14` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:14 | DSC::Weather_Options_WeatherOptionString:14 |
| `WeatherOptionString:15` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:15 | DSC::Weather_Options_WeatherOptionString:15 |
| `WeatherOptionString:16` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:16 | DSC::Weather_Options_WeatherOptionString:16 |
| `WeatherOptionString:17` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:17 | DSC::Weather_Options_WeatherOptionString:17 |
| `WeatherOptionString:9` |  | String | Yes | FLD::Weather_Options_WeatherOptionString:9 | DSC::Weather_Options_WeatherOptionString:9 |
| `WeatherOptionString:7` |  | String | Yes | GRIBDecodeData | If yes then decode all the data when loading the messages |
| `WeatherOptionSingle:5` | OneLocLat | Real | Yes | OneLocLat | When doing one location analysis this is the latitude to check |
| `WeatherOptionSingle:6` | OneLocLon | Real | Yes | OneLocLon | When doiing one location analysis this is the longitude to check |
| `WeatherOptionInteger:8` | OneLocYearEnd | Integer | Yes | OneLocYearEnd | When doing one location analysis this is the ending year |
| `WeatherOptionInteger:7` | OneLocYearStart | Integer | Yes | OneLocYearStart | When doing one location analysis this is the starting year |
| `WeatherOptionString:8` |  | String | Yes | PFWStochasticIncludePFDefault | If yes then include the stochastic PFW models when setting the PFW models for a power flow solution |
| `WeatherOptionString:6` |  | String | Yes | PWWReducePrefixDefault | Default prefix to use when saving reduced PWW files |

### Real-time, alarms, SDI

#### `RT_Study_Options` (28 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `ARCHIVE_Active` |  | String | Yes/Always | ARCHIVE_Active |  |
| `ARCHIVE_ArcNumRetrievals` |  | Integer | Yes/Always | ARCHIVE_ArcNumRetrievals |  |
| `ARCHIVE_FileNameConsCase` |  | String | Yes/Always | ARCHIVE_FileNameConsCase |  |
| `ARCHIVE_FileNameFullCase` |  | String | Yes/Always | ARCHIVE_FileNameFullCase |  |
| `ARCHIVE_Populate` |  | String | Yes/Always | ARCHIVE_Populate |  |
| `ARCHIVE_RunPF` |  | String | Yes/Always | ARCHIVE_RunPF |  |
| `ARCHIVE_SaveConsCase` |  | String | Yes/Always | ARCHIVE_SaveConsCase |  |
| `ARCHIVE_SaveConsType` |  | String | Yes/Always | ARCHIVE_SaveConsType |  |
| `ARCHIVE_SaveFullCase` |  | String | Yes/Always | ARCHIVE_SaveFullCase |  |
| `ARCHIVE_UseSuffixFullSave` |  | String | Yes/Always | ARCHIVE_UseSuffixFullSave |  |
| `RTCreateShuntBlocks` |  | String | Yes/Always | Convert Shunts to Blocks | When saving a consolidated case, switched shunts at the same superbus will be combined into a single switched shunt with multiple blocks. |
| `RTOpenDeadBranches` |  | String | Yes/Always | Open Non-Energized Branches | When saving a consolidated case, any branch where both terminal buses are disconnected will have its Status set to OPEN. |
| `POPULATION_CheckTPError` |  | String | Yes/Always | POPULATION_CheckTPError |  |
| `POPULATION_CorrectCBStatus` |  | String | Yes/Always | POPULATION_CorrectCBStatus |  |
| `POPULATION_CreateUPFRef` |  | String | Yes/Always | POPULATION_CreateUPFRef |  |
| `POPULATION_EqualBranchVolt` |  | String | Yes/Always | POPULATION_EqualBranchVolt |  |
| `POPULATION_RetainNodeVoltages` |  | String | Yes/Always | POPULATION_RetainNodeVoltages |  |
| `POPULATION_RunTPAfterRetrieval` |  | String | Yes/Always | POPULATION_RunTPAfterRetrieval |  |
| `POPULATION_UseAngleTap` | POPULATION_UseAngleTop | String | Yes/Always | POPULATION_UseAngleTap |  |
| `POPULATION_UseVoltageTop` |  | String | Yes/Always | POPULATION_UseVoltageTop |  |
| `RTEstimateUnpopulated` |  | String | Yes/Always | RTEstimateUnpopulated |  |
| `RTOptimizeBaseCase` | OptimizeBaseCaseStorage | String | Yes/Always | RTOptimizeBaseCase |  |
| `RTSetBaseCase` |  | String | Yes/Always | RTSetBaseCase |  |
| `RTSetBaseCase:1` | StorePreviousMonitoredValues | String | Yes/Always | RTSetBaseCase:1 |  |
| `SavePreservesCB` | SaveCTGsAndRelated | String | Yes/Always | Save Contingencies and Related Objects | When saving a consolidated case, contingencies, primary contingencies, remedial actions, and other related contingency objects will be saved with the case, and branches that are part of any of these contingency related objects will not be consolidated. |
| `STUDYMODE_FileNameSimulator` |  | String | Yes/Always | STUDYMODE_FileNameSimulator |  |
| `STUDYMODE_FileNameStudyCase` |  | String | Yes/Always | STUDYMODE_FileNameStudyCase |  |
| `STUDYMODE_RunPF` |  | String | Yes/Always | STUDYMODE_RunPF |  |

#### `AlarmOptions` (25 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `RTAlarmLog:1` |  | String | Yes/Always | Active Alarm Log |  |
| `AlarmFadeColor` |  | Integer | Yes/Always | Alarm fade color 1 |  |
| `AlarmFadeColor:1` |  | Integer | Yes/Always | Alarm fade color 2 |  |
| `RTAlarmLog` |  | String | Yes/Always | Alarm Log |  |
| `CaseInfoAuxDataFormat` |  | String | Yes/Always | AUX Data Format |  |
| `SchedAlarmTimeBuffer:1` |  | Real | Yes/Always | Buffer Time After |  |
| `SchedAlarmTimeBuffer` |  | Real | Yes/Always | Buffer Time Before |  |
| `EnableChatterBuffer` |  | String | Yes/Always | Chatter Buffer |  |
| `ChatterBufferInhibitTime` |  | String | Yes/Always | Chatter Buffer Inhibit Time |  |
| `ChatterBufferPeroid` |  | String | Yes/Always | Chatter Buffer Peroid |  |
| `ChatterBufferThreshold` |  | String | Yes/Always | Chatter Buffer Threshold |  |
| `DefaultInhibitExpire` |  | Integer | Yes/Always | Default Inhibit Expire |  |
| `AlarmBackgroundFading` |  | String | Yes/Always | Do alarm background fading |  |
| `ExpireAllInhibitEnable` |  | String | Yes/Always | Expire All Inhibit Enable |  |
| `ExpireAllInhibit` |  | String | Yes/Always | Expire All Inhibit Time |  |
| `ExpireAllInhibit:1` |  | String | Yes/Always | Expire All Inhibit Time |  |
| `ExpireAllInhibit:2` |  | String | Yes/Always | Expire All Inhibit Time |  |
| `ExpireAllInhibit:3` |  | String | Yes/Always | Expire All Inhibit Time |  |
| `ExpireAllInhibit:4` |  | String | Yes/Always | Expire All Inhibit Time |  |
| `ExpireAllInhibit:5` |  | String | Yes/Always | Expire All Inhibit Time |  |
| `MetaThreshold` |  | Integer | Yes/Always | Meta Threshold |  |
| `MetaThresholdEnabled` |  | String | Yes/Always | Meta Threshold Enabled |  |
| `ProcessChangeMonitorsInParallel` |  | String | Yes/Always | ProcessChangeMonitorsInParallel |  |
| `QualityCodeBufferTime` |  | String | Yes/Always | Quality Buffer Time |  |
| `EnableQualityCodeBuffer` |  | String | Yes/Always | Quality Code Buffer |  |

#### `SDI_Options` (5 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `SDIAutoAssignLoad` | AutoAssignLoad | String | Yes | FLD::SDI_Options_SDIAutoAssignLoad | DSC::SDI_Options_SDIAutoAssignLoad |
| `SDIClassification` | Classification | String | Yes | FLD::SDI_Options_SDIClassification | DSC::SDI_Options_SDIClassification |
| `SDIDistanceUnits` | DistanceUnits | Integer | Yes | FLD::SDI_Options_SDIDistanceUnits | DSC::SDI_Options_SDIDistanceUnits |
| `SDIMaxDistance` | MaximumDistanceforLoad | Real | Yes | FLD::SDI_Options_SDIMaxDistance | DSC::SDI_Options_SDIMaxDistance |
| `SDIMinMW` | MinimumMWforLoad | Real | Yes | FLD::SDI_Options_SDIMinMW | DSC::SDI_Options_SDIMinMW |

### Outside steady-state scope (listed for completeness)

#### `Transient_Options` (132 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `TSOBusIDFormat` | GNRL_ResultsEventsBusID | String | Yes | General\Bus ID Format for Events and Results | This is the format to use when displaying result information and event descriptions: "Name", "Number", "Name(Number)", "Number(Name)", "Name_KV", "Number_KV", "Name_KV(Number)", "Number(Name_KV)" |
| `Interactive` | GRNL_Interactive | String | Yes | General\Interactive | Set to YES to allow interactive mode. |
| `TSOUpdateDisplayNTimeStep` | GNRL_UpdateDisplayInterval | Integer | Yes | General\Interval to Update User Interface Displays | Interval Check: Number of time steps after which displays are updated. |
| `TSORestoreTimePointIntervalSec` | RTP_IntervalSec | Real | read-only | General\Restore Time Point Auto Save Interval (Seconds) | For the restore time points, gives the interaval in seconds for which restore time points are automatically saved |
| `TSORestoreTimePointIntervalMaxCount` | RTP_IntervalMaxCount | Integer | read-only | General\Restore Time Point Auto Save Max Count | For the restore time points, gives the maximum number of restore time points to automatically saved; once this limit is reached newer time points are deleted. |
| `TSORunProportionalMult` | GNRL_RunPropToRealTimeMult | Real | Yes | General\Run Proportional Slow Down Multiplier | Specify a multiplier regarding how much slower than real-time to run. For example, 60 means 1 minute = 1 second. |
| `TSORunProportional` | GNRL_RunPropToRealTime | String | Yes | General\Run Proportional to Real-Time | Set to YES to run the simulation at a speed proportional to real-time |
| `TSOShowResultPageWhenDone` | GNRL_ShowResultsPageWhenDone | String | Yes | General\Show Results Page When Done | Set to YES to automatically go the Results page after a transient stability run is completed |
| `TSOTransferOnEvent` | GNRL_TransferResultsOnEvent | String | Yes | General\Transfer Immediately for Events | Set to YES to transfer data back to the user interface immediately after an event |
| `TSOTransferOnManualTimeStep` | GNRL_TransferResultsManual | String | Yes | General\Transfer on Manual Time Step | Set to YES to transfer data back to the user interface after each manual control time step |
| `TSOTransferOnRunUntil` | GNRL_TransferResultsRunUntil | String | Yes | General\Transfer on Run Until | Set to YES to transfer data back to the user interface after each manual control Run Until |
| `TSOTimeStepUpdateTransferToPF` | GNRL_TransferResultsOnUpdate | String | Yes | General\Transfer on Time Step Interval Check | Set to YES to transfer data back to the user interface after each interval check |
| `TSOTimeStepUpdateResults` | GNRL_UpdateDisplay | String | Yes | General\Update Results on Time Step Interval Check | Set to YES to update displays after each interval check |
| `TSOSynGenAngleAction` | GLM_AngleAbsDevAction | String | Yes | Generic Limit Monitor\Abs Angle Deviation Action | Type of action to take when the absolute angle deviation is exceeded for the specified Time. May be set to Ignore, Log Warning, Trip, or Abort |
| `TSOSynGenAngleSec` | GLM_AngleAbsDevTime | Real | Yes | Generic Limit Monitor\Abs Angle Deviation Time | The absolute angle deviation must also be exceeded for this time in seconds before the limit monitor is considered violated |
| `TSOSynGenAngleDeg` | GLM_AngleAbsDevValue | Real | Yes | Generic Limit Monitor\Abs Angle Deviation Value | Absolute Angle Deviation (from the initial state) that a generator's internal angle must go for the limit monitor to be violated. |
| `TSOSynGenCBDelayCycles` | GLM_BreakerDelayCycles | Real | Yes | Generic Limit Monitor\Breaker Delay Time in Cycles | If a generic limit monitor specifies an action type of Trip, then the device will be tripped after this delay in cycles |
| `SynGenSpeedHighAction` | GLM_SpeedHighAction | String | Yes | Generic Limit Monitor\High Speed Action | Type of action to take when the High Speed Value is exceeded for the specified Time. May be set to Ignore, Log Warning, Trip, or Abort |
| `SynGenSpeedHighSec` | GLM_SpeedHighTime | Real | Yes | Generic Limit Monitor\High Speed Time | The Speed must also be above the High Speed Value for this time in seconds before the limit monitor is considered violated |
| `SynGenSpeedHigh` | GLM_SpeedHighValue | Real | Yes | Generic Limit Monitor\High Speed Value | Speed in per unit above which the synchronous generator must go for the limit monitor to be violated. |
| `TSOImpRelayAction` | GLM_ImpRelayAction | String | Yes | Generic Limit Monitor\Impedance Relay Action | Type of action to take when impedance relay reach is violated for the specified Time. May be set to Ignore, Log Warning, Trip, or Abort |
| `TSOImpRelayFilterName` | GLM_ImpRelayFilterName | String | Yes | Generic Limit Monitor\Impedance Relay Filter Name | Branch filter name that will be used to apply the impedance relay |
| `TSOImpRelayReach` | GLM_ImpRelayReach | Real | Yes | Generic Limit Monitor\Impedance Relay Reach | Impedance Relay Reach In % |
| `TSOImpRelayTime` | GLM_ImpRelayTime | Real | Yes | Generic Limit Monitor\Impedance Relay Time | Impedance Relay Time In Seconds |
| `SynGenSpeedLowAction` | GLM_SpeedLowAction | String | Yes | Generic Limit Monitor\Low Speed Action | Type of action to take when the Low Speed Value is exceeded for the specified Time. May be set to Ignore, Log Warning, Trip, or Abort |
| `SynGenSpeedLowSec` | GLM_SpeedLowTime | Real | Yes | Generic Limit Monitor\Low Speed Time | The Speed must also be below the Low Speed Value for this time in seconds before the limit monitor is considered violated |
| `SynGenSpeedLow` | GLM_SpeedLowValue | Real | Yes | Generic Limit Monitor\Low Speed Value | Speed in per unit below which the synchronous generator must fall for the limit monitor to be violated. |
| `TSOMaxAngleDifference` | GLM_MaxAngleDiff | Real | Yes | Generic Limit Monitor\Maximum Angle Difference | Maximum Angle Difference allowed |
| `TSOSynGenOnlyNoRelay` | GLM_OnlyApplyNoRelay | String | Yes | Generic Limit Monitor\Only Apply if No Relay | Set to YES to apply the Generic Synchronous Generator Limit Monitors only to those generators that do not have a specific relay model defined |
| `TSOManualTimeSteps` | MANCTRL_NumTimeStep | Integer | Yes | Manual Control\Number of Time Steps | When using manual control, run this number of time steps. |
| `TSOManualRunUntilTime` | MANCTRL_RunUntilTime | Real | Yes | Manual Control\Run Until Time | When using manual control, run until this specific time |
| `TSOBusFreqCalcROCOF` | MOD_FreqCalcROCOF | String | Yes | Modeling\Calculate Bus ROCOF | Set to YES to calculate the bus rate of change of frequency (ROCOF) |
| `TSODefaultLoadModel` | MOD_LoadModelDefault | String | Yes | Modeling\Default Load Model | Default Load Model. This load model will be used for all loads that do not have a transient stablity load model characteristic specified: "Impedance", "ZIP", "Current", or "PI, QZ" |
| `TSExciterParamCalc` | MOD_ExciterAutoParam | String | Yes | Modeling\Exciter Automatic Parameter Treatment | Set to either GE Approach for Vr=Zero or PSSE Approach for Vr>Zero |
| `TSOFastValvingOption` | MOD_FastValvingOption | String | Yes | Modeling\Fast Valving Option | Fast Valving Initation Option: "Frequency", "Time", "Specify", "None"; "Frequency" means after rotor speed deviation in rad/sec threshold is met. "Time" means a time delay after the first user specified TSContingencyElement. "Specify" means at a particular time. "None" means never. |
| `TSOFastValvingParameter` | MOD_FastValvingParameter | Real | Yes | Modeling\Fast Valving Parameter | Fast Valving Parameter. If Fast Valving Option is "Frequency" then units are rad/sec. If Option is "Time" then units are seconds. |
| `TSOForceSolution` | MOD_NetworkForceUpdateTime | Real | Yes | Modeling\Force Network Equations Update Time | Force the network equations to rebuild the Jacobian at least once every so many seconds. |
| `TimeDelay` | MOD_GICTimeDelay | Real | Yes | Modeling\GIC Time Delay | Specify the number of seconds used as a time delay for the GIC currents. |
| `TSOInitLimitViolation` | MOD_InitLimitViolations | String | Yes | Modeling\Handling Initial Limit Violations | Specify how to handle limit violations in the initial conditions: Modify, Abort, or Run |
| `TSOIgnorePSDynamics` | MOD_GICSolutionOnly | String | Yes | Modeling\Ignore PS Dynamics | Ignore the power system dynamics during the transient stability solution |
| `TSOIgnoreSpeedInSwing` | MOD_GenIgnoreSpeedEffects | String | Yes | Modeling\Ignore Speed Effects in Generator Swing Equation | Set to YES to ignore speed effects in the generator switch equations. |
| `IncludePDCI` | MOD_IncludePDCI | String | Yes | Modeling\Include PDCI | Set to YES to automatically include the dynamics of the Pacific DC Intertie if an appropriate MTDC record exists. |
| `RemedialActionInclude` | MOD_RemedialActionInclude | String | Yes | Modeling\Include Remedial Actions | Set to YES to include Remedial Actions in the transient stability analysis. |
| `TSOInfiniteBusModeling` | MOD_InfiniteBus | String | Yes | Modeling\Infinite Bus Modeling | Set to YES to allow slack buses to be modeled as infinite buses |
| `PlayIn` | MOD_FreqInitFromPlayIn | String | Yes | Modeling\Inital System Frequency set by PlayIn | Set to YES so that the initial system frequency is determined by the PlayIn object. |
| `TSInitFrequency` | MOD_FreqInit | Real | Yes | Modeling\Initial System Frequency (Hz) | Initial uniform system frequency; usually identical to nominal frequency, but can be slightly different when doing PMU matching; must be with 5% of nominal frequency |
| `ConvergenceTol:1` | MOD_NetworkInnerLoopScalar | Real | Yes | Modeling\Inner Time Step Network Equations Solution Tolerance | When using a integration method such as Runga-Kutta order 2, additional network equation solution occur for each time step. This multiplier can be used to increase the convergence tolerance for the inner time step solutions. |
| `IntegrationMethod` | MOD_IntegrationMethod | String | Yes | Modeling\Integration Method | Specify either "RK2" or "Euler" to specify whether to use the Second Order Runga-Kutta or Euler's method for each dynamic time step |
| `TSIslandNewCount` | MOD_IslandNewCountBus | Integer | Yes | Modeling\Island New Count Bus | A newly created island must have this many buses to continue being numerically simulated |
| `TSIslandNewCount:1` | MOD_IslandNewCountGen | Integer | Yes | Modeling\Island New Count Gen | A newly created island must have this many online generators to continue being numerically simulated |
| `TSIslandSynchHz` | MOD_IslandSyncHz | Real | Yes | Modeling\Island Sync Hz | Tells how to change the frequency of an island when synchronizing to a large island: 0=shift by the specified amount relative to the other island, 1=shift by amount only if the difference is larger than the specified amount, 2=no shift |
| `TSIslandSyncDegOption` | MOD_IslandSyncDegreeOption | Integer | Yes | Modeling\Island Sync. Degree Option | Tells how to change the angle of an island when synchronizing to a larger island: 0=shift by the specified frequency relative to the other island, 1=shift by amount only if the difference is larger than the specified amount, 2=no shift |
| `TSIslandSyncDeg` | MOD_IslandSyncDegree | Real | Yes | Modeling\Island Sync. Degrees | Tells how to change the angle of an island when synchronizing to a larger island: 0=shift by the specified amount relative to the other island, 1=shift by amount only if the difference is larger than the specified amount, 2=no shift |
| `TSIslandSyncHzOption` | MOD_IslandSyncHzOption | Integer | Yes | Modeling\Island Sync. Hz Option | Tells how to change the frequency of an island when synchronizing to a large island: 0=shift by the specified amount relative to the other island, 1=shift by amount only if the difference is larger than the specified amount, 2=no shift |
| `TSLoadOnlyOrDistGenAndLoad` | MOD_LoadOnlyOrDistGenAndLoad | String | Yes | Modeling\Load Only Or Dist Gen And Load | Set how the relay or event scaling will scale/affect the loads. The options are to affect Only Load MW and MVAR; or Dist Gen and Load MW and MVAR |
| `TSMachSatIgnore` | MOD_MachineS12LessS10 | String | Yes | Modeling\Machine Saturation S12 less S10 Treatment | Set to either Flip Values or Ignore to specify whether the automatically flip values for valid input or just ignore saturation completely |
| `TSOComplexLoadMinMW` | MOD_LoadCompMinMW | Real | Yes | Modeling\Minimum MW for Complex Load Models | Minimum MW value for representing a load using a complex load model; this minimum prevents very small loads from being represented by computationally intensive load models. "Complex Loads" are models which are not intended to represent one particular device, but instead represent an composite various of load types. Examples include CLOD, CPMLDW, and MOTORW. This also is used as a filter on using a Distribution Equivalent model. |
| `TSODistEquivXFMinNomkV` | MOD_LoadDistEquivMinKV | Real | Yes | Modeling\Minimum Nom KV for Distribution Equivalent | Minimum terminal bus Nominal kV for a load model to use a distribution equivalent |
| `TSOComplexLoadMinPQRatio` | MOD_LoadCompMinPQRatio | Real | Yes | Modeling\Minimum P/Q Ratio for Complex Load Models | Minimum absolution P/Q ratio for representing loads with complex load models; since the distribution and feeder impedance is specified on the MW base, a small P/Q ratio can cause difficulties. "Complex Loads" are models which are not intended to represent one particular device, but instead represent an composite various of load types. Examples include CLOD, CPMLDW, and MOTORW. This also is used as a filter on using a Distribution Equivalent model. |
| `TSOComplexLoadMinVpu` | MOD_LoadCompMinVpu | Real | Yes | Modeling\Minimum Per Unit Voltage for Complex Load Models | Minimum terminal bus voltage in per unit for representing a load using a complex load model. "Complex Loads" are models which are not intended to represent one particular device, but instead represent an composite various of load types. Examples include CLOD, CPMLDW, and MOTORW. This also is used as a filter on using a Distribution Equivalent model. |
| `Inhibit` | MOD_FreqRelayMinVpu | String | Yes | Modeling\Minimum pu voltage for frequency relay | Specify a value of per unit voltage below which all frequency relays will treat their measured frequency as nominal frequency representing the voltage inhibit behavior of frequency relays. |
| `MotorW` | MOD_MotorW | String | Yes | Modeling\MotorW Treatment | Set to either PSLF or FULL. Setting to PSLF will model the induction motor using the MOTORW treatment used in PSLF. |
| `ConvergenceTol` | MOD_NetworkPUConvergenceTol | Real | Yes | Modeling\Network Equations Solution Convergence Tolerance | Specify the convergence tolerance used in the transient stability's network equations solution algorithm. |
| `MaxItr` | MOD_NetworkMaxItr | Integer | Yes | Modeling\Network Equations Solution Maximum Iterations | Specify the maximum number of iterations used in the transient stability's network equations solution algorithm. |
| `TSOAbortNumNetworkSolutions` | MOD_NetworkAbortFailCount | Integer | Yes | Modeling\Number of Failed Network Solutions to Abort | If this number of consecutive network solutions fail because the maximum iteration count is reached, then the entire simulation will be aborted. |
| `SaturationModel` | MOD_ExciterSaturationModel | String | Yes | Modeling\Saturation Model for Exciters | Specify either "Quadratic" or "Scaled Quadratic" or "Exponential" to specify what type of function is used to fit the two points given for a saturation function in an exciter model. Quadratic = A*(Input-B)^2; Scaled Quadratic = A*(Input-B)^2/Input; Exponential = A*Exp(B*Input) |
| `TSSatSEOneZero` | MOD_SatSEOneZero | Integer | Yes | Modeling\Saturation Treatment when one SE value is zero | Specify the treatment of saturation when one SE value is zero. Set to either 'Always Zero' or 'Normal Curve Fit'. |
| `Split` | MOD_EventsSplitTimeSteps | String | Yes | Modeling\Split Timestep for Non-User Events | Specify YES to have non-user-defined events split a numerical integration timestep for more precise timing. An example is a breaker delay set to trip in 3.1 cycles when using a timestep of 0.25 cycles. When splitting timesteps an extra time is inserted at a time related to 3.1 cycles, while when not spliting the breaker would open the device after 3.25 cycles, at the next time step after 3.1 cycles. The default is NO so that many extra timesteps are not added by user events. |
| `Split:1` | MOD_UserEventsSplitTimeSteps | String | Yes | Modeling\Split Timestep for User Events | Specify YES to have user-defined events split a numerical integration timestep for more precise timing. The default, and usual value is YES, but set to NO if there are many user defined events. An example is a breaker delay set to trip in 3.1 cycles when using a timestep of 0.25 cycles. When splitting timesteps an extra time is inserted at a time related to 3.1 cycles, while when not spliting the breaker would open the device after 3.25 cycles, at the next time step after 3.1 cycles. The default is NO so that many extra timesteps are not added by user events. |
| `TSBusFreqMeasT` | MOD_FreqBusTimeConst | Real | Yes | Modeling\Time Constant for Bus Frequency Measurement | Bus Frequency is calculated by taking the derivative of the bus angles in the system using this time delay |
| `TripExtraVarsComponentTripping` | MOD_LoadTripExtraVarsComponents | String | Yes | Modeling\Trip Extra Mvar Component Tripping | Trip Extra Mvar from initialization when individual components are tripping in a complex load model such as include CLOD, CPMLDW, MOTORW and CompLoad. |
| `Undocumented` | MOD_UndocPILimits | String | Yes | Modeling\Undocumented PI Limit Enforcement | Set to YES to include various hystorically undocument limits on PI loops for Governor models. |
| `TSUseParallel` | MOD_UseParallelProcessing | String | Yes | Modeling\Use Parallel Processing | Set to Yes to allow single transient stability parallel processing |
| `TSOUseVoltageExtrapolation` | MOD_NetworkVoltExtrap | String | Yes | Modeling\Use voltage extrapolation in network equations solution | Set to YES to use a quadratic voltage extrapolation for initial guesses to the network equations. |
| `TSAllowCreationDialogFaultsSequenceNetwork` | MOD_AllowCreationDialogFaultsSequenceNetwork | String | Yes | Modelling\Allow Creation Dialog Calculate Effect Impedance from Sequence Networks | The use of this option is not recommended. When choosing it, you will be able to create fault actions that calculate the effective impedance from the sequence networks. We do not recommend this because most of our users running transient stability do not have sequence network information available and instead make sure of features such as applying a fault impedance to achieve a per unit voltage. |
| `TSAnalyzeTimeWindows` | RO_AnalyzeTimeWindows | String | Yes | Result Options\Analyze Time Windows | Automatically analyze time windows and keep Signal Violations after running a transient stability simulation |
| `TSOAngleRefGenID` | RO_AngleRefGenID | String | Yes | Result Options\Angle Reference Generator ID | ID of the reference generator |
| `TSOAngleRefGenNum` | RO_AngleRefGenNum | Integer | Yes | Result Options\Angle Reference Generator Num | Terminal bus number of the reference generator |
| `TSOInitRefAngleAtZero` | RO_AngleRefInitAtZero | String | Yes | Result Options\Angle Reference Initialize at Zero | Set to YES to initialize the reference angle to zero |
| `TSOAngleReferenceOption` | RO_AngleRefOption | String | Yes | Result Options\Angle Reference Option | Option for what to use as an angle reference: "Average", "Weighted Average", "Terminal Angle", "Internal Angle", "Synchronous" |
| `TSOSaveMinMaxValuesTime` | RO_SaveMinMaxStartTime | Real | Yes | Result Options\Custom Time for Saving Min/Max Values | Specify value in seconds. Use when starting to save the min/max values at a custom time. |
| `TSDoNotStoreEvents` | RO_DoNotStoreEvents | String | Yes | Result Options\Do not store events | Set to YES to not store events during the simulation |
| `TSDoNotStoreSolutionDetails` | RO_DoNotStoreDetails | String | Yes | Result Options\Do not store solution details | Set to YES to not store solution details during the simulation |
| `TSOStartLimitMonitoringValues` | RO_MonitorStart | String | Yes | Result Options\When to Start Monitoring Transient Limit Monitors | Specifies when to begin monitoring transient limit monitor values: "After last event", "Immediately" or "Custom Time". If Custom Time is specified then you must choose a value for that field. |
| `TSOStartLimitMonitoringValuesAfterLastEventTime` | RO_MonitorStartLastEventTime | Real | Yes | Result Options\When to Start Monitoring Transient Limit Monitors After Last Event Time | Specify value in seconds. Use when starting to monitoring transient limit monitor values at a specified time after the last event |
| `TSOStartLimitMonitoringValuesTime` | RO_MonitorStartTime | Real | Yes | Result Options\When to Start Monitoring Transient Limit Monitors Time | Specify value in seconds. Use when starting to monitoring transient limit monitor values at a custom time. |
| `TSOSaveMinMaxValues` | RO_SaveMinMaxStart | String | Yes | Result Options\When to Start Saving Min/Max Values | Specifies when to begin checking and saving min/max values: "After last event", "Immediately" or "Custom Time". If Custom Time is specified then you must choose a value for that field. |
| `TSOWhereResultEvents:3` | RO_EventsReportDSUser | String | Yes | Result Options\Where to store result events for Level = DS User | For Level = DS User, specify where to store results events. Options are "Event Only, Not Log","Both Log and Event" |
| `TSOWhereResultEvents:1` | RO_EventsReportModelTrip | String | Yes | Result Options\Where to store result events for Level = Model Trip | For Level = Model Trip, specify where to store results events. Options are "Event Only, Not Log","Both Log and Event" |
| `TSOWhereResultEvents:2` | RO_EventsReportRelayTrip | String | Yes | Result Options\Where to store result events for Level = Relay Trip | For Level = Relay Trip, specify where to store results events. Options are "Event Only, Not Log","Both Log and Event" |
| `TSOWhereResultEvents:4` | RO_EventsReportRemedialAction | String | Yes | Result Options\Where to store result events for Level = Remedial Action | For Level = Remedial Action, specify where to store results events. Options are "Event Only, Not Log","Both Log and Event" |
| `TSOWhereResultEvents` | RO_EventsReportTransition | String | Yes | Result Options\Where to store result events for Level = Transition | For Level = Transition, specify where to store results events. Options are "Event Only, Not Log","Both Log and Event" |
| `TSDoNotCombineRAMwithHDResults` | RS_DoNotCombineRAMWithHD | String | Yes | Result Storage\Do not combine RAM with stored HD Results | Set to YES to only show plot results stored in RAM and do not combine RAM results with Hard Drive stored results. |
| `ExpDirectory` | RSHD_Directory | String | Yes | Result Storage\Hard Drive Directory to Export to | Specifies the directory to which Every Result TSR files will be written. The filename is determined by the name of the Transient Contingency |
| `TSEveryResult:9` | RSHD_ArchiveAuto | String | Yes | Result Storage\Hard Drive Enable Auto-Archiving | Set to enable automatic archiving of TSR files |
| `TSEveryResult:5` | RSHD_IncArea | String | Yes | Result Storage\Hard Drive Export Area Results | Set to YES to save area results to the Every Result TSR file |
| `TSEveryResult:3` | RSHD_IncBranch | String | Yes | Result Storage\Hard Drive Export Branch Results | Set to YES to save branch results to the Every Result TSR file |
| `TSEveryResult:23` | RSHD_IncBusPair | String | Yes | Result Storage\Hard Drive Export Bus Pair Results | Set to YES to save Bus Pair results to the Every Result TSR file |
| `TSEveryResult:1` | RSHD_IncBus | String | Yes | Result Storage\Hard Drive Export Bus Results | Set to YES to save buse results to the Every Result TSR file |
| `TSEveryResult:4` | RSHD_IncDCLine | String | Yes | Result Storage\Hard Drive Export DC Line Results | Set to YES to save dc line results to the Every Result TSR file |
| `TSEveryResult` | RSHD_IncGen | String | Yes | Result Storage\Hard Drive Export Generator Results | Set to YES to save generator results to the Every Result TSR file |
| `TSEveryResult:13` | RSHD_IncInjectionGroup | String | Yes | Result Storage\Hard Drive Export Injection Group Results | Set to YES to save injection group results to the Every Result TSR file |
| `TSEveryResult:8` | RSHD_IncInterface | String | Yes | Result Storage\Hard Drive Export Interface Results | Set to YES to save interface results to Every Result TSR file |
| `TSEveryResult:19` | RSHD_IncLineShunt | String | Yes | Result Storage\Hard Drive Export Line Shunt Results | Set to Yes to store line shunt results to the Every Result TSR file |
| `TSEveryResult:2` | RSHD_IncLoad | String | Yes | Result Storage\Hard Drive Export Load Results | Set to YES to save load results to the Every Result TSR file |
| `TSEveryResult:20` | RSHD_IncMeasurementModel | String | Yes | Result Storage\Hard Drive Export Measurement Model Results | Set to Yes to store measurement model results to the Every Result TSR file |
| `TSEveryResult:24` | RSHD_IncModelExpression | String | Yes | Result Storage\Hard Drive Export Model Expression Results | Set to YES to save Model Expression results to the Every Result TSR file |
| `TSEveryResult:21` | RSHD_IncModelPlane | String | Yes | Result Storage\Hard Drive Export Model Plane Results | Set to YES to store model plane results to the Every Result TSR file |
| `TSEveryResult:7` | RSHD_IncMTDCConverter | String | Yes | Result Storage\Hard Drive Export MTDC Converter Results | Set to YES to save multi-terminal DC converter results to the Every Result TSR file |
| `TSEveryResult:12` | RSHD_IncMultiterminalDC | String | Yes | Result Storage\Hard Drive Export MTDC Record Results | Set to YES to save multiterminal DC record results to the Every Result TSR file |
| `TSEveryResult:16` | RSHD_StoreInput | String | Yes | Result Storage\Hard Drive Export Store Dynamic Input Fields | Set to YES to store dynamic model input fields to the Every Result TSR file |
| `TSEveryResult:15` | RSHD_StoreOther | String | Yes | Result Storage\Hard Drive Export Store Dynamic Other Fields | Set to YES to store dynamic model other fields to the Every Result TSR file |
| `TSEveryResult:14` | RSHD_StoreStates | String | Yes | Result Storage\Hard Drive Export Store Dynamic States | Set to YES to store dynamic model states to the Every Result TSR file |
| `TSEveryResult:18` | RSHD_IncSubstation | String | Yes | Result Storage\Hard Drive Export Substation Results | Set to YES to save substation results to the Every Result TSR file |
| `TSEveryResult:11` | RSHD_IncShunt | String | Yes | Result Storage\Hard Drive Export Switched Shunt Results | Set to YES to save switched shunt results to the Every Result TSR file |
| `TSEveryResult:17` | RSHD_IncSystem | String | Yes | Result Storage\Hard Drive Export System Results | Set to YES to save System results to the Every Result TSR file |
| `TSEveryResult:25` | RSHD_IncTransformer | String | Yes | Result Storage\Hard Drive Export Transformer Results | Set to YES to save Transformer results to the Every Result TSR file |
| `TSEveryResult:22` | RSHD_IncVSCDCLine | String | Yes | Result Storage\Hard Drive Export VSC DC Line Results | Set to YES to save VSC DC line results to the Every Result TSR file |
| `TSEveryResult:6` | RSHD_IncZone | String | Yes | Result Storage\Hard Drive Export Zone Results | Set to YES to save zone results to the Every Result TSR file |
| `TSEveryResult:10` | RSHD_ArchiveMaxNum | String | Yes | Result Storage\Hard Drive Max Archive Num | Set the maximum number of TSR archives to store. This is only used if Auto-Archiving is enabled. |
| `TSUseAreaZone` | RSHD_UseAreaZone | String | Yes | Result Storage\Hard Drive Use Area/Zone filters | Set to YES to only save objects which meet the Area/Zone filters to the Every Result TSR file |
| `TSOSaveResultsTimeStepsPerSave` | RS_SaveXTimeSteps | Integer | Yes | Result Storage\Save Every X Time Steps:1 | Specify the number of time steps to save data for while performing the transient stability run. |
| `TSOSaveResultsForOpenDevices` | RS_SaveOpenDevices | String | Yes | Result Storage\Save for Open Devices | Set to NO to not save results for devices that are opened regardless of other Save options |
| `TSSaveResultsToHardDrive` | RS_StoreHD | String | Yes | Result Storage\Save Results to Hard Drive | Set to YES to use the options related to saveing results to hard drive as they are calculated |
| `TSOStorageOption` | RS_SaveRAMinPWB | String | Yes | Result Storage\Save to the PWB the Results stored in RAM | Set to YES to to save in the results stored to RAM in the PWB file. |
| `TSStoreMinMaxInPWB` | RS_SaveMinMaxinPWB | String | Yes | Result Storage\Store Min/Max Results in PWB | Set to YES to store the Min/Max results in the PWB file |
| `TSStorePowerFlowState` | RS_SavePowerFlowState | String | Yes | Result Storage\Store Power Flow State | Set to YES to store the power flow state; use with caution since this can consume lots of memory! |
| `TSStoreResultsInRAM` | RS_StoreRAM | String | Yes | Result Storage\Store Results in RAM | Set to YES to use the options related to storing results in RAM as they are calculated |
| `TSOGroupResultsBy` | RESDISP_GroupBy | String | Yes | Results Display\Group Results by | Effects how results are grouped in columns in the user interface: "Object/Field" or "Field/Object" |
| `TSOResultsUseAreaZoneFilters` | RESDISP_UseAreaZone | String | Yes | Results Display\Use Area/Zone/Owner filters | Effects when Area/Zone/Owner filters are applied to filter columns in the user interface results. |
| `TSOMinDelt` | VAL_DeltaTimeStep | Real | Yes | Validation\Time Constant Minimum Time Step Multiple | Many models have time constants which must be larger than a multiple of the integration time step. This multiplier specified the multiple needed. |
| `TSOValidationAllowUnSupportedModel` | VAL_UnsupportedModels | String | Yes | Validation\Validation of Unsupported Models | How to validate unsupported models: "Error", "Warning", "None" |

#### `GIC_Options` (87 fields)

| field | concise | type | enterable | dialog path | description |
|---|---|---|---|---|---|
| `XFCoreScale` | MvarLoss1PhK1 | Real | Yes | AC Scaling by Core Type\Single Phase (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer made up of Single Phase devices. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:11` | MvarLoss1PhBP2 | Real | Yes | AC Scaling by Core Type\Single Phase (Per Unit Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer made up of Single Phase devices. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:12` | MvarLoss1PhK2 | Real | Yes | AC Scaling by Core Type\Single Phase (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer made up of Single Phase devices. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:2` | MvarLoss3Ph3LegK1 | Real | Yes | AC Scaling by Core Type\Three Phase, 3-Legged (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 3-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:9` | MvarLoss3Ph3LegBP2 | Real | Yes | AC Scaling by Core Type\Three Phase, 3-Legged (Per Unit Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 3-Legged. This model using a piecewise linear model; this is the per unit breakpoint. Per unit using transformer current base. |
| `XFCoreScale:10` | MvarLoss3Ph3LegK2 | Real | Yes | AC Scaling by Core Type\Three Phase, 3-Legged (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 3-Legged. This model using a piecewise linear model; this is the slope after the breakpoint. Per unit using transformer current base. |
| `XFCoreScale:15` | MvarLoss3Ph5LegBP2 | Real | Yes | AC Scaling by Core Type\Three Phase, 5-Legged (Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 5-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:3` | MvarLoss3Ph5LegK1 | Real | Yes | AC Scaling by Core Type\Three Phase, 5-Legged (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 5-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:16` | MvarLoss3Ph5LegK2 | Real | Yes | AC Scaling by Core Type\Three Phase, 5-Legged (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 5-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:17` | MvarLoss3Ph7LegBP2 | Real | Yes | AC Scaling by Core Type\Three Phase, 7-Legged (Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 7-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:4` | MvarLoss3Ph7LegK1 | Real | Yes | AC Scaling by Core Type\Three Phase, 7-Legged (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 7-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:18` | MvarLoss3Ph7LegK2 | Real | Yes | AC Scaling by Core Type\Three Phase, 7-Legged (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, 7-Legged. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:25` | MvarLoss3PhCoreBP2 | Real | Yes | AC Scaling by Core Type\Three Phase, Core Form Generic (Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, Core Form Generic. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:8` | MvarLoss3PhCoreK1 | Real | Yes | AC Scaling by Core Type\Three Phase, Core Form Generic (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, Core Form Generic. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:26` | MvarLoss3PhCoreK2 | Real | Yes | AC Scaling by Core Type\Three Phase, Core Form Generic (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, Core Form Generic. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:13` | MvarLoss3PhShellBP2 | Real | Yes | AC Scaling by Core Type\Three Phase, Shell Form (Breakpoint Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, Shell Form. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:1` | MvarLoss3PhShellK1 | Real | Yes | AC Scaling by Core Type\Three Phase, Shell Form (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, Shell Form. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:14` | MvarLoss3PhShellK2 | Real | Yes | AC Scaling by Core Type\Three Phase, Shell Form (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Three Phase, Shell Form. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:23` | MvarLossUnkLowBP2 | Real | Yes | AC Scaling by Core Type\Unknown Core, <= 200 kV (Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, <= 200 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:7` | MvarLossUnkLowK1 | Real | Yes | AC Scaling by Core Type\Unknown Core, <= 200 kV (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, <= 200 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:24` | MvarLossUnkLowK2 | Real | Yes | AC Scaling by Core Type\Unknown Core, <= 200 kV (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, <= 200 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:21` | MvarLossUnkMedBP2 | Real | Yes | AC Scaling by Core Type\Unknown Core, > 200 kV (Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, > 200 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:6` | MvarLossUnkMedK1 | Real | Yes | AC Scaling by Core Type\Unknown Core, > 200 kV (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, > 200 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:22` | MvarLossUnkMedK2 | Real | Yes | AC Scaling by Core Type\Unknown Core, > 200 kV (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, > 200 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:19` | MvarLossUnkHighBP2 | Real | Yes | AC Scaling by Core Type\Unknown Core, > 400 kV (Breakpoint) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, > 400 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:5` | MvarLossUnkHighK1 | Real | Yes | AC Scaling by Core Type\Unknown Core, > 400 kV (First Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, > 400 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `XFCoreScale:20` | MvarLossUnkHighK2 | Real | Yes | AC Scaling by Core Type\Unknown Core, > 400 kV (Second Segment) | Scaling used to convert GIC DC Amps to AC Mvar Losses for a transformer of core type: Unknown Core, > 400 kV. Per unit using transformer current base. Modeled as two piecewise linear segments. |
| `RTAutoUpdate` | TimeAutoUpdate | String | Yes | Auto Update | Set to YES to automatically recalculate the GIC DC currents when the GIC Current Time is changed) |
| `Mode` | CalcMode | String | Yes | Calculation Mode | Calculation Mode (Either SnapShot, TimeVarying, NonUniformTimeVarying, or SpatiallyUniformTimeVarying) |
| `MinkV:1` | TransDistMinkV | Real | Yes | Current Calculation Options\Assume Autotransformer Minimum Medium Side Voltage | When the Autotransformer status is unknown, only assume an autotranformer is the medium (non-tertiary) side kV voltage is larger than this value |
| `XFTapMax` | AutoXFMaxTurnsRatio | Real | Yes | Current Calculation Options\Assume Autotransformer Turns Ratio | When the Autotransformer status is unknown, only assume an autotranformer is the turns ratio is less than this value |
| `XFConfiguration:1` | DistXFConfigDefault | String | Yes | Current Calculation Options\Default Dist. Side XF Config | Default transformer configuration on the distribution side. |
| `XFConfiguration` | TransXFConfigDefault | String | Yes | Current Calculation Options\Default Trans. Side XF Config | Default transformer configuration on the transmission side. |
| `GICXFAlwaysMedVoltSubGround` | XFAlwaysMedVoltSubGround | String | Yes | Current Calculation Options\For transformers in multiple substations always ground them in the medium voltage substation | For transformers modeled in multiple substations always ground them in the medium (or low voltage for a two winder) substation. This situation is common with GSUs, in which the transformer itself is in the generator's substation but the high voltage bus is modeled in the nearby transmission susbstation. |
| `MinkV:2` | TransMinkVAlwaysGSU | Real | Yes | Current Calculation Options\Minimum High Side Voltage for Always GSU | If the medium voltage is low, any time the high voltage is above this kV the transformer is always assumed to be a GSU |
| `MinkV` | IgnoreInducedDCVoltBelowkV | Real | Yes | Current Calculation Options\Minimum Voltage to Include GIC | Do not model a dc voltage in series on branches with minimum nominal kV voltage below this value |
| `SubAutoInserted` |  | String | Yes | Current Calculation Options\Substation auto insert for buses with no lat/lon | Set to YES to auto insert substations for buses without latitude/longitude coordinates |
| `BusNoSub` |  | String | Yes | Current Calculation Options\Substation auto insert option | Specify where to auto insert substations for buses without substations. Set to either Group by Lat/Long, One Sub Per Bus, or None (Ungrounded) |
| `GICEFieldEventInteger:1` | EFieldEventsCountActive | Integer | read-only | Events\Count Active | Count of all the active events |
| `GICEFieldEventInteger` | EFieldEventsCount | Integer | read-only | Events\Count All | Count of all the events |
| `GICEFieldEventString:1` | EFieldEventsRefDateTimeLocal | String | read-only | Events\Reference Date/Time (Local) | Reference time of the earliest active event in the local time zone |
| `GICEFieldEventString` | EFieldEventsRefDateTimeUTC | String | read-only | Events\Reference Date/Time (UTC) | Reference time of the earliest active event in UTC |
| `GICEFieldEventInteger:2` | EFieldEventsTimeCount | Integer | read-only | Events\Time Series Count | Count of Time Series Voltage Input times |
| `GICEFieldEventSingle` | EFieldEventsTimeFirstSec | Real | read-only | Events\Time Series First Offset (Seconds) | Offset time in seconds for the first time point from the reference time |
| `GICEFieldEventSingle:1` | EFieldEventsTimeLastSec | Real | read-only | Events\Time Series Last Offset (Seconds) | Offset time in seconds for the last time point from the reference time |
| `GICEFieldEventSingle:2` | EFieldEventsTimeLineVoltMax | Real | read-only | Events\Time Series Max. Line Voltage | Maximum line voltage in the time series in volts |
| `GICEFieldEventSingle:3` | EFieldEventsTimeSubEFieldMaxVKM | Real | read-only | Events\Time Series Max. Substation Electric Field (V/km) | Maximum substation electric field in V/km |
| `GICEFieldEventString:2` | EFieldEventsfB3DSaveAll | String | Yes | FLD::GIC_Options_GICEFieldEventString:2 | DSC::GIC_Options_GICEFieldEventString:2 |
| `GICIncludeTimeDomain` | IncludeTimeDomain | String | Yes | FLD::GIC_Options_GICIncludeTimeDomain | DSC::GIC_Options_GICIncludeTimeDomain |
| `GICIncludeTimeDomainDateTime` | IncludeTimeDomainDateTime | String | read-only | FLD::GIC_Options_GICIncludeTimeDomainDateTime | DSC::GIC_Options_GICIncludeTimeDomainDateTime |
| `MSLineBusesGeoEstimatedSave` |  | String | Yes | For Multi-Section Lines Save Estimated Bus Latitude and Longitude | If YES then save the estimated latitude and longitude values for the multi-section line intermediate buses |
| `GICTimeSec` | TimeSeconds | Real | Yes | GIC Current Time | GIC Current Time in Seconds |
| `Latitude` | HotSpotLatitude | Real | Yes | Hotspot\Center Latitude | The latitude in degrees of the hotspot center |
| `Longitude` | HotSpotLongitude | Real | Yes | Hotspot\Center Longitude | The longitude in degrees of the hotspot center |
| `SOHeight` | HotSpotHeightMile | Real | Yes | Hotspot\Height | Height of the hotspot rectangle in Distance measure (Distance measure is determined by Efield Units option) |
| `GICHotspotHeightKM` | HotSpotHeightKM | Real | Yes | Hotspot\Height in km | Height of the hotspot rectangle in km |
| `Include:1` | HotSpotInclude | String | Yes | Hotspot\Include | Set to YES to include a hotspot in the Electric Field |
| `GICGeographicRegionSetName:1` | HotSpotGeographicRegionScalar | String | Yes | Hotspot\Scale value with geographic earth resistivity region | Set to YES to include the geographic earth resistivity region scalar in the hotspot efield |
| `GICMagLatFunctName:1` | HotSpotGeoMagLatitudeScalar | String | Yes | Hotspot\Scale value with geomagnetic latitude | Set to YES to include the geomagnetic latitude scalar in the hotspot efield |
| `GICGeographicRegionSetName:2` | HotSpotGeographicRegionHotSpotScalar | String | Yes | Hotspot\Use Hotspot scalar values of each region | Set to YES to to use the region's hotspot scalar, otherwise NO to use the region's scalar |
| `GICHotspotScalarVKM` | HotSpotValueScalarVKM | Real | Yes | Hotspot\Value of Field, V/km | Hotspot electric field in volts per km |
| `Magnitude` | HotSpotValueScalarVMile | Real | Yes | Hotspot\Value or Scalar | Hotspot electric field per Distance measure (Distance measure is determined by Efield Units option) |
| `SOWidth` | HotSpotWidthMile | Real | Yes | Hotspot\Width | Width of the hotspot rectangle in Distance measure (Distance measure is determined by Efield Units option) |
| `GICHotspotWidthKM` | HotSpotWidthKM | Real | Yes | Hotspot\Width in km | Width of the hotspot rectangle in km |
| `Include` | IncludeInPowerFlow | String | Yes | Include GIC in Power Flow | Set to YES to include the impact of GIC in the power flow solution by modeling an Constant Current AC Mvar loss on transformers based on the DC GIC Current |
| `CalcHigh` | CalcMaxDirection | String | Yes | Input\Calculate Maximum Direction | Set to YES to indicate that the maximum Efield direction should automatically be calculated |
| `GICCalcInducedDCVoltLowR` | CalcInducedDCVoltLowR | String | Yes | Input\Do not calculate DC voltages if Line Per Distance R is Low | If Yes then calculate DC voltages on lines that have low per unit distance R values; usually the R value is low because of an error in the geographic location for the substation or the bus is incorrectly mapped to a substation |
| `BusEquiv` | CalcInducedDCVoltEquiv | String | Yes | Input\Do not calculate DC voltages on Equivalent Lines | Set to YES to signify that DC voltages should not be modeled on equivalent lines |
| `LineLength` | CalcInducedDCVoltLength | Real | Yes | Input\Do not calculate DC voltages on Line Length | Do not calculate a dc voltage for lines which have a length shorter than this value (units are determined by the Efield Units field) |
| `EFieldMag` | EfieldMag | Real | Yes | Input\Electric Field Magnitude | Magnitude of the storm (units are DC Volt per Distance measure. Distance measure is determined by the Efield Units option) |
| `EFieldMagVKM` | EfieldMagKM | Real | Yes | Input\Electric Field Magnitude in V/km | Magnitude of the storm in volts per km |
| `EFieldMagVMile` | EfieldMagMile | Real | Yes | Input\Electric Field Magnitude in V/Mile | Magnitude of the storm in volts per mile |
| `EFieldAngle` | EfieldAngle | Real | Yes | Input\Electric Field Storm Direction | The direction of the storm in degrees (0 degrees = North; 90 degrees = East; 180 degrees = South; 270 degrees = West) |
| `UnitsType` | UnitType | String | Yes | Input\Electric Field Units | Electric Field Units (Either miles or km) |
| `GICGeographicRegionSetName` | GeographicRegionScalar | String | Yes | Input\GIC Active Geographic Region Set | Name of the active geographic region set. May set to blank to signify none in use. |
| `GICMagLatFunctName` | GeoMagLatitudeScalar | String | Yes | Input\GIC Active Geomagnetic Latitude Scaling | Name of the active geomagnetic latitude scaling function. May set to blank to signify none in use. |
| `GICEField3DFileMultLoad` | EField3dFileMultLoad | String | Yes | Input\Load multiple 3D electric field files | Tells whether to load multiple 3D electric field files in a directory: 0=just specified file, 1=all files after last time, 2=all files before first time, 3=all files of selected type. |
| `GICEField3DFileMerge` | EField3dFileMerge | String | Yes | Input\Merge 3D electric field data | If yes then when loading an input 3D electric field file the data is merged with existing data; otherwise any existing data is first deleted. |
| `GICEField3DFileNewNamePrompt` | EField3dFileNewNamePrompt | String | Yes | Input\Prompt for Name When Entering New Event | If yes then prompt for the name when entering a new event |
| `CalcMethod` | ScalingCalcMethod | String | Yes | Input\Scaling Calculation Method | Set to either Substation or Interpolate to indiciate if scaling and hotspot analysis should be approximated by taking values at the terminal substation, or if values should be interpolated along the line path |
| `GICSegLengthKM` | SegmentLengthKM | Real | Yes | Segment Length in km | To model nonuniform fields, the lines are divided into segments and the field is evaluated for each segment. This field gives the maximum segment length in km. |
| `GICSegLengthMile` | SegmentLengthMile | Real | Yes | Segment Length in Miles | To model nonuniform fields, the lines are divided into segments and the field is evaluated for each segment. This field gives the maximum segment length in miles. |
| `GICETTMOutputFile` | ETTMOutputFile | String | Yes | Spatially Uniform Options\ETTM Output File Name | Specify the name of the file for saving the ETTM data from the spatially uniform results. |
| `GICSaveETTMFile` | SaveETTMFile | String | Yes | Spatially Uniform Options\Save ETTM File | When saving the spatially uniform results, also save the EPRI Thermal Transformer Model GIC signature for a single transformer in text format. The Tables and Results must be filtered to show a single transformer for an ETTM file to be saved for that transformer with the results. |
| `GICSaveOutputFile` | SaveOutputFile | String | Yes | Spatially Uniform Options\Save Output File | Specify the name of the file for saving the spatially uniform time-varying results. |
| `GICTimeVarInputFile` | TimeVarInputFile | String | Yes | Spatially Uniform Options\Time-Varying Input File | Specify the name of an input file containing the spatially uniform time-varying E-field input data. |
| `GICUpdateLineVolts` | UpdateLineVoltages | String | Yes | Update Line DC Voltages | If true the line dc voltages are automatically udpated during the GIC solution; this is the normal choice; only set it false if the line dc voltages are explicitly entered, such as loading a *.GIC file |


---

# ==== powerworld-study-commands.md ====

---
type: reference
domain: tooling
topic: scripting
aliases: [powerworld-study-commands, study-commands, script-commands-by-study, aux-commands, solvepowerflow-parameters, ctgsolveall-parameters, aux-option-syntax]
tags: [powerworld, aux, script, commands, contingency, opf, reference]
---

# Reference: SCRIPT commands that run and control each study, with every parameter

## Abstract

Every aux SCRIPT command that runs or configures a PowerWorld study, grouped by study area, with
each parameter's meaning and default, how options are written in aux, and 29 silent behaviours.
Read "Surprises" before automating a study. Option-object fields live on [powerworld-option-objects-v25](powerworld-option-objects-v25.md).

## Connections

- **Up:** [Home](../index.md)
- **Hub:** [powerworld-study-options](powerworld-study-options.md) (which option to change per study, provenance-tagged)
- **Across:** [powerworld-option-objects-v25](powerworld-option-objects-v25.md) (the option fields these commands read) · [aux-script-commands](aux-script-commands.md) (the task-organised command index) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (parallel contingencies without PowerWorld's distributed add-on)

## Content

Source: PowerWorld, *Auxiliary File Format for Simulator 24*, last updated 2026-09-01 (PowerWorld publishes it with Simulator; page numbers refer to that PDF).
Extracted 2026-09-28. Every syntax line, parameter and default is cited to its PDF page, and five of the
highest-stakes claims (SetData's filter rule, ResetToFlatStart's setpoint reset, LODF's missing AC
method, CTGSolveAll clearing skipped results, the three-level solution-option precedence) were
re-read against the text. **Version skew:** this document is for Simulator 24 while the field
export is Simulator 25 — command syntax comes from here, field names from the export.

Where the document is silent or contradicts itself the tables say so. Nothing here is inferred.

General statement grammar (p.16): `Keyword(arg1, arg2, ...);` Lists go in `[ ]`. Statements end with `;`,
may span lines, and several can share a line. Omitted optional arguments are left blank between commas,
e.g. `CalculateLODF([BRANCH 1 2 1], DC, );` (p.79). YES/NO flags are bare words. Strings go in **straight**
double quotes; smart quotes fail (p.15).

Object identifier formats used by many commands (e.g. p.79, p.84, pp.47-48):
`[BUS num]`, `[BUS "name_nomkv"]`, `[BUS "label"]`; `[BRANCH bus1 bus2 ckt]`, `[BRANCH "name_kv1" "name_kv2" ckt]`,
`[BRANCH "buslabel1" "buslabel2" ckt]`, `[BRANCH "label"]`; `[GEN bus id]`; `[AREA num|"name"|"label"]`,
`[ZONE ...]`, `[SUPERAREA "name"|"label"]`, `[INJECTIONGROUP "name"|"label"]`, `[INTERFACE "name"|"label"]`, `[SLACK]`.

---

### Filter syntax (applies to every command with a `filter` parameter)

| form | meaning | page |
|---|---|---|
| blank | "Unless otherwise specified, a blank filter will select all objects." Exceptions are listed per command below (SetData, EstimateVoltages, InterfaceCreate, SetSelectedFromNetworkCut). | p.16 |
| `"FilterName"` | Name of an advanced filter of the same object type, in double quotes. | p.16 |
| `"<Objecttype>filtername"` | Advanced filter belonging to a **different** object type, e.g. a bus filter applied to generators. | p.16 |
| `"<DEVICE>objecttype 'key1' 'key2' 'key3'"` | Device filter: select by relation to one specific object, e.g. `"<DEVICE>Bus 1"` (p.45), `"<Device>Area 2"` (p.43). | p.16 |
| `AREAZONE` | Only objects meeting the area/zone/owner filters. | p.16 |
| `SELECTED` | Only objects whose Selected field is YES. | p.16 |
| `ALL` | Accepted by many commands explicitly (SetData, ConditionVoltagePockets, InterfaceFlattenFilter, etc.). For SetData it is **required** to mean "all". | p.31, p.54 |
| `"Variablename Comparison Value1 Value2"` | Inline single-condition filter, no filter object needed (added Oct 5 2023 patch of v23). Examples: `"NomkV between 220 550"`, `"MW >= 50"`, `"AreaNumber = 1"`, `"Name contains 'Combined'"`, `"SubNumber IsBlank"`. | p.16, p.44, p.44, p.76 |
| Branch-traverse filters | `DeterminePathDistance`, `DetermineShortestPath`, `SetBusFieldFromClosest` take `All`, `Selected`, `Closed`, or a branch advanced-filter name. | p.74, p.76 |
| LODF-specific keywords | `CalculateLODFScreening` adds `CTG` (branches in any defined contingency) and `LIMITMONITOR` (branches meeting Limit Monitoring Settings); `SAME` in monitor filters means "same set as filterProcess". | p.81, p.81, p.80 |

Defining an advanced filter as DATA (p.189; condition operators p.188):
```
FILTER (objecttype, filtername, filtertype, prefilter)
{
BUS "a bus filter" "AND" "no"
   <SUBDATA CONDITION>
      BusNomVolt  >  100
      AreaNum   inrange  "1 - 5 , 7 , 90-95"
   </SUBDATA>
}
```
Condition operators: `between (><)`, `notbetween (~><)`, `equal (= ==)`, `notequal (<> ~=)`, `greaterthan (>)`, `lessthan (<)`,
`greaterthanorequal (>=)`, `lessthanorequal (<=)`, `about`, `notabout` (take a tolerance), `contains`, `notcontains`, `startswith`,
`notstartswith`, `inrange`, `notinrange`, `meets`, `notmeets`, `isblank`, `notisblank` (p.188). A condition line can be
`_UseAnotherFilter meets|notmeets <filtername>` (p.188). An optional trailing `ABS` (or legacy `1`) makes strings case-sensitive
and takes absolute values (p.188). The meaning of the `filtertype` and `prefilter` header fields is shown only by example
(`"AND"`/`"OR"`, `"no"`); the document does not define them.

Per-command filter exceptions:
- `SetData` with the filter omitted does **not** mean all objects. The key fields must then be in the field list and it updates one object (p.31, p.31).
- `EstimateVoltages` fails on a blank filter (p.58).
- `InterfaceCreate` requires a non-blank filter (p.45).
- `SetSelectedFromNetworkCut`: a blank Branch/Interface/DCLine filter selects **nothing**, and at least one of the three must be non-blank (p.77).
- `InjectionGroupRemoveDuplicates` and `InterfaceRemoveDuplicates` reject `SELECTED` and `AREAZONE` (p.44, p.46).
- `CTGProcessRemedialActionsAndDependencies` does not accept `AREAZONE` (p.95).
- `QVWriteCurves` ignores `AREAZONE` on QVCurve objects and returns all results (p.126).
- `CTGCreateContingentInterfaces` and `ATCCreateContingentInterfaces` take only an advanced-filter **name** (p.93, p.103).

### Special keywords and value tricks inside parameters

| item | syntax | page |
|---|---|---|
| File/text keywords | `@BUILDDATE @CASEFILENAME @CASEFILEPATH @CASENAME @DATE @DATETIME @TIME @VERSION`, plus `@MODELFIELD<objecttype 'key1' 'key2' variablename:digits:rod>` | p.17 |
| Prompt the user for a file | `"<PROMPT 'Caption' 'FileTypes' 'InitialDirectory' 'CancelAction'>"`. CancelAction is `Abort` (default) or `Continue`. Does **not** work under SimAuto. | p.17 |
| `ALL` in field lists | `SaveData`, `SaveDataWithExtra`, `SaveObjectFields`, `SendToExcel`: `ALL` in place of the field list returns all fields, and `Var:ALL` returns every location, e.g. `LinePTDFMult:ALL`, `MultBusTLRSens:ALL`. | p.18 |
| TS model params | `AllModelParams`, `AllModelParamsPriKey`, `AllModelParamsSecKey`, `AllModelParamsLabel` in Save* field lists | p.18 |
| Field-valued inputs | `"@var:loc:digits:dec"` or `"@concisename:loc:digits:dec"` reads a field of the same object | p.75 |
| Other object's field | `"&Objecttype 'keys' concisename:digits:dec"`, `"&ModelExpressionName:digits:dec"`, `"&Objecttype '@keyfield' field"`, `"&@field field2"`. Usable for key-field values in SetData/CreateData. Default is 7 decimals. | pp.160-161 |
| Field precision | `variablenamelegacy:location:digits:rod` or `concisename:digits:rod` in Save field lists | p.25 |
| Sort list | `[var1:+:0, var2:-:1]`: +/- ascending/descending (required); 0/1 = case-insensitive-no-abs / case-sensitive-or-abs (optional) | pp.25-26 |

---

#### Power flow solution and initialization

| command | syntax | parameters (meaning, allowed values, default) | page |
|---|---|---|---|
| SolvePowerFlow | `SolvePowerFlow(SolMethod, "filename1", "filename2", CreateIfNotFound1, CreateIfNotFound2);` | **SolMethod**: `RECTNEWT` (rectangular NR), `POLARNEWTON`, `GAUSSSEIDEL`, `FASTDEC`, `ROBUST` (robust solution process), `DC`. Default is RECTNEWT if the case is in AC mode and DC if it is in DC mode. **DC switches the case into DC mode, and any AC method switches it back to AC.** The doc warns an AC solve can be hard after the case has been in DC. **filename1**: aux loaded on success, or `STOP` to halt all aux execution; default "". **filename2**: aux loaded on failure, or `STOP`; default "". **CreateIfNotFound1/2**: default NO with a legacy header, YES with a concise header, and only enforced when the legacy header says PROMPT (otherwise YES). | pp.60-61 |
| ResetToFlatStart | `ResetToFlatStart(FlatVoltagesAngles, ShuntsToMax, LTCsToMiddle, PSAnglesToMiddle);` | **FlatVoltagesAngles** YES/NO, default YES: sets all \|V\| **and generator setpoint voltages** to 1.0 pu and angles to 0. **ShuntsToMax** default NO: moves switched shunts half-way to max Mvar. **LTCsToMiddle** default NO. **PSAnglesToMiddle** default NO. | p.59 |
| ClearPowerFlowSolutionAidValues | `ClearPowerFlowSolutionAidValues;` | None. Clears the internal branch-status and generator-MW-estimate memory that drives angle smoothing and generator MW estimation before a solve, so Simulator does not alter initial V/angle or generator MW. | p.54 |
| ConditionVoltagePockets | `ConditionVoltagePockets(VoltageThreshold, AngleThreshold, filter);` | **VoltageThreshold**: pu \|ΔV\| across a branch. **AngleThreshold**: degrees \|Δθ\|. **filter** (branches): optional, omitted means all; accepts ALL/SELECTED/AREAZONE/"name". Re-estimates voltages inside pockets bounded by such branches. | p.54 |
| EstimateVoltages | `EstimateVoltages(filter);` | **filter** (buses): required, and blank is an error. Estimates V/angle at buses meeting the filter from the surrounding buses that do not. | p.58 |
| VoltageConditioning | `VoltageConditioning;` | None. Uses Voltage Conditioning tool options and case voltage targets. | p.63 |
| UpdateIslandsAndBusStatus | `UpdateIslandsAndBusStatus;` | None. Refreshes islands and bus energization without solving. This is done automatically at the start of each solve. | p.61 |
| ZeroOutMismatches | `ZeroOutMismatches(ObjectType);` | **ObjectType**: `BUSSHUNT` (default) adjusts bus shunt fields, `LOAD` adds loads with ID `Q1` (incremented if taken). Applies at buses whose mismatch exceeds the MVA tolerance. | p.61 |
| InitializeGenMvarLimits | `InitializeGenMvarLimits;` | None. Re-marks generators as at/not-at Mvar limits. | p.43 |
| GenForceLDC_RCC | `GenForceLDC_RCC(filter);` | **filter** (gens): default all. Sets the gen setpoint to the present LDC/RCC-point voltage. If \|Z\| ≤ 2e-6·MVAbase the gen regulates its terminal bus instead. | p.59 |
| InterfacesCalculatePostCTGMWFlows | `InterfacesCalculatePostCTGMWFlows;` | None. Updates contingent-interface flows per the *Monitor/Enforce Contingent Interface Elements* option. Does nothing if that option is "Never". | p.59 |
| DoCTGAction | `DoCTGAction([action]);` or `DoCTGAction("action");` | One CTGElement-format action string (see "Contingency action strings" below). COMPENSATION sections are not allowed. Example `DoCTGAction([BRANCH One_138.0 Two_138.0 1 OPEN]);` | p.58 |
| RotateBusAnglesInIsland | `RotateBusAnglesInIsland([BUS key], Value);` | Shifts all angles in the bus's island so that the bus sits at **Value** degrees. | p.49 |
| SetScheduledVoltageForABus | `SetScheduledVoltageForABus([bus identifier], voltage);` | Sets the EPC vsched. **Also sets the setpoints of gens and switched shunts regulating the bus**, and re-centres the shunt band as vband=(VHigh-VLow)/2. The BUS prefix and brackets are optional. | pp.50-51 |
| SaveJacobian | `SaveJacobian("JacFile", "JIDFile", FileType, JacForm);` | **FileType**: `M` (Matlab), `TXT`, `EXPM` (Matlab, exponential). **JacForm**: `R` (AC rectangular), `P` (AC polar), `DC` (B'). | p.60 |
| SaveYbusInMatlabFormat | `SaveYbusInMatlabFormat("filename", IncludeVoltages);` | **IncludeVoltages** YES/NO | p.60 |
| SaveGenLimitStatusAction | `SaveGenLimitStatusAction("filename");` | Text dump of gen Mvar, limits and AVR flags | p.59 |
| StoreState | `StoreState(StateName);` | **StateName** optional. Blank stores the one unnamed state, and a unique name stores one of several. | p.63 |
| RestoreState | `RestoreState(WhichState, StateName);` | **WhichState**: `USER` (default; from StoreState), `BEFOREFAILED` (auto-stored before each solve and **removed once any later solve succeeds**), `LASTSUCCESSFUL` (auto-stored after each successful solve). **StateName** is used only with USER; blank means the unnamed state. **Fails if the state was not set.** | pp.62-63 |
| DeleteState | `DeleteState(WhichState, StateName);` | Same options as RestoreState. Fails if the state was not set. | p.62 |

Note: `SaveState`/`LoadState` **do not exist** in this document. The state commands are `StoreState`/`RestoreState`/`DeleteState` (TOC p.4).

#### Difference case (base vs present)

| command | syntax | parameters | page |
|---|---|---|---|
| DiffCaseSetAsBase | `DiffCaseSetAsBase;` | Present case becomes the diff base. Old name `DiffFlowSetAsBase` is still read. | p.55 |
| DiffCaseClearBase | `DiffCaseClearBase;` | Old name DiffFlowClearBase | p.54 |
| DiffCaseKeyType | `DiffCaseKeyType(KeyType);` | Only the first letter counts: `P`=PRIMARY, `S`=SECONDARY, `L`=LABEL | pp.54-55 |
| DiffCaseMode | `DiffCaseMode(diffmode);` | First letter: `P` PRESENT, `B` BASE, `D` DIFFERENCE, `C` CHANGE | p.55 |
| DiffCaseShowPresentAndBase | `DiffCaseShowPresentAndBase(How);` | YES/NO toggles "Show Present\|Base in Difference and Change Mode" | p.55 |
| DiffCaseRefresh | `DiffCaseRefresh;` | Re-link base and present. Run it before saving added/removed objects after topology edits. | p.55 |
| DiffCaseWriteCompleteModel | `DiffCaseWriteCompleteModel("filename", AppendFile, SaveAdded, SaveRemoved, SaveBoth, KeyFields, "ExportFormat", UseAreaZone, UseDataMaintainer, AssumeBaseMeet, IncludeClearPowerFlowSolutionAidValues, DeleteBranchesThatFlipBusOrder);` | AppendFile, SaveAdded, SaveRemoved, SaveBoth: YES/NO, required. **KeyFields**: Primary (default) or Secondary. **ExportFormat**: default blank. **UseAreaZone**: default NO. **UseDataMaintainer**: default NO. **AssumeBaseMeet**: default YES. **IncludeClearPowerFlowSolutionAidValues**: default YES, which writes that command into the aux. **DeleteBranchesThatFlipBusOrder**: default NO (always done for transformers). | pp.55-56 |
| DiffCaseWriteNewEPC / DiffCaseWriteRemovedEPC | `(..."filename", GEFileType, UseAreaZone, BaseAreaZoneMeetFilter, Append, UseDataMaintainer);` | **GEFileType**: GE14-GE23, default latest. **UseAreaZone**: default NO. **BaseAreaZoneMeetFilter**: default NO. **Append**: default YES. **UseDataMaintainer**: default NO (added Oct 30 2025). | pp.57-58 |
| DiffCaseWriteBothEPC | `DiffCaseWriteBothEPC("filename", GEFileType, UseAreaZone, BaseAreaZoneMeetFilter, Append, "ExportFormat", UseDataMaintainer);` | Same parameters as above plus **ExportFormat** (default blank), which chooses the change-detection fields | p.57 |

#### Contingency analysis

| command | syntax | parameters (meaning, allowed values, default) | page |
|---|---|---|---|
| CTGSolveAll | `CTGSolveAll(DoDistributed, ClearAllResults);` | **DoDistributed**: default NO (needs the distributed add-on). **ClearAllResults**: default **YES**, which clears all results **including those of skipped contingencies**. NO clears only the non-skipped ones. Solves every contingency not marked Skip. | pp.97-98 |
| CTGSolve | `CTGSolve("ContingencyName");` | Solves one contingency. **Leaves the system in the post-contingency state.** | p.97 |
| CTGApply | `CTGApply("ContingencyName");` | Applies the actions **without** solving the power flow | p.90 |
| CTGSetAsReference | `CTGSetAsReference;` | Present state becomes the CTG reference | p.97 |
| CTGRestoreReference | `CTGRestoreReference;` | Resets the system to the CTG reference state | p.96 |
| CTGAutoInsert | `CTGAutoInsert;` | **No parameters.** Set every option in `Ctg_AutoInsert_Options` beforehand (SetData or DATA). | p.90 |
| CTGPrimaryAutoInsert | `CTGPrimaryAutoInsert;` | No parameters. Also driven by `Ctg_AutoInsert_Options`. | p.95 |
| CTGClearAllResults | `CTGClearAllResults;` | Deletes all violations and comparison results | p.90 |
| CTGSkipWithIdenticalActions | `CTGSkipWithIdenticalActions;` | Added Nov 6 2025 (v24). For each identical-action group, the alphabetically first CTG keeps Skip=NO and the rest get Skip=YES. Only processes CTGs that start with Skip=NO. | p.97 |
| CTGDeleteWithIdenticalActions | `CTGDeleteWithIdenticalActions;` | Deletes duplicates and keeps the alphabetically first one | p.95 |
| CTGSort | `CTGSort([SortFieldList]);` | Default sorts alphabetically by name. Uses the sort-list format. CTGs are **processed in internal storage order (creation order)**, not sorted. | p.98 |
| CTGProduceReport | `CTGProduceReport("filename");` | Text report using CTG_Options settings | p.95 |
| CTGWriteResultsAndOptions | `CTGWriteResultsAndOptions("filename", [opt1..opt22], KeyField, UseDATASection, UseConcise, UseObjectIDs, UseSelectedDataMaintainers, SaveDependencies, UseAreaZoneFilters);` | Option list (YES/NO, default in parentheses): 1 unlinked actions (NO); 2 CTG options (YES); 3 limit monitoring (NO); 4 general PF solution options (YES); 5 list display settings (NO); 6 CTG results (YES); 7 inactive violations (YES); 8 interfaces (NO); 9 injection groups (NO); 10 distributed options (YES); 11 suppress gen/load options (NO); 12 CTG definitions (YES); 13 RAS and global actions (YES); 14 custom monitors (YES); 15 model conditions/filters/expressions (YES); 16 advanced filters used by them (YES); 17 limit cost functions (YES); 18 auto-convert CTG blocks/global actions (NO); 19 voltage control groups (YES); 20 primary CTG options (NO); 21 primary CTGs (NO); 22 combo results (NO). **KeyField**: PRIMARY (default), SECONDARY, or LABEL. **UseDATASection**: default NO; YES writes SUBDATA content as DATA (e.g. ContingencyElement). **UseConcise**: named in the signature but **not documented** (see Surprises). **UseObjectIDs**: default NO; also YES, YES_MS, YES_3W, YES_MS_3W. **UseSelectedDataMaintainers**, **SaveDependencies**, **UseAreaZoneFilters**: default NO. | pp.100-101 |
| CTGWriteAllOptions | `CTGWriteAllOptions("filename", KeyField, UseSelectedDataMaintainer, SaveDependencies, UseAreaZoneFilters);` | Concise names, DATA not SUBDATA. KeyField default PRIMARY and the rest default NO. Equivalent to opts `NO,YES,YES,YES,NO,NO,NO,YES,YES,NO,NO,YES,YES,YES,YES,YES,NO,YES,YES,NO,NO,NO` with UseObjectIDs=YES_MS_3W. It **omits results** (opt6=NO). | pp.98-99 |
| CTGWriteAuxUsingOptions | `CTGWriteAuxUsingOptions("filename", Append);` | Contents come from the `CTGWriteAux_Options` object. **Append**: default YES. Added Aug 18 2023. | p.99 |
| CTGSaveViolationMatrices | `CTGSaveViolationMatrices("filename", filetype, UsePercentage, [ObjectTypesToReport], SaveContingency, SaveObjects, FieldListObjectType, [FieldList], IncludeUnsolvableCTGs);` | **filetype**: CSVNOHEADER or CSVCOLHEADER. **UsePercentage** YES/NO. **ObjectTypes**: BRANCH, BUS, INTERFACE, CUSTOMMONITOR. **SaveContingency** YES/NO (rows=CTGs). **SaveObjects** YES/NO (one file per type, rows=objects). **FieldListObjectType**: default blank; BRANCH, BUS, INTERFACE, CUSTOMMONITOR, or CONTINGENCY. **FieldList**: default blank. **IncludeUnsolvableCTGs**: default NO. Files are named `filename_<objecttype>`. | pp.96-97 |
| CTGCalculateOTDF | `CTGCalculateOTDF([seller], [buyer], LinearMethod);` | Runs CalculatePTDF, then OTDFs for every CTG/violation pair. LinearMethod as in CalculatePTDF. | p.90 |
| CTGComboSolveAll | `CTGComboSolveAll(DoDistributed, ClearAllResults);` | Combo analysis of primary × regular CTGs not skipped. DoDistributed default NO. ClearAllResults default YES (clears even skipped primaries). | p.91 |
| CTGComboDeleteAllResults | `CTGComboDeleteAllResults;` | Clears combo violations, what-occurred, summaries, injection sensitivities | p.91 |
| CTGConvertToPrimaryCTG | `CTGConvertToPrimaryCTG(filter, KeepOriginal, "Prefix", "Suffix");` | filter default all. KeepOriginal default YES. Prefix default blank. Suffix default `"-Primary"`. Unsupported actions are logged, not converted. | p.93 |
| CTGJoinActiveCTGs | `CTGJoinActiveCTGs(InsertSolvePowerFlow, DeleteExisting, JoinWithSelf, "filename");` | All YES/NO. Skip=YES CTGs are excluded. filename is not needed if JoinWithSelf=YES. Order follows internal storage (see CTGSort). | p.95 |
| CTGCloneMany | `CTGCloneMany(filter, "Prefix", "Suffix", SetSelected);` | filter default all. Prefix/Suffix default blank; with both blank the name gets `"- Copy"`. SetSelected default NO. | p.90 |
| CTGCloneOne | `CTGCloneOne("ctgname", "newctgname", "Prefix", "Suffix", SetSelected);` | newctgname may use `@CTGName`. Prefix/Suffix are used only when newctgname is blank. SetSelected default NO. | p.91 |
| CTGCreateContingentInterfaces | `CTGCreateContingentInterfaces(filter, maxOption);` | **filter**: advanced-filter name on ViolationCTG. **maxOption**: BRANCH, CTG, BRANCHCTG, or blank (all) | p.93 |
| CTGCreateStuckBreakerCTGs | `CTGCreateStuckBreakerCTGs(filter, AllowDuplicates, "PrefixName", IncludeCTGLabel, BranchFieldName, "SuffixName", "PrefixComment", BranchFieldComment, "SuffixComment");` | All optional. AllowDuplicates NO; IncludeCTGLabel YES; SuffixName `"STK"`; the rest blank | p.94 |
| CTGCreateExpandedBreakerCTGs | `CTGCreateExpandedBreakerCTGs;` | Permanently converts Open/Close-with-breakers actions to explicit breaker actions | p.93 |
| CTGConvertAllToDeviceCTG | `CTGConvertAllToDeviceCTG(KeepOriginalIfEmpty);` | Full-topology → planning-device CTGs. Default NO. | p.92 |
| CTGProcessRemedialActionsAndDependencies | `CTGProcessRemedialActionsAndDependencies(DoDelete, filter);` | DoDelete YES=delete, NO=mark Selected. filter default blank (all); AREAZONE is invalid | p.95 |
| CTGReadFilePTI / CTGReadFilePSLF | `CTGReadFilePTI("file.con");` / `CTGReadFilePSLF("file.otg");` | Import CTGs | p.96 |
| CTGWriteFilePTI | `CTGWriteFilePTI("filename", BusFormat, TruncateCTGLabels, "filtername", Append);` | **BusFormat**: Number, Name8, or Name12. **Truncate** YES/NO (12 chars). **filter**: default blank (all). **Append**: default **NO** | pp.99-100 |
| CTGCompareTwoListsofContingencyResults | `CTGCompareTwoListsofContingencyResults(PRESENT or "ControllingFile", PRESENT or "ComparisonFile");` | Files may be .aux, .ctg, .con, .thr/.dat, .otg | p.92 |
| CTGRelinkUnlinkedElements | `CTGRelinkUnlinkedElements;` | — | p.96 |
| CTGVerifyIteratedLinearActions | `CTGVerifyIteratedLinearActions("filename");` | Validation text for the "Iterate on Action Status" linear option | p.98 |
| InterfaceAddElementsFromContingency | `InterfaceAddElementsFromContingency(InterfaceName, ContingencyName);` | Creates the interface if missing and adds the CTG elements as contingent elements | pp.44-45 |

**Contingency action strings** (used in the CTGElement SUBDATA, DoCTGAction, RemedialAction, GlobalContingencyActions, PostPowerFlowActions): each line is
`"Action" "ModelCriteria" Status TimeDelay Persistent ... //comment`. Status is CHECK (default), ALWAYS, NEVER, TOPOLOGYCHECK, POSTCHECK, or SOLUTIONFAIL (pp.170-171).
Action examples: `BRANCH b1 b2 ckt OPEN|CLOSE|OPENCBS|CLOSECBS|SET_TO value LimitMVA REF` (p.172);
`GEN|LOAD|SHUNT bus id OPEN|CLOSE|OPENCBS|CLOSECBS` (p.172); `AREA a SET_TO 'OFF'|'PARTFAC'|'AREASLACK bus'|'IGSLACK ig'` (p.180);
`SUBSTATION s OPEN|OPENCBS|SET_P_TO|CHANGE_P_BY` (pp.180-181); `ABORT` (p.181); `SOLVEPOWERFLOW` splits the actions into groups (p.181);
`CONTINGENCYBLOCK name` (p.181); `COMPENSATION ... END` (p.181). Values can be `<Field>var` or `<Expression>name`, with `REF` meaning evaluate in the reference case (pp.171-172).
RemedialAction and GlobalContingencyActions disallow SOLVEPOWERFLOW (p.191, p.206). PostPowerFlowActions disallows ABORT, CONTINGENCYBLOCK and SOLVEPOWERFLOW (p.202).

#### OPF and SCOPF

| command | syntax | parameters | page |
|---|---|---|---|
| SolvePrimalLP | `SolvePrimalLP("filename1", "filename2", CreateIfNotFound1, CreateIfNotFound2);` | filename1: aux on success or `STOP`. filename2: aux on failure or `STOP`. Both default "". CreateIfNotFound works as in SolvePowerFlow. Iterates PF ↔ LP until converged. | p.118 |
| InitializePrimalLP | `InitializePrimalLP("filename1", "filename2", CreateIfNotFound1, CreateIfNotFound2);` | Clears all previous primal-LP structures and results. Same parameters. | pp.118-119 |
| SolveSinglePrimalLPOuterLoop | `SolveSinglePrimalLPOuterLoop("filename1", "filename2", CreateIfNotFound1, CreateIfNotFound2);` | Same parameters. Runs one LP, then one PF, then stops. | p.119 |
| SolveFullSCOPF | `SolveFullSCOPF(BCMethod, "filename1", "filename2", CreateIfNotFound1, CreateIfNotFound2);` | **BCMethod**: `POWERFLOW` (default) or `OPF` for the base case. The rest as above. | pp.119-120 |
| OPFWriteResultsAndOptions | `OPFWriteResultsAndOptions("filename");` | Writes limit monitoring and area/bus/branch/interface/gen/superarea OPF options plus OPF solution options | p.120 |

All OPF tuning lives in option objects set with SetData/DATA. No command parameter exposes it.

#### Sensitivities (PTDF, LODF, shift factors, voltage, loss)

| command | syntax | parameters | page |
|---|---|---|---|
| CalculatePTDF | `CalculatePTDF([seller], [buyer], LinearMethod);` | Transactors: AREA, ZONE, SUPERAREA, INJECTIONGROUP, BUS, or SLACK (seller ≠ buyer). **LinearMethod**: AC (with losses), DC (lossless), DCPS (DC with phase shifters). Default lossless DC. | p.84 |
| CalculatePTDFMultipleDirections | `CalculatePTDFMultipleDirections(StoreForBranches, StoreForInterfaces, LinearMethod);` | YES/NO, YES/NO, AC/DC/DCPS (default DC). Covers all defined directions (example: those with Include=YES). | p.84 |
| CalculateLODF | `CalculateLODF([BRANCH b1 b2 ckt], LinearMethod, PostClosureLCDF);` | Closed branch gives LODF, open branch gives LCDF. **LinearMethod**: DC or DCPS; **AC is not allowed**; default lossless DC. **PostClosureLCDF**: default YES (LCDF). NO gives MLCDF from pre-closure V/θ. | p.79 |
| CalculateLODFMatrix | `CalculateLODFMatrix(WhichOnes, filterProcess, filterMonitor, MonitorOnlyClosed, LinearMethod, filterMonitorInterface, PostClosureLCDF);` | **WhichOnes**: OUTAGES or CLOSURES. **filterProcess**: ALL, SELECTED, AREAZONE, or name. **filterMonitor**: the same plus SAME. **MonitorOnlyClosed** YES/NO. **LinearMethod**: DC (default) or DCPS. **filterMonitorInterface**: default none; adds interface member lines. **PostClosureLCDF**: default YES. | pp.80-81 |
| CalculateLODFAdvanced | `CalculateLODFAdvanced(IncludePhaseShifters, FileType, MaxColumns, MinLODF, NumberFormat, DecimalPoints, OnlyIncludingLinesIncreasing, "FileName", IncludeIslandingCTG);` | FileType PROMOD or MATRIX. NumberFormat EXPONENTIAL or DECIMAL. **IncludeIslandingCTG**: default YES; islanding CTGs are reported as a very large number, and NO omits them. | pp.79-80 |
| CalculateLODFScreening | `CalculateLODFScreening(filterProcess, filterMonitor, IncludePhaseShifters, IncludeOpenLines, UseLODFThreshold, LODFThreshold, UseOverloadThreshold, OverloadLow, OverloadHigh, DoSaveFile, FileLocation, CustomFieldHighLODF, CustomFieldHighLODFLine, CustomFieldHighOverload, CustomFieldHighOverloadLine, DoUseCTGName, CustomFieldOrigCTGName);` | filterProcess: ALL, AREAZONE, CTG, LIMITMONITOR, SELECTED, or name. filterMonitor: the same without CTG, plus SAME. Overload thresholds are in %. FileLocation is a directory and Simulator names the file. CustomField* are integer indices, default 0. DoUseCTGName default NO. It pairs significant single outages into new double CTGs. | pp.81-83 |
| CalculateShiftFactors | `CalculateShiftFactors([flow element], direction, [transactor], LinearMethod, SetOutOfServiceBuses, filter, AbortOnError, BranchDistMeas);` | **Old name `CalculateTLR` is still accepted.** flow element: INTERFACE or BRANCH. **direction**: BUYER or SELLER. **LinearMethod**: AC, DC (default), or DCPS. **SetOutOfServiceBuses**: default NO. **filter**: default all buses (used only with SetOOS). **AbortOnError**: default **YES**, which terminates the rest of the aux on failure. **BranchDistMeas**: default blank (node count); X, Z, Length, Nodes, FixedNumBus, SuperBus, or a branch field. Other options are in `TLR_Options`. | pp.84-86 |
| CalculateShiftFactorsMultipleElement | `CalculateShiftFactorsMultipleElement(TypeElement, WhichElement, direction, [transactor], LinearMethod);` | Old name CalculateTLRMultipleElement. **TypeElement**: INTERFACE, BRANCH, or BOTH. **WhichElement**: SELECTED, OVERLOAD (normal rating), or CTGOVERLOAD (needs a prior CTG run). LinearMethod default DC. | p.86 |
| CalculateFlowSense | `CalculateFlowSense([flow element], FlowType);` | FlowType MW, MVAR, or MVA. Injection at each bus, withdrawn at slack. | p.79 |
| CalculateVoltSense | `CalculateVoltSense([BUS num]);` | Sensitivity of one bus's V to P/Q injections at all buses (slack-referenced) | p.87 |
| CalculateVoltSelfSense | `CalculateVoltSelfSense(filter);` | Default all buses | p.87 |
| CalculateVoltToTransferSense | `CalculateVoltToTransferSense([seller], [buyer], TransferType, TurnOffAVR);` | **TransferType**: P, Q, or PQ. **TurnOffAVR** YES/NO for participating gens | p.87 |
| CalculateTapSense | `CalculateTapSense(filter);` | Added Jun 4 2025. Forces dV/dtap to be current. filter: default all transformers; ALL or name | pp.86-87 |
| CalculateLossSense | `CalculateLossSense(FunctionType, AreaSALossReference, IslandLossReference);` | **FunctionType**: NONE, ISLAND, AREA, AREASA, or SELECTED. **AreaSALossReference**: default NO (AREA/AREASA only). **IslandLossReference**: default EXISTING; LOADS or "InjGroupName" | p.83 |
| SetSensitivitiesAtOutOfServiceToClosest | `SetSensitivitiesAtOutOfServiceToClosest(filter, BranchDistMeas);` | Copies P/Q sensitivities to OOS buses. filter default all. BranchDistMeas as above | p.89 |
| LineLoadingReplicatorCalculate | `LineLoadingReplicatorCalculate([Flow Element], [Injection Group(s)], AGCOnly, DesiredFlow, Implement, LinearMethod, UseLoadMinMax, MaxMultiplier, MinMultiplier);` | IG list `["IG1","IG2"]`. AGCOnly and Implement are YES/NO. LinearMethod DC or DCPS. UseLoadMinMax default YES. Max/MinMultiplier default 1.0 (required when UseLoadMinMax=NO) | p.88 |
| LineLoadingReplicatorImplement | `LineLoadingReplicatorImplement;` | Applies the stored injection change list | p.89 |

#### ATC / transfer capability

| command | syntax | parameters | page |
|---|---|---|---|
| ATCDetermine | `ATCDetermine([seller], [buyer], DoDistributed, DoMultipleScenarios);` | Transactors as in PTDF. DoDistributed default NO. **DoMultipleScenarios default YES if scenarios are defined.** Other settings are in `ATC_Options`. | p.103 |
| ATCDetermineMultipleDirections | `ATCDetermineMultipleDirections(DoDistributed, DoMultipleScenarios);` | Both default **NO** (note the different default from ATCDetermine) | p.104 |
| ATCDetermineATCFor | `ATCDetermineATCFor(RL, G, I, ApplyTransfer);` | Scenario indices (0-based). ApplyTransfer default NO; YES leaves the case at the found transfer level (the CTG is not applied under IL-then-full) | p.104 |
| ATCDetermineMultipleDirectionsATCFor | `ATCDetermineMultipleDirectionsATCFor(RL, G, I);` | — | p.104 |
| ATCIncreaseTransferBy | `ATCIncreaseTransferBy(amount);` | MW | p.104 |
| ATCSetAsReference / ATCRestoreInitialState | `ATCSetAsReference;` / `ATCRestoreInitialState;` | — | p.104 |
| ATCTakeMeToScenario | `ATCTakeMeToScenario(RL, G, I);` | All three required, 0-based integers | p.104 |
| ATCDeleteAllResults | `ATCDeleteAllResults;` | Removes TransferLimiter, ATCExtraMonitor, ATCFlowValue | p.103 |
| ATCDeleteScenarioChangeIndexRange | `ATCDeleteScenarioChangeIndexRange(RL\|G\|I, [0-2, 5, 7-9]);` | 0-based index ranges | p.103 |
| ATCCreateContingentInterfaces | `ATCCreateContingentInterfaces(filter);` | Advanced-filter name on TransferLimiter. Default blank (all) | p.103 |
| ATCDataWriteOptionsAndResults | `ATCDataWriteOptionsAndResults("filename", AppendFile, KeyField);` | Replaces `ATCWriteAllOptions` (renamed Dec 2021). AppendFile default YES. KeyField default PRIMARY. Concise, DATA sections | pp.104-105 |
| ATCWriteResultsAndOptions | `ATCWriteResultsAndOptions("filename", AppendFile);` | AppendFile default YES. Saves CTG/RAS definitions with dependencies | p.105 |
| ATCWriteScenarioLog | `ATCWriteScenarioLog("filename", AppendFile, filter);` | AppendFile default **NO**. No scenarios means no file and no error | p.105 |
| ATCWriteScenarioMinMax | `ATCWriteScenarioMinMax("filename", filetype, AppendFile, [fieldlist], Operation, OperationField, GroupScenario, [RLFilter], [GFilter], [IFilter], DirectionFilter, DoGroupDirection, filter, PreferIterativelyFound);` | Operation MIN, MAX, or MIN/MAX. OperationField TransferLimit or an ATC_ExtraMonitor field. GroupScenario None, RL, G, or I. R/G/I filters are integer ranges (ignored if filter is set). DirectionFilter IGNORE (default), ALL, or "name". DoGroupDirection default YES. PreferIterativelyFound default YES | pp.106-108 |
| ATCWriteToExcel / ATCWriteToText | `ATCWriteToExcel("sheet", [fieldlist]);` / `ATCWriteToText("filename", TAB\|CSV, [fieldlist]);` | Multiple-scenario only. **Omitting fieldlist can give blank output** if the TransferLimiter DataGrid was never initialized | pp.108-109 |

#### PV and QV curves

| command | syntax | parameters | page |
|---|---|---|---|
| PVSetSourceAndSink | `PVSetSourceAndSink([INJECTIONGROUP "src"], [INJECTIONGROUP "sink"]);` | Injection groups only | p.122 |
| PVRun | `PVRun([source], [sink]);` | Both optional (default is the already-set source/sink). IG only | pp.121-122 |
| PVClear / PVStartOver / PVDestroy | `PVClear;` `PVStartOver;` `PVDestroy;` | Clear results / restore the initial state, re-baseline and reset step / remove everything including the ability to restore the initial state | p.121, p.122, p.121 |
| PVWriteInadequateVoltages | `PVWriteInadequateVoltages("file.csv", AppendFile, InadequateType);` | AppendFile default YES. InadequateType LOW (default) or HIGH | p.122 |
| PVWriteResultsAndOptions / PVDataWriteOptionsAndResults | `(..."filename", AppendFile)` / `(..."filename", AppendFile, KeyField)` | AppendFile default YES. KeyField default PRIMARY | pp.122-123, p.121 |
| PVQVTrackSingleBusPerSuperBus | `PVQVTrackSingleBusPerSuperBus;` | Topology add-on. Monitors only the pnode per superbus | p.121 |
| RefineModel | `RefineModel(objecttype, filter, Action, Tolerance);` | objecttype AREA or ZONE. Action TRANSFORMERTAPS, SHUNTS, or OFFAVR. Fixes devices whose Vmax-Vmin (or Qmax-Qmin) ≤ Tolerance | p.123 |
| QVRun | `QVRun("filename", InErrorMakeBaseSolvable, DoDistributed);` | Runs on buses with QVSELECTED=YES. filename is optional (no CSV if omitted). InErrorMakeBaseSolvable default YES. DoDistributed default NO | p.124 |
| QVWriteCurves | `QVWriteCurves("file.csv", IncludeQuantitiesToTrack, filter, Append);` | Filter on QVCurve (AREAZONE ignored) | p.126 |
| QVDeleteAllResults | `QVDeleteAllResults;` | — | p.124 |
| QVSelectSingleBusPerSuperBus | `QVSelectSingleBusPerSuperBus;` | One monitored bus per pnode | p.124 |
| QVWriteResultsAndOptions / QVDataWriteOptionsAndResults | `(..."filename", AppendFile)` / `(..., AppendFile, KeyField)` | AppendFile default YES | p.126, p.124 |

The PV study name and `PVCreate` are legacy. The name is ignored, and PVCreate equals PVSetSourceAndSink (p.121).

#### Scaling, dispatch set-up, and study objects

| command | syntax | parameters | page |
|---|---|---|---|
| Scale | `Scale(scaletype, basedon, [parameters], scalemarker);` | **scaletype**: LOAD, GEN, INJECTIONGROUP, or BUSSHUNT. **basedon**: MW or FACTOR. **parameters**: LOAD/IG `[MW, MVAR]` or `[MW]` (MW only means constant pf); GEN `[MW]`; BUSSHUNT `[GMW, BCAPMVAR, BREAMVAR]`. Field names can replace numbers, and then scaling is **per object** instead of aggregate. **scalemarker**: BUS (default), AREA, ZONE, or OWNER; ignored for INJECTIONGROUP. Scaling acts on objects whose marker has **Scale=YES**, and more options are in `SCALE_OPTIONS`. | pp.39-40 |
| SetParticipationFactors | `SetParticipationFactors(Method, ConstantValue, Object);` | Method MAXMWRAT, RESERVE, or CONSTANT. ConstantValue (0 unless CONSTANT). Object `[Area ..]`, `[Zone ..]`, SYSTEM, AREAZONE, or DISPLAYFILTERS | p.50 |
| InjectionGroupCreate | `InjectionGroupCreate("Name", objecttype, InitialValue, filter, Append);` | objecttype GEN, LOAD, SHUNT, or BUS. InitialValue is a number or a keyword (PRESENT, MAX GEN INC, MAX GEN DEC, MAX GEN MW, LOAD MW, MAX SHUNT INC/DEC/MVAR, `<FIELD>var`, `<EXPRESSION>name`). Append default YES | pp.43-44 |
| InjectionGroupsAutoInsert | `InjectionGroupsAutoInsert;` | Options come from `IG_AutoInsert_Options` | p.43 |
| InjectionGroupRemoveDuplicates / RenameInjectionGroup | `(PreferenceFilter)` / `("Old", "New")` | — | p.44, p.49 |
| InterfaceCreate | `InterfaceCreate("Name", DeleteExisting, ObjectType, Filter);` | ObjectType BRANCH or INTERFACE. Filter required | p.45 |
| InterfacesAutoInsert | `InterfacesAutoInsert(Type, DeleteExisting, UseFilters, "Prefix", Limits);` | Type AREA or ZONE. Limits ZEROS, AUTO, or `[8 values]` | p.45 |
| InterfaceFlatten / InterfaceFlattenFilter / InterfaceModifyIsolatedElements / InterfaceRemoveDuplicates / SetInterfaceLimitToMonitoredElementLimitSum | see source | — | pp.45-46, p.51 |
| DirectionsAutoInsert | `DirectionsAutoInsert(Source, Sink, DeleteExisting, UseAreaZoneFilters);` | Source AREA, ZONE, or INJECTIONGROUP. Sink the same plus SLACK | p.42 |
| DirectionsAutoInsertReference | `DirectionsAutoInsertReference(SourceType, ReferenceObject, DeleteExisting, SourceFilterName, OppositeDirection);` | SourceType Area, Zone, InjectionGroup, or Bus. DeleteExisting default YES. OppositeDirection default NO | p.43 |
| BranchMVALimitReorder | `BranchMVALimitReorder(Filter, SetA, ..., SetO);` | Each Set is a letter (copy from that set), a number, or blank (keep) | p.41 |
| TemperatureLimitsBranchUpdate, WeatherLimitsGenUpdate | see Weather | | |
| AutoInsertTieLineTransactions | `AutoInsertTieLineTransactions;` | **Deletes all MW transactions**, zeroes unspecified interchange, then creates tie-flow transactions | p.41 |
| ChangeSystemMVABase | `ChangeSystemMVABase(NewBase);` | — | p.41 |
| SetGenPMaxFromReactiveCapabilityCurve | `SetGenPMaxFromReactiveCapabilityCurve(filter);` | — | p.50 |
| SuperAreaAddAreas / SuperAreaRemoveAreas | `("Name", Filter)` | — | pp.51-52 |

#### Island / topology / network-distance tools

| command | syntax | parameters | page |
|---|---|---|---|
| DetermineBranchesThatCreateIslands | `DetermineBranchesThatCreateIslands(Filter, StoreBuses, "filename", SetSelectedOnLines, FileType);` | Filter ALL, SELECTED, AREAZONE, or name. StoreBuses YES writes the islanded buses. **filename blank forces SetSelectedOnLines=YES**. SetSelectedOnLines YES **overwrites** Selected. FileType AUX (default) or CSV (one bus/branch pair per line) | p.73 |
| DeterminePathDistance | `DeterminePathDistance([start], BranchDistMeas, BranchFilter, BusField);` | start is Bus, Area, Zone, SuperArea, Substation, or InjectionGroup. BranchDistMeas X, Z, Length, Nodes, FixedNumBus, SuperBus, or a branch field. BranchFilter All, Selected, Closed, or name. BusField receives the distance (0 in the start group, **-1 if unreachable**) | pp.73-74 |
| DetermineShortestPath | `DetermineShortestPath([start], [end], BranchDistanceMeasure, BranchFilter, "Filename");` | Output lines are "Number DistanceMeasure Name", listed end → start | pp.74-75 |
| FindRadialBusPaths | `FindRadialBusPaths(IgnoreStatus, TreatParallelAsNotRadial, BusOrSuperBus);` | NO, NO, BUS defaults. Fills Radial Path End Number, Index and Length | p.75 |
| SetSelectedFromNetworkCut | `SetSelectedFromNetworkCut(SetHow, [BusOnCutSide], BranchFilter, InterfaceFilter, DCLineFilter, Energized, NumTiers, InitializeSelected, [ObjectsToSelect], UseAreaZone, UsekV, MinkV, MaxkV, LowerMinkV, LowerMaxkV);` | ObjectsToSelect BRANCH, BUS, DCTRANSMISSIONLINE, GEN, LOAD, or SHUNT. UseAreaZone/UsekV default NO. MinkV 0, MaxkV 9999, LowerMinkV 0, LowerMaxkV 9999 | pp.77-78 |
| SetBusFieldFromClosest | `SetBusFieldFromClosest(variablename, BusFilterSetTo, BusFilterFromThese, BranchFilterTraverse, BranchDistMeas);` | Added Jan 15 2025 | p.76 |
| DoFacilityAnalysis | `DoFacilityAnalysis("Filename", SetSelected);` | Min-cut. Options come from the dialog/objects set beforehand. SetSelected default NO | p.75 |
| CreateNewAreasFromIslands | `CreateNewAreasFromIslands;` | — | p.73 |
| ClearSmallIslands | `ClearSmallIslands;` | Keeps the island with the most buses. Others are de-energized by **opening their generators** | p.42 |
| ITP: CloseWithBreakers | `CloseWithBreakers(objecttype, filter or [id], OnlyEnergizeSpecifiedObjects, [SwitchingDeviceTypes], CloseNormallyClosedDisconnects);` | Only NO default; types default `"Breaker"` (also "Load Break Disconnect"); last default NO | pp.114-115 |
| ITP: OpenWithBreakers | `OpenWithBreakers(objecttype, filter or [id], [SwitchingDeviceTypes], OpenNormallyOpenDisconnects);` | Types default "Breaker". Last default NO | pp.116-117 |
| ITP: ExpandBusTopology / ExpandAllBusTopology | `ExpandBusTopology(BUS n, TopologyType);` / `ExpandAllBusTopology;` | DOUBLEBUSDOUBLEBREAKER, MAINTRANSFER, RINGBUS, BREAKERANDAHALF, SINGLEBUS, or SECTIONALIZEBUS. The "All" form reads Custom String 5 | p.115 |
| ITP: SaveConsolidatedCase | `SaveConsolidatedCase("filename", filetype, [BusFormat, TruncateCtgLabels, AddCommentsForObjectLabels]);` | filetype PWB, PWBx, PTI23-35, or GE14-23 | p.117 |

Network edits relevant to studies (syntax at source): TapTransmissionLine (pp.52-53), SplitBus (p.51, InsertBusTieLine default YES), MergeBuses (p.47), MergeLineTerminals (p.47), MergeMSLineSections (p.47), Move (pp.47-48), Combine (p.42), CreateLineDeriveExisting (p.42), ReassignIDs (pp.48-49), Remove3WXformerContainer (p.49), CalculateRXBGFromLengthConfigCondType (p.41).

#### Equivalencing

| command | syntax | parameters | page |
|---|---|---|---|
| Equivalence | `Equivalence;` | None. Options are in `Equiv_Options` (SetData or DATA). Each bus to be equivalenced needs **Equiv** set true | p.34 |
| DeleteExternalSystem | `DeleteExternalSystem;` | Deletes buses whose Equiv is true | p.34 |
| SaveExternalSystem | `SaveExternalSystem("filename", SaveFileType, WithTies);` | SaveFileType PWB, PWB16-23, PTI23-35, GE14-23, CF, or AUX. WithTies must start with Y to be YES, and **needs an explicit file type** | p.38 |
| SaveMergedFixedNumBusCase | `SaveMergedFixedNumBusCase("filename", SaveFileType);` | Same types as SaveCase | p.38 |

#### Fault analysis

| command | syntax | parameters | page |
|---|---|---|---|
| Fault | `Fault([BUS n], faulttype, R, X);` / `Fault([BRANCH b1 b2 ckt], faultlocation, faulttype, R, X);` | faultlocation is 0-100 % from the near bus (branch only, required). faulttype SLG, LL, 3PB, or DLG. R, X optional, default 0 | p.102 |
| FaultAutoInsert | `FaultAutoInsert;` | Uses the relevant `CTG_AutoInsert_Options`. Lines and buses only | p.102 |
| FaultMultiple | `FaultMultiple(UseDummyBus);` | Default NO (faults at the nearest terminal). YES inserts dummy buses | p.102 |
| FaultClear | `FaultClear;` | — | p.102 |
| LoadPTISEQData | `LoadPTISEQData("filename", version);` | Integer PTI version | p.102 |

#### Time-step simulation

Datetimes are ISO8601 in UTC or with an offset, e.g. `2025-06-01T00:00:00-05:00`, unquoted in the doc examples. Solution type strings: `"Single Solution"`, `"Unconstrained OPF"`, `"OPF"`, `"SCOPF"`, `"GIC Only (No Power Flow)"`, `"Weather Only"`.

| command | syntax | parameters | page |
|---|---|---|---|
| TimeStepLoadPWW | `TimeStepLoadPWW("FileName", "SolutionTypeString");` | **Deletes existing timepoints.** Solution type default "Single Solution". Suspected glitch 2026-10-20-timestep-loadpww-plain: on builds dated 2026-09-20 and 2026-09-25 plain `TimeStepLoadPWW` failed with `Error With Loading PWWFile` while `TimeStepLoadPWWRange` loaded the same files; see [timestep-workflow](../concepts/timestep-workflow.md) | pp.143-144 |
| TimeStepLoadPWWRange | `TimeStepLoadPWWRange("FileName", Start, End, "SolutionType");` | Empty or out-of-range start/end means the file's own bounds. Deletes existing | p.144 |
| TimeStepLoadPWWRangeLatLon | `(..."FileName", Start, End, minLat, maxLat, minLon, maxLon, "SolutionType")` | Lat -90..90, lon -180..180 defaults. No date-line crossing. Added Nov 3 2025 | pp.144-145 |
| TimeStepAppendPWW / ...Range / ...RangeLatLon | same parameters as Load* | **Appends** to existing timepoints | pp.141-142 |
| TimeStepLoadB3D | `TimeStepLoadB3D("FileName", "SolutionType");` | Deletes existing. **Default solution type "GIC Only (No Power Flow)"** | p.143 |
| TimeStepLoadTSB | `TimeStepLoadTSB("FileName");` | Deletes existing | p.145 |
| TimeStepDoRun | `TimeStepDoRun(Start, End);` | No arguments runs all timepoints | p.143 |
| TimeStepDoSinglePoint | `TimeStepDoSinglePoint(DateTime);` | Errors if outside the TSS range | p.143 |
| TimeStepResetRun | `TimeStepResetRun` | Reset to the beginning | p.145 |
| TimeStepClearResults | `TimeStepClearResults(Start, End);` | Keeps the timepoints | p.142 |
| TimeStepDeleteAll | `TimeStepDeleteAll;` | Deletes all timepoints | p.142 |
| TimeStepSaveFieldsSet | `TimeStepSaveFieldsSet(objecttype, [fieldlist], filter);` | **Clears previous fields/objects for that type first.** filter default ALL | pp.145-146 |
| TimeStepSaveFieldsSetByObject | `TimeStepSaveFieldsSetByObject(objecttype, [fieldlist], [objectIDList]);` | **Does not clear**, and fields are unioned per type | p.146 |
| TimeStepSaveFieldsClear | `TimeStepSaveFieldsClear([objecttype]);` | Omitted clears all types | p.145 |
| TIMESTEPSaveSelectedModifyStart / ...Finish | `TIMESTEPSaveSelectedModifyStart;` ... `SetData(obj, [..., TimeDomainSelected], [...]);` ... `TIMESTEPSaveSelectedModifyFinish;` | Required bracket around TimeDomainSelected edits (Simulator 25). **Changing the selection deletes saved results for that type**, and the selection is stored in the .tsb, not the .pwb | p.146 |
| TIMESTEPSaveInputCSV | `TIMESTEPSaveInputCSV("file", [input fields], Start, End);` | Fields such as LOAD_MW, GEN_MW, GEN_MWMAX, BRANCH_STATUS, WEATHERSTATION_* (the list is in the source). The TOC signature shows a stray `", "`. | p.147 |
| TimeStepSaveResultsByTypeCSV | `TimeStepSaveResultsByTypeCSV(ObjectType, "file.csv", Start, End);` | Only the first 3 letters of the type are significant | pp.147-148 |
| TimeStepSaveTSB / SavePWW / SavePWWRange | `("FileName")` / `("FileName", Start, End)` | — | p.148 |

#### Weather

| command | syntax | parameters | page |
|---|---|---|---|
| WeatherPWWSetDirectory | `WeatherPWWSetDirectory("dir", IncludeSubDirectories);` | IncludeSubDirectories default YES | p.152 |
| WeatherPWWLoadForDateTimeUTC | `WeatherPWWLoadForDateTimeUTC("2024-03-06T18:00Z");` | Searches the directory set above | p.152 |
| WeatherPFWModelsSetInputs | `WeatherPFWModelsSetInputs;` | Sets PFWModel inputs without applying them | p.150 |
| WeatherPFWModelsSetInputsAndApply | `WeatherPFWModelsSetInputsAndApply(SolvePowerFlow);` | **SolvePowerFlow is required** (added Dec 31 2024). YES solves with the default method. Applying **changes case values** such as gen MaxMW | p.150 |
| WeatherPFWModelsRestoreDesignValues | `WeatherPFWModelsRestoreDesignValues;` | Undoes those changes | p.151 |
| TemperatureLimitsBranchUpdate | `TemperatureLimitsBranchUpdate(RatingSetPrecedence, NormalRatingSet, CTGRatingSet);` | Precedence NORMAL (default), CTG, or blank. Rating sets DEFAULT (the Limit Monitoring set), NO, or A-O | p.149 |
| WeatherLimitsGenUpdate | `WeatherLimitsGenUpdate(UpdateMax, UpdateMin);` | Both default YES | pp.149-150 |
| WeatherPWWFileAllMeasValid | `WeatherPWWFileAllMeasValid("file", [fields], Start, End);` | Fields TEMP, DEWPOINT, WINDSPEED, WINDSPEED100, GLOBALHORZIRRAD, DIRECTHORZIRRAD, WINDGUST, SMOKEVERTINT, PRECIPRATE, or PRECIPPERCFROZEN. PWW v2+ | pp.150-151 |
| WeatherPWWFileCombine2 / WeatherPWWFileGeoReduce | `("src1", "src2", "dest")` / `("src", "dest", minLat, maxLat, minLon, maxLon)` | Same stations and non-overlapping ranges required | p.151 |

#### Scheduled actions

| command | syntax | parameters | page |
|---|---|---|---|
| SetScheduleWindow | `SetScheduleWindow(Start, End, Resolution, ResolutionUnits);` | Units MINUTES, HOURS, or DAYS. Times use the **current locale's** date format | p.140 |
| SetScheduleView | `SetScheduleView(ViewTime, ApplyActions, UseNormalStatus, ApplyWindow);` | Blank keeps the current settings | p.140 |
| ApplyScheduledActionsAt / RevertScheduledActionsAt | `(Start, End, Filter, Revert)` / `(Start, End, Filter)` | End defaults to Start. Revert default NO | pp.139-140 |
| ScheduledActionsSetReference / IdentifyBreakersForScheduledActions | `ScheduledActionsSetReference;` / `(IdentifyFromNormalStatus)` | — | p.140, p.139 |

#### Case management, data I/O, modes, logging

| command | syntax | parameters | page |
|---|---|---|---|
| OpenCase | `OpenCase("filename", OpenFileType, [LoadTransactions, StarBus, HowToKeepDuplicates]);` (PTI) or `[MSLine, VarLimDead, PostCTGAGC, MSLineDummyBus]` (GE) | OpenFileType default PWB; PTI, PTI23-35, GE, GE14-23, CF, AUX, UCTE, AREVAHDB, or OPENNETEMS. PTI: LoadTransactions YES, NO, or DEFAULT; StarBus NEAR, MAX, or value; duplicates LAST or ALL. GE: MSLine MAINTAIN or EQUIVALENCE; VarLimDead number; PostCTGAGC YES/NO; MSLineDummyBus FROM, MAX, or value/range | pp.34-35 |
| AppendCase | `AppendCase("filename", OpenFileType, [StarBus, EstimateVoltages]);` (PTI) or `[MSLine, VarLimDead, PostCTGAGC, EstimateVoltages]` (GE) | StarBus NEAR default. VarLimDead 2.0. PostCTGAGC NO. EstimateVoltages YES (angle smoothing) | p.33 |
| NewCase | `NewCase;` | — | p.34 |
| SaveCase | `SaveCase("filename", SaveFileType, [PostCTGAGC, UseAreaZone]);` (GE) or `[AddCommentForObjectLabels, IncludeSubstations]` (PTI) | SaveFileType default PWB (latest); listed values PWB, **PWB16-PWB23**, PTI23-PTI35, GE14-GE23, CF, UCTE, AUXNETWORK (recommended for aux), AUX, AUXSECOND, or AUXLABEL. GE opts default NO. PTI opts default NO | pp.37-38 |
| EnterMode | `EnterMode(RUN\|EDIT);` | Needed for creating network objects. Mode-specific commands switch automatically | p.34, p.16 |
| CaseDescriptionSet / CaseDescriptionClear | `("text", Append)` / `;` | — | pp.33-34 |
| LoadEMS | `LoadEMS("filename", AREVAHDB);` | — | p.34 |
| RenumberBuses/Areas/Zones/Subs | `(NumCI)` | The 1-based header index of the Custom Integer, i.e. `RenumberBuses(2)` uses CustomInteger:1 | pp.36-37 |
| RenumberCase / Renumber3WXFormerStarBuses / RenumberMSLineDummyBuses | see source | | p.37, pp.35-36, p.36 |
| LoadAux | `LoadAux("filename", CreateIfNotFound);` | CreateIfNotFound default NO (legacy header) or YES (concise), and **only honoured when the legacy DATA header says PROMPT** | p.23 |
| LoadAuxDirectory | `LoadAuxDirectory("dir", "filterstring", CreateIfNotFound);` | Loads alphabetically. Wildcard filter | pp.23-24 |
| LoadData | `LoadData("filename", DataName, CreateIfNotFound);` | Loads only the named DATA section | p.24 |
| LoadScript | `LoadScript("filename", ScriptName);` | Runs only the named SCRIPT. The third argument is **ignored** | pp.24-25 |
| LoadCSV | `LoadCSV("filename", CreateIfNotFound);` | Send-to-Excel CSV layout. Default NO | p.24 |
| ImportData | `ImportData("filename", FileType, HeaderLine, CreateIfNotFound);` | CSV, PWCSV, or CROW (Scheduled Actions). HeaderLine 1 or 2 | p.23 |
| SetData | `SetData(objecttype, [fieldlist], [valuelist], filter);` | **Filter omitted means the key fields must be in the list and one object is edited.** ALL, AREAZONE, SELECTED, or "name" | p.31 |
| CreateData | `CreateData(objecttype, [fieldlist], [valuelist]);` | Key and required fields are mandatory | p.21 |
| SetElseCreateData | `SetElseCreateData(objecttype, [fieldlist], [SetValueList], [DefaultValueList]);` | Updates one object or creates it. **Blank entry = use default; `""` = literal empty.** Creation auto-switches to EDIT. Added "September ?, 2026" (sic) | pp.31-32 |
| Delete / DeleteDevice / DeleteIncludingContents | `Delete(objecttype, filter);` / `DeleteDevice([Bus 1]);` | Delete's filter defaults to **all objects of the type** | p.22 |
| SelectAll / UnSelectAll | `(objecttype, filter)` | Default all | p.29, p.32 |
| SaveData | `SaveData("filename", filetype, objecttype, [fieldlist], [subdatalist], filter, [SortFieldList], Transpose, Append);` | filetype AUXCSV, AUX, CSV, CSVNOHEADER, or CSVCOLHEADER. Transpose default NO (CSV only). **Append default YES** | pp.25-26 |
| SaveDataWithExtra | `SaveDataWithExtra(..., [Header_List], [Header_Value_List], Transpose, Append);` | CSV variants only. Append default YES | pp.28-29 |
| SaveDataUsingBuiltInAUXFormat | `("filename", filetype, [List_of_built_ins], ModelToUse)` | **Always appends if the file exists**. Built-ins: Custom Info, Network Model, Contingency, Transient Models, Transient, Model Info, Voltage Conditioning, Weather Dependent Limits | p.27 |
| SaveDataUsingExportFormat / SaveDataEPC / SaveObjectFields / SendtoExcel / WriteLimitMonitoringSettings | see source | SaveDataEPC Append default YES | pp.27-28, p.26, p.29, pp.29-30, p.32 |
| LogAdd / LogAddDateTime / LogClear / LogSave / LogShow | `LogAdd("text");` `LogSave("filename", AppendFile);` | — | pp.19-20 |
| SetCurrentDirectory | `SetCurrentDirectory("dir", CreateIfNotFound);` | Default NO | p.20 |
| StopAuxFile | `StopAuxFile;` | The rest of the file is treated as a comment | p.20 |
| CopyFile / DeleteFile / RenameFile / WriteTextToFile / ExitProgram | see source | WriteTextToFile appends. ExitProgram is not for SimAuto | pp.19-20 |
| EnterDistMasterPassword / VerifyDistributedComputersAvailable | `(Password)` / `;` | For the DoDistributed options | p.153 |

#### Transient stability (names only, out of scope)

TSAutoCorrect (auto-fix parameters, aborts the script if errors remain, p.129); TSAutoInsertDistRelay (p.129); TSAutoInsertZPOTT (p.129); TSAutoSavePlots (p.129); TSCalculateCriticalClearTime (p.130); TSCalculateSMIBEigenValues (p.130); TSClearAllModels (p.130); TSClearModelsforObjects (p.130); TSClearResultsFromRAM (p.130); TSDisableMachineModelNonZeroDerivative (p.131); TSGetVCurveData (p.131); TSGetResults (export results, p.131); TSInitialize (p.132); TSJoinActiveCTGs (p.132); TSLoadBPA / TSLoadGE / TSLoadPTI / TSLoadRDB / TSLoadRelayCSV (load dynamics/relays, pp.133-134); TSPlotSeriesAdd (p.134); TSResultStorageSetAll (p.135); TSRunResultAnalyzer (p.135); TSRunUntilSpecifiedTime (p.135); TSSaveBPA / TSSaveGE / TSSavePTI (pp.135-136); TSSaveTwoBusEquivalent (p.136); TSSolve (one TS contingency, p.136); TSSolveAll (p.137); TSSolveContinue (p.137); TSTransferStateToPowerFlow (p.137); TSValidate (p.137); TSWriteModels (p.137); TSWriteOptions (p.137); TSSetSelectedForTransientReferences (p.138); TSSaveDynamicModels (p.138).

#### GIC (names only here; see [gic](../concepts/gic.md))

GICCalculate(MaxField, Direction, SolvePF) single snapshot (p.110); GICClear (p.110, duplicated at p.111); GICLoad3DEfield (p.110); GICReadFilePSLF / GICReadFilePTI (p.110); GICSaveGMatrix (p.110); GICSensitivitiesCalculate (Simulator 25, p.111); GICSetupTimeVaryingSeries (p.111); GICShiftOrStretchInputPoints (p.111); GICTimeVaryingCalculate (p.112); GICTimeVaryingAddTime (p.112); GICTimeVaryingDeleteAllTimes (p.112); GICTimeVaryingEFieldCalculate (p.112); GICTimeVaryingElectricFieldsDeleteAllTimes (p.112); GICWriteFilePSLF / GICWriteFilePTI (p.112); GICWriteOptions (p.113).

Also present but not study control: Oneline actions (pp.68-72), User Interface (pp.64-67), Regions (pp.127-128), Trainer (p.154), ISONEInterfaceLimitCalculation (pp.155-156), AXD display actions (p.210+).

---

### Aux option syntax

1. **Two DATA header forms.**
   - Concise (default since v19): `object_type DataName(field1, field2, ...) { values }`. No square brackets. Data is **always space-delimited**, and **Create_if_not_found is always YES** (p.157, p.158).
   - Legacy: `DATA DataName(object_type, [field1, field2], file_type_specifier, create_if_not_found) { ... }`. file_type_specifier is blank/AUXDEF/DEF (space) or AUXCSV/CSV/CSVAUX (comma). create_if_not_found is YES, NO, or PROMPT, and **YES if omitted** (pp.157-158, p.158).
   - Both forms are readable by v19+ (p.157). DataName is optional and is only used by `LoadData` (p.157).
2. **Setting an option object.** The document says to set options objects "using the SetData script command or DATA sections". Examples are `Equiv_Options` (p.34), `Ctg_AutoInsert_Options` (p.90), `SCALE_OPTIONS` (p.39), `TLR_Options` (p.84), `ATC_Options` (p.103), `IG_AutoInsert_Options` (p.43), and `CTGWriteAux_Options` (p.99). As DATA this is `Sim_Solution_Options (FieldA, FieldB) { valueA valueB }`, following the generic concise header.
3. **Key-less, single-record objects: not documented.** The document never explains how to address an object with no key fields. It says SetData without a filter needs key fields to find "the one object" (p.31, p.31), and it never says what happens when the object type has no keys. The document gives **no example** of `SetData(Sim_Solution_Options, ...)` or of a DATA block for an option object. Behaviour on an options object with the filter omitted is therefore unverified by this source. Test it before relying on it; `ALL` is the documented "all objects" filter.
4. **Per-contingency and per-tool solution options.** `Contingency`, `CTG_Options` and `QVCurve_Options` accept a `<SUBDATA Sim_Solution_Options>` block of **two lines**: field names first, then values (p.183, pp.183-184, p.206). The precedence is Contingency record > CTG_Options > global solution options (p.183).
5. **Field names.** The parser accepts concise and legacy names automatically (p.160). Concise names replace most location indices, e.g. legacy `LineMW:1` → `MWTo` (p.159). Location `:0` may be omitted (p.159). Dynamic-count fields keep `:n` (CustomFloat:n, PTDFMult:n) (p.159). Some fields can be referenced by user-defined name, e.g. `"CustomExpression:my name"`, `"CustomSingle:name"`, `"BGCalcField:name"` (p.159). Field lists are comma-separated and allow `//` comments (p.158). The field list for any object is available from Window > Export Case Object Fields, where key fields are starred (p.157, p.159).
6. **Creation vs edit (LoadAux is a merge).** A record whose key matches an existing object edits that object. A new object is created **only if all Required Fields are present** (and Create_if_not_found allows it). Otherwise the file silently only edits existing objects (p.158, p.158). Topology objects (Bus, Gen, Load, Shunt, Branch, LineShunt, DCTransmissionLine, VSCDCLine, MSLine, 3WXFormer, MTDC*) can be created **only in EDIT mode** (p.158).
7. **LoadAux CreateIfNotFound precedence.** The DATA section's own create flag overrides the LoadAux argument. The script argument is used only when the section says PROMPT (p.158, p.23).
8. **Deletion through DATA.** `REMOVEDBUS`, `REMOVEDBRANCH`, etc. delete objects when loaded in EDIT mode. Only the Difference-Flows object types have a REMOVED* form (p.157).
9. **SUBDATA.** The form is `<SUBDATA type> ... </SUBDATA>` inside a record, with a rigid per-type format (p.165). For Contingency, `CTGElement` **replaces** all existing elements and `CTGElementAppend` appends (p.170).
10. **Identification by label.** If the `Label` field is present it is the **only** identifier used, even when keys are also given. Blank labels are not read, and objects cannot be created by label (p.162). SUBDATA references resolve in this order: key fields, secondary keys, component labels, then labels (p.163).
11. **Values.** Strings with spaces or commas must be quoted (p.160). The `}` must be on its own line (p.160). Each record starts on its own line (p.160).
12. **Mode.** Mode-specific script commands switch RUN/EDIT themselves (p.16, p.34). `EnterMode(EDIT)` is needed explicitly for DATA creation of topology objects.

---

### Surprises / silent behaviour

1. **SetData with no filter is not "all".** It targets one object by keys, and `ALL` is needed for every object. Elsewhere, including `Delete`, a blank filter means all (p.31, p.16, p.22).
2. **`CTGSolveAll` clears results even for skipped contingencies** by default (`ClearAllResults` defaults to YES). The same holds for `CTGComboSolveAll` (pp.97-98, p.91).
3. **`CTGSolve` leaves the case in the post-contingency state.** Call `CTGRestoreReference` afterwards (p.97, p.96).
4. **`SolvePowerFlow(DC, ...)` flips the case into DC mode**, and later solves then default to DC. The doc warns AC may be hard to recover (p.60).
5. **`ResetToFlatStart` with defaults resets generator voltage setpoints to 1.0 pu**, not just bus voltages (p.59).
6. **Before each solve Simulator pre-processes** with angle smoothing and generator MW estimation from remembered state. `ClearPowerFlowSolutionAidValues` stops that (p.54).
7. **`RestoreState(BEFOREFAILED)` disappears after any successful solve**, and Restore/Delete **fail** if the state was never set (p.62, p.62).
8. **LoadAux's `CreateIfNotFound` is effectively ignored.** Concise headers always create. Legacy headers use their own flag, which defaults to YES, and the argument matters only for PROMPT. A record missing Required Fields never creates anything and gives no stated warning (p.23, p.157, p.158).
9. **Save commands append by default**: SaveData, SaveDataWithExtra, SaveDataEPC, CTGWriteAuxUsingOptions, the ATC/PV/QV Write*, and the DiffCase EPC writers. SaveDataUsingBuiltInAUXFormat and WriteTextToFile always append. The exceptions default to overwrite: CTGWriteFilePTI and ATCWriteScenarioLog (p.26, p.28, p.26, p.99, p.27, p.20, p.99, p.105).
10. **`CalculateShiftFactors` defaults to `AbortOnError=YES`**, so a failure kills the rest of the aux file (p.85).
11. **LODF has no AC method.** Only DC or DCPS is allowed. Islanding outages are reported as a huge number unless `IncludeIslandingCTG=NO` (p.79, p.81, p.80).
12. **Renamed commands** are still accepted under their old names: `CalculateTLR` → `CalculateShiftFactors`, `CalculateTLRMultipleElement` → `CalculateShiftFactorsMultipleElement`, `DiffFlow*` → `DiffCase*`, `ATCWriteAllOptions` → `ATCDataWriteOptionsAndResults` (p.84, p.86, p.54, p.104).
13. **`CTGAutoInsert`, `CTGPrimaryAutoInsert`, `FaultAutoInsert`, `InjectionGroupsAutoInsert` and `Equivalence` take no parameters.** Everything comes from their options objects, so stale options from a prior session silently drive the result (p.90, p.95, p.102, p.43, p.34).
14. **Contingencies run in creation order**, not name order. Use `CTGSort` first if order matters, e.g. before `CTGJoinActiveCTGs` (p.98).
15. **`DetermineBranchesThatCreateIslands` overwrites the Selected field.** With a blank filename it forces SetSelectedOnLines=YES (p.73, p.73).
16. **`ClearSmallIslands` de-energizes by opening generators** in every island except the one with the most buses (p.42).
17. **`Scale` only touches objects whose bus/area/zone/owner has Scale=YES.** Set and reset that field around each call, as in the doc's example. Numeric parameters scale the aggregate, and field-name parameters scale per object (p.39, p.39, p.40).
18. **`SetScheduledVoltageForABus` also rewrites the setpoints of regulating gens and switched shunts** (p.50).
19. **`WeatherPFWModelsSetInputsAndApply` changes case values** such as gen MaxMW. Its `SolvePowerFlow` argument is **required** (p.150).
20. **Time step:** Load* commands delete existing timepoints and Append* commands keep them. B3D defaults to "GIC Only (No Power Flow)". `TimeStepSaveFieldsSet` clears prior fields for the type, while `SetByObject` unions. Changing TimeDomainSelected deletes saved results, and the selection lives in the .tsb, not the .pwb (p.143, p.141, p.143, p.145, p.146, p.146).
21. **`ATCDetermine` and `ATCDetermineMultipleDirections` have opposite `DoMultipleScenarios` defaults**: YES if scenarios exist versus NO (p.103, p.104). `ATCWriteToExcel`/`ATCWriteToText` can write **blank** results without an explicit field list (p.108).
22. **An Area SET_TO contingency action needs manually set options.** Island-based AGC must be disabled, make-up power must be "Same as Power Flow case", and AGC must not be disabled. "Simulator does not automatically set these options" (p.180).
23. **The Label field wins over key fields** whenever it is present in a DATA list (p.162).
24. **SimAuto limits:** `<PROMPT>` filenames, `MessageBox` and `ObjectFieldsInputDialog` fail, and `ExitProgram` should not be used (p.17, p.64, p.64, p.19).
25. **Smart quotes break parsing** (p.15). `StopAuxFile;` silently comments out everything after it (p.20).
26. **Document gaps and errors worth knowing:**
    - `CTGWriteResultsAndOptions` lists a `UseConcise` parameter that has no description (p.100 vs pp.100-101).
    - `SaveCase` lists only `PWB16-PWB23` explicitly, plus `PWB` = latest (p.37).
    - `ResetToFlatStart`'s intro reuses SolvePowerFlow's "conditional response" wording, which does not apply (p.59).
    - `DiffCaseWriteRemovedEPC`'s rename note names the wrong old command (p.57).
    - `MergeLineTerminals` says "multi-section lines" in its filter text (p.47).
    - `SetElseCreateData` is dated "September ?, 2026" (p.31).
    - The `filtertype`/`prefilter` fields of FILTER DATA are shown only by example.
    - Key-less option-object addressing via SetData is undocumented (see Aux option syntax item 3).
27. **`CTGWriteAllOptions` does not save results.** It is fixed to opt6=NO (p.99), so use `CTGWriteResultsAndOptions` to capture violations.
28. **`LoadScript` ignores its CreateIfNotFound argument** (pp.24-25).
29. **`EstimateVoltages` errors on a blank filter** and needs some buses outside the filter (p.58).


---

# ==== powerworld-study-options.md ====

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
`GEN` (silently ignored, V). On the Simulator 25 beta build used 2026-09-28, `CTGAutoInsert`
inserted **zero** contingencies with no error: always count the result against lines plus
two-winding transformers.

### C. OPF

| want | object.field / command | tag |
|---|---|---|
| area under OPF | `Area.BGAGC = "OPF"` (values: Off AGC, Part. AGC, ED, Area Slack, IG Slack, OPF) | V 2026-09-11 |
| super area under OPF | `SuperArea.BGAGC` — value vocabulary not in the export | S |
| movable gens | `Gen.GenAGCAble = "YES"`; writing `GenMW` turns it off, so set it after MW writes | V |
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


---

# ==== time-step-simulation-backend.md ====

---
type: reference
domain: cross-cutting
topic: timestep
aliases: [timestep-backend, time-step-simulation-backend]
tags: [timestep, powerworld, esapp, simauto, backend, reference]
---

# Reference: time-step-simulation backend

> ⚠️ **TimeStep ≠ Transient Stability.** This is PowerWorld's **TimeStep** weather
> feature (quasi-static `.pww` weather → hourly MW), driven by the low-level `esapp`
> `TimeStep*` script commands. It is **NOT** a transient-stability/dynamics study and
> does **NOT** use esapp's `pw.ts_solve` / `TSWatch` / `ContingencyBuilder` API (see the
> "TS" warning on [esapp](../concepts/esapp.md)). The "TS" in the `TSPFWModelString` field means *TimeStep*,
> not Transient Stability. Do not import or call any transient-stability function here.

## Abstract

Code-reconstruction reference for a timestep simulation pipeline — the worker function's PowerWorld call sequence (weather load → generator selection → field-save wrapper → run → export), `_GEN_PARAM` field list, `process_results` CSV post-processing with 8 header rows skipped, and both series and parallel orchestration variants. Covers every SimAuto command, required wrapper (`TIMESTEPSaveSelectedModifyStart`/`Finish`), and gotcha in enough detail to regenerate working simulation code from scratch. Read this in full only when writing or regenerating code for a timestep simulation; for the gist, use [timestep-simulation](../concepts/timestep-simulation.md).

## Connections

- **Up:** [timestep-simulation](../concepts/timestep-simulation.md) + [Home](../index.md)
- **Across:** [pww-data](../concepts/pww-data.md), [copper-plate](../concepts/copper-plate.md), [timestep-simulation](../concepts/timestep-simulation.md), [timestep-simulation-setup](../methods/timestep-simulation-setup.md)

## Content

> **Library note — prefer `esapp` over `esa`.** This repo imports the standalone `esa` (Easy SimAuto) package. For new or regenerated code, prefer **`esapp` (ESA++)**: it wraps the **same** PowerWorld SimAuto server, and esapp exposes each of those SCRIPT commands as a typed named method (`pw.esa.TimeStepDoRun()`), which is what you should call — see [esapp-script-command-wrappers](../concepts/esapp-script-command-wrappers.md) — an agent reasons about it more reliably. Swap esa's data helpers (`GetParametersMultipleElement`, `change_parameters_multiple_element_df`, `get_key_field_list`) for esapp's bracket interface (`pw[Type, fields]`, `pw[Type] = df`, `Type.keys()`). See [esapp-overview](../methods/esapp-overview.md). (Library choice only — unrelated to the TimeStep-vs-Transient-Stability distinction.)

Code-reconstruction knowledge for the timestep simulation pipeline. Given a plain prompt
("run the renewable sim on the Synth2k case"), an agent reads this page and
writes WORKING code. Everything here is verified against the real source on disk
(the pipeline's source tree). Hub: [Home](../index.md).

The whole engine is two functions in one engine module: `timestep_worker(...)` (drives
PowerWorld) and `process_results(...)` (post-processes the CSV). The pipeline's CLI entry script and
the parallel variant's entry script are just CLI + grouping + I/O around them. The time math lives in
`time_utils.py`. **The parallel variant's engine module is byte-identical to the series one** — the
engine is shared; only the entry-script orchestration differs.

---

## 0. Imports & environment (get these wrong and nothing runs)

- **`from esapp import PowerWorld`** — esapp (ESA++) wraps the same PowerWorld SimAuto
  server as the older standalone `esa` package, and is the one to write. `pw.esa` is
  esapp's own raw SimAuto handle, and each SCRIPT command below is exposed as a typed named
  method (`pw.esa.TimeStepDoRun()`) — call those, not a hand-written script string. Only the
  data helpers differ beyond that: the bracket interface replaces esa's
  `GetParametersMultipleElement` / `change_parameters_multiple_element_df`.
- The import is **lazy** — done *inside* the worker function, not at module top —
  so importing the engine module never requires PowerWorld to be installed. Keep it lazy
  if you regenerate this.
- **Windows-only.** esapp drives PowerWorld Simulator through SimAuto (COM). No
  PowerWorld → no run.
- `numpy` is imported at module top with `# noqa: F401` purely "for parity with
  downstream tooling" — it's not used directly in the engine module. `pandas` is used.
- `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` is done so
  `from time_utils import convert_to_utc` resolves regardless of CWD.

```python
import os, sys, shutil, struct, tempfile
import numpy as np   # noqa: F401
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from time_utils import convert_to_utc
# ... inside the worker:
from esapp import PowerWorld       # lazy, only when actually simulating
from esapp.components import Gen
```

---

## 1. `_GEN_PARAM` — the generator field list (reconstructed)

These extra fields are appended to the case's key fields and pulled from every
generator. Reconstructed from the pipeline's engine module:

```python
_GEN_PARAM = [
    'Latitude', 'Longitude', 'GenUnitType', 'GenFuelType',
    'ZoneName', 'AreaName', 'TSPFWModelString', 'GenMWMax',
    'Selected', 'CustomString:1', 'CustomString:2',
]
```

Why each field is pulled:

| Field | Used for |
|---|---|
| `Latitude`, `Longitude` | output header rows (rows 7 & 8); also fed to the ISO-assignment step (a geopandas spatial join) to assign ISO region |
| `GenUnitType` | pulled for completeness; not used downstream in the engine module |
| `GenFuelType` | **the renewable selector** — `.str.contains('WND\|SUN')` picks wind/solar; also splits solar (`SUN`) vs wind (`WND`) |
| `ZoneName` | output header "State" row (label maps `ZoneName` → "State") |
| `AreaName` | output header "Utility" row (label maps `AreaName` → "Utility") |
| `TSPFWModelString` | output header "PV / Wind Types" row — the unit's PFW model string |
| `GenMWMax` | output header "Gen Max MW" row |
| `Selected` | toggled to `'YES'` for renewables, then used to drive `TimeDomainSelected` |
| `CustomString:1` | pulled but not used in the engine module |
| `CustomString:2` | output header "ISO" row (label maps `CustomString:2` → "ISO"); populated by the ISO-assignment step's spatial join |

Key fields come from `Gen.keys()` (typically `BusNum`, `GenID`)
and are **prepended**, so the resulting `gen` DataFrame has columns
`[<key fields>] + _GEN_PARAM`.

> ⚠️ **This prepend is not optional.** Later the code pushes `gen` back with
> `pw[Gen] = gen` (twice — to set `Selected` and
> `TimeDomainSelected`). PowerWorld matches each row to a generator by its key fields, so
> if `BusNum`/`GenID` weren't in the DataFrame the write would **silently do nothing** and
> no generators would be selected. Always keep the key columns in any DataFrame you write
> back. (Same rule on the esapp bracket path — see [esapp](../concepts/esapp.md).)

---

## 2. `timestep_worker` — the FULL backend sequence, IN ORDER

Signature: `timestep_worker(case_path, pww_list, result_csv) -> gen (DataFrame)`.
Returns the generator metadata DataFrame (the caller needs it for `process_results`).
Reconstructed from the pipeline's worker function:

```python
def timestep_worker(case_path, pww_list, result_csv):
    from esapp import PowerWorld                     # lazy import
    from esapp.components import Gen, Timepoint
    tmp_case = None
    try:
        # (a) temp-copy the case so parallel runs never fight over the .pwb lock
        tmp_fd, tmp_case = tempfile.mkstemp(suffix='.PWB')
        os.close(tmp_fd)
        shutil.copy2(case_path, tmp_case)

        # (b) open the temp case
        pw = PowerWorld(tmp_case)

        # (c) pull generator metadata (key fields + _GEN_PARAM)
        gen_param = list(Gen.keys()) + _GEN_PARAM
        gen = pw[Gen, gen_param]

        # (d) load weather file(s): first = Load, rest = Append. The project calls plain
        # TimeStepLoadPWW here, which fails on every file on Simulator 25 (builds dated
        # 2026-09-20 and 2026-09-25). Load the file's full span with the Range form instead.
        d0, d1 = struct.unpack_from("<dd", open(pww_list[0], "rb").read(22), 6)  # OLE days, UTC
        t0, t1 = [(pd.Timestamp("1899-12-30") + pd.Timedelta(days=d)).round("h") for d in (d0, d1)]
        pw.esa.TimeStepLoadPWWRange(pww_list[0], f"{t0:%Y-%m-%dT%H:%M:%SZ}",
                                    f"{t1:%Y-%m-%dT%H:%M:%SZ}", "Weather Only")
        for pww in pww_list[1:]:
            pw.esa.TimeStepAppendPWW(pww, "Weather Only")
        assert len(pw[Timepoint, ["TimeDomainDateTimeUTC"]]) > 0, "weather load gave no timepoints"

        # (e) EDIT mode: mark renewables Selected = YES, push back
        pw.esa.EnterMode("EDIT")
        gen.loc[gen['GenFuelType'].str.contains('WND|SUN', na=False), 'Selected'] = 'YES'
        pw[Gen] = gen
        pw.esa.EnterMode("RUN")

        # (f) declare which fields to save — MUST be wrapped (see callout below)
        pw.esa.TIMESTEPSaveSelectedModifyStart()
        gen.loc[gen['Selected'] == 'YES', 'TimeDomainSelected'] = 'YES'
        pw[Gen] = gen
        pw.esa.TimeStepSaveFieldsSet(
            "GEN",
            ["BGGenMWFuelTypeGeneric:10", "BGGenMWFuelTypeGeneric:12"],
            "SELECTED",
        )
        pw.esa.TIMESTEPSaveSelectedModifyFinish()

        # (g) run + export
        pw.esa.TimeStepDoRun()
        pw.esa.TimeStepSaveResultsByTypeCSV("gen", result_csv)
        pw.esa.CloseCase()
        return gen
    finally:
        # (h) always delete the temp case
        if tmp_case and os.path.exists(tmp_case):
            try:
                os.remove(tmp_case)
            except OSError:
                pass
```

Step-by-step, every SimAuto call / SAW method in execution order:

1. `tempfile.mkstemp(suffix='.PWB')` → `os.close(fd)` → `shutil.copy2(case_path, tmp_case)` — work on a private temp copy, never the original `.pwb`.
2. `pw = PowerWorld(tmp_case)` — open the case.
3. `gen_param = list(Gen.keys()) + _GEN_PARAM`
4. `gen = pw[Gen, gen_param]` — DataFrame of all gens.
5. `pw.esa.TimeStepLoadPWWRange(pww0, t0, t1, "Weather Only")` — load the first weather file over
   its full span, read from the file header. Plain `TimeStepLoadPWW` fails on Simulator 25 builds
   dated 2026-09-20 and 2026-09-25; assert the case now has timepoints.
6. for each remaining pww: `pw.esa.TimeStepAppendPWW(pww, "Weather Only")` — append.
7. `pw.esa.EnterMode("EDIT")`
8. set `gen['Selected'] = 'YES'` where `GenFuelType` contains `WND|SUN`.
9. `pw[Gen] = gen` — push selection into the case.
10. `pw.esa.EnterMode("RUN")`
11. **`pw.esa.TIMESTEPSaveSelectedModifyStart()`** ← opens the save-field edit transaction.
12. set `gen['TimeDomainSelected'] = 'YES'` where `Selected == 'YES'`.
13. `pw[Gen] = gen` — push `TimeDomainSelected`.
14. `pw.esa.TimeStepSaveFieldsSet("GEN", ["BGGenMWFuelTypeGeneric:10", "BGGenMWFuelTypeGeneric:12"], "SELECTED")` — choose the two MW-by-fuel-type fields to save for selected gens.
15. **`pw.esa.TIMESTEPSaveSelectedModifyFinish()`** ← closes the transaction.
16. `pw.esa.TimeStepDoRun()` — run the time-step simulation.
17. `pw.esa.TimeStepSaveResultsByTypeCSV("gen", result_csv)` — export gen results to CSV.
18. `pw.esa.CloseCase()`.
19. `finally:` delete `tmp_case`.

### ⚠️ REQUIRED wrapper — do not drop it

```
TIMESTEPSaveSelectedModifyStart;
   ... set TimeDomainSelected = YES + TimeStepSaveFieldsSet(...) ...
TIMESTEPSaveSelectedModifyFinish;
```

The `TimeStepSaveFieldsSet` + `TimeDomainSelected` changes **MUST** be bracketed by
`TIMESTEPSaveSelectedModifyStart;` … `TIMESTEPSaveSelectedModifyFinish;`. Without this
wrapper the field-save selection **silently fails** — the sim runs, the CSV is
written, but the per-generator MW columns you wanted are missing/empty. There is no
error; you just get a useless file. If you regenerate this code, keep the Start/Finish
pair around steps 11–15 exactly.

### Field codes `BGGenMWFuelTypeGeneric:10` / `:12`

These are the two PowerWorld TimeStep result fields saved per selected generator —
"generator MW by generic fuel type", indices `10` and `12`. Downstream
`process_results` splits output columns by the literal substrings `'solar'` and
`'wind'` in the exported CSV column names, so the two indices correspond to the solar
and wind MW outputs.
> **UNVERIFIED:** needs confirmation -- which of `:10` / `:12` is solar vs wind in the PowerWorld fuel-type
> generic enumeration (code only relies on the column-name token, not the index).

### `pww_list` semantics

`pww_list[0]` → `TimeStepLoadPWWRange` over its full span; every subsequent entry → `TimeStepAppendPWW`. Both
use the `"Weather Only"` mode argument. In practice the callers pass **one PWW per
worker call** (`[pww]`) and concatenate the resulting CSVs in pandas afterward — the
Append branch exists but the production paths feed single-file lists and stitch
quarters at the DataFrame level (see §4).

---

## 3. `process_results(gen, df)` — CSV → (solar_df, wind_df)

Signature: `process_results(gen, df) -> (solar_df, wind_df)`. `gen` is the DataFrame
returned by the worker; `df` is the raw exported CSV read back via `pd.read_csv`.
Reconstructed from the pipeline's `process_results` function.

### 3a. Time conversion first
`result = convert_to_utc(df)` — replaces the first column (Excel-serial timestamps,
which PowerWorld writes in UTC but the code treats as CST) with ISO-8601 strings marked
UTC that run 7 h early in summer (see §6).

### 3b. The 8 metadata header rows
Eight rows are prepended above the time-series. `row_names` are the row labels;
`labels` are the `gen` columns each row pulls its values from (positional zip):

```python
row_names = ['ISO', 'PV / Wind', 'PV / Wind Types', 'Gen Max MW', 'State', 'Utility',
             'Latitude', 'Longitude']
labels    = ['CustomString:2', 'GenFuelType', 'TSPFWModelString',
             'GenMWMax', 'ZoneName', 'AreaName', 'Latitude', 'Longitude']
```

| Header row | Source `gen` column |
|---|---|
| ISO | `CustomString:2` |
| PV / Wind | `GenFuelType` |
| PV / Wind Types | `TSPFWModelString` |
| Gen Max MW | `GenMWMax` |
| State | `ZoneName` |
| Utility | `AreaName` |
| Latitude | `Latitude` |
| Longitude | `Longitude` |

### 3c. `(BusNum, GenID)` meta_lookup
An O(1) dict over only the renewable rows, keyed by `(int(BusNum), str(GenID))`:

```python
ren_mask = gen['GenFuelType'].str.contains('WND|SUN', na=False)
meta_lookup = {
    (int(row['BusNum']), str(row['GenID'])): row
    for _, row in gen[ren_mask].iterrows()
}
```

### 3d. Header build — per-column branch logic
Walk every column of `result` once:

- column == `'DateTimeUTCExcelFormat'` → each header row gets its own label (the row name itself) in this column.
- column contains `'Gen'` → parse `parts = col.split(' ')`; `busnum = int(parts[2].replace("'", ""))`, `genid = parts[3].replace("'", "")`. On `IndexError`/`ValueError` → fill `'N/A'`. Otherwise look up `meta_lookup[(busnum, genid)]` and fill each header row from its mapped label (`'N/A'` if not found).
- any other column → fill `''` (empty) for all header rows.

The column-name shape PowerWorld emits is therefore like `... Gen '<BusNum>' '<GenID>' ...` (quoted bus and id at `parts[2]`/`parts[3]`), with `'solar'`/`'wind'` somewhere in the name. Header rows are assembled into `header_df` and `pd.concat([header_df, result], ignore_index=True)` → `result_1`.

### 3e. Solar / wind split by token matching
```python
PV_gen = gen[gen['GenFuelType'].str.contains('SUN', na=False)]
WT_gen = gen[gen['GenFuelType'].str.contains('WND', na=False)]

solar_tokens = {f"'{int(r['BusNum'])}' '{r['GenID']}'" for _, r in PV_gen.iterrows()}
wind_tokens  = {f"'{int(r['BusNum'])}' '{r['GenID']}'" for _, r in WT_gen.iterrows()}

solar_columns = ['DateTimeUTCExcelFormat'] + [
    c for c in result_1.columns
    if 'solar' in c.lower() and any(tok in c for tok in solar_tokens)]
wind_columns = ['DateTimeUTCExcelFormat'] + [
    c for c in result_1.columns
    if 'wind' in c.lower() and any(tok in c for tok in wind_tokens)]

return result_1[solar_columns], result_1[wind_columns]
```

A column lands in the solar output iff its name contains `'solar'` (case-insensitive)
**AND** contains a `'<BusNum>' '<GenID>'` token of a `SUN` generator; symmetric for
wind/`WND`. The timestamp column `DateTimeUTCExcelFormat` is always kept first in both.
Both returned frames carry the 8 header rows on top.

---

## 4. The pipeline's CLI entry script (series) — grouping, run loop, output naming

- CLI args (`parse_args`): `--case` (required), mutually-exclusive **required** group
  `--pww FILE...` xor `--pww-dir DIR`, plus `--year YYYY` (int, filters `--pww-dir`),
  `--output-dir`, `--yes/-y` (skip the `input()` confirm prompt).
- Default output: `Results/` next to the entry script (`os.path.join(_script_dir, "Results")`).
- **Grouping (`_group_files`)**: for each file, `re.search(r"(\d{4})_Q\d", name)`.
  Matches (quarter files like `NorthAmerica2025_Q1.pww`) are grouped by **year** so all
  4 quarters run as one logical run (`groups[year] = [...]`). Non-matches (e.g. forecast
  files) become individual runs keyed by their filename stem. With `--pww-dir`, only
  `.pww` files are listed and `year_filter=args.year` drops other years.
- **Run loop**: for each `(key, pww_list)`:
  - `is_historical = bool(re.search(r"\d{4}_Q\d", basename(pww_list[0])))`.
  - `out_stem = f"Historical_{key}"` if historical else `key` (forecast stems already
    start with `Forecast_`, so don't double-prefix).
  - Outputs: `{out_stem}_solar.csv`, `{out_stem}_wind.csv` in `output_dir`.
  - **Resume-safe skip**: if BOTH solar and wind CSVs already exist → skip (delete to re-run).
  - Runs each pww **one at a time** via `timestep_worker(args.case, [pww], q_csv)`
    into `_raw_<qname>.csv`, reads each back with `pd.read_csv`, removes the temp csv,
    `pd.concat(dfs, ignore_index=True)`, then `process_results(gen, df)` → write
    `solar_path` / `wind_path`. `gen` from the last quarter is reused (identical per case).
  - Wrapped in try/except → prints error + `traceback.print_exc()`, continues to next group.

---

## 5. The parallel variant's entry script

Same engine (the parallel variant's copy of the engine module); only orchestration differs. What can produce a wrong
or failed run:

- **Cap `--workers` at what the PowerWorld licence and RAM allow.** Each worker drives its
  own SimAuto instance against its own temp copy of the case — the temp-copy in
  the worker function is what makes concurrency safe.
- **Workers must stay top-level and import the engine inside the child.** Windows spawn
  needs them picklable, and the parent must never load PowerWorld.
- **Incomplete years are skipped silently** — only years with all four quarters become
  groups, and a group with any failed sim skips assembly.
- **Resume-safe:** a group whose solar *and* wind CSVs both exist is skipped, so a rerun
  after a partial failure does not redo finished work.

## 6. `time_utils.py` — time math

> **Correction:** the conversion below is wrong. PowerWorld writes column 0 in **UTC**
> (measured 2026-10-20 on build 2026-09-25: it matched `Timepoint.TimeDomainDateTimeUTC` row for
> row), but the code treats it as CST and shifts it the wrong way. Labels run 7 h early in summer
> and 6 h early in winter (7 h measured 2026-10-14 against `TimeDomainDateTimeUTC`). Re-label from
> `Timepoint.TimeDomainDateTimeUTC` before joining on time; see [how-to-analyze-results](../methods/how-to-analyze-results.md).
> The text below describes what the code does, not what is right.

Two facts that change an answer:

- **The conversion applies a DST step, not a fixed offset.** The code reads column 0 as
  Excel-serial CST, subtracts 6 h, and takes one more hour off inside US DST (second Sunday in
  March 02:00 → first Sunday in November 02:00) before rounding to the hour. A summer label is
  therefore 7 h earlier than the true UTC hour, and a winter label 6 h earlier.
- **`interpolate_to_hourly` exists but is NOT called** in the current run path. It fills
  3-hour forecast gaps; assuming it ran is how a gapped forecast series gets read as hourly.
## 7. Gotchas checklist (regenerate-safe)

- ✅ `from esapp import PowerWorld` — **esapp, not the standalone `esa`**. Same SimAuto
  underneath; do not mix the two in one script.
- ✅ **Windows + PowerWorld only** (SimAuto/COM).
- ✅ **Temp-copy the case** (`mkstemp('.PWB')` + `shutil.copy2`) and run against the
  copy; delete in `finally`. This is what makes parallel runs lock-safe.
- ✅ **`TIMESTEPSaveSelectedModifyStart;` … `TIMESTEPSaveSelectedModifyFinish;`** must
  wrap the `TimeStepSaveFieldsSet` + `TimeDomainSelected` edits, or saved fields
  silently come back empty.
- ✅ Selection is two-stage: `Selected='YES'` (EDIT mode) for renewables, then
  `TimeDomainSelected='YES'` (inside the Save-Modify wrapper) for those same gens.
- ✅ `EnterMode(EDIT)` before pushing `Selected`; `EnterMode(RUN)` before the
  Save-Modify wrapper and the run.
- ✅ Renewable selector everywhere: `GenFuelType.str.contains('WND|SUN', na=False)`;
  solar = `SUN`, wind = `WND`.
- ✅ **Resume-safe skip**: a run is skipped iff BOTH its solar and wind CSVs exist.
- ✅ **Historical grouping** keys off `re.search(r"(\d{4})_Q\d", name)` — quarter files
  group by year and are named `Historical_{year}_{solar,wind}.csv`; anything else runs
  individually under its stem. Keep `_group_files` and the `is_historical` check in sync.
- ✅ Confirmation prompt via `input()` unless `--yes/-y`; parallel adds `--workers`.
- ✅ Parallel workers must stay **top-level / picklable** and import the engine module inside
  the child process (Windows spawn).

---

## Related

- Hub: [Home](../index.md)
- Concept/how-to: [timestep-simulation](../concepts/timestep-simulation.md) · [timestep-simulation-setup](../methods/timestep-simulation-setup.md)
- Inputs: [pww-data](../concepts/pww-data.md) · PFW context: [copper-plate](../concepts/copper-plate.md) · ISO prep: the ISO-assignment step (a geopandas spatial join)


---
