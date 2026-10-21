---
type: method
domain: tooling
topic: contingency
aliases: [rank-new-devices, contingency-severity-ranking, base-case-subtraction,
  configuring-a-rank-run, min-kv, only-new, transmission-only-violations,
  worsening-tolerance, three-way-ranking, relative-severity, fraction-beyond-limit, devices-csv, ranking-new-devices-by-severity]
tags: [esapp, powerworld, simauto, contingency, n-1, ranking, severity, violations, planning-model, synth2k]
---

# Ranking New Devices by the Severity of the Violations Their Outage Causes

## Abstract

Given a contingency AUX built by [new-device-contingency-aux](new-device-contingency-aux.md) — one N-1 contingency per
device that is new in a planning case — solve it and answer **which new device is worst**.

**One file comes out: `devices.csv`, one row per new device, ranked worst first.** It is
the only file at the top of the output directory; the per-metric sorts and the
per-violation-row evidence live one level down in `_audit/`. The question it answers is the
one that gets asked out loud — *without device X, what does this case experience?* — so a
device that was never tested must still have a row, or "absent" and "harmless" become the
same thing.

**The single ordering rests on one idea: the FRACTION BEYOND THE LIMIT.** Percent-of-rating
and per-unit volts genuinely do not share a unit — but each quantity *divided by the limit
it actually violated* is dimensionless, and those are comparable without inventing an
exchange rate. That is what makes a 0.80 pu bus (0.158 beyond a 0.95 floor) outrank a 101%
branch (0.010 beyond its rating), which no per-metric sort does. It still asserts that a 5%
overload and a 5% voltage excursion are comparably bad — but that claim is visible and
checkable, which "percent vs per-unit" never was. The per-metric sorts in `_audit/` keep
the two apart on their own units; this is the one sanctioned crossing.

Six things here decide whether the ranking means anything, and each fails silently:

1. **Subtract the base case — AND attribute the magnitude.** A branch already at 105%
   appears under *every* contingency, so without subtraction every device inherits the same
   overloads (**38% of all rows** on one measured run, 464,794 of 1,218,162). But the
   subtraction only decides *whether* a row counts: a branch at 220% nudged to 221% survives
   it legitimately and then reports **221%** for a device that caused **+1%**. Score
   `min(exceedance, addition)` — see *Attribution* below. Measured at a 60% threshold:
   **97.8% of caused thermal rows are on an already-violating branch, the reported
   exceedance is a median 82.6x what the device added, and 883 of 890 devices move.**
2. **Rank voltage on distance OUTSIDE the band, never on `LimViolPct`.** Low and high volts
   have opposite polarity; one percent key orders one of them backwards.
3. **A device with no violation of a category gets `NaN`, not `0`.** Zero is a real severity
   and sorts above a device that was never measured.
4. **A diverged, missing, or islanding contingency is not a safe device.** Each produces no
   violation rows and is indistinguishable from "caused nothing" unless handled explicitly.
   A diverged device scores `NaN` and ranks **first**: an unknown outranks any measured
   damage, and burying it below hundreds of harmless devices is how an incomplete run reads
   as complete.
5. **Report the bus AS IT SITS, not only its excursion.** `0.037 pu outside the band` and
   `0.913 pu` are the same bus, and only one of them reads as serious. The excursion is
   measured against whichever band the run was configured with, so a reader who forgets the
   band reads a severe bus as trivial. Carry both — the score is built from the excursion
   and must stay auditable.
6. **A device's own area is not the reporting scope.** They routinely differ, and the file
   gives no hint that they do. See *The area trap* below.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Input from:** [new-device-contingency-aux](new-device-contingency-aux.md) — builds the AUX this solves;
  [comparing-planning-cases](../demos/comparing-planning-cases.md) — decides which devices are new
