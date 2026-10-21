---
type: method
domain: tooling
topic: scripting
aliases: [aux-file-mode, aux-mode, no-python-mode, powerworld-llm-interaction,
  llm-interaction-programming, drop-file-mode, agent-operating-mode]
tags: [powerworld, aux, script-transfer, llm, agent, operating-mode, template]
---

# Aux-file mode: PowerWorld and LLM interaction through files

## Abstract

A working mode where the exchange between an agent and Simulator is files, not function
calls: the agent writes a `.aux`, drops it in a folder Simulator watches, and reads the
results back out of CSVs. No code of yours talks to PowerWorld, but plenty of code runs on
your side, parsing the log and the CSVs, because that is the only way to find out what
happened. It costs you return values, branching, headless operation and the ability to test
your own work. This page is the setup handshake, the rules, and a working template to copy.

## Connections

- **Up:** [Home](../index.md)
- **The channel:** [powerworld-script-transfer](../concepts/powerworld-script-transfer.md),
  how the drop folder works
- **The language:** [aux-only-powerworld](../concepts/aux-only-powerworld.md), what a `.aux`
  can do unaided, and the syntax traps
- **The alternative:** [esapp](../concepts/esapp.md), the Python mode this one replaces
- **Command names:** [aux-script-commands](../references/aux-script-commands.md)
- **Build floor:** [version-requirements](../concepts/version-requirements.md)

## Content

### What this mode is for

This is **PowerWorld and LLM interaction programming**: the unit of exchange between the
agent and Simulator is a file, not a function call. The agent writes a script, you drop it
in, Simulator runs it and writes back. Both sides read the same artifacts.

That shape has its own advantages, independent of tooling:

- **Everything is inspectable.** The script, the log and the results are all files on disk
  that you can read, diff, archive and send to someone. There is no opaque call whose
  behaviour you have to take on trust.
- **The human is in the loop by construction.** You see every script before it runs. For work
  that edits a case, that is a feature rather than friction.
- **The deliverable is the script.** What the agent produces is a `.aux` you keep and re-run
  yourself, not a transcript of an API session that only existed once.
- **No code of yours touches PowerWorld.** Nothing imports a COM library, nothing holds a
  handle on Simulator, nothing can leave it in a state you did not ask for.

That last point draws a boundary around PowerWorld, not around code in general.

### You still write code, it just runs on your side

This mode is not "no scripting". The log is English prose and the answers are in CSVs, so
the caller does real work to find out what happened, and an agent working this way writes and
runs that code constantly. Four jobs:

- **Delivery.** Copy the file in, poll for the input file to disappear, and pull your own
  file on a timeout. A run that fails the wrong way is never cleaned up, so without a timeout
  you wait forever while Simulator re-executes it.
- **Reading the outcome.** Grep the output for the trailing `finished successfully in N
  seconds`, then for `Successful Power Flow Solution`, then for `Warning:` lines. An unknown
  field name is a warning rather than an error, so the column goes missing from the CSV while
  the run reports success.
- **Getting the answer.** Load the CSVs and diff them. The log never contains the answer.
- **Validating before you drop.** Check the object types and field names against PowerWorld's
  field export, and check that every `DATA` block carries its full key, before the file goes
  in. A bad name costs a re-execution loop and a manual recovery; catching it costs a lookup.

Code on your side, files across the boundary. What you give up is an automation surface into
Simulator, not automation.

Use [esapp](../concepts/esapp.md) when you want speed and automation: it returns real values,
branches on them, runs headless and in parallel, and needs nobody to move a file between
steps.

Pick one and stay in it. An aux deliverable that was secretly debugged through the Python
path is no longer a self-contained script, and nobody finds that out until someone else runs
it.

> **On licensing, be careful what you claim.** Published material describes this channel as
> needing no COM and no SimAuto call. What has *not* been established here is whether a
> Simulator install lacking the SimAuto add-on will run dropped scripts. The script actions
> are the same action set SimAuto invokes, and where the licence check sits is an open
> question. Do not sell this mode as a licence workaround until someone has tested it on a
> machine without the add-on. Treat it as an interaction pattern.

### Step 1 — the setup handshake

Five things have to happen in the GUI, and an agent cannot do any of them. If you are an
agent entering this mode, your first output is these five steps with the real folder path
filled in, before you write a single line of aux:

1. Open Simulator.
2. **Load the case by hand.** Do not script this; see the `OpenCase` warning below.
3. **Switch to Run Mode**, then Tools → Script. Set *ScriptTransferFileDirectory* by
   browsing to the folder **they chose**. Run Mode at this step is specified by the source
   deck.
