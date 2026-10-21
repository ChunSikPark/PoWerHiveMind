---
type: concept
domain: cross-cutting
topic: contingency
aliases: [parallel-contingency-solve, parallel-ctg, os-process-n1-sweep, contingency-parallel]
tags: [contingency, n-1, ctgsolveall, esapp, powerworld, multiprocessing, technique, cross-cutting]
---

# Parallel N-1 Contingency Solve (OS-process level)

## Abstract

A workaround for PowerWorld's own distributed `CTGSolveAll` being non-functional in this
environment: instead of relying on PowerWorld's DS server + registered compute hosts (which never
spawn workers here — it silently degrades to single-process serial), split the case's contingency
set into N chunks and run N independent `pwrworld.exe`/esapp instances as separate OS processes
(Python `concurrent.futures.ProcessPoolExecutor`), each solving a plain serial `CTGSolveAll` on
only its own chunk, then merge the per-bus voltage envelopes. Built for a reactive power planning study
to unblock a Synth8k N-1 sweep, which was timing out at 7200s
(2 hrs) serial. Live-measured: **~6-7x faster on the 8k case** (18.4 min vs. the 2-hr timeout,
more than 10k contingencies), but only **~1.7-1.8x on a smaller 2k case** (5,344 contingencies) — the
speedup scales with per-contingency solve cost because each worker pays a fixed ~20-45 sec
`open()` overhead that does not parallelize away.

## Connections

- **Up:** [Home](../index.md)
- **Used in:** a reactive planning study, as a parallel contingency-solve wrapper
- **💡 Could apply to (idea transfer):** any PowerWorld study that leans on `CTGSolveAll` for a
  large N-k contingency set — dynamic line rating branch-outage screening, any N-k security
  study; more generally, any SimAuto/COM-driven batch analysis where PowerWorld's own distributed
  computing can't be relied on (no DS server infrastructure).
- **Across:** [esapp](esapp.md) (the SimAuto wrapper each worker process opens independently) ·
  [powerworld-simauto](powerworld-simauto.md) (the COM server underneath — proven safe to open multiple independent
  instances concurrently; the rule is never `.exit()` a shared instance, always `.exit()` one you own)

## Content

### Why PowerWorld's own distributed computing doesn't help here

`CTGSolveAll(distributed=True)` requires a running DS (distributed-solve) server plus registered
compute hosts already set up in PowerWorld Simulator. On this machine, `VerifyDistributedComputersAvailable`
confirms the server is reachable but **zero workers ever actually spawn** — PowerWorld silently
falls back to single-process serial. That's a real, previously-diagnosed blocker: the Synth8k
case's N-1 set of more than 10k contingencies was timing out at 7200s (2 hrs) running serial. Distributed
computing settings are also GLOBAL Simulator settings, not serialized into the `.pwb` — so there is
no case-level fix, only an infrastructure one (standing up a real DS server), which is out of scope.

### The workaround: OS-process-level parallelism, not PowerWorld-level

Sidestep PowerWorld's distributed-computing feature entirely and parallelize one level up, at the
OS process level:

```
Case's existing CTGLabel set (already autoinserted + saved to a case file)
        │
        ▼  split into N chunks (np.array_split)
  N independent OS processes, each:
    - opens its OWN esapp/PowerWorld instance on the SAME case file
    - sets CTGSkip=NO only for its own chunk's labels, YES for everything else
    - runs a plain serial CTGSolveAll on just its chunk
    - returns its own per-bus Bus.BusMin/MaxVoltageContingency envelope
        │
        ▼  merge (pure function, no PowerWorld)
  min-of-mins on BusMinVoltageContingency, max-of-maxes on BusMaxVoltageContingency,
  joined on BusNum → same output shape as the serial function
```

This works because concurrent *independent* PowerWorld/esapp instances are safe on this machine —
the earlier assumption of "single-instance SimAuto" was proven wrong by a live probe (3 concurrent
handles, isolated reads+writes); the real rule is just **never call `.exit()`** on a shared/ambient
instance, not "one instance only." Each worker here opens and owns its own instance for its own
process lifetime, so that's a non-issue.

