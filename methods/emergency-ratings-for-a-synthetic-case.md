---
type: method
domain: synthetic-grid
topic: contingency
aliases: [emergency-ratings-for-a-synthetic-case, rate-b-c-design, emergency-rating-design, rate-b-rate-c]
tags: [synthetic-grid, contingency, powerworld, thermal]
---

# Method: Designing emergency ratings (Rate B / C) for a synthetic case

## Abstract

How to give every branch of a synthetic case its own Rate B and Rate C from a reviewer's aggregate statistics
(mean, min, max uplift per voltage class and device type), instead of one flat ratio. Covers the class mapping,
the per-branch draw, why % beats MVA, C >= B, and what must happen after, plus the basis behind any uplift: a planning manual's
Rate 1–5 definitions, a published FAC-008 method, and IEEE 738 / C57.91 on catalogue ratings. Read before setting
any emergency rating.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-base-case-violations](remediating-base-case-violations.md) (copy the rating
  set when cloning a branch) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the limit set contingency analysis reads) ·
  [timestep-dispatch-into-design-bands](timestep-dispatch-into-design-bands.md) (the same idea for dispatch: match a distribution, not one value)

## Content

### Why not one flat ratio

A flat rule (for example every line B = 1.25 x A, every transformer 1.15 x A, C = B) gives every device of a type
identical headroom. A reviewer reads that as unrealistic, and it is: post-contingency loading in % of Rate B then
ranks branches exactly as % of Rate A does, so the emergency rating adds no information. Vary it at three levels
instead: by voltage class, by device type, and by branch.

### The basis: what each rating means, and where an uplift comes from

