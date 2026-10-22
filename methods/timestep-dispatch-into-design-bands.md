---
type: method
domain: synthetic-grid
topic: timestep
aliases: [timestep-dispatch-into-design-bands, weather-based-dispatch, scaling-timestep-dispatch, renewable-dispatch-from-timestep]
tags: [timestep, dispatch, pfw, powerworld, synthetic-grid, curtailment, agc]
---

# Method: Turning time-step output into a scenario dispatch that meets the design bands

## Abstract

How to dispatch wind and solar unit by unit from a PowerWorld time-step run, and how to scale that pattern
into the scenario's design bands when no real hour fits. Covers the clock trap, the scaling rule, batteries,
rebalancing, AGC, and what the new dispatch exposes. Read before building any renewable scenario dispatch.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation-setup](timestep-simulation-setup.md) (getting the per-unit output) ·
  [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md) (writing the result into the case) · [pww-data](../concepts/pww-data.md) ·
  [opf-preconditions](../concepts/opf-preconditions.md) (AGC fields) · [agc-participation-factors](../concepts/agc-participation-factors.md) (step 7 in full)

## Content

### The symptom this fixes

A fleet-level dispatch ("wind at 45% of fleet") filled **largest unit first, each to 100%** gives the right total
and an unrealistic split: the online units are exactly the N largest, every one at maximum, the rest off. Test
for it directly: sort a fuel's units by MWMax and check whether the online set is the top N. On a ~9k-bus synthetic case (measured
2026-10-16) it was, in three of five scenarios, with one farm on and a farm barely smaller off. Offline units in
such a case are not outages, weather or curtailment, and a reviewer will ask which they are.

### Steps

1. **Get each unit's output on PowerWorld's own clock.** Run the time-step simulation with a PFW model on every
   wind and solar unit and save `GenMW` per unit ([timestep-simulation-setup](timestep-simulation-setup.md)). Take times from the raw export's
   column 0 (Excel serial days, UTC). Check any pipeline's own CSV time labels against column 0 before trusting them: one
   pipeline's ran 7 h early inside US DST and 6 h outside. Load data from an ISO is usually local hour ending;
   convert it to UTC before joining. A wrong join pairs the load with weather from another hour; measured
   2026-10-16, every scenario's renewables on that case came from about 2 h after its load hour, and the "no solar"
   scenario's load hour still had sun.
2. **Look for a real hour first.** Over a year of per-unit output, compute fleet wind % and solar % (output over
   the whole fleet's MWMax) and the load % for the same instant, and keep the in-season hours that sit inside
   all bands. Prefer the hour whose fleet totals are closest to what the case already carries, so thermal barely
   moves. Expect few or none for demanding scenarios: on a 2025 search, one scenario had 0 hours, one had 2.
3. **When no hour fits, scale the pattern.** Scenario designs usually ask for *statistically representative*
   conditions, not a copy of a historical hour, so a real hour's weather may set the unit-by-unit pattern and
   the fleet total may be scaled into the band. Per fuel:
   - target `T` = a fleet MW inside the band (keeping the case's current total, if it is in band, leaves the
     balance and thermal dispatch untouched);
   - unit MW = `min(k × w_i, Pmax_i)`, where `w_i` is the unit's weather output (negative clipped to 0) and one
     factor `k` per fuel is found by bisection so the units sum to `T` (water-filling: a capped unit's excess
     spreads to the units that still have room);
   - a unit with zero weather output stays off. If the units with output cannot reach `T` even at their maxima,
     report the shortfall instead of turning on dark units.
   - `k < 1` is **curtailment**: report each unit's held-back MW (weather minus dispatched). `k > 1` is allowed but
     say how large; at roughly 1.5× and above, which farms are windy rests on the weather file more than on the
     target, so verify the weather first.
   - The band's headroom is also a reserve lever: when every conventional unit is already online, raising wind
     inside its band and taking the MW off gas is how thermal reserve gets freed.
4. **Batteries have no weather.** Run every battery at the same design % of its own MWMax. A design 0% means all
   open, **including a battery that sits on the slack bus**: PowerWorld splits the slack's swing among that bus's
   units, so a slack-bus battery discharges whenever the slack moves (on the ~9k-bus case it ran 79–200 MW in scenarios
   designed for 0%).
5. **Rebalance the net change on thermal, never on the slack.** Wind and solar scaled to the old total change
   nothing; the battery change does. Move that MW onto or off the online non-slack thermal units, pro rata to
   their room (above GenMWMin to reduce, below GenMWMax to raise). A slack unit near its minimum cannot absorb
   hundreds of MW.
6. **Write, read back, solve, save** as in [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md): write `GenStatus` and `GenMW` with
   the key fields, read them back (a write without keys no-ops silently), warm-solve, save to a temporary file and
   swap it in, then reopen cold in a fresh process and compare.
7. **Turn on AGC so contingencies share lost MW.** Set `GenAGCAble = YES` on dispatchable synchronous units (not
   wind, solar, batteries, or 0 MW condensers); run PowerWorld's `SetParticipationFactors(MAXMWRAT, 0, SYSTEM);`
   and set `CTG_Options.UseAreaPartsMakeUpPower` to `Gen Part Factors`. `MAXMWRAT` stores MWMax in per unit on the
   100 MVA base (150 MW becomes 1.5); only ratios matter. With AGC flags on but every factor 0, lost MW still lands
   on the slack alone. This matches the Synth2k series 24 and ACTIVSg10k convention (surveyed read-only
   2026-10-18; one other public case shipped all factors at 0). The base case does not move.

### What the new dispatch exposes

Measured 2026-10-18 on the ~9k-bus case, five scenarios, warm AC solve after applying the scaled dispatch:

- **Undersized generator step-ups.** Spreading output over every farm runs small units that the largest-first
  fill never touched; base-case overloads were almost all their step-up transformers, at roughly 1.2–2× rating.
  Check each step-up's rating against its unit's MVA before solving.
- **Renewables with a non-zero minimum** fall below it at low weather output. Wind and solar minimums should be 0.
- **Light-load voltages rise.** In the low-load, high-renewable scenario, buses above 1.05 pu went from about 20
  to about 150, mostly at 345 kV, once output was spread across the fleet.
- **Losses move**, so the slack moves; check it against its limits after the solve.

### Check the weather file before trusting a season

Compare the time-step run's monthly fleet capacity factor with an independent source before using a season.
Measured 2026-10-18 on an ERA5 PWW for 2024–2025: summer fleet wind was 5–7% against 26–38% in an
independent forecast set; the file's 100 m wind read 2–4 m/s at the wind sites in summer against 6–11 m/s in
other seasons, every unit dropped alike (so not the models), and October–December matched the forecast set
exactly. **Cause found 2026-10-19:** that file's grid is scrambled for nine consecutive months; the low summer
wind was a symptom, not a wind-model problem. Run the sunrise/sunset geography check in [pww-data](../concepts/pww-data.md) (check 3)
on every month a scenario draws from. Any scenario whose pattern comes from a failing month is provisional.

### Checks before calling it done

- every fuel's fleet % inside its band, from the saved file, not from the plan;
- no unit above MWMax, no open unit carrying MW, and every unit below its minimum listed (not clamped);
- curtailment and shortfall reported per scenario in MW;
- base-case overloads and voltages compared before and after, and the slack inside its limits;
- AGC units carry non-zero participation factors, and make-up power reads `Gen Part Factors` on a cold reopen.
