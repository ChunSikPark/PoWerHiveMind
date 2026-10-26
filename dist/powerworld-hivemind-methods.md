# PoWerHiveMind - METHODS

# ==== adding-devices-esapp.md ====

---
type: method
domain: tooling
topic: design
aliases: [add-devices, create-devices, createdata, add-buses-branches]
tags: [esapp, powerworld, createdata, device-creation, dcopf, contingency, n-1]
---

# Adding devices to a PowerWorld case via esapp

## Abstract

How to create buses, branches (lines/transformers) and loads in an open PowerWorld case with
`esapp`, then solve a DC OPF and screen N-1. These are the write-side mechanics the read-focused
[esapp-overview](esapp-overview.md) doesn't cover. Read this before writing any transmission-expansion or
what-if code. The main gotcha: `CreateData` **silently no-ops** unless every primary, secondary
and required key field is supplied, and PowerWorld truncates `LineCircuit` (and `ShuntID`) to **2 characters**. All
symbols below were live-verified against the installed package. For switched shunts, a stepped
reactor created on a bus that already has a capacitor may not stay on automatic control, and
`SSRegVolt` is a reading; the target is `DesiredVoltage`.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [esapp-overview](esapp-overview.md) · [esapp-schema-reference](../references/esapp-schema-reference.md) · [powerworld-simauto](../concepts/powerworld-simauto.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The write path: `pw.esa.CreateData` (not the bracket writer)

To create objects, use the SAW script command `CreateData` on `pw.esa`, wrapped in EDIT mode:

> **Why not the bracket writer?** Through esapp 0.1.x it rejected read-only key/status fields
> outright. On **0.2.1 it only warns and writes anyway**, so `pw[GType] = df` can now create
> objects too (EDIT mode, `CreateIfNotFound=True` and a complete key set). `CreateData` is still
> preferred: it states the intent to create, fails loudly on a malformed field list, and does not
> bury a real problem under a `UserWarning: Read-only field(s)` that is usually a false alarm
> (see [esapp](../concepts/esapp.md)).

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

**Always verify the count went up.** Failures are silent, so assert `pw.n_bus` / `pw.n_branch`
increased by the expected amount after creation and raise otherwise. Never solve a partially applied
design:

```python
n0 = int(pw.n_branch)
# ... create branches ...
assert int(pw.n_branch) - n0 == n_expected, "CreateData silently skipped devices — check key fields"
```

### Parallel-circuit IDs: any distinct short string (mind the 2-char cap)

Parallel circuits between the same bus pair need **distinct** `LineCircuit` IDs. Any short
string works: `1`, `2`, `11`, `22`, `33`. The trap is PowerWorld's ~2-char cap. A 3-char ID gets
truncated, so IDs that look distinct can collide: `NE1` and `NE2` both become `NE`, and the second
silently no-ops. Keep circuit IDs ≤ 2 chars and distinct per pair.

**The same cap applies to every 2-character ID, `ShuntID` included.** PowerWorld's field export
describes `ShuntID` (and `GenID`) as a "2 character ... identification field". Seen 2026-09 on a
~10k-bus planning model: `C10` silently became `C1`, the create reported success, the bank existed
under the truncated ID, and the lookup that followed failed on a bank that was really there. Use
short numeric IDs: `1`, or the next free number at that bus. The "count moved by exactly N" guard
above caught it; nothing else did.

> One research pipeline tagged its new circuits with an `N` prefix (`N1`, `N2`) only so its
> own code could detect which devices were new. PowerWorld does not require the prefix.

### Setting a load: write `LoadSMW`

`LoadSMW` is the scheduled ("pure") load value, the constant-power setpoint you specify. `LoadMW` is
the load's actual MW **when it is connected / in service**. To place or change a load, write
`LoadSMW`; read `LoadMW` for the connected value.

```python
pw.esa.CreateData("Load", ["BusNum", "LoadID", "LoadSMW", "LoadSMVR", "LoadStatus"],
                  [bus, "1", 1000.0, 0.0, "Closed"])
```

### Creating a switched shunt: the bracket writer DOES work, and three fields are traps

Measured 2026-09-07 on a ~10k-bus synthetic case (about a thousand existing shunts), adding about ten capacitor banks.

**`ChangeParametersMultipleElement` cannot create a shunt.** It answers `Object not found` for
every row, because it only modifies objects that already exist. Creation goes through the bracket
writer, which, despite the general advice above, works for `Shunt`:

```python
from esapp.components import Shunt
pw.edit_mode()
pw[Shunt] = df          # one row per new bank
pw.run_mode()
assert len(pw.esa.GetParametersMultipleElement("Shunt", ["BusNum","ShuntID"])) - n0 == n_expected
```

**`SSMinMVR` and `SSMaxMVR` are NOT writable.** They are derived from the blocks. Pass them and
esapp 0.1.x raised `Cannot set read-only field(s)`; **0.2.1 only warns, sends the write, and
PowerWorld discards it**, so on 0.2.1 you get a silent no-op instead of an error. Size the bank
through the block instead and read the limits back afterwards to confirm.

Unlike the `Branch`/`Gen` false alarms in [esapp](../concepts/esapp.md), this one is a **true**
read-only: PowerWorld's own `enterable` column is blank for both fields, which is why the write
vanishes. Apply this test whenever you see the warning:

```python
fl = pw.esa.GetFieldList('shunt')
fl[fl.internal_field_name.isin(['SSMinMVR','SSMaxMVR'])][['internal_field_name','enterable']]
```

✅ **Verified live 2026-09-10** (~2,000-bus synthetic case, 157 shunts, build 2026-07-22, esapp 0.2.1):
`enterable` blank for both; `pw[Shunt] = df` with `SSMinMVR = -999.0` raised nothing and left
the value at `-15.0`.

**The block spelling is `SSBlockMVarPerStep` (capital V), and block 0 carries NO `:0` suffix**
(`:1` through `:9` are blocks 1-9). Same for `SSBlockNumSteps`. esapp's own `Shunt.settable()`
settles this. `SSBlockMvarPerStep:0` is tolerated on the READ side, which is how the wrong spelling
survives. PowerWorld accepts an unrecognised field silently, so a misspelled block name leaves a
shunt with capacity, no block definition and no error.

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
solver's initial guess (see [violation-remediation](../demos/violation-remediation.md)).

**Sizing: let PowerWorld measure it, do not estimate.** Install a deliberately oversized continuous
bank, solve, and read back `SSNMVR`. The dispatched value IS the requirement. Then reinstall at
that value (rounded up to a standard bank size) and confirm nothing rails at its own cap, which
would mean the probe truncated the requirement. Required MVAr does not track depth of
violation: on that case a bus needing +0.0335 pu took 10 MVAr while one needing +0.0277 took 50.
System strength at the bus decides it, not how far the bus had sagged.

**Regulation is a deadband, not a target.** With `[SSVLow, SSVHigh] = [0.96, 1.06]`, a bank that
lands the bus anywhere inside that band has no reason to back off, so the final dispatch depends on
where the solve started. If you need provably minimal dispatch, tighten the band; do not shrink
the bank. **Disputed 2026-09-29:** a measurement on a large synthetic regional planning model found
every continuous shunt that was neither at a limit nor at zero sitting exactly on its
`DesiredVoltage`, which reads as steering to a target rather than holding anywhere in the band.
Unresolved; do not build anything that depends on either reading.

### A stepped reactor next to a capacitor reads `AutoControl = NO`

Suspected, not confirmed. Measured 2026-09-29 on a large synthetic regional planning model,
creating one extra shunt record at a bus that already carried an adjustable capacitor.
`AutoControl = YES` in the create call, or written again straight afterwards, or through a script
`SetData`, read back **NO before any solve** for exactly one combination: a **Discrete** record
with **negative** blocks (a reactor) on a bus that already has a capacitor record. No error is
raised. Every other variant held `YES`:

| new record | same bus as a capacitor? | AutoControl after the write |
|---|---|---|
| discrete capacitor (positive block) | yes | YES |
| discrete reactor | no, alone on a neighbouring bus | YES |
| continuous reactor | yes | YES |
| **discrete reactor** | **yes** | **NO** |
| discrete capacitor | yes, beside a continuous **reactor** (2026-09-30) | YES |

The last row is the mirror case, measured 2026-09-30 on the same model at six sites in five
operating conditions. A stepped capacitor added next to an existing adjustable reactor kept `YES`
through creation, a solve and a re-assertion in every case. So the refusal is specific to a stepped
reactor joining a capacitor; mixing directions on one bus is fine. A related observation, also
suspected (2026-10-20, Simulator build 2026-09-25): a new discrete shunt whose `DesiredVoltage` is
0 had `AutoControl` turned back to NO by the next solve, and kept YES once `DesiredVoltage` was set.

A reactor with `AutoControl = NO` never switches, so a capacitor-plus-reactor design built this way
is inert with no warning. **Read `AutoControl` back on every created record, after a solve.** Two
layouts held `YES`, both verified the same day: put the reactor on **another bus in the same
substation**, or make **one record carrying both kinds of block** (block 0 the reactor, block 1 the
capacitor, one switching range). Why PowerWorld resets it is not established; this is the observed
rule.

### `SSRegVolt` is a reading; the voltage target is `DesiredVoltage`

PowerWorld's field catalog describes `SSRegVolt` as *"the present per unit voltage at the
regulated bus"* and marks it not enterable. Writing a setpoint into it does nothing. The target a
switched shunt steers toward is **`DesiredVoltage`** ("Regulated Bus\\Target Value"), with
`DesiredVoltage:1` as an optional separate high-side target. Code that writes `SSRegVolt = 1.04`
as if it were a setpoint has set nothing; the device keeps whatever `DesiredVoltage` it already
had. When a design gives a bank its own switching range, set its `DesiredVoltage` inside that
range, or the bank steers toward a target it can never reach.

### Transformer vs line: you MUST flag it — kV mismatch is not enough

A branch whose two ends sit at different nominal kV is physically a transformer, but PowerWorld does
**not** infer that. `BranchDeviceType` is **read-only** ("determined by other settings"), so a plain
`CreateData` with only line fields lands the device as a `Line` even across a 500→230 kV step. That
bug once put 500/230 transformers into a case as lines. Flag it explicitly with `LineXfmr="YES"`
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

Substations have **no key fields** and are **not needed for DC power flow**, so don't create them for a
DC study. Their lat/lon is only useful for right-of-way / distance (cost) calculations.

### Solving a DC OPF and reading the objective

```python
pw.run_mode()
pw.pflow(method="DC")      # SolvePowerFlow(DC): the case stays DC until an AC method solves
assert (pw[Bus, ["BusPUVolt"]]["BusPUVolt"] == 1.0).all(), "not a DC solve"
pw.esa.SolvePrimalLP()     # the LP OPF on the DC case
tfc = float(pw[OPFSolutionSummary, :]["LPOPFCostFunction"].iloc[0])   # "Total Final Cost"
```

`OPFSolutionSummary.LPOPFCostFunction` is the OPF objective ("Total Final Cost").

Writing the DC flag is not enough. `pw.dc_mode`, `DCApprox` and `DCPFMode` are one field
(`Sim_Solution_Options`), and on 2026-09-23 setting it did not make the next
`SolvePowerFlow()` run DC: an AC method argument (esapp's `pw.pflow()` defaults to
`POLARNEWT`) puts the case back in AC. Solve with the DC method itself and check that every
bus sits at exactly 1.0 pu ([powerworld-study-options](../references/powerworld-study-options.md),
[lodf](../concepts/lodf.md)). Not yet live-tested: that `SolvePrimalLP` keeps the DC model
after a DC solve. The 1.0 pu check after the OPF is the test.

### Overloads: tolerate the binding-at-limit edge

`pw.overloads(threshold=100.0)` returns branches at/over `threshold` percent. The LP OPF **binds lines
to exactly 100.000% of rating** at the economic optimum, and solver float noise then reads
~100.000001% on a line that is fully loaded, not overloaded. Use a small tolerance so a binding
constraint isn't misreported as a violation:

```python
overloaded = pw.overloads(threshold=100.1)   # >100.1% = a real overload; <=100.1% = at-limit
```

### N-1 on new devices — just run the contingency analysis (don't hand-roll it)

PowerWorld's built-in **contingency analysis** applies each outage, re-solves, records
violations/non-convergence, and **restores the base case automatically**. You never open or re-close
anything yourself. Run it in DC by solving the base case with the DC method and setting the
CTG method to `DC`:

```python
# DC contingency analysis
pw.esa.SetData("CTG_Options", ["CTG_CalculationMethod"], ["DC"])
pw.pflow(method="DC")                                                  # DC base case; the flag alone is not enough
pw.esa.CTGClearAllResults()
pw.esa.CTGSolveAll()                                                    # solves all defined contingencies

# read results (per-contingency solve/violation flags + branch loading)
ctg    = pw[Contingency, [Contingency.CTGSolved, Contingency.CTGViol]]   # CTGSolved=="YES", CTGViol>0
branch = pw[Branch, [Branch.CTGViol, Branch.LineMaxPercentContingency, Branch.CTGSolved]]
n_diverged  = int((ctg["CTGSolved"] != "YES").sum())
n_violating = int((ctg["CTGViol"] > 0).sum())
```

The contingencies themselves must exist in the case first. Define one per new device (open that
line/transformer), e.g. via `ContingencyBuilder`/`SimAction` (`esapp.utils`) or by auto-inserting
N-1 branch contingencies. `CTGViol`/`CTGSolved` on the `Contingency` object give per-contingency
violation counts and convergence; `Branch.LineMaxPercentContingency` gives the worst loading seen.

For AC, solve with `pw.pflow()` (an AC method) and set the CTG method to `AC`. Don't write a manual
snapshot→open→re-solve loop; it re-implements, worse, what `CTGSolveAll` already does.

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

> Rules followed here: drive SimAuto via `esapp` (not raw `esa`); always keep an object's key
> field(s) on any write or it silently no-ops (see [esapp](../concepts/esapp.md)).


---

# ==== applying-a-dispatch-to-a-case.md ====

---
type: method
domain: tooling
topic: power-flow
aliases: [applying-a-dispatch, apply-dispatch, dispatch-to-case, scenario-case-build, write-genmw, open-unused-generators]
tags: [esapp, powerworld, simauto, dispatch, scenario, dcpf, genmw, genstatus, slack, load-scaling]
---

# Applying a dispatch to a PowerWorld case (and saving it as a scenario `.pwb`)

## Abstract

How to turn a computed dispatch (a MW number per generator) into a runnable scenario case:
write `GenMW`, switch the unused units `Open`, scale load to the scenario's level, solve DC,
and save. The main gotcha: **the DC solve fakes a balance instead of telling you the
fleet is short.** It pushes the entire deficit through the slack *bus's* generators, past
nameplate, and the resulting branch overloads look like a transmission finding but are a
pure artifact. Verify the schedule against load **before** you trust any flow. Second trap:
esapp's `pw[Obj, field] = values` setter is **positional over the whole object table**, so a
filtered subset writes nothing, silently. Live-verified on Synth9k/Synth8k 2031, 2026-08-18.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [save-powerworld-case](save-powerworld-case.md) (the `SaveCase` no-op trap this depends on) ·
  [adding-devices-esapp](adding-devices-esapp.md) (same key-field discipline, and the `CreateData` silent no-op) ·
  [converting-lines-to-transformers](converting-lines-to-transformers.md) (the other place esapp's static whitelist is wrong) ·
  [case-impedance-completeness](../concepts/case-impedance-completeness.md) (**check this before promising anyone AC** — the cases
  these scenarios are built from are DC-only skeletons) · *Verify it worked* below
  (reopen the saved `.pwb` cold; a save that "succeeded" is not evidence)

## Content

### Steps

1. **Compute the dispatch first, in pure pandas, against a read-only pull.** Keep the
   allocation logic in a module with no `SaveCase` in it, so it can be tested and re-run
   without a license risk. The case write is a separate, dumb step.

2. **Scale load to the scenario level.** Write `LoadSMW` (and `LoadSMVR` by the same factor,
   to hold power factor; DC ignores Q, but the case stays usable later). Do **not** assume
   every load scales. On the 2031 planning cases the few hundred buses named `*_DataCenter` /
   `*_LargeLoad` (about 29% of peak load) are flat 24/7 and are held fixed, so the scenario % applies
   only to the several thousand ordinary loads. That tag lives **only in `Load.BusName`**: `Label`
   and `CustomString*` are empty, and `Interruptible` is `NO` on every record.

3. **Write `GenMW` and `GenStatus` together, as full-length columns.**

   ```python
   pw.edit_mode()
   for col in ("GenMW", "GenStatus"):          # full table, original row order
       s = gens_full[col]
       pw[Gen, col] = s.astype(str).tolist() if s.dtype == object else s.tolist()
   ```

   `GenStatus` is `"Open"` for every unit dispatched to 0 MW. That is how a unit is taken out of
   service for this scenario.

4. **Keep every generator on the slack BUS closed**, even at 0 MW, or the solve has nothing
   to swing. *Bus*, not unit: the slack bus hosts **about a dozen** generators on both the 8k and 9k
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

**Post-solve generation always equals load, so it proves nothing.** If the
scheduled dispatch cannot meet the load, PowerWorld closes the gap by driving the slack bus's
generators as far past their own `GenMWMax` as it takes.

Measured on `Synth8k_draft`, in a high-load, no-solar scenario, short **~31
GW**: each of the generators at the slack bus was pushed **+2,840.8 MW over nameplate** (a
44.5 MW unit landed at 2,885 MW), producing **hundreds of branches over 100% and a 683.4% maximum**.
Those overloads are entirely an artifact of 31 GW injected at one 345 kV bus.

It is **not** AGC doing this. Area AGC status read `0` on all 8 zones, and exactly **1** of roughly
1.5k generators is `GenAGCAble`. (That status was recorded under the nonexistent name
`AGC_AGCStatus`; the area field is `Area.BGAGC`, see [opf-preconditions](../concepts/opf-preconditions.md).)

The check that works, before reading a single flow:

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
filtered subset resolves every record to NAN and writes nothing, with no exception or warning.
Build the full-length column (edit by key into a copy of the full table) and write that. As with
the `CreateData` silent no-op in [adding-devices-esapp](adding-devices-esapp.md), **assert the effect;
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

Five scenarios × two fleets, same loads (~140 GW peak, same ~40 GW fixed block):

| Fleet | Conventional | Outcome |
|---|---|---|
| Synth9k 2031 (post-swap, +thermal) | ~100 GW | **5 of 5 balance at exactly 0.0 MW** |
| Synth8k 2031 draft (pre-swap) | ~65 GW | 3 of 5; **one scenario short ~4 GW, another short ~31 GW** |

The 8k shortfalls are genuine nameplate deficits: the whole conventional fleet runs flat out.
That matches an earlier real-hour dispatch rebuild. The gap is larger here only because the
datacenter block is held at full load while the rest scales down.

**Both base cases are DC-only skeletons** (`LineR ≤ 1e-6` and `LineC == 0` on 97.5% / 100% of
closed lines; median X/R **100,010** and **113,465**), so every scenario case built from them
inherits that and can never carry an AC study. See [case-impedance-completeness](../concepts/case-impedance-completeness.md).


---

# ==== aux-file-mode.md ====

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

This is **PowerWorld and LLM interaction programming**. The agent writes a script, you drop it
in, Simulator runs it and writes back. Both sides read the same artifacts.

That shape has its own advantages, independent of tooling:

- **Everything is inspectable.** The script, the log and the results are all files on disk
  that you can read, diff, archive and send to someone. There is no opaque call whose
  behaviour you have to take on trust.
- **The human is in the loop by construction.** You see every script before it runs. For work
  that edits a case, that is a feature.
- **The deliverable is the script.** The agent produces a `.aux` you keep and re-run
  yourself, not a transcript of an API session that only existed once.
- **No code of yours touches PowerWorld.** Nothing imports a COM library, nothing holds a
  handle on Simulator, nothing can leave it in a state you did not ask for.

### You still write code, it just runs on your side

The log is English prose and the answers are in CSVs, so the caller does real work to find out
what happened, and an agent working this way writes and runs that code constantly. Four jobs:

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

Step 5 matters because the output file appears only once a run finishes. For every failure that
never finishes (an abort, a loop, a poller that is not running) the folder stays silent and the
log is the only thing that says which one you have. A looping run shows the same block of lines
once per poll interval.

Three things here cost time when you do not know them:

- **The settings persist in the registry, the dialog does not.** The panel says so itself:
  its heading reads *External Script Control (Only Active when Dialog is Open; Fields Saved
  in Registry)*. `ScriptTransferFileEnabled`, `ScriptTransferFileDirectory` and
  `ScriptInputOutputPollSec` survive a restart, so the browsing step is once per machine.
- **Tick `Always Delete an Invalid Input Aux File` while you are in there.** It makes
  Simulator discard a script it cannot parse instead of leaving it in the folder to be
  retried. A script can still parse cleanly and fail mid-run, so this does not fully guard
  against the re-execution loop, but it removes the most common cause.
- **Closing the dialog stops the poller while the flag still reads enabled.** The dropped
  file sits there, which looks exactly like a crash, a failed run, and a run still in
  progress. If a drop is not picked up, check the dialog before you debug the aux.

Once the user confirms the setup, the agent should propose a device scan without being
asked, **then stop and wait for an answer:**

> *"Channel is live. I cannot see your case from here. Do you want me to scan it first and
> list what devices are in it? It is read-only, it writes CSVs and changes nothing."*

**Ask which folder. Do not pick one.** The transfer folder is the user's choice. They may
already have one configured from a previous session, they may want it on a particular drive,
and on a shared or managed machine the obvious location may not be writable. Ask, and use the
answer verbatim. `<your transfer folder>` below is a placeholder for whatever they tell you,
not a suggestion.

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

**Propose, then wait. Do not drop the file until they answer.** The user is sitting in front
of a live Simulator with their own case loaded, and a dropped script executes against it the
moment it lands, so the first drop of a session is theirs to approve, even when it only reads.

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
case, not the case as you have edited it. The spec says "the pwb file for the current
case" and means it literally. Unsaved in-memory changes are invisible to it, so diffing two
summaries across an unsaved edit shows no difference, which looks exactly like a change that
never happened. Read the CSVs.

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
Angles differ in the fifth decimal and the slack by about a kilowatt, because Newton–Raphson
converges from the outaged solution instead of the loaded state. **That is solver tolerance,
not a failed restore.** Expecting an exact match will make a correct run look broken.


---

# ==== case-data-lint.md ====

---
type: method
domain: cross-cutting
topic: case-audit
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
fields. It never stops a study. It says what is wrong, where, and whether it looks broken or
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
reports it as *beyond its blocks* instead. Every combination counts, not only in-order switching,
so the check errs towards fewer flags. A shunt with no blocks defined is skipped, because there is
nothing to check it against. A shunt whose blocks give more than 100,000 combinations is not
enumerated. It is listed instead, as an FYI that says it was not checked.

### Emergency ratings: Worth a look or FYI

Rating A with blank B and C is common: the public Texas2k case carries it on all 2,562 of its
rated branches. Whether that matters depends on what the N-1 reads. The rule looks at
`LSLineRateSet:1` in the limit sets in use. If that letter is B or C and the branches lack it,
those branches go unmonitored after an outage, and the finding is **Worth a look**, triaged Broken.
If the N-1 reads A, the blanks are data still to fill, and the finding is **FYI**, triaged Your call.
A rate set the N-1 uses that is empty everywhere is a different, stopping rule: `mon.rate_set_empty`.

### A field that was not read

If the case did not return a field, or it reads blank on every row (a number as NaN, text as empty),
the engine treats it as not read and its rule reports nothing. That happens with an older snapshot,
or with a PowerWorld that lacks the field. The engine lists the rule under `rules_skipped` naming
the field. A rule whose one half could not run is listed as run and as not checked for that half.
Silence from a rule is not a pass.

The one exception is a switched-shunt block slot after the first. PowerWorld leaves an unused slot
blank, so a blank slot column is data, and only a slot the case did not return counts as not read.
A release that returned blank for a slot a shunt really uses cannot be told apart by the data.
`BusName` gets no exception: every name blank reads as a field not returned, so `lint.bus_names` is
listed as not checked instead of flagging every bus.

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
topic: case-audit
aliases: [line-to-transformer, linexfmr, make-branch-a-transformer, branchdevicetype]
tags: [esapp, powerworld, simauto, branch, transformer, linexfmr, editmode]
---

# Converting a PowerWorld branch from Line to Transformer

## Abstract

How to reclassify existing `Branch` objects as transformers when a case models every branch as a
line even where the two ends sit at different nominal kV. Two gotchas, both live-verified on
Synth8k. **(1)** `BranchDeviceType` is derived and read-only; the real switch is `LineXFMR = "YES"`
plus `XFNominalKV`/`XFNominalKV:1`. **(2)** esapp flags every `XF*` field read-only from its own
**static whitelist**, which is wrong: the fields are writable in PowerWorld EDIT mode. On esapp
0.2.1 that flag is only a `UserWarning` and `pw[Branch] = df` works; on 0.1.x it raised and you had
to go around esapp via `pw.esa.ChangeParametersMultipleElement`. With `XFFixedTap = 1.0`
and `LineC = 0`, the conversion is electrically a **no-op** (verified: max |ΔV| = 0.0 pu,
max |ΔMW| = 0.0). It is pure reclassification, with R+jX untouched.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [adding-devices-esapp](adding-devices-esapp.md) · [save-powerworld-case](save-powerworld-case.md) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) · [esapp-overview](esapp-overview.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### When you need this

A case where transmission was built branch-by-branch (synthetic-grid pipelines do this) can end up
with every branch typed `Line`, including the step-down connections. Symptom: `pw.transformers()`
returns empty and `BranchDeviceType.value_counts()` is 100% `Line`, yet many branches have
`BusNomVolt != BusNomVolt:1`.

The mismatched-nominal-kV test is the right detector. Check that the pairs it finds are sane
step-downs before trusting it. On Synth8k the only pairs were 765/345, 345/138, 138/69 (about 12% of branches).

### The two traps

**`BranchDeviceType` is derived.** You cannot set it. It reports `Transformer` once `LineXFMR` is
`YES`. Setting `LineXFMR` alone is the switch; the `XF*` fields are the transformer's parameters.

**esapp's read-only list is a static whitelist, not PowerWorld truth.** It marks every `XF*`
field read-only (`['LineXFMR', 'XFAuto', 'XFNominalKV', 'XFNominalKV:1', 'XFFixedTap',
'XFMVABase', 'XFTapMin', 'XFTapMax', 'XFStep', 'XFTapDegree', 'XFRegMin', 'XFRegMax',
'XFRegBus', 'XFUseLineZ', 'XFPhaseType']`), and PowerWorld disagrees. What that costs you
depends on your esapp version:

| esapp | `pw[Branch] = df` with `XF*` columns |
|---|---|
| 0.1.x | **raises** `ValueError: Cannot set read-only field(s) on Branch: [...]` — the bypass below was mandatory |
| 0.2.1 | **warns** `UserWarning: Read-only field(s) on Branch: [...]` and the write goes through |

✅ **Verified live 2026-09-10** (~2,000-bus synthetic case, Simulator build 2026-07-22, esapp 0.2.1): a
2-row `pw[Branch] = df` carrying `LineXFMR='YES'` raised nothing and flipped
`BranchDeviceType` from `Line` to `Transformer`.

So **on 0.2.1 the bracket writer is the recipe**. Don't run under `-W error::UserWarning`,
which turns that harmless warning back into a hard failure.

### The recipe (esapp 0.2.1)

```python
pw.edit_mode()                     # required — these are EDIT-mode fields
pw[Branch] = df                    # keys + XF* columns; warns, writes
pw.run_mode()
```

`df` must carry the key columns (`BusNum`, `BusNum:1`, `LineCircuit`). The bracket read
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

`LineCircuit` must be a **string** (`"1"`, not `1`). `XFConfiguration` is derived: it self-populates
to `Unknown`, so don't try to set it.

### House defaults (from Synth2k_series2)

All 1351 transformers in `Synth2k_series2_case1` share **identical** settings, so this is the
series' convention:

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
these regulating voltage (e.g. reactive power planning), that is a separate setup (regulated bus
and setpoint scheme) not covered here.

### Verify it was a no-op

With `XFFixedTap = 1.0` the power flow should not move. Solve before and after and assert it:

```python
pw.pflow(); before = pw[Branch, "LineMW"]["LineMW"]; vb = pw.voltage(complex=False)[0]
# ...convert...
pw.pflow(); after = pw[Branch, "LineMW"]["LineMW"]; va = pw.voltage(complex=False)[0]
assert (va - vb).abs().max() == 0.0 and (after - before).abs().max() == 0.0
```

This is guaranteed **only if** the converted branches already had `LineC == 0`. Check that first.
A branch with real line charging **may** move when reclassified, since a transformer's `LineC` is
treated as magnetizing susceptance rather than π-model charging. It may also not: one 2026-10-20
run converted a single branch on a public synthetic case with its `LineC` kept, and the solution
was identical (41.917784% loading before and after). That is one branch, measured once, so run the
before/after assertion above instead of assuming either way. Zeroing nonzero charging is a
modelling decision, not a cleanup; surface it instead of doing it silently.

Then save via the aux script command, never the COM function (see [save-powerworld-case](save-powerworld-case.md)):

```python
pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
assert os.path.exists(out)
```

Reopen the saved file and re-check `BranchDeviceType.value_counts()` to confirm that EDIT-mode
writes which looked fine in-session survived the round-trip.

### Worked application

An 8,000-bus synthetic working model: 13523 branches, all typed `Line`, 1586 with mismatched
nominal kV and all with `LineC = 0`. Converted to 1586 transformers with the table above; power
flow bit-identical; written to `..._xfmr.pwb` (a new file; the source WIP case was left untouched).


---

# ==== diagnosing-a-non-converging-contingency.md ====

---
type: method
domain: synthetic-grid
topic: contingency
aliases: [unsolved-contingency-diagnosis, non-converging-contingency, why-a-contingency-diverges,
  ctg-did-not-solve, reserve-limits, island-reserve-limits, voltage-collapse-n-1]
tags: [synthetic-grid, contingency, n-1, voltage, powerworld, convergence, remediation, islanding]
---

# Method: Diagnosing a non-converging contingency

## Abstract

How to tell **why** an N-1 outage returns "unsolved" (voltage collapse, a bad Newton start, a
real-power infeasibility, an island that cannot balance, or a harness bug) in four probes: check
whether it islands, run a real DC solve, walk the element's impedance to open, and read the P-vs-Q
mismatch where the solver stops while checking that the low-voltage load model is not hiding a
collapse. First read the stop reason: **RESERVE LIMITS** means an island ran out of balancing
units, not a Newton failure. Read this before sizing anything for an unsolved outage; it carries no
violation row to size against.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-n1-contingency-violations](remediating-n1-contingency-violations.md)
  (the loop that routes unsolved outages aside and never fixes them; this page is what to do with
  that pile) · [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  (the fix, once this page says "collapse" or "island") · [lodf](../concepts/lodf.md) (a DC solve
  cannot legitimately fail; islanding detection) ·
  [reading-violationctg](reading-violationctg.md) (`Unsolved` rows carry no element)
- **Traps it depends on:** [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) ·
  [powerworld-study-options](../references/powerworld-study-options.md)

## Content

### Why this needs its own method

An unsolved contingency writes no violation rows and names no element, so a remediation loop
that ranks elements by violation never targets it
([remediating-n1-contingency-violations](remediating-n1-contingency-violations.md)). Measured
2026-09-23 on a ~9k-bus synthetic planning model across five dispatches: a long unattended
remediation loop cleared almost every thermal and voltage violation and moved the unsolved count
by one, incidentally. The unsolved set is its own work item.

### First: an outage that stops at RESERVE LIMITS is an island, not a divergence

Read the stop reason before running any probe. With island handling on
(`Sim_Solution_Options.EvalSolutionIsland` and `AllowMultIslands` = YES, Island rows on in
`CTG_Options`), PowerWorld keeps an energized island and balances it with that island's own AGC
units. When they cannot, it stops at **RESERVE LIMITS** and the outage reads unsolved. That is a
power-balance limit, so probes 2–4 below do not apply.

The **Island Reserve Limits** row in `ViolationCTG` says where it ran out: a bus and an MW. A
positive MW is a shortfall the island cannot cover (deficit); a negative MW is a surplus it cannot
back down, because its units' minimums exceed its load. A third kind sits on the **main grid**: a
plant trips and the remaining AGC units lack the headroom to cover its MW
([agc-participation-factors](../concepts/agc-participation-factors.md)).

What decides it is what the cut-off pocket holds:
- **units and load:** stays energized, and fails whenever its units cannot match its load.
  Measured 2026-10-19/20 on a ~9k-bus synthetic case, every pocket that could not balance had load
  on the cut-off side.
- **units only:** goes dead, and the plant simply trips. The outage solves and writes no row. The
  exception is a pocket holding the system slack, which stays energized and fails on surplus.
- **load only:** the load is dropped. The outage solves; `Contingency.LoadMW` holds the MW
  ([reading-violationctg](reading-violationctg.md)).

So **islanding is not a thermal or voltage violation row.** A dead pocket writes nothing, and a
failed one writes one Island row and an unsolved flag. A count of violations misses both. Find
islands by topology instead (the bridge screen in
[finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)), and fix
them there.

### The four probes, in order

**1. Does the outage island anything?** Remove the element from the closed-branch graph and
check connectivity ([lodf](../concepts/lodf.md)'s denominator gives the same answer for free).
Islanding is a different problem (see above); everything below assumes it does not.

**2. Real-power feasibility: a *real* DC solve.** `RunScriptCommand("SolvePowerFlow(DC)")`
after `CTGApply`. It should converge (a DC solve is linear). If the DC case converges and the
AC case does not, the flows exist and the problem is reactive/voltage. See the trap below: the
obvious way of asking for DC does not run DC.

**3. Impedance walk: separate "no solution" from "a bad Newton start".** Scale the element's
R and X up geometrically (x1.1 ... x10^4), solving at every step from the previous solution, and
record the element flow and the lowest nearby voltage at each step. Then:
- **The walk breaks at some multiplier**: there is no solution beyond it; the pocket's voltage
  falls steadily into the break. That is a voltage collapse; the multiplier is the margin.
- **The walk reaches x10^4 and opening from there converges**: read the voltages before
  believing it (probe 4).
- **The walk reaches open with sane voltages**: the outage has a solution and the sweep's
  failure is the Newton jump from the intact start. Rare; measured once in the example study,
  and it did not reproduce under a different step size.

Near the nose, whether a walk crosses depends on step size. Report the edge ("no solution past
x_k"), not a single crisp number.

**4. Where does the mismatch sit, and is the load model hiding a collapse?** After a failed
solve with `RestoreSolution=NO`, read `BusMismatchP` / `BusMismatchQ`. Measured on every
failing outage in the example: **the real-power mismatch closed by >90 %** relative to the
outage applied on intact voltages (flows reroute as the angles swing), **while the reactive
mismatch grew**, concentrating on the load bus or pocket that collapses. P closes, Q does
not: reactive transfer, not a generation shortfall. Two patterns share that diagnosis:
- the solver **holds voltage near nominal and leaves a large Q hole** at the load bus;
- the bus has **already sagged to ~0.75–0.85 pu** and the mismatch is small: Newton is at the
  nose and cannot take another step.

Then check `MinVoltSLoad` (and `MinVoltILoad`) in `Sim_Solution_Options`. Below that voltage a
constant-power load stops being constant power. A walked outage that "solves" with a bus at
~0.2–0.5 pu has **collapsed with the load model quietly shedding the load**. That is not a
solution.

### What the probes found (example study)

Every unsolved outage in the example was a **voltage collapse in a pocket that one outage left on
a single long tie**. None was an island, a real-power infeasibility, or a thermal overload: nothing
near the collapsing pocket exceeded its rating at the last solvable step. Local generators near
several pockets still had reactive headroom that could not reach the collapsing bus. The fix is
structural:
[finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md).

### Traps, each of which reports success

- **Restoring a saved state may not restore the case you saved.** Suspected, not confirmed: in
  the example study a previous `CTGApply`'s topology survived `LoadState()`, and every later probe
  in the same process measured the previous outage's pocket (an outage far away "showed" the first
  one's collapse). A raw-COM repro (2026-10-21) restored MW and branch status, so the `CTGApply`
  case is unreproduced. But it did **not** restore branches created or deleted in between, nor
  impedance edits (`LineR`), so an impedance walk (probe 3) "undone" by `LoadState` is not undone.
  Possibly by design. Workaround either way: run one outage per fresh
  process, or **fingerprint** before every probe (closed-branch count plus a voltage near the
  element) and stop on a mismatch. A control that only checks "the base still solves" passes this
  bug.
- **`SetData("Sim_Solution_Options", ["DCApprox"], ["YES"])` does not make `SolvePowerFlow()`
  solve DC.** It still runs Newton, so "DC fails" is the AC failure again. Use
  `SolvePowerFlow(DC)` as a script command
  ([powerworld-study-options](../references/powerworld-study-options.md)).
- **`DoOneIteration=YES` does not step Newton through a failure.** Each failed single step resets
  and the same state repeats. The post-failure state is also invariant to `MaxItr` and to the
  optimal multiplier; read it as "where the solver stopped", not as iterate k.
- **A DC solve leaves the AC state slightly moved** (discrete controls land differently on the
  next AC solve). Run it last, or accept a looser fingerprint after it.
- **`CTGRestoreReference` can raise "reference case did not converge"** after a failed solve.
  Restore the element by hand, solve, then call it inside `try`.
- **Labels passed through a text file on Windows carry a trailing `\r`.** PowerWorld trims it,
  so the solve is right, and every result dict keyed on the label silently misses.


---

# ==== emergency-ratings-for-a-synthetic-case.md ====

---
type: method
domain: synthetic-grid
topic: contingency
aliases: [emergency-ratings-for-a-synthetic-case, rate-b-c-design, emergency-rating-design, rate-b-rate-c]
tags: [synthetic-grid, contingency, powerworld, thermal]
---

# Method: Designing emergency ratings (Rate B / C) for a synthetic case

## Abstract

How to give every branch of a synthetic case its own Rate B and Rate C from a reviewer's aggregate statistics
(mean, min, max uplift per voltage class and device type), instead of one flat ratio. Covers the class mapping,
the per-branch draw, why % beats MVA, C >= B, and what must happen after, plus the basis behind any uplift: a planning manual's
Rate 1–5 definitions, a published FAC-008 method, and IEEE 738 / C57.91 on catalogue ratings. Read before setting
any emergency rating.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [remediating-base-case-violations](remediating-base-case-violations.md) (copy the rating
  set when cloning a branch) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the limit set contingency analysis reads) ·
  [timestep-dispatch-into-design-bands](timestep-dispatch-into-design-bands.md) (the same idea for dispatch: match a distribution, not one value)

## Content

### Why not one flat ratio

A flat rule (for example every line B = 1.25 x A, every transformer 1.15 x A, C = B) gives every device of a type
identical headroom. A reviewer reads that as unrealistic, and it is: post-contingency loading in % of Rate B then
ranks branches exactly as % of Rate A does, so the emergency rating adds no information. Vary it at three levels
instead: by voltage class, by device type, and by branch.

### The basis: what each rating means, and where an uplift comes from

**Definitions (a US ISO's public steady-state planning procedure manual, §4.4.1.4).** Rate 1 Normal (continuous), Rate 2 Emergency (2 h),
Rate 3 15-Minute (after a step from 90% of normal), Rate 4 Transformer 2-Hour / Branch Conductor, Rate 5 Relay
Loadability. "By definition, Rate 5 >= Rate 3 >= Rate 2 >= Rate 1 and Rate 4 >= Rate 2 >= Rate 1." Security studies
default to Rate 2. A rating may not exceed its most limiting series element, so terminal equipment caps Rate 1 and
Rate 2. In PowerWorld terms A = Rate 1 (intact case), B = Rate 2 (contingencies), C = Rate 3, hence `C >= B`. **The
manual gives no uplift number.** Each transmission owner sets its own method under NERC FAC-008, so cite a method for
any ratio, never the manual.

**A published FAC-008 method** (one US utility, 2020 revision): bare overhead conductor at 75 °C
normal and 100 °C for a 4-hour emergency, at 40 °C ambient; autotransformers per IEEE C57.91 at 115% for 4 h and
125% for 30 min; generator step-ups given no emergency rating above nameplate. That is the usual source of a flat
"lines a bit over 1.2, transformers 1.15" rule. [Certain, read at source]

**IEEE 738 on the case's own conductors** (calculated 2026-10-18 for a ~9k-bus synthetic case). A synthetic
case's line Rate A usually comes from a catalogue table. Dividing its MVA by √3·kV recovers the classic catalogue
ampacity: 75 °C conductor, 25 °C ambient, 2 ft/s wind, full sun. An IEEE 738 steady-state run at those conditions
reproduces the table within about 3% from 336 to 2156 kcmil. [Likely] What follows from that:
- At the same weather, a 75 → 100 °C emergency step gives **1.22–1.24 × A** across conductor sizes. The tables give
  the same amps per subconductor at every voltage, so one ratio fits every line class.
- **Rate A is optimistic for a 40 °C summer peak.** The same 100 °C emergency at 40 °C ambient gives only about
  1.07–1.13 × the catalogue A. Using that number mixes a weather correction into the uplift; keep the two apart.
- A 125 °C emergency gives about 1.45–1.53 × A, too far without an annealing study.
- Rate C: the IEEE 738 transient from 90% preload up to 100 °C in 15 minutes gives about 1.3–1.6 × A, rising with
  conductor size. Terminal equipment caps it well below that, so the 15-minute rating is set by terminal gear, not
  conductor.

**Transformers.** An IEEE C57.91 thermal model (140 °C hot spot, 35–40 °C ambient, typical parameters, not a
nameplate) gives about 1.25–1.35 for 2 h and 1.19–1.25 for 4 h. A published 1.15 for 4 h sits below that because it
also covers bushings and other parts the model leaves out. **Do not use the ONAN → ONAF nameplate step (about 1.33)
as an emergency factor** if Rate A is already the forced-cooled rating: it counts the same fans twice.
Step-ups: emergency = normal under the method above, and a unit
cannot push more than its maximum output through its step-up anyway. [Likely; the C57.91 parameters are typical
values]

**Why not run IEEE 738 per line for a planning case.** The conductor data carry no temperatures and no emergency
column, so each line's ratio needs assumed temperatures and weather, and the answer reflects those choices more
than the conductor. It also does nothing for transformers, about a quarter of the branches. Per-class bands drawn per
branch (below) give the same spread with stated assumptions.

### Inputs

Per (voltage class, device type), from the reviewer's statistics:

| field | definition |
|---|---|
| uplift % | `100 x (B - A) / A`, and the same for C |
| mean uplift % | the class average; the one number the design must reproduce |
| mean MVA uplift | `B - A` averaged over the class; used as a check only |
| min / max | usually 0 and an extreme tail; **never use them as the band** |

If the statistics carry only mean, min and max, the spread is unknown and any band width is a judgement call. Say so
in the report.

### Mapping a branch to a class

- **Line:** its nominal kV.
- **Two-winding transformer:** the high/low kV pair, with every side at or below 35 kV in one `<=35` bucket.
  Generator step-ups land in `<kV>/<=35`. Pairs the statistics do not list go to an "other pairs" row.
- **Three-winding transformer:** PowerWorld models each winding as a branch to a star bus at 1 kV, so classify each
  winding by its own terminal kV. The `<=35` row is the tertiaries.
- **A class with no statistics** (for example a voltage the reviewer's system lacks) falls back to the nearest
  class below of the same device type. Report every fallback.

Every branch must map to exactly one row. Count the unmatched before writing anything.

### The rule

1. Rate A is never touched.
2. Per branch, draw `p` uniformly in `[0.5 m, 1.5 m]`, where `m` is the class mean %. Use a fixed seed so a rerun
   writes the same ratings. `B = A x (1 + p / 100)`.
3. Draw C the same way from its own class mean, then lift it to at least B: **`A <= B <= C` on every branch**, as
   the rating definitions above require.
4. Skip breakers, jumpers and zero-impedance ties, and any branch with Rate A = 0. List the skipped ones.
5. Overwrite an existing B or C only after saving the originals (keys plus old B and C) as the undo.
6. Read every written rating back, and assert A unchanged and `A <= B <= C`. Ratings are single precision, so the
   tolerance is about 0.05 MVA, not 1e-6.

### Why the band is 0.5x to 1.5x the mean

- **Min to max is useless.** With a 0% floor and an extreme top, a uniform draw lands far above the real mean. The
  top tail also gives a few branches a Rate B so loose they can never overload, which hides real N-1 problems.
- **A band a few points wide is a flat ratio again.** Every device of the class gets nearly the same uplift.
- **0.5x to 1.5x keeps the class mean on average** (a uniform draw centred on it; check the realized mean per
  class) and gives a visible spread. If the statistics include percentiles,
  use the 25th to 75th instead; that is measured, not chosen.
- **Model a share at 0% only if you know the share.** A minimum of 0 says at least one device has B = A, not how many.

### Why % and not MVA

Emergency uplift is thermal, so it scales with device size. A fixed MVA uplift taken from someone else's fleet scales
backwards: tiny on a large unit, huge on a small one. Use the reviewer's mean MVA uplift as a **report-only** check.
Divide it by the mean % and you get the reviewer's implied mean Rate A; compare that with your own class mean Rate A.
A large gap means the two populations differ in size, not that the % rule is wrong. Measured 2026-10-20 on a
synthetic ~9k-bus case: about half the classes matched within about 15%. On the step-up classes, % gave several times
the reviewer's MVA average, because the reviewer's class was mostly much smaller units than the synthetic case's
step-ups.

### When the statistics show mean C below mean B

If every device had `C >= B`, the class mean C % could not be below the class mean B % over the same devices. A lower
C mean therefore means a different population (blank C excluded, for example) or a C column that is not the
15-minute rating. Do not copy it into the case. Force `C >= B` and report how many C draws were lifted.

### After the ratings are written

- **Contingency analysis must monitor Rate B.** Filling B changes nothing if the contingency limit set still reads A.
  The field is `LimitSet.LSLineRateSet:1` (contingency rate set); `LimitSet.LSLineRateSet` is the normal one, and
  no `CTG_Options` field overrides either (Simulator 25 field export). Write the **whole** `LimitSet` row, or
  `SetData` fails on missing key fields ([powerworld-limitset-setdata](powerworld-limitset-setdata.md)). Read it back
  comparing only the letter, since a case with named rate sets returns `B: RATE2`. Then read `Branch.LSLineRateSet:1` (read-only) to confirm what
  each branch actually uses.
- **Keep normal on A and contingency on B, and know what that costs.** With the two set differently, a pre-contingency
  `Branch.LinePercent` divides by A and a post-contingency `ViolationCTG.LimViolPct` divides by B, so the two
  percentages are not comparable. Compare in MVA, or label each percentage with its rating.
- **Rerun the full N-1.** A per-branch draw puts some branches below the old flat ratio, so a violation list built
  against the old limits misses rows. Re-checking only the old violations is not enough.
- **Report the spread** per class: count, min / median / max uplift %, C draws lifted to B, and the MVA check. That
  table is the evidence that the ratings are not unified.

### Restricted statistics

A reviewer's statistics may be restricted to internal review. Your % times your own Rate A gives their number back,
so the band file stays local and out of every shared report; the report shows spread and pass/fail flags, not the
reviewer's values. Banding and widening put a chosen distribution in the case, not their exact table. Whether that is
far enough from the source is the data owner's call.

### Upgrade path

A random draw has no reason behind any one branch's value. If a reviewer asks "why 27% here and 21% there", tie
line uplift to conductor type through the IEEE 738 transient rating (IEEE 738 §4.4.2) and transformer uplift
to IEEE C57.91 loading. At a fixed temperature step and fixed weather the steady-state line ratio barely varies by
conductor (1.22–1.24, basis section above); the 15-minute transient ratio does (about 1.3–1.6, rising with size).


---

# ==== esapp-overview.md ====

---
type: method
domain: tooling
topic: scripting
aliases: [esapp-howto, using-esapp, esapp-getting-started]
tags: [esapp, powerworld, simauto, python, getting-started]
---

# Method: Getting started with ESA++ (esapp)

## Abstract

The entry-point how-to for driving PowerWorld from Python with `esapp`: open a case, read and write data with the bracket interface, solve power flow, inspect results, and use `snapshot()` for safe experimentation. All code snippets are verified against the `esapp` source at `C:\path\to\esapp`. This is step 1 of this reading sequence; for the full API map see [esapp](../concepts/esapp.md).

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](../concepts/esapp.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · step 1 of this reading sequence — next: [timestep-simulation-setup](timestep-simulation-setup.md) · [pww-data](../concepts/pww-data.md) · [how-to-analyze-results](how-to-analyze-results.md)

## Content

**Step 1 of this reading sequence** → next: [timestep-simulation-setup](timestep-simulation-setup.md).

## 0. Prereqs

Windows + PowerWorld Simulator installed (SimAuto is a COM server), and a Python environment
with `esapp` installed (verified on Python 3.13).
See [esapp-environment](../concepts/esapp-environment.md) for the exact environment.

## 1. Open a case

```python
from esapp import PowerWorld
from esapp.components import Bus, Gen, Load, Branch, Shunt, Area, Zone

pw = PowerWorld(r"C:\path\to\case.pwb")   # opens via SAW(..., CreateIfNotFound=True)
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

Bulk `pw[Type] = df` can also create new objects, but only in EDIT mode
(`pw.edit_mode()`) with `CreateIfNotFound=True`, and the DataFrame must carry a complete
key set. A filtered subset is fine: PowerWorld matches rows by key, so writing 3 rows
touches 3 objects (the positional `pw[Obj, field]` form differs; see [AGENTS.md](../AGENTS.md) code rule 2).

On esapp 0.1.x a read-only column made the whole write raise. **On 0.2.1 it only emits
`UserWarning: Read-only field(s)` and the write is attempted anyway.** That warning is
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
`pw.max_iterations = 30`, etc. Not `pw.dc_mode = True` or `pw.flat_start = True`: a
scripted solve ignores both. Use `pw.pflow(method="DC")` for a DC solve and
`pw.flatstart()` for a flat start (see [handling-errors](handling-errors.md)).

## Where to go next

> **Note:** Older repos import `esa`; esapp is the updated, better-documented version of the same thing, so write esapp. (This is a library choice only, unrelated to the TimeStep-vs-Transient-Stability distinction.)

- Run a study over time → [timestep-simulation-setup](timestep-simulation-setup.md) (then [timestep-simulation](../concepts/timestep-simulation.md))
- Pull weather into the study → [pww-data](../concepts/pww-data.md)
- Make sense of the outputs → [how-to-analyze-results](how-to-analyze-results.md)
- Full tool reference (matrices, GIC, network, TS) → [esapp](../concepts/esapp.md)

> esapp symbols on this page validated against `esapp` source
> (`C:\path\to\workbench.py` + `indexable.py`).


---

# ==== finding-and-fixing-radial-by-n1-pockets.md ====

---
type: method
domain: synthetic-grid
topic: contingency
aliases: [radial-by-n1, radial-by-n-1-pockets, weak-pocket-screen, siting-a-second-tie]
tags: [synthetic-grid, contingency, n-1, voltage, topology, remediation, powerworld]
---

# Method: Finding and fixing radial-by-N-1 pockets

## Abstract

A pocket is **radial-by-N-1** when it reaches the bulk grid through two ties and one outage
leaves it on a long, weak survivor. Nothing islands, yet the pocket collapses. This page gives
a whole-case screen that finds them, the siting rules for the new tie (where it must land, and
which ties look useful but do not help), and the in-memory harness that measures candidates.
It also covers the extreme case, a **radial tree** that one outage islands outright, with a
whole-grid bridge screen, tie rules per tree shape, and why shared tree-to-tree ties mostly fail.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [violation-remediation](../demos/violation-remediation.md) (the
  diagnose-then-test loop this complements) · [lodf](../concepts/lodf.md) (the islanding
  screen this one extends past) ·
  [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md) (why a radial
  EHV tree also runs high, and what a tie does to it) ·
  [violation-network-map](violation-network-map.md) (the radial-ties map page draws the bridge
  screen below) · [reading-violationctg](reading-violationctg.md) (getting PowerWorld's own
  islanding result)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md)

## Content

### The shape

Two shapes showed up, both measured 2026-09-23 on a synthetic ~9k-bus planning model:
- **A large load tap with one real 138 kV feed.** Its "second path" is a step-down to 69 kV that
  cannot carry the load. It passes a screen for "radial at its own voltage level" because a
  second path exists, at the wrong voltage.
- **A string of substations fed from both ends.** Any link of the string, or either end feed,
  leaves part of the string hanging from the other end. One pocket has several failing outages,
  so site one fix, not one per outage.

In both, the reactance from the collapsing bus to the 345 kV+ grid rose roughly x2.5–x14 when the
outage opened, and a capacitor could not save it. A bus heading to 0.2–0.5 pu gets a few
percent of a shunt's nameplate, so a shunt is the wrong instrument here.

### Screen: find them in the whole case, linearly

1. **Ground = buses on the >= 300 kV *line* network.** Not every >= 300 kV bus: a stub 345 kV bus
   (the high side of a step-up, with no 345 kV line out) can sit *inside* a pocket, and
   grounding it makes the whole pocket look stiff. Local generator buses are not ground either:
   the units near failing pockets were at their limits during the collapse.
2. `B` = the X-only Laplacian of closed branches over the non-ground buses; factorise once.
   `Z_kk` from `B^-1` is each bus's Thevenin reactance to the EHV grid.
3. Opening branch `(i, j, x)` is a rank-1 change. With `w = Z e_ij` and `d = x - (w_i - w_j)`:
   `Z'_kk = Z_kk + w_k^2 / d` for every bus at once (`d -> 0` means the outage islands).
4. A bus is **stranded** when `Z'_kk >= 1.8 x Z_kk` and `Z'_kk >= 0.15` pu. Stress index
   **SI = (pocket |S_load| + pocket zero-Q generation MW) x max Z'_kk** (pu, 100 MVA base).
   Count zero-Q generation: its MW rides the surviving path just like load, and it brings no
   voltage support. A radial reactance `X` delivers ~`V^2/2X` at unity power factor, so SI of a
   few tenths is already near a nose.
5. Rank, then **AC-check the top of the list** in every dispatch (`CTGApply` + one solve).

Validation, same model: the screen ranked **every** known failing outage in its top 13 of ~900
flagged. Its first two versions missed most of them (one by grounding stub 345 kV buses, one
by a 2.5x gate that a failing tap sat just below), so check a screen against known failures
before trusting its silence. The AC check of the next 40 flags found **no new divergence** and a
short watchlist at 0.90–0.93 pu. The screen ranks margin; it does not predict failure alone.

### Siting the fix

- **A tie back into the pocket does not help the end-feed outage.** For a string whose only
  source sits at one end with zero reactive capability, a tie into the middle of the string
  fixed every outage *along* the string but not the loss of the end feed. That one needed a
  second way **out of the source's bus to a substation outside the pocket**. Two lines, one
  mid-string and one exit at the injection, closed all of them. Giving the zero-Q unit ±0.95 pf
  capability alone fixed only half: a pocket with generation can still collapse when that
  generation is modelled with no reactive capability.
- **Land on the meshed grid, never on another load pocket.** Candidate landings: a 138 kV
  substation outside the pocket that stays in the main grid with the pocket removed, with >= 2
  ties, not itself a large-load or data-center tap.
- **Check what the landing depends on.** A landing whose strong tie runs to the same substation
  as the pocket's existing feed passes every *branch* outage and fails the single-substation
  test. Read the landing's own ties before choosing it.
- **Search geography, not the hop extract.** A good landing can be close as the crow flies and
  7–11 substation-hops away through the network; a neighbourhood built by hop count misses it.
  Delaunay 1–3 neighbours over every substation, within a reach cap.
- **Rate the template to clear the load**, then pick by length. A new tie's impedance decides
  its own flow, and it can carry most of the load even intact: measured up to ~94 % on one where
  the old feed was twice as long.

### Islanding trees: the whole-grid bridge screen

When one outage **islands** a pocket instead of weakening it, the screen is pure topology and needs
no solve:

1. Build the **substation** graph from in-service inter-substation branches, keeping parallel
   circuits as separate edges so a double circuit is never a bridge. Put 3-winding star buses in the
   substation their windings reach, since they carry no substation of their own.
2. Find the **bridges** (Tarjan, iterative; the graph is too deep for recursion). The largest
   2-edge-connected piece is the **meshed core**.
3. Root the bridge tree at the core. Each bridge hangs a **pocket** (everything on the far side),
   and nested bridges along one branch group under the tree's **attachment** bridge. Tag each tree by
   the attachment bridge's kV and total the load and generation it strands (worst dispatch).

This screen leaves out two things on purpose, both better handled elsewhere:
- **Transformer-only islanding inside a substation** (a generator step-up, a load hung on its own
  split bus behind one short line). The split-bus load is a modelling convention on many synthetic
  cases, touches nearly every load, and is treated here by convention as **consequential load loss**
  instead of a violation. The fix for an internal split bus is a second bus tie, not a line.
- **Radial 69 kV taps**, which are ordinary sub-transmission design.

**Check it against PowerWorld's own islanding result before trusting its silence.** Measured
2026-09-28 on a synthetic ~9k-bus planning model: the screen listed every between-substation
islanding outage at 138 kV and above that a full N-1 with islanding reporting found, and missed none.
How to get that N-1 result is on [reading-violationctg](reading-violationctg.md); the island option
alone reports nothing.

**What it found there**, as shapes rather than counts: a few percent of substations sit in radial
trees; at 345 kV the stranded MW is almost all **generation on a single line**, at 138 kV mostly
**load taps**. So the islanding problem at EHV is a plant-connection problem.

### Siting a tie for an islanding tree

The radial-pocket rules above still hold: land on the meshed core, never on another pocket, and check
what the landing depends on. The tree shape adds four:

- **A chain takes one tie, from its far end.** A tie from the dead end back to the core makes every
  bridge on the way a loop. Do not start it at the plant just because the plant is there.
- **Start at the plant only when the plant's path to the far end is weaker than the plant.** On two
  345 kV plant trees whose substations were joined by a **138 kV** line, the far-end tie pushed the
  plant through that line at **1.4–2.0x its rating** when the plant's own exit opened. Tie from the
  plant instead, and then the far end, on the other side of the plant, needs **its own** tie.
- **A branching tree needs a tie per branch.** A hub with two spokes and one exit cannot be closed by
  one line; the leftover spoke islands whatever else is built.
- **Spread the landings.** Two ties from one tree into the same substation, or a new tie onto a
  substation that already feeds another tree, stacks several plants behind one station: it passes
  every single-branch outage and fails the substation outage. It also concentrates new line charging
  where a light-load region may already sit high (see
  [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md)). Prefer a landing
  that shares nothing with the tree's existing feed.

A tie is a same-voltage line between two existing buses with no transformer, so the source and the
landing must both already have a network bus at the tree's kV.

### Fewer lines: shared ties, and why most fail

Pairing dead ends is the textbook way to use fewer lines: one line between the ends of two trees
that hang off **different** core substations gives each the other's feed as its second path, so the
minimum is about half the number of dead ends (2-edge-connectivity augmentation). On topology alone,
with pairs limited to 40 mi, that cut the line count by about a third.

**The AC check takes most of it back.** Measured 2026-09-28, same model, five dispatches: about one in
five topology-chosen shared lines failed, two ways.

- **The partner's bridge carries both plants.** With tree A's exit open, A's output leaves through
  B's single bridge on top of B's own — measured up to **2.4x** rating.
- **The middle of a chain stays radial.** Joining the *ends* of two chains leaves the substations
  between each end and its feed still hanging on one line.

Built only from lines that passed all five dispatches on their own, the shared-tie portfolio used
about **20% fewer lines than one tie per tree for about 4% more miles**, every tree closed. The best
shared ties join two generation trees a short distance apart whose feeds are strong. **Measure the
portfolio's lines one at a time before believing its count.** The greedy that picks them cannot see
flow.

### Measuring candidates in memory

Build each candidate as a template same-kV line (R/X/B scaled by miles, rating copied) in the
open case ([adding-devices-esapp](adding-devices-esapp.md)), solve N-0, apply each target outage
the way the sweep does (`CTGApply` + one solve from the intact solution), and read convergence, the
lowest pocket voltage and the worst pocket loading. Then undo and **fingerprint** (closed-branch
count + a pocket voltage) before the next candidate. Undoing a cloned transformer by opening it
failed to restore the case once, and only the fingerprint caught it. Pass = converges, pocket >=
0.90 pu, nothing over Rate A, in every dispatch. Confirm the winner with PowerWorld's own
`CTGSolve` on the label, then a full N-1 with the new lines' own contingency records.


---

# ==== fixing-plant-islands-from-single-outages.md ====

---
type: method
domain: synthetic-grid
topic: contingency
aliases: [plant-islanding-screen, islanding-screen, direct-345, resource-island-screen, single-outage-islands]
tags: [synthetic-grid, contingency, n-1, islanding, topology, gsu, remediation, powerworld]
---

# Method: Finding and fixing plant islands from single outages

## Abstract

A topology screen, independent of dispatch, that finds every single outage cutting a generating plant off the
grid, sorts the cut-off pockets into four shapes, and fixes the shapes that fail. It rests on one rule: a pocket
with units and load stays energized and fails to balance, while a pocket with units only goes dead.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md) (what a RESERVE LIMITS stop means) ·
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md) (the load-pocket sibling: one outage leaves a weak tie) ·
  [removing-empty-buses](removing-empty-buses.md) (cut-offs that strand nothing) · [gsu-outages-in-n1](../concepts/gsu-outages-in-n1.md) (the step-up outages this
  screen leaves to the generator-outage question) · [reading-violationctg](reading-violationctg.md) (`Contingency.LoadMW`, Island rows) ·
  [lodf](../concepts/lodf.md) (the same cut test from the PTDF side) · [agc-participation-factors](../concepts/agc-participation-factors.md) (who balances the main grid)

## Content

### The rule the screen rests on

When one outage cuts a pocket off the grid, what happens next depends on what the pocket holds:

| Pocket holds | What PowerWorld does | Shows up as |
|---|---|---|
| units only | the pocket goes dead; the plant trips | a solved outage, no row. The main grid must cover the lost MW |
| units and load | keeps it energized and balances it with the pocket's own units | unsolved at RESERVE LIMITS when they cannot ([diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md)) |
| load only | drops the load | a solved outage; `Contingency.LoadMW` > 0 ([reading-violationctg](reading-violationctg.md)) |
| nothing | nothing | nothing (an empty bus, or a 3W bank's own star and tertiary) |

A units-only pocket fails only when it holds the system slack, so give the slack two paths first (see
[gsu-outages-in-n1](../concepts/gsu-outages-in-n1.md)). Measured 2026-10-19/20 on a ~9k-bus synthetic case, five dispatches: **every pocket
that could not balance had load on the cut-off side**, and no pocket without load failed.

### The screen: topology only, every single outage

1. Build the graph of closed branches. A 3W bank is three windings meeting at its star bus, and its outage opens
   all three.
2. For each outage, remove its element and find what is cut off from the piece that holds the slack.
3. Label each cut-off piece by what it holds (table above). Drop a 3W bank's own dead star and tertiary before
   counting: they are cut off by the bank's own outage and strand nothing.
4. Keep the pieces with units ("resource islands"), and group outages that strand the same plant into one fix
   group, keyed by the substation that connects the plant to the grid.
5. Leave out the outage of a single step-up (GSU) feeding a single unit: that is a generator outage. A step-up
   feeding several units is also a generator-outage question ([gsu-outages-in-n1](../concepts/gsu-outages-in-n1.md)), so list those plants apart.

It needs no solve, so it runs in seconds and holds for every dispatch on the same network. Run the AC check only
on the candidates. On the case above, roughly one single outage in sixty stranded at least one unit, and grouping
by plant roughly halved the list.

**Re-derive it once before applying fixes.** An independent rebuild from the written spec matched the original
outage for outage (2026-10-20), and it caught three definitions that read wrong:
- A cut-off with no unit is not automatically "pure load". Some have no load either.
- "MW exposed" is ambiguous. The largest outage per substation counts a plant once; a sum over outages counts it
  once per outage that strands it. Say which one.
- "Failed" must include islanded load, not only unsolved outages. A pocket whose only unit is a battery at 0 MW
  is pure load in that dispatch, and the outage solves while quietly dropping a few MW. Read `Contingency.LoadMW`.

### The four shapes

Classify each fix group by the bus between the plant's step-ups and the grid (the "middle bus": a cut-off bus that
is not a unit terminal, star or tertiary). Shares are from the case above:

| Shape | Share of groups | Failed to balance | Fix |
|---|---|---|---|
| A: empty 138 kV middle bus behind one 345/138 transformer | ~2 in 5 | none (the plant just trips) | Direct 345, or accept the plant trip |
| B: the 138 kV middle bus carries load | ~1 in 5 | all of them | move the load to the GSU low side, then Direct 345 |
| C: plant on a bus fed by one line | ~1 in 4 | about a quarter: small battery or solar plus a few MW of load | second line or tie, measured |
| D: other shapes | ~1 in 6 | rare | its own design |

### Direct 345 (shape A)

Remove the empty 138 kV bus and its 345/138 transformer, and connect each plant step-up straight to the 345 kV bus:

- **Move each GSU's high side** to the 345 kV bus (PowerWorld `Move`, so the record keeps its rating, tap, lock and
  contingency element).
- **Keep the series impedance:** new GSU impedance = GSU + removed transformer / w, where w is that GSU's share of the
  plant's total GSU MVA. With several GSUs, the added parts in parallel sum back to exactly the removed transformer.
  For a 3W bank, add its high and 138 kV windings and ignore an idle tertiary.
- **Keep the GSU tap.** Do not multiply it by the removed transformer's tap. That tap was mostly an LTC position
  holding the removed bus, and the two transformers face opposite ways, so the product is not the series ratio.
- **Regulation:** units that held the removed bus now hold the 345 kV bus at the case's 345 kV setpoint rule. If
  another plant already holds that bus at a different setpoint, keep that setpoint: two regulators on one bus must
  agree.
- **Contingencies:** delete the removed transformer's outage and relabel the moved GSUs' outages to their new ends.

Measured on the case above, at the 345 kV setpoint rule: the largest base-case voltage rise was about 0.02 pu, no
bus went above 1.05 pu, and every Direct 345 group passed in all five dispatches.

### Middle bus with load (shape B)

Here the 138 kV middle bus holds the step-ups, one small load and the 345/138 transformer, and nothing else. Move
the load to the low-voltage side of the largest unit's GSU (same MW, Mvar, ID, status and zone), then apply Direct
345. The transformer outage that islanded the pocket no longer exists. Each moved GSU's outage now trips a unit and
its load together, which solves. **Moving load needs the case owner's go-ahead.**

Checked on the case above (2026-10-20): total load unchanged to 0.000 MW, every outage within two substation hops
of a change solved before and after, and no new or worse violation in any dispatch.

### Line-fed and other shapes (C, D)

Measure options rather than reasoning about them: a second transformer, a tie line to a nearby substation, a second
circuit, a second jumper. **Pass** means the group's outage solves in every dispatch and nothing new appears: no new
or worse violation, no newly unsolved outage, nothing new in the base case. On the case above, about nine options in
ten passed in all five dispatches. Accept a plant-only trip as a generator loss; it is not an islanding defect.

### Re-screen after any AGC or dispatch change

Pass and fail depend on who can balance a pocket. Batteries on AGC balanced several small battery pockets; after
batteries were taken off AGC (no state of charge, see [agc-participation-factors](../concepts/agc-participation-factors.md)), those pockets failed again.
Re-run the AC check on every candidate whenever the AGC set or the dispatch changes.


---

# ==== handling-errors.md ====

---
type: method
domain: tooling
topic: scripting
aliases: [handling-errors, error-handling, troubleshooting, recovery, agent-errors]
tags: [errors, troubleshooting, recovery, agent-behaviour, powerworld, esapp]
---

# Method: Handling errors without bothering the user

## Abstract

What to do when something fails. The agent can recover from most PowerWorld failures
alone, so recover and keep going. The user asked for an analysis, not a running
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

The default is tier 1. Escalating a tier-1 problem to the user is itself a failure.
"Should I install pandas?" does not need a human.

---

### Tier 1 — fix it yourself, say nothing

**A package is missing.**

```
ModuleNotFoundError: No module named 'esapp'
ModuleNotFoundError: No module named 'win32com'
ModuleNotFoundError: No module named 'pandas'
```

Install it and carry on. `pip install esapp`, `pip install pywin32`,
`pip install TeamOverbyeWeather`. If `pip` itself fails on permissions, retry with `--user` before escalating.

**You used the wrong access path.** These are the common ones, all verified:

| You wrote | Correct | Why |
|---|---|---|
| `pw.RunScriptCommand(...)` | `pw.esa.RunScriptCommand(...)` | The SAW wrapper is on `.esa` |
| `pw.overloads` | `pw.overloads()` | It is a method |
| `pw.flows`, `pw.ptdf`, `pw.lodf`, `pw.ybus` | all methods — call them | Same |
| `pw.dc_mode(True)` or `pw.dc_mode = True` | `pw.pflow(method="DC")` | `dc_mode` is not a method, and assigning it does not make a scripted solve run DC (see *Power flow did not converge* below) |

**A field name is wrong.** Do not guess a second time. Ask PowerWorld for the field list and look:

```python
fl = pw.esa.GetFieldList('branch')
print(fl[fl.internal_field_name.str.contains("mva", case=False)].internal_field_name.tolist())
```

Don't read every field with `pw[Branch, :]` to find a name: on some cases that read hits a suspected access
violation (glitch `2026-10-20-savedata-all-field-av`).

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

No exception handler will catch this.

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

**The recovery changed what the answer means.** A real example on Hawaii40:

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

A second failure hides inside the first. On this case the largest generator and the
largest load are **the same bus**, so the naive recovery reproduces the original error.
Force the buses to differ.

Report it, because the answer now means something different to the user: *"the case has
a single area, so I computed a bus-to-bus PTDF from bus 23 to bus 26 instead"*.

**Power flow did not converge.** Escalate through the ladder, do not give up at step 1:

```python
pw.pflow(method="POLARNEWT")     # default
pw.pflow(method="RECTNEWT")      # different formulation
pw.flatstart(); pw.pflow()       # reset the starting point, then re-solve
pw.pflow(method="DC")            # DC, if the study tolerates it
```

Do not reach for `pw.flat_start = True` or `pw.dc_mode = True` here. PowerWorld ignores the
`FlatStart` option on scripted solves, and on 2026-09-23 setting the DC flag alone did not
make the next solve run DC. `pw.flatstart()` runs `ResetToFlatStart`, which with its defaults
also resets generator voltage setpoints to 1.0 pu
([powerworld-study-commands](../references/powerworld-study-commands.md), from PowerWorld's manual). `pw.pflow(method="DC")` leaves the case in
DC mode until an AC method solves it again.

If only the DC solve converges, **say so**. A DC answer is not an AC answer.

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

Track which pages you used and cite them when you finish, so a wrong answer points at a
page that needs fixing rather than at "the AI got it wrong."


---

# ==== how-to-analyze-results.md ====

---
type: method
domain: cross-cutting
topic: timestep
aliases: [analyze-results, results-analysis, post-processing]
tags: [powerworld, analysis, post-processing, csv, solar, wind, renewables]
---

# Method: Writing code to analyze timestep-simulation results

## Abstract

How to write code that reads and analyzes the solar/wind generation CSVs produced by the timestep simulation. Covers the two-CSV-per-run naming convention, the 8-row metadata header layout (ISO, fuel type, PFW model string, max MW, state, utility, lat, lon), why the pipeline's UTC labels run early (PowerWorld's raw export is already UTC), and typical pandas reductions for fleet profiles, capacity factors, and regional totals. This is step 4 of this reading sequence; to plot the results see [visualize-renewable-output](visualize-renewable-output.md).

## Connections

- **Up:** [Home](../index.md) · [timestep-simulation](../concepts/timestep-simulation.md)
- **Across:** step 4 of this reading sequence — prev: [pww-data](../concepts/pww-data.md) · next: [visualize-renewable-output](visualize-renewable-output.md) · start: [esapp-overview](esapp-overview.md) · [timestep-simulation-setup](timestep-simulation-setup.md)

## Content

**Step 4 (final) of this reading sequence.** ← prev: [pww-data](../concepts/pww-data.md) · start over:
[esapp-overview](esapp-overview.md).

Once [timestep-simulation-setup](timestep-simulation-setup.md) has produced the output
CSVs, this page covers how they are structured and how to read and reduce them. It
covers the **solar/wind generation files**, not a network or contingency report.

### What the simulation produces
Each run writes **two CSVs**: one solar, one wind. Naming:

| Run type | Solar file | Wind file |
|---|---|---|
| Historical (a full year of quarter files) | `Historical_2025_solar.csv` | `Historical_2025_wind.csv` |
| Forecast (a single `.pww`) | `Forecast_..._solar.csv` | `Forecast_..._wind.csv` |

### File layout (8 metadata rows, then hourly data)
`process_results(gen, df)` in the results post-processor's module builds each CSV. The first column is
`DateTimeUTCExcelFormat`; every other column is one renewable generator. The file
opens with **8 metadata header rows**, then the hourly time series. The header rows,
in order, come from these generator fields:

| Header row | Source field |
|---|---|
| `ISO` | `CustomString:2` (assigned by the ISO-assignment step) |
| `PV / Wind` | `GenFuelType` (`SUN` / `WND`) |
| `PV / Wind Types` | `TSPFWModelString` (the PFW model on the unit) |
| `Gen Max MW` | `GenMWMax` |
| `State` | `ZoneName` |
| `Utility` | `AreaName` |
| `Latitude` | `Latitude` |
| `Longitude` | `Longitude` |

Below the header rows, each data row is one UTC hour and each cell is that
generator's MW for that hour. The time conversion has already run, and its labels are
marked UTC but run early. Read *Timestamps* below before joining this CSV to anything
on time.

### How the values get there
- **Timestamps:** PowerWorld's **raw** export (`TimeStepSaveResultsByTypeCSV`) writes
  column 0, `DateTimeUTCExcelFormat`, as Excel-serial days in **UTC**, not Central time.
  Measured 2026-10-20 on Simulator build 2026-09-25: over a loaded `05:00Z`–`04:00Z`
  window the column matched `Timepoint.TimeDomainDateTimeUTC` row for row, and solar
  output started at 13:00Z. `Timepoint.TimeDomainDateHour` is the field that carries the
  case's local clock. Not yet shown: other builds, and cases set to a time zone other
  than Central.
  `time_utils.convert_to_utc` treats the column as CST: it subtracts 6 h, then 1 h more
  inside US DST (second Sunday in March → first Sunday in November), rounds to the hour,
  and writes ISO-8601 strings marked `Z`. On a UTC input that files every value **7 h
  early in summer and 6 h early in winter** (7 h measured 2026-10-14; the winter figure
  is read from the code). The MW values are right; only their hour labels are wrong.
  Before joining these CSVs on time, re-label them from `Timepoint.TimeDomainDateTimeUTC`
  after checking the row counts match, or add 7 h inside DST and 6 h outside.
- **Solar vs wind split:** columns are matched to generators whose `GenFuelType`
  contains `SUN` (solar file) or `WND` (wind file), keyed by `'BusNum' 'GenID'`.

> **Note on forecast pre-processing:** `interpolate_to_hourly` exists in
> `time_utils.py` for forecast pre-processing but is NOT invoked by the current run
> path (the results post-processor's module / `process_results` / the pipeline's CLI entry script).

### Reading / analyzing the CSVs
The first 8 rows are metadata, so split them off when loading:

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

### When the run also feeds a loading or N-1 study
Report the **intact (no outage) per-hour branch loading first**: the worst hour and its
percent, read as `max(LinePercent, LinePercent:1)` ([reading-violationctg](reading-violationctg.md)).
Then any N-1 results. A 2026-10-20 run that reported only post-contingency rows missed an
intact 141% overload.

### File the answer back
Per [AGENTS](../AGENTS.md), save notable
comparisons or charts as a new `concept`/`method` page, and link it from
[timestep-simulation](../concepts/timestep-simulation.md) and [index](../index.md).

### Next

Plot the results → [visualize-renewable-output](visualize-renewable-output.md)

### Trail complete
[esapp-overview](esapp-overview.md) → [timestep-simulation-setup](timestep-simulation-setup.md) → [pww-data](../concepts/pww-data.md) →
**how-to-analyze-results** → [visualize-renewable-output](visualize-renewable-output.md) ✅


---

# ==== ltc-regulation-checks.md ====

---
type: method
domain: cross-cutting
topic: case-audit
aliases: [ltc-regulation-checks, ltc-regulated-bus, XFRegBus, XFRegTargetType, SSRegNum,
  regulates-nothing, ltc-middle-target, ltc-regulates-lv-side, repoint-the-regulator,
  ltc-causes-violation, which-bus-does-the-ltc-hold]
tags: [powerworld, esapp, transformer, ltc, tap, switched-shunt, voltage, case-quality,
  validation, remediation, n-0]
---

# Checking what each LTC and switched shunt actually regulates

## Abstract

A case can carry a full fleet of live load tap changers (LTCs) and still control voltage badly.
Switching the LTCs on decides little. The outcome turns on **which bus each one holds and how
it drives toward its band**. Three defects are common, and each one leaves
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
`XFTapMin`) with a non-zero `XFRegError` is actively pushing the bus out of band.

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
correct form is `new_tap = old_tap × (v_target / v_measured)`. Re-measure on each new case
family whether the tap sits at the `XFNominalKV` end or the `:1` end.

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
   pulling down the load bus behind it, from about 0.94 to about 0.89, in every dispatch,
   including one that had been clean. Both sides were already low, so there was nothing to borrow. That floor was a
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
topic: contingency
aliases: [contingency-aux, ctgautoinsert, bgreportlimits, monitored-areas, ctgelement-subdata, new-device-contingency]
tags: [esapp, powerworld, simauto, contingency, aux, n-1, limit-monitoring, areas, synth2k]
---

# Building a Contingency Set for Chosen Devices, and an AUX That Carries It

## Abstract

How to turn **a list of devices** (e.g. the branches and generators that are new in a
planning case) into a PowerWorld contingency set, restrict violation reporting to **the
areas you care about**, and ship both as one `.aux` file that loads into the case, without
ever saving the case. The mechanism is **autoinsert-then-restrict**: run the case's own
`CTGAutoInsert`, match your devices to the labels it produced, and write only those out.
Hand-writing `Contingency` records from scratch invents labels PowerWorld would not use.

Five things here are silent failures, each live-measured on `Synth2k_case` on 2026-08-17.
Each produces a plausible wrong answer instead of an error:

> **`ElementType`, `DeleteExisting` and `Handle3WXF` are *concise* names.** PowerWorld's
> object-field export lists two names per field, and these three appear only in the Concise
> Variable Name column. Grep the export for them and you find nothing, which reads as "the
> field does not exist". Their full variable names are `CtgAutoInsElementType`,
> `CtgAutoInsDeleteExistCtgs` and `Include3WXfifFoundWithXf`. Both spellings are accepted;
> search the export on either column before concluding a field is missing.

1. **`CTG_AutoInsert_Options` rejects `ElementType=GEN` without complaining** and leaves it
   at `BRANCH` (suspected, possibly by design: glitch `2026-10-20-ctgautoinsert-gen-ignored`). You ask for 743 generator outages and get 3,911 branch ones.
2. **The `CTGElement` SUBDATA action string must be quoted.** Unquoted, PowerWorld parses
   the *first* contingency and drops the other 690 with no error.
3. **`LoadAux` needs an ABSOLUTE path.** A relative one resolves against `pwrworld.exe`'s
   working directory, not yours.
4. **`LoadAux` merges, it does not replace.** Loading a contingency list into a case that
   already has a set gives you both.
5. **`Ctg_Options.CTG_ReportMonitoredAreas` is a decoy.** It only affects text-file report
   writing. The real area switch is `Area.BGReportLimits`.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Input from:** [comparing-planning-cases](../demos/comparing-planning-cases.md) — produces the device list this method turns into a contingency set
- **Across:** [reading-violationctg](reading-violationctg.md) (what you read back after solving this set) ·
  [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the limit *thresholds*; this page is the limit *scope*) ·
  [save-powerworld-case](save-powerworld-case.md) · [adding-devices-esapp](adding-devices-esapp.md) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md)
