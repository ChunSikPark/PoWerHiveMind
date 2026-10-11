# PowerWorldHiveMind - METHODS

# ==== adding-devices-esapp.md ====

---
type: method
domain: tooling
aliases: [add-devices, create-devices, createdata, add-buses-branches]
tags: [esapp, powerworld, createdata, device-creation, dcopf, contingency, n-1]
---

# Adding devices to a PowerWorld case via esapp

## Abstract

How to programmatically create buses, branches (lines/transformers) and set loads in an open
PowerWorld case with `esapp`, then solve a DC OPF and screen N-1 — the write-side mechanics the
read-focused [esapp-overview](esapp-overview.md) doesn't cover. Read this before writing any transmission-expansion /
what-if code. The headline gotcha: `CreateData` **silently no-ops** unless every primary + secondary
+ required key field is supplied, and PowerWorld truncates `LineCircuit` to **2 characters**. All
symbols below were live-verified against the installed package (not guessed).

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esa pp llm
- **Across:** [esapp-overview](esapp-overview.md) · [esapp-schema-reference](../references/esapp-schema-reference.md) · [powerworld-simauto](../concepts/powerworld-simauto.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The write path: `pw.esa.CreateData` (not the bracket writer)

For creating objects use the SAW script command `CreateData` on `pw.esa`. Wrap creation in EDIT mode:

> **Why not the bracket writer?** Through esapp 0.1.x it *rejected* read-only key/status fields
> outright, which settled the question. On **0.2.1 it only warns and writes anyway**, so
> `pw[GType] = df` can now create objects too (EDIT mode + `CreateIfNotFound=True` + a complete
> key set). `CreateData` is still preferred here because it states the intent to create, fails
> loudly on a malformed field list, and does not bury a real problem under a
> `UserWarning: Read-only field(s)` that is usually a false alarm — see
> [esapp](../concepts/esapp.md).

```python
pw.edit_mode()
pw.esa.CreateData("Bus", ["BusNum", "BusName", "BusNomVolt", "AreaNum", "ZoneNum"],
                  [9100, "NEW500", 500.0, 1, 1])
pw.run_mode()
```

**The #1 gotcha — silent no-op on missing key fields.** `CreateData` writes nothing (no error, no
change) unless EVERY *primary + secondary + required* field for that object type is present. For a
**Branch** that means all of:

- primary: `BusNum`, `BusNum:1`, `LineCircuit`
- secondary/composite: `BusName_NomVolt`, `BusName_NomVolt:1` (the "name_nomvolt" bus identifiers)
- required: `LineR`, `LineX`, `LineAMVA`, **`LineAMVA:1`, `LineAMVA:2`** — all THREE MVA limits, even
  if the study only uses the A limit. Supplying only `LineAMVA` silently skips the branch.

```python
# build the BusName_NomVolt map AFTER creating any new buses so both ends resolve
nv = {int(x["BusNum"]): x["BusName_NomVolt"] for _, x in pw[Bus, ["BusName_NomVolt"]].iterrows()}
pw.esa.CreateData(
    "Branch",
    ["BusNum", "BusName_NomVolt", "BusNum:1", "BusName_NomVolt:1", "LineCircuit",
     "LineR", "LineX", "LineAMVA", "LineAMVA:1", "LineAMVA:2", "LineStatus"],
    [frm, nv[frm], to, nv[to], "N1", 0.0, x_pu, mva, mva, mva, "Closed"])
```

Check `GType.keys()` / `.secondary()` / `.identifiers()` (classmethods, call with `()`) to see the
full required set for any type — see [esapp-schema-reference](../references/esapp-schema-reference.md).

**Always verify the count went up.** Because failures are silent, assert `pw.n_bus` / `pw.n_branch`
increased by the expected amount after creation and raise otherwise — never solve a partially-applied
design:

```python
n0 = int(pw.n_branch)
# ... create branches ...
assert int(pw.n_branch) - n0 == n_expected, "CreateData silently skipped devices — check key fields"
```

### Parallel-circuit IDs: any distinct short string (mind the 2-char cap)

Parallel circuits between the same bus pair just need **distinct** `LineCircuit` IDs — any short
string works: `1`, `2`, `11`, `22`, `33`. The only trap is PowerWorld's ~2-char cap: a 3-char ID gets
truncated, so distinct-*looking* IDs can collide — `NE1` and `NE2` both become `NE`, and the second
silently no-ops. Keep circuit IDs ≤ 2 chars and distinct per pair.

> The `esa_pp_llm` pipeline tagged its new circuits with an `N` prefix (`N1`, `N2`) **only** so its
> own code could detect which devices were new — that prefix is a project convention, not a
> PowerWorld requirement.

### Setting a load: write `LoadSMW`

`LoadSMW` is the scheduled ("pure") load value — the constant-power setpoint you specify. `LoadMW` is
the load's actual MW **when it is connected / in service**. So to place or change a load, write
`LoadSMW`; read `LoadMW` for the connected value.

```python
pw.esa.CreateData("Load", ["BusNum", "LoadID", "LoadSMW", "LoadSMVR", "LoadStatus"],
                  [bus, "1", 1000.0, 0.0, "Closed"])
```

### Creating a switched shunt: the bracket writer DOES work, and three fields are traps

Measured 2026-09-07 on Synth9k (10,476 buses, 1,187 existing shunts), adding 11 capacitor banks.

**`ChangeParametersMultipleElement` cannot create a shunt** - it answers `Object not found` for
every row, because it only modifies objects that already exist. Creation goes through the bracket
writer, which despite this page's general advice above *does* work for `Shunt`:

```python
from esapp.components import Shunt
pw.edit_mode()
pw[Shunt] = df          # one row per new bank
pw.run_mode()
assert len(pw.esa.GetParametersMultipleElement("Shunt", ["BusNum","ShuntID"])) - n0 == n_expected
```

**`SSMinMVR` and `SSMaxMVR` are NOT writable.** They are *derived* from the blocks. Pass them and
esapp 0.1.x raised `Cannot set read-only field(s)`; **0.2.1 only warns, sends the write, and
PowerWorld discards it** — so on 0.2.1 you get a silent no-op instead of an error. Size the bank
through the block instead and read the limits back afterwards to confirm.

Unlike the `Branch`/`Gen` false alarms in [esapp](../concepts/esapp.md), this one is a **true**
read-only: PowerWorld's own `enterable` column is blank for both fields, which is why the write
vanishes. That is the test to apply whenever you see the warning —

```python
fl = pw.esa.GetFieldList('shunt')
fl[fl.internal_field_name.isin(['SSMinMVR','SSMaxMVR'])][['internal_field_name','enterable']]
```

✅ **Verified live 2026-09-10** (~2,000-bus synthetic case, 157 shunts, build 2026-07-22, esapp 0.2.1):
`enterable` blank for both; `pw[Shunt] = df` with `SSMinMVR = -999.0` raised nothing and left
the value at `-15.0`.

**The block spelling is `SSBlockMVarPerStep` - capital V, and block 0 carries NO `:0` suffix**
(`:1` through `:9` are blocks 1-9). Same for `SSBlockNumSteps`. This is settled by esapp's own
`Shunt.settable()`, not inferred: `SSBlockMvarPerStep:0` is tolerated on the READ side, which is
exactly what makes the wrong spelling survive - PowerWorld accepts an unrecognised field silently,
so a misspelled block name leaves a shunt with capacity and no block definition and no error.

A complete, working continuous capacitor bank regulating its own bus:

```python
{"BusNum": n, "ShuntID": "1", "BusName_NomVolt": name_nomvolt[n],
 "SSStatus": "Closed", "SSCMode": "Continuous", "AutoControl": "YES",
 "SSRegulates": "Volt", "SSRegNum": n,          # SSRegNum, not SSRegBusNum
 "SSVLow": 0.96, "SSVHigh": 1.06,               # SSVLow < SSVHigh is mandatory
 "SSBlockMVarPerStep": mvar, "SSBlockNumSteps": 1,
 "SSNMVR": mvar,                                # seed to dispatch, NEVER 0
 "AreaNum": area, "ZoneNum": zone}
```

`SSNMVR` seeded at 0 can diverge a stressed case by yanking reactive sources to zero as the
solver's initial guess - see remediating base case violations.

**Sizing: let PowerWorld measure it, do not estimate.** Install a deliberately oversized continuous
bank, solve, and read back `SSNMVR` - the dispatched value IS the requirement. Then reinstall at
that value (rounded up to a standard bank size) and confirm nothing rails at its own cap, which
would mean the requirement was truncated by the probe. Required MVAr does not track depth of
violation: on Synth9k a bus needing +0.0335 pu took 10 MVAr while one needing +0.0277 took 50,
because the difference is system strength at the bus, not how far it had sagged.

**Regulation is a deadband, not a target.** With `[SSVLow, SSVHigh] = [0.96, 1.06]`, a bank that
lands the bus anywhere inside that band has no reason to back off, so the final dispatch depends on
where the solve started. If you need provably-minimal dispatch, tighten the band - do not shrink
the bank.

### Transformer vs line: you MUST flag it — kV mismatch is not enough

A branch whose two ends sit at different nominal kV is *physically* a transformer, but PowerWorld will
**not** infer that. `BranchDeviceType` is **read-only** ("determined by other settings"), so a plain
`CreateData` with only line fields lands the device as a `Line` even across a 500→230 kV step — the
exact bug that put 500/230 transformers into a case as lines. Flag it explicitly with `LineXfmr="YES"`
plus the transformer nominal fields:

```python
fields = [..., "LineStatus"]                       # the usual line fields
values = [..., "Closed"]
if from_kv != to_kv:                               # or a design "Xfrmr"/"DeviceType" flag
    fields += ["LineXfmr", "XFNominalKV", "XFNominalKV:1", "XFMVABase", "LineTap"]
    values += ["YES", from_kv, to_kv, mva, 1.0]    # XFNominalKV per side; tap ratio 1.0
pw.esa.CreateData("Branch", fields, values)
```

After creation, verify: `pw[Branch, ["BranchDeviceType"]]` should read `Transformer` (not `Line`) for
those rows. `LineXfmr="YES"` alone flips `BranchDeviceType`; `XFNominalKV(:1)`, `XFMVABase`, and
`LineTap=1.0` give it a well-defined turns ratio so the DC OPF solves unchanged. Live-verified on
Synth2k: agent design → 10 lines + 10 transformers; expert → 13 + 12.

### Substations

Substations have **no key fields** and are **not needed for DC power flow** — don't create them for a
DC study. Their lat/lon is only useful for right-of-way / distance (cost) calculations.

### Solving a DC OPF and reading the objective

```python
pw.dc_mode = True          # DC approximation
pw.run_mode()
pw.esa.SolvePrimalLP()     # the LP OPF; with dc_mode this is the DC OPF
tfc = float(pw[OPFSolutionSummary, :]["LPOPFCostFunction"].iloc[0])   # "Total Final Cost"
```

`OPFSolutionSummary.LPOPFCostFunction` is the OPF objective ("Total Final Cost").

### Overloads: tolerate the binding-at-limit edge

`pw.overloads(threshold=100.0)` returns branches at/over `threshold` percent. The LP OPF **binds lines
to exactly 100.000% of rating** at the economic optimum, and solver float noise then reads
~100.000001% — a fully-loaded (not overloaded) line. Use a small tolerance so a binding constraint
isn't misreported as a violation:

```python
overloaded = pw.overloads(threshold=100.1)   # >100.1% = a real overload; <=100.1% = at-limit
```

### N-1 on new devices — just run the contingency analysis (don't hand-roll it)

PowerWorld's built-in **contingency analysis** applies each outare-solves, records
violations/non-convergence, and **restores the base case automatge, ically** — you never open or re-close
anything yourself. Run it in DC mode by setting `DCApprox=YES` and the CTG method to `DC`. Verified
call sequence (from `esa_pp_llm/Functions/contingency.py`):

```python
# DC contingency analysis
pw.esa.SetData("Sim_Solution_Options", ["DCApprox"], ["YES"])          # DC power flow
pw.esa.SetData("CTG_Options", ["CTG_CalculationMethod"], ["DC"])
pw.esa.SolvePowerFlow()
pw.esa.CTGClearAllResults()
pw.esa.CTGSolveAll()                                                    # solves all defined contingencies

# read results (per-contingency solve/violation flags + branch loading)
ctg    = pw[Contingency, [Contingency.CTGSolved, Contingency.CTGViol]]   # CTGSolved=="YES", CTGViol>0
branch = pw[Branch, [Branch.CTGViol, Branch.LineMaxPercentContingency, Branch.CTGSolved]]
n_diverged  = int((ctg["CTGSolved"] != "YES").sum())
n_violating = int((ctg["CTGViol"] > 0).sum())
```

The contingencies themselves must exist in the case first — define one per new device (open that
line/transformer), e.g. via `ContingencyBuilder`/`SimAction` (`esapp.utils`) or by auto-inserting
N-1 branch contingencies. `CTGViol`/`CTGSolved` on the `Contingency` object give per-contingency
violation counts and convergence; `Branch.LineMaxPercentContingency` gives the worst loading seen.

The `esa_pp_llm` bench wraps all of this as **`run_contingency(pw, method="DC", ...)`** →
`solve_contingency` (the `SetData`/`CTGSolveAll` above) + `get_contingency_results` (the result
frames) + an optional summary. For AC, pass `method="AC"` (`DCApprox=NO`).
A manual snapshot→open→re-solve
loop is unnecessary — it just re-implements, worse, what `CTGSolveAll` already does.

### Recovering the devices a case already added (diff a modified vs base case)

To reverse-engineer what a solved/modified case added over its base, diff the branch-key sets:

```python
def branch_keys(pw):
    df = pw[Branch, ["BusNum", "BusNum:1", "LineCircuit"]]
    return {(int(r["BusNum"]), int(r["BusNum:1"]), str(r["LineCircuit"])) for _, r in df.iterrows()}

added_branches = branch_keys(modified_pw) - branch_keys(base_pw)   # (f, t, ckt) tuples
added_buses    = set(bus_kv(modified_pw)) - set(bus_kv(base_pw))
```

A branch whose two endpoint buses have different nominal kV is a transformer; equal kV is a line.

> House rules honored: drive SimAuto via `esapp` (not raw `esa`); always keep an object's key
> field(s) on any write or it silently no-ops (see [esapp](../concepts/esapp.md)).


---

# ==== applying-a-dispatch-to-a-case.md ====

---
type: method
domain: tooling
aliases: [applying-a-dispatch, apply-dispatch, dispatch-to-case, scenario-case-build, write-genmw, open-unused-generators]
tags: [esapp, powerworld, simauto, dispatch, scenario, dcpf, genmw, genstatus, slack, load-scaling]
---

# Applying a dispatch to a PowerWorld case (and saving it as a scenario `.pwb`)

## Abstract

How to turn a computed dispatch (a MW number per generator) into a runnable scenario case:
write `GenMW`, switch the unused units `Open`, scale load to the scenario's level, solve DC,
and save. The headline gotcha is **the DC solve will fake a balance rather than tell you the
fleet is short** — it pushes the entire deficit through the slack *bus's* generators, past
nameplate, and the resulting branch overloads look like a transmission finding while being a
pure artifact. Verify the schedule against load **before** you trust any flow. Second trap:
esapp's `pw[Obj, field] = values` setter is **positional over the whole object table**, so a
filtered subset writes nothing, silently. Live-verified on Synth9k/Synth8k 2031, 2026-08-18.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · dispatch
- **Across:** [save-powerworld-case](save-powerworld-case.md) (the `SaveCase` no-op trap this depends on) ·
  [adding-devices-esapp](adding-devices-esapp.md) (same key-field discipline, and the `CreateData` silent no-op) ·
  [converting-lines-to-transformers](converting-lines-to-transformers.md) (the other place esapp's static whitelist is wrong) ·
  [case-impedance-completeness](../concepts/case-impedance-completeness.md) (**check this before promising anyone AC** — the cases
  these scenarios are built from are DC-only skeletons) · artifact-level validation
  (reopen the saved `.pwb` cold; a save that "succeeded" is not evidence)

## Content

### Steps

1. **Compute the dispatch first, in pure pandas, against a read-only pull.** Keep the
   allocation logic in a module with no `SaveCase` in it, so it can be tested and re-run
   without a license risk. The case write is a separate, dumb step.

2. **Scale load to the scenario level.** Write `LoadSMW` (and `LoadSMVR` by the same factor,
   to hold power factor — DC ignores Q, but the case stays usable later). Do **not** assume
   every load scales: on the 2031 planning cases the 224 buses named `*_DataCenter` /
   `*_LargeLoad` (41,465.0 MW) are flat 24/7 and are held fixed, so the scenario % applies
   only to the 6,880 ordinary loads. That tag lives **only in `Load.BusName`** — `Label`,
   `CustomString*` are empty and `Interruptible` is `NO` on every record.

3. **Write `GenMW` and `GenStatus` together, as full-length columns.**

   ```python
   pw.edit_mode()
   for col in ("GenMW", "GenStatus"):          # full table, original row order
       s = gens_full[col]
       pw[Gen, col] = s.astype(str).tolist() if s.dtype == object else s.tolist()
   ```

   `GenStatus` is `"Open"` for every unit dispatched to 0 MW — that is what "take it out of
   service for this scenario" means.

4. **Keep every generator on the slack BUS closed**, even at 0 MW, or the solve has nothing
   to swing. Note *bus*, not unit: bus 7738 hosts **11** generators on both the 8k and 9k
   planning cases, and a naive "keep the first gen at the slack bus" rule under-reports the
   swing by 10×.

5. **Solve and save.** `pw.run_mode()` before `SolvePowerFlow`, then the aux-script save form
   from [save-powerworld-case](save-powerworld-case.md):

   ```python
   pw.run_mode()
   pw.esa.RunScriptCommand("SolvePowerFlow(DC);")
   pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
   assert os.path.exists(out)
   ```

### The trap: a DC solve fakes the balance at the slack bus

**Post-solve generation always equals load. That is not evidence of anything.** If the
scheduled dispatch cannot meet the load, PowerWorld closes the gap by driving the slack bus's
generators as far past their own `GenMWMax` as it takes.

Measured on `Synth8k_draft`, Scenario 4 (High Load – No Solar), short **31,248.5
MW**: each of the 11 generators at bus 7738 was pushed **+2,840.8 MW over nameplate** — a
44.5 MW unit landed at 2,885 MW — producing **366 branches over 100% and a 683.4% maximum**.
Those overloads are entirely an artifact of 31 GW injected at one 345 kV bus.

It is **not** AGC doing this, so do not go looking there: area `AGC_AGCStatus` is `0` on all
8 zones and exactly **1 of 1,467** generators is `GenAGCAble`.

The check that actually works, before reading a single flow:

```python
short = abs(scheduled_gen_mw - target_load_mw) >= 1.0   # compare the SCHEDULE, not the solve
```

and a post-hoc confirmation on the saved file:

```python
(post_solve_gen_mw > gen_mwmax + 0.1).sum() == 0        # nothing above nameplate
```

Refuse to save a scenario that fails the first check (a `--strict` flag), or you ship a case
whose branch loading is fiction.

### The trap: the positional setter

`pw[Obj, field] = values` is **positional over the entire object table**. Handing it a
filtered subset resolves every record to NAN and writes nothing — no exception, no warning.
Build the full-length column (edit by key into a copy of the full table) and write that. Same
family as the `CreateData` silent no-op in [adding-devices-esapp](adding-devices-esapp.md): **assert the effect,
never trust the absence of an error.**

### Verify it worked

Reopen every saved `.pwb` **cold** (fresh `PowerWorld(path)`, not the handle you wrote with)
and check all five:

- every dispatch key present in the case's `Gen` table (outer-join indicator, no `left_only`);
- `max|GenMW − DispatchMW|` at rounding noise (observed **3.4e-5** across 8 cases);
- `GenStatus` matches the intended Open/Closed set exactly (0 mismatches);
- closed-load MW equals the scenario target;
- **zero generators above nameplate**, and post-solve gen − load ≈ 0.

### Worked result (2026-08-18)

Five scenarios × two fleets, same loads (143,590.9 MW peak, same 41,465.0 MW fixed block):

| Fleet | Conventional | Outcome |
|---|---|---|
| Synth9k 2031 (post-swap, +thermal) | 102,099.4 MW | **5 of 5 balance at exactly 0.0 MW** |
| Synth8k 2031 draft (pre-swap) | 65,313.9 MW | 3 of 5; **Sce2 short 4,283.0 MW, Sce4 short 31,248.5 MW** |

The 8k shortfalls are genuine nameplate deficits — the whole conventional fleet runs flat out
— consistent with an earlier real-hour dispatch rebuild, larger here only because the datacenter block is held at full load while the rest scales down.

**Both base cases are DC-only skeletons** (`LineR ≤ 1e-6` and `LineC == 0` on 97.5% / 100% of
closed lines; median X/R **100,010** and **113,465**), so every scenario case built from them
inherits that and can never carry an AC study. See [case-impedance-completeness](../concepts/case-impedance-completeness.md).


---

# ==== aux-file-mode.md ====

---
type: method
domain: tooling
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


---

# ==== case-data-lint.md ====

---
type: method
domain: cross-cutting
aliases: [case-data-lint, lint-profile, data-quality-checks, case-sanity, shunt-steps,
  gen-below-min, missing-emergency-ratings, negative-reactance, islands-and-slacks, nominal-kv]
tags: [powerworld, esapp, case-quality, validation, switched-shunt, generator, ratings,
  topology, n-0]
---

# Linting a case for data defects that still solve

## Abstract

A case that converges can still be wrong, and the defects that matter most are the ones the
solve never complains about. A discrete shunt set to 40 Mvar when its blocks only switch in
steps of 15. A unit online below its own minimum output. Every branch rated on A and blank on
B and C, so an N-1 that monitors B checks nothing. The case-auditor's `lint` profile reads each
of these straight from the case, with no solve and no write, and names every object by its key
fields. It never stops a study; it says what is wrong, where, and whether it looks broken or
deliberate. On a synthetic planning model, measured 2026-10-10, the shunt-step rule matched an
independent engineer's hand count exactly, scenario by scenario, across all five dispatch
scenarios. The units-below-minimum rule found the same units the engineer did.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [ltc-regulation-checks](ltc-regulation-checks.md) (the regulating-mode set the
  shunt-band rule shares) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md)
  (which rate-set letter the N-1 reads)
