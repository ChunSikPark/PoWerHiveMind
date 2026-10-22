---
type: concept
domain: tooling
topic: scripting
aliases: [esapp-wrappers, runscriptcommand-vs-named-method, esapp-named-methods]
tags: [esapp, powerworld, simauto, script-commands, runscriptcommand, api-drift, house-rule]
---

# Named SAW methods vs. `RunScriptCommand`

## Abstract

House rule for every line of PowerWorld-from-Python code: call the named esapp method
(`pw.esa.TimeStepDoRun()`), not the hand-written script string
(`pw.esa.RunScriptCommand("TimeStepDoRun;")`). 310 of esapp 0.2.1's SAW methods wrap a
PowerWorld SCRIPT command. Both forms reach the same COM call; the named method
buys a Python-side signature check, correct argument-string construction, and, above all,
**one place the maintainer can patch when PowerWorld changes a command's syntax**. This
page records the rule, the exact mechanism (so nobody overclaims it as runtime
validation), the two live-probed exceptions already settled elsewhere in this knowledge base, and
the related 0.2.1 change that turned a write-time `ValueError` into a warning. Origin:
feedback from the esapp author on the author's `pw.esa.RunScriptCommand` usage, verified
against the 0.2.1 source on 2026-09-08.

## Connections

- **Up:** [esapp](esapp.md) · [Home](../index.md)
- **Across:** [powerworld-simauto](powerworld-simauto.md) · [aux-script-commands](../references/aux-script-commands.md) (SCRIPT names) ·
  [esapp-overview](../methods/esapp-overview.md)
- **Exceptions to this rule:** [save-powerworld-case](../methods/save-powerworld-case.md) (COM `SaveCase` is a silent
  no-op; the *script* `SaveCase` is the one that writes)
- **Obsoleted by 0.2.1, needs re-check:** [converting-lines-to-transformers](../methods/converting-lines-to-transformers.md)
- **Deeper:** [esapp-package-backend](../references/esapp-package-backend.md)

## Content

### The rule

```python
pw.esa.TimeStepDoRun()                       # correct
pw.esa.RunScriptCommand("TimeStepDoRun;")    # wrong
```

Applies to every SCRIPT command esapp wraps: 310 named methods across 20 SAW mixins in
0.2.1, covering roughly 300 of the ~370 SCRIPT actions Simulator defines.

### Why — the actual mechanism

Both forms end at the same COM call. `SAWBase._run_script` (`esapp/saw/base.py:185`) is
a thin builder:

```python
arg_list = list(args)
while arg_list and arg_list[-1] is None:   # strip trailing Nones
    arg_list.pop()
stmt = f"{command}({arg_str});" if arg_list else f"{command};"
return self.RunScriptCommand(stmt)
```

`TimeStepDoRun` (`saw/timestep.py:10`) is
`self._run_script("TimeStepDoRun", start_time or None, end_time or None)`. The wrapper does
nothing special at the COM boundary. The win is three ordinary things:

1. **The signature is checked in Python, before COM.** `TimeStepDoRun(start_time: str =
   "", end_time: str = "")` is typed. A wrong arg count is a `TypeError` on your machine,
   not a misbehaviour inside Simulator.
2. **The argument string is built correctly.** Trailing-`None` stripping, `format_list()`
   bracket lists with proper quoting, `format_filter()` and the `_enums` types
   (`FilterKeyword`, `SolverMethod`, `TSGetResultsMode`, …), so a bogus filter name or
   solver method cannot reach PowerWorld. Hand-rolled f-strings get this wrong.
3. **One patch point.** When PowerWorld changes a command's syntax, the fix lands in
   esapp and `pip install -U esapp` repairs every call site at once. A hand-written
   string is a call site the maintainer can never reach.

### What it does NOT do — do not overclaim this

esapp does **not** introspect PowerWorld's live command table, does **not** check the
installed Simulator version, and does **not** auto-correct a stale command at runtime.
Confirmed byte-identical in `_run_script` across 0.1.3 and 0.2.1. The guarantee is an
**upgrade path, not a runtime check.**

A hand-written string does not fail silently *if PowerWorld reports an error*: `_com_call` (`saw/base.py:378-387`) raises
`PowerWorldError` on any non-empty error string, specialised by
`PowerWorldError.from_message` into `SimAutoFeatureError`, `PowerWorldPrerequisiteError`,
or `PowerWorldAddonError`. The dangerous case is narrower: **a
command whose name stays valid but whose parameter order or meaning changes.** The string
"succeeds" and does the wrong thing. That is what the typed wrapper prevents.

