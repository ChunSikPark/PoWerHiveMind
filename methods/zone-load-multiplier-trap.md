---
type: method
domain: tooling
topic: case-audit
aliases: [zone-load-multiplier, load-multiplier-trap, area-load-multiplier, served-load-check]
tags: [esapp, powerworld, load, device-creation, synthetic-grid]
---

# Adding load under a zone or area load multiplier

## Abstract

A case can scale every load in a zone or area by a stored multiplier, so the MW a new load
draws is `LoadSMW` times that multiplier rather than `LoadSMW`, and PowerWorld gives no
warning. The fix is to divide the intended MW by the multiplier before writing, then read
the solved MW back and assert it matches. A second, related trap: load on an islanded
(Disconnected) bus drops out of system totals silently, so a totals check cannot catch a
load that is not connected. Read this before writing `LoadSMW` into any case you did not
build yourself.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [adding-devices-esapp](adding-devices-esapp.md) (the `LoadSMW` write this page
  corrects; `LoadSMW` is the scheduled input, `LoadMW` the served value) ·
  [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md) (scaling load to a
  scenario level hits the same multiplier) · [case-data-lint](case-data-lint.md) ·
  [reviewing-a-design](reviewing-a-design.md) (the islanded-load check, applied to a
  submitted design)
- **Deeper:** [esapp-schema-reference](../references/esapp-schema-reference.md) for the `Load`
  keys (`BusNum`, `LoadID`)

## Content

### What happens

Measured 2026-10-19 on Synth2k, in one of its published scenarios. One zone carries a load
multiplier of **×1.305**. A new load created there with `LoadSMW = 600` drew **783 MW** in
the solved case (600 × 1.305). There was no warning, the write read back as 600, and nothing
in the solve reported a difference. Every downstream number then carries a load 183 MW
larger than intended: the flows, the N-1 violations, and the generation balance.

The multiplier sits outside the load record, so reading `LoadSMW` back proves nothing. It
returns exactly what you wrote.

### The fields

From the Simulator 25 field export, via the schema lookup on 2026-10-19:

| field | concise name | what the export says | writable |
|---|---|---|---|
| `Load.LoadMultiplier:2` | `MultiplierMWZone` | Scaling value applied to all the real power load values in the zone | read-only |
| `Load.LoadMultiplier:3` | `MultiplierMvarZone` | the Mvar twin of the above | read-only |
| `Load.LoadMultiplier` | `MultiplierMWArea` | Scaling value applied to all the real power load values in the area | read-only |
| `Load.LoadMultiplier:1` | `MultiplierMvarArea` | the Mvar twin | read-only |

These are per-load *views* of the multiplier, so they are the ones to read. **Where the
multiplier is set is not confirmed.** The only writable candidate on `Zone` / `Area` in the
export is `SchedValue` (concise `LoadMWScale`, "Load Scale MW Value"), and the export does
not say whether it holds a multiplier or a target MW. Do not write it on the strength of
this page. The read-side fields come from the export, and they were not read back on the
measured case. **Whether the area and zone multipliers compound** when both differ from 1 is
also untested. The read-back below catches either case.

### The fix

1. Create the load as usual ([adding-devices-esapp](adding-devices-esapp.md)), keeping
   `BusNum` + `LoadID`.
2. Read its multipliers and write `LoadSMW = intent / multiplier`. Scale `LoadSMVR` by the
   Mvar multiplier the same way.
3. Solve, read `LoadMW` (the served value), and assert it matches the intent.

```python
from esapp.components import Load

key = (bus, "1")                      # BusNum, LoadID of the new load
intent_mw = 600.0

m = pw[Load, ["LoadSMW", "LoadMultiplier", "LoadMultiplier:2", "LoadStatus"]]
row = m[(m.BusNum == key[0]) & (m.LoadID.astype(str).str.strip() == key[1])]
mult = float(row["LoadMultiplier:2"].iloc[0])        # zone MW multiplier
# simple: assumes the area multiplier is 1; assert it rather than compound blindly
assert abs(float(row["LoadMultiplier"].iloc[0]) - 1.0) < 1e-6, "area multiplier too: check compounding"

fix = row[["BusNum", "LoadID"]].assign(LoadSMW=intent_mw / mult)
pw[Load] = fix                                       # keyed write, subset is fine
pw.pflow()

served = pw[Load, ["LoadMW"]]
got = float(served[(served.BusNum == key[0]) & (served.LoadID.astype(str).str.strip() == key[1])]["LoadMW"].iloc[0])
assert abs(got - intent_mw) < 0.5, f"served {got:.1f} MW, intended {intent_mw} MW"
```

Assert on `LoadMW` after a solve, never on `LoadSMW`. The read-back is the real check,
because it holds whichever multiplier is in force, including one this page has not
identified.

### Islanded load leaves the totals silently

PowerWorld counts load on a **Disconnected** bus out of the zone, area and system totals,
and it says nothing. A check that compares total load before and after an edit therefore
passes for a new load that landed on an islanded bus: the totals do not move, and the load
serves nothing. Check connectivity per device instead:

- `Bus.BusStatus` reads `Connected` or `Disconnected`, read-only, from the solve.
- `Load.BusObjectOnline` is the load's own online flag.

Assert that the new load's bus reads `Connected` after the solve, alongside the `LoadMW`
check above. `LoadMW` is the connected value, so a new load that reads 0 MW is consistent
with an islanded bus. That inference was not tested separately; the bus status is the check.