- **Deeper:** [aux-script-commands](../references/aux-script-commands.md) for the SCRIPT actions.

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

> **On Simulator 25, build dated 2026-09-25, this exact block inserted 0 contingencies and
> reported success.** Suspected PowerWorld issue, not yet confirmed: the cause may still turn
> out to be a setting. The workaround below holds either way. The condition is
> `CTGAutoInsert` run straight after `Delete(Contingency)`. Measured 2026-10-19 on a public
> synthetic grid. The same block gave the full branch set on 2026-08-17 (the counts below),
> so the behaviour changed with the newer build, not through misuse.
> [powerworld-study-options](../references/powerworld-study-options.md) saw zero inserts on a
> Simulator 25 build on 2026-09-28 as well.
>
> **Assert the count. Never trust the return.** Read `Contingency` back after every
> `CTGAutoInsert` and fail on zero, or on any count far below the case's in-service branches
> above 69 kV. When it comes back empty, build the set yourself. Write the contingency aux
> in the Step 3 shape, one record per branch, with every `CTGElement` action string quoted.
> `LoadAux` it with an absolute path, then assert the loaded `CTGLabel` count equals the
> number you wrote. That path worked on the same build. Your labels will not be
> autoinsert's, so match devices by unordered bus pair plus circuit (Step 2), never by label.

