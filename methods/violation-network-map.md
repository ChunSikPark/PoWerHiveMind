---
type: method
domain: tooling
topic: contingency
aliases: [violation-network-map, violation-map, voltage-map, reactive-balance-map, radial-ties-map,
  islanding-screen, map-the-violations, visualize-the-violations, network-map, bridge-screen,
  thermal-map, overload-map, worst-case-per-line]
tags: [esapp, powerworld, voltage, overvoltage, islanding, radial, bridges, visualization, html,
  remediation, n-1, reactive-power, thermal, overload, contingency]
---

# Mapping Violations on the Network: the Voltage and Thermal Page, and the Radial-Ties Page

## Abstract

Two single-file HTML pages that put a violation **on the map** instead of in a table, built by the
`violation-map` skill's engine (`skills/violation-map/engine/`). The **voltage page** shows the
substations around a set of out-of-band buses, every line in its own kV colour, a click-to-zoom
problem list, a one-line of any substation, the **reactive balance** inside the radius (line
charging against generators absorbing and reactors, with the *room* each has left), and —
optionally — measured candidate fixes with a Before/After switch and a scenario × outage
pass/fail grid. Its **thermal view** colours every line by its loading against the rating in
use (red at or above 100%, orange from 90%, the rest grey), with nothing out, after any one
outage, or each line at its worst post-outage loading with the outage behind it. The **radial-ties page** screens the whole grid for **bridges** (lines whose
single outage splits the network), groups them into radial trees, suggests a tie per tree and
shows its AC-measured verdict.

Four facts decide whether the pages tell the truth, and each fails silently: an outage that
**islands load solves with zero violations**, so islanding needs its own screen; a measured
candidate needs a **fresh case**, because LTC taps and switched shunts do not move back when you
undo; a tie's **rating does not scale with its length**; and a PowerWorld process you do not
`esa.exit()` stays resident. The thermal view adds two more: a case's shipped contingency list
rarely trips the study's **new** devices, and **ViolationCTG cannot draw the orange band**,
because it reports only what is already over the limit.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [adding-devices-esapp](adding-devices-esapp.md) · [esapp-overview](esapp-overview.md) · [reading-violationctg](reading-violationctg.md)
- **Across:** [violation-remediation](../demos/violation-remediation.md) · [ranking-new-devices-by-severity](ranking-new-devices-by-severity.md) · [handling-errors](handling-errors.md)

## Content

### When to reach for it

When the question is *where* — where the high buses sit, what feeds them, what one outage cuts
off, what a new line would close. A table of 40 overvoltage rows is four problems in four
places; the map makes that grouping visible before any fix is proposed. It is the diagnose step
of [violation-remediation](../demos/violation-remediation.md), drawn.

It is **not** a replacement for the N-1 run. The voltage page tests only the outages you list;
the radial page tests only bridge outages. Neither is a full contingency analysis — the pages
say so on every measured result, and so should you.

### Ask before extracting anything

Four decisions belong to the user, and each changes what gets extracted:

| Ask | Default to offer |
|---|---|
| Which cases, and which **states** (as delivered, after a fix) | the delivered set only |
| Which violations: intact voltage, N-1 voltage, islanding | intact voltage |
| Area and depth: seeded from which buses, how many substation-hops | seeds = the out-of-band buses, 5 hops |
| Look only, or also **measure candidate fixes** | look only |

Very meshed areas explode past a few hops — open those at 2–3 and say so. Step-up, star-point
and tertiary buses are out of the count by default (`exclude_bus_prefixes`); list them
separately if the user wants them.

**Opening view, by case size.** A light case (under a bus-count cutoff) opens on the whole case
with the site highlighted, as an orientation view. Zooming into a site switches to that area
exclusively: the rest is hidden, not just off-screen, boundary stubs stay, and clicking a
substation re-centres; on a light case a "Back to whole case" control returns to the whole-case
view. A "Render further network" button grows the area by N more
substation-hops per press. A heavy case (over the cutoff) opens straight on the area. The cutoff
is a tunable bus-count default, measured by timing page build and render on public synthetic
cases, and the page states which mode it opened in and why. The engine does not apply this rule
yet. What is drawn never limits what is computed.

### The pipeline

Everything is driven by one `config.json` (see `skills/violation-map/config.example.json`):
scenarios, states with one case path per scenario, the voltage band, the seeded areas, and
optionally a `designs` block. Every output lands in the config's `out_dir`; nothing is written
to a case.

```bash
E=<kit root>/skills/violation-map/engine
# voltage page
python $E/extract.py         config.json topo      # area topology + hop rings
python $E/extract.py         config.json state     # solved values, every state x scenario
python $E/extract_thermal.py config.json           # optional: loading with nothing out and after every outage
python $E/measure_designs.py config.json           # optional: candidate fixes, in memory
python $E/build.py           config.json           # -> voltage_map.html, or thermal_map.html with thermal data
python $E/test_thermal.py                          # after touching the colour rule in vmap.py or the template
# radial-ties page
python $E/extract_full.py    config.json topo
python $E/extract_full.py    config.json inj
python $E/islanding_screen.py config.json          # bridges, core, radial trees
python $E/designs_all.py     config.json           # suggested tie per tree
python $E/measure_trees.py   config.json <scenario>   # per scenario; AC, in memory
python $E/build_radial.py    config.json           # -> radial_ties.html
```