- **Across:** [case-impedance-completeness](../concepts/case-impedance-completeness.md) (the other
  silent defect, a DC skeleton) · [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md)
  (the commonest source of units below their minimum)
- **Checked by:** the case-auditor's `lint.*` rules (`skills/case-audit/engine/rules_lint.py`),
  run with `--profiles base,lint`

## Content

### What each rule reads and why it matters

| rule | flags | fields | why the solve hides it |
|---|---|---|---|
| `lint.shunt_steps` | a `Discrete` shunt whose `SSNMVR` is beyond all its blocks together, or not reachable by whole steps | `SSBlockNumSteps[:1-9]`, `SSBlockMVarPerStep[:1-9]`, `SSNMVR` | the solve starts from the nominal setting whatever the blocks say |
| `lint.shunt_band_inverted` | a regulating shunt with `SSVHigh < SSVLow` | `SSVHigh`, `SSVLow`, `SSCMode` | the band is empty, so the shunt cannot regulate (an engineer reports PowerWorld switches such a control off; not tested here) |
| `lint.gen_below_min` | an online unit with `GenMW < GenMWMin` | `GenMW`, `GenMWMin`, `GenStatus` | the power flow does not enforce the minimum |
| `lint.gen_limits` | a missing MW or Mvar limit, one at ±9999, or max below min | `GenMWMax/Min`, `GenMVRMax/Min` | ±9999 is a format placeholder that reads as "no limit" |
| `lint.negative_x` | a closed branch with `LineX < 0`, star legs left out | `LineX`, `BusIsStarBus` | it solves; the branch's flow share comes out reversed |
| `lint.missing_ratings` | no rating A (jumpers left out), or rating A with no B or C | `LineAMVA`, `LineAMVA:1`, `LineAMVA:2`, `LimitSet.LSLineRateSet:1` | a 0 rating is never monitored |
| `lint.bus_names` | a blank `BusName` | `BusName` | breaks anything that finds a bus by name |
| `lint.islands` | energized islands apart from the main one; an island with load or generation and not exactly one slack | `BusStatus`, `LineStatus`, `BusCat` | each island solves, or fails, on its own |
| `lint.nominal_kv` | a nominal kV that is missing, 0, or has more than two decimals | `BusNomVolt` | kV-level filters skip the bus |

### How the shunt-step check decides

A discrete shunt can only sit on a whole number of steps of each block. The rule builds every
total the blocks can reach (each block from 0 to its step count, summed, rounded to 0.01 Mvar)
and asks whether `SSNMVR` is within 0.01 Mvar of one of them. Two steps of 15 reach 0, 15 and
30. A setting of 20 is *between steps*. A setting of 40 lies beyond the 30 maximum, so the rule
reports it as *beyond its blocks* instead. Every combination counts, not just in-order switching, so the
check errs towards fewer flags. A shunt with no blocks defined is skipped, because there is
nothing to check it against. A shunt whose blocks give more than 100,000 combinations is not
enumerated. It is listed instead, as an FYI that says it was not checked.

### Emergency ratings: Worth a look or FYI

Rating A with blank B and C is common: the public Texas2k case carries it on all 2,562 of its
rated branches. Whether that matters depends on what the N-1 reads. The rule looks at
`LSLineRateSet:1` in the limit sets in use. If that letter is B or C and the branches lack it,
those branches go unmonitored after an outage, and the finding is **Worth a look**, triaged Broken. If the N-1
reads A, the blanks are data still to fill, and the finding is **FYI**, triaged Your call. A rate set the N-1 uses
that is empty everywhere is a different, stopping rule: `mon.rate_set_empty`.

### A field that was not read

If the case did not return a field, or it reads blank on every row (a number as NaN, text as empty),
the engine treats it as not read and its rule reports nothing. That happens with an older snapshot, or with a PowerWorld that lacks the field. The engine
lists the rule under `rules_skipped` naming the field, and a rule whose one half could not run is
listed as run and as not checked for that half. Silence from a rule is not a pass.
The one exception is a switched-shunt block slot after the first: PowerWorld leaves an unused slot blank,
so a blank slot column is data and only a slot the case did not return counts as not read; a release that
returned blank for a slot a shunt really uses cannot be told apart by the data.
`BusName` gets no exception: every name blank reads as a field not returned, so `lint.bus_names` is listed
as not checked rather than flagging every bus.

### Thresholds

All are proposed defaults in `engine/thresholds.py`, not measurements: 0.01 Mvar step tolerance,
0.1 MW below minimum, ±9999 as the placeholder limit, 2e-4 pu as the jumper reactance (PowerWorld's
default zero-impedance threshold), and two decimals for nominal kV.

### Not in this version

These need a solve, a second case, or a scenario label that the case does not carry. Each is a
candidate for a later rule:

- a low-voltage or alternate solution
- regulators that conflict (a unit and a shunt holding the same bus to different targets)
- area interchange far from schedule
- load against generation by region
- a contingency count that dropped since the last version
- renewables online in a scenario that should have none


---

# ==== converting-lines-to-transformers.md ====

---
type: method
domain: tooling
aliases: [line-to-transformer, linexfmr, make-branch-a-transformer, branchdevicetype]
tags: [esapp, powerworld, simauto, branch, transformer, linexfmr, editmode]
---

# Converting a PowerWorld branch from Line to Transformer

## Abstract