(`CommandNotRespectedError` was **removed in 0.2.0**. Do not reference it.)

### When `RunScriptCommand` is correct

Only when no named wrapper exists. About 41 of the catalogued actions have none,
largely oneline/GUI actions (`OpenOneline`, `ExportOneline`, `Animate`), dialogs
(`MessageBox`, `ObjectFieldsInputDialog`), and a few writers
(`ATCWriteToExcel`, `SaveDataUsingExportFormat`).

Look the command up in the **SCRIPT command → esapp method index** at the bottom of
esapp's own method list before concluding one is missing. Absence from
[aux-script-commands](../references/aux-script-commands.md) proves nothing, since that
page is a task-organized working subset rather than a complete index.

Leave a comment saying why whenever you do call `RunScriptCommand`.

### Exception: `SaveCase` — the script command beats the COM method

[save-powerworld-case](../methods/save-powerworld-case.md) is live-probed and still stands: `pw.esa.SaveCase(...)` is a
**silent no-op** on this machine (returns `None`, raw COM returns `('',)` = success, no
file appears), while the aux script form writes:

```python
pw.esa.RunScriptCommand(f'SaveCase("{out}", PWB);')   # exactly 2 params
assert os.path.exists(out), "SaveCase reported success but wrote nothing"
```

There is no contradiction. esapp routes `SaveCase` through `_com_call`, not
`_run_script`, so it is not one of the 310 SCRIPT wrappers this rule governs. The rule
says *prefer the named wrapper over a hand-written string for the same command*; here the
COM method and the script command are different code paths with different behaviour, and
the script path is the one that works. Same for `OpenCase`/`CloseCase` being absent from
the SCRIPT index.

### Related: 0.2.1 turned a write-time `ValueError` into a warning

A different rule from the same philosophy: esapp treats PowerWorld as the authority and
does not let its own generated schema block you.

Through 0.1.x, writing an unknown or read-only column raised
(`indexable.py:228`, `:280`):

```
ValueError: Cannot set read-only field(s) on Branch: [...]
```

In 0.2.1 that became `warnings.warn` and **the write is still attempted**
(`indexable.py:198-210`): *"PowerWorld is the authority, and the generated schema may lag
the installed Simulator version."*

Two consequences:

- **A field-name typo no longer raises.** `pw[Gen, "GenMWW"] = 100` emits a warning to
  stderr and writes nothing useful. This joins the same silent-no-op
  family as dropping an object's key fields ([applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md)) and as
  the COM `SaveCase` above: the call reports success and the effect never happens.
  **Do not reach for `python -W error::UserWarning` to fix this.** That was the advice
  here through 2026-09-09, and it backfires because the *same* warning fires on ~150
  fields that write perfectly well (below). Assert the effect instead: read the field back
  and compare.
- **`Read-only field(s)` is usually a false alarm.** The flag comes from esapp's generated
  schema, which keeps only fields whose `enterable` is an unconditional `Yes` and discards
  every conditional one. PowerWorld's own answer for `LineStatus` is *"Depends: Normally
  enterable except when field Lockout is YES"*, so esapp calls it read-only and the write
  works anyway. Counted against build 2026-07-22: **112 Branch fields, 33 Bus, 5 Gen
  (including `GenMVR`), 1 Load** are enterable in PowerWorld but `is_settable() == False`.
  The authority is `pw.esa.GetFieldList(<type>)`, whose `enterable` column is PowerWorld's,
  not esapp's.
- **The `XF*` bypass in [converting-lines-to-transformers](../methods/converting-lines-to-transformers.md) is now confirmed
  unnecessary.** ✅ **Verified live 2026-09-10** on a ~2,000-bus synthetic case, Simulator build 2026-07-22,
  esapp 0.2.1: `pw[Branch] = df` carrying `LineXFMR='YES'` warns and goes through:
  `BranchDeviceType` flips `Line` → `Transformer`, on a 2-row subset, no exception. That
  page has been rewritten accordingly.

### Provenance

Author feedback relayed by the author, 2026-09-08. Verified against the esapp 0.2.1 source
(`github.com/lukelowry/ESApp`, `VERSION` 0.2.1, 2026-09-01) and diffed against the 0.1.3
build then installed in site-packages. The readthedocs `api/saw.html` page states none of
this; it documents `RunScriptCommand` neutrally, so this page is the only written record of
the rule.
