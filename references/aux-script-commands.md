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
