---
type: method
domain: cross-cutting
topic: case-audit
aliases: [case-data-lint, lint-profile, data-quality-checks, case-sanity, shunt-steps,
  gen-below-min, missing-emergency-ratings, negative-reactance, islands-and-slacks, nominal-kv]
tags: [powerworld, esapp, case-quality, validation, switched-shunt, generator, ratings,
  topology, n-0]
---

# Linting a case for data defects that still solve

## Abstract

A case that converges can still be wrong, and the defects that matter most are the ones the
solve never complains about. A discrete shunt set to 40 Mvar when its blocks only switch in
steps of 15. A unit online below its own minimum output. Every branch rated on A and blank on
B and C, so an N-1 that monitors B checks nothing. The case-auditor's `lint` profile reads each
of these straight from the case, with no solve and no write, and names every object by its key
fields. It never stops a study; it says what is wrong, where, and whether it looks broken or
deliberate. On a synthetic planning model, measured 2026-10-10, the shunt-step rule matched an
independent engineer's hand count exactly, scenario by scenario, across all five dispatch
scenarios. The units-below-minimum rule found the same units the engineer did.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [ltc-regulation-checks](ltc-regulation-checks.md) (the regulating-mode set the
  shunt-band rule shares) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md)
  (which rate-set letter the N-1 reads)
- **Across:** [case-impedance-completeness](../concepts/case-impedance-completeness.md) (the other
  silent defect, a DC skeleton) · [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md)
  (the commonest source of units below their minimum)
- **Checked by:** the case-auditor's `lint.*` rules (`skills/case-audit/engine/rules_lint.py`),
  run with `--profiles base,lint`

## Content

### What each rule reads and why it matters

| rule | flags | fields | why the solve hides it |
|---|---|---|---|
| `lint.shunt_steps` | a `Discrete` shunt whose `SSNMVR` is beyond all its blocks together, or not reachable by whole steps | `SSBlockNumSteps[:1-9]`, `SSBlockMVarPerStep[:1-9]`, `SSNMVR` | the solve starts from the nominal setting whatever the blocks say |
| `lint.shunt_band_inverted` | a regulating shunt with `SSVHigh < SSVLow` | `SSVHigh`, `SSVLow`, `SSCMode` | the band is empty, so the shunt cannot regulate (an engineer reports PowerWorld switches such a control off; not tested here) |
| `lint.gen_below_min` | an online unit with `GenMW < GenMWMin` | `GenMW`, `GenMWMin`, `GenStatus` | the power flow does not enforce the minimum |
| `lint.gen_limits` | a missing MW or Mvar limit, one at ±9999, or max below min | `GenMWMax/Min`, `GenMVRMax/Min` | ±9999 is a format placeholder that reads as "no limit" |
| `lint.negative_x` | a closed branch with `LineX < 0`, star legs left out | `LineX`, `BusIsStarBus` | it solves; the branch's flow share comes out reversed |
| `lint.missing_ratings` | no rating A (jumpers left out), or rating A with no B or C | `LineAMVA`, `LineAMVA:1`, `LineAMVA:2`, `LimitSet.LSLineRateSet:1` | a 0 rating is never monitored |
| `lint.bus_names` | a blank `BusName` | `BusName` | breaks anything that finds a bus by name |
| `lint.islands` | energized islands apart from the main one; an island with load or generation and not exactly one slack | `BusStatus`, `LineStatus`, `BusCat` | each island solves, or fails, on its own |
| `lint.nominal_kv` | a nominal kV that is missing, 0, or has more than two decimals | `BusNomVolt` | kV-level filters skip the bus |

### How the shunt-step check decides

A discrete shunt can only sit on a whole number of steps of each block. The rule builds every
total the blocks can reach (each block from 0 to its step count, summed, rounded to 0.01 Mvar)
and asks whether `SSNMVR` is within 0.01 Mvar of one of them. Two steps of 15 reach 0, 15 and
30. A setting of 20 is *between steps*. A setting of 40 lies beyond the 30 maximum, so the rule
reports it as *beyond its blocks* instead. Every combination counts, not just in-order switching, so the
check errs towards fewer flags. A shunt with no blocks defined is skipped, because there is
nothing to check it against. A shunt whose blocks give more than 100,000 combinations is not
enumerated. It is listed instead, as an FYI that says it was not checked.

### Emergency ratings: Worth a look or FYI

Rating A with blank B and C is common: the public Texas2k case carries it on all 2,562 of its
rated branches. Whether that matters depends on what the N-1 reads. The rule looks at
`LSLineRateSet:1` in the limit sets in use. If that letter is B or C and the branches lack it,
those branches go unmonitored after an outage, and the finding is **Worth a look**, triaged Broken. If the N-1
reads A, the blanks are data still to fill, and the finding is **FYI**, triaged Your call. A rate set the N-1 uses
that is empty everywhere is a different, stopping rule: `mon.rate_set_empty`.

### A field that was not read

If the case did not return a field, or it reads blank on every row (a number as NaN, text as empty),
the engine treats it as not read and its rule reports nothing. That happens with an older snapshot, or with a PowerWorld that lacks the field. The engine
lists the rule under `rules_skipped` naming the field, and a rule whose one half could not run is
listed as run and as not checked for that half. Silence from a rule is not a pass.
The one exception is a switched-shunt block slot after the first: PowerWorld leaves an unused slot blank,
so a blank slot column is data and only a slot the case did not return counts as not read; a release that
returned blank for a slot a shunt really uses cannot be told apart by the data.
`BusName` gets no exception: every name blank reads as a field not returned, so `lint.bus_names` is listed
as not checked rather than flagging every bus.

### Thresholds

All are proposed defaults in `engine/thresholds.py`, not measurements: 0.01 Mvar step tolerance,
0.1 MW below minimum, ±9999 as the placeholder limit, 2e-4 pu as the jumper reactance (PowerWorld's
default zero-impedance threshold), and two decimals for nominal kV.

### Not in this version

These need a solve, a second case, or a scenario label that the case does not carry. Each is a
candidate for a later rule:

- a low-voltage or alternate solution
- regulators that conflict (a unit and a shunt holding the same bus to different targets)
- area interchange far from schedule
- load against generation by region
- a contingency count that dropped since the last version
- renewables online in a scenario that should have none
