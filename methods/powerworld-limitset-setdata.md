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
change — unlike most other PowerWorld objects, where key + changed fields is enough. Live-verified
by round-tripping the same case's `LimitSet` values through a CSV export/reimport and a
`SetData` script command.

## Connections

- **Up:** [esapp](../concepts/esapp.md)
- **Across:** [save-powerworld-case](save-powerworld-case.md) · [adding-devices-esapp](adding-devices-esapp.md) · [powerworld-simauto](../concepts/powerworld-simauto.md)
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