`ElementType` is `BRANCH` or **`GENERATOR`** — **never `GEN`**. `GEN` is accepted by the
parser, silently ignored, and leaves the previous value in place (suspected, possibly by design:
glitch `2026-10-20-ctgautoinsert-gen-ignored`). Use `GENERATOR` either way:

```python
pw.esa.RunScriptCommand("SetData(CTG_AutoInsert_Options,[ElementType],[GEN]);")
pw.esa.GetParametersSingleElement("CTG_AutoInsert_Options", ["ElementType"], [""])
# -> 'BRANCH'          <- the write did not happen, and nothing said so
# 'GENERATOR' and 'Gen' both -> 'GENERATOR'
```

**Always read the option back and assert it** before `CTGAutoInsert`. `Handle3WXF` applies
to branches only. On Synth2k case 3 this yields **3,911 branch** contingencies (= its branch count)
and **743 generator** ones (= its generator count).

### Step 2 — match your devices to the labels autoinsert chose

Read `ContingencyElement` with an explicit field list
(`CTGLabel, BusNum, BusNum:1, ElementID, Object, Action`):

| device | `Object` | `BusNum` / `BusNum:1` | `ElementID` | example `CTGLabel` |
|---|---|---|---|---|
| branch | `BRANCH 1001 1064 1` | both ends | **the circuit ID** | `L_001001ODESSA20-001064ODESSA30C1` |
| 3W xfmr | `BRANCH …` | both ends | circuit | `T_…` prefix |
| generator | `GEN 1004 1` | bus / **`0`** | **the `GenID`** | `G_001004ODONNELL11U1` |