- **Across:** [reading-violationctg](reading-violationctg.md) (the read this ranks, and its traps) ·
  [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the thresholds it ranks against) ·
  [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (solving the set across processes) ·
  [lodf](../concepts/lodf.md) (the unbuilt fix for the islanding gap)

## Content

### Attribution: what the outage is actually responsible for

Subtracting the base case is only half the job, and the missing half is invisible: the row
set is corrected while the *magnitudes* are not. Score each row as the smaller of

    exceedance   how far past the limit the element ended up
    addition     how far the outage moved it

| branch | base | post | limit | exceedance | addition | score |
|---|---|---|---|---|---|---|
| A | 220% | 221% | 100% | 121 | 1 | **1** |
| B | 80% | 150% | 100% | 50 | 70 | **50** |
| C | 105% | 150% | 100% | 50 | 45 | **45** |

You can blame a device for neither more damage than exists, nor more than it put there. The
`min` self-corrects when the base was *below* the limit as well: a branch at 88% taken to
157% has addition 69 but exceedance 57, and only 57 points of it are a violation at all.
A row with no base value was clean, so the whole exceedance is the device's — missing base
data must never silently zero a real violation.

| category | exceedance | addition |
|---|---|---|
| `thermal` | `(pct - T)/T` | `(pct - base_pct)/T` |
| `voltage_low` | `(limit - V)/limit` | `(base_V - V)/limit` |
| `voltage_high` | `(V - limit)/limit` | `(V - base_V)/limit` |

`T` is the run's thermal threshold, so thermal normalizes exactly as voltage does. **Read
the base value with the SAME key the subtraction uses** — unordered bus pair plus
normalized circuit — or a row is filtered against one baseline and scored against another,
which is worse than either alone.

**`LimViolLimit` on a thermal row is the branch's MVA RATING, not 100.** Measured 21, 46,
57, 4352. Thermal must score off `LimViolPct` and voltage off `LimViolLimit`; borrowing the
other's field yields percent-minus-MVA, which is a plausible-looking number.

**Average as well as worst, on the attributed quantity.** The mean over a device's rows
separates one catastrophic element from twenty mildly-over ones — which the count only
half-answers. Computed on absolute percent it would re-inherit the whole base-case
contamination. Measured: the top devices score ~1.16 on their worst element and average
~0.010 across ~190 rows.

### The output table: natural units only

**A number the reader cannot interpret is not a result.** The score below is correct,
dimensionless, and unreadable to someone opening a spreadsheet — and requiring them to
learn the scoring scheme before they can read the answer is the wrong trade for a file
whose whole purpose is to be opened by other people. So the file carries **only** percent
of rating, per unit, and counts; the arithmetic that produced the ordering moves to a
sidecar. The rank stays auditable, it is just not in the way.

| column | unit |
|---|---|
| `rank` | 1..N, dense, worst first |
| `device` `device_type` `from_bus` `to_bus` `kv` `area` | identity and location |
| `ranked_by` | words: `overload` / `low voltage` / `high voltage` / `no violation` / `did not solve` |
| `worst_overload_pct` `avg_overload_pct` | percent of the branch's own rating |
| `worst_voltage_pu` `avg_voltage_pu` `worst_voltage_pct` | per unit, plus PowerWorld's own percent |
| `n_overloads` `n_voltage_violations` `n_violations` | counts |
| `converged` `count_verified` | integrity flags |

**`count_verified` means "no row was dropped between the solve and this table", and it
covers TWO ways rows go missing, not one.** It was originally keyed only off the row-count
mismatch guard, which let a run discard **2,972 unclassified violation rows on one planning model and
still write `count_verified = True` on all 297 devices** — the audit trail was correct and
the file people open was not. An unclassified row now taints its device exactly as a count
mismatch does. The general rule: a
bucket that means *"rows were dropped"* must reach the summary artifact, because `_audit/`
is not what gets mailed.

**Worst and average answer different questions**, and the count answers neither. A device
whose worst overload is 157% and whose average is also 157% overloads exactly one branch;
one with a high worst and a low average has a single hot spot among many marginal
violations. Averages must be taken in the SAME natural unit as the worst — an average of
the dimensionless score reads as noise (`0.064`), and an average of two different units at
once is meaningless even though it is well-defined.

**`worst_*` means most attributable, not highest number.** The reported rows are the ones
that drove the rank. Once the base case is attributed those need not be the arithmetic
maximum — a 221%-on-a-220%-branch loses to a 150%-from-clean one — and printing the
maximum beside a rank derived from a different row is how the two disagree in public.

**What was deliberately taken OFF the file**, and the cost: `severity_score`,
`severity_from`, `avg_severity`, the band excursion, and the per-device *how much did this
device add* figures. All are still computed and written to a sidecar. The accepted cost is
that on a case whose base already carries big overloads, a `221%` row reads as a 221%
device with nothing on the page to say the device only added 1%. That is a real loss; it
was traded for a table anyone can read.

### The one ordering: fraction beyond the limit

`rank` is dense `1..N` — no ties, no gaps — and orders **diverged first**, then
`severity_score` descending, then `CTGLabel` ascending so two runs of the same case agree.

`severity_score` is each violation's fraction beyond the limit it actually violated:

| category | score | example |
|---|---|---|
| `thermal` | `pct/100 - 1` | 157% loading -> `0.571` |
| `voltage_low` | `(limit - V)/limit` | 0.80 pu vs a 0.95 floor -> `0.158` |
| `voltage_high` | `(V - limit)/limit` | 1.10 pu vs a 1.05 ceiling -> `0.048` |

The units cancel, so this is a real dimensionless quantity rather than a fudge factor. **Do
not collapse it to `abs(pct/100 - 1)`** — it is arithmetically identical on all three
categories today, but it gets `voltage_low` right for the wrong reason and would keep
"working" silently if a polarity were ever redefined.

A device that solved and broke nothing scores a measured `0.0` and ranks last; a diverged
one scores `NaN` and ranks first. **There is deliberately no `status` column**: `converged
== False` *is* the diverged set and `n_violations == 0` *is* the silent set, so both facts
stay filterable data rather than a string to parse, and `ranked_by` says which in words.

Derive those labels from the COUNTS, never from the score. A silent device carries a real
`0.0`, not `NaN`, so a test keyed on a missing score never fires for it — a mistake that
leaves the label silently blank on exactly the rows it was written for.

The percentage for voltage is `LimViolPct` **for the row already chosen as worst by
severity**, never a re-max on pct — for `voltage_low`, *lower* pct is worse, so re-maxing
selects the least severe bus while looking entirely correct.

### The per-metric sorts, and why they survive in `_audit/`

| list | sort key | unit |
|---|---|---|
| thermal | worst `LimViolPct` | percent of the branch's own rating |
| voltage | worst pu distance **outside** the band | per unit |
| count | violations the outage caused | count |

Percent-of-rating is what makes differently-rated branches comparable — a 250% overload
outranks a 200% regardless of the MVA behind it. Voltage cannot use percent: measured,
`Bus Low Volts` rows sit *below* their limit with `LimViolPct` in 94-100 (lower is worse)
while `Bus High Volts` sit *above* with pct 100-103 (higher is worse). Ranking both on pct
orders overvoltages exactly backwards. Distance outside the band fixes it: 0.87 pu against a
0.90 floor and 1.13 against a 1.10 ceiling both score 0.03, and are genuinely equally bad.

"Worst single violation" and "broke the most things" are different questions, which is why
the count is its own axis rather than a tiebreaker — and why the single `severity_score`
ordering does not retire these. It answers the first question only.

### The area trap

A device's own area and the **reporting scope** are different things, and nothing in the
file says so. Violations are scoped by `Area.BGReportLimits` in the AUX, which monitors
*violated elements*, not outaged devices — so a device far outside the monitored region is
still solved and still counted, because its outage can violate something inside.

Measured on Synth2k with two of eight areas monitored: **364 of the 531 out-of-area devices
caused in-region violations.** So `n_violations = 0` on an out-of-area device means "causes
nothing in the monitored region", never "was not checked" — and filtering the device table
on area to "recover the region" silently discards 364 real results while looking like a
sensible narrowing.

### Subtracting the base case

Solve the base power flow first and record what was **already** violating, from
`Branch.LinePercent` and `Bus.BusPUVolt` — *not* from `ViolationCTG`, which is
per-contingency and says nothing about the base state. Then a post-contingency violation
counts only if the outage **caused it or made it worse**:

| category | already violating when | worse when |
|---|---|---|
| thermal | `LinePercent >= threshold` | post pct > base pct |
| voltage low | `BusPUVolt < v_min` | post pu < base pu |
| voltage high | `BusPUVolt > v_max` | post pu > base pu |

Three identity rules, each of which silently subtracts nothing if got wrong:

- **The branch key is the UNORDERED bus pair.** Identity is direction-sensitive in the raw
  data, so an ordered key matches nothing — which looks exactly like a base case with no
  violations.
- **The circuit ID is compared as normalized text.** `'10'` from one table, `10.0` after a
  CSV round-trip.
- **Read the base frames AFTER applying the limits**, because `LinePercent` is evaluated
  against the monitored rate set the limit write patches.

**Comparing percent to percent is only valid because both rate sets are pinned.** Write
`LSLineRateSet` *and* `LSLineRateSet:1` to the same value and assert it (see
[powerworld-limitset-setdata](powerworld-limitset-setdata.md)); then the base percent and the contingency percent share a
denominator. Do **not** "fix" this by comparing MVA instead — it was tried: `LinePercent` is
a *from-end* percent (from-end MVA ÷ LinePercent recovers exact ratings — 149.000001,
221.000004, 4352.000046 — while the larger of the two ends gives 149.46, 221.11, which are
not ratings), but `LimViolValue` is not guaranteed to be that same end. The swap moved 5,092
rows on a measured run for no gain, trading a denominator pinned by construction for an
end-mismatch pinned by nothing.

### What must never read as a safe device

An empty result and a clean grid look identical, so each of these is handled explicitly:

- **Diverged** (`CTGSolved != 'YES'`) — no rows. Report separately; never file as "caused
  nothing".
- **Absent from the `Contingency` table** — the run learned nothing about it, which is not
  the same as learning it is clean.
- **Islanding** — solves `YES`, emits **zero** violation rows, and ranks as harmless. Nothing
  in `CTGSolveAll` detects it (see [reading-violationctg](reading-violationctg.md)); [lodf](../concepts/lodf.md)'s `1 − ψ_kk → 0`
  catches it from topology with no solve. Until that is built, say so on every run.
- **All violations pre-existing** — a real result, but keep the raw pre-subtraction count on
  the row, because that device is the one most worth auditing and it leaves no ranked entry.
- **No area monitored** — if every `Area.BGReportLimits` is `NO`, PowerWorld reports nothing
  anywhere and *every* device ranks harmless. Abort; do not warn.

### The bus's own voltage limit, not the band you configured

`Bus.BusVoltCtgLimHigh` / `BusVoltCtgLimLow` are PowerWorld's **effective** per-bus
contingency limits — "Ctg Limit PU Volt presently being used by bus, as specified by its
limit group". A bus carrying `BusVoltLim = YES` overrides the `LimitSet` band the tool
writes, so **the configured band is not necessarily the criterion any given bus was judged
against**, and a baseline that assumes it is will be blind in exactly one direction.

MEASURED on a planning model: three buses carry a **1.05** ceiling while the run was configured for
**1.10**. Sitting at ~1.053 they are inside the configured band, so the baseline never
recorded them; their post-contingency rows carried no `base_value`, were read as violations
the outage CREATED, and survived `--only-new`. **657 of 673 reported rows were those three
buses under all 219 devices** — 219 of 220 devices ranked as causing something, off a
base-case condition. Overlap with the base-case high-voltage set: **0 of 3**. A flat band
cannot detect this; the buses never exceed 1.10 at all.

Two traps in the fix itself:

- **Compare the limits with a RELATIVE tolerance.** They come back single-precision: write
  1.10, read 1.10000002; write 0.90, read 0.89999998. An exact test reported **4000
  phantom overrides on Synth2k**, where all 2000 buses carry exactly the band and
  `BusVoltLim = NO`. Third instance of this trap in one codebase.
- **A zero or missing limit means "not reported", not "a ceiling of zero".** Taken
  literally it puts every bus in the baseline and subtracts the whole case away.

### `CTG_WhatToDoWithBC` and `--only-new` are the same answer

PowerWorld's own `CTG_Options.CTG_WhatToDoWithBC` (0 = do not report base-case violations;
1 = report all; 2 = change-from-base criteria) and this tool's Python-side `--only-new` are
**redundant, not conflicting** — verified rather than assumed. Setting the option to `0` on
Synth2k case4 and running with `--include-worsened` yields **the identical 36-row set** that
`--only-new` yields on the unmodified case: same rows, zero difference either way. Two
independent mechanisms, one inside PowerWorld's contingency engine and one in Python,
agreeing exactly.

