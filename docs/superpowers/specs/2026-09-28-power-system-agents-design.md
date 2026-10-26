# Power-system agents for PoWerHiveMind — design

Date: 2026-09-28. Status: design approved in conversation, awaiting review of this written spec.
Revised 2026-09-29 with the decisions from a review of the agent drafts.

## 1. Goal

Give anyone who installs PoWerHiveMind a small team of agents that audit a case, run
steady-state studies with the user's own preferences, map and compare the engineer's designs on
the full N-1, and answer "which object and field?" questions — so an open-ended request ("the bus is at 1.06, what fixes it?") is worked on
real numbers instead of guesses.

**Audience:** every user of the kit, including its author. Everything ships inside the kit and is
self-contained: no imports from any private research repository, worked examples and tests on
public synthetic grids only.

**Scope:** steady state only. Transient stability and GIC are out.

## 2. Design principles

1. **Methods are knowledge; agents are roles.** A study method (AC power flow, DC, N-1, OPF,
   SCOPF, time step) is a kit page plus an engine script. Adding a method never adds an agent.
2. **An agent exists only when a skill cannot do the job:** it needs a **fresh context** (output too
   noisy for the main session), **different permissions** (must never write the case), or
   **independence** (must not grade its own work).
3. **Deterministic checks live in code, not in prompts.** An agent reads findings and judges them;
   it does not re-derive a rule on each run.
4. **Judgment happens once, up front, where the user can see it.** Execution is mechanical and
   recorded, so the same request always reproduces the same numbers.
5. **Every PowerWorld write is read back.** PowerWorld reports success on writes that change
   nothing; a write that did not stick fails the run.
6. **Plain English in everything the engineer reads.** Every agent's and skill's Output format
   carries the kit's own short *Plain English* rule (see `docs/agents/`); internal sections stay
   technical.
7. **Plain requests in.** Every agent works from what the engineer says in their own words. It works
   out the study, profile, files and settings itself, and never asks for or depends on an internal
   id, flag or format. Test prompts are written the way an engineer talks. Any scaffolding a test
   needs lives in the test harness, never in the prompt. This also applies to every agent added
   later.

## 3. The team

| role | kind | one-line job |
|---|---|---|
| engineer | the user + the main session with the `powerworld` skill | frames the problem, forms hypotheses, chooses candidates, decides |
| case-auditor | subagent, read-only | "is this case sane, and can it run study X?" |
| study-runner | subagent | turns preferences into settings, runs studies exactly, summarises |
| network-visualizer | subagent | maps the network around a site, measures the engineer's design and its own challengers on identical settings, and compares them side by side |
| schema-librarian | subagent, cheap model, read-only | "which object, field, command — and how sure?" |

There is no separate planner agent: power-system judgment belongs in the context the user is
talking to.

**Plan pictures — a main-session skill, not an agent** (`docs/agents/plan-pictures.md`). At every
approval gate — the runner's settings approval, the visualizer's challenger list, the supervisor's
next round, and a written plan before work starts — the plan is shown as a picture before the
approval question: a **swimlane** by default (lanes You / Agent / Script (fixed code, no AI) /
PowerWorld, numbered steps, safety checks drawn inline with "fails → stop + tell you"), and a
**flowchart** of what can stop the run as the second view. Data-flow and timeline views were
considered and rejected. **Hard rule:** the picture is generated from `plan.json`, which the **engine** writes from
the manifest it will run (`study.py plan`), never from prose, the agent's summary, or a step list an
agent typed, so it cannot show a step the run will not take. `plan.json` records the hash of each
file it was drawn from; a picture whose source has changed since is stale and is not shown
(revised 2026-09-30: an agent-written `steps` array could disagree with what runs, and a count
check against that same array could never fail). Every study gate has one: the runner's settings
approval (§5), the visualizer's challenger list (`study.py plan --designs challengers.json`, §6), and
the supervisor's next round; a written plan before work starts uses the plan markdown file's
numbered task list. The picture's closing line is the gate's only approval question. It always writes a
**Mermaid** swimlane file (portable to GitHub, Obsidian, Codex, Gemini), plus a styled Claude page
for Claude Code users built from the same data. Each engineer can set their own default view per
gate in the kit's user config, as a `plan_pictures.default_view` map `{gate: swimlane|flowchart}`;
with no entry, the default is the swimlane.

**Portability:** subagents are a Claude Code feature. Every role is therefore a **skill plus an
engine** first; the skill carries the commands, and the agent file carries the **role contract**
(responsible / not responsible, protocol, failure modes, examples, checklist — revised 2026-09-28,
see `docs/agents/`). Codex and Gemini users of the kit get the skills and engines and lose only the
context isolation.

