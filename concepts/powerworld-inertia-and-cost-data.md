---
type: concept
domain: cross-cutting
topic: case-audit
aliases: [TSH, GenMCost, GenInertia, inertia constant]
tags: [powerworld, inertia, cost-curve, dynamics, gotcha]
---

# PowerWorld inertia (`TSH`) and cost (`GenMCost`) field semantics

## Abstract

Four non-obvious PowerWorld/esapp case-data facts, found the hard way while building a
generator dispatch algorithm, for any project that touches generator inertia or cost data:
(1) `Gen.TSH` is H on a **100 MVA system base**, not the generator's own `GenMVABase`,
**and the "don't multiply by `GenMVABase`" rule that follows from it inverts the moment you
synthesize H yourself instead of reading it**
(this bit a second time on 2026-07-27; see the ⛔ box in §1 before writing any inertia
code); (2) `Gen.GenMCost` is a **live** cost-curve
evaluation at the case's *current* `GenMW`, not a fixed per-unit rate; (3) a system's official
zonal scheme may already be modelled natively as `AreaNum`/`AreaName`, in which case no
spatial join is needed; (4) a sibling project's fuel-category *name* doesn't
always match its actual `GenFuelType` mapping, so verify against source code, not the
label. Read the Content section before writing any code that sums inertia, ranks
generators by cost, needs zonal load data on a Synth2k case, or reconstructs
per-generator detail from another project's category-level summary.

## Connections
- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) ·
  [per-unit-basis-discipline](per-unit-basis-discipline.md) (the transferable rule)
- **Found in:** a generator dispatch study, where §1's original wording failed in practice
  and the fuel-mapping trap below cost a rebuild.

## Content

### 1. `Gen.TSH` (inertia constant H) is on a 100 MVA system base

`esapp` has no `GenInertia` attribute; inertia lives on the `Gen` object as `TSH`.
But `Gen.TSH`, read via `pw[Gen, ["TSH", "GenMVABase"]]`, is **not** the per-unit
inertia constant on the generator's own MVA base. It is H expressed on a fixed
**100 MVA system base**, a standard PSS/E-style dynamics convention. Confirmed two
independent ways on a Synth2k case:

- **Round-number test:** converting via `H = TSH * 100 / GenMVABase` lands every
  nuclear unit and nearly every coal unit on exactly `4.00` seconds, inside the
  published per-technology ranges operators tabulate (nuclear and coal both sit
  around 3–4.5 s). That is not a coincidence at that precision.
- **Direct cross-check:** the case's own `MachineModel_GENROU` (round-rotor) and
  `MachineModel_GENSAL` (salient-pole, e.g. hydro) dynamic model objects expose a
  `TSH` field of their own, and it reads the true per-unit H **directly, no
  conversion needed**: e.g. `4.0` for the same generator whose `Gen.TSH` reads
  `56.888`. The ratio between the two paths is exactly `GenMVABase/100` for every
  unit tested.

**Correct formula** for total system inertia (GW·s) over online synchronous units,
**when `TSH` is read from the case**:
```
GW·s = Σ(Gen.TSH) * 100 / 1000     # do NOT multiply by GenMVABase -- already implicit
```
Multiplying `TSH * GenMVABase` (the intuitive-looking but wrong formula) overstates
inertia by roughly `GenMVABase/100` per unit, ~13x too high for a ~1,400 MVA nuclear
unit.

> #### ⛔ The precondition on that rule — read before reusing the formula
>
> **"Do NOT multiply by `GenMVABase`" holds only because real `Gen.TSH` has already been
> multiplied by it.** That is a property of *the field*, not of inertia. If you are
> **synthesizing** H yourself (assumed values from an operator's published table, a textbook, or any
> per-machine source), H is on the **machine's own base** and you **MUST** multiply:
>
> ```python
> gens["H_assumed"] = gens["GenFuelType"].map(INERTIA_ASSUMED_BY_FUEL)
> gens["TSH"] = gens["H_assumed"] * gens["GenMVABase"] / 100.0   # re-base, THEN use the formula
> ```
>
> Writing assumed H straight into a column named `TSH` silently asserts every generator is
> 100 MVA. **This exact regression happened** on 2026-07-27, on a Synth8k
> case with *no* measured `TSH`, so all three notebook builders took the assumed-data path,
> which this page's original wording did not cover. Fleet inertia came out about 51% of its
> true GW·s value, nuclear about 9%. Because the error scales with machine
> size it was **non-uniform**, so unit *commitment order* was wrong too, not just totals.
>
> Physically, **H alone is not an inertia quantity.** System inertia is defined as
> `M_sys = Σ Hᵢ · MVAᵢ`: seconds must be weighted by machine size before they mean anything
> at system level. So for any downstream analysis, **unit count is not a proxy for
> inertia**; many small machines can carry less than a few large ones.
>
> The general lesson (guidance inherits the preconditions of the data it was derived from)
> is [per-unit-basis-discipline](per-unit-basis-discipline.md).

