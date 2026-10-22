---
type: method
domain: synthetic-grid
topic: contingency
aliases: [n-1-remediation, contingency-remediation-loop, remediating-contingency-violations,
  contingency-remediation-playbook, fix-n-1-violations, make-the-case-n-1-clean]
tags: [synthetic-grid, contingency, n-1, thermal, voltage, remediation, powerworld, loop]
---

# Method: Remediating N-1 contingency violations

## Abstract

The loop that drives a solved case's **post-contingency** violations to zero or to an explained
residue: sweep, classify, rank **elements**, spend the cheapest action that works, re-measure,
and stop when everything left is either fixed or explained. The base-case ladder in
[remediating-base-case-violations](remediating-base-case-violations.md) does **not transfer
unchanged**: the N-1 regime is larger, three of its rungs turn out to be structurally unavailable
on a synthetic case, and a free-rating-bump cap that is comfortable on intact-case overloads sits
below the *median* of the contingency-induced ones. Measured 2026-09-13/14 on a ~9k-bus synthetic
planning model with about eleven thousand contingencies: a few dozen actions and five new devices
cut the violated elements by about a quarter in one pass.

The headline rule: **an element is the unit, a sweep is the round, and every number is measured
rather than asserted.** This toolchain fails by returning a confident, smaller answer, not an
error. **The playbook** section is the eight-step order of play that took the
last residue to a clean full N-1 (2026-09-24).

## Connections

- **Up:** [Home](../index.md) · [violation-remediation](../demos/violation-remediation.md) (the
  diagnose-propose-test-rank loop on a small case; this page is that loop at scale)
- **Across:** [remediating-base-case-violations](remediating-base-case-violations.md) (the N-0
  ladder and action menu this diverges from) ·
  [one-device-per-voltage-pocket](../concepts/one-device-per-voltage-pocket.md) (why the voltage
  half is cheap) · [reading-violationctg](reading-violationctg.md) (the row contract and its
  identity traps) · [reducing-a-contingency-set](reducing-a-contingency-set.md) (what scopes a
  parallel sweep) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (the
  sweep itself) ·
  [diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md) and
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md) (the
  non-converging residue, playbook step 7) · [ltc-regulation-checks](ltc-regulation-checks.md)
  (the free voltage levers the playbook tries first) ·
  [agc-participation-factors](../concepts/agc-participation-factors.md) (the swing taking all
  make-up power)
- **Traps it depends on:**
  [sizing-a-device-whose-impedance-determines-its-own-flow](../concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md) ·
  [aggregate-clauses-cannot-bound-one-row](../concepts/aggregate-clauses-cannot-bound-one-row.md) ·
  [adding-devices-esapp](adding-devices-esapp.md) · [save-powerworld-case](save-powerworld-case.md)

## Content

### The loop

1. **Sweep** the full contingency set once. This is the expensive step and the round is built
   around paying it once.
2. **Classify** every row, and **rank violated ELEMENTS**, not contingencies. An element that
   violates under forty-five different outages is one target, not forty-five. Ranking
   contingencies instead re-spends the ladder on the same asset.
3. **Act** on the worst element with the cheapest rung that reaches it.
4. **Propagate** the action wherever it applies, and **re-sweep** to measure what else it
   cleared, and what it broke.
5. **Reduce** the active set by everything that no longer violates, so later rounds are cheaper.
6. Stop when the set is empty, or when everything left is in a failure file **with a reason**.

"All violations solved" in practice means **all solved or all explained**. A residue with a
recorded reason is a deliverable: it is the design finding the study exists to surface. An
*unexplained* residue is the only real failure.

### Severity: one number, and two ways to get it wrong

Rank on one dimensionless quantity, "fraction beyond the limit", so a voltage and a thermal
violation can be ordered against each other at all
([ranking-new-devices-by-severity](ranking-new-devices-by-severity.md)).

- **Voltage ranks on signed deviation over its limit, never on the reported percentage.** That
  percentage's polarity is three-way (Trap 2 in [reading-violationctg](reading-violationctg.md)).
  The cost here: sorting on it selects a bus **0.0001 pu** below its limit as the worst
  undervoltage while the genuinely worst sits **0.11 pu** below, so the round spends its one
  action on nothing.