Run the script by its full path rather than changing directory first: each script imports its
sibling `vmap.py`, and Python finds it because the script's own folder is on the path.

### The page contract

- **Every line in its own kV colour, everywhere** (765 green, 345 red, 138 dark, ≤69 olive).
  Emphasis is by width only. Recolouring a line by the group it belongs to reads as a different
  voltage and confuses the reader. **The one exception is the thermal view**, where colour *is*
  the message and kV is left to the layer filter and the hover.
- **Problem list with click-to-zoom**, plus Prev/Next on the map bar.
- **Voltage-layer filter** (All / 765 / 345 / 138 / ≤69) that hides the other classes' lines and
  substations.
- **Substation one-line** on click: bus bars by kV with pu, transformers with X and flow,
  generators and shunts with MVAr and pinned flags, outgoing lines fanned with far-end names —
  and **Isolate neighbourhood** at 1–3 hops.
- A **scenario switch**, a **state switch** (as delivered / after a fix), and for measured
  designs a **Before/After** switch and a scenario × condition grid of pass/fail cells.
- **Reactive balance** inside the radius. Capability is not room: a generator at its absorbing
  limit has capability and no room, which is exactly the unit that cannot help.
- **Choose / Accept** writes the pick to the page's own store when the page is published where
  one exists (a Claude artifact with the `db` capability); the agent reads it back instead of
  asking the user to retype it. Without a store the button is replaced by "tell your agent".
- **PNG/SVG export** with a title band and colours baked in, and a **CSV** of the problems or the
  candidate table.

**The thermal view**, built when `extract_thermal.py` has run (the page then opens on it, with a
Thermal / Voltage switch):

- **Red** at or above `thermal.over` (default 100) % of the rating in use, **orange** from
  `thermal.near` (default 90), **every other line grey**, so the eye lands on red and orange.
  Every red or orange line carries its % in a pill, and the % is in ink, never in the line colour.
  Colour is never the only signal.
- **Three views:** *nothing out*; *after an outage*, picked from a list ordered by the worst
  loading each causes, with Prev/Next to step through it; *worst case per line*, where each
  branch is drawn at its highest post-outage loading and the outage behind it shows in the list
  and the hover. Selecting a line in that view draws its causing outage dashed.
- **Width scales with MVA flow**, against one reference per state, so widths do not jump between
  views. **Moving dots** show flow direction on lines above half their rating, and an arrow does
  the same on every red or orange line, so a still export keeps the direction. **Overloaded
  lines pulse gently.** Under `prefers-reduced-motion` the dots and the pulse stop and a steady
  glow stays.
- **The element that is out** is drawn dashed in ink with an `OUT` pill. An outaged generator or
  transformer gets a dashed ring at its substation instead.
- **Transformers inside a substation** have no line to colour, so a red or orange one rings its
  substation with an `XF nn%` pill. Without this they would sit in the problem list but nowhere
  on the map.
- **Ranked problem list** (branch, %, MVA vs rating, causing outage), click to zoom, plus
  Prev/Next on the map bar. **Hover** a line for every circuit's MVA, rating and %. **Click** a
  line for its circuits in this view, with nothing out, and at worst, plus the eight outages that
  load it most, each one click away from its own view.
- Substations are neutral grey in this view. Voltages are a voltage-view question, and a dot
  coloured by base-case voltage under a post-outage label would be wrong.

Open the built HTML in a browser, or publish it. Take one screenshot before handing it over —
a page that renders blank from a data error looks identical to one still loading.

### Traps, each of which cost a run

**`esa.exit()` every case you open.** `del pw` leaves one `pwrworld.exe` resident per open —
roughly a gigabyte each on a 10,000-bus model — and a measurement loop that opens a case per
candidate will starve every other process on the machine. The engine closes in a `finally`.

**A fresh open per candidate; never trust an undo.** Taking a new line back out does not move
LTC taps or switched shunts back to where they were, so the next candidate is measured on a
different case. `measure_designs.py` reopens per candidate. `measure_trees.py` reuses one case
per scenario for speed, and **fingerprints** it after every design — closed-branch count plus a
fixed 40-bus voltage sample — and reopens the moment either drifts. An undo that did not restore
the case once went unnoticed until the fingerprint caught it.

**Islanding solves with zero violations.** When an outage strands buses, PowerWorld drops them
from the solution rather than flagging them, so the violation count stays clean. The radial page
exists because of this; the voltage page marks a substation ISLANDED when every one of its
network buses loses its voltage. Read [reading-violationctg](reading-violationctg.md) for the
N-1 side of the same trap.

**Adding several devices before one solve: freeze the controls.** Live taps and shunts drift
between writes, and the saved case then disagrees with what you measured. Set `ChkTaps`,
`ChkShunts` and `ChkPhaseShifters` to `NO`, add everything, restore them, and take one solve.
The engine adds one device per candidate, so it does not need this — a multi-device candidate
does.

