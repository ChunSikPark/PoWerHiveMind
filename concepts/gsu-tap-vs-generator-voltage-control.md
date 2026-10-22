---
type: concept
domain: synthetic-grid
topic: power-flow
aliases: [gsu-tap-control, gsu-ltc, generator-voltage-control, one-controller-per-bus, fixed-gsu-tap]
tags: [synthetic-grid, gsu, transformer, tap, ltc, voltage, generator, convention]
---

# GSU tap control vs generator voltage control

## Abstract

Who regulates voltage at a plant: the step-up's tap changer or the generator? The planning convention is a fixed
GSU tap with the generator regulating one bus, and exactly one automatic controller per regulated bus. Covers the
evidence, per-class rules, how to pick the fixed tap, and what stays open. Most of it is [Likely], not [Certain].

## Connections

- **Up:** [Home](../index.md)
- **Across:** [ltc-regulation-checks](../methods/ltc-regulation-checks.md) (checking what each tap regulates) ·
  [gsu-outages-in-n1](gsu-outages-in-n1.md) (twins copy the fixed tap)

## Content

### The convention

1. **Real GSUs are mostly fixed-ratio.** Their taps are no-load (de-energized) taps, typically about ±5% in 2.5%
   steps, set at an outage. The generator's voltage regulator does the voltage work. [Likely]
2. **So the planning model runs GSU tap control off at a fixed tap, and the generator regulates one bus** (its
   terminal, or the GSU high side as a remote bus). [Likely]
3. **Exactly one automatic controller per regulated bus.** If a transformer keeps automatic control, its regulated
   bus must not be a bus a generator also regulates. Two controllers on one target fight, and in practice the
   machine pins at a reactive limit. [Likely]
4. **Inverter-based plants are the one exception worth a flag.** Many main power transformers have an on-load tap
   changer, but the plant controller at the point of interconnection is the regulator of record. Model the OLTC only
   where data says it exists, and only on the collector side. [Guessing on how common]

| Unit class | GSU tap | Transformer regulates | Generator regulates | Confidence |
|---|---|---|---|---|
| Thermal, hydro, nuclear | fixed (`XFAuto = NO`) | nothing | GSU high side (remote) or own terminal, one choice per fleet | Likely |
| Wind, solar, battery | fixed by default | collector side only, if an OLTC is kept | the POI or high-side bus, via the plant controller | Guessing |
| Synchronous condenser | fixed | nothing | own terminal or high side | Likely |
| Offline unit, any class | fixed, always | nothing | nothing | Certain |

### Evidence

- **A US ISO's public steady-state planning procedure manual** (2026 revision), section 4.5.1.8: control mode zero "prohibits
  automatic adjustment", and the controlled bus "should be non-zero only for voltage controlling transformers".
  No-load taps give ratios "usually in the range of 0.95 to 1.05"; automatic LTC ranges are "typically 0.80 to
  1.20". [Certain]
- **Same manual, section 4.3.5:** the GSU tap position, GSU tap control and the generator's remote regulated bus are
  all resource-registration data items. The manual models the GSU explicitly and gives the generator its own regulated-bus
  field, **but the manual never says what the tap control should be.** [Certain on the table; gap on the rule]
- **Section 4.3.4:** scheduled voltages "should reflect actual voltage set points used by the generator
  operators". [Certain]
- **NERC PRC-019 (draft revision):** defines the IBR main power transformer and makes the plant controller's
  voltage control act before protection trips, so the plant controller is the regulator of record. [Certain on the
  definition, Likely on the inference]
- **PowerWorld** has a remotely-regulated-bus view that lists every generator, transformer and shunt regulating a bus
  and flags mixed AVR status, so the conflict can be listed directly. Its transformer-control help covers parallel
  transformers fighting, not generator-plus-transformer. [Likely]
- **Measured on a ~9k-bus synthetic case (2026-10-11):** one outage failed with tap adjustment on and solved with it
  off. Bisection landed on twin offline-unit GSU LTCs, each regulating its own dead-end bus; locking the offline-GSU
  LTCs fixed it. A tap control on a dead unit has no physical meaning. [Certain]

### Picking the fixed tap

1. **Keep the solved tap.** Zero change to the solved case, but an offline unit's tap is wherever its LTC hunted
   to, which is arbitrary.
2. **Snap to the nearest real no-load step** (2.5% steps within 0.95–1.05). Matches equipment, and PSS/E and
   PowerWorld then agree on the same values.
3. **Centre the unit's reactive range:** the tap at which the unit sits mid-range at its typical dispatch and
   setpoint. Best N-1 headroom; costs a solve loop per unit.

Recommended: offline units at nominal; online units option 3, then rounded to option 2's step grid.

### Trade-offs to expect in review

- A fixed GSU cannot buck a post-contingency swing, so the generator reaches its Q limit sooner. Real units behave
  the same way, so this is realistic, not a defect.
- Fixed taps make bad tap data matter more: a wrong ratio keeps a unit at a Q limit all the time.
- "Keep the LTC and drop the generator's remote regulation" moves control onto a device real GSUs do not have, and
  does not match registration data, which lists a generator remote bus.

### Until the rule is settled

Lock every GSU tap at its solved tap. If locking every GSU tap and aligning setpoints still fails a full Newton
solve in another tool such as PSS/E, tap conflict was not the cause; switch controls off one class at a time instead.

Not found: a public GSU tap specification (IEEE C57.116 not reached), what PSS/E does with a tap and a generator on
one bus, IEEE 2800 guidance on OLTC coordination, and the ACTIVSg synthetic grids' own convention. The last one can
be read straight off Synth2k: for each transformer with a generator bus at one end, compare `XFAuto` and
`XFRegBus` with the generator's `GenRegNum`.