- **Thermal ranks on the ATTRIBUTED magnitude**, `min(exceedance, addition) / rating`, never raw
  exceedance. Subtracting the base decides *which* rows count, not *how big* they are.
- **An unsolved contingency emits no rows at all**, so it makes a sweep read *cleaner* than the
  truth. It carries no element and cannot be remediated. Route it to a diverged file and never
  let "no rows" sort as "nothing wrong".

### Three rungs of the N-0 ladder are structurally unavailable here

Catalogued, built, and unreachable, each for a different reason. All three were discovered by
trying:

| rung | why it is unavailable |
|---|---|
| transformer cooling stage | needs to know whether the stage is already spent; nothing in the case records it, and inferring it from rating arithmetic leaves most units unknown. An unknown stage is not an available one |
| bump an existing shunt | needs per-device headroom limits; on this case family those fields are **zero fleet-wide**, so there is no headroom to work within |
| reconductor by identity | the conductor is **not stored**: the conductor-type, bundle and length fields are populated on *no* branch. See below for what can be recovered instead |

**Expect the middle of a ladder to be missing on a synthetic case**, and expect to find out
only by attempting the rung. A rung that silently never fires reads exactly like a rung that
never helps.

### The free-bump cap does not transfer from N-0 to N-1

A free rating increase is honest only while it can be read as *"the rating was assigned
conservatively"*. Where that stops is a policy choice, and the policy that is comfortable
against intact-case overloads is the wrong one here.

Intact-case overloads on this case family cluster just above nameplate. **Contingency-induced
overloads do not**: measured across ~150 thermal elements, the median required multiplier sat
*above* the policy cap, so **more than half of all thermal violations were purchased hardware
by default**. Relaxing the cap by one notch cut the purchased circuit count by roughly **3×**,
and by three notches by roughly **10×**.

**The cap is the answer, not a tuning knob.** Set it against the regime you are in, record it
as a decision, and report the sensitivity rather than the single number, so the reader sees what
the choice costs.

### Fixing the highest voltage first does not relieve the rest

A natural strategy is to fix EHV thermal violations first and let the redistribution relieve the
sub-transmission ones. **Measured, on this case, it does not.** After clearing every violation at
345 kV and above, the median change across the ~100 remaining 69/138 kV elements was **−0.000
percentage points**, and the single best improvement anywhere was under one point, on a branch
still over its limit.

EHV fixes here were **electrically local**. The sub-transmission problem is its own problem. It
is cheap to assume the cascade exists and expensive to plan around it.

### A parallel circuit is counted across the corridor

Adding one circuit beside `n` existing ones splits the flow `n+1` ways, so the count that
matters is `ceil(m · n) − n`, not `ceil(m) − 1`. On a corridor whose circuits all violate
together, **one added circuit clears every circuit on it**, which is why a seven-element EHV
problem can be four devices.

Use `ceil`, never truncation: truncation gives one circuit fewer than needed, which is the
cheaper answer and therefore the direction that wrongly survives a review.

### What can be recovered when the conductor is not stored

Where a branch's conductor identity is absent, two handles remain, and **they disagree**:

- **the rating**, matched to a catalog entry. Weak, because assigned ratings need not
  correspond to any real conductor. Measured here: nearly a quarter of sub-transmission lines
  were rated at values sitting in a *gap* in the catalog, where no conductor exists.
- **the impedance ratio** `R/X`, matched to a catalog's per-mile `Ra/Xa`. **Length and base both
  cancel**, so this identifies a conductor without knowing the line's length. Measured: ~90% of
  sub-transmission lines matched a catalog conductor within 5% on this ratio, against a median
  error of ~2%.

**Open question, unresolved as of 2026-09-14.** The two handles imply *different* conductors, by
a median of ~37%, with the impedance consistently implying a **larger** conductor than the rating
does. Either the ratings are derate artifacts, in which case most sub-transmission thermal
violations are reporting artifacts rather than real overloads, or the ratings are correct
because the limiting element is terminal equipment rather than the conductor, which is ordinary
in a real utility model. **Do not assume either way.** The pattern also has a hard boundary: at EHV the impedances matched no catalog conductor at all, so
the ratio handle is sub-transmission-only.

