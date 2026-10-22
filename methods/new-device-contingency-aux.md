---
type: method
domain: tooling
topic: contingency
aliases: [contingency-aux, ctgautoinsert, bgreportlimits, monitored-areas, ctgelement-subdata, new-device-contingency]
tags: [esapp, powerworld, simauto, contingency, aux, n-1, limit-monitoring, areas, synth2k]
---

# Building a Contingency Set for Chosen Devices, and an AUX That Carries It

## Abstract

How to turn **a list of devices** (e.g. the branches and generators that are new in a
planning case) into a PowerWorld contingency set, restrict violation reporting to **the
areas you care about**, and ship both as one `.aux` file that loads into the case, without
ever saving the case. The mechanism is **autoinsert-then-restrict**: run the case's own
`CTGAutoInsert`, match your devices to the labels it produced, and write only those out.
Hand-writing `Contingency` records from scratch invents labels PowerWorld would not use.

Five things here are silent failures, each live-measured on `Synth2k_case` on 2026-08-17.
Each produces a plausible wrong answer instead of an error:

> **`ElementType`, `DeleteExisting` and `Handle3WXF` are *concise* names.** PowerWorld's
> object-field export lists two names per field, and these three appear only in the Concise
> Variable Name column. Grep the export for them and you find nothing, which reads as "the
> field does not exist". Their full variable names are `CtgAutoInsElementType`,
> `CtgAutoInsDeleteExistCtgs` and `Include3WXfifFoundWithXf`. Both spellings are accepted;
> search the export on either column before concluding a field is missing.

1. **`CTG_AutoInsert_Options` rejects `ElementType=GEN` without complaining** and leaves it
   at `BRANCH` (suspected, possibly by design: glitch `2026-10-20-ctgautoinsert-gen-ignored`). You ask for 743 generator outages and get 3,911 branch ones.
2. **The `CTGElement` SUBDATA action string must be quoted.** Unquoted, PowerWorld parses
   the *first* contingency and drops the other 690 with no error.
3. **`LoadAux` needs an ABSOLUTE path.** A relative one resolves against `pwrworld.exe`'s
   working directory, not yours.
4. **`LoadAux` merges, it does not replace.** Loading a contingency list into a case that
   already has a set gives you both.
5. **`Ctg_Options.CTG_ReportMonitoredAreas` is a decoy.** It only affects text-file report
   writing. The real area switch is `Area.BGReportLimits`.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Input from:** [comparing-planning-cases](../demos/comparing-planning-cases.md) — produces the device list this method turns into a contingency set
- **Across:** [reading-violationctg](reading-violationctg.md) (what you read back after solving this set) ·
  [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the limit *thresholds*; this page is the limit *scope*) ·
  [save-powerworld-case](save-powerworld-case.md) · [adding-devices-esapp](adding-devices-esapp.md) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md)
- **Deeper:** [aux-script-commands](../references/aux-script-commands.md) for the SCRIPT actions.

## Content

### Step 1 — build the full N-1 set in memory, then keep only what you want

```python
pw.esa.RunScriptCommand("EnterMode(EDIT);")
pw.esa.RunScriptCommand("Delete(Contingency);")
pw.esa.RunScriptCommand(
    "SetData(CTG_AutoInsert_Options, "
    "[ElementType, DeleteExisting, Handle3WXF], [BRANCH, YES, INSERT3WXF]);")
pw.esa.RunScriptCommand("CTGAutoInsert;")
pw.esa.RunScriptCommand("EnterMode(RUN);")
```

> **On Simulator 25, build dated 2026-09-25, this exact block inserted 0 contingencies and
> reported success.** Suspected PowerWorld issue, not yet confirmed: the cause may still turn
> out to be a setting. The workaround below holds either way. The condition is
> `CTGAutoInsert` run straight after `Delete(Contingency)`. Measured 2026-10-19 on a public
> synthetic grid. The same block gave the full branch set on 2026-08-17 (the counts below),
> so the behaviour changed with the newer build, not through misuse.
> [powerworld-study-options](../references/powerworld-study-options.md) saw zero inserts on a
> Simulator 25 build on 2026-09-28 as well.
>
> **Assert the count. Never trust the return.** Read `Contingency` back after every
> `CTGAutoInsert` and fail on zero, or on any count far below the case's in-service branches
> above 69 kV. When it comes back empty, build the set yourself. Write the contingency aux
> in the Step 3 shape, one record per branch, with every `CTGElement` action string quoted.
> `LoadAux` it with an absolute path, then assert the loaded `CTGLabel` count equals the
> number you wrote. That path worked on the same build. Your labels will not be
> autoinsert's, so match devices by unordered bus pair plus circuit (Step 2), never by label.

