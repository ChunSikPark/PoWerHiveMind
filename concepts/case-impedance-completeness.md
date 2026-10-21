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
lines** — undetected because every consumer up to that point was DC. **Check X/R before
trusting any case you did not build**, and especially before promising anyone an AC study.

## Connections

- **Up:** [Home](../index.md)
- **Found in:** a real-power planning study — the Synth9k 2031 case, 2026-08-18 — and
  independently confirmed on a second lineage the same day: `LineR <= 1e-6`
  and `LineC == 0` on **97.5%** of `Synth9k_case` and
  **100.0%** of `Synth8k_draft` (median X/R 100,010 and 113,465), so the five
  scenario cases built from them in [applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md) inherit it
- **💡 Applies to:** any study whose input is exactly such a case · synthetic case
  construction, where the handoff between build stages is where this is introduced · case
  diffing, since a diff that ignores R/C will not see it · any statistics computed over a case's branches · any project
  that receives a `.pwb` from another project or vintage
- **Across:** deriving a quantity by ratio (a ratio on a placeholder zero stays zero —
  check this first) · validating any produced artifact (same family: the artifact exists, but is
  it real?)

## Content

### The check

One line, and it is decisive:

```python
xr = (br.LineX / br.LineR.replace(0, np.nan)).median()      # closed, non-transformer lines
```

| median X/R | verdict |
|---|---|
| **2 – 20** | normal overhead transmission |
| **> 1000** | R is placeholder. The case cannot do losses, and AC will not mean anything. |
| **74,195** | what the Synth9k 2031 case actually measured |

Alongside it, count `LineC == 0`. Legitimate zeros exist — genuine intra-substation bus ties,
thousands of them in this case — so compare the count against the number of zero-length branches
rather than expecting zero.

### Why it survives so long

**DC power flow reads only `X`.** Losses, charging, voltage and reactive power are the only
things that read `R` and `B`, and none of them appear in a DC pipeline. So a case can pass
through case-building, dispatch, DC screening and a conductor-planning loop with two-thirds of
its impedance missing, and every stage reports success.

The failure surfaces only when someone finally runs AC — typically a different person, in a
different project, months later, who then debugs *their* code.

### The trap inside the trap

A conductor-resizing or reinforcement loop **does not fix this**, even though it writes
impedance. It only writes R/X/C on the lines it upgrades — 2.8% of the lines in the Aug-13
Synth9k run. Running it and declaring the case AC-ready is exactly wrong: you get a case
that is 97% DC-skeleton and 3% real, with **no way to tell the two apart** by inspection.

### The fix is usually a restore, not a model

Do not model R and B back in if they exist somewhere. In this case the same branch keys (more than 10k)
had healthy impedance in an older vintage of the same network, whose `X` agreed with the
current case on **96.2%** of lines — so the repair was a keyed copy of R and C, not a
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

The 2031 case solved DC fine throughout. Convergence is not evidence of a complete model — it
is evidence that the subset of the model your solver reads is self-consistent.

