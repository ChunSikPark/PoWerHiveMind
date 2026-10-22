# PowerWorldHiveMind - CONCEPTS

# ==== agc-participation-factors.md ====

---
type: concept
domain: tooling
topic: contingency
aliases: [agc-participation-factors, participation-factors, contingency-make-up-power, GenParFac,
  SetParticipationFactors, who-covers-lost-mw, UseAreaPartsMakeUpPower]
tags: [powerworld, agc, contingency, n-1, gotcha, synthetic-grid]
---

# AGC flags and participation factors: who covers lost MW in a contingency

## Abstract

When an outage drops generation, PowerWorld's contingency solve must find the MW somewhere. Three
settings decide who supplies it: the AGC flag, the participation factor, and the make-up power
option. **AGC on with every factor at 0 changes nothing, so the slack still takes everything.**
The common convention is AGC on for dispatchable synchronous units only, factors from
`MAXMWRAT`, and make-up power `Gen Part Factors`. Setting them leaves the base case untouched;
only contingency solves move. Read before any N-1 run on a case that loses generation.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [opf-preconditions](opf-preconditions.md) (the same AGC flag, needed for an OPF) ·
  [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md)
  (the swing taking all make-up power, playbook step 4) ·
  [reading-violationctg](../methods/reading-violationctg.md) (reading what the contingency solve
  then reports)
- **Deeper:** [powerworld-option-objects-v25](../references/powerworld-option-objects-v25.md) ·
  [powerworld-study-commands](../references/powerworld-study-commands.md)

## Content

### The three settings

| Setting | Field | What it does |
|---|---|---|
| AGC flag | `Gen.GenAGCAble` = `YES` / `NO` | whether a unit may be moved to cover a change in MW |
| Participation factor | `Gen.GenParFac` | the unit's share; a unit with twice the factor picks up twice the MW |
| Make-up power | `CTG_Options.UseAreaPartsMakeUpPower` | `Area Part Factors`, `Gen Part Factors`, or `Same as Power Flow`; PowerWorld's field note recommends `Gen Part Factors` ([powerworld-option-objects-v25](../references/powerworld-option-objects-v25.md)) |

The area's own AGC status (`Area.AreaAGCStatus`, `None` on every public case surveyed below) is a
separate switch; with `Gen Part Factors` the make-up goes straight by each unit's factor.

### Setting the factors

`SetParticipationFactors(Method, ConstantValue, Object);`
([powerworld-study-commands](../references/powerworld-study-commands.md)):

- `MAXMWRAT`: factor from each unit's maximum MW. It does not go stale when the dispatch changes.
  The usual choice.
- `RESERVE`: factor from headroom, MWMax minus present MW. Better physics, but it must be rerun
  after any dispatch change.
- `CONSTANT`: every unit the same `ConstantValue`.
- `Object`: `SYSTEM`, `[Area n]`, `[Zone n]`, `AREAZONE`, or `DISPLAYFILTERS`. It sets factors on
  every generator in scope; only units with `GenAGCAble = YES` take part.

### Traps

- **AGC flags with zero factors do nothing.** Measured 2026-10-18 on a ~9k-bus synthetic case: AGC
  switched on for several hundred units, every factor 0, and the solution did not move. Lost MW
  still lands on the slack, which on that case was one unit that could not cover a large plant.
- **`MAXMWRAT` stores per unit on the 100 MVA base.** A 150 MW unit gets 1.5, not 150. A check for
  "factor equals MWMax" fails on a correct case; check that factor / MWMax is constant across the
  AGC units. Some public cases store the factor in MW instead; only the ratios matter.
- **A battery on the slack bus shares the slack's swing.** The slack's change is split among that
  bus's units, so the battery charges or discharges whenever the slack moves, regardless of its
  scheduled MW.
- **The base case does not change.** With the area AGC status at `None`, setting factors and
  make-up power left every bus voltage identical (max change 0.0). Only contingency solves are
  affected.
- **Writing a unit's MW may switch its AGC flag off.** Suspected, not confirmed (seen 2026-10-18,
  reproduced on Synth40 on 2026-10-20, Simulator build 2026-09-25): writing a *changed* `GenMW`
  read back `GenAGCAble = NO` for that unit, while writing the same MW or another field did not.
  Workaround: write `GenAGCAble = YES` in the same call as the MW, or set the AGC flags after the
  dispatch write, and read them back either way.

### What public synthetic grids use

Surveyed read-only on 2026-10-18:

| Case | AGC on for | Factor | Make-up power |
|---|---|---|---|
| Synth2k series 25 summer peak | every unit, renewables and batteries included | = MWMax | Area Part Factors |
| Synth2k series 24, 2016 summer peak | thermal and hydro | = MWMax | Gen Part Factors |
| Synth2k series 24, 2024 high renewables | thermal and hydro | = MWMax | Gen Part Factors |
| a public 10k-bus synthetic case | thermal and hydro | = MWMax | Gen Part Factors |
| Synth40 | every unit | all 0 | Area Part Factors |

The common convention is AGC on for dispatchable synchronous units only (not wind, solar,
batteries, or condensers with no MW range), factors from `MAXMWRAT`, make-up `Gen Part Factors`.

### Checking it

Read back on a cold reopen, not in the session that set it: the AGC units each have a factor above
0 with factor / MWMax constant, renewables and batteries keep `GenAGCAble = NO`, and
`UseAreaPartsMakeUpPower` reads `Gen Part Factors`.


---

# ==== aggregate-clauses-cannot-bound-one-row.md ====

---
type: concept
domain: cross-cutting
topic: contingency
aliases: [non-regression-oracle, dominance-test, is-this-change-safe, acceptance-criterion,
  no-worse-than-base, per-element-check]
tags: [verification, contingency, n-1, remediation, acceptance-test, technique]
---

# Aggregate clauses cannot bound one row

## Abstract

Any "is this change safe?" test built from **counts, maxima, sums and set membership** is blind
to one element getting arbitrarily worse, because another element improving more pays for it. A
corridor going from 102% to 290% of its rating passed a four-clause non-regression test. The fix
is a **per-element clause over the elements present in both states**; no combination of
aggregates substitutes for it. Two sibling failures sit in the same family: an empty measurement
beats every aggregate, and a row that stopped being measured reads as cured. Read before
designing any acceptance criterion for a pruning, screening or remediation loop.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md)
  (the loop whose rounds this judges) ·
  [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) (the same
  "empty result reads as clean" rule for a ranking) ·
  [reading-violationctg](../methods/reading-violationctg.md) (the rows being compared) ·
  [violation-remediation](../demos/violation-remediation.md) (why one element can improve while
  another worsens)

## Content

### The measurement

A prune asks: *"if I remove this device, is the system no worse than with everything?"* The test
had four clauses, all sensible, evaluated per scenario:

```
count of elements over limit    <= reference
total exceedance (MW)           <= reference + tol
max loading m                   <= reference + tol
newly-crossed elements          == zero
```

It accepts this:

```
ref   : La m=1.02   Lb m=9.00   Lc m=4.00
trial : La m=2.90   Lb m=9.00   Lc m=1.10     -> ok=True
```

`La` nearly triples. Why every clause is satisfied:

- **count** unchanged, 3 → 3: all three were *already* over, so nothing crossed a threshold;
- **max(m)** unchanged: `Lb` at 9.0 is still the maximum, and it did not move;
- **total exceedance FALLS**: `Lc` drops 290 and `La` rises 188, a net improvement;
- **newly-crossed** is zero: `La` was already over, so it never *crossed* anything.

### Why this is structural, not a tuning problem

Each clause reduces the state to a **scalar or a set**. A scalar cannot express "this particular
element got worse"; a set membership test cannot either, once the element is already *in* the set.

The newly-crossed clause looks like per-element protection, but **it guards only the
boundary.** It protects an element at 0.99 from being pushed to 1.01. It offers nothing to an
element already at 1.02, which is exactly the population a remediation loop is working on.

The fix is a fifth clause with a different shape:

```
per-element m, for elements over in BOTH states   <= reference + tol, ELEMENT BY ELEMENT
```

Give it the **same** tolerance as the `max(m)` clause. Two different slacks for the same physical
quantity is a second number to get wrong, and reviewers cannot tell which one governs.

### Two sibling failures in the same family

In both, the reduction loses the thing being judged.

**An empty measurement dominates every aggregate.** If one scenario's trial table comes back
empty, its stats are all zero, which beats any reference on every clause. `"No rows"` is not
`"nothing wrong"`. A scenario *missing from the mapping* may already be handled; an empty *frame*
walks straight past that check. Refuse when the reference measured rows and the trial measured
none.

**Rows that vanish read as cured.** Set-differencing in one direction only (`trial − reference`,
for newly-crossed) means `reference − trial` is silently read as "fixed". But a row can disappear
because it *was no longer measured*: removing a parallel circuit deletes its contingency records,
so every row under that outage label vanishes, including rows on **other** elements that were
genuinely over. Those disappearances lower the count and the sum, which buys headroom for a real
regression elsewhere. The two defects compound.

**Fixed and not-measured must never share an encoding.** Account for the labels a removal
deletes, explicitly, and refuse a trial whose row set is not a superset of the reference minus
that accounted set. Default the accounted set to **empty**, so an unwired caller gets the strict
answer rather than a permissive one.

### The precondition everyone forgets

The test this replaced was `over == 0`: zero elements above limit. The loop's own accepted end
state still had well over a hundred elements over, so the criterion was **unsatisfiable**. Every
probe returned False, the search fell through to a blame heuristic, and it discarded almost every
device it was meant to prune, none ever confirmed safe. Its summary showed the device count
collapsing to a few percent of the start, which looked like success.

**Assert that your test can return True on the state you are about to test**, as a dry-run
precondition, before the search starts. An unsatisfiable criterion does not error; it quietly
turns your search into whatever the fallback does.

### Checklist for a non-regression test

1. Is there a **per-element** clause, not only aggregates?
2. Does it protect elements **already** in violation, not just the threshold crossing?
3. Is it evaluated **per scenario / per case**, so one cannot pay for another?
4. At what **granularity** are rows keyed, and is it the same granularity the loop acts on? (A
   collapsed or argmax view hides every non-argmax row.)
5. Can an **empty** measurement pass it?
6. Can a **vanished** row read as cured?
7. Is it **satisfiable** on the real end state, asserted rather than assumed?
8. Is each clause **individually** necessary, so that deleting any one of them makes some bad
   case pass?


---

# ==== auto-pfw-scripts.md ====

---
type: tool
domain: weather
topic: timestep
aliases: [auto-pfw-scripts, auto-pfw, pfw-insertion-script, pfw_eia,
  PFW_EIA.py, attach-pfw-models, missing-pfw-models]
tags: [pfw, weather, renewables, wind, solar, timestep, aux, powerworld, tool]
---

# Tool: `Auto_PFW` — attaching PFW weather models to renewables

## Abstract

A research group's `Auto_PFW` scripts attach PFW (power-flow weather) models to a case's wind
and solar units, so TimeStep can turn weather into MW. They are where the kit's case-auditor
sends you when renewables lack a PFW model. Read this before running them: they **silently skip
wind units they cannot classify**, so always re-count PFW coverage on the copy they save.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation-setup](../methods/timestep-simulation-setup.md) (the per-unit
  prerequisites a PFW model is one of) · [timestep-and-pfw](../demos/timestep-and-pfw.md) (the
  coverage count that decides whether a case can run a time step) ·
  [timestep-workflow](timestep-workflow.md) (the TimeStep chain that consumes PFW models)
- **Checked by:** the case-auditor's `ts.pfw_missing` rule, which names this tool as the handoff
  and counts how many of the missing wind units carry a class it can use

## Content

### What it does

Two scripts, both driving PowerWorld through SimAuto with the older `esa` package (not `esapp`):

| script | how it chooses the model | prompts |
|---|---|---|
| `PFW_EIA.py` | Wind: `GenMWMax_WindClass1` … `4` from `CustomInteger:1` (1–4) **or** `GenUnitType` (W1–W4). Solar: every unit gets `GenMWMax_SolarPVBasic2`. | none |
| `Automation_integrating_PFW_into_PowerWorld.py` | One user-chosen class applied to every wind unit (WindBasic, WindGeneral, WindClass1–4) and/or every solar unit (SolarPVBasic1/2). | wind / solar / both, then the class |

The sequence is the same in both:

1. Open the case, export the generator table (`PW.csv`) with `GenFuelType`, `GenMWMax`,
   `CustomInteger:1`, `GenUnitType`.
2. Select units by fuel type: `WND (Wind)` and `SUN (Solar)`.
3. Write one AUX record per unit attaching the chosen `GenMWMax_*` model object.
4. `LoadAux` the file and save a **copy** as `<case>_PFW.pwb`; the original is not modified.