`ElementType` is `BRANCH` or **`GENERATOR`** — **never `GEN`**. `GEN` is accepted by the
parser, silently ignored, and leaves the previous value in place (suspected, possibly by design:
glitch `2026-10-20-ctgautoinsert-gen-ignored`). Use `GENERATOR` either way:

```python
pw.esa.RunScriptCommand("SetData(CTG_AutoInsert_Options,[ElementType],[GEN]);")
pw.esa.GetParametersSingleElement("CTG_AutoInsert_Options", ["ElementType"], [""])
# -> 'BRANCH'          <- the write did not happen, and nothing said so
# 'GENERATOR' and 'Gen' both -> 'GENERATOR'
```

**Always read the option back and assert it** before `CTGAutoInsert`. `Handle3WXF` applies
to branches only. On Synth2k case 3 this yields **3,911 branch** contingencies (= its branch count)
and **743 generator** ones (= its generator count).

### Step 2 — match your devices to the labels autoinsert chose

Read `ContingencyElement` with an explicit field list
(`CTGLabel, BusNum, BusNum:1, ElementID, Object, Action`):

| device | `Object` | `BusNum` / `BusNum:1` | `ElementID` | example `CTGLabel` |
|---|---|---|---|---|
| branch | `BRANCH 1001 1064 1` | both ends | **the circuit ID** | `L_001001ODESSA20-001064ODESSA30C1` |
| 3W xfmr | `BRANCH …` | both ends | circuit | `T_…` prefix |
| generator | `GEN 1004 1` | bus / **`0`** | **the `GenID`** | `G_001004ODONNELL11U1` |

Two matching rules, both inherited from [reading-violationctg](reading-violationctg.md):

- **`ContingencyElement` has no `LineCircuit`.** The circuit ID is `ElementID` (verified on
  a 3-circuit bank: `'1'`, `'10'`, `'20'`). For generators `ElementID` is the `GenID`.
- **Match the bus pair UNORDERED and never parse the `CTGLabel`.** A case may store a branch
  either way round, and the label embeds *truncated* substation names, which collide.

### Step 3 — write the AUX, in PowerWorld's own shape

Do not guess the format. PowerWorld will export the set it is holding:

```python
# Write ONLY through RunScriptCommand -- the COM SaveCase method silently no-ops,
# see methods/save-powerworld-case.md. This applies to every PowerWorld file write, not
# cases: SaveData through RunScriptCommand produced a real 523 KB file here.
# NOTE: SaveContingencies is NOT a script command ("Unknown script command").
# The filter argument is a bare string; the sort lists MUST be bracketed.
pw.esa.RunScriptCommand(
    f'SaveData("{abs_path}",AUX,Contingency,[CTGLabel,CTGSkip],[CTGElement],"",[],[],YES);')
```

which writes (3,911 contingencies → 523 KB):

```
Contingency (Name,Skip)
{
"L_001001ODESSA20-001064ODESSA30C1" "NO "
   <SUBDATA CTGElement>
     "BRANCH 1001 1064 1 OPEN" "" CHECK 0 NO
   </SUBDATA>
}
```

Copy that shape when writing a **subset** by hand in Python. `Contingency (CTGLabel,CTGSkip)`
works as the header too. **The action string must be quoted**: written as bare
`BRANCH 1001 1064 1 OPEN`, a 691-contingency file loads as **one** contingency and the load
reports success.

### Step 4 — scope the violations to your areas, in the same file

`Area.BGReportLimits` — *"Set to NO to not monitor elements (buses, branches or
interfaces)"* — is PowerWorld's own limit-monitoring switch (the `Zone` object carries it
too). Write every area, not just yours, or you inherit whatever the case already restricted:

```
Area (AreaNum,BGReportLimits)
{
"1" "NO"
"5" "YES"
}
```

Measured on Synth2k case 3 (8 areas, 2,000 buses, 3,911 branches), reading the **effective**
flags `Bus.BusMonEle:1` / `Branch.LineMonEle:1`, not the requested ones:

