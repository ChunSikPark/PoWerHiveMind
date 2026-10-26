# Changelog

## Unreleased — 2026-10-26

- Renamed PowerWorldHiveMind to PoWerHiveMind. The repository is now github.com/ChunSikPark/PoWerHiveMind and the site
  chunsikpark.github.io/PoWerHiveMind. GitHub redirects the old repository links, including `git clone`; the old site
  address does not redirect.
- The plugin ID is now `powerhivemind` (was `powerworld-hivemind`). Skills are called `powerhivemind:powerworld`,
  `powerhivemind:case-audit` and so on, setup is `/powerhivemind:powerworld-setup`, and the install sentence clones into
  `~/.claude/skills/powerhivemind`. An existing install picks up the new ID after `git pull` and `/reload-plugins`;
  its folder can keep its old name. The `dist/` files are now `powerhivemind-*`.
  Entries below keep the old names.

## 0.5.1 — 2026-10-21

- Five new pages:
  - `concepts/gsu-outages-in-n1.md`: double every single generator step-up or leave GSU outages out of N-1. Measured,
    both fail on the same transmission outages.
  - `concepts/gsu-tap-vs-generator-voltage-control.md`: a fixed GSU tap, the generator regulating one bus, and one
    automatic controller per regulated bus.
  - `methods/emergency-ratings-for-a-synthetic-case.md`: a per-branch Rate B and C from per-class statistics instead of
    one flat ratio, then contingency monitoring pointed at Rate B.
  - `methods/fixing-plant-islands-from-single-outages.md`: a topology-only screen for single outages that strand a plant,
    and the fix for each of four shapes.
  - `methods/timestep-dispatch-into-design-bands.md`: unit-by-unit wind and solar dispatch from a time-step run, scaled
    into a scenario's design bands.
- **The site's front page** puts the page graph right under the hero, coloured by topic, then plays the two animated
  walkthroughs in place ("When the knowledge exists" / "When no knowledge exists"). Two thumbnail cards open the install
  guide and the design replay. "Does it help?" leads with the 30-request validation: 30 of 30 for 0.5 against 20 of 30
  for 0.4. The walkthroughs start at 1.5x, and the results step shows the wind file beside the solar one.
- **Pages name no private tool repository.** The PFW handoff page is now `concepts/auto-pfw-scripts.md`, and the
  case-auditor's handoff message says "the Auto_PFW scripts".
- **Six suspected PowerWorld issues are now marked as suspected**, with their glitch ids, wherever pages stated them
  as fact: plain `TimeStepLoadPWW` failing on two Simulator 25 builds; contingency results inside TimeStep reusing the
  first hour's reference; the PWW loader's access violation on weather code 112; `ElementType=GEN` being ignored;
  `CTGAutoInsert` inserting zero contingencies; and writing a changed `GenMW` clearing `GenAGCAble`. The workaround
  for each is unchanged.
- `methods/handling-errors.md` now finds a field name with `GetFieldList` instead of reading every field with
  `pw[Branch, :]`, which can hit a suspected access violation on some cases.
- A wording pass across the pages: shorter sentences, fewer em-dashes, and no first-person setup notes. A few worked
  examples now describe their case generically instead of by its size or counts. The technical claims are unchanged.

## 0.5.0 — 2026-10-21

- **The site leads with what is new.** The front page board is now "What's new in 0.5", and a
  Validation page shows all 30 graded study requests with their answers.
