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

