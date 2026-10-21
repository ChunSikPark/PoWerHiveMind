---
type: method
domain: synthetic-grid
topic: design
aliases: [base-case-remediation, n-0-remediation, voltage-remediation-actions, remediation-action-space,
  action-ladder, remediation-action-catalog, what-can-i-do-about-a-violation, fix-intact-case-violations]
tags: [synthetic-grid, voltage, thermal, remediation, powerworld, reactive-power, n-0, ladder]
---

# Method: Remediating base-case (N-0) violations

## Abstract

The action ladder for fixing **intact-case** voltage and thermal violations, cheapest first, with
the measured evidence for each rung and the traps that inflate the answer. Actions are **priced in
devices added, not money**: free levers (generator setpoints, transformer taps, rating bumps,
bumping a device already present) are exhausted before anything is bought, and removing an unneeded
device is the one action with **negative** cost. The headline rule: **fix the VIOLATIONS, not every
bus, and change the controls before you buy equipment.** Measured 2026-09-02 on a ~9k-bus synthetic
planning model across five dispatches: a dozen emergency overvoltages went to **zero** with one free
setpoint change and one reactor, after a first estimate that was too large by a factor of ~50; and
some forty overloads went to one with rating increases and a handful of parallel circuits.

## Connections

- **Up:** [Home](../index.md) · [violation-remediation](../demos/violation-remediation.md) (the
  diagnose-then-test loop on a small case)
- **Across:** [remediating-n1-contingency-violations](remediating-n1-contingency-violations.md)
  (the N-1 loop this feeds, where three of these rungs turn out to be unavailable and the free-bump
  cap does not transfer) · [ltc-regulation-checks](ltc-regulation-checks.md) (the tap rung) ·
  [one-device-per-voltage-pocket](../concepts/one-device-per-voltage-pocket.md) (where a new device
  goes) · [ranking-new-devices-by-severity](ranking-new-devices-by-severity.md) (which violation to
  spend an action on) · [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md)
  (an overvoltage a tie fixes better than a reactor)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md) (`CreateData` silent
  no-op, two-character IDs) · [save-powerworld-case](save-powerworld-case.md) ·
  [sizing-a-device-whose-impedance-determines-its-own-flow](../concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md)

## Content

### The pricing rule

An action costs the number of **devices it adds**, gross, never netted against removals. A
settings change costs 0 no matter how many units it touches. A rating change costs 0 because no
equipment is bought. This is why the ladder order below is not a preference: it is the objective.

| cost | meaning |
|---|---|
| **−1** | removes a device |
| **0** | free: a settings change, or a rating or cooling-stage change on equipment already installed |
| **1** | one new device |
| **n** | n parallel circuits or units is n interventions, never one record |

### Rung 0: settle which band you are judging against, first

The contingency band and the normal band are different criteria. Re-scoping the same case from a
`[0.90, 1.10]` band to a `[0.94, 1.04]` normal band took the base-case count from about a dozen
violations to about a thousand buses, two orders of magnitude. On one dispatch alone, the buses over
1.06 pu outnumbered those over 1.10 by ~15×, and those over 1.04 outnumbered those over 1.06 by ~6×.
**Settle the criterion before sizing anything, and record it as a decision.** An unrecorded band is
how a study silently changes scope.

### The voltage ladder

Undervoltage and overvoltage need separate ladders because the corrective sign is opposite.

| tier | action | cost | bound |
|---|---|---|---|
| **V0** | transformer tap: re-point an LTC's regulated bus, or correct a fixed ratio | 0 | `XFTapMin` / `XFTapMax` |
| **V1** | raise `GenVoltSet` | 0 | walk in **≤0.0025 pu steps** |
| **V2** | bump an existing capacitor bigger | 0 | the device's own `SSMaxMVR` |
| **V3** | new capacitor | 1 | walk up in **50 MVAr steps** |
| **V1′** | lower `GenVoltSet` | 0 | same 0.0025 pu walk |
| **V2′** | bump an existing reactor bigger | 0 | the device's own `SSMinMVR` |
| **V2″** | **remove an unneeded capacitor** | **−1** | |
| **V3′** | new reactor | 1 | walk up in 50 MVAr steps |
| | **remove an unneeded reactor** (for undervoltage) | **−1** | |

**V0 goes first, ahead of the setpoints.** A tap is a ratio, not a source, so it only works where
the *other* side has headroom, but where it does it costs zero and is almost perfectly local
(measured max |dV| of 1e-5 on every untouched bus). It must precede V1 because on a case with
generator step-ups modelled, the generator terminals are real buses, so raising every setpoint
raises all of them and blocks V1 outright; fixing the taps first is what makes V1 available at all.
Measured: it cleared over a dozen GSU terminals of 5–12% overvoltage for zero devices. On a fleet
whose LTCs are already live, re-pointing the regulated bus beats writing a fixed tap, and **a
mis-pointed LTC can cause the violation next to it**: one ran its tap to the limit holding a healthy
bus and drove the other side to 1.126 pu. See [ltc-regulation-checks](ltc-regulation-checks.md).