4. Tick **Enabled External Script Control**, and leave that dialog open.
5. **Click Show Log** in that dialog, and keep the log window visible.

After that, any file copied into the folder as `SimulatorScriptInput.aux` runs automatically,
one poll interval later.

Step 5 earns its place. The output file appears only once a run finishes, so for every
failure that never finishes (an abort, a loop, a poller that is not running) the folder stays
silent and the log is the only thing that says which one you have. A looping run shows the
same block of lines once per poll interval.

Two things here cost time when you do not know them:

- **The settings persist in the registry, the dialog does not.** The panel says so itself:
  its heading reads *External Script Control (Only Active when Dialog is Open; Fields Saved
  in Registry)*. `ScriptTransferFileEnabled`, `ScriptTransferFileDirectory` and
  `ScriptInputOutputPollSec` survive a restart, so the browsing step is once per machine.
- **Tick `Always Delete an Invalid Input Aux File` while you are in there.** It makes
  Simulator discard a script it cannot parse rather than leaving it in the folder to be
  retried. It is not a complete guard against the re-execution loop, since a script can parse
  cleanly and still fail mid-run, but it removes the most common cause.
- **Closing the dialog stops the poller while the flag still reads enabled.** The dropped
  file sits there, which looks exactly like a crash, a failed run, and a run still in
  progress. If a drop is not picked up, check the dialog before you debug the aux.

Once the user confirms the setup, the agent should propose a device scan without being
asked, **then stop and wait for an answer:**

> *"Channel is live. I cannot see your case from here. Do you want me to scan it first and
> list what devices are in it? It is read-only, it writes CSVs and changes nothing."*

**Ask which folder. Do not pick one.** The transfer folder is the user's choice — they may
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

**Propose, then wait. Do not drop the file until they answer.** Volunteering the idea is the
helpful part; running it unasked is not. The user is sitting in front of a live Simulator
with their own case loaded, and a dropped script executes against it the moment it lands —
so the first drop of a session is theirs to approve, even when it only reads.

Until that runs the agent knows nothing about the case: not the bus numbers, not whether
there are transformers, not whether a contingency set already exists. Anything it proposes
beforehand is a guess, and one read-only drop replaces all of it. See
[aux-file-cookbook](../demos/aux-file-cookbook.md) for the script and how to read what comes
back.

### Step 2 — deliver by copy, never by authoring in place

Write the aux somewhere else, then copy it in as `SimulatorScriptInput.aux`. The poller
cannot tell a finished file from one still being written, and a truncated aux stays valid up
to the cut, so authoring in place races the poll interval and can feed Simulator half a
script that runs and reports success.

Simulator deletes the input file once it has read it. That deletion is the acknowledgement,
which means the script destroys itself. Archive a copy before you drop it, or you end up with
results and no record of what produced them.

### The rules

**Never:**

- **`OpenCase`.** It raises an access violation, aborts the file, and the poller then re-runs
  it every interval *forever*. Measured 2026-09-21 with a file containing nothing but
  `OpenCase` and three log markers, on a freshly started Simulator with no case loaded, so
  this is not a case-swap problem. Load the case by hand. `CaseSummaryGet` on a named `.pwb`
  works fine, so you can read a case file, just not load one.
- **`LogClear`.** Anywhere in a dropped file it suppresses `SimulatorScriptOutput.txt`
  entirely: the script runs and the channel returns nothing.
- **A `("", STOP)` failure slot**, unless you mean it. A file that stops early is never
  consumed, so it loops.
- **Writing a derived field to cause a state.** A status field that *reports* a condition
  cannot set it. `BusStatus` is the classic: PowerWorld's field export leaves its `Enterable`
  column empty, so writing it is a no-op that still reports success. Open the branches and call
  `UpdateIslandsAndBusStatus`; the status follows.

**Always:**

- **Get a yes before the first drop of a session.** The user is at a live Simulator with
  their case loaded, and the file runs the moment it lands. Show the script, say what it
  does, wait. Read-only follow-ups after that first yes are fine; anything that modifies the
  case needs its own.
- **Read back.** The channel returns a log transcript, not a return value. If the answer
  matters, `SaveData` it to CSV and read the CSV. `Simulation: Successful Power Flow Solution`
  is worth grepping for, but its absence is not a diagnosis.
- **Carry the key fields** in every table you write or intend to write back: `BusNum`+`GenID`,
  `BusNum`+`BusNum:1`+`LineCircuit`, `BusNum`+`ShuntID`. Drop one and PowerWorld cannot tell
  which row you mean; the write no-ops and reports success.