How to reclassify existing `Branch` objects as transformers when a case models every branch as a
line even where the two ends sit at different nominal kV. Two gotchas, both live-verified on
Synth8k: **(1)** `BranchDeviceType` is derived and read-only — the real switch is `LineXFMR = "YES"`
plus `XFNominalKV`/`XFNominalKV:1`; **(2)** esapp flags every `XF*` field read-only from its own
**static whitelist**, which is wrong — the fields are writable in PowerWorld EDIT mode. On esapp
0.2.1 that flag is only a `UserWarning` and `pw[Branch] = df` works; on 0.1.x it raised and you had
to go around esapp via `pw.esa.ChangeParametersMultipleElement`. With `XFFixedTap = 1.0`
and `LineC = 0`, the conversion is electrically a **no-op** (verified: max |ΔV| = 0.0 pu,
max |ΔMW| = 0.0) — pure reclassification, R+jX untouched.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esapp package
- **Across:** [adding-devices-esapp](adding-devices-esapp.md) · [save-powerworld-case](save-powerworld-case.md) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) · [esapp-overview](esapp-overview.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### When you need this

A case where transmission was built branch-by-branch (synthetic-grid pipelines do this) can end up
with every branch typed `Line`, including the step-down connections. Symptom: `pw.transformers()`
returns empty and `BranchDeviceType.value_counts()` is 100% `Line`, yet many branches have
`BusNomVolt != BusNomVolt:1`.

The mismatched-nominal-kV test is the right detector — check the pairs it finds are sane step-downs
before trusting it. On Synth8k the only pairs were 765/345, 345/138, 138/69 (1586 of 13523 branches).

### The two traps

**`BranchDeviceType` is derived.** You cannot set it. It reports `Transformer` once `LineXFMR` is
`YES`. Setting `LineXFMR` alone is the switch; the `XF*` fields are the transformer's parameters.

**esapp's read-only list is a static whitelist, not PowerWorld truth.** It marks every `XF*`
field read-only — `['LineXFMR', 'XFAuto', 'XFNominalKV', 'XFNominalKV:1', 'XFFixedTap',
'XFMVABase', 'XFTapMin', 'XFTapMax', 'XFStep', 'XFTapDegree', 'XFRegMin', 'XFRegMax',
'XFRegBus', 'XFUseLineZ', 'XFPhaseType']` — and PowerWorld disagrees. What that costs you
depends on your esapp version:

| esapp | `pw[Branch] = df` with `XF*` columns |
|---|---|
| 0.1.x | **raises** `ValueError: Cannot set read-only field(s) on Branch: [...]` — the bypass below was mandatory |
| 0.2.1 | **warns** `UserWarning: Read-only field(s) on Branch: [...]` and the write goes through |

✅ **Verified live 2026-09-10** (~2,000-bus synthetic case, Simulator build 2026-07-22, esapp 0.2.1): a
2-row `pw[Branch] = df` carrying `LineXFMR='YES'` raised nothing and flipped
`BranchDeviceType` from `Line` to `Transformer`.

So **on 0.2.1 the bracket writer is the recipe** — just don't run under
`-W error::UserWarning`, which turns that harmless warning back into a hard failure.

### The recipe (esapp 0.2.1)

```python
pw.edit_mode()                     # required — these are EDIT-mode fields
pw[Branch] = df                    # keys + XF* columns; warns, writes
pw.run_mode()
```

`df` must carry the key columns (`BusNum`, `BusNum:1`, `LineCircuit`) — the bracket read
includes them automatically, so a read-modify-write round-trip is safe. A filtered subset
is fine: PowerWorld matches rows by key, so writing 1586 of 13523 branches touches only
those 1586.

**On 0.1.x**, or any time you want to skip the warning entirely, go around esapp:

```python
pw.edit_mode()                     # required — these are EDIT-mode fields
pw.esa.ChangeParametersMultipleElement("Branch", fields, values)
pw.esa.EnterMode("RUN")
```

with `fields` (keys first, as always):

```python
["BusNum", "BusNum:1", "LineCircuit",      # keys — omit and it silently no-ops
 "LineXFMR", "XFAuto",                     # "YES", "NO"
 "XFNominalKV", "XFNominalKV:1",           # = each end's BusNomVolt
 "XFTapPos", "XFFixedTap", "XFMVABase",    # 0.0, 1.0, 100.0
 "XFTapMin", "XFTapMax", "XFStep",         # 0.51, 1.5, 0.00625
 "XFTapDegree", "XFRegMin", "XFRegMax"]    # 0.0, 0.51, 1.5
```

`LineCircuit` must be a **string** (`"1"`, not `1`). `XFConfiguration` is derived — it self-populates
to `Unknown`; don't try to set it.

### House defaults (from Synth2k_series2)

Worth knowing these are not invented: all 1351 transformers in
`Synth2k_series2_case1` share **identical** settings, so this is the series' convention:

| Field | Value | Meaning |
|---|---|---|
| `LineXFMR` | `YES` | the actual type switch |
| `XFAuto` | `NO` | automatic control off (the field takes `YES`, `NO` or `OPF`; it is not an autotransformer flag) |
| `XFNominalKV` / `:1` | each end's `BusNomVolt` | |
| `XFFixedTap` | `1.0` | **fixed tap** — no LTC control |
| `XFTapPos` | `0.0` | |
| `XFMVABase` | `100.0` | matches system base |
| `XFTapMin` / `XFTapMax` / `XFStep` | `0.51` / `1.5` / `0.00625` | 160 steps |
| `XFRegMin` / `XFRegMax` | `0.51` / `1.5` | regulation range |
| `XFTapDegree`, `XFUseLineZ`, `XFPhaseType`, `XFRegBus` | `0` | not a phase shifter |
| `LineC` | `0.0` | transformers carry no line charging |

`XFAuto=NO` + `XFTapPos=0` + `XFFixedTap=1.0` means **fixed-tap, non-regulating**. If a study needs
these regulating voltage (e.g. reactive power planning), that is a separate setup — regulated bus
and setpoint scheme — not covered here.

### Verify it was a no-op

The whole point of copying `XFFixedTap = 1.0` is that the power flow should not move. Solve before
and after and assert it:

```python
pw.pflow(); before = pw[Branch, "LineMW"]["LineMW"]; vb = pw.voltage(complex=False)[0]
# ...convert...
pw.pflow(); after = pw[Branch, "LineMW"]["LineMW"]; va = pw.voltage(complex=False)[0]
assert (va - vb).abs().max() == 0.0 and (after - before).abs().max() == 0.0
```

This holds **only if** the converted branches already had `LineC == 0`. Check that first — a branch
with real line charging will move when reclassified, because a transformer's `LineC` is magnetizing
susceptance, not π-model charging. Zeroing nonzero charging is a modelling decision, not a cleanup;
surface it rather than doing it silently.

Then save via the aux script command, never the COM function — see [save-powerworld-case](save-powerworld-case.md):

```python
pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
assert os.path.exists(out)
```

Reopen the saved file and re-check `BranchDeviceType.value_counts()`; EDIT-mode writes that look fine
in-session are worth confirming survived the round-trip.

### Worked application

an 8,000-bus working model (reactive power planning inputs):
13523 branches, all typed `Line`, 1586 with mismatched nominal kV and all with `LineC = 0`.
Converted to 1586 transformers with the table above; power flow bit-identical; written to
`..._xfmr.pwb` (a new file — the source WIP case was left untouched).


---

# ==== esapp-overview.md ====

---
type: method
domain: tooling
aliases: [esapp-howto, using-esapp, esapp-getting-started]
tags: [esapp, powerworld, simauto, python, getting-started]
---

# Method: Getting started with ESA++ (esapp)

## Abstract

The entry-point how-to for driving PowerWorld from Python with `esapp`: open a case, read and write data with the bracket interface, solve power flow, inspect results, and use `snapshot()` for safe experimentation. All code snippets are verified against the `esapp` source at `C:\path\to\esapp`. This is Step 1 of the flagship trail; for the full API map see [esapp](../concepts/esapp.md).

## Connections

- **Up:** [Home](../index.md) · esapp package
- **Across:** [esapp](../concepts/esapp.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · esa pp llm · flagship step 1 — next: [timestep-simulation-setup](timestep-simulation-setup.md) · [pww-data](../concepts/pww-data.md) · [how-to-analyze-results](how-to-analyze-results.md)

## Content

**Step 1 of the flagship trail** → next: [timestep-simulation-setup](timestep-simulation-setup.md).
What esapp *is* (the full API map): [esapp](../concepts/esapp.md). The COM server underneath:
[powerworld-simauto](../concepts/powerworld-simauto.md).

This is the "how do I actually drive a PowerWorld case from Python" entry point.
All snippets below are verified against `C:\path\to\esapp`.

## 0. Prereqs

Windows + PowerWorld Simulator installed (SimAuto is a COM server). Use the
project venv `C:\path\to\.venv` (Python 3.13, `esapp` editable).
See esapp package for the exact environment.

## 1. Open a case

```python
from esapp import PowerWorld
from esapp.components import Bus, Gen, Load, Branch, Shunt, Area, Zone

pw = PowerWorld(r"D:\path\to\case.pwb")   # opens via SAW(..., CreateIfNotFound=True)
pw.summary()          # dict: n_bus, n_branch, n_gen, n_load, total_gen_mw,
                      #       total_load_mw, v_min, v_max, sbase
pw.n_bus, pw.n_gen    # quick integer properties
```

## 2. Read data — bracket syntax

Everything comes back as a pandas DataFrame; primary-key columns are always
included.

```python
pw[Bus]                                   # key columns only
pw[Bus, "BusPUVolt"]                      # keys + one field
pw[Gen, ["GenMW", "GenMVR", "GenStatus"]] # keys + several
pw[Bus, :]                                # keys + every defined field
```

Convenience tables exist for the common ones: `pw.gens()`, `pw.loads()`,
`pw.shunts()`, `pw.lines()`, `pw.transformers()`, `pw.flows()`,
`pw.overloads(threshold=100.0)`, `pw.areas()`, `pw.zones()`.

## 3. Write data — same syntax (sent to PowerWorld immediately)

```python
pw[Gen, "GenMW"] = 100.0              # broadcast scalar to all existing gens
pw[Gen, "GenMW"] = [100, 150, 200]    # per-element (length must match)

# read-modify-write a whole table
loads = pw[Load, ["LoadMW", "LoadMVR"]]
loads[["LoadMW", "LoadMVR"]] *= 1.10
pw[Load] = loads                      # bulk update; must carry primary keys
```

Bulk `pw[Type] = df` can also create new objects — but only in EDIT mode
(`pw.edit_mode()`) with `CreateIfNotFound=True`, and the DataFrame must carry a complete
key set. A filtered subset is fine: PowerWorld matches rows by key, so writing 3 rows
touches 3 objects.

On esapp 0.1.x a read-only column made the whole write raise. **On 0.2.1 it only emits
`UserWarning: Read-only field(s)` and the write is attempted anyway** — and that warning is
more often wrong than right (112 `Branch` fields, 33 `Bus`, 5 `Gen`, 1 `Load` are enterable
in PowerWorld but flagged read-only by esapp). Treat it as advisory, check
`pw.esa.GetFieldList(<type>)`'s `enterable` column for the real answer, and confirm writes
by reading the field back. See [esapp](../concepts/esapp.md).

## 4. Solve and inspect

```python
V = pw.pflow()                  # solve power flow -> complex voltage Series
mag, ang = pw.voltage(complex=False)   # (magnitude pu, angle rad)
P, Q = pw.mismatch()            # bus power mismatches
pw.violations(v_min=0.9, v_max=1.1)    # DataFrame of Low/High voltage violations
```

Matrices and sensitivities when you need them:

```python
Y = pw.ybus()                   # sparse Y-bus (dense=True for ndarray)
J = pw.jacobian()               # power-flow Jacobian
pw.ptdf(seller=101, buyer=205)  # PTDF column on branches
pw.lodf((101, 205, "1"))        # LODF for a branch outage
```

## 5. Safe experimentation

`snapshot()` is a context manager that calls `SaveState` on entry and
`LoadState` on exit, so the case is restored no matter what:

```python
with pw.snapshot():             # auto-saves/restores case state
    pw[Gen, "GenMW"] = scaled
    pw.pflow()
    v = pw.voltage()
# state restored here
```

Tune the solver via descriptor attributes before solving:
`pw.flat_start = True`, `pw.max_iterations = 30`, `pw.dc_mode = True`, etc.

## Where to go next

> **Note:** Older repos import `esa`; esapp is the updated, better-documented version of the same thing — write esapp. (Library choice only — unrelated to the TimeStep-vs-Transient-Stability distinction.)

- Run a study over time → [timestep-simulation-setup](timestep-simulation-setup.md) (then time step simulation)
- Pull weather into the study → [pww-data](../concepts/pww-data.md)
- Make sense of the outputs → [how-to-analyze-results](how-to-analyze-results.md)
- Full tool reference (matrices, GIC, network, TS) → [esapp](../concepts/esapp.md)

> esapp symbols on this page validated against `esapp` source
> (`C:\path\to\workbench.py` + `indexable.py`).


---

# ==== handling-errors.md ====

---
type: method
domain: tooling
aliases: [handling-errors, error-handling, troubleshooting, recovery, agent-errors]
tags: [errors, troubleshooting, recovery, agent-behaviour, powerworld, esapp]
---

# Method: Handling errors without bothering the user

## Abstract

What to do when something fails. Most PowerWorld failures are recoverable by the agent
alone, so recover and keep going — the user asked for an analysis, not a running
commentary on your debugging. This page sorts failures into **fix it yourself**,
**fix it and mention it**, and **stop and ask**, and gives the recovery for each. It
also covers the harder case: the call that did not fail but did nothing.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [preflight-powerworld](preflight-powerworld.md) · [esapp-environment](../concepts/esapp-environment.md) · [adding-devices-esapp](adding-devices-esapp.md)
- **Demo:** [adding-a-device](../demos/adding-a-device.md) — a real three-failure recovery, start to finish

## Content

### The three tiers

| Tier | Meaning | What you do |
|---|---|---|
| **1 — Fix silently** | The environment is missing something, or you made a recoverable mistake | Fix it and continue. Do not narrate it |
| **2 — Fix and mention** | You recovered, but the recovery changed the answer's meaning | Fix it, continue, and state it in the final report |
| **3 — Stop and ask** | A fact about the machine, or a decision that is genuinely the user's | Stop. Say exactly what is blocked and why |

The default is tier 1. Escalating a tier-1 problem to the user is itself a failure —
"should I install pandas?" is not a question worth a human's attention.

---

### Tier 1 — fix it yourself, say nothing

**A package is missing.**

```
ModuleNotFoundError: No module named 'esapp'
ModuleNotFoundError: No module named 'win32com'
ModuleNotFoundError: No module named 'pandas'
```

Install it and carry on. `pip install esapp`, `pip install pywin32`,
`pip install TeamOverbyeWeather`. Dependencies are plumbing; the user asked for an
analysis. If `pip` itself fails on permissions, retry with `--user` before escalating.

**You used the wrong access path.** These are the common ones, all verified:

| You wrote | Correct | Why |
|---|---|---|
| `pw.RunScriptCommand(...)` | `pw.esa.RunScriptCommand(...)` | The SAW wrapper is on `.esa` |
| `pw.overloads` | `pw.overloads()` | It is a method |
| `pw.flows`, `pw.ptdf`, `pw.lodf`, `pw.ybus` | all methods — call them | Same |
| `pw.dc_mode(True)` | `pw.dc_mode = True` | It is an assignable solver option, not a method |

**A field name is wrong.** Do not guess a second time. Read the whole table and look:

```python
df = pw[Branch, :]
print([c for c in df.columns if "mva" in c.lower()])
```

Then check [esapp-schema-reference](../references/esapp-schema-reference.md). Guessing field names is how you spend an hour.

**A write was rejected.** Many writes require EDIT mode. Wrap them:

```python
pw.edit_mode()
...
pw.run_mode()
```

**A relative path was not found.** Use an absolute path and retry. Relative paths
resolve against PowerWorld's working directory, not your script's.

---

### The dangerous case: it did not fail, it did nothing

This deserves its own section because no exception handler will catch it.

PowerWorld frequently accepts a malformed request, reports success, and changes nothing.
An agent that treats "no exception" as "it worked" produces a confident wrong answer,
which is worse than a crash.

**Assert the effect, never the absence of an error.**

```python
n0 = len(pw[Branch])
pw.esa.CreateData("Branch", fields, values)
assert len(pw[Branch]) - n0 == 1, "CreateData silently skipped the device"
```

Known silent failures, all verified:

| Operation | Silent failure | Guard |
|---|---|---|
| `CreateData` | Writes nothing if any required key field is missing | Count objects before and after; assert the delta |
| `pw[Obj, field] = values` | Positional over the whole table; a filtered subset writes nothing | Build the full column and assign that |
| COM `SaveCase` | No-ops | Use `pw.esa.RunScriptCommand('SaveCase(...)')`, then confirm the file's timestamp |
| DC solve | Reports zero mismatch even when generation is short | Compare the generation schedule against total load directly |
| Contingency results | Persist stale inside the `.pwb` | `CTGClearAllResults` before solving |
| `LODF` / `PTDF` | Returns `1e8` as an "undefined" sentinel, not a real value | Filter `abs(value) < 1e7` before ranking |
| Writes without key fields | Report success, change nothing | Keep `BusNum`, `GenID`, circuit id in every DataFrame you write back |

**A result that looks absurd is a bug, not a finding.** A branch with a 100,000,000
LODF, a 683% overload, a line at 12,000 MVA — treat these as your own error until you
have proven otherwise. Never report them as results.

---

### Tier 2 — recover, then say so

**The recovery changed what the answer means.** A real example from this case:

```
PowerWorldError: Error in script action execution:
Seller and Buyer can not be the same in script action CalculatePTDF
```

The case has exactly one area, so an area-to-area PTDF is impossible. The recovery is a
bus-to-bus transfer instead:

```python
g = pw[Gen, "GenMW"].groupby("BusNum")["GenMW"].sum().sort_values(ascending=False)
l = pw[Load, "LoadSMW"].groupby("BusNum")["LoadSMW"].sum().sort_values(ascending=False)
src = int(g.index[0])
snk = int(next(b for b in l.index if int(b) != src))   # must differ
P = pw.ptdf(seller=src, buyer=snk)
```

Note the second failure hiding inside the first: on this case the largest generator and
the largest load are **the same bus**, so the naive recovery reproduces the original
error. Force the buses to differ.

Report it as: *"the case has a single area, so I computed a bus-to-bus PTDF from bus 23
to bus 26 instead"* — because the user's mental model of the answer is now different.

**Power flow did not converge.** Escalate through the ladder, do not give up at step 1:

```python
pw.pflow(method="POLARNEWT")     # default
pw.pflow(method="RECTNEWT")      # different formulation
pw.flat_start = True             # reset the starting point
pw.dc_mode = True                # DC, if the study tolerates it
```

If only the DC solve converges, **say so** — a DC answer is not an AC answer.

**The result is empty.** A filter that returns nothing is usually a filter bug, not a
finding. Loosen it, confirm the unfiltered set is non-empty, then narrow again. Report
"no violations found" only after proving the query itself works.

---

### Tier 3 — stop and ask

Three cases, and only three.

**1. The SimAuto licence.** [preflight-powerworld](preflight-powerworld.md) failed on the COM check.

> PowerWorld's SimAuto add-on is licensed separately from Simulator, and this machine's
> licence does not appear to include it. Simulator itself may work fine. No code change
> can work around this — it needs whoever administers your PowerWorld licence.

Do not attempt workarounds. There are none.

**2. Something destructive.** Overwriting a case, deleting devices, writing outside a
scratch directory. Ask first, always. Default to saving somewhere new rather than in
place.

**3. A genuine modelling decision.** Which contingency set, which limit set, which
scenario, what counts as a violation. These change what the answer *means*, and guessing
produces a confident answer to a question the user did not ask.

Everything else you handle yourself.

---

### How to report a failure you could not fix

Bad:

> I encountered an error while trying to run the analysis.

Good:

> Preflight failed at check 4 of 5: the SimAuto COM server would not start
> (`com_error -2147221005, 'Invalid class string'`). That means PowerWorld automation is
> unavailable on this machine — most likely Simulator is not installed, or the licence
> does not include the SimAuto add-on. Simulator's own interface is unaffected.
>
> Nothing in the PowerWorld half of this kit can run until that is resolved. The weather
> side still works if that is useful.

State the check, the exact error, what it means, what you tried, and what remains
possible.

---

### The loop

1. **Read the error.** PowerWorld's messages are terse but usually accurate.
2. **Consult the page**, do not guess again. A second guess repeats the first mistake
   more expensively.
3. **Try the documented fix.**
4. **Assert the effect** — not the absence of an error.
5. **Two failed attempts at the same thing?** Change approach entirely rather than
   varying parameters.
6. **Only then** consider whether it is genuinely tier 3.

Track which pages you used. When you finish, cite them — a wrong answer then points at a
page that needs fixing, rather than at "the AI got it wrong."


---

# ==== how-to-analyze-results.md ====

---
type: method
domain: cross-cutting
aliases: [analyze-results, results-analysis, post-processing]
tags: [powerworld, analysis, post-processing, csv, solar, wind, renewables]
---

# Method: Writing code to analyze timestep-simulation results

## Abstract

How to write code that reads and analyzes the solar/wind generation CSVs produced by the timestep simulation. Covers the two-CSV-per-run naming convention, the 8-row metadata header layout (ISO, fuel type, PFW model string, max MW, state, utility, lat, lon), UTC timestamp conversion from PowerWorld's CST Excel-serial format, and typical pandas reductions for fleet profiles, capacity factors, and regional totals. This is Step 4 of the flagship trail; to plot the results see [visualize-renewable-output](visualize-renewable-output.md).

## Connections

- **Up:** [Home](../index.md) · time step simulation
- **Across:** flagship step 4 — prev: [pww-data](../concepts/pww-data.md) · next: [visualize-renewable-output](visualize-renewable-output.md) · start: [esapp-overview](esapp-overview.md) · [timestep-simulation-setup](timestep-simulation-setup.md)

## Content

**Step 4 (final) of the flagship trail.** ← prev: [pww-data](../concepts/pww-data.md) · start over:
[esapp-overview](esapp-overview.md). Owning project: time step simulation.

You've written the simulation ([timestep-simulation-setup](timestep-simulation-setup.md)) and produced the output
CSVs — this page is how those CSVs are structured and how to write code that reads
and reduces them. The analysis target here is the **solar/wind generation files**,
not a network/contingency report.

## What the simulation produces
Each run writes **two CSVs**: one solar, one wind. Naming:

| Run type | Solar file | Wind file |
|---|---|---|
| Historical (a full year of quarter files) | `Historical_2025_solar.csv` | `Historical_2025_wind.csv` |
| Forecast (a single `.pww`) | `Forecast_..._solar.csv` | `Forecast_..._wind.csv` |

## File layout (8 metadata rows, then hourly data)
`process_results(gen, df)` in `function.py` builds each CSV. The first column is
`DateTimeUTCExcelFormat`; every other column is one renewable generator. The file
opens with **8 metadata header rows**, then the hourly time series. The header rows,
in order, come from these generator fields:

| Header row | Source field |
|---|---|
| `ISO` | `CustomString:2` (assigned by the PFW_Insertion step) |
| `PV / Wind` | `GenFuelType` (`SUN` / `WND`) |
| `PV / Wind Types` | `TSPFWModelString` (the PFW model on the unit) |
| `Gen Max MW` | `GenMWMax` |
| `State` | `ZoneName` |
| `Utility` | `AreaName` |
| `Latitude` | `Latitude` |
| `Longitude` | `Longitude` |

Below the header rows, each data row is one UTC hour and each cell is that
generator's MW for that hour. The conversion has already happened by this point —
this file is post-conversion, so parse the column as UTC and do **not** shift it
again. The CST figure under *Timestamps* below describes PowerWorld's raw export,
not this CSV.

## How the values get there
- **Timestamps:** PowerWorld's **raw** export uses Excel-serial timestamps in CST
  (this is the input to the pipeline, not the CSV described above).
  `time_utils.convert_to_utc` shifts CST→UTC, subtracts an hour during US DST
  (second Sunday in March → first Sunday in November), rounds to the nearest hour,
  and writes ISO-8601 UTC strings. (`time_utils.py` is verified against real runs —
  don't change it without a reason.)
- **Solar vs wind split:** columns are matched to generators whose `GenFuelType`
  contains `SUN` (solar file) or `WND` (wind file), keyed by `'BusNum' 'GenID'`.

> **Note on forecast pre-processing:** `interpolate_to_hourly` exists in
> `time_utils.py` for forecast pre-processing but is NOT invoked by the current run
> path (`function.py` / `process_results` / `main.py`).

## Reading / analyzing the CSVs
Because the first 8 rows are metadata, load with pandas accordingly, e.g.:

```python
import pandas as pd
raw = pd.read_csv("Historical_2025_solar.csv")
meta = raw.iloc[:8]            # the 8 description rows (ISO, type, max MW, lat/lon...)
data = raw.iloc[8:].copy()     # hourly time series
data["DateTimeUTCExcelFormat"] = pd.to_datetime(data["DateTimeUTCExcelFormat"])
data.iloc[:, 1:] = data.iloc[:, 1:].astype(float)
```

Typical reductions once loaded: sum across generator columns for a fleet
solar/wind profile; group columns by the `ISO` / `State` / `Utility` metadata rows
for regional totals; divide by `Gen Max MW` for capacity factors; find peak/trough
hours for extreme-scenario screening.

To write matplotlib code that plots these reductions → [visualize-renewable-output](visualize-renewable-output.md).

## File the answer back
A good analysis is a wiki asset, not chat exhaust. Per [CLAUDE](../AGENTS.md), save notable
comparisons or charts as a new `concept`/`method` page, link it from
time step simulation and [index](../index.md), and append to log.

## Next

Plot the results → [visualize-renewable-output](visualize-renewable-output.md)

## Trail complete
[esapp-overview](esapp-overview.md) → [timestep-simulation-setup](timestep-simulation-setup.md) → [pww-data](../concepts/pww-data.md) →
**how-to-analyze-results** → [visualize-renewable-output](visualize-renewable-output.md) ✅


---

# ==== ltc-regulation-checks.md ====

---
type: method
domain: cross-cutting
aliases: [ltc-regulation-checks, ltc-regulated-bus, XFRegBus, XFRegTargetType, SSRegNum,
  regulates-nothing, ltc-middle-target, ltc-regulates-lv-side, repoint-the-regulator,
  ltc-causes-violation, which-bus-does-the-ltc-hold]
tags: [powerworld, esapp, transformer, ltc, tap, switched-shunt, voltage, case-quality,
  validation, remediation, n-0]
---

# Checking what each LTC and switched shunt actually regulates

## Abstract

A case can carry a full fleet of live load tap changers (LTCs) and still control voltage badly,
because what decides the outcome is not whether the LTCs are switched on but **which bus each
one holds and how it drives toward its band**. Three defects are common, and each one leaves
the power flow converging with no warning. (1) **A regulator pointed at nothing.** The regulated
bus (`Branch.XFRegBus` for an LTC, `Shunt.SSRegNum` for a switched shunt) does not exist or is
disconnected. (2) **`XFRegTargetType = Middle`**, the shipped value. When the regulated bus
leaves `[XFRegMin, XFRegMax]`, the LTC drives it back to the band's midpoint, not to the nearest
edge. A symmetric band then either lifts healthy buses or overshoots, and no band tuning fixes
both. `Max/Min` does. (3) **An LTC holding its low-voltage side while its high-voltage side is
out of band.** A tap is a ratio, not a source. Holding the LV bus moves the reactive deficit or
surplus onto the HV bus, so the LTC can cause the violation next to it. On a regional planning
model, measured 2026-09-14, re-pointing the regulated bus and switching the target type cleared
both emergency overvoltages and most normal-limit overvoltages. It added no devices.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [converting-lines-to-transformers](converting-lines-to-transformers.md) (writing
  `XF*` fields when esapp's whitelist refuses them) · [save-powerworld-case](save-powerworld-case.md)
  (a fix applied in memory and never saved is the commonest way to lose one) ·
  [adding-devices-esapp](adding-devices-esapp.md) (a switched shunt's `SSRegNum`)
- **Across:** [ranking-new-devices-by-severity](ranking-new-devices-by-severity.md) (a bus's own
  voltage limits, not the band you configured) ·
  [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md) (the other
  intact-case overvoltage, the one no LTC reaches) ·
  [violation-remediation](../demos/violation-remediation.md) (the diagnose-then-fix study this
  check feeds)
- **Checked by:** the case-auditor's `base.regulates_nothing`, `base.ltc_middle_target` and
  `base.ltc_regulates_lv_side` rules

## Content

### First, find out whether the fleet is live

Read these before drawing any conclusion about an LTC:

| field | what it tells you |
|---|---|
| `Branch.LineXfmr` | `YES` if the branch is a transformer |
| `Branch.LineXFType` | `Fixed`, `LTC`, `Mvar` or `Phase`. Only `LTC` regulates voltage |
| `Branch.XFAuto` | `YES`, `NO` or `OPF`: whether automatic control is on for this unit |
| `Branch.XFRegBus` | the bus it regulates. `0` on a fixed transformer |
| `Branch.XFRegMin` / `XFRegMax` | the voltage band, in per unit on the regulated bus |
| `Branch.XFRegTargetType` | `Middle` or `Max/Min` (below) |
| `Sim_Solution_Options.ChkTaps` | `YES` lets the solver move taps at all |

Three reading traps:

- **A band copied from the tap range never acts.** Some synthetic cases ship
  `XFRegMin`/`XFRegMax` = 0.51/1.5, the same numbers as `XFTapMin`/`XFTapMax`. Synth2k_series2
  does this on every transformer, alongside `XFAuto = NO` and `XFRegBus = 0`, so no unit there
  regulates anything (see [converting-lines-to-transformers](converting-lines-to-transformers.md)).
  Read as a voltage band, 0.51–1.5 is ±49 %. The regulated bus is always inside it and the tap
  never moves, yet the unit still reports as regulating.
- **Read the unsuffixed band.** `XFRegMin:1` / `XFRegMax:1` are the Time Step Simulation
  secondary regulation limits, not the power-flow band. On one case family the old 0.51/1.5
  values moved there when the power-flow band was set properly. A search for those numbers
  still finds them and suggests the wrong diagnosis.
- **`XFFixedTap` is not the live ratio.** It is the fixed component and can read `1.0` on every
  auto transformer, which looks like a fleet that has never moved. The live ratio is
  `Branch.LineTap`. It tracks `1 + XFTapPos × XFStep` exactly: `XFTapPos = -1` with
  `XFStep = 0.00625` reads `LineTap = 0.99375`.

### The rule that decides every tap question

A tap changes the turns ratio. It creates no reactive power. Raising the LV bus pulls the same
Mvar through the transformer from the HV side, so the HV bus goes down, and lowering the LV bus
pushes the HV bus up. **A tap moves a deficit or a surplus; it does not fill or absorb it.** It
fixes a violation only where the other side has headroom.

To find which side is the source, look at which side is higher in the solved case, not which
one has the higher nominal kV. A large load at 138 kV fed from a 69 kV network can sit below the
69 kV bus feeding it.

### Defect 1: the regulator points at nothing

An LTC's `XFRegBus`, or a switched shunt's `SSRegNum`, names a bus number. If that number is not
a bus in the case, or the bus reads `Bus.BusStatus = Disconnected`, the device has no valid
target. The case still solves, and the device either sits idle or does something PowerWorld
chose for it. Neither is what the modeller intended.

A switched shunt whose nominal range is zero (`SSMaxMVR = SSMinMVR = 0`) and whose regulated bus
is empty is usually a placeholder, not a defect.

**What `0` means.** Probed 2026-09-30 on two public synthetic cases (Hawaii40, Texas2k): writing
`XFRegBus = 0` on an LTC, or `SSRegNum = 0` on a regulating shunt, through SimAuto is **silently
refused** - the call succeeds and the previous bus number stays. A write to another existing bus
number does take. And a shunt that regulates its own terminal reads its own bus number: every
regulating shunt on both cases did (1 of 1 and 202 of 202). So `0` is never PowerWorld's spelling
of "own bus". A `0` read back on an active regulator came in with the case file, and it names no
target. `Shunt.AutoControl` read `YES` on every regulating shunt of both cases.

### Defect 2: `XFRegTargetType = Middle`

The field takes exactly two values. Measured on a live case:

| written | reads back |
|---|---|
| `Middle` | `Middle` |
| `Max`, `Maximum`, `High` | `Max/Min` |
| `Value`, `Specified`, `Target`, `Min` | coerced to `Middle` |

While the regulated bus is inside `[XFRegMin, XFRegMax]`, the LTC does nothing. When the bus
leaves the band:

- **`Middle`** drives it to the **midpoint** of the band.
- **`Max/Min`** drives it to the **nearest edge** and stops. A wide band becomes a one-sided
  limit: above `XFRegMax` the LTC taps down to `XFRegMax`, and anywhere inside the band it
  leaves the bus alone.

`XFRegTargetValue` is derived and read-only. Writing 1.04 to it read back 1.014, which was the
midpoint of the band in force at the time. That read-back is what confirmed the mechanism.

**Why a symmetric band cannot be tuned into working.** Measured 2026-09-14 on a regional
planning model: the same few tens of LTCs were retuned across five dispatches, four ways. Each
attempt was scored by the violations it *created*.

| attempt | band (pu) | target type | result |
|---|---|---|---|
| 1 | 1.030 – 1.045 | `Middle` | created many new violations |
| 2 | 1.035 – 1.048 | `Middle` | the 1.035 floor lifted healthy buses; one went from just under 1.03 to just over 1.05 |
| 3 | 0.98 – 1.048 | `Middle` | midpoint 1.014 overshot downward and dumped reactive power into neighbouring buses |
| 4 | **0.98 – 1.045** | **`Max/Min`** | one new violation; worked |

Attempts 2 and 3 fail in opposite directions for the same reason. A band low enough not to lift
a healthy bus has a midpoint well below the criterion. A band whose midpoint sits near the
criterion has a floor that lifts healthy buses. `Max/Min` removes the conflict: the floor can
stay at a harmless 0.98, and the LTC only ever acts downward.

Leave margin under the criterion. With a 1.05 criterion, 1.045 is safer than 1.050. A case
tuned to sit at exactly 1.050 in one dispatch violates in every other dispatch on the same base.

### Defect 3: the LTC holds its low-voltage side

If `XFRegBus` is the transformer's LV terminal, the LTC keeps a healthy 138 kV bus inside a
tight band while the HV bus it does not regulate drifts. The tap then works against the HV side.

The worst case measured (2026-09-14, regional planning model): an EHV bus at about **1.13 pu**,
past the 1.10 emergency limit. It had no generator, no shunt and no load, just two branches. The
transformer beside it held its LV bus just above the top of a narrow band (`XFRegError` a few
thousandths of a pu). Its tap was at `XFTapMax`, more than a dozen steps up, and the transformer
carried only a few MVA.
That LTC was the only device that could control the EHV bus, and it had spent its whole range
pushing that bus away. Re-pointing it to the EHV bus brought the bus to about **1.03**. A second
EHV bus hanging off the first by one line cleared with it.

**Standing check.** At any bus that violates with no local reactive source, list the
transformers touching it and read their `XFRegBus`. An LTC at `LineTap = XFTapMax` (or
`XFTapMin`) with a non-zero `XFRegError` is not failing to help. It is actively pushing.

Holding the LV side is right for a distribution tap feeding load and wrong for a bulk
transformer between two transmission voltages. The case alone cannot say which one was
intended, so this is a judgement call, not a defect.

**Which band the HV side is judged against.** `Bus.BusVoltLimLow` / `BusVoltLimHigh` are the
limits in force at that bus. Probed 2026-09-30 on both public cases: with no bus setting its own
limits (`BusVoltLim = NO` everywhere) they read the limit group's 0.9 / 1.1 on every bus, as
`0.89999998` / `1.10000002` - single precision, so compare with a tolerance. After writing
`BusVoltLim = YES` with 0.95 / 1.04 on one bus in memory, that bus read `0.94999999` /
`1.03999996`. Only where they read 0 or blank does a check need a band of its own.

### The fix: re-point the regulator, do not write the tap

Set `XFRegBus`, the band and the target type, and let the LTC find its own position. Do not
compute a tap yourself. Hand arithmetic brings its own direction trap:
`new_tap = old_tap × (v_measured / v_target)` is the natural guess, and it is backwards. The
correct form is `new_tap = old_tap × (v_target / v_measured)`, and whether the tap sits at the
`XFNominalKV` end or the `:1` end is worth re-measuring on each new case family.

```python
pw.edit_mode()
pw.esa.ChangeParametersSingleElement(
    "Branch", ["BusNum", "BusNum:1", "LineCircuit",
               "XFRegBus", "XFRegMin", "XFRegMax", "XFRegTargetType"],
    [str(f), str(t), "1", str(target_bus), "0.98000", "1.04500", "Max/Min"])
pw.run_mode()
pw.pflow()
# Read it back, target type included. esapp does not confirm the write for you.
```

`LineCircuit` is a string. `GetParametersSingleElement` needs one value slot per field, so pass a
trailing `""` for each field you are reading. esapp's bracket writer rejects `XF*` fields from a
wrong static whitelist; [converting-lines-to-transformers](converting-lines-to-transformers.md)
has the workaround.

Three exclusions, each measured:

1. **Never re-point a generator step-up (GSU).** Its HV bus is already regulated by its own
   machine through `Gen.GenRegNum`. Re-pointing the LTC puts two controllers on one target, and
   the machines there were already pinned at `GenMVRMin` with nothing left to give.
2. **Do not "repair" `XFTapMin = 1.00`.** A range that cannot go below nominal looks like a data
   defect. Widening it to 0.90 on two undervoltage units let each LTC hold its source bus by
   pulling down the load bus behind it, from about 0.94 to about 0.89, in every dispatch, including one that had
   been clean. Both sides were already low, so there was nothing to borrow. That floor was a
   guard.
3. **Never lower `XFTapMin`. Raise `XFTapMax` only where it sits below the unit's own tap
   position.** Widening ranges wholesale to 0.90–1.10 let one 345 kV bus swing 0.11 pu on travel
   it did not need.

### Judge a change by what it broke

A net violation count is the wrong acceptance test. List every bus that was in band before and is
out of band after. On the 2026-09-14 run, attempt 1 cut the total by about 40 % and still put
two new violations into the one dispatch that had been clean. Only the created-list caught it.

Voltage fixes move thermal loading too, in a direction that depends on the case. Size any
thermal fix against the flows after the voltage fix. On that run the worst branch in one
dispatch fell from about 106 % to 98 % before any rating changed.

## Worked result: re-pointing instead of buying devices

Measured 2026-09-14 on a regional planning model, five dispatches, intact case:

| | before → after |
|---|---|
| emergency overvoltage (> 1.10 pu) | a few → **0** |
| overvoltage (> 1.05 pu) | about four in five cleared; the rest within 0.006 pu of the limit |
| undervoltage (< 0.94 pu) | unchanged. A tap cannot reach it: both sides were low |
| thermal (> 100 %) | all cleared, with free rating corrections on installed equipment |
| devices added | **0** |

Every action was a settings change on equipment already in the case: a few tens of LTCs
re-pointed to their HV bus, band 0.98–1.045, `XFRegTargetType = Max/Min`, GSUs left alone.
Every check was run again on the cases reopened from disk, not in the session that wrote them.

## How the case-auditor checks this

The `case-audit` engine (`skills/case-audit/engine/rules_reg.py`) runs these checks read-only on
every audit. An **active LTC** is a closed branch with `LineXfmr = YES`, `LineXFType = LTC` and
`XFAuto = YES` whose terminals are not three-winding star buses (`Bus.BusIsStarBus = YES`).

| rule | fires when | needs a solve |
|---|---|---|
| `base.regulates_nothing` | a closed regulating shunt (`SSCMode` Discrete, Continuous or SVC, `AutoControl = YES`) or an active LTC names a regulated bus that is `0`, not in the case, or `Disconnected`. A 0 Mvar shunt with no target is reported separately as probably a placeholder | no |
| `base.ltc_middle_target` | active LTCs on `Middle` whose band is narrow enough to act; one finding for all of them, with the most common band | no |
| `base.ltc_regulates_lv_side` | an active LTC holds its LV terminal (or a remote bus at LV level) while its HV terminal is outside that bus's limits; generator step-ups are skipped and counted | yes |

Numbers with no source, each a proposed default in `skills/case-audit/engine/thresholds.py`:

| number | used for |
|---|---|
| band ≤ 0.2 pu | a band that can act (the sourced facts: 0.02–0.065 pu bands act, a 0.99 pu band never does) |
| 1 % | two terminals whose nominal kV agree this closely have no LV side |
| 1e-4 pu | the tolerance on a bus's limits |
| 0.94 / 1.05 pu | the band used only where a bus's limits read 0 or blank - the study criterion of the measured runs above, not a PowerWorld default |
| a unit on the LV bus (any status), no closed load there, and only transformers at that bus | how a generator step-up is recognised; units skipped this way are counted |

**Not checked in this version:** three-winding transformers. They carry their own regulation
fields on `3WXFormer`, and neither public case has one (0 rows on both), so how their legs appear
in `Branch` is untested. Also not checked: a band copied from the tap range
(`XFRegMin = XFTapMin`, `XFRegMax = XFTapMax`), described above; it has no rule yet.

Neither public case has an active LTC - every transformer on both reads `Fixed`, `XFAuto = NO`,
`XFRegTargetType = Middle` - so the LTC rules are tested on hand-built cases, not on a live one.


---

# ==== new-device-contingency-aux.md ====

---
type: method
domain: tooling
aliases: [contingency-aux, ctgautoinsert, bgreportlimits, monitored-areas, ctgelement-subdata, new-device-contingency]
tags: [esapp, powerworld, simauto, contingency, aux, n-1, limit-monitoring, areas, synth2k]
---

# Building a Contingency Set for Chosen Devices, and an AUX That Carries It

## Abstract

How to turn **a list of devices** (e.g. the branches and generators that are new in a
planning case) into a PowerWorld contingency set, restrict violation reporting to **the
areas you care about**, and ship both as one `.aux` file that loads into the case — without
ever saving the case. The mechanism is **autoinsert-then-restrict**: run the case's own
`CTGAutoInsert`, match your devices to the labels it produced, and write only those out.
Hand-writing `Contingency` records from scratch invents labels PowerWorld would not use.

Five things here are silent failures, all live-measured on
`Synth2k_case` on 2026-08-17 — each produces a plausible wrong
answer, not an error:

> **`ElementType`, `DeleteExisting` and `Handle3WXF` are *concise* names.** PowerWorld's
> object-field export lists two names per field, and these three appear only in the Concise
> Variable Name column. Grep the export for them and you find nothing, which reads as "the
> field does not exist". Their full variable names are `CtgAutoInsElementType`,
> `CtgAutoInsDeleteExistCtgs` and `Include3WXfifFoundWithXf`. Both spellings are accepted;
> search the export on either column before concluding a field is missing.

1. **`CTG_AutoInsert_Options` rejects `ElementType=GEN` without complaining** and leaves it
   at `BRANCH`. You ask for 743 generator outages and get 3,911 branch ones.
2. **The `CTGElement` SUBDATA action string must be quoted.** Unquoted, PowerWorld parses
   the *first* contingency and drops the other 690 with no error.
3. **`LoadAux` needs an ABSOLUTE path** — a relative one resolves against `pwrworld.exe`'s
   working directory, not yours.
4. **`LoadAux` merges, it does not replace.** Loading a 220-contingency list into a case
   that already has a set gives you both.
5. **`Ctg_Options.CTG_ReportMonitoredAreas` is a decoy** — it only affects text-file report
   writing. The real area switch is `Area.BGReportLimits`.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esapp package
- **Input from:** identify differences — produces the device list this method turns into a contingency set
- **Across:** [reading-violationctg](reading-violationctg.md) (what you read back after solving this set) ·
  [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the limit *thresholds*; this page is the limit *scope*) ·
  [save-powerworld-case](save-powerworld-case.md) · [adding-devices-esapp](adding-devices-esapp.md) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md)
- **Deeper:** aux script catalog for the full SCRIPT action list; the working
  implementation is `Power_System/regional-contingency/main.py`, which consumes the
  `new_devices_for_contingencies*.xlsx` produced by `identify_differences`.

## Content

### Step 1 — build the full N-1 set in memory, then keep only what you want

```python
pw.esa.RunScriptCommand("EnterMode(EDIT);")
pw.esa.RunScriptCommand("Delete(Contingency);")
pw.esa.RunScriptCommand(
    "SetData(CTG_AutoInsert_Options, "
    "[ElementType, DeleteExisting, Handle3WXF], [BRANCH, YES, INSERT3WXF]);")
pw.esa.RunScriptCommand("CTGAutoInsert;")
pw.esa.RunScriptCommand("EnterMode(RUN);")
```

`ElementType` is `BRANCH` or **`GENERATOR`** — **never `GEN`**. `GEN` is accepted by the
parser, silently ignored, and leaves the previous value in place:

```python
pw.esa.RunScriptCommand("SetData(CTG_AutoInsert_Options,[ElementType],[GEN]);")
pw.esa.GetParametersSingleElement("CTG_AutoInsert_Options", ["ElementType"], [""])
# -> 'BRANCH'          <- the write did not happen, and nothing said so
# 'GENERATOR' and 'Gen' both -> 'GENERATOR'
```

**Always read the option back and assert it** before `CTGAutoInsert`. `Handle3WXF` applies
to branches only. On case 3 this yields **3,911 branch** contingencies (= its branch count)
and **743 generator** ones (= its generator count).

### Step 2 — match your devices to the labels autoinsert chose

Read `ContingencyElement` with an explicit field list
(`CTGLabel, BusNum, BusNum:1, ElementID, Object, Action`):

| device | `Object` | `BusNum` / `BusNum:1` | `ElementID` | example `CTGLabel` |
|---|---|---|---|---|
| branch | `BRANCH 1001 1064 1` | both ends | **the circuit ID** | `L_001001ODESSA20-001064ODESSA30C1` |
| 3W xfmr | `BRANCH …` | both ends | circuit | `T_…` prefix |
| generator | `GEN 1004 1` | bus / **`0`** | **the `GenID`** | `G_001004ODONNELL11U1` |

Two matching rules that are easy to get wrong, both inherited from [reading-violationctg](reading-violationctg.md):

- **`ContingencyElement` has no `LineCircuit`.** The circuit ID is `ElementID` (verified on
  a 3-circuit bank: `'1'`, `'10'`, `'20'`). For generators `ElementID` is the `GenID`.
- **Match the bus pair UNORDERED and never parse the `CTGLabel`.** A case may store a branch
  either way round, and the label embeds *truncated* substation names, which collide.

### Step 3 — write the AUX, in PowerWorld's own shape

Get the ground truth from PowerWorld rather than guessing — it will export the set it is
holding:

```python
# Write ONLY through RunScriptCommand -- the COM SaveCase method silently no-ops,
# see methods/save-powerworld-case.md. This applies to every PowerWorld file write, not
# cases: SaveData through RunScriptCommand produced a real 523 KB file here.
# NOTE: SaveContingencies is NOT a script command ("Unknown script command").
# The filter argument is a bare string; the sort lists MUST be bracketed.
pw.esa.RunScriptCommand(
    f'SaveData("{abs_path}",AUX,Contingency,[CTGLabel,CTGSkip],[CTGElement],"",[],[],YES);')
```

which writes (3,911 contingencies → 523 KB):

```
Contingency (Name,Skip)
{
"L_001001ODESSA20-001064ODESSA30C1" "NO "
   <SUBDATA CTGElement>
     "BRANCH 1001 1064 1 OPEN" "" CHECK 0 NO
   </SUBDATA>
}
```

Copy that shape when writing a **subset** by hand in Python. `Contingency (CTGLabel,CTGSkip)`
works as the header too. **The action string must be quoted**: written as bare
`BRANCH 1001 1064 1 OPEN`, a 691-contingency file loads as **one** contingency and the load
reports success.

### Step 4 — scope the violations to your areas, in the same file

`Area.BGReportLimits` — *"Set to NO to not monitor elements (buses, branches or
interfaces)"* — is PowerWorld's own limit-monitoring switch (the `Zone` object carries it
too). Write every area, not just yours, or you inherit whatever the case already restricted:

```
Area (AreaNum,BGReportLimits)
{
"1" "NO"
"5" "YES"
}
```

Measured on case 3 (8 areas, 2,000 buses, 3,911 branches), reading the **effective** flags
`Bus.BusMonEle:1` / `Branch.LineMonEle:1` — not the requested ones:

| monitored areas | buses monitored | branches monitored |
|---|---|---|
| all 8, as shipped | 2000 | 3878 |
| `5` (North Central) | 483 = area 5 exactly | 866 = its own 822 **+ 44 ties** |
| `3, 5` | 630 | 1341 |

**A bus is monitored when its area is; a branch when EITHER end is** — so tie lines into the
region are included automatically, which is the opposite of the `ViolationCTG.AreaNum` trap
in [reading-violationctg](reading-violationctg.md), where a naive filter *drops* them. Related knobs found in the
same field-list dig: `Area.BGReportLimMinKV` / `BGReportLimMaxKV` (monitor only a kV band)
and `Branch.LineMonEle` / `Bus.BusMonEle` (switch off one device).

### Verify it worked

Load the file back into the open case and assert — never trust the write:

```python
pw.esa.RunScriptCommand("EnterMode(EDIT);")
pw.esa.RunScriptCommand("Delete(Contingency);")     # LoadAux MERGES; delete to replace
pw.esa.RunScriptCommand(f'LoadAux("{absolute_path}", NO);')
pw.esa.RunScriptCommand("EnterMode(RUN);")
```

Assert **three** things, because each failure looks like success:

1. the loaded `CTGLabel` set equals what you wrote — a parse failure loads a prefix;
2. the `ContingencyElement` **count** equals what you wrote — a contingency with no element
   loads fine and outages nothing, which reads as "the grid survives everything";
3. every area's `BGReportLimits` came back as intended.

### Gotchas beyond the five in the Abstract

- **A device that gets no contingency is normal, not a bug.** Autoinsert requires both ends
  ≥ 69 kV **and** `LineStatus == 'Closed'`, and `Handle3WXF=INSERT3WXF` collapses a
  3-winding transformer's three branch rows into **one** contingency — so three device rows
  legitimately map to one label. Report the bucket with a per-device reason; do not abort.
- **The dominant unmatched cause on a real planning model is the 3-winding transformer's
  star bus, and it presents as a kV failure, not as a 3WXF one.** A 3W transformer is
  modelled as three branches meeting at a **fictitious star/tertiary bus carried at ~1 kV
  nominal**, so the winding branches touching it fail the 69 kV floor and autoinsert never
  builds a branch contingency for them. (measured 2026-08-17, on regional planning cases: 111
  of 273 new branches.) Do not read that bucket as missing coverage — the transformer
  itself is covered by the single collapsed `T_…` contingency; what is absent is a separate
  outage of an internal winding, which is not a real N-1 event.
- **`GetFieldList` on an object name that does not exist can fault `pwrworld.exe`** with an
  access violation rather than returning an error. Do not fuzz object names.
- Autoinsert labels are **not** unique-safe to parse: `L_`/`T_`/`G_` + truncated substation
  names. Treat them as opaque keys.


---

# ==== powerworld-limitset-setdata.md ====

---
type: method
domain: tooling
aliases: [limitset, ctg-voltage-band, setdata-key-fields, limit-monitoring]
tags: [esapp, powerworld, simauto, setdata, limitset, contingency, key-fields]
---

# Changing PowerWorld Limit Monitoring (LimitSet) via SetData

## Abstract

How to change PowerWorld's own limit-monitoring thresholds (`LimitSet` object — normal-ops
`LSPULow`/`LSPUHigh` and N-1 contingency `LSCtgPULow`/`LSCtgPUHigh`) from a script command or from
esapp. The headline gotcha: **`SetData` on `LimitSet` errors "some of the key fields is missing"
unless you supply the ENTIRE field row**, not just the key field(s) plus the fields you want to
change — unlike most other PowerWorld objects, where key + changed fields is enough. Live-verified
by round-tripping the same case's `LimitSet` values through a CSV export/reimport and a
`SetData` script command.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esapp package
- **Across:** [save-powerworld-case](save-powerworld-case.md) · [adding-devices-esapp](adding-devices-esapp.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · reactive power planning
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The gotcha

A short `SetData` call naming only the key field and the fields you want to change —

```
SetData(LimitSet, [LSNum, LSPULow, LSPUHigh, LSCtgPULow, LSCtgPUHigh], [1, 0.920, 1.080, 0.880, 1.120]);
```

— fails with **"some of the key fields is missing"**, even though `LSNum` (the object's key field)
*is* in the list. `LimitSet` (unlike `Bus`/`Gen`/`Shunt`) apparently needs its full row supplied to
resolve unambiguously. The only proven-working shape is to supply **every field PowerWorld exports
for the object**, changed values included, unchanged values copied through verbatim:

```
SetData(LimitSet, [LSNum,LSName,LSPULow,LSPUHigh,LSLinePercent,LSInterfacePercent,
   LSInterfacePercent:1,LSLineRateSet,LSLineRateSet:1,LSInterfaceRateSet,
   LSInterfaceRateSet:1,LSDisabled,LSAmpMVA,Selected,CTG_WhatToDoWithBC:1,
   CTG_WhatToDoWithBC:2,CTG_WhatToDoWithBC:3,CTG_BCFlows:1,CTG_BCFlows:2,
   CTG_BCLowVolt:1,CTG_BCLowVolt:2,CTG_BCHighVolt:1,CTG_BCHighVolt:2,
   CTG_BCInterface:1,CTG_BCInterface:2,LSEndMonitor,LSLowVSuspectCutoff,
   LSUseLimitCost,LSBusLowRateSet,LSBusHighRateSet,LSCtgBusLowRateSet,
   LSCtgBusHighRateSet,LSCtgPULow,LSCtgPUHigh,CTG_BCDiscBusReporting,
   LSGroupSpecificAdvancedLimMon,DataMaintainer,DataMaintainerAssign,
   ScreenPercent,ScreenPercent:1,ScreenPercent:3,ScreenTol,ScreenTol:1,
   ScreenTol:2,LSBusPairPercent,LSBusPairRateSet,LSBusPairRateSet:1,ScreenMult],
   [1,"Default",0.920,1.080,100.000,100.000,100.000,"A","A","A","A","NO ","MVA",
   "NO ","NO ","NO ","NO ",0.000,999.000,0.000,2.000,0.000,2.000,0.000,999.000,
   "Higher",0.000,"No","A","A","A","A",0.880,1.120,"NO ","NO ","","",90.000,
   90.000,90.000,0.010,0.010,0.010,100.000,"A","A",1.000]);
```

This round-tripped clean on Synth2k (verified: reopened the LimitSet case info display, the 4
changed fields read back exactly as set, nothing else on the row moved).

#### A rate-set field can read back as its DISPLAY string, not the bare letter

Asserting the read-back is right, but comparing rate-set fields as **raw strings** is not.
`LSLineRateSet` is a choice list, and PowerWorld may return the letter **plus that rate
set's name on the case**:

```
wrote 'A'  ->  read back 'A: RATE1'
```

Measured on a regional planning case (2026-08-17). **Synth2k returns the bare `'A'`**, so this
never appears there — it shows up only on a case whose rate sets are *named*, which a real
planning model's are.

The write took. A raw comparison nonetheless fails it, and the natural error message
("the limits did not take — every violation would be measured against the wrong limit") is
then the exact opposite of the truth, on a run that is fine. **Compare the letter before the
colon**, so a genuine mismatch (`A` wanted, `B` stored) is still caught:

```python
def rate_set_letter(value) -> str:
    return str(value).strip().split(":")[0].strip().upper()
```

Related, and load-bearing if you subtract a base case from post-contingency results:
`LSLineRateSet` and `LSLineRateSet:1` are the **normal** and **contingency** rate sets. Write
both to the same value and a pre-contingency `Branch.LinePercent` is directly comparable to a
post-contingency `ViolationCTG.LimViolPct`; leave them different and the two percentages
divide by different ratings, silently.

### Field semantics

| Field | Meaning |
|---|---|
| `LSNum` / `LSName` | key fields — `1` / `"Default"` is the case's default (usually only) LimitSet |
| `LSPULow` / `LSPUHigh` | **normal-operations** voltage band (pu) |
| `LSCtgPULow` / `LSCtgPUHigh` | **N-1 contingency** voltage band (pu) — this is the threshold PowerWorld's own CTG/limit-monitoring flags violations against, distinct from any Python-side `v_min`/`v_max` check a pipeline does after reading `BusMin/MaxVoltageContingency` |

### Two ways to apply it

**1. Manual, in the PowerWorld script command bar** — paste the single-line `SetData(...)` block
above (values edited to taste). Useful for a one-off manual test/round-trip check.

**2. From Python (esapp)** — do NOT hand-write the full-field `SetData` call in code; read the
current full row, patch only the target columns, write the full row back. `pw.esa.SetData(...)` and
`pw.esa.ChangeParametersMultipleElement(...)` are both thin passthroughs to the raw SimAuto call (no
key-field auto-resolution, no partial-write convenience) — so the same "supply everything" rule
applies programmatically. Pattern:

```python
LIMITSET_FIELDS = ["LSNum", "LSName", "LSPULow", "LSPUHigh", ...]   # all ~48 fields, PowerWorld's own export order

def set_ctg_voltage_limits(pw, v_min=0.90, v_max=1.10):
    ls = pw.esa.GetParametersMultipleElement("LimitSet", LIMITSET_FIELDS)
    ls["LSCtgPULow"] = v_min
    ls["LSCtgPUHigh"] = v_max
    pw.esa.RunScriptCommand("EnterMode(EDIT);")
    pw.esa.ChangeParametersMultipleElement("LimitSet", LIMITSET_FIELDS, ls[LIMITSET_FIELDS].values.tolist())
    pw.esa.RunScriptCommand("EnterMode(RUN);")
```

This generalizes to any case (reads whatever LimitSet rows actually exist, rather than hardcoding
one case's original values) and touches only the 2 target columns while carrying every other field
through unchanged — the read-modify-write shape sidesteps hand-transcribing values entirely.

### Why this matters for N-1 work

A reactive planning pipeline checked contingency voltage violations in Python
(`Bus.BusMin/MaxVoltageContingency` against a hardcoded `[0.90, 1.10]` band). That
Python-side check was never actually tied
to PowerWorld's own `LimitSet.LSCtgPULow/LSCtgPUHigh` — the case's native limit monitoring could
silently disagree with the band the Python code assumes. Setting the contingency limits
explicitly closes that gap:
call it once after opening/building a case to force the case's own contingency band to match the
band the rest of the pipeline checks against.

> House rules honored: full-row read-modify-write via `esapp` (not a hand-maintained partial
> `SetData` literal in code); values verified by reading them back, mirroring the assert-after-save
> discipline in [save-powerworld-case](save-powerworld-case.md).


---

# ==== preflight-powerworld.md ====

---
type: method
domain: tooling
aliases: [preflight, preflight-powerworld, powerworld-check, simauto-check, license-check]
tags: [powerworld, simauto, esapp, setup, troubleshooting, preflight]
---

# Method: Preflight — is PowerWorld actually usable here?

## Abstract

Run this before writing any analysis code. It takes about five seconds and answers the
only question that matters at the start of a session: can this machine drive PowerWorld
from Python at all? Five checks, each with the exact error you get when it fails and
what that error actually means. Skipping this is why an agent writes two hundred lines
of a study and then discovers on the last line that SimAuto was never licensed.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp-overview](esapp-overview.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [esapp](../concepts/esapp.md)
- **Next:** [esapp-overview](esapp-overview.md) once every check passes

## Content

> **Agents: run this first.** Do not write analysis code before the preflight passes.
> A failure here is not a bug in your code — it is a fact about the machine, and no
> amount of rewriting the analysis will fix it. Report which check failed and stop.

### The preflight script

Paste this and run it. It prints a line per check and stops at the first failure.

Checks 1-4 are about the **machine** and need no case file; check 5 opens **your case**.
Call `preflight_machine()` on its own when you do not have a case yet — during setup, say —
and `preflight(case_path)` when you do.

```python
"""PowerWorld preflight. Run before writing any analysis code."""

import sys
from pathlib import Path

CASE = r"C:\path\to\your_case.pwb"   # <- change this


def preflight_machine() -> bool:
    """Checks 1-4: can this machine drive PowerWorld? No case file needed."""
    # 1. Platform. SimAuto is a Windows COM server; there is no Linux or macOS path.
    if not sys.platform.startswith("win"):
        print(f"FAIL 1/5  platform is {sys.platform!r}, SimAuto requires Windows")
        return False
    print("ok   1/5  platform is Windows")

    # 2. pywin32, the COM bridge esapp calls through.
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        print("FAIL 2/5  pywin32 missing -> pip install pywin32")
        return False
    print("ok   2/5  pywin32 importable")

    # 3. esapp itself.
    try:
        from esapp import PowerWorld  # noqa: F401
    except ImportError:
        print("FAIL 3/5  esapp missing -> pip install esapp")
        return False
    print("ok   3/5  esapp importable")

    # 4. The SimAuto COM server. This is where an unlicensed add-on shows up.
    #    Also record the build date, so the version is on file before any analysis.
    try:
        import win32com.client
        from datetime import date, timedelta

        sa = win32com.client.Dispatch("pwrworld.SimulatorAuto")
        try:
            # RequestBuildDate is a Delphi serial date: days since 1899-12-30
            build = date(1899, 12, 30) + timedelta(days=int(sa.RequestBuildDate))
            version = f", build {build.isoformat()}"
        except Exception:  # noqa: BLE001 - version is useful, not required
            version = ", build unknown"
    except Exception as exc:  # noqa: BLE001 - the message is the diagnosis
        print(f"FAIL 4/5  cannot start SimAuto: {exc}")
        print("          see the failure table: this is usually 'not installed'")
        print("          or 'installed but the SimAuto add-on is not licensed'")
        return False
    print(f"ok   4/5  SimAuto COM server responds{version}")
    return True


def preflight_case(case_path: str) -> bool:
    """Check 5: this particular case opens. Run preflight_machine() first."""
    # 5. The case itself opens and solves.
    if not Path(case_path).is_file():
        print(f"FAIL 5/5  case not found: {case_path}")
        return False
    try:
        from esapp import PowerWorld

        pw = PowerWorld(case_path)
        info = pw.summary()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL 5/5  case will not open: {exc}")
        return False
    print(f"ok   5/5  case opens: {info['n_bus']} buses, {info['n_gen']} generators")
    return True


def preflight(case_path: str) -> bool:
    """All five checks, stopping at the first failure."""
    return preflight_machine() and preflight_case(case_path)


if __name__ == "__main__":
    ok = preflight(CASE)
    print("\nPREFLIGHT PASSED" if ok else "\nPREFLIGHT FAILED - fix the above before continuing")
    raise SystemExit(0 if ok else 1)
```

### What each failure actually means

| Error you see | What is wrong | Fix |
|---|---|---|
| `platform is 'linux'` / `'darwin'` | SimAuto is a Windows COM server. There is no port | Use Windows. The weather half of this kit still works — see [teamoverbyeweather-client](teamoverbyeweather-client.md) |
| `ModuleNotFoundError: No module named 'win32com'` | pywin32 is not installed | `pip install pywin32` |
| `ModuleNotFoundError: No module named 'esapp'` | esapp is not installed, or you are in the wrong interpreter | `pip install esapp`, and check `sys.executable` is the interpreter you think it is |
| `com_error: (-2147221005, 'Invalid class string', ...)` | SimAuto is not registered. Usually PowerWorld Simulator is not installed at all | Install Simulator. If it *is* installed, run it once as administrator so it registers its COM server |
| `com_error: (-2147221164, 'Class not registered', ...)` | Same as above, or a 32/64-bit mismatch between Python and Simulator | Match the bitness. A 32-bit Simulator will not serve a 64-bit Python |
| A COM error mentioning **licence**, **not authorized**, or **add-on** | Simulator is installed and licensed, but the **SimAuto add-on is a separate licence** and yours does not include it | This cannot be fixed in code. Talk to whoever administers your PowerWorld licence |
| SimAuto starts but a feature errors | Possibly a version difference | Check the build date against [version-requirements](../concepts/version-requirements.md) before assuming a page is wrong |
| `PowerWorldPrerequisiteError` | **Not** a version or licence problem — the case lacks a prerequisite state | e.g. clearing TimeStep results that do not exist yet. Do the prerequisite step first |
| `case not found` | Path typo, or a relative path resolving somewhere unexpected | Use an absolute path. Always |
| Case opens but `n_bus` is 0 | The file opened but is not a valid case | Confirm the `.pwb` is not corrupt; try opening it in Simulator directly |

### The licence check, specifically

This is the check people forget, so it gets its own note.

**PowerWorld Simulator and the SimAuto add-on are licensed separately.** A machine can
have a fully valid, fully working Simulator installation and still be unable to run a
single line of this kit, because automation is a different SKU. Simulator's own GUI will
give you no hint of this — it works fine.

The symptom is that check 4 fails while Simulator itself launches normally. If you can
open your case by double-clicking it but `Dispatch("pwrworld.SimulatorAuto")` raises,
that is the licence, not your code.

### Record the version before you analyse anything

Check 4 prints the Simulator build date. Put it in your report. Field availability and
script-action behaviour both shift between releases, and they shift silently, so when a
result later looks wrong the build date is the first thing worth checking.

`RequestBuildDate` is a Delphi serial date (days since 1899-12-30), not a version number.
For the full version string and what this kit was verified against, see
[version-requirements](../concepts/version-requirements.md).

### Quick version

If you only want the one-line answer:

```python
import win32com.client
win32com.client.Dispatch("pwrworld.SimulatorAuto")   # raises if PowerWorld automation is unavailable
```

If that line runs without raising, everything downstream in this kit is available to
you. If it raises, nothing is, and no rewrite of the analysis will change that.

### What preflight does not tell you

It confirms you can *drive* PowerWorld. It says nothing about whether the case is
suitable for the study you have in mind — whether it solves, whether it has the
generators or weather models you need, whether its limits are configured. Those are
questions for the analysis itself, starting at [esapp-overview](esapp-overview.md).


---

# ==== ranking-new-devices-by-severity.md ====

---
type: method
domain: tooling
aliases: [rank-new-devices, contingency-severity-ranking, base-case-subtraction,
  configuring-a-rank-run, min-kv, only-new, transmission-only-violations,
  worsening-tolerance, three-way-ranking, relative-severity, fraction-beyond-limit, devices-csv, ranking-new-devices-by-severity]
tags: [esapp, powerworld, simauto, contingency, n-1, ranking, severity, violations, planning-model, synth2k]
---

# Ranking New Devices by the Severity of the Violations Their Outage Causes

## Abstract

Given a contingency AUX built by [new-device-contingency-aux](new-device-contingency-aux.md) — one N-1 contingency per
device that is new in a planning case — solve it and answer **which new device is worst**.

**One file comes out: `devices.csv`, one row per new device, ranked worst first.** It is
the only file at the top of the output directory; the per-metric sorts and the
per-violation-row evidence live one level down in `_audit/`. The question it answers is the
one that gets asked out loud — *without device X, what does this case experience?* — so a
device that was never tested must still have a row, or "absent" and "harmless" become the
same thing.

**The single ordering rests on one idea: the FRACTION BEYOND THE LIMIT.** Percent-of-rating
and per-unit volts genuinely do not share a unit — but each quantity *divided by the limit
it actually violated* is dimensionless, and those are comparable without inventing an
exchange rate. That is what makes a 0.80 pu bus (0.158 beyond a 0.95 floor) outrank a 101%
branch (0.010 beyond its rating), which no per-metric sort does. It still asserts that a 5%
overload and a 5% voltage excursion are comparably bad — but that claim is visible and
checkable, which "percent vs per-unit" never was. The per-metric sorts in `_audit/` keep
the two apart on their own units; this is the one sanctioned crossing.

Six things here decide whether the ranking means anything, and each fails silently:

1. **Subtract the base case — AND attribute the magnitude.** A branch already at 105%
   appears under *every* contingency, so without subtraction every device inherits the same
   overloads (**38% of all rows** on one measured run, 464,794 of 1,218,162). But the
   subtraction only decides *whether* a row counts: a branch at 220% nudged to 221% survives
   it legitimately and then reports **221%** for a device that caused **+1%**. Score
   `min(exceedance, addition)` — see *Attribution* below. Measured at a 60% threshold:
   **97.8% of caused thermal rows are on an already-violating branch, the reported
   exceedance is a median 82.6x what the device added, and 883 of 890 devices move.**
2. **Rank voltage on distance OUTSIDE the band, never on `LimViolPct`.** Low and high volts
   have opposite polarity; one percent key orders one of them backwards.
3. **A device with no violation of a category gets `NaN`, not `0`.** Zero is a real severity
   and sorts above a device that was never measured.
4. **A diverged, missing, or islanding contingency is not a safe device.** Each produces no
   violation rows and is indistinguishable from "caused nothing" unless handled explicitly.
   A diverged device scores `NaN` and ranks **first**: an unknown outranks any measured
   damage, and burying it below hundreds of harmless devices is how an incomplete run reads
   as complete.
5. **Report the bus AS IT SITS, not only its excursion.** `0.037 pu outside the band` and
   `0.913 pu` are the same bus, and only one of them reads as serious. The excursion is
   measured against whichever band the run was configured with, so a reader who forgets the
   band reads a severe bus as trivial. Carry both — the score is built from the excursion
   and must stay auditable.
6. **A device's own area is not the reporting scope.** They routinely differ, and the file
   gives no hint that they do. See *The area trap* below.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esapp package
- **Input from:** [new-device-contingency-aux](new-device-contingency-aux.md) — builds the AUX this solves;
  identify differences — decides which devices are new
- **Across:** [reading-violationctg](reading-violationctg.md) (the read this ranks, and its traps) ·
  [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the thresholds it ranks against) ·
  [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (solving the set across processes) ·
  [lodf](../concepts/lodf.md) (the unbuilt fix for the islanding gap) · critical branch screening ·
  percentile auc scoring (a different severity-scoring approach, for comparison)
- **Deeper:** the implementation is `Power_System/regional-contingency` —
  `rank_main.py` (batch driver), `regional_contingency/rank.py`, `baseline.py`,
  `ranking.py`, `parallel.py`.

## Content

### Attribution: what the outage is actually responsible for

Subtracting the base case is only half the job, and the missing half is invisible: the row
set is corrected while the *magnitudes* are not. Score each row as the smaller of

    exceedance   how far past the limit the element ended up
    addition     how far the outage moved it

| branch | base | post | limit | exceedance | addition | score |
|---|---|---|---|---|---|---|
| A | 220% | 221% | 100% | 121 | 1 | **1** |
| B | 80% | 150% | 100% | 50 | 70 | **50** |
| C | 105% | 150% | 100% | 50 | 45 | **45** |

You can blame a device for neither more damage than exists, nor more than it put there. The
`min` self-corrects when the base was *below* the limit as well: a branch at 88% taken to
157% has addition 69 but exceedance 57, and only 57 points of it are a violation at all.
A row with no base value was clean, so the whole exceedance is the device's — missing base
data must never silently zero a real violation.

| category | exceedance | addition |
|---|---|---|
| `thermal` | `(pct - T)/T` | `(pct - base_pct)/T` |
| `voltage_low` | `(limit - V)/limit` | `(base_V - V)/limit` |
| `voltage_high` | `(V - limit)/limit` | `(V - base_V)/limit` |

`T` is the run's thermal threshold, so thermal normalizes exactly as voltage does. **Read
the base value with the SAME key the subtraction uses** — unordered bus pair plus
normalized circuit — or a row is filtered against one baseline and scored against another,
which is worse than either alone.

**`LimViolLimit` on a thermal row is the branch's MVA RATING, not 100.** Measured 21, 46,
57, 4352. Thermal must score off `LimViolPct` and voltage off `LimViolLimit`; borrowing the
other's field yields percent-minus-MVA, which is a plausible-looking number.

**Average as well as worst, on the attributed quantity.** The mean over a device's rows
separates one catastrophic element from twenty mildly-over ones — which the count only
half-answers. Computed on absolute percent it would re-inherit the whole base-case
contamination. Measured: the top devices score ~1.16 on their worst element and average
~0.010 across ~190 rows.

### The output table: natural units only

**A number the reader cannot interpret is not a result.** The score below is correct,
dimensionless, and unreadable to someone opening a spreadsheet — and requiring them to
learn the scoring scheme before they can read the answer is the wrong trade for a file
whose whole purpose is to be opened by other people. So the file carries **only** percent
of rating, per unit, and counts; the arithmetic that produced the ordering moves to a
sidecar. The rank stays auditable, it is just not in the way.

| column | unit |
|---|---|
| `rank` | 1..N, dense, worst first |
| `device` `device_type` `from_bus` `to_bus` `kv` `area` | identity and location |
| `ranked_by` | words: `overload` / `low voltage` / `high voltage` / `no violation` / `did not solve` |
| `worst_overload_pct` `avg_overload_pct` | percent of the branch's own rating |
| `worst_voltage_pu` `avg_voltage_pu` `worst_voltage_pct` | per unit, plus PowerWorld's own percent |
| `n_overloads` `n_voltage_violations` `n_violations` | counts |
| `converged` `count_verified` | integrity flags |

**`count_verified` means "no row was dropped between the solve and this table", and it
covers TWO ways rows go missing, not one.** It was originally keyed only off the row-count
mismatch guard, which let a run discard **2,972 unclassified violation rows on one planning model and
still write `count_verified = True` on all 297 devices** — the audit trail was correct and
the file people open was not. An unclassified row now taints its device exactly as a count
mismatch does. The general rule: a
bucket that means *"rows were dropped"* must reach the summary artifact, because `_audit/`
is not what gets mailed.

**Worst and average answer different questions**, and the count answers neither. A device
whose worst overload is 157% and whose average is also 157% overloads exactly one branch;
one with a high worst and a low average has a single hot spot among many marginal
violations. Averages must be taken in the SAME natural unit as the worst — an average of
the dimensionless score reads as noise (`0.064`), and an average of two different units at
once is meaningless even though it is well-defined.

**`worst_*` means most attributable, not highest number.** The reported rows are the ones
that drove the rank. Once the base case is attributed those need not be the arithmetic
maximum — a 221%-on-a-220%-branch loses to a 150%-from-clean one — and printing the
maximum beside a rank derived from a different row is how the two disagree in public.

**What was deliberately taken OFF the file**, and the cost: `severity_score`,
`severity_from`, `avg_severity`, the band excursion, and the per-device *how much did this
device add* figures. All are still computed and written to a sidecar. The accepted cost is
that on a case whose base already carries big overloads, a `221%` row reads as a 221%
device with nothing on the page to say the device only added 1%. That is a real loss; it
was traded for a table anyone can read.

### The one ordering: fraction beyond the limit

`rank` is dense `1..N` — no ties, no gaps — and orders **diverged first**, then
`severity_score` descending, then `CTGLabel` ascending so two runs of the same case agree.

`severity_score` is each violation's fraction beyond the limit it actually violated:

| category | score | example |
|---|---|---|
| `thermal` | `pct/100 - 1` | 157% loading -> `0.571` |
| `voltage_low` | `(limit - V)/limit` | 0.80 pu vs a 0.95 floor -> `0.158` |
| `voltage_high` | `(V - limit)/limit` | 1.10 pu vs a 1.05 ceiling -> `0.048` |

The units cancel, so this is a real dimensionless quantity rather than a fudge factor. **Do
not collapse it to `abs(pct/100 - 1)`** — it is arithmetically identical on all three
categories today, but it gets `voltage_low` right for the wrong reason and would keep
"working" silently if a polarity were ever redefined.

A device that solved and broke nothing scores a measured `0.0` and ranks last; a diverged
one scores `NaN` and ranks first. **There is deliberately no `status` column**: `converged
== False` *is* the diverged set and `n_violations == 0` *is* the silent set, so both facts
stay filterable data rather than a string to parse, and `ranked_by` says which in words.

Derive those labels from the COUNTS, never from the score. A silent device carries a real
`0.0`, not `NaN`, so a test keyed on a missing score never fires for it — a mistake that
leaves the label silently blank on exactly the rows it was written for.

The percentage for voltage is `LimViolPct` **for the row already chosen as worst by
severity**, never a re-max on pct — for `voltage_low`, *lower* pct is worse, so re-maxing
selects the least severe bus while looking entirely correct.

### The per-metric sorts, and why they survive in `_audit/`

| list | sort key | unit |
|---|---|---|
| thermal | worst `LimViolPct` | percent of the branch's own rating |
| voltage | worst pu distance **outside** the band | per unit |
| count | violations the outage caused | count |

Percent-of-rating is what makes differently-rated branches comparable — a 250% overload
outranks a 200% regardless of the MVA behind it. Voltage cannot use percent: measured,
`Bus Low Volts` rows sit *below* their limit with `LimViolPct` in 94-100 (lower is worse)
while `Bus High Volts` sit *above* with pct 100-103 (higher is worse). Ranking both on pct
orders overvoltages exactly backwards. Distance outside the band fixes it: 0.87 pu against a
0.90 floor and 1.13 against a 1.10 ceiling both score 0.03, and are genuinely equally bad.

"Worst single violation" and "broke the most things" are different questions, which is why
the count is its own axis rather than a tiebreaker — and why the single `severity_score`
ordering does not retire these. It answers the first question only.

### The area trap

A device's own area and the **reporting scope** are different things, and nothing in the
file says so. Violations are scoped by `Area.BGReportLimits` in the AUX, which monitors
*violated elements*, not outaged devices — so a device far outside the monitored region is
still solved and still counted, because its outage can violate something inside.

Measured on Synth2k with two of eight areas monitored: **364 of the 531 out-of-area devices
caused in-region violations.** So `n_violations = 0` on an out-of-area device means "causes
nothing in the monitored region", never "was not checked" — and filtering the device table
on area to "recover the region" silently discards 364 real results while looking like a
sensible narrowing.

### Subtracting the base case

Solve the base power flow first and record what was **already** violating, from
`Branch.LinePercent` and `Bus.BusPUVolt` — *not* from `ViolationCTG`, which is
per-contingency and says nothing about the base state. Then a post-contingency violation
counts only if the outage **caused it or made it worse**:

| category | already violating when | worse when |
|---|---|---|
| thermal | `LinePercent >= threshold` | post pct > base pct |
| voltage low | `BusPUVolt < v_min` | post pu < base pu |
| voltage high | `BusPUVolt > v_max` | post pu > base pu |

Three identity rules, each of which silently subtracts nothing if got wrong:

- **The branch key is the UNORDERED bus pair.** Identity is direction-sensitive in the raw
  data, so an ordered key matches nothing — which looks exactly like a base case with no
  violations.
- **The circuit ID is compared as normalized text.** `'10'` from one table, `10.0` after a
  CSV round-trip.
- **Read the base frames AFTER applying the limits**, because `LinePercent` is evaluated
  against the monitored rate set the limit write patches.

**Comparing percent to percent is only valid because both rate sets are pinned.** Write
`LSLineRateSet` *and* `LSLineRateSet:1` to the same value and assert it (see
[powerworld-limitset-setdata](powerworld-limitset-setdata.md)); then the base percent and the contingency percent share a
denominator. Do **not** "fix" this by comparing MVA instead — it was tried: `LinePercent` is
a *from-end* percent (from-end MVA ÷ LinePercent recovers exact ratings — 149.000001,
221.000004, 4352.000046 — while the larger of the two ends gives 149.46, 221.11, which are
not ratings), but `LimViolValue` is not guaranteed to be that same end. The swap moved 5,092
rows on a measured run for no gain, trading a denominator pinned by construction for an
end-mismatch pinned by nothing.

### What must never read as a safe device

An empty result and a clean grid look identical, so each of these is handled explicitly:

- **Diverged** (`CTGSolved != 'YES'`) — no rows. Report separately; never file as "caused
  nothing".
- **Absent from the `Contingency` table** — the run learned nothing about it, which is not
  the same as learning it is clean.
- **Islanding** — solves `YES`, emits **zero** violation rows, and ranks as harmless. Nothing
  in `CTGSolveAll` detects it (see [reading-violationctg](reading-violationctg.md)); [lodf](../concepts/lodf.md)'s `1 − ψ_kk → 0`
  catches it from topology with no solve. Until that is built, say so on every run.
- **All violations pre-existing** — a real result, but keep the raw pre-subtraction count on
  the row, because that device is the one most worth auditing and it leaves no ranked entry.
- **No area monitored** — if every `Area.BGReportLimits` is `NO`, PowerWorld reports nothing
  anywhere and *every* device ranks harmless. Abort; do not warn.

### The bus's own voltage limit, not the band you configured

`Bus.BusVoltCtgLimHigh` / `BusVoltCtgLimLow` are PowerWorld's **effective** per-bus
contingency limits — "Ctg Limit PU Volt presently being used by bus, as specified by its
limit group". A bus carrying `BusVoltLim = YES` overrides the `LimitSet` band the tool
writes, so **the configured band is not necessarily the criterion any given bus was judged
against**, and a baseline that assumes it is will be blind in exactly one direction.

MEASURED on a planning model: three buses carry a **1.05** ceiling while the run was configured for
**1.10**. Sitting at ~1.053 they are inside the configured band, so the baseline never
recorded them; their post-contingency rows carried no `base_value`, were read as violations
the outage CREATED, and survived `--only-new`. **657 of 673 reported rows were those three
buses under all 219 devices** — 219 of 220 devices ranked as causing something, off a
base-case condition. Overlap with the base-case high-voltage set: **0 of 3**. A flat band
cannot detect this; the buses never exceed 1.10 at all.

Two traps in the fix itself:

- **Compare the limits with a RELATIVE tolerance.** They come back single-precision: write
  1.10, read 1.10000002; write 0.90, read 0.89999998. An exact test reported **4000
  phantom overrides on Synth2k**, where all 2000 buses carry exactly the band and
  `BusVoltLim = NO`. Third instance of this trap in one codebase.
- **A zero or missing limit means "not reported", not "a ceiling of zero".** Taken
  literally it puts every bus in the baseline and subtracts the whole case away.

### `CTG_WhatToDoWithBC` and `--only-new` are the same answer

PowerWorld's own `CTG_Options.CTG_WhatToDoWithBC` (0 = do not report base-case violations;
1 = report all; 2 = change-from-base criteria) and this tool's Python-side `--only-new` are
**redundant, not conflicting** — verified rather than assumed. Setting the option to `0` on
Synth2k case4 and running with `--include-worsened` yields **the identical 36-row set** that
`--only-new` yields on the unmodified case: same rows, zero difference either way. Two
independent mechanisms, one inside PowerWorld's contingency engine and one in Python,
agreeing exactly.

Two honest qualifications. The `CTGViol` COUNTS differ (82 vs 153 summed over those 36
rows), because PowerWorld reports fewer violations per contingency when it is suppressing
base-case ones — the row SET is identical, the per-contingency tallies are not. And the two
runs were not config-identical: the `= 0` run screened every voltage level while the
`--only-new` run used a 69 kV floor. The comparison still holds because the kV filter
dropped nothing on this case (its lowest violated element is 115 kV), but that is a
property of Synth2k rather than of the equivalence.

`base_case_violations.csv` is unaffected by the option, because it is read from
`Branch.LinePercent` / `Bus.BusPUVolt` and never from `ViolationCTG` — a `= 0` run still
records its 6 base-case violations and simply drops 0 of them as pre-existing.

**So there is no reason to modify and re-save a case for this.** The flag does the same job
and leaves the case untouched, which matters when the cases are CEII and read-only.

### Measured: what the base case does to the answer

| | case3 (0 base viol.) | | case4 (6 base viol.) | |
|---|---|---|---|---|
| | WITH | WITHOUT | WITH | WITHOUT |
| violation rows | 29 | 29 | 278 | **36** |
| devices causing something | 18 | 18 | 252 | **20** |
| voltage_low rows | 0 | 0 | 8 | **8** |

case3 is the control: zero base-case violations, so the filter is a proven no-op. On case4
**87.1% of the WITH rows were already-broken elements**, six pre-existing violations
inflated the device count **12.6x**, and the thermal median moved `100.125 -> 104.383` while
the **maximum stayed at 153.647** — the worst outage survives either way. The 8
low-voltage rows survive both ways too, which is what shows the filter discriminating
rather than just cutting.

### Configuring a run

**Two CONFIG blocks answering different questions.** `main.py`'s decides WHICH DEVICES get
a contingency and is baked into the AUX. `rank_main.py`'s decides WHAT COUNTS AS A
VIOLATION when that AUX is solved. Changing the second never needs the AUX rebuilt;
changing the first always does. Every `rank_main.py` setting also has a flag and **the flag
wins** — CONFIG is the study's standing answer, a flag is a one-off.

| setting | flag | default | decides |
|---|---|---|---|
| `V_MIN` / `V_MAX` | `--v-min` / `--v-max` | 0.90 / 1.10 | post-contingency band, pu — written to `LimitSet`, so it is PowerWorld's own criterion |
| `THERMAL_PCT` | `--thermal-pct` | 100.0 | percent of rating that counts as overloaded |
| `RATE_SET` | `--rate-set` | `A` | which rate set — written to BOTH normal and contingency sets |
| `MIN_KV` | `--min-kv` | 69.0 | report only where the VIOLATED element is above this kV; 0 disables |
| `ONLY_NEW` | `--only-new` / `--include-worsened` | True | report only elements CLEAN in the base case |
| `SERIAL` | `--serial` / `--parallel` | False | one process (reference path) or many |

**The three filters stack and each can empty the report.** `MIN_KV`, `ONLY_NEW` and the
base-case subtraction are independent and compound hard. Measured on Synth2k case4: 786
attributable rows, subtraction drops 508, `--only-new` drops 242, **36 survive** (890
devices to 20 ranked). A near-empty result is far likelier to be three filters stacking than
a clean grid, so the run header prints the band, the kV floor and the reporting mode, and
every silent device carries three counters — `n_violations_raw` (pre-filter),
`n_below_kv`, `n_worsened_only`. **Never add a filter without a per-device counter beside
it**: it shipped once without one, and at `--min-kv 200` the branch ranked #2 at 133.9% of
rating came out at rank 585 reading `n_violations = 0`.

**`MIN_KV` screens the VIOLATED element, on its HIGHER end, strictly above.** Not the
outaged device — a generator sits at its terminal kV (13.8-20 kV on Synth2k), so screening
devices would delete every generator contingency while looking like a voltage filter. The
higher end is a deliberate trade, and NOT (as first written) for consistency with
`device_attributes`, whose `kv` is an identity label rather than a membership test: the
strict both-ends rule is cleaner on distribution but drops a 500/161 autotransformer from a
200 kV screen, and a vanished bulk asset beats clutter. Consequence to know: at
`--min-kv 100` every 115/13.8 step-down passes. `element_kv_low` is carried so the strict
rule can be applied afterwards without re-solving. A transformer overload is ONE MVA limit
on the whole device, so `element_kv` is a convention about the ASSET, not a property of the
row.

**`ONLY_NEW` discards real N-1 effects on purpose.** A pre-existing violation the outage
worsened is a genuine failure, and the attribution already credits only the increment. This
narrows the question from *what does this make worse* to *what does this BREAK*. Rows go to
`_audit/worsened_preexisting.csv`, counted per device — excluded by policy, not as noise.

**`WORSENING_REL_TOL = 1e-4` is a constant, not a knob.** The floor below which a
difference is solver noise, RELATIVE to the base value. Deliberately not a flag: a
solver-precision number is a property of the numerics, not a planner's decision, and a flag
invites silencing a flaky run by inflating it into a materiality threshold.

**Do not confuse any of this with `set_limit_monitoring.py`.** That standalone script sets
`CTG_Options.CTG_WhatToDoWithBC` (0 = do not report base-case violations; 1 = report all;
2 = change-from-base criteria) and is **not part of this pipeline**. Applying 0 to a case
this tool consumes double-filters: PowerWorld suppresses base-case violations before Python
sees them, deleting the worsened rows the subtraction deliberately keeps.

### Solving it across processes

The set comes from an AUX, so each worker can `Delete(Contingency)` + `LoadAux` the **same
file** and solve its own chunk — provably the same set, and no saved case required (see
[parallel-contingency-solve](../concepts/parallel-contingency-solve.md), whose original form needed one). The merge is a plain
**concat** of per-contingency `ViolationCTG` rows, not that page's per-bus envelope merge,
which cannot say *which* outage caused what.

Assert the merged result covers **every dispatched label**: a worker that dies after
returning an empty frame contributes nothing and its share of the grid reads as clean.

Measured on Synth2k case 3, 890 new-device contingencies: **27.1 s serial vs 38.8 s across 7
workers** — parallel is *slower* here, because each worker pays a fixed 20-45 s PowerWorld
`open()` that does not parallelize away. It earns its keep on a planning model, not on a 2k
case.

**"Byte-identical ranked CSVs" was claimed here and is FALSE — measured 2026-08-22.** The
two paths reach the same operating point by different Newton trajectories, so solved values
differ in their last digits, and a threshold applied to a noisy float is a coin flip near
the boundary. On case 4 the old absolute tolerance gave **460 caused rows serial vs 459
parallel**, flipping one device between ranked and silent. What holds after the relative
tolerance fix, and what to actually assert:

- the caused violation **set** is identical, row for row;
- the **ranked/silent partition** is identical;
- `rank` may differ only among devices whose `severity_score` differs by less than
  `WORSENING_REL_TOL`. Measured: 10 of 890 devices REORDER, by at most 5 positions, all in
  ranks 131-238, none in the material band, with a maximum severity difference among those
  ten of **8.5e-07**. That is not a suite-wide bound and must not be quoted as one — 110
  devices carry a nonzero severity difference, the largest being **1.1e-06**. They simply
  do not reorder, because the gap to their neighbour is wider than the wobble.

## Provenance

**2026-08-22 (b)** — **the baseline was judging buses against the wrong number.** A bus can
carry its own contingency voltage limits that override the `LimitSet` band the tool writes,
and the baseline was testing every bus against the configured `v_min`/`v_max`. On that planning model
three buses at a 1.05 ceiling, sitting at ~1.053, were therefore invisible to it — and
**657 of 673 reported rows were those three buses re-reported under all 219 devices**, with
219 of 220 devices ranked as causing something. `from_case` now reads
`BusVoltCtgLimHigh`/`Low` and judges each bus against the limit PowerWorld applied,
falling back to the band only where a case reports none. Comparing those limits needs the
relative floor too: they come back single-precision (1.10 -> 1.10000002), and an exact test
reported 4000 phantom overrides on a Synth2k case where every bus carries exactly the band.

Separately verified, and it settles a question that had been assumed both ways:
**`CTG_WhatToDoWithBC = 0` and `--only-new` produce the identical 36-row set** on Synth2k
case4. Redundant, not conflicting; no case needs modifying or re-saving to get the
behaviour. `set_limit_monitoring.py`, which sets that option, turned out never to have run
at all — its input path pointed at a case that does not exist — and it verified its own
write from memory BEFORE saving, so a no-op save would have passed. Both fixed.

Suite 292 -> 305 tests.


**2026-08-22** — **two scope filters added, one absolute tolerance replaced, and a
reproducibility claim retracted.** `MIN_KV` (report only violations above a nominal kV,
judged on the violated element's higher end) and `ONLY_NEW` (report only elements clean in
the base case) are now the study defaults at 69.0 / True. Three defects caught by review
before either shipped: the per-device pre-filter count was computed DOWNSTREAM of the kV
filter, so a device whose every violation was out of scope read identically to one that
breaks nothing (at `--min-kv 200` on case3, 14 of 18 offending devices, including the
branch ranked #2 at 133.9% of rating landing at rank 585 with `n_violations = 0`); a branch
with one unresolvable end was screened on the other, so a 345/13.8 transformer missing its
345 kV bus would be deleted as distribution; and `min_kv` was echoed nowhere, making a
filtered and an unfiltered run byte-identical on disk.

`THERMAL_TOL`/`VOLTAGE_TOL` (absolute 1e-6) replaced by one **relative**
`WORSENING_REL_TOL = 1e-4` via `baseline.worsened()`, mirroring the fix `limits.py` had
already made for its own read-back check. An absolute 1e-6 on a percent near 100 asks for
~1e-8 relative precision — below one float32 ULP there (7.6e-6) and far below solver
repeatability, so it was not a tolerance, it was `>`. Measured: a branch at 100.072085% in
the base case read 100.072148% after one outage, 6.3e-5 pp, and the absolute test admitted
it. Effect on case4: caused rows 460 serial / 459 parallel to **278 / 278, identical row for
row**; devices "causing a violation" 431 to 252, with all 36 material devices still in the
top 36. **The "byte-identical ranked CSVs" claim recorded here on 2026-08-18 is retracted**
-- see *Solving it across processes* for the invariant that does hold.

Suite 238 to 292 tests. The regression test pins the DERIVATION, not the number: the floor
must exceed float32 resolution at a base of 100, which is what would have caught the
original.


**2026-08-18 (b)** — **attribution added, and it changes the answer.** Subtracting the base
case was only filtering rows, not correcting magnitudes, so a device that nudged an
already-broken branch outranked one that broke a healthy line. Measured on Synth2k with the
threshold at 60%: 878 base thermal violations, **97.8% of caused thermal rows on an
already-violating branch**, reported exceedance a **median 82.6x** what the device added,
and **883 of 890 devices change position** once scored on `min(exceedance, addition)`.
At the default 100% threshold Synth2k has no base thermal violations so the thermal top-10
is unchanged, but its 13 base *voltage* violations still move 624 of 890. `severity_score`
and `avg_severity` were both recomputed independently from the raw rows and matched to
**2.8e-16** and **1.05e-16**.

Two facts found along the way, each of which produces a plausible wrong number rather than
an error: **`LimViolLimit` on a thermal row is the branch's MVA rating** (21, 46, 57, 4352),
not 100 — so thermal must score off `LimViolPct`; and the LimitSet read-back used an
**absolute** `1e-6` tolerance on `LSLinePercent`, which lives near 100 where float32 cannot
resolve that finely. Wrote 60.0, read back 60.00000238418579, run aborted claiming every
violation was measured against the wrong limit. The default 100.0 passed **only because 1.0
is exactly representable in binary**, hiding it for every threshold except the default; the
tolerance is now relative to the value's magnitude.

**2026-08-18 (a)** — the three ranked lists were collapsed into a single ranked `devices.csv`
with the `relative_severity` ordering, on `Synth2k_case` (890
new-device contingencies, band squeezed to `[0.95, 1.05]` to force voltage rows). Exit 0 in
40.5 s across 7 workers. Every number in the file was recomputed independently from the raw
violation rows: `severity_score` matched to **2.6e-16**, thermal percent to **0.00e+00**,
and the counts exactly. Two consecutive parallel runs produced a **byte-identical** file
(sha256), confirming the `CTGLabel` tiebreak holds under real worker scheduling. The shared
scale visibly reorders: thermal and voltage interleave between ranks 16 and 20, a voltage
device at `0.0386` outranking a ~103% overload at `0.0310`.

Two paths that case could **not** exercise, and which stay unit-test-only until a planning-model run:
zero diverged contingencies (so `converged=False` and the NaN-ranks-first rule), and zero
`voltage_high` rows — all 4,238 voltage rows were `voltage_low`, leaving the polarity half
of the severity function unmeasured on real data.

Measured 2026-08-17 by `C:\path\to\regional-contingency`
(`rank_main.py`, `regional_contingency/rank.py`, `baseline.py`), on
`Synth2k_case` with the 890-contingency new-device AUX, and against
the regional planning models for the base-subtraction and parallel figures. The 38%
pre-existing figure comes from a deliberately squeezed band (`[0.99, 1.01]` pu, 25% thermal)
run to force every violation category to appear — the same technique used in
[reading-violationctg](reading-violationctg.md).


---

# ==== reading-violationctg.md ====

---
type: method
domain: tooling
aliases: [violationctg, per-contingency-violations, limviolcat, limviolpct, areanum-tie-line, branch-amp]
tags: [esapp, powerworld, simauto, contingency, violations, limitset, n-1, synth2k]
---

# Reading Per-Contingency Violations (`ViolationCTG`)

## Abstract

How to get **which contingency caused which violation** out of PowerWorld — thermal, voltage
and interface, keyed by `CTGLabel` — by reading the `ViolationCTG` object after
`CTGSolveAll()`. This is the only read path that gives per-contingency attribution from a
single solve; the per-bus envelope (`BusMin/MaxVoltageContingency`) collapses everything to
one worst case and cannot say *which* outage did it.

Five traps, each of which produces a **plausible wrong answer rather than an error**. The
first four were live-measured on `Synth2k_case` on 2026-08-16; the
fifth only appears on a case Synth2k cannot produce, which is the point of it:

1. **`AreaNum` is the branch's OWN area and reads `0` on a tie-line.** Filtering on it
   silently drops every cross-area violation. The endpoint areas are `AreaNum:1` / `:2`.
2. **`LimViolPct` polarity is three-way, not two-way.** `Bus Low Volts` is a violation
   where *lower* pct is worse; `Bus High Volts` inverts. One sort key ranks one of them
   backwards.
3. **Results persist in the `.pwb`** and read back fine with no solve at all. 148 stale
   rows came out of a freshly-opened case.
4. **A bare `pw[ViolationCTG]` returns 2 columns.** You must pass an explicit field list.
5. **The `LimViolCat` vocabulary is case-dependent, not fixed.** An amp-rated branch
   reports `Branch Amp`, which Synth2k never emits — so a classifier measured there drops
   every one of those overloads as an unknown category and still completes, still writes
   plausible CSVs, and still reports a grid it never screened.

Also settled here: the claim in `contingency_esapp.py`'s module docstring that esapp's typed
read of `ViolationCTG` errors *"interface unknown"* on Synth2k **does not reproduce**.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esapp package
- **Across:** [new-device-contingency-aux](new-device-contingency-aux.md) (building the set you solve, and scoping
  monitoring to an area) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) · [lodf](../concepts/lodf.md) ·
  [powerworld-simauto](../concepts/powerworld-simauto.md) · critical-branch screening
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The read

```python
from esapp.components import ViolationCTG

VIOLATION_FIELDS = [
    "CTGLabel", "LimViolCat", "LimViolValue", "LimViolLimit", "LimViolPct",
    "AreaNum", "AreaNum:1", "AreaNum:2", "BusNum", "BusNum:1", "BusNum:2",
    "LineCircuit", "CTGViol", "CTGNVoltViol", "LimViolID",
]

pw.esa.SetData("Sim_Solution_Options", ["DCApprox"], ["NO"])
pw.esa.SetData("CTG_Options", ["CTG_CalculationMethod"], ["AC"])
pw.esa.SolvePowerFlow()
pw.esa.CTGClearAllResults()          # MANDATORY -- see trap 3
pw.esa.CTGSolveAll()

violations = pw[ViolationCTG, VIOLATION_FIELDS]
```

**Field spelling is `AreaNum:1`, with a colon.** `ViolationCTG.fields()` has 394 entries and
none of them use a `__1` double-underscore form. There is no `ObjectString` field on
`ContingencyElement` either, despite what you may have been told.

### `LimViolCat` — the vocabulary

| `LimViolCat` | means | first seen on |
|---|---|---|
| `Branch MVA` | thermal overload, branch rated in MVA | Synth2k |
| `Branch Amp` | thermal overload, branch rated in **amps** | planning model |
| `Bus Low Volts` | undervoltage | Synth2k |
| `Bus High Volts` | overvoltage | Synth2k |
| `Interface MW` | interface flow (Synth2k carries weather-zone interfaces natively) | Synth2k |
| `Unsolved` | pseudo-row for a contingency that did not solve — a divergence, **not** a violation | planning model |

The original four were observed by squeezing both bands on Synth2k until every category had
to appear, with the note *"treat this as a vocabulary to fail loudly against, not an
exhaustive enum."* **That note was right, and ignoring it cost a wrong answer.** Synth2k
rates every branch in MVA, so `Branch Amp` was never seen there; a real utility planning
model rates part of its system in amps and PowerWorld emits **both strings from the same
solve**, on disjoint sets of branches. In one measured run, 2,972 real overloads on a
planning model
(101.7%–240.7% of rating, all 297 contingencies) were classified `unknown` and dropped
while the run reported 18 violations and looked clean.

Two rules follow, and they are not the same rule:

- **`Branch Amp` is thermal.** Score it off `LimViolPct` exactly as `Branch MVA` — percent
  is percent regardless of the rating's unit, so the two never need an exchange rate. But
  `LimViolValue` / `LimViolLimit` on those rows **are amps** (284–2,176 A on that model) and
  must never be compared against an MVA row's.
- **`Unsolved` is not.** It is `CTGSolved = NO` arriving through the violation table.
  Ranking it as a violation scores a contingency the run established *nothing* about.

Before trusting a thermal count on a new case, check what the case rates in:
`LimitSet.LSAmpMVA` says which, and `LSEndMonitor` says which end.

### Trap 1 — `AreaNum` is the branch's own area, and it is `0` on a tie-line

This is the expensive one. The four `AreaNum` slots are not four copies of the same thing:

| slot | meaning |
|---|---|
| `AreaNum` | the **object's own** area — `0` when a branch spans two areas |
| `AreaNum:1` | the FROM-bus's area |
| `AreaNum:2` | the TO-bus's area |
| `AreaNum:3` | tracked `AreaNum:1` on every observed row |

Measured on branch 1004 (Far West) → 3133 (West):
`AreaNum=0, AreaNum:1=1, AreaNum:2=3, AreaNum:3=1`.

On an intra-area branch all four read the same number, which is exactly why this is easy to
miss — you have to look at a tie-line to see the difference at all. **1,933 of 36,122
thermal rows** on the observed run were tie-lines, i.e. `AreaNum == 0`.

> **A region filter written as `AreaNum in R` drops every tie-line violation and looks
> completely correct while doing it.** The safe rule is to join `BusNum` / `BusNum:1` to
> the `Bus` table and use those areas; keep `AreaNum:1` / `:2` only as a cross-check.

### Trap 2 — `LimViolPct` polarity is three-way

| category | value vs limit | worse means | observed pct range |
|---|---|---|---|
| `Branch MVA` | above | **higher** pct | >100 |
| `Bus Low Volts` | below (6,385/6,385 rows) | **lower** pct | 94.06 – 100 |
| `Bus High Volts` | above (7,956/7,956 rows) | **higher** pct | 100 – 102.97 |

So a `{thermal, voltage}` two-way split ranks over-voltages backwards. Rank **thermal on
`LimViolPct`** (percent of its own rating is what makes differently-rated branches
comparable) and **voltage on the signed pu deviation** from `LimViolValue`. Per-bus rate
sets (`LSCtgBusLowRateSet` / `LSCtgBusHighRateSet`) also mean `LimViolLimit` need not be
constant across rows, so percent is not comparable bus-to-bus either.

`LimViolValue == LimViolLimit * LimViolPct / 100` held on **120,428 of 120,428 rows** — so
the typed value is trustworthy, and the arithmetic is a good cross-check assertion.

### Trap 3 — results persist in the `.pwb`

`ViolationCTG` survives in the saved case. Opening a case and reading it immediately
returned **148 rows** from some previous run, full of real-looking numbers.

Call `CTGClearAllResults()` before every solve, and assert every returned `CTGLabel` is in
the set you meant to solve.

### Trap 4 — never use a bare read

```python
pw[ViolationCTG]                    # -> 2 columns: CTGLabel, LimViolID:1
pw[ViolationCTG, VIOLATION_FIELDS]  # -> everything you asked for
```

### The per-category column contract

Which identity slots are populated, by category (`1.0` = always, `0.0` = never):

| `LimViolCat` | `AreaNum` | `AreaNum:1` | `AreaNum:2` | `BusNum` | `BusNum:1` | `BusNum:2` | `LineCircuit` |
|---|---|---|---|---|---|---|---|
| `Branch MVA` | 1.0 intra / **0 tie** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| `Branch Amp` | 1.0 intra / **0 tie** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| `Bus High Volts` | 1.0 | 1.0 | 0.0 | 1.0 | **0.0** | 1.0 | 0.0 |
| `Bus Low Volts` | 1.0 | 1.0 | 0.0 | 1.0 | **0.0** | 1.0 | 0.0 |
| `Interface MW` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Two consequences worth internalising:

- **A bus violation carries a populated `AreaNum:1`.** So a two-endpoint OR applied
  unconditionally attributes a bus to an unrelated area. `BusNum:1` is the clean
  discriminator — populated for branch rows, empty for bus rows.
- **Interface rows carry no identity at all.** They cannot be attributed to a region; drop
  them deliberately and print the count.

### Row-count integrity, and why not to deduplicate

`rows_per_label == CTGViol` held exactly on **40/40** labels. Assert it — it catches
duplication *and* dropped rows for free.

**But it does NOT hold on every model, and the reason matters.** On a regional
planning model (2026-08-17) a label returned 1 row while its own `CTGViol` read `0`.

The tempting explanation — that `CTGViol` counts only branch violations, so a voltage-only
contingency reads 0 — is **wrong, and was tested**:

- esapp's schema defines `CTGViol` as *"the number of violations that occurred under this
  contingency"*, unqualified (`esapp/components/grid.py`, class `Contingency`), while
  `CTGNBranchViol` / `CTGNVoltViol` / `CTGNInterfaceViol` are the branch / **bus** /
  interface counts.
- Synth2k confirms it is the sum: `3010 + 1 + 1195 = 4206` exactly, on a label carrying all
  three kinds (Stage 0b, Q4).

So `CTGViol` **does** include voltage violations, and a disagreement is a real signal rather
than a scope quirk. The live candidates are a **stale or duplicate-labelled `Contingency`
record** — a label-keyed join silently collapses duplicates to whichever side wins, and
`Contingency` aggregates persist in the `.pwb` exactly like `ViolationCTG` does (trap 3) —
or rows genuinely dropped.

The discriminating probe, from data you have already read:

| check | what it means |
|---|---|
| more than one `Contingency` row shares the label | duplicate record; the count you read is the wrong record's |
| `rows == 0` while `CTGViol > 0` | rows were dropped — and that device will read as causing nothing |
| `CTGViol != CTGNBranchViol + CTGNVoltViol + CTGNInterfaceViol` | the aggregate is stale for that label |

Note the guard is worth keeping but **not worth aborting on after an expensive solve** —
report the evidence and mark the run unverified instead, or you destroy the rows you would
need to tell these three apart.

`LimViolCTGSpecifiedLimit` (*"If YES, Limit was specified during a contingency action. This
Limit overrides all Limit Monitoring Settings."*) is a separate, real mechanism for a
violation whose limit differs from the standing `LimitSet`. It read `NO` on those rows
above, so it did not explain them — but it is not in the default field list and is worth
reading when limits and violations disagree.

Do **not** deduplicate on `(label, category, element)`. Repeated-looking rows are usually
real: four parallel circuits on one bus pair produce one contingency each, and outaging any
one overloads the other three. That is 3 rows per label with identical bus numbers and
*different* `LineCircuit` values — a dedup on the bus pair would silently eat them.

### `ContingencyElement` has no `LineCircuit`

To map a branch to its auto-inserted contingency label, the third key comes from
**`ElementID`**, verified to distinguish parallel circuits on three bus pairs including a
three-circuit transformer bank (`'1'`, `'10'`, `'20'`). `Object` (`"BRANCH 1001 1064 1"`)
works equally well.

**Never parse the `CTGLabel` string.** It embeds *truncated* substation names
(`L_001068MIDLAND10-001016GARDENCITY0C1`) and truncation collides.

### Islanding: invisible to `ViolationCTG`, visible through three other checks

`CTGSolved` catches divergence reliably. Islanding it does not, and neither does anything
else that was probed against eight outages that provably island a bus:

- `BusMinVoltageContingency == 0` is **not** an islanding signal — 1,466 of 2,000 buses read
  0.0 on an ordinary run. It means "the band was never breached in that direction for that
  bus". (This is the same `0.0` that `n1_voltage_violations` already treats as
  "not evaluated".)
- All eight islanding contingencies reported `CTGSolved='YES'` with thousands of ordinary
  violations — indistinguishable from any other contingency.
- `CTGWhatOccurredCount`/`:1`/`:2`, `CTGAltPFBusCount`, `CTGAltPFPossible` and
  `CTGRemedialActionApplied` are identically zero/`"Not Checked"` either way.
- No `Bus Low Volts` row anywhere read near 0 pu (minimum 0.9312) — **islanded buses emit no
  violation rows at all.**

If you need islanding detection, `ViolationCTG` alone will not give it to you — **and
[lodf](../concepts/lodf.md) will, for free and without a solve.** When the LODF denominator `1 − ψ_kk → 0`
there is no alternate path, i.e. outaging that branch splits the network; the math flags it
before any solve is attempted. Measured on Synth8k: **420 of 13,470** outages, found in the
~6 s it takes to build the PTDF. That page reached the same conclusion from the other
direction — *"in a PowerWorld CTG sweep, islanded buses read 0 and get skipped, so stranding
a 138 kV pocket reports CLEAN"* — and this page is the independent confirmation of that hole
from inside `ViolationCTG`.

**Correction (2026-09-24, completed 2026-09-28): islanding *is* visible after `CTGSolveAll` —
through three checks that each catch a different set, and no single one catches all.**

- **`Contingency.LoadMW` / `GenMW`** hold the load and generation cut off by each outage and are
  non-zero only on islanding outages — these are islands PowerWorld **drops**. Checked against a
  direct `CTGApply` plus re-solve of every outage on a public 40-bus synthetic case (93 of 93
  agreed). A generation-only pocket reads `LoadMW = 0`; catch it through `GenMW`.
- **`CTG_Options.Include`** (concise `IslandViolations`) = YES, with `BGLoadMW` and
  `IslandTotalBus` as minimum-size filters and `Sim_Solution_Options.EvalSolutionIsland` = YES as
  its prerequisite, reports *Island Solved* rows for self-sustaining pockets PowerWorld keeps
  **energized** — exactly the ones where `LoadMW` / `GenMW` read 0.
- **`DetermineBranchesThatCreateIslands`** (script) is the structural check: it finds both kinds
  plus 0-MW pockets whose generation is offline.

Measured 2026-09-28 on a regional synthetic planning model. Gate an island check on MW only when
the stranded pocket carries MW. The LODF denominator above remains the solve-free screen.
`ViolationCTG` alone still ranks every one of these outages harmless — read the island checks
alongside it.

### Rate sets on Synth2k series-24

Only rate set **A** carries any limit — 3,911 branches, median 221 MVA, max 4,352. `LineAMVA:1`
through `:7` (B–H) are entirely unpopulated, and the case ships monitoring `LSLineRateSet="A"`.

**There is no separate emergency rating on these cases.** Do not assume `"B"`; read
`LineAMVA:N` and see which letters actually carry numbers before claiming a result is against
an emergency criterion.

### Aggregates you get for free

`Contingency` also carries per-contingency aggregates PowerWorld computes itself:
`CTGViolMaxLine`, `CTGViolMaxVolt`, `CTGViolMinVolt`, `CTGNBranchViol`, `CTGNInterfaceViol`,
`AggrMVAOverload`, `AggrPercentOverload`. They are **not** region-filtered, so they cannot
replace a regional study — but they are a free whole-system cross-check on a ranking.

## Provenance

Measured live on 2026-08-16 against
`Synth2k_case.PWB` by the Stage-0 spike of
`C:\path\to\regional-contingency` — `spike/stage0_spike.py` and
`spike/stage0b_spike.py`, with the full output tables in that repo's
`docs/stage0_findings.md` and `docs/stage0b_findings.md`.

Numbers quoted here come from a run with the bands deliberately squeezed
(`LSLinePercent=25`, band `[0.99, 1.01]`) so that every category was forced to appear.


---

# ==== reducing-a-contingency-set.md ====

---
type: method
domain: cross-cutting
aliases: [ctgskip, ctg-skip, reducing-the-ctg-set, contingency-subset, skip-column]
tags: [powerworld, contingency, ctg, esapp, simauto, n-1]
---

# Method: Reducing or partitioning a contingency set

## Abstract

`CTGSkip` and `Delete(Contingency, <filter>)` do two different jobs and are
routinely confused. **`CTGSkip` partitions a set without shrinking it** — every
contingency stays in the case and the skipped ones are simply not solved this
pass, which is how the parallel solver gives each worker a slice. **`Delete` with
a violation filter is the only thing that actually reduces the set**, and it is
destructive, so it needs a backup first. This page collects the mechanism, the
three places it is used, and the three silent failures around it; before this,
`CTGSkip` was mentioned on five pages and owned by none.

## Connections

- **Up:** [Home](../index.md) · contingency remediation
- **Across:** [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) — the chunking use ·
  [new-device-contingency-aux](new-device-contingency-aux.md) — writing a subset to `.aux` ·
  [reading-violationctg](reading-violationctg.md) — where the violation columns the filter uses come from

## Content

### The two mechanisms, and which one you want

| you want | use | destructive? |
|---|---|---|
| solve part of the set now, keep all of it | `CTGSkip` = `YES` / `NO` | no |
| permanently drop contingencies that did nothing | `Delete(Contingency, "<filter>")` | **yes** |

**"Are you reducing the ctg set by setting SKIP to YES?"** — no. Setting
`CTGSkip="YES"` excludes a contingency from *this* `CTGSolveAll` and leaves it in
the case. The set is the same size afterwards. That is the right tool for
partitioning and the wrong tool for reduction.

### `CTGSkip` — partitioning

`CTGSkip` is a field on the `Contingency` object, per contingency. Write it with
`change_parameters_multiple_element_df`, and **keep the `Contingency` key field
in the DataFrame** or the write silently no-ops.

Three recorded uses:

1. **Parallel chunking** ([parallel-contingency-solve](../concepts/parallel-contingency-solve.md)). Split the existing
   `CTGLabel` set with `np.array_split`; each OS process sets `CTGSkip=NO` for
   only its own chunk's labels and `YES` for everything else, then runs a plain
   serial `CTGSolveAll`. The full set is intact in every worker's case; each just
   solves its slice.
2. **Reactivating everything.** Read the
   `Contingency` key plus `CTGSkip`, set `CTGSkip="NO"` across the frame, write
   it back. This is the reset before a full sweep.
3. **Persisting a subset** ([new-device-contingency-aux](new-device-contingency-aux.md)). `CTGSkip` travels in
   the `.aux` alongside `CTGLabel`, so a saved subset remembers what was skipped.

### `Delete` — the actual reduction

To shrink the set to what actually violated, filter on the violation counts that
the previous solve wrote:

```
Delete(Contingency, "CTGNVoltViol = 0")    # drop those with no voltage violation
Delete(Contingency, "CTGNBranchViol = 0")  # drop those with no overload
Delete(Contingency, "CTGViol = 0")         # drop those with neither
EnterMode(RUN);
```

**One condition only. `AND` is not supported in this filter.** If you need both,
delete twice or use `CTGViol`.

**Back up first, because this is destructive:**

```
CTGWriteAuxUsingOptions("<path>", NO);   # save the full set
Delete(Contingency);                      # ... work ...
LoadAux("<path>");                        # restore
```

### Multi-round: full sweep, then violations only

The pattern of *"first round full CTG, later rounds only the ones that violated"*
is assembled from the two mechanisms above and is **not** a single built feature:

1. Solve the full set (partition with `CTGSkip` across processes if it is large).
2. Back up with `CTGWriteAuxUsingOptions`.
3. `Delete(Contingency, "CTGViol = 0")` — the survivors are the reduced set.
4. Re-solve the survivors each later round.
5. `LoadAux` the backup when a round needs the full set again.

Step 3 reads violation counts populated by step 1, so the ordering is not
optional. [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) explicitly scopes *out* per-contingency
remediation walks that mutate state between rounds, so do not expect its parallel
helper to carry this loop for you.

### Three silent failures

- **An unquoted action string in a hand-written `.aux`.** Written bare as
  `BRANCH 1001 1064 1 OPEN` instead of quoted, a 691-contingency file loads as
  **one** contingency — and the load **reports success**. Always quote the action.
- **`SaveContingencies` is not a script command** ("Unknown script command"). Use
  `SaveData(<path>,AUX,Contingency,[CTGLabel,CTGSkip],[CTGElement],"",[],[],YES);`
  — the filter argument is a bare string and the sort lists must be bracketed.
- **A missing key field on the write-back.** `change_parameters_multiple_element_df`
  needs the object's key field present or the `CTGSkip` change does nothing and
  says nothing.

### Where the filter's columns come from

`CTGNVoltViol`, `CTGNBranchViol` and `CTGViol` are populated by the solve.
[reading-violationctg](reading-violationctg.md) covers reading per-contingency violations back;
`CTGSolved` and `CTGViol` are among the fields the contingency object exposes.

## Provenance

Every fact here was already recorded and is consolidated rather than derived:
the chunking scheme from [parallel-contingency-solve](../concepts/parallel-contingency-solve.md), the `.aux` shape and its
quoting trap from [new-device-contingency-aux](new-device-contingency-aux.md), the `Delete` filters, the
single-condition limit, the backup/restore pair, and the contingency field list.

Written 2026-09-07 because the A/B measurement found `CTGSkip` mentioned on five
pages and owned by none: asked *"are you reducing the ctg set as well by setting
the SKIP column to YES?"*, three independent agents each picked a **different**
wrong page.


---

# ==== save-powerworld-case.md ====

---
type: method
domain: tooling
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
against the installed package.

## Connections

- **Up:** [esapp](../concepts/esapp.md) · esa pp llm
- **Across:** [adding-devices-esapp](adding-devices-esapp.md) · [esapp-overview](esapp-overview.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) · [converting-lines-to-transformers](converting-lines-to-transformers.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The one-liner that works

```python
import os
out = os.path.abspath(r"D:\path\to\Outputs\case_out.pwb")
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

### Typical use: save a solved design so a human can open it

Open the base case, apply a design, solve, then save — the pattern used by
`esa_pp_llm/Functions/save_cases.py` to emit inspectable cases for the agent-vs-expert demo:

```python
pw = tep.open_case(scenario_path)
try:
    tep.set_target_loads(pw)
    tep.apply_design(pw, design)     # CreateData buses/branches/loads — see methods/adding-devices-esapp.md
    tep.solve_dcopf(pw)
    out = os.path.abspath(r"D:\...\Outputs\Synth2k_scenarioA.pwb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
    assert os.path.exists(out)
finally:
    pw.close()
```

Saving before `pw.close()` captures the in-memory edits (new devices + solved state); the reopened
`.pwb` shows exactly what the pipeline built.

> House rules honored: drive SimAuto via `esapp` `RunScriptCommand` (not raw `esa`, not the flaky COM
> `SaveCase`); verify the artifact exists before claiming success (see [esapp](../concepts/esapp.md)).


---

# ==== teamoverbyeweather-client.md ====

---
type: method
domain: weather
aliases: [teamoverbyeweather, team-overbye-weather, weather-client, weather-sdk, TeamOverbyeWeather]
tags: [weather, pww, era5, hrrr, noaa, python, client, download]
---

# Method: Getting weather data with the TeamOverbyeWeather client

## Abstract

`TeamOverbyeWeather` is a pip-installable Python client for the Team Overbye weather
portal. One call downloads a weather dataset, crops it to a region, and crops it to a
time window, returning `.pww` files ready for PowerWorld. This is the kit's front door
for getting the `.pww` files PowerWorld's TimeStep feature consumes, and the **one part
that needs no PowerWorld licence** — the client, the PWW reader, and the cropping tools
are pure Python. Verified against version 0.4.0.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [pww-data](../concepts/pww-data.md) · [timestep-workflow](../concepts/timestep-workflow.md)
- **Next:** [timestep-simulation-setup](timestep-simulation-setup.md) to feed the downloaded PWW into PowerWorld

## Content

### Install

```bash
pip install TeamOverbyeWeather
```

Depends only on `numpy`, `requests`, and `tqdm`. No PowerWorld, no Windows requirement.

### The whole thing in five lines

```python
from TeamOverbyeWeather import WeatherClient

client = WeatherClient()
files = client.download("era5", "2021-02", region="TX", dest="./weather")
print(files)   # [PosixPath('weather/era5_texas_2021-02.pww')]
```

`download()` fetches, crops to the region, and crops to the time window server- or
client-side as appropriate, then writes `.pww`. Everything else on this page is detail.

### What data is available

Do not guess source or type names — ask the server:

```python
client.sources()          # ['era5', 'extreme', 'hrrr', 'noaa']
client.types("era5")      # ['historical', 'na', 'north_america', 'texas', 'tx']
client.types("hrrr")      # ['archive', 'current', 'forecast', 'history',
                          #  'hourly_archive', 'hourly_current']
client.types("noaa")      # ['archive', 'forecast', 'recent']
client.types("extreme")   # ['events']
client.catalog()          # everything, as a dict
client.status()           # server health
```

The four sources, and when to reach for each:

| Source | What it is | Use it for |
|---|---|---|
| `era5` | ECMWF reanalysis, hourly, ~0.25° | Long historical records. The default for screening a whole year |
| `hrrr` | NOAA High-Resolution Rapid Refresh, ~3 km, sub-hourly | Refining a specific event once screening has found it |
| `noaa` | NOAA GFS forecasts and archive | Forward-looking studies |
| `extreme` | The portal's curated extreme-event catalogue | Jumping straight to a known event without hunting for its dates |

Screen wide with `era5`, then refine a specific window with `hrrr`. Downloading HRRR for
a full year is neither necessary nor kind to the server.

### Selecting a region

Four mutually exclusive ways, in increasing order of precision:

```python
client.download("era5", "2021-02", region="TX")                       # a state
client.download("era5", "2021-02", iso="<ISO>")                        # an ISO footprint
client.download("era5", "2021-02", bbox=(25.8, -106.7, 36.5, -93.5))  # lat/lon box
client.download("era5", "2021-02")                                    # everything, usually too much
```

Discover valid identifiers rather than guessing:

```python
client.regions()                    # every layer the server knows
client.region_ids("states")         # ['AL', 'AK', 'AZ', 'AR', 'CA', ...]
```

`bbox` is `(lat_min, lon_min, lat_max, lon_max)`. West longitudes are negative.

**A too-large request raises `RegionTooLargeError` rather than silently truncating.**
That is the server protecting itself; narrow the region or shorten the window.

### Selecting a time window

`dates` accepts a single date, a month string, or a list. For sub-day precision, add
`time_start` and `time_end`:

```python
files = client.download(
    "era5",
    "2021-02",
    region="TX",
    time_start="2021-02-14T00:00:00Z",
    time_end="2021-02-19T23:00:00Z",
    dest="./winter_storm_uri",
)
```

### The full signature

```python
client.download(
    source,                # 'era5' | 'hrrr' | 'noaa' | 'extreme'
    dates,                 # date, month string, or list
    type=None,             # from client.types(source)
    region=None,           # state/region id
    iso=None,              # ISO footprint
    bbox=None,             # (lat_min, lon_min, lat_max, lon_max)
    time_start=None,
    time_end=None,
    dest=".",              # output directory
    show_progress=None,    # overrides the client-level setting
    local_crop=True,       # crop client-side after download
    keep_raw=False,        # keep the uncropped download too
) -> list[Path]
```

Two flags:

- `local_crop=True` (the default) crops on your machine after downloading. Set it
  `False` only if you want exactly what the server sent.
- `keep_raw=True` keeps the uncropped file alongside the cropped one. Useful when you
  expect to re-crop the same download several ways; wasteful otherwise.

### Errors it raises

| Exception | Meaning | What to do |
|---|---|---|
| `RegionTooLargeError` | The requested region × time window exceeds the server's limit | Narrow the region, or split the time window and concatenate |
| `ServerBusyError` | The portal is under load | Back off and retry. Do not hammer it in a loop |
| `WeatherAPIError` | Anything else from the API | Read the message; usually a bad source/type/region name. Call `client.sources()` and `client.types()` to check |

```python
from TeamOverbyeWeather import RegionTooLargeError, ServerBusyError, WeatherAPIError
```

### Working with PWW files locally, without PowerWorld

The package reads and writes the PWW format directly. This is how you inspect weather
data on a machine with no PowerWorld licence.

```python
from TeamOverbyeWeather import pww_io

header, stations, arr = pww_io.read_pww_file("weather/era5_texas_2021-02.pww")
print(header)              # metadata: fields, time base, counts
print(len(stations))       # weather stations in the file
print(arr.shape)           # (time, station, field) numpy array
```

Crop, concatenate, and write back:

```python
from TeamOverbyeWeather import pww_io, localcrop

# crop an existing file on disk in one call
localcrop.crop_file("big.pww", "texas_only.pww",
                    bbox=(25.8, -106.7, 36.5, -93.5))

# or work in memory
header, stations, arr = pww_io.crop_to_bbox(header, stations, arr,
                                            (25.8, -106.7, 36.5, -93.5))
header, arr = pww_io.crop_to_timerange(header, arr, t_start, t_end)

# stitch several downloads into one continuous series
header, stations, arr = pww_io.concat_time([piece1, piece2, piece3])

open("combined.pww", "wb").write(pww_io.write_pww(header, stations, arr))
```

`concat_time` is the client-side answer to a region-too-large or window-too-long
rejection: download the pieces separately, then join them.

### Handing the result to PowerWorld

The `.pww` file this produces is the input to PowerWorld's TimeStep simulation. Continue
at [timestep-simulation-setup](timestep-simulation-setup.md), which loads it with `TimeStepLoadPWWRangeLatLon` and
runs the weather-to-MW conversion.

Crop before loading, not after. PowerWorld will happily ingest a continental PWW and
then spend a long time on stations you do not care about.

### What this client is not

It serves the Team Overbye portal specifically. It is not a general ERA5 or HRRR client
— for raw upstream access, see weather sources. Its value is that the region crop,
the time crop, and the PWW conversion are already done, which is normally the tedious
part.


---

# ==== timestep-simulation-setup.md ====

---
type: method
domain: cross-cutting
aliases: [timestep-setup, ts-setup, timestep-simulation-howto]
tags: [powerworld, simauto, timestep, simulation, weather, renewables, pww]
---

# Method: Writing a timestep simulation

## Abstract

How to drive PowerWorld's TimeStep simulation — turning `.pww` weather files into hourly solar/wind generation CSVs. Covers the prerequisites a case must satisfy per renewable generator (`GenFuelType` containing WND or SUN, valid Lat/Lon, a `TSPFWModelString` PFW model), one pipeline's optional ISO-labelling step, and the `_simulation_worker` function sequence. This is Step 2 of the flagship trail; for the PWW weather files see [pww-data](../concepts/pww-data.md).

> 🔧 **Writing the backend code?** → **[time-step-simulation-backend](../references/time-step-simulation-backend.md)** has the full `_simulation_worker` call sequence, the required `TIMESTEPSaveSelectedModifyStart/Finish` wrapper, the `_GEN_PARAM` field list, and the key-field rule. That page is the *rebuild-the-code* reference; this page is the *write-it* guide.

## Connections

- **Up:** [Home](../index.md) · time step simulation
- **Deeper (backend code):** [time-step-simulation-backend](../references/time-step-simulation-backend.md) — exact call sequence, field lists, gotchas (read this for the backend, not just running it)
- **Across:** [timestep-simulation](../concepts/timestep-simulation.md) · [grid-workshop-auto-pfw](../concepts/grid-workshop-auto-pfw.md) (attaching the PFW models) · [esapp](../concepts/esapp.md) · flagship step 2 — prev: [esapp-overview](esapp-overview.md) · next: [pww-data](../concepts/pww-data.md) · final: [how-to-analyze-results](how-to-analyze-results.md)

## Content

**Step 2 of the flagship trail.** ← prev: [esapp-overview](esapp-overview.md) · next: [pww-data](../concepts/pww-data.md).
Owning project: time step simulation. The concept behind it: [timestep-simulation](../concepts/timestep-simulation.md).

This is the how-to for **writing** a PowerWorld TimeStep simulation — code that drives PowerWorld through SimAuto to turn weather files (`.pww`) into hourly solar/wind generation CSVs. It is *not* a transient-stability study.

> **Library note — prefer `esapp` over `esa`.** Older repos import the standalone `esa` (Easy SimAuto) package. `esapp` (ESA++) is the updated, better-documented version of the same thing — write esapp. Every `RunScriptCommand` / `TimeStep*` script command is identical via `pw.esa.RunScriptCommand(...)`, and the bracket interface (`pw[Type, fields]`, `pw[Type] = df`) replaces esa's `GetParametersMultipleElement` / `change_parameters_multiple_element_df`. See [esapp-overview](esapp-overview.md). (Library choice only — unrelated to the TimeStep-vs-Transient-Stability distinction.)

## 0. Prerequisites

PowerWorld needs, on each renewable generator: a `GenFuelType` that contains `WND`
or `SUN` (the case labels them `WND (Wind)`, `SUN (Solar)`), valid coordinates, and a
PFW model string (`TSPFWModelString` longer than 2 characters). A unit with no PFW model
runs and reads 0 MW for the whole run; attach models with
[grid-workshop-auto-pfw](../concepts/grid-workshop-auto-pfw.md). Coordinates: on both public
synthetic cases probed 2026-09-30 the unit's own `Gen.Latitude` read blank and the substation's
`Gen.Latitude:1` / `Longitude:1` (the field export's "Substation Latitude") were set. That
TimeStep then reads the substation pair is not verified in the kit.

## 1. (Optional, one pipeline's convention) Label units with an ISO region

This is **not** a PowerWorld prerequisite. One time-step pipeline writes an ISO region into
`CustomString:2`, a custom field, so its output CSVs can carry an ISO header row; TimeStep does
not read it. Skip this section unless your post-processing needs the label.

`PFW_Insertion/ISO_Insertion_code_shape_file.ipynb` does a geopandas spatial join
of every generator's lat/long against ISO-region shapefiles (nearest-neighbor for
units outside any boundary) and writes the ISO assignment back into the case. This
populates the ISO that later appears as the first metadata header row. Run it once
per case; skip it if the case already has ISO assignments.

> **Resolved:** `PFW_Insertion` (`ISO_Insertion_code_shape_file.ipynb`) writes
> **only `CustomString:2`** (the ISO region via geopandas spatial join). It does
> **not** touch `TSPFWModelString`. PFW model strings must already be in the case;
> [grid-workshop-auto-pfw](../concepts/grid-workshop-auto-pfw.md) attaches them, and the
> case-auditor's `timestep` profile counts which units still lack one.

## 2. What your code does (`_simulation_worker`)

`_simulation_worker(case, pww_list, result_csv)` is the core function to implement:
1. Copies the case to a temp `.pwb`, opens it with `PowerWorld(tmp_case)` from esapp.
2. Pulls generator metadata (`GetParametersMultipleElement('gen', ...)` / `pw[Gen, fields]`).
3. Loads weather: `TimeStepLoadPWW("...","Weather Only")` then
   `TimeStepAppendPWW(...)` for any additional files.
4. Selects renewables (`GenFuelType` contains `WND|SUN`) and marks them
   `TimeDomainSelected`.
5. Picks the saved fields:
   `TimeStepSaveFieldsSet(GEN, [BGGenMWFuelTypeGeneric:10, BGGenMWFuelTypeGeneric:12], SELECTED)`.
6. Runs `TimeStepDoRun()` and exports via `TimeStepSaveResultsByTypeCSV(gen, ...)`.

> The simulation is **generator-level** by construction — `TimeStepSaveFieldsSet`
> targets `GEN`. Area/substation-level output is a noted future extension.

## 3. Inputs and outputs

- **In:** one case + one or more `.pww` weather files ([pww-data](../concepts/pww-data.md)).
- **Out:** per run, two CSVs (solar + wind). Historical quarter files grouped by
  year are named `Historical_{year}_solar.csv` / `_wind.csv`; a forecast file is
  named after its stem. Resume-safe: a run is skipped if both its CSVs already
  exist (delete them to re-run).

## Next

- Get the weather inputs → [pww-data](../concepts/pww-data.md)
- Analyze the CSVs → [how-to-analyze-results](how-to-analyze-results.md)


---

# ==== violation-network-map.md ====

---
type: method
domain: tooling
aliases: [violation-network-map, violation-map, voltage-map, reactive-balance-map, radial-ties-map,
  islanding-screen, map-the-violations, visualize-the-violations, network-map, bridge-screen]
tags: [esapp, powerworld, voltage, overvoltage, islanding, radial, bridges, visualization, html,
  remediation, n-1, reactive-power]
---

# Mapping Violations on the Network: the Voltage Page and the Radial-Ties Page

## Abstract

Two single-file HTML pages that put a violation **on the map** instead of in a table, built by the
`violation-map` skill's engine (`skills/violation-map/engine/`). The **voltage page** shows the
substations around a set of out-of-band buses, every line in its own kV colour, a click-to-zoom
problem list, a one-line of any substation, the **reactive balance** inside the radius (line
charging against generators absorbing and reactors, with the *room* each has left), and —
optionally — measured candidate fixes with a Before/After switch and a scenario × outage
pass/fail grid. The **radial-ties page** screens the whole grid for **bridges** (lines whose
single outage splits the network), groups them into radial trees, suggests a tie per tree and
shows its AC-measured verdict.

Four facts decide whether the pages tell the truth, and each fails silently: an outage that
**islands load solves with zero violations**, so islanding needs its own screen; a measured
candidate needs a **fresh case**, because LTC taps and switched shunts do not move back when you
undo; a tie's **rating does not scale with its length**; and a PowerWorld process you do not
`esa.exit()` stays resident.

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
python $E/measure_designs.py config.json           # optional: candidate fixes, in memory
python $E/build.py           config.json           # -> voltage_map.html
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
  voltage and confuses the reader.
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

### What it does not do yet

**No thermal view.** Both pages were built for voltage and islanding. A thermal page would extend
the voltage template — lines coloured by percent of Rate A, overloaded branches as the problem
list, the driving outage per branch from `ViolationCTG` — rather than start a new one. Say so
when asked for it; do not present the voltage page as covering thermal.


---

# ==== visualize-renewable-output.md ====

---
type: method
domain: cross-cutting
aliases: [viz-renewable, plot-solar-wind, visualize-timestep-output]
tags: [powerworld, analysis, visualization, matplotlib, solar, wind, renewables, pandas]
---

# Method: Writing code to visualize renewable output

## Abstract

How to write matplotlib code that visualizes the solar/wind CSVs produced by the timestep simulation. Covers loading the 8-row metadata + hourly data structure, parsing timestamps, and the four key plot patterns: fleet total solar+wind stacked over time, per-ISO or per-State totals, capacity factor curves, and peak/trough hour identification. This is Step 5 (final) of the flagship trail.

## Connections

- **Up:** [Home](../index.md) · time step simulation
- **Across:** prev in flow: [how-to-analyze-results](how-to-analyze-results.md) · [pww-data](../concepts/pww-data.md) · start: [esapp-overview](esapp-overview.md)

## Content

**Step 5 (final) of the flagship trail.** ← prev: [how-to-analyze-results](how-to-analyze-results.md).
Owning project: time step simulation.

This page teaches you to write visualization code for the CSVs that come out of the timestep simulation. The data format is described fully in [how-to-analyze-results](how-to-analyze-results.md); this page focuses on the plotting patterns.

## 1. Load the CSV

The first 8 rows are metadata, everything below is hourly MW data.

```python
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

raw = pd.read_csv("Historical_2025_solar.csv")

# Split metadata from time series
meta = raw.iloc[:8]          # rows: ISO / PV-Wind / Types / Gen Max MW /
                             #        State / Utility / Latitude / Longitude
data = raw.iloc[8:].copy()

# Parse timestamp and cast generation columns to float
data["DateTimeUTCExcelFormat"] = pd.to_datetime(data["DateTimeUTCExcelFormat"])
data = data.set_index("DateTimeUTCExcelFormat")
data = data.astype(float)
```

`meta.columns` gives the generator names (same order as `data.columns`). Pull any
metadata row by its position:

```python
iso_row    = meta.iloc[0]   # ISO assignment per generator
type_row   = meta.iloc[1]   # SUN / WND
maxmw_row  = meta.iloc[3].astype(float)  # Gen Max MW
state_row  = meta.iloc[4]
```

## 2. Fleet total — solar + wind stacked

Load both CSVs and sum across all generator columns for each:

```python
raw_s = pd.read_csv("Historical_2025_solar.csv")
raw_w = pd.read_csv("Historical_2025_wind.csv")

def load_series(raw):
    d = raw.iloc[8:].copy()
    d["DateTimeUTCExcelFormat"] = pd.to_datetime(d["DateTimeUTCExcelFormat"])
    d = d.set_index("DateTimeUTCExcelFormat").astype(float)
    return d.sum(axis=1)   # fleet total MW

solar_total = load_series(raw_s)
wind_total  = load_series(raw_w)

fig, ax = plt.subplots(figsize=(14, 4))
ax.stackplot(solar_total.index, solar_total, wind_total,
             labels=["Solar", "Wind"], colors=["#f4a261", "#457b9d"], alpha=0.85)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylabel("Generation (MW)")
ax.set_title("Fleet Solar + Wind — 2025")
ax.legend(loc="upper left")
plt.tight_layout()
```

## 3. Per-ISO or per-State totals

Group generator columns by a metadata row value, then sum within each group:

```python
def group_by_meta(data, meta_row):
    """Sum generator columns by the value in meta_row (e.g. ISO or State)."""
    groups = {}
    for gen_col in data.columns:
        key = meta_row[gen_col]
        groups.setdefault(key, []).append(gen_col)
    return {k: data[cols].sum(axis=1) for k, cols in groups.items()}

iso_totals = group_by_meta(data, iso_row)    # dict: ISO → hourly MW Series

fig, ax = plt.subplots(figsize=(14, 4))
for iso, series in iso_totals.items():
    ax.plot(series.index, series, label=iso, linewidth=0.8)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
ax.set_ylabel("Solar MW")
ax.set_title("Solar by ISO — 2025")
ax.legend(fontsize=7)
plt.tight_layout()
```

Replace `iso_row` with `state_row` to group by state instead.

## 4. Capacity factor

Divide hourly MW by the `Gen Max MW` metadata row (row index 3):

```python
cf = data.div(maxmw_row, axis=1)   # per-generator capacity factor (0–1)
fleet_cf = cf.mean(axis=1)         # fleet-average capacity factor

fig, ax = plt.subplots(figsize=(14, 3))
ax.plot(fleet_cf.index, fleet_cf, linewidth=0.7, color="#2a9d8f")
ax.set_ylim(0, 1)
ax.set_ylabel("Capacity Factor")
ax.set_title("Fleet Solar Capacity Factor — 2025")
ax.xaxis.set_major_formatter(mdates.DateFormatter("%b"))
plt.tight_layout()
```

## 5. Peak and trough hours

Useful for extreme-scenario screening:

```python
fleet_mw = data.sum(axis=1)

peak_hour  = fleet_mw.idxmax()
trough_hour = fleet_mw[fleet_mw > 0].idxmin()   # exclude zero (nighttime)

print(f"Peak:   {peak_hour}  →  {fleet_mw[peak_hour]:.0f} MW")
print(f"Trough: {trough_hour}  →  {fleet_mw[trough_hour]:.0f} MW")

# Mark on the fleet total plot
fig, ax = plt.subplots(figsize=(14, 4))
ax.plot(fleet_mw.index, fleet_mw, linewidth=0.7, color="#457b9d")
ax.axvline(peak_hour,   color="red",   linestyle="--", label=f"Peak {peak_hour:%Y-%m-%d %H:%M}")
ax.axvline(trough_hour, color="orange",linestyle="--", label=f"Trough {trough_hour:%Y-%m-%d %H:%M}")
ax.legend()
plt.tight_layout()
```

## Trail complete

[esapp-overview](esapp-overview.md) → [timestep-simulation-setup](timestep-simulation-setup.md) → [pww-data](../concepts/pww-data.md) →
[how-to-analyze-results](how-to-analyze-results.md) → **visualize-renewable-output** ✅


---
