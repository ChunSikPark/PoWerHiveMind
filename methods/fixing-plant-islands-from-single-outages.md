---
type: method
domain: synthetic-grid
topic: contingency
aliases: [plant-islanding-screen, islanding-screen, direct-345, resource-island-screen, single-outage-islands]
tags: [synthetic-grid, contingency, n-1, islanding, topology, gsu, remediation, powerworld]
---

# Method: Finding and fixing plant islands from single outages

## Abstract

A topology screen, independent of dispatch, that finds every single outage cutting a generating plant off the
grid, sorts the cut-off pockets into four shapes, and fixes the shapes that fail. It rests on one rule: a pocket
with units and load stays energized and fails to balance, while a pocket with units only goes dead.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md) (what a RESERVE LIMITS stop means) ·
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md) (the load-pocket sibling: one outage leaves a weak tie) ·
  [removing-empty-buses](removing-empty-buses.md) (cut-offs that strand nothing) · [gsu-outages-in-n1](../concepts/gsu-outages-in-n1.md) (the step-up outages this
  screen leaves to the generator-outage question) · [reading-violationctg](reading-violationctg.md) (`Contingency.LoadMW`, Island rows) ·
  [lodf](../concepts/lodf.md) (the same cut test from the PTDF side) · [agc-participation-factors](../concepts/agc-participation-factors.md) (who balances the main grid)

## Content

### The rule the screen rests on

When one outage cuts a pocket off the grid, what happens next depends on what the pocket holds:

| Pocket holds | What PowerWorld does | Shows up as |
|---|---|---|
| units only | the pocket goes dead; the plant trips | a solved outage, no row. The main grid must cover the lost MW |
| units and load | keeps it energized and balances it with the pocket's own units | unsolved at RESERVE LIMITS when they cannot ([diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md)) |
| load only | drops the load | a solved outage; `Contingency.LoadMW` > 0 ([reading-violationctg](reading-violationctg.md)) |
| nothing | nothing | nothing (an empty bus, or a 3W bank's own star and tertiary) |

A units-only pocket fails only when it holds the system slack, so give the slack two paths first (see
[gsu-outages-in-n1](../concepts/gsu-outages-in-n1.md)). Measured 2026-10-19/20 on a ~9k-bus synthetic case, five dispatches: **every pocket
that could not balance had load on the cut-off side**, and no pocket without load failed.

### The screen: topology only, every single outage

1. Build the graph of closed branches. A 3W bank is three windings meeting at its star bus, and its outage opens
   all three.
2. For each outage, remove its element and find what is cut off from the piece that holds the slack.
3. Label each cut-off piece by what it holds (table above). Drop a 3W bank's own dead star and tertiary before
   counting: they are cut off by the bank's own outage and strand nothing.
4. Keep the pieces with units ("resource islands"), and group outages that strand the same plant into one fix
   group, keyed by the substation that connects the plant to the grid.
5. Leave out the outage of a single step-up (GSU) feeding a single unit: that is a generator outage. A step-up
   feeding several units is also a generator-outage question ([gsu-outages-in-n1](../concepts/gsu-outages-in-n1.md)), so list those plants apart.

It needs no solve, so it runs in seconds and holds for every dispatch on the same network. Run the AC check only
on the candidates. On the case above, roughly one single outage in sixty stranded at least one unit, and grouping
by plant roughly halved the list.

**Re-derive it once before applying fixes.** An independent rebuild from the written spec matched the original
outage for outage (2026-10-20), and it caught three definitions that read wrong:
- A cut-off with no unit is not automatically "pure load". Some have no load either.
- "MW exposed" is ambiguous. The largest outage per substation counts a plant once; a sum over outages counts it
  once per outage that strands it. Say which one.
- "Failed" must include islanded load, not only unsolved outages. A pocket whose only unit is a battery at 0 MW
  is pure load in that dispatch, and the outage solves while quietly dropping a few MW. Read `Contingency.LoadMW`.

### The four shapes

Classify each fix group by the bus between the plant's step-ups and the grid (the "middle bus": a cut-off bus that
is not a unit terminal, star or tertiary). Shares are from the case above:

| Shape | Share of groups | Failed to balance | Fix |
|---|---|---|---|
| A: empty 138 kV middle bus behind one 345/138 transformer | ~2 in 5 | none (the plant just trips) | Direct 345, or accept the plant trip |
| B: the 138 kV middle bus carries load | ~1 in 5 | all of them | move the load to the GSU low side, then Direct 345 |
| C: plant on a bus fed by one line | ~1 in 4 | about a quarter: small battery or solar plus a few MW of load | second line or tie, measured |
| D: other shapes | ~1 in 6 | rare | its own design |

### Direct 345 (shape A)

Remove the empty 138 kV bus and its 345/138 transformer, and connect each plant step-up straight to the 345 kV bus:

- **Move each GSU's high side** to the 345 kV bus (PowerWorld `Move`, so the record keeps its rating, tap, lock and
  contingency element).
- **Keep the series impedance:** new GSU impedance = GSU + removed transformer / w, where w is that GSU's share of the
  plant's total GSU MVA. With several GSUs, the added parts in parallel sum back to exactly the removed transformer.
  For a 3W bank, add its high and 138 kV windings and ignore an idle tertiary.
- **Keep the GSU tap.** Do not multiply it by the removed transformer's tap. That tap was mostly an LTC position
  holding the removed bus, and the two transformers face opposite ways, so the product is not the series ratio.
- **Regulation:** units that held the removed bus now hold the 345 kV bus at the case's 345 kV setpoint rule. If
  another plant already holds that bus at a different setpoint, keep that setpoint: two regulators on one bus must
  agree.
- **Contingencies:** delete the removed transformer's outage and relabel the moved GSUs' outages to their new ends.

Measured on the case above, at the 345 kV setpoint rule: the largest base-case voltage rise was about 0.02 pu, no
bus went above 1.05 pu, and every Direct 345 group passed in all five dispatches.

### Middle bus with load (shape B)

Here the 138 kV middle bus holds the step-ups, one small load and the 345/138 transformer, and nothing else. Move
the load to the low-voltage side of the largest unit's GSU (same MW, Mvar, ID, status and zone), then apply Direct
345. The transformer outage that islanded the pocket no longer exists. Each moved GSU's outage now trips a unit and
its load together, which solves. **Moving load needs the case owner's go-ahead.**

Checked on the case above (2026-10-20): total load unchanged to 0.000 MW, every outage within two substation hops
of a change solved before and after, and no new or worse violation in any dispatch.

### Line-fed and other shapes (C, D)

Measure options rather than reasoning about them: a second transformer, a tie line to a nearby substation, a second
circuit, a second jumper. **Pass** means the group's outage solves in every dispatch and nothing new appears: no new
or worse violation, no newly unsolved outage, nothing new in the base case. On the case above, about nine options in
ten passed in all five dispatches. Accept a plant-only trip as a generator loss; it is not an islanding defect.

### Re-screen after any AGC or dispatch change

Pass and fail depend on who can balance a pocket. Batteries on AGC balanced several small battery pockets; after
batteries were taken off AGC (no state of charge, see [agc-participation-factors](../concepts/agc-participation-factors.md)), those pockets failed again.
Re-run the AC check on every candidate whenever the AGC set or the dispatch changes.
