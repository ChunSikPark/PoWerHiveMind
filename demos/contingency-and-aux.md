---
type: method
domain: tooling
topic: contingency
aliases: [demo-contingency, n-1-demo, aux-generation-demo, ctg-demo, filter-demo]
tags: [demo, contingency, n-1, aux, filter, esapp, worked-example]
---

# Demo: N-1 contingency analysis, and generating an aux file

## Abstract

Running N-1 from nothing on the public synthetic Synth40 case (37 buses), then **writing a filter and contingency
`.aux` automatically** from the analysis result and loading it back. All numbers are from
an actual run: 89 auto-inserted contingencies, 12 violations, then 5 targeted
contingencies generated and merged.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [reading-violationctg](../methods/reading-violationctg.md) · [new-device-contingency-aux](../methods/new-device-contingency-aux.md) · [aux-script-commands](../references/aux-script-commands.md) · [handling-errors](../methods/handling-errors.md)

## Content

### The user's prompts

> *"Run N-1 on everything and tell me what breaks."*
> *"Build me a contingency file for the five most loaded lines."*

### Part 1 — N-1 from scratch

Three script actions, in this order:

```python
from esapp import PowerWorld
from esapp.components import Contingency, ViolationCTG

pw = PowerWorld(r"C:\path\to\Synth40.pwb")
pw.pflow()

pw.esa.RunScriptCommand("CTGClearAllResults")   # do not skip this
pw.esa.RunScriptCommand("CTGAutoInsert")
pw.esa.RunScriptCommand("CTGSolveAll")

print(f"auto-inserted {len(pw[Contingency])} contingencies")
```

```
auto-inserted 89 contingencies
```

**`CTGClearAllResults` first, always.** Contingency results persist inside the `.pwb`, so
a freshly opened case can hand you results from someone else's run last month. They look
exactly like yours.

### Reading the violations

```python
v = pw[ViolationCTG, ["CTGLabel", "ObjectType", "LimViolPct",
                      "LimViolValue", "LimViolLimit"]]
print("violation rows:", len(v))
```

```
violation rows: 12
L_000019PEARLCITY69-000023WA   val=100.525  lim=100.300  pct=100.224
```

> **That field list is Python-side only. Do not paste it into an aux `SaveData`.**
> `ViolationCTG` has no `ObjectType` in the aux object-field vocabulary; the violation
> category there is **`LimViolCat`** (concise `LV_Type`). Asking an aux for `ObjectType`
> produces a `Warning:` rather than an error, so the column is silently missing and the run
> still reports success. A field list verified against the export, with no warnings:
> `[CTGLabel,LimViolID:1,LimViolLimit,LimViolValue,LimViolPct,LimViolCat,BusNum,BusNum:1]`.
> The aux keys are `CTGLabel` and `LimViolID:1`. See
> [aux-file-mode](../methods/aux-file-mode.md).

Three things to know before you interpret this:

- **A bare read returns 2 of 15 columns.** Ask for the fields you need by name, or you
  get `CTGLabel` and an id and nothing useful.
- **`pw[ViolationCTG, :]` returns 394 columns** on this case. Never do that casually.
- **Repeated labels are usually parallel circuits**, not duplicates — the same
  PEARLCITY–WAIPAHU corridor appearing several times. Check before reporting a data
  problem.

Here the worst violation is a 69 kV line at **100.22%** of its 100.3 MVA rating: real,
but marginal. Say "marginally over" rather than "overloaded", because those mean
different things to a planner.

More traps — polarity, tie-line `AreaNum` reading 0, `LimViolLimit` being the branch's
MVA rating rather than 100 — are in [reading-violationctg](../methods/reading-violationctg.md).

### Part 2 — generate an aux file automatically

The user wants a contingency set for the five most loaded lines. Build it from the solved
case rather than by hand:

```python
from pathlib import Path
from esapp.components import Branch

br = pw[Branch, ["LineMVA", "LinePercent", "LineStatus"]]
top = br.sort_values("LinePercent", ascending=False).head(5)

def label(r):
    return f'L_{int(r["BusNum"])}_{int(r["BusNum:1"])}_{str(r["LineCircuit"]).strip()}'

lines = ["// auto-generated contingency + filter set", ""]

lines += ["FILTER (Filter, ObjectType, FilterLogic, FilterPre, Enabled)", "{",
          '"HighLoad" "Branch" "AND" "NO" "YES"', "}", ""]

lines += ["CONTINGENCY (Name, Skip)", "{"]
lines += [f'"{label(r)}" "NO"' for _, r in top.iterrows()]
lines += ["}", ""]

lines += ["CONTINGENCYELEMENT (Contingency, Object, Action, Status)", "{"]
for _, r in top.iterrows():
    obj = f'BRANCH {int(r["BusNum"])} {int(r["BusNum:1"])} {str(r["LineCircuit"]).strip()}'
    lines.append(f'"{label(r)}" "{obj}" "OPEN" "CHECK"')
lines += ["}"]

out = Path(r"C:\path\to\demo_ctg.aux")     # absolute
out.write_text("\n".join(lines), encoding="utf-8")
```

What it produced:

```
// auto-generated contingency + filter set

FILTER (Filter, ObjectType, FilterLogic, FilterPre, Enabled)
{
"HighLoad" "Branch" "AND" "NO" "YES"
}

CONTINGENCY (Name, Skip)
{
"L_27_29_1" "NO"
"L_19_23_2" "NO"
"L_19_23_3" "NO"
"L_19_23_1" "NO"
"L_19_23_4" "NO"
}
```

565 bytes.

### Loading it back

```python
before = len(pw[Contingency])
pw.esa.RunScriptCommand(f'LoadAux("{out}", YES)')
after = len(pw[Contingency])
print(f"contingencies before: {before}\nafter: {after}  (added {after - before})")
```

```
contingencies before: 89
after: 94  (added 5)
```

**Four rules the aux format will punish you for breaking:**

1. **Absolute paths.** A relative path resolves against PowerWorld's working directory,
   not your script's.
2. **`LoadAux` merges.** It does not replace. Loading twice duplicates everything —
   which is exactly why the count check above matters.
3. **Quote the action string.** An unquoted `CTGElement` action loads only the first
   contingency and silently drops the rest.
4. **`ElementType=GEN` is silently ignored.** The keyword is `GENERATOR`.

And a fifth that will confuse you later: **PowerWorld trims whitespace from `CTGLabel`
on load**, so the label you wrote is not always the label you read back. Do not match on
labels you have not round-tripped.

### Verify, do not assume

```python
assert after - before == 5, "LoadAux merged the wrong number of contingencies"
```

An aux that fails to parse can leave the case unchanged without raising. Count.

### What to report back

> Auto-inserted **89** N-1 contingencies and solved them all. **12 violations**, the worst
> a 69 kV PEARLCITY–WAIPAHU circuit at **100.22%** of its 100.3 MVA rating — marginally
> over, not severe.
>
> Also generated `demo_ctg.aux` with a `HighLoad` branch filter and 5 targeted
> contingencies for the most loaded lines, and confirmed it loaded: 89 → 94.
>
> The case was not saved. The aux is on disk if you want to reuse it.
>
> Pages used: `methods/reading-violationctg.md`, `methods/new-device-contingency-aux.md`,
> `references/aux-script-commands.md`.
