---
name: powerworld
description: "Use when working with PowerWorld Simulator, .pwb case files, SimAuto, or the esapp Python package - opening or modifying cases, solving power flow, adding buses/lines/generators, applying a dispatch, contingency analysis and violation reports, saving cases, and PowerWorld SCRIPT/aux actions. Also covers PowerWorld's built-in weather features: PWW weather files, TimeStep simulation for hourly renewable generator output, and fetching the .pww files those need via the TeamOverbyeWeather client. Also fires on power-system study work phrased without any tool name: overloaded or heavily loaded branches, N-1 violations and what caused them, comparing two planning cases or vintages, what a transmission plan builds, testing whether a new line or reinforcement helps, hourly wind and solar output from weather, and applying a dispatch."
topic: agents
---

# PowerWorld expert

A knowledge base of PowerWorld Simulator automation. Most PowerWorld mistakes are silent;
this records them.

## Where these pages live

Every path on this page (`concepts/`, `methods/`, `demos/`, `references/`, `index.md`,
`AGENTS.md`) is relative to the **kit root**, never to the user's working directory.

Installed as a Claude Code plugin, the kit root is `${CLAUDE_PLUGIN_ROOT}`. Resolve it once
at the start of the session and prefix every path below with it
(`${CLAUDE_PLUGIN_ROOT}/methods/preflight-powerworld.md`), and scope every search to it.

Anywhere else (Codex, Cursor, or the kit copied into a project), the kit root is whichever
directory holds `AGENTS.md` alongside the four content directories. That is usually the
project root or a `PowerWorldHiveMind/` subdirectory of it. Find it once, then use it the
same way.

**Searching the working directory instead of the kit root is the one failure this skill
cannot survive**: it fires, sends you to a page, and the page is not there. If a path
below does not resolve, you have the wrong root. Find the root; do not conclude the page
is missing.

## Consult it before you reason

**Do not work PowerWorld problems out from first principles or from general API
intuition.** PowerWorld fails silently: it accepts a wrong call, reports success, and
returns a wrong answer. Nothing will prompt you to look something up.

- Open the relevant page **before** writing code, and say which page you followed.
- Code failed? Re-read the page before inventing a fix. The page usually already warned you.
- No page covers it? **Say so explicitly** and mark the answer as unsourced. Do not present
  a guess with the confidence of sourced work.
- Believe a page is wrong? Say so with evidence. Never silently override it.

## Before anything else

**Run the preflight** in `methods/preflight-powerworld.md` (under the kit root). Five
seconds, and it tells you whether this machine can drive PowerWorld at all. Record the
Simulator build date it prints, because behaviour shifts silently between versions
(`concepts/version-requirements.md`).

A preflight failure is a fact about the machine, not a bug in your code. Report which check
failed and stop. In particular the **SimAuto add-on is licensed separately from Simulator**,
so a healthy-looking installation can still run no automation at all.

## Finding the right page

**Search the four content directories first**: `concepts/`, `methods/`, `demos/`,
`references/`, all under the kit root resolved above. Search page text, not the catalog.
Put several terms in one pass and include both the plain-English phrasing and the
identifier it maps to ("save the case" *and*
`SaveCase`), then rank a page by how many terms land on it. Measured 2026-09-07 over 48 agents on 16
questions: search found the right page 10 times out of 16, the routing table 8, starting from
`index.md` 7.

Once you have the right page, **read its `## Content` in full.** The limit is on **breadth,
not depth**. Opening eight pages while hunting means your search terms were wrong, not that
you should read less of the page you found.

`AGENTS.md` at the kit root carries the full 28-row task-routing table and the rest of the
ladder. Use it and `index.md` as disambiguators when search comes back thin, never as the
first move: both name topics, and a topic is coarser than a page.

**Never conclude "not in the knowledge base" from a routing-table miss alone.** Report an
absence only after searching all four directories on both phrasings.

## Run studies, not queries

The user rarely wants a number; they want the work it is for. Diagnose before proposing, and
test before recommending. Group symptoms into causes, then test candidate fixes on a fresh
case each and measure. Reinforcing a network can make it worse, and reasoning will not tell
you which. Track count and severity separately; they disagree. Say what you rejected and what
you did not save. See `demos/violation-remediation.md`, where 2 of 5 plausible reinforcements
degraded N-1.

When you open a case, count the load and generation on buses that are not connected. An
islanded load keeps a closed status and the solve still converges, so a 0 pu bus is not
"just dead" until you have checked. If the count is not zero, it is your first finding.

## Scope the work before you start

Studies are slow, and an agent that keeps going after the answer is in hand ends with nothing
to show. `AGENTS.md` has the full rules; in short:

1. **Answer the question asked, then offer.** Diagnosis and quick checks are part of the answer;
   a new long study is a one-line offer. Don't run it unasked.
2. **Estimate minutes before a long study.** Over 15, say so and ask; if you can't ask, spend at
   most half your time on it and report the best result so far.
3. **Design requests: one working design first.** It must solve AC, serve the load (MW read back)
   and pass N-1, with its cost reported. Improving it is an offer. "The cheapest" means a named
   candidate set, reported as "best of N tried, not proven optimal".
4. **Vague requests** ("fix my case") get the case audit, findings grouped by cause, and one
   question with a default. Don't pick a criterion yourself and run a study on it.
5. **Out of scope means stop**, before running anything. Out of scope is theory with no procedure
   page here; if a page shows how to run it, it is in scope. See *Scope* below.
6. **A wrong premise: show the evidence, propose the fix, ask.** Say it's wrong, prove it with a
   table of the counts and the items behind them, offer the concrete fix, and wait for approval.
