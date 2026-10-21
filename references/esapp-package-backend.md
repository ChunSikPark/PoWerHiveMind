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
