---
type: concept
domain: cross-cutting
topic: contingency
aliases: [non-regression-oracle, dominance-test, is-this-change-safe, acceptance-criterion,
  no-worse-than-base, per-element-check]
tags: [verification, contingency, n-1, remediation, acceptance-test, technique]
---

# Aggregate clauses cannot bound one row

## Abstract

Any "is this change safe?" test built from **counts, maxima, sums and set membership** is blind
to one element getting arbitrarily worse, because another element improving more pays for it. A
corridor going from 102% to 290% of its rating passed a four-clause non-regression test. The fix
is a **per-element clause over the elements present in both states**; no combination of
aggregates substitutes for it. Two sibling failures sit in the same family: an empty measurement
beats every aggregate, and a row that stopped being measured reads as cured. Read before
designing any acceptance criterion for a pruning, screening or remediation loop.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md)
  (the loop whose rounds this judges) ·
  [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) (the same
  "empty result reads as clean" rule for a ranking) ·
  [reading-violationctg](../methods/reading-violationctg.md) (the rows being compared) ·
  [violation-remediation](../demos/violation-remediation.md) (why one element can improve while
  another worsens)

## Content

### The measurement

A prune asks: *"if I remove this device, is the system no worse than with everything?"* The test
had four clauses, all sensible, evaluated per scenario:

```
count of elements over limit    <= reference
total exceedance (MW)           <= reference + tol
max loading m                   <= reference + tol
newly-crossed elements          == zero
```

It accepts this:

```
ref   : La m=1.02   Lb m=9.00   Lc m=4.00
trial : La m=2.90   Lb m=9.00   Lc m=1.10     -> ok=True
```

`La` nearly triples. Why every clause is satisfied:

- **count** unchanged, 3 → 3: all three were *already* over, so nothing crossed a threshold;
- **max(m)** unchanged: `Lb` at 9.0 is still the maximum, and it did not move;
- **total exceedance FALLS**: `Lc` drops 290 and `La` rises 188, a net improvement;
- **newly-crossed** is zero: `La` was already over, so it never *crossed* anything.

### Why this is structural, not a tuning problem

Each clause reduces the state to a **scalar or a set**. A scalar cannot express "this particular
element got worse"; a set membership test cannot either, once the element is already *in* the set.

The newly-crossed clause is the one that *looks* like per-element protection, and this is the
trap: **it guards only the boundary.** It protects an element at 0.99 from being pushed to 1.01.
It offers nothing at all to an element already at 1.02, which is precisely the population a
remediation loop is working on.

The fix is a fifth clause with a different shape:

```
per-element m, for elements over in BOTH states   <= reference + tol, ELEMENT BY ELEMENT
```

Give it the **same** tolerance as the `max(m)` clause. Two different slacks for the same physical
quantity is a second number to get wrong, and reviewers cannot tell which one governs.

### Two sibling failures in the same family

Both are the same species: *a reduction that loses the thing being judged*.

**An empty measurement dominates every aggregate.** If one scenario's trial table comes back
empty, its stats are all zero, which beats any reference on every clause. `"No rows"` is not
`"nothing wrong"`. A scenario *missing from the mapping* may already be handled; an empty *frame*
walks straight past that check. Refuse when the reference measured rows and the trial measured
none.

**Rows that vanish read as cured.** Set-differencing in one direction only (`trial − reference`,
for newly-crossed) means `reference − trial` is silently read as "fixed". But a row can disappear
because it *was no longer measured*: removing a parallel circuit deletes its contingency records,
so every row under that outage label vanishes, including rows on **other** elements that were
genuinely over. Those disappearances lower the count and the sum, **which then buys headroom for
a real regression elsewhere.** The two defects compound.

**Fixed and not-measured must never share an encoding.** Account for the labels a removal
deletes, explicitly, and refuse a trial whose row set is not a superset of the reference minus
that accounted set. Default the accounted set to **empty**, so an unwired caller gets the strict
answer rather than a permissive one.

### The precondition everyone forgets

The test this replaced was `over == 0`: zero elements above limit. The loop's own accepted end
state still had well over a hundred elements over, so the criterion was **unsatisfiable**. Every
probe returned False, the search fell through to a blame heuristic, and it discarded almost every
device it was meant to prune, none ever confirmed safe. Its summary showed the device count
collapsing to a few percent of the start, which **looks like a triumph**.

So: **assert that your test can return True on the state you are about to test**, as a dry-run
precondition, before the search starts. An unsatisfiable criterion does not error; it quietly
turns your search into whatever the fallback does.

### Checklist for a non-regression test

1. Is there a **per-element** clause, not only aggregates?
2. Does it protect elements **already** in violation, not just the threshold crossing?
3. Is it evaluated **per scenario / per case**, so one cannot pay for another?
4. At what **granularity** are rows keyed, and is it the same granularity the loop acts on? (A
   collapsed or argmax view hides every non-argmax row.)
5. Can an **empty** measurement pass it?
6. Can a **vanished** row read as cured?
7. Is it **satisfiable** on the real end state, asserted rather than assumed?
8. Is each clause **individually** necessary, so that deleting any one of them makes some bad
   case pass?