Two matching rules, both inherited from [reading-violationctg](reading-violationctg.md):

- **`ContingencyElement` has no `LineCircuit`.** The circuit ID is `ElementID` (verified on
  a 3-circuit bank: `'1'`, `'10'`, `'20'`). For generators `ElementID` is the `GenID`.
- **Match the bus pair UNORDERED and never parse the `CTGLabel`.** A case may store a branch
  either way round, and the label embeds *truncated* substation names, which collide.

### Step 3 — write the AUX, in PowerWorld's own shape

Do not guess the format. PowerWorld will export the set it is holding:

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

Measured on Synth2k case 3 (8 areas, 2,000 buses, 3,911 branches), reading the **effective**
flags `Bus.BusMonEle:1` / `Branch.LineMonEle:1`, not the requested ones:

| monitored areas | buses monitored | branches monitored |
|---|---|---|
| all 8, as shipped | 2000 | 3878 |
| `5` (North Central) | 483 = area 5 exactly | 866 = its own 822 **+ 44 ties** |
| `3, 5` | 630 | 1341 |

**A bus is monitored when its area is; a branch when EITHER end is.** Tie lines into the
region are included automatically. That is the opposite of the `ViolationCTG.AreaNum` trap
in [reading-violationctg](reading-violationctg.md), where a naive filter *drops* them. Related knobs found in the
same field-list dig: `Area.BGReportLimMinKV` / `BGReportLimMaxKV` (monitor only a kV band)
and `Branch.LineMonEle` / `Bus.BusMonEle` (switch off one device).

**Monitoring a region is not testing it.** `BGReportLimits` decides where violations are
*reported*; the contingency list decides what is *tripped*. A case often ships with a list
built for one area. Turn monitoring on for a second area, solve, and you get a clean report
for an area none of whose elements was ever outaged. That is a silent wrong answer, and it
reads exactly like a passing N-1. Before solving "N-1 for area X":

```python
import pandas as pd
from esapp.components import Bus

el = pw.esa.GetParametersMultipleElement("ContingencyElement", ["CTGLabel", "BusNum", "BusNum:1"])
area = {int(r["BusNum"]): int(r["AreaNum"]) for _, r in pw[Bus, ["AreaNum"]].iterrows()}
hit = {}                                   # area -> contingencies with an element touching it
for _, r in el.iterrows():
    for b in (r["BusNum"], r["BusNum:1"]):  # BusNum:1 reads None for a generator
        if pd.notna(b) and int(b) in area:
            hit.setdefault(area[int(b)], set()).add(r["CTGLabel"])
for x in asked_areas:
    assert hit.get(x), f"no outage touches area {x}: the list does not test it"
```

Non-zero is the floor, not the test. Measured 2026-10-20 on a 2,000-bus synthetic case whose
shipped list of 176 outages was built for one area: a neighbouring area still counted 12,
all tie lines on the boundary. So compare each count with that area's in-service branches
above 69 kV. A count that is a small fraction of them means the area is not tested. When the
list does not cover an area, build the area's set (Step 1) and load it alongside the
shipped one.

### Verify it worked

Load the file back into the open case and assert. Never trust the write:

```python
pw.esa.RunScriptCommand("EnterMode(EDIT);")
pw.esa.RunScriptCommand("Delete(Contingency);")     # LoadAux MERGES; delete to replace
pw.esa.RunScriptCommand(f'LoadAux("{absolute_path}", NO);')
pw.esa.RunScriptCommand("EnterMode(RUN);")
```

Assert **three** things, because each failure looks like success:

1. the loaded `CTGLabel` set equals what you wrote (a parse failure loads a prefix);
2. the `ContingencyElement` **count** equals what you wrote (a contingency with no element
   loads fine and outages nothing, which reads as "the grid survives everything");
3. every area's `BGReportLimits` came back as intended.

### Gotchas beyond the five in the Abstract

- **A device that gets no contingency is normal, not a bug.** Autoinsert requires both ends
  ≥ 69 kV **and** `LineStatus == 'Closed'`, and `Handle3WXF=INSERT3WXF` collapses a
  3-winding transformer's three branch rows into **one** contingency, so three device rows
  legitimately map to one label. Report the bucket with a per-device reason; do not abort.
- **The dominant unmatched cause on a real planning model is the 3-winding transformer's
  star bus, and it presents as a kV failure, not as a 3WXF one.** A 3W transformer is
  modelled as three branches meeting at a **fictitious star/tertiary bus carried at ~1 kV
  nominal**, so the winding branches touching it fail the 69 kV floor and autoinsert never
  builds a branch contingency for them (measured 2026-08-17 on regional planning cases:
  roughly two in five new branches). Do not read that bucket as missing coverage. The single
  collapsed `T_…` contingency covers the transformer itself. What is absent is a separate
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
topic: contingency
aliases: [limitset, ctg-voltage-band, setdata-key-fields, limit-monitoring]
tags: [esapp, powerworld, simauto, setdata, limitset, contingency, key-fields]
---

# Changing PowerWorld Limit Monitoring (LimitSet) via SetData

## Abstract