**Definitions (a US ISO's public steady-state planning procedure manual, §4.4.1.4).** Rate 1 Normal (continuous), Rate 2 Emergency (2 h),
Rate 3 15-Minute (after a step from 90% of normal), Rate 4 Transformer 2-Hour / Branch Conductor, Rate 5 Relay
Loadability. "By definition, Rate 5 >= Rate 3 >= Rate 2 >= Rate 1 and Rate 4 >= Rate 2 >= Rate 1." Security studies
default to Rate 2. A rating may not exceed its most limiting series element, so terminal equipment caps Rate 1 and
Rate 2. In PowerWorld terms A = Rate 1 (intact case), B = Rate 2 (contingencies), C = Rate 3, hence `C >= B`. **The
manual gives no uplift number.** Each transmission owner sets its own method under NERC FAC-008, so cite a method for
any ratio, never the manual.

**A published FAC-008 method** (one US utility, 2020 revision): bare overhead conductor at 75 °C
normal and 100 °C for a 4-hour emergency, at 40 °C ambient; autotransformers per IEEE C57.91 at 115% for 4 h and
125% for 30 min; generator step-ups given no emergency rating above nameplate. That is the usual source of a flat
"lines a bit over 1.2, transformers 1.15" rule. [Certain, read at source]

**IEEE 738 on the case's own conductors** (calculated 2026-10-18 for a ~9k-bus synthetic case). A synthetic
case's line Rate A usually comes from a catalogue table. Dividing its MVA by √3·kV recovers the classic catalogue
ampacity: 75 °C conductor, 25 °C ambient, 2 ft/s wind, full sun. An IEEE 738 steady-state run at those conditions
reproduces the table within about 3% from 336 to 2156 kcmil. [Likely] What follows from that:
- At the same weather, a 75 → 100 °C emergency step gives **1.22–1.24 × A** across conductor sizes. The tables give
  the same amps per subconductor at every voltage, so one ratio fits every line class.
- **Rate A is optimistic for a 40 °C summer peak.** The same 100 °C emergency at 40 °C ambient gives only about
  1.07–1.13 × the catalogue A. Using that number mixes a weather correction into the uplift; keep the two apart.
- A 125 °C emergency gives about 1.45–1.53 × A, too far without an annealing study.
- Rate C: the IEEE 738 transient from 90% preload up to 100 °C in 15 minutes gives about 1.3–1.6 × A, rising with
  conductor size. Terminal equipment caps it well below that, so the 15-minute rating is set by terminal gear, not
  conductor.

**Transformers.** An IEEE C57.91 thermal model (140 °C hot spot, 35–40 °C ambient, typical parameters, not a
nameplate) gives about 1.25–1.35 for 2 h and 1.19–1.25 for 4 h. A published 1.15 for 4 h sits below that because it
also covers bushings and other parts the model leaves out. **Do not use the ONAN → ONAF nameplate step (about 1.33)
as an emergency factor** if Rate A is already the forced-cooled rating: it counts the same fans twice.
Step-ups: emergency = normal under the method above, and a unit
cannot push more than its maximum output through its step-up anyway. [Likely; the C57.91 parameters are typical
values]

**Why not run IEEE 738 per line for a planning case.** The conductor data carry no temperatures and no emergency
column, so each line's ratio needs assumed temperatures and weather, and the answer reflects those choices more
than the conductor. It also does nothing for transformers, about a quarter of the branches. Per-class bands drawn per
branch (below) give the same spread with stated assumptions.

### Inputs

Per (voltage class, device type), from the reviewer's statistics:

| field | definition |
|---|---|
| uplift % | `100 x (B - A) / A`, and the same for C |
| mean uplift % | the class average; the one number the design must reproduce |
| mean MVA uplift | `B - A` averaged over the class; used as a check only |
| min / max | usually 0 and an extreme tail; **never use them as the band** |

If the statistics carry only mean, min and max, the spread is unknown and any band width is a judgement call. Say so
in the report.

### Mapping a branch to a class

- **Line:** its nominal kV.
- **Two-winding transformer:** the high/low kV pair, with every side at or below 35 kV in one `<=35` bucket.
  Generator step-ups land in `<kV>/<=35`. Pairs the statistics do not list go to an "other pairs" row.
- **Three-winding transformer:** PowerWorld models each winding as a branch to a star bus at 1 kV, so classify each
  winding by its own terminal kV. The `<=35` row is the tertiaries.
- **A class with no statistics** (for example a voltage the reviewer's system lacks) falls back to the nearest
  class below of the same device type. Report every fallback.

Every branch must map to exactly one row. Count the unmatched before writing anything.

### The rule

1. Rate A is never touched.
2. Per branch, draw `p` uniformly in `[0.5 m, 1.5 m]`, where `m` is the class mean %. Use a fixed seed so a rerun
   writes the same ratings. `B = A x (1 + p / 100)`.
3. Draw C the same way from its own class mean, then lift it to at least B: **`A <= B <= C` on every branch**, as
   the rating definitions above require.
4. Skip breakers, jumpers and zero-impedance ties, and any branch with Rate A = 0. List the skipped ones.
5. Overwrite an existing B or C only after saving the originals (keys plus old B and C) as the undo.
6. Read every written rating back, and assert A unchanged and `A <= B <= C`. Ratings are single precision, so the
   tolerance is about 0.05 MVA, not 1e-6.

### Why the band is 0.5x to 1.5x the mean

- **Min to max is useless.** With a 0% floor and an extreme top, a uniform draw lands far above the real mean. The
  top tail also gives a few branches a Rate B so loose they can never overload, which hides real N-1 problems.
- **A band a few points wide is a flat ratio again.** Every device of the class gets nearly the same uplift.
- **0.5x to 1.5x keeps the class mean on average** (a uniform draw centred on it; check the realized mean per
  class) and gives a visible spread. If the statistics include percentiles,
  use the 25th to 75th instead; that is measured, not chosen.
- **Model a share at 0% only if you know the share.** A minimum of 0 says at least one device has B = A, not how many.

### Why % and not MVA

Emergency uplift is thermal, so it scales with device size. A fixed MVA uplift taken from someone else's fleet scales
backwards: tiny on a large unit, huge on a small one. Use the reviewer's mean MVA uplift as a **report-only** check.
Divide it by the mean % and you get the reviewer's implied mean Rate A; compare that with your own class mean Rate A.
A large gap means the two populations differ in size, not that the % rule is wrong. Measured 2026-10-20 on a
synthetic ~9k-bus case: about half the classes matched within about 15%. On the step-up classes, % gave several times
the reviewer's MVA average, because the reviewer's class was mostly much smaller units than the synthetic case's
step-ups.

### When the statistics show mean C below mean B

If every device had `C >= B`, the class mean C % could not be below the class mean B % over the same devices. A lower
C mean therefore means a different population (blank C excluded, for example) or a C column that is not the
15-minute rating. Do not copy it into the case. Force `C >= B` and report how many C draws were lifted.

### After the ratings are written

- **Contingency analysis must monitor Rate B.** Filling B changes nothing if the contingency limit set still reads A.
  The field is `LimitSet.LSLineRateSet:1` (contingency rate set); `LimitSet.LSLineRateSet` is the normal one, and
  no `CTG_Options` field overrides either (Simulator 25 field export). Write the **whole** `LimitSet` row, or
  `SetData` fails on missing key fields ([powerworld-limitset-setdata](powerworld-limitset-setdata.md)). Read it back
  comparing only the letter, since a case with named rate sets returns `B: RATE2`. Then read `Branch.LSLineRateSet:1` (read-only) to confirm what
  each branch actually uses.
- **Keep normal on A and contingency on B, and know what that costs.** With the two set differently, a pre-contingency
  `Branch.LinePercent` divides by A and a post-contingency `ViolationCTG.LimViolPct` divides by B, so the two
  percentages are not comparable. Compare in MVA, or label each percentage with its rating.
- **Rerun the full N-1.** A per-branch draw puts some branches below the old flat ratio, so a violation list built
  against the old limits misses rows. Re-checking only the old violations is not enough.
- **Report the spread** per class: count, min / median / max uplift %, C draws lifted to B, and the MVA check. That
  table is the evidence that the ratings are not unified.

### Restricted statistics

A reviewer's statistics may be restricted to internal review. Your % times your own Rate A gives their number back,
so the band file stays local and out of every shared report; the report shows spread and pass/fail flags, not the
reviewer's values. Banding and widening put a chosen distribution in the case, not their exact table. Whether that is
far enough from the source is the data owner's call.

### Upgrade path

A random draw has no reason behind any one branch's value. If a reviewer asks "why 27% here and 21% there", tie
line uplift to conductor type through the IEEE 738 transient rating (IEEE 738 §4.4.2) and transformer uplift
to IEEE C57.91 loading. At a fixed temperature step and fixed weather the steady-state line ratio barely varies by
conductor (1.22–1.24, basis section above); the 15-minute transient ratio does (about 1.3–1.6, rising with size).
