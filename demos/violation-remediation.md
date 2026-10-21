---
type: method
domain: tooling
topic: contingency
aliases: [violation-remediation, remediation, fix-violations, reinforcement-study, n-1-remediation]
tags: [demo, remediation, contingency, n-1, reinforcement, esapp, worked-example]
---

# Demo: Violation remediation — diagnose, propose, test, rank

## Abstract

The full study, not a readout: find the N-1 violations, work out *why* they happen,
propose candidate reinforcements, test each one independently, and rank them by measured
effect. Real numbers from the public synthetic Synth40 case (37 buses). The headline result is one you cannot reach
by intuition — **two of five plausible reinforcements made the system worse**, and a
third reduced the violation count while making the worst violation more severe.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [reading-violationctg](../methods/reading-violationctg.md) · [adding-devices-esapp](../methods/adding-devices-esapp.md) · [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) · [contingency-and-aux](contingency-and-aux.md) · [handling-errors](../methods/handling-errors.md)

## Content

### The user's prompt

> *"Run N-1, work out what's wrong, and tell me what to build to fix it."*

That is a study, not a query. Everything below is what answering it properly looks like.

### Step 1 — measure the baseline

```python
from esapp import PowerWorld
from esapp.components import Bus, Branch, ViolationCTG

def n1(pw):
    """Solve N-1 and return (violation rows, worst severity as % of limit)."""
    pw.esa.RunScriptCommand("CTGClearAllResults")
    pw.esa.RunScriptCommand("CTGSolveAll")
    v = pw[ViolationCTG, ["CTGLabel", "LimViolValue", "LimViolLimit"]]
    worst = float((v["LimViolValue"] / v["LimViolLimit"] * 100).max()) if len(v) else 0.0
    return len(v), worst

CASE = r"C:\path\to\Synth40.pwb"
pw = PowerWorld(CASE)
pw.pflow()
pw.esa.RunScriptCommand("CTGClearAllResults")
pw.esa.RunScriptCommand("CTGAutoInsert")

base_n, base_w = n1(pw)
print(f"BASE: {base_n} violation rows, worst {base_w:.2f}% of limit")
```

```
BASE: 12 violation rows, worst 100.22% of limit
```

**Track two numbers, not one.** Count and severity move independently, and a change that
improves one can degrade the other — as Step 4 shows.

### Step 2 — diagnose before proposing anything

Do not jump to a fix. Ask which contingencies are producing the violations:

```python
v = pw[ViolationCTG, ["CTGLabel", "LimViolValue", "LimViolLimit"]]
print(v["CTGLabel"].astype(str).str.strip().unique())
```

```
L_000019PEARLCITY69-000023WAIPAHU69C1
L_000019PEARLCITY69-000023WAIPAHU69C2
L_000019PEARLCITY69-000023WAIPAHU69C3
L_000019PEARLCITY69-000023WAIPAHU69C4
```

All twelve violations come from **one corridor**: the four parallel 69 kV circuits
between PEARLCITY (bus 19) and WAIPAHU (bus 23). Circuits C1 through C4.

That is the whole diagnosis. Losing any one of the four pushes the surviving three over
their limit. This is not twelve problems; it is **one problem seen four times**, and it
tells you exactly where reinforcement belongs.

Reporting "12 violations" without this step is a readout. Reporting "the 19–23 corridor
is N-1 insecure against loss of any of its four parallel circuits" is an answer.

### Step 3 — test candidates independently

Each candidate is tested on a **fresh case**, not stacked onto the previous one.
Otherwise you measure combinations while believing you are measuring individuals.

```python
CANDIDATES = [(19, 23), (27, 29), (19, 25), (23, 26), (2, 26)]
results = []

for frm, to in CANDIDATES:
    p = PowerWorld(CASE)                 # fresh every time
    p.pflow()
    p.esa.RunScriptCommand("CTGClearAllResults")
    p.esa.RunScriptCommand("CTGAutoInsert")

    nv = {int(r["BusNum"]): r["BusName_NomVolt"]
          for _, r in p[Bus, ["BusName_NomVolt"]].iterrows()}

    n0 = len(p[Branch])
    p.edit_mode()
    p.esa.CreateData(
        "Branch",
        ["BusNum", "BusName_NomVolt", "BusNum:1", "BusName_NomVolt:1", "LineCircuit",
         "LineR", "LineX", "LineAMVA", "LineAMVA:1", "LineAMVA:2", "LineStatus"],
        [frm, nv[frm], to, nv[to], "R1", 0.01, 0.05, 150.0, 150.0, 150.0, "Closed"])
    p.run_mode()

    if len(p[Branch]) - n0 != 1:         # the guard that makes this trustworthy
        print(f"{frm}->{to} SKIPPED - CreateData no-op")
        p.close()
        continue

    p.pflow()
    n, w = n1(p)
    results.append((f"{frm}->{to}", n, w, n - base_n))
    p.close()
```