**A tie starts where the MW is, then where it closes the most bridges.** For a chain of substations,
the far end usually removes the most bridges; for a plant tree, start at the plant only when the
plant's own exit is weaker than the plant. `designs_all.py` ranks sources by MW first because
the other order once routed a plant's whole output through a lower-voltage line inside the
pocket when its exit opened.

**Rating does not scale with length; impedance does.** A new line cloned from a template gets R,
X, C and G scaled by the length ratio and the template's whole `LineAMVA` set unchanged. Choose
the template by **rating first** (it must clear the stranded MW) and length second — a template
chosen by length alone once put a line at 250% into a delivered case. The create is read back:
branch count +1, X as asked, status Closed, device type Line. See
[adding-devices-esapp](adding-devices-esapp.md) for why every create must be read back.

### Thermal traps

**The shipped contingency list rarely trips the new devices.** A case's list is built for one
area and before the study's own additions existed. Solve it alone and the one outage that
matters, losing the new line, is never run: the page draws a clean design that overloads to
nearly three times its rating. `thermal.outages` therefore defaults to `"case+area"`, which keeps
the shipped list and adds one outage per in-service drawn branch at or above `min_net_kv` that
the list does not already open. Matching is by unordered bus pair plus circuit, read from
`ContingencyElement.Object`, never by parsing a label. Only a case contingency that runs (not
`CTGSkip`) and opens that one branch alone counts as covering it. A branch that appears only
inside a skipped or multi-element contingency still gets its own single outage. The added set goes in through an aux file
loaded by absolute path, and the loaded element count is asserted
([new-device-contingency-aux](new-device-contingency-aux.md)).

**ViolationCTG cannot draw the orange band.** It reports only what is over the monitoring limit,
so a line at 97% after an outage never appears there. The engine applies each outage itself
(`CTGApply`, solve, read every drawn branch), then puts it back with `CTGRestoreReference` **and
a fresh solve**: the restore puts the inputs back, but not the flows. Every undo is checked
against the base loadings, and the run stops if they move by more than 0.01 points. Then it runs
`CTGClearAllResults` and `CTGSolveAll` on the same list, and the check runs both ways:
- every `ViolationCTG` thermal row must match the per-outage loading within 1 point;
- every per-outage overload above the limit set's `LSLinePercent` on a **monitored** branch
  (`LineMonEle:1`) must have a `ViolationCTG` row.

An overload on a branch the case does not monitor is drawn anyway, and the page says PowerWorld
did not report it. Two independent paths that agree are the evidence; a disagreement stops the
build instead of drawing either. The base case is solved in AC before anything is read, and a
second solve must reproduce it, because a case saved with the DC approximation would otherwise
give a DC "nothing out" view under an AC "after an outage" one.

**Which percent, against which rating.** `LinePercent` is the from-end percent and
`LinePercent:1` the to-end. `LineMaxPercent` is the higher of the two, and it equals
`max(LineMVA, LineMVA:1) / LineLimMVA` exactly. `LineLimMVA` is the normal rating and
`LineLimMVA:1` the **contingency** rating. Each comes from the limit set's own rate-set choice
(`LSLineRateSet`, `LSLineRateSet:1`), so the page judges nothing out against the first and
post-outage loading against the second. On a case where both sets are A they agree; on one with
an emergency set they do not, and a page that used `LineMaxPercent` after an outage would show
false red. Measured 2026-10-21 on a design case built on the public 2,000-bus Texas synthetic
grid, Simulator 25.

**Amp ratings are refused, not guessed.** A limit set with `LSAmpMVA` other than `MVA` stops
the run. An MVA percent on an amp-rated branch is a plausible wrong number
([reading-violationctg](reading-violationctg.md), trap 5).

**Islanding still hides.** An outage that strands load leaves those lines at zero flow, grey. The
outage list marks every outage whose `Contingency.LoadMW` is non-zero with how much it cuts off.
PowerWorld leaves that field **blank, not 0**, when nothing is cut off. On a 2026-10-21 run it was
blank on every outage while `GenMW` on the same rows carried numbers wherever generation was
lost, so the engine reads blank as zero. `GenMW` is also non-zero on an ordinary generator trip,
so it is not an islanding signal. Read the radial page for the rest.

**Cost and size.** About 0.4 s per outage on a 2,000-bus case: two solves and three reads. Each
outage stores only the branches it moved by at least 0.5 points, or that sit within 1 point of
the orange threshold, and the page falls back to the base value for the rest. A few hundred
outages over a few hundred drawn branches build to well under a megabyte.

### What it does not do yet

- **Thermal covers the drawn area's branches plus the case's list, not a full N-1 of the whole
  case.** An overload whose outage and line both sit outside the drawn hops is not found. The
  page says how many outages ran and where they came from; say the same in the answer.
- **No amp-rated limits** in the thermal view (above).
- **No candidate fixes measured for thermal.** The designs panel is voltage-only.