`MachineModel_GENROU`/`GENSAL`'s own `TSH` is the more robust source (no
conversion arithmetic to get wrong) but only covers round-rotor + salient-pole units.
Verify the two object types' record counts sum to the full synchronous fleet before
trusting it on a new case family.

### 2. `Gen.GenMCost` is a live evaluation at the case's *current* `GenMW`

`GenMCost` (marginal cost, $/MWh) is not a fixed per-unit number. It is PowerWorld
re-evaluating each generator's cost curve (`GenCostModel`, `GenCostCurvePoints`) at
whatever `GenMW` the case currently holds. Confirmed: `GenMW` correlates **0.95** with
`GenMCost` in a real case (marginal cost rises with output, as expected for a convex
cost curve).

**Consequence:** if you want to rank generators by cost *at a specific dispatch
point* (e.g. their `GenMWMin`, for a must-run/backstop step), reading `GenMCost` as-is
gives you cost at whatever the base case's *original* operating point was, which can
differ from the true value at your intended dispatch point by double digits of percent
(one tested unit: 6.37 → 5.56 $/MWh, a ~13% swing, when forced from its base-case
`GenMW` down to `GenMWMin`).

**Technique — live re-evaluation without saving:** temporarily overwrite `GenMW` for
the candidates via the bracket write interface, re-read `GenMCost`, then restore the
original `GenMW`, entirely in memory against the live SimAuto session, with nothing
written to the `.pwb`:
```python
orig = pw[Gen, ["BusNum", "GenID", "GenMW"]]
mw_at_target = orig["GenMW"].copy()
mw_at_target[mask] = target_values  # e.g. GenMWMin for the units you care about
pw[Gen, "GenMW"] = mw_at_target.tolist()

recomputed_cost = pw[Gen, ["BusNum", "GenID", "GenMCost"]]

pw[Gen, "GenMW"] = orig["GenMW"].tolist()  # restore -- verify max diff == 0.0
```
This generalizes to any PowerWorld field that's live-derived from `GenMW` (or other
mutable state) rather than stored directly. Check for this before trusting a field that
looks like a fixed property.

**Two silent-zero traps, and neither field settles it alone.** `GenCostCurvePoints == 0`
with `GenMCost == 0` means no cost curve was ever fit: no real cost data, never "free". But
a unit with curve points can read `GenMCost == 0` because its curve is 0 at today's output
(wind and solar: a price of zero, not missing data), and some Cubic units read
`GenCostCurvePoints == 0` with `GenMCost > 0`, because a cubic model is evaluated from its
coefficients. A unit has cost data when `GenCostModel` is not None and it has curve points
or a cost above 0 at today's output (`GenCostCurvePoints > 0 OR GenMCost > 0`); see the
dated notes (2026-09-30 and 2026-10-01) in [opf-preconditions](opf-preconditions.md).
Guard explicitly on that before using cost data to rank or select
generators, or a data gap silently becomes "dispatch this first."

### 3. Check `AreaNum`/`AreaName` before doing a spatial join

`AreaNum`/`AreaName` are native PowerWorld fields carried on **both `Gen` and `Load`**
objects, and a case is often built with the system operator's own zonal scheme already
encoded in them. Verify that before writing any geographic join: where it is populated,
zonal load and generation analysis needs no spatial work at all.

Don't confuse it with a **custom region field**, typically something like
`CustomString:2`, written by a case-specific spatial join against a boundary shapefile.
Two things regularly make such a field the wrong key: it is usually **generator-scoped
only**, never written to loads, and its distribution can be so dominated by a single
bucket that it differentiates nothing. Check the value distribution before you group by
it. `AreaNum` is the right key for zonal granularity *inside* one system; a region field
is right only when the analysis genuinely spans regions.

### 4. Another project's fuel-category name doesn't always mean what it says

Not a PowerWorld field-semantics gotcha but the same *don't-take-a-label-at-face-value*
family. A companion dispatch script's `"GAS_CT"` category actually maps to Synth8k's
`GenFuelType == "DFO (Distillate Fuel Oil)"`, not `"NG (Natural Gas)"`, confirmed by
reading the source's own fuel-classification code. Conflating the two misassigns
`TSH`/cost and mis-totals capacity. When reconstructing per-generator detail from another
project's per-category summary output, verify the category↔`GenFuelType` mapping against that project's actual
classification code, never the category's plain-English name.
