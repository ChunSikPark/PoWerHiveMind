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
- **Contingencies, interfaces, injection groups and nomograms** are **string-keyed**
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

> Preference (house rule): for **data**, use the bracket interface
> (`pw[Gen, fields]`, `pw[Gen] = df`) over raw `GetParametersMultipleElement` /
> `ChangeParametersMultipleElementRect`; for **script commands**, use the named SAW
> methods (`pw.esa.SolvePowerFlow()`) or `pw.esa.RunScriptCommand("...")` for anything
> not yet wrapped. See [esapp-overview](../methods/esapp-overview.md) for end-to-end recipes and [powerworld-simauto](../concepts/powerworld-simauto.md)
> for the underlying COM server.