- **Get field names from PowerWorld's own field export**, never from the manual and never from
  memory. The *Auxiliary File Format* manual has no per-object field catalog. The vocabularies
  also differ between the Python and aux sides: a Python class name is not always the aux
  object type, and using one for the other is a hard validation error.

**Cannot, and say so rather than fake it:**

- Return a value, or branch on a result. There is no query-then-act, so a choice that depends
  on the case is made by a human reading an exported CSV between two runs. Asked to "pick one
  at random", say the language has no RNG and no variables, and expose the choice as an edit
  point instead of hardcoding a pick and calling it random.
- Run headless, batched or in parallel. A visible dialog is required.
- **Make Simulator run anything.** An agent writes a file; Simulator picks it up on its own
  poll interval. Whether the agent can *trigger* a run depends on access, not on the mode: if
  it can write to the watched folder it drops its own scripts and reads its own results, and
  if it cannot, every run waits on a human. Either way, reaching for the Python channel "just
  to check" has left the mode. Validate statically before dropping (object types, field names,
  full keys on every `DATA` block), because a bad name costs a re-execution loop whoever
  drops it.

### Knowing whether it worked

A completed run writes `SimulatorScriptOutput.txt`, framed like this:

```
Automatic loading of file ...\SimulatorScriptInput.Aux started at 2026-09-21T14:43:01.314Z
Starting load of auxiliary file: ...\SimulatorScriptInput.Aux
  ... your LogAdd markers and PowerWorld's own lines ...
Finished load of auxiliary file: ...\SimulatorScriptInput.Aux
Automatic loading of file finished successfully in 0.083 seconds
```

That trailing line is the completion signal, and it is parseable. Typical round trips are
0.08–0.5 s for a small case.

The failure shape is the input file still sitting there with no output file written. That
happens on an abort, and, measured 2026-09-21, it also happens on a fully successful run that
called `OpenCase`: all stages ran, both solves converged, every output file was correct, zero
errors logged, and the poller still re-ran the whole thing five times. Any harness must pull
its own input file on a timeout rather than wait for a signal that is not coming.

### CaseSummaryGet describes the file, not your edits

`CaseSummaryGet` with a blank first argument describes the `.pwb` file behind the current
case rather than the case as you have edited it. The spec says "the pwb file for the current
case" and means it literally. Unsaved in-memory changes are invisible to it, so diffing two
summaries across an unsaved edit shows no difference at all, which reads exactly like a
change that never happened. Read the CSVs.

### Template

A complete working file. It identifies the loaded case, surveys the folder for other cases,
baselines, opens a bus by opening the branches that touch it, solves, and restores. Change the
two marked lines to match your own case and it runs.

