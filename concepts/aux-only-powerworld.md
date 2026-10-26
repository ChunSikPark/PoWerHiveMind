---
type: concept
domain: tooling
topic: scripting
aliases: [aux-only, aux-without-esapp, aux-without-simauto, headless-aux, pure-aux]
tags: [powerworld, aux, script, simauto, esapp, provenance, house-rule]
---

# Driving PowerWorld with aux files alone

## Abstract

A PowerWorld `.aux` file is a complete program. One loaded file can open a case, edit it,
solve it, export results to CSV, write the message log to a text file and exit, with **no
Python and no SimAuto call of your own**. Live-verified 2026-09-11 on a regional synthetic
planning model. This page covers what the aux language can do unaided, what it structurally
lacks (no return values, almost no control flow, no assertions), and the read-back
discipline that substitutes for them. It covers the two conditional constructs it *does*
have: the solve-failure `STOP` slots and, since the September 2026 patch,
`SetElseCreateData`'s exists-check. It lists the syntax traps measured the same day. Most
important is **the field-name provenance rule**: the *Auxiliary File Format* manual is a
syntax manual with no per-object field catalog, so field names must come from esapp's
generated schema or PowerWorld's own field export, never from the manual and never from
memory. Read before writing any `.aux` by hand.

## Connections

- **Up:** [powerworld-simauto](powerworld-simauto.md) · [Home](../index.md)
- **Across:** [aux-script-commands](../references/aux-script-commands.md) (the SCRIPT actions, a working subset) ·
  [esapp-script-command-wrappers](esapp-script-command-wrappers.md) (the inverse house rule for the *Python* side) ·
  [opf-preconditions](opf-preconditions.md) (the first real study run this way) 
- **Applied in:** [new-device-contingency-aux](../methods/new-device-contingency-aux.md) · [case-to-case-device-transplant](case-to-case-device-transplant.md)
- **Across:** [powerworld-script-transfer](powerworld-script-transfer.md) (the same aux text, delivered by drop file instead of a launcher)
- **Deeper:** [esapp-schema-reference](../references/esapp-schema-reference.md) · Simulator's *Auxiliary File Format* manual (Help menu)

## Content

### It works, and the whole loop closes

Verified 2026-09-11, ~9k-bus synthetic planning model, Simulator 24 build 577. A single
`.aux` loaded through the GUI performed, unattended, in file order:

```
OpenCase -> EnterMode(RUN) -> SolvePowerFlow(RECTNEWT) -> SaveData x2 -> LogSave
```

The log recorded `Simulation: Successful Power Flow Solution` and both CSVs landed on
disk. Nothing in the chain went through `pw.esa`, `RunScriptCommand`, `LoadAux` or
`ProcessAuxFile` from the caller's side; the file was only opened.

The self-contained shape is:

```
SCRIPT
{
  LogClear;  LogAdd("start");  LogAddDateTime;
  OpenCase("<absolute path>.pwb");
  EnterMode(RUN);
  SolvePowerFlow(RECTNEWT);
  SaveData("<absolute path>.csv", CSV, Branch, [<fields>], [], "", [], NO, NO);
  LogSave("<absolute path>.txt", NO);
  ExitProgram;                     // omit to leave the GUI open
}
```

`LogSave` is the cheapest and only general feedback channel. Everything PowerWorld says
during the run, including warnings you would otherwise never see, lands in that text file.

**Unnamed `SCRIPT { }` blocks auto-execute on load.** The manual never says so in a
positive sentence, but `StopAuxFile` is documented as suppressing every later SCRIPT and
DATA block in the file (which presupposes they would otherwise run), and `LoadScript` is
described as executing only the section it names — a restriction stated against normal
open-the-file behaviour. Naming a block makes it
*additionally* addressable via `LoadScript`; it does not gate it. Several `SCRIPT` blocks
interleaved with `DATA` blocks in one file is the manual's own canonical layout.

### The one branch aux does have: conditional-response slots

Several analysis actions take a pair of optional filename slots that fire on success and
on failure, and either slot accepts the literal `STOP`, which halts **all** aux execution:

```
SolvePrimalLP("", STOP);        // succeed: continue.  fail: halt the file.
```

The manual describes all four parameters as optional, and says they specify what should
happen conditionally on whether a solution was found. `InitializePrimalLP`,
`SolveSinglePrimalLPOuterLoop` and `SolveFullSCOPF` carry the same slots.

**Use them on every solve whose failure would invalidate what follows.** The bare form has
no failure handler, so a solve that does not converge lets every later stage run against
an unsolved case and write plausible-looking numbers to correctly-named files. That is the
silent failure the read-back rule exists to catch, arriving through the one door a read-back
does not cover.

### What the aux language cannot do, and what to do instead

Beyond those slots and `SetElseCreateData` below: no return values, no general branching,
no arithmetic over a table, no assertions. Consequently:

- **A failed edit is indistinguishable from a successful one at runtime.** Same family as
  [case-to-case-device-transplant](case-to-case-device-transplant.md)'s `ProcessAuxFile` trap:
  it reports success and changes nothing.
- **Substitute a read-back CSV for every assertion.** After a write, `SaveData` the fields
  you just wrote, *before* any solve, to a file named for the check. Then read it. A run
  whose edit silently no-opped otherwise produces the unchanged case under new filenames,
  with plausible numbers throughout.
- **Per-object arithmetic is impossible.** `SetData` writes one literal to every object
  matching a filter, so "set each unit to 80% of its own maximum" cannot be expressed.
  That is the point to go back to Python.

### The one exists-check: `SetElseCreateData`

