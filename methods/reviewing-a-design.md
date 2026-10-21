---
type: method
domain: cross-cutting
topic: design
aliases: [reviewing-a-design, design-review, review-a-submitted-design, tep-design-checklist,
  transmission-design-review]
tags: [transmission-planning, review, case-diff, n-1, topology, impedance, powerworld, esapp]
---

# Method: Reviewing a submitted transmission design

## Abstract

A reviewer's checklist for a transmission design handed in as a modified case beside the
base case it was built from, by a student or a team. Diff the two cases to recover what the
design added, then check six things a design can get wrong while still solving cleanly: a
load that loses service when one new device trips, a single transformer behind redundant
lines (a defect only under some criteria), four or more circuits on one right-of-way, a branch typed as a line across two
voltage levels, a per-mile reactance entered as the line total, and a line with X far below
R. **Report only. Never edit or save the submitted case.** Each finding names the device by
its key fields and gives the number behind it; every fix and trade-off stays with the
designer.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [comparing-planning-cases](../demos/comparing-planning-cases.md) (the guarded diff
  that recovers the added devices) · [new-device-contingency-aux](new-device-contingency-aux.md)
  (a contingency set for only the new devices)
- **Across:** [zone-load-multiplier-trap](zone-load-multiplier-trap.md) (load that islands
  leaves the totals silently) ·
  [converting-lines-to-transformers](converting-lines-to-transformers.md) (`BranchDeviceType`
  is derived from `LineXFMR`) ·
  [case-impedance-completeness](../concepts/case-impedance-completeness.md) (X/R as a data
  check) · [case-data-lint](case-data-lint.md) (whole-case data defects) ·
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  (where a second tie should land)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md) ·
  [handling-errors](handling-errors.md)

## Content

### Ground rules

- **Read, never write back.** Open both cases, never save either. Outage tests run in memory
  inside `pw.snapshot()`, which restores the case on exit.
- **Check the base case first.** Solve it in every scenario the design must meet. A violation
  already in the base case is not the design's fault, and the report must say which is which.
- **Diff, do not trust a device list.** Recover the added and changed devices with the guarded
  diff in [comparing-planning-cases](../demos/comparing-planning-cases.md): normalise from/to
  order, pair buses by name and kV, and compare ratings and impedance on common keys to find
  upgrades. A naive diff reports construction that never happened.
- **Diff the generators too.** Compare status, AVR (`GenAVRAble`) and AGC (`GenAGCAble`) per
  generator on `BusNum` + `GenID`, and in-service MW and capacity by area, zone and fuel type
  (code in [comparing-planning-cases](../demos/comparing-planning-cases.md), Step 2). A design can switch off a unit's voltage control or move where
  power comes from without adding a single device.
- **If the design ships as several scenario cases, diff them against each other too.** The same
  modification must appear in every scenario file. A design that differs between files is a
  bookkeeping error, and an easy one to make when several files are edited by hand.
- **Grade each finding by kind.** A *rule* breach (a written requirement, checkable with no
  solve), a *physical* failure (a live solve shows it), or a *practice* judgement (a planner
  would question it, but the threshold is opinion). Say which.

### Check 1 — every load still served with any one new device out

Outage each new line and transformer one at a time, solve, and check **served MW and bus
connectivity** at every load the design must deliver. Do not stop at thermal violations.

An islanded load is the trap. The load keeps a closed `LoadStatus`, its bus goes
`Disconnected`, and the solver converges on what is left. A status check reports success, a
thermal check finds nothing over rating, and the load is not served. PowerWorld also drops a
Disconnected bus's load out of the system totals without a word, so a before/after totals
check passes as well (both seen 2026-10-20 on a 2,000-bus synthetic case) ([zone-load-multiplier-trap](zone-load-multiplier-trap.md)).

```python
import pandas as pd
from esapp import PowerWorldError
from esapp.components import Branch, Bus, Load

intent_mw = {(9101, "1"): 600.0, (9102, "1"): 600.0}   # BusNum, LoadID -> MW to deliver
targets   = set(intent_mw)
new_br    = added_branches                           # (from, to, ckt) from the guarded diff

def served(pw):
    ld = pw[Load, ["LoadMW"]]
    bs = pw[Bus, ["BusStatus"]].set_index("BusNum")["BusStatus"]
    out = {}
    for _, r in ld.iterrows():
        k = (int(r["BusNum"]), str(r["LoadID"]).strip())
        if k in targets:
            out[k] = (float(r["LoadMW"]), bs[int(r["BusNum"])])
    return out

findings = []
for f, t, c in new_br:
    with pw.snapshot():                              # restored on exit, never saved
        pw[Branch] = pd.DataFrame({"BusNum": [f], "BusNum:1": [t], "LineCircuit": [c],
                                   "LineStatus": ["Open"]})   # keyed write
        br = pw[Branch, ["LineStatus"]]
        hit = br[(br.BusNum == f) & (br["BusNum:1"] == t) & (br.LineCircuit.astype(str).str.strip() == str(c))]
        assert (hit.LineStatus == "Open").all() and len(hit) == 1, f"outage of {f}-{t} {c} did not take"
        try:
            pw.pflow()                               # solve the way the study does
        except PowerWorldError:                      # a collapsing outage is the worst finding, keep it
            findings.append((f, t, c, None, None, "did not converge"))
            continue
        for k, (mw, st) in served(pw).items():
            if st != "Connected" or mw < 0.999 * intent_mw[k]:
                findings.append((f, t, c, k, mw, st))
```

