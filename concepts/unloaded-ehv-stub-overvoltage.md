---
type: concept
domain: cross-cutting
topic: design
aliases: [unloaded-ehv-stub-overvoltage, floating-stub, ehv-stub-overvoltage, ferranti-rise,
  dead-end-ehv-overvoltage, line-charging-overvoltage, radial-ehv-line, open-end-rise]
tags: [powerworld, voltage, overvoltage, reactive-power, line-charging, topology, radial,
  islanding, case-quality, n-0]
---

# An unloaded EHV stub runs high, and only closing it fixes both of its problems

## Abstract

An extra-high-voltage (EHV) line that runs out to a dead end and carries almost no MW behaves like
an open-ended capacitor. Its own charging lifts the far end above the near end (the Ferranti
rise). If nothing at the far end can absorb Mvar, for example because the only unit there is
modelled with zero reactive range, the far end runs high in exactly the light-load dispatches
where the unit is off. The same topology also islands on the loss of its one link. Measured
2026-09-28 on a regional planning model: a tie closing the stub into a substation that still had
absorbing room fixed both problems. A reactor fixed only the voltage. A long tie to a substation
whose reactor was already at full output fixed neither.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [ltc-regulation-checks](../methods/ltc-regulation-checks.md) (the other intact-case
  overvoltage, which an LTC can reach) ·
  [violation-network-map](../methods/violation-network-map.md) (the radial-ties page finds the
  bridges and radial trees this shape sits on, and the voltage page shows the reactive balance
  around it) · [case-impedance-completeness](case-impedance-completeness.md) (a case with
  `LineC = 0` has no charging, so this rise cannot appear there; check that first) ·
  [adding-devices-esapp](../methods/adding-devices-esapp.md) (placing the reactor or tie once
  chosen)
- **Checked by:** the case-auditor's `base.floating_stub` rule

## Content

### The shape

One or two EHV substations hang off the meshed grid on a single line a few tens of miles long.
The only device at the far end is a solar or storage plant modelled with zero reactive range
(`GenMVRMax = GenMVRMin = 0`). When that plant is off (winter peak, spring minimum, a light-load
night) the line carries almost no MW. Its charging, `LineC` in per unit on the system base,
split half to each end, has nowhere to go, so the far end rises above the near end.

Measured 2026-09-28 on a regional planning model, intact case, five dispatches:

| dispatch | far-end voltage |
|---|---|
| plant off, line nearly unloaded | **1.06 – 1.08 pu** |
| plant running, current through the line | 1.02 – 1.03 pu |

The loss of either link islands the plant. An outage that islands a bus often solves with no
violations reported, because the stranded buses are dropped rather than flagged. So the
islanding half of this problem needs its own screen.

### Why the obvious levers do not reach it

- **Generator setpoints.** Walking every unit within six hops down by up to 0.05 pu cleared small
  overshoots elsewhere but left the stub above 1.05. Every unit near it was already pinned at
  its absorbing limit (`GenMVR = GenMVRMin`). The one unit with room was injecting: it
  regulated a 138 kV bus that sat below its setpoint while the 345 kV side floated high. A
  setpoint on a pinned unit moves nothing.
- **Shunt deadbands.** Lowering the switched-shunt bands (`SSVHigh`, `SSVLow`) by 0.02 pu across
  the area changed nothing measurable. The nearby reactors were already at full absorption
  (`SSNMVR = SSMinMVR`), and the capacitors nearby were holding up load taps.
- **A long tie to the biggest reactive substation.** A tie several tens of miles long to a
  substation with a large reactor did not clear it. The new line's own charging cancelled the benefit, and that
  reactor was already at full output. **Capability is not room.** Rank landing points by what
  they can still absorb, not by what they own.
- **A 138 kV tie** from the stub made it worse, by up to 0.005 pu. It adds a path and nothing
  that absorbs, and it relieves none of the 345 kV charging.

### What fixed it

An **EHV tie a few tens of miles long from the dead end into a nearby substation whose unit still
had absorbing room** brought the stub to 1.03–1.05 pu in all five dispatches and removed both
islanding outages. It works because it turns the stub into a loop through a substation that can
take the stub's surplus Mvar. A tie landing on the middle of the stub fixed the voltage but left
the far end on one line.

For comparison:

| design | voltage | islanding |
|---|---|---|
| EHV tie from the far end to a substation with room | fixed | fixed |
| a reactor of order 100 Mvar at the stub | fixed except one dispatch, barely over | not fixed |
| a two-way bank of similar size at the stub | same as the reactor while out of band; idle once back in | not fixed |
| long tie to a substation whose reactor was pinned | not fixed | not fixed |
| 138 kV tie | worse | not measured |

Neither the reactor nor the bank is wrong. The tie is the only single device that answers both
problems.

### The same physics at regional scale

Many short EHV ties in one region raise it even when no single tie does. Measured on the same
model with discrete controls frozen: closing on the order of ten radial trees in one light-load region
pushed tens more buses over 1.05 in one dispatch. Removing any one of those ties moved
the worst bus by under 0.001 pu. The rise is the sum of their charging. Check a batch of ties
as a set, in the lightest dispatch, not one at a time. Where a region already runs near the
limit, site absorbing capacity along with the ties.

### What the auditor can and cannot tell from one case

The shape is structural: a radial EHV line whose far side has no absorbing room. The rise is
dispatch-dependent. A case solved with the far-end plant running can sit comfortably in band,
yet the same case at light load sits above it. So a clean voltage on this shape in the case
you have does not mean the shape is safe. Check the lightest dispatch you study. Whether to
close the stub, add a reactor or accept it is a planning choice the case cannot make for you.

### How the case-auditor finds it

The `case-audit` engine's `base.floating_stub` rule (`skills/case-audit/engine/rules_stub.py`)
works on the solved case, read-only:

1. **Structure.** Over the connected buses and closed branches (parallel circuits are separate
   edges, so a double circuit is never a bridge), find the bridges. The meshed core is the largest
   2-edge-connected piece; each bridge's far side is the part away from it. A candidate is a bridge
   that is a line, with both terminals at EHV, whose far side is small. Along one radial chain only
   the bridge nearest the core is reported.
2. **Lightly loaded.** The bridge's `LineMaxPercent` is low, or, on an unrated bridge
   (`LineAMVA = 0`), its `|LineMW|` is.
3. **Rising.** The highest far-side EHV bus sits above the bridge's core-side end, and there is
   line charging to rise on (`LineC` summed over the far side and the bridge is above 0; a case
   with `LineC = 0` everywhere is a DC skeleton, which `base.dc_skeleton` reports instead).

Each finding carries the bridge's keys, the near and far voltages, whether the far end is above
its own high limit, the bridge's MW and loading, the far-side bus count, the charging in Mvar
(`sum(LineC) × Sim_Solution_Options.SBase`; `SBase` read 100 on both public cases probed
2026-09-30, and the engine reads it from each case rather than assuming it), the **absorbing
room** left on the far side (`GenMVR − GenMVRMin` over closed units plus `SSNMVR − SSMinMVR` over
closed shunts - room, not capability), and the far-side units with zero reactive range.

Numbers with no source, each a proposed default in `skills/case-audit/engine/thresholds.py`:
EHV means 300 kV and above (catches 345, 500 and 765, excludes 230); a far side of at most 50
buses; lightly loaded means under 10 % of rating, or under 10 MW when unrated; a rise of at least
0.005 pu. The rise is dispatch-dependent, so a stub that is in band on this dispatch is not
reported; a structure-only warning for it is not built. On Texas2k (182 buses at 500 kV) the rule
found none.
