---
name: violation-map
description: "Build an interactive network map of the violations in PowerWorld cases: out-of-band voltages with the reactive balance around them, overloaded branches with nothing out and after each outage, or the radial trees one outage can island, with candidate fixes measured and a Before/After switch. Use when the user says map the violations, visualize the violations, show me where the high voltages are, which lines overload, show me the overloads on a map, show me the network around a bus, which outages island load, where are the radial lines, or asks to see a voltage, thermal or islanding problem and what could fix it."
---

# Violation map

A working engine plus a page contract. The engine lives in `engine/` next to this file and is
driven by one config file; the contract and every trap it guards against are in
`methods/violation-network-map.md` under the **kit root** (`${CLAUDE_PLUGIN_ROOT}` when installed
as a plugin, otherwise the directory holding `AGENTS.md`). Read that page in full before running
anything. Reuse the engine; do not rebuild the map from scratch.

## 1. Before anything else

- Run the preflight in `methods/preflight-powerworld.md`. The engine drives PowerWorld through
  esapp; a machine that cannot is a fact about the machine, not a bug to code around.
- Read `methods/violation-network-map.md`, then the page it points at for anything you are about
  to write (`methods/adding-devices-esapp.md` before a candidate that creates a device).

## 2. Ask before extracting (four questions, defaults stated)

1. **Which cases and which states.** One case per scenario; a second state (after a fix) is
   optional. If the cases are restricted — CEII or otherwise — say that the built page embeds
   bus names, substation names and coordinates, and must be shared accordingly.
2. **Which violations:** intact voltage, voltage after listed outages, thermal loading (nothing
   out and after each outage), or islanding (the radial page). **The band is the case's own limits by default**: read `BusVoltLimLow` /
   `BusVoltLimHigh` and set `band` in the config from them. 0.94–1.05 pu (the engine's fallback)
   applies only when the case carries none, or when the user asks for it. A bus inside the case's
   limits is not a violation, whatever the fallback says.
   **"Show me the violations" with no qualifier means intact *and* N-1.** Solve the case's
   contingencies too, and make sure the list covers the study area's own elements, the new
   devices included (`methods/new-device-contingency-aux.md`, "Monitoring a region is not testing
   it"). Thermal overloads go on the map's **thermal view** (below) and in your text answer,
   worst first.
3. **Area and depth:** the seed buses (default: the out-of-band network buses) and the
   substation-hops around them (default 5; offer 2–3 for a very meshed area). What is drawn
   never limits what is computed.
4. **Look only, or measure fixes:** reactors, new lines, setpoint edits, measured in memory.

Then write their `config.json` from `config.example.json` next to this file. Keep it and the
`out_dir` outside the kit folder.

When you cannot ask (a headless or one-shot run), use these defaults and say each one in your
answer: the case's own limits, intact plus N-1, the out-of-band buses as seeds, 5 hops, look only.

## 3. Run

Call each script by its full path with the config as the first argument; the order is on the
method page. Measurement scripts open PowerWorld once per candidate — say roughly how long
before starting a long one, and run it in the background.

## 4. Hand it over

- Screenshot the built HTML once (a headless browser is enough) before saying it is done.
- Say what was measured and what was not: the voltage page tests only the listed outages, the
  radial page only bridge outages. Neither is a full N-1.
- If the page is published somewhere with a store (a Claude artifact with the `db` capability),
  read the user's Choose/Accept back from it rather than asking them to retype the pick.

## Thermal view

Built when `extract_thermal.py` has run: `build.py` then writes `thermal_map.html`, which opens
on thermal with the voltage view one switch away. Run it after `extract.py topo` and `state`.
For a thermal question, seed the area at the new devices or at the ends of the overloaded
branches from the N-1 pass.

- **Colours:** red at or above `thermal.over` (default 100) % of the rating in use, orange from
  `thermal.near` (default 90), every other line grey. Each red or orange line carries its % label.
- **Rating in use:** the normal rating with nothing out, the contingency rating after an outage.
  It reads MVA ratings only, and stops with a message on a case rated in amps.
- **Three views:** nothing out; after one outage (picked from a list ordered by the worst
  loading it causes, with the tripped element dashed); worst case per line (each branch at its
  highest post-outage loading, with the outage behind it).
- **Outages:** `thermal.outages` defaults to `"case+area"`: the case's own list, plus one outage
  for every in-service drawn branch at or above `min_net_kv` that the list does not already
  open. `"case"` uses the shipped list alone, which often misses the study's new devices.
  Say how many outages ran, and from where. It is a full N-1 of the drawn area's branches plus
  the case's list, not of the whole case.
- It fails loudly instead of drawing a wrong page: an undo that does not restore the base
  loadings stops the run, and PowerWorld's `ViolationCTG` must agree with the per-outage loading
  both ways: every reported row within 1 point, and every overload on a monitored branch reported.
- Roughly 0.4 s per outage on a 2,000-bus case. Run it in the background past a few hundred.
- `engine/test_thermal.py` holds the Python and page colour rules together. Run it after
  touching either.

## Not built yet

**Opening view:** a light case (under a bus-count cutoff) opens on the whole case with the
site highlighted; zooming into a site shows that area only, the rest hidden, with boundary
stubs, click to re-centre; on a light case a "Back to whole case" control returns to the
whole-case view; and a "Render further network" button that adds N more hops per press; a
heavy case (over the cutoff) opens straight on the area. The page says which mode it opened in
and why. The cutoff is a tunable bus-count default, measured by timing page build and render
on public synthetic cases; the engine does not apply this rule yet.
