---
type: concept
domain: cross-cutting
topic: design
aliases: [circular-sizing, self-fulfilling-under-sizing, size-against-converged-flow-trap,
  impedance-flow-feedback, transformer-sizing, how-big-a-transformer]
tags: [sizing, impedance, power-flow, transformers, gotcha, technique, feedback-loop, design]
---

# Sizing a device whose impedance determines its own flow

## Abstract

"Size it against the flow it actually carries" is the correct rule for a **line** and a
silently wrong one for a **transformer**. The difference is whether the device's impedance
moves with its rating. A transformer's does: `x_pu` is quoted on its *own* MVA base, so
`x_sys = x_pu · S_base / MVA` and a small nameplate **is** a high impedance. Flow routes
around the small unit, the converged flow comes back small, and the sizing rule confirms the
unit should stay small. The loop closes on itself and the answer looks converged. A
conductor's impedance barely moves with its rating, so a line has no such loop.

The failure is invisible in the device's own numbers (the under-sized unit reports *low*
loading, not high) and surfaces somewhere else entirely, as an overload on whatever path
picked up the flow it declined. Break it with a floor derived from something the device
cannot influence: the load it is obliged to serve.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [per-unit-basis-discipline](per-unit-basis-discipline.md) (why `x_pu` on its own
  base is the mechanism) ·
  [one-device-per-voltage-pocket](one-device-per-voltage-pocket.md) (a shunt's output varies with
  the voltage it is sizing itself against: the same shape) ·
  [remediating-base-case-violations](../methods/remediating-base-case-violations.md) (why a
  device walk-up must re-solve at every step) ·
  [reviewing-a-design](../methods/reviewing-a-design.md) (where an under-sized unit shows up in a
  review)
- **Used in:** [finding-and-fixing-radial-by-n1-pockets](../methods/finding-and-fixing-radial-by-n1-pockets.md)
  (a new tie's impedance decides its own flow)

## Content

### The shape of the trap

A device is **self-referential for sizing** when its rating changes its impedance, and its
impedance changes the flow you are sizing it against:

```
rating ↓  →  impedance ↑  →  flow routes elsewhere  →  measured flow ↓  →  rating ↓
```

Any fixed point of that loop is self-consistent, so nothing in the convergence test fires.
The loop does not oscillate or diverge; it settles quietly on a wrong answer.

Test for it before choosing a sizing basis: **does the quantity I am sizing against depend on
the size I choose?** For a line, no in any practical degree. For a transformer, a phase
shifter, an HVDC link, a series reactor, a switched shunt: yes.

### The measured case

Measured 2026-08-22 on a ~9k-bus synthetic planning model: a few dozen substations where a 69 kV
corridor was re-terminated at 138 kV and needed a new 138/69 kV transformer back to the original
bus. Three sizing rules were tried:

| basis | result |
|---|---|
| corridor need (pre-move flow ÷ 0.8) | **R² = 0.110** against real flow. Uncorrelated, not biased. About one unit in six over nameplate, worst **139.2%** |
| converged flow alone | **about a third of the units below the load on their own low-side bus**, worst **4.8×** |
| `max(converged flow, own-bus load)` | **none** over nameplate, worst **79.1%** |

The middle row is the trap: a *better-targeted* rule than the first, and it produced a
**worse** grid. One substation finished with a **30 MVA** transformer
against roughly five times that in load on its own bus, carrying under a fifth of its own rating.
The rest of the load arrived across the 69 kV network from neighbouring substations: the
low-voltage system quietly acting as a distribution bus to backfill under-sized station
transformers.

Nothing in the transformer's own report looked wrong. It read 19% loaded. The symptom appeared
two buses away, on a 69 kV line whose flow rose more than fifteen-fold to 105.2% of a rating
already at its class ceiling, which no conductor can raise. Chasing that line (a parallel circuit,
a voltage upgrade) would have treated the symptom and left fifteen more under-sized units waiting
to produce the next one.

The first rule was also wrong, but *conservatively* wrong: its 150 MVA floor accidentally
masked the circularity. Removing a bad rule can expose a worse one that the bad rule was
hiding, so the improvement and the regression are both real.

### The fix: floor it with something the device cannot influence

```
need = max( converged flow , load the device is obliged to serve ) / (1 − headroom)
```

The load behind a station transformer's low-side bus is **static input data**. The device's
impedance cannot change it, so it cannot take part in the loop. Converged flow still governs
any unit with genuine transit duty; the floor is a lower bound, not a target.

The general form: **find a quantity downstream of the device's obligation, not of its
behaviour**, and floor the sizing with it.

### Four details that each cost a full run

1. **Share the floor across parallel devices** on the same bus (`load / n`). Giving each the
   whole load builds the substation twice (measured 2 × 500 MVA against a 600 MVA need), and
   paralleling two over-sized units halves the impedance again, re-creating the redistribution
   the fix exists to remove.
2. **Decide exhaustion against the catalogue, not against `need`.** A device that cannot be made
   big enough must still be made *as big as the catalogue allows*, then reported. Returning
   "cannot" strands it at its seed: it published a 411.3% "dead end" sitting at a 30 MVA seed.
3. **One definition of the sizing driver**, used by the loop *and* the report. They diverged
   once and the artifact contradicted the algorithm: the loop judged a unit against one MW
   figure while the published table carried a figure a quarter of that.
4. **Seed low, not high**, wherever a never-downgrade invariant applies, because the seed becomes
   permanent. A low seed is also a *high* impedance, so the loop climbs monotonically instead
   of oscillating through the size-drops-X-attracts-flow feedback.

### Why the count is a different decision from the size

The number of devices is a **topology** fact and belongs in the pass that builds topology; the
size belongs in the loop. Where one standard unit physically cannot serve the obligation,
`n = ceil(need / largest_standard_rating)`. Exactly one unit in the measured set needed it
(598 MVA of need against a 500 MVA catalogue ceiling).

Keep the justification straight: "two corridors terminate here" is **not** a reason for two
transformers. "One unit that exists cannot carry the load" is.