A PFW model is a per-generator object record ("this unit converts weather to MW with the
WindClass2 curve"). TimeStep reads it together with a `.pww` weather file; without it a unit
produces nothing, and TimeStep still reports success.

### Failure modes

- **Silent skip.** In `PFW_EIA.py`, a wind unit with neither `CustomInteger:1` in 1–4 nor
  `GenUnitType` W1–W4 gets **no record and no warning**. Cases built from EIA-860 carry the class;
  many synthetic cases do not, and then most wind units are skipped. On both public synthetic
  cases probed 2026-09-30, `CustomInteger:1` read blank on every unit.
- **Record shape.** `WindClass1` records carry 10 values for 9 listed fields (an extra value
  before the hub height); classes 2–4 carry 9. Check the PowerWorld message log after the AUX loads.
- **Interactive script input.** The solar answer is lower-cased and then compared with a
  mixed-case name, so only the answer `1` selects SolarPVBasic1; answering `quit` at a class prompt
  raises an `AttributeError`; the WindGeneral field list spells `DefaultWindMSS`.

### Verifying the result

Count, on the saved `_PFW` copy, the renewable units whose PFW model string is empty
(`TSPFWModelString` two characters or fewer). The count should be zero; anything else is the
silent skip above. Also confirm valid coordinates on those units, since this tool sets only the
PFW model. Running the case-auditor with the `timestep` profile on the copy does both counts.

### When to use which

- The case carries a wind class per unit (EIA-derived): `PFW_EIA.py` is sufficient.
- It does not: give the units a class first (from EIA-860 plant data, or your own judgment), or
  accept that unclassified wind units get no model. The interactive script applies one class to
  every unit, which runs but flattens the fleet into one turbine type.

Established 2026-09-28 from the repository's scripts and README; not re-run on a case for this
page.


---

# ==== aux-only-powerworld.md ====

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
one such page in PowerWorldHiveMind carried an Area field name that does not exist in the schema.

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


---

# ==== case-impedance-completeness.md ====

---
type: concept
domain: cross-cutting
topic: case-audit
aliases: [case-impedance-completeness, dc-only-skeleton, missing-r-and-b, impedance-health-check]
tags: [technique, cross-cutting, validation, powerworld, impedance, case-quality, acpf]
---

# Case impedance completeness — a case that solves in DC may carry no R and no B at all

## Abstract

A PowerWorld case can solve DC power flow perfectly, report sensible flows, and be handed
between projects for years while carrying **no resistance and no line charging whatsoever**.
DC power flow reads only `X`, so nothing in a DC pipeline ever touches `R` or `C` and nothing
complains. The Synth9k 2031 case had `LineR ≤ 1e-6` and `LineC == 0` on **97.2% of its closed
lines**, undetected because every consumer up to that point was DC. **Check X/R before
trusting any case you did not build**, and especially before promising anyone an AC study.

## Connections

- **Up:** [Home](../index.md)
- **Found in:** a real-power planning study on the Synth9k 2031 case, 2026-08-18, and
  independently confirmed on a second lineage the same day: `LineR <= 1e-6`
  and `LineC == 0` on **97.5%** of a 9k-bus base case and
  **100.0%** of an 8k-bus draft case (median X/R 100,010 and 113,465), so the five
  scenario cases built from them in [applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md) inherit it
- **💡 Applies to:** any study whose input is exactly such a case · synthetic case
  construction, where the handoff between build stages is where this is introduced · case
  diffing, since a diff that ignores R/C will not see it · any statistics computed over a case's branches · any project
  that receives a `.pwb` from another project or vintage
- **Across:** any quantity derived by ratio (a ratio on a placeholder zero stays zero, so
  check this first), and any check on a produced artifact (same family: the artifact exists,
  but is it real?)

## Content

### The check

One line:

```python
xr = (br.LineX / br.LineR.replace(0, np.nan)).median()      # closed, non-transformer lines
```

| median X/R | verdict |
|---|---|
| **2 – 20** | normal overhead transmission |
| **> 1000** | R is placeholder. The case cannot do losses, and AC will not mean anything. |
| **74,195** | what the Synth9k 2031 case actually measured |

Alongside it, count `LineC == 0`. Legitimate zeros exist (genuine intra-substation bus ties,
thousands of them in this case), so compare the count against the number of zero-length branches
rather than expecting zero.

### Why it survives so long

**DC power flow reads only `X`.** Losses, charging, voltage and reactive power are the only
things that read `R` and `B`, and none of them appear in a DC pipeline. So a case can pass
through case-building, dispatch, DC screening and a conductor-planning loop with two-thirds of
its impedance missing, and every stage reports success.

The failure surfaces only when someone finally runs AC, typically a different person, in a
different project, months later, who then debugs *their* code.

### The trap inside the trap

A conductor-resizing or reinforcement loop **does not fix this**, even though it writes
impedance. It only writes R/X/C on the lines it upgrades: 2.8% of the lines in one Synth9k
run. Running it and declaring the case AC-ready leaves a case that is 97% DC-skeleton and
3% real, with **no way to tell the two apart** by inspection.

### The fix is usually a restore, not a model

Do not model R and B back in if they exist somewhere. In this case the same branch keys (more than 10k)
had healthy impedance in an older vintage of the same network, whose `X` agreed with the
current case on **96.2%** of lines, so the repair was a keyed copy of R and C, not a
reconstruction. Median X/R went 74,195 → 5.40.

Checklist for a restore:
1. **Key on the real key fields** (`BusNum`, `BusNum:1`, `LineCircuit` as a *stripped string* —
   see [per-unit-basis-discipline](per-unit-basis-discipline.md)'s cousin trap, a CSV round-trip turns `'01'` into `1`).
2. **Assert zero unmatched rows on both sides.** A partial join silently leaves placeholders.
3. **Check the donor's `X` agrees** with the target's. If it does not, you are transplanting
   R and C onto a different network's reactance — count and list those lines rather than
   hiding them (3.8% of lines here).
4. **Prefer a donor untouched by known-buggy code.** About 3% of the lines in the chosen donor carried R/C
   written by a defective recomputation and were sourced from its pre-upgrade ancestor instead.

### Do not confuse "solves" with "is physical"

The 2031 case solved DC fine throughout. Convergence is evidence only that the subset of the
model your solver reads is self-consistent, not that the model is complete.


---

# ==== case-to-case-device-transplant.md ====

---
type: concept
domain: cross-cutting
topic: design
aliases: [AUX transplant, device delta transplant, LoadAux create]
tags: [powerworld, esapp, aux, technique, case-diff]
---

# Case-to-case device transplant

## Abstract

How to copy a set of devices from one PowerWorld case into another without rebuilding the chain
that produced them. It is useful whenever a feature was developed on one scenario and the others
are stranded behind unscripted stages. Carve a **filtered AUX out of the source case's own
`SaveCase(AUX)` dump** so the field lists are PowerWorld's rather than hand-written, and load it
with `LoadAux(create_if_not_found=True)`. To *move* a device between buses, carve its record out
of the **target** case and re-point the bus number, so the whole schema transfers by construction.
Proven 2026-09-01 on four Synth9k scenarios: hundreds of buses, over a thousand shunts, about a
thousand branches, hundreds of gen moves, over a hundred load moves, criterion-10 clean on all four.

## Connections

- Used in a study spanning several scenarios, to answer an accepted migration risk.
- Complements [comparing-planning-cases](../demos/comparing-planning-cases.md), which is about
  *reading* a diff across two model vintages; this page is about *applying* one.
- Depends on the same key-field constraint as renaming a branch's circuit ID: some fields can only be changed
  through an AUX text round-trip, never by a write.
- 💡 **Could transfer to:** any study where one scenario got a
  feature and the rest need it, or where a chain is unreproducible and only the *result* survives.

## Content

### The method

1. `SaveCase(AUX)` the **source** case. Its per-object blocks (`Bus (…) { … }`) carry PowerWorld's
   own complete field lists. Never hand-write one, and never assume a field name.
2. Keep only the records you want, by key. Watch for **duplicate blocks**: a full dump writes
   `Bus`, `Gen`, `Load` and `Branch` more than once (the extras carry cost / OPF fields). Filter
   every occurrence, not the first.
3. Write them back out ordered **Bus → Shunt → Branch → Transformer** so references resolve.
4. Load into the **target** with `LoadAux(path, create_if_not_found=True)`.

### The trap that eats an hour

**`ProcessAuxFile` on a data aux creates nothing and reports success.** No error, no warning, and
the device counts are simply unchanged. `LoadAux(..., create_if_not_found=True)` is the working
call; the create flag is the entire difference. Assert on device counts after the load, never on
the absence of an exception.

### Moving a device between buses

There is no move operation. Delete-and-recreate risks dropping fields silently. The
`LoadGrounded` bug hit every moved load in the original migration and was invisible to a diff over
the write set, because a dropped field is by definition absent from it.

**Carve the record out of the TARGET case's own aux and re-point only the leading bus-number
token, then delete the original.** The whole schema then transfers by construction: there is no
field list to get wrong, and no value from the source case can leak in. This makes the
technique safe across scenarios: a moved generator keeps *its own* scenario's dispatch, not the
donor's.

### Always undo the text rounding

The aux writes R/X/C to 6 decimals and MW / limits to 3. Snapshot exact values before the
round-trip and write them back afterwards, confirming on read-back. Skipping this left the moved
loads 7.3e-3 MW light — small enough to pass a loose tolerance and wrong enough to poison a
conservation check later.

### esapp notes

- esapp has **no `change_and_confirm_params_multiple_element`** (the older `esa` package does).
  Write with `ChangeParametersMultipleElement`, then read back and compare yourself.
- `GetParametersMultipleElement` returns **`None`**, not an empty frame, for an object type with
  zero instances — a case with no shunts will crash a naive `len()`.
- See [esapp](esapp.md) and the `SaveCase` script-command trap: `pw.save()` writes nothing silently.

### When the numbering cooperates, check for it first

The Synth9k transplant needed **no renumbering at all**, because the target's highest bus number
sat below every new bus number in the source, which formed one contiguous block above it. That is worth two minutes of checking before
designing a remap: disjoint ranges turn a hard problem into a copy.


---

# ==== copper-plate.md ====

---
type: concept
domain: cross-cutting
topic: power-flow
aliases: [copper-plate, copperplate, copper-plate-model, network-collapse, unconstrained-dispatch]
tags: [copper-plate, dispatch, transmission, network, slack-bus, power-flow, technique, cross-cutting]
---

# Copper-Plate Model

## Abstract
Collapse the entire transmission network (strip all branches, loads, and shunts, then add a single slack bus) so generators dispatch to serve total system load **without any transmission constraints**. Every generator sees infinite capacity between itself and every other bus; hence "copper plate" (ideal conductor). Used in a weather-driven copper-plate study to let weather-driven renewable output dispatch freely, isolating the weather → MW signal from network topology artifacts. The build sequence (delete Branch/Load/Shunt → add slack bus 999999 → large slack gen) is documented under Build steps below.

## Connections
- **Up:** [Home](../index.md)
- **Used in:** a weather-driven copper-plate study (renewable dispatch without network limits — exact build steps under Build steps below)
- **💡 Could apply to (idea transfer):** renewable resource or potential assessment, max-generation studies, and isolating a weather → MW signal from any network study
- **Across:** [timestep-simulation](timestep-simulation.md) (copper-plate runs are typically time-step simulations over a weather period)

## Content

### What it does and why

A full power-flow model enforces transmission constraints: a wind farm may be curtailed because a nearby line is at thermal limit, even if the wind is blowing. For studies that ask "how much energy could these generators produce given this weather?" rather than "how much does the network allow?", those constraints are noise. Copper-plate removes them.

With all branches deleted:
- No line flow limits to violate.
- No voltage constraints (no shunts, no reactive power coupling).
- Total generation = total load, balanced by the slack bus.
- Each generator dispatches to its weather-driven maximum (wind speed → MW, solar irradiance → MW).

The slack bus absorbs any imbalance (positive or negative), so the power balance always closes regardless of the renewable dispatch profile.

### Build steps (from a weather-driven copper-plate study)

Starting from a full PowerWorld case:
1. **Delete Branch objects** — removes all transmission lines and transformers, eliminating all flow constraints.
2. **Delete Load objects** — removes all bus loads (load is represented as a net system-wide value, served by the slack).
3. **Delete Shunt objects** — removes all capacitors/reactors (no reactive power devices needed in a copper-plate model).
4. **Add slack bus 999999** — a synthetic bus that acts as the infinite balancing node.
5. **Add large slack generator at bus 999999** — set to AGC/slack mode with very large MW limits (e.g., ±99999 MW) so it can absorb any imbalance.

The result is a star topology: every original generator bus connects to the slack, and the slack sets system frequency/voltage reference.

### Use in a weather-driven copper-plate study

The PowerFlow Weather (PFW) copper-plate model drives weather-dependent renewable generators (wind, solar) through a time-step simulation over a historical weather period. Because the network is gone, the MW output of each generator in each time step is determined purely by the weather at its location — wind speed for wind, GHI/DNI for solar. This isolates the **weather → MW** relationship and produces a clean time series of potential (unconstrained) renewable generation.

Downstream studies can then take this unconstrained generation signal and apply network constraints separately, which keeps the weather modeling and the network modeling apart.

### 💡 Idea-transfer targets

- **Renewable resource/potential assessment:** "How much energy could all the wind and solar in a region produce over a 20-year climate?" Copper-plate gives you the unconstrained answer; the gap between copper-plate and network-constrained output quantifies curtailment potential.
- **Max-generation studies:** "What is the theoretical maximum MW this fleet could produce on any hour?" Strip the network, dispatch everything to maximum, read the total.
- **Weather → MW signal isolation for dynamic line rating:** DLR studies need to know how wind-driven generation affects line loading. A copper-plate pre-pass isolates the weather → generation relationship before layering in network effects.
- **Benchmarking network congestion:** the difference between copper-plate dispatch and constrained dispatch quantifies how much transmission is limiting renewable utilization.

### What copper-plate does NOT give you

- **Voltage profiles** — no branches means no voltage drops, no reactive coupling.
- **Line loading** — by construction there are no lines.
- **Congestion signals** — the whole point is to remove them.
- **Locational marginal prices** — no network, no transmission component to the LMP.

If you need any of these, you need the full network model. Copper-plate is specifically for studies where the question is about energy potential, not delivery constraints.

### Relationship to timestep simulation

Copper-plate models are almost always run as time-step simulations: the weather input changes each time step, the renewable dispatch updates, and the slack absorbs the balance. The [timestep-simulation](timestep-simulation.md) framework is the computational engine; the copper-plate topology is the network configuration.


---

# ==== esapp-environment.md ====

---
type: concept
domain: tooling
topic: scripting
aliases: [esapp-environment, esapp-setup, esapp-install, esapp-package]
tags: [esapp, powerworld, simauto, setup, environment, install]
---

# Concept: The esapp environment

## Abstract

What `esapp` is, what it needs to run, and how its pieces fit together. `esapp` (ESA++)
is a Pythonic wrapper over PowerWorld Simulator's SimAuto COM server: a `PowerWorld`
entry point, a bracket interface that returns pandas DataFrames, and a `SAW` wrapper
exposing the raw SimAuto surface underneath. Read this once when setting up; read
[esapp-overview](../methods/esapp-overview.md) to actually drive a case.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) · [preflight-powerworld](../methods/preflight-powerworld.md) · [esapp-overview](../methods/esapp-overview.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md) · [esapp-schema-reference](../references/esapp-schema-reference.md)

## Content

### Install

```bash
pip install esapp
```

Pulls in `pandas`, `numpy`, `scipy`, `matplotlib`, `geopandas`, and `pywin32`. The last
one is the COM bridge and is why this is Windows-only.

Before writing anything, run [preflight-powerworld](../methods/preflight-powerworld.md). It takes five seconds and
distinguishes "my code is wrong" from "this machine cannot run PowerWorld at all".

### What you actually need

| Requirement | Why | If missing |
|---|---|---|
| Windows | SimAuto is a COM server with no cross-platform equivalent | The weather half of this kit still works; see [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) |
| PowerWorld Simulator, installed | esapp drives it; it does not reimplement it | Nothing in the PowerWorld half functions |
| **The SimAuto add-on, licensed** | Automation is licensed separately from Simulator itself | Simulator's GUI works fine and every script fails. See [preflight-powerworld](../methods/preflight-powerworld.md) |
| Matching bitness | A 32-bit Simulator will not serve a 64-bit Python | `Class not registered` at dispatch time |

Without the SimAuto licence, a working Simulator installation cannot run a single line of
automation, and nothing in the GUI hints at it.

### Contributing to esapp

`esapp` is open source (Apache-2.0) and developed at Texas A&M:
**https://github.com/lukelowry/ESApp**

Found a bug, a missing field, or an undocumented behaviour while using this knowledge
base? Two places to send it: a defect in the **package** goes to the esapp repository
above; a defect in a **page** here goes to this repository's issues.

### Prefer `esapp` over `esa`

There is an older standalone `esa` package wrapping the same SimAuto server. Both work;
`esapp` is better documented and is what this kit's pages assume. Mixing them in one
project buys nothing and creates two mental models of the same COM object.

### The three layers

```
your code
    |
    v
PowerWorld          <- the entry point; open a case, get a summary
    |
    v
Indexable           <- the bracket interface: pw[Bus, "BusPUVolt"] -> DataFrame
    |
    v
SAW                 <- the SimAuto wrapper; RunScriptCommand and friends
    |
    v
pwrworld.SimulatorAuto   <- the COM server, i.e. PowerWorld itself
```

Most work happens in the bracket interface. Drop to `SAW` when you need a SCRIPT action
that has no bracket equivalent (see [aux-script-commands](../references/aux-script-commands.md) for the catalogue). Drop
below that almost never.

### Use the high-level helpers before reaching for script commands

`PowerWorld` exposes helpers for the common tasks. Verified
against esapp 0.1.3 by calling them:

```python
pw.pflow(getvolts=True, method="POLARNEWT")   # solve
pw.mismatch(asComplex=False)                  # per-bus P and Q mismatch
pw.overloads(threshold=100.0)                 # branches above a % of rating
pw.violations(v_min=0.9, v_max=1.1)           # limit violations
pw.flows()                                    # branch flows
pw.lodf((frm, to, ckt), method="DC")          # line outage distribution factors
pw.ptdf(seller, buyer, method="DC")           # transfer distribution factors
pw.ybus(dense=False)                          # admittance matrix (scipy sparse)
pw.jacobian(dense=False, form="R")            # the Jacobian
pw.gens(); pw.lines(); pw.loads()             # convenience tables
pw.voltage(complex=True, pu=True)
pw.save(filename=None)                        # silent no-op: writes nothing, see save-powerworld-case
pw.snapshot()                                 # restore point
pw.run_mode(); pw.edit_mode()                 # switch modes
```

**Every one of these is a method — call it.** Referencing `pw.overloads` or `pw.flows`
without parentheses hands you a bound method where you expected a DataFrame, and the
failure surfaces further down looking like something else.

Solver settings are the opposite: they are **assignable options**, not methods.

```python
pw.max_iterations = 50
pw.enforce_gen_mw_limits = True
```

Two of them do not do what their names say. `pw.dc_mode = True` and `pw.flat_start = True`
are accepted, but a scripted solve ignores both (live-tested 2026-09-23). For a DC solve
call `pw.pflow(method="DC")`; for a flat start call `pw.flatstart()` and then solve. See
[handling-errors](../methods/handling-errors.md).

Reach for a raw SCRIPT action only when no helper covers what you need.

### Getting at SimAuto directly

When you do need a raw SCRIPT action, the SimAuto wrapper is on the `.esa` attribute,
**not** on `PowerWorld` itself:

```python
pw.esa.RunScriptCommand('SolvePowerFlow(RECTNEWT)')
pw.esa.RunScriptCommand(r'SaveCase("C:\out\case.pwb", PWB)')
```

`pw.RunScriptCommand(...)` raises `AttributeError`. This is the single most common
first-attempt mistake with esapp, because every PowerWorld example you will find online
is written against the SAW object directly.

See [aux-script-commands](../references/aux-script-commands.md) for which action to use.

### Components and schema

Object types are importable classes rather than magic strings:

```python
from esapp.components import Bus, Gen, Load, Branch, Shunt, Area, Zone
```

The component schema is generated from PowerWorld's own field definitions, so field
names track Simulator rather than being hand-maintained. The full field map lives in
[esapp-schema-reference](../references/esapp-schema-reference.md).

### The rule that silently ruins writes

**Always keep an object's key fields in any DataFrame you write back.** For a generator
that is `BusNum` plus `GenID`; for a branch it includes the circuit identifier. Without
the key fields PowerWorld cannot tell which row you mean, and the write does not error;
it does nothing.

A second, related trap: `pw[Obj, field] = values` is **positional over the entire
table**. Assigning to a filtered subset writes nothing at all, silently. See
[applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md).
[AGENTS.md](../AGENTS.md) code rule 2 describes the same trap differently: a list built from
a filtered subset lands on the wrong rows. Not settled here; either way, build the full column.

Both fail without raising.

### Snapshots

`snapshot()` gives you a restore point for safe experimentation, which is much cheaper
than reloading a large case between scenarios. PowerWorld's own `StoreState` /
`RestoreState` script actions do the same at the solver level.

### Verifying your setup

```python
from esapp import PowerWorld

pw = PowerWorld(r"C:\path\to\case.pwb")
print(pw.summary())    # n_bus, n_branch, n_gen, n_load, totals, v_min, v_max, sbase
```

If that prints a sensible dictionary, the environment is good and you can start at
[esapp-overview](../methods/esapp-overview.md).


---

# ==== esapp-script-command-wrappers.md ====

---
type: concept
domain: tooling
topic: scripting
aliases: [esapp-wrappers, runscriptcommand-vs-named-method, esapp-named-methods]
tags: [esapp, powerworld, simauto, script-commands, runscriptcommand, api-drift, house-rule]
---

# Named SAW methods vs. `RunScriptCommand`

## Abstract

House rule for every line of PowerWorld-from-Python code: call the named esapp method
(`pw.esa.TimeStepDoRun()`), not the hand-written script string
(`pw.esa.RunScriptCommand("TimeStepDoRun;")`). 310 of esapp 0.2.1's SAW methods wrap a
PowerWorld SCRIPT command. Both forms reach the same COM call; the named method
buys a Python-side signature check, correct argument-string construction, and, above all,
**one place the maintainer can patch when PowerWorld changes a command's syntax**. This
page records the rule, the exact mechanism (so nobody overclaims it as runtime
validation), the two live-probed exceptions already settled elsewhere in this knowledge base, and
the related 0.2.1 change that turned a write-time `ValueError` into a warning. Origin:
feedback from the esapp author on the author's `pw.esa.RunScriptCommand` usage, verified
against the 0.2.1 source on 2026-09-08.

## Connections

- **Up:** [esapp](esapp.md) · [Home](../index.md)
- **Across:** [powerworld-simauto](powerworld-simauto.md) · [aux-script-commands](../references/aux-script-commands.md) (SCRIPT names) ·
  [esapp-overview](../methods/esapp-overview.md)
- **Exceptions to this rule:** [save-powerworld-case](../methods/save-powerworld-case.md) (COM `SaveCase` is a silent
  no-op; the *script* `SaveCase` is the one that writes)
- **Obsoleted by 0.2.1, needs re-check:** [converting-lines-to-transformers](../methods/converting-lines-to-transformers.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The rule

```python
pw.esa.TimeStepDoRun()                       # correct
pw.esa.RunScriptCommand("TimeStepDoRun;")    # wrong
```

Applies to every SCRIPT command esapp wraps: 310 named methods across 20 SAW mixins in
0.2.1, covering roughly 300 of the ~370 SCRIPT actions Simulator defines.

### Why — the actual mechanism

Both forms end at the same COM call. `SAWBase._run_script` (`esapp/saw/base.py:185`) is
a thin builder:

```python
arg_list = list(args)
while arg_list and arg_list[-1] is None:   # strip trailing Nones
    arg_list.pop()
stmt = f"{command}({arg_str});" if arg_list else f"{command};"
return self.RunScriptCommand(stmt)
```

`TimeStepDoRun` (`saw/timestep.py:10`) is
`self._run_script("TimeStepDoRun", start_time or None, end_time or None)`. The wrapper does
nothing special at the COM boundary. The win is three ordinary things:

1. **The signature is checked in Python, before COM.** `TimeStepDoRun(start_time: str =
   "", end_time: str = "")` is typed. A wrong arg count is a `TypeError` on your machine,
   not a misbehaviour inside Simulator.
2. **The argument string is built correctly.** Trailing-`None` stripping, `format_list()`
   bracket lists with proper quoting, `format_filter()` and the `_enums` types
   (`FilterKeyword`, `SolverMethod`, `TSGetResultsMode`, …), so a bogus filter name or
   solver method cannot reach PowerWorld. Hand-rolled f-strings get this wrong.
3. **One patch point.** When PowerWorld changes a command's syntax, the fix lands in
   esapp and `pip install -U esapp` repairs every call site at once. A hand-written
   string is a call site the maintainer can never reach.

### What it does NOT do — do not overclaim this

esapp does **not** introspect PowerWorld's live command table, does **not** check the
installed Simulator version, and does **not** auto-correct a stale command at runtime.
Confirmed byte-identical in `_run_script` across 0.1.3 and 0.2.1. The guarantee is an
**upgrade path, not a runtime check.**

A hand-written string does not fail silently *if PowerWorld reports an error*: `_com_call` (`saw/base.py:378-387`) raises
`PowerWorldError` on any non-empty error string, specialised by
`PowerWorldError.from_message` into `SimAutoFeatureError`, `PowerWorldPrerequisiteError`,
or `PowerWorldAddonError`. The dangerous case is narrower: **a
command whose name stays valid but whose parameter order or meaning changes.** The string
"succeeds" and does the wrong thing. That is what the typed wrapper prevents.

(`CommandNotRespectedError` was **removed in 0.2.0**. Do not reference it.)

### When `RunScriptCommand` is correct

Only when no named wrapper exists. About 41 of the catalogued actions have none,
largely oneline/GUI actions (`OpenOneline`, `ExportOneline`, `Animate`), dialogs
(`MessageBox`, `ObjectFieldsInputDialog`), and a few writers
(`ATCWriteToExcel`, `SaveDataUsingExportFormat`).

Look the command up in the **SCRIPT command → esapp method index** at the bottom of
esapp's own method list before concluding one is missing. Absence from
[aux-script-commands](../references/aux-script-commands.md) proves nothing, since that
page is a task-organized working subset rather than a complete index.

Leave a comment saying why whenever you do call `RunScriptCommand`.

### Exception: `SaveCase` — the script command beats the COM method

[save-powerworld-case](../methods/save-powerworld-case.md) is live-probed and still stands: `pw.esa.SaveCase(...)` is a
**silent no-op** on this machine (returns `None`, raw COM returns `('',)` = success, no
file appears), while the aux script form writes:

```python
pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')   # exactly 2 params
assert os.path.exists(out), "SaveCase reported success but wrote nothing"
```

There is no contradiction. esapp routes `SaveCase` through `_com_call`, not
`_run_script`, so it is not one of the 310 SCRIPT wrappers this rule governs. The rule
says *prefer the named wrapper over a hand-written string for the same command*; here the
COM method and the script command are different code paths with different behaviour, and
the script path is the one that works. Same for `OpenCase`/`CloseCase` being absent from
the SCRIPT index.

### Related: 0.2.1 turned a write-time `ValueError` into a warning

A different rule from the same philosophy: esapp treats PowerWorld as the authority and
does not let its own generated schema block you.

Through 0.1.x, writing an unknown or read-only column raised
(`indexable.py:228`, `:280`):

```
ValueError: Cannot set read-only field(s) on Branch: [...]
```

In 0.2.1 that became `warnings.warn` and **the write is still attempted**
(`indexable.py:198-210`): *"PowerWorld is the authority, and the generated schema may lag
the installed Simulator version."*

Two consequences:

- **A field-name typo no longer raises.** `pw[Gen, "GenMWW"] = 100` emits a warning to
  stderr and writes nothing useful. This joins the same silent-no-op
  family as dropping an object's key fields ([applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md)) and as
  the COM `SaveCase` above: the call reports success and the effect never happens.
  **Do not reach for `python -W error::UserWarning` to fix this.** That was the advice
  here through 2026-09-09, and it backfires because the *same* warning fires on ~150
  fields that write perfectly well (below). Assert the effect instead: read the field back
  and compare.
- **`Read-only field(s)` is usually a false alarm.** The flag comes from esapp's generated
  schema, which keeps only fields whose `enterable` is an unconditional `Yes` and discards
  every conditional one. PowerWorld's own answer for `LineStatus` is *"Depends: Normally
  enterable except when field Lockout is YES"*, so esapp calls it read-only and the write
  works anyway. Counted against build 2026-07-22: **112 Branch fields, 33 Bus, 5 Gen
  (including `GenMVR`), 1 Load** are enterable in PowerWorld but `is_settable() == False`.
  The authority is `pw.esa.GetFieldList(<type>)`, whose `enterable` column is PowerWorld's,
  not esapp's.
- **The `XF*` bypass in [converting-lines-to-transformers](../methods/converting-lines-to-transformers.md) is now confirmed
  unnecessary.** ✅ **Verified live 2026-09-10** on a ~2,000-bus synthetic case, Simulator build 2026-07-22,
  esapp 0.2.1: `pw[Branch] = df` carrying `LineXFMR='YES'` warns and goes through:
  `BranchDeviceType` flips `Line` → `Transformer`, on a 2-row subset, no exception. That
  page has been rewritten accordingly.

### Provenance

Author feedback relayed by the author, 2026-09-08. Verified against the esapp 0.2.1 source
(`github.com/lukelowry/ESApp`, `VERSION` 0.2.1, 2026-09-01) and diffed against the 0.1.3
build then installed in site-packages. The readthedocs `api/saw.html` page states none of
this; it documents `RunScriptCommand` neutrally, so this page is the only written record of
the rule.


---

# ==== esapp.md ====

---
type: tool
domain: tooling
topic: scripting
aliases: [ESA++, esa_pp, esapp-api]
tags: [esapp, powerworld, simauto, python, tool]
---

# ESA++ (esapp) — tool reference

## Abstract

`esapp` (ESA++) is a Python toolkit that gives a Pythonic, pandas-flavored interface to PowerWorld Simulator's Automation Server (SimAuto) over COM. It is Windows-only and requires PowerWorld locally. This page is the full API map: top-level imports, architecture (mixin-built `SAW`, `PowerWorld` workbench, embedded modules), the bracket read/write interface, all `pw.*` methods, transient-stability helpers, and the GObject schema accessors. For how to drive it in practice, start at [esapp-overview](../methods/esapp-overview.md).

## Connections

- **Up:** [Home](../index.md)
- **Across:** [powerworld-simauto](powerworld-simauto.md) · [esapp-overview](../methods/esapp-overview.md) · [timestep-simulation](timestep-simulation.md) · [gic](gic.md)
- **Field schema + commands:** [esapp-schema-reference](../references/esapp-schema-reference.md) — exact object key/identifier fields + SimAuto command catalog for writing esapp code
- **SCRIPT action catalog:** [aux-script-commands](../references/aux-script-commands.md) — task-organized PowerWorld SCRIPT commands, for anything not yet wrapped by a named SAW method
- **House rule for calling them:** [esapp-script-command-wrappers](esapp-script-command-wrappers.md) — call `pw.esa.TimeStepDoRun()`, never `RunScriptCommand("TimeStepDoRun;")`; also the 0.2.1 change that made a bad write warn instead of raise

## Content

esapp talks to SimAuto (see [powerworld-simauto](powerworld-simauto.md)) through `pywin32`
for COM interop, hence **Windows-only**.

> Source of truth: `C:\path\to\esapp`. Every symbol below was
> read out of that tree. Validate against `esapp` source (or the `esapp` skill)
> before shipping any `methods/` page that calls the API.

## Top-level imports

```python
from esapp import PowerWorld          # main entry point
from esapp import SAW                 # low-level SimAuto wrapper (usually via pw.esa)
from esapp import TS, TSField         # transient-stability field constants
from esapp.components import Bus, Gen, Load, Branch, Shunt, Area, Zone  # GObject types
from esapp.utils import TSWatch, ContingencyBuilder, SimAction, BranchType  # helpers
```

`esapp/__init__.py` exports `PowerWorld`, `SAW`, `TS`, `TSField`, and the
exception hierarchy (`PowerWorldError`, `COMError`, `SimAutoFeatureError`,
`PowerWorldPrerequisiteError`, `PowerWorldAddonError`). `CommandNotRespectedError` was
**removed in 0.2.0** — do not reference it.
`TSWatch` / `ContingencyBuilder` are **not** top-level — import them from
`esapp.utils`.

## Architecture (real)

- **`PowerWorld`** — `esapp/workbench.py`. The user-facing class; subclass of
  `Indexable`. Holds the live SimAuto connection on `pw.esa` and three embedded
  application modules: `pw.network`, `pw.gic`, `pw.buscat`.
- **`Indexable`** — `esapp/indexable.py`. Implements the bracket read/write
  interface (`__getitem__` / `__setitem__`) and `open()`.
- **`SAW` (SimAuto Wrapper)** — `esapp/saw/saw.py`. Built by the **mixin
  pattern** from `SAWBase` (`saw/base.py`) plus ~20 focused mixins:
  `DataMixin`, `PowerflowMixin`, `MatrixMixin`, `ContingencyMixin`,
  `TransientMixin`, `SensitivityMixin`, `GICMixin`, `OPFMixin`, `PVMixin`,
  `QVMixin`, `ATCMixin`, `FaultMixin`, `TopologyMixin`, `RegionsMixin`,
  `ModifyMixin`, `GeneralMixin`, `CaseActionsMixin`, `ScheduledActionsMixin`,
  `TimeStepMixin`, `WeatherMixin`. This is the raw COM layer, reached via
  `pw.esa`.
- **Components** — `esapp/components/`. `grid.py` (auto-generated, large) holds
  a `GObject` subclass per PowerWorld object type; `ts_fields.py` holds the
  `TS` / `TSField` constants; `gobject.py` is the base class;
  `generate_components.py` regenerates both from the `PWRaw` TSV schema. **Do
  not hand-edit `grid.py` / `ts_fields.py` — regenerate them.**
- **Utils** — `esapp/utils/`: `network.py` (`Network`), `gic.py` (`GIC`),
  `dynamics.py` (`TSWatch`, TS result processing), `contingency.py`
  (`ContingencyBuilder`, `SimAction`), `b3d.py` (`B3D` field-file I/O),
  `buscat.py` (`BusCat`).
- **Enums / descriptors / exceptions** — `saw/_enums.py` (`SolverMethod`,
  `JacobianForm`, `LinearMethod`, `PowerWorldMode`, filter keywords, …),
  `_descriptors.py` (`SolverOption`, `GICOption` descriptors), and
  `saw/_exceptions.py` (`PowerWorldError` hierarchy).

## Bracket data interface (the core idiom)

```python
pw[Bus]                              # primary-key columns only
pw[Bus, "BusPUVolt"]                 # keys + one field
pw[Gen, ["GenMW", "GenMVR", "GenStatus"]]   # keys + several
pw[Bus, :]                           # keys + EVERY defined field
```

Reads go through `esa.GetParamsRectTyped` and return a typed `DataFrame`.
Writes use the same brackets:

```python
pw[Gen, "GenMW"] = 100.0             # broadcast scalar to existing gens
pw[Gen, "GenMW"] = [100, 150, 200]   # per-element list
pw[Bus] = df                         # bulk update from a DataFrame (must carry primary keys)
pw[Gen, "GenStatus"] = True          # bools are serialized -> "Closed" (0.2.1)
```

**Status fields accept Python bools** as of 0.2.1. `_serialize_bools` maps them through
`BOOL_FIELD_VOCAB` (`components/gobject.py:39`), so you no longer have to remember which
string a given field wants:

| Field | `True` | `False` |
|---|---|---|
| `GenStatus`, `LineStatus`, `LoadStatus`, `SSStatus` | `Closed` | `Open` |
| `BusStatus` | `Connected` | `Disconnected` |
| `BusSlack`, `GenAGCAble`, `GenAVRAble` | `YES` | `NO` |

Indexed variants resolve to their base name, so `LineStatus:1` works too. A bool aimed at
an **unregistered** field raises `ValueError` rather than guessing. Pass PowerWorld's
string, or add the field to `BOOL_FIELD_VOCAB`. The plain strings still work everywhere,
and most pages in this kit still use them.

`pw[Type] = df` can also **create** objects when the case is in EDIT mode and
the SAW was opened with `CreateIfNotFound=True`.

> ⚠️ **Changed in 0.2.1.** Unknown and read-only columns used to raise
> `ValueError: Cannot set read-only field(s)` (`indexable.py:228`/`:280` in 0.1.x). They
> now emit a `warnings.warn` and the write is **still attempted**. PowerWorld is treated
> as the authority, so a lagging generated schema can't block a newer Simulator's fields.
> The cost is that a field-name typo no longer raises.
> See [esapp-script-command-wrappers](esapp-script-command-wrappers.md).

> 🚫 **Do not run `python -W error::UserWarning` to get the old strictness back.** That
> advice was here through 2026-09-09 and it is wrong: esapp's read-only flag is a *stale
> generated whitelist*, not PowerWorld truth, so promoting the warning to an error breaks
> writes that work. Measured on Simulator build 2026-07-22, the count of fields PowerWorld
> reports as enterable but `is_settable()` calls read-only: **112 on Branch, 33 on Bus,
> 5 on Gen (including `GenMVR`), 1 on Load**. `pw[Branch, 'LineStatus'] = 'Open'` warns,
> succeeds on all 3950 branches, and dies under `-W error`. PowerWorld's own answer for
> `LineStatus` is *"Depends: Normally enterable except when field Lockout is YES"*; esapp
> drops every conditional field. To check settability, ask PowerWorld, not the schema:
>
> ```python
> fl = pw.esa.GetFieldList('branch')          # authoritative
> fl[fl.internal_field_name == 'LineStatus'][['enterable']]
> ```
>
> Catch typos by asserting the *effect* (read the field back and compare), as everywhere
> else in this kit.

> ⚠️ **Key fields are mandatory for writes.** PowerWorld matches each row back to an
> object by its **key field(s)** (e.g. `BusNum`+`GenID` for a Gen). The bracket read
> includes the keys automatically, so a read-modify-write round-trip keeps them. If
> you build a DataFrame by hand, or drop columns, it **must still carry the key columns**
> or the write silently does nothing (no error, no change applied). On the raw `esa`/SAW
> path you must prepend them yourself: `Gen.keys() + [<fields>]` (or read them off
> PowerWorld with `pw.esa.GetFieldList('gen')`, whose `key_field` column marks them
> `*1*`, `*2*`, …). Rule of thumb: never strip key columns from a DataFrame you intend
> to push back.
>
> `pw.esa.get_key_field_list(...)` does **not** exist. It was named here in error through
> 2026-09-09 and raises `AttributeError`.

## PowerWorld API surface (`pw.*`, from workbench.py)

- **State / case** — `pw.open()`, `pw.save(filename=None)` ⚠️ **silent no-op, see below**,
  `pw.close()`, `pw.edit_mode()`, `pw.run_mode()`, `pw.flatstart()`, `pw.snapshot()`
  (context manager: `SaveState` on enter, `LoadState` on exit),
  `pw.log(msg)`, `pw.print_log(...)`.

> 🚫 **`pw.save()` writes nothing and reports success.** It is a one-line passthrough to
> `self.esa.SaveCase(filename)`, so it inherits the `SaveCase` no-op documented in
> [save-powerworld-case](../methods/save-powerworld-case.md); this is the same trap, not
> a second one. The no-op is below esapp: the raw COM call
> `SimAuto.SaveCase(path, "PWB", True)` returns `('',)` (SimAuto's success convention) and
> creates no file. Measured on build 2026-07-22, absolute path, both slash styles.
> Use the script form and assert the file exists:
>
> ```python
> pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
> assert os.path.exists(out), "SaveCase reported success but wrote nothing"
> ```
- **Solve** — `pw.pflow(getvolts=True, method=SolverMethod.POLARNEWT)` returns a
  complex voltage Series; `pw.ts_solve(ctgs, fields)` runs transient stability
  and returns `(metadata, timeseries)` DataFrames. That is outside what these pages cover;
  see the note under *Transient stability* below.
- **Voltages / power** — `pw.voltage(complex=True, pu=True)`,
  `pw.set_voltages(V)`, `pw.mismatch(asComplex=False)`, `pw.netinj(...)`,
  `pw.violations(v_min=0.9, v_max=1.1)`.
- **Matrices / topology** — `pw.ybus(dense=False)`,
  `pw.jacobian(dense=False, form=JacobianForm.RECTANGULAR, ids=False)`,
  `pw.busmap()`, `pw.buscoords(astuple=True)` (returns a `(Longitude,
  Latitude)` tuple by default — **not** a DataFrame).
- **Convenience tables** — `pw.gens()`, `pw.loads()`, `pw.shunts()`,
  `pw.lines()`, `pw.transformers()`, `pw.areas()`, `pw.zones()`,
  `pw.flows()`, `pw.overloads(threshold=100.0)`.
- **Sensitivities** — `pw.ptdf(seller, buyer, method=LinearMethod.DC)`,
  `pw.lodf(branch, method=LinearMethod.DC)`.
- **Quick props** — `pw.n_bus`, `pw.n_branch`, `pw.n_gen`, `pw.sbase`,
  `pw.summary()` (dict of counts + totals + v_min/v_max).
- **Solver options as descriptors** — set them like attributes:
  `pw.max_iterations = 30`, `pw.convergence_tol = 1e-4`, … (each is a `SolverOption`
  mapping to a PowerWorld Sim_Solution_Options field). ⚠️ `pw.dc_mode = True` and
  `pw.flat_start = True` exist too, but a scripted solve ignores both (live-tested
  2026-09-23). Use `pw.pflow(method="DC")` for a DC solve and `pw.flatstart()` for a flat
  start (see [handling-errors](../methods/handling-errors.md)).

## Embedded modules

- **`pw.network`** (`utils/network.py`) — `incidence()`, `laplacian(weights,
  ...)`, `lengths()`, `zmag()`, `ybranch()`, `yshunt()`, `gamma()`, `delay()`,
  `busmap()`, `buscoords()`; `BranchType.{LENGTH, RES_DIST, DELAY}` weighting.
- **`pw.gic`** (`utils/gic.py`) — `configure()`, `storm(maxfield, direction,
  solvepf=True)`, `model()`, `gmatrix(sparse=True)`, `settings()`,
  `cleargic()`, `loadb3d()`, `timevary_csv()`; result matrices on properties
  `A, G, H, zeta, Px, eff`; options via descriptors `pf_include`, `efield_mag`,
  `efield_angle`, `calc_mode`, … See [gic](gic.md).
- **`pw.buscat`** (`utils/buscat.py`) — bus classification.

## Transient stability (TS)

> ⚠️ **"TS" disambiguation — do not conflate.** Here `TS` = **Transient Stability**: a
> dynamics study of faults, generator trips, rotor angles, and frequency over
> milliseconds-to-seconds (`pw.ts_solve`, `TSWatch`, `ContingencyBuilder`, `TS.*` field
> constants). This is **unrelated** to PowerWorld's **TimeStep** weather feature (`.pww`
> weather → hourly solar/wind MW), which uses the low-level `esa` `TimeStep*` script
> commands, NOT this `ts_solve` API. The shared letters are a coincidence; the
> `TSPFWModelString` field's "TS" likewise means *TimeStep*, not Transient Stability.

> 🚫 **Transient stability is outside what these pages cover** (see *Reporting back* in
> `AGENTS.md`). The API below is listed so you can recognise it, not as a recipe. If asked
> for a transient stability study, say it is out of scope and stop; do not run `ts_solve`.

```python
from esapp.utils import TSWatch, ContingencyBuilder
tsw = TSWatch().watch(Gen, [TS.Gen.P, TS.Gen.W])
fields = tsw.prepare(pw)
ctg = ContingencyBuilder("GenTrip", runtime=5.0).at(1.0).fault_bus("101").at(1.1).clear_fault("101")
meta, data = pw.ts_solve("GenTrip", fields)
```

`TSWatch` registers result fields; `ContingencyBuilder` fluently builds transient-stability
event sequences (`SimAction` enum). For dynamics studies only; see [powerworld-simauto](powerworld-simauto.md)
for the underlying `TransientMixin`.

## GObject schema access

Every component class exposes `@classmethod` schema accessors (call with `()`):
`Bus.TYPE()`, `Bus.keys()`, `Bus.fields()`, `Bus.secondary()`,
`Bus.editable()`, `Bus.identifiers()`, `Bus.settable()`.

## Used across

[timestep-simulation](timestep-simulation.md) and most other PowerWorld work in this knowledge base
route through it.

## Related

- How-to entry: [esapp-overview](../methods/esapp-overview.md) · underlying COM server: [powerworld-simauto](powerworld-simauto.md)
- Writing devices + DC OPF + N-1 (write-side mechanics): [adding-devices-esapp](../methods/adding-devices-esapp.md)


---

# ==== gic.md ====

---
type: concept
domain: tooling
topic: power-flow
aliases: [gic, geomagnetically-induced-current, gmd, geomagnetic-disturbance]
tags: [gic, gmd, powerworld, esapp, transformer, solar-storm]
---

# Concept: GIC — geomagnetically induced current

## Abstract

Geomagnetically induced currents are quasi-DC currents driven into the grid during a
geomagnetic disturbance, flowing through long transmission lines and transformer
neutrals. They cause half-cycle transformer saturation, harmonics, reactive-power
absorption, and in severe cases thermal damage. PowerWorld models GIC natively, and
`esapp` exposes it through `esapp.utils.GIC`. Verified against esapp 0.1.3.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) · [glossary](glossary.md)
- **Deeper:** [aux-script-commands](../references/aux-script-commands.md) for the underlying `GIC*` SCRIPT actions

## Content

### The physics, briefly

A changing geomagnetic field induces a geoelectric field at the earth's surface. That
field drives quasi-DC current through any long conductor grounded at both ends, which
describes a transmission line with grounded-wye transformers at each end.

The current is quasi-DC relative to 60 Hz, so it biases the transformer core into
half-cycle saturation. Consequences, in the order they usually matter:

- **Reactive power absorption** rises sharply, depressing voltage
- **Harmonics** appear and can trip protective relays
- **Transformer heating**, which is the damage mechanism in a severe storm

### The API, and the mistake to avoid

**There is no `pw.gic`.** GIC lives in `esapp.utils` as a class you construct with the
`PowerWorld` object:

```python
from esapp import PowerWorld
from esapp.utils import GIC

pw = PowerWorld(r"C:\path\to\case.pwb")
g = GIC(pw)
```

Then:

```python
g.configure(pf_include=True, ts_include=False, calc_mode="SnapShot")
g.storm(maxfield=100.0, direction=90.0, solvepf=True)   # V/km, degrees
g.model()                                               # build the GIC model
G = g.gmatrix(sparse=True)                              # conductance matrix
```

Verified signatures:

| Call | Signature |
|---|---|
| `GIC(pw)` | `__init__(self, pw=None)` |
| `configure` | `(pf_include: bool = True, ts_include: bool = False, calc_mode: str = 'SnapShot') -> None` |
| `storm` | `(maxfield: float, direction: float, solvepf: bool = True) -> None` |
| `model` | `() -> GIC` |
| `gmatrix` | `(sparse: bool = True) -> csr_matrix | ndarray` |

### Other settings on the object

The `GIC` object exposes the modelling knobs as attributes rather than arguments:

| Attribute | Controls |
|---|---|
| `efield_mag`, `efield_angle` | The geoelectric field magnitude and direction |
| `min_kv` | Voltage floor below which branches are excluded |
| `skip_low_r_lines`, `skip_equiv_lines` | Exclude low-resistance or equivalenced branches |
| `segment_length_km` | Line segmentation length for the field integral |
| `hotspot_include` | Include transformer hot-spot heating |
| `pf_include`, `ts_include` | Couple GIC into the power flow and/or transient stability |
| `calc_mode` | `SnapShot` and related calculation modes |
| `zeta`, `eff`, `Px` | Model coefficients |
| `bus_no_sub` | Buses without an assigned substation |
| `update_line_volts` | Whether induced line voltages are refreshed |
| `timevary_csv`, `loadb3d` | Time-varying field input and B3D field data |
| `calc_max_direction` | Solve for the worst-case field direction |
| `A`, `G`, `H` | The assembled model matrices |
| `cleargic` | Clear GIC results |

### Substation grounding is the input that matters most

GIC results are dominated by substation grounding resistance and transformer winding
configuration. A case that has never been prepared for GIC study will have placeholder
grounding data, and it will still produce plausible-looking, meaningless numbers.

Before trusting any GIC result, confirm the case actually carries substation grounding
resistances and correct transformer configurations. Nothing errors; the answer is just
not about your system.

### Direction matters, and the worst case is not obvious

GIC magnitude depends on the angle between the geoelectric field and each line. The
worst direction for one transformer is rarely the worst for another, so a single
assumed direction under-reports system risk. Use `calc_max_direction` rather than
guessing, or sweep the direction and keep the envelope.

### Script-level access

Everything above maps to PowerWorld `GIC*` SCRIPT actions: `GICCalculate`,
`GICTimeVaryingCalculate`, `GICSaveGMatrix`, and the PTI/PSLF exchange actions. See
[aux-script-commands](../references/aux-script-commands.md). Reach for those only when the `esapp.utils.GIC` surface does
not cover what you need.

### Scope

This page covers **driving PowerWorld's GIC feature**. It does not teach geomagnetic
hazard assessment, earth-conductivity modelling, or how to choose a storm scenario. For
those, go to the GMD literature and the relevant NERC standards.


---

# ==== glossary.md ====

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


---

# ==== gsu-outages-in-n1.md ====

---
type: concept
domain: synthetic-grid
topic: contingency
aliases: [gsu-outages-in-n1, gsu-contingencies, double-gsu, twin-gsu, parallel-gsu, generator-step-up-outage]
tags: [synthetic-grid, contingency, n-1, gsu, transformer, voltage]
---

# GSU outages in a transmission N-1: double every step-up, or leave them out

## Abstract

Two ways to treat generator step-up (GSU) outages in a transmission N-1 list: give every single GSU an identical
twin and keep all GSU outages, or leave GSU outages out. Measured on one case, both fail on the same transmission
outages. Twins cost base-case high voltage and a point or two of loading; leaving them out never tests a GSU outage.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [fixing-plant-islands-from-single-outages](../methods/fixing-plant-islands-from-single-outages.md) (the topology screen that sets GSU outages aside) ·
  [gsu-tap-vs-generator-voltage-control](gsu-tap-vs-generator-voltage-control.md) (why twins get a fixed tap) ·
  [agc-participation-factors](agc-participation-factors.md) (who covers a tripped unit's MW) ·
  [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md) (the loop both variants feed)

## Content

### The question

An auto-inserted N-1 list holds every branch, and the step-up between a unit and the grid is a branch. Losing a
single GSU strands its unit, so its outage is really a **generator outage**, which NERC TPL-001 counts as a single
contingency (P1) of its own. The two clean options:

| | A: double every single GSU | B: leave GSU outages out |
|---|---|---|
| Network | +1 twin per single-GSU plant: identical R, X, B, ratings, MVA base, a fixed tap equal to the original's, automatic tap control off | unchanged |
| Contingency list | every GSU outage kept, plus one per twin | GSU outages deleted |
| What a GSU outage tests | that the twin carries the plant alone | nothing; add a separate one-per-unit generator-outage set |

### Measured: both fail on the same transmission outages

Full AC N-1, five dispatches, on a ~9k-bus synthetic case, both variants built from one shared base
(2026-10-20). Same settings in both: Rate A and 0.94–1.05 pu before an outage, Rate B and 0.90–1.10 pu after,
Gen Part Factors make-up, island handling on.

- **The same failing outages, in the same dispatches.** The list of outages with a real violation or no solve was
  identical in both. Every unsolved outage in either was an island at RESERVE LIMITS; none diverged.
- **Variant A's GSU outages were all non-events.** Original and twin outages solved in every dispatch, stranded no
  unit and raised no network violation.
- **Twins cost voltage.** Halving each GSU's impedance lets a unit hold its regulated high side with less Mvar, so
  fewer units sit at Qmax, more sit at Qmin, and the base-case high-voltage count rose by about a third (bus-dispatch
  pairs above 1.05 pu summed over five dispatches; worst bus +0.003 pu).
- **Twins add a point or two of loading** on the worst post-outage branches, and the worst post-outage high voltage
  rose by up to 0.007 pu.
- **Variant B never tests a GSU outage.** On an earlier build of the same case, GSU outages tripped units that left
  the main grid short of AGC headroom, and one islanded a pocket. That was not re-measured on this base.
- **Size:** A adds roughly one branch in eleven and about a fifth more outages per dispatch.

### Build either one by script from a shared base

Every network fix goes on one shared base, and A and B are rebuilt from it by script, so the choice can change at
any time. A twin is made with `CreateData` from the original's fields (no `ObjectID` carried), in batches with a
warm solve after each, plus a new contingency per twin in the case's label format. Read every twin back on a cold
reopen: present, a transformer, and no GSU bus pair left with one unit. Each GSU then carries half its plant, and
the slack's output drops slightly because GSU losses halve.

### Two cases to handle whatever the choice

- **The slack must not sit behind one GSU.** If it does, that GSU's outage leaves the slack alone in an island in
  every dispatch. Twin the slack's GSU in both variants. Moving the slack instead only works onto a unit with room
  both up and down in every dispatch.
- **Several units behind one GSU.** Its outage trips them all together, which is a multi-unit generator loss.
  Screen those plants separately; [fixing-plant-islands-from-single-outages](../methods/fixing-plant-islands-from-single-outages.md) lists them apart.

### Which to pick

The measurement does not settle it. Either way: add a one-per-unit generator-outage set, since P1 includes single generator
loss and variant B otherwise tests none.


---

# ==== gsu-tap-vs-generator-voltage-control.md ====

---
type: concept
domain: synthetic-grid
topic: power-flow
aliases: [gsu-tap-control, gsu-ltc, generator-voltage-control, one-controller-per-bus, fixed-gsu-tap]
tags: [synthetic-grid, gsu, transformer, tap, ltc, voltage, generator, convention]
---

# GSU tap control vs generator voltage control

## Abstract

Who regulates voltage at a plant: the step-up's tap changer or the generator? The planning convention is a fixed
GSU tap with the generator regulating one bus, and exactly one automatic controller per regulated bus. Covers the
evidence, per-class rules, how to pick the fixed tap, and what stays open. Most of it is [Likely], not [Certain].

## Connections

- **Up:** [Home](../index.md)
- **Across:** [ltc-regulation-checks](../methods/ltc-regulation-checks.md) (checking what each tap regulates) ·
  [gsu-outages-in-n1](gsu-outages-in-n1.md) (twins copy the fixed tap)

## Content

### The convention

1. **Real GSUs are mostly fixed-ratio.** Their taps are no-load (de-energized) taps, typically about ±5% in 2.5%
   steps, set at an outage. The generator's voltage regulator does the voltage work. [Likely]
2. **So the planning model runs GSU tap control off at a fixed tap, and the generator regulates one bus** (its
   terminal, or the GSU high side as a remote bus). [Likely]
3. **Exactly one automatic controller per regulated bus.** If a transformer keeps automatic control, its regulated
   bus must not be a bus a generator also regulates. Two controllers on one target fight, and in practice the
   machine pins at a reactive limit. [Likely]
4. **Inverter-based plants are the one exception worth a flag.** Many main power transformers have an on-load tap
   changer, but the plant controller at the point of interconnection is the regulator of record. Model the OLTC only
   where data says it exists, and only on the collector side. [Guessing on how common]

| Unit class | GSU tap | Transformer regulates | Generator regulates | Confidence |
|---|---|---|---|---|
| Thermal, hydro, nuclear | fixed (`XFAuto = NO`) | nothing | GSU high side (remote) or own terminal, one choice per fleet | Likely |
| Wind, solar, battery | fixed by default | collector side only, if an OLTC is kept | the POI or high-side bus, via the plant controller | Guessing |
| Synchronous condenser | fixed | nothing | own terminal or high side | Likely |
| Offline unit, any class | fixed, always | nothing | nothing | Certain |

### Evidence

- **A US ISO's public steady-state planning procedure manual** (2026 revision), section 4.5.1.8: control mode zero "prohibits
  automatic adjustment", and the controlled bus "should be non-zero only for voltage controlling transformers".
  No-load taps give ratios "usually in the range of 0.95 to 1.05"; automatic LTC ranges are "typically 0.80 to
  1.20". [Certain]
- **Same manual, section 4.3.5:** the GSU tap position, GSU tap control and the generator's remote regulated bus are
  all resource-registration data items. The manual models the GSU explicitly and gives the generator its own regulated-bus
  field, **but the manual never says what the tap control should be.** [Certain on the table; gap on the rule]
- **Section 4.3.4:** scheduled voltages "should reflect actual voltage set points used by the generator
  operators". [Certain]
- **NERC PRC-019 (draft revision):** defines the IBR main power transformer and makes the plant controller's
  voltage control act before protection trips, so the plant controller is the regulator of record. [Certain on the
  definition, Likely on the inference]
- **PowerWorld** has a remotely-regulated-bus view that lists every generator, transformer and shunt regulating a bus
  and flags mixed AVR status, so the conflict can be listed directly. Its transformer-control help covers parallel
  transformers fighting, not generator-plus-transformer. [Likely]
- **Measured on a ~9k-bus synthetic case (2026-10-11):** one outage failed with tap adjustment on and solved with it
  off. Bisection landed on twin offline-unit GSU LTCs, each regulating its own dead-end bus; locking the offline-GSU
  LTCs fixed it. A tap control on a dead unit has no physical meaning. [Certain]

### Picking the fixed tap

1. **Keep the solved tap.** Zero change to the solved case, but an offline unit's tap is wherever its LTC hunted
   to, which is arbitrary.
2. **Snap to the nearest real no-load step** (2.5% steps within 0.95–1.05). Matches equipment, and PSS/E and
   PowerWorld then agree on the same values.
3. **Centre the unit's reactive range:** the tap at which the unit sits mid-range at its typical dispatch and
   setpoint. Best N-1 headroom; costs a solve loop per unit.

Recommended: offline units at nominal; online units option 3, then rounded to option 2's step grid.

### Trade-offs to expect in review

- A fixed GSU cannot buck a post-contingency swing, so the generator reaches its Q limit sooner. Real units behave
  the same way, so this is realistic, not a defect.
- Fixed taps make bad tap data matter more: a wrong ratio keeps a unit at a Q limit all the time.
- "Keep the LTC and drop the generator's remote regulation" moves control onto a device real GSUs do not have, and
  does not match registration data, which lists a generator remote bus.

### Until the rule is settled

Lock every GSU tap at its solved tap. If locking every GSU tap and aligning setpoints still fails a full Newton
solve in another tool such as PSS/E, tap conflict was not the cause; switch controls off one class at a time instead.

Not found: a public GSU tap specification (IEEE C57.116 not reached), what PSS/E does with a tap and a generator on
one bus, IEEE 2800 guidance on OLTC coordination, and the ACTIVSg synthetic grids' own convention. The last one can
be read straight off Synth2k: for each transformer with a generator bus at one end, compare `XFAuto` and
`XFRegBus` with the generator's `GenRegNum`.


---

# ==== lodf.md ====

---
type: concept
domain: cross-cutting
topic: contingency
aliases: [lodf, line-outage-distribution-factor, line-outage-distribution-factors, ptdf, isf, dc-contingency-screening]
tags: [contingency, n-1, dcpf, lodf, ptdf, powerworld, esapp, screening, technique, cross-cutting]
---

# LODF — Line Outage Distribution Factors (DC N-1 in one factorization)

## Abstract

LODF gives every branch's post-outage MW flow for every single-branch outage from one
matrix factorization, with no per-contingency power-flow solve. Measured live, it **is** DC
contingency analysis, not an approximation of it (`corr = 1.00000000`, `max|err| = 0.0000 MW`
vs PowerWorld's own DC CTG), and ~190× faster. On Synth8k the full ~13k-outage table took
**5.8 s** versus **1,101 s** for the 10-worker parallel AC sweep
([parallel-contingency-solve](parallel-contingency-solve.md)). This page covers the mechanism,
the free islanding detector that falls out of it, what it structurally cannot do (voltage,
reactive power, losses, control limits, divergence), and why it was **evaluated and NOT
adopted** for reactive power planning: that work's binding constraint is local reactive
adequacy, not MW redistribution.

## Connections

- **Up:** [Home](../index.md)
- **Measured in:** a reactive planning study, 2026-08-10, in a LODF-versus-contingency
  comparison. **Measured and rejected** for the removal-stage screen; see the verdict below.
- **💡 Could apply to (idea transfer):**
  a conductor-resizing study, whose 70-iteration DCPF resizing loop is a pure MW problem
  (N-1 flows for every candidate resize with no extra solves) ·
  dynamic line rating, where Impact×Likelihood branch screening needs post-outage loading,
  which is a LODF column ·
  synthetic-grid validation, as an N-1-secure-by-construction check on synthetic cases (see below)
- **Across:** [parallel-contingency-solve](parallel-contingency-solve.md) (what you still need when the question is
  voltage, not MW) · [esapp](esapp.md) (topology + base flows come from here) ·
  [powerworld-simauto](powerworld-simauto.md) (the COM server; see the `SetData` / `dc_mode` traps below)

## Content

### The idea

Contingency analysis **simulates**: open branch k, re-solve the whole network with
Newton-Raphson, read the result. LODF **precomputes the redistribution**.

It works because DC power flow is linear (`f = H·P`: angles and reactances only, no
voltage magnitude, no reactive power, no losses), and linear systems obey superposition.

Instead of removing branch k, leave it in place and inject power at its two endpoints that
exactly cancels its flow. A branch carrying zero current may as well be absent, so the two
are electrically identical. The response to an injection can be precomputed once (that is
what PTDF/ISF is), so knowing the response to injections gives you the response to every
outage.

### The formula

```
f_l(after k trips)  =  f_l  +  LODF[l,k] · f_k
                                └──────┘   └─┘
                                 share    orphaned flow
```

`LODF[l,k]` is the fraction of the **outaged** branch's flow that lands on branch `l`, not a
percentage increase of `l`'s own flow. Column `k` is the whole grid's response to losing
`k`, so one column answers "what happens everywhere."

**The danger is the product `LODF × f_k`, not the factor alone.** A 0.20 share of a 100 MW
line adds 20 MW; the same 0.20 share of a 400 MW line adds 80 MW. LODF is also **signed**,
so always evaluate `|f_new| / limit`.

Where the shares come from:

```
LODF[l,k] = ψ[l,k] / (1 − ψ[k,k])          ψ = diag(b)·A·Xbus   (the ISF / PTDF matrix)
```

The denominator is a feedback term. When k's power pushes onto its neighbours, their
changes feed back onto k's own terminals, which pushes again. Expanded,
`1/(1−ψ_kk) = 1 + ψ_kk + ψ_kk² + …`, a geometric series that sums every round of
redistribution in closed form.

### Free islanding detection

When `ψ_kk → 1` the denominator goes to 0 and the shares blow up. Physically, the feedback
never damps because there is no alternate path: outaging `k` splits the network. The math
flags it before any solve. On Synth8k, **about 3%** of outages (roughly 1 in 30) were found
this way in the ~6 s it takes to build the PTDF.

This fixes correctness, and it plugs a real hole. In a PowerWorld CTG sweep, islanded buses
read 0 and get skipped, so stranding a 138 kV pocket **reports CLEAN in `ViolationCTG`**.
PowerWorld does record it elsewhere (`Contingency.LoadMW` / `GenMW` and the *Island Solved*
rows of `CTG_Options.Include`, see
[reading-violationctg](../methods/reading-violationctg.md)), but only for whoever reads those.
A free connectivity check turns it into an explicit list before any solve.

### Building it (measured recipe, Synth8k: ~8k buses / ~13k branches)

```
A     = incidence (L×N, +1 from / −1 to)      b = 1/x, floor |x| at 1e-5
B'    = Aᵀ·diag(b)·A , delete the slack row/col, factorize (scipy splu)   ~6 s
Xbus  = B'⁻¹ (slack row/col zero-filled)
ψ     = diag(b)·A·Xbus                        (L×N = 0.91 GB float64)
Φ[:,k]= ψ[:,from_k] − ψ[:,to_k]               → LODF[:,k] = Φ[:,k] / (1 − Φ[k,k])
```

Φ is just column differences of ψ at the branch endpoints, which is cheap. Stream the L×L
table in column chunks (512 works) and accumulate statistics rather than materialising it
(0.73 GB in float32 if you do want it whole).

**Take base flows from PowerWorld's own DC solve. Do not reconstruct the injection vector.**
On a real case, generation exceeds load by the AC loss provision (several GW on Synth8k). A
hand-built `P` dumps that entire imbalance on the single slack bus while PowerWorld
distributes it, giving a **220 MW max discrepancy**. LODF needs only base flows + topology,
so reading the base flows removes the question. A DC solve is still shunt-blind, so the
property that makes this usable for siting work survives.

### Measured verdict (Synth8k, 2026-08-10)

**1 — LODF *is* DC contingency analysis, exactly.**

| | |
|---|---|
| LODF vs PowerWorld DC CTG | `corr = 1.00000000`, `max\|err\| = 0.0000 MW` |

Within DC's linear world, "delete the branch and re-solve" and "apply the compensating
injection by superposition" are the same algebraic operation (Sherman–Morrison). Same
answer, far less arithmetic.

**2 — Cost.**

| Method | Full ~13k-outage sweep |
|---|---|
| **LODF** (+6.0 s PTDF, once per topology) | **5.8 s** |
| PowerWorld DC, serial | 2,106 s |
| PowerWorld AC, serial | 6,025 s |
| PowerWorld AC, 10-worker parallel | 1,101 s |

PTDF depends only on topology, so it is built once and reused. **Each additional scenario
costs one matrix-vector product**, not another sweep, which answers "more scenarios =
linearly more time."

**3 — Rank fidelity vs AC is high, and the residual is DC's fault, not LODF's.**

```
per-substation stress, Spearman:   ρ(LODF, AC) = 0.9929
                                   ρ(PW_DC, AC) = 0.9929   ← identical to 4 dp
top-k set agreement (LODF vs AC):  top 5% J=0.936 · top 22% J=0.920 · top 50% J=0.955
```

LODF loses nothing versus running the real DC sweep. The whole gap to AC is the DC/AC
modelling gap (base flows: `corr 0.981`, mean 5.5 MW, **8.5 % mean relative**).

**4 — Predicting individual AC flow *changes* is mediocre**, and again identical for both:

| mover threshold | 1 MW | 5 | 10 | 25 | 50 | 100 |
|---|---|---|---|---|---|---|
| `corr(ΔLODF, ΔAC)` | .6430 | .6493 | .6592 | .6990 | .7733 | .8492 |
| `corr(ΔPW-DC, ΔAC)` | .6430 | .6493 | .6592 | .6990 | .7733 | .8492 |

Good enough to **rank**; not good enough to read a post-contingency loading number off.

### UPDATE 2026-08-25 — the "does not compose" limitation is SOLVED in the literature

An earlier corridor-collapse study dropped LODF partly because *"single-row LODF does
not compose across simultaneous outages, and 209 corridors go out together."* That is true
for chaining rank-1 updates one at a time, but chaining is not the only way to do it.

**Ronellenfitsch, Manik, Hörsch, Brown, Witthaut, *"Dual theory of transmission line outages"*,
arXiv:1606.07276v2** (primary text verified 2026-08-25). Abstract:

> *"a new formula for the computation of Line Outage Distribution Factors (LODFs) is derived,
> which is not only computationally faster than existing methods, but also generalizes easily for
> multiple line outages and **arbitrary changes to line series reactance**."*

- **Eq. (28) — ARBITRARY REACTANCE CHANGE, not just outage.** For `x_ℓ -> x_ℓ + ξ_ℓ`:
  `ΔF = [ -ξ_ℓ F_ℓ / (1 + ξ_ℓ u_ℓᵀ M u_ℓ) ] · M u_ℓ`, with `M = C A⁻¹ Cᵀ`. Ordinary LODF is the
  `ξ→∞` limit (Eq. 29). The paper flags this generality for *"series compensation devices... or
  adjustable inductors"*. **A new parallel circuit is exactly this case**: two lines of `x` in
  parallel give `x/2`, i.e. `ξ = -x/2`, finite and negative.
- **Eq. (35) — M SIMULTANEOUS changes, JOINTLY:**
  `ΔF = -CA⁻¹Cᵀ U (𝟙 + Ξ UᵀMU)⁻¹ Ξ UᵀF`
  One joint low-rank correction via a single M×M inverse, not a sequential composition of M
  rank-1 updates, so **no accumulated chaining error**. Exact within DC linearity.

**Scope limits.** "Exact" removes the sequential-composition error, not the DC
linearisation itself. The paper does NOT cover adding a corridor where no branch existed (that
needs the cycle basis extended, not a row perturbed). And **no literature was found** bounding a
linear pre-screen's error as a function of the number of simultaneous changes, so use it to
SHRINK a candidate list, then confirm the shortlist with a real solve.

**Where this lands:** the composition objection does not block LODF for the DC subsystem of
a violation-remediation study ([violation-remediation](../demos/violation-remediation.md)). Its ~93 changes are all reactance perturbations on
EXISTING corridors (measured: 42 single-circuit, 3 double), and its 454 rating bumps do not touch
these matrices at all: a rating change moves no flow, only the limit you compare against. Both
reasons LODF was rejected for reactive planning also **invert** there. That case has 482
corridors over 100% (worst 296%) rather than 2, and it is a DC study by design, so DC's
blindness costs it nothing.

### Why it was NOT adopted for reactive power planning

Two independent reasons, both measured. Neither is "LODF is inaccurate":

1. **No thermal headroom to discriminate on.** Across all outages, exactly **2 branches**
   exceed 100 % loading (max `1.000014`). TAMU synthetic grids are built N-1 thermally
   secure, so a correct detector runs on a grid engineered to have no positives. *(This is
   itself a reusable check for synthetic-grid validation: does a synthetic case's rating
   set actually satisfy N-1?)*
2. **N-1 barely moves the ranking.** `Spearman(base-case stress, full-N-1 stress) = 0.8893`.
   The contingency dimension mostly reproduces the base-case stress signal already computed.

LODF also structurally cannot carry that work's late stage, because it **inherits all of
DC's blindness**: no voltage (every bus pinned at 1.0 pu), no reactive power, no losses, no
generator VAr limits / tap changes / switched-shunt action, and it can never return "did not
converge," which is sometimes the physically meaningful answer. That study's real violations
are 69/138 kV low-side buses sagging from a **local MVAr deficit**, which exact MW
bookkeeping cannot see. Voltage security still needs
[parallel-contingency-solve](parallel-contingency-solve.md).

> **Open question, unresolved:** median *relative* error on movers is 100.0 % at **every**
> threshold for both LODF and PowerWorld DC (for the median branch that moves under AC,
> DC predicts no change at all), yet correlation reaches 0.85. Not explained. The AC re-solve
> jitter floor was also never measured (the case stopped solving after ~300 open/close
> cycles), so some small-mover "change" may be re-convergence noise.

### PowerWorld / esapp traps found while measuring this

Each cost real time; all measured 2026-08-10.

- **`pw.dc_mode` is effectively one-way.** Setting it `False` moves the case to AC; setting it
  `True` does **not** move it back, so every later "DC" solve silently stays AC. Use the
  explicit script commands and verify: `SolvePowerFlow(DC);` vs
  `SolvePowerFlow(POLARNEWT);` (the Aux manual's token is `POLARNEWTON`; see
  [aux-only-powerworld](aux-only-powerworld.md)). **The only unambiguous test is that a real DC solve pins every
  bus to exactly 1.0 pu.** Check it; don't trust the flag.
- **esapp calls `Branch.LineStatus` read-only. esapp is wrong, but what that costs you
  depends on your version.** `Branch.is_settable('LineStatus')` returns `False`, and that
  flag is a stale generated whitelist, not PowerWorld's answer. PowerWorld's own
  `GetFieldList('branch')` reports `enterable` as *"Depends: Normally enterable except when
  field Lockout is YES"*. esapp's generator keeps only unconditional `Yes` fields and drops
  every conditional one. Through 0.1.x that bad flag *blocked* the write: `pw[Branch] = df`
  raised `Cannot set read-only field(s)`, which is what the 2026-08-10 runs above hit.

  **On 0.2.1 it only warns** (`UserWarning: Read-only field(s) on Branch: ['LineStatus']`)
  **and the write goes through.** ✅ **Verified live 2026-09-10** (~2,000-bus synthetic case, Simulator build
  2026-07-22): `pw[Branch, 'LineStatus'] = 'Open'` opened all 3950 branches; the per-element
  list form opened exactly the one branch intended. So the bracket writer is usable. The
  only hazard is that the warning scrolls past and looks like a failure when it isn't.

  Do **not** apply the `-W error::UserWarning` mitigation that older revisions of this kit
  suggested. It turns this false alarm into a hard failure on 112 `Branch` fields that
  write fine. See [esapp](esapp.md) for the full count and
  [esapp-script-command-wrappers](esapp-script-command-wrappers.md) for the 0.2.1 change.

  If you would rather not have the warning in your logs at all, `SetData` is equivalent and
  silent:

  ```python
  pw.esa.SetData("Branch", ["BusNum", "BusNum:1", "LineCircuit", "LineStatus"],
                 [f, t, "ckt", "Open"])
  ```

  `SetData` is a typed wrapper in 0.2.1, so this obeys the call-the-named-method rule and is
  consistent with [powerworld-limitset-setdata](../methods/powerworld-limitset-setdata.md).
  `OpenBranch(...)` and `Open(...)` have no esapp wrapper at all and are reachable only as
  `RunScriptCommand` strings. **Assert the effect whichever route you take**: read the
  branch's status back, or check its flow went to zero. Never the absence of an exception.
- **`pw.lodf(branch)` exists in esapp but is per-branch**, so 13k COM round-trips. Build the
  matrix yourself.
- **Always confirm the case solves before analysing it.** A freshly-opened `.pwb` returns
  plausible-looking `LineMW` from its *saved* state, so an analysis that never calls a solve
  will read sane numbers off an unsolvable case. A **DC solve is a linear system and cannot
  legitimately fail**. If it does, the case is broken, not the contingency.
- **Do not average error over the whole (branch × outage) table.** ~2 M entries are dominated
  by branches far from the outage that trivially do not move, which flatters any method to
  `mean |err| ≈ 0`. Measure error on the **flow change**, restricted to branches that actually
  moved, and against **each solver's own base** (mixing a DC base with an AC result folds the
  hundreds-of-MW DC/AC gap into the thing being tested).


---

# ==== one-device-per-voltage-pocket.md ====

---
type: concept
domain: synthetic-grid
topic: contingency
aliases: [voltage-pocket, pocket-siting, one-capacitor-per-pocket, grouping-undervoltage-by-driver,
  where-to-put-the-capacitor, post-contingency-undervoltage-siting]
tags: [synthetic-grid, voltage, contingency, n-1, remediation, siting, powerworld, shunt]
---

# One device per voltage pocket

## Abstract

Post-contingency undervoltage clusters by **driving outage**, not by bus. Buses that fail
together under one outage are **one problem with one fix**, so the unit of remediation is the
pocket, not the violated bus. A worklist that ranks buses cannot see this, because the
structure lives in a column it does not group on. Measured 2026-09-14 on a ~9k-bus synthetic
planning model: the undervoltage buses resolved to fewer than half as many driving outages, and
the multi-bus pockets among them covered about 85% of the buses. One modest capacitor at the worst
bus of the largest pocket cleared **all seven of its buses**, created zero new violations anywhere
across the full contingency set, and left the thermal side untouched.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md)
  (the loop this belongs to) ·
  [remediating-base-case-violations](../methods/remediating-base-case-violations.md) (the N-0
  ladder, which sites one device at the worst bus for the same reason) ·
  [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) ·
  [reading-violationctg](../methods/reading-violationctg.md) (the `CTGLabel` column to group on)
- **Traps it depends on:**
  [sizing-a-device-whose-impedance-determines-its-own-flow](sizing-a-device-whose-impedance-determines-its-own-flow.md)
  (a shunt is the second form of that trap) · [adding-devices-esapp](../methods/adding-devices-esapp.md)

## Content

### The structure, and why a ranked list hides it

A per-element worklist sorts violated buses by severity. That ordering is correct and useless
for siting: the buses of one pocket scatter through it by depth, so the list presents a dozen
separate problems where the network has one. The grouping key is the **driving contingency**,
which the violation rows already carry.

Grouped that way, a handful of outages cause most of the undervoltage, and the long tail is
singletons.

| pocket size | outages | buses covered |
|---|---|---|
| 2+ buses | roughly half the outages | **~85% of the violated buses** |
| 1 bus | the rest | the remainder |

**Most multi-bus pockets are single-transformer-fed.** That is why they behave as units: one
element is the only path in, and losing it strands everything behind it together. A severity
ranking has no way to represent that topology.

### Why one device fixes the whole pocket

Every bus in a pocket is healthy intact and fails only post-outage, and they fail *together*
because they share the constraint. Reactive support injected anywhere inside the pocket holds
the whole pocket up. Siting per violated bus buys one device for each symptom of a single cause.

Measured on the largest pocket: one capacitor of ordinary size at its worst bus took all seven
buses, spanning three voltage levels including two generator step-ups, back inside band, and
introduced nothing new across the full contingency set.

**Site at the worst bus in the pocket**, and verify against the whole set rather than the one
outage the walk used: the device changes the case for every contingency, not only the one it
was sized against.

### The sizing trap, in its shunt form

A shunt's output goes with the **square of the voltage it is sizing itself against**. Measured on
an existing fleet, actual-over-nominal equals V² to four figures. That has two opposite
consequences:

- **It is weakest exactly where it is needed most.** At a collapsed bus the device delivers
  substantially less than nameplate: measured here at ~61% while the bus sat deep below limit.
  Sizing from a linear intuition under-buys.
- **It is strongest once it has worked.** The same device delivers *above* nameplate once the
  bus recovers. Measured: the repaired bus became the **case maximum** intact voltage, rising by
  ~0.05 pu. That was comfortably inside the emergency band but would sit at the edge of a
  narrower normal band.

So the walk must **re-solve at every step and accept the measurement**. Extrapolating a size from
one step's `dV` is the trap in
[sizing-a-device-whose-impedance-determines-its-own-flow](sizing-a-device-whose-impedance-determines-its-own-flow.md)
again. The acceptance test has two halves: the target back inside band **and** nothing pushed
out that was inside before. A device that rescues its own pocket while
overvolting a neighbour is not a fix.

### When the pocket is telling you something else

A pocket that collapses by a large margin (a fifth of a per-unit or more) on the loss of a
single element is describing a **connectivity** problem, not a voltage-support one. Reactive
support may still hold it, and holding it may be the right economic answer, but record that
one element is the only path in
([finding-and-fixing-radial-by-n1-pockets](../methods/finding-and-fixing-radial-by-n1-pockets.md)).

**Both facts belong in the output**: the device that holds it, and the redundancy that is
missing. A study that reports only the capacitor has answered the question and hidden the
problem.


---

# ==== opf-preconditions.md ====

---
type: concept
domain: tooling
topic: power-flow
aliases: [SolvePrimalLP, DCOPF preconditions, OPF constraints, BGAGC, opf-area-control]
tags: [powerworld, opf, dcopf, scopf, agc, cost-curve, gotcha, synthetic-grid]
---

# What an OPF needs before `SolvePrimalLP` will run at all

## Abstract

PowerWorld's LP OPF refuses to start unless **three** independent preconditions hold at
once: some area under OPF control (`Area.BGAGC = "OPF"`), some generators AGC-able
(`Gen.GenAGCAble = "YES"`), and those generators carrying a cost model that is not NONE.
Miss any one and you get a fatal error, not a degraded solve. That is the good news,
because the third condition is *data* and cannot be switched on honestly. Synthetic cases
routinely ship with all three off, so any OPF work on that case family hits this first.
This page records the three conditions, the confirmed field names and how
they were confirmed, the integrity trap in "just set a cost model", and the DC power flow
fallback that answers a thermal question without needing any of it. Verified 2026-09-11
on a regional synthetic planning model, Simulator 24.

## Connections

- **Up:** [powerworld-simauto](powerworld-simauto.md) · [Home](../index.md)
- **Across:** [aux-only-powerworld](aux-only-powerworld.md) (how this was driven, and the provenance rule that
  settled the field names) · [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md) (the cost-curve
  silent-zero traps) · [applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md) (same case family, AGC off)
- **Deeper:** [esapp-schema-reference](../references/esapp-schema-reference.md)

## Content

### The error, and what it actually means

```
Fatal Error: No Areas or Super Areas set as OPF Constraints
  To correct, on the OPF Area Records (or OPF Super Area Records) display
  toggle the AGC Status field to "OPF" for some areas/super areas
  Also, make sure some generators are set to AGC = YES and have a Cost Model
  that is not NONE.
```

The headline names one condition; the message body names two more. All three are
required. The OPF optimises *specific controls under specific constraints*, and with none
declared it has nothing to do and says so.

| # | Condition | Field | Nature |
|---|---|---|---|
| 1 | an area (or super area) under OPF control | `Area.BGAGC` = `"OPF"` | switch |
| 2 | generators the OPF may move | `Gen.GenAGCAble` = `"YES"` | switch |
| 3 | those generators priced | `Gen.GenCostModel` ≠ NONE | **data** |

### The field names, and how they were confirmed

`BGAGC` is **not** in the *Auxiliary File Format* manual, and neither is any other field name,
because that manual carries no per-object catalog (see [aux-only-powerworld](aux-only-powerworld.md)). It was
confirmed instead against esapp 0.2.1's generated schema, offline, without a PowerWorld
session:

```python
from esapp.components import Area
"BGAGC" in Area.fields()          # True  -- one of Area's 444 fields
Area.is_editable("BGAGC")         # True
Area.is_edit_mode_only("BGAGC")   # False -- writable in RUN mode, no EnterMode(EDIT)
```

`Gen.GenAGCAble`, `Gen.GenCostModel`, `Gen.GenCostCurvePoints` and `Gen.GenMCost` all
confirm the same way: real, editable, not edit-mode-only.

⚠ **`AGC_AGCStatus` is not an Area field.** It appears in this knowledge base's prose
([applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md), which now flags the name) as the area AGC-status field name and does not exist in
esapp's schema. Do not use it. A field name read out of a prose page is a lead, not a fact.
Check it against the schema before writing it into a script.

esapp declares no value vocabulary for `BGAGC`, so the literal `"OPF"` rests on
PowerWorld's own error text. If a write does not take, read the field's current value back
and match the spelling you see.

In aux, with `ALL` as the filter keyword (`""` is not legal; see [aux-only-powerworld](aux-only-powerworld.md)):

```
SetData(Area, [BGAGC], ["OPF"], ALL);
SetData(Gen, [GenAGCAble], ["YES"], ALL);
```

Then read both back before believing either. `SetData` reports success on writes that
change nothing.

### Condition 3 is data, and forcing it is a research-integrity failure

Conditions 1 and 2 are switches and may be flipped freely: they change what the OPF is
*allowed* to do, not what the answer is. Setting `GenCostModel` to something non-NONE
without real cost curves means inventing fuel costs, and the resulting dispatch is then
driven entirely by fabricated numbers. It will look like an economic dispatch, produce a
cost column, and mean nothing. **Check whether the case
carries cost data; do not manufacture it.**

Per [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md), the guard is
`GenCostCurvePoints > 0 AND GenMCost > 0`. `GenCostCurvePoints == 0` means no curve was
ever fit and the cost fields read `0`, which is *no data*, never *free*. A handful of
units can also report `GenMCost == 0` with curve points defined.

**Refined 2026-09-30, measured on a public synthetic 37-bus case.** Those units are the wind and
solar: five curve points each, and a curve that is 0 at their output. The OPF solved with them in
the movable set. `GenMCost` is the curve *at today's output*, so a zero there is a price of zero,
not missing data. The case-auditor therefore counts a unit as priced when `GenCostModel` is not
None and `GenCostCurvePoints > 0`, says nothing about a zero-cost renewable, and flags a
*thermal* unit whose curve reads 0 as worth a look.

**Refined again 2026-10-01, measured on Synth2k.** Some units on a Cubic cost
model read `GenCostCurvePoints = 0` with `GenMCost > 0` (others carry curve points): a cubic model is evaluated from its
coefficients, not from curve points, so a zero point count there is not missing data. The
auditor counts a unit as priced when `GenCostModel` is not None and it has curve points or a
positive cost at today's output (`GenCostCurvePoints > 0` or `GenMCost > 0`). A unit with
neither still counts as carrying no cost data.

Synthetic cases are the live hazard here. A generation pipeline may assign piecewise cost
curves at build time, but whether they survived into the dated case you are holding is a
question about that file, so measure it.

**And the measurement can come back unsatisfiable.** On a ~9k-bus synthetic planning model,
2026-09-11:

| Field | Reading |
|---|---|
| `GenCostModel` | `"None"` on **every** unit |
| `GenCostCurvePoints` | `0` on every unit |
| `GenMCost` | zero nonzero values |
| `GenAGCAble` | `"NO"` on all but one |
| `Area.BGAGC` | one area, `"Off AGC"` |

Conditions 1 and 2 were one `SetData` each. Condition 3 had nothing to switch on: the case
carries no cost data. **DC OPF is therefore not available on that case at all** until
cost models are populated upstream. No tuning or setting fixes absent data. Check for this
*before* designing a study around an OPF: the recon costs seconds, and the alternative is
discovering it at the solve.

This also fixes the shape of the value vocabulary: `BGAGC` reads back as the
human-readable string `"Off AGC"`, spaces included, which makes `"OPF"` from PowerWorld's
error text the right shape to write.

### `Sim_Solution_Options` is the lowest-priority place to set a solve mode

`SetData(Sim_Solution_Options, [DCApprox], [YES]);` is how the DC approximation gets set in
an aux, and it works. But the manual documents `Sim_Solution_Options` only as a
SUBDATA section nested inside `Contingency`, `CTG_Options` and `QVCurve_Options`, never as a
standalone `SetData` target. The shape is an analogy to the sibling `Equiv_Options` (which
the manual explicitly says may be set "using the SetData action, or a DATA section"), not a
citation.

What the manual does settle is **precedence**, which bites the moment OPF meets
contingency analysis. Contingency analysis reads power flow solution options from three
places, and applies them in this order of precedence:

1. options stored on the individual contingency record
2. options stored on the contingency tool (`CTG_Options`)
3. the global solution options

**Global solution options rank last.** Setting DC once at the top of an aux does not make it
true during contingency analysis: anything the contingency record or `CTG_Options` carries
overrides it. This is why a research pipeline's SCOPF sequence sets both
`Sim_Solution_Options.DCApprox` *and* `CTG_Options.CTG_CalculationMethod`.

### Super areas count, and a refusal through SimAuto does not raise

Measured 2026-09-30 on two public synthetic cases, in memory, never saved:

| as the case opened | OPF (`InitializePrimalLP`, `SolvePrimalLP`) |
|---|---|
| a super area on OPF, every member area (`Area.SAName`) `Off AGC` | **ran**: *Successful Solution* |
| an area on OPF inside a super area that is `Off AGC` | **ran**: *Successful Solution* |
| every area and super area switched to `Off AGC` | **refused** |

So condition 1 is met by an area **or** a super area on OPF; a super area on OPF makes its member
areas redispatchable, and one that is `Off AGC` does not override a member area set to OPF.
`SuperArea.BGAGC` reads back the same strings as `Area.BGAGC` (`OPF`, `Off AGC`).

The refusal did **not** raise through esapp: both calls returned, and the only sign was
`OPFSolutionSummary.LPOPFSolutionStatus = "Error = No area/superarea constraints set"` with
`LPOPFCostFunction:1 = 0`. Read the status after every solve; a script that trusts the absence
of an exception reads a zero-cost "solution".

### Always give the solve a failure handler

`SolvePrimalLP` takes four optional arguments (a success slot, a failure slot, and two
create-if-not-found flags), and either filename slot accepts the literal `STOP`, meaning
halt all aux execution:

```
InitializePrimalLP("", STOP);
SolvePrimalLP("", STOP);
```

Bare `SolvePrimalLP;` has no failure handler. A refused or non-converged OPF then becomes
one line in the log while every later stage runs against an **unsolved case** and writes
plausible numbers into correctly-named files. `SolveSinglePrimalLPOuterLoop` and
`SolveFullSCOPF` carry the same slots. See [aux-only-powerworld](aux-only-powerworld.md).

### "Successful Solution" can still leave a limit unenforced

`OPFSolutionSummary.LPOPFSolutionStatus = "Successful Solution"` does not mean every limit
holds. When no controllable unit can relieve a branch, the LP relaxes that constraint, prices it
at the penalty cost, and reports success anyway. Measured 2026-09-24 on Synth40: two 69 kV lines
were left at 138% and 120%. The only AGC-able units sat on the far side of the network, so no
dispatch could unload those lines. Check after every OPF:

```python
b = pw[Branch, ["LineLPUnenforceableMVA", "LinePercent", "LinePercent:1"]]
unenforced = b[b["LineLPUnenforceableMVA"].astype(str).str.strip() == "YES"]
```

A non-empty result is a network limit (transmission, or dispatchable generation on the wrong
side), not a dispatch finding. `OPFSolutionSummary.LPOPFMC` reading the penalty price is the same
signal from the other end.

### Flipping condition 2 globally is blunt

`GenAGCAble = "YES"` on every unit lets the OPF redispatch the entire fleet, including
units that would never move in operation. Acceptable for a first look; narrow it before
any result is reported.

### The fallback that needs none of this

If the question is *thermal* (what happens to branch loadings when an element is removed),
a **DC power flow** answers it and requires no area control, no AGC flags and no cost data:

```
SetData(Sim_Solution_Options, [DCApprox], [YES]);
SolvePowerFlow(DC);
```

What is lost versus a DC OPF is economic redispatch. On a case whose areas are off AGC
and whose units are almost entirely not AGC-able, very little was being redispatched
anyway.

Two things to carry into the comparison:

- **A DC solve pins every bus to exactly 1.0 pu** ([lodf](lodf.md)). So neither DC OPF nor DC
  power flow yields any voltage answer; a before/after voltage table from a DC run is
  identically zero change. Voltage requires an AC re-solve at the post-change dispatch,
  compared against an AC baseline.
- `pw.dc_mode` is effectively one-way ([lodf](lodf.md)); prefer the explicit script form above and
  verify by checking that the bus voltages really did go to 1.0.


---

# ==== parallel-contingency-solve.md ====

---
type: concept
domain: cross-cutting
topic: contingency
aliases: [parallel-contingency-solve, parallel-ctg, os-process-n1-sweep, contingency-parallel]
tags: [contingency, n-1, ctgsolveall, esapp, powerworld, multiprocessing, technique, cross-cutting]
---

# Parallel N-1 Contingency Solve (OS-process level)

## Abstract

A workaround for PowerWorld's own distributed `CTGSolveAll` being non-functional in this
environment. PowerWorld's DS server + registered compute hosts never spawn workers here; it
silently degrades to single-process serial. Instead, split the case's contingency set into N
chunks and run N independent `pwrworld.exe`/esapp instances as separate OS processes (Python
`concurrent.futures.ProcessPoolExecutor`), each solving a plain serial `CTGSolveAll` on only
its own chunk, then merge the per-bus voltage envelopes. Built for a reactive power planning
study to unblock a Synth8k N-1 sweep that was timing out at 7200s (2 hrs) serial.
Live-measured: **~6-7x faster on the 8k case** (18.4 min vs. the 2-hr timeout, more than 10k
contingencies), but only **~1.7-1.8x on a smaller 2k case** (5,344 contingencies). The
speedup scales with per-contingency solve cost because each worker pays a fixed ~20-45 sec
`open()` overhead that does not parallelize away.

## Connections

- **Up:** [Home](../index.md)
- **Used in:** a reactive planning study, as a parallel contingency-solve wrapper
- **💡 Could apply to (idea transfer):** any PowerWorld study that leans on `CTGSolveAll` for a
  large N-k contingency set (dynamic line rating branch-outage screening, any N-k security
  study); more generally, any SimAuto/COM-driven batch analysis where PowerWorld's own distributed
  computing can't be relied on (no DS server infrastructure).
- **Across:** [esapp](esapp.md) (the SimAuto wrapper each worker process opens independently) ·
  [powerworld-simauto](powerworld-simauto.md) (the COM server underneath, proven safe to open multiple independent
  instances concurrently; the rule is never `.exit()` a shared instance, always `.exit()` one you own)

## Content

### Why PowerWorld's own distributed computing doesn't help here

`CTGSolveAll(distributed=True)` requires a running DS (distributed-solve) server plus registered
compute hosts already set up in PowerWorld Simulator. On this machine, `VerifyDistributedComputersAvailable`
confirms the server is reachable but **zero workers ever spawn**; PowerWorld silently
falls back to single-process serial. That blocked the Synth8k case's N-1 set of more than 10k
contingencies, which was timing out at 7200s (2 hrs) running serial. Distributed computing
settings are also GLOBAL Simulator settings, not serialized into the `.pwb`, so there is no
case-level fix, only an infrastructure one (standing up a real DS server), which is out of scope.

### The workaround: parallelize at the OS process level

Skip PowerWorld's distributed-computing feature and parallelize one level up:

```
Case's existing CTGLabel set (already autoinserted + saved to a case file)
        │
        ▼  split into N chunks (np.array_split)
  N independent OS processes, each:
    - opens its OWN esapp/PowerWorld instance on the SAME case file
    - sets CTGSkip=NO only for its own chunk's labels, YES for everything else
    - runs a plain serial CTGSolveAll on just its chunk
    - returns its own per-bus Bus.BusMin/MaxVoltageContingency envelope
        │
        ▼  merge (pure function, no PowerWorld)
  min-of-mins on BusMinVoltageContingency, max-of-maxes on BusMaxVoltageContingency,
  joined on BusNum → same output shape as the serial function
```

This works because concurrent *independent* PowerWorld/esapp instances are safe on this machine.
A live probe (3 concurrent handles, isolated reads+writes) disproved the earlier "single-instance
SimAuto" assumption. The real rule is **never call `.exit()`** on a shared/ambient instance.
Each worker here opens and owns its own instance for its own process lifetime, so that rule
does not bite.

**The rule cuts the other way for an instance you own and reopen in a loop.** A worker that opens a
fresh case per candidate (the pattern a measurement harness uses so no tap or shunt state carries
between candidates) must call `.exit()` on **its own** instance before the next open. Dropping the
Python reference (`del pw`) does not release the COM server: measured 2026-09-28, each open left one
`pwrworld.exe` of ~1 GB running, and a run of four workers reached sixteen stray servers in a few
minutes, starving the other sweep on the machine. Never `.exit()` a shared instance; always
`.exit()` one you opened and are done with. Killing the Python process eventually frees them too, but
only once COM notices the client is gone.

### CPU/RAM headroom — don't naively use `os.cpu_count()` workers

Live-measured on an i9-12900K (16 physical / 24 logical cores): 10 worker processes pegged the
**whole machine** near 100% CPU. Each `pwrworld.exe` worker burns **more than one logical core
internally** (PowerWorld's own sparse-solver threading is not user-controllable or documented), so
"1 worker == 1 logical core" is wrong. The observed ratio was roughly 2.4 logical threads per
worker at `n_workers=10`. A `recommended_workers()` helper computes a conservative default from
both CPU headroom (`(logical_cores − reserve) // per_worker_cores`, defaults `reserve=2`,
`per_worker_cores=3`) and RAM headroom (`available_mb // per_worker_mb`, default 700 MB/worker,
measured from the 8k run's actual `pwrworld.exe` footprints of ~150-600 MB each), returning
whichever bound is tighter. On this machine that resolves to **7**, not 10.

### GPU is not an option

PowerWorld's solver (`pwrworld.exe`) is a closed-source CPU sparse-LU Newton-Raphson engine
accessed only through the SimAuto/COM interface. There is no GPU path in PowerWorld itself, and
[esapp](esapp.md) is a thin Python wrapper around that COM interface, so it cannot inject GPU
acceleration into solver internals it doesn't control. The only lever for CTG solve speed here is
OS-level process parallelism (this technique).

### Correctness check + measured numbers

This changes *how* the sweep runs but not the physics, so the parallel result should exactly
match the serial baseline's violating-bus set. Verified live, with both sweeps run back to back
on the same case + same contingency set:

| Case | Contingencies | Serial | Parallel | Workers | Speedup | Match? |
|---|---|---|---|---|---|---|
| Synth2k series25 summerpeak | 5,344 (3,993 line + 1,351 xfmr) | 196-266 s | 107-152 s | 10 | 1.75-1.84x | Yes, exact violating-bus set |
| Synth8k (an ~8k-bus working model, see [lodf](lodf.md)) | more than 10k | ~7200 s (prior timeout, never completed) | 1,101 s (18.4 min) | 10 | ~6-7x vs. the timeout budget | violating buses found (about 2% of buses) |

The speedup grows with case size / per-contingency solve cost. The fixed per-worker `open()`
overhead (20-45 sec, does not parallelize away) is a much smaller fraction of total time on the
bigger, slower-per-contingency 8k case than on the 2k case. Run-to-run variance on the identical
2k case was also notable (196 s vs 266 s, ~35%), likely machine/process contention, not a code
issue. Don't trust a single sample when planning capacity for a big sweep.

### Scope limitation (deliberate)

This technique parallelizes ONLY the base N-1 voltage sweep. It does not parallelize a
remediation walk over contingencies that mutates a shared base fleet sequentially (e.g. an
after-removal security loop), because each fix changes state the next step depends on.
It also does not autoinsert contingencies itself. The case must already carry its N-1 set before
the parallel sweep opens it (autoinsert once, save, then hand that saved case path to the workers).


---

# ==== per-unit-basis-discipline.md ====

---
type: concept
domain: cross-cutting
topic: case-audit
aliases: [per-unit basis, base conversion, normalization base, basis discipline]
tags: [per-unit, normalization, powerworld, gotcha, data-provenance, technique]
---

# Per-unit basis discipline — a normalized number is meaningless without its base

## Abstract

A per-unit or normalized quantity is a **pair**: the number *and* the base it was
normalized against. Store only the number and you have stored nothing recoverable. Yet
per-unit values look like plain scalars, so they get copied between sources, written into
shared columns, and summed, with the base silently changing underneath. This page is the
reusable form of a mistake that hit a dispatch study twice, the second time *because* the
documented fix was written down without its precondition. Read it before mixing a
case-read normalized quantity with a synthesized or textbook one, and before trusting any
"correct formula" recorded from a previous session.

## Connections
- **Up:** [Home](../index.md)
- **Across:** [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md) (the concrete `TSH` case) ·
  [esapp](esapp.md)
- **Found in:** a generator dispatch study: an inertia-basis regression, and a later round
  of dispatch corrections with the same cause.
- **💡 Applies to:** reactive planning (synchronous-condenser and SVC machine bases) ·
  real-power planning (per-unit r/x/b) · normalized load fractions, where the per-zone and
  whole-system denominators differ · [gic](gic.md) · any study that sums or ranks a
  normalized quantity across heterogeneous equipment

## Content

### The rule

> A per-unit value carries an implicit denominator. Two per-unit numbers are only
> comparable, and only **summable**, if they share a base.

Three failure shapes, in increasing order of nastiness:

1. **Wrong base, uniformly.** Everything is off by one constant factor. Bad, but the error
   is visible in totals and usually caught by a sanity check.
2. **Wrong base, non-uniformly.** The base varies per device, so the error varies per
   device. Totals are wrong *and* any **ordering, ranking, or selection** built on the
   values is wrong. This is much harder to spot, because nothing looks broken; it quietly
   picks the wrong equipment.
3. **Two different bases in one column.** A field populated from two code paths (read
   from source on one, synthesized on the other) where only one path re-bases. The column
   name is now a lie for half its rows.

### The worked case: PowerWorld `TSH`

The inertia constant H (seconds) is per-unit on **each machine's own MVA base**.
PowerWorld's `Gen.TSH` is the same H re-based onto a fixed **100 MVA system base**:

```
TSH = H · GenMVABase / 100          system inertia (GW·s) = Σ TSH · 100 / 1000
```

Both expressions are "inertia in seconds." Neither is wrong. They are not interchangeable.

On the Synth8k case `GenMVABase` spans **2.2 – 1,444.4 MVA (median 170)**, so treating
assumed H as if it were `TSH` produced failure shape **2**: fleet inertia read about 51% of
its true GW·s value, nuclear about 9%, and the unit-commitment order in the
dispatch algorithm was silently wrong.

The physical statement underneath: **H alone is not an inertia quantity.** System inertia is
`M_sys = Σ Hᵢ · MVAᵢ`. Seconds must be size-weighted before they mean anything at system
level, which is also why *unit count is not a proxy for system inertia*.

### The meta-lesson: guidance inherits preconditions

This is why the bug recurred, and it applies to every other project.

A session on 2026-07-14 found the original inertia error and recorded the fix as a rule:

> `GW·s = Σ(Gen.TSH) · 100 / 1000` — **do NOT multiply by `GenMVABase`, it's already
> implicit.**

That is correct *for values read out of a case*. It was written down without the
qualifier, because at the time only one data path existed. Later a case arrived with **no
measured `TSH` at all**, so H had to be synthesized from published typical values. On that
path the rule **inverts**: you must multiply. Anyone, human or agent, following the
recorded guidance while writing the new path would produce exactly the bug that shipped.
And one did, in all three builders.

> **A documented correction is only valid under the conditions of the data it was derived
> from.** When you record a rule, record what made it true. When you *apply* a recorded
> rule, check that its precondition still holds — especially if the data source changed.

Practical habit: state the rule's scope in the same sentence as the rule.
"Don't multiply by the base" → "don't multiply by the base **when reading `Gen.TSH` from
the case, because it is already re-based**."

### How to make it stick (what actually worked)

Documentation alone failed here: the fix was written down and the bug still recurred. Two
mechanical guards were added instead:

- **Assert on the physical magnitude, at compute time.** `assert 460 <= fleet_gws <= 480`
  in the notebook cell catches every wrong-base variant regardless of how it was
  introduced, because it checks the *answer*, not the code. It is cheap.
- **Assert on the code shape, in CI.** A source-level test that greps the conversion works
  without a PowerWorld licence, but write it **precisely**. The first version accepted
  `/ 1000` (because `"100" in "1000"`) and an inverted `H · 100 / GenMVABase`. Anchor the
  regex and mutation-test the guard by reintroducing the bug and confirming it fails. A
  guard that silently accepts the defect is worse than none: it advertises coverage it
  doesn't have.

Prefer the magnitude assert if you only do one. It is source-agnostic and it fires before
a wrong number reaches a document.

### The same trap with a length base: per-mile impedance entered as the total

A line's impedance has a hidden second denominator, its length. A value copied from a
per-mile table and entered as the whole line's impedance is off by exactly the line's
mileage. That is often 30 to 100 times, and the case still solves, just with a line far
stronger than the real one.

Use magnitude as the check. On a 100 MVA base, an overhead line's reactance is roughly
**2e-4 pu per mile at 500 kV** and **1.2e-3 to 1.5e-3 pu per mile at 230 kV**. So a line
whose *total* X sits near those numbers is almost certainly per-mile data: multiply by its
length. A 60-mile 500 kV line should carry about 0.012 to 0.015 pu, not 0.0002. Name that
cause when you see it. A "typical value" from memory is a weaker answer than the length
ratio the case itself shows.

### Checklist when a normalized quantity enters a project

- What is the base: system-wide constant, per-device, or per-zone?
- Does every row in this column share it? If the column is populated from more than one
  source, the answer is probably no.
- Does the base *vary across devices*? If yes, a wrong base corrupts **ordering**, not just
  totals. Check any ranking or selection downstream.
- Is there a physical sanity band (a published typical range) to assert against?
- If I am reusing a recorded formula: what data path was it derived for, and am I on it?


---

# ==== powerworld-inertia-and-cost-data.md ====

---
type: concept
domain: cross-cutting
topic: case-audit
aliases: [TSH, GenMCost, GenInertia, inertia constant]
tags: [powerworld, inertia, cost-curve, dynamics, gotcha]
---

# PowerWorld inertia (`TSH`) and cost (`GenMCost`) field semantics

## Abstract

Four non-obvious PowerWorld/esapp case-data facts, found the hard way while building a
generator dispatch algorithm, for any project that touches generator inertia or cost data:
(1) `Gen.TSH` is H on a **100 MVA system base**, not the generator's own `GenMVABase`,
**and the "don't multiply by `GenMVABase`" rule that follows from it inverts the moment you
synthesize H yourself instead of reading it**
(this bit a second time on 2026-07-27; see the ⛔ box in §1 before writing any inertia
code); (2) `Gen.GenMCost` is a **live** cost-curve
evaluation at the case's *current* `GenMW`, not a fixed per-unit rate; (3) a system's official
zonal scheme may already be modelled natively as `AreaNum`/`AreaName`, in which case no
spatial join is needed; (4) a sibling project's fuel-category *name* doesn't
always match its actual `GenFuelType` mapping, so verify against source code, not the
label. Read the Content section before writing any code that sums inertia, ranks
generators by cost, needs zonal load data on a Synth2k case, or reconstructs
per-generator detail from another project's category-level summary.

## Connections
- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) ·
  [per-unit-basis-discipline](per-unit-basis-discipline.md) (the transferable rule)
- **Found in:** a generator dispatch study, where §1's original wording failed in practice
  and the fuel-mapping trap below cost a rebuild.

## Content

### 1. `Gen.TSH` (inertia constant H) is on a 100 MVA system base

`esapp` has no `GenInertia` attribute; inertia lives on the `Gen` object as `TSH`.
But `Gen.TSH`, read via `pw[Gen, ["TSH", "GenMVABase"]]`, is **not** the per-unit
inertia constant on the generator's own MVA base. It is H expressed on a fixed
**100 MVA system base**, a standard PSS/E-style dynamics convention. Confirmed two
independent ways on a Synth2k case:

- **Round-number test:** converting via `H = TSH * 100 / GenMVABase` lands every
  nuclear unit and nearly every coal unit on exactly `4.00` seconds, inside the
  published per-technology ranges operators tabulate (nuclear and coal both sit
  around 3–4.5 s). That is not a coincidence at that precision.
- **Direct cross-check:** the case's own `MachineModel_GENROU` (round-rotor) and
  `MachineModel_GENSAL` (salient-pole, e.g. hydro) dynamic model objects expose a
  `TSH` field of their own, and it reads the true per-unit H **directly, no
  conversion needed**: e.g. `4.0` for the same generator whose `Gen.TSH` reads
  `56.888`. The ratio between the two paths is exactly `GenMVABase/100` for every
  unit tested.

**Correct formula** for total system inertia (GW·s) over online synchronous units,
**when `TSH` is read from the case**:
```
GW·s = Σ(Gen.TSH) * 100 / 1000     # do NOT multiply by GenMVABase -- already implicit
```
Multiplying `TSH * GenMVABase` (the intuitive-looking but wrong formula) overstates
inertia by roughly `GenMVABase/100` per unit, ~13x too high for a ~1,400 MVA nuclear
unit.

> #### ⛔ The precondition on that rule — read before reusing the formula
>
> **"Do NOT multiply by `GenMVABase`" holds only because real `Gen.TSH` has already been
> multiplied by it.** That is a property of *the field*, not of inertia. If you are
> **synthesizing** H yourself (assumed values from an operator's published table, a textbook, or any
> per-machine source), H is on the **machine's own base** and you **MUST** multiply:
>
> ```python
> gens["H_assumed"] = gens["GenFuelType"].map(INERTIA_ASSUMED_BY_FUEL)
> gens["TSH"] = gens["H_assumed"] * gens["GenMVABase"] / 100.0   # re-base, THEN use the formula
> ```
>
> Writing assumed H straight into a column named `TSH` silently asserts every generator is
> 100 MVA. **This exact regression happened** on 2026-07-27, on a Synth8k
> case with *no* measured `TSH`, so all three notebook builders took the assumed-data path,
> which this page's original wording did not cover. Fleet inertia came out about 51% of its
> true GW·s value, nuclear about 9%. Because the error scales with machine
> size it was **non-uniform**, so unit *commitment order* was wrong too, not just totals.
>
> Physically, **H alone is not an inertia quantity.** System inertia is defined as
> `M_sys = Σ Hᵢ · MVAᵢ`: seconds must be weighted by machine size before they mean anything
> at system level. So for any downstream analysis, **unit count is not a proxy for
> inertia**; many small machines can carry less than a few large ones.
>
> The general lesson (guidance inherits the preconditions of the data it was derived from)
> is [per-unit-basis-discipline](per-unit-basis-discipline.md).

`MachineModel_GENROU`/`GENSAL`'s own `TSH` is the more robust source (no
conversion arithmetic to get wrong) but only covers round-rotor + salient-pole units.
Verify the two object types' record counts sum to the full synchronous fleet before
trusting it on a new case family.

### 2. `Gen.GenMCost` is a live evaluation at the case's *current* `GenMW`

`GenMCost` (marginal cost, $/MWh) is not a fixed per-unit number. It is PowerWorld
re-evaluating each generator's cost curve (`GenCostModel`, `GenCostCurvePoints`) at
whatever `GenMW` the case currently holds. Confirmed: `GenMW` correlates **0.95** with
`GenMCost` in a real case (marginal cost rises with output, as expected for a convex
cost curve).

**Consequence:** if you want to rank generators by cost *at a specific dispatch
point* (e.g. their `GenMWMin`, for a must-run/backstop step), reading `GenMCost` as-is
gives you cost at whatever the base case's *original* operating point was, which can
differ from the true value at your intended dispatch point by double digits of percent
(one tested unit: 6.37 → 5.56 $/MWh, a ~13% swing, when forced from its base-case
`GenMW` down to `GenMWMin`).

**Technique — live re-evaluation without saving:** temporarily overwrite `GenMW` for
the candidates via the bracket write interface, re-read `GenMCost`, then restore the
original `GenMW`, entirely in memory against the live SimAuto session, with nothing
written to the `.pwb`:
```python
orig = pw[Gen, ["BusNum", "GenID", "GenMW"]]
mw_at_target = orig["GenMW"].copy()
mw_at_target[mask] = target_values  # e.g. GenMWMin for the units you care about
pw[Gen, "GenMW"] = mw_at_target.tolist()

recomputed_cost = pw[Gen, ["BusNum", "GenID", "GenMCost"]]

pw[Gen, "GenMW"] = orig["GenMW"].tolist()  # restore -- verify max diff == 0.0
```
This generalizes to any PowerWorld field that's live-derived from `GenMW` (or other
mutable state) rather than stored directly. Check for this before trusting a field that
looks like a fixed property.

