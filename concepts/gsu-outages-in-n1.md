---
type: concept
domain: synthetic-grid
topic: contingency
aliases: [gsu-outages-in-n1, gsu-contingencies, double-gsu, twin-gsu, parallel-gsu, generator-step-up-outage]
tags: [synthetic-grid, contingency, n-1, gsu, transformer, voltage]
---

# GSU outages in a transmission N-1: double every step-up, or leave them out

## Abstract

Two ways to treat generator step-up (GSU) outages in a transmission N-1 list: give every single GSU an identical
twin and keep all GSU outages, or leave GSU outages out. Measured on one case, both fail on the same transmission
outages. Twins cost base-case high voltage and a point or two of loading; leaving them out never tests a GSU outage.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [fixing-plant-islands-from-single-outages](../methods/fixing-plant-islands-from-single-outages.md) (the topology screen that sets GSU outages aside) ·
  [gsu-tap-vs-generator-voltage-control](gsu-tap-vs-generator-voltage-control.md) (why twins get a fixed tap) ·
  [agc-participation-factors](agc-participation-factors.md) (who covers a tripped unit's MW) ·
  [remediating-n1-contingency-violations](../methods/remediating-n1-contingency-violations.md) (the loop both variants feed)

## Content

### The question

An auto-inserted N-1 list holds every branch, and the step-up between a unit and the grid is a branch. Losing a
single GSU strands its unit, so its outage is really a **generator outage**, which NERC TPL-001 counts as a single
contingency (P1) of its own. The two clean options:

| | A: double every single GSU | B: leave GSU outages out |
|---|---|---|
| Network | +1 twin per single-GSU plant: identical R, X, B, ratings, MVA base, a fixed tap equal to the original's, automatic tap control off | unchanged |
| Contingency list | every GSU outage kept, plus one per twin | GSU outages deleted |
| What a GSU outage tests | that the twin carries the plant alone | nothing; add a separate one-per-unit generator-outage set |

### Measured: both fail on the same transmission outages

Full AC N-1, five dispatches, on a ~9k-bus synthetic case, both variants built from one shared base
(2026-10-20). Same settings in both: Rate A and 0.94–1.05 pu before an outage, Rate B and 0.90–1.10 pu after,
Gen Part Factors make-up, island handling on.

- **The same failing outages, in the same dispatches.** The list of outages with a real violation or no solve was
  identical in both. Every unsolved outage in either was an island at RESERVE LIMITS; none diverged.
- **Variant A's GSU outages were all non-events.** Original and twin outages solved in every dispatch, stranded no
  unit and raised no network violation.
- **Twins cost voltage.** Halving each GSU's impedance lets a unit hold its regulated high side with less Mvar, so
  fewer units sit at Qmax, more sit at Qmin, and the base-case high-voltage count rose by about a third (bus-dispatch
  pairs above 1.05 pu summed over five dispatches; worst bus +0.003 pu).
- **Twins add a point or two of loading** on the worst post-outage branches, and the worst post-outage high voltage
  rose by up to 0.007 pu.
- **Variant B never tests a GSU outage.** On an earlier build of the same case, GSU outages tripped units that left
  the main grid short of AGC headroom, and one islanded a pocket. That was not re-measured on this base.
- **Size:** A adds roughly one branch in eleven and about a fifth more outages per dispatch.

### Build either one by script from a shared base

Every network fix goes on one shared base, and A and B are rebuilt from it by script, so the choice can change at
any time. A twin is made with `CreateData` from the original's fields (no `ObjectID` carried), in batches with a
warm solve after each, plus a new contingency per twin in the case's label format. Read every twin back on a cold
reopen: present, a transformer, and no GSU bus pair left with one unit. Each GSU then carries half its plant, and
the slack's output drops slightly because GSU losses halve.

### Two cases to handle whatever the choice

- **The slack must not sit behind one GSU.** If it does, that GSU's outage leaves the slack alone in an island in
  every dispatch. Twin the slack's GSU in both variants. Moving the slack instead only works onto a unit with room
  both up and down in every dispatch.
- **Several units behind one GSU.** Its outage trips them all together, which is a multi-unit generator loss.
  Screen those plants separately; [fixing-plant-islands-from-single-outages](../methods/fixing-plant-islands-from-single-outages.md) lists them apart.

### Which to pick

The measurement does not settle it. Either way: add a one-per-unit generator-outage set, since P1 includes single generator
loss and variant B otherwise tests none.