A reconductor still **derives R/X/C by ratio** and never recomputes them absolutely, and a
reactance that *rises* with rating is normal (the catalog is not monotone), so report it rather
than assume it away.

### Guards this loop cannot run without

Every serious failure met building this announced itself as success. None raised an exception.

- **A partial sweep reads as a clean grid.** One contingency that crashes the solver takes its
  whole worker chunk with it, and a driver that counts a dead chunk as zero contribution quietly
  removes a quarter to a half of the case. Record per-round completeness as data, and make the
  next stage *refuse* a degraded round rather than trusting a reader to notice.
- **Not having measured coverage is not evidence of coverage.** A sweep that returned zero
  violation rows because every worker died is the most dangerous artifact this loop can produce:
  it is indistinguishable from success by inspection and arrives looking like a win.
- **A write that no-ops reads as "the fix did not help".** Read every change back and confirm it
  against what was requested, and confirm the *object* is the object you asked for, not merely
  that its numbers match.
- **A guard can be wrong in the safe direction and still cost you.** A read-back tolerance
  tighter than the solver's own storage precision rejects every successful write; the failure
  looks like diligence and trains the reader to loosen guards that work.
- **An acceptance test built from counts and maxima lets one element get much worse.** See
  [aggregate-clauses-cannot-bound-one-row](../concepts/aggregate-clauses-cannot-bound-one-row.md).

### Verify it worked

- Violated **elements** fell, and the set that cleared is the set that was acted on.
- **Nothing new appeared**, or, if it did, it is named and understood. A fix that trades one
  violation for another is not a fix.
- The round's sweep was **not degraded**, and the shortfall between dispatched and total is
  exactly the deliberately excluded labels, with no unexplained remainder.
- Actions are replay-sufficient: object type, key fields, field, value before, value after. The
  ledger is the only reconstruction path when cases are written once at the end.
- **A cleared element stays cleared.** One sized to its measured flow plus a thin margin can
  return once later fixes redistribute flow onto it. If that happens, the margin is too thin,
  and a fix that does not stay fixed is churn.
- **A re-rating can pass a "no worse than base" score without fixing anything.** Raising a
  branch's rating lowers its loading percentage while the flow stays exactly the same. So a
  score that counts an element only when it is more than *k* points worse than base will
  clear an overload by relabelling it. The branch can still sit well above 100% after the
  contingency. Measured 2026-10-06 on Synth2k with two large added loads: a package of 10%
  rating bumps alone passed that score. Nine of its bumped branches stayed at 102–133% after the
  contingency. With the bumps undone, the result matched the unremediated case row for row. A
  competing package of parallel circuits also passed, and kept most of its relief with its bumps
  undone. Two guards close this:
  - require every element an action touched to end **below 100%**, not merely "no worse
    than base";
  - re-score the final case on **base ratings**. Whatever comes back is what the bumps were
    hiding.

### The playbook: from a residue to a clean full N-1

The loop above takes a case most of the way. This is the order of play that took the last
residue (a few dozen (dispatch, element) pairs across thermal, GSU, voltage and non-converging
outages) to **zero on a full N-1 in every dispatch**. Measured 2026-09-22 to 2026-09-24 on a
~9k-bus synthetic planning model, five dispatches, one grid sized to the worst-case envelope.
It cost roughly a dozen reconductors, six new lines, one reactor and two LTC setting changes.