The `LineStatus` read-back is there because a write that silently missed its branch produces
a pass for an outage that never happened. A non-converging outage is recorded, not skipped:
it is usually the worst finding of the review.

### Check 2 — a single transformer behind redundant lines (criterion-dependent)

A common shape behind a dropped load: two or more new lines into a new substation,
then **one** transformer down to the load. The lines look redundant, and that transformer's
outage islands the load.

Whether that is a defect depends on the criterion the design is judged against:

- **A brief that requires full delivery with any one new device out** (Check 1's test): it
  fails.
- **NERC TPL-001's single-element (P1) event:** consequential load loss (load directly served
  by the element removed) is permitted, and non-consequential load loss is not. A load served
  radially through one transformer is consequential load loss, which the NERC baseline allows.
  This is per NERC's TPL-001 definitions; check the current TPL-001-5.1 Table 1 and any
  regional criteria, which can be stricter.
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  already treats such a load as consequential load loss by convention.

Its outage can show **no thermal violation at all**, because the island carries no flow. So
this is found by Check 1's connectivity and served-MW test, never by an overload screen. In
the report, name the transformer, the load behind it, and the criterion you judged against.
Under a full-delivery brief, say that duplicating the lines did not duplicate the path; under
TPL-001 P1 alone, report it as consequential load loss, not a violation.

### Check 3 — four or more circuits on one right-of-way (practice judgement)

Group every in-service circuit, existing and new, by the unordered pair of substations it
joins. Flag any corridor carrying **four or more** circuits.

DC power flow and single-device N-1 both accept a stacked corridor: four circuits are four
separate devices, each survivable alone. A cost objective may even reward it, since several
lower-voltage circuits can match one higher-voltage circuit with no transformer or substation
cost. A utility would question it, because one structure failure, wildfire, ice storm or
excavation can take the whole corridor at once, and only a common-mode or tower contingency
would show that. Report it as a **judgement**, not a violation: the threshold of four is
opinion, and the design brief may not define a common-corridor contingency.

### Check 4 — a branch typed as a Line across two voltage levels

Read `BranchDeviceType` with the nominal kV of both end buses. A branch whose ends sit at
different `BusNomVolt` and whose `BranchDeviceType` reads `Line` should have been a
transformer.

```python
br = pw[Branch, ["BranchDeviceType"]]
kv = pw[Bus, ["BusNomVolt"]].set_index("BusNum")["BusNomVolt"]
br["kv_from"] = br["BusNum"].map(kv)
br["kv_to"]   = br["BusNum:1"].map(kv)
bad = br[(br.BranchDeviceType == "Line") & ((br.kv_from - br.kv_to).abs() > 0.5)]
```

**Trust the device-type field, never the rule "the ends differ in kV, so it is a
transformer".** That inference relabels the defect away. A DC solve ignores voltage
magnitude, so this case solves and its cost looks plausible. How the type is set is on
[converting-lines-to-transformers](converting-lines-to-transformers.md). Run the check on
the base case too: if the base already has such branches, report only the new ones.

### Check 5 — per-mile reactance entered as the line total

A design brief usually gives reactance per mile. The common error is entering that per-mile
value as the whole line's `LineX`. On a 100 MVA base, an `X` of about **2e-4 pu on a 500 kV
line** or **1.2e-3 pu on a 230 kV line** is per-mile scale. A line tens of miles long
should carry tens of times that.

Divide each new line's `LineX` by its length and compare with the brief's per-mile value.
Length comes from `LineLength` where the designer entered it, otherwise from the distance
between the end buses (`pw.buscoords()`). A ratio near `1/length` is this error. A line
entered too strong electrically draws flow toward itself, so a DC OPF routes through it
preferentially, and the flows and cost the design reports are wrong.

Two cautions. The brief may define route length as a multiple of straight-line distance
without saying which mile the per-mile X uses; a band of designs sitting at exactly that
multiple is an ambiguity in the brief, not an error. And quote the ratio in the report,
not just "wrong X", so the designer can see which reading they took.

### Check 6 — X much smaller than R on a transmission line

A transmission line's X is several times its R. A new line at 115 kV or above with
`LineX` well below `LineR` almost always has the two swapped, or one entered in the wrong
unit. DC power flow reads only X, so a swap there changes the flows without any error
([case-impedance-completeness](../concepts/case-impedance-completeness.md) covers the
whole-case version of this check). Flag it with both values.

### What the report looks like

Open with the criterion the review judged against (the brief's delivery rule, TPL-001 P1, a
regional criterion), since Check 2 and some Check 1 findings pass under one and fail under
another. Then one line per finding, worst first: the check, the kind (rule, physical,
judgement), the device by its key fields, and the number. For example:

> **Physical** — Check 1/2, against a full-delivery brief: with transformer 9201→9101 ckt 1 out, bus 9101 goes Disconnected
> and its 600 MW load is not served. Both new 500 kV lines into 9201 survive their own
> outages; the single transformer below them does not.

Then say what was checked and passed, which base-case problems were excluded, and that
nothing was edited or saved. Leave every fix to the designer. A review that rewrites the
design has stopped being a review.