**Removal is ordered ahead of adding the opposite sign, and the reason generalises**: *adding a
reactor to cancel an unneeded capacitor is two devices doing the work of zero.* Any ladder that can
both add and remove must try removal before it adds the opposite sign. Undervoltage is usually the
common direction after contingencies (measured 2026-09-02 on one N-1 sweep of a ~9k-bus synthetic planning model: about eight
undervoltage rows for
every overvoltage row), so do not build the removal rung for capacitors only.

Two eligibility rules that look alike and are opposite:

- **Bumping ignores which contingency placed the device.** One bus violating under four drivers is
  one bus, not four targets; treat it as four and four devices land beside it.
- **Removal excludes devices this run placed for another target.** That device is load-bearing for
  a target already worked, and removing it re-breaks that one silently. The two then oscillate.

### Rung 1: generator voltage setpoints. Free, and usually the dominant lever

Check `GenVoltSet` before anything else. On the measured case **every closed unit sat at exactly
1.0400**, identical to the normal high limit, so every bus picking up line charging floated
*above* it. The system was not randomly high; **it was scheduled high.** Walking 1.04 → 1.02
across all five dispatches took the emergency overvoltages from twelve to two, at zero cost.

**Walk it, do not jump it.** One dispatch *failed to converge* at 1.03 and 1.02 as a single write,
while converging at both 1.04 and 1.01 either side: non-monotonic, so the step was the problem, not
the setpoint. Re-walked in **0.0025 pu steps carrying each solution forward**, every setpoint
converged. The same rule applies to walking a shunt up.

**There is a floor.** Pushing further converts overvoltage into undervoltage: at 1.00, dozens of
buses fell under 0.94 pu and two under 0.90. The usable window on that case was ~1.0125–1.0225.

**It runs in both directions.** A case **already** walked down with **zero overvoltages** has
headroom to walk back **up**, and that is again the free lever. Measured 2026-09-04: the entire N-0
problem was one undervoltage at 0.8986 pu, and one 0.0025 step up cleared it for zero devices. **It
was still declined, for two measured reasons**, which is the more useful half of the lesson, because
"free" is not the same as "best":

1. **The margin was a rounding.** 0.9006 against a 0.90 limit is +0.0006 pu. One 25 MVAr capacitor
   at the violating bus gave **+0.0188, thirty times more**, for one device.
2. **The free lever is not free once the GSU low side is a real bus.** Raising every setpoint raises
   every generator terminal: the worst went 1.143 → 1.159 pu, on a machine already 14% above
   nameplate. The capacitor *lowered* it.

So the price of a system-wide setpoint move is paid at the generator terminals. Screen GSU terminal
voltage alongside the transmission counts whenever you walk a setpoint on a case with step-ups.

### Rung 2: one reactor (or capacitor) at the worst remaining bus. Size by walk-up

After rung 1 the entire remaining emergency problem was **one bus in two dispatches**. A reactor
walked up in 50 MVAr steps until the bus cleared:

| target | MVAr |
|---|---|
| clear 1.10 (emergency) | **−200** |
| clear 1.06 | −800 |
| clear 1.04 | −1,420 |

Verified across all five dispatches: zero emergency violations anywhere, no new undervoltage in any
dispatch, the minimum voltage moved by at most 0.0001 pu, and it *improved* the three dispatches
that did not need it. **Verify across every dispatch, checking the undervoltage end**: a reactor
absorbs at peak too.

Seed a new shunt to its expected dispatch, never to `SSNMVR = 0`: a cold-started shunt can diverge a
stressed case by yanking reactive sources to zero as the solver's initial guess. `SSVLow < SSVHigh`
is mandatory; a zero-width band cannot regulate.

### Rung 3: capacitor removal. Sound idea; usually no target

Removing a capacitor at a bus that is overvoltage in several dispatches has **negative device
count**, the only such lever. Screened it and found **zero candidates**, for an instructive reason:
in the overvoltage dispatch the controller had already backed them off (at peak almost every
capacitor was dispatched; at minimum load almost every one sat at zero). Screen it anyway, because it
is cheap, but expect nothing where the fleet regulates.

### The thermal ladder: rating or conductor first, parallel only where it cannot reach