Two honest qualifications. The `CTGViol` COUNTS differ (82 vs 153 summed over those 36
rows), because PowerWorld reports fewer violations per contingency when it is suppressing
base-case ones — the row SET is identical, the per-contingency tallies are not. And the two
runs were not config-identical: the `= 0` run screened every voltage level while the
`--only-new` run used a 69 kV floor. The comparison still holds because the kV filter
dropped nothing on this case (its lowest violated element is 115 kV), but that is a
property of Synth2k rather than of the equivalence.

`base_case_violations.csv` is unaffected by the option, because it is read from
`Branch.LinePercent` / `Bus.BusPUVolt` and never from `ViolationCTG` — a `= 0` run still
records its 6 base-case violations and simply drops 0 of them as pre-existing.

**So there is no reason to modify and re-save a case for this.** The flag does the same job
and leaves the case untouched, which matters when the cases are CEII and read-only.

### Measured: what the base case does to the answer

| | case3 (0 base viol.) | | case4 (6 base viol.) | |
|---|---|---|---|---|
| | WITH | WITHOUT | WITH | WITHOUT |
| violation rows | 29 | 29 | 278 | **36** |
| devices causing something | 18 | 18 | 252 | **20** |
| voltage_low rows | 0 | 0 | 8 | **8** |

