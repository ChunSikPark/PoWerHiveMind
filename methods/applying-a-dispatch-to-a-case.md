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
and save. The headline gotcha is **the DC solve will fake a balance rather than tell you the
fleet is short** — it pushes the entire deficit through the slack *bus's* generators, past
nameplate, and the resulting branch overloads look like a transmission finding while being a
pure artifact. Verify the schedule against load **before** you trust any flow. Second trap:
esapp's `pw[Obj, field] = values` setter is **positional over the whole object table**, so a
filtered subset writes nothing, silently. Live-verified on Synth9k/Synth8k 2031, 2026-08-18.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [save-powerworld-case](save-powerworld-case.md) (the `SaveCase` no-op trap this depends on) ·
  [adding-devices-esapp](adding-devices-esapp.md) (same key-field discipline, and the `CreateData` silent no-op) ·
  [converting-lines-to-transformers](converting-lines-to-transformers.md) (the other place esapp's static whitelist is wrong) ·
  [case-impedance-completeness](../concepts/case-impedance-completeness.md) (**check this before promising anyone AC** — the cases
  these scenarios are built from are DC-only skeletons) · validating the saved file
  (reopen the saved `.pwb` cold; a save that "succeeded" is not evidence)

## Content

### Steps

1. **Compute the dispatch first, in pure pandas, against a read-only pull.** Keep the
   allocation logic in a module with no `SaveCase` in it, so it can be tested and re-run
   without a license risk. The case write is a separate, dumb step.

2. **Scale load to the scenario level.** Write `LoadSMW` (and `LoadSMVR` by the same factor,
   to hold power factor — DC ignores Q, but the case stays usable later). Do **not** assume
   every load scales: on the 2031 planning cases the few hundred buses named `*_DataCenter` /
   `*_LargeLoad` (about 29% of peak load) are flat 24/7 and are held fixed, so the scenario % applies
   only to the several thousand ordinary loads. That tag lives **only in `Load.BusName`** — `Label`,
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
   to swing. Note *bus*, not unit: the slack bus hosts **about a dozen** generators on both the 8k and 9k
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

Measured on `Synth8k_draft`, in a high-load, no-solar scenario, short **~31
GW**: each of the generators at the slack bus was pushed **+2,840.8 MW over nameplate** — a
44.5 MW unit landed at 2,885 MW — producing **hundreds of branches over 100% and a 683.4% maximum**.
Those overloads are entirely an artifact of 31 GW injected at one 345 kV bus.

It is **not** AGC doing this, so do not go looking there: area `AGC_AGCStatus` is `0` on all 8 zones (recorded under the nonexistent name `AGC_AGCStatus`; the area field is `Area.BGAGC`, see [opf-preconditions](../concepts/opf-preconditions.md))
and exactly **1** of roughly 1.5k generators is `GenAGCAble`.

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

Five scenarios × two fleets, same loads (~140 GW peak, same ~40 GW fixed block):

| Fleet | Conventional | Outcome |
|---|---|---|
| Synth9k 2031 (post-swap, +thermal) | ~100 GW | **5 of 5 balance at exactly 0.0 MW** |
| Synth8k 2031 draft (pre-swap) | ~65 GW | 3 of 5; **one scenario short ~4 GW, another short ~31 GW** |

The 8k shortfalls are genuine nameplate deficits — the whole conventional fleet runs flat out
— consistent with an earlier real-hour dispatch rebuild, larger here only because the datacenter block is held at full load while the rest scales down.

**Both base cases are DC-only skeletons** (`LineR ≤ 1e-6` and `LineC == 0` on 97.5% / 100% of
closed lines; median X/R **100,010** and **113,465**), so every scenario case built from them
inherits that and can never carry an AC study. See [case-impedance-completeness](../concepts/case-impedance-completeness.md).