| rung | action | cost | cap |
|---|---|---|---|
| **BUMP** | line rating increase | 0 | **1.5×** |
| **COOLING** | transformer cooling stage (fans) | 0 | **1.33×** |
| **CONDUCTOR** | reconductor: new rating **and** new R/X/C | 1 | catalogue-bounded |
| **PARALLEL** | parallel circuit | n | `n = ceil(m) − 1` alone; across a corridor see [remediating-n1-contingency-violations](remediating-n1-contingency-violations.md) |
| **PARALLEL_UNIT** | parallel transformer unit | n | as above |

**The ordering rule is worth most of the circuits.** A parallel-first pass on the same few dozen
overloaded branches wanted **32 parallel circuits**; rating-first needed **8**.

**The caps are validity boundaries, not conservatism knobs.** A rating increase is honest only up
to the point its "impedance unchanged" claim holds: lines ×1.5 is where HTLS reconductoring stops
giving ampacity at unchanged geometry; transformers ×1.33 is a cooling stage (rating up, impedance
untouched). Because a rating bump is priced at zero, the cap is also the only bound on an otherwise
unbounded free action. Raising it to make a number look better is the wrong move.

**Evaluate every cap cumulatively, against a write-once baseline the case carries.** If the
denominator is the rating the *previous* bump wrote, the cap measures its own output: ×1.33 applied
three times is ×2.36 with every pass reporting compliance. Store the original rating once and judge
against it. This is not hypothetical: two passes on one case lineage (2026-09-03 and 2026-09-14)
both measured against the current rating, and tracing the lineage showed they had touched disjoint
branch sets, so nothing compounded. That was luck, not a check.

**Expect the middle of the thermal ladder to be missing on a synthetic case.** A reconductor needs
the line's present conductor, and on the measured case only about 6% of branches recovered one
exactly (measured 2026-09-03), because the rest were rated by a derate or headroom script rather
than by a conductor choice. The ladder then escalates from a free bump straight to a parallel
circuit ([remediating-n1-contingency-violations](remediating-n1-contingency-violations.md) has what
can still be recovered).

On the measured case the bumps were small (median ×1.08, max ×1.35); only three branches, all
generator step-ups, exceeded a cap and had to go parallel. One policy that worked: prefer rating or
conductor at 69/138 kV, and accept a parallel circuit at 345 kV, where a re-rate is a major
reconductor anyway and a parallel EHV circuit is the asset the network wants.

**Preserve the rating ratio.** Copy the rating *set*, do not invent it. On most branches of a
synthetic case `LineAMVA:1` and `LineAMVA:2` (rates B and C) are 0.0 and must stay 0.0; scaling only
`LineAMVA` and leaving a fabricated B/A ratio behind silently creates emergency headroom. But some
branches carry `B = C = A`, and forcing those to 0.0 strips ratings that exist. Scale B and C with A
where they are non-zero; leave them at 0.0 where they are 0.0.

**A parallel circuit is a SEPARATE ROW with the SAME impedance.** Never "halve X on the existing
row": an N-1 outage of the merged row then removes both circuits at once, and it scored one action
at +9,171 violations against a measured +2.

**Sizing conventions that are load-bearing:**

- The multiplier is measured against the **original nameplate**, always, and the request is
  `standing × m`. Sizing against the current rating once wrongly refused almost every corridor.
- Carry **~2% headroom** (× 1.02). Sized to exactly the measured flow, the branch lands at
  precisely 100% and any redistribution puts it back over, so the ladder revisits what it paid for.
- A reconductor **derives** R/X/C by ratio and never recomputes them absolutely, and `Xa` is
  **not monotone in MVA**: an upgrade can raise X.

**A rating increase asserts the branch was under-rated.** That is defensible on a synthetic case
whose ratings were assigned rather than surveyed, but state the assumption rather than letting a
number quietly disappear, and see *Do not bump a rating without provenance* below.

### Cheap actions usually left off the menu

| action | cost | why it is worth naming |
|---|---|---|
| **enable inverter-based reactive capability** | 0 | synthetic cases often model solar and storage at **zero MVAr**. A modelling decision, not equipment, and possibly the largest voltage lever on the case |
| **switching / topology reconfiguration** | 0 | opening a line to redirect flow. No hardware, but it interacts with the contingency set |
| **series compensation** | 1 | rarely considered |
| **SVC / synchronous condenser** | 1 | usually owned by a separate reactive planning study |
| **generation redispatch / load shedding** | — | an operating answer, not a build; out of scope for a planning study |

### The traps, all paid for

**Solve the violations, not the distribution.** Targeting "every bus inside the normal band"
produced an estimate of ~9–10 GVAr and around twenty new EHV banks. Targeting the actual violations
produced **200 MVAr**. The inflated figure came from a linear extrapolation of single-device tests
stretched ~7× beyond anything measured, ignoring that the candidates all relieved substantially the
same buses. **Not every bus has to be in range.**