**Two silent-zero traps, and neither field settles it alone.** `GenCostCurvePoints == 0`
with `GenMCost == 0` means no cost curve was ever fit: no real cost data, never "free". But
a unit with curve points can read `GenMCost == 0` because its curve is 0 at today's output
(wind and solar: a price of zero, not missing data), and some Cubic units read
`GenCostCurvePoints == 0` with `GenMCost > 0`, because a cubic model is evaluated from its
coefficients. A unit has cost data when `GenCostModel` is not None and it has curve points
or a cost above 0 at today's output (`GenCostCurvePoints > 0 OR GenMCost > 0`); see the
dated notes (2026-09-30 and 2026-10-01) in [opf-preconditions](opf-preconditions.md).
Guard explicitly on that before using cost data to rank or select
generators, or a data gap silently becomes "dispatch this first."

### 3. Check `AreaNum`/`AreaName` before doing a spatial join

`AreaNum`/`AreaName` are native PowerWorld fields carried on **both `Gen` and `Load`**
objects, and a case is often built with the system operator's own zonal scheme already
encoded in them. Verify that before writing any geographic join: where it is populated,
zonal load and generation analysis needs no spatial work at all.

Don't confuse it with a **custom region field**, typically something like
`CustomString:2`, written by a case-specific spatial join against a boundary shapefile.
Two things regularly make such a field the wrong key: it is usually **generator-scoped
only**, never written to loads, and its distribution can be so dominated by a single
bucket that it differentiates nothing. Check the value distribution before you group by
it. `AreaNum` is the right key for zonal granularity *inside* one system; a region field
is right only when the analysis genuinely spans regions.