case3 is the control: zero base-case violations, so the filter is a proven no-op. On case4
**87.1% of the WITH rows were already-broken elements**, six pre-existing violations
inflated the device count **12.6x**, and the thermal median moved `100.125 -> 104.383` while
the **maximum stayed at 153.647** — the worst outage survives either way. The 8
low-voltage rows survive both ways too, which is what shows the filter discriminating
rather than just cutting.

### Configuring a run

**Two CONFIG blocks answering different questions.** The study script's decides WHICH DEVICES get
a contingency and is baked into the AUX. The ranking script's decides WHAT COUNTS AS A
VIOLATION when that AUX is solved. Changing the second never needs the AUX rebuilt;
changing the first always does. Every ranking-script setting also has a flag and **the flag
wins** — CONFIG is the study's standing answer, a flag is a one-off.

| setting | flag | default | decides |
|---|---|---|---|
| `V_MIN` / `V_MAX` | `--v-min` / `--v-max` | 0.90 / 1.10 | post-contingency band, pu — written to `LimitSet`, so it is PowerWorld's own criterion |
| `THERMAL_PCT` | `--thermal-pct` | 100.0 | percent of rating that counts as overloaded |
| `RATE_SET` | `--rate-set` | `A` | which rate set — written to BOTH normal and contingency sets |
| `MIN_KV` | `--min-kv` | 69.0 | report only where the VIOLATED element is above this kV; 0 disables |
| `ONLY_NEW` | `--only-new` / `--include-worsened` | True | report only elements CLEAN in the base case |
| `SERIAL` | `--serial` / `--parallel` | False | one process (reference path) or many |

