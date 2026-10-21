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
What esapp *is* (the full API map): [esapp](../concepts/esapp.md). The COM server underneath:
[powerworld-simauto](../concepts/powerworld-simauto.md).

This is the "how do I actually drive a PowerWorld case from Python" entry point.
All snippets below are verified against `C:\path\to\esapp`.

## 0. Prereqs

Windows + PowerWorld Simulator installed (SimAuto is a COM server). Use the
project venv `C:\path\to\.venv` (Python 3.13, `esapp` editable).
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

Bulk `pw[Type] = df` can also create new objects — but only in EDIT mode
(`pw.edit_mode()`) with `CreateIfNotFound=True`, and the DataFrame must carry a complete
key set. A filtered subset is fine: PowerWorld matches rows by key, so writing 3 rows
touches 3 objects (the positional `pw[Obj, field]` form differs; see [AGENTS.md](../AGENTS.md) code rule 2).

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
`pw.max_iterations = 30`, etc. Not `pw.dc_mode = True` or `pw.flat_start = True`: a
scripted solve ignores both. Use `pw.pflow(method="DC")` for a DC solve and
`pw.flatstart()` for a flat start — see [handling-errors](handling-errors.md).

## Where to go next

> **Note:** Older repos import `esa`; esapp is the updated, better-documented version of the same thing — write esapp. (Library choice only — unrelated to the TimeStep-vs-Transient-Stability distinction.)

- Run a study over time → [timestep-simulation-setup](timestep-simulation-setup.md) (then [timestep-simulation](../concepts/timestep-simulation.md))
- Pull weather into the study → [pww-data](../concepts/pww-data.md)
- Make sense of the outputs → [how-to-analyze-results](how-to-analyze-results.md)
- Full tool reference (matrices, GIC, network, TS) → [esapp](../concepts/esapp.md)

> esapp symbols on this page validated against `esapp` source
> (`C:\path\to\workbench.py` + `indexable.py`).