```
//=============================================================================
// Identify the case -> baseline -> open a bus -> solve -> restore.
// Read-only on disk: edits memory, never calls SaveCase.
//
// BEFORE DROPPING:
//   1. Load the case by hand. Stage E names its bus numbers.
//   2. Tools -> Script open, "Enabled External Script Control" ticked.
//   3. Copy in as SimulatorScriptInput.aux. Never author in place.
//
// FOUR RULES (each a silent failure if ignored):
//   - No OpenCase. Access violation, then the poller re-runs the file forever.
//   - No LogClear. It suppresses SimulatorScriptOutput.txt entirely.
//   - CaseSummaryGet reads the .pwb FILE, not your edited case.
//   - BusStatus is derived, not settable. Open the branches, not the bus.
//=============================================================================


//--- A: output folder --------------------------------------------------------
SCRIPT
{
  // <<< EDIT: where the CSVs go, under the folder you chose. YES = create it if absent.
  SetCurrentDirectory("<your transfer folder>\out", YES);
  LogAdd("A1 output dir set");
  LogAddDateTime;
}


//--- B: what case is loaded? -------------------------------------------------
SCRIPT
{
  // Blank name = the file behind the current case. Detail 3 = the most fields.
  CaseSummaryGet("", "01_case_identity.txt", 3);

  // "# of Breakers" decides how you open a bus:
  //   0  -> bus-branch. Open the incident branches (stage E).
  //   >0 -> node-breaker. Use OpenWithBreakers instead.
  LogAdd("B1 01_case_identity.txt -- check '# of Buses' and '# of Breakers'");
}


//--- C: survey the folder ----------------------------------------------------
SCRIPT
{
  // Reads .pwb files WITHOUT opening them -- identify a case with no OpenCase.
  // <<< EDIT: the folder to survey.
  CaseDirectorySummaryGet("<your transfer folder>", NO,
                          "00_directory_survey.txt", 1);   // NO = skip subfolders
  LogAdd("C1 00_directory_survey.txt");
}


//--- D: baseline -------------------------------------------------------------
SCRIPT
{
  EnterMode(RUN);
  SolvePowerFlow(RECTNEWT);     // no ("",STOP) slot: a bad solve is a result
  LogAdd("D1 base solve -- grep above for 'Successful Power Flow Solution'");

  SaveData("base_bus.csv", CSV, Bus,
           [BusNum,BusName_NomVolt,BusStatus,BusSlack,BusPUVolt,BusAngle,BusGenMW,BusLoadMW],
           [], "", [], NO, NO);

  // Read this file to choose the bus for stage E. Aux has no RNG.
  SaveData("base_branch.csv", CSV, Branch,
           [BusNum,BusNum:1,LineCircuit,LineStatus,LineMW,LineMVA,LinePercent],
           [], "", [], NO, NO);
  LogAdd("D2 base_bus.csv + base_branch.csv");
}


//--- E: open the bus ---------------------------------------------------------
// <<< EDIT: one line per branch touching your chosen bus, from base_branch.csv.
// KEY = BusNum + BusNum:1 + LineCircuit. All three, or the write no-ops and
// still reports success.
// Pick a bus with gen and load that is NOT the slack, so the case still solves.
DATA (Branch, [BusNum,BusNum:1,LineCircuit,LineStatus])
{
2 4 "1" "Open"
3 4 "1" "Open"
4 5 "1" "Open"
}

SCRIPT
{
  UpdateIslandsAndBusStatus;    // without this the bus stays "Connected"
  LogAdd("E1 branches opened, islands updated");

  // Proof the flip is topological: the bus is already dead here, no solve yet.
  SaveData("pre_solve_bus.csv", CSV, Bus,
           [BusNum,BusName_NomVolt,BusStatus,BusPUVolt,BusGenMW,BusLoadMW],
           [], "", [], NO, NO);
  LogAdd("E2 pre_solve_bus.csv -- bus Disconnected BEFORE any solve");
}


//--- F: solve and read back --------------------------------------------------
SCRIPT
{
  SolvePowerFlow(RECTNEWT);
  LogAdd("F1 post-outage solve");

  SaveData("post_bus.csv", CSV, Bus,
           [BusNum,BusName_NomVolt,BusStatus,BusSlack,BusPUVolt,BusAngle,BusGenMW,BusLoadMW],
           [], "", [], NO, NO);
  SaveData("post_branch.csv", CSV, Branch,
           [BusNum,BusNum:1,LineCircuit,LineStatus,LineMW,LineMVA,LinePercent],
           [], "", [], NO, NO);

  // Wrong on purpose: shows the as-saved totals, not the outaged ones.
  CaseSummaryGet("", "03_summary_AFTER_outage.txt", 3);

  LogAdd("F2 post_bus.csv + post_branch.csv written");
  LogAdd("F3 ANSWER = diff base_bus.csv vs post_bus.csv");
}


//--- G: restore --------------------------------------------------------------
DATA (Branch, [BusNum,BusNum:1,LineCircuit,LineStatus])
{
2 4 "1" "Closed"
3 4 "1" "Closed"
4 5 "1" "Closed"
}

SCRIPT
{
  UpdateIslandsAndBusStatus;
  SolvePowerFlow(RECTNEWT);
  SaveData("restored_bus.csv", CSV, Bus,
           [BusNum,BusName_NomVolt,BusStatus,BusSlack,BusPUVolt,BusAngle,BusGenMW,BusLoadMW],
           [], "", [], NO, NO);

  // Matches base_bus.csv on status and voltage. Angles differ in the 5th
  // decimal -- solver tolerance from a different start point, not a failure.
  LogAdd("G1 restored, re-solved, restored_bus.csv");
  LogAddDateTime;
  LogSave("run.log.txt", NO);
}
```

### What that template produces

On the 7-bus sample this was measured on, the outaged bus carried 93.71 MW of generation and
80 MW of load. Your numbers will differ. The result is visible in one diff:

| | base | post-outage |
|---|---|---|
| bus 4 status | `Connected` | `Disconnected` |
| bus 4 voltage | 1.000000 pu | 0.000000 |
| bus 3 voltage | 0.992669 pu | 0.961330 |
| slack output | 200.63 MW | 215.83 MW |
| worst branch loading | 68.7 % | 91.9 % |

Only one surviving bus moves, because it was the one leaning on the outaged bus's local
generation. The five voltage-controlled buses hold their setpoints exactly.

The restore returns every bus to `Connected` with voltage magnitudes identical to six decimals.
Angles differ in the fifth decimal and the slack by about a kilowatt: Newton–Raphson
converging from the outaged solution rather than the loaded state. **That is solver tolerance,
not a failed restore**, and expecting an exact match will make a correct run look broken.
