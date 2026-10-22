---
type: method
domain: synthetic-grid
topic: contingency
aliases: [radial-by-n1, radial-by-n-1-pockets, weak-pocket-screen, siting-a-second-tie]
tags: [synthetic-grid, contingency, n-1, voltage, topology, remediation, powerworld]
---

# Method: Finding and fixing radial-by-N-1 pockets

## Abstract

A pocket is **radial-by-N-1** when it reaches the bulk grid through two ties and one outage
leaves it on a long, weak survivor. Nothing islands, yet the pocket collapses. This page gives
a whole-case screen that finds them, the siting rules for the new tie (where it must land, and
which ties look useful but do not help), and the in-memory harness that measures candidates.
It also covers the extreme case, a **radial tree** that one outage islands outright, with a
whole-grid bridge screen, tie rules per tree shape, and why shared tree-to-tree ties mostly fail.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [violation-remediation](../demos/violation-remediation.md) (the
  diagnose-then-test loop this complements) · [lodf](../concepts/lodf.md) (the islanding
  screen this one extends past) ·
  [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md) (why a radial
  EHV tree also runs high, and what a tie does to it) ·
  [violation-network-map](violation-network-map.md) (the radial-ties map page draws the bridge
  screen below) · [reading-violationctg](reading-violationctg.md) (getting PowerWorld's own
  islanding result)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md)

## Content

### The shape

Two shapes showed up, both measured 2026-09-23 on a synthetic ~9k-bus planning model:
- **A large load tap with one real 138 kV feed.** Its "second path" is a step-down to 69 kV that
  cannot carry the load. It passes a screen for "radial at its own voltage level" because a
  second path exists, at the wrong voltage.
- **A string of substations fed from both ends.** Any link of the string, or either end feed,
  leaves part of the string hanging from the other end. One pocket has several failing outages,
  so site one fix, not one per outage.

In both, the reactance from the collapsing bus to the 345 kV+ grid rose roughly x2.5–x14 when the
outage opened, and a capacitor could not save it. A bus heading to 0.2–0.5 pu gets a few
percent of a shunt's nameplate, so a shunt is the wrong instrument here.

### Screen: find them in the whole case, linearly

1. **Ground = buses on the >= 300 kV *line* network.** Not every >= 300 kV bus: a stub 345 kV bus
   (the high side of a step-up, with no 345 kV line out) can sit *inside* a pocket, and
   grounding it makes the whole pocket look stiff. Local generator buses are not ground either:
   the units near failing pockets were at their limits during the collapse.
2. `B` = the X-only Laplacian of closed branches over the non-ground buses; factorise once.
   `Z_kk` from `B^-1` is each bus's Thevenin reactance to the EHV grid.
3. Opening branch `(i, j, x)` is a rank-1 change. With `w = Z e_ij` and `d = x - (w_i - w_j)`:
   `Z'_kk = Z_kk + w_k^2 / d` for every bus at once (`d -> 0` means the outage islands).
4. A bus is **stranded** when `Z'_kk >= 1.8 x Z_kk` and `Z'_kk >= 0.15` pu. Stress index
   **SI = (pocket |S_load| + pocket zero-Q generation MW) x max Z'_kk** (pu, 100 MVA base).
   Count zero-Q generation: its MW rides the surviving path just like load, and it brings no
   voltage support. A radial reactance `X` delivers ~`V^2/2X` at unity power factor, so SI of a
   few tenths is already near a nose.
5. Rank, then **AC-check the top of the list** in every dispatch (`CTGApply` + one solve).

Validation, same model: the screen ranked **every** known failing outage in its top 13 of ~900
flagged. Its first two versions missed most of them (one by grounding stub 345 kV buses, one
by a 2.5x gate that a failing tap sat just below), so check a screen against known failures
before trusting its silence. The AC check of the next 40 flags found **no new divergence** and a
short watchlist at 0.90–0.93 pu. The screen ranks margin; it does not predict failure alone.

### Siting the fix

- **A tie back into the pocket does not help the end-feed outage.** For a string whose only
  source sits at one end with zero reactive capability, a tie into the middle of the string
  fixed every outage *along* the string but not the loss of the end feed. That one needed a
  second way **out of the source's bus to a substation outside the pocket**. Two lines, one
  mid-string and one exit at the injection, closed all of them. Giving the zero-Q unit ±0.95 pf
  capability alone fixed only half: a pocket with generation can still collapse when that
  generation is modelled with no reactive capability.
- **Land on the meshed grid, never on another load pocket.** Candidate landings: a 138 kV
  substation outside the pocket that stays in the main grid with the pocket removed, with >= 2
  ties, not itself a large-load or data-center tap.
- **Check what the landing depends on.** A landing whose strong tie runs to the same substation
  as the pocket's existing feed passes every *branch* outage and fails the single-substation
  test. Read the landing's own ties before choosing it.
- **Search geography, not the hop extract.** A good landing can be close as the crow flies and
  7–11 substation-hops away through the network; a neighbourhood built by hop count misses it.
  Delaunay 1–3 neighbours over every substation, within a reach cap.
