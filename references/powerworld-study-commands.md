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
