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
it, and writes back a log plus whatever CSVs the script asked for. Claude reads those.

This page assumes you are the one moving the file, which is the case when Claude is somewhere
it cannot reach that folder. If Claude is running on the same machine and can write there, it
copies its own scripts in and reads its own results, and your job shrinks to the setup in
recipe 1. Simulator behaves the same either way: it polls the folder and picks up whatever it
finds.

You choose the folder. Any empty one on a drive you can write to will do. If Simulator
already has a transfer folder configured from an earlier session, use that one rather than
making a second. Tell Claude the full path. It cannot see your filesystem, so it should ask
rather than assume.

Everything below writes `<your transfer folder>` where that path goes.

---

### Recipe 1 — Turn the channel on

Do this in Simulator. Claude cannot do any of it, and will ask you to.

**1. Open PowerWorld Simulator.**

**2. Open your case.** Any `.pwb` will do. The numbers further down came from a small 7-bus
sample, so yours will differ. Follow the shape of each step rather than the values.

**3. Switch to Run Mode, then open the Tools tab.** The source deck specifies Run Mode here.
Do not skip it on the assumption that a script can switch modes later.

![The Tools tab in the ribbon](../assets/aux-step-tools.png)

**4. Click Script** to open the Script Command Execution Dialog.

![The Script button under the Tools tab](../assets/aux-step-script.png)

**5. Set ScriptTransferFileDirectory.** Click **Browse...** and pick your folder. The
screenshot below shows one machine's path; yours will differ, and that box is the
authoritative answer to "which folder is Simulator actually watching".

![The External Script Control panel with Browse highlighted](../assets/aux-step-browse.png)

Everything you need is on that one panel. Two things on it before you move on:

- The heading says **"Only Active when Dialog is Open; Fields Saved in Registry"**. The
  folder and the tick survive a restart; the open dialog does not.
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

The output file appears only once a run finishes, so while something is wrong the folder
tells you nothing. The log separates two failures that otherwise look identical to waiting:

- A looping run repeats the same block of lines every poll interval.
- A failed run prints its error in full, including the cases where no output file is ever
  written.

Then tell Claude, in these words or your own:

> *"Aux-file mode. My transfer folder is `<your transfer folder>` and I have my case loaded."*

Steps 5 and 6 are once per machine; the registry keeps them across restarts. Steps 1, 2, 3,
7 and 8 are every session.

---

### Recipe 2 — Prove it is alive before you trust it

**Skip this if you have used the channel before and know it works.** It is for your first
run on a machine, where a broken script and a channel that was never running look the same
from the folder. Nothing happens either way.

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

Open it and look at the last line:

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

**Read the folder back to each other.** Nothing on the file side tells you whether
Simulator is watching the folder you are writing to. There is no heartbeat file and no echo
of the setting. When a drop goes unanswered, whoever is at the GUI reads the
**ScriptTransferFileDirectory** box out loud, character for character, and compares it to
the path the script is being copied into. A trailing space, a different drive letter or a
near-identical folder name all produce the same silence, and the file side cannot tell any
of them from a closed dialog.

---

### Recipe 3 — Let it scan the case first

Once you confirm the setup, the agent should raise this on its own, **and then wait for you
to answer:**

> *"Channel is live. I cannot see your case from here. Do you want me to scan it first and
> list what devices are in it? It is read-only, it writes CSVs and changes nothing."*

It should not drop anything until you reply. Your Simulator is live and your case is loaded,
so the first file that lands runs against your session. That decision is yours, even for a
read-only scan. An agent that scans without asking is not following this page.

It should also not raise this **until you have said the setup is done**. Recipe 1's steps and
this proposal belong in two separate messages: activation first, ending there, and the scan
offered only after you confirm the dialog is up. An agent that hands you the setup steps and a
script to approve in the same breath is asking you to consent to a drop on a channel that does
not exist yet.

Say yes. Until it runs, the agent does not know the bus numbers, whether there are
transformers, or whether a contingency set already exists. One drop replaces that guessing.

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

Guessing on the Area and Zone lines is what the warning trap catches. Their MW totals are
**`BGLoadMW` / `BGGenMW` / `BGLossMW`**, on a balancing-group prefix. The names you would reach for by analogy, `AreaLoadMW` and
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
  one is only a warning. Nothing else tells you the numbers you asked for are missing. The
  log lines are under [When it goes wrong](#when-it-goes-wrong).

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

Only bus 3 moves, because it was leaning on bus 4's local generation. Line 1–3 goes from
comfortable to nearly loaded. All of that came out of the CSVs; the log never contained it.

**Why the script opens branches instead of the bus.** You cannot switch a bus off by setting
its status. That field reports whether the bus is energised; it does not control it, and
writing to it does nothing while still reporting success. The script opens the branches, lets
the status follow, then reads it back to prove it worked.

---

### When it goes wrong

Three failure shapes, all of which look similar from your side of the folder.

**The file sits there and nothing happens.** A setup problem: dialog closed, checkbox
unticked, or wrong folder. Delete the file, fix the setting, drop again.

Wait **30 seconds on a small case, a couple of minutes on a large one** before calling it
dead. Successful round trips here run 0.08-0.5 s on a seven-bus case, so anything past a few
seconds is already abnormal; the extra margin is only for a case big enough that the solve
itself is slow. If the input file has not been touched in 30 seconds, it is not running.

**The file sits there but files keep being written.** The script failed partway and Simulator
is re-running it every poll interval, forever. Output timestamps advance while the input file
stays put. Delete `SimulatorScriptInput.aux` yourself.

`Always Delete an Invalid Input Aux File` in the setup panel is aimed at this, and you should
have it ticked. It is not a complete guard. A run was observed looping on 2026-09-21 with a
script that parsed fine and then crashed Simulator partway through, which is not an invalid
file. Keep a timeout on anything that drops files automatically.

**Everything completed, but a column is missing from a CSV.** A bad field name is a
`Warning:`, not an error. The column is dropped and the run still reports success. Search the
log for `Warning:` after every run:

```
Warning: unknown fields will not be written to the file
Warning: Variable name 'AREALOADMW' is not defined for Area objects.
```

That run produced a 75-byte `SCAN_area.csv` with the key column and nothing else, and
reported success.

### What this mode costs you

- **It is not headless.** A dialog has to stay open, so nothing batches or runs in parallel.
- **Something has to move the file.** Whoever can write to the watched folder triggers the
  run. If Claude can write there, you only supply the GUI setup. If it cannot reach the
  folder, which is the hand-off case this mode exists for, every run waits on you.
- **Claude never makes Simulator do anything.** It writes a file, and Simulator picks it up
  on its own poll interval. That is all the control Claude has, so a dropped script cannot
  leave your case somewhere you did not ask for.

In exchange, every script is reviewable before it touches your case, every artifact is a file
you can read and keep, and you end up with a script you own rather than a session that
happened once.