- **Rate the template to clear the load**, then pick by length. A new tie's impedance decides
  its own flow, and it can carry most of the load even intact: measured up to ~94 % on one where
  the old feed was twice as long.

### Islanding trees: the whole-grid bridge screen

When one outage **islands** a pocket instead of weakening it, the screen is pure topology and needs
no solve:

1. Build the **substation** graph from in-service inter-substation branches, keeping parallel
   circuits as separate edges so a double circuit is never a bridge. Put 3-winding star buses in the
   substation their windings reach, since they carry no substation of their own.
2. Find the **bridges** (Tarjan, iterative; the graph is too deep for recursion). The largest
   2-edge-connected piece is the **meshed core**.
3. Root the bridge tree at the core. Each bridge hangs a **pocket** (everything on the far side),
   and nested bridges along one branch group under the tree's **attachment** bridge. Tag each tree by
   the attachment bridge's kV and total the load and generation it strands (worst dispatch).

This screen leaves out two things on purpose, both better handled elsewhere:
- **Transformer-only islanding inside a substation** (a generator step-up, a load hung on its own
  split bus behind one short line). The split-bus load is a modelling convention on many synthetic
  cases, touches nearly every load, and is treated here by convention as **consequential load loss**
  instead of a violation. The fix for an internal split bus is a second bus tie, not a line.
- **Radial 69 kV taps**, which are ordinary sub-transmission design.

**Check it against PowerWorld's own islanding result before trusting its silence.** Measured
2026-09-28 on a synthetic ~9k-bus planning model: the screen listed every between-substation
islanding outage at 138 kV and above that a full N-1 with islanding reporting found, and missed none.
How to get that N-1 result is on [reading-violationctg](reading-violationctg.md); the island option
alone reports nothing.

**What it found there**, as shapes rather than counts: a few percent of substations sit in radial
trees; at 345 kV the stranded MW is almost all **generation on a single line**, at 138 kV mostly
**load taps**. So the islanding problem at EHV is a plant-connection problem.

### Siting a tie for an islanding tree

The radial-pocket rules above still hold: land on the meshed core, never on another pocket, and check
what the landing depends on. The tree shape adds four:

- **A chain takes one tie, from its far end.** A tie from the dead end back to the core makes every
  bridge on the way a loop. Do not start it at the plant just because the plant is there.
- **Start at the plant only when the plant's path to the far end is weaker than the plant.** On two
  345 kV plant trees whose substations were joined by a **138 kV** line, the far-end tie pushed the
  plant through that line at **1.4–2.0x its rating** when the plant's own exit opened. Tie from the
  plant instead, and then the far end, on the other side of the plant, needs **its own** tie.
- **A branching tree needs a tie per branch.** A hub with two spokes and one exit cannot be closed by
  one line; the leftover spoke islands whatever else is built.
- **Spread the landings.** Two ties from one tree into the same substation, or a new tie onto a
  substation that already feeds another tree, stacks several plants behind one station: it passes
  every single-branch outage and fails the substation outage. It also concentrates new line charging
  where a light-load region may already sit high (see
  [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md)). Prefer a landing
  that shares nothing with the tree's existing feed.

A tie is a same-voltage line between two existing buses with no transformer, so the source and the
landing must both already have a network bus at the tree's kV.

### Fewer lines: shared ties, and why most fail

Pairing dead ends is the textbook way to use fewer lines: one line between the ends of two trees
that hang off **different** core substations gives each the other's feed as its second path, so the
minimum is about half the number of dead ends (2-edge-connectivity augmentation). On topology alone,
with pairs limited to 40 mi, that cut the line count by about a third.

**The AC check takes most of it back.** Measured 2026-09-28, same model, five dispatches: about one in
five topology-chosen shared lines failed, two ways.

- **The partner's bridge carries both plants.** With tree A's exit open, A's output leaves through
  B's single bridge on top of B's own — measured up to **2.4x** rating.
- **The middle of a chain stays radial.** Joining the *ends* of two chains leaves the substations
  between each end and its feed still hanging on one line.

Built only from lines that passed all five dispatches on their own, the shared-tie portfolio used
about **20% fewer lines than one tie per tree for about 4% more miles**, every tree closed. The best
shared ties join two generation trees a short distance apart whose feeds are strong. **Measure the
portfolio's lines one at a time before believing its count.** The greedy that picks them cannot see
flow.

### Measuring candidates in memory

Build each candidate as a template same-kV line (R/X/B scaled by miles, rating copied) in the
open case ([adding-devices-esapp](adding-devices-esapp.md)), solve N-0, apply each target outage
the way the sweep does (`CTGApply` + one solve from the intact solution), and read convergence, the
lowest pocket voltage and the worst pocket loading. Then undo and **fingerprint** (closed-branch
count + a pocket voltage) before the next candidate. Undoing a cloned transformer by opening it
failed to restore the case once, and only the fingerprint caught it. Pass = converges, pocket >=
0.90 pu, nothing over Rate A, in every dispatch. Confirm the winner with PowerWorld's own
`CTGSolve` on the label, then a full N-1 with the new lines' own contingency records.
