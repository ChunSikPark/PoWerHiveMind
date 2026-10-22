---
type: concept
domain: synthetic-grid
topic: contingency
aliases: [voltage-pocket, pocket-siting, one-capacitor-per-pocket, grouping-undervoltage-by-driver,
  where-to-put-the-capacitor, post-contingency-undervoltage-siting]
tags: [synthetic-grid, voltage, contingency, n-1, remediation, siting, powerworld, shunt]
---

# One device per voltage pocket

## Abstract

Post-contingency undervoltage clusters by **driving outage**, not by bus. Buses that fail
together under one outage are **one problem with one fix**, so the unit of remediation is the
pocket, not the violated bus. A worklist that ranks buses cannot see this, because the
structure lives in a column it does not group on. Measured 2026-09-14 on a ~9k-bus synthetic
planning model: the undervoltage buses resolved to fewer than half as many driving outages, and
the multi-bus pockets among them covered about 85% of the buses. One modest capacitor at the worst
bus of the largest pocket cleared **all seven of its buses**, created zero new violations anywhere
across the full contingency set, and left the thermal side untouched.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md)
  (the loop this belongs to) ·
  [remediating-base-case-violations](../methods/remediating-base-case-violations.md) (the N-0
  ladder, which sites one device at the worst bus for the same reason) ·
  [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) ·
  [reading-violationctg](../methods/reading-violationctg.md) (the `CTGLabel` column to group on)
- **Traps it depends on:**
  [sizing-a-device-whose-impedance-determines-its-own-flow](sizing-a-device-whose-impedance-determines-its-own-flow.md)
  (a shunt is the second form of that trap) · [adding-devices-esapp](../methods/adding-devices-esapp.md)

## Content

### The structure, and why a ranked list hides it

A per-element worklist sorts violated buses by severity. That ordering is correct and useless
for siting: the buses of one pocket scatter through it by depth, so the list presents a dozen
separate problems where the network has one. The grouping key is the **driving contingency**,
which the violation rows already carry.

Grouped that way, a handful of outages cause most of the undervoltage, and the long tail is
singletons.

| pocket size | outages | buses covered |
|---|---|---|
| 2+ buses | roughly half the outages | **~85% of the violated buses** |
| 1 bus | the rest | the remainder |

**Most multi-bus pockets are single-transformer-fed.** That is why they behave as units: one
element is the only path in, and losing it strands everything behind it together. A severity
ranking has no way to represent that topology.

### Why one device fixes the whole pocket

Every bus in a pocket is healthy intact and fails only post-outage, and they fail *together*
because they share the constraint. Reactive support injected anywhere inside the pocket holds
the whole pocket up. Siting per violated bus buys one device for each symptom of a single cause.

Measured on the largest pocket: one capacitor of ordinary size at its worst bus took all seven
buses, spanning three voltage levels including two generator step-ups, back inside band, and
introduced nothing new across the full contingency set.

**Site at the worst bus in the pocket**, and verify against the whole set rather than the one
outage the walk used: the device changes the case for every contingency, not only the one it
was sized against.

### The sizing trap, in its shunt form

A shunt's output goes with the **square of the voltage it is sizing itself against**. Measured on
an existing fleet, actual-over-nominal equals V² to four figures. That has two opposite
consequences:

- **It is weakest exactly where it is needed most.** At a collapsed bus the device delivers
  substantially less than nameplate: measured here at ~61% while the bus sat deep below limit.
  Sizing from a linear intuition under-buys.
- **It is strongest once it has worked.** The same device delivers *above* nameplate once the
  bus recovers. Measured: the repaired bus became the **case maximum** intact voltage, rising by
  ~0.05 pu. That was comfortably inside the emergency band but would sit at the edge of a
  narrower normal band.

So the walk must **re-solve at every step and accept the measurement**. Extrapolating a size from
one step's `dV` is the trap in
[sizing-a-device-whose-impedance-determines-its-own-flow](sizing-a-device-whose-impedance-determines-its-own-flow.md)
again. The acceptance test has two halves: the target back inside band **and** nothing pushed
out that was inside before. A device that rescues its own pocket while
overvolting a neighbour is not a fix.

### When the pocket is telling you something else

A pocket that collapses by a large margin (a fifth of a per-unit or more) on the loss of a
single element is describing a **connectivity** problem, not a voltage-support one. Reactive
support may still hold it, and holding it may be the right economic answer, but record that
one element is the only path in
([finding-and-fixing-radial-by-n1-pockets](../methods/finding-and-fixing-radial-by-n1-pockets.md)).

**Both facts belong in the output**: the device that holds it, and the redundancy that is
missing. A study that reports only the capacitor has answered the question and hidden the
problem.
