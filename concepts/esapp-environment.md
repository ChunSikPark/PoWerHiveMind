---
type: concept
domain: tooling
topic: scripting
aliases: [esapp-environment, esapp-setup, esapp-install, esapp-package]
tags: [esapp, powerworld, simauto, setup, environment, install]
---

# Concept: The esapp environment

## Abstract

What `esapp` is, what it needs to run, and how its pieces fit together. `esapp` (ESA++)
is a Pythonic wrapper over PowerWorld Simulator's SimAuto COM server: a `PowerWorld`
entry point, a bracket interface that returns pandas DataFrames, and a `SAW` wrapper
exposing the raw SimAuto surface underneath. Read this once when setting up; read
[esapp-overview](../methods/esapp-overview.md) to actually drive a case.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp](esapp.md) · [powerworld-simauto](powerworld-simauto.md) · [preflight-powerworld](../methods/preflight-powerworld.md) · [esapp-overview](../methods/esapp-overview.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md) · [esapp-schema-reference](../references/esapp-schema-reference.md)

## Content

### Install

```bash
pip install esapp
```

Pulls in `pandas`, `numpy`, `scipy`, `matplotlib`, `geopandas`, and `pywin32`. The last
one is the COM bridge and is why this is Windows-only.

Before writing anything, run [preflight-powerworld](../methods/preflight-powerworld.md). It takes five seconds and
distinguishes "my code is wrong" from "this machine cannot run PowerWorld at all".

### What you actually need

| Requirement | Why | If missing |
|---|---|---|
| Windows | SimAuto is a COM server with no cross-platform equivalent | The weather half of this kit still works; see [teamoverbyeweather-client](../methods/teamoverbyeweather-client.md) |
| PowerWorld Simulator, installed | esapp drives it; it does not reimplement it | Nothing in the PowerWorld half functions |
| **The SimAuto add-on, licensed** | Automation is licensed separately from Simulator itself | Simulator's GUI works fine and every script fails. See [preflight-powerworld](../methods/preflight-powerworld.md) |
| Matching bitness | A 32-bit Simulator will not serve a 64-bit Python | `Class not registered` at dispatch time |

Without the SimAuto licence, a working Simulator installation cannot run a single line of
automation, and nothing in the GUI hints at it.

### Contributing to esapp

`esapp` is open source (Apache-2.0) and developed at Texas A&M:
**https://github.com/lukelowry/ESApp**

Found a bug, a missing field, or an undocumented behaviour while using this knowledge
base? Two places to send it: a defect in the **package** goes to the esapp repository
above; a defect in a **page** here goes to this repository's issues.

### Prefer `esapp` over `esa`

There is an older standalone `esa` package wrapping the same SimAuto server. Both work;
`esapp` is better documented and is what this kit's pages assume. Mixing them in one
project buys nothing and creates two mental models of the same COM object.

### The three layers

```
your code
    |
    v
PowerWorld          <- the entry point; open a case, get a summary
    |
    v
Indexable           <- the bracket interface: pw[Bus, "BusPUVolt"] -> DataFrame
    |
    v
SAW                 <- the SimAuto wrapper; RunScriptCommand and friends
    |
    v
pwrworld.SimulatorAuto   <- the COM server, i.e. PowerWorld itself
```

Most work happens in the bracket interface. Drop to `SAW` when you need a SCRIPT action
that has no bracket equivalent (see [aux-script-commands](../references/aux-script-commands.md) for the catalogue). Drop
below that almost never.

### Use the high-level helpers before reaching for script commands

`PowerWorld` exposes helpers for the common tasks. Verified
against esapp 0.1.3 by calling them:

```python
pw.pflow(getvolts=True, method="POLARNEWT")   # solve
pw.mismatch(asComplex=False)                  # per-bus P and Q mismatch
pw.overloads(threshold=100.0)                 # branches above a % of rating
pw.violations(v_min=0.9, v_max=1.1)           # limit violations
pw.flows()                                    # branch flows
pw.lodf((frm, to, ckt), method="DC")          # line outage distribution factors
pw.ptdf(seller, buyer, method="DC")           # transfer distribution factors
pw.ybus(dense=False)                          # admittance matrix (scipy sparse)
pw.jacobian(dense=False, form="R")            # the Jacobian
pw.gens(); pw.lines(); pw.loads()             # convenience tables
pw.voltage(complex=True, pu=True)
pw.save(filename=None)                        # silent no-op: writes nothing, see save-powerworld-case
pw.snapshot()                                 # restore point
pw.run_mode(); pw.edit_mode()                 # switch modes
```

**Every one of these is a method — call it.** Referencing `pw.overloads` or `pw.flows`
without parentheses hands you a bound method where you expected a DataFrame, and the
failure surfaces further down looking like something else.

Solver settings are the opposite: they are **assignable options**, not methods.

```python
pw.max_iterations = 50
pw.enforce_gen_mw_limits = True
```

Two of them do not do what their names say. `pw.dc_mode = True` and `pw.flat_start = True`
are accepted, but a scripted solve ignores both (live-tested 2026-09-23). For a DC solve
call `pw.pflow(method="DC")`; for a flat start call `pw.flatstart()` and then solve. See
[handling-errors](../methods/handling-errors.md).

Reach for a raw SCRIPT action only when no helper covers what you need.

### Getting at SimAuto directly

When you do need a raw SCRIPT action, the SimAuto wrapper is on the `.esa` attribute,
**not** on `PowerWorld` itself:

```python
pw.esa.RunScriptCommand('SolvePowerFlow(RECTNEWT)')
pw.esa.RunScriptCommand(r'SaveCase("C:\out\case.pwb", PWB)')
```

`pw.RunScriptCommand(...)` raises `AttributeError`. This is the single most common
first-attempt mistake with esapp, because every PowerWorld example you will find online
is written against the SAW object directly.

See [aux-script-commands](../references/aux-script-commands.md) for which action to use.

### Components and schema

Object types are importable classes rather than magic strings:

```python
from esapp.components import Bus, Gen, Load, Branch, Shunt, Area, Zone
```

The component schema is generated from PowerWorld's own field definitions, so field
names track Simulator rather than being hand-maintained. The full field map lives in
[esapp-schema-reference](../references/esapp-schema-reference.md).

### The rule that silently ruins writes

**Always keep an object's key fields in any DataFrame you write back.** For a generator
that is `BusNum` plus `GenID`; for a branch it includes the circuit identifier. Without
the key fields PowerWorld cannot tell which row you mean, and the write does not error;
it does nothing.

A second, related trap: `pw[Obj, field] = values` is **positional over the entire
table**. Assigning to a filtered subset writes nothing at all, silently. See
[applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md).
[AGENTS.md](../AGENTS.md) code rule 2 describes the same trap differently: a list built from
a filtered subset lands on the wrong rows. Not settled here; either way, build the full column.

Both fail without raising.

### Snapshots

`snapshot()` gives you a restore point for safe experimentation, which is much cheaper
than reloading a large case between scenarios. PowerWorld's own `StoreState` /
`RestoreState` script actions do the same at the solver level.

### Verifying your setup

```python
from esapp import PowerWorld

pw = PowerWorld(r"C:\path\to\case.pwb")
print(pw.summary())    # n_bus, n_branch, n_gen, n_load, totals, v_min, v_max, sbase
```

If that prints a sensible dictionary, the environment is good and you can start at
[esapp-overview](../methods/esapp-overview.md).