Added in the **September 2026 patch of Simulator 24**. Older builds do not have it, and
the aux will fail on a machine running one. PowerWorld's own justification names the gap
this page describes: *"Because AUX scripts provide no process control to determine if a
power flow case contains a particular object, this command provides a way to do that."*

```
SetElseCreateData(objecttype, [fieldlist], [SetValueList], [DefaultValueList]);
```

If the object exists it is updated; if it does not, it is created, and **Simulator switches
itself to EDIT mode to do so**. It affects exactly one object. There is no filter form, so
this is not a way to conditionally update a set.

The two value lists are where it goes wrong quietly:

- `[fieldlist]` must carry the key fields, and `[SetValueList]` must give them non-blank
  values. Same rule as everywhere else in this kit.
- **A blank entry (nothing between the commas) means "fall through to the default".** An
  empty pair of double-quotes `""` does *not*; it is a real value and suppresses the
  default. PowerWorld's own worked example turns on exactly this distinction: with
  `Status` written as `""` the command errors when the generator is absent, and with
  `Status` left blank it creates the generator using the default `"Closed"`.
- `[DefaultValueList]` is optional; omit it and Simulator's own defaults apply. Key fields
  in it are ignored.
- Creation still needs every **required** field to end up non-blank across the two lists.
  Most object types silently decline to create when a required field is blank.

```
SetElseCreateData(Bus, [Number, Name, AreaNumber, ZoneNumber, NomkV],
                       [1,,,3,], [1, "NewBus", 1, 3, 138]);
```

It does not lift the read-back rule. It tells you nothing about which branch it took, so
if the distinction matters, `SaveData` the object afterwards and look.

### The field-name provenance rule

**Simulator's own *Auxiliary File Format* manual documents script syntax and contains no
per-object field catalog.** Measured 2026-09-11: across ~10,300 lines, zero hits for any of
the Area or generator field names needed for an OPF setup. Re-confirmed 2026-09-12 against
the **September 1, 2026** edition — same result. **Check the `Last Updated` line on page 1
before trusting a claim sourced from it**: the manual gains actions between editions, and
the November 6, 2025 edition is missing four that exist by September 2026,
`SetElseCreateData` among them. The manual says so itself and directs you to
*Window → Export Case Object Fields* in the GUI instead. It therefore cannot confirm or
refute a field name, ever.

Do not guess field names, and do not take them from prose pages in this knowledge base either —
one such page in PoWerHiveMind carried an Area field name that does not exist in the schema.

**Verify against esapp's generated schema first, then emit the aux.** This costs seconds,
needs no PowerWorld session, and is the correct workflow for authoring aux by hand:

```python
from esapp.components import Area
[f for f in Area.fields() if "AGC" in f.upper()]   # does the name exist?
Area.is_editable("BGAGC")                           # can it be written?
Area.is_edit_mode_only("BGAGC")                     # does it need EnterMode(EDIT)?
Area.keys()                                         # what identifies the object?
```

`is_edit_mode_only` is the one that decides whether an `EnterMode(EDIT)` wrapper is
required or merely noise. `keys()` matters because a `SetData` with no filter needs the
full key row (see below). Within a script, `SaveObjectFields` gets the same metadata —
variable name, field, column header and description — straight from the running program.

### Syntax traps, all measured 2026-09-11 against the manual

| Trap | Correct form |
|---|---|
| `SetData`'s "all objects" token is the **bare keyword** `ALL`. `""` is not legal; the quotes make it parse as a filter *named* empty string | `SetData(Area, [Field], ["Value"], ALL);` |
| With **no** filter, `SetData` requires the object's full key row in the field list | see `Type.keys()` |
| `SaveObjectFields` takes **three required** arguments; the field list is not optional | `SaveObjectFields("f.csv", Area, [FieldA, FieldB]);` |
| `SaveData`'s `Transpose` and `Append` are **scalars**, not lists; a `[]` there is wrong even when it appears to work | `..., filter, [SortFieldList], NO, NO);` |
| `SaveData`'s filter *may* be blank (unlike `SetData`'s) — blank means all objects | `..., [], "", [], NO, NO);` |
| The `ALL` keyword is documented as usable "instead of a list of fields" on the Save commands, but the manual gives **no worked example anywhere**; bare `ALL` vs `[ALL]` is undocumented | use an explicit field list |
| Every file path must be **absolute**; a relative path resolves against `pwrworld.exe`'s working directory, not yours | — |
| **Smart quotes silently break a script.** Straight quotes only | never paste from Word or a PDF |
| Solver token is `POLARNEWTON`, not the commonly written `POLARNEWT`. esapp's `pflow(method=)` takes `"POLARNEWT"` ([handling-errors](../methods/handling-errors.md)), not `POLARNEWTON` | `RECTNEWT`, `POLARNEWTON`, `GAUSSSEIDEL`, `FASTDEC`, `ROBUST`, `DC` |
| `EnterMode(EDIT)` is required only to **create** topology objects. Modifying an existing one is not documented as needing it | keep the wrapper anyway; it costs nothing and the manual never positively blesses modify-in-RUN |

`DATA (Object, [fields]) { rows }` is the legacy header form and is correct; omitting the
file-type specifier means space-delimited rows. `BusNum:1` is the to-bus (`variablename:location`,
where `:0` may be omitted). Quoting string values is optional but advisable.

### When to use this, and when not to

Aux-only is right when the logic is declarative and the value is auditability: the whole
study is one reviewable text file, diffable and version-controllable, with no Python
environment to reproduce. It is wrong the moment you need to branch on a result, compute
per-object values, or assert anything beyond "read it back and look".

The middle path costs five lines and keeps both: author the whole study as `.aux` text and
use Python purely as the launcher via `exec_aux`, which buys back the read-back assertion
without moving any logic into Python. A stochastic-model study backend already runs this way.