## 4. case-auditor

**Triggers:** "review this case", "scan the case", "can I run time step / OPF / N-1 on this",
"is this case ready for X".

**Engine** (`skills/case-audit/engine/`, esapp):
- `audit.py --case <pwb> --profiles base,timestep --out <dir>` → `findings.json` + `findings.md`.
- A **rule** is one small function: id, profile, severity (*Stops the study* / *Worth a look* / *FYI*), fields
  read, the check, a one-line why, the kit page that explains it, and a fix pointer — either a kit
  page or an external handoff.
- Findings carry the object's key fields so each points at exact objects.
- **Read-only, enforced by a test:** the engine may solve N-0 in memory but never calls
  `SaveCase` or writes a case. An AST test fails the build otherwise.

**v1 profiles** (every rule backed by a kit page; the pages for the four LTC, shunt and stub
rules are written in Plan 2, and those rules ship in v1):

| profile | checks |
|---|---|
| base | N-0 (AC) converges; not a DC-only skeleton (`dc_skeleton`); no unit above its rating after the solve (`gen_over_nameplate`: stops the study only past max(1 % of rating, 5 MW), a starting value measured in Plan 2; a smaller overshoot is Worth a look with its MW); switched shunt or LTC regulating nothing or an out-of-service bus; LTC `XFRegTargetType = Middle`; LTC regulating its low-voltage side while its high side is out of band (`ltc_regulates_lv_side`); lightly loaded EHV radial stubs; holds no `ViolationCTG` rows from an earlier run (`stale_ctg_results`, FYI — do not read them) |
| monitoring (reported with base) | something is monitored (`mon.nothing_monitored`); the monitored footprint as the case holds it (`mon.footprint`); the normal and contingency rate sets in use carry ratings (`mon.rate_set_empty`); which rate sets carry values (`mon.rate_sets_populated`); buses with their own voltage limits (`mon.bus_limit_overrides`) |
| summary (every audit; facts, not findings) | load MW/Mvar; generation MW/Mvar and losses; headroom on online dispatchable units (wind/solar "weather-limited"); a fuel-type table keyed by the case's own `GenFuelType` code (units online/total, installed MW, output MW, share, headroom); online Mvar range; shunt count, Mvar now (`SSAMVR`), capacitive/inductive capacity (`SSMaxMVR`/`SSMinMVR`); size (buses, branches, transformers, areas, zones, kV levels). "Give me a summary" runs `base` and leads with these tables |
| timestep | renewables have `GenFuelType` WND/SUN, a PFW model string, valid Lat/Lon; for each wind unit missing a model, its wind class (`CustomInteger:1` 1–4 or `GenUnitType` W1–W4), because `Auto_PFW` silently skips a unit with neither; the `.pww` weather file given with the request covers the units (`ts.pww_footprint`) — no file given → an FYI line, not a blocker. TimeStep runs with any number of PFW models, so missing models, lat/lon and coverage **never stop it**. They are Worth a look, stated as what the run will do ("84 of 87 renewables will follow the weather; 3 read 0 MW, 410 MW, 1.4%: bus … unit …") |
| opf | an area on `BGAGC = "OPF"`; AGC-able gens; `GenCostModel` ≠ None with `GenCostCurvePoints > 0` and `GenMCost > 0` |

The weather file is an **input** given with the request. The auditor is a subagent: it returns,
it does not converse, so it cannot ask for the file mid-run.

