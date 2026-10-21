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
power-balance limit, not a Newton failure, and probes 2–4 below do not apply.

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
a single long tie**: none was an island, a real-power infeasibility, or a thermal overload (nothing near the collapsing pocket exceeded its rating at the last solvable step).
Local generators near several pockets still had reactive headroom that could not reach the
collapsing bus. The fix is structural:
[finding-and-fixing-radial-by-n1-pockets](finding-and-fixing-radial-by-n1-pockets.md).

### Traps, each of which reports success

- **Restoring a saved state may not restore the case you saved.** Suspected, not confirmed: in
  the example study a previous `CTGApply`'s topology survived `LoadState()`, and every later probe
  in the same process measured the previous outage's pocket (an outage far away "showed" the first
  one's collapse). A raw-COM repro (2026-10-21) restored MW and branch status, so the `CTGApply`
  case is unreproduced; but it did **not** restore branches created or deleted in between, nor
  impedance edits (`LineR`). So an impedance walk (probe 3) "undone" by `LoadState` is not undone.
  Possibly by design. Workaround either way: run one outage per fresh
  process, or **fingerprint** before every probe (closed-branch count plus a voltage near the
  element) and stop on a mismatch. A control that only checks "the base still solves" passes this
  bug.
- **`SetData("Sim_Solution_Options", ["DCApprox"], ["YES"])` does not make `SolvePowerFlow()`
  solve DC.** It still runs Newton, so "DC fails" is just the AC failure again. Use
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
