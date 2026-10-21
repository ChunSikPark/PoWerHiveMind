---
type: method
domain: tooling
topic: scripting
aliases: [save-case, savecase, save-pwb, write-case, export-pwb]
tags: [esapp, powerworld, simauto, savecase, runscriptcommand, pwb]
---

# Saving a PowerWorld case (.pwb) from esapp

## Abstract

How to write an open PowerWorld case back to disk as a `.pwb` so it can be reopened and inspected in
the GUI. The headline gotcha: **do NOT use the SimAuto `SaveCase` COM function** (`pw.esa.SaveCase(...)`)
— on our setup it returns success (`('',)`, no error raised) yet **silently writes no file**. Use the
PowerWorld aux **script** command `SaveCase` via `RunScriptCommand` instead, which actually writes.
The second trap: the aux `SaveCase` takes **exactly two parameters** `(FileName, FileType)` — adding a
third overwrite/`YES` arg raises `Invalid number of parameters`. All behavior below was live-verified
against the installed package. **On the Simulator 25 build dated 2026-09-20, `PWB` through `PWB24`
failed and `PWB21` saved but silently dropped every generator's PFW weather model; the build dated
2026-09-28 fixed it.** Plain `PWB` writes the newest format, which Simulator 24 cannot open, so save
`PWB24` for anyone on version 24.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [adding-devices-esapp](adding-devices-esapp.md) · [esapp-overview](esapp-overview.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) · [converting-lines-to-transformers](converting-lines-to-transformers.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The one-liner that works

```python
import os
out = os.path.abspath(r"C:\path\to\Outputs\case_out.pwb")
os.makedirs(os.path.dirname(out), exist_ok=True)
pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')   # 2 args only; overwrites by default
assert os.path.exists(out), "SaveCase reported success but wrote nothing"
```

- `FileType` is the bare keyword `PWB` (unquoted also works; `"PWB"` is accepted too). This saves the
  current binary format for the running Simulator version.
- The command **overwrites** an existing file silently — there is no separate overwrite flag.
- Use an **absolute** path (`os.path.abspath`). The SimAuto server is a separate process; a relative
  path resolves against *its* working directory — the PowerWorld **install folder** — not your
  script's. Symptom when you forget: `RunScriptCommand: Exception: Access is denied` (PowerWorld can't
  write into its own program dir). A relative-path arg from a README example or CLI is the usual cause;
  `abspath` the output path inside any save wrapper so a caller can pass a relative path safely.

### Why not `pw.esa.SaveCase(...)` (the COM function)

esapp exposes a COM wrapper `SaveCase(FileName, FileType="PWB", Overwrite=True)` in
`saw/case_actions.py`. It looks right and raises nothing, but on this machine it is a **silent no-op**:

```python
pw.esa.SaveCase(out, "PWB", True)     # returns None, no exception
pw.esa._pwcom.SaveCase(out, "PWB", True)  # raw COM returns ('',) == "success"
os.path.exists(out)                    # -> False.  No file. No error.
```

Because `_com_call` only raises when SimAuto returns a non-empty error string, a "success" that writes
nothing sails straight through. **Always `assert os.path.exists(out)` after any save** — a save that
"worked" but produced no file is the failure mode to guard against, mirroring the silent-no-op
discipline in [adding-devices-esapp](adding-devices-esapp.md).

### The 2-parameter rule (the other silent trap)

The aux script command signature is `SaveCase(FileName, FileType);`. Live-probed on the Synth2k case:

| Statement | Result |
|---|---|
| `SaveCase("out.pwb", PWB);` | ✅ file written |
| `SaveCase("out.pwb", "PWB");` | ✅ file written |
| `SaveCase("out.pwb", PWB, YES);` | ❌ `RunScriptCommand: Error in script action validation: Invalid number of parameters.` |

So the aux command does not take an overwrite argument — it always overwrites. (This differs from the
COM function's 3-arg `(FileName, FileType, Overwrite)` shape, which is another reason the two are easy
to confuse.)

### Simulator 25 builds: which format keyword writes

On SimAuto registered to **Simulator 25, build dated 2026-09-20** (read the build from
`pw.esa._pwcom.ProgramInformation`, or from [preflight](preflight-powerworld.md)), the
current-format keywords failed on every case, edited or not:

