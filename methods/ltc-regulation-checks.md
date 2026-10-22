---
type: method
domain: cross-cutting
topic: case-audit
aliases: [ltc-regulation-checks, ltc-regulated-bus, XFRegBus, XFRegTargetType, SSRegNum,
  regulates-nothing, ltc-middle-target, ltc-regulates-lv-side, repoint-the-regulator,
  ltc-causes-violation, which-bus-does-the-ltc-hold]
tags: [powerworld, esapp, transformer, ltc, tap, switched-shunt, voltage, case-quality,
  validation, remediation, n-0]
---

# Checking what each LTC and switched shunt actually regulates

## Abstract

A case can carry a full fleet of live load tap changers (LTCs) and still control voltage badly.
Switching the LTCs on decides little. The outcome turns on **which bus each one holds and how
it drives toward its band**. Three defects are common, and each one leaves
the power flow converging with no warning. (1) **A regulator pointed at nothing.** The regulated
bus (`Branch.XFRegBus` for an LTC, `Shunt.SSRegNum` for a switched shunt) does not exist or is
disconnected. (2) **`XFRegTargetType = Middle`**, the shipped value. When the regulated bus
leaves `[XFRegMin, XFRegMax]`, the LTC drives it back to the band's midpoint, not to the nearest
edge. A symmetric band then either lifts healthy buses or overshoots, and no band tuning fixes
both. `Max/Min` does. (3) **An LTC holding its low-voltage side while its high-voltage side is
out of band.** A tap is a ratio, not a source. Holding the LV bus moves the reactive deficit or
surplus onto the HV bus, so the LTC can cause the violation next to it. On a regional planning
model, measured 2026-09-14, re-pointing the regulated bus and switching the target type cleared
both emergency overvoltages and most normal-limit overvoltages. It added no devices.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [converting-lines-to-transformers](converting-lines-to-transformers.md) (writing
  `XF*` fields when esapp's whitelist refuses them) · [save-powerworld-case](save-powerworld-case.md)
  (a fix applied in memory and never saved is the commonest way to lose one) ·
  [adding-devices-esapp](adding-devices-esapp.md) (a switched shunt's `SSRegNum`)
- **Across:** [ranking-new-devices-by-severity](ranking-new-devices-by-severity.md) (a bus's own
  voltage limits, not the band you configured) ·
  [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md) (the other
  intact-case overvoltage, the one no LTC reaches) ·
  [violation-remediation](../demos/violation-remediation.md) (the diagnose-then-fix study this
  check feeds)
- **Checked by:** the case-auditor's `base.regulates_nothing`, `base.ltc_middle_target` and
  `base.ltc_regulates_lv_side` rules

## Content

### First, find out whether the fleet is live

Read these before drawing any conclusion about an LTC:

| field | what it tells you |
|---|---|
| `Branch.LineXfmr` | `YES` if the branch is a transformer |
| `Branch.LineXFType` | `Fixed`, `LTC`, `Mvar` or `Phase`. Only `LTC` regulates voltage |
| `Branch.XFAuto` | `YES`, `NO` or `OPF`: whether automatic control is on for this unit |
| `Branch.XFRegBus` | the bus it regulates. `0` on a fixed transformer |
| `Branch.XFRegMin` / `XFRegMax` | the voltage band, in per unit on the regulated bus |
| `Branch.XFRegTargetType` | `Middle` or `Max/Min` (below) |
| `Sim_Solution_Options.ChkTaps` | `YES` lets the solver move taps at all |

Three reading traps:

- **A band copied from the tap range never acts.** Some synthetic cases ship
  `XFRegMin`/`XFRegMax` = 0.51/1.5, the same numbers as `XFTapMin`/`XFTapMax`. Synth2k_series2
  does this on every transformer, alongside `XFAuto = NO` and `XFRegBus = 0`, so no unit there
  regulates anything (see [converting-lines-to-transformers](converting-lines-to-transformers.md)).
  Read as a voltage band, 0.51–1.5 is ±49 %. The regulated bus is always inside it and the tap
  never moves, yet the unit still reports as regulating.
- **Read the unsuffixed band.** `XFRegMin:1` / `XFRegMax:1` are the Time Step Simulation
  secondary regulation limits, not the power-flow band. On one case family the old 0.51/1.5
  values moved there when the power-flow band was set properly. A search for those numbers
  still finds them and suggests the wrong diagnosis.
- **`XFFixedTap` is not the live ratio.** It is the fixed component and can read `1.0` on every
  auto transformer, which looks like a fleet that has never moved. The live ratio is
  `Branch.LineTap`. It tracks `1 + XFTapPos × XFStep` exactly: `XFTapPos = -1` with
  `XFStep = 0.00625` reads `LineTap = 0.99375`.

### The rule that decides every tap question

A tap changes the turns ratio. It creates no reactive power. Raising the LV bus pulls the same
Mvar through the transformer from the HV side, so the HV bus goes down, and lowering the LV bus
pushes the HV bus up. **A tap moves a deficit or a surplus; it does not fill or absorb it.** It
fixes a violation only where the other side has headroom.

To find which side is the source, look at which side is higher in the solved case, not which
one has the higher nominal kV. A large load at 138 kV fed from a 69 kV network can sit below the
69 kV bus feeding it.

### Defect 1: the regulator points at nothing

An LTC's `XFRegBus`, or a switched shunt's `SSRegNum`, names a bus number. If that number is not
a bus in the case, or the bus reads `Bus.BusStatus = Disconnected`, the device has no valid
target. The case still solves, and the device either sits idle or does something PowerWorld
chose for it. Neither is what the modeller intended.

A switched shunt whose nominal range is zero (`SSMaxMVR = SSMinMVR = 0`) and whose regulated bus
is empty is usually a placeholder, not a defect.

**What `0` means.** Probed 2026-09-30 on two public synthetic cases (Hawaii40, Texas2k): writing
`XFRegBus = 0` on an LTC, or `SSRegNum = 0` on a regulating shunt, through SimAuto is **silently
refused** - the call succeeds and the previous bus number stays. A write to another existing bus
number does take. And a shunt that regulates its own terminal reads its own bus number: every
regulating shunt on both cases did (1 of 1 and 202 of 202). So `0` is never PowerWorld's spelling
of "own bus". A `0` read back on an active regulator came in with the case file, and it names no
target. `Shunt.AutoControl` read `YES` on every regulating shunt of both cases.

### Defect 2: `XFRegTargetType = Middle`

The field takes exactly two values. Measured on a live case:

| written | reads back |
|---|---|
| `Middle` | `Middle` |
| `Max`, `Maximum`, `High` | `Max/Min` |
| `Value`, `Specified`, `Target`, `Min` | coerced to `Middle` |

While the regulated bus is inside `[XFRegMin, XFRegMax]`, the LTC does nothing. When the bus
leaves the band:

- **`Middle`** drives it to the **midpoint** of the band.
- **`Max/Min`** drives it to the **nearest edge** and stops. A wide band becomes a one-sided
  limit: above `XFRegMax` the LTC taps down to `XFRegMax`, and anywhere inside the band it
  leaves the bus alone.

`XFRegTargetValue` is derived and read-only. Writing 1.04 to it read back 1.014, which was the
midpoint of the band in force at the time. That read-back is what confirmed the mechanism.

**Why a symmetric band cannot be tuned into working.** Measured 2026-09-14 on a regional
planning model: the same few tens of LTCs were retuned across five dispatches, four ways. Each
attempt was scored by the violations it *created*.

| attempt | band (pu) | target type | result |
|---|---|---|---|
| 1 | 1.030 – 1.045 | `Middle` | created many new violations |
| 2 | 1.035 – 1.048 | `Middle` | the 1.035 floor lifted healthy buses; one went from just under 1.03 to just over 1.05 |
| 3 | 0.98 – 1.048 | `Middle` | midpoint 1.014 overshot downward and dumped reactive power into neighbouring buses |
| 4 | **0.98 – 1.045** | **`Max/Min`** | one new violation; worked |

Attempts 2 and 3 fail in opposite directions for the same reason. A band low enough not to lift
a healthy bus has a midpoint well below the criterion. A band whose midpoint sits near the
criterion has a floor that lifts healthy buses. `Max/Min` removes the conflict: the floor can
stay at a harmless 0.98, and the LTC only ever acts downward.

Leave margin under the criterion. With a 1.05 criterion, 1.045 is safer than 1.050. A case
tuned to sit at exactly 1.050 in one dispatch violates in every other dispatch on the same base.

### Defect 3: the LTC holds its low-voltage side

If `XFRegBus` is the transformer's LV terminal, the LTC keeps a healthy 138 kV bus inside a
tight band while the HV bus it does not regulate drifts. The tap then works against the HV side.

The worst case measured (2026-09-14, regional planning model): an EHV bus at about **1.13 pu**,
past the 1.10 emergency limit. It had no generator, no shunt and no load, just two branches. The
transformer beside it held its LV bus just above the top of a narrow band (`XFRegError` a few
thousandths of a pu). Its tap was at `XFTapMax`, more than a dozen steps up, and the transformer
carried only a few MVA.
That LTC was the only device that could control the EHV bus, and it had spent its whole range
pushing that bus away. Re-pointing it to the EHV bus brought the bus to about **1.03**. A second
EHV bus hanging off the first by one line cleared with it.

**Standing check.** At any bus that violates with no local reactive source, list the
transformers touching it and read their `XFRegBus`. An LTC at `LineTap = XFTapMax` (or
`XFTapMin`) with a non-zero `XFRegError` is actively pushing the bus out of band.

Holding the LV side is right for a distribution tap feeding load and wrong for a bulk
transformer between two transmission voltages. The case alone cannot say which one was
intended, so this is a judgement call, not a defect.

**Which band the HV side is judged against.** `Bus.BusVoltLimLow` / `BusVoltLimHigh` are the
limits in force at that bus. Probed 2026-09-30 on both public cases: with no bus setting its own
limits (`BusVoltLim = NO` everywhere) they read the limit group's 0.9 / 1.1 on every bus, as
`0.89999998` / `1.10000002` - single precision, so compare with a tolerance. After writing
`BusVoltLim = YES` with 0.95 / 1.04 on one bus in memory, that bus read `0.94999999` /
`1.03999996`. Only where they read 0 or blank does a check need a band of its own.

### The fix: re-point the regulator, do not write the tap

Set `XFRegBus`, the band and the target type, and let the LTC find its own position. Do not
compute a tap yourself. Hand arithmetic brings its own direction trap:
`new_tap = old_tap × (v_measured / v_target)` is the natural guess, and it is backwards. The
correct form is `new_tap = old_tap × (v_target / v_measured)`. Re-measure on each new case
family whether the tap sits at the `XFNominalKV` end or the `:1` end.

```python
pw.edit_mode()
pw.esa.ChangeParametersSingleElement(
    "Branch", ["BusNum", "BusNum:1", "LineCircuit",
               "XFRegBus", "XFRegMin", "XFRegMax", "XFRegTargetType"],
    [str(f), str(t), "1", str(target_bus), "0.98000", "1.04500", "Max/Min"])
pw.run_mode()
pw.pflow()
# Read it back, target type included. esapp does not confirm the write for you.
```

`LineCircuit` is a string. `GetParametersSingleElement` needs one value slot per field, so pass a
trailing `""` for each field you are reading. esapp's bracket writer rejects `XF*` fields from a
wrong static whitelist; [converting-lines-to-transformers](converting-lines-to-transformers.md)
has the workaround.

Three exclusions, each measured:

1. **Never re-point a generator step-up (GSU).** Its HV bus is already regulated by its own
   machine through `Gen.GenRegNum`. Re-pointing the LTC puts two controllers on one target, and
   the machines there were already pinned at `GenMVRMin` with nothing left to give.
2. **Do not "repair" `XFTapMin = 1.00`.** A range that cannot go below nominal looks like a data
   defect. Widening it to 0.90 on two undervoltage units let each LTC hold its source bus by
   pulling down the load bus behind it, from about 0.94 to about 0.89, in every dispatch,
   including one that had been clean. Both sides were already low, so there was nothing to borrow. That floor was a
   guard.
3. **Never lower `XFTapMin`. Raise `XFTapMax` only where it sits below the unit's own tap
   position.** Widening ranges wholesale to 0.90–1.10 let one 345 kV bus swing 0.11 pu on travel
   it did not need.

### Judge a change by what it broke

A net violation count is the wrong acceptance test. List every bus that was in band before and is
out of band after. On the 2026-09-14 run, attempt 1 cut the total by about 40 % and still put
two new violations into the one dispatch that had been clean. Only the created-list caught it.

Voltage fixes move thermal loading too, in a direction that depends on the case. Size any
thermal fix against the flows after the voltage fix. On that run the worst branch in one
dispatch fell from about 106 % to 98 % before any rating changed.

## Worked result: re-pointing instead of buying devices

Measured 2026-09-14 on a regional planning model, five dispatches, intact case:

| | before → after |
|---|---|
| emergency overvoltage (> 1.10 pu) | a few → **0** |
| overvoltage (> 1.05 pu) | about four in five cleared; the rest within 0.006 pu of the limit |
| undervoltage (< 0.94 pu) | unchanged. A tap cannot reach it: both sides were low |
| thermal (> 100 %) | all cleared, with free rating corrections on installed equipment |
| devices added | **0** |

Every action was a settings change on equipment already in the case: a few tens of LTCs
re-pointed to their HV bus, band 0.98–1.045, `XFRegTargetType = Max/Min`, GSUs left alone.
Every check was run again on the cases reopened from disk, not in the session that wrote them.

## How the case-auditor checks this

The `case-audit` engine (`skills/case-audit/engine/rules_reg.py`) runs these checks read-only on
every audit. An **active LTC** is a closed branch with `LineXfmr = YES`, `LineXFType = LTC` and
`XFAuto = YES` whose terminals are not three-winding star buses (`Bus.BusIsStarBus = YES`).

| rule | fires when | needs a solve |
|---|---|---|
| `base.regulates_nothing` | a closed regulating shunt (`SSCMode` Discrete, Continuous or SVC, `AutoControl = YES`) or an active LTC names a regulated bus that is `0`, not in the case, or `Disconnected`. A 0 Mvar shunt with no target is reported separately as probably a placeholder | no |
| `base.ltc_middle_target` | active LTCs on `Middle` whose band is narrow enough to act; one finding for all of them, with the most common band | no |
| `base.ltc_regulates_lv_side` | an active LTC holds its LV terminal (or a remote bus at LV level) while its HV terminal is outside that bus's limits; generator step-ups are skipped and counted | yes |

Numbers with no source, each a proposed default in `skills/case-audit/engine/thresholds.py`:

| number | used for |
|---|---|
| band ≤ 0.2 pu | a band that can act (the sourced facts: 0.02–0.065 pu bands act, a 0.99 pu band never does) |
| 1 % | two terminals whose nominal kV agree this closely have no LV side |
| 1e-4 pu | the tolerance on a bus's limits |
| 0.94 / 1.05 pu | the band used only where a bus's limits read 0 or blank - the study criterion of the measured runs above, not a PowerWorld default |
| a unit on the LV bus (any status), no closed load there, and only transformers at that bus | how a generator step-up is recognised; units skipped this way are counted |

**Not checked in this version:** three-winding transformers. They carry their own regulation
fields on `3WXFormer`, and neither public case has one (0 rows on both), so how their legs appear
in `Branch` is untested. Also not checked: a band copied from the tap range
(`XFRegMin = XFTapMin`, `XFRegMax = XFTapMax`), described above; it has no rule yet.

Neither public case has an active LTC - every transformer on both reads `Fixed`, `XFAuto = NO`,
`XFRegTargetType = Middle` - so the LTC rules are tested on hand-built cases, not on a live one.