7. **N-1 for a region needs that region's outages**, not just its monitoring. Before solving,
   assert each area's outage count is non-zero and plausible against its in-service branches
   (`methods/new-device-contingency-aux.md`).

**This machine is shared.** Never kill a process by name (`Stop-Process -Name`,
`Get-Process x | Stop-Process`, `taskkill /IM`, `pkill`): it takes down other people's work.
Stop only the PIDs you started, and never a `pwrworld.exe` you did not start.

## Rules that fail silently

Apply these to every line of PowerWorld code you write. None raises an exception; each just
produces a wrong answer.

1. **Keep key fields** (`BusNum`, `GenID`, circuit id) in any DataFrame written back, or the
   write is a no-op that reports success.
2. **`pw[Obj, field] = values` is positional over the whole table.** Assigning to a filtered
   subset writes nothing.
3. **Call the named esapp method, not a hand-written script string.**
   `pw.esa.TimeStepDoRun()`, never `pw.esa.RunScriptCommand("TimeStepDoRun;")`. esapp 0.2.1
   wraps 310 SCRIPT commands. You get a typed signature and correct argument building, but
   the real reason is that a hand-written string is a call site nobody can patch when
   PowerWorld changes that command's syntax. Reach for `RunScriptCommand` only where no
   wrapper exists (~41 actions, mostly oneline/GUI and dialogs). Check esapp's own method
   list before concluding a wrapper is missing, and leave a comment saying why.
   Some demos and concept pages predate this rule and call `RunScriptCommand`; follow the
   rule, not the page.
4. **`SaveCase` is the exception.** It is a COM method, not one of the 310, and
   `pw.esa.SaveCase(...)` is a silent no-op: it returns success and writes nothing. Use the script
   form and assert the file exists:
   `pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')` (exactly two parameters).
5. **A DC solve always reports zero mismatch.** Check the generation schedule against load
   directly; the slack bus hides a shortfall.
6. **Clear contingency results before solving.** They persist stale inside the `.pwb`.
7. **Absolute paths only.** Relative paths resolve against PowerWorld's working directory,
   not yours.
8. **Write `esapp`, not the standalone `esa`.** Same SimAuto underneath, better documented;
   do not mix the two in one script.

**Assert the effect, never the absence of an error.** PowerWorld accepts malformed requests,
reports success, and does nothing. Count objects before and after.
`demos/adding-a-device.md` is a real run where three attempts silently created nothing.

When something does fail, `methods/handling-errors.md`. Fix missing packages and wrong access
paths yourself without narrating. Stop and ask only for a missing SimAuto licence, a
destructive action, a real modelling decision, or the aux-file-mode case below.

**In aux-file mode, ask before the first drop.** That mode is different from driving
Simulator yourself: the user is sitting in front of a live GUI with their own case loaded,
and every file you drop executes against it. Show them the script you propose to run, say
what it will do, and **wait for an answer before dropping anything**, including a read-only
scan. After they say yes once, read-only follow-ups need no further permission, but anything
that modifies the case gets its own yes.

**Ask which folder. Do not pick one.** The transfer folder is the user's choice. They may
already have one configured from a previous session, they may want it on a particular drive,
and on a shared or managed machine the obvious location may not be writable. Ask, and use the
answer verbatim. `<your transfer folder>` below stands for whatever they tell you; it is a
placeholder, not a suggestion.

**Two turns, never one.**

**Turn 1 — activation only.** List the setup steps, name the transfer folder, and **end the
message there.** Do not propose a script, do not name a file you would like to drop, do not
say "say the word and I will run X". The user has not opened the dialog yet; there is nothing
to consent to, and bundling the two makes them approve a drop before the channel exists.
Close with nothing more than: *tell me when the dialog is up.*

**Turn 2 — only after they say it is ready.** Now propose the first script, say what it
writes and that it is read-only, and wait again.

Collapsing these into one message is the most common way this goes wrong, and it reads as
pressure to skip the setup.

See `methods/aux-file-mode.md`.

## When this base is wrong or missing, report it

Two cases are worth a bug report, and both are rare enough to be signal:

- **No page covers it**, but only after you have searched all four content directories on
  both the plain-English and the identifier phrasing. A routing-table miss is not enough.
- **A page is wrong**: you followed it, the code failed or returned a wrong answer, and
  re-reading did not resolve it. Name the page and say what PowerWorld actually did.

**Offer the user a report; never file one silently.** Compose a pre-filled link and hand it
over; they click, review on GitHub, and submit:

```
https://github.com/ChunSikPark/PowerWorldHiveMind/issues/new?title=TITLE&body=BODY&labels=LABEL
```

URL-encode both fields. Title as `Page wrong: methods/<page>.md` or `No page: <topic>`;
label `page-defect` or `missing-page`. In the body put the page you followed, what you ran,
what PowerWorld did instead, the Simulator build date from preflight, and the esapp version.
Keep it short: an over-long URL will not open.

Where `gh` is installed and authenticated, `gh issue create --repo
ChunSikPark/PowerWorldHiveMind --title "..." --body "..."` files it directly. Still show the
user the exact text first.

**Show the text before anything is submitted.** A traceback can carry case filenames, bus
numbers, and substation or utility names, the tracker is public, and the cases this kit
drives are often CEII or otherwise restricted. State that it will be public, and let the
user edit it or decline.

## Scope

Covers PowerWorld automation, including its PWW/TimeStep weather features. Does **not** cover
contingency analysis fundamentals, OPF formulation, PV/QV curve theory, transient stability
theory, or weather science such as dynamic line ratings and IEEE 738. Say so rather than
improvising, and don't run the out-of-scope study anyway.

Cite which pages you used, so a wrong answer is traceable to a page that needs fixing.
