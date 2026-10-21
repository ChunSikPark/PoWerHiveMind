---
type: method
domain: tooling
topic: scripting
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
| `pw.dc_mode(True)` or `pw.dc_mode = True` | `pw.pflow(method="DC")` | `dc_mode` is not a method, and assigning it does not make a scripted solve run DC (see *Power flow did not converge* below) |

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
pw.flatstart(); pw.pflow()       # reset the starting point, then re-solve
pw.pflow(method="DC")            # DC, if the study tolerates it
```

Do not reach for `pw.flat_start = True` or `pw.dc_mode = True` here. PowerWorld ignores the
`FlatStart` option on scripted solves, and on 2026-09-23 setting the DC flag alone did not
make the next solve run DC. `pw.flatstart()` runs `ResetToFlatStart`, which with its defaults
also resets generator voltage setpoints to 1.0 pu
([powerworld-study-commands](../references/powerworld-study-commands.md), from PowerWorld's manual). `pw.pflow(method="DC")` leaves the case in
DC mode until an AC method solves it again.

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
