# Index — every page in PowerWorldHiveMind

One line per page. Read this to decide what to open; do not open everything.

**Start here:**
1. [preflight-powerworld](methods/preflight-powerworld.md): can this machine drive PowerWorld at all?
2. [esapp-overview](methods/esapp-overview.md): open a case, read data, solve power flow.
3. [Task routing in AGENTS.md](AGENTS.md#task-routing): the page for your task.
4. [glossary](concepts/glossary.md): any term you do not recognise.

## Demos — worked examples with real output

Complete runs on the public synthetic Synth40 case (37 buses), plus a Synth2k run, including what goes wrong and how it was fixed.

| Page | What it covers |
|---|---|
| [aux-file-cookbook](demos/aux-file-cookbook.md) | Claude in one window, Simulator in the other. Four recipes in order: turn the channel on, prove it with a four-line script, inventory a case, then take a bus out and measure it. Start here if you are working through files rather than Python. |
| [adding-a-device](demos/adding-a-device.md) | Three attempts that reported success and created nothing, then the fix. `CreateData` accepts a malformed call and builds nothing. If you read one demo, read this one. |
| [comparing-planning-cases](demos/comparing-planning-cases.md) | Diff a 2016 and a 2024 case to find what the plan builds (691 new branches, 199 new generators), then solve a contingency set for only the new devices. Includes the scoping trap that makes the naive answer 87% wrong. |
| [contingency-and-aux](demos/contingency-and-aux.md) | Run N-1 from nothing, then write a filter and contingency `.aux` from the result and load it back. 89 auto-inserted contingencies, 12 violations, 5 targeted ones merged. |
| [power-flow-and-sensitivities](demos/power-flow-and-sensitivities.md) | AC and DC solves plus LODF and PTDF, including the `1e8` sentinel that makes LODF output look insane and a PTDF failure whose obvious fix fails the same way. |
| [start-here](demos/start-here.md) | The one-line prompts to open with, and worked runs on the public synthetic Synth40 case (37 buses) with every failure left in on purpose. |
| [timestep-and-pfw](demos/timestep-and-pfw.md) | Turn a weather file into hourly wind and solar output, starting with the check that decides whether the case can do it at all: do its renewable units carry PFW model strings? Here, 9 of 45 did. |
| [violation-remediation](demos/violation-remediation.md) | The full study: find 12 N-1 violations, work out why they happen, test five reinforcements, and rank them by measured effect. Two of the five made the system worse. |

## Methods — how to do a thing

Step-by-step procedures. Read the one that matches your task.

| Page | What it covers |
|---|---|
| [adding-devices-esapp](methods/adding-devices-esapp.md) | Create buses, branches and loads in an open case, then solve a DC OPF and screen N-1. The write-side counterpart to esapp-overview. |
| [case-data-lint](methods/case-data-lint.md) | Find the data defects a case solves straight through: discrete shunts set off their steps, units below their minimum, placeholder or inverted limits, missing emergency ratings, negative reactance, unnamed buses, stray islands and slacks, odd nominal kV. The case-auditor's `lint` profile. |
| [aux-file-mode](methods/aux-file-mode.md) | PowerWorld and LLM interaction through files: the agent writes `.aux`, you drop it into a watched folder, results come back as CSVs. The GUI setup handshake an agent cannot perform itself, the rules (never `OpenCase`, never `LogClear`, always read back), and a working template to copy. |
| [applying-a-dispatch-to-a-case](methods/applying-a-dispatch-to-a-case.md) | Turn a MW-per-generator dispatch into a runnable scenario case. The DC solve fakes a balance rather than telling you the fleet is short. |
| [converting-lines-to-transformers](methods/converting-lines-to-transformers.md) | Reclassify branches as transformers when a case models every branch as a line. `BranchDeviceType` is read-only; the real switch is `LineXFMR = "YES"` plus the nominal kV fields. |
| [diagnosing-a-non-converging-contingency](methods/diagnosing-a-non-converging-contingency.md) | Why an N-1 outage did not solve: an island stopped at RESERVE LIMITS, a voltage collapse, a bad Newton start or a harness bug, told apart in four probes. Read before sizing anything for an unsolved outage. |
| [emergency-ratings-for-a-synthetic-case](methods/emergency-ratings-for-a-synthetic-case.md) | Give every branch its own Rate B and C from a reviewer's per-class statistics instead of one flat ratio: a per-branch draw in 0.5–1.5× the class mean, `A <= B <= C`, then point contingency monitoring at Rate B and rerun N-1. |
| [esapp-overview](methods/esapp-overview.md) | The starting page: open a case, read and write data, solve power flow, and use `snapshot()` to experiment without damaging anything. |
| [finding-and-fixing-radial-by-n1-pockets](methods/finding-and-fixing-radial-by-n1-pockets.md) | Find pockets that one outage leaves on a long, weak survivor, or islands outright, with a linear whole-case screen and a bridge screen. Where the new tie must land, and why shared tree-to-tree ties mostly fail the AC check. |
| [fixing-plant-islands-from-single-outages](methods/fixing-plant-islands-from-single-outages.md) | A topology-only screen for single outages that cut a plant off the grid. A pocket with units and load fails to balance; units only just trips. Four shapes, and the fix for each. |
| [handling-errors](methods/handling-errors.md) | What to do when something fails, sorted into fix it yourself, fix it and mention it, and stop and ask. |
| [how-to-analyze-results](methods/how-to-analyze-results.md) | Read the solar and wind CSVs a timestep run produces: the two-file naming, the 8-row metadata header, and the UTC timestamp conversion. |
| [ltc-regulation-checks](methods/ltc-regulation-checks.md) | Check which bus each LTC and switched shunt actually holds and how it targets its band: a regulator pointed at nothing, `XFRegTargetType = Middle`, and an LTC holding its LV side while the HV side floats. Re-point, don't write taps. |
| [new-device-contingency-aux](methods/new-device-contingency-aux.md) | Turn a list of devices into a contingency set plus an area-restricted violation filter, shipped as one `.aux` that loads without saving the case. |
| [powerworld-limitset-setdata](methods/powerworld-limitset-setdata.md) | Change PowerWorld's limit-monitoring thresholds. `SetData` on `LimitSet` fails with a missing-key-field error unless you supply the entire field row. |
| [preflight-powerworld](methods/preflight-powerworld.md) | Five checks in five seconds: can this machine drive PowerWorld from Python at all? Run it before writing any analysis code. |
| [ranking-new-devices-by-severity](methods/ranking-new-devices-by-severity.md) | Solve a new-device contingency set and answer which new device is worst. Produces one `devices.csv`, ranked worst first. |
| [reading-violationctg](methods/reading-violationctg.md) | Get which contingency caused which violation, keyed by `CTGLabel`, by reading `ViolationCTG` after `CTGSolveAll()`. |
| [reducing-a-contingency-set](methods/reducing-a-contingency-set.md) | `CTGSkip` and `Delete` do different jobs and get confused for each other. `CTGSkip` partitions a set without shrinking it. |
| [remediating-base-case-violations](methods/remediating-base-case-violations.md) | The cheapest-first ladder for intact-case voltage and thermal violations, priced in devices added: taps and generator setpoints first, one device at the worst bus, a rating increase before a parallel circuit. |
| [remediating-n1-contingency-violations](methods/remediating-n1-contingency-violations.md) | The loop that drives post-contingency violations to zero or to an explained residue: rank elements, not contingencies, spend the cheapest action, re-sweep. Plus the eight-step playbook for the last residue. |
| [removing-empty-buses](methods/removing-empty-buses.md) | Find and delete dead-end voltage levels that carry nothing, without moving the power flow, when they inflate islanding and N-1 counts. Two shapes look empty and must stay. |
| [reviewing-a-design](methods/reviewing-a-design.md) | A reviewer's checklist for a transmission design submitted as a modified case: diff it against the base, then check served load with each new device out, a single transformer behind redundant lines, stacked corridors, lines across two kV levels, per-mile X entered as the total, and X below R. Report only, never edit. |
| [save-powerworld-case](methods/save-powerworld-case.md) | Write an open case back to disk. The COM `SaveCase` returns success and writes no file, so use the script form and check the file exists. |
| [teamoverbyeweather-client](methods/teamoverbyeweather-client.md) | Download a weather dataset, crop it to a region and a time window, and get `.pww` files ready for PowerWorld. Pure Python, no PowerWorld licence needed. |
| [timestep-simulation-setup](methods/timestep-simulation-setup.md) | Drive TimeStep to turn `.pww` files into hourly generation CSVs, including the per-generator prerequisites a case must satisfy first. |
| [timestep-dispatch-into-design-bands](methods/timestep-dispatch-into-design-bands.md) | Dispatch wind and solar unit by unit from a time-step run, and scale that pattern into a scenario's design bands when no real hour fits. The clock trap, water-filling, batteries, and AGC. |
| [violation-network-map](methods/violation-network-map.md) | Put the violations on an interactive map: the voltage page (problem list, one-lines, reactive balance, measured fixes with Before/After) and the radial-ties page (bridges whose one outage islands load, a suggested tie per tree). Built by the `violation-map` skill. |
| [visualize-renewable-output](methods/visualize-renewable-output.md) | Plot the timestep CSVs: fleet totals over time, per-ISO and per-state breakdowns, capacity-factor curves, and peak and trough hours. |
| [zone-load-multiplier-trap](methods/zone-load-multiplier-trap.md) | A zone or area load multiplier scales a new load's `LoadSMW` without warning, so 600 MW written draws 783 MW. Divide by the multiplier, then assert the solved `LoadMW`. Load on an islanded bus also drops out of the totals silently. |

## Concepts — what a thing is

Background. Read when a method references something you do not recognise.

| Page | What it covers |
|---|---|
| [agc-participation-factors](concepts/agc-participation-factors.md) | Who covers lost MW in a contingency: the AGC flag, the participation factor and the make-up power option. AGC on with every factor at 0 changes nothing, so the slack still takes it all. |
| [aggregate-clauses-cannot-bound-one-row](concepts/aggregate-clauses-cannot-bound-one-row.md) | A "no worse than before" test built from counts, maxima and sums lets one element get much worse. Add a per-element clause, and refuse an empty or vanished row. |
| [auto-pfw-scripts](concepts/auto-pfw-scripts.md) | The `Auto_PFW` scripts attach PFW weather models to wind and solar units so TimeStep produces MW. They skip a wind unit with no class without a warning, so re-count coverage on the copy they save. |
| [aux-only-powerworld](concepts/aux-only-powerworld.md) | A `.aux` file is a complete program: open a case, edit it, solve it, export CSVs, write the log and exit, with no Python and no SimAuto call at all. Field names must come from esapp's schema or PowerWorld's own field export, never from the *Auxiliary File Format* manual, which has no per-object field catalog. |
| [case-impedance-completeness](concepts/case-impedance-completeness.md) | A case can solve DC power flow for years while carrying no resistance and no line charging at all. DC reads only `X`, so nothing ever complains. |
| [case-to-case-device-transplant](concepts/case-to-case-device-transplant.md) | Copy a set of devices from one case into another without rebuilding the chain that produced them, by carving a filtered AUX out of the source case. |
| [copper-plate](concepts/copper-plate.md) | Strip every branch, load and shunt and leave a single slack bus, so generators dispatch to total system load with no transmission constraints. |
| [esapp-environment](concepts/esapp-environment.md) | What `esapp` is, what it needs to run, and how the `PowerWorld` entry point, the bracket interface and the `SAW` wrapper fit together. |
| [esapp-script-command-wrappers](concepts/esapp-script-command-wrappers.md) | Why you call `pw.esa.TimeStepDoRun()` rather than `RunScriptCommand("TimeStepDoRun;")`, and the roughly 41 actions where no wrapper exists. |
| [esapp](concepts/esapp.md) | The full API map for `esapp`: top-level imports, architecture, and what the package can actually do. |
| [gic](concepts/gic.md) | Geomagnetically induced currents: what they do to transformers during a geomagnetic disturbance, and what PowerWorld models. |
| [glossary](concepts/glossary.md) | Every acronym and piece of jargon this kit uses, defined once. Read the confused-pairs section even if you skip the rest. PWW versus PFW has cost people whole afternoons. |
| [gsu-outages-in-n1](concepts/gsu-outages-in-n1.md) | Double every single generator step-up or leave GSU outages out of N-1: measured, both fail on the same transmission outages. What each costs, and the slack-behind-one-GSU case. |
| [gsu-tap-vs-generator-voltage-control](concepts/gsu-tap-vs-generator-voltage-control.md) | The planning convention: a fixed GSU tap, the generator regulates one bus, and one automatic controller per regulated bus. How to pick the fixed tap, and what stays open. |
| [lodf](concepts/lodf.md) | Every branch's post-outage flow for every single-branch outage, from one matrix factorization. Measured live, it gives the same answer as DC contingency analysis, not an approximation of it. |
| [one-device-per-voltage-pocket](concepts/one-device-per-voltage-pocket.md) | Post-contingency undervoltage clusters by driving outage. Buses that fail together under one outage take one device at the worst bus, not one device each. |
| [opf-preconditions](concepts/opf-preconditions.md) | LP OPF needs three independent preconditions at once (an area under `BGAGC = "OPF"`, AGC-able generators, and a real cost model). Missing any one is a fatal error rather than a degraded solve. Synthetic cases routinely ship with all three off. |
| [parallel-contingency-solve](concepts/parallel-contingency-solve.md) | PowerWorld's own distributed `CTGSolveAll` never spawns workers here and silently degrades to serial. Split the contingency set across N processes instead. |
| [per-unit-basis-discipline](concepts/per-unit-basis-discipline.md) | A per-unit value is meaningless without the base it was normalized against, and it looks like a plain scalar, so it gets copied between sources and summed. |
| [powerworld-inertia-and-cost-data](concepts/powerworld-inertia-and-cost-data.md) | Four case-data facts to know before touching generator inertia or cost, starting with `Gen.TSH` being H on a 100 MVA system base rather than the unit's own. |
| [powerworld-script-transfer](concepts/powerworld-script-transfer.md) | Simulator 25 beta watches a directory and executes any `.aux` dropped in it, writing the log back to a text file. It is a channel into PowerWorld that needs no COM, no SimAuto and no SimAuto licence. Undocumented in the manual. |
| [powerworld-simauto](concepts/powerworld-simauto.md) | The Windows COM server every PowerWorld Python script ultimately talks to, its SAW mixin architecture, and the verified raw COM calls. |
| [pww-data](concepts/pww-data.md) | The PWW binary weather format: gridded variables packed as uint8 per timestep and grid point, with 255 as the NaN sentinel. |
| [sizing-a-device-whose-impedance-determines-its-own-flow](concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md) | Sizing a transformer against its own converged flow under-sizes it, because a small unit is a high impedance and flow routes around it. Floor the size with the load it must serve. |
| [timestep-simulation](concepts/timestep-simulation.md) | What a timestep simulation is here: hourly renewable output computed quasi-statically from weather data. It is not a transient-stability study. |
| [timestep-workflow](concepts/timestep-workflow.md) | The whole chain from a `.pww` file to per-generator hourly CSVs, in the order PowerWorld requires it. |
| [unloaded-ehv-stub-overvoltage](concepts/unloaded-ehv-stub-overvoltage.md) | A lightly loaded EHV dead end rises at its open end on its own line charging and islands on one outage. A tie into a substation with absorbing room fixes both; a reactor fixes only the voltage. |
| [version-requirements](concepts/version-requirements.md) | Which Simulator version you need and what this kit was verified against: build 24.2026.7.22, with 13 of 14 feature areas confirmed working. |

## References — the heavy code layer

Exact backend mechanics. Open ONLY when writing code, and only the one you need.

| Page | What it covers |
|---|---|
| [aux-script-commands](references/aux-script-commands.md) | Which SCRIPT command does a job, organized by task. Argument lists and exact syntax for study commands are in [powerworld-study-commands](references/powerworld-study-commands.md). |
| [powerworld-study-options](references/powerworld-study-options.md) | **Start here to change how a study runs.** Per study (power flow, DC, N-1, OPF, SCOPF, sensitivities, ATC, PV/QV, scaling, islands, time step, weather): the option object and command that control it, key fields tagged verified / documented / schema-only, and the silent behaviours. |
| [powerworld-option-objects-v25](references/powerworld-option-objects-v25.md) | Generated: every field of all 32 `*_Options` objects from the Simulator 25 field export, with writability and PowerWorld's descriptions. |
| [powerworld-study-commands](references/powerworld-study-commands.md) | Every study SCRIPT command with its parameters and defaults, how options are written in aux, and 29 silent behaviours. |
| [esapp-package-backend](references/esapp-package-backend.md) | esapp internals: bracket-interface mechanics, SAW mixin composition, the component-generation pipeline, the schema model, and the exception hierarchy. |
| [esapp-schema-reference](references/esapp-schema-reference.md) | The exact key fields and command names for writing esapp code. Open it when a read-modify-write has to round-trip. |
| [time-step-simulation-backend](references/time-step-simulation-backend.md) | The timestep worker's PowerWorld call sequence, its generator field list, and the CSV post-processing that skips the 8 header rows. |

## Skills and agents

| File | What it does |
|---|---|
| [powerworld](skills/powerworld/SKILL.md) | The main HiveMind skill: fires on any PowerWorld, esapp or SimAuto task and sends you to the page that covers it before you write code. |
| [schema-lookup](skills/schema-lookup/SKILL.md) | Says which object, field or SCRIPT command to use, from the Simulator 25 field export, and quotes what HiveMind's study pages say about it. |
| [case-audit](skills/case-audit/SKILL.md) | The HiveMind skill that checks a case read-only and says whether it is READY for a base, N-1 monitoring, TimeStep or OPF study, with a case summary and a data lint. |
| [violation-map](skills/violation-map/SKILL.md) | The HiveMind skill that builds an interactive map of out-of-band voltages or of the radial trees one outage can island, with candidate fixes measured. |
| [knowledge-base-page](skills/knowledge-base-page/SKILL.md) | The HiveMind skill that writes or edits a page in this knowledge base in the house schema, then checks the pages still hang together. |
| [case-auditor](agents/case-auditor.md) | The HiveMind subagent that runs the case-audit skill and triages every finding. |
| [schema-librarian](agents/schema-librarian.md) | The HiveMind subagent that answers field and command questions through schema-lookup and never opens a case. |

## Browse by topic

The same pages grouped by what you are doing. Each page's `topic:` field decides its group.

### Power flow & OPF

- [copper-plate](concepts/copper-plate.md): Strip every branch, load and shunt and leave a single slack bus, so generators dispatch to total system load with no transmission constraints.
- [gic](concepts/gic.md): Geomagnetically induced currents: what they do to transformers during a geomagnetic disturbance, and what PowerWorld models.
- [gsu-tap-vs-generator-voltage-control](concepts/gsu-tap-vs-generator-voltage-control.md): The planning convention: a fixed GSU tap, the generator regulates one bus, and one automatic controller per regulated bus.
- [opf-preconditions](concepts/opf-preconditions.md): LP OPF needs three independent preconditions at once (an area under `BGAGC = "OPF"`, AGC-able generators, and a real cost model). Missing any one is a fatal error rather than a degraded solve.
- [applying-a-dispatch-to-a-case](methods/applying-a-dispatch-to-a-case.md): Turn a MW-per-generator dispatch into a runnable scenario case.
- [power-flow-and-sensitivities](demos/power-flow-and-sensitivities.md): AC and DC solves plus LODF and PTDF, including the `1e8` sentinel that makes LODF output look insane and a PTDF failure whose obvious fix fails the same way.

### Contingency (N-1)

- [agc-participation-factors](concepts/agc-participation-factors.md): Who covers lost MW in a contingency: the AGC flag, the participation factor and the make-up power option.
- [aggregate-clauses-cannot-bound-one-row](concepts/aggregate-clauses-cannot-bound-one-row.md): A "no worse than before" test built from counts, maxima and sums lets one element get much worse.
- [gsu-outages-in-n1](concepts/gsu-outages-in-n1.md): Double every single generator step-up or leave GSU outages out of N-1.
- [lodf](concepts/lodf.md): Every branch's post-outage flow for every single-branch outage, from one matrix factorization.
- [one-device-per-voltage-pocket](concepts/one-device-per-voltage-pocket.md): Buses that fail together under one outage take one device at the worst bus, not one device each.
- [parallel-contingency-solve](concepts/parallel-contingency-solve.md): PowerWorld's own distributed `CTGSolveAll` never spawns workers here and silently degrades to serial.
- [diagnosing-a-non-converging-contingency](methods/diagnosing-a-non-converging-contingency.md): Why an N-1 outage did not solve: an island stopped at RESERVE LIMITS, a voltage collapse, a bad Newton start or a harness bug, told apart in four probes.
- [emergency-ratings-for-a-synthetic-case](methods/emergency-ratings-for-a-synthetic-case.md): Give every branch its own Rate B and C from a reviewer's per-class statistics instead of one flat ratio: a per-branch draw in 0.5–1.5× the class mean, `A <= B <= C`, then point contingency monitoring at Rate B and rerun N-1.
- [finding-and-fixing-radial-by-n1-pockets](methods/finding-and-fixing-radial-by-n1-pockets.md): Find pockets that one outage leaves on a long, weak survivor, or islands outright, with a linear whole-case screen and a bridge screen.
- [fixing-plant-islands-from-single-outages](methods/fixing-plant-islands-from-single-outages.md): A topology-only screen for single outages that cut a plant off the grid.
- [new-device-contingency-aux](methods/new-device-contingency-aux.md): Turn a list of devices into a contingency set plus an area-restricted violation filter, shipped as one `.aux` that loads without saving the case.
- [powerworld-limitset-setdata](methods/powerworld-limitset-setdata.md): Change PowerWorld's limit-monitoring thresholds.
- [ranking-new-devices-by-severity](methods/ranking-new-devices-by-severity.md): Solve a new-device contingency set and answer which new device is worst.
- [reading-violationctg](methods/reading-violationctg.md): Get which contingency caused which violation, keyed by `CTGLabel`, by reading `ViolationCTG` after `CTGSolveAll()`.
- [reducing-a-contingency-set](methods/reducing-a-contingency-set.md): `CTGSkip` and `Delete` do different jobs and get confused for each other.
- [remediating-n1-contingency-violations](methods/remediating-n1-contingency-violations.md): The loop that drives post-contingency violations to zero or to an explained residue: rank elements, not contingencies, spend the cheapest action, re-sweep.
- [violation-network-map](methods/violation-network-map.md): Put the violations on an interactive map: the voltage page (problem list, one-lines, reactive balance, measured fixes with Before/After) and the radial-ties page (bridges whose one outage islands load, a suggested tie per tree).
- [contingency-and-aux](demos/contingency-and-aux.md): Run N-1 from nothing, then write a filter and contingency `.aux` from the result and load it back.
- [violation-remediation](demos/violation-remediation.md): The full study: find 12 N-1 violations, work out why they happen, test five reinforcements, and rank them by measured effect.

### TimeStep & weather

- [auto-pfw-scripts](concepts/auto-pfw-scripts.md): The `Auto_PFW` scripts attach PFW weather models to wind and solar units so TimeStep produces MW.
- [pww-data](concepts/pww-data.md): The PWW binary weather format: gridded variables packed as uint8 per timestep and grid point, with 255 as the NaN sentinel.
- [timestep-simulation](concepts/timestep-simulation.md): What a timestep simulation is here: hourly renewable output computed quasi-statically from weather data.
- [timestep-workflow](concepts/timestep-workflow.md): The whole chain from a `.pww` file to per-generator hourly CSVs, in the order PowerWorld requires it.
- [how-to-analyze-results](methods/how-to-analyze-results.md): Read the solar and wind CSVs a timestep run produces: the two-file naming, the 8-row metadata header, and the UTC timestamp conversion.
- [teamoverbyeweather-client](methods/teamoverbyeweather-client.md): Download a weather dataset, crop it to a region and a time window, and get `.pww` files ready for PowerWorld.
- [timestep-simulation-setup](methods/timestep-simulation-setup.md): Drive TimeStep to turn `.pww` files into hourly generation CSVs, including the per-generator prerequisites a case must satisfy first.
- [timestep-dispatch-into-design-bands](methods/timestep-dispatch-into-design-bands.md): Dispatch wind and solar unit by unit from a time-step run, and scale that pattern into a scenario's design bands when no real hour fits.
- [visualize-renewable-output](methods/visualize-renewable-output.md): Plot the timestep CSVs: fleet totals over time, per-ISO and per-state breakdowns, capacity-factor curves, and peak and trough hours.
- [timestep-and-pfw](demos/timestep-and-pfw.md): Turn a weather file into hourly wind and solar output, starting with the check that decides whether the case can do it at all: do its renewable units carry PFW model strings?
- [time-step-simulation-backend](references/time-step-simulation-backend.md): The timestep worker's PowerWorld call sequence, its generator field list, and the CSV post-processing that skips the 8 header rows.

### Design & planning

- [case-to-case-device-transplant](concepts/case-to-case-device-transplant.md): Copy a set of devices from one case into another without rebuilding the chain that produced them, by carving a filtered AUX out of the source case.
- [sizing-a-device-whose-impedance-determines-its-own-flow](concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md): Sizing a transformer against its own converged flow under-sizes it, because a small unit is a high impedance and flow routes around it.
- [unloaded-ehv-stub-overvoltage](concepts/unloaded-ehv-stub-overvoltage.md): A lightly loaded EHV dead end rises at its open end on its own line charging and islands on one outage.
- [adding-devices-esapp](methods/adding-devices-esapp.md): Create buses, branches and loads in an open case, then solve a DC OPF and screen N-1.
- [remediating-base-case-violations](methods/remediating-base-case-violations.md): The cheapest-first ladder for intact-case voltage and thermal violations, priced in devices added: taps and generator setpoints first, one device at the worst bus, a rating increase before a parallel circuit.
- [reviewing-a-design](methods/reviewing-a-design.md): A reviewer's checklist for a transmission design submitted as a modified case: diff it against the base, then check served load with each new device out, a single transformer behind redundant lines, stacked corridors, lines across two kV levels, per-mile X entered as the total, and X below R.
- [adding-a-device](demos/adding-a-device.md): Three attempts that reported success and created nothing, then the fix.
- [comparing-planning-cases](demos/comparing-planning-cases.md): Diff a 2016 and a 2024 case to find what the plan builds (691 new branches, 199 new generators), then solve a contingency set for only the new devices.

### Case data & audit

- [case-impedance-completeness](concepts/case-impedance-completeness.md): A case can solve DC power flow for years while carrying no resistance and no line charging at all.
- [per-unit-basis-discipline](concepts/per-unit-basis-discipline.md): A per-unit value is meaningless without the base it was normalized against, and it looks like a plain scalar, so it gets copied between sources and summed.
- [powerworld-inertia-and-cost-data](concepts/powerworld-inertia-and-cost-data.md): Four case-data facts to know before touching generator inertia or cost, starting with `Gen.TSH` being H on a 100 MVA system base rather than the unit's own.
- [case-data-lint](methods/case-data-lint.md): Find the data defects a case solves straight through: discrete shunts set off their steps, units below their minimum, placeholder or inverted limits, missing emergency ratings, negative reactance, unnamed buses, stray islands and slacks, odd nominal kV.
- [converting-lines-to-transformers](methods/converting-lines-to-transformers.md): Reclassify branches as transformers when a case models every branch as a line.
- [ltc-regulation-checks](methods/ltc-regulation-checks.md): Check which bus each LTC and switched shunt actually holds and how it targets its band: a regulator pointed at nothing, `XFRegTargetType = Middle`, and an LTC holding its LV side while the HV side floats.
- [removing-empty-buses](methods/removing-empty-buses.md): Find and delete dead-end voltage levels that carry nothing, without moving the power flow, when they inflate islanding and N-1 counts.
- [zone-load-multiplier-trap](methods/zone-load-multiplier-trap.md): A zone or area load multiplier scales a new load's `LoadSMW` without warning, so 600 MW written draws 783 MW.

### Saving & scripting

- [aux-only-powerworld](concepts/aux-only-powerworld.md): A `.aux` file is a complete program: open a case, edit it, solve it, export CSVs, write the log and exit, with no Python and no SimAuto call at all.
- [esapp-environment](concepts/esapp-environment.md): What `esapp` is, what it needs to run, and how the `PowerWorld` entry point, the bracket interface and the `SAW` wrapper fit together.
- [esapp-script-command-wrappers](concepts/esapp-script-command-wrappers.md): Why you call `pw.esa.TimeStepDoRun()` rather than `RunScriptCommand("TimeStepDoRun;")`, and the roughly 41 actions where no wrapper exists.
- [esapp](concepts/esapp.md): The full API map for `esapp`: top-level imports, architecture, and what the package can actually do.
- [glossary](concepts/glossary.md): Every acronym and piece of jargon HiveMind uses, defined once.
- [powerworld-script-transfer](concepts/powerworld-script-transfer.md): Simulator 25 beta watches a directory and executes any `.aux` dropped in it, writing the log back to a text file. It is a channel into PowerWorld that needs no COM, no SimAuto and no SimAuto licence.
- [powerworld-simauto](concepts/powerworld-simauto.md): The Windows COM server every PowerWorld Python script ultimately talks to, its SAW mixin architecture, and the verified raw COM calls.
- [version-requirements](concepts/version-requirements.md): Which Simulator version you need and what HiveMind was verified against: build 24.2026.7.22, with 13 of 14 feature areas confirmed working.
- [aux-file-mode](methods/aux-file-mode.md): PowerWorld and LLM interaction through files: the agent writes `.aux`, you drop it into a watched folder, results come back as CSVs.
- [esapp-overview](methods/esapp-overview.md): The starting page: open a case, read and write data, solve power flow, and use `snapshot()` to experiment without damaging anything.
- [handling-errors](methods/handling-errors.md): What to do when something fails, sorted into fix it yourself, fix it and mention it, and stop and ask.
- [preflight-powerworld](methods/preflight-powerworld.md): Five checks in five seconds: can this machine drive PowerWorld from Python at all?
- [save-powerworld-case](methods/save-powerworld-case.md): Write an open case back to disk; the COM `SaveCase` returns success and writes no file, so use the script form and check the file exists.
- [aux-file-cookbook](demos/aux-file-cookbook.md): Four recipes for working through `.aux` files rather than Python: turn the channel on, prove it, inventory a case, take a bus out and measure it.
- [start-here](demos/start-here.md): The one-line prompts to open with, and worked runs on the public synthetic Synth40 case (37 buses) with every failure left in on purpose.
- [aux-script-commands](references/aux-script-commands.md): Which SCRIPT command does a job, organized by task.
- [esapp-package-backend](references/esapp-package-backend.md): esapp internals: bracket-interface mechanics, SAW mixin composition, the component-generation pipeline, the schema model, and the exception hierarchy.
- [esapp-schema-reference](references/esapp-schema-reference.md): The exact key fields and command names for writing esapp code.
- [powerworld-option-objects-v25](references/powerworld-option-objects-v25.md): Generated: every field of all 32 `*_Options` objects from the Simulator 25 field export, with writability and PowerWorld's descriptions.
- [powerworld-study-commands](references/powerworld-study-commands.md): Every study SCRIPT command with its parameters and defaults, how options are written in aux, and 29 silent behaviours.
- [powerworld-study-options](references/powerworld-study-options.md): **Start here to change how a study runs.** Per study (power flow, DC, N-1, OPF, SCOPF, sensitivities, ATC, PV/QV, scaling, islands, time step, weather): the option object and command that control it, key fields tagged verified / documented / schema-only, and the silent behaviours.

### Agents

- [case-audit](skills/case-audit/SKILL.md): The HiveMind skill that checks a case read-only and says whether it is READY for a base, N-1 monitoring, TimeStep or OPF study, with a case summary and a data lint.
- [knowledge-base-page](skills/knowledge-base-page/SKILL.md): The HiveMind skill that writes or edits a page in this knowledge base in the house schema, then checks the pages still hang together.
- [powerworld](skills/powerworld/SKILL.md): The main HiveMind skill: fires on any PowerWorld, esapp or SimAuto task and sends you to the page that covers it before you write code.
- [schema-lookup](skills/schema-lookup/SKILL.md): Says which object, field or SCRIPT command to use, from the Simulator 25 field export, and quotes what HiveMind's study pages say about it.
- [violation-map](skills/violation-map/SKILL.md): The HiveMind skill that builds an interactive map of out-of-band voltages or of the radial trees one outage can island, with candidate fixes measured.
- [case-auditor](agents/case-auditor.md): The HiveMind subagent that runs the case-audit skill and triages every finding.
- [schema-librarian](agents/schema-librarian.md): The HiveMind subagent that answers field and command questions through schema-lookup and never opens a case.