### 4. Another project's fuel-category name doesn't always mean what it says

Not a PowerWorld field-semantics gotcha but the same *don't-take-a-label-at-face-value*
family. A companion dispatch script's `"GAS_CT"` category actually maps to Synth8k's
`GenFuelType == "DFO (Distillate Fuel Oil)"`, not `"NG (Natural Gas)"`, confirmed by
reading the source's own fuel-classification code. Conflating the two misassigns
`TSH`/cost and mis-totals capacity. When reconstructing per-generator detail from another
project's per-category summary output, verify the category↔`GenFuelType` mapping against that project's actual
classification code, never the category's plain-English name.


---

# ==== powerworld-script-transfer.md ====

---
type: concept
domain: tooling
topic: scripting
aliases: [script-transfer, drop-file-aux, SimulatorScriptInput, SimulatorScriptOutput, external-script-control, sced]
tags: [powerworld, aux, script, external-program, llm, simulator-25, undocumented]
---

# Drop-file script transfer: driving Simulator without SimAuto

## Abstract

Simulator 25 beta can watch a directory and execute any `.aux` dropped into it, writing
back the message-log slice produced by that load. Write a file, read a file: **no COM and
no SimAuto call of your own.** This is the cheapest channel an external program (an LLM
among them) has ever had into PowerWorld, and it needs nothing installed on the caller's
side.

