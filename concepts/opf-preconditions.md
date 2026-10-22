---
type: concept
domain: tooling
topic: power-flow
aliases: [SolvePrimalLP, DCOPF preconditions, OPF constraints, BGAGC, opf-area-control]
tags: [powerworld, opf, dcopf, scopf, agc, cost-curve, gotcha, synthetic-grid]
---

# What an OPF needs before `SolvePrimalLP` will run at all

## Abstract

PowerWorld's LP OPF refuses to start unless **three** independent preconditions hold at
once: some area under OPF control (`Area.BGAGC = "OPF"`), some generators AGC-able
(`Gen.GenAGCAble = "YES"`), and those generators carrying a cost model that is not NONE.
Miss any one and you get a fatal error, not a degraded solve. That is the good news,
because the third condition is *data* and cannot be switched on honestly. Synthetic cases
routinely ship with all three off, so any OPF work on that case family hits this first.
This page records the three conditions, the confirmed field names and how
they were confirmed, the integrity trap in "just set a cost model", and the DC power flow
fallback that answers a thermal question without needing any of it. Verified 2026-09-11
on a regional synthetic planning model, Simulator 24.

## Connections

- **Up:** [powerworld-simauto](powerworld-simauto.md) · [Home](../index.md)
- **Across:** [aux-only-powerworld](aux-only-powerworld.md) (how this was driven, and the provenance rule that
  settled the field names) · [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md) (the cost-curve
  silent-zero traps) · [applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md) (same case family, AGC off)
- **Deeper:** [esapp-schema-reference](../references/esapp-schema-reference.md)

## Content

### The error, and what it actually means

```
Fatal Error: No Areas or Super Areas set as OPF Constraints
  To correct, on the OPF Area Records (or OPF Super Area Records) display
  toggle the AGC Status field to "OPF" for some areas/super areas
  Also, make sure some generators are set to AGC = YES and have a Cost Model
  that is not NONE.
```

The headline names one condition; the message body names two more. All three are
required. The OPF optimises *specific controls under specific constraints*, and with none
declared it has nothing to do and says so.

| # | Condition | Field | Nature |
|---|---|---|---|
| 1 | an area (or super area) under OPF control | `Area.BGAGC` = `"OPF"` | switch |
| 2 | generators the OPF may move | `Gen.GenAGCAble` = `"YES"` | switch |
| 3 | those generators priced | `Gen.GenCostModel` ≠ NONE | **data** |

### The field names, and how they were confirmed

`BGAGC` is **not** in the *Auxiliary File Format* manual, and neither is any other field name,
because that manual carries no per-object catalog (see [aux-only-powerworld](aux-only-powerworld.md)). It was
confirmed instead against esapp 0.2.1's generated schema, offline, without a PowerWorld
session:

```python
from esapp.components import Area
"BGAGC" in Area.fields()          # True  -- one of Area's 444 fields
Area.is_editable("BGAGC")         # True
Area.is_edit_mode_only("BGAGC")   # False -- writable in RUN mode, no EnterMode(EDIT)
```

`Gen.GenAGCAble`, `Gen.GenCostModel`, `Gen.GenCostCurvePoints` and `Gen.GenMCost` all
confirm the same way: real, editable, not edit-mode-only.

⚠ **`AGC_AGCStatus` is not an Area field.** It appears in this knowledge base's prose
([applying-a-dispatch-to-a-case](../methods/applying-a-dispatch-to-a-case.md), which now flags the name) as the area AGC-status field name and does not exist in
esapp's schema. Do not use it. A field name read out of a prose page is a lead, not a fact.
Check it against the schema before writing it into a script.

esapp declares no value vocabulary for `BGAGC`, so the literal `"OPF"` rests on
PowerWorld's own error text. If a write does not take, read the field's current value back
and match the spelling you see.

In aux, with `ALL` as the filter keyword (`""` is not legal; see [aux-only-powerworld](aux-only-powerworld.md)):

```
SetData(Area, [BGAGC], ["OPF"], ALL);
SetData(Gen, [GenAGCAble], ["YES"], ALL);
```

