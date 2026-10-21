---
type: concept
domain: cross-cutting
topic: case-audit
aliases: [per-unit basis, base conversion, normalization base, basis discipline]
tags: [per-unit, normalization, powerworld, gotcha, data-provenance, technique]
---

# Per-unit basis discipline — a normalized number is meaningless without its base

## Abstract

A per-unit or normalized quantity is a **pair**: the number *and* the base it was
normalized against. Store only the number and you have stored nothing recoverable — yet
per-unit values look like plain scalars, so they get copied between sources, written into
shared columns, and summed, with the base silently changing underneath. This page is the
reusable form of a mistake that hit dispatch twice: the second time *because* the
documented fix was written down without its precondition. Read it before mixing a
case-read normalized quantity with a synthesized or textbook one, and before trusting any
"correct formula" recorded from a previous session.

## Connections
- **Up:** [Home](../index.md)
- **Across:** [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md) (the concrete `TSH` case) ·
  [esapp](esapp.md)
- **Found in:** a generator dispatch study — an inertia-basis regression, and a later round
  of dispatch corrections with the same cause.
- **💡 Applies to:** reactive planning (synchronous-condenser and SVC machine bases) ·
  real-power planning (per-unit r/x/b) · normalized load fractions, where the per-zone and
  whole-system denominators differ · [gic](gic.md) · any study that sums or ranks a
  normalized quantity across heterogeneous equipment

## Content

### The rule

> A per-unit value carries an implicit denominator. Two per-unit numbers are only
> comparable — and only **summable** — if they share a base.

Three failure shapes, in increasing order of nastiness:

1. **Wrong base, uniformly.** Everything is off by one constant factor. Bad, but the error
   is visible in totals and usually caught by a sanity check.
2. **Wrong base, non-uniformly.** The base varies per device, so the error varies per
   device. Totals are wrong *and* any **ordering, ranking, or selection** built on the
   values is wrong. This is far worse, and much harder to spot, because nothing looks
   obviously broken — it just quietly picks the wrong equipment.
3. **Two different bases in one column.** A field populated from two code paths — read
   from source on one, synthesized on the other — where only one path re-bases. The column
   name is now a lie for half its rows.

### The worked case: PowerWorld `TSH`

The inertia constant H (seconds) is per-unit on **each machine's own MVA base**.
PowerWorld's `Gen.TSH` is the same H re-based onto a fixed **100 MVA system base**:

```
TSH = H · GenMVABase / 100          system inertia (GW·s) = Σ TSH · 100 / 1000
```

Both expressions are "inertia in seconds." Neither is wrong. They are not interchangeable.

On the Synth8k case `GenMVABase` spans **2.2 – 1,444.4 MVA (median 170)**, so treating
assumed H as if it were `TSH` produced failure shape **2**: fleet inertia read about 51% of
its true GW·s value, nuclear about 9%, and the unit-commitment order in the
dispatch algorithm was silently wrong.

The physical statement underneath: **H alone is not an inertia quantity.** System inertia is
`M_sys = Σ Hᵢ · MVAᵢ`. Seconds must be size-weighted before they mean anything at system
level — which is also why *unit count is not a proxy for system inertia*.

### The meta-lesson: guidance inherits preconditions

This is the part worth carrying to every other project, and it is why the bug recurred.

The 2026-07-14 session found the original inertia error and recorded the fix as a rule:

> `GW·s = Σ(Gen.TSH) · 100 / 1000` — **do NOT multiply by `GenMVABase`, it's already
> implicit.**

That is correct — *for values read out of a case*. It was written down without the
qualifier, because at the time only one data path existed. Later a case arrived with **no
measured `TSH` at all**, so H had to be synthesized from published typical values. On that
path the rule **inverts**: you must multiply. Anyone — human or agent — following the
recorded guidance while writing the new path would produce exactly the bug that shipped.
And one did, in all three builders.

> **A documented correction is only valid under the conditions of the data it was derived
> from.** When you record a rule, record what made it true. When you *apply* a recorded
> rule, check that its precondition still holds — especially if the data source changed.

Practical habit: state the rule's scope in the same sentence as the rule.
"Don't multiply by the base" → "don't multiply by the base **when reading `Gen.TSH` from
the case, because it is already re-based**."

### How to make it stick (what actually worked)

Documentation alone demonstrably failed here — it was written down and the bug still
recurred. Two mechanical guards were added instead, and both earn their keep:

- **Assert on the physical magnitude, at compute time.** `assert 460 <= fleet_gws <= 480`
  in the notebook cell catches every wrong-base variant regardless of how it was
  introduced, because it checks the *answer*, not the code. Cheap and high-yield.
- **Assert on the code shape, in CI.** A source-level test that greps the conversion works
  without a PowerWorld licence — but write it **precisely**. The first version accepted
  `/ 1000` (because `"100" in "1000"`) and an inverted `H · 100 / GenMVABase`. Anchor the
  regex and mutation-test the guard by reintroducing the bug and confirming it fails. A
  guard that silently accepts the defect is worse than none: it advertises coverage it
  doesn't have.

Prefer the magnitude assert if you only do one. It is source-agnostic and it fires before
a wrong number reaches a document.

### The same trap with a length base: per-mile impedance entered as the total

A line's impedance has a hidden second denominator, its length. A value copied from a
per-mile table and entered as the whole line's impedance is off by exactly the line's
mileage. That is often 30 to 100 times, and the case still solves, just with a line far
stronger than the real one.

Use magnitude as the check. On a 100 MVA base, an overhead line's reactance is roughly
**2e-4 pu per mile at 500 kV** and **1.2e-3 to 1.5e-3 pu per mile at 230 kV**. So a line
whose *total* X sits near those numbers is almost certainly per-mile data: multiply by its
length. A 60-mile 500 kV line should carry about 0.012 to 0.015 pu, not 0.0002. Name that
cause when you see it. A "typical value" from memory is a weaker answer than the length
ratio the case itself shows.

### Checklist when a normalized quantity enters a project

- What is the base — system-wide constant, per-device, or per-zone?
- Does every row in this column share it? If the column is populated from more than one
  source, the answer is probably no.
- Does the base *vary across devices*? If yes, a wrong base corrupts **ordering**, not just
  totals — check any ranking or selection downstream.
- Is there a physical sanity band (a published typical range) to assert against?
- If I am reusing a recorded formula: what data path was it derived for, and am I on it?