**The deck also says it therefore needs no SimAuto licence. That claim is untested.** Every run behind this page was made on a machine that *has*
the add-on, so nothing measured here could have falsified it. The script actions a dropped
file executes are the same action set SimAuto invokes, so where the licence check actually
sits is an open question. **Do not repeat it as a benefit** until someone has run a drop on
a Simulator without the add-on installed.

**It is not in the *Auxiliary File Format* manual.** Searched 2026-09-12 against the
September 1, 2026 edition: zero hits for `ScriptTransfer`, `SimulatorScriptInput`,
`SimulatorScriptOutput`, `ScriptInputOutputPollSec` and "drop file". The only source is
Overbye's September 2026 slide deck *Recent Modifications to PowerWorld Simulator to Allow
for More Interaction with External Programs*, which describes the functionality as new and
"probably evolving". Everything below is from that deck; nothing here is measured yet.

## Connections

- **Up:** [powerworld-simauto](powerworld-simauto.md) · [Home](../index.md)
- **Across:** [aux-only-powerworld](aux-only-powerworld.md) (what to write *inside* the dropped file; every trap
  and the read-back rule apply unchanged) · [aux-script-commands](../references/aux-script-commands.md) ·
  [esapp-script-command-wrappers](esapp-script-command-wrappers.md) (the Python-side channel this one bypasses)