Then read both back before believing either. `SetData` reports success on writes that
change nothing.

### Condition 3 is data, and forcing it is a research-integrity failure

Conditions 1 and 2 are switches and may be flipped freely: they change what the OPF is
*allowed* to do, not what the answer is. Setting `GenCostModel` to something non-NONE
without real cost curves means inventing fuel costs, and the resulting dispatch is then
driven entirely by fabricated numbers. It will look like an economic dispatch, produce a
cost column, and mean nothing. **Check whether the case
carries cost data; do not manufacture it.**

Per [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md), the guard is
`GenCostCurvePoints > 0 AND GenMCost > 0`. `GenCostCurvePoints == 0` means no curve was
ever fit and the cost fields read `0`, which is *no data*, never *free*. A handful of
units can also report `GenMCost == 0` with curve points defined.

**Refined 2026-09-30, measured on a public synthetic 37-bus case.** Those units are the wind and
solar: five curve points each, and a curve that is 0 at their output. The OPF solved with them in
the movable set. `GenMCost` is the curve *at today's output*, so a zero there is a price of zero,
not missing data. The case-auditor therefore counts a unit as priced when `GenCostModel` is not
None and `GenCostCurvePoints > 0`, says nothing about a zero-cost renewable, and flags a
*thermal* unit whose curve reads 0 as worth a look.

**Refined again 2026-10-01, measured on Synth2k.** Some units on a Cubic cost
model read `GenCostCurvePoints = 0` with `GenMCost > 0` (others carry curve points): a cubic model is evaluated from its
coefficients, not from curve points, so a zero point count there is not missing data. The
auditor counts a unit as priced when `GenCostModel` is not None and it has curve points or a
positive cost at today's output (`GenCostCurvePoints > 0` or `GenMCost > 0`). A unit with
neither still counts as carrying no cost data.

Synthetic cases are the live hazard here. A generation pipeline may assign piecewise cost
curves at build time, but whether they survived into the dated case you are holding is a
question about that file, so measure it.

**And the measurement can come back unsatisfiable.** On a ~9k-bus synthetic planning model,
2026-09-11:

| Field | Reading |
|---|---|
| `GenCostModel` | `"None"` on **every** unit |
| `GenCostCurvePoints` | `0` on every unit |
| `GenMCost` | zero nonzero values |
| `GenAGCAble` | `"NO"` on all but one |
| `Area.BGAGC` | one area, `"Off AGC"` |

Conditions 1 and 2 were one `SetData` each. Condition 3 had nothing to switch on: the case
carries no cost data. **DC OPF is therefore not available on that case at all** until
cost models are populated upstream. No tuning or setting fixes absent data. Check for this
*before* designing a study around an OPF: the recon costs seconds, and the alternative is
discovering it at the solve.

This also fixes the shape of the value vocabulary: `BGAGC` reads back as the
human-readable string `"Off AGC"`, spaces included, which makes `"OPF"` from PowerWorld's
error text the right shape to write.

### `Sim_Solution_Options` is the lowest-priority place to set a solve mode

`SetData(Sim_Solution_Options, [DCApprox], [YES]);` is how the DC approximation gets set in
an aux, and it works. But the manual documents `Sim_Solution_Options` only as a
SUBDATA section nested inside `Contingency`, `CTG_Options` and `QVCurve_Options`, never as a
standalone `SetData` target. The shape is an analogy to the sibling `Equiv_Options` (which
the manual explicitly says may be set "using the SetData action, or a DATA section"), not a
citation.

What the manual does settle is **precedence**, which bites the moment OPF meets
contingency analysis. Contingency analysis reads power flow solution options from three
places, and applies them in this order of precedence:

1. options stored on the individual contingency record
2. options stored on the contingency tool (`CTG_Options`)
3. the global solution options

**Global solution options rank last.** Setting DC once at the top of an aux does not make it
true during contingency analysis: anything the contingency record or `CTG_Options` carries
overrides it. This is why a research pipeline's SCOPF sequence sets both
`Sim_Solution_Options.DCApprox` *and* `CTG_Options.CTG_CalculationMethod`.