| Statement | Result on the 2026-09-20 build |
|---|---|
| `SaveCase("out.pwb", PWB);` | ❌ `Exception: Error. TQVOptions.getFileDirectory IGUIDialogService not assigned` |
| `SaveCase("out.pwb", PWB24);` / `PWB23` / `PWB22` | ❌ same error |
| `SaveCase("out.pwb", PWB21);` | ✅ file written, reopens, **but PFW models are gone** |

**`PWB21` loses the PFW weather models.** It is an older format: on reopen, `Gen.TSPFWModelString`
was blank on every renewable (9 of 9 → 0 of 9 on a small synthetic case, measured 2026-09-23). A
TimeStep run on that file then produces no weather-driven output, and nothing warns you. Topology,
loads, dispatch and contingency definitions survived in that test; nothing else was audited.

If you are stuck on a build where only `PWB21` writes, carry the models across in an aux. The PFW
models are their own object types, one per model class, so export each from a case that still has
them and load them onto the saved one:

```python
PFW_TYPES = ["GenMWMax_SolarPVBasic1", "GenMWMax_SolarPVBasic2", "GenMWMax_WindClass1",
             "GenMWMax_WindClass2", "GenMWMax_WindClass3", "GenMWMax_WindClass4"]
for t in PFW_TYPES:                                   # on the case that HAS the models
    pw.esa.SaveData(pfw_aux, "AUX", t, ["ALL"])       # skip types the case has none of
# later, on the PWB21-saved case
pw.esa.LoadAux(pfw_aux, create_if_not_found=True)
assert (pw[Gen, ["TSPFWModelString"]]["TSPFWModelString"].astype(str).str.len() > 2).sum() == n_renewables
```

`TSPFWModelString` is read-only, so the only way to restore it is through the model objects.
Setting `UIVisible = True` (before or after `OpenCase`) and setting the QV output directory did not
fix the `PWB` failure.

**Fixed on the build dated 2026-09-28: `PWB` and `PWB24` write again.** Measured 2026-09-30 on five
~10k-bus synthetic cases: each `PWB24` file, reopened cold in a fresh process, matched the source
exactly on buses, branches, shunts and their control modes, generators and contingencies, and
solved. Two rules follow:

- **Plain `PWB` is the newest format.** Someone on Simulator 24 cannot open it. Save
  `SaveCase(path, PWB24);` for anyone who runs 24, and say so wherever you hand the file over.
- **A file once saved as `PWB21` stays stripped.** Re-saving it as `PWB24` does not bring back what
  `PWB21` dropped. Restore the PFW models from an earlier case first, then save.

Even a format that keeps the PFW models may not keep the TimeStep run around them. Suspected, not
confirmed (build 2026-09-25): a script-form `SaveCase` kept the PFW models but dropped the loaded
weather hours and the unit selections. Reload the weather after reopening rather than trusting the
saved file to carry it ([timestep-simulation-setup](timestep-simulation-setup.md)).

A path bug worth knowing: building the path in a shell string with `\\$var` turns into a literal
`$var`, and SaveCase then reports *"Windows has prevented us from writing to the file"*. That
message means a bad path as often as a permission problem; print the path before blaming access.

### Typical use: save a solved design so a human can open it

Open the base case, apply a design, solve, then save — the pattern for handing a
reviewer a case they can open:

```python
pw = tep.open_case(scenario_path)
try:
    tep.set_target_loads(pw)
    tep.apply_design(pw, design)     # CreateData buses/branches/loads — see methods/adding-devices-esapp.md
    tep.solve_dcopf(pw)
    out = os.path.abspath(r"C:\...\Outputs\Synth2k_scenarioA.pwb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
    assert os.path.exists(out)
finally:
    pw.close()
```

Saving before `pw.close()` captures the in-memory edits (new devices + solved state); the reopened
`.pwb` shows exactly what was built.

> House rules honored: drive SimAuto via `esapp` `RunScriptCommand` (not raw `esa`, not the flaky COM
> `SaveCase`); verify the artifact exists before claiming success (see [esapp](../concepts/esapp.md)).
