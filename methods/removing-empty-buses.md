---
type: method
domain: synthetic-grid
topic: case-audit
aliases: [removing-empty-buses, empty-bus-cleanup, dead-end-bus-removal, blank-bus-removal,
  delete-dead-buses, inflated-islanding-count]
tags: [synthetic-grid, powerworld, esapp, topology, cleanup, transformer, islanding, contingency]
---

# Method: Removing empty buses from a case

## Abstract

How to find and delete voltage levels that carry nothing (no load, no running plant, no shunt, no
line out of the substation) and hang off one transformer, without changing the power flow. Use it
when islanding or N-1 counts are inflated by outages that only cut off dead buses. Measured
2026-10-04 on a ~9k-bus synthetic case: about one in eighty substation voltage levels qualified,
and deleting them moved no voltage or flow at all. The two shapes that look empty and must stay
are a pass-through bus in a transformer chain and a winding of a three-winding bank.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  (the islanding screen whose zero-MW rows these buses fill) ·
  [reading-violationctg](reading-violationctg.md) (islanding does not show as a violation) ·
  [ltc-regulation-checks](ltc-regulation-checks.md) (why a tap changer on a deleted transformer
  matters) · [case-data-lint](case-data-lint.md) (other data defects a case solves through)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md) ·
  [save-powerworld-case](save-powerworld-case.md)

## Content

### What counts as empty

Work per **substation voltage level**: every network bus of one nominal kV in one substation. Fold
step-up (GSU), three-winding star and tertiary buses into the network bus they feed, so a plant
behind its own step-up counts on the bus it feeds. A level is a delete candidate only if **all** of
these hold in **every** dispatch:

1. no load record, no shunt, and no unit producing MW **or Mvar**. A unit switched on at 0 MW but
   holding voltage with Mvar is not empty, and a screen that checks MW alone misses it;
2. no line leaving the substation at that voltage;
3. one outage of its transformer cuts it off, so it is a dead end and not a pass-through;
4. nothing that stays regulates a bus on it, and deleting it removes no tap changer that regulates
   a bus that stays.

Units that never run in any dispatch do not make a level non-empty. They go with the bus, so list
them.

### Two shapes that look empty and must stay

- **Pass-through.** An empty middle bus in a 345 → 138 → 69 kV chain carries the 69 kV network's
  supply through two transformers. No single outage strands it, so rule 3 catches it. On the
  measured case these carried from a few MW to a couple of hundred MW, and deleting one dropped a
  nearby 69 kV bus below 0.94 pu.
- **Three-winding banks.** An empty bus on one winding of a three-winding transformer cannot be
  cut off alone. Rebuild the bank as a two-winding unit first, or leave it.

The tap-changer rule looks like it blocks an empty 345 kV stub whose 345/138 transformer is set to
hold the 138 kV side. Measure before obeying it: with no current through the transformer the tap
sits at 1.000 and holds nothing. Deleting a couple of dozen such stubs moved voltages by at most
0.0002 pu.

### Delete and verify

1. Delete the whole piece the transformer outage cuts off: the bus, its GSU and star or tertiary
   buses, the transformer, the idle units, and **every contingency whose element was deleted**.
2. Re-check that contingencies = contingency elements = lines + two-winding + three-winding ÷ 3.
3. Solve warm and from a flat start. Compare every remaining bus voltage and branch flow against
   the original, and compare flat start against the **original's** flat start, because a flat
   start can land a few MW away from the saved solution on its own.
4. Gate on no new N-0 violation, then save to a temp name, rename, and cold-reopen
   ([save-powerworld-case](save-powerworld-case.md)).

The transformers removed carried exactly 0 MW and 0 Mvar, so the result was zero change in all
five dispatches, and the full N-1 afterwards matched the earlier one label for label.

### PowerWorld traps met on the way

- **Deleting a three-winding transformer needs `BusIdentifier` as its key.** Keyed on the three bus
  numbers, the delete is refused as not adequately defining the object.
- **Loads, units, shunts, branches and substations each carry their own area and zone**, separate
  from their bus. Moving buses alone leaves every device behind.
- **A blank write to the case's one-line link is ignored.** To clear it, rebuild from a copy that
  never had it.
- **SimAuto cannot create a new one-line.** `LoadAXD` into a new diagram fails with "No MDI forms
  are currently active". Draw the diagram in the GUI.