### Super areas count, and a refusal through SimAuto does not raise

Measured 2026-09-30 on two public synthetic cases, in memory, never saved:

| as the case opened | OPF (`InitializePrimalLP`, `SolvePrimalLP`) |
|---|---|
| a super area on OPF, every member area (`Area.SAName`) `Off AGC` | **ran**: *Successful Solution* |
| an area on OPF inside a super area that is `Off AGC` | **ran**: *Successful Solution* |
| every area and super area switched to `Off AGC` | **refused** |

So condition 1 is met by an area **or** a super area on OPF; a super area on OPF makes its member
areas redispatchable, and one that is `Off AGC` does not override a member area set to OPF.
`SuperArea.BGAGC` reads back the same strings as `Area.BGAGC` (`OPF`, `Off AGC`).

The refusal did **not** raise through esapp: both calls returned, and the only sign was
`OPFSolutionSummary.LPOPFSolutionStatus = "Error = No area/superarea constraints set"` with
`LPOPFCostFunction:1 = 0`. Read the status after every solve; a script that trusts the absence
of an exception reads a zero-cost "solution".

### Always give the solve a failure handler

`SolvePrimalLP` takes four optional arguments (a success slot, a failure slot, and two
create-if-not-found flags), and either filename slot accepts the literal `STOP`, meaning
halt all aux execution:

```
InitializePrimalLP("", STOP);
SolvePrimalLP("", STOP);
```

Bare `SolvePrimalLP;` has no failure handler. A refused or non-converged OPF then becomes
one line in the log while every later stage runs against an **unsolved case** and writes
plausible numbers into correctly-named files. `SolveSinglePrimalLPOuterLoop` and
`SolveFullSCOPF` carry the same slots. See [aux-only-powerworld](aux-only-powerworld.md).

### "Successful Solution" can still leave a limit unenforced

`OPFSolutionSummary.LPOPFSolutionStatus = "Successful Solution"` does not mean every limit
holds. When no controllable unit can relieve a branch, the LP relaxes that constraint, prices it
at the penalty cost, and reports success anyway. Measured 2026-09-24 on Synth40: two 69 kV lines
were left at 138% and 120%. The only AGC-able units sat on the far side of the network, so no
dispatch could unload those lines. Check after every OPF:

```python
b = pw[Branch, ["LineLPUnenforceableMVA", "LinePercent", "LinePercent:1"]]
unenforced = b[b["LineLPUnenforceableMVA"].astype(str).str.strip() == "YES"]
```

A non-empty result is a network limit (transmission, or dispatchable generation on the wrong
side), not a dispatch finding. `OPFSolutionSummary.LPOPFMC` reading the penalty price is the same
signal from the other end.

### Flipping condition 2 globally is blunt

`GenAGCAble = "YES"` on every unit lets the OPF redispatch the entire fleet, including
units that would never move in operation. Acceptable for a first look; narrow it before
any result is reported.

### The fallback that needs none of this

If the question is *thermal* (what happens to branch loadings when an element is removed),
a **DC power flow** answers it and requires no area control, no AGC flags and no cost data:

```
SetData(Sim_Solution_Options, [DCApprox], [YES]);
SolvePowerFlow(DC);
```

What is lost versus a DC OPF is economic redispatch. On a case whose areas are off AGC
and whose units are almost entirely not AGC-able, very little was being redispatched
anyway.

Two things to carry into the comparison:

- **A DC solve pins every bus to exactly 1.0 pu** ([lodf](lodf.md)). So neither DC OPF nor DC
  power flow yields any voltage answer; a before/after voltage table from a DC run is
  identically zero change. Voltage requires an AC re-solve at the post-change dispatch,
  compared against an AC baseline.
- `pw.dc_mode` is effectively one-way ([lodf](lodf.md)); prefer the explicit script form above and
  verify by checking that the bus voltages really did go to 1.0.