- **Deeper:** [esapp-schema-reference](../references/esapp-schema-reference.md) (field-name provenance, still mandatory here)

## Content

### What it does

With the feature enabled, every `ScriptInputOutputPollSec` Simulator checks the configured
directory for a file named exactly **`SimulatorScriptInput.aux`**. If it is there:

1. the aux file is **loaded** (i.e. executed; unnamed `SCRIPT{}` blocks auto-run, see
   [aux-only-powerworld](aux-only-powerworld.md)),
2. the input file is **deleted**,
3. **`SimulatorScriptOutput.txt`** is written into the same directory, containing the new
   message-log entries associated with that load.

The request is a file appearing, the response is a file appearing, and the deletion of the
request is the acknowledgement.

### Turning it on

The deck states two preconditions, and both are real constraints rather than setup steps:
**a case must already be loaded**, and **the Script Command Execution Dialog (SCED) must be
visible**. Tools → Script opens it.

In the SCED:

| Field | Registry name (PowerWorld section) |
|---|---|
| Enabled External Script Control | `ScriptTransferFileEnabled` |
| ScriptTransferFileDirectory | `ScriptTransferFileDirectory` |
| Script File Poll Interval | `ScriptInputOutputPollSec` |

Settings persist in the registry, so this is configurable ahead of a session rather than
only through the dialog.

### The shape of a request

From the deck's worked example, on PowerWorld's own shipped `B7Flat` case:

```
// First change the generator status
DATA (Gen [ObjectID, STATUS])
{
"Gen 1 '1'" "Open"
}
// Then solve the power flow
SCRIPT{SolvePowerFlow;}
```

