# PowerWorldHiveMind - DEMOS

# ==== adding-a-device.md ====

---
type: method
domain: tooling
topic: design
aliases: [demo-adding-device, add-line-demo, createdata-demo, silent-no-op-demo]
tags: [demo, esapp, createdata, branch, n-1, worked-example]
---

# Demo: Adding a line — and the silent failure that hides it

## Abstract

A complete worked run on the public synthetic Synth40 case (37 buses). **Everything below actually happened**,
including three failed attempts that raised no error at all. This is the single most
important demo in the kit: `CreateData` accepts a malformed call, reports success, and
creates nothing. If you read only one demo, read this one.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [adding-devices-esapp](../methods/adding-devices-esapp.md) · [handling-errors](../methods/handling-errors.md) · [esapp-environment](../concepts/esapp-environment.md)

## Content

### The user's prompt

> *"Add a line between bus 27 and bus 31 and tell me if it helps with N-1."*

That is all a user should have to say.

### Step 1 — establish the baseline

```python
from esapp import PowerWorld
from esapp.components import Branch, Bus, ViolationCTG

CASE = r"C:\path\to\Synth40.pwb"
pw = PowerWorld(CASE)
pw.pflow()

n0 = len(pw[Branch])
print("branches before:", n0)
```

```
branches before: 89
```

Baseline N-1, so there is something to compare against:

```python
pw.esa.RunScriptCommand("CTGClearAllResults")
pw.esa.RunScriptCommand("CTGAutoInsert")
pw.esa.RunScriptCommand("CTGSolveAll")
print("base violations:", len(pw[ViolationCTG, ["CTGLabel", "LimViolPct"]]))
```

```
base violations: 12
```

### Step 2 — three attempts that all "succeeded" and did nothing

These are the natural things to try. Each ran without raising:

```python
# attempt A
pw.esa.RunScriptCommand(
    'CreateData(BRANCH,[BusNum,BusNum:1,LineCircuit,LineR,LineX,LineC,LineLimMVA,LineStatus],'
    '[27,31,"9",0.01,0.05,0.0,100.0,"Closed"])')

# attempt B - fewer fields
pw.esa.RunScriptCommand(
    'CreateData(BRANCH,[BusNum,BusNum:1,LineCircuit,LineR,LineX],[27,31,"8",0.01,0.05])')

# attempt C - same thing, but inside EDIT mode
pw.edit_mode()
pw.esa.RunScriptCommand(
    'CreateData(BRANCH,[BusNum,BusNum:1,LineCircuit,LineR,LineX],[27,31,"7",0.01,0.05])')
pw.run_mode()
```

The observed result of all three:

```
  A: quoted circuit, Closed: no exception
     -> branches now 89
  B: no status field: no exception
     -> branches now 89
  C: in EDIT mode: no exception
     -> branches now 89
```

**No exception. No warning. No device.** The buses both exist, no branch 27–31 was
already there, and the call reported success three different ways.

An agent that trusts the absence of an error will now happily run N-1, get the same 12
violations, and report "adding this line does not help" — a conclusion drawn from a line
that was never added. That is the failure mode this whole knowledge base exists to
prevent.

### Step 3 — stop guessing, read the page

The fix is in [adding-devices-esapp](../methods/adding-devices-esapp.md), and it is not something you would arrive at by
trying variations:

1. Use the **`pw.esa.CreateData(...)` method**, not a `RunScriptCommand` string.
2. Supply **every** primary, secondary, and required field. For a `Branch` that means
   `BusName_NomVolt` for *both* ends, not just the bus numbers.
3. Supply **all three** MVA limits — `LineAMVA`, `LineAMVA:1`, `LineAMVA:2`. Giving only
   the A limit silently skips the branch.

```python
# build the name/nominal-voltage map first; both ends must resolve
nv = {int(r["BusNum"]): r["BusName_NomVolt"]
      for _, r in pw[Bus, ["BusName_NomVolt"]].iterrows()}

frm, to, mva = 27, 31, 100.0

pw.edit_mode()
pw.esa.CreateData(
    "Branch",
    ["BusNum", "BusName_NomVolt", "BusNum:1", "BusName_NomVolt:1", "LineCircuit",
     "LineR", "LineX", "LineAMVA", "LineAMVA:1", "LineAMVA:2", "LineStatus"],
    [frm, nv[frm], to, nv[to], "N1", 0.01, 0.05, mva, mva, mva, "Closed"])
pw.run_mode()

n1 = len(pw[Branch])
print(f"branches after: {n1}  (created {n1 - n0})")
assert n1 - n0 == 1, "CreateData silently skipped the device"
```

```
branches before: 89
branches after : 90   (created 1)
ASSERTION PASSED - device really created
```

### Step 4 — always assert the count

```python
expected = 1
assert n1 - n0 == expected, "CreateData silently skipped the device"
```

**Never skip this line.** It is the only thing standing between a silent no-op and a
confident wrong answer. Count before, count after, assert the difference. Do it for
every `CreateData` call, every time.

### Step 5 — answer the actual question

```python
pw.pflow()
pw.esa.RunScriptCommand("CTGClearAllResults")
pw.esa.RunScriptCommand("CTGSolveAll")
print("violations with the new line:", len(pw[ViolationCTG, ["CTGLabel", "LimViolPct"]]))
```

```
N-1 violations WITH the new line: 10  (base case was 12)
```

### What to report back

> Added a 69 kV line from bus 27 to bus 31 (circuit N1, R=0.01, X=0.05, 100 MVA on all
> three limits) and verified the branch count went 89 → 90.
>
> N-1 violations dropped from **12 to 10**. The line helps.
>
> The case was **not saved** — this ran in memory. Say the word and I will write it out.
>
> Pages used: `methods/adding-devices-esapp.md`, `methods/reading-violationctg.md`.

Note the last two points. Say plainly that nothing was written to disk, and cite the
pages so a wrong answer is traceable.

### The lesson

The correct call is not guessable. Three reasonable attempts failed identically and
silently.


---

# ==== aux-file-cookbook.md ====

---
type: reference
domain: tooling
topic: scripting
aliases: [aux-cookbook, two-window-workflow, script-transfer-walkthrough, first-drop,
  getting-started-aux, external-script-control-setup]
tags: [demo, aux, script-transfer, walkthrough, getting-started, two-window]
---

# Cookbook: Claude in one window, Simulator in the other

## Abstract

A start-to-finish walkthrough of the file-based workflow, written for someone sitting in
front of two windows. Four recipes, in order: turn the channel on, prove it is alive with a
four-line script (skip that one once you trust it), let the agent scan the case for its
devices, then change something and measure it. Every number here came from a real run on a
small sample case, failures included.

## Connections

- **Up:** [Home](../index.md)
- **The reference:** [aux-file-mode](../methods/aux-file-mode.md), the rules and the full
  template this page walks you through
- **The channel:** [powerworld-script-transfer](../concepts/powerworld-script-transfer.md)
- **The language:** [aux-only-powerworld](../concepts/aux-only-powerworld.md)
- **Other demos:** [start-here](start-here.md)

## Content

### How this works

Two windows, side by side: Simulator with your case open, and Claude. They never talk to
each other directly. They pass files through one folder you nominate.

Claude writes a script. You copy it into the folder. Simulator notices it, runs it, deletes
it, and writes back a log plus whatever CSVs the script asked for. Claude reads those. That
is the whole loop.

This page assumes you are the one moving the file, which is the case when Claude is somewhere
it cannot reach that folder. If Claude is running on the same machine and can write there, it
copies its own scripts in and reads its own results, and your job shrinks to the setup in
recipe 1. Simulator behaves the same either way: it polls the folder and picks up whatever it
finds.

You choose the folder. Any empty one will do, on any drive you can write to — and if
Simulator already has a transfer folder configured from an earlier session, use that one
rather than making a second. Decide now and tell Claude the full path; it should ask rather
than assume, and it has no way to see your filesystem layout.

Everything below writes `<your transfer folder>` where that path goes.

---

### Recipe 1 — Turn the channel on

Do this in Simulator. Claude cannot do any of it, and will ask you to.

**1. Open PowerWorld Simulator.**

**2. Open your case.** Any `.pwb` will do. The numbers further down came from a small 7-bus
sample, so yours will differ. Follow the shape of each step rather than the values.

**3. Switch to Run Mode, then open the Tools tab.** The source deck specifies Run Mode here.
Do not skip it and assume a script can switch modes for you later.

![The Tools tab in the ribbon](../assets/aux-step-tools.png)

**4. Click Script** to open the Script Command Execution Dialog.

![The Script button under the Tools tab](../assets/aux-step-script.png)

**5. Set ScriptTransferFileDirectory.** Click **Browse...** and pick your folder. The
screenshot below shows one machine's path; yours will differ, and that box is the
authoritative answer to "which folder is Simulator actually watching".