1. **Collect from a full sweep, and count elements, not pairs.** Twenty unsolved pairs were
   seven outages; seventeen GSU pairs were eight transformers. Tabulate per element: class,
   dispatches, worst value, and every driving outage. Screen three-winding star and dead
   tertiary buses out first: they are not network buses, and one high star bus can appear
   under almost every outage
   ([reducing-a-contingency-set](reducing-a-contingency-set.md#a-re-check-set-that-deletes-nothing)).
2. **Re-seed the sweep scope from that full sweep.** A reduced scope that shrank over many rounds
   had set aside **every** outage still driving a violation, and several had never been in scope
   at all. Put each violating and unsolved outage back to active before the next round.
3. **Judge each round against the last FULL sweep whenever the scope changed.** A round is scored
   only on outages both sweeps dispatched, so an outage newly in scope has no "before" and its fix
   is invisible: the score reads 0 → 0 while the target cleared.
4. **Diagnose GSU overloads before buying anything.** Three distinct causes, told apart by
   comparing the machine's MVA capability with the step-up's own rating:
   - **the swing takes all contingency make-up power** (participation factors all zero, see
     [agc-participation-factors](../concepts/agc-participation-factors.md)): the swing unit's
     step-up overloads on every *other* unit's trip, and a neighbour becomes the island swing
     when the swing's own step-up trips. A modelling choice, not a network problem.
   - **a parallel step-up unit trips and the machine stays on**: the survivor carries the whole
     machine. A contingency-definition question.
   - **the step-up is rated below its own machine**: a real sizing defect.
   Whether to fix the model or raise ratings is the study owner's call. If step-ups can be
   custom-built, raise **every unit** of a multi-unit step-up to the worst post-outage flow ×
   1.02; the rating moves no flow, so it cannot create a violation elsewhere.
5. **Thermal on lines: the free bump, then metal.** The bump cap is **cumulative from the base
   rating**, not per bump: a line already bumped once may have almost nothing left. Above the cap,
   reconductor, identifying the present conductor from the **base** rating within 5% of a catalog
   entry and choosing a conductor ≥ 1.2× the rating, which lands ~20% post-outage headroom rather
   than the 2–6% a minimum step leaves. Where the conductor cannot be identified, clone a parallel
   circuit with its own contingency record. Converting earlier bumps to reconductors one line per
   round costs little and buys real margin.
6. **Voltage: read the neighbourhood, then try free levers before any device.** For each bus, sum
   the MVAr its own substation makes and the headroom (up for undervoltage, down for overvoltage)
   in every substation within three hops. Then probe each free lever **alone, from a fresh open**
   (generator setpoint, LTC regulation band, LTC tap limit, switched-shunt band) under the
   driving outage, checking N-0 stays in band. Only then walk a capacitor or reactor in 25 MVAr
   steps. A device walked to "just clears" can miss by ~1e-4 pu under the full contingency solve;
   one more step closes it.
7. **Non-converging outages are collapses of radial-by-N-1 pockets.** Diagnose with
   [diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md), fix with
   a new tie per [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md).
   Then **run a full sweep before believing it**: the reduced sweep called the new ties clean, and
   the full sweep found them overloading the feeders of a **two-tie landing substation** when
   either upstream source tripped, up to ~140% on an 8-mile feeder. Land a tie on a substation
   with three or more ties, or reinforce the landing's feeders as part of the same package. On
   Synth40 (2026-09-24), a full plan of two second ties to large new loads, two radial-closing
   circuits and six re-rated branches left 0 violation rows and 0 islanding outages.
8. **Finish with a full N-1 of the final network, then write the cases.** Save in a format your
   Simulator build writes correctly ([save-powerworld-case](save-powerworld-case.md)). To ship
   post-contingency results, run Solve All in-process with any solver-crashing label skipped for
   the solve and un-skipped after, then cold-open each file and check branch, shunt and
   contingency counts and the solved count. PowerWorld's own per-contingency violation counts in
   those files still include the star and tertiary artefacts.

#### Three findings from the voltage work

- **An LTC can lose its regulated bus after an outage and park its tap.** When the outage leaves the
  LTC's far side as a dead end with no load, moving the tap can no longer change the regulated bus,
  so the tap stays where N-0 put it and the dead-end bus floats at V(regulated side) × tap: ~1.125 pu
  from a 1.075 tap. **Capping `XFTapMax`** so V × tap stays under the limit fixes it for zero devices
  and binds only in the dispatch that parked the tap high. A reactor also works, but spends a device
  holding an unloaded bus down.
- **Lowering an LTC's regulation band can lift the bus on its HIGH side.** The low side then draws
  less reactive power off the system above it. Measured: a 0.02 pu lower band on one nearby LTC
  lifted a sagging 345 kV load tap by ~0.01 pu under its outage, where generator setpoints and shunt
  bands gave under 0.002. Raising the same bands made it **worse**, so probe both directions.
- **An LTC tap does not return when its band is restored.** A lever probe that undoes a band change
  leaves the tap where it moved, so only the **first** change after a fresh open is a clean
  measurement; later rows in the same session are contaminated.