**The three filters stack and each can empty the report.** `MIN_KV`, `ONLY_NEW` and the
base-case subtraction are independent and compound hard. Measured on Synth2k case4: 786
attributable rows, subtraction drops 508, `--only-new` drops 242, **36 survive** (890
devices to 20 ranked). A near-empty result is far likelier to be three filters stacking than
a clean grid, so the run header prints the band, the kV floor and the reporting mode, and
every silent device carries three counters — `n_violations_raw` (pre-filter),
`n_below_kv`, `n_worsened_only`. **Never add a filter without a per-device counter beside
it**: it shipped once without one, and at `--min-kv 200` the branch ranked #2 at 133.9% of
rating came out at rank 585 reading `n_violations = 0`.

**`MIN_KV` screens the VIOLATED element, on its HIGHER end, strictly above.** Not the
outaged device — a generator sits at its terminal kV (13.8-20 kV on Synth2k), so screening
devices would delete every generator contingency while looking like a voltage filter. The
higher end is a deliberate trade, and NOT (as first written) for consistency with
`device_attributes`, whose `kv` is an identity label rather than a membership test: the
strict both-ends rule is cleaner on distribution but drops a 500/161 autotransformer from a
200 kV screen, and a vanished bulk asset beats clutter. Consequence to know: at
`--min-kv 100` every 115/13.8 step-down passes. `element_kv_low` is carried so the strict
rule can be applied afterwards without re-solving. A transformer overload is ONE MVA limit
on the whole device, so `element_kv` is a convention about the ASSET, not a property of the
row.

**`ONLY_NEW` discards real N-1 effects on purpose.** A pre-existing violation the outage
worsened is a genuine failure, and the attribution already credits only the increment. This
narrows the question from *what does this make worse* to *what does this BREAK*. Rows go to
`_audit/worsened_preexisting.csv`, counted per device — excluded by policy, not as noise.