| monitored areas | buses monitored | branches monitored |
|---|---|---|
| all 8, as shipped | 2000 | 3878 |
| `5` (North Central) | 483 = area 5 exactly | 866 = its own 822 **+ 44 ties** |
| `3, 5` | 630 | 1341 |

**A bus is monitored when its area is; a branch when EITHER end is.** Tie lines into the
region are included automatically. That is the opposite of the `ViolationCTG.AreaNum` trap
in [reading-violationctg](reading-violationctg.md), where a naive filter *drops* them. Related knobs found in the
same field-list dig: `Area.BGReportLimMinKV` / `BGReportLimMaxKV` (monitor only a kV band)
and `Branch.LineMonEle` / `Bus.BusMonEle` (switch off one device).

**Monitoring a region is not testing it.** `BGReportLimits` decides where violations are
*reported*; the contingency list decides what is *tripped*. A case often ships with a list
built for one area. Turn monitoring on for a second area, solve, and you get a clean report
for an area none of whose elements was ever outaged. That is a silent wrong answer, and it
reads exactly like a passing N-1. Before solving "N-1 for area X":

```python
import pandas as pd
from esapp.components import Bus

el = pw.esa.GetParametersMultipleElement("ContingencyElement", ["CTGLabel", "BusNum", "BusNum:1"])
area = {int(r["BusNum"]): int(r["AreaNum"]) for _, r in pw[Bus, ["AreaNum"]].iterrows()}
hit = {}                                   # area -> contingencies with an element touching it
for _, r in el.iterrows():
    for b in (r["BusNum"], r["BusNum:1"]):  # BusNum:1 reads None for a generator
        if pd.notna(b) and int(b) in area:
            hit.setdefault(area[int(b)], set()).add(r["CTGLabel"])
for x in asked_areas:
    assert hit.get(x), f"no outage touches area {x}: the list does not test it"
```

Non-zero is the floor, not the test. Measured 2026-10-20 on a 2,000-bus synthetic case whose
shipped list of 176 outages was built for one area: a neighbouring area still counted 12,
all tie lines on the boundary. So compare each count with that area's in-service branches
above 69 kV. A count that is a small fraction of them means the area is not tested. When the
list does not cover an area, build the area's set (Step 1) and load it alongside the
shipped one.

### Verify it worked

Load the file back into the open case and assert. Never trust the write:

```python
pw.esa.RunScriptCommand("EnterMode(EDIT);")
pw.esa.RunScriptCommand("Delete(Contingency);")     # LoadAux MERGES; delete to replace
pw.esa.RunScriptCommand(f'LoadAux("{absolute_path}", NO);')
pw.esa.RunScriptCommand("EnterMode(RUN);")
```

Assert **three** things, because each failure looks like success:

1. the loaded `CTGLabel` set equals what you wrote (a parse failure loads a prefix);
2. the `ContingencyElement` **count** equals what you wrote (a contingency with no element
   loads fine and outages nothing, which reads as "the grid survives everything");
3. every area's `BGReportLimits` came back as intended.

### Gotchas beyond the five in the Abstract

- **A device that gets no contingency is normal, not a bug.** Autoinsert requires both ends
  ≥ 69 kV **and** `LineStatus == 'Closed'`, and `Handle3WXF=INSERT3WXF` collapses a
  3-winding transformer's three branch rows into **one** contingency, so three device rows
  legitimately map to one label. Report the bucket with a per-device reason; do not abort.
- **The dominant unmatched cause on a real planning model is the 3-winding transformer's
  star bus, and it presents as a kV failure, not as a 3WXF one.** A 3W transformer is
  modelled as three branches meeting at a **fictitious star/tertiary bus carried at ~1 kV
  nominal**, so the winding branches touching it fail the 69 kV floor and autoinsert never
  builds a branch contingency for them (measured 2026-08-17 on regional planning cases:
  roughly two in five new branches). Do not read that bucket as missing coverage. The single
  collapsed `T_…` contingency covers the transformer itself. What is absent is a separate
  outage of an internal winding, which is not a real N-1 event.
- **`GetFieldList` on an object name that does not exist can fault `pwrworld.exe`** with an
  access violation rather than returning an error. Do not fuzz object names.
- Autoinsert labels are **not** unique-safe to parse: `L_`/`T_`/`G_` + truncated substation
  names. Treat them as opaque keys.