**Site by reach, never by dV/dQ.** The most locally sensitive bus is the worst place to put a
device. One candidate moved 0.29 pu for 300 MVAr, 8–30× more sensitive than any other, and it
**fixed the fewest buses and created three new undervoltages**. High dV/dQ means a *weak* bus.

**"Fix the worst first" does not predict reach; volume does.** Sizing each candidate to genuinely
clear its own bus, then counting what else fell:

```
corr(worst voltage, buses fixed)  =  0.042      <- essentially zero
corr(MVAr installed, buses fixed) =  0.971      <- almost perfect
```

Efficiency was near-uniform at ~100–130 buses per 1,000 MVAr regardless of which bus. Worst-first
still wins as a tie-breaker, because a worse bus needs more MVAr to clear, but the volume is doing
the work.

**Do not bump a rating without provenance.** On the measured case nine of ten overloaded corridors
had **zero rating drift**: the sizing was correct for the network it was done on. The AC/DC gap
(1.7–5.6× in real power) came from the network having churned by about 30% since, under a
**lossless DC** sizing solve that never saw the case's AC losses. A bump there asserts an
under-rating nobody measured.

**Re-measure thermal after a voltage action, and do not guess the sign.** The intuition is that
lower voltage means higher current for the same power, so the voltage fix should worsen thermal.
**Measured, it mostly did the opposite**: the reactor removes reactive flow, and that cuts MVA by
more than the voltage drop raises current. Four of five dispatches improved and one overload
disappeared; one dispatch's worst branch degraded by 2.9 points. The sign is case-dependent and
cheap to measure, so measure it.

**Diagnose a shunt fleet by measurement, not by its settings.** Two wrong diagnoses came before the
right one: "the reactors are exhausted" (they read 100% dispatched at EHV, but that was a
consequence of the 1.04 setpoints, not a limit) and "the controller is disabled" (`SSAutoControl`
read `None`). **Both were wrong. The shunts did regulate**: the same fleet ran tens of GVAr
capacitive at summer peak (over twenty) and over ten GVAr inductive at minimum load, tracking load. Writes of
`SSAutoControl = YES` read back `None` over raw SimAuto (suspected, not confirmed). Judge the fleet by whether its
dispatch moves, not by a settings field.

**Read `SSMaxMVR` / `SSMinMVR` before planning a band change, not just `SSNMVR`.** A bank already
sitting at its own limit has no travel, so a band change on it is free and worth nothing. Measured
2026-09-14: every 765 kV reactor at a violated bus read `SSNMVR == SSMinMVR`, and a planned "tighten
the band to the criterion" rung had to be struck.

### Two screening traps on a case with three-winding transformers

- **Star and tertiary buses are not violations.** A three-winding conversion adds a fictitious
  star point (1.0 kV nominal) and often a dead tertiary per unit, and some read above 1.10 pu. The
  tertiary carries no current, so its pu voltage simply equals its star point's. Screen network buses
  only (69 kV and up, excluding step-up terminals, star and tertiary buses); on the measured case
  that left about four buses in five. A naive screen reports violations that do not exist.
- **IDs are two characters.** A new shunt with `ShuntID` `C10` silently becomes `C1`; the create
  reports success and the lookup that follows fails on a bank that is really there. See
  [adding-devices-esapp](adding-devices-esapp.md).

### Recipe

1. Fix the band. Record it.
2. Check the taps ([ltc-regulation-checks](ltc-regulation-checks.md)), then read `GenVoltSet`. If
   the setpoints equal the limit, that is the problem: walk them in ≤0.0025 pu steps, carrying each
   solution forward, and stop before undervoltage appears.
3. Re-measure. Whatever emergency violations remain are usually a handful of buses.
4. Walk a reactor or capacitor up at the worst survivor in small steps; stop at the first size that
   clears.
5. **Verify across every dispatch**, checking the opposite end too.
6. Re-measure **thermal**: the voltage action moves it, in a direction you cannot predict.
7. **Thermal: rating or conductor first, parallel only where a cap cannot reach.** Lines ×1.5,
   transformers ×1.33, cumulative from the original rating. Union the requirement across dispatches
   so all cases keep one topology.
8. Screen for removable capacitors (cheap; often empty).
9. Only then consider hardware beyond the above.

**Guards worth writing into any script that does this**, all of which fired or would have:
`CreateData` silently no-ops, so assert the branch or shunt count moved by exactly what you added;
write the full field row; read ratings back off the live case before saving; refuse to save any
case whose violation count got worse on the metric the action targeted; back up first; and save
with the script `SaveCase` plus a file-exists check ([save-powerworld-case](save-powerworld-case.md)).