How to change PowerWorld's own limit-monitoring thresholds (`LimitSet` object — normal-ops
`LSPULow`/`LSPUHigh` and N-1 contingency `LSCtgPULow`/`LSCtgPUHigh`) from a script command or from
esapp. The headline gotcha: **`SetData` on `LimitSet` errors "some of the key fields is missing"
unless you supply the ENTIRE field row**, not just the key field(s) plus the fields you want to
change. Most other PowerWorld objects need only the key plus the changed fields. Live-verified
by round-tripping the same case's `LimitSet` values through a CSV export/reimport and a
`SetData` script command.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [save-powerworld-case](save-powerworld-case.md) · [adding-devices-esapp](adding-devices-esapp.md) · [powerworld-simauto](../concepts/powerworld-simauto.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The gotcha

A short `SetData` call that names only the key field and the fields you want to change:

```
SetData(LimitSet, [LSNum, LSPULow, LSPUHigh, LSCtgPULow, LSCtgPUHigh], [1, 0.920, 1.080, 0.880, 1.120]);
```

fails with **"some of the key fields is missing"**, even though `LSNum` (the object's key field)
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
never appears there. It shows up only on a case whose rate sets are *named*, as a real
planning model's are.

The write took, but a raw comparison fails it. The natural error message ("the limits did
not take — every violation would be measured against the wrong limit") then says the
opposite of the truth on a run that is fine. **Compare the letter before the colon**, so a genuine mismatch (`A` wanted, `B` stored) is still caught:

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
| `LSCtgPULow` / `LSCtgPUHigh` | **N-1 contingency** voltage band (pu): the threshold PowerWorld's own CTG/limit monitoring flags violations against, distinct from any Python-side `v_min`/`v_max` check a pipeline does after reading `BusMin/MaxVoltageContingency` |

### Two ways to apply it

**1. Manually, in the PowerWorld script command bar.** Paste the `SetData(...)` block above
with your values. Useful for a one-off manual test or round-trip check.

**2. From Python (esapp).** Do NOT hand-write the full-field `SetData` call in code. Read the
current full row, patch only the target columns, and write the full row back. `pw.esa.SetData(...)`
and `pw.esa.ChangeParametersMultipleElement(...)` are both thin passthroughs to the raw SimAuto call
(no key-field auto-resolution, no partial-write convenience), so the same "supply everything" rule
applies in code:

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

This works on any case, because it reads whatever LimitSet rows exist instead of hardcoding one
case's values. It changes only the 2 target columns and carries every other field through
unchanged, so nothing is hand-transcribed.

### Why this matters for N-1 work

A reactive planning pipeline checked contingency voltage violations in Python
(`Bus.BusMin/MaxVoltageContingency` against a hardcoded `[0.90, 1.10]` band). That check was
never tied to PowerWorld's own `LimitSet.LSCtgPULow/LSCtgPUHigh`, so the case's native limit
monitoring could silently disagree with the band the Python code assumes. Call
`set_ctg_voltage_limits` once after opening or building a case, so the case's own contingency
band matches the band the rest of the pipeline checks against.

> Read the values back after writing, as with the assert-after-save check in
> [save-powerworld-case](save-powerworld-case.md).


---

# ==== preflight-powerworld.md ====

---
type: method
domain: tooling
topic: scripting
aliases: [preflight, preflight-powerworld, powerworld-check, simauto-check, license-check]
tags: [powerworld, simauto, esapp, setup, troubleshooting, preflight]
---

# Method: Preflight — is PowerWorld actually usable here?

## Abstract

Run this before writing any analysis code. It takes about five seconds and answers one
question: can this machine drive PowerWorld from Python at all? Five checks, each with
the exact error you get when it fails and what that error means. Skipping this is why an agent writes two hundred lines
of a study and then discovers on the last line that SimAuto was never licensed.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp-overview](esapp-overview.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [esapp](../concepts/esapp.md)
- **Next:** [esapp-overview](esapp-overview.md) once every check passes

## Content

> **Agents: run this first.** Do not write analysis code before the preflight passes.
> A failure here is a fact about the machine, not a bug in your code, and no amount of
> rewriting the analysis will fix it. Report which check failed and stop.

### The preflight script

Paste this and run it. It prints a line per check and stops at the first failure.

**Run it with plain `python`, never `python -I`.** Isolated mode hides the user
site-packages, which is where `pip install --user` puts esapp, so check 3 reports esapp
missing when it is installed. In a 2026-10-20 validation run two agents hit exactly that and
then ran `pip install` on a shared machine unasked. If esapp really is missing, tell the user
to run `/powerworld-hivemind:powerworld-setup` (it installs esapp, TeamOverbyeWeather,
pywin32 and openpyxl). **Never pip-install on your own.**

Checks 1-4 are about the **machine** and need no case file; check 5 opens **your case**.
Call `preflight_machine()` on its own when you do not have a case yet (during setup, say),
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
        print(f"FAIL 2/5  pywin32 not importable from {sys.executable}")
        print("          ask the user to run /powerworld-hivemind:powerworld-setup")
        return False
    print("ok   2/5  pywin32 importable")

    # 3. esapp itself.
    try:
        from esapp import PowerWorld  # noqa: F401
    except ImportError:
        print(f"FAIL 3/5  esapp not importable from {sys.executable} (not under python -I?)")
        print("          ask the user to run /powerworld-hivemind:powerworld-setup")
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
    # 5. The case itself opens.
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
| `ModuleNotFoundError: No module named 'win32com'` | pywin32 is not installed | Ask the user to run `/powerworld-hivemind:powerworld-setup`; do not pip-install yourself |
| `ModuleNotFoundError: No module named 'esapp'` | esapp is not installed, you are in the wrong interpreter, or you ran under `python -I` | Rerun without `-I` and check `sys.executable`. If it is still missing, ask the user to run `/powerworld-hivemind:powerworld-setup`; do not pip-install yourself |
| `com_error: (-2147221005, 'Invalid class string', ...)` | SimAuto is not registered. Usually PowerWorld Simulator is not installed at all | Install Simulator. If it *is* installed, run it once as administrator so it registers its COM server |
| `com_error: (-2147221164, 'Class not registered', ...)` | Same as above, or a 32/64-bit mismatch between Python and Simulator | Match the bitness. A 32-bit Simulator will not serve a 64-bit Python |
| A COM error mentioning **licence**, **not authorized**, or **add-on** | Simulator is installed and licensed, but the **SimAuto add-on is a separate licence** and yours does not include it | This cannot be fixed in code. Talk to whoever administers your PowerWorld licence |
| SimAuto starts but a feature errors | Possibly a version difference | Check the build date against [version-requirements](../concepts/version-requirements.md) before assuming a page is wrong |
| `PowerWorldPrerequisiteError` | **Not** a version or licence problem. The case lacks a prerequisite state | e.g. clearing TimeStep results that do not exist yet. Do the prerequisite step first |
| `case not found` | Path typo, or a relative path resolving somewhere unexpected | Use an absolute path. Always |
| Case opens but `n_bus` is 0 | The file opened but is not a valid case | Confirm the `.pwb` is not corrupt; try opening it in Simulator directly |

### The licence check, specifically

**PowerWorld Simulator and the SimAuto add-on are licensed separately.** A machine can
have a fully valid, fully working Simulator installation and still be unable to run a
single line of this kit, because automation is a different SKU. Simulator's own GUI works
fine and gives no hint of this.

The symptom is that check 4 fails while Simulator itself launches normally. If you can
open your case by double-clicking it but `Dispatch("pwrworld.SimulatorAuto")` raises,
that is the licence, not your code.

### Record the version before you analyse anything

Check 4 prints the Simulator build date. Put it in your report. Field availability and
script-action behaviour both shift between releases, and they shift silently, so when a
result later looks wrong, check the build date first.

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
you. If it raises, nothing is.

### What preflight does not tell you

It confirms you can *drive* PowerWorld. It says nothing about whether the case is
suitable for the study you have in mind: whether it solves, whether it has the
generators or weather models you need, whether its limits are configured. Those are
questions for the analysis itself, starting at [esapp-overview](esapp-overview.md).


---

# ==== ranking-new-devices-by-severity.md ====

---
type: method
domain: tooling
topic: contingency
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
the only file at the top of the output directory. The per-metric sorts and the
per-violation-row evidence live one level down in `_audit/`. It answers *without device X,
what does this case experience?*, so a device that was never tested must still have a row,
or "absent" and "harmless" become the same thing.

**The single ordering uses the FRACTION BEYOND THE LIMIT.** Percent-of-rating and per-unit
volts do not share a unit, but each quantity *divided by the limit it violated* is
dimensionless, and those are comparable without inventing an exchange rate. So a 0.80 pu bus
(0.158 beyond a 0.95 floor) outranks a 101% branch (0.010 beyond its rating), which no
per-metric sort does. It still asserts that a 5% overload and a 5% voltage excursion are
comparably bad, but that claim is visible and checkable, which "percent vs per-unit" never
was. The per-metric sorts in `_audit/` keep
the two apart on their own units; this is the one sanctioned crossing.

Six things here decide whether the ranking means anything, and each fails silently:

1. **Subtract the base case — AND attribute the magnitude.** A branch already at 105%
   appears under *every* contingency, so without subtraction every device inherits the same
   overloads (**38% of all rows** on one measured Texas2k run, 464,794 of 1,218,162). The subtraction only decides
   *whether* a row counts: a branch at 220% nudged to 221% survives it legitimately and then
   reports **221%** for a device that caused **+1%**. Score `min(exceedance, addition)` (see
   *Attribution* below). Measured at a 60% threshold:
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
   band reads a severe bus as trivial. Carry both. The score is built from the excursion
   and must stay auditable.
6. **A device's own area is not the reporting scope.** They routinely differ, and the file
   gives no hint that they do. See *The area trap* below.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Input from:** [new-device-contingency-aux](new-device-contingency-aux.md) — builds the AUX this solves;
  [comparing-planning-cases](../demos/comparing-planning-cases.md) — decides which devices are new
- **Across:** [reading-violationctg](reading-violationctg.md) (the read this ranks, and its traps) ·
  [powerworld-limitset-setdata](powerworld-limitset-setdata.md) (the thresholds it ranks against) ·
  [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (solving the set across processes) ·
  [lodf](../concepts/lodf.md) (the unbuilt fix for the islanding gap)

## Content

### Attribution: what the outage is actually responsible for

Subtracting the base case corrects the row set but not the *magnitudes*, and nothing shows
the gap. Score each row as the smaller of

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
A row with no base value was clean, so the whole exceedance is the device's. Missing base
data must never silently zero a real violation.

| category | exceedance | addition |
|---|---|---|
| `thermal` | `(pct - T)/T` | `(pct - base_pct)/T` |
| `voltage_low` | `(limit - V)/limit` | `(base_V - V)/limit` |
| `voltage_high` | `(V - limit)/limit` | `(V - base_V)/limit` |

`T` is the run's thermal threshold, so thermal normalizes exactly as voltage does. **Read
the base value with the SAME key the subtraction uses** (unordered bus pair plus
normalized circuit), or a row is filtered against one baseline and scored against another,
which is worse than either alone.

**`LimViolLimit` on a thermal row is the branch's MVA RATING, not 100.** Measured 21, 46,
57, 4352. Thermal must score off `LimViolPct` and voltage off `LimViolLimit`; borrowing the
other's field yields percent-minus-MVA, which is a plausible-looking number.

**Average as well as worst, on the attributed quantity.** The mean over a device's rows
separates one catastrophic element from twenty mildly-over ones, which the count only
half-answers. Computed on absolute percent, it would re-inherit the whole base-case
contamination. Measured: the top devices score ~1.16 on their worst element and average
~0.010 across ~190 rows.

### The output table: natural units only

**A number the reader cannot interpret is not a result.** The score below is correct,
dimensionless, and unreadable to someone opening a spreadsheet. Other people open this file,
and they should not have to learn the scoring scheme first. So the file carries **only**
percent of rating, per unit, and counts. The arithmetic behind the ordering moves to a
sidecar, where the rank stays auditable.

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
covers TWO ways rows go missing.** It was first keyed only off the row-count mismatch
guard. That let a run discard **2,972 unclassified violation rows on a planning model
and still write `count_verified = True` on all 297 devices**: the audit trail was correct and
the file people open was not. An unclassified row now taints its device exactly as a count
mismatch does. In general, a bucket that means *"rows were dropped"* must reach the summary
artifact, because `_audit/` is not what gets mailed.

**Worst and average answer different questions**, and the count answers neither. A device
whose worst overload is 157% and whose average is also 157% overloads exactly one branch;
one with a high worst and a low average has a single hot spot among many marginal
violations. Take averages in the SAME natural unit as the worst. An average of the
dimensionless score reads as noise (`0.064`), and an average of two different units at
once is meaningless even though it is well-defined.

**`worst_*` means most attributable, not highest number.** The reported rows are the ones
that drove the rank. Once the base case is attributed, those need not be the arithmetic
maximum (a 221%-on-a-220%-branch loses to a 150%-from-clean one). Printing the maximum
beside a rank derived from a different row is how the two disagree in public.

**What was deliberately taken OFF the file**, and the cost: `severity_score`,
`severity_from`, `avg_severity`, the band excursion, and the per-device *how much did this
device add* figures. All are still computed and written to a sidecar. The accepted cost is
that on a case whose base already carries big overloads, a `221%` row reads as a 221%
device with nothing on the page to say the device only added 1%. That is a real loss; it
was traded for a table anyone can read.

### The one ordering: fraction beyond the limit

`rank` is dense `1..N` (no ties, no gaps) and orders **diverged first**, then
`severity_score` descending, then `CTGLabel` ascending so two runs of the same case agree.

`severity_score` is each violation's fraction beyond the limit it actually violated:

| category | score | example |
|---|---|---|
| `thermal` | `pct/100 - 1` | 157% loading -> `0.571` |
| `voltage_low` | `(limit - V)/limit` | 0.80 pu vs a 0.95 floor -> `0.158` |
| `voltage_high` | `(V - limit)/limit` | 1.10 pu vs a 1.05 ceiling -> `0.048` |

The units cancel, so this is a real dimensionless quantity rather than a fudge factor. **Do
not collapse it to `abs(pct/100 - 1)`.** It is arithmetically identical on all three
categories today, but it gets `voltage_low` right for the wrong reason and would keep
"working" silently if a polarity were ever redefined.

A device that solved and broke nothing scores a measured `0.0` and ranks last; a diverged
one scores `NaN` and ranks first. **There is deliberately no `status` column**: `converged
== False` *is* the diverged set and `n_violations == 0` *is* the silent set, so both facts
stay filterable data rather than a string to parse, and `ranked_by` says which in words.

Derive those labels from the COUNTS, never from the score. A silent device carries a real
`0.0`, not `NaN`, so a test keyed on a missing score never fires for it, and the label stays
blank on exactly the rows it was written for.

The percentage for voltage is `LimViolPct` **for the row already chosen as worst by
severity**, never a re-max on pct. For `voltage_low`, *lower* pct is worse, so re-maxing
selects the least severe bus while looking entirely correct.

### The per-metric sorts, and why they survive in `_audit/`

| list | sort key | unit |
|---|---|---|
| thermal | worst `LimViolPct` | percent of the branch's own rating |
| voltage | worst pu distance **outside** the band | per unit |
| count | violations the outage caused | count |

Percent-of-rating makes differently-rated branches comparable: a 250% overload outranks a
200% one regardless of the MVA behind it. Voltage cannot use percent: measured,
`Bus Low Volts` rows sit *below* their limit with `LimViolPct` in 94-100 (lower is worse)
while `Bus High Volts` sit *above* with pct 100-103 (higher is worse). Ranking both on pct
orders overvoltages exactly backwards. Distance outside the band fixes it: 0.87 pu against a
0.90 floor and 1.13 against a 1.10 ceiling both score 0.03 and are equally bad.

"Worst single violation" and "broke the most things" are different questions, so the count
is its own axis rather than a tiebreaker. The single `severity_score` ordering answers only
the first, so it does not retire these lists.

### The area trap

A device's own area and the **reporting scope** are different things, and nothing in the
file says so. Violations are scoped by `Area.BGReportLimits` in the AUX, which monitors
*violated elements*, not outaged devices. A device far outside the monitored region is
still solved and still counted, because its outage can violate something inside.

Measured on Synth2k with two of eight areas monitored: **364 of the 531 out-of-area devices
caused in-region violations.** So `n_violations = 0` on an out-of-area device means "causes
nothing in the monitored region", never "was not checked". Filtering the device table on
area to "recover the region" silently discards 364 real results while looking like a
sensible narrowing.

### Subtracting the base case

Solve the base power flow first and record what was **already** violating, from
`Branch.LinePercent` and `Bus.BusPUVolt`, *not* from `ViolationCTG`, which is
per-contingency and says nothing about the base state. Then a post-contingency violation
counts only if the outage **caused it or made it worse**:

| category | already violating when | worse when |
|---|---|---|
| thermal | `LinePercent >= threshold` | post pct > base pct |
| voltage low | `BusPUVolt < v_min` | post pu < base pu |
| voltage high | `BusPUVolt > v_max` | post pu > base pu |

Three identity rules. Get any one wrong and the subtraction silently removes nothing:

- **The branch key is the UNORDERED bus pair.** Identity is direction-sensitive in the raw
  data, so an ordered key matches nothing, which looks exactly like a base case with no
  violations.
- **The circuit ID is compared as normalized text.** `'10'` from one table, `10.0` after a
  CSV round-trip.
- **Read the base frames AFTER applying the limits**, because `LinePercent` is evaluated
  against the monitored rate set the limit write patches.

**Comparing percent to percent is only valid because both rate sets are pinned.** Write
`LSLineRateSet` *and* `LSLineRateSet:1` to the same value and assert it (see
[powerworld-limitset-setdata](powerworld-limitset-setdata.md)); then the base percent and the contingency percent share a
denominator. Do **not** "fix" this by comparing MVA instead; it was tried. `LinePercent` is
a *from-end* percent: from-end MVA ÷ LinePercent recovers exact ratings (149.000001,
221.000004, 4352.000046), while the larger of the two ends gives 149.46, 221.11, which are
not ratings. `LimViolValue` is not guaranteed to be that same end. The swap moved 5,092
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
buses, re-reported under all 219 devices**, so 219 of 220 devices ranked as causing
something, off a base-case condition. Overlap with the base-case high-voltage set: **0 of 3**. A flat band
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
**redundant, not conflicting**, verified rather than assumed. Setting the option to `0` on
Synth2k case4 and running with `--include-worsened` yields **the identical 36-row set** that
`--only-new` yields on the unmodified case: same rows, zero difference either way.

Two qualifications. The `CTGViol` COUNTS differ (82 vs 153 summed over those 36
rows), because PowerWorld reports fewer violations per contingency when it is suppressing
base-case ones; the row SET is identical, the per-contingency tallies are not. And the two
runs were not config-identical: the `= 0` run screened every voltage level while the
`--only-new` run used a 69 kV floor. The comparison still holds because the kV filter
dropped nothing on this case (its lowest violated element is 115 kV), but that is a
property of Synth2k rather than of the equivalence.

`base_case_violations.csv` is unaffected by the option, because it is read from
`Branch.LinePercent` / `Bus.BusPUVolt` and never from `ViolationCTG`. A `= 0` run still
records its 6 base-case violations and drops 0 of them as pre-existing.

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
low-voltage rows survive both ways too, so the filter discriminates rather than just
cutting.

### Configuring a run

**Two CONFIG blocks answering different questions.** The study script's decides WHICH DEVICES get
a contingency and is baked into the AUX. The ranking script's decides WHAT COUNTS AS A
VIOLATION when that AUX is solved. Changing the second never needs the AUX rebuilt;
changing the first always does. Every ranking-script setting also has a flag and **the flag
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
every silent device carries three counters: `n_violations_raw` (pre-filter),
`n_below_kv`, `n_worsened_only`. **Never add a filter without a per-device counter beside
it**: it shipped once without one, and at `--min-kv 200` the branch ranked #2 at 133.9% of
rating came out at rank 585 reading `n_violations = 0`.

**`MIN_KV` screens the VIOLATED element, on its HIGHER end, strictly above.** It does not
screen the outaged device: a generator sits at its terminal kV (13.8-20 kV on Synth2k), so
screening devices would delete every generator contingency while looking like a voltage
filter. The higher end is a deliberate trade. It is NOT (as first written) for consistency
with `device_attributes`, whose `kv` is an identity label rather than a membership test. The
strict both-ends rule is cleaner on distribution but drops a 500/161 autotransformer from a
200 kV screen, and losing a bulk asset is worse than some clutter. One consequence: at
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

**Do not confuse any of this with a standalone script that sets
`CTG_Options.CTG_WhatToDoWithBC`** (0 = do not report base-case violations; 1 = report all;
2 = change-from-base criteria). It is **not part of this pipeline**. Applying 0 to a case
this tool consumes double-filters: PowerWorld suppresses base-case violations before Python
sees them, deleting the worsened rows the subtraction deliberately keeps.

### Solving it across processes

The set comes from an AUX, so each worker can `Delete(Contingency)` + `LoadAux` the **same
file** and solve its own chunk: provably the same set, and no saved case required (see
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
  ten of **8.5e-07**. That is not a suite-wide bound and must not be quoted as one: 110
  devices carry a nonzero severity difference, the largest being **1.1e-06**. They simply
  do not reorder, because the gap to their neighbour is wider than the wobble.

## Provenance

**2026-08-22 (b)** — **the baseline was judging buses against the wrong number** (see *The
bus's own voltage limit, not the band you configured*). It tested every bus against the
configured `v_min`/`v_max`. The baseline loader now reads `BusVoltCtgLimHigh`/`Low` and
judges each bus against the limit PowerWorld applied, falling back to the band only where a
case reports none. Comparing those limits needs a relative tolerance too: they come back
single-precision (1.10 -> 1.10000002), and an exact test reported 4000 phantom overrides on a
Synth2k case where every bus carries exactly the band.

Separately verified, settling a question that had been assumed both ways:
**`CTG_WhatToDoWithBC = 0` and `--only-new` produce the identical 36-row set** on Synth2k
case4 (see the section above). The standalone script that sets that option turned out never to have run at all
(its input path pointed at a case that does not exist), and it verified its own write from
memory BEFORE saving, so a no-op save would have passed. Both fixed.


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
`WORSENING_REL_TOL = 1e-4` in the baseline's worsened test, mirroring the fix the limit
writer had already made for its own read-back check. An absolute 1e-6 on a percent near 100 asks for
~1e-8 relative precision — below one float32 ULP there (7.6e-6) and far below solver
repeatability, so it was not a tolerance, it was `>`. Measured: a branch at 100.072085% in
the base case read 100.072148% after one outage, 6.3e-5 pp, and the absolute test admitted
it. Effect on case4: caused rows 460 serial / 459 parallel to **278 / 278, identical row for
row**; devices "causing a violation" 431 to 252, with all 36 material devices still in the
top 36. **The "byte-identical ranked CSVs" claim recorded here on 2026-08-18 is retracted**
-- see *Solving it across processes* for the invariant that does hold.

The regression test pins the DERIVATION, not the number: the floor
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
an error: **`LimViolLimit` on a thermal row is the branch's MVA rating**, not 100 (see
*Attribution*); and the LimitSet read-back used an **absolute** `1e-6` tolerance on `LSLinePercent`, which lives near 100 where float32 cannot
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

Measured 2026-08-17 by a ranking script written for the purpose, on
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
topic: contingency
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

Six traps, each of which produces a **plausible wrong answer rather than an error**. The
first four were live-measured on `Synth2k_case` on 2026-08-16; the fifth and sixth appear
only on cases Synth2k cannot produce:

1. **`AreaNum` is the branch's OWN area and reads `0` on a tie-line.** Filtering on it
   silently drops every cross-area violation. The endpoint areas are `AreaNum:1` / `:2`.
2. **`LimViolPct` polarity is three-way, not two-way.** `Bus Low Volts` is a violation
   where *lower* pct is worse; `Bus High Volts` inverts. One sort key ranks one of them
   backwards.
3. **Results persist in the `.pwb`** and read back fine with no solve at all. 148 stale
   rows came out of a freshly-opened case.
4. **A bare `pw[ViolationCTG]` returns 2 columns.** You must pass an explicit field list.
5. **The `LimViolCat` vocabulary is case-dependent, not fixed.** An amp-rated branch
   reports `Branch Amp`, which Synth2k never emits, so a classifier measured there drops
   every one of those overloads as an unknown category and still completes, still writes
   plausible CSVs, and still reports a grid it never screened.
6. **`LimViolID:1` identifies a monitored END, not an element.** A branch monitored at both
   ends appears under two ids, so grouping on the raw string counts ends and reports them as
   distinct violated elements.

Also settled here: an earlier claim that esapp's typed read of `ViolationCTG` errors
*"interface unknown"* on Synth2k **does not reproduce**.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [new-device-contingency-aux](new-device-contingency-aux.md) (building the set you solve, and scoping
  monitoring to an area) · [powerworld-limitset-setdata](powerworld-limitset-setdata.md) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) · [lodf](../concepts/lodf.md) ·
  [powerworld-simauto](../concepts/powerworld-simauto.md)
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
solve**, on disjoint sets of branches. In one measured run on a planning model, 2,972 real
overloads (101.7%–240.7% of rating, all 297 contingencies) were classified `unknown` and
dropped while the run reported 18 violations and looked clean.

Two rules follow:

- **`Branch Amp` is thermal.** Score it off `LimViolPct` exactly as `Branch MVA`. Percent
  is percent regardless of the rating's unit, so the two never need an exchange rate. But
  `LimViolValue` / `LimViolLimit` on those rows **are amps** (284–2,176 A on that model) and must never be compared against an MVA row's.
- **`Unsolved` is not.** It is `CTGSolved = NO` arriving through the violation table.
  Ranking it as a violation scores a contingency the run established *nothing* about.

Before trusting a thermal count on a new case, check what the case rates in:
`LimitSet.LSAmpMVA` says which, and `LSEndMonitor` says which end.

### Trap 1 — `AreaNum` is the branch's own area, and it is `0` on a tie-line

This is the expensive one. The four `AreaNum` slots mean different things:

| slot | meaning |
|---|---|
| `AreaNum` | the **object's own** area — `0` when a branch spans two areas |
| `AreaNum:1` | the FROM-bus's area |
| `AreaNum:2` | the TO-bus's area |
| `AreaNum:3` | tracked `AreaNum:1` on every observed row |

Measured on branch 1004 (Far West) → 3133 (West):
`AreaNum=0, AreaNum:1=1, AreaNum:2=3, AreaNum:3=1`.

On an intra-area branch all four read the same number, so the difference shows only on a
tie-line. **1,933 of 36,122
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

`LimViolValue == LimViolLimit * LimViolPct / 100` held on **120,428 of 120,428 rows**. The
typed value is trustworthy, and the arithmetic makes a good cross-check assertion.

### Trap 3 — results persist in the `.pwb`

`ViolationCTG` survives in the saved case. Opening a case and reading it immediately
returned **148 rows** from some previous run, full of real-looking numbers.

Call `CTGClearAllResults()` before every solve, and assert every returned `CTGLabel` is in
the set you meant to solve.

### Trap 3b — the contingency reference does not follow the case

`CTGSolveAll` applies each outage to the **stored contingency reference**, not to the state
the case is in now. Move the operating point (a TimeStep hour, a new dispatch, an edit) and
solve without `pw.esa.CTGSetAsReference()`, and every contingency is solved against the old
reference. Nothing errors, and the rows look real. Status: suspected, possibly by design: glitch `2026-10-20-ctg-reference-timestep`; call `CTGSetAsReference()`
whichever it turns out to be.

Measured 2026-10-20 on Simulator build 2026-09-25, on the public Texas2k grid with a weather
file: three TimeStep hours with renewable output from about 2.7 GW to 7.6 GW, each set with
`TimeStepDoSinglePoint` and then solved with `CTGClearAllResults()` + `CTGSolveAll()`,
returned identical results. Calling `CTGSetAsReference()` after each `TimeStepDoSinglePoint`
turned two of the three hours into more than 170 violation rows each.

```python
for hour in hours:                         # ISO 8601, e.g. "2023-08-10T19:00:00Z"
    pw.esa.TimeStepDoSinglePoint(hour)
    pw.esa.CTGSetAsReference()             # without this every hour reuses the old reference
    pw.esa.CTGClearAllResults(); pw.esa.CTGSolveAll()
```

If every hour returns the same results while the hours' generation differs, the reference was
not reset.

### Trap 4 — never use a bare read

```python
pw[ViolationCTG]                    # -> 2 columns: CTGLabel, LimViolID:1
pw[ViolationCTG, VIOLATION_FIELDS]  # -> everything you asked for
```

### Trap 6 — one identity per MONITORED END, not per element

A branch appears under a **separate `LimViolID:1` per monitored end**. The two strings differ
only in the monitored-bus token, and the direction token does **not** discriminate; both ends
can report the same direction. Measured 2026-09-14 on a real planning-model export: about one
id in a hundred was the second end of a branch already counted, and the two ends reported
materially different percentages.

So **grouping on the raw id string counts monitored ends, not elements.** Any "distinct violated
elements" figure produced that way is an end count wearing an element count's name.

The element key is `(min(from, to), max(from, to), circuit)`: drop the monitored-end and
direction tokens and normalise the endpoint order. Severity is the **max across ends**,
because the end is where the measurement was taken and not part of the identity. This matters
most under a one-element-per-round remediation loop: ungrouped, the loop targets one branch on
two separate rounds, and the second round sizes an action against a branch it already upgraded.

Endpoints are available as real columns on the same row, so only the circuit and monitored end
need to come from the string. That also makes the parse self-checking, since the string's
own endpoint tokens must agree with those columns.

### The per-category column contract

Which identity slots are populated, by category (`1.0` = always, `0.0` = never):

| `LimViolCat` | `AreaNum` | `AreaNum:1` | `AreaNum:2` | `BusNum` | `BusNum:1` | `BusNum:2` | `LineCircuit` |
|---|---|---|---|---|---|---|---|
| `Branch MVA` | 1.0 intra / **0 tie** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| `Branch Amp` | 1.0 intra / **0 tie** | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| `Bus High Volts` | 1.0 | 1.0 | 0.0 | 1.0 | **0.0** | 1.0 | 0.0 |
| `Bus Low Volts` | 1.0 | 1.0 | 0.0 | 1.0 | **0.0** | 1.0 | 0.0 |
| `Interface MW` | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

Two consequences:

- **A bus violation carries a populated `AreaNum:1`.** So a two-endpoint OR applied
  unconditionally attributes a bus to an unrelated area. `BusNum:1` is the clean
  discriminator: populated for branch rows, empty for bus rows.
- **Interface rows carry no identity at all.** They cannot be attributed to a region; drop
  them deliberately and print the count.

### Row-count integrity, and why not to deduplicate

`rows_per_label == CTGViol` held exactly on **40/40** labels. Assert it. It catches
duplication *and* dropped rows for free.

**But it does NOT hold on every model.** On a regional
planning model (2026-08-17) a label returned 1 row while its own `CTGViol` read `0`.

The tempting explanation — that `CTGViol` counts only branch violations, so a voltage-only
contingency reads 0 — is **wrong, and was tested**:

- esapp's schema defines `CTGViol` as *"the number of violations that occurred under this
  contingency"*, unqualified (`esapp/components/grid.py`, class `Contingency`), while
  `CTGNBranchViol` / `CTGNVoltViol` / `CTGNInterfaceViol` are the branch / **bus** /
  interface counts.
- Synth2k confirms it is the sum: `3010 + 1 + 1195 = 4206` exactly, on a label carrying all
  three kinds.

So `CTGViol` **does** include voltage violations, and a disagreement is a real signal rather
than a scope quirk. The live candidates are a **stale or duplicate-labelled `Contingency`
record**, or rows genuinely dropped. A label-keyed join silently collapses duplicates to
whichever side wins, and `Contingency` aggregates persist in the `.pwb` exactly like
`ViolationCTG` does (trap 3).

The discriminating probe, from data you have already read:

| check | what it means |
|---|---|
| more than one `Contingency` row shares the label | duplicate record; the count you read is the wrong record's |
| `rows == 0` while `CTGViol > 0` | rows were dropped — and that device will read as causing nothing |
| `CTGViol != CTGNBranchViol + CTGNVoltViol + CTGNInterfaceViol` | the aggregate is stale for that label |

Keep the guard, but **do not abort on it after an expensive solve**. Report the evidence and
mark the run unverified instead, or you destroy the rows you would need to tell these three
apart.

`LimViolCTGSpecifiedLimit` (*"If YES, Limit was specified during a contingency action. This
Limit overrides all Limit Monitoring Settings."*) is a separate, real mechanism for a
violation whose limit differs from the standing `LimitSet`. It read `NO` on those rows
above, so it did not explain them. It is not in the default field list; read it when limits
and violations disagree.

Do **not** deduplicate on `(label, category, element)`. Repeated-looking rows are usually
real: four parallel circuits on one bus pair produce one contingency each, and outaging any
one overloads the other three. That is 3 rows per label with identical bus numbers and
*different* `LineCircuit` values, and a dedup on the bus pair would silently eat them.

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
  bus". (This is the same `0.0` that a per-bus N-1 voltage check treats as
  "not evaluated".)
- All eight islanding contingencies reported `CTGSolved='YES'` with thousands of ordinary
  violations — indistinguishable from any other contingency.
- `CTGWhatOccurredCount`/`:1`/`:2`, `CTGAltPFBusCount`, `CTGAltPFPossible` and
  `CTGRemedialActionApplied` are identically zero/`"Not Checked"` either way.
- No `Bus Low Volts` row anywhere read near 0 pu (minimum 0.9312) — **islanded buses emit no
  violation rows at all.**

`ViolationCTG` alone will not detect islanding, **but [lodf](../concepts/lodf.md) will, for
free and without a solve.** When the LODF denominator `1 − ψ_kk → 0`
there is no alternate path, i.e. outaging that branch splits the network; the math flags it
before any solve is attempted. Measured on Synth8k: **about 3%** of outages (roughly 1 in 30), found in the
~6 s it takes to build the PTDF. That page reached the same conclusion from the other
direction (*"in a PowerWorld CTG sweep, islanded buses read 0 and get skipped, so stranding
a 138 kV pocket reports CLEAN"*); this page confirms the hole independently from inside
`ViolationCTG`.

**Correction (2026-09-24, completed 2026-09-28): islanding *is* visible after `CTGSolveAll` —
through three checks that each catch a different set, and no single one catches all.**

- **`Contingency.LoadMW` / `GenMW`** hold the load and generation cut off by each outage and are
  non-zero only on islanding outages. These are islands PowerWorld **drops**. Checked against a
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
`ViolationCTG` alone still ranks every one of these outages harmless. Read the island checks
alongside it.

### Branch loading: read the worse end

`Branch.LinePercent` is the **from end** only; `LinePercent:1` is the to end (PowerWorld's field
export: "% of MVA Limit at From Bus" / "at To Bus"). The contingency monitor, and so every
`ViolationCTG` row, uses whichever end is larger. An N-0 maximum built from `LinePercent` alone
understates it: measured by up to ~3.5 points on a stressed 69 kV branch (recorded
2026-09-24). Use `max(LinePercent, LinePercent:1)` whenever an N-0 number sits
next to N-1 results.

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
replace a regional study. They are still a free whole-system cross-check on a ranking.

## Provenance

Measured live on 2026-08-16 against
`Synth2k_case.PWB` by a pair of spike scripts written for the purpose.

Numbers quoted here come from a run with the bands deliberately squeezed
(`LSLinePercent=25`, band `[0.99, 1.01]`) so that every category was forced to appear.


---

# ==== reducing-a-contingency-set.md ====

---
type: method
domain: cross-cutting
topic: contingency
aliases: [ctgskip, ctg-skip, reducing-the-ctg-set, contingency-subset, skip-column]
tags: [powerworld, contingency, ctg, esapp, simauto, n-1]
---

# Method: Reducing or partitioning a contingency set

## Abstract

`CTGSkip` and `Delete(Contingency, <filter>)` do two different jobs and are
routinely confused. **`CTGSkip` partitions a set without shrinking it** — every
contingency stays in the case and the skipped ones are not solved this pass,
which is how the parallel solver gives each worker a slice. **`Delete` with
a violation filter is the only thing that actually reduces the set**, and it is
destructive, so it needs a backup first. This page collects the mechanism, the
three places it is used, and the three silent failures around it. **A parallel sweep driver overwrites
`CTGSkip` in every worker**, so for a parallel loop keep every label in the case and scope by the
active-label list, never by `Delete`.

## Connections

- **Up:** [Home](../index.md) · [violation-remediation](../demos/violation-remediation.md)
- **Across:** [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) — the chunking use ·
  [new-device-contingency-aux](new-device-contingency-aux.md) — writing a subset to `.aux` ·
  [reading-violationctg](reading-violationctg.md) — where the violation columns the filter uses come from

## Content

### The two mechanisms, and which one you want

| you want | use | destructive? |
|---|---|---|
| solve part of the set now, keep all of it | `CTGSkip` = `YES` / `NO` | no |
| permanently drop contingencies that did nothing | `Delete(Contingency, "<filter>")` | **yes** |

**"Are you reducing the ctg set by setting SKIP to YES?"** No. Setting
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
Delete(Contingency, "CTGNVoltViol = 0");    // drop those with no voltage violation
Delete(Contingency, "CTGNBranchViol = 0");  // drop those with no overload
Delete(Contingency, "CTGViol = 0");         // drop those with neither
EnterMode(RUN);
```

**One condition only. `AND` is not supported in this filter.** If you need both,
delete twice or use `CTGViol`.

**Back up first, because this is destructive:**

```
CTGWriteAuxUsingOptions("<path>", NO);   // save the full set
Delete(Contingency, "CTGViol = 0");  // your filtered delete
LoadAux("<path>");                        // restore
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

### The parallel driver is scoped by neither mechanism

Step 3 above assumes `Delete` is what makes later rounds cheaper. **For a chunked parallel sweep
it is not, and `Delete` buys nothing there.** A parallel driver of the kind in
[parallel-contingency-solve](../concepts/parallel-contingency-solve.md) reads every label off the
`Contingency` object itself, and each worker **overwrites `CTGSkip`** to scope itself to its own
chunk. A skip list saved in the `.pwb` speeds up a serial solve and the GUI, and does nothing
here.

Scoping the parallel path happens through **its active-label argument or not at all**. Two
consequences:

- **`Delete` saves no sweep time** that passing the surviving labels does not already save.
- **It costs something.** The case you eventually ship carries a mutilated contingency set, and a
  set that can only shrink is one where a contingency missed on an early round can never be found
  again. A contingency clean at round 0 does not stay clean.

So for a parallel loop: **keep every label in the case, pass the survivors as the active set,
and never call `Delete`.** Write the round's `.aux` with *every* label and its skip flag, not
only the survivors, so the round is a snapshot rather than a one-way door.

### A re-check set that deletes nothing

To re-check a fix without rerunning the whole N-1, keep every contingency and skip all but the
ones that mattered:

1. From the full sweep, list every outage that produced a violation row or did not solve, in
   **any** dispatch.
2. Write two aux files: one that sets `Skip = NO` on that list and `YES` on every other
   contingency, and one that sets `Skip = NO` on all of them. `LoadAux` the first, solve,
   `LoadAux` the second to go back.
3. Load-test both on a scratch copy first: each must leave exactly its set unskipped, and no
   contingency or element may be added or lost.
4. After a fix, add every outage within two or three substation hops of the change and the
   outages of any new element. A fix can create a violation elsewhere, and the old list cannot
   see it.

Two limits. A rating change needs the **full** N-1 again, because lowered ratings create rows
that were never on the list. And a thermal value read off an outage that did not solve describes
no solved state; do not rank it.

**Screen three-winding internal buses before building the list, or it is the whole list.** A
three-winding bank is modelled as three windings meeting at a star bus (nominal 1 kV), often with
an unloaded tertiary. Measured 2026-10-20 on a ~9k-bus synthetic case: in a light-load dispatch
one bank's star and empty tertiary sat at 1.1055 pu **before any outage**, while the bank's
terminals read 1.034 and 0.995 pu. Above the 1.10 post-outage limit, PowerWorld listed both buses
under all but two of the outages: tens of thousands of rows for two buses that are not network
buses. With them screened out, the real re-check set was under two outages in a thousand.

So: drop star, tertiary, unit-terminal (step-up low side) and ≤1 kV buses from every violation
count; tag the outages whose only rows are on them as internal-only; and report those rows apart,
per bank, with the terminal voltages next to them. Screening hides the symptom, not the cause. A
star sitting above both its terminals is a model fault in the bank's data, so log it and fix it
there.

### Three silent failures

- **An unquoted action string in a hand-written `.aux`.** Written bare as
  `BRANCH 1001 1064 1 OPEN` instead of quoted, a 691-contingency file loads as
  **one** contingency, and the load **reports success**. Always quote the action.
- **`SaveContingencies` is not a script command** ("Unknown script command"). Use
  `SaveData(<path>,AUX,Contingency,[CTGLabel,CTGSkip],[CTGElement],"",[],[],YES);`.
  The filter argument is a bare string and the sort lists must be bracketed.
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

# ==== remediating-base-case-violations.md ====

---
type: method
domain: synthetic-grid
topic: design
aliases: [base-case-remediation, n-0-remediation, voltage-remediation-actions, remediation-action-space,
  action-ladder, remediation-action-catalog, what-can-i-do-about-a-violation, fix-intact-case-violations]
tags: [synthetic-grid, voltage, thermal, remediation, powerworld, reactive-power, n-0, ladder]
---

# Method: Remediating base-case (N-0) violations

## Abstract

The action ladder for fixing **intact-case** voltage and thermal violations, cheapest first, with
the measured evidence for each rung and the traps that inflate the answer. Actions are **priced in
devices added, not money**: free levers (generator setpoints, transformer taps, rating bumps,
bumping a device already present) are exhausted before anything is bought, and removing an unneeded
device is the one action with **negative** cost. The headline rule: **fix the VIOLATIONS, not every
bus, and change the controls before you buy equipment.** Measured 2026-09-02 on a ~9k-bus synthetic
planning model across five dispatches: a dozen emergency overvoltages went to **zero** with one free
setpoint change and one reactor, after a first estimate that was too large by a factor of ~50; and
some forty overloads went to one with rating increases and a handful of parallel circuits.

## Connections

- **Up:** [Home](../index.md) · [violation-remediation](../demos/violation-remediation.md) (the
  diagnose-then-test loop on a small case)
- **Across:** [remediating-n1-contingency-violations](remediating-n1-contingency-violations.md)
  (the N-1 loop this feeds, where three of these rungs turn out to be unavailable and the free-bump
  cap does not transfer) · [ltc-regulation-checks](ltc-regulation-checks.md) (the tap rung) ·
  [one-device-per-voltage-pocket](../concepts/one-device-per-voltage-pocket.md) (where a new device
  goes) · [ranking-new-devices-by-severity](ranking-new-devices-by-severity.md) (which violation to
  spend an action on) · [unloaded-ehv-stub-overvoltage](../concepts/unloaded-ehv-stub-overvoltage.md)
  (an overvoltage a tie fixes better than a reactor)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md) (`CreateData` silent
  no-op, two-character IDs) · [save-powerworld-case](save-powerworld-case.md) ·
  [sizing-a-device-whose-impedance-determines-its-own-flow](../concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md)

## Content

### The pricing rule

An action costs the number of **devices it adds**, gross, never netted against removals. A
settings change costs 0 no matter how many units it touches. A rating change costs 0 because no
equipment is bought. The ladder order below is therefore the objective itself.

| cost | meaning |
|---|---|
| **−1** | removes a device |
| **0** | free: a settings change, or a rating or cooling-stage change on equipment already installed |
| **1** | one new device |
| **n** | n parallel circuits or units is n interventions, never one record |

### Rung 0: settle which band you are judging against, first

The contingency band and the normal band are different criteria. Re-scoping the same case from a
`[0.90, 1.10]` band to a `[0.94, 1.04]` normal band took the base-case count from about a dozen
violations to about a thousand buses, two orders of magnitude. On one dispatch alone, the buses over
1.06 pu outnumbered those over 1.10 by ~15×, and those over 1.04 outnumbered those over 1.06 by ~6×.
**Settle the criterion before sizing anything, and record it as a decision.** An unrecorded band is
how a study silently changes scope.

### The voltage ladder

Undervoltage and overvoltage need separate ladders because the corrective sign is opposite.

| tier | action | cost | bound |
|---|---|---|---|
| **V0** | transformer tap: re-point an LTC's regulated bus, or correct a fixed ratio | 0 | `XFTapMin` / `XFTapMax` |
| **V1** | raise `GenVoltSet` | 0 | walk in **≤0.0025 pu steps** |
| **V2** | bump an existing capacitor bigger | 0 | the device's own `SSMaxMVR` |
| **V3** | new capacitor | 1 | walk up in **50 MVAr steps** |
| **V1′** | lower `GenVoltSet` | 0 | same 0.0025 pu walk |
| **V2′** | bump an existing reactor bigger | 0 | the device's own `SSMinMVR` |
| **V2″** | **remove an unneeded capacitor** | **−1** | |
| **V3′** | new reactor | 1 | walk up in 50 MVAr steps |
| | **remove an unneeded reactor** (for undervoltage) | **−1** | |

**V0 goes first, ahead of the setpoints.** A tap is a ratio, not a source, so it only works where
the *other* side has headroom, but where it does it costs zero and is almost perfectly local
(measured max |dV| of 1e-5 on every untouched bus). It must precede V1. On a case with generator
step-ups modelled, the generator terminals are real buses, so raising every setpoint raises all of
them and blocks V1 outright; fixing the taps first makes V1 available. Measured: it cleared over a dozen GSU terminals of 5–12% overvoltage for zero devices. On a fleet
whose LTCs are already live, re-pointing the regulated bus beats writing a fixed tap, and **a
mis-pointed LTC can cause the violation next to it**: one ran its tap to the limit holding a healthy
bus and drove the other side to 1.126 pu. See [ltc-regulation-checks](ltc-regulation-checks.md).

**Removal comes before adding the opposite sign.** Adding a reactor to cancel an unneeded
capacitor is two devices doing the work of zero, so any ladder that can both add and remove must try
removal first. Undervoltage is usually the common direction after contingencies (measured 2026-09-02
on one N-1 sweep of a ~9k-bus synthetic planning model: about eight undervoltage rows for every
overvoltage row), so do not build the removal rung for capacitors only.

Two eligibility rules that look alike and are opposite:

- **Bumping ignores which contingency placed the device.** One bus violating under four drivers is
  one bus, not four targets; treat it as four and four devices land beside it.
- **Removal excludes devices this run placed for another target.** That device is load-bearing for
  a target already worked, and removing it re-breaks that one silently. The two then oscillate.

### Rung 1: generator voltage setpoints. Free, and usually the dominant lever

Check `GenVoltSet` before anything else. On the measured case **every closed unit sat at exactly
1.0400**, identical to the normal high limit, so every bus picking up line charging floated
*above* it. **The system was scheduled high.** Walking 1.04 → 1.02
across all five dispatches took the emergency overvoltages from twelve to two, at zero cost.

**Walk it, do not jump it.** One dispatch *failed to converge* at 1.03 and 1.02 as a single write,
while converging at both 1.04 and 1.01 either side: non-monotonic, so the step was the problem, not
the setpoint. Re-walked in **0.0025 pu steps carrying each solution forward**, every setpoint
converged. The same rule applies to walking a shunt up.

**There is a floor.** Pushing further converts overvoltage into undervoltage: at 1.00, dozens of
buses fell under 0.94 pu and two under 0.90. The usable window on that case was ~1.0125–1.0225.

**It runs in both directions.** A case **already** walked down with **zero overvoltages** has
headroom to walk back **up**, and that is again the free lever. Measured 2026-09-04: the entire N-0
problem was one undervoltage at 0.8986 pu, and one 0.0025 step up cleared it for zero devices. **It
was still declined, for two measured reasons.** Free is not the same as best:

1. **The margin was a rounding.** 0.9006 against a 0.90 limit is +0.0006 pu. One 25 MVAr capacitor
   at the violating bus gave **+0.0188, thirty times more**, for one device.
2. **The free lever is not free once the GSU low side is a real bus.** Raising every setpoint raises
   every generator terminal: the worst went 1.143 → 1.159 pu, on a machine already 14% above
   nameplate. The capacitor *lowered* it.

So the price of a system-wide setpoint move is paid at the generator terminals. Screen GSU terminal
voltage alongside the transmission counts whenever you walk a setpoint on a case with step-ups.

### Rung 2: one reactor (or capacitor) at the worst remaining bus. Size by walk-up

After rung 1 the entire remaining emergency problem was **one bus in two dispatches**. A reactor
walked up in 50 MVAr steps until the bus cleared:

| target | MVAr |
|---|---|
| clear 1.10 (emergency) | **−200** |
| clear 1.06 | −800 |
| clear 1.04 | −1,420 |

Verified across all five dispatches: zero emergency violations anywhere, no new undervoltage in any
dispatch, the minimum voltage moved by at most 0.0001 pu, and it *improved* the three dispatches
that did not need it. **Verify across every dispatch, checking the undervoltage end**: a reactor
absorbs at peak too.

Seed a new shunt to its expected dispatch, never to `SSNMVR = 0`: a cold-started shunt can diverge a
stressed case by yanking reactive sources to zero as the solver's initial guess. `SSVLow < SSVHigh`
is mandatory; a zero-width band cannot regulate.

### Rung 3: capacitor removal. Sound idea; usually no target

Removing a capacitor at a bus that is overvoltage in several dispatches has **negative device
count**, the only such lever. Screened it and found **zero candidates**, because in the
overvoltage dispatch the controller had already backed them off (at peak almost every
capacitor was dispatched; at minimum load almost every one sat at zero). Screen it anyway, because it
is cheap, but expect nothing where the fleet regulates.

### The thermal ladder: rating or conductor first, parallel only where it cannot reach

| rung | action | cost | cap |
|---|---|---|---|
| **BUMP** | line rating increase | 0 | **1.5×** |
| **COOLING** | transformer cooling stage (fans) | 0 | **1.33×** |
| **CONDUCTOR** | reconductor: new rating **and** new R/X/C | 1 | catalogue-bounded |
| **PARALLEL** | parallel circuit | n | `n = ceil(m) − 1` alone; across a corridor see [remediating-n1-contingency-violations](remediating-n1-contingency-violations.md) |
| **PARALLEL_UNIT** | parallel transformer unit | n | as above |

**The ordering rule is worth most of the circuits.** A parallel-first pass on the same few dozen
overloaded branches wanted **32 parallel circuits**; rating-first needed **8**.

**The caps are validity boundaries, not conservatism knobs.** A rating increase is honest only up
to the point its "impedance unchanged" claim holds: lines ×1.5 is where HTLS reconductoring stops
giving ampacity at unchanged geometry; transformers ×1.33 is a cooling stage (rating up, impedance
untouched). Because a rating bump is priced at zero, the cap is also the only bound on an otherwise
unbounded free action. Raising it to make a number look better is the wrong move.

**Evaluate every cap cumulatively, against a write-once baseline the case carries.** If the
denominator is the rating the *previous* bump wrote, the cap measures its own output: ×1.33 applied
three times is ×2.36 with every pass reporting compliance. Store the original rating once and judge
against it. Two passes on one case lineage (2026-09-03 and 2026-09-14)
both measured against the current rating, and tracing the lineage showed they had touched disjoint
branch sets, so nothing compounded. That was luck, not a check.

**Expect the middle of the thermal ladder to be missing on a synthetic case.** A reconductor needs
the line's present conductor, and on the measured case only about 6% of branches recovered one
exactly (measured 2026-09-03), because the rest were rated by a derate or headroom script rather
than by a conductor choice. The ladder then escalates from a free bump straight to a parallel
circuit ([remediating-n1-contingency-violations](remediating-n1-contingency-violations.md) has what
can still be recovered).

On the measured case the bumps were small (median ×1.08, max ×1.35); only three branches, all
generator step-ups, exceeded a cap and had to go parallel. One policy that worked: prefer rating or
conductor at 69/138 kV, and accept a parallel circuit at 345 kV, where a re-rate is a major
reconductor anyway and a parallel EHV circuit is the asset the network wants.

**Preserve the rating ratio.** Copy the rating *set*, do not invent it. On most branches of a
synthetic case `LineAMVA:1` and `LineAMVA:2` (rates B and C) are 0.0 and must stay 0.0; scaling only
`LineAMVA` and leaving a fabricated B/A ratio behind silently creates emergency headroom. But some
branches carry `B = C = A`, and forcing those to 0.0 strips ratings that exist. Scale B and C with A
where they are non-zero; leave them at 0.0 where they are 0.0.

**A parallel circuit is a SEPARATE ROW with the SAME impedance.** Never "halve X on the existing
row": an N-1 outage of the merged row then removes both circuits at once, and it scored one action
at +9,171 violations against a measured +2.

**Sizing conventions that are load-bearing:**

- The multiplier is measured against the **original nameplate**, always, and the request is
  `standing × m`. Sizing against the current rating once wrongly refused almost every corridor.
- Carry **~2% headroom** (× 1.02). Sized to exactly the measured flow, the branch lands at
  precisely 100% and any redistribution puts it back over, so the ladder revisits what it paid for.
- A reconductor **derives** R/X/C by ratio and never recomputes them absolutely, and `Xa` is
  **not monotone in MVA**: an upgrade can raise X.

**A rating increase asserts the branch was under-rated.** That is defensible on a synthetic case
whose ratings were assigned rather than surveyed, but state the assumption rather than letting a
number quietly disappear, and see *Do not bump a rating without provenance* below.

### Cheap actions usually left off the menu

| action | cost | why it is worth naming |
|---|---|---|
| **enable inverter-based reactive capability** | 0 | synthetic cases often model solar and storage at **zero MVAr**. A modelling decision, not equipment, and possibly the largest voltage lever on the case |
| **switching / topology reconfiguration** | 0 | opening a line to redirect flow. No hardware, but it interacts with the contingency set |
| **series compensation** | 1 | rarely considered |
| **SVC / synchronous condenser** | 1 | usually owned by a separate reactive planning study |
| **generation redispatch / load shedding** | — | an operating answer, not a build; out of scope for a planning study |

### The traps, all paid for

**Solve the violations, not the distribution.** Targeting "every bus inside the normal band"
produced an estimate of ~9–10 GVAr and around twenty new EHV banks. Targeting the actual violations
produced **200 MVAr**. The inflated figure came from a linear extrapolation of single-device tests
stretched ~7× beyond anything measured, ignoring that the candidates all relieved substantially the
same buses. **Not every bus has to be in range.**

**Site by reach, never by dV/dQ.** The most locally sensitive bus is the worst place to put a
device. One candidate moved 0.29 pu for 300 MVAr, 8–30× more sensitive than any other, and it
**fixed the fewest buses and created three new undervoltages**. High dV/dQ means a *weak* bus.

**"Fix the worst first" does not predict reach; volume does.** Sizing each candidate to genuinely
clear its own bus, then counting what else fell:

```
corr(worst voltage, buses fixed)  =  0.042      <- essentially zero
corr(MVAr installed, buses fixed) =  0.971      <- almost perfect
```

Efficiency was near-uniform at ~100–130 buses per 1,000 MVAr regardless of which bus. Worst-first
still wins as a tie-breaker, because a worse bus needs more MVAr to clear, but the volume is doing
the work.

**Do not bump a rating without provenance.** On the measured case nine of ten overloaded corridors
had **zero rating drift**: the sizing was correct for the network it was done on. The AC/DC gap
(1.7–5.6× in real power) came from the network having churned by about 30% since, under a
**lossless DC** sizing solve that never saw the case's AC losses. A bump there asserts an
under-rating nobody measured.

**Re-measure thermal after a voltage action, and do not guess the sign.** The intuition is that
lower voltage means higher current for the same power, so the voltage fix should worsen thermal.
**Measured, it mostly did the opposite**: the reactor removes reactive flow, and that cuts MVA by
more than the voltage drop raises current. Four of five dispatches improved and one overload
disappeared; one dispatch's worst branch degraded by 2.9 points. The sign is case-dependent and
cheap to measure, so measure it.

**Diagnose a shunt fleet by measurement, not by its settings.** Two wrong diagnoses came before the
right one: "the reactors are exhausted" (they read 100% dispatched at EHV, but that was a
consequence of the 1.04 setpoints, not a limit) and "the controller is disabled" (`SSAutoControl`
read `None`). **The shunts did regulate**: the same fleet ran tens of GVAr
capacitive at summer peak (over twenty) and over ten GVAr inductive at minimum load, tracking load. Writes of
`SSAutoControl = YES` read back `None` over raw SimAuto (suspected, not confirmed). Judge the fleet by whether its
dispatch moves, not by a settings field.

**Read `SSMaxMVR` / `SSMinMVR` before planning a band change, not just `SSNMVR`.** A bank already
sitting at its own limit has no travel, so a band change on it is free and worth nothing. Measured
2026-09-14: every 765 kV reactor at a violated bus read `SSNMVR == SSMinMVR`, and a planned "tighten
the band to the criterion" rung had to be struck.

### Two screening traps on a case with three-winding transformers

- **Star and tertiary buses are not violations.** A three-winding conversion adds a fictitious
  star point (1.0 kV nominal) and often a dead tertiary per unit, and some read above 1.10 pu. The
  tertiary carries no current, so its pu voltage simply equals its star point's. Screen network buses
  only (69 kV and up, excluding step-up terminals, star and tertiary buses); on the measured case
  that left about four buses in five. A naive screen reports violations that do not exist.
- **IDs are two characters.** A new shunt with `ShuntID` `C10` silently becomes `C1`; the create
  reports success and the lookup that follows fails on a bank that is really there. See
  [adding-devices-esapp](adding-devices-esapp.md).

### Recipe

1. Fix the band. Record it.
2. Check the taps ([ltc-regulation-checks](ltc-regulation-checks.md)), then read `GenVoltSet`. If
   the setpoints equal the limit, that is the problem: walk them in ≤0.0025 pu steps, carrying each
   solution forward, and stop before undervoltage appears.
3. Re-measure. Whatever emergency violations remain are usually a handful of buses.
4. Walk a reactor or capacitor up at the worst survivor in small steps; stop at the first size that
   clears.
5. **Verify across every dispatch**, checking the opposite end too.
6. Re-measure **thermal**: the voltage action moves it, in a direction you cannot predict.
7. **Thermal: rating or conductor first, parallel only where a cap cannot reach.** Lines ×1.5,
   transformers ×1.33, cumulative from the original rating. Union the requirement across dispatches
   so all cases keep one topology.
8. Screen for removable capacitors (cheap; often empty).
9. Only then consider hardware beyond the above.

**Guards worth writing into any script that does this**, all of which fired or would have:
`CreateData` silently no-ops, so assert the branch or shunt count moved by exactly what you added;
write the full field row; read ratings back off the live case before saving; refuse to save any
case whose violation count got worse on the metric the action targeted; back up first; and save
with the script `SaveCase` plus a file-exists check ([save-powerworld-case](save-powerworld-case.md)).


---

# ==== remediating-n1-contingency-violations.md ====

---
type: method
domain: synthetic-grid
topic: contingency
aliases: [n-1-remediation, contingency-remediation-loop, remediating-contingency-violations,
  contingency-remediation-playbook, fix-n-1-violations, make-the-case-n-1-clean]
tags: [synthetic-grid, contingency, n-1, thermal, voltage, remediation, powerworld, loop]
---

# Method: Remediating N-1 contingency violations

## Abstract

The loop that drives a solved case's **post-contingency** violations to zero or to an explained
residue: sweep, classify, rank **elements**, spend the cheapest action that works, re-measure,
and stop when everything left is either fixed or explained. The base-case ladder in
[remediating-base-case-violations](remediating-base-case-violations.md) does **not transfer
unchanged**: the N-1 regime is larger, three of its rungs turn out to be structurally unavailable
on a synthetic case, and a free-rating-bump cap that is comfortable on intact-case overloads sits
below the *median* of the contingency-induced ones. Measured 2026-09-13/14 on a ~9k-bus synthetic
planning model with about eleven thousand contingencies: a few dozen actions and five new devices
cut the violated elements by about a quarter in one pass.

The headline rule: **an element is the unit, a sweep is the round, and every number is measured
rather than asserted.** This toolchain fails by returning a confident, smaller answer, not an
error. **The playbook** section is the eight-step order of play that took the
last residue to a clean full N-1 (2026-09-24).

## Connections

- **Up:** [Home](../index.md) · [violation-remediation](../demos/violation-remediation.md) (the
  diagnose-propose-test-rank loop on a small case; this page is that loop at scale)
- **Across:** [remediating-base-case-violations](remediating-base-case-violations.md) (the N-0
  ladder and action menu this diverges from) ·
  [one-device-per-voltage-pocket](../concepts/one-device-per-voltage-pocket.md) (why the voltage
  half is cheap) · [reading-violationctg](reading-violationctg.md) (the row contract and its
  identity traps) · [reducing-a-contingency-set](reducing-a-contingency-set.md) (what scopes a
  parallel sweep) · [parallel-contingency-solve](../concepts/parallel-contingency-solve.md) (the
  sweep itself) ·
  [diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md) and
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md) (the
  non-converging residue, playbook step 7) · [ltc-regulation-checks](ltc-regulation-checks.md)
  (the free voltage levers the playbook tries first) ·
  [agc-participation-factors](../concepts/agc-participation-factors.md) (the swing taking all
  make-up power)
- **Traps it depends on:**
  [sizing-a-device-whose-impedance-determines-its-own-flow](../concepts/sizing-a-device-whose-impedance-determines-its-own-flow.md) ·
  [aggregate-clauses-cannot-bound-one-row](../concepts/aggregate-clauses-cannot-bound-one-row.md) ·
  [adding-devices-esapp](adding-devices-esapp.md) · [save-powerworld-case](save-powerworld-case.md)

## Content

### The loop

1. **Sweep** the full contingency set once. This is the expensive step and the round is built
   around paying it once.
2. **Classify** every row, and **rank violated ELEMENTS**, not contingencies. An element that
   violates under forty-five different outages is one target, not forty-five. Ranking
   contingencies instead re-spends the ladder on the same asset.
3. **Act** on the worst element with the cheapest rung that reaches it.
4. **Propagate** the action wherever it applies, and **re-sweep** to measure what else it
   cleared, and what it broke.
5. **Reduce** the active set by everything that no longer violates, so later rounds are cheaper.
6. Stop when the set is empty, or when everything left is in a failure file **with a reason**.

"All violations solved" in practice means **all solved or all explained**. A residue with a
recorded reason is a deliverable: it is the design finding the study exists to surface. An
*unexplained* residue is the only real failure.

### Severity: one number, and two ways to get it wrong

Rank on one dimensionless quantity, "fraction beyond the limit", so a voltage and a thermal
violation can be ordered against each other at all
([ranking-new-devices-by-severity](ranking-new-devices-by-severity.md)).

- **Voltage ranks on signed deviation over its limit, never on the reported percentage.** That
  percentage's polarity is three-way (Trap 2 in [reading-violationctg](reading-violationctg.md)).
  The cost here: sorting on it selects a bus **0.0001 pu** below its limit as the worst
  undervoltage while the genuinely worst sits **0.11 pu** below, so the round spends its one
  action on nothing.
- **Thermal ranks on the ATTRIBUTED magnitude**, `min(exceedance, addition) / rating`, never raw
  exceedance. Subtracting the base decides *which* rows count, not *how big* they are.
- **An unsolved contingency emits no rows at all**, so it makes a sweep read *cleaner* than the
  truth. It carries no element and cannot be remediated. Route it to a diverged file and never
  let "no rows" sort as "nothing wrong".

### Three rungs of the N-0 ladder are structurally unavailable here

Catalogued, built, and unreachable, each for a different reason. All three were discovered by
trying:

| rung | why it is unavailable |
|---|---|
| transformer cooling stage | needs to know whether the stage is already spent; nothing in the case records it, and inferring it from rating arithmetic leaves most units unknown. An unknown stage is not an available one |
| bump an existing shunt | needs per-device headroom limits; on this case family those fields are **zero fleet-wide**, so there is no headroom to work within |
| reconductor by identity | the conductor is **not stored**: the conductor-type, bundle and length fields are populated on *no* branch. See below for what can be recovered instead |

**Expect the middle of a ladder to be missing on a synthetic case**, and expect to find out
only by attempting the rung. A rung that silently never fires reads exactly like a rung that
never helps.

### The free-bump cap does not transfer from N-0 to N-1

A free rating increase is honest only while it can be read as *"the rating was assigned
conservatively"*. Where that stops is a policy choice, and the policy that is comfortable
against intact-case overloads is the wrong one here.

Intact-case overloads on this case family cluster just above nameplate. **Contingency-induced
overloads do not**: measured across ~150 thermal elements, the median required multiplier sat
*above* the policy cap, so **more than half of all thermal violations were purchased hardware
by default**. Relaxing the cap by one notch cut the purchased circuit count by roughly **3×**,
and by three notches by roughly **10×**.

**The cap is the answer, not a tuning knob.** Set it against the regime you are in, record it
as a decision, and report the sensitivity rather than the single number, so the reader sees what
the choice costs.

### Fixing the highest voltage first does not relieve the rest

A natural strategy is to fix EHV thermal violations first and let the redistribution relieve the
sub-transmission ones. **Measured, on this case, it does not.** After clearing every violation at
345 kV and above, the median change across the ~100 remaining 69/138 kV elements was **−0.000
percentage points**, and the single best improvement anywhere was under one point, on a branch
still over its limit.

EHV fixes here were **electrically local**. The sub-transmission problem is its own problem. It
is cheap to assume the cascade exists and expensive to plan around it.

### A parallel circuit is counted across the corridor

Adding one circuit beside `n` existing ones splits the flow `n+1` ways, so the count that
matters is `ceil(m · n) − n`, not `ceil(m) − 1`. On a corridor whose circuits all violate
together, **one added circuit clears every circuit on it**, which is why a seven-element EHV
problem can be four devices.

Use `ceil`, never truncation: truncation gives one circuit fewer than needed, which is the
cheaper answer and therefore the direction that wrongly survives a review.

### What can be recovered when the conductor is not stored

Where a branch's conductor identity is absent, two handles remain, and **they disagree**:

- **the rating**, matched to a catalog entry. Weak, because assigned ratings need not
  correspond to any real conductor. Measured here: nearly a quarter of sub-transmission lines
  were rated at values sitting in a *gap* in the catalog, where no conductor exists.
- **the impedance ratio** `R/X`, matched to a catalog's per-mile `Ra/Xa`. **Length and base both
  cancel**, so this identifies a conductor without knowing the line's length. Measured: ~90% of
  sub-transmission lines matched a catalog conductor within 5% on this ratio, against a median
  error of ~2%.

**Open question, unresolved as of 2026-09-14.** The two handles imply *different* conductors, by
a median of ~37%, with the impedance consistently implying a **larger** conductor than the rating
does. Either the ratings are derate artifacts, in which case most sub-transmission thermal
violations are reporting artifacts rather than real overloads, or the ratings are correct
because the limiting element is terminal equipment rather than the conductor, which is ordinary
in a real utility model. **Do not assume either way.** The pattern also has a hard boundary: at EHV the impedances matched no catalog conductor at all, so
the ratio handle is sub-transmission-only.

A reconductor still **derives R/X/C by ratio** and never recomputes them absolutely, and a
reactance that *rises* with rating is normal (the catalog is not monotone), so report it rather
than assume it away.

### Guards this loop cannot run without

Every serious failure met building this announced itself as success. None raised an exception.

- **A partial sweep reads as a clean grid.** One contingency that crashes the solver takes its
  whole worker chunk with it, and a driver that counts a dead chunk as zero contribution quietly
  removes a quarter to a half of the case. Record per-round completeness as data, and make the
  next stage *refuse* a degraded round rather than trusting a reader to notice.
- **Not having measured coverage is not evidence of coverage.** A sweep that returned zero
  violation rows because every worker died is the most dangerous artifact this loop can produce:
  it is indistinguishable from success by inspection and arrives looking like a win.
- **A write that no-ops reads as "the fix did not help".** Read every change back and confirm it
  against what was requested, and confirm the *object* is the object you asked for, not merely
  that its numbers match.
- **A guard can be wrong in the safe direction and still cost you.** A read-back tolerance
  tighter than the solver's own storage precision rejects every successful write; the failure
  looks like diligence and trains the reader to loosen guards that work.
- **An acceptance test built from counts and maxima lets one element get much worse.** See
  [aggregate-clauses-cannot-bound-one-row](../concepts/aggregate-clauses-cannot-bound-one-row.md).

### Verify it worked

- Violated **elements** fell, and the set that cleared is the set that was acted on.
- **Nothing new appeared**, or, if it did, it is named and understood. A fix that trades one
  violation for another is not a fix.
- The round's sweep was **not degraded**, and the shortfall between dispatched and total is
  exactly the deliberately excluded labels, with no unexplained remainder.
- Actions are replay-sufficient: object type, key fields, field, value before, value after. The
  ledger is the only reconstruction path when cases are written once at the end.
- **A cleared element stays cleared.** One sized to its measured flow plus a thin margin can
  return once later fixes redistribute flow onto it. If that happens, the margin is too thin,
  and a fix that does not stay fixed is churn.
- **A re-rating can pass a "no worse than base" score without fixing anything.** Raising a
  branch's rating lowers its loading percentage while the flow stays exactly the same. So a
  score that counts an element only when it is more than *k* points worse than base will
  clear an overload by relabelling it. The branch can still sit well above 100% after the
  contingency. Measured 2026-10-06 on Synth2k with two large added loads: a package of 10%
  rating bumps alone passed that score. Nine of its bumped branches stayed at 102–133% after the
  contingency. With the bumps undone, the result matched the unremediated case row for row. A
  competing package of parallel circuits also passed, and kept most of its relief with its bumps
  undone. Two guards close this:
  - require every element an action touched to end **below 100%**, not merely "no worse
    than base";
  - re-score the final case on **base ratings**. Whatever comes back is what the bumps were
    hiding.

### The playbook: from a residue to a clean full N-1

The loop above takes a case most of the way. This is the order of play that took the last
residue (a few dozen (dispatch, element) pairs across thermal, GSU, voltage and non-converging
outages) to **zero on a full N-1 in every dispatch**. Measured 2026-09-22 to 2026-09-24 on a
~9k-bus synthetic planning model, five dispatches, one grid sized to the worst-case envelope.
It cost roughly a dozen reconductors, six new lines, one reactor and two LTC setting changes.

1. **Collect from a full sweep, and count elements, not pairs.** Twenty unsolved pairs were
   seven outages; seventeen GSU pairs were eight transformers. Tabulate per element: class,
   dispatches, worst value, and every driving outage. Screen three-winding star and dead
   tertiary buses out first: they are not network buses, and one high star bus can appear
   under almost every outage
   ([reducing-a-contingency-set](reducing-a-contingency-set.md#a-re-check-set-that-deletes-nothing)).
2. **Re-seed the sweep scope from that full sweep.** A reduced scope that shrank over many rounds
   had set aside **every** outage still driving a violation, and several had never been in scope
   at all. Put each violating and unsolved outage back to active before the next round.
3. **Judge each round against the last FULL sweep whenever the scope changed.** A round is scored
   only on outages both sweeps dispatched, so an outage newly in scope has no "before" and its fix
   is invisible: the score reads 0 → 0 while the target cleared.
4. **Diagnose GSU overloads before buying anything.** Three distinct causes, told apart by
   comparing the machine's MVA capability with the step-up's own rating:
   - **the swing takes all contingency make-up power** (participation factors all zero, see
     [agc-participation-factors](../concepts/agc-participation-factors.md)): the swing unit's
     step-up overloads on every *other* unit's trip, and a neighbour becomes the island swing
     when the swing's own step-up trips. A modelling choice, not a network problem.
   - **a parallel step-up unit trips and the machine stays on**: the survivor carries the whole
     machine. A contingency-definition question.
   - **the step-up is rated below its own machine**: a real sizing defect.
   Whether to fix the model or raise ratings is the study owner's call. If step-ups can be
   custom-built, raise **every unit** of a multi-unit step-up to the worst post-outage flow ×
   1.02; the rating moves no flow, so it cannot create a violation elsewhere.
5. **Thermal on lines: the free bump, then metal.** The bump cap is **cumulative from the base
   rating**, not per bump: a line already bumped once may have almost nothing left. Above the cap,
   reconductor, identifying the present conductor from the **base** rating within 5% of a catalog
   entry and choosing a conductor ≥ 1.2× the rating, which lands ~20% post-outage headroom rather
   than the 2–6% a minimum step leaves. Where the conductor cannot be identified, clone a parallel
   circuit with its own contingency record. Converting earlier bumps to reconductors one line per
   round costs little and buys real margin.
6. **Voltage: read the neighbourhood, then try free levers before any device.** For each bus, sum
   the MVAr its own substation makes and the headroom (up for undervoltage, down for overvoltage)
   in every substation within three hops. Then probe each free lever **alone, from a fresh open**
   (generator setpoint, LTC regulation band, LTC tap limit, switched-shunt band) under the
   driving outage, checking N-0 stays in band. Only then walk a capacitor or reactor in 25 MVAr
   steps. A device walked to "just clears" can miss by ~1e-4 pu under the full contingency solve;
   one more step closes it.
7. **Non-converging outages are collapses of radial-by-N-1 pockets.** Diagnose with
   [diagnosing-a-non-converging-contingency](diagnosing-a-non-converging-contingency.md), fix with
   a new tie per [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md).
   Then **run a full sweep before believing it**: the reduced sweep called the new ties clean, and
   the full sweep found them overloading the feeders of a **two-tie landing substation** when
   either upstream source tripped, up to ~140% on an 8-mile feeder. Land a tie on a substation
   with three or more ties, or reinforce the landing's feeders as part of the same package. On
   Synth40 (2026-09-24), a full plan of two second ties to large new loads, two radial-closing
   circuits and six re-rated branches left 0 violation rows and 0 islanding outages.
8. **Finish with a full N-1 of the final network, then write the cases.** Save in a format your
   Simulator build writes correctly ([save-powerworld-case](save-powerworld-case.md)). To ship
   post-contingency results, run Solve All in-process with any solver-crashing label skipped for
   the solve and un-skipped after, then cold-open each file and check branch, shunt and
   contingency counts and the solved count. PowerWorld's own per-contingency violation counts in
   those files still include the star and tertiary artefacts.

#### Three findings from the voltage work

- **An LTC can lose its regulated bus after an outage and park its tap.** When the outage leaves the
  LTC's far side as a dead end with no load, moving the tap can no longer change the regulated bus,
  so the tap stays where N-0 put it and the dead-end bus floats at V(regulated side) × tap: ~1.125 pu
  from a 1.075 tap. **Capping `XFTapMax`** so V × tap stays under the limit fixes it for zero devices
  and binds only in the dispatch that parked the tap high. A reactor also works, but spends a device
  holding an unloaded bus down.
- **Lowering an LTC's regulation band can lift the bus on its HIGH side.** The low side then draws
  less reactive power off the system above it. Measured: a 0.02 pu lower band on one nearby LTC
  lifted a sagging 345 kV load tap by ~0.01 pu under its outage, where generator setpoints and shunt
  bands gave under 0.002. Raising the same bands made it **worse**, so probe both directions.
- **An LTC tap does not return when its band is restored.** A lever probe that undoes a band change
  leaves the tap where it moved, so only the **first** change after a fresh open is a clean
  measurement; later rows in the same session are contaminated.


---

# ==== removing-empty-buses.md ====

---
type: method
domain: synthetic-grid
topic: case-audit
aliases: [removing-empty-buses, empty-bus-cleanup, dead-end-bus-removal, blank-bus-removal,
  delete-dead-buses, inflated-islanding-count]
tags: [synthetic-grid, powerworld, esapp, topology, cleanup, transformer, islanding, contingency]
---

# Method: Removing empty buses from a case

## Abstract

How to find and delete voltage levels that carry nothing (no load, no running plant, no shunt, no
line out of the substation) and hang off one transformer, without changing the power flow. Use it
when islanding or N-1 counts are inflated by outages that only cut off dead buses. Measured
2026-10-04 on a ~9k-bus synthetic case: about one in eighty substation voltage levels qualified,
and deleting them moved no voltage or flow at all. The two shapes that look empty and must stay
are a pass-through bus in a transformer chain and a winding of a three-winding bank.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  (the islanding screen whose zero-MW rows these buses fill) ·
  [reading-violationctg](reading-violationctg.md) (islanding does not show as a violation) ·
  [ltc-regulation-checks](ltc-regulation-checks.md) (why a tap changer on a deleted transformer
  matters) · [case-data-lint](case-data-lint.md) (other data defects a case solves through)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md) ·
  [save-powerworld-case](save-powerworld-case.md)

## Content

### What counts as empty

Work per **substation voltage level**: every network bus of one nominal kV in one substation. Fold
step-up (GSU), three-winding star and tertiary buses into the network bus they feed, so a plant
behind its own step-up counts on the bus it feeds. A level is a delete candidate only if **all** of
these hold in **every** dispatch:

1. no load record, no shunt, and no unit producing MW **or Mvar**. A unit switched on at 0 MW but
   holding voltage with Mvar is not empty, and a screen that checks MW alone misses it;
2. no line leaving the substation at that voltage;
3. one outage of its transformer cuts it off, so it is a dead end and not a pass-through;
4. nothing that stays regulates a bus on it, and deleting it removes no tap changer that regulates
   a bus that stays.

Units that never run in any dispatch do not make a level non-empty. They go with the bus, so list
them.

### Two shapes that look empty and must stay

- **Pass-through.** An empty middle bus in a 345 → 138 → 69 kV chain carries the 69 kV network's
  supply through two transformers. No single outage strands it, so rule 3 catches it. On the
  measured case these carried from a few MW to a couple of hundred MW, and deleting one dropped a
  nearby 69 kV bus below 0.94 pu.
- **Three-winding banks.** An empty bus on one winding of a three-winding transformer cannot be
  cut off alone. Rebuild the bank as a two-winding unit first, or leave it.

The tap-changer rule looks like it blocks an empty 345 kV stub whose 345/138 transformer is set to
hold the 138 kV side. Measure before obeying it: with no current through the transformer the tap
sits at 1.000 and holds nothing. Deleting a couple of dozen such stubs moved voltages by at most
0.0002 pu.

### Delete and verify

1. Delete the whole piece the transformer outage cuts off: the bus, its GSU and star or tertiary
   buses, the transformer, the idle units, and **every contingency whose element was deleted**.
2. Re-check that contingencies = contingency elements = lines + two-winding + three-winding ÷ 3.
3. Solve warm and from a flat start. Compare every remaining bus voltage and branch flow against
   the original, and compare flat start against the **original's** flat start, because a flat
   start can land a few MW away from the saved solution on its own.
4. Gate on no new N-0 violation, then save to a temp name, rename, and cold-reopen
   ([save-powerworld-case](save-powerworld-case.md)).

The transformers removed carried exactly 0 MW and 0 Mvar, so the result was zero change in all
five dispatches, and the full N-1 afterwards matched the earlier one label for label.

### PowerWorld traps met on the way

- **Deleting a three-winding transformer needs `BusIdentifier` as its key.** Keyed on the three bus
  numbers, the delete is refused as not adequately defining the object.
- **Loads, units, shunts, branches and substations each carry their own area and zone**, separate
  from their bus. Moving buses alone leaves every device behind.
- **A blank write to the case's one-line link is ignored.** To clear it, rebuild from a copy that
  never had it.
- **SimAuto cannot create a new one-line.** `LoadAXD` into a new diagram fails with "No MDI forms
  are currently active". Draw the diagram in the GUI.


---

# ==== reviewing-a-design.md ====

---
type: method
domain: cross-cutting
topic: design
aliases: [reviewing-a-design, design-review, review-a-submitted-design, tep-design-checklist,
  transmission-design-review]
tags: [transmission-planning, review, case-diff, n-1, topology, impedance, powerworld, esapp]
---

# Method: Reviewing a submitted transmission design

## Abstract

A reviewer's checklist for a transmission design handed in as a modified case beside the
base case it was built from, by a student or a team. Diff the two cases to recover what the
design added, then check six things a design can get wrong while still solving cleanly: a
load that loses service when one new device trips, a single transformer behind redundant
lines (a defect only under some criteria), four or more circuits on one right-of-way, a branch typed as a line across two
voltage levels, a per-mile reactance entered as the line total, and a line with X far below
R. **Report only. Never edit or save the submitted case.** Each finding names the device by
its key fields and gives the number behind it; every fix and trade-off stays with the
designer.

## Connections

- **Up:** [Home](../index.md)
- **Uses:** [comparing-planning-cases](../demos/comparing-planning-cases.md) (the guarded diff
  that recovers the added devices) · [new-device-contingency-aux](new-device-contingency-aux.md)
  (a contingency set for only the new devices)
- **Across:** [zone-load-multiplier-trap](zone-load-multiplier-trap.md) (load that islands
  leaves the totals silently) ·
  [converting-lines-to-transformers](converting-lines-to-transformers.md) (`BranchDeviceType`
  is derived from `LineXFMR`) ·
  [case-impedance-completeness](../concepts/case-impedance-completeness.md) (X/R as a data
  check) · [case-data-lint](case-data-lint.md) (whole-case data defects) ·
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  (where a second tie should land)
- **Traps it depends on:** [adding-devices-esapp](adding-devices-esapp.md) ·
  [handling-errors](handling-errors.md)

## Content

### Ground rules

- **Read, never write back.** Open both cases, never save either. Outage tests run in memory
  inside `pw.snapshot()`, which restores the case on exit.
- **Check the base case first.** Solve it in every scenario the design must meet. A violation
  already in the base case is not the design's fault, and the report must say which is which.
- **Diff, do not trust a device list.** Recover the added and changed devices with the guarded
  diff in [comparing-planning-cases](../demos/comparing-planning-cases.md): normalise from/to
  order, pair buses by name and kV, and compare ratings and impedance on common keys to find
  upgrades. A naive diff reports construction that never happened.
- **Diff the generators too.** Compare status, AVR (`GenAVRAble`) and AGC (`GenAGCAble`) per
  generator on `BusNum` + `GenID`, and in-service MW and capacity by area, zone and fuel type
  (code in [comparing-planning-cases](../demos/comparing-planning-cases.md), Step 2). A design can switch off a unit's voltage control or move where
  power comes from without adding a single device.
- **If the design ships as several scenario cases, diff them against each other too.** The same
  modification must appear in every scenario file. A design that differs between files is a
  bookkeeping error, and an easy one to make when several files are edited by hand.
- **Grade each finding by kind.** A *rule* breach (a written requirement, checkable with no
  solve), a *physical* failure (a live solve shows it), or a *practice* judgement (a planner
  would question it, but the threshold is opinion). Say which.

### Check 1 — every load still served with any one new device out

Outage each new line and transformer one at a time, solve, and check **served MW and bus
connectivity** at every load the design must deliver. Do not stop at thermal violations.

An islanded load is the trap. The load keeps a closed `LoadStatus`, its bus goes
`Disconnected`, and the solver converges on what is left. A status check reports success, a
thermal check finds nothing over rating, and the load is not served. PowerWorld also drops a
Disconnected bus's load out of the system totals without a word, so a before/after totals
check passes as well (both seen 2026-10-20 on a 2,000-bus synthetic case) ([zone-load-multiplier-trap](zone-load-multiplier-trap.md)).

```python
import pandas as pd
from esapp import PowerWorldError
from esapp.components import Branch, Bus, Load

intent_mw = {(9101, "1"): 600.0, (9102, "1"): 600.0}   # BusNum, LoadID -> MW to deliver
targets   = set(intent_mw)
new_br    = added_branches                           # (from, to, ckt) from the guarded diff

def served(pw):
    ld = pw[Load, ["LoadMW"]]
    bs = pw[Bus, ["BusStatus"]].set_index("BusNum")["BusStatus"]
    out = {}
    for _, r in ld.iterrows():
        k = (int(r["BusNum"]), str(r["LoadID"]).strip())
        if k in targets:
            out[k] = (float(r["LoadMW"]), bs[int(r["BusNum"])])
    return out

findings = []
for f, t, c in new_br:
    with pw.snapshot():                              # restored on exit, never saved
        pw[Branch] = pd.DataFrame({"BusNum": [f], "BusNum:1": [t], "LineCircuit": [c],
                                   "LineStatus": ["Open"]})   # keyed write
        br = pw[Branch, ["LineStatus"]]
        hit = br[(br.BusNum == f) & (br["BusNum:1"] == t) & (br.LineCircuit.astype(str).str.strip() == str(c))]
        assert (hit.LineStatus == "Open").all() and len(hit) == 1, f"outage of {f}-{t} {c} did not take"
        try:
            pw.pflow()                               # solve the way the study does
        except PowerWorldError:                      # a collapsing outage is the worst finding, keep it
            findings.append((f, t, c, None, None, "did not converge"))
            continue
        for k, (mw, st) in served(pw).items():
            if st != "Connected" or mw < 0.999 * intent_mw[k]:
                findings.append((f, t, c, k, mw, st))
```

The `LineStatus` read-back is there because a write that silently missed its branch produces
a pass for an outage that never happened. A non-converging outage is recorded, not skipped:
it is usually the worst finding of the review.

### Check 2 — a single transformer behind redundant lines (criterion-dependent)

A common shape behind a dropped load: two or more new lines into a new substation,
then **one** transformer down to the load. The lines look redundant, and that transformer's
outage islands the load.

Whether that is a defect depends on the criterion the design is judged against:

- **A brief that requires full delivery with any one new device out** (Check 1's test): it
  fails.
- **NERC TPL-001's single-element (P1) event:** consequential load loss (load directly served
  by the element removed) is permitted, and non-consequential load loss is not. A load served
  radially through one transformer is consequential load loss, which the NERC baseline allows.
  This is per NERC's TPL-001 definitions; check the current TPL-001-5.1 Table 1 and any
  regional criteria, which can be stricter.
  [finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md)
  already treats such a load as consequential load loss by convention.

Its outage can show **no thermal violation at all**, because the island carries no flow.
Check 1's connectivity and served-MW test finds it; an overload screen never does. In
the report, name the transformer, the load behind it, and the criterion you judged against.
Under a full-delivery brief, say that duplicating the lines did not duplicate the path; under
TPL-001 P1 alone, report it as consequential load loss, not a violation.

### Check 3 — four or more circuits on one right-of-way (practice judgement)

Group every in-service circuit, existing and new, by the unordered pair of substations it
joins. Flag any corridor carrying **four or more** circuits.

DC power flow and single-device N-1 both accept a stacked corridor: four circuits are four
separate devices, each survivable alone. A cost objective may even reward it, since several
lower-voltage circuits can match one higher-voltage circuit with no transformer or substation
cost. A utility would question it, because one structure failure, wildfire, ice storm or
excavation can take the whole corridor at once, and only a common-mode or tower contingency
would show that. Report it as a **judgement**, not a violation: the threshold of four is
opinion, and the design brief may not define a common-corridor contingency.

### Check 4 — a branch typed as a Line across two voltage levels

Read `BranchDeviceType` with the nominal kV of both end buses. A branch whose ends sit at
different `BusNomVolt` and whose `BranchDeviceType` reads `Line` should have been a
transformer.

```python
br = pw[Branch, ["BranchDeviceType"]]
kv = pw[Bus, ["BusNomVolt"]].set_index("BusNum")["BusNomVolt"]
br["kv_from"] = br["BusNum"].map(kv)
br["kv_to"]   = br["BusNum:1"].map(kv)
bad = br[(br.BranchDeviceType == "Line") & ((br.kv_from - br.kv_to).abs() > 0.5)]
```

**Trust the device-type field, never the rule "the ends differ in kV, so it is a
transformer".** That inference relabels the defect away. A DC solve ignores voltage
magnitude, so this case solves and its cost looks plausible. How the type is set is on
[converting-lines-to-transformers](converting-lines-to-transformers.md). Run the check on
the base case too: if the base already has such branches, report only the new ones.

### Check 5 — per-mile reactance entered as the line total

A design brief usually gives reactance per mile. The common error is entering that per-mile
value as the whole line's `LineX`. On a 100 MVA base, an `X` of about **2e-4 pu on a 500 kV
line** or **1.2e-3 pu on a 230 kV line** is per-mile scale. A line tens of miles long
should carry tens of times that.

Divide each new line's `LineX` by its length and compare with the brief's per-mile value.
Length comes from `LineLength` where the designer entered it, otherwise from the distance
between the end buses (`pw.buscoords()`). A ratio near `1/length` is this error. A line
entered too strong electrically draws flow toward itself, so a DC OPF routes through it
preferentially, and the flows and cost the design reports are wrong.

Two cautions. The brief may define route length as a multiple of straight-line distance
without saying which mile the per-mile X uses; a band of designs sitting at exactly that
multiple is an ambiguity in the brief, not an error. And quote the ratio in the report,
not just "wrong X", so the designer can see which reading they took.

### Check 6 — X much smaller than R on a transmission line

A transmission line's X is several times its R. A new line at 115 kV or above with
`LineX` well below `LineR` almost always has the two swapped, or one entered in the wrong
unit. DC power flow reads only X, so a swap there changes the flows without any error
([case-impedance-completeness](../concepts/case-impedance-completeness.md) covers the
whole-case version of this check). Flag it with both values.

### What the report looks like

Open with the criterion the review judged against (the brief's delivery rule, TPL-001 P1, a
regional criterion), since Check 2 and some Check 1 findings pass under one and fail under
another. Then one line per finding, worst first: the check, the kind (rule, physical,
judgement), the device by its key fields, and the number. For example:

> **Physical** — Check 1/2, against a full-delivery brief: with transformer 9201→9101 ckt 1 out, bus 9101 goes Disconnected
> and its 600 MW load is not served. Both new 500 kV lines into 9201 survive their own
> outages; the single transformer below them does not.

Then say what was checked and passed, which base-case problems were excluded, and that
nothing was edited or saved. Leave every fix to the designer.


---

# ==== save-powerworld-case.md ====

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
the GUI. **Do NOT use the SimAuto `SaveCase` COM function** (`pw.esa.SaveCase(...)`). It returns
success (`('',)`, no error raised) yet **silently writes no file**. Use the PowerWorld aux **script**
command `SaveCase` via `RunScriptCommand` instead, which actually writes. The second trap: the aux
`SaveCase` takes **exactly two parameters** `(FileName, FileType)`, and a third overwrite/`YES` arg
raises `Invalid number of parameters`. All behavior below was live-verified
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
- The command **overwrites** an existing file silently. There is no separate overwrite flag.
- Use an **absolute** path (`os.path.abspath`). The SimAuto server is a separate process, so a
  relative path resolves against *its* working directory (the PowerWorld **install folder**), not
  your script's. Symptom when you forget: `RunScriptCommand: Exception: Access is denied` (PowerWorld can't
  write into its own program dir). A relative-path arg from a README example or CLI is the usual cause;
  `abspath` the output path inside any save wrapper so a caller can pass a relative path safely.

### Why not `pw.esa.SaveCase(...)` (the COM function)

esapp exposes a COM wrapper `SaveCase(FileName, FileType="PWB", Overwrite=True)` in
`saw/case_actions.py`. It looks right and raises nothing, but it is a **silent no-op**:

```python
pw.esa.SaveCase(out, "PWB", True)     # returns None, no exception
pw.esa._pwcom.SaveCase(out, "PWB", True)  # raw COM returns ('',) == "success"
os.path.exists(out)                    # -> False.  No file. No error.
```

Because `_com_call` only raises when SimAuto returns a non-empty error string, a "success" that writes
nothing sails straight through. **Always `assert os.path.exists(out)` after any save.** A save that
"worked" but produced no file is the failure mode to guard against, the same silent no-op as in
[adding-devices-esapp](adding-devices-esapp.md).

### The 2-parameter rule (the other silent trap)

The aux script command signature is `SaveCase(FileName, FileType);`. Live-probed on the Synth2k case:

| Statement | Result |
|---|---|
| `SaveCase("out.pwb", PWB);` | ✅ file written |
| `SaveCase("out.pwb", "PWB");` | ✅ file written |
| `SaveCase("out.pwb", PWB, YES);` | ❌ `RunScriptCommand: Error in script action validation: Invalid number of parameters.` |

The aux command takes no overwrite argument; it always overwrites. The COM function's 3-arg
`(FileName, FileType, Overwrite)` shape differs, which makes the two easy to confuse.

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

A path bug: building the path in a shell string with `\\$var` turns into a literal
`$var`, and SaveCase then reports *"Windows has prevented us from writing to the file"*. That
message means a bad path as often as a permission problem; print the path before blaming access.

### Typical use: save a solved design so a human can open it

Open the base case, apply a design, solve, then save. This is the pattern for handing a
reviewer a case they can open:

```python
# open_case / set_target_loads / apply_design / solve_dcopf stand for your own study helpers
pw = open_case(scenario_path)
try:
    set_target_loads(pw)
    apply_design(pw, design)     # CreateData buses/branches/loads — see methods/adding-devices-esapp.md
    solve_dcopf(pw)
    out = os.path.abspath(r"C:\...\Outputs\Synth2k_scenarioA.pwb")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')
    assert os.path.exists(out)
finally:
    pw.close()
```

Saving before `pw.close()` captures the in-memory edits (new devices + solved state); the reopened
`.pwb` shows exactly what was built.

> Rules this page follows: drive SimAuto via `esapp` `RunScriptCommand` (not raw `esa`, not the flaky COM
> `SaveCase`); verify the artifact exists before claiming success (see [esapp](../concepts/esapp.md)).


---

# ==== teamoverbyeweather-client.md ====

---
type: method
domain: weather
topic: timestep
aliases: [teamoverbyeweather, team-overbye-weather, weather-client, weather-sdk, TeamOverbyeWeather]
tags: [weather, pww, era5, hrrr, noaa, python, client, download]
---

# Method: Getting weather data with the TeamOverbyeWeather client

## Abstract

`TeamOverbyeWeather` is a pip-installable Python client for the Team Overbye weather
portal. One call downloads a weather dataset, crops it to a region, and crops it to a
time window, returning `.pww` files ready for PowerWorld's TimeStep feature. It is the
**one part of the kit that needs no PowerWorld licence**: the client, the PWW reader, and
the cropping tools are pure Python. Verified against version 0.4.0; the `bbox` order and the `download()`
signature were re-checked against 0.4.2's installed source on 2026-10-19.

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
client-side as appropriate, then writes `.pww`.

### What data is available

Do not guess source or type names. Ask the server:

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
client.download("era5", "2021-02", bbox=(36.5, -106.7, 25.8, -93.5))  # lat/lon box: N, W, S, E
client.download("era5", "2021-02")                                    # everything, usually too much
```

Discover valid identifiers rather than guessing:

```python
client.regions()                    # every layer the server knows
client.region_ids("states")         # ['AL', 'AK', 'AZ', 'AR', 'CA', ...]
```

`bbox` is `(lat_max, lon_min, lat_min, lon_max)`: **north, west, south, east**, in client
0.4.2. West longitudes are negative. Most libraries use min-then-max order instead, and
getting it wrong fails two different ways:

- `download()` checks the order and raises `ValueError: bbox (...) is inverted`.
- `pww_io.crop_to_bbox` and `localcrop.crop_file` take the same order but **do not check
  it**. A south-first box slices zero latitude rows and returns an empty crop with no error.
  Check the station count of a cropped file before you load it.

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
    *,                     # everything below is keyword-only
    region=None,           # state/region id
    iso=None,              # ISO footprint
    bbox=None,             # (lat_max, lon_min, lat_min, lon_max) = N, W, S, E
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
print(arr.shape)           # (time, field, lat, lon) uint8 grid, 0.25-degree cells
```

Crop, concatenate, and write back:

```python
from TeamOverbyeWeather import pww_io, localcrop

# crop an existing file on disk in one call
localcrop.crop_file("big.pww", "texas_only.pww",
                    bbox=(36.5, -106.7, 25.8, -93.5))   # N, W, S, E

# or work in memory
header, stations, arr = pww_io.crop_to_bbox(header, stations, arr,
                                            (36.5, -106.7, 25.8, -93.5))
assert stations, "empty crop: bbox order is (lat_max, lon_min, lat_min, lon_max)"
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

It serves the Team Overbye portal only. For raw upstream access, go to the ERA5, HRRR or
NOAA services directly. What it saves you is the region crop, the time crop, and the PWW
conversion, which are normally the tedious part.


---

# ==== timestep-dispatch-into-design-bands.md ====

---
type: method
domain: synthetic-grid
topic: timestep
aliases: [timestep-dispatch-into-design-bands, weather-based-dispatch, scaling-timestep-dispatch, renewable-dispatch-from-timestep]
tags: [timestep, dispatch, pfw, powerworld, synthetic-grid, curtailment, agc]
---

# Method: Turning time-step output into a scenario dispatch that meets the design bands

## Abstract

How to dispatch wind and solar unit by unit from a PowerWorld time-step run, and how to scale that pattern
into the scenario's design bands when no real hour fits. Covers the clock trap, the scaling rule, batteries,
rebalancing, AGC, and what the new dispatch exposes. Read before building any renewable scenario dispatch.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation-setup](timestep-simulation-setup.md) (getting the per-unit output) ·
  [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md) (writing the result into the case) · [pww-data](../concepts/pww-data.md) ·
  [opf-preconditions](../concepts/opf-preconditions.md) (AGC fields) · [agc-participation-factors](../concepts/agc-participation-factors.md) (step 7 in full)

## Content

### The symptom this fixes

A fleet-level dispatch ("wind at 45% of fleet") filled **largest unit first, each to 100%** gives the right total
and an unrealistic split: the online units are exactly the N largest, every one at maximum, the rest off. Test
for it directly: sort a fuel's units by MWMax and check whether the online set is the top N. On a ~9k-bus synthetic case (measured
2026-10-16) it was, in three of five scenarios, with one farm on and a farm barely smaller off. Offline units in
such a case are not outages, weather or curtailment, and a reviewer will ask which they are.

### Steps

1. **Get each unit's output on PowerWorld's own clock.** Run the time-step simulation with a PFW model on every
   wind and solar unit and save `GenMW` per unit ([timestep-simulation-setup](timestep-simulation-setup.md)). Take times from the raw export's
   column 0 (Excel serial days, UTC). Check any pipeline's own CSV time labels against column 0 before trusting them: one
   pipeline's ran 7 h early inside US DST and 6 h outside. Load data from an ISO is usually local hour ending;
   convert it to UTC before joining. A wrong join pairs the load with weather from another hour; measured
   2026-10-16, every scenario's renewables on that case came from about 2 h after its load hour, and the "no solar"
   scenario's load hour still had sun.
2. **Look for a real hour first.** Over a year of per-unit output, compute fleet wind % and solar % (output over
   the whole fleet's MWMax) and the load % for the same instant, and keep the in-season hours that sit inside
   all bands. Prefer the hour whose fleet totals are closest to what the case already carries, so thermal barely
   moves. Expect few or none for demanding scenarios: on a 2025 search, one scenario had 0 hours, one had 2.
3. **When no hour fits, scale the pattern.** Scenario designs usually ask for *statistically representative*
   conditions, not a copy of a historical hour, so a real hour's weather may set the unit-by-unit pattern and
   the fleet total may be scaled into the band. Per fuel:
   - target `T` = a fleet MW inside the band (keeping the case's current total, if it is in band, leaves the
     balance and thermal dispatch untouched);
   - unit MW = `min(k × w_i, Pmax_i)`, where `w_i` is the unit's weather output (negative clipped to 0) and one
     factor `k` per fuel is found by bisection so the units sum to `T` (water-filling: a capped unit's excess
     spreads to the units that still have room);
   - a unit with zero weather output stays off. If the units with output cannot reach `T` even at their maxima,
     report the shortfall instead of turning on dark units.
   - `k < 1` is **curtailment**: report each unit's held-back MW (weather minus dispatched). `k > 1` is allowed but
     say how large; at roughly 1.5× and above, which farms are windy rests on the weather file more than on the
     target, so verify the weather first.
   - The band's headroom is also a reserve lever: when every conventional unit is already online, raising wind
     inside its band and taking the MW off gas is how thermal reserve gets freed.
4. **Batteries have no weather.** Run every battery at the same design % of its own MWMax. A design 0% means all
   open, **including a battery that sits on the slack bus**: PowerWorld splits the slack's swing among that bus's
   units, so a slack-bus battery discharges whenever the slack moves (on the ~9k-bus case it ran 79–200 MW in scenarios
   designed for 0%).
5. **Rebalance the net change on thermal, never on the slack.** Wind and solar scaled to the old total change
   nothing; the battery change does. Move that MW onto or off the online non-slack thermal units, pro rata to
   their room (above GenMWMin to reduce, below GenMWMax to raise). A slack unit near its minimum cannot absorb
   hundreds of MW.
6. **Write, read back, solve, save** as in [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md): write `GenStatus` and `GenMW` with
   the key fields, read them back (a write without keys no-ops silently), warm-solve, save to a temporary file and
   swap it in, then reopen cold in a fresh process and compare.
7. **Turn on AGC so contingencies share lost MW.** Set `GenAGCAble = YES` on dispatchable synchronous units (not
   wind, solar, batteries, or 0 MW condensers); run PowerWorld's `SetParticipationFactors(MAXMWRAT, 0, SYSTEM);`
   and set `CTG_Options.UseAreaPartsMakeUpPower` to `Gen Part Factors`. `MAXMWRAT` stores MWMax in per unit on the
   100 MVA base (150 MW becomes 1.5); only ratios matter. With AGC flags on but every factor 0, lost MW still lands
   on the slack alone. This matches the Synth2k series 24 and ACTIVSg10k convention (surveyed read-only
   2026-10-18; one other public case shipped all factors at 0). The base case does not move.

### What the new dispatch exposes

Measured 2026-10-18 on the ~9k-bus case, five scenarios, warm AC solve after applying the scaled dispatch:

- **Undersized generator step-ups.** Spreading output over every farm runs small units that the largest-first
  fill never touched; base-case overloads were almost all their step-up transformers, at roughly 1.2–2× rating.
  Check each step-up's rating against its unit's MVA before solving.
- **Renewables with a non-zero minimum** fall below it at low weather output. Wind and solar minimums should be 0.
- **Light-load voltages rise.** In the low-load, high-renewable scenario, buses above 1.05 pu went from about 20
  to about 150, mostly at 345 kV, once output was spread across the fleet.
- **Losses move**, so the slack moves; check it against its limits after the solve.

### Check the weather file before trusting a season

Compare the time-step run's monthly fleet capacity factor with an independent source before using a season.
Measured 2026-10-18 on an ERA5 PWW for 2024–2025: summer fleet wind was 5–7% against 26–38% in an
independent forecast set; the file's 100 m wind read 2–4 m/s at the wind sites in summer against 6–11 m/s in
other seasons, every unit dropped alike (so not the models), and October–December matched the forecast set
exactly. **Cause found 2026-10-19:** that file's grid is scrambled for nine consecutive months; the low summer
wind was a symptom, not a wind-model problem. Run the sunrise/sunset geography check in [pww-data](../concepts/pww-data.md) (check 3)
on every month a scenario draws from. Any scenario whose pattern comes from a failing month is provisional.

### Checks before calling it done

- every fuel's fleet % inside its band, from the saved file, not from the plan;
- no unit above MWMax, no open unit carrying MW, and every unit below its minimum listed (not clamped);
- curtailment and shortfall reported per scenario in MW;
- base-case overloads and voltages compared before and after, and the slack inside its limits;
- AGC units carry non-zero participation factors, and make-up power reads `Gen Part Factors` on a cold reopen.


---

# ==== timestep-simulation-setup.md ====

---
type: method
domain: cross-cutting
topic: timestep
aliases: [timestep-setup, ts-setup, timestep-simulation-howto]
tags: [powerworld, simauto, timestep, simulation, weather, renewables, pww]
---

# Method: Writing a timestep simulation

## Abstract

How to drive PowerWorld's TimeStep simulation, turning `.pww` weather files into hourly solar/wind generation CSVs. Covers the prerequisites a case must satisfy per renewable generator (`GenFuelType` containing WND or SUN, valid Lat/Lon, a `TSPFWModelString` PFW model), one pipeline's optional ISO-labelling step, and the pipeline's worker-function sequence. This is step 2 of this reading sequence; for the PWW weather files see [pww-data](../concepts/pww-data.md).

> **Writing the backend code?** [time-step-simulation-backend](../references/time-step-simulation-backend.md) has the full worker-function call sequence, the required `TIMESTEPSaveSelectedModifyStart/Finish` wrapper, the `_GEN_PARAM` field list, and the key-field rule.

## Connections

- **Up:** [Home](../index.md) · [timestep-simulation](../concepts/timestep-simulation.md)
- **Deeper (backend code):** [time-step-simulation-backend](../references/time-step-simulation-backend.md) (exact call sequence, field lists, gotchas)
- **Across:** [timestep-simulation](../concepts/timestep-simulation.md) · [auto-pfw-scripts](../concepts/auto-pfw-scripts.md) (attaching the PFW models) · [esapp](../concepts/esapp.md) · step 2 of this reading sequence: prev [esapp-overview](esapp-overview.md) · next: [pww-data](../concepts/pww-data.md) · final: [how-to-analyze-results](how-to-analyze-results.md)

## Content

**Step 2 of this reading sequence.** ← prev: [esapp-overview](esapp-overview.md) · next: [pww-data](../concepts/pww-data.md).
The concept behind it: [timestep-simulation](../concepts/timestep-simulation.md).

TimeStep simulation is *not* a transient-stability study.

> **Library note: prefer `esapp` over `esa`.** Older repos import the standalone `esa` (Easy SimAuto) package. `esapp` (ESA++) is the updated, better-documented version of the same thing, so write esapp. Every `RunScriptCommand` / `TimeStep*` script command is identical via `pw.esa.RunScriptCommand(...)`, and the bracket interface (`pw[Type, fields]`, `pw[Type] = df`) replaces esa's `GetParametersMultipleElement` / `change_parameters_multiple_element_df`. See [esapp-overview](esapp-overview.md).

### 0. Prerequisites

PowerWorld needs, on each renewable generator: a `GenFuelType` that contains `WND`
or `SUN` (the case labels them `WND (Wind)`, `SUN (Solar)`), valid coordinates, and a
PFW model string (`TSPFWModelString` longer than 2 characters). A unit with no PFW model
runs and reads 0 MW for the whole run; attach models with
[auto-pfw-scripts](../concepts/auto-pfw-scripts.md). Coordinates: on both public
synthetic cases probed 2026-09-30 the unit's own `Gen.Latitude` read blank and the substation's
`Gen.Latitude:1` / `Longitude:1` (the field export's "Substation Latitude") were set. That
TimeStep then reads the substation pair is not verified in the kit.

### 1. (Optional, one pipeline's convention) Label units with an ISO region

This is **not** a PowerWorld prerequisite. One time-step pipeline writes an ISO region into
`CustomString:2`, a custom field, so its output CSVs can carry an ISO header row; TimeStep does
not read it. Skip this section unless your post-processing needs the label.

The pipeline's ISO-assignment step does a geopandas spatial join
of every generator's lat/long against ISO-region shapefiles (nearest-neighbor for
units outside any boundary) and writes the ISO assignment back into the case, where it
later appears as the first metadata header row. Run it once per case; skip it if the
case already has ISO assignments.

> The ISO-assignment step writes **only `CustomString:2`**. It does
> **not** touch `TSPFWModelString`. PFW model strings must already be in the case;
> [auto-pfw-scripts](../concepts/auto-pfw-scripts.md) attaches them, and the
> case-auditor's `timestep` profile counts which units still lack one.

### 2. What your code does (the worker function)

`timestep_worker(case, pww_list, result_csv)` is the core function to implement:
1. Copies the case to a temp `.pwb`, opens it with `PowerWorld(tmp_case)` from esapp.
2. Pulls generator metadata (`GetParametersMultipleElement('gen', ...)` / `pw[Gen, fields]`).
3. Loads weather: `TimeStepLoadPWW("...","Weather Only")` then
   `TimeStepAppendPWW(...)` for any additional files. On Simulator 25 (builds dated 2026-09-20
   and 2026-09-25) the plain load fails with `Error With Loading PWWFile` (suspected PowerWorld issue, not yet confirmed: glitch `2026-10-20-timestep-loadpww-plain`); use
   `TimeStepLoadPWWRange` over the file's full span and assert the timepoint count (see
   [pww-data](../concepts/pww-data.md)).
4. Selects renewables (`GenFuelType` contains `WND|SUN`) and marks them
   `TimeDomainSelected`.
5. Picks the saved fields:
   `TimeStepSaveFieldsSet(GEN, [BGGenMWFuelTypeGeneric:10, BGGenMWFuelTypeGeneric:12], SELECTED)`.
6. Runs `TimeStepDoRun()` and exports via `TimeStepSaveResultsByTypeCSV(gen, ...)`.

> The simulation is **generator-level** by construction: `TimeStepSaveFieldsSet`
> targets `GEN`. Area/substation-level output is not covered here.

### 3. Inputs and outputs

- **In:** one case + one or more `.pww` weather files ([pww-data](../concepts/pww-data.md)).
- **Out:** per run, two CSVs (solar + wind). Historical quarter files grouped by
  year are named `Historical_{year}_solar.csv` / `_wind.csv`; a forecast file is
  named after its stem. Resume-safe: a run is skipped if both its CSVs already
  exist (delete them to re-run).

### Next

- Get the weather inputs → [pww-data](../concepts/pww-data.md)
- Analyze the CSVs → [how-to-analyze-results](how-to-analyze-results.md)


---

# ==== violation-network-map.md ====

---
type: method
domain: tooling
topic: contingency
aliases: [violation-network-map, violation-map, voltage-map, reactive-balance-map, radial-ties-map,
  islanding-screen, map-the-violations, visualize-the-violations, network-map, bridge-screen,
  thermal-map, overload-map, worst-case-per-line]
tags: [esapp, powerworld, voltage, overvoltage, islanding, radial, bridges, visualization, html,
  remediation, n-1, reactive-power, thermal, overload, contingency]
---

# Mapping Violations on the Network: the Voltage and Thermal Page, and the Radial-Ties Page

## Abstract

Two single-file HTML pages that put a violation **on the map** instead of in a table, built by the
`violation-map` skill's engine (`skills/violation-map/engine/`). The **voltage page** shows the
substations around a set of out-of-band buses, every line in its own kV colour, a click-to-zoom
problem list, a one-line of any substation, the **reactive balance** inside the radius (line
charging against generators absorbing and reactors, with the *room* each has left), and
optionally measured candidate fixes with a Before/After switch and a scenario × outage
pass/fail grid. Its **thermal view** colours every line by its loading against the rating in
use (red at or above 100%, orange from 90%, the rest grey), with nothing out, after any one
outage, or each line at its worst post-outage loading with the outage behind it. The **radial-ties page** screens the whole grid for **bridges** (lines whose
single outage splits the network), groups them into radial trees, suggests a tie per tree and
shows its AC-measured verdict.

Four facts decide whether the pages tell the truth, and each fails silently: an outage that
**islands load solves with zero violations**, so islanding needs its own screen; a measured
candidate needs a **fresh case**, because LTC taps and switched shunts do not move back when you
undo; a tie's **rating does not scale with its length**; and a PowerWorld process you do not
`esa.exit()` stays resident. The thermal view adds two more: a case's shipped contingency list
rarely trips the study's **new** devices, and **ViolationCTG cannot draw the orange band**,
because it reports only what is already over the limit.

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
the radial page tests only bridge outages. Neither is a full contingency analysis. The pages
say so on every measured result, and so should you.

### Ask before extracting anything

Four decisions belong to the user, and each changes what gets extracted:

| Ask | Default to offer |
|---|---|
| Which cases, and which **states** (as delivered, after a fix) | the delivered set only |
| Which violations: intact voltage, N-1 voltage, islanding | intact voltage |
| Area and depth: seeded from which buses, how many substation-hops | seeds = the out-of-band buses, 5 hops |
| Look only, or also **measure candidate fixes** | look only |

Very meshed areas explode past a few hops; open those at 2–3 and say so. Step-up, star-point
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
python $E/extract_thermal.py config.json           # optional: loading with nothing out and after every outage
python $E/measure_designs.py config.json           # optional: candidate fixes, in memory
python $E/build.py           config.json           # -> voltage_map.html, or thermal_map.html with thermal data
python $E/test_thermal.py                          # after touching the colour rule in vmap.py or the template
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
  voltage and confuses the reader. **The one exception is the thermal view**, where colour *is*
  the message and kV is left to the layer filter and the hover.
- **Problem list with click-to-zoom**, plus Prev/Next on the map bar.
- **Voltage-layer filter** (All / 765 / 345 / 138 / ≤69) that hides the other classes' lines and
  substations.
- **Substation one-line** on click: bus bars by kV with pu, transformers with X and flow,
  generators and shunts with MVAr and pinned flags, outgoing lines fanned with far-end names,
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

**The thermal view**, built when `extract_thermal.py` has run (the page then opens on it, with a
Thermal / Voltage switch):

- **Red** at or above `thermal.over` (default 100) % of the rating in use, **orange** from
  `thermal.near` (default 90), **every other line grey**, so the eye lands on red and orange.
  Every red or orange line carries its % in a pill, and the % is in ink, never in the line colour.
  Colour is never the only signal.
- **Three views:** *nothing out*; *after an outage*, picked from a list ordered by the worst
  loading each causes, with Prev/Next to step through it; *worst case per line*, where each
  branch is drawn at its highest post-outage loading and the outage behind it shows in the list
  and the hover. Selecting a line in that view draws its causing outage dashed.
- **Width scales with MVA flow**, against one reference per state, so widths do not jump between
  views. **Moving dots** show flow direction on lines above half their rating, and an arrow does
  the same on every red or orange line, so a still export keeps the direction. **Overloaded
  lines pulse gently.** Under `prefers-reduced-motion` the dots and the pulse stop and a steady
  glow stays.
- **The element that is out** is drawn dashed in ink with an `OUT` pill. An outaged generator or
  transformer gets a dashed ring at its substation instead.
- **Transformers inside a substation** have no line to colour, so a red or orange one rings its
  substation with an `XF nn%` pill. Without this they would sit in the problem list but nowhere
  on the map.
- **Ranked problem list** (branch, %, MVA vs rating, causing outage), click to zoom, plus
  Prev/Next on the map bar. **Hover** a line for every circuit's MVA, rating and %. **Click** a
  line for its circuits in this view, with nothing out, and at worst, plus the eight outages that
  load it most, each one click away from its own view.
- Substations are neutral grey in this view. Voltages are a voltage-view question, and a dot
  coloured by base-case voltage under a post-outage label would be wrong.

Open the built HTML in a browser, or publish it. Take one screenshot before handing it over:
a page that renders blank from a data error looks identical to one still loading.

### Traps, each of which cost a run

**`esa.exit()` every case you open.** `del pw` leaves one `pwrworld.exe` resident per open
(roughly a gigabyte each on a 10,000-bus model), and a measurement loop that opens a case per
candidate will starve every other process on the machine. The engine closes in a `finally`.

**A fresh open per candidate; never trust an undo.** Taking a new line back out does not move
LTC taps or switched shunts back to where they were, so the next candidate is measured on a
different case. `measure_designs.py` reopens per candidate. `measure_trees.py` reuses one case
per scenario for speed, and **fingerprints** it after every design (closed-branch count plus a
fixed 40-bus voltage sample), and reopens the moment either drifts. An undo that did not restore
the case once went unnoticed until the fingerprint caught it.

**Islanding solves with zero violations.** When an outage strands buses, PowerWorld drops them
from the solution rather than flagging them, so the violation count stays clean. The radial page
exists because of this; the voltage page marks a substation ISLANDED when every one of its
network buses loses its voltage. Read [reading-violationctg](reading-violationctg.md) for the
N-1 side of the same trap.

**Adding several devices before one solve: freeze the controls.** Live taps and shunts drift
between writes, and the saved case then disagrees with what you measured. Set `ChkTaps`,
`ChkShunts` and `ChkPhaseShifters` to `NO`, add everything, restore them, and take one solve.
The engine adds one device per candidate, so it does not need this; a multi-device candidate
does.

**A tie starts where the MW is, then where it closes the most bridges.** For a chain of substations,
the far end usually removes the most bridges; for a plant tree, start at the plant only when the
plant's own exit is weaker than the plant. `designs_all.py` ranks sources by MW first because
the other order once routed a plant's whole output through a lower-voltage line inside the
pocket when its exit opened.

**Rating does not scale with length; impedance does.** A new line cloned from a template gets R,
X, C and G scaled by the length ratio and the template's whole `LineAMVA` set unchanged. Choose
the template by **rating first** (it must clear the stranded MW) and length second. A template
chosen by length alone once put a line at 250% into a delivered case. The create is read back:
branch count +1, X as asked, status Closed, device type Line. See
[adding-devices-esapp](adding-devices-esapp.md) for why every create must be read back.

### Thermal traps

**The shipped contingency list rarely trips the new devices.** A case's list is built for one
area and before the study's own additions existed. Solve it alone and the one outage that
matters, losing the new line, is never run: the page draws a clean design that overloads to
nearly three times its rating. `thermal.outages` therefore defaults to `"case+area"`, which keeps
the shipped list and adds one outage per in-service drawn branch at or above `min_net_kv` that
the list does not already open. Matching is by unordered bus pair plus circuit, read from
`ContingencyElement.Object`, never by parsing a label. Only a case contingency that runs (not
`CTGSkip`) and opens that one branch alone counts as covering it. A branch that appears only
inside a skipped or multi-element contingency still gets its own single outage. The added set goes in through an aux file
loaded by absolute path, and the loaded element count is asserted
([new-device-contingency-aux](new-device-contingency-aux.md)).

**ViolationCTG cannot draw the orange band.** It reports only what is over the monitoring limit,
so a line at 97% after an outage never appears there. The engine applies each outage itself
(`CTGApply`, solve, read every drawn branch), then puts it back with `CTGRestoreReference` **and
a fresh solve**: the restore puts the inputs back, but not the flows. Every undo is checked
against the base loadings, and the run stops if they move by more than 0.01 points. Then it runs
`CTGClearAllResults` and `CTGSolveAll` on the same list, and the check runs both ways:
- every `ViolationCTG` thermal row must match the per-outage loading within 1 point;
- every per-outage overload above the limit set's `LSLinePercent` on a **monitored** branch
  (`LineMonEle:1`) must have a `ViolationCTG` row.

An overload on a branch the case does not monitor is drawn anyway, and the page says PowerWorld
did not report it. Two independent paths that agree are the evidence; a disagreement stops the
build instead of drawing either. The base case is solved in AC before anything is read, and a
second solve must reproduce it, because a case saved with the DC approximation would otherwise
give a DC "nothing out" view under an AC "after an outage" one.

**Which percent, against which rating.** `LinePercent` is the from-end percent and
`LinePercent:1` the to-end. `LineMaxPercent` is the higher of the two, and it equals
`max(LineMVA, LineMVA:1) / LineLimMVA` exactly. `LineLimMVA` is the normal rating and
`LineLimMVA:1` the **contingency** rating. Each comes from the limit set's own rate-set choice
(`LSLineRateSet`, `LSLineRateSet:1`), so the page judges nothing out against the first and
post-outage loading against the second. On a case where both sets are A they agree; on one with
an emergency set they do not, and a page that used `LineMaxPercent` after an outage would show
false red. Measured 2026-10-21 on a design case built on the public 2,000-bus Texas synthetic
grid, Simulator 25.

**Amp ratings are refused, not guessed.** A limit set with `LSAmpMVA` other than `MVA` stops
the run. An MVA percent on an amp-rated branch is a plausible wrong number
([reading-violationctg](reading-violationctg.md), trap 5).

**Islanding still hides.** An outage that strands load leaves those lines at zero flow, grey. The
outage list marks every outage whose `Contingency.LoadMW` is non-zero with how much it cuts off.
PowerWorld leaves that field **blank, not 0**, when nothing is cut off. On a 2026-10-21 run it was
blank on every outage while `GenMW` on the same rows carried numbers wherever generation was
lost, so the engine reads blank as zero. `GenMW` is also non-zero on an ordinary generator trip,
so it is not an islanding signal. Read the radial page for the rest.

**Cost and size.** About 0.4 s per outage on a 2,000-bus case: two solves and three reads. Each
outage stores only the branches it moved by at least 0.5 points, or that sit within 1 point of
the orange threshold, and the page falls back to the base value for the rest. A few hundred
outages over a few hundred drawn branches build to well under a megabyte.

### What it does not do yet

- **Thermal covers the drawn area's branches plus the case's list, not a full N-1 of the whole
  case.** An overload whose outage and line both sit outside the drawn hops is not found. The
  page says how many outages ran and where they came from; say the same in the answer.
- **No amp-rated limits** in the thermal view (above).
- **No candidate fixes measured for thermal.** The designs panel is voltage-only.


---

# ==== visualize-renewable-output.md ====

---
type: method
domain: cross-cutting
topic: timestep
aliases: [viz-renewable, plot-solar-wind, visualize-timestep-output]
tags: [powerworld, analysis, visualization, matplotlib, solar, wind, renewables, pandas]
---

# Method: Writing code to visualize renewable output

## Abstract

How to write matplotlib code that visualizes the solar/wind CSVs produced by the timestep simulation. Covers loading the 8-row metadata + hourly data structure, parsing timestamps, and the four key plot patterns: fleet total solar+wind stacked over time, per-ISO or per-State totals, capacity factor curves, and peak/trough hour identification. This is step 5 (final) of this reading sequence.

## Connections

- **Up:** [Home](../index.md) · [timestep-simulation](../concepts/timestep-simulation.md)
- **Across:** prev in flow: [how-to-analyze-results](how-to-analyze-results.md) · [pww-data](../concepts/pww-data.md) · start: [esapp-overview](esapp-overview.md)

## Content

**Step 5 (final) of this reading sequence.** ← prev: [how-to-analyze-results](how-to-analyze-results.md).

The CSV format is described fully in [how-to-analyze-results](how-to-analyze-results.md); this page covers the plotting patterns.

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

# ==== zone-load-multiplier-trap.md ====

---
type: method
domain: tooling
topic: case-audit
aliases: [zone-load-multiplier, load-multiplier-trap, area-load-multiplier, served-load-check]
tags: [esapp, powerworld, load, device-creation, synthetic-grid]
---

# Adding load under a zone or area load multiplier

## Abstract

A case can scale every load in a zone or area by a stored multiplier, so the MW a new load
draws is `LoadSMW` times that multiplier rather than `LoadSMW`, and PowerWorld gives no
warning. The fix is to divide the intended MW by the multiplier before writing, then read
the solved MW back and assert it matches. A second, related trap: load on an islanded
(Disconnected) bus drops out of system totals silently, so a totals check cannot catch a
load that is not connected. Read this before writing `LoadSMW` into any case you did not
build yourself.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [adding-devices-esapp](adding-devices-esapp.md) (the `LoadSMW` write this page
  corrects; `LoadSMW` is the scheduled input, `LoadMW` the served value) ·
  [applying-a-dispatch-to-a-case](applying-a-dispatch-to-a-case.md) (scaling load to a
  scenario level hits the same multiplier) · [case-data-lint](case-data-lint.md) ·
  [reviewing-a-design](reviewing-a-design.md) (the islanded-load check, applied to a
  submitted design)
- **Deeper:** [esapp-schema-reference](../references/esapp-schema-reference.md) for the `Load`
  keys (`BusNum`, `LoadID`)

## Content

### What happens

Measured 2026-10-19 on Synth2k, in one of its published scenarios. One zone carries a load
multiplier of **×1.305**. A new load created there with `LoadSMW = 600` drew **783 MW** in
the solved case (600 × 1.305). There was no warning, the write read back as 600, and nothing
in the solve reported a difference. Every downstream number then carries a load 183 MW
larger than intended: the flows, the N-1 violations, and the generation balance.

The multiplier sits outside the load record, so reading `LoadSMW` back proves nothing. It
returns exactly what you wrote.

### The fields

From the Simulator 25 field export, via the schema lookup on 2026-10-19:

| field | concise name | what the export says | writable |
|---|---|---|---|
| `Load.LoadMultiplier:2` | `MultiplierMWZone` | Scaling value applied to all the real power load values in the zone | read-only |
| `Load.LoadMultiplier:3` | `MultiplierMvarZone` | the Mvar twin of the above | read-only |
| `Load.LoadMultiplier` | `MultiplierMWArea` | Scaling value applied to all the real power load values in the area | read-only |
| `Load.LoadMultiplier:1` | `MultiplierMvarArea` | the Mvar twin | read-only |

These are per-load *views* of the multiplier, so they are the ones to read. **Where the
multiplier is set is not confirmed.** The only writable candidate on `Zone` / `Area` in the
export is `SchedValue` (concise `LoadMWScale`, "Load Scale MW Value"), and the export does
not say whether it holds a multiplier or a target MW. Do not write it on the strength of
this page. The read-side fields come from the export, and they were not read back on the
measured case. **Whether the area and zone multipliers compound** when both differ from 1 is
also untested. The read-back below catches either case.

### The fix

1. Create the load as usual ([adding-devices-esapp](adding-devices-esapp.md)), keeping
   `BusNum` + `LoadID`.
2. Read its multipliers and write `LoadSMW = intent / multiplier`. Scale `LoadSMVR` by the
   Mvar multiplier the same way.
3. Solve, read `LoadMW` (the served value), and assert it matches the intent.

```python
from esapp.components import Load

key = (bus, "1")                      # BusNum, LoadID of the new load
intent_mw = 600.0

m = pw[Load, ["LoadSMW", "LoadMultiplier", "LoadMultiplier:2", "LoadStatus"]]
row = m[(m.BusNum == key[0]) & (m.LoadID.astype(str).str.strip() == key[1])]
mult = float(row["LoadMultiplier:2"].iloc[0])        # zone MW multiplier
# simple: assumes the area multiplier is 1; assert it rather than compound blindly
assert abs(float(row["LoadMultiplier"].iloc[0]) - 1.0) < 1e-6, "area multiplier too: check compounding"

fix = row[["BusNum", "LoadID"]].assign(LoadSMW=intent_mw / mult)
pw[Load] = fix                                       # keyed write, subset is fine
pw.pflow()

served = pw[Load, ["LoadMW"]]
got = float(served[(served.BusNum == key[0]) & (served.LoadID.astype(str).str.strip() == key[1])]["LoadMW"].iloc[0])
assert abs(got - intent_mw) < 0.5, f"served {got:.1f} MW, intended {intent_mw} MW"
```

Assert on `LoadMW` after a solve, never on `LoadSMW`. The read-back is the real check,
because it holds whichever multiplier is in force, including one this page has not
identified.

### Islanded load leaves the totals silently

PowerWorld counts load on a **Disconnected** bus out of the zone, area and system totals,
and it says nothing. A check that compares total load before and after an edit therefore
passes for a new load that landed on an islanded bus: the totals do not move, and the load
serves nothing. Check connectivity per device instead:

- `Bus.BusStatus` reads `Connected` or `Disconnected`, read-only, from the solve.
- `Load.BusObjectOnline` is the load's own online flag.

Assert that the new load's bus reads `Connected` after the solve, alongside the `LoadMW`
check above. `LoadMW` is the connected value, so a new load that reads 0 MW is consistent
with an islanded bus. That inference was not tested separately; the bus status is the check.


---