Two things to copy from this rather than invent:

- **`DATA` + `ObjectID` is a compact one-field key.** `"Gen 1 '1'"` identifies the unit
  without a separate `BusNum`/`GenID` pair. The manual documents `ObjectID` as an
  identifier form on several commands, so this is not deck-only syntax.
- **A single dropped file mixes `DATA` and `SCRIPT` blocks and they run in file order.**
  The edit lands, then the solve runs against it.

The corresponding `SimulatorScriptOutput.txt` is the raw log slice: `1 records read from
file.`, the AGC adjustments, the mismatch iterations, `Simulation: Successful Power Flow
Solution`, bracketed by `Starting load of auxiliary file:` and `Finished load of auxiliary
file:` lines.

### Write it elsewhere, then copy it in

The deck says to create `SimulatorScriptInput.aux` and "store it somewhere other than in
this directory", then copy it into the watched directory. Treat that as mandatory. The
poller has no way to tell a finished file from one still being written, so authoring in
place races the poll interval and can feed Simulator half an aux. A truncated script is
still a *valid* script up to the truncation point, so that failure is silent.

An atomic move within the same volume is the safer version of the same idea.

### What it does not give you

The output is a **log transcript, not a return value.** `SolvePowerFlow` succeeding or
failing shows up as English in a text file, not as a status your caller can branch on
without parsing. So:

- **The read-back discipline from [aux-only-powerworld](aux-only-powerworld.md) applies unchanged.** If the
  answer matters, `SaveData` it to a CSV and read the CSV. Do not infer success from the
  output file merely existing.
- `Simulation: Successful Power Flow Solution` is the string worth grepping for, but its
  absence is not the same as a specific diagnosis.
- This is **not headless**. A visible GUI dialog is required, so it does not replace
  [esapp](esapp.md) for batch or parallel work; see [parallel-contingency-solve](parallel-contingency-solve.md).

### Open questions to settle by experiment

None of these are answered by the deck, and each one changes how a caller must be written:

- Is `SimulatorScriptOutput.txt` **overwritten or appended** on each cycle?
- Is there any signal that the output file is **complete**, or must the caller poll for
  size stability?
- What happens when the aux **fails to parse**? Is an output file written at all, and does
  the input file still get deleted?
- Does `StopAuxFile` or `ExitProgram` inside a dropped file behave sanely here?
- What is the **minimum usable poll interval**, and does a short one cost anything?
- Does a second `SimulatorScriptInput.aux` dropped mid-execution get picked up, queued, or
  lost?

### Version floor

**The deck states Simulator 25 beta with a build date at or after September 19, 2026.**

**A measurement disagrees with that floor and has not been reconciled.** On 2026-09-21 the
channel was exercised end to end (dozens of drops, every one consumed and answered) on an
install whose own `CaseSummaryGet` output reports `EXE Build Date: 25 beta September 12,
2026`, a week before the stated floor.

Either the floor is conservative, or the string the EXE reports is not the build date the
deck means; nothing here settles which. Until someone checks, **treat the deck's date as the
number to quote and the measurement as the reason not to tell anyone their build is too
old**. A build reporting an earlier date may well work. See [version-requirements](version-requirements.md).


---

# ==== powerworld-simauto.md ====

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

**SimAuto** exposes the running simulator to external scripts: open cases,
read/write objects, solve power flow, run script commands, switch EDIT/RUN modes.
It is the layer *underneath* [esapp](esapp.md), which wraps it in the
**`SAW` (SimAuto Wrapper)** class. Because it is a COM server, everything here
is **Windows-only** (esapp talks to it via `pywin32`).

## SAW — the wrapper esapp puts on top

`SAW` lives in `esapp/saw/saw.py` and is assembled by the **mixin pattern**:
`SAWBase` (`saw/base.py`, core COM interface + case management + generic data
retrieval) plus ~20 capability mixins: `DataMixin`, `PowerflowMixin`,
`MatrixMixin`, `ContingencyMixin`, `TransientMixin`, `SensitivityMixin`,
`GICMixin`, `OPFMixin`, `PVMixin`, `QVMixin`, `ATCMixin`, `FaultMixin`,
`TopologyMixin`, `RegionsMixin`, `ModifyMixin`, `GeneralMixin`,
`CaseActionsMixin`, `ScheduledActionsMixin`, `TimeStepMixin`, `WeatherMixin`.

You rarely instantiate `SAW` directly. `PowerWorld.open()` does
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


---

# ==== pww-data.md ====

---
type: dataset
domain: weather
topic: timestep
aliases: [pww, pww-file, powerworld-weather, powerworld-weather-data]
tags: [pww, weather, dataset, binary-format, era5, hrrr, noaa]
---

# PWW data (PowerWorld Weather)

## Abstract

PWW (PowerWorld Weather) is a custom byte-packed binary format, produced by a weather pipeline and consumed by PowerWorld Simulator's TimeStep Simulation engine. It encodes gridded weather variables as uint8 values (0–254) per timestep and grid point, with 255 as the NaN sentinel. This page covers the VERSION 2 binary spec, variable encoding formulas, per-source production pipelines (ERA5, HRRR, GFS, WRF), and verification procedures. Drill deeper when writing or debugging a PWW file, or tracing weather data into a timestep study.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) (downloading PWW files) · [timestep-simulation](timestep-simulation.md) · [copper-plate](copper-plate.md) · step 3 of this reading sequence: prev [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · next [how-to-analyze-results](../methods/how-to-analyze-results.md)

## Content

**Step 3 of this reading sequence.** ← prev: [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · next: [how-to-analyze-results](../methods/how-to-analyze-results.md).

> **Firewall: PWW ≠ PFW.** PWW = weather *data* files (this page). PFW = the PowerFlow Weather *model* used in [copper-plate](copper-plate.md) studies. Never cross-link their aliases.

PWW stores gridded weather variables at discrete timesteps as uint8 values, one byte per variable per grid point per timestep.

### Binary Format (VERSION 2)

All values are **little-endian**. Types: `h`=int16, `i`=int32, `d`=float64, `u8`=uint8.

```
Offset  Type    Field
──────  ──────  ───────────────────────────────────────────────────────────
0       h       KEY1 = 2001
2       h       KEY2 = 8066  (8065 = VERSION 1; 8066 signals VERSION 2)
4       h       VERSION = 2
6       d       date_min  (OLE automation date — days since 1899-12-30)
14      d       date_max
22      d       lat_min / lat_max / lon_min / lon_max   (4 × d = 32 bytes)
54      h       META_STRINGS  (≥ 1 for VERSION 2)
56      cstr[]  meta_strings[META_STRINGS]  — "PowerWorld Timestep Simulation Weather\0"
─       i       COUNT       (number of timesteps)
─       i       SAMPLE_seconds  (3600=hourly, 900=15-min subh, 0=irregular)
─       i       LOC         (number of stations / grid points)
─       h       LOC_FC = 0
─       h       VARCOUNT
─       h[]     var_codes[VARCOUNT]
─       h       BYTECOUNT = VARCOUNT  (always VARCOUNT when all vars are uint8)
─       i[]     valid_counts[VARCOUNT]   ← VERSION 2 only — non-255 count per variable
─               station_records[LOC]   lat(d), lon(d), elev(h), who(cstr), country(cstr), region(cstr)
─       u8[]    data_array[COUNT × VARCOUNT × n_lat × n_lon]  — C order, 255 = NaN sentinel
```

**Grid dimensions** are derived from header bounds (ERA5 grid is 0.25°):
```python
n_lat = round((lat_max - lat_min) / 0.25) + 1
n_lon = round((lon_max - lon_min) / 0.25) + 1
```

**Longitude convention:** descending east→west (e.g. −60 → −130 for CONUS). Lat is ascending south→north.

**OLE epoch:** 1899-12-30. Timestamps before this date encode as negative and PowerWorld rejects the file. Pre-1900 data must be re-based forward (e.g. 1899 shifted to 1999, +100 years, preserving month/day/hour).

### VERSION 2 Traps (undocumented; the spec doc only covers VERSION 1)

Three requirements are missing from the format doc, and PowerWorld needs all of them to parse the file:

1. **KEY2 = 8066** (not 8065; this magic number signals VERSION 2 to the loader)
2. **META_STRINGS ≥ 1** with at least one description string
3. **VARCOUNT × int32 valid_count block** between BYTECOUNT and station data, counting non-255 values per variable

Without all three, PowerWorld misaligns the byte stream: station block bytes are read as valid counts, producing nonsense `ValidPercent*` values (e.g. 1267%, 990%) and shifted variable readings (temperature showing cloud cover bytes, etc.).

### Variable Codes and Encoding

All values stored as **uint8 (0–254)**; **255 = NaN sentinel** (excluded from valid counts).

| Code | Variable | Encoding formula | Unit stored |
|------|----------|-----------------|-------------|
| 102 | tempF | `round(°F + 115)` | °F+115 offset |
| 104 | DewPointF | `round(°F + 115)` | °F+115 offset |
| 106 | WindSpeedmph | `round(m/s × 2.236936)` | mph (10 m) |
| 107 | WindDirection | `round(degrees / 5)` — division INSIDE round() | ×5 to decode |
| 119 | CloudCoverPerc | `round(fraction × 100)` — GFS/ERA5 tcc is 0.0–1.0, must ×100 | % |
| 110 | WindSpeed100mph | `round(m/s × 2.236936)` | mph (100 m) — ERA5, GFS |
| 112 | WindSpeed80mph | `round(m/s × 2.236936)` | mph (80 m) — HRRR only |
| 120 | GHI | `round(W/m² / 5)` | ×5 to decode |
| 121 | DHI | `round(W/m² / 5)` | ×5 to decode |
| 136 | WindGust | `round(m/s × 2.236936)` | mph |
| 151 | PrecipitationRate | `round(kg/m²/s × 3600)` | mm/hr |
| 150 | PercentFrozenPrecip | direct percent byte | % — HRRR only |
| 122 | VerticallyIntegratedSmoke | `round(40 × log10(colmd × 1e6))` | dBZ-equiv — HRRR only |

**Wind direction encoding trap:** the division MUST be inside `round()`: `round(degrees / 5)`, never `round(degrees) / 5`. The latter truncates (not rounds) on uint8 cast, causing up to 4° systematic error.

**Code-112 (suspected PowerWorld bug):** PowerWorld's TimeStep loader throws an access violation on code 112 (no loadable 80 m wind field in PowerWorld). HRRR pipelines deliberately keep 112 because their wind is genuinely 80 m; this is a suspected PowerWorld bug, not yet verified (glitch `2026-10-21-pww-code112-av`). Do NOT remap 112→110.

### How PWW Is Produced

The weather pipeline runs four Docker pipelines, each writing a different PWW flavor:

| Pipeline | SAMPLE_sec | Variables | Output naming |
|----------|-----------|-----------|---------------|
| ERA5/CDS | 3600 (hourly) | 9 (no precip/smoke) | `{Region}{YYYY}_Q{Q}.pww` |
| NOAA/GFS forecast | 3600 | 8 (no DHI — written as 255) | `Forecast_{Region}_Run{YYYY-MM-DD}T{HH}Z.pww` |
| HRRR Forecast | 3600 | 10 | `{YYYY-MM-DD}T{HH}Z_sfc_48_CONUS.pww` |
| HRRR History (15-min) | 900 | 10 | `{YYYY-MM-DD}_Q{1..4}_subh_15min_CONUS.pww` |
| HRRR History (hourly) | 3600 | 10 | `{YYYY-MM-DD}_hourly_CONUS.pww` |
| WRF reanalysis | varies | 9 (no precip) | `WRF_{period}_{Region}.pww` |

ERA5 also emits a human-readable `.parquet` alongside the PWW.

### Who Consumes PWW

- dynamic line rating: weather around each line for IEEE 738 thermal rating
- hottest- and coldest-hour studies: finding the temperature-extreme scenarios
- [copper-plate](copper-plate.md) studies: weather inputs for the PFW model on renewables
- Any [timestep-simulation](timestep-simulation.md) study needing time-varying weather driving

### Using PWW in a Study

1. Pick spatial/temporal crop (via [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md), which crops by region and time window)
2. Map weather to case elements (lines, renewable units, load zones)
3. Feed per-timestep into the run; see [timestep-simulation-setup](../methods/timestep-simulation-setup.md)
4. Analyze → [how-to-analyze-results](../methods/how-to-analyze-results.md)

### Verifying a PWW (do both before trusting a new file)

1. **Structural + positional round-trip** (offline): parse header, assert KEY2=8066, VERSION=2, ≥1 meta string, valid_count block length == VARCOUNT, data size == COUNT × VARCOUNT × LOC. Then pick a few stations and confirm decoded bytes match the source grid cell at that (lat, lon).
2. **PowerWorld load test:** `TimeStepLoadPWW(file, "Weather Only")` via ESA/SimAuto; exit 0 = file loads cleanly. Pass absolute paths (PowerWorld resolves relative paths against its own working dir). Keep the smoke test as a small standalone script next to the converter that wrote the file.
   **On Simulator 25 (builds dated 2026-09-20 and 2026-09-25) this test fails for every file**: plain `TimeStepLoadPWW` raises `Error With Loading PWWFile` (suspected PowerWorld issue, not yet confirmed: glitch `2026-10-20-timestep-loadpww-plain`). `TimeStepLoadPWWRange(file, start, end, "Weather Only")` over the file's full span loads the same files (72 and 2,064 timepoints on two files, reproduced 2026-09-24). On those builds, run the smoke test with the Range form and assert the timepoint count. A failure of the plain form says nothing about the file.

### Does the file cover the units? (the case auditor's footprint check)

A renewable whose nearest station in the file is far away still runs: it takes that station's
weather, and the time step gives no warning. The case auditor (`ts.pww_footprint`) reads only the
file's header station list and flags every located renewable whose nearest station is more than
**25 miles** away. That number has no source: it is a proposed default in
`skills/case-audit/engine/thresholds.py` (`PWW_MAX_STATION_MILES`), chosen because a 0.25-degree
grid puts every point inside its footprint within about 12 miles of a station, so 25 miles leaves
margin and still catches a unit outside the grid.

### Related

- [Home](../index.md)


---

# ==== sizing-a-device-whose-impedance-determines-its-own-flow.md ====

---
type: concept
domain: cross-cutting
topic: design
aliases: [circular-sizing, self-fulfilling-under-sizing, size-against-converged-flow-trap,
  impedance-flow-feedback, transformer-sizing, how-big-a-transformer]
tags: [sizing, impedance, power-flow, transformers, gotcha, technique, feedback-loop, design]
---

# Sizing a device whose impedance determines its own flow

## Abstract

"Size it against the flow it actually carries" is the correct rule for a **line** and a
silently wrong one for a **transformer**. The difference is whether the device's impedance
moves with its rating. A transformer's does: `x_pu` is quoted on its *own* MVA base, so
`x_sys = x_pu · S_base / MVA` and a small nameplate **is** a high impedance. Flow routes
around the small unit, the converged flow comes back small, and the sizing rule confirms the
unit should stay small. The loop closes on itself and the answer looks converged. A
conductor's impedance barely moves with its rating, so a line has no such loop.

The failure is invisible in the device's own numbers (the under-sized unit reports *low*
loading, not high) and surfaces somewhere else entirely, as an overload on whatever path
picked up the flow it declined. Break it with a floor derived from something the device
cannot influence: the load it is obliged to serve.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [per-unit-basis-discipline](per-unit-basis-discipline.md) (why `x_pu` on its own
  base is the mechanism) ·
  [one-device-per-voltage-pocket](one-device-per-voltage-pocket.md) (a shunt's output varies with
  the voltage it is sizing itself against: the same shape) ·
  [remediating-base-case-violations](../methods/remediating-base-case-violations.md) (why a
  device walk-up must re-solve at every step) ·
  [reviewing-a-design](../methods/reviewing-a-design.md) (where an under-sized unit shows up in a
  review)