![The External Script Control panel with Browse highlighted](../assets/aux-step-browse.png)

Everything you need is on that one panel. Two things on it before you move on:

- The heading says **"Only Active when Dialog is Open; Fields Saved in Registry"**. That is
  the whole story on persistence: the folder and the tick survive a restart, the open dialog
  does not.
- **"Always Delete an Invalid Input Aux File"** makes Simulator throw away a script it cannot
  parse instead of leaving it in the folder. Leave it ticked. It does not cover everything
  (see [When it goes wrong](#when-it-goes-wrong)), but it removes the most common way a run
  gets stuck repeating.

**6. Tick Enable External Script Control.**

![The Enable External Script Control checkbox](../assets/aux-step-enable.png)

**7. Leave the dialog open.** Closing it stops Simulator watching the folder, and the settings
keep reading as enabled either way, so everything still looks configured while nothing
happens.

**8. Click Show Log** and keep that window where you can see it. Every script writes its
progress there as it runs.

![The Show Log button](../assets/aux-step-showlog.png)

Watch that log. The output file appears only once a run finishes, so while something is wrong
the folder tells you nothing. The log separates two failures that otherwise look identical to
waiting:

- A looping run repeats the same block of lines every poll interval.
- A failed run prints its error in full, including the cases where no output file is ever
  written.

Then tell Claude, in these words or your own:

> *"Aux-file mode. My transfer folder is `<your transfer folder>` and I have my case loaded."*

Steps 5 and 6 are once per machine; the registry keeps them across restarts. Steps 1, 2, 3,
7 and 8 are every session.

---

### Recipe 2 — Prove it is alive before you trust it

**Skip this if you have used the channel before and know it works.** It is here for your
first run on a machine, where a broken script and a channel that was never running look
exactly the same from the folder: nothing happens either way.

Do not debug a real script against an unproven channel. Ask for the smallest possible one:

> *"Give me a four-line aux that just writes a marker to the log, so I can check the channel
> works."*

You get something like this. Save it anywhere except the transfer folder:

```
SCRIPT
{
  LogAdd("HELLO -- the channel works");
  LogAddDateTime;
}
```

Now copy it into your transfer folder and rename it to exactly `SimulatorScriptInput.aux`.

> Copy it in finished. Do not save into the folder from an editor. Simulator cannot tell a
> finished file from one you are still writing, and a half-written script is still valid up
> to the cut. It will run the fragment.

Within a second, two things happen:

| | |
|---|---|
| `SimulatorScriptInput.aux` disappears | Simulator consumed it. The deletion is the acknowledgement |
| `SimulatorScriptOutput.Txt` appears | The log from that run |

Open it. The last line is what you are looking for:

```
Automatic loading of file ...\SimulatorScriptInput.Aux started at 2026-09-21T14:43:01.314Z
Starting load of auxiliary file: ...\SimulatorScriptInput.Aux
HELLO -- the channel works
September 21, 2026 09:43:01.342
Finished load of auxiliary file: ...\SimulatorScriptInput.Aux
Automatic loading of file finished successfully in 0.083 seconds
```

`finished successfully in N seconds` is the completion signal. A small case runs in
0.08–0.5 s; a large one takes longer and prints the same line. If you see it, the channel
works, and every later problem is in your script rather than your setup.

If the file does not disappear, the channel is not running. In order of likelihood: the
Script dialog got closed, the checkbox is not ticked, or the folder in the dialog is not the
folder you copied into. Delete `SimulatorScriptInput.aux` before you retry, or it will run
the moment you fix the setting.

**Read the folder back to each other.** Nothing on the file side can tell you whether
Simulator is watching the folder you are writing to: there is no heartbeat file and no echo
of the setting. So when a drop goes unanswered, the first move is for whoever is at the GUI
to read the **ScriptTransferFileDirectory** box out loud, character for character, and
compare it to the path the script is being copied into. A trailing space, a different drive
letter or a near-identical folder name all produce exactly the silence you are looking at,
and the file side cannot distinguish any of them from a closed dialog.

---

### Recipe 3 — Let it scan the case first

Once you confirm the setup, the agent should raise this on its own, **and then wait for you
to answer:**

> *"Channel is live. I cannot see your case from here. Do you want me to scan it first and
> list what devices are in it? It is read-only, it writes CSVs and changes nothing."*

It should not drop anything until you reply. Your Simulator is live and your case is loaded,
so the first file that lands runs against your session — that decision is yours, even for a
read-only scan. If an agent scans without asking, it is not following this page.

It should also not raise this **until you have said the setup is done**. Recipe 1's steps and
this proposal belong in two separate messages: activation first, ending there, and the scan
offered only after you confirm the dialog is up. An agent that hands you the setup steps and a
script to approve in the same breath is asking you to consent to a drop on a channel that does
not exist yet.

Say yes. Until it runs, the agent knows nothing about your case: not the bus numbers, not
whether there are transformers, not whether a contingency set already exists. One drop
replaces all of that guessing.

The script it hands you writes the case summary plus one CSV per device class: buses,
branches, substations, generators, loads, shunts, contingencies, areas, zones. The pattern
repeats:

```
//--- STAGE A: where the CSVs go -------------------------------------------
SCRIPT
{
  // <<< EDIT: your transfer folder. YES = create the subfolder if absent.
  SetCurrentDirectory("<your transfer folder>\scan", YES);
  CaseSummaryGet("", "SCAN_00_case_identity.txt", 3);
}

//--- STAGE B: the network -------------------------------------------------
SCRIPT
{
  // KEY: BusNum
  SaveData("SCAN_bus.csv", CSV, Bus,
           [BusNum,BusName_NomVolt,BusNomVolt,SubNum,SubName,AreaNum,ZoneNum,
            BusStatus,BusSlack,BusPUVolt,BusAngle,BusGenMW,BusLoadMW],
           [], "", [], NO, NO);

  // KEY: BusNum, BusNum:1, LineCircuit
  // BranchDeviceType is what separates a Line from a Transformer.
  SaveData("SCAN_branch.csv", CSV, Branch,
           [BusNum,BusNum:1,LineCircuit,BranchDeviceType,LineStatus,
            LineR,LineX,LineAMVA,LineMW,LinePercent],
           [], "", [], NO, NO);
}

//--- STAGE C: the injections ----------------------------------------------
SCRIPT
{
  // KEY: BusNum, GenID
  // GenMVRMax/Min is capability, not dispatch. A unit idling at 0 MVAr with
  // 200 MVAr of range is reactive support; GenMVR alone would call it nothing.
  SaveData("SCAN_gen.csv", CSV, Gen,
           [BusNum,GenID,GenStatus,GenMW,GenMVR,GenMVRMax,GenMVRMin],
           [], "", [], NO, NO);

  LogAdd("SCAN COMPLETE");
}
```

The remaining classes follow the same shape. Field names below were read out of
PowerWorld's own object-field export, which is the only authority; do not invent names or
take them from the *Auxiliary File Format* manual, which has no per-object field catalog.

```
  // KEY: BusNum, LoadID
  SaveData("SCAN_load.csv", CSV, Load,
           [BusNum,LoadID,BusName_NomVolt,LoadStatus,LoadMW,LoadMVR,LoadSMW,LoadSMVR,
            AreaNum,ZoneNum],
           [], "", [], NO, NO);

  // KEY: BusNum, ShuntID
  SaveData("SCAN_shunt.csv", CSV, Shunt,
           [BusNum,ShuntID,BusName_NomVolt,SSStatus,SSNMVR,SSCMode,AreaNum,ZoneNum],
           [], "", [], NO, NO);

  // KEY: SubNum
  SaveData("SCAN_substation.csv", CSV, Substation,
           [SubNum,SubName,Latitude,Longitude,AreaNum,ZoneNum],
           [], "", [], NO, NO);

  // KEY: AreaNum   -- note the MW fields are BG-prefixed, NOT AreaLoadMW
  SaveData("SCAN_area.csv", CSV, Area,
           [AreaNum,AreaName,BGLoadMW,BGGenMW,BGLossMW,BusLoadNum],
           [], "", [], NO, NO);

  // KEY: ZoneNum   -- same BG prefix here
  SaveData("SCAN_zone.csv", CSV, Zone,
           [ZoneNum,ZoneName,BGLoadMW,BGGenMW,BGLossMW,BusLoadNum],
           [], "", [], NO, NO);

  // KEY: CTGLabel  -- empty file just means no contingency set is defined
  SaveData("SCAN_contingency.csv", CSV, Contingency,
           [CTGLabel,CTGSkip,CTGSolved,CTGViol,CTGProc],
           [], "", [], NO, NO);
```

The Area and Zone lines are worth a second look, because guessing here is exactly what the
warning trap catches. Their MW totals are **`BGLoadMW` / `BGGenMW` / `BGLossMW`**, on a
balancing-group prefix. The names you would reach for by analogy, `AreaLoadMW` and
`ZoneLoadMW`, do not exist. Asking for them produces a `Warning:`, not an error, and a CSV
holding the key column and nothing else while the run reports success.

Every table leads with its key fields. A bus row is keyed by `BusNum`, a generator by
`BusNum` + `GenID`, a branch by `BusNum` + `BusNum:1` + `LineCircuit`. Drop the key and you
cannot join the CSV to anything, and if you write it back PowerWorld cannot tell which device
you meant: the change does nothing and still reports success.

Three things to know when you read the results:

- **A zero-byte CSV means the case has none of that class**, not that the scan failed. No
  header row is written for an empty type. An empty `SCAN_shunt.csv` is a real answer.
- **The summary header and the CSVs can disagree, on purpose.** `SCAN_00_case_identity.txt`
  describes the `.pwb` on disk; the CSVs describe what is loaded right now. If you changed
  something without saving, the CSVs are the truthful half.
- **Search the log for `Warning:`.** A scan asks for many field names at once, and a wrong
  one is only a warning:

  ```
  Warning: unknown fields will not be written to the file
  Warning: Variable name 'AREALOADMW' is not defined for Area objects.
  ```

  That run wrote a 75-byte `SCAN_area.csv` containing the key column and nothing else, and
  reported success. Nothing else tells you the numbers you asked for are missing.

With those CSVs the agent answers follow-ups without another drop: what the voltage range is,
how many transformers there are, which branches are most loaded, whether a contingency set
already exists.

### Recipe 4 — Change something and measure it

> *"Take bus 4 out of service and tell me what it does to the system."*

What comes back is one script that baselines the case, opens the three branches touching bus
4, re-solves, writes everything to CSV, then closes those branches again so your case is
where you left it. Copy in, rename, watch it go. It takes about 0.4 s.

Bus 4 was carrying 93.71 MW of generation and 80 MW of load. Diffing the before and after
CSVs:

| | before | after |
|---|---|---|
| bus 4 status | `Connected` | `Disconnected` |
| bus 4 voltage | 1.000000 pu | 0.000000 |
| bus 3 voltage | 0.992669 pu | 0.961330 |
| slack output | 200.63 MW | 215.83 MW |
| worst branch loading | 68.7 % | 91.9 % |

Only bus 3 moves, because it was the one leaning on bus 4's local generation. Line 1–3 goes
from comfortable to nearly loaded. All of that came out of the CSVs; the log never contained
it.

**Why the script opens branches instead of the bus.** You cannot switch a bus off by setting
its status. That field reports whether the bus is energised; it does not control it, and
writing to it does nothing while still reporting success. The script opens the branches, lets
the status follow, then reads it back to prove it worked.

---

### When it goes wrong

Three failure shapes, all of which look similar from your side of the folder.

**The file sits there and nothing happens.** A setup problem: dialog closed, checkbox
unticked, or wrong folder. Delete the file, fix the setting, drop again.

How long to wait before calling it dead: **30 seconds on a small case, a couple of minutes on
a large one.** Successful round trips here run 0.08-0.5 s on a seven-bus case, so anything
past a few seconds is already abnormal; the extra margin is only for a case big enough that
the solve itself is slow. If the input file has not been touched in 30 seconds, stop waiting.
It is not slow, it is not running.

**The file sits there but files keep being written.** The script failed partway and Simulator
is re-running it every poll interval, forever. Output timestamps advance while the input file
stays put. Delete `SimulatorScriptInput.aux` yourself.

`Always Delete an Invalid Input Aux File` in the setup panel is aimed at exactly this, and
you should have it ticked. It is not a complete guard, though: a run was observed looping on
2026-09-21 with a script that parsed fine and then crashed Simulator partway through, which
is not the same thing as an invalid file. Keep a timeout on anything that drops files
automatically.

**Everything completed, but a column is missing from a CSV.** A bad field name is a
`Warning:`, not an error. The column is dropped and the run still reports success. Search the
log for `Warning:` after every run:

```
Warning: unknown fields will not be written to the file
Warning: Variable name 'AREALOADMW' is not defined for Area objects.
```

That run produced a 75-byte CSV with the key column and nothing else, and reported success.

### What this mode costs you

- **It is not headless.** A dialog has to stay open, so nothing batches or runs in parallel.
- **Something has to move the file.** Whoever can write to the watched folder triggers the
  run. If Claude is running on the same machine and can write there, it drops its own scripts
  and reads its own results, and you only supply the GUI setup. If it cannot reach the folder,
  which is the hand-off case this mode exists for, every run waits on you.
- **Claude never makes Simulator do anything.** It writes a file. Simulator decides, on its
  own poll interval, to pick it up. That is the whole extent of the control it has, and it is
  why a dropped script cannot leave your case somewhere you did not ask for.

In exchange, every script is reviewable before it touches your case, every artifact is a file
you can read and keep, and you end up with a script you own rather than a session that
happened once.


---

# ==== comparing-planning-cases.md ====

---
type: method
domain: tooling
topic: design
aliases: [comparing-planning-cases, case-diff, case-comparison, planning-delta, what-changed, new-devices]
tags: [demo, planning, case-diff, contingency, aux, esapp, worked-example]
---

# Demo: Comparing two planning cases, and testing what the plan builds

## Abstract

Two vintages of the same system — a 2016 summer peak and a 2024 summer peak — diffed to
find what the plan actually builds, then a contingency set generated for **only the new
devices** and solved. Real numbers throughout: 691 new branches, 199 new generators, and
a scoping trap that would have made the headline answer **87% wrong**.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [new-device-contingency-aux](../methods/new-device-contingency-aux.md) · [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) · [contingency-and-aux](contingency-and-aux.md) · [reading-violationctg](../methods/reading-violationctg.md) · [adding-devices-esapp](../methods/adding-devices-esapp.md)

## Content

### The user's prompt

> *"Compare my 2016 and 2024 cases, work out what the plan builds, and tell me whether
> the new devices cause problems."*

### Step 1 — the two cases

```python
import os
from esapp import PowerWorld
from esapp.components import Bus, Branch, Gen, Contingency, ViolationCTG

a = PowerWorld(r"C:\cases\Synth2k_case1.pwb")
b = PowerWorld(r"C:\cases\Synth2k_case.PWB")
for name, s in (("2016", a.summary()), ("2024", b.summary())):
    print(f"{name}: {s['n_bus']} buses / {s['n_branch']} branches / "
          f"{s['n_gen']} gens / load {s['total_load_mw']:.0f} MW")
```

```
2016 summerpeak: 2000 buses / 3220 branches / 544 gens / load 67109 MW
2024 summerpeak: 2000 buses / 3911 branches / 743 gens / load 87578 MW
```

Load grows 67.1 GW → 87.6 GW, **+30.5%** over eight years. That framing matters: the
build is a response to that growth, and it is the first thing to report.

### Step 2 — diff, but guard against false construction

**A naive diff is wrong in the direction that looks right.** A renumbered bus, a
relabelled circuit, or a swapped from/to each produce a RETIRED row *and* a matching NEW
row. An unguarded comparison reports construction that never happened, and the output
looks entirely plausible.

So run the naive diff and the guarded one, and compare them:

```python
# --- buses: naive by number, then paired by (name, kV) ---
ba, bb = a[Bus, ["BusName", "BusNomVolt"]], b[Bus, ["BusName", "BusNomVolt"]]
na, nb = set(ba["BusNum"].astype(int)), set(bb["BusNum"].astype(int))

key = lambda d: set(zip(d["BusName"].astype(str).str.strip(), d["BusNomVolt"].round(2)))
ka, kb = key(ba), key(bb)

renumbered = (len(na - nb) + len(nb - na)) - (len(ka - kb) + len(kb - ka))
```

```
BUSES  naive by BusNum  : retired-looking 0, new-looking 0
       paired by (name,kV): only-2016 0, only-2024 0
       => 0 bus rows differ by NUMBERING only
```

Same for branches, normalising the endpoint order:

```python
bf = lambda pw: set(zip(pw[Branch]["BusNum"].astype(int),
                        pw[Branch]["BusNum:1"].astype(int),
                        pw[Branch]["LineCircuit"].astype(str).str.strip()))
norm = lambda s: {(min(x, y), max(x, y), c) for x, y, c in s}
```

```
BRANCHES naive             : retired-looking 0, new-looking 691
         from/to normalised: retired 0, NEW 691
         => 0 were FROM/TO SWAPS, not construction

GENERATORS: retired 0, NEW 199
```

**This pair is clean** — no renumbering, no swaps, nothing retired. Pure expansion: 691
branches and 199 generators added.

That is a finding, not a formality. Run the guarded diff *anyway*, every time. When the
two counts agree you have earned the right to trust the number; when they disagree, the
naive answer was fiction and you would never have known.

Devices present in both but with changed parameters are a third category — **UPGRADED**
— found by comparing ratings and impedances on the common keys, not by set difference.

**When the two counts disagree, pair a removal with an addition on a second identity.** A key is a
label, and labels get rewritten for reasons that have nothing to do with the device. Find an
attribute that names the *thing* rather than the *record* and that the relabelling does not touch:
for a bus, `(BusName, BusNomVolt)`, because a renumbered substation keeps its name and its voltage.
Pair a retired-looking record with a new-looking one only when the rest of its identity matches
(the `GenID`, the untouched far endpoint) **and** the moved key's second identity is unchanged.
Three rules keep the pairing from hiding real findings:

1. **Decline ambiguity; do not resolve it.** Several buses in one substation often share a name at
   one voltage. If more than one candidate fits, make no pair. A guess that lands wrong turns a
   real retirement into housekeeping, silently.
2. **One addition can excuse only one removal.** Otherwise two devices that genuinely went away
   both point at one new record and both vanish from the count.
3. **Mark both halves, or neither.** Excusing the retirement while leaving its partner in the added
   list is worse than doing nothing: the totals now disagree with each other, and the clean-looking
   one is the wrong one.

**Name what stayed behind.** Reserve "removed" for the strongest claim: the record is gone **and**
so is the thing it named (neither number nor name survives). Everything weaker gets a verdict that
says what is left: *bus remains, device gone*, *renumbered*, *renumbered (unpaired)*. A confirmed
relabelling belongs in its own category, not under "removed" or "added", or the reader has to
subtract in their head.

**The two errors do not cost the same.** Calling a relabelling a retirement inflates the project
list, which is **visible** on inspection. Calling a retirement a relabelling hides a removed device,
which **silently never appears**. So when the evidence is suggestive but unconfirmed, let it count
as gone and say why in the label.

**Generators need their own two comparisons.** In a 2026-10-20 validation run, three agents
reported "no generator settings changed" while voltage control (AVR) had been switched off on
two generators. Compare status, AVR and AGC per generator on its key pair, then in-service MW
and capacity by area, zone and fuel type. A design that quietly shifts where power comes from
shows up in the second table.

```python
import pandas as pd

def gens(pw, fields):
    g = pw[Gen, ["BusNum", "GenID"] + fields]
    g["GenID"] = g["GenID"].astype(str).str.strip()
    return g.set_index(["BusNum", "GenID"])

ctl = ["GenStatus", "GenAVRAble", "GenAGCAble"]
ga, gb = gens(a, ctl), gens(b, ctl)
common = ga.index.intersection(gb.index)
flips = (ga.loc[common] != gb.loc[common]).any(axis=1)
print(pd.concat({"base": ga.loc[common][flips], "design": gb.loc[common][flips]}, axis=1))

mix = ["GenStatus", "GenMW", "GenMWMax", "AreaNum", "ZoneNum", "GenFuelType"]
def by(pw, col):
    g = gens(pw, mix)
    return g[g.GenStatus == "Closed"].groupby(col)[["GenMW", "GenMWMax"]].sum()
for col in ("AreaNum", "ZoneNum", "GenFuelType"):
    t = pd.concat({"base": by(a, col), "design": by(b, col)}, axis=1).fillna(0)
    d = t["design"] - t["base"]
    print(t[d["GenMWMax"].abs() > 1.0])                  # capacity added, removed or switched off
    print(d["GenMW"].sort_values(key=abs, ascending=False).head(5))  # where the new load's MW came from
```

Judge the shift on **capacity** (`GenMWMax` of in-service units), not on `GenMW`. A design that
adds load moves dispatched MW in every area, because the slack and AGC pick it up, so a
threshold on `GenMW` flags everything. Read the `GenMW` change as where the new load's power came
from. Measured 2026-10-21 on a 2,000-bus synthetic case and a design copy: the control flip found
exactly the two units with AVR switched off, while a 1 MW `GenMW` threshold flagged all 8 areas.
`GenAVRAble` and `GenAGCAble` read back padded (`"NO "`), so strip them before comparing to a
literal.

### Step 3 — a contingency set for only the new devices

```python
kv = {int(r["BusNum"]): float(r["BusNomVolt"]) for _, r in b[Bus, ["BusNomVolt"]].iterrows()}
new = sorted(bf(b) - bf(a))
hv = [t for t in new if max(kv.get(t[0], 0), kv.get(t[1], 0)) >= 345]
```

```
new branches: 691
of which >=345 kV: 31
```

Scope before you solve. 691 contingencies on a 2000-bus case is a long wait; the 31
highest-voltage additions answer the question that matters first.

```python
sel = hv[:25]
lines  = ["CONTINGENCY (Name, Skip)", "{"]
lines += [f'"NEW_{f}_{t}_{c}" "NO"' for f, t, c in sel] + ["}", ""]
lines += ["CONTINGENCYELEMENT (Contingency, Object, Action, Status)", "{"]
lines += [f'"NEW_{f}_{t}_{c}" "BRANCH {f} {t} {c}" "OPEN" "CHECK"' for f, t, c in sel] + ["}"]

aux = os.path.abspath(r"C:\out\tx_new_devices.aux")
open(aux, "w", encoding="utf-8").write("\n".join(lines))

b.esa.RunScriptCommand("CTGClearAllResults")
n0 = len(b[Contingency])
b.esa.RunScriptCommand(f'LoadAux("{aux}", YES)')
n1 = len(b[Contingency])
assert n1 - n0 == len(sel)
```

```
wrote aux: 2216 bytes, 25 contingencies
contingencies in case before LoadAux: 3875
after LoadAux: 3900  (added 25)
```

**Note that first number.** The 2024 case already carried **3,875 contingencies** of its
own. Which sets up the trap.

### Step 4 — the trap that makes the answer 87% wrong

```python
b.esa.RunScriptCommand("CTGSolveAll")
v = b[ViolationCTG, ["CTGLabel", "LimViolValue", "LimViolLimit"]]
print("total violation rows:", len(v))
```

```
total violation rows: 240
```

Report that and you have said the plan's new 345 kV devices cause 240 violations. Now
filter by the labels you actually created:

```python
labs = v["CTGLabel"].astype(str).str.strip()
mine = labs.str.startswith("NEW_")
print("from MY new-device contingencies :", int(mine.sum()))
print("from OTHER contingencies already in the case:", int((~mine).sum()))
```

```
from MY new-device contingencies : 32
from OTHER contingencies already in the case: 208
```

**`LoadAux` adds contingencies. It does not scope the solve.** `CTGSolveAll` solved all
3,900, and 208 of the 240 violations belong to contingencies that were already in the
case and have nothing to do with the plan. The honest number is **32**, not 240 — the
naive answer overstates by 87%.

Two ways to get this right, and you should do both:

1. **Filter results by your label prefix**, as above. Cheap, and it also documents intent.
2. **Restrict what solves.** Set `Skip` to `YES` on the pre-existing contingencies, or
   build a case that carries only your set. This is the autoinsert-then-restrict pattern
   in [new-device-contingency-aux](../methods/new-device-contingency-aux.md).

Filtering alone still *solves* 3,900 contingencies, so on a large case do the restriction
too — for the runtime, not just the arithmetic.

And remember PowerWorld **trims whitespace from `CTGLabel` on load**, so strip before
matching on a prefix. A label that fails to match looks exactly like a contingency with
no violations.

### Step 5 — rank the new devices

With the correct 32 rows, group by contingency and rank:

```python
v = v[mine].copy()
v["pct"] = v["LimViolValue"] / v["LimViolLimit"] * 100
agg = (v.groupby(labs[mine])
        .agg(rows=("pct", "size"), worst=("pct", "max"))
        .sort_values(["rows", "worst"], ascending=False))
```

Rank on **rows and worst severity together**. A device causing one 130% violation is a
different problem from one causing eight at 101%, and which is worse is a planning call.
Full scoring method, including why voltage must not rank on `LimViolPct`, is in
[ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md).

### What to report back

> **The plan.** Between 2016 and 2024 summer peak, load grows 67.1 → 87.6 GW (+30.5%).
> The build adds **691 branches and 199 generators**, retires nothing, and renumbers
> nothing — I checked, by pairing buses on (name, kV) and normalising branch endpoint
> order, so none of those additions are diff artifacts.
>
> **Testing.** I built a contingency set for the 25 highest-voltage new branches
> (31 are ≥345 kV) and solved.
>
> **Result: 32 violations attributable to the new devices.** The raw solve reported 240,
> but 208 belong to the 3,875 contingencies already in the case and are not part of this
> plan.
>
> Nothing was saved. The aux is on disk for reuse.
>
> Pages used: `methods/new-device-contingency-aux.md`,
> `methods/reading-violationctg.md`, `demos/contingency-and-aux.md`.

### The two lessons

**Guard the diff.** Numbering, labelling and endpoint order all manufacture fake
construction. Run both the naive and guarded comparisons and report when they disagree.

**Scope the solve, or scope the results.** Adding contingencies does not remove the ones
already there. Attribute every violation to the contingency that produced it before
attributing anything to the plan.


---

# ==== contingency-and-aux.md ====

---
type: method
domain: tooling
topic: contingency
aliases: [demo-contingency, n-1-demo, aux-generation-demo, ctg-demo, filter-demo]
tags: [demo, contingency, n-1, aux, filter, esapp, worked-example]
---

# Demo: N-1 contingency analysis, and generating an aux file

## Abstract

Running N-1 from nothing on the public synthetic Synth40 case (37 buses), then **writing a filter and contingency
`.aux` automatically** from the analysis result and loading it back. All numbers are from
an actual run: 89 auto-inserted contingencies, 12 violations, then 5 targeted
contingencies generated and merged.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [reading-violationctg](../methods/reading-violationctg.md) · [new-device-contingency-aux](../methods/new-device-contingency-aux.md) · [aux-script-commands](../references/aux-script-commands.md) · [handling-errors](../methods/handling-errors.md)

## Content

### The user's prompts

> *"Run N-1 on everything and tell me what breaks."*
> *"Build me a contingency file for the five most loaded lines."*

### Part 1 — N-1 from scratch

Three script actions, in this order:

```python
from esapp import PowerWorld
from esapp.components import Contingency, ViolationCTG

pw = PowerWorld(r"C:\path\to\Synth40.pwb")
pw.pflow()

pw.esa.RunScriptCommand("CTGClearAllResults")   # do not skip this
pw.esa.RunScriptCommand("CTGAutoInsert")
pw.esa.RunScriptCommand("CTGSolveAll")

print(f"auto-inserted {len(pw[Contingency])} contingencies")
```

```
auto-inserted 89 contingencies
```

**`CTGClearAllResults` first, always.** Contingency results persist inside the `.pwb`, so
a freshly opened case can hand you results from someone else's run last month. They look
exactly like yours.

### Reading the violations

```python
v = pw[ViolationCTG, ["CTGLabel", "ObjectType", "LimViolPct",
                      "LimViolValue", "LimViolLimit"]]
print("violation rows:", len(v))
```

```
violation rows: 12
L_000019PEARLCITY69-000023WA   val=100.525  lim=100.300  pct=100.224
```

> **That field list is Python-side only. Do not paste it into an aux `SaveData`.**
> `ViolationCTG` has no `ObjectType` in the aux object-field vocabulary; the violation
> category there is **`LimViolCat`** (concise `LV_Type`). Asking an aux for `ObjectType`
> produces a `Warning:` rather than an error, so the column is silently missing and the run
> still reports success. A field list verified against the export, with no warnings:
> `[CTGLabel,LimViolID:1,LimViolLimit,LimViolValue,LimViolPct,LimViolCat,BusNum,BusNum:1]`.
> The aux keys are `CTGLabel` and `LimViolID:1`. See
> [aux-file-mode](../methods/aux-file-mode.md).

Three things to know before you interpret this:

- **A bare read returns 2 of 15 columns.** Ask for the fields you need by name, or you
  get `CTGLabel` and an id and nothing useful.
- **`pw[ViolationCTG, :]` returns 394 columns** on this case. Never do that casually.
- **Repeated labels are usually parallel circuits**, not duplicates — the same
  PEARLCITY–WAIPAHU corridor appearing several times. Check before reporting a data
  problem.

Here the worst violation is a 69 kV line at **100.22%** of its 100.3 MVA rating: real,
but marginal. Say "marginally over" rather than "overloaded", because those mean
different things to a planner.

More traps — polarity, tie-line `AreaNum` reading 0, `LimViolLimit` being the branch's
MVA rating rather than 100 — are in [reading-violationctg](../methods/reading-violationctg.md).

### Part 2 — generate an aux file automatically

The user wants a contingency set for the five most loaded lines. Build it from the solved
case rather than by hand:

```python
from pathlib import Path
from esapp.components import Branch

br = pw[Branch, ["LineMVA", "LinePercent", "LineStatus"]]
top = br.sort_values("LinePercent", ascending=False).head(5)

def label(r):
    return f'L_{int(r["BusNum"])}_{int(r["BusNum:1"])}_{str(r["LineCircuit"]).strip()}'

lines = ["// auto-generated contingency + filter set", ""]

lines += ["FILTER (Filter, ObjectType, FilterLogic, FilterPre, Enabled)", "{",
          '"HighLoad" "Branch" "AND" "NO" "YES"', "}", ""]

lines += ["CONTINGENCY (Name, Skip)", "{"]
lines += [f'"{label(r)}" "NO"' for _, r in top.iterrows()]
lines += ["}", ""]

lines += ["CONTINGENCYELEMENT (Contingency, Object, Action, Status)", "{"]
for _, r in top.iterrows():
    obj = f'BRANCH {int(r["BusNum"])} {int(r["BusNum:1"])} {str(r["LineCircuit"]).strip()}'
    lines.append(f'"{label(r)}" "{obj}" "OPEN" "CHECK"')
lines += ["}"]

out = Path(r"C:\path\to\demo_ctg.aux")     # absolute
out.write_text("\n".join(lines), encoding="utf-8")
```

What it produced:

```
// auto-generated contingency + filter set

FILTER (Filter, ObjectType, FilterLogic, FilterPre, Enabled)
{
"HighLoad" "Branch" "AND" "NO" "YES"
}

CONTINGENCY (Name, Skip)
{
"L_27_29_1" "NO"
"L_19_23_2" "NO"
"L_19_23_3" "NO"
"L_19_23_1" "NO"
"L_19_23_4" "NO"
}
```

565 bytes.

### Loading it back

```python
before = len(pw[Contingency])
pw.esa.RunScriptCommand(f'LoadAux("{out}", YES)')
after = len(pw[Contingency])
print(f"contingencies before: {before}\nafter: {after}  (added {after - before})")
```

```
contingencies before: 89
after: 94  (added 5)
```

**Four rules the aux format will punish you for breaking:**

1. **Absolute paths.** A relative path resolves against PowerWorld's working directory,
   not your script's.
2. **`LoadAux` merges.** It does not replace. Loading twice duplicates everything —
   which is exactly why the count check above matters.
3. **Quote the action string.** An unquoted `CTGElement` action loads only the first
   contingency and silently drops the rest.
4. **`ElementType=GEN` is silently ignored.** The keyword is `GENERATOR`.

And a fifth that will confuse you later: **PowerWorld trims whitespace from `CTGLabel`
on load**, so the label you wrote is not always the label you read back. Do not match on
labels you have not round-tripped.

### Verify, do not assume

```python
assert after - before == 5, "LoadAux merged the wrong number of contingencies"
```

An aux that fails to parse can leave the case unchanged without raising. Count.

### What to report back

> Auto-inserted **89** N-1 contingencies and solved them all. **12 violations**, the worst
> a 69 kV PEARLCITY–WAIPAHU circuit at **100.22%** of its 100.3 MVA rating — marginally
> over, not severe.
>
> Also generated `demo_ctg.aux` with a `HighLoad` branch filter and 5 targeted
> contingencies for the most loaded lines, and confirmed it loaded: 89 → 94.
>
> The case was not saved. The aux is on disk if you want to reuse it.
>
> Pages used: `methods/reading-violationctg.md`, `methods/new-device-contingency-aux.md`,
> `references/aux-script-commands.md`.


---

# ==== power-flow-and-sensitivities.md ====

---
type: method
domain: tooling
topic: power-flow
aliases: [demo-power-flow, dcpf-demo, ptdf-demo, lodf-demo, sensitivities-demo]
tags: [demo, powerflow, dcpf, ptdf, lodf, esapp, worked-example]
---

# Demo: Power flow, DC mode, LODF and PTDF

## Abstract

Solving a case and asking the three standard sensitivity questions, on the public synthetic
Synth40 case (37 buses). Includes the `1e8` sentinel that makes LODF results look insane, and a PTDF
failure whose obvious recovery **also fails** — both encountered in an actual run, both
recovered without asking the user.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [esapp-overview](../methods/esapp-overview.md) · [lodf](../concepts/lodf.md) · [handling-errors](../methods/handling-errors.md) · [esapp-environment](../concepts/esapp-environment.md)

## Content

### The user's prompts

> *"Open my case and tell me which branches are most heavily loaded."*
> *"Run it as a DC power flow instead."*
> *"If the most loaded line trips, where does the flow go?"*

### AC power flow

```python
from esapp import PowerWorld
from esapp.components import Bus, Branch, Gen, Load, Area

pw = PowerWorld(r"C:\path\to\Synth40.pwb")
pw.pflow()

v = pw[Bus, "BusPUVolt"]["BusPUVolt"]
print(f"V {v.min():.4f} - {v.max():.4f} pu, overloads {len(pw.overloads())}")
```

```
V 0.9749-1.0034 pu, overloads 0
```

`overloads()`, `violations()`, `mismatch()`, `flows()`, `ptdf()`, `lodf()`, `ybus()` are
**all methods** — call them. Referencing one without parentheses hands you a bound method
that fails confusingly further down.

Ranking by loading:

```python
br = pw[Branch, ["LineMVA", "LineLimMVA", "LinePercent"]]
top = br.sort_values("LinePercent", ascending=False).head(5)
```

```
  27 ->  29 ckt 1     54.65 /   67.50 MVA =  80.96%
  19 ->  23 ckt 2     78.14 /  100.30 MVA =  77.90%
  19 ->  23 ckt 3     78.14 /  100.30 MVA =  77.90%
  19 ->  23 ckt 1     78.14 /  100.30 MVA =  77.90%
  19 ->  23 ckt 4     78.14 /  100.30 MVA =  77.90%
```

Four identical rows for 19→23 are four **parallel circuits**, not duplicates. Check the
circuit id before reporting a repeated bus pair as a data error.

### DC power flow — pass the method, do not set the flag

```python
pw.pflow(method="DC")      # NOT pw.dc_mode = True
print(f"max loading {pw[Branch, 'LinePercent']['LinePercent'].max():.2f}%")
pw.pflow()                 # an AC method puts the case back to AC
```

`pw.dc_mode(True)` raises `TypeError: 'bool' object is not callable`, and
`pw.dc_mode = True` is no better: PowerWorld ignores it on a scripted solve (live-tested
2026-09-23), so the next `pw.pflow()` still runs AC. An earlier version of this demo did
exactly that and printed `max loading 80.96%`, the same figure as the AC ranking above.
To confirm a solve really ran DC, check that every bus sits at exactly 1.0 pu
([lodf](../concepts/lodf.md)). `flat_start` is
the same trap: call `pw.flatstart()` instead. See
[handling-errors](../methods/handling-errors.md).

**A DC solve always reports zero mismatch.** It cannot tell you generation is short — the
slack bus absorbs the shortfall silently. Check the schedule against load directly, and
say plainly when a result is DC.

### LODF — and the sentinel that ruins it

```python
L = pw.lodf((27, 29, "1"))       # (from_bus, to_bus, circuit)
```

Ranked naively, the answer is nonsense:

```
    1 ->   2  +100000000.0000
    1 ->   2  +100000000.0000
    1 ->   5  +100000000.0000
```

`1e8` is PowerWorld's **"undefined"** marker, not a distribution factor. Nothing receives
a hundred million times the flow. Filter it:

```python
real = L[L["LineLODF"].abs() < 1e7]
top = real.reindex(real["LineLODF"].abs().sort_values(ascending=False).index).head(5)
```

```
rows total 89, sentinel rows 88, real 1
    27 ->  29 ckt 1  LODF -100.0000
```

Only the outaged branch itself has a defined factor: it loses 100% of its own flow. On
this small system that outage does not redistribute onto anything with a defined LODF,
which is a finding about the topology — report it as such, not as "the calculation
failed."

**A result that looks absurd is your bug until proven otherwise.** Never report a
100,000,000 anything.

### PTDF — a failure, and a recovery that also fails

The obvious first attempt:

```python
areas = pw[Area]
P = pw.ptdf(seller=int(areas["AreaNum"].iloc[0]), buyer=int(areas["AreaNum"].iloc[-1]))
```

```
PowerWorldError: Error in script action execution:
Seller and Buyer can not be the same in script action CalculatePTDF
```

The case has exactly **one** area, so first and last are the same. Recovery: use buses.

```python
g = pw[Gen, "GenMW"].groupby("BusNum")["GenMW"].sum().sort_values(ascending=False)
l = pw[Load, "LoadSMW"].groupby("BusNum")["LoadSMW"].sum().sort_values(ascending=False)
P = pw.ptdf(seller=int(g.index[0]), buyer=int(l.index[0]))
```

```
biggest gen bus 23, biggest load bus 23
PowerWorldError: Seller and Buyer can not be the same
```

**The recovery failed the same way.** On this case the largest generator and the largest
load are the same bus. Force them apart:

```python
src = int(g.index[0])
snk = int(next(b for b in l.index if int(b) != src))
P = pw.ptdf(seller=src, buyer=snk)
```

```
seller bus 23 (460.8 MW gen), buyer bus 26 (75.3 MW load)
OK  89 branches, 89 with real PTDF
    2 ->  26 ckt 2   PTDF +27.2714
    2 ->  26 ckt 1   PTDF +27.2714
   24 ->  33 ckt 1   PTDF -21.3910
   25 ->  26 ckt 1   PTDF +12.0331
   25 ->  26 ckt 2   PTDF +12.0331
```

Two lessons. First, **an error's obvious fix can reproduce the same error** — check that
the recovery actually satisfies the constraint. Second, do not ask the user about any of
this. They wanted sensitivities, not a report on area counts.

Signatures, verified:

```python
pw.ptdf(seller: int, buyer: int, method: str = "DC") -> DataFrame
pw.lodf(branch: tuple, method: str = "DC")           -> DataFrame
pw.ybus(dense: bool = False)                          # csr_matrix (37, 37)
```

### What to report back

> Case solved: 37 buses, voltage 0.975–1.003 pu, no base-case overloads. The most loaded
> branch is 27→29 at **80.96%** of its 67.5 MVA rating; the four parallel 19→23 circuits
> each sit at 77.9%.
>
> Outaging 27→29 produces no defined LODF onto other branches — on this system that
> outage does not redistribute measurably.
>
> The case has one area, so I computed PTDFs for a bus-to-bus transfer, bus 23 → bus 26.
> Most sensitive: 2→26 at +27.3.
>
> Pages used: `methods/esapp-overview.md`, `concepts/lodf.md`, `methods/handling-errors.md`.


---

# ==== start-here.md ====

---
type: method
domain: tooling
topic: scripting
aliases: [demos-index, demos, demo-index, examples, worked-examples]
tags: [demo, index, examples, prompts, getting-started]
---

# Demos: what to say, and what happens

## Abstract

Worked runs on the public synthetic Synth40 case (37 buses, 89 branches, 45 generators).
Every number on these pages came from an actual run — including the failures, which were
left in on purpose. Start with the one-line prompts below: you should not have to know
which page covers what.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [handling-errors](../methods/handling-errors.md) · [preflight-powerworld](../methods/preflight-powerworld.md) · [esapp-overview](../methods/esapp-overview.md)

## Content

### Just say this

You do not need to name a function, a field, or a file. Say the thing you want:

| Say this | The agent will |
|---|---|
| *"Is PowerWorld working on this machine?"* | Run the 5-check preflight and tell you what is missing |
| *"Open my case and summarize it."* | Load it, solve, report buses/branches/generators and voltage range |
| *"Which branches are most heavily loaded?"* | AC solve, rank by percent of rating |
| *"Anything overloaded?"* | Solve and check limits, base case and N-1 |
| *"Run a DC power flow instead."* | Switch solver mode and re-solve |
| *"If line 27–29 trips, where does the flow go?"* | LODF, sentinel values filtered |
| *"How sensitive are the lines to a transfer from bus 23 to bus 26?"* | PTDF |
| *"Add a line between bus 27 and bus 31 and tell me if it helps N-1."* | Create it, verify it was really created, re-run N-1, compare |
| *"Run N-1 on everything."* | Auto-insert contingencies, solve, report violations |
| *"Build me a contingency file for the five most loaded lines."* | Generate an `.aux` and load it |
| *"Get February 2021 weather for Texas."* | Download a cropped `.pww` |
| *"How much wind and solar would these units produce?"* | Set up and run a TimeStep simulation |
| *"Run N-1, work out what's wrong, and tell me what to build to fix it."*  | Diagnose the cause, test candidate reinforcements, rank them, and say which to reject |
| *"Compare my 2016 and 2024 cases and tell me what the plan builds."* | Diff both, guard against renumbering artifacts, classify NEW / RETIRED / UPGRADED |
| *"Do the new devices in this plan cause violations?"* | Build a contingency set for just those devices, solve, and attribute correctly |
| *"Can this case run a weather study?"* | Check whether its renewable units carry PFW models |
| *"Save the case."* | Write it out — after asking where, since that is destructive |

If a prompt fails, that is a defect worth reporting. The routing is
[AGENTS.md](../AGENTS.md)'s job, not yours.

### The demos

| Demo | Shows |
|---|---|
| [comparing-planning-cases](comparing-planning-cases.md) | **Multi-case.** 2016 vs 2024: 691 new branches, 199 new generators, and a scoping trap that makes the naive answer 87% wrong |
| [violation-remediation](violation-remediation.md) | **The full study.** 12 violations diagnosed to one cause, five reinforcements tested and ranked, two of which make things worse |
| [adding-a-device](adding-a-device.md) | **Read this one.** Three attempts that succeeded and did nothing, then the fix. The silent-failure problem in full |
| [power-flow-and-sensitivities](power-flow-and-sensitivities.md) | AC, DC, LODF, PTDF — with the `1e8` sentinel and a two-step error recovery |
| [contingency-and-aux](contingency-and-aux.md) | N-1 from scratch, and generating a filter + contingency `.aux` automatically |
| [timestep-and-pfw](timestep-and-pfw.md) | Weather to megawatts: PFW models, TimeStep, and reading the output |
| [aux-file-cookbook](aux-file-cookbook.md) | Claude in one window, Simulator in the other. Four recipes in order: turn the channel on, prove it with a four-line script, inventory a case, then take a bus out and measure it. Start here if you are working through files rather than Python. |

### Queries versus studies

The first few prompts above are queries — one number, one answer. The interesting ones
are studies: *diagnose the cause, propose a fix, apply it, re-verify, and report what you
rejected.*

That second kind is what this kit is really for. A voltage readout needs no knowledge
base. Knowing that reinforcing the most loaded branch can make N-1 **worse** — and having
measured it rather than argued it — does.

### Measuring whether this actually works — in progress

The traversal protocol claims a fresh agent needs three to five pages for a typical task.
**That is a design target, not yet a measured result.** The check:

1. Start a fresh session with no prior PowerWorld context, in a clean clone.
2. Give it one prompt from the table above.
3. Count the pages it opens before it writes code.

**Pass is fewer than 8 of 41.** Reading 25 means the router's traversal instructions are
too weak and belong in the next revision — a defect in this knowledge base, not in the
agent.

If you run it, the page count and the prompt you used are worth an issue on the
repository either way. A failure here is more useful than a pass.

### What every demo assumes

Preflight passed. If it did not, nothing here runs — see [preflight-powerworld](../methods/preflight-powerworld.md).

### The case used

```
Synth40.pwb
  37 buses, 89 branches, 45 generators, 27 loads
  1154.7 MW generation vs 1136.3 MW load
  voltage 0.9749 - 1.0034 pu, Sbase 100 MVA
  base case: 0 overloads
  N-1: 12 violations across 89 auto-inserted contingencies
```

It is small enough that a wrong answer is visibly wrong, which is exactly why it was
chosen. A synthetic case, so nothing here is sensitive.

### Two habits these demos are trying to teach

**Assert the effect, not the absence of an error.** PowerWorld will accept a malformed
request, report success, and do nothing. Count before, count after, assert the delta.

**Say what you did not do.** None of these demos saved the case. Every one of them says
so. An analysis that quietly wrote to disk is worse than one that quietly did not.


---

# ==== timestep-and-pfw.md ====

---
type: method
domain: weather
topic: timestep
aliases: [demo-timestep, pfw-demo, weather-to-mw-demo, timestep-demo]
tags: [demo, timestep, pfw, pww, weather, renewables, esapp, worked-example]
---

# Demo: Weather to megawatts — PFW models and TimeStep

## Abstract

Turning a weather file into hourly wind and solar output. Covers the check that decides
whether the case can do this at all — **do its renewable units carry PFW model
strings?** — verified on a real case where 9 of 45 generators do. Getting that check
wrong is why TimeStep runs "successfully" and produces nothing.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [timestep-workflow](../concepts/timestep-workflow.md) · [timestep-simulation-setup](../methods/timestep-simulation-setup.md) · [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) · [pww-data](../concepts/pww-data.md) · [how-to-analyze-results](../methods/how-to-analyze-results.md)

## Content

### The user's prompts

> *"Can this case do a weather simulation?"*
> *"Get February 2021 weather and tell me how much wind and solar these units produce."*

### Step 1 — can this case do it at all?

Ask before setting anything up. TimeStep does not convert weather to power — **each
generator's embedded PFW model does**. A unit without one produces nothing, and nothing
warns you.

```python
from esapp import PowerWorld
from esapp.components import Gen

pw = PowerWorld(r"C:\path\to\Synth40_with_PFW.pwb")

g = pw[Gen, ["GenFuelType", "GenMW", "GenMWMax", "TSPFWModelString"]]
ft = g["GenFuelType"].astype(str).str.strip()
print(ft.value_counts().to_dict())

ren = g[ft.str.contains("WND|SUN", na=False)]
has_pfw = g["TSPFWModelString"].astype(str).str.len() > 2
print(f"renewable units: {len(ren)}   with a PFW model: {has_pfw.sum()}")
```

```
fuel types: {'DFO (Distillate Fuel Oil)': 23, 'OBL (Other Biomass Liquids)': 12,
             'SUN (Solar)': 6, 'WND (Wind)': 3, 'BIT (Bituminous Coal)': 1}
renewable units: 9
with a PFW model: 9
```

9 renewables — 6 solar, 3 wind — and all 9 carry a PFW model. This case is ready.

**If that second number were 0**, stop and say so. Do not run TimeStep and report zero
output as a finding; report that the case has no weather models. Those are completely
different answers, and only one of them is true.

Note the two case files here. The base `Synth40.pwb` and
`Synth40_with_PFW.pwb` differ precisely in this: the `_with_PFW` variant has the
models. Check which one you were handed.

### PWW is not PFW

The single most expensive confusion in this workflow:

| | What it is | Where it lives |
|---|---|---|
| **PWW** | PowerWorld **Weather** data — measurements at stations over time | A `.pww` file you load |
| **PFW** | Power **Flow Weather** — the model converting weather to MW for one unit | A string inside each generator |

One letter apart. You load a PWW; a PFW is already in the case. If output is zero, the
question is which of the two is missing — and the answer is usually PFW.

### Step 2 — get the weather

```python
from TeamOverbyeWeather import WeatherClient

client = WeatherClient()
files = client.download("era5", "2021-02", region="TX", dest="./weather")
```

Crop at download time, not after. See [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) for regions, ISO
footprints, bounding boxes, and the `RegionTooLargeError` recovery.

Match the weather footprint to the case. Loading Texas weather against the Synth40 case
produces a run with no matching stations — and it will not tell you.

### Step 3 — run TimeStep

```python
pw.esa.RunScriptCommand(rf'TimeStepLoadPWWRangeLatLon("{pww}", ...)')
pw.esa.RunScriptCommand('TimeStepSaveFieldsSet(GEN, [GenMW])')
pw.esa.RunScriptCommand('TimeStepDoSinglePoint')        # debug ONE point first
pw.esa.RunScriptCommand('TimeStepDoRun')
pw.esa.RunScriptCommand(rf'TimeStepSaveResultsByTypeCSV("{out}", GEN)')
```

Four things worth internalising:

1. **`TimeStepDoSinglePoint` before `TimeStepDoRun`.** One timestamp fails in seconds; a
   full run fails after a long wait, with the same error.
2. **Fields not named in `TimeStepSaveFieldsSet` are simply absent** from the output. No
   warning.
3. **Only selected units produce output.** Select the renewables explicitly.
4. **Work on a copy of the case.** The run mutates it.

Full sequence and field lists: [timestep-simulation-setup](../methods/timestep-simulation-setup.md).

### Step 4 — read the output

The exported CSV is **not** a plain table. Expect **8 metadata header rows** before the
data. Read past them or every column parses as text and your first plot is empty.

Timestamps commonly need a timezone conversion, and the natural last step is splitting
solar from wind. See [how-to-analyze-results](../methods/how-to-analyze-results.md).

### When output is zero

Walk this in order — it is almost never the weather file:

| Check | If it fails |
|---|---|
| Do the units have PFW models? | The case cannot do this. Say so |
| Are the renewables actually selected? | Only selected units produce output |
| Does the weather footprint cover the case? | Texas weather, the Synth40 case — no matching stations |
| Was `GenMW` in `TimeStepSaveFieldsSet`? | The column is absent, not zero |
| Did `TimeStepDoSinglePoint` work? | Fix that before running the whole series |

Zero output is a setup failure until proven otherwise. Reporting "these units generate
nothing" when the real answer is "this case has no weather models" is exactly the
confident wrong answer this kit exists to prevent.

### What to report back

> The `_with_PFW` case has 9 renewable units — 6 solar, 3 wind — and **all 9 carry PFW
> model strings**, so it is set up for a weather simulation. The base case is not; make
> sure you are pointing me at the `_with_PFW` variant.
>
> Note the weather footprint has to match the case. This is the Synth40 system, so Texas
> ERA5 data will produce a run with no matching stations.
>
> Pages used: `concepts/timestep-workflow.md`, `methods/timestep-simulation-setup.md`,
> `methods/teamoverbyeweather-client.md`.


---

# ==== violation-remediation.md ====

---
type: method
domain: tooling
topic: contingency
aliases: [violation-remediation, remediation, fix-violations, reinforcement-study, n-1-remediation]
tags: [demo, remediation, contingency, n-1, reinforcement, esapp, worked-example]
---

# Demo: Violation remediation — diagnose, propose, test, rank

## Abstract

The full study, not a readout: find the N-1 violations, work out *why* they happen,
propose candidate reinforcements, test each one independently, and rank them by measured
effect. Real numbers from the public synthetic Synth40 case (37 buses). The headline result is one you cannot reach
by intuition — **two of five plausible reinforcements made the system worse**, and a
third reduced the violation count while making the worst violation more severe.

## Connections

- **Up:** [Home](../index.md) · [index](../index.md)
- **Across:** [reading-violationctg](../methods/reading-violationctg.md) · [adding-devices-esapp](../methods/adding-devices-esapp.md) · [ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md) · [contingency-and-aux](contingency-and-aux.md) · [handling-errors](../methods/handling-errors.md)

## Content

### The user's prompt

> *"Run N-1, work out what's wrong, and tell me what to build to fix it."*

That is a study, not a query. Everything below is what answering it properly looks like.

### Step 1 — measure the baseline

```python
from esapp import PowerWorld
from esapp.components import Bus, Branch, ViolationCTG

def n1(pw):
    """Solve N-1 and return (violation rows, worst severity as % of limit)."""
    pw.esa.RunScriptCommand("CTGClearAllResults")
    pw.esa.RunScriptCommand("CTGSolveAll")
    v = pw[ViolationCTG, ["CTGLabel", "LimViolValue", "LimViolLimit"]]
    worst = float((v["LimViolValue"] / v["LimViolLimit"] * 100).max()) if len(v) else 0.0
    return len(v), worst

CASE = r"C:\path\to\Synth40.pwb"
pw = PowerWorld(CASE)
pw.pflow()
pw.esa.RunScriptCommand("CTGClearAllResults")
pw.esa.RunScriptCommand("CTGAutoInsert")

base_n, base_w = n1(pw)
print(f"BASE: {base_n} violation rows, worst {base_w:.2f}% of limit")
```

```
BASE: 12 violation rows, worst 100.22% of limit
```

**Track two numbers, not one.** Count and severity move independently, and a change that
improves one can degrade the other — as Step 4 shows.

### Step 2 — diagnose before proposing anything

Do not jump to a fix. Ask which contingencies are producing the violations:

```python
v = pw[ViolationCTG, ["CTGLabel", "LimViolValue", "LimViolLimit"]]
print(v["CTGLabel"].astype(str).str.strip().unique())
```

```
L_000019PEARLCITY69-000023WAIPAHU69C1
L_000019PEARLCITY69-000023WAIPAHU69C2
L_000019PEARLCITY69-000023WAIPAHU69C3
L_000019PEARLCITY69-000023WAIPAHU69C4
```

All twelve violations come from **one corridor**: the four parallel 69 kV circuits
between PEARLCITY (bus 19) and WAIPAHU (bus 23). Circuits C1 through C4.

That is the whole diagnosis. Losing any one of the four pushes the surviving three over
their limit. This is not twelve problems; it is **one problem seen four times**, and it
tells you exactly where reinforcement belongs.

Reporting "12 violations" without this step is a readout. Reporting "the 19–23 corridor
is N-1 insecure against loss of any of its four parallel circuits" is an answer.

### Step 3 — test candidates independently

Each candidate is tested on a **fresh case**, not stacked onto the previous one.
Otherwise you measure combinations while believing you are measuring individuals.

```python
CANDIDATES = [(19, 23), (27, 29), (19, 25), (23, 26), (2, 26)]
results = []

for frm, to in CANDIDATES:
    p = PowerWorld(CASE)                 # fresh every time
    p.pflow()
    p.esa.RunScriptCommand("CTGClearAllResults")
    p.esa.RunScriptCommand("CTGAutoInsert")

    nv = {int(r["BusNum"]): r["BusName_NomVolt"]
          for _, r in p[Bus, ["BusName_NomVolt"]].iterrows()}

    n0 = len(p[Branch])
    p.edit_mode()
    p.esa.CreateData(
        "Branch",
        ["BusNum", "BusName_NomVolt", "BusNum:1", "BusName_NomVolt:1", "LineCircuit",
         "LineR", "LineX", "LineAMVA", "LineAMVA:1", "LineAMVA:2", "LineStatus"],
        [frm, nv[frm], to, nv[to], "R1", 0.01, 0.05, 150.0, 150.0, 150.0, "Closed"])
    p.run_mode()

    if len(p[Branch]) - n0 != 1:         # the guard that makes this trustworthy
        print(f"{frm}->{to} SKIPPED - CreateData no-op")
        p.close()
        continue

    p.pflow()
    n, w = n1(p)
    results.append((f"{frm}->{to}", n, w, n - base_n))
    p.close()
```

**The `!= 1` guard is not optional.** Without it, a silently skipped `CreateData` yields
"this reinforcement changes nothing" — a confident, completely wrong recommendation. See
[adding-a-device](adding-a-device.md).

### Step 4 — the results, and the surprise

```
candidate      viol rows   worst %   delta
19->23                 2    100.19     -10
27->29                15    100.23      +3
19->25                 7    105.76      -5
23->26                 4    102.05      -8
2->26                 13    100.23      +1
```

Ranked:

| Rank | Reinforcement | Violations | Worst | vs base |
|---|---|---|---|---|
| 1 | **19→23** | **2** | 100.19% | **−10** |
| 2 | 23→26 | 4 | 102.05% | −8 |
| 3 | 19→25 | 7 | **105.76%** | −5 |
| 4 | 2→26 | 13 | 100.23% | **+1** |
| 5 | 27→29 | 15 | 100.23% | **+3** |

Three findings worth more than the ranking itself:

**Two candidates made it worse.** Adding a line to 2→26 or 27→29 *increased* violations,
by 1 and 3. Reinforcing a network can redistribute flow onto elements that were
previously fine — the same intuition failure Braess's paradox describes. **This is why
you test rather than reason.** An agent that proposed 27→29 because it was the most
loaded branch would have recommended making the system worse.

**Count and severity can disagree.** 19→25 removes 5 violations but pushes the worst one
from 100.22% to **105.76%**. Fewer problems, each one worse. Which is preferable is a
planning judgement, not an arithmetic one — so present both numbers and let the user
decide.

**The diagnosis predicted the winner.** Step 2 said the 19–23 corridor was the problem;
reinforcing 19–23 directly was best by a wide margin. Diagnosing first is not ceremony,
it is what makes the candidate list intelligent instead of a sweep.

### What to report back

> **Diagnosis.** All 12 N-1 violations come from a single corridor: the four parallel
> 69 kV circuits between PEARLCITY (19) and WAIPAHU (23). Losing any one overloads the
> surviving three. One problem, seen four times.
>
> **Recommendation.** A new 150 MVA circuit on **19→23** takes violations from 12 to
> **2** and drops the worst from 100.22% to 100.19%. Best of the five tested.
>
> **Alternative.** 23→26 gets to 4 violations — worth considering if a fifth parallel
> circuit on an existing corridor is undesirable for right-of-way or common-mode reasons.
>
> **Do not build 27→29 or 2→26.** Both make N-1 *worse* (+3 and +1). 27→29 is the most
> loaded branch in the base case, so it is the intuitive choice and it is wrong.
>
> **Caveat.** 19→25 removes 5 violations but raises the worst to 105.76%. If your
> criterion is severity rather than count, it is a bad option despite the improvement.
>
> All five were tested independently from a clean case, and each device creation was
> verified by branch count. Nothing was saved to disk.
>
> Pages used: `methods/reading-violationctg.md`, `methods/adding-devices-esapp.md`,
> `demos/contingency-and-aux.md`.

### What makes this a study and not a query

- The **diagnosis** turned 12 symptoms into 1 cause
- Candidates were **tested, not argued** — and 2 of 5 refuted the intuition
- **Two metrics** were tracked, because they disagreed
- Every device creation was **verified**, so no result rests on a silent no-op
- The recommendation includes what **not** to build, which is often the more valuable half

### Going further

This loop generalises. The same shape covers redispatch instead of reinforcement
([applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md)), adjusting limit monitoring
([powerworld-limitset-setdata](../methods/powerworld-limitset-setdata.md)), scoring a large candidate set by severity rather than
count ([ranking-new-devices-by-severity](../methods/ranking-new-devices-by-severity.md)), and restricting contingencies to a chosen
device list ([new-device-contingency-aux](../methods/new-device-contingency-aux.md)).

For a weather-driven study — where the violations depend on the hour rather than a single
snapshot — the same diagnose-propose-test-rank loop runs on top of
[timestep-workflow](../concepts/timestep-workflow.md).


---