Deferred: `n1` profile (with the runner's coverage guard), `transient` (out of scope).

**Handoffs for data the kit does not own.** The auditor detects; it never fabricates. Missing PFW
models link to the `Auto_PFW` scripts (EIA-860 data the kit does not
carry), and the user re-audits the returned case — which catches units the insertion silently
skipped. Missing cost curves are reported as data to be sourced, never set to a default.

**Agent:** maps the question to profiles, runs the engine, triages each finding as *Broken /
Probably on purpose / Your call*, and returns **READY / NOT READY for <study>**, the blocker table
and the handoffs. The raw findings stay in the file.

## 5. study-runner

**Phase 1 — configure (agentic).** The user's request in plain words becomes an **option delta**
using the schema-librarian and `references/powerworld-study-options.md`, shown before anything
runs:

```
Sim_Solution_Options.MaxItr               100 → 200
CTG_Options.Include                       NO  → YES
Sim_Solution_Options.EvalSolutionIsland   NO  → YES   (required for island reporting)
```

A preference with no matching field is reported as such, with the nearest real field — never
improvised.

Configure ends by writing `manifest.json` — the delta, case hash, commands, PowerWorld build,
alarms, and a `variants` array (the base plus the engineer's candidates) — then running
`study.py plan`, which writes `plan.json`: a `steps` array,
`[{"n": 1, "lane": "You|Agent|Script|PowerWorld", "label": "...", "checks": ["..."]}]`, one entry
per step the run will take, in order, with the safety checks that guard it, plus the hash of the
manifest it was drawn from. The agent never writes `steps`. Then it stops. The plan picture at this
gate is drawn from `plan.json`.

**Who approves.** A subagent never receives the engineer's words directly. They arrive relayed by
the main session, and the harness marks relayed messages as coming from another agent (found in the
2026-09-29 runner trial, where a relayed "run it" was refused twice). So the approval record is a
file that only the **main session** writes: on any clear go-ahead ("approved", "run it", "go",
"yes") it appends to `approval.json` beside the approved file
`{"file": "manifest.json" | "challengers.json", "hash": "<study.py hash output>", "at": "<ISO time>",
"said": "<the engineer's words>"}`. **The engine, not the agent, checks it:** it recomputes the
file's hash and refuses unless a matching entry exists. So an edit after approval — by anyone —
voids the approval and needs a fresh one. Agents never write `approval.json`. (Revised 2026-09-30:
the first version flipped a `status` field inside the manifest, which the agent itself writes, and
the engine checked only that word.)

**Two hashes.** `manifest_hash` covers the whole manifest and binds the approval.
`settings_hash` covers everything except `variants`: two designs are comparable when their
`settings_hash` and contingency count match, so challengers added later (§6) do not force the
engineer's design to be re-run.

**Phase 2 — execute (deterministic).**
- The approved `manifest.json` runs unchanged; workers and replays run it and record both hashes.
- **Every worker replays the manifest itself.** Each parallel worker opens its own PowerWorld
  instance; an option set in the parent does not exist in the workers.
- Each option: read, write, read back, record before and after in `results/<run>/readback.json`
  (never in the manifest). A mismatch fails the run.
- The original case is never saved; variants run on fresh copies with their aux delta loaded and
  the case **solved after `LoadAux`** before anything is read.

**v1 methods:** AC power flow, DC power flow, N-1 contingency, OPF, SCOPF, TimeStep.

- **TimeStep** (added 2026-09-30; sources `demos/timestep-and-pfw.md`,
  `methods/timestep-simulation-setup.md`, `concepts/timestep-workflow.md`, `concepts/pww-data.md`,
  `references/time-step-simulation-backend.md`, and the *Time-step simulation* table of
  `references/powerworld-study-commands.md`). Configure items: the case (run on a copy), the `.pww`
  file, the window (`Start`/`End` for `TimeStepLoadPWWRange(…, "Weather Only")`; the step is the
  file's own `SAMPLE_seconds`), the units (`GenFuelType` WND/SUN, `TimeDomainSelected` inside the
  `TIMESTEPSaveSelectedModifyStart/Finish` bracket), and the fields recorded each step
  (`TimeStepSaveFieldsSet(GEN, [GenMW], SELECTED)` by default). `TimeStepDoSinglePoint` runs first;
  then `TimeStepDoRun`, `TimeStepSaveResultsByTypeCSV`. At approval the runner states, in the case's
  terms, which renewables follow the weather (`TSPFWModelString` longer than 2 characters) and which
  read 0 MW, with IDs (at most 5; the rest in the file) and MW share; missing PFW models never block
  it. If `PauseOnError` or `PauseOnNoSolution` is YES, the approval says a pause looks like a stall.
  `SAMPLE_seconds = 0` means irregular steps (`concepts/pww-data.md`).
  **Slicing** (`slice_steps` in the manifest): `TimeStepDoRun` gives no documented progress signal, so
  with `"Weather Only"` — whose timestamps the kit treats as independent points
  (`concepts/timestep-workflow.md`) — the engine runs the window as `TimeStepDoRun(Start, End)`
  slices and counts between them. For any other solution type slicing is forced off and the window
  runs in one unbroken call, because PowerWorld's time-step controller time delays make results
  differ from a plain repeated solve. Each slice takes at most a third of the stall threshold, sized
  from the single-point time. Unsliced, the stall threshold is max(approved stall, 1.5 × the
  whole-run estimate), the estimate being single-point time × number of steps. Sliced results carry "run in <k> slices, not yet checked against one
  unbroken run" until the §10 slice test passes. **Not documented in the kit:** splitting one weather
  file across parallel workers (so one file runs as one chunk; the only documented parallel runner
  gives each worker a whole file), a setting that changes the step, and how solution types other
  than `"Weather Only"` change the results.
- **Long runs hand off.** A run expected to take longer than a few minutes — a time step over weeks,
  a full N-1 on a large case — is launched by the runner calling `study.py run` in the foreground;
  the engine detaches the run so it outlives the subagent and returns at once (never a background
  shell). The runner returns one line ("<study> started: <n> <unit>, about <t>. Watching:
  <heartbeat path>.") and ends; the main session's run-supervisor skill (§8a) watches it. A subagent
  cannot wait hours. Alarm thresholds go in the manifest's `alarms`, approved with the settings.

- **OPF and SCOPF need cost data** for the generators the study moves: real data in the case (the
  auditor's opf condition 3), or cost curves the engineer supplies themselves — even deliberately
  made-up ones, e.g. "flat $20/MWh". With the engineer's curves, every result is stamped "costs
  supplied by you, not from the case". Otherwise the runner refuses. It never invents costs and
  never switches a cost model on by itself. Area/super-area OPF control and `GenAGCAble` are
  switches the runner sets only for the areas and units the engineer approved. Naming an area turns
  on its OPF control only: units keep the case's `GenAGCAble`, and turning more on is a numbered
  decision at approval, default no (the 2026-09-30 SCOPF trial turned on every unit and widened
  monitoring from an area name).
- OPF: `InitializePrimalLP` then `SolvePrimalLP`, fail handler always given; results from
  `OPFSolutionSummary` (final cost is `LPOPFCostFunction:1`) and `Branch.LineLPUnenforceableMVA`.
- SCOPF: `SolveFullSCOPF(POWERFLOW|OPF)`; `SCOPFMaxOuterLoopItr` and the other `SCOPF*` options
  set through the configure phase like any other option. There is no inner-loop setting; a request
  for one is answered with `OPF_MaxLPIterations` as the nearest real field.
- **SCOPF ships in v1 without a dated end-to-end verification.** Every SCOPF result carries "not
  yet verified" until the first SCOPF run on a public case passes; that run is the verification,
  and its result is written back to `references/powerworld-study-options.md`.
- **DC OPF / DC SCOPF** use `SolvePowerFlow(DC)` to enter DC mode (never the `DCPFMode` flag alone)
  and `CTG_CalculationMethod = DC`; the AC re-solve guard applies afterwards.

**N-1 engine:** OS-process parallelism as described in `concepts/parallel-contingency-solve.md`,
re-implemented self-contained in the kit — contingency set split into chunks, one PowerWorld
instance per worker, `CTGSkip` partitioning, pure-Python merge. Serial or parallel is chosen by case
size (the fixed per-worker open cost dominates on small cases); worker count from CPU and RAM
headroom, not core count; every instance the runner opens is `.exit()`-ed.

**Monitoring default:** an N-1 monitors what the case's own setup monitors, unchanged, and every
result states it (e.g. "monitored: areas 1–3, 69 kV and up"). The runner never widens or narrows
it unless the engineer asks.

**Guards:**
- contingency coverage counted before a sweep (records vs lines plus two-winding transformers);
  `CTGAutoInsert` is not trusted without the count. A shorter list the engineer **chose** at
  configure (`contingency_set.source = "case list (engineer's choice)"`) runs, and every result is
  stamped "ran your list: <in_set> of <expected>; <n> not tested". The guard stops only a shortfall
  nobody chose, and it cannot be overridden after approval.
- DC only via `SolvePowerFlow(DC)`, followed by an AC re-solve before any AC result is read
- islands reported with all three checks — dropped (`LoadMW`/`GenMW`), energized
  (`CTG_Options.Include`), structural (`DetermineBranchesThatCreateIslands`) — gated on MW only
  when the pocket carries MW

**Post-processing:**
- violations from `ViolationCTG` with an explicit field list: thermal, voltage, unsolved, islands
- rankings both ways: worst outages, and most-hit elements (the kit's severity method)
- a reduced set (contingencies that produced a violation, plus an LODF near-miss screen) saved as
  aux for fast repeat runs — **never used for a verdict**. The near-miss loading threshold is a
  runner parameter, recorded in the manifest; its default is set in the implementation plan.

**Output:** `results/<run>/manifest.json`, `readback.json`, `scoreboard.csv`, `violations.csv`, `islands.csv`,
`rankings.csv`, `reduced_set.aux`, `REPORT.md`, and one status line to the engineer. For a time step
the engine writes `readback.json`, `timestep_summary.csv` (one row per step) and `REPORT.md` (wind and
solar average, lowest and highest with their times, the biggest drop, and the units that read 0 MW),
from which the runner's result and the supervisor's digest are written.

**Heartbeat (for run supervision, §8a).** While a run is live the engine rewrites
`results/<run>/heartbeat.json` at least once a minute: `study`, `state` (`running` / `finished` /
`failed`), progress as `done`, `total` and `unit` (`"outages"` or `"time steps"`), ETA, failed chunks
(meaningful only when the run is split into chunks; a time step on one weather file is one chunk),
unsolved so far (`null` on a time step: how a failed step is reported is not documented in the kit),
the count of `pwrworld.exe` processes the run owns, and `last_solve_at`, the time of the last
completed solve of either kind (an outage, or a slice of time steps). `updated` is written by a
heartbeat thread that runs independently of the solve, so a slow slice never reads as a dead run.
Written atomically (temp file,
then replace) so a reader never sees half a file. Watching a run means reading this file, never the
raw results.

## 6. network-visualizer

*Replaced the fix-reviewer on 2026-09-28.* A standalone reviewer grading AI-proposed fixes was the
awkward role; the useful one is the planner's question: *"here is my design — show me the network,
try it, try yours, and tell me which is better and why."*

**Triggers:** "visualize the network around …", "I want to connect this load / plant to that
substation — what happens?", "will it overload?", "compare my design with yours", "map the
violations".

1. **Map** with the existing `violation-map` engine, wrapped, not replaced. The opening view
   depends on case size (this reverses the 2026-09-28 focus-first rule):
   - a **light case** (under a bus-count cutoff) opens on the **whole case**, with the site
     highlighted, as an orientation view;
   - **zooming into a site** switches to that area **exclusively** — the rest is hidden, not just
     off-screen; boundary stubs stay for lines leaving it, and clicking a substation re-centres;
   - on a light case, a **"Back to whole case"** control returns from the zoomed area to the
     whole-case view;
   - a **"Render further network"** button grows the area by N more substation-hops per press;
   - a **heavy case** (over the cutoff, e.g. 100,000 buses) opens straight on the area view (the
     site plus the violation-map default (5 hops));
   - the **cutoff is measured in Plan 4**, by timing page build and render on public synthetic
     cases, and is a tunable bus-count default; the page states which mode it opened in and why;
   - what is drawn never limits what is computed: the N-1 stays full-system.
2. **Measure the engineer's design(s)** exactly as given: N-0, then the **full** N-1 through the
   study-runner engine with one settings manifest, and all three island checks.
3. **Propose challengers** only when asked, 1–3, cheapest first from the kit's action menu
   (setpoints and controls before new devices), each labelled as the agent's proposal. The list is
   written to `challengers.json`: a `designs` array,
   `[{"name": "...", "devices": "...", "changes": "what it changes, in plain words"}]`, and nothing
   else. The engine writes the measuring plan into `plan.json`
   (`study.py plan --manifest manifest.json --designs challengers.json`), each measuring step labelled with its design name.
   Challengers never enter the approved manifest; they run under its settings, so the
   `settings_hash` is unchanged and the engineer's design is not re-run. The agent returns
   "awaiting approval" before measuring any challenger; approval is an `approval.json` entry for
   `challengers.json` (§5).
4. **Compare** every design under the same `settings_hash` in one scoreboard, and render a map
   with a Before / Engineer / Challenger switch.

**Long measurements hand off** exactly as the runner's do (§5): the engine detaches, the agent
returns one start line and ends, the run-supervisor watches, and the agent is started again on the
results. Between gates the output folder is its memory.

**The page is local (2026-09-30, maintainer decision).** The Design Compare page is a local file for the agent
and the engineer. The agent never publishes it; sharing it with teammates is the engineer's call.
With no store behind a local file, Choose marks the card and copies "I pick <name>", and the pick
comes back through the chat. On a restricted case the agent says once that the page embeds bus
names, substation names and coordinates.

**Guards (they carry what the reviewer existed for):**
- every design — the engineer's and the agent's — is measured on identical settings and the full
  contingency set; a design measured on fewer outages is never compared with one measured on all;
- the comparison is engine numbers only; the agent states **where the engineer's design wins**, and
  never declares a winner without the table;
- the agent never edits the engineer's design, and never saves over the original case.

**Engine work this needs** (none of it exists yet): **the size-based opening rule on every view**
(whole case under the cutoff, area view over it, exclusive zoom, "Back to whole case", "Render
further network", and the measured cutoff) — the radial-ties page today draws the whole grid
whatever its size; the voltage page's hop slider tops out at 6, which caps "Render further
network", so that maximum must be raised; a *large-load* candidate kind (today: shunt,
line, setpoint edit); the **thermal view** `violation-map` lists as not built; and full-N-1
measurement of candidates through the study-runner engine (today the voltage page measures listed
outages and the radial page bridge outages only).

## 7. schema-librarian

Answers "which object, field, command?" in a few lines, with a confidence tag.

- **Sources, in order:** `references/powerworld-study-options.md` (curated, provenance-tagged) →
  `references/powerworld-option-objects-v25.md` and `powerworld-object-fields-v25.xlsx` (exact
  fields, keys, required fields, writability) → `references/powerworld-study-commands.md` (syntax).
- **Answer shape:** object, key fields, required fields, the field(s), a write snippet, and one of
  *verified on a live case / documented / schema-only*.
- **Used by** the user directly and by the runner's configure phase.
- Never touches a case; never states a field name absent from the export.

## 8. Walkthrough: "a bus sits at 1.06 pu, what fixes it?"

1. Engineer forms hypotheses from the kit's pages (line charging on a stub, an LTC holding the
   wrong side, a capacitor left on, a generator setpoint).
2. case-auditor (base profile) returns the neighbourhood diagnosis. Nothing changes.
3. Engineer turns it into candidates, cheapest first (zero-device setpoint and control fixes before
   new devices).
4. study-runner measures each candidate on a copy — N-0, then an N-1 screen on the survivors, a
   screen that narrows the list and is never used for a final answer — and returns a scoreboard.
5. network-visualizer maps the neighbourhood and puts the engineer's pick beside its own
   challenger on the full N-1, same settings, with a Before / Engineer / Challenger switch.
6. Engineer decides from the side-by-side scoreboard.

## 8a. Run supervision — a mode, not an agent

Long runs — a full N-1 on a large case, a TimeStep year — take hours. Today the engineer starts one,
trusts it, and finds out the next day whether it finished. Run supervision lets the engineer
follow a run from anywhere and make each round's decision from a phone.

It is a **mode of the main session** (a skill, `run-supervisor`), not a subagent: a subagent lives
only while its parent task runs, so it cannot wait hours for a reply or reach a phone. The main
session can — it runs the study in the background, wakes on meaningful heartbeat changes plus one
stall timer rather than polling, sends push notifications, and can be opened from the Claude
mobile or web app through Remote Control.

1. **Launch** the study-runner engine in the background with an approved manifest — or pick up a
   run the study-runner already started and handed off (§5, *Long runs hand off*): launch nothing,
   confirm that `approval.json` beside the heartbeat holds an entry matching the manifest's hash
   (`study.py hash --file manifest.json`), and watch.
2. **Watch** `heartbeat.json`. Wake only on a meaningful field change: `state` changes,
   `failed_chunks` grows, `unsolved` crosses its threshold, or `pwrworld_owned` exceeds
   workers + 1. Also run **one** stall timer that checks the age of `last_solve_at` (stall) and of
   `updated` (no heartbeat). Never a tight polling loop. The mechanism is the skill's watcher
   script (`watch.py`), started with the harness's background execution: it reads the heartbeat
   about once a minute and exits — waking the session — on a meaningful change or a stall timer.
   The session restarts it after each wake until the run ends.
3. **Alarm** (push notification) on: no progress for N minutes (default 15; on a time step, longer
   than one slice takes), any failed chunk (only on runs split into chunks), an unsolved count above
   the manifest's threshold (N-1), more `pwrworld.exe` processes than workers (a leak), the run
   failing, and the run finishing. Alarms speak in the run's own `unit`: outages or time steps.
4. **Round digest** when a round finishes: the scoreboard's headline, the worst offenders, islands,
   and two to four concrete next moves — e.g. "measure the three cheapest candidates on the worst
   corridor", "map the islanded pocket with the network-visualizer", "stop here". For a time step
   the digest says what the run produced — wind and solar average, lowest and highest with their
   times, the biggest drop, and the units that read 0 MW — not N-1 counts.
5. **The engineer decides** from the phone. The answer is a choice among the offered moves or free
   text; nothing proceeds without it — no auto-approval, same as every other gate in this design.
6. The chosen move launches the next round (study-runner or network-visualizer) and supervision
   continues.

**The run page (added 2026-09-30).** Every event is appended to `results/<run>/events.jsonl` and also
written as ONE document, `runs/<run_id>`, into a private Claude Artifact page, *Run Watch*
(`docs/agents/pages/run-watch.html`; it moves to the skill in Plan 5). The engineer glances at it on
a laptop or phone. It shows a status badge top right (running, stalled, failed, waiting for you,
finished), a one-line answer to "do I need to do anything?", progress, a run clock coloured by
state, and a timestamped timeline. The page listens to its database and redraws live. The supervisor
writes only on events, never on a timer; only the owner can write, and viewers read. It follows
the same privacy rule as notifications: no case identifiers. **The page follows the run, not the
watch:** every event from launch to close is written, including a failed launch, a rerun, or a
result returned inline between hand-offs (found in the 2026-09-30 time-step trial, where the page
sat on "setting it up" through all three).

Portability: the engine, the heartbeat file and `events.jsonl` are plain files any harness can
read. Push notifications, background watching, Remote Control and the run page are Claude Code
features; other harnesses get the heartbeat, the event log and the digest, not the phone or the
page.

## 9. Kit layout

```
agents/case-auditor.md  study-runner.md  network-visualizer.md  schema-librarian.md
skills/case-audit/SKILL.md      engine/  tests/
skills/study-runner/SKILL.md    engine/  tests/
skills/violation-map/SKILL.md   engine/  (exists; extended in Plan 4)
skills/schema-lookup/SKILL.md
skills/run-supervisor/SKILL.md  (a main-session mode; no agent file)
skills/plan-pictures/SKILL.md   (a main-session skill; no agent file)
```

Engines are Python on esapp, matching `skills/violation-map/engine/`.

## 10. Testing

All on public synthetic cases.

| test | passes when |
|---|---|
| auditor, clean case | READY for each profile the case supports |
| auditor, seeded defects (strip PFW from 3 units, zero a regulated bus, set a cost model to None) | reports exactly those, nothing new |
| auditor read-only | AST test finds no `SaveCase` / case write in the engine |
| runner, serial vs parallel | the same violation set and the same devices ranked; values agree within 1e-4 relative |
| runner, manifest replay | two runs of one manifest give the same violation set and the same devices ranked; values agree within 1e-4 relative |
| runner, read-back | a write that does not stick fails the run loudly |
| runner, coverage | an incomplete contingency set that nobody chose fails the guard; the same set chosen at configure runs, and every result is stamped "ran your list: n of N" |
| runner, OPF gate | on a case with no cost data, OPF and SCOPF are refused, not run |
| runner, user-supplied costs | an OPF run on cost curves the engineer supplied carries the stamp "costs supplied by you, not from the case" on every result |
| runner, OPF | on a case with cost data, OPF returns a solved status and a final cost, and binding lines match `LineLPUnenforceableMVA` |
| runner, SCOPF | converges within `SCOPFMaxOuterLoopItr`; changing that option changes the recorded loop count; result recorded as the dated verification |
| runner, approval binding | with no `approval.json` entry, or with the manifest edited after its entry was written, the engine refuses and runs nothing; with a matching entry it runs |
| runner, plan | `study.py plan` writes `plan.json` from the manifest alone; editing the manifest afterwards makes the recorded hash stale |
| visualizer, parity | two designs measured in one comparison share one `settings_hash` and one contingency count; adding challengers does not change the engineer's design's `settings_hash` |
| visualizer, side effects | a design that clears the target but creates a new overload shows the new overload in the scoreboard |
| runner, heartbeat | during a run the heartbeat advances; a killed worker shows up as a failed chunk within one heartbeat interval |
| supervisor, stall | a run whose `last_solve_at` stops advancing raises the stall alarm after the configured interval |
| supervisor, run page | each event updates `runs/<run_id>` once (badge, sentence, timeline match the chat) and appends to `events.jsonl`; no write without an event; a viewer below owner cannot write |
| supervisor, gate | the next round never launches without an engineer's answer |
| runner, timestep hand-off | the approval block says "time step will run" and which renewables read 0 MW (IDs, MW share) in 8 lines or fewer; after approval the runner calls the engine in the foreground, the engine detaches the run, and the runner returns one line with the step count, the time estimate and the heartbeat path, and ends; the heartbeat keeps advancing after the subagent has ended |
| runner, timestep slices | on `"Weather Only"`, a window run in `TimeStepDoRun(Start, End)` slices and the same window run in one call give the same per-step MW within 1e-4 relative; until this passes, every sliced result carries "run in <k> slices, not yet checked against one unbroken run" |
| supervisor, timestep heartbeat | on a heartbeat with `unit = "time steps"`, one chunk and `unsolved = null`: one stall alarm when `last_solve_at` freezes while `updated` moves, none for `updated` alone, no failed-chunk or unsolved alarm, and a finish digest that reports what the run produced with numbered moves ending "stop here" |
| visualizer, large load | adding a load candidate changes N-0 flows and appears on the map's Before/Engineer switch |
| auditor, no weather file | a timestep audit with no `.pww` given reports an FYI line and does not block timestep on it |
| auditor, renewable gaps | 3 of 87 renewables without a PFW model → timestep READY, with a Worth-a-look line saying which units read 0 MW and their MW share; never NOT READY for missing models alone |
| runner, monitoring stated | every N-1 result states what was monitored |
| runner, SCOPF stamp | every SCOPF result is stamped "not yet verified" until the first public-case run passes |
| visualizer, opening mode | the map opens in the right mode for its bus count (whole case under the cutoff, area view over it) and says which |
| plan pictures, fidelity | at each gate — the engine's `plan.json` for the runner, the visualizer's challengers and the supervisor's next round, or a written plan's numbered task list — picture steps == file steps (none added, none missing, same order); a `plan.json` whose recorded hash no longer matches its source is refused |
| librarian | known lookups (shunt keys, island reporting, SCOPF outer loops, no SCOPF inner loop) answered correctly with the right confidence tag |

## 11. Build order

0. Prerequisites: sync the kit's `concepts/parallel-contingency-solve.md` (missing the rule to
   `.exit()` instances you own) and `methods/reading-violationctg.md` (still says islanding is
   undetectable).
0b. Before Plans 2–3 — kit pages the agent drafts found wrong or missing (gap audit, 2026-09-28):
   - **Contradictions to resolve:** `methods/adding-devices-esapp.md` calls bare
     `LPOPFCostFunction` the final cost, while `references/powerworld-study-options.md` says `:1` is
     final and bare is initial; the same page runs DC off the `DCApprox` flag, which
     `powerworld-study-options.md` says is not enough; the solver token is `POLARNEWTON` in
     `concepts/aux-only-powerworld.md` but `POLARNEWT` in `methods/handling-errors.md` and
     `concepts/lodf.md`; the coverage rule in `powerworld-study-options.md` ignores the autoinsert
     exclusions in `methods/new-device-contingency-aux.md`.
   - **Not a PowerWorld prerequisite:** `methods/timestep-simulation-setup.md` lists an ISO region in
     `CustomString:2` among TimeStep's per-unit prerequisites. It comes from one project's own
     shapefile join, not from PowerWorld; reword the page so it reads as that pipeline's
     convention.
   - **Monitoring footprint:** document how area, zone, kV and element monitoring settings combine
     and which area a tie line belongs to (today only `Area.BGReportLimits` is verified).
   - **Pages to write:** the PFW insertion tool; cost-model types, curve structure and the values
     `OPF_GenCostModel` / `OPF_PtsPerCurve` accept; OPF result fields (solve status, LMPs, detecting
     an infeasible solve); the `SuperArea.BGAGC` value list; when to call `CTGSetAsReference` after
     loading a variant; worse-end branch loading (`LinePercent:1`, `LSEndMonitor`); how monitoring
     and OPF treat zero-rated branches; `Limit_Monitoring_Options` defaults.
1. schema-librarian — smallest, reads pages that already exist, and the runner depends on it.
2. case-auditor — first writes the four rule pages (a switched shunt or LTC regulating a bus that
   does not exist or is out of service, `base.regulates_nothing`; an LTC with
   `XFRegTargetType = Middle`, `base.ltc_middle_target`; an LTC regulating its low-voltage side
   while its high side is out of band, `base.ltc_regulates_lv_side`; a lightly loaded EHV stub
   rising on its own line charging, `base.floating_stub`), then the base/timestep/opf profiles.
3. study-runner — ACPF, DCPF, N-1, then OPF and SCOPF (behind the auditor's opf gate), then
   TimeStep last: it reuses the auditor's timestep profile for the "who follows the weather" count
   and the N-1 heartbeat, generalised to `done`/`total`/`unit`. Its background hand-off is exercised
   end to end only once run supervision (5) exists; until then it is tested against the heartbeat
   file alone.
4. network-visualizer — measure the opening cutoff, large-load candidate, thermal view, full-N-1 comparison through the study-runner engine.
5. run supervision — the `run-supervisor` mode over the runner's heartbeat; after Plan 3, because it
   supervises the runner's runs.
6. plan pictures — the `plan-pictures` skill; after the runner (Plan 3), because it draws from the
   `plan.json` the runner's engine writes (`study.py plan`, built in Plan 3 with the approval check).

## 12. Out of scope for v1

Transient stability, GIC, unit commitment, an n1 audit profile.

## 13. Open questions

- Which public synthetic cases serve as fixtures: one without PFW models or cost data, one with
  PFW models (the time-step demo's case), one with cost data if any public case carries it.
- Whether the kit may redistribute PowerWorld's field export and a digest of the aux-file-format
  document; this decides whether the librarian's sources ship or are fetched by the user.
- Does PowerWorld/SimAuto keep running with the PC locked, or the user logged out? Run supervision
  assumes the machine stays up for hours; test this before building Plan 5.
- ~~Plugin agent discovery~~ — answered 2026-09-28: `agents/` in the kit is loaded
  (`claude --plugin-dir <kit> plugin details powerhivemind`, Claude Code 2.1.284).