**`WORSENING_REL_TOL = 1e-4` is a constant, not a knob.** The floor below which a
difference is solver noise, RELATIVE to the base value. Deliberately not a flag: a
solver-precision number is a property of the numerics, not a planner's decision, and a flag
invites silencing a flaky run by inflating it into a materiality threshold.

**Do not confuse any of this with `set_limit_monitoring.py`.** That standalone script sets
`CTG_Options.CTG_WhatToDoWithBC` (0 = do not report base-case violations; 1 = report all;
2 = change-from-base criteria) and is **not part of this pipeline**. Applying 0 to a case
this tool consumes double-filters: PowerWorld suppresses base-case violations before Python
sees them, deleting the worsened rows the subtraction deliberately keeps.

### Solving it across processes

The set comes from an AUX, so each worker can `Delete(Contingency)` + `LoadAux` the **same
file** and solve its own chunk — provably the same set, and no saved case required (see
[parallel-contingency-solve](../concepts/parallel-contingency-solve.md), whose original form needed one). The merge is a plain
**concat** of per-contingency `ViolationCTG` rows, not that page's per-bus envelope merge,
which cannot say *which* outage caused what.

Assert the merged result covers **every dispatched label**: a worker that dies after
returning an empty frame contributes nothing and its share of the grid reads as clean.

Measured on Synth2k case 3, 890 new-device contingencies: **27.1 s serial vs 38.8 s across 7
workers** — parallel is *slower* here, because each worker pays a fixed 20-45 s PowerWorld
`open()` that does not parallelize away. It earns its keep on a planning model, not on a 2k
case.

**"Byte-identical ranked CSVs" was claimed here and is FALSE — measured 2026-08-22.** The
two paths reach the same operating point by different Newton trajectories, so solved values
differ in their last digits, and a threshold applied to a noisy float is a coin flip near
the boundary. On case 4 the old absolute tolerance gave **460 caused rows serial vs 459
parallel**, flipping one device between ranked and silent. What holds after the relative
tolerance fix, and what to actually assert:

- the caused violation **set** is identical, row for row;
- the **ranked/silent partition** is identical;
- `rank` may differ only among devices whose `severity_score` differs by less than
  `WORSENING_REL_TOL`. Measured: 10 of 890 devices REORDER, by at most 5 positions, all in
  ranks 131-238, none in the material band, with a maximum severity difference among those
  ten of **8.5e-07**. That is not a suite-wide bound and must not be quoted as one — 110
  devices carry a nonzero severity difference, the largest being **1.1e-06**. They simply
  do not reorder, because the gap to their neighbour is wider than the wobble.

## Provenance

**2026-08-22 (b)** — **the baseline was judging buses against the wrong number.** A bus can
carry its own contingency voltage limits that override the `LimitSet` band the tool writes,
and the baseline was testing every bus against the configured `v_min`/`v_max`. On that planning model
three buses at a 1.05 ceiling, sitting at ~1.053, were therefore invisible to it — and
**657 of 673 reported rows were those three buses re-reported under all 219 devices**, with
219 of 220 devices ranked as causing something. `from_case` now reads
`BusVoltCtgLimHigh`/`Low` and judges each bus against the limit PowerWorld applied,
falling back to the band only where a case reports none. Comparing those limits needs the
relative floor too: they come back single-precision (1.10 -> 1.10000002), and an exact test
reported 4000 phantom overrides on a Synth2k case where every bus carries exactly the band.

Separately verified, and it settles a question that had been assumed both ways:
**`CTG_WhatToDoWithBC = 0` and `--only-new` produce the identical 36-row set** on Synth2k
case4. Redundant, not conflicting; no case needs modifying or re-saving to get the
behaviour. `set_limit_monitoring.py`, which sets that option, turned out never to have run
at all — its input path pointed at a case that does not exist — and it verified its own
write from memory BEFORE saving, so a no-op save would have passed. Both fixed.

Suite 292 -> 305 tests.