**The rule cuts the other way for an instance you own and reopen in a loop.** A worker that opens a
fresh case per candidate — the pattern a measurement harness uses so no tap or shunt state carries
between candidates — must call `.exit()` on **its own** instance before the next open. Dropping the
Python reference (`del pw`) does not release the COM server: measured 2026-09-28, each open left one
`pwrworld.exe` of ~1 GB running, and a run of four workers reached sixteen stray servers in a few
minutes, starving the other sweep on the machine. So: never `.exit()` a shared instance; always
`.exit()` one you opened and are done with. Killing the Python process eventually frees them too, but
only once COM notices the client is gone.

### CPU/RAM headroom — don't naively use `os.cpu_count()` workers

Live-measured on an i9-12900K (16 physical / 24 logical cores): 10 worker processes pegged the
**whole machine** near 100% CPU. Each `pwrworld.exe` worker burns **more than one logical core
internally** (PowerWorld's own sparse-solver threading is not user-controllable or documented), so
"1 worker == 1 logical core" is the wrong mental model — observed ratio was roughly 2.4 logical
threads per worker at `n_workers=10`. A `recommended_workers()` helper computes a conservative
default from both CPU headroom (`(logical_cores − reserve) // per_worker_cores`, defaults
`reserve=2`, `per_worker_cores=3`) and RAM headroom (`available_mb // per_worker_mb`, default
700 MB/worker, measured from the 8k run's actual `pwrworld.exe` footprints of ~150-600 MB each),
returning whichever bound is tighter. On this machine that resolves to **7**, not 10.

### GPU is not an option

PowerWorld's solver (`pwrworld.exe`) is a closed-source CPU sparse-LU Newton-Raphson engine
accessed only through the SimAuto/COM interface. There is no GPU path in PowerWorld itself, and
[esapp](esapp.md) is a thin Python wrapper around that COM interface — it cannot inject GPU acceleration
into solver internals it doesn't control. The only real lever for CTG solve speed here is OS-level
process parallelism (this technique), not GPU offload.

### Correctness check + measured numbers

Because this changes *how* the sweep runs but not the physics, the parallel result should exactly
match the serial baseline's violating-bus set — verified live (`ctg_parallel_demo.ipynb`, both
sweeps run back to back on the same case + same contingency set):

| Case | Contingencies | Serial | Parallel | Workers | Speedup | Match? |
|---|---|---|---|---|---|---|
| Synth2k series25 summerpeak | 5,344 (3,993 line + 1,351 xfmr) | 196-266 s | 107-152 s | 10 | 1.75-1.84x | Yes, exact violating-bus set |
| Synth8k (an ~8k-bus working model, see [lodf](lodf.md)) | more than 10k | ~7200 s (prior timeout, never completed) | 1,101 s (18.4 min) | 10 | ~6-7x vs. the timeout budget | violating buses found (about 2% of buses) |

The speedup ratio is **not constant** — it grows with case size / per-contingency solve cost,
because the fixed per-worker `open()` overhead (20-45 sec, does not parallelize away) is a much
smaller fraction of total time on the bigger, slower-per-contingency 8k case than on the smaller 2k
case. Run-to-run variance on the identical 2k case was also notable (196 s vs 266 s, ~35%) — likely
machine/process contention, not a code issue; don't trust a single sample when planning capacity
for a big sweep.

### Scope limitation (deliberate)

This technique parallelizes ONLY the base N-1 voltage sweep, not any remediation walk over
contingencies that mutates a shared base fleet sequentially (e.g. an after-removal security loop) —
that kind of loop can't be split this way since each fix changes state the next step depends on.
It also does not autoinsert contingencies itself — the case must already carry its N-1 set before
the parallel sweep opens it (autoinsert once, save, then hand that saved case path to the workers).