**The `!= 1` guard is not optional.** Without it, a silently skipped `CreateData` yields
"this reinforcement changes nothing" — a confident, completely wrong recommendation. See
[adding-a-device](adding-a-device.md).

### Step 4 — the results, and the surprise

```
candidate      viol rows   worst %   delta
19->23                 2    100.19     -10
27->29                15    100.23      +3
19->25                 7    105.76      -5
23->26                 4    102.05      -8
2->26                 13    100.23      +1
```

Ranked:

| Rank | Reinforcement | Violations | Worst | vs base |
|---|---|---|---|---|
| 1 | **19→23** | **2** | 100.19% | **−10** |
| 2 | 23→26 | 4 | 102.05% | −8 |
| 3 | 19→25 | 7 | **105.76%** | −5 |
| 4 | 2→26 | 13 | 100.23% | **+1** |
| 5 | 27→29 | 15 | 100.23% | **+3** |

Three findings worth more than the ranking itself:

**Two candidates made it worse.** Adding a line to 2→26 or 27→29 *increased* violations,
by 1 and 3. Reinforcing a network can redistribute flow onto elements that were
previously fine — the same intuition failure Braess's paradox describes. **This is why
you test rather than reason.** An agent that proposed 27→29 because it was the most
loaded branch would have recommended making the system worse.

**Count and severity can disagree.** 19→25 removes 5 violations but pushes the worst one
from 100.22% to **105.76%**. Fewer problems, each one worse. Which is preferable is a
planning judgement, not an arithmetic one — so present both numbers and let the user
decide.

**The diagnosis predicted the winner.** Step 2 said the 19–23 corridor was the problem;
reinforcing 19–23 directly was best by a wide margin. Diagnosing first is not ceremony,
it is what makes the candidate list intelligent instead of a sweep.

### What to report back

> **Diagnosis.** All 12 N-1 violations come from a single corridor: the four parallel
> 69 kV circuits between PEARLCITY (19) and WAIPAHU (23). Losing any one overloads the
> surviving three. One problem, seen four times.
>
> **Recommendation.** A new 150 MVA circuit on **19→23** takes violations from 12 to
> **2** and drops the worst from 100.22% to 100.19%. Best of the five tested.
>
> **Alternative.** 23→26 gets to 4 violations — worth considering if a fifth parallel
> circuit on an existing corridor is undesirable for right-of-way or common-mode reasons.
>
> **Do not build 27→29 or 2→26.** Both make N-1 *worse* (+3 and +1). 27→29 is the most
> loaded branch in the base case, so it is the intuitive choice and it is wrong.
>
> **Caveat.** 19→25 removes 5 violations but raises the worst to 105.76%. If your
> criterion is severity rather than count, it is a bad option despite the improvement.
>
> All five were tested independently from a clean case, and each device creation was
> verified by branch count. Nothing was saved to disk.
>
> Pages used: `methods/reading-violationctg.md`, `methods/adding-devices-esapp.md`,
> `demos/contingency-and-aux.md`.

### What makes this a study and not a query

- The **diagnosis** turned 12 symptoms into 1 cause
- Candidates were **tested, not argued** — and 2 of 5 refuted the intuition
- **Two metrics** were tracked, because they disagreed
- Every device creation was **verified**, so no result rests on a silent no-op
- The recommendation includes what **not** to build, which is often the more valuable half

### Going further

This loop generalises. The same shape covers redispatch instead of reinforcement
([applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md)), adjusting limit monitoring
([powerworld-limitset-setdata](../methods/powerworld-limitset-setdata.md)), scoring a large candidate set by severity rather than
count ([ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md)), and restricting contingencies to a chosen
device list ([new-device-contingency-aux](../methods/new-device-contingency-aux.md)).

For a weather-driven study — where the violations depend on the hour rather than a single
snapshot — the same diagnose-propose-test-rank loop runs on top of
[timestep-workflow](../concepts/timestep-workflow.md).