**2026-08-22** — **two scope filters added, one absolute tolerance replaced, and a
reproducibility claim retracted.** `MIN_KV` (report only violations above a nominal kV,
judged on the violated element's higher end) and `ONLY_NEW` (report only elements clean in
the base case) are now the study defaults at 69.0 / True. Three defects caught by review
before either shipped: the per-device pre-filter count was computed DOWNSTREAM of the kV
filter, so a device whose every violation was out of scope read identically to one that
breaks nothing (at `--min-kv 200` on case3, 14 of 18 offending devices, including the
branch ranked #2 at 133.9% of rating landing at rank 585 with `n_violations = 0`); a branch
with one unresolvable end was screened on the other, so a 345/13.8 transformer missing its
345 kV bus would be deleted as distribution; and `min_kv` was echoed nowhere, making a
filtered and an unfiltered run byte-identical on disk.

`THERMAL_TOL`/`VOLTAGE_TOL` (absolute 1e-6) replaced by one **relative**
`WORSENING_REL_TOL = 1e-4` via `baseline.worsened()`, mirroring the fix `limits.py` had
already made for its own read-back check. An absolute 1e-6 on a percent near 100 asks for
~1e-8 relative precision — below one float32 ULP there (7.6e-6) and far below solver
repeatability, so it was not a tolerance, it was `>`. Measured: a branch at 100.072085% in
the base case read 100.072148% after one outage, 6.3e-5 pp, and the absolute test admitted
it. Effect on case4: caused rows 460 serial / 459 parallel to **278 / 278, identical row for
row**; devices "causing a violation" 431 to 252, with all 36 material devices still in the
top 36. **The "byte-identical ranked CSVs" claim recorded here on 2026-08-18 is retracted**
-- see *Solving it across processes* for the invariant that does hold.

Suite 238 to 292 tests. The regression test pins the DERIVATION, not the number: the floor
must exceed float32 resolution at a base of 100, which is what would have caught the
original.


**2026-08-18 (b)** — **attribution added, and it changes the answer.** Subtracting the base
case was only filtering rows, not correcting magnitudes, so a device that nudged an
already-broken branch outranked one that broke a healthy line. Measured on Synth2k with the
threshold at 60%: 878 base thermal violations, **97.8% of caused thermal rows on an
already-violating branch**, reported exceedance a **median 82.6x** what the device added,
and **883 of 890 devices change position** once scored on `min(exceedance, addition)`.
At the default 100% threshold Synth2k has no base thermal violations so the thermal top-10
is unchanged, but its 13 base *voltage* violations still move 624 of 890. `severity_score`
and `avg_severity` were both recomputed independently from the raw rows and matched to
**2.8e-16** and **1.05e-16**.

Two facts found along the way, each of which produces a plausible wrong number rather than
an error: **`LimViolLimit` on a thermal row is the branch's MVA rating** (21, 46, 57, 4352),
not 100 — so thermal must score off `LimViolPct`; and the LimitSet read-back used an
**absolute** `1e-6` tolerance on `LSLinePercent`, which lives near 100 where float32 cannot
resolve that finely. Wrote 60.0, read back 60.00000238418579, run aborted claiming every
violation was measured against the wrong limit. The default 100.0 passed **only because 1.0
is exactly representable in binary**, hiding it for every threshold except the default; the
tolerance is now relative to the value's magnitude.

**2026-08-18 (a)** — the three ranked lists were collapsed into a single ranked `devices.csv`
with the `relative_severity` ordering, on `Synth2k_case` (890
new-device contingencies, band squeezed to `[0.95, 1.05]` to force voltage rows). Exit 0 in
40.5 s across 7 workers. Every number in the file was recomputed independently from the raw
violation rows: `severity_score` matched to **2.6e-16**, thermal percent to **0.00e+00**,
and the counts exactly. Two consecutive parallel runs produced a **byte-identical** file
(sha256), confirming the `CTGLabel` tiebreak holds under real worker scheduling. The shared
scale visibly reorders: thermal and voltage interleave between ranks 16 and 20, a voltage
device at `0.0386` outranking a ~103% overload at `0.0310`.

Two paths that case could **not** exercise, and which stay unit-test-only until a planning-model run:
zero diverged contingencies (so `converged=False` and the NaN-ranks-first rule), and zero
`voltage_high` rows — all 4,238 voltage rows were `voltage_low`, leaving the polarity half
of the severity function unmeasured on real data.

Measured 2026-08-17 by a ranking script written for the purpose, on
`Synth2k_case` with the 890-contingency new-device AUX, and against
the regional planning models for the base-subtraction and parallel figures. The 38%
pre-existing figure comes from a deliberately squeezed band (`[0.99, 1.01]` pu, 25% thermal)
run to force every violation category to appear — the same technique used in
[reading-violationctg](reading-violationctg.md).