- **Agents scope the work before they start.** A fresh-agent validation (41 graded runs, see the
  site's Validation page) found that most failures were not missing knowledge. The agent kept
  going after it had the answer, searched for an optimum nobody could finish in time, picked its
  own criterion for "fix my case", or ran a study it had just said was out of scope. AGENTS.md
  and the `powerworld` skill now carry seven rules for this: answer, then offer; estimate minutes
  before a long study; one working design first; audit and ask on a vague request; out of scope
  means stop; a wrong premise still gets a deliverable; and N-1 for a region needs that region's
  outages, not just its monitoring.
- **case-audit stops a study when load or generation sits on a disconnected bus**
  (`base.dead_bus_injection`, over 10 MW). The stranded MW is reported after the area and zone
  multipliers. Before this, a case with 2 GW of islanded load audited as READY. Opening a case now
  also counts load on disconnected buses as the first finding.
- **`CTGAutoInsert` can insert 0 contingencies and report success** on a recent Simulator 25
  build (suspected PowerWorld issue, not yet confirmed). `methods/new-device-contingency-aux.md`
  says to assert the count and build the set yourself, and now shows how to check that a
  contingency list covers each area asked about (live-tested).
- **Hourly contingency runs inside TimeStep reuse the first hour** unless `CTGSetAsReference()` is
  called (Trap 3b in `methods/reading-violationctg.md`; suspected, possibly by design). TimeStep's raw CSV exports are UTC.
  `TimeStepLoadPWWRange` replaces plain `TimeStepLoadPWW`, which fails on two Simulator 25 builds
  (suspected PowerWorld issue, not yet confirmed).
- New pages: `methods/reviewing-a-design.md` (a reviewer's checklist for a submitted design),
  `methods/finding-and-fixing-radial-by-n1-pockets.md`, and
  `methods/zone-load-multiplier-trap.md` (why the served load differs from the load entered).
  `concepts/per-unit-basis-discipline.md` adds the per-mile impedance trap with magnitudes.
- New pages on fixing violations in large cases: `methods/remediating-base-case-violations.md`
  (the intact-case action ladder, cheapest first), `methods/remediating-n1-contingency-violations.md`
  (the N-1 loop, round after round), `methods/diagnosing-a-non-converging-contingency.md` (why an
  outage returns unsolved, in four probes), `methods/removing-empty-buses.md` (dead voltage levels
  that inflate islanding and N-1 counts), `concepts/agc-participation-factors.md` (who picks up
  lost generation), `concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md` (why a
  transformer is not sized like a line), `concepts/one-device-per-voltage-pocket.md`
  (undervoltage clusters by driving outage, not by bus) and
  `concepts/aggregate-clauses-cannot-bound-one-row.md` (why counts and maxima hide one element
  getting worse).
- violation-map uses the case's own voltage limits by default, treats "show me the violations" as
  intact plus N-1, and reports thermal overloads in text.
- knowledge-base-page gains a "Share it" step: scrub a copy, then hand the user a pre-filled
  GitHub issue to review and submit.
- Fixed: six pages still taught `pw.dc_mode = True` and `pw.flat_start = True` as working. A
  scripted solve ignores both, so they now point at `pw.pflow(method="DC")` and
  `pw.flatstart()`. The weather client's bbox order is N, W, S, E. Pages no longer name a private
  research project or its file paths. AGENTS.md's page count is now 68. New rule: never kill a process by name on a shared machine.

- **The case-auditor lints for data defects: a `lint` profile with nine rules** (`--profiles base,lint`).
  Discrete shunts set beyond their blocks or between steps, inverted shunt bands, online units below
  their minimum, missing, placeholder or inverted unit limits, negative reactance, branches with no
  rating A or no B/C, unnamed buses, stray islands and slack counts, and nominal kV that is missing
  or not round. None needs a solve and none stops a study. A field that reads blank on every row is
  treated as not read, so its rule stays silent instead of flagging everything. New page:
  `methods/case-data-lint.md`. The reader now also reads `GenMWMin`, `SSVHigh`, `SSVLow` and the
  ten shunt blocks.
- **The case-auditor is live: a fifth skill, `case-audit`, and the `case-auditor` agent.** Checks a
  case read-only and says whether it is READY for a base power flow, an N-1 (its monitoring), a
  time step, an OPF and a SCOPF, with the case summary the agent presents (load, generation,
  headroom by fuel type, shunts, size). Eighteen checks as small pure functions over what one
  esapp read returns, each tested on hand-built cases with no PowerWorld; one AC solve in memory,
  no retry; the case file's sha256 before and after in `findings.json`; and a test that fails the
  build if the engine names a write or uses PowerWorld outside an allowlist. Findings go
  to `./case-audit/<case>/`, which ignores itself in git.
- Two rule pages: `methods/ltc-regulation-checks.md` and
  `concepts/unloaded-ehv-stub-overvoltage.md`, with what a live probe of two public cases found
  (a regulated bus of 0 cannot be written through SimAuto; `BusVoltLimLow/High` read the limit
  group's band; generator coordinates live on the substation). A third,
  `concepts/auto-pfw-scripts.md`, is the handoff for missing PFW models.
- `concepts/opf-preconditions.md`: measured on two public cases, a super area on OPF meets the
  area condition and makes its member areas redispatchable; a refused OPF does not raise through
  esapp (read `LPOPFSolutionStatus`); a zero marginal cost on wind and solar is a price, not
  missing data.
- Fixed: `methods/timestep-simulation-setup.md` listed an ISO label in `CustomString:2` as a
  TimeStep prerequisite (it is one pipeline's convention) and pointed at a page that does not
  exist; `methods/converting-lines-to-transformers.md` glossed `XFAuto = NO` as "not an
  autotransformer" (it is the automatic-control switch).
- An eval suite for the case-auditor under `evals/` (`claude plugin eval`): two cases on live
  audits of the public Hawaii40 and Texas2k cases, six on seeded copies of Hawaii40 that test its
  judgment. Developer tools (the probe, snapshots, replays, fixtures) are in `tools/case-audit-dev/`,
  outside `skills/`.

## 0.4.0 — 2026-09-30

- **An agent team, designed and drafted.** `docs/superpowers/specs/2026-09-28-power-system-agents-design.md`
  sets out a small team that works on measured numbers instead of guesses. Methods are knowledge
  and agents are roles, so adding a study never adds an agent.
  - `schema-librarian` is live.
  - `case-auditor`, `study-runner` and `network-visualizer` ship as role-contract drafts in
    `docs/agents/`. They load only once their engines are built.
  - `run-supervisor` and `plan-pictures` are drafts of main-session skills.
  - The auditor opens every scan with a case summary: load, generation, headroom by fuel type,
    shunt capacity. It says what a study will actually do ("84 of 87 renewables will follow the
    weather; 3 read 0 MW") and blocks only what cannot run.
  - The runner turns a plain request into a settings change, stops for approval, and covers AC,
    DC, N-1, OPF, SCOPF and now TimeStep. Long runs hand off to the supervisor.
  - Every draft follows the same rules: plain requests in, short answers out (an approval is
    8 lines or fewer, a break is 3 plain lines), and approval recorded in the settings file.
- **Pages are the answer where a picture beats a paragraph.** Two reference pages ship in
  `docs/agents/pages/`.
  - `design-compare.html` draws every option on the network around the site, with its overloads
    and low buses painted on, side by side.
  - `run-watch.html` is a live status page for a long run: a badge top right, a one-line answer,
    progress, a run clock and the timeline.
- **Study references.** `references/powerworld-study-options.md` (curated, provenance-tagged),
  `references/powerworld-option-objects-v25.md` (every option object's fields),
  `references/powerworld-study-commands.md` (every study SCRIPT command) and the Simulator 25
  field export, `references/powerworld-object-fields-v25.xlsx`.

- **A fourth skill, `schema-lookup`, and the kit's first agent, `schema-librarian`.** Answers which
  PowerWorld object, field or SCRIPT command to use from the Simulator 25 field export
  (`references/powerworld-object-fields-v25.xlsx`), and prints what
  `references/powerworld-study-options.md` says about the field verbatim — including rows that
  call a field a decoy or a trap. Key fields, required fields, writability, concise and colon
  names, and a ranked search across ~100,000 fields; no PowerWorld needed. `powerworld-setup` now
  installs `openpyxl`. Also fixed: two pages still said islanding is undetectable after
  `CTGSolveAll`, and the parallel-contingency page lacked the rule to `.exit()` instances you own.

- **A third skill, `violation-map`, and the method page behind it.** It builds two
  single-file HTML maps from a case: a **voltage page** (the substations around the
  out-of-band buses, every line in its own kV colour, a click-to-zoom problem list,
  substation one-lines, the reactive balance inside the radius, and candidate fixes measured
  in memory with a Before/After switch and a scenario × outage grid) and a **radial-ties page**
  (every bridge whose single outage islands part of the grid, grouped into radial trees, with
  a suggested tie per tree and its AC-measured verdict). The engine under
  `skills/violation-map/engine/` is driven by one `config.json`; nothing it runs writes to a
  case. `methods/violation-network-map.md` carries the page contract and the traps each of
  which cost a run: islanding solves with zero violations, an undo does not restore taps or
  shunts, a tie's rating does not scale with its length, and an un-exited PowerWorld stays
  resident. Verified end to end on a 10,000-bus synthetic planning model; there is no thermal
  view yet, and the page says so.

## 0.3.0 — 2026-09-21

- **Three new concept pages.** `concepts/powerworld-script-transfer.md` documents Simulator
  25 beta's watched-directory channel — drop an `.aux` in, read the message-log slice back,
  with no COM, no SimAuto call and therefore no SimAuto licence — which appears in no
  edition of the *Auxiliary File Format* manual and is sourced from a September 2026 slide
  deck. `concepts/aux-only-powerworld.md` records what the aux language can do with no
  Python at all, what it structurally cannot (no return values, almost no control flow, no
  assertions), and the read-back discipline that substitutes. `concepts/opf-preconditions.md`
  names the three independent preconditions the LP OPF refuses to start without, one of
  which is data and cannot be switched on honestly. All three verified live in September
  2026 against a regional synthetic planning model.
- **The kit can now be grown from inside a session.** A new `knowledge-base-page` skill and
  `/kb-page` command teach the schema these pages already follow — the filing tree, the
  `Abstract`/`Connections`/`Content` shape, the closed frontmatter enums, the two-link floor
  and the `index.md` row — so a session that worked something out can file it instead of
  losing it to chat. It ships as **one markdown file with no checker**, deliberately: a
  checker, a test suite and a `PreToolUse` hook were built, used, and then removed, because
  a clone never syncs back upstream and a gate that edits the user's global config is not
  something to hand a stranger. Two corpus queries survive inline, for the only two
  questions a single page cannot answer — which pages have no index row, and which links
  point at nothing. The plugin now registers two skills and two commands.
- **System and project identity are gone from the published pages.** Three classes were
  leaking: a system operator's name and its zone list, the research programme's own project
  names framing findings as project decisions, and four pages still naming a case in their
  provenance line. Each is replaced by the general rule, which is the part a reader can use
  — the zone list becomes "check whether `AreaNum`/`AreaName` already carries the operator's
  scheme before writing a spatial join". The export's forbidden-term list gains 13 entries
  so the gate catches this class next time rather than a reviewer catching it page by page.
- **An Obsidian graph config ships with the pages** (`.obsidian/graph.json`): coloured by
  folder, with `index.md` and the top-level files filtered out, since `index.md` links to
  every page and would swamp the view. Open the repo as a vault to see the page network and
  spot an orphan or a cluster that has grown big enough to split. The rest of `.obsidian/`
  is per-machine state and stays ignored.
- **`BENCHMARK.md` had the wrong baseline.** It said v0.2.0 was 47 pages; v0.2.0 was **44**,
  and 47 is the count as of this release. The note also warned that ten unbenchmarked manual
  pages had been added — those were withdrawn before shipping, so the warning described a
  state no release ever had. Corrected to what is true: 19-of-23 was measured on the 44-page
  v0.2.0, this release adds three pages, and page count is the variable retrieval cost is
  most sensitive to.

- **The esapp 0.2.1 read-only correction had only reached `concepts/`.** Five pages in
  `methods/` and `references/` still stated the 0.1.x behaviour — that a read-only column
  makes `pw[Type] = df` raise `ValueError: Cannot set read-only field(s)` — as current:
  `adding-devices-esapp.md` (twice), `converting-lines-to-transformers.md`,
  `esapp-overview.md` and `esapp-package-backend.md`. On 0.2.1 it only warns and the write
  proceeds. `converting-lines-to-transformers.md` was the costly one: its entire
  `ChangeParametersMultipleElement` recipe existed to route around a `ValueError` that no
  longer happens, and the bracket writer is now the recipe. All corrections verified live
  against Texas2K on Simulator build 2026-07-22 with esapp 0.2.1.
- **`is_settable()` is wrong far more often than it is right, and the kit told you to trust
  it harder.** esapp's generated schema keeps a field as editable only when Simulator
  reports `enterable` as an unconditional `Yes`, silently discarding every conditional one.
  Measured against build 2026-07-22: **112 `Branch` fields, 33 `Bus`, 5 `Gen` (including
  `GenMVR`), 1 `Load`** are enterable in PowerWorld but flagged read-only by esapp.
  `Branch.LineStatus` is the one everyone hits — PowerWorld's own answer is *"Depends:
  Normally enterable except when field Lockout is YES"*, and the write succeeds.
  `pw.esa.GetFieldList(<type>)`'s `enterable` column is now documented as the authority.
- **The kit's own mitigation broke working code.** `concepts/esapp.md` and
  `concepts/esapp-script-command-wrappers.md` advised running write-heavy code under
  `python -W error::UserWarning` to make field-name typos fail loudly. That promotes the
  false-positive read-only warning to a hard error, so it crashes on ~150 fields that write
  correctly. Removed everywhere and replaced with the rule the rest of the kit already uses:
  assert the effect, never the absence of an exception. `concepts/lodf.md`'s account of
  `LineStatus` was corrected in the same pass — it blamed the bracket writer for a bad flag.
- **`pw.save()` is a silent no-op and nothing said so.** `AGENTS.md` rule 5 has always
  warned that `pw.esa.SaveCase(...)` writes no file, but `concepts/esapp.md` listed
  `pw.save(filename=None)` as the case-save API with no warning. It is a one-line
  passthrough to `esa.SaveCase`, so it inherits the trap. Confirmed at the raw COM layer:
  `SimAuto.SaveCase(path, "PWB", True)` returns `('',)`, SimAuto's success value, and
  creates nothing. Both are now flagged together.
- **`pw.esa.get_key_field_list()` does not exist.** `concepts/esapp.md` named it as the way
  to prepend key fields on the raw SAW path; it raises `AttributeError`. Replaced with
  `Type.keys()` and `pw.esa.GetFieldList(<type>)`'s `key_field` column.
- **`AGENTS.md` rule 2 was true of one write form and wrong about the other.** "Assigning to
  a filtered subset writes nothing" holds for `pw[Obj, field] = values`, which is positional
  over the whole table — but `pw[Obj] = df` matches rows by key field, so a filtered subset
  is correct and writes exactly those rows. Rule 2 now separates the two; a new rule 9
  covers the read-only false positive. `GEMINI.md` resynced from `AGENTS.md` (it had also
  drifted to a stale "~345 catalogued actions").
- **Python bools on status fields were undocumented.** 0.2.1 serializes them through
  `BOOL_FIELD_VOCAB`, so `pw[Gen, "GenStatus"] = True` writes `"Closed"`. `concepts/esapp.md`
  now carries the vocabulary table; the plain strings still work and most pages still use them.
- **`dist/` had no build script and had drifted a day and three pages behind.** The bundles
  were missing `methods/reducing-a-contingency-set.md`,
  `concepts/case-to-case-device-transplant.md` and
  `concepts/esapp-script-command-wrappers.md` — the last being a page whose whole subject is
  the 0.2.1 change — so chat-tool users got the uncorrected text with no correction page at
  all. Added `build_dist.py`, which regenerates all five bundles and the skill zip from the
  source pages; rebuilt output carries 46 sections, up from 43.

- **The plugin's skill could not find its own pages.** `skills/powerworld/SKILL.md` sent the
  agent to `concepts/`, `methods/`, `demos/` and `references/` as bare relative paths, so an
  installed plugin — which lives under `~/.claude/plugins/cache/…` — had the agent searching
  the user's working directory instead. All 44 pages shipped correctly; nothing could find
  them. The skill now resolves `${CLAUDE_PLUGIN_ROOT}` first and anchors every path to it,
  with a fallback for agents that do not set that variable. Verified by installing the
  plugin and reading back its component inventory and cached page count.
- **New `/powerworld-setup` command** (`commands/powerworld-setup.md`): finds Python,
  installs `esapp`, `TeamOverbyeWeather` and `pywin32`, runs preflight checks 1–4, reports
  the Simulator build date, and reads the failure back in plain language — including that
  the SimAuto add-on is licensed separately and no code change fixes it.
- **`GETTING-STARTED.md` rebuilt around the plugin install.** Six steps to five: the ZIP
  download and the folder-picker are gone from the main path, replaced by two `/plugin`
  lines and `/powerworld-setup`. Both survive as a manual route for agents without a plugin
  system. `README.md`'s install section leads with the same route.
- **`index.md` was unreadable as a catalog.** 43 of its 44 rows were page abstracts cut at a
  character count, so every description stopped mid-sentence — the page whose only job is
  helping you choose which page to open. All 44 rewritten as complete one-line descriptions.
- **`references/aux-script-commands.md` was described as a complete catalog by four other
  pages.** It holds 198 actions under 15 headings and its own abstract calls it a working
  subset, but `esapp-schema-reference.md`, `concepts/esapp.md`,
  `concepts/esapp-script-command-wrappers.md` and `AGENTS.md` variously called it "full",
  "all 26 categories", "344 actions" and "345 catalogued actions". The two sentences about
  esapp's wrapper coverage now measure against the ~370 actions Simulator defines rather
  than against the catalog's own size, which made "roughly 300 of 345" impossible.
- **`/powerworld-setup` could not be followed as written.** It told the agent to run
  "checks 1 through 4" of the preflight script without writing its own version, but that
  script ran all five as one function with a hardcoded case path. `preflight-powerworld.md`
  now splits into `preflight_machine()` (checks 1-4, no case needed), `preflight_case()`
  and `preflight()`; the command calls the first.
- **Both plugin manifests advertised IEEE 738 dynamic line ratings**, which `AGENTS.md`
  declares out of scope. Removed from the descriptions and the keyword arrays, so the
  plugin browser no longer sells what the kit refuses to cover.
- **`README.md` carried three contradictory setup routes** and its "which file your agent
  reads" table claimed Claude Code loads `CLAUDE.md` — untrue on the plugin route, where a
  plugin ships skills and commands and its instruction files are never loaded. The `git
  clone` block labelled "fastest" and the beginner walkthrough that disagreed with
  `GETTING-STARTED.md` on Node.js, on verifying Python, and on twenty versus thirty minutes
  are gone; the paste-block survives as a labelled fallback. 369 lines to 286.
- **A README claim contradicted the benchmark it linked to.** It said the kit is "weaker
  than a web search" at command lookup; `BENCHMARK.md` reports 4 of 7 against 2 of 7, worse
  on cost rather than on answers.
- **Prose pass across the human-facing docs and the knowledge pages** for AI-slop patterns:
  kickers, colon reveals, stacked rhetorical questions, metadiscourse that told the reader
  what to notice, a benchmark pitch duplicated verbatim in two sections, and one page using
  ASCII `--` where the other 43 use an em dash. Page counts corrected to 44/17/16/7/4 and
  the rule count to eight.
- **Codex plugin support**: adds a portable `plugin.json` at the repo root and
  `.agents/plugins/marketplace.json`, per the agent-plugins.org 1.0.0 schema, which Codex
  discovers via `codex plugin marketplace add`. Manifests validate against the published
  schema but are **untested against a released Codex build**; both docs say so.

## 0.1.5 — 2026-09-09

**Example cases are now referred to by neutral names** — `Synth2k`, `Synth40`, `Synth8k`,
`Synth9k` — instead of by the specific model each measurement was taken on. Roughly a
hundred references across seventeen pages. Every figure is unchanged: the bus counts, the
row counts, the timings and the violation numbers are the same measurements they always
were. What is gone is which model produced them, which was never something a reader could
use.

The export now refuses to publish a page containing a name from a maintained list, so this
cannot drift back in one page at a time. It is the third check on the same boundary as the
existing private-path and personal-name checks, and it caught five references the manual
pass had missed, including two hidden in page metadata.

## 0.1.4 — 2026-09-09

- **The Claude Skill (`skills/powerworld/SKILL.md`) is rewritten** to match `AGENTS.md`:
  search the four content directories first and read the page you find in full, rather
  than starting at `index.md`. It also gains a defect-reporting section — how to hand the
  user a pre-filled issue link when a page is wrong or missing, and why the text must be
  shown first, since a traceback can carry case filenames and substation names into a
  public tracker.
- **Three dangling `[[wikilinks]]` removed** from code comments in
  `concepts/powerworld-simauto.md`, `methods/save-powerworld-case.md` and
  `methods/new-device-contingency-aux.md`. They pointed at pages that exist only in the
  private source vault. The export now fails on this shape instead of shipping it.
- `dist/` bundles rebuilt.

## 0.1.3 — 2026-09-09

The instruction layer. Nothing about PowerWorld changed; what changed is whether your
agent ever sees the rules that govern the 41 pages.

### The bug: instructions detached from the knowledge

`AGENTS.md` holds everything that makes this kit work — search before you reason, read
the right page in full, cite the page or say there is not one. Codex, Cursor, Copilot and
Windsurf load that file natively. Claude Code does not: it reads `CLAUDE.md` and nothing
else. Ours said "Instructions for agents live in AGENTS.md. Read that file" — a markdown
link, which loads nothing. So every Claude Code user got the knowledge base with the
rules detached from it, and the symptom looked like an agent ignoring instructions it had
in fact never been shown.

Fixed with the documented `@AGENTS.md` import. That fix was luck: nobody had ever written
down which tool reads which file, so nothing could have caught it.

- **`GEMINI.md` is new.** Gemini CLI reads `GEMINI.md` by default and reaches `AGENTS.md`
  only if you set `context.fileName` in your own settings — which a kit cannot do for you.
  It had the same detached instructions, and the AGENTS.md standard's own supporter list
  says Gemini CLI is supported, which is how it stayed invisible. The file is generated
  from `AGENTS.md` at export; edit `AGENTS.md`.
- **The README now says which file your agent actually reads**, per vendor, verified
  against each vendor's own documentation on 2026-09-09.
- **The export now fails** if a listed vendor has no shim, if an import shim has no real
  import, if a generated copy has been hand-edited, or if `AGENTS.md` grows past the
  32 KiB Codex truncates at without saying so.

## 0.1.2 — 2026-09-08

One troubleshooting entry, from watching the same install go wrong twice. Both people
downloaded the Claude installer, never ran it, and reported that Claude was missing.

- **Step 3 says to run the installer**, not only to download it, and says that Claude
  creates no desktop icon — an empty desktop is not evidence the install failed. The fix
  is Start, type `Claude`, right-click, **Pin to taskbar**.
- **"I downloaded Claude but I cannot find it"** is now a troubleshooting entry, with both
  causes, because from the outside they look the same.

## 0.1.1 — 2026-09-08

Setup and navigation. Nothing about PowerWorld changed; what changed is how you install
this and how an agent finds the right page inside it.

### Getting started, rewritten

Feedback from someone installing the kit with no Python and no GitHub background: they got
as far as "start your assistant in the folder you unzipped" and stopped. The old page never
said what to actually start, and it listed the Claude desktop app as a coding agent without
saying what to do with it.

- **The desktop app is now the documented route.** Click `Code`, click the folder button,
  choose `Open folder...`. Three screenshots at the three places people got stuck. No
  terminal, no launch command, no folder path to type.
- **The terminal instructions moved to an appendix** for people using a command-line agent,
  and now link Anthropic's terminal guide rather than re-explaining it.
- **Two prerequisites that were missing entirely:** Claude Code needs a paid plan, and on
  Windows it needs Git installed. Both used to fail late and look like bugs.
- **Your agent now installs the Python packages** as part of the first question, instead of
  a separate `pip` step.
- **One word for one thing.** The page used "AI assistant", "AI coding assistant" and
  "agent" interchangeably, which was the literal question the tester asked. It is "agent"
  throughout now.
- **If you have no paid plan**, the `dist/` bundles and what you lose by using them are
  documented rather than implied.

### Navigation, measured and rewritten

`AGENTS.md` used to send an agent to `index.md` first, then to a task-routing table. Both
lost a measurement: 48 agents, 16 questions with human-written answers, scored against
ground truth. Searching the page text found the right page 10 times out of 16, the routing
table 8, `index.md` 7.

- **Search all four content directories first**, with both the plain-English phrasing and
  the identifier, ranked by how many terms land. Concrete forms given for Claude Code,
  ripgrep, Cursor and PowerShell.
- **`index.md` and the routing table are now disambiguators, not routers.** Both name
  topics, and a topic is coarser than a page.
- **A false-absent rule.** "Not in the knowledge base" is not a conclusion you may reach
  from a routing-table miss. In the same measurement the table produced two confident
  "not here" answers on pages it does route.
- **The read budget is about breadth, not depth.** The old wording capped pages opened,
  which agents read as permission to stop halfway through the right page. Once a page is
  the right page, read all of it.

### Removed

- **`install.ps1` and `install.sh` are gone.** A PowerShell script that strangers are asked
  to run makes a repository look hostile regardless of what it does. Install by unzipping
  the folder, or through your agent's own plugin mechanism.

### Pages updated

- `concepts/esapp.md`
- `concepts/powerworld-simauto.md`

## 0.1.0 — 2026-08-27

First release.

A markdown knowledge base that makes a coding agent competent at PowerWorld Simulator
automation. 41 linked pages, no software to run.

### What it covers

- **Driving PowerWorld from Python** with `esapp` — opening cases, reading and writing
  data, solving power flow, saving
- **Modifying cases** — adding buses, branches, loads and generators; applying a
  dispatch; reclassifying branches as transformers
- **Contingency analysis** — building sets, reading violations, ranking devices by
  severity, generating filter and contingency `.aux` files
- **PowerWorld's weather features** — the PWW format, TimeStep simulation for hourly
  renewable output, and fetching `.pww` files with the TeamOverbyeWeather client
- **198 SCRIPT actions**, organized by task rather than by manual chapter

### Demos

Five worked runs on a real 37-bus case. Every number is from an actual execution, and
the failures were left in deliberately:

- `demos/comparing-planning-cases.md` — diffing two vintages of one system (2016 vs 2024
  summer peak): 691 new branches, 199 new generators, guarded against renumbering and
  endpoint-swap artifacts, then a contingency set for only the new devices. The naive
  solve reports 240 violations; only 32 belong to the plan
- `demos/violation-remediation.md` — the full study: 12 N-1 violations diagnosed down to
  a single corridor, five candidate reinforcements tested independently and ranked. Two
  of the five made the system worse, including the one an engineer would reach for first
- `demos/adding-a-device.md` — three `CreateData` attempts that raised no exception and
  created nothing, then the documented fix, then the N-1 comparison it enables
- `demos/power-flow-and-sensitivities.md` — AC, DC, LODF, PTDF, including the `1e8`
  sentinel and an error whose obvious recovery fails the same way
- `demos/contingency-and-aux.md` — N-1 from scratch, then generating and loading an aux
- `demos/timestep-and-pfw.md` — the PFW-model check that decides whether a case can run
  a weather study at all
- `demos/start-here.md` — one-line prompts, so you never need to know which page covers
  what

### Version awareness

Preflight now reports the Simulator build date on every run, so the version is on record
before any analysis is written. `concepts/version-requirements.md` covers three ways to
detect your version, what this kit was verified against, and the behaviours that shift
silently between releases.

Verified against **Simulator 24, build 24.2026.7.22**: 13 of 14 feature areas confirmed
working (the fourteenth was a prerequisite error on an empty case, which is correct
behaviour, not a failure).

### Error handling

`methods/handling-errors.md` sorts failures into three tiers: fix silently (missing
packages, wrong access paths), fix and mention (a recovery that changes the answer's
meaning), or stop and ask (SimAuto licence, destructive actions, real modelling
decisions).

It also covers what no exception handler catches: PowerWorld frequently accepts a
malformed request, reports success, and does nothing. Seven verified silent failures are
tabulated with a guard for each. The rule is to assert the *effect*, never the absence of
an error.

### Install

```bash
git clone https://github.com/ChunSikPark/PoWerHiveMind.git
```

- **Claude Code:** `/plugin marketplace add ChunSikPark/PoWerHiveMind`
- **Any other project:** copy the cloned folder in as a subdirectory — it is plain
  markdown, with nothing to build or run
- **ChatGPT / claude.ai:** upload from `dist/` — a Claude Skill zip, a single-file
  bundle, or split files for Custom GPT knowledge

### Verification at release

- 119 Python code blocks checked against the installed `esapp` 0.1.3 — 0 invalid API
  references
- 0 dead internal links, 0 private paths, 0 personal names
- Five build gates: code integrity, link resolution, index completeness, private paths,
  personal names
- The preflight script was extracted from the published markdown of a fresh public clone
  and run end to end: 5/5 checks passed against a real case

### Known limitations

- **Cold-agent navigation: validation in progress.** The traversal protocol is designed
  so a fresh assistant reads three to five pages before writing code, and the acceptance
  criterion is fewer than 8 of 41. That has not been measured yet. The test is defined in
  `demos/start-here.md` and runs against the public clone; results will land in a
  subsequent release. Until then, treat the page-count claim as a design target rather
  than a measured result.
- **Scope is PowerWorld automation.** Contingency analysis fundamentals, OPF
  formulation, PV/QV theory, transient stability theory, and weather science such as
  dynamic line ratings are deliberately out.
- **Some claims are marked UNVERIFIED** in the reference pages, inherited from the source
  material. They are labelled rather than removed, so unverified content stays
  distinguishable from verified content.
- **PowerWorld automation requires a separately licensed SimAuto add-on.** Fetching and
  inspecting weather data is the only part that works without it.