- **Used in:** [finding-and-fixing-radial-by-n1-pockets](../methods/finding-and-fixing-radial-by-n1-pockets.md)
  (a new tie's impedance decides its own flow)

## Content

### The shape of the trap

A device is **self-referential for sizing** when its rating changes its impedance, and its
impedance changes the flow you are sizing it against:

```
rating ↓  →  impedance ↑  →  flow routes elsewhere  →  measured flow ↓  →  rating ↓
```

Any fixed point of that loop is self-consistent, so nothing in the convergence test fires.
The loop does not oscillate or diverge; it settles quietly on a wrong answer.

Test for it before choosing a sizing basis: **does the quantity I am sizing against depend on
the size I choose?** For a line, no in any practical degree. For a transformer, a phase
shifter, an HVDC link, a series reactor, a switched shunt: yes.

### The measured case

Measured 2026-08-22 on a ~9k-bus synthetic planning model: a few dozen substations where a 69 kV
corridor was re-terminated at 138 kV and needed a new 138/69 kV transformer back to the original
bus. Three sizing rules were tried:

| basis | result |
|---|---|
| corridor need (pre-move flow ÷ 0.8) | **R² = 0.110** against real flow. Uncorrelated, not biased. About one unit in six over nameplate, worst **139.2%** |
| converged flow alone | **about a third of the units below the load on their own low-side bus**, worst **4.8×** |
| `max(converged flow, own-bus load)` | **none** over nameplate, worst **79.1%** |

The middle row is the trap: a *better-targeted* rule than the first, and it produced a
**worse** grid. One substation finished with a **30 MVA** transformer
against roughly five times that in load on its own bus, carrying under a fifth of its own rating.
The rest of the load arrived across the 69 kV network from neighbouring substations: the
low-voltage system quietly acting as a distribution bus to backfill under-sized station
transformers.

Nothing in the transformer's own report looked wrong. It read 19% loaded. The symptom appeared
two buses away, on a 69 kV line whose flow rose more than fifteen-fold to 105.2% of a rating
already at its class ceiling, which no conductor can raise. Chasing that line (a parallel circuit,
a voltage upgrade) would have treated the symptom and left fifteen more under-sized units waiting
to produce the next one.

The first rule was also wrong, but *conservatively* wrong: its 150 MVA floor accidentally
masked the circularity. Removing a bad rule can expose a worse one that the bad rule was
hiding, so the improvement and the regression are both real.

### The fix: floor it with something the device cannot influence

```
need = max( converged flow , load the device is obliged to serve ) / (1 − headroom)
```

The load behind a station transformer's low-side bus is **static input data**. The device's
impedance cannot change it, so it cannot take part in the loop. Converged flow still governs
any unit with genuine transit duty; the floor is a lower bound, not a target.

The general form: **find a quantity downstream of the device's obligation, not of its
behaviour**, and floor the sizing with it.

### Four details that each cost a full run

1. **Share the floor across parallel devices** on the same bus (`load / n`). Giving each the
   whole load builds the substation twice (measured 2 × 500 MVA against a 600 MVA need), and
   paralleling two over-sized units halves the impedance again, re-creating the redistribution
   the fix exists to remove.
2. **Decide exhaustion against the catalogue, not against `need`.** A device that cannot be made
   big enough must still be made *as big as the catalogue allows*, then reported. Returning
   "cannot" strands it at its seed: it published a 411.3% "dead end" sitting at a 30 MVA seed.
3. **One definition of the sizing driver**, used by the loop *and* the report. They diverged
   once and the artifact contradicted the algorithm: the loop judged a unit against one MW
   figure while the published table carried a figure a quarter of that.
4. **Seed low, not high**, wherever a never-downgrade invariant applies, because the seed becomes
   permanent. A low seed is also a *high* impedance, so the loop climbs monotonically instead
   of oscillating through the size-drops-X-attracts-flow feedback.

### Why the count is a different decision from the size

The number of devices is a **topology** fact and belongs in the pass that builds topology; the
size belongs in the loop. Where one standard unit physically cannot serve the obligation,
`n = ceil(need / largest_standard_rating)`. Exactly one unit in the measured set needed it
(598 MVA of need against a 500 MVA catalogue ceiling).

Keep the justification straight: "two corridors terminate here" is **not** a reason for two
transformers. "One unit that exists cannot carry the load" is.


---

# ==== timestep-simulation.md ====

---
type: concept
domain: cross-cutting
topic: timestep
aliases: [timestep-simulation, time-step-simulation-concept, temporal-simulation]
tags: [timestep, simulation, powerworld, weather, renewables, concept]
---

# Timestep simulation (concept)

## Abstract

A timestep simulation (in this knowledge base's sense) is PowerWorld's built-in TimeStep feature run over a weather time series: each renewable generator's hourly solar or wind MW output is computed quasi-statically from PWW weather data via its embedded PFW model. It is not a transient-stability study and has nothing to do with faults or rotor angles. For how to set one up and run it see [timestep-simulation-setup](../methods/timestep-simulation-setup.md); for the code see [time-step-simulation-backend](../references/time-step-simulation-backend.md).

## Connections

- **Up:** [Home](../index.md) · [time-step-simulation-backend](../references/time-step-simulation-backend.md)
- **Across:** [pww-data](pww-data.md) · [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · [how-to-analyze-results](../methods/how-to-analyze-results.md)

## Content

A power-system case is stepped through a sequence of weather timestamps, and PowerWorld
computes, for each renewable generator, how much **solar** or **wind** MW it would produce
at every hour. It is a quasi-static, hour-by-hour weather-to-generation evaluation, not a
dynamics study.

This page is **what it is**. For **how to set one up and run it** see the method
[timestep-simulation-setup](../methods/timestep-simulation-setup.md); for the engine/code see
[time-step-simulation-backend](../references/time-step-simulation-backend.md).

## How it works conceptually
1. A weather time series ([pww-data](pww-data.md)) is loaded into the case
   (`TimeStepLoadPWWRange`; plain `TimeStepLoadPWW` fails on Simulator 25 builds dated
   2026-09-20 and 2026-09-25, a suspected PowerWorld issue not yet confirmed).
2. Each renewable generator carries an embedded **PFW (PowerFlow Weather) model**
   that maps weather (irradiance, wind speed, etc.) to MW.
3. PowerWorld walks every timestep, applies the weather, and records each
   generator's output (`TimeStepDoRun`).
4. The result is an hourly MW table per generator, split into solar and wind.

## Why it matters
- Converts gridded weather into generation numbers, hour by hour.
- Turns historical years (ERA5 quarter files) and forecast files alike into generation
  profiles for downstream studies.
- Feeds extreme-scenario and renewable-integration analysis.

## Series vs parallel
A runner can process it **in series** (slow, for testing) or **in parallel** (fast, many
sims at once). Output resolution is **generator-level**.

## Related
- [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · [how-to-analyze-results](../methods/how-to-analyze-results.md) · [pww-data](pww-data.md) · [Home](../index.md)


---

# ==== timestep-workflow.md ====

---
type: concept
domain: cross-cutting
topic: timestep
aliases: [timestep-workflow, time-step-simulation, timestep-engine, weather-to-mw]
tags: [timestep, simulation, powerworld, weather, renewables, pww, parallel]
---

# Concept: The weather-to-MW timestep workflow

## Abstract

The end-to-end chain that turns a weather file into hourly solar and wind output for
every renewable generator in a case: open the case, load a `.pww`, select the renewable
units, tell PowerWorld which fields to save, run its built-in TimeStep simulation, and
export per-generator CSVs. PowerWorld does the weather-to-MW conversion itself using
each unit's embedded PFW model. This is a quasi-static production study, **not** a
transient stability run.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation](timestep-simulation.md) · [pww-data](pww-data.md) · [copper-plate](copper-plate.md) · [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md)
- **Next:** [timestep-simulation-setup](../methods/timestep-simulation-setup.md) to write the code, then [how-to-analyze-results](../methods/how-to-analyze-results.md)
- **Deeper:** [time-step-simulation-backend](../references/time-step-simulation-backend.md)

## Content

### What it is, and what it is not

PowerWorld's TimeStep feature solves a sequence of independent steady-state points, one
per timestamp. It is a production-cost-style study, not dynamics: there is no swing
equation, no machine model, no sub-second behaviour. Transient stability is the `TS*`
family of script actions and a completely different setup. "Timestep simulation" here
means hourly snapshots across a weather series.

### The chain

1. **Copy the case to a temporary `.pwb`.** The run mutates the case; work on a copy so
   a failed run does not leave your original in a strange state.
2. **Open it** with `esapp`.
3. **Load weather** with `TimeStepLoadPWWRange` over the file's full time span, or
   `TimeStepLoadPWWRangeLatLon` to also crop to a lat/lon box at load time. Append further
   files with `TimeStepAppendPWW`, then assert the timepoint count. **Do not use plain
   `TimeStepLoadPWW` on Simulator 25:** on builds dated 2026-09-20 and 2026-09-25 it fails on
   every file with `Error With Loading PWWFile`, while `TimeStepLoadPWWRange` loads the same
   files (suspected PowerWorld issue, not yet confirmed: glitch `2026-10-20-timestep-loadpww-plain`). A failure of the plain form says nothing about the file.
4. **Select the renewable generators**, typically those whose fuel type contains `WND`
   or `SUN`. Only selected units produce output.
5. **Declare the fields to save** with `TimeStepSaveFieldsSet(GEN, ...)`. Fields not
   declared here are simply absent from the results, with no warning.
6. **Run** with `TimeStepDoRun()`. Debug a broken setup with
   `TimeStepDoSinglePoint()` first: it solves one timestamp and fails in seconds
   rather than after a long run.
7. **Export** with `TimeStepSaveResultsByTypeCSV`.

**Running contingencies hour by hour?** Set each hour with `TimeStepDoSinglePoint(...)`, then
call `CTGSetAsReference()` before `CTGSolveAll()`. Without it every hour is solved against an
older stored reference and returns the same results. Measured 2026-10-20 on build 2026-09-25:
three hours with about 2.7 GW to 7.6 GW of renewables gave identical answers until the
reference was reset (suspected, possibly by design: glitch `2026-10-20-ctg-reference-timestep`). See [reading-violationctg](../methods/reading-violationctg.md) (Trap 3b).

### PowerWorld does the conversion

You do not compute power curves. Each renewable unit carries an embedded **PFW** (Power
Flow Weather) model string, and PowerWorld applies it to convert weather into MW for
that unit. You supply weather and select units; the physics is already in the case.

If a unit produces nothing, the usual cause is that it has no PFW model, not bad weather
data.

**PWW and PFW are different things.** PWW is the weather data file; PFW is the
generator's weather-to-power model. The names are one letter apart. See
[pww-data](pww-data.md).

### Reading the output

The exported CSVs are not plain tables. Expect **eight metadata header rows** before the
data begins; read past them or every column parses as text. Timestamps commonly need
a timezone conversion, and the natural final step is splitting the table into a solar
file and a wind file.

Details in [how-to-analyze-results](../methods/how-to-analyze-results.md).

### Series and parallel

A series runner processes timestamps one at a time: slow, but its errors are legible.
A parallel runner using a process pool is much faster because each timestamp is
independent.

Develop against the series runner and switch to parallel for production. A process pool
failing on one timestamp out of eight thousand is hard to debug.

### Copper-plate cases

These studies often run on a copper-plate version of the case (transmission constraints
removed), because the question is usually "what could these renewables have produced?"
rather than "what could have been delivered?" See [copper-plate](copper-plate.md).

Decide which question you are asking before the run, or you will rerun it.

### Granularity

The workflow is generator-level. Aggregating to area or substation is a post-processing
step on the exported CSVs, not something to ask PowerWorld for during the run.


---

# ==== unloaded-ehv-stub-overvoltage.md ====

---
type: concept
domain: cross-cutting
topic: design
aliases: [unloaded-ehv-stub-overvoltage, floating-stub, ehv-stub-overvoltage, ferranti-rise,
  dead-end-ehv-overvoltage, line-charging-overvoltage, radial-ehv-line, open-end-rise]
tags: [powerworld, voltage, overvoltage, reactive-power, line-charging, topology, radial,
  islanding, case-quality, n-0]
---

# An unloaded EHV stub runs high, and only closing it fixes both of its problems

## Abstract

An extra-high-voltage (EHV) line that runs out to a dead end and carries almost no MW behaves like
an open-ended capacitor. Its own charging lifts the far end above the near end (the Ferranti
rise). If nothing at the far end can absorb Mvar, for example because the only unit there is
modelled with zero reactive range, the far end runs high in exactly the light-load dispatches
where the unit is off. The same topology also islands on the loss of its one link. Measured
2026-09-28 on a regional planning model: a tie closing the stub into a substation that still had
absorbing room fixed both problems. A reactor fixed only the voltage. A long tie to a substation
whose reactor was already at full output fixed neither.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [ltc-regulation-checks](../methods/ltc-regulation-checks.md) (the other intact-case
  overvoltage, which an LTC can reach) ·
  [violation-network-map](../methods/violation-network-map.md) (the radial-ties page finds the
  bridges and radial trees this shape sits on, and the voltage page shows the reactive balance
  around it) · [case-impedance-completeness](case-impedance-completeness.md) (a case with
  `LineC = 0` has no charging, so this rise cannot appear there; check that first) ·
  [adding-devices-esapp](../methods/adding-devices-esapp.md) (placing the reactor or tie once
  chosen)
- **Checked by:** the case-auditor's `base.floating_stub` rule

## Content

### The shape

One or two EHV substations hang off the meshed grid on a single line a few tens of miles long.
The only device at the far end is a solar or storage plant modelled with zero reactive range
(`GenMVRMax = GenMVRMin = 0`). When that plant is off (winter peak, spring minimum, a light-load
night) the line carries almost no MW. Its charging, `LineC` in per unit on the system base,
split half to each end, has nowhere to go, so the far end rises above the near end.

Measured 2026-09-28 on a regional planning model, intact case, five dispatches:

| dispatch | far-end voltage |
|---|---|
| plant off, line nearly unloaded | **1.06 – 1.08 pu** |
| plant running, current through the line | 1.02 – 1.03 pu |

The loss of either link islands the plant. An outage that islands a bus often solves with no
violations reported, because the stranded buses are dropped rather than flagged. So the
islanding half of this problem needs its own screen.

### Why the obvious levers do not reach it

- **Generator setpoints.** Walking every unit within six hops down by up to 0.05 pu cleared small
  overshoots elsewhere but left the stub above 1.05. Every unit near it was already pinned at
  its absorbing limit (`GenMVR = GenMVRMin`). The one unit with room was injecting: it
  regulated a 138 kV bus that sat below its setpoint while the 345 kV side floated high. A
  setpoint on a pinned unit moves nothing.
- **Shunt deadbands.** Lowering the switched-shunt bands (`SSVHigh`, `SSVLow`) by 0.02 pu across
  the area changed nothing measurable. The nearby reactors were already at full absorption
  (`SSNMVR = SSMinMVR`), and the capacitors nearby were holding up load taps.
- **A long tie to the biggest reactive substation.** A tie several tens of miles long to a
  substation with a large reactor did not clear it. The new line's own charging cancelled the
  benefit, and that reactor was already at full output. **Capability is not room.** Rank landing points by what
  they can still absorb, not by what they own.
- **A 138 kV tie** from the stub made it worse, by up to 0.005 pu. It adds a path and nothing
  that absorbs, and it relieves none of the 345 kV charging.

### What fixed it

An **EHV tie a few tens of miles long from the dead end into a nearby substation whose unit still
had absorbing room** brought the stub to 1.03–1.05 pu in all five dispatches and removed both
islanding outages. It works because it turns the stub into a loop through a substation that can
take the stub's surplus Mvar. A tie landing on the middle of the stub fixed the voltage but left
the far end on one line.

For comparison:

| design | voltage | islanding |
|---|---|---|
| EHV tie from the far end to a substation with room | fixed | fixed |
| a reactor of order 100 Mvar at the stub | fixed except one dispatch, barely over | not fixed |
| a two-way bank of similar size at the stub | same as the reactor while out of band; idle once back in | not fixed |
| long tie to a substation whose reactor was pinned | not fixed | not fixed |
| 138 kV tie | worse | not measured |

Neither the reactor nor the bank is wrong. The tie is the only single device that answers both
problems.

### The same physics at regional scale

Many short EHV ties in one region raise it even when no single tie does. Measured on the same
model with discrete controls frozen: closing on the order of ten radial trees in one light-load region
pushed tens more buses over 1.05 in one dispatch. Removing any one of those ties moved
the worst bus by under 0.001 pu. The rise is the sum of their charging. Check a batch of ties
as a set, in the lightest dispatch, not one at a time. Where a region already runs near the
limit, site absorbing capacity along with the ties.

### What the auditor can and cannot tell from one case

The shape is structural: a radial EHV line whose far side has no absorbing room. The rise is
dispatch-dependent. A case solved with the far-end plant running can sit in band while the
same case at light load sits above it, so a clean voltage on this shape in the case you have
does not mean the shape is safe. Check the lightest dispatch you study. Whether to
close the stub, add a reactor or accept it is a planning choice the case cannot make for you.

### How the case-auditor finds it

The `case-audit` engine's `base.floating_stub` rule (`skills/case-audit/engine/rules_stub.py`)
works on the solved case, read-only:

1. **Structure.** Over the connected buses and closed branches (parallel circuits are separate
   edges, so a double circuit is never a bridge), find the bridges. The meshed core is the largest
   2-edge-connected piece; each bridge's far side is the part away from it. A candidate is a bridge
   that is a line, with both terminals at EHV, whose far side is small. Along one radial chain only
   the bridge nearest the core is reported.
2. **Lightly loaded.** The bridge's `LineMaxPercent` is low, or, on an unrated bridge
   (`LineAMVA = 0`), its `|LineMW|` is.
3. **Rising.** The highest far-side EHV bus sits above the bridge's core-side end, and there is
   line charging to rise on (`LineC` summed over the far side and the bridge is above 0; a case
   with `LineC = 0` everywhere is a DC skeleton, which `base.dc_skeleton` reports instead).

Each finding carries the bridge's keys, the near and far voltages, whether the far end is above
its own high limit, the bridge's MW and loading, the far-side bus count, the charging in Mvar
(`sum(LineC) × Sim_Solution_Options.SBase`; `SBase` read 100 on both public cases probed
2026-09-30, and the engine reads it from each case rather than assuming it), the **absorbing
room** left on the far side (`GenMVR − GenMVRMin` over closed units plus `SSNMVR − SSMinMVR` over
closed shunts - room, not capability), and the far-side units with zero reactive range.

Numbers with no source, each a proposed default in `skills/case-audit/engine/thresholds.py`:
EHV means 300 kV and above (catches 345, 500 and 765, excludes 230); a far side of at most 50
buses; lightly loaded means under 10 % of rating, or under 10 MW when unrated; a rise of at least
0.005 pu. The rise is dispatch-dependent, so a stub that is in band on this dispatch is not
reported; a structure-only warning for it is not built. On Texas2k (182 buses at 500 kV) the rule
found none.


---

# ==== version-requirements.md ====

---
type: concept
domain: tooling
topic: scripting
aliases: [version-requirements, powerworld-version, simulator-version, compatibility, version-check]
tags: [version, compatibility, simulator, simauto, requirements, preflight]
---

# Concept: PowerWorld version requirements

## Abstract

Which PowerWorld version you need, how to find out which one you have, and what this
knowledge base was verified against. The core features were tested on **Simulator 24, build
24.2026.7.22**, and again on a **Simulator 25 beta, build 24.2026.9.25**. Every feature
behaved the same on both except `CTGAutoInsert`, a suspected regression on the beta. Field
availability and script-action behaviour both shift between releases, and they shift
*silently*.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [preflight-powerworld](../methods/preflight-powerworld.md) · [esapp-environment](esapp-environment.md) · [powerworld-simauto](powerworld-simauto.md) · [glossary](glossary.md)

## Content

### Find your version — three ways

**1. From Python, during preflight** (no admin rights needed):

```python
import win32com.client
from datetime import date, timedelta

sa = win32com.client.Dispatch("pwrworld.SimulatorAuto")
build = date(1899, 12, 30) + timedelta(days=int(sa.RequestBuildDate))
print("PowerWorld build date:", build.isoformat())
```

`RequestBuildDate` is a Delphi serial date (days since 1899-12-30), not a version number.
`46225` decodes to `2026-07-22`.

**Ask SimAuto for the release name too.** `sa.ProgramInformation[0]` returns
`('version', <major>, <build date>, <release label>)`. On a beta, measured 2026-10-21, it read
`('version', 24, 2026-09-25, '25 beta')`: a beta of the next release keeps the previous major
number, so report the label as well as the number.

**2. From the executable** (PowerShell), which gives the real version string:

```powershell
Get-ChildItem 'C:\Program Files\PowerWorld\Simulator*\pwrworld.exe' |
  ForEach-Object { $_.VersionInfo.ProductVersion }
# 24.2026.7.22
```

The format is `<major>.<year>.<month>.<day>`: major version 24, built 2026-07-22. A beta keeps
the old major: a Simulator 25 beta installed into the `Simulator 24` folder reports
`24.2026.9.25`. Use way 1's release label to tell them apart.

**3. From the registry**, which also reveals where SimAuto actually points:

```powershell
(Get-ItemProperty 'HKLM:\SOFTWARE\Classes\pwrworld.SimulatorAuto\CLSID').'(default)'
```

Then look up that CLSID's `LocalServer32` to see the exact `pwrworld.exe` being served.

**Watch for stale registry keys.** A machine can carry `Simulator 22` and `Simulator 23`
keys from previous installs while SimAuto actually serves Simulator 24. The CLSID lookup
is authoritative; the version-numbered keys are not.

### What this kit was verified against

| | |
|---|---|
| **Simulator** | 24, build `24.2026.7.22`; and a 25 beta, build `24.2026.9.25` (re-probed 2026-10-21) |
| **`esapp`** | 0.1.3, what the pages here were live-tested against. 0.2.1 is current and changes write behaviour; see [esapp-script-command-wrappers](esapp-script-command-wrappers.md) |
| **`TeamOverbyeWeather`** | 0.4.0; 0.4.2 on the 25 beta probe |
| **Python** | 3.13, 64-bit |
| **Platform** | Windows |

### Feature probe results

Both runs used a public 37-bus synthetic case, and every count matched.

| Feature | Pages | 24, build 2026-07-22 | 25 beta, build 2026-09-25 |
|---|---|---|---|
| AC power flow | [esapp-overview](../methods/esapp-overview.md) | OK | OK |
| DC mode | [power-flow-and-sensitivities](../demos/power-flow-and-sensitivities.md) | OK | OK |
| LODF | [lodf](lodf.md) | OK — 89 rows | OK — 89 rows |
| PTDF | [power-flow-and-sensitivities](../demos/power-flow-and-sensitivities.md) | OK — 89 rows | OK — 89 rows |
| Ybus | [esapp](esapp.md) | OK — (37, 37) sparse | OK — (37, 37) sparse |
| Jacobian | [esapp](esapp.md) | OK | OK — (74, 74) sparse |
| `CTGAutoInsert` | [contingency-and-aux](../demos/contingency-and-aux.md) | OK — 89 contingencies (see below) | **Suspected regression:** inserts 0 after the set is deleted; see glitch `2026-10-20-ctgautoinsert-zero-insert`. Workaround: write the contingency aux and `LoadAux` it, as in [new-device-contingency-aux](../methods/new-device-contingency-aux.md) |
| `CTGSolveAll` | [reading-violationctg](../methods/reading-violationctg.md) | OK — 12 violation rows | OK — 12 violation rows |
| `CreateData` (Branch) | [adding-a-device](../demos/adding-a-device.md) | OK — 89 → 90 | OK — 89 → 90 |
| `SaveCase` script action | [save-powerworld-case](../methods/save-powerworld-case.md) | OK | OK — file written |
| `LimitSet` `SetData` | [powerworld-limitset-setdata](../methods/powerworld-limitset-setdata.md) | OK | OK — read back |
| GIC | [gic](gic.md) | OK | OK |
| `LoadAux` | [contingency-and-aux](../demos/contingency-and-aux.md) | OK — merged 89 → 94 | OK — merged 89 → 94 |
| TimeStep family | [timestep-workflow](timestep-workflow.md) | Prerequisite error on an empty case (expected) | Prerequisite error on an empty case (expected) |

The 24 `CTGAutoInsert` row proves less than it looks: the case already held 89
contingencies, so the count could not move whether the call worked or not. Test it after
deleting the existing set, which is what the beta run did.

In the TimeStep row, `TimeStepClearResults` raised `PowerWorldPrerequisiteError` because
there were no TimeStep results to clear. That is the feature working, not a version problem. Prerequisite errors are about **case state**,
not capability.

### Minimum versions

**Not tested here.** Only Simulator 24 and a 25 beta were tested, nothing older.

What can be said:

- The core surface (power flow, contingency analysis, `CreateData`, `SaveCase`,
  sensitivities, TimeStep, GIC) has been present in Simulator for many releases. It is
  very unlikely you need 24 specifically.
- The [aux-script-commands](../references/aux-script-commands.md) index was compiled against Simulator 24's action set. Older
  releases have fewer actions; newer ones may add some.
- **If you are on an older version and something in this kit fails, the version is a
  plausible cause.** Say so rather than assuming the page is wrong, and if you confirm
  it, open an issue on the repository.

### Known version differences

A row goes here only when a behaviour was seen on one version and not another. **Suspected**
rows are not yet confirmed as PowerWorld's own behaviour, so do not treat them as fact; use
the workaround.

| Behaviour | Seen on | Status | Workaround |
|---|---|---|---|
| `CTGAutoInsert` returns OK but inserts 0 contingencies after the set is deleted | 25 beta, build 2026-09-25 | suspected, see glitch `2026-10-20-ctgautoinsert-zero-insert` | Write the contingency aux and `LoadAux` it: [new-device-contingency-aux](../methods/new-device-contingency-aux.md) |
| Plain `TimeStepLoadPWW` fails with `Error With Loading PWWFile` | builds dated 2026-09-20 and 2026-09-25 | suspected, see glitch `2026-10-20-timestep-loadpww-plain` | `TimeStepLoadPWWRange` loads the same files: [timestep-workflow](timestep-workflow.md) |

### Version-sensitive behaviour to watch for

These shift between releases and fail *silently*:

| Behaviour | Why version matters |
|---|---|
| **Field availability** | A field can exist and return blank in one release and be populated in another. Derived weather fields have done exactly this. Check for all-null columns before trusting any derived field |
| **Script action names and arguments** | Actions are added, and argument lists occasionally change. An unrecognised action is not always a loud failure |
| **Required key fields for `CreateData`** | The required set is version-specific. A call that worked on an older release can silently no-op on a newer one, which is why [adding-a-device](../demos/adding-a-device.md) insists on asserting the object count |
| **Default limit sets and monitoring** | Defaults change, which changes what counts as a violation without changing your code |

### The SimAuto licence is not a version question

**SimAuto is licensed separately from Simulator**, and having the newest Simulator does not mean you have automation. A perfect
Simulator 24 install can fail every script in this kit.

On a working install you will see `PWSimAutoService.exe` alongside `pwrworld.exe` in the
Simulator directory, and `Dispatch("pwrworld.SimulatorAuto")` will succeed. If it raises,
see [preflight-powerworld](../methods/preflight-powerworld.md). No code change fixes a licence.

### What to do at the start of a session

Run [preflight-powerworld](../methods/preflight-powerworld.md). It reports the build date along with the five checks, so
the version is on the record before any analysis is written. If a later result looks
wrong, that line is the first thing to check.


---
