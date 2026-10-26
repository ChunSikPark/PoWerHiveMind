# PoWerHiveMind — agent instructions

You have a knowledge base for **PowerWorld Simulator automation**: driving PowerWorld
from Python with `esapp`, including PowerWorld's own weather features (PWW files and
TimeStep simulation).

**Start here:**
1. [Run the preflight](#when-the-user-hands-you-a-case-file) before any analysis code.
2. [Search the pages](#how-to-find-the-page--and-how-much-of-it-to-read) on both the plain-English and the identifier phrasing.
3. [Task routing](#task-routing) when search comes back thin.
4. [Rules that fail silently](#rules-that-apply-to-every-line-of-code-you-write) before writing any code.

## The rule that overrides your defaults

**Consult this knowledge base before you reason. Do not work it out yourself.**

Your instinct on an unfamiliar API is to infer the answer from naming, from similar
libraries, from what looks reasonable. Here that instinct is wrong, and wrong in a
specific way: PowerWorld's failures are **silent**. It accepts your call, returns
success, and gives a wrong answer. You will not get an exception telling you to look
things up. By the time a mistake surfaces, it looks like a modelling result rather than
a bug.

So, without exception:

1. **Before writing any PowerWorld or weather code, open the page that covers it** and
   say which page you are following. Not after your first attempt fails — before the
   first line.
2. **When you do not know something, look it up here first.** Check
   [index.md](index.md) before reasoning from general knowledge. Assume this base
   contradicts what you would have guessed, because it usually does.
3. **When code fails, re-read the page before inventing a fix.** The failure is almost
   always something the page already warns about. Guessing a second time repeats the
   first mistake more expensively.
4. **When no page covers it, say so out loud** and mark the answer as outside the
   knowledge base. Do not quietly improvise and present it with the same confidence as
   sourced work. An unmarked guess is the one failure mode this base cannot fix.
5. **Never contradict a page from memory.** If you believe a page is wrong, say that
   explicitly and give your evidence — do not silently substitute your own answer.

You are not being asked to be less capable. You are being asked to spend two hundred
tokens reading before you spend twenty thousand debugging something this base already
knew.

## How to find the page — and how much of it to read

HiveMind is 73 pages — 28 in `concepts/`, 30 in `methods/`, 8 in `demos/`, 7 in
`references/` — and you will need three to five of them. The ladder below is about
**finding** the right page cheaply. It is not a budget on how much of that page you read.

1. **Search all four content directories first.** Search the page text, not the catalog
   and not the routing table below. Put several terms in one pass, and include **both**
   the plain-English phrasing and the identifier it probably maps to: "save the case"
   *and* `SaveCase`; "tighten the limits" *and* `LimitSet`; "what's overloaded" *and*
   `ViolationCTG`. You do not know which vocabulary a page uses, so search both and let
   the page tell you. Then **rank a page by how many of your terms land on it** — three
   of five terms on one page is your page; one common word is noise.

   Whatever your tool calls it, you want a full-text search across `concepts/`,
   `methods/`, `demos/` and `references/` — **all four relative to the kit root, not to the
   working directory.** The kit root is `${CLAUDE_PLUGIN_ROOT}` when installed as a plugin,
   and otherwise the directory holding this file. `$KIT` below means that path: substitute
   it before running anything, or the search hits the wrong tree and returns nothing.
   - **Claude Code** — the `Grep` tool with `path` set to the kit root and
     `output_mode: "files_with_matches"`, one call per term or an alternation.
   - **Any shell with ripgrep** — `rg -il "savecase|save the case" "$KIT/concepts" "$KIT/methods" "$KIT/demos" "$KIT/references"`
   - **Cursor** — project-wide find (Ctrl+Shift+F), or a codebase search scoped to those
     four directories.
   - **Windows with neither `rg` nor `grep`** — PowerShell:
     `Select-String -Pattern "SaveCase" -Path $KIT\concepts\*.md,$KIT\methods\*.md,$KIT\demos\*.md,$KIT\references\*.md`

   Search is step one because it was measured against the alternatives. 48 agents, 16
   questions with human-written answers, 2026-09-07: searching found the right page 10
   times out of 16, the routing table 8, and starting from `index.md` 7.

2. **A page's `## Abstract` and `## Connections`** — enough to know if it is the right
   page, and which link to follow if it is not.

3. **The page's `## Content`** — the actual procedure. **Read it in full.** Once a page
   is the right page there is no budget: a half-read page is how you end up guessing at
   the exact step it warned you about.

4. **A `references/*-backend.md`** — only when writing code, and only the one you need.

The limit is on **breadth, not depth**. Opening eight pages while hunting for the right
one means your search terms were wrong — change the terms rather than reading a ninth.
Opening one page and reading all of it is the entire point of this base.

**When search comes back thin, [index.md](index.md) and the routing table below are
disambiguators, not routers.** Both name topics, and a topic is coarser than a page. That
gap is what cost them the measurement: agents read a row, picked the right *area*, then
opened the wrong page inside it. Use them to
see what areas exist, or to choose between two candidates search already found. Do not
start there, and do not stop at whatever page a row happens to mention.

**Never conclude "not in the knowledge base" from a routing-table miss alone.** A miss
there means the table has no row matching your phrasing, which is not the same as the kit
having no page. The rows describe what a page *covers* without saying what it *says*, so
they share little vocabulary with the way a question actually gets asked — in the same
measurement, routing produced two confident "not here" answers on pages it does route.
Report an absence only after searching all four directories for both the plain-English and
the identifier phrasing and finding nothing.

## When the user hands you a case file

Do this in order. Do not skip step 1.

1. **Run the preflight** in [methods/preflight-powerworld.md](methods/preflight-powerworld.md).
   Five seconds. It tells you whether this machine can drive PowerWorld at all. Failing
   here is a fact about the machine, not a bug in your code — report which check failed
   and stop rather than rewriting the analysis. Preflight also prints the Simulator
   **build date** — include it in your report, because behaviour shifts between versions
   and it shifts silently. See
   [concepts/version-requirements.md](concepts/version-requirements.md).
2. **Open and summarize** the case using [methods/esapp-overview.md](methods/esapp-overview.md).
   Report bus/branch/generator counts and whether it solves before doing anything else.
   **Count the load and generation on buses that are not connected**, and the MW they
   carry. A 0 pu bus is not "just a dead bus" until you have checked: an islanded load
   keeps a closed status, the solve still converges, and the case quietly serves less
   than it says (seen 2026-10-20 on a 2,000-bus synthetic case). If that count is not zero, it is your first finding.
3. **Then** find the page for the actual task in the table below.

## You are here to run studies, not answer queries

The user rarely wants a number. They want the work that number is for. When asked
"what's overloaded", the useful answer usually continues: *why*, *what would fix it*, and
*what you verified*.

So: **diagnose before proposing, and test before recommending.** Group symptoms into
causes — 12 violations on 4 parallel circuits is one problem, not twelve. Then test
candidate fixes on a fresh case each and measure the result, because reinforcing a
network can make it worse and you cannot tell which by reasoning. See
[demos/violation-remediation.md](demos/violation-remediation.md), where 2 of 5 plausible
reinforcements degraded N-1.

Track **count and severity separately** — they disagree, and which one matters is the
user's call, not yours.

Say what you tested, what you rejected, and what you did **not** save.

## Scope the work before you start

Studies here are slow: one N-1 pass takes minutes, and a search over designs takes hours.
An agent that keeps going after the answer is in hand ends with nothing to show. These
rules decide how much to do.

1. **Answer the question asked, then offer.** Once the question is answered with evidence,
   report it. The diagnosis and quick checks that make the answer trustworthy are part of it
   (see *You are here to run studies*). A new long study is not: list it as a one-line offer
   and do not run it unasked.
2. **Estimate before any long study.** Before a study or search, estimate its minutes. Over
   15 minutes, say so and ask first. If you cannot ask (a headless run), spend at most half
   your time on it, then report the best result so far. Never spend the whole budget on a
   search and report nothing.
3. **Design requests: one design that works, first.** For "connect these loads", "design
   …", "the cheapest …", first build one design that solves in AC, serves the load (read the
   MW back), and passes N-1. Cost it and report it. That is a deliverable. Improving it is an
   offer. If the user explicitly wants the cheapest, search only a candidate set you name,
   and report "best of the N tried, not proven optimal".
4. **Vague requests get an audit and one question.** For "fix my case", "check this" or
   "improve it", run the [case audit](skills/case-audit/SKILL.md), list what it found grouped
   by cause, and ask one question with a default ("fix the islanded loads first?"). Do not
   pick a criterion yourself and run a study on it.
5. **Out of scope means stop.** If the task needs something this base does not cover (see
   *Reporting back*), say so in your first lines and stop **before running anything**.
   "Not covered" means theory with no procedure page here. If a page shows how to run it
   (N-1 contingency analysis, a DC or AC OPF, a time step), it is in scope.
   Offer what you can do instead. Starting it anyway costs the user time and a working
   answer.
6. **A wrong premise: show the evidence, propose the fix, ask.** If the request rests on
   something false ("the contingency list is huge" when it is in fact incomplete), say so in
   the first line and **prove it with a table**: the counts, and the specific items behind
   them (for example every in-service branch in the area that has no outage). Then propose
   the concrete fix ("I can build the complete N-1 set for Far West and West, about N
   outages. Go ahead?") and wait for approval before building it. If asked for something
   safe that still makes sense (a smaller list), deliver it, verified, beside the evidence.
7. **N-1 for a region needs that region's outages.** Monitoring an area is not testing it.
   Before solving "N-1 for West", count the outages whose elements sit in each area asked
   about, and assert each count is non-zero and plausible against that area's in-service
   branches. See [methods/new-device-contingency-aux.md](methods/new-device-contingency-aux.md).

## Task routing

| The user wants… | Read |
|---|---|
| To know which PowerWorld version is needed | [concepts/version-requirements.md](concepts/version-requirements.md) |
| To know what a term or acronym means | [concepts/glossary.md](concepts/glossary.md) |
| To compare two cases / find what a plan builds | [demos/comparing-planning-cases.md](demos/comparing-planning-cases.md) |
| To fix violations, not just report them | [demos/violation-remediation.md](demos/violation-remediation.md) |
| To make a large case N-1 clean, round after round | [methods/remediating-n1-contingency-violations.md](methods/remediating-n1-contingency-violations.md) |
| To fix intact-case (N-0) voltage or thermal violations cheaply | [methods/remediating-base-case-violations.md](methods/remediating-base-case-violations.md) |
| Why a contingency did not solve | [methods/diagnosing-a-non-converging-contingency.md](methods/diagnosing-a-non-converging-contingency.md) |
| Who picks up lost generation in a contingency (participation factors) | [concepts/agc-participation-factors.md](concepts/agc-participation-factors.md) |
| How big a new transformer should be | [concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md](concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md) |
| To delete dead buses that inflate islanding or N-1 counts | [methods/removing-empty-buses.md](methods/removing-empty-buses.md) |
| To review a design against a brief before presenting it | [methods/reviewing-a-design.md](methods/reviewing-a-design.md) |
| Which loads go radial or get cut off by one outage | [methods/finding-and-fixing-radial-by-n1-pockets.md](methods/finding-and-fixing-radial-by-n1-pockets.md) |
| Load served differs from the load entered | [methods/zone-load-multiplier-trap.md](methods/zone-load-multiplier-trap.md) |
| To see violations or islanding on a map | [methods/violation-network-map.md](methods/violation-network-map.md), built by the `violation-map` skill |
| Which object, field or command to use, and what the kit says about it | `python "$KIT/skills/schema-lookup/engine/lookup.py"`, see [skills/schema-lookup/SKILL.md](skills/schema-lookup/SKILL.md) |
| Whether a case is sane and ready for a study, with a case summary | `python "$KIT/skills/case-audit/engine/audit.py"`, see [skills/case-audit/SKILL.md](skills/case-audit/SKILL.md) |
| A worked example of any of this | [demos/start-here.md](demos/start-here.md) |
| **Anything to fail, at any point** | [methods/handling-errors.md](methods/handling-errors.md) |
| Anything at all, first | [methods/preflight-powerworld.md](methods/preflight-powerworld.md) |
| Open a case, read data, solve power flow | [methods/esapp-overview.md](methods/esapp-overview.md) |
| To know what esapp can do | [concepts/esapp.md](concepts/esapp.md) · [concepts/esapp-environment.md](concepts/esapp-environment.md) |
| Weather data downloaded | [methods/teamoverbyeweather-client.md](methods/teamoverbyeweather-client.md) |
| Hourly renewable output from weather | [concepts/timestep-workflow.md](concepts/timestep-workflow.md) → [methods/timestep-simulation-setup.md](methods/timestep-simulation-setup.md) |
| To read timestep result CSVs | [methods/how-to-analyze-results.md](methods/how-to-analyze-results.md) |
| To add buses, lines, loads, generators | [methods/adding-devices-esapp.md](methods/adding-devices-esapp.md) |
| To apply a dispatch to a case | [methods/applying-a-dispatch-to-a-case.md](methods/applying-a-dispatch-to-a-case.md) |
| To save a case to disk | [methods/save-powerworld-case.md](methods/save-powerworld-case.md) |
| Contingency analysis results | [methods/reading-violationctg.md](methods/reading-violationctg.md) |
| A contingency set for chosen devices | [methods/new-device-contingency-aux.md](methods/new-device-contingency-aux.md) |
| Devices ranked by violation severity | [methods/ranking-new-devices-by-severity.md](methods/ranking-new-devices-by-severity.md) |
| To change limit-monitoring thresholds | [methods/powerworld-limitset-setdata.md](methods/powerworld-limitset-setdata.md) |
| To reclassify lines as transformers | [methods/converting-lines-to-transformers.md](methods/converting-lines-to-transformers.md) |
| To drive Simulator without SimAuto, by dropping aux files | [methods/aux-file-mode.md](methods/aux-file-mode.md) for the rules and a working template; [concepts/powerworld-script-transfer.md](concepts/powerworld-script-transfer.md) for how the channel itself works. Read the first one before writing a script |
| A SCRIPT action but does not know its name | [references/aux-script-commands.md](references/aux-script-commands.md), then call the esapp method of the same name (code rule 4) |
| Exact field names and signatures | [references/esapp-schema-reference.md](references/esapp-schema-reference.md) |

## Rules that apply to every line of code you write

These are not style preferences. Each one fails **silently** — no exception, no warning,
just a wrong answer or a write that did nothing.

1. **Keep key fields in any DataFrame you write back.** `BusNum` for a bus, `BusNum` +
   `GenID` for a generator, bus pair + circuit for a branch. Without them PowerWorld
   cannot tell which row you mean and the write is a no-op that reports success.

2. **`pw[Obj, field] = values` is positional over the whole table.** The two write forms
   behave differently, and mixing them up is how a write silently hits the wrong objects:

   - `pw[Obj, field] = values` — **positional, whole table.** A scalar broadcasts to every
     object of that type; a list must be one value per object, in table order. There is no
     row matching here, so a list built from a filtered subset lands on the wrong rows.
     Build the full column and assign that.
   - `pw[Obj] = df` — **matched by key field.** A filtered subset is fine and correct:
     writing 3 rows changes exactly those 3 objects, provided the DataFrame carries a
     complete key set (rule 1).

   So "filter, then write" works — just do it with the DataFrame form, not the field form.

3. **Prefer `esapp` over the standalone `esa` package.** Same SimAuto underneath, better
   documented. Do not mix them.

4. **Call the named esapp method, not a hand-written script string.**

   ```python
   pw.esa.TimeStepDoRun()                          # correct
   pw.esa.RunScriptCommand("TimeStepDoRun;")       # wrong
   ```

   esapp 0.2.1 wraps **310 SCRIPT commands** as typed methods across 20 SAW mixins —
   roughly 300 of the ~370 actions Simulator defines. Both forms reach the same COM call, so the
   win is not runtime validation: it is a Python-side signature check, correct argument
   building (bracket lists, quoting, filter and solver enums), and above all **one place
   the maintainer can patch when PowerWorld changes a command's syntax.** A hand-written
   string is a call site nobody can reach. The dangerous case is not a command that
   disappears — that raises — but one whose parameter order or meaning changes, so the
   string "succeeds" and does the wrong thing.

   Use `RunScriptCommand` only where no wrapper exists — about 41 actions, mostly
   oneline/GUI (`OpenOneline`, `ExportOneline`), dialogs, and a few writers. Check the
   command against esapp's own method list before concluding a wrapper is missing —
   absence from `references/aux-script-commands.md` proves nothing, since that page is a
   working subset. Leave a comment saying why whenever you do fall back to a string.

5. **`SaveCase` is the exception, and it is not one of the 310.** esapp routes it through
   COM, not the script builder, and `pw.esa.SaveCase(...)` is a **silent no-op** — returns
   success, writes no file. **`pw.save(...)` is the same trap**: it is a one-line
   passthrough to `esa.SaveCase`, so it also writes nothing and says nothing. The no-op is
   below esapp — the raw `SimAuto.SaveCase(path, "PWB", True)` returns `('',)`, SimAuto's
   success value, and creates no file. Use the script form, exactly two parameters, and
   assert the file exists:

   ```python
   pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
   assert os.path.exists(out), "SaveCase reported success but wrote nothing"
   ```

   `OpenCase` and `CloseCase` are likewise absent from the SCRIPT index.

6. **A DC solve always reports zero mismatch.** It cannot tell you a generation schedule
   is short — the slack bus absorbs the shortfall. Check the schedule against total load
   directly, never the post-solve mismatch.

7. **Use absolute paths.** Relative paths resolve against PowerWorld's working
   directory, not your script's.

8. **Clear contingency results before solving.** They persist stale inside the `.pwb`,
   so a fresh-looking read can be from a previous run.

9. **`UserWarning: Read-only field(s)` is usually wrong — do not code around it.** On
   esapp 0.2.1 a write to a field its generated schema calls read-only **warns and then
   writes anyway**. The schema keeps only fields Simulator reports as unconditionally
   `enterable` and drops every conditional one, so it under-reports badly: 112 `Branch`
   fields, 33 `Bus`, 5 `Gen` (including `GenMVR`), 1 `Load`. `Branch.LineStatus` is the
   one you will hit first — PowerWorld's own answer is *"Depends: Normally enterable except
   when field Lockout is YES"*, and `pw[Branch, 'LineStatus'] = 'Open'` works.

   Ask PowerWorld, not esapp:

   ```python
   fl = pw.esa.GetFieldList('branch')     # 'enterable' is PowerWorld's answer
   fl[fl.internal_field_name == 'LineStatus'][['enterable']]
   ```

   A genuinely read-only field has `enterable` blank (e.g. `Shunt.SSMinMVR`) and its write
   vanishes with no error. Both directions therefore land in the same place: **assert the
   effect — read the field back and compare — never the absence of an exception** (see
   *When something goes wrong* below). And never run under `-W error::UserWarning`: it
   converts these false alarms into hard failures on code that works.

## This machine is shared

Other people and other agents run PowerWorld and Python on the same machine. **Never kill a
process by name**: no `Stop-Process -Name`, no `Get-Process python | Stop-Process`, no
`taskkill /IM`, no `pkill`. Each of those takes down work that is not yours. Record the PID of
anything you start and stop only those PIDs (`Stop-Process -Id <pid>`). Never kill a
`pwrworld.exe` you did not start: you cannot tell whose it is.

**Never install or upgrade packages on your own.** If an import fails, check first that you
did not run Python with `-I` (isolated mode hides user-installed packages such as esapp),
then tell the user to run `/powerworld-hivemind:powerworld-setup`. A `pip install` on a shared
machine changes everyone's environment.

## When something goes wrong

Read [methods/handling-errors.md](methods/handling-errors.md). The short version: most
failures are yours to fix silently — a missing package, a wrong access path, a field name
you guessed. Fix them and keep going; the user asked for an analysis, not a debugging log.

Stop and ask in exactly three cases: the SimAuto licence is missing (no code change can
fix it), the action is destructive, or it is a genuine modelling decision.

**And the harder case: PowerWorld often fails without failing.** It accepts a malformed
request, reports success, and does nothing. Assert the *effect* — count objects before
and after — never the absence of an exception. See
[demos/adding-a-device.md](demos/adding-a-device.md) for a real three-failure run.

## Reporting back

Say which pages you used. If your answer turns out to be wrong, that makes it traceable
to a specific page rather than to "the AI got it wrong" — which is how this knowledge
base gets fixed.

State plainly when something is outside what these pages cover. This kit is about
**PowerWorld automation** — operating Simulator from Python. It does not cover
contingency analysis fundamentals, OPF formulation, PV/QV curve studies, transient
stability theory, or weather science such as dynamic line ratings and IEEE 738 thermal
modelling. Say so rather than improvising, and do not run the out-of-scope study anyway
(rule 5 of *Scope the work before you start*).

## Filing a defect against this knowledge base

The two reports worth making, both rare:

1. **No page covers it.** Only after searching `concepts/`, `methods/`, `demos/` and
   `references/` on both the plain-English and the identifier phrasing and finding
   nothing. A routing-table miss is not evidence of absence — see the false-absent rule
   above. Between `esapp-schema-reference.md` and `aux-script-commands.md` the API surface
   is close to fully covered, so a genuine gap is unusual and therefore worth recording.
2. **A page is wrong.** You followed it, the code failed or returned a wrong answer, and
   re-reading it did not resolve the failure. This is the more valuable report: every page
   here exists because someone lost time to the thing it documents.

**Offer the report. Do not file one on your own.** Build a pre-filled link and hand it to
the user, who clicks it, reviews the issue on GitHub, and submits:

```
https://github.com/ChunSikPark/PoWerHiveMind/issues/new?title=TITLE&body=BODY&labels=LABEL
```

Percent-encode `TITLE` and `BODY`. Use `Page wrong: methods/<page>.md` or
`No page: <topic>` as the title and `page-defect` or `missing-page` as the label, plus a
second label for the page's `topic:` slug (or, for a missing page, the topic it would belong
under), e.g. `labels=page-defect,scripting`. The body
should carry: the page you followed, the code you ran, what PowerWorld did instead of what
the page predicted, the Simulator build date from preflight, and the esapp version. Keep it
compact — a URL past roughly 8,000 characters will not open, so link to a gist or ask the
user to paste a long traceback into the issue themselves.

If `gh` is installed and authenticated on this machine, this files it in one step:

```bash
gh issue create --repo ChunSikPark/PoWerHiveMind \
  --title "Page wrong: methods/save-powerworld-case.md" \
  --label page-defect --label scripting --body "..."
```

**Either way, show the user the exact text first and say that the tracker is public.** A
traceback carries case filenames, bus numbers, and substation or utility names, and the
cases this kit drives are frequently CEII or otherwise restricted. Let the user edit the
text or decline entirely; a report is never worth leaking a case.

Before reporting a page wrong, rule yourself out: re-read the page in full, confirm you
kept the key fields, and confirm you asserted the effect rather than the absence of an
exception. Most first-guess "the page is wrong" turns out to be one of those three.

## What you cannot do here

PowerWorld automation needs Windows, an installed Simulator, and a **separately licensed
SimAuto add-on**. If preflight fails on the licence check, no code change fixes it.

Fetching weather data and inspecting PWW files is pure Python and works anywhere — see
[methods/teamoverbyeweather-client.md](methods/teamoverbyeweather-client.md). But
*applying* that weather needs PowerWorld, because TimeStep runs inside Simulator.
