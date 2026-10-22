# Case-auditor (Plan 2 of 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the kit's second agent — a read-only case auditor that says, with evidence, whether a PowerWorld case is sane and READY for a base power flow, an N-1 (its monitoring), a time step and an OPF, opens every answer with a case summary the engine computed, and names every blocker by its object keys — plus the four rule pages and the three 0b page fixes it cites.

**Architecture:** Pure rule functions over a `CaseData` (named pandas DataFrames plus scalars) that never import esapp, so every rule is unit-tested on hand-built frames with no PowerWorld. One thin esapp reader opens the case, runs **one** AC solve in memory, reads only the fields the rules need, and closes with `esa.exit()` in a `finally`. A CLI, `audit.py --case <pwb> [--profiles base,timestep,opf] [--pww <file>] [--out <dir>]`, writes `findings.json` and `findings.md` (verdicts, `case_summary`, findings, the read-only proof) into `./case-audit/<case name>/` by default. The shipped CLI has no snapshot flags: storing what was read and replaying it are developer tools in `tools/case-audit-dev/`, outside `skills/`, and a replay stamps its output as one. Tests run the real reader against a stand-in esapp that serves a stored public-case snapshot. A skill (`skills/case-audit/SKILL.md`) carries the procedure; the agent (`agents/case-auditor.md`, moved from its draft in the last task) is the role contract.

**Tech Stack:** Python 3.11+ (dry run on 3.13.14), pandas, numpy, esapp 0.2.1 (the reader only), pytest. `claude plugin eval` for the agent evals.

**Spec:** `docs/superpowers/specs/2026-09-28-power-system-agents-design.md` (§4 case-auditor, §10 auditor test rows, §11 steps 0b and 2). **Agent brief:** `docs/agents/case-auditor.md` — the engine produces exactly what that file says the agent receives, and Task 17 lists every edit the brief needs.

**Revision 3 (2026-09-30)** — revision 2 came after a serial architect → critic review (both REVISE); revision 3 fixes the eight defects a critic's re-check found in revision 2. What changed and why is in the revision record at the end. Every code block below was run from a **fresh** scratch clone of the kit before it was written here: **case-audit suite 166 passed, 1 skipped** (the live test, which passed separately against Hawaii40 with `PWHM_LIVE_CASE` set); whole kit `python -m pytest skills -q -p no:cacheprovider` **211 passed, 1 skipped**. The probe (Task 1), one OPF per case, and the engine were run live on the two public cases; every PowerWorld instance was closed and both case files were byte-identical afterwards.

**Decisions this plan follows (made before it was written):**

| # | decision |
|---|---|
| D1 | Pure rules over `CaseData`, one esapp reader, a CLI writing `findings.json` + `findings.md`; summary numbers computed by the engine, never the agent |
| D2 | Read-only proof: sha256 of the case file before and after, in `findings.json`; an AST test fails the build if the engine names SaveCase, LoadAux, ChangeParameters*, SetData, WriteAuxFile, Delete, or any `RunScriptCommand` (the same idea as a no-SaveCase test used elsewhere — described, not imported). Revision 2 adds an allowlist over every esapp-bound name in `reader.py` and a test that only `reader.py` imports esapp (R7) |
| D3 | `base.ac_converges` = `SolvePowerFlow` did not raise **and** max bus mismatch ≤ `Sim_Solution_Options.ConvergenceTol:2` (MVA). Never `vmap.solve()`; no retry, no flat start, no DC |
| D4 | A live probe (Task 1) resolves every UNVERIFIED item first; the rules are written against what it observed |
| D5 | Unsourced numbers are named constants in `engine/thresholds.py`, each commented "proposed default, <why>", and listed in the rule pages. `base.gen_over_nameplate` stops past max(1 % of `GenMWMax`, 5 MW), Worth a look above 0.1 MW |
| D6 | `base.ltc_middle_target` is ONE aggregated finding (count + most common band); the full list is in `findings.md` |
| D7 | Three-winding LTCs are out of scope for v1; the rule page and the finding text say so |
| D8 | Not in scope, listed as open questions: a band copied from the tap range, the structure-only stub FYI, `Gen.GenRegNum` pointing at nothing, an `n1` coverage profile |
| D9 | 0b items owned here: reword the ISO / `CustomString:2` lines of `methods/timestep-simulation-setup.md` and replace its "pfw copperplate" reference with the Auto_PFW handoff; port `auto-pfw-scripts` (scrubbed); fix the `XFAuto` gloss in `methods/converting-lines-to-transformers.md` |
| D10 | `ts.pww_footprint` reads the `.pww` header per `concepts/pww-data.md` with a small reader in the kit; no file given → one FYI |
| D11 | Evals on pre-computed `findings.*` from the real engine on the public cases, regex graders plus one `llm` grader, and a `tool_used` grader on `Agent` |
| D12 | The last task moves the agent into `agents/`, registers it, updates `docs/agents/README.md`, re-checks discovery, rebuilds `dist/`, and lists every change to the agent text |

**Rulings for revision 2** (from the review coordinator; the plan follows them):

| # | ruling |
|---|---|
| R1 | The shipped `audit.py` has no snapshot flags. `snapshot.py`, `replay.py`, `make_fixture.py`, `scrub_findings.py` and `probe.py` live in `tools/case-audit-dev/`. A replay is stamped `"source": "snapshot"`, `read_only.unchanged: null`, and findings.md's first line reads "Replayed from a stored snapshot; no case was opened". Seeded fixtures come from replays; real ones from live runs, path-scrubbed. CLI tests drive the real `--case` path through a stand-in esapp |
| R2 | Default `--out` is `./case-audit/<stem>/` under the working folder, holding a `.gitignore` of `*`; the path is printed once. Variants are found with `Path.exists()` on computed names; the folder is never listed |
| R3 | The super-area question is settled live (Task 1): an OPF solved on both public cases as they opened, including Texas2k's super area on OPF with every area Off AGC, and Hawaii40's area on OPF inside an Off-AGC super area. A super area on OPF makes its members OPF areas; condition 3 is judged per OPF area |
| R4 | Priced = `GenCostModel` ≠ None **and** `GenCostCurvePoints > 0`. `GenMCost = 0` with a curve is no finding on a renewable, and Worth a look / Probably on purpose on a thermal unit |
| R5 | Evals: no `Skill` in `allowed_tools`; the dispatch grader pins `"subagent_type"`; fixture paths in the prompt body; seeded judgment cases with `not_contains` graders and a line-count regex; the inferred parts named |
| R6 | A failed open stops only the `pwrworld.exe` processes that are new since it began (a helper, tested with a fake process lister) |
| R7 | The AST guard: an allowlist over esapp-bound names, bound-name tracking, the existing substring scan, and `test_only_reader_imports_esapp` |

**Plans 3–4** (study-runner, network-visualizer) are written after this plan ships.

## Global Constraints

- Everything ships inside the kit and is self-contained: no imports from any private research repository.
- Never `cd` in a compound shell command; run every command from the kit root, with absolute paths for anything outside it.
- Commit messages carry no AI attribution lines. `git add` is always path-scoped, never `-A`.
- The kit is public: no case-specific data. The two public synthetic cases may be named with their numbers. **Never** read, list or scan the machine's CEII folders; point tools only at the two public cases below.
- The engine never writes a case (Task 5's AST test). The dev probe (Task 1) is the only code that edits a case, in memory, and it lives in `tools/case-audit-dev/`, outside `skills/`, so no agent is pointed at it.
- A snapshot holds every field the engine reads for every object of a case. Take one only of the two public cases, and commit one only after `make_fixture.py`.
- Every PowerWorld instance is closed with `esa.exit()` in a `finally`.
- Run pytest with `-p no:cacheprovider`. Test file names start `test_audit_` so they never collide with the schema-lookup suite when both run in one session (pytest imports test modules by basename).
- The public cases are not in the kit. Set three variables to your local copies before Tasks 1, 5 and 16 (all public synthetic grids):

```bash
export HAWAII40=/abs/path/to/Hawaii40_base.pwb                                   # 37 buses
export HAWAII40_PWW=/abs/path/to/Hawaii_KonaDay_SYNTHETIC.pww                   # its 3-day weather file
export TEXAS2K=/abs/path/to/Texas2k_series25_case1_summerpeak_PFW.pwb            # 2,751 buses, PFW models attached
```

- **Do not push.** The parent session reviews and pushes.

## Review Focus

1. **An object with zero rows.** `GetParametersMultipleElement` returns `None`, not an empty frame (confirmed live: `3WXFormer` on both public cases). A case with no shunts, loads or contingencies must audit, not crash. → Task 4 `test_none_frame_becomes_empty_frame_with_columns`; Task 5 `test_reads_every_object_and_exits` (Gen reads `None`); Task 6 `test_summary_of_a_case_with_no_shunts_or_loads`.
2. **A case that will not converge.** esapp raises `PowerWorldError` (probed: "Exceeded maximum number…", "Power flow unable to converge"), so the raise decides; the mismatch is a second check, applied only when both it and the tolerance were read. Expect NOT READY everywhere, one solve only, every solve-dependent rule listed as not checked, and the summary marked as unsolved. → Task 4 `test_converged_needs_no_raise_and_mismatch_under_tolerance`, `test_an_unreadable_tolerance_does_not_fail_the_case`; Task 5 `test_a_solve_that_raises_is_recorded_not_retried`; Task 7 `test_raised_solve_stops_every_study`; Task 13 `test_unsolved_case_is_not_ready_and_says_what_was_not_checked`.
3. **`LineCircuit` is text.** PowerWorld pads it (`" 1 "`), and circuits like `01` or `W2` exist; casting to int loses or breaks keys, and a finding without exact keys cannot be acted on. → Task 4 `test_line_circuit_stays_text`; Task 8 `test_ltc_pointing_at_a_disconnected_bus`.
4. **A huge case.** The reader reads only `casedata.READS` (Texas2k: open, solve, read and close in about 12 s; the branch read is ~1 s for 5,344 rows × 41 fields); the bridge search is iterative with integer subtree sizes, and a far side is only built, capped, for the few bridges the stub rule asks about; the weather reader stops at the station list. → Task 9 `test_long_chain_is_linear_in_time_and_memory` (20,000-bus chain, peak memory under 200 MB); Task 11 `test_the_public_hawaii_weather_file_header`.
5. **The auditor run from outside the kit, on a cp1252 console, into a folder with a non-ASCII name.** Under a plugin install the cwd is the user's project; Windows consoles default to cp1252; the output must not land in a git tree unignored. → Task 14 `test_runs_from_outside_the_kit`, `test_survives_a_cp1252_console_with_a_non_ascii_folder` (fails without the console fix, checked), `test_default_out_is_under_the_working_folder_and_ignored`; Task 13 `test_files_are_utf8_whatever_the_names`.

---

## What the probe found (Task 1, run 2026-09-30)

These are the observations every later task is written against. Rows marked **changed a rule** altered the detection spec.

| question | observed on Hawaii40 and Texas2k | consequence |
|---|---|---|
| Does a non-converged AC solve raise? | Yes: `PowerWorldError` "NR PowerFlow - Power flow unable to converge" (load ×12 on Hawaii40) and "…Exceeded maximum number…" (load ×4 on Texas2k). At load ×8 Hawaii40 still "converged" to a 0.18 pu minimum voltage | the raise is the deciding signal; mismatch is the second check (D3); convergence is not sanity |
| `GetParametersMultipleElement` on zero rows | `None` (`3WXFormer`) | `typed()` turns `None` into an empty frame with its columns |
| `XFRegBus = 0` / `SSRegNum = 0` | a SimAuto write of 0 is **silently refused** (previous value stays); a write of another bus takes; own-bus shunts read their own bus number (1 of 1, 202 of 202) | **changed a rule:** 0 is never "own bus"; `reason = "zero"` is a defect |
| `Shunt.AutoControl` | `YES` on every regulating shunt | used as written |
| `Bus.BusIsStarBus` | `NO` on every bus; `3WXFormer` 0 rows on both | whether 3-winding legs appear in `Branch` stays untested (D7) |
| `XFRegTargetType` values | `Middle` on all 12 / 1,351 transformers; no active LTC on either case (all `Fixed`, `XFAuto = NO`) | LTC rules tested on hand-built cases only |
| `Bus.BusVoltLimLow/High` | limit group 0.9 / 1.1 on every bus, read back `0.89999998` / `1.10000002`; an in-memory override 0.95 / 1.04 read back `0.94999999` / `1.03999996` | effective limits; the 0.94 / 1.05 fallback applies only to 0 or blank |
| System MVA base | `Sim_Solution_Options.SBase = 100` on both | the stub charging estimate reads `SBase` per case |
| `ConvergenceTol:2` (MVA) | 1e-5 on Hawaii40, 0.1 on Texas2k | the tolerance is read per case |
| `Gen.Latitude` / `Gen.Latitude:1` | bus pair **blank on every unit** (9 / 400 renewables); the substation pair ("Substation Latitude" in the export) set on all | **changed a rule:** `ts.latlon_missing` accepts either pair; which one TimeStep reads is not verified in the kit |
| `Branch.LineLength` | 0 on every branch | **changed a rule:** `base.dc_skeleton` cannot count zero-length branches; it uses median X/R > 1000 or ≥ 90 % of closed lines with R ≤ 1e-6 and B = 0 |
| `Gen.CustomInteger:1` | blank (`None`) on every unit | Auto_PFW would skip every unclassified wind unit on these cases |
| `SuperArea.BGAGC`, `Area.SAName` | Hawaii40: area 1 `OPF` inside super area `FullCase` = `Off AGC`. Texas2k: super area `Texas` = `OPF`, all 8 member areas `Off AGC` | membership is `Area.SAName` |
| One OPF as the case opened (`InitializePrimalLP`, `SolvePrimalLP`) | **ran** on both: *Successful Solution*, cost 4,206 (Hawaii40) and 260,127 (Texas2k) | **changed a rule:** a super area on OPF meets condition 1 and makes its members OPF areas; an Off-AGC super area does not override a member on OPF. Texas2k's `opf` is READY |
| The same OPF with every area and super area `Off AGC` (in memory) | **did not raise**; `LPOPFSolutionStatus = "Error = No area/superarea constraints set"`, cost 0 | a refused OPF is a status string, not an exception; recorded in `concepts/opf-preconditions.md` (Task 3) |
| `GenMCost` on units with a curve | 0 on Hawaii40's wind and solar (5 curve points each), and the OPF above ran with them movable | **changed a rule:** priced = cost model and curve points; a zero price is not missing data (R4) |
| `ViolationCTG` rows as opened | 14 (Hawaii40), 173 (Texas2k) | `base.stale_ctg_results` fires on both public cases |
| esapp `Scale(LOAD, FACTOR, [4], SYSTEM)` | system load **unchanged** on both (silent no-op) | the probe scales load by writing `LoadMW`/`LoadMVR`; no kit page covers this |

---

## File Structure

| file | responsibility |
|---|---|
| `tools/case-audit-dev/probe.py` | live probe of the fields the rules depend on, plus one OPF (edits in memory, never saves; outside `skills/`) |
| `tools/case-audit-dev/snapshot.py` | read a public case the way the engine does and store what was read |
| `tools/case-audit-dev/make_fixture.py` | turn a snapshot into a public fixture (file name only), optionally seeded with one defect |
| `tools/case-audit-dev/replay.py` | audit a snapshot with no PowerWorld, stamped as a replay |
| `tools/case-audit-dev/scrub_findings.py` | turn every absolute path in a live audit's findings into its file name |
| `methods/ltc-regulation-checks.md` (create) | rule page for `base.regulates_nothing`, `base.ltc_middle_target`, `base.ltc_regulates_lv_side` |
| `concepts/unloaded-ehv-stub-overvoltage.md` (create) | rule page for `base.floating_stub` |
| `concepts/auto-pfw-scripts.md` (create) | the Auto_PFW handoff for missing PFW models |
| `concepts/opf-preconditions.md` (modify) | super areas, the silent refusal, zero-cost renewables — measured |
| `methods/timestep-simulation-setup.md`, `methods/converting-lines-to-transformers.md`, `index.md` (modify) | 0b fixes and index rows |
| `skills/case-audit/engine/thresholds.py` | every number the rules compare against |
| `skills/case-audit/engine/casedata.py` | `READS`, `typed()`, `Solve`, `CaseData` (+ snapshot JSON) |
| `skills/case-audit/engine/findings.py` | `Finding` (with `handoff`), the closed severity/triage sets, `clean()`, key helpers |
| `skills/case-audit/engine/reader.py` | the only esapp module: open, one AC solve, read, `exit()`; stray-server cleanup on a failed open |
| `skills/case-audit/engine/summary.py` | the case summary; which areas the OPF may move |
| `skills/case-audit/engine/rules_base.py` | `ac_converges`, `dc_skeleton`, `gen_over_nameplate`, `stale_ctg_results` |
| `skills/case-audit/engine/rules_reg.py` | `regulates_nothing`, `ltc_middle_target`, `ltc_regulates_lv_side`, step-up detection |
| `skills/case-audit/engine/topology.py` | iterative bridges, integer far-side sizes, a capped far-side search |
| `skills/case-audit/engine/rules_stub.py` | `floating_stub` |
| `skills/case-audit/engine/rules_mon.py` | the six monitoring rules |
| `skills/case-audit/engine/pww.py` | `.pww` header and station reader |
| `skills/case-audit/engine/rules_ts.py` | `pfw_missing`, `latlon_missing`, `pww_footprint`, `coverage` |
| `skills/case-audit/engine/rules_opf.py` | the three OPF conditions, per area, and the per-area table |
| `skills/case-audit/engine/checks.py` | rule registry, `run_rules`, `verdicts` (with `scopf`) |
| `skills/case-audit/engine/report.py` | `build`, `render_md`, `write` |
| `skills/case-audit/engine/audit.py` | the CLI (standard library only at import) |
| `skills/case-audit/tests/conftest.py`, `auditcase.py` | engine on `sys.path`; the 6-bus toy case; the Hawaii40 fixture; the stand-in esapp fixture |
| `skills/case-audit/tests/fake_esapp/esapp/__init__.py` | a stand-in esapp that serves a stored snapshot |
| `skills/case-audit/tests/fixtures/hawaii40.json.gz` | what the reader read from Hawaii40 (public; file name only) |
| `skills/case-audit/tests/fixtures/hawaii_konaday_header.pww` | the header and station list of the public Hawaii40 weather file |
| `skills/case-audit/tests/test_audit_*.py` | one file per task |
| `skills/case-audit/SKILL.md` | the procedure any harness follows |
| `evals/<case>/…` | eight eval cases for the agent |
| `agents/case-auditor.md` (moved from `docs/agents/`) | the role contract |
| `.gitignore`, `README.md`, `AGENTS.md`, `GEMINI.md`, `CHANGELOG.md`, `docs/agents/README.md`, `dist/` (modify) | registration |

---

### Task 1: Probe the public cases

**Files:**
- Create: `tools/case-audit-dev/probe.py`

**Interfaces:**
- Consumes: esapp; `$HAWAII40`, `$TEXAS2K`.
- Produces: the observation table above; nothing the engine imports.

This task has no unit test: its output is evidence. The probe solves one OPF as the case opened, then edits area and super-area OPF control, one shunt, one transformer, one bus and the loads **in memory** to answer five questions; it never saves, and exits non-zero if a case file's sha256 changes. It lives outside `skills/` so no agent is pointed at a tool that edits cases.

- [ ] **Step 1: Write the probe**

`tools/case-audit-dev/probe.py`:

```python
"""Live probe for the case-auditor: what the fields the rules depend on actually read.

    python tools/case-audit-dev/probe.py <case.pwb> [<case.pwb> ...]

Developer tool, kept outside skills/ so no agent runs it: it edits cases in memory. Opens each
case, prints one line per question, and closes it with esa.exit(). One OPF is solved as the case
opened. Five questions need an in-memory edit (area and super-area OPF control switched off; a
value written to one shunt, one transformer and one bus; load scaled until the AC solve fails).
Nothing is ever saved: the case file's sha256 is printed before and after, and the run fails
if they differ.
"""
import hashlib
import os
import sys
import time

import pandas as pd

num = lambda s: pd.to_numeric(s, errors="coerce")


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def get(E, obj, fields):
    d = E.GetParametersMultipleElement(obj, fields)
    if d is None:
        return None
    for c in d.columns:
        d[c] = d[c].astype(str).str.strip()
    return d


def counts(s, n=6):
    return dict(s.value_counts().head(n))


def row(item, value):
    print(f"| {item} | {value} |")


def opf(E):
    """Run an OPF and say whether it started: the refusal is a status string, not an exception."""
    try:
        E.InitializePrimalLP()
        E.SolvePrimalLP()
        raised = "no raise"
    except Exception as e:
        raised = f"RAISED {type(e).__name__}: {str(e)[:90]}"
    s = get(E, "OPFSolutionSummary", ["LPOPFSolutionStatus", "LPOPFCostFunction:1"])
    return f"{raised}; {None if s is None else s.iloc[0].to_dict()}"


def probe(path):
    from esapp import PowerWorld
    before = sha(path)
    print(f"\n## {os.path.basename(path)}\n\n| question | observed |\n|---|---|")
    t = time.perf_counter()
    pw = PowerWorld(path)
    try:
        E = pw.esa
        row("open, seconds", f"{time.perf_counter() - t:.1f}")
        opts = get(E, "Sim_Solution_Options", ["SBase", "ChkTaps", "ConvergenceTol:2"])
        row("Sim_Solution_Options SBase / ChkTaps / ConvergenceTol:2 (MVA)", opts.iloc[0].to_dict())
        info = get(E, "PWCaseInformation", ["BusNum", "BranchNum", "GenNum", "BranchNum:2", "BGNIslands"])
        row("PWCaseInformation counts (before solve)", None if info is None else info.iloc[0].to_dict())
        ctg = E.GetParametersMultipleElement("ViolationCTG", ["CTGLabel", "LimViolID:1"])
        row("ViolationCTG rows held in the case as opened", 0 if ctg is None else len(ctg))
        row("zero-row object: GetParametersMultipleElement('3WXFormer', key)",
            repr(E.GetParametersMultipleElement("3WXFormer", ["BusIdentifier"])))
        t = time.perf_counter()
        try:
            E.SolvePowerFlow()
            row("AC SolvePowerFlow as opened", f"no raise, {time.perf_counter() - t:.1f} s")
        except Exception as e:
            row("AC SolvePowerFlow as opened", f"RAISED {type(e).__name__}: {str(e)[:120]}")
        bus = get(E, "Bus", ["BusNum", "BusCat", "BusStatus", "BusIsStarBus", "BusNomVolt", "BusPUVolt",
                             "BusVoltLim", "BusVoltLimLow", "BusVoltLimHigh", "BusMismatchP", "BusMismatchQ"])
        row("max |BusMismatchP| / |BusMismatchQ| after solve",
            f"{num(bus.BusMismatchP).abs().max():.4g} / {num(bus.BusMismatchQ).abs().max():.4g}")
        row("Bus.BusStatus values", counts(bus.BusStatus))
        row("Bus.BusCat values", counts(bus.BusCat))
        row("Bus.BusIsStarBus values", counts(bus.BusIsStarBus))
        row("Bus.BusVoltLim values", counts(bus.BusVoltLim))
        row("Bus (BusVoltLimLow, BusVoltLimHigh) most common",
            dict(bus.groupby(["BusVoltLimLow", "BusVoltLimHigh"]).size().sort_values(ascending=False).head(4)))
        br = get(E, "Branch", ["BusNum", "BusNum:1", "LineCircuit", "LineStatus", "LineXfmr",
                               "BranchDeviceType", "LineXFType", "XFAuto", "XFRegBus", "XFRegBus:1",
                               "XFRegTargetType", "XFRegMin", "XFRegMax", "XFTapMin", "XFTapMax",
                               "XFRegBusOnWhichSide", "LineLength"])
        row("Branch.LineLength = 0 share", f"{(num(br.LineLength) == 0).mean():.3f}")
        row("Branch.BranchDeviceType values", counts(br.BranchDeviceType))
        row("Branch.LineCircuit values with a space or non-digit", sorted(set(c for c in br.LineCircuit if not c.isdigit()))[:8])
        star = set(bus.BusNum[bus.BusIsStarBus == "YES"])
        row("Branch rows touching a star bus", int((br.BusNum.isin(star) | br["BusNum:1"].isin(star)).sum()))
        xf = br[br.LineXfmr == "YES"]
        row("transformer LineXFType values", counts(xf.LineXFType))
        row("transformer XFAuto values", counts(xf.XFAuto))
        row("transformer XFRegTargetType values", counts(xf.XFRegTargetType))
        ltc = xf[(xf.LineXFType == "LTC") & (xf.XFAuto == "YES") & (xf.LineStatus == "Closed")]
        own = (ltc.XFRegBus == ltc.BusNum) | (ltc.XFRegBus == ltc["BusNum:1"])
        row("active LTCs: XFRegBus = own terminal / = 0 / elsewhere",
            f"{int(own.sum())} / {int((ltc.XFRegBus == '0').sum())} / {int((~own & (ltc.XFRegBus != '0')).sum())}")
        row("active LTCs: (XFRegMin, XFRegMax) most common",
            dict(ltc.groupby(["XFRegMin", "XFRegMax"]).size().sort_values(ascending=False).head(3)))
        row("active LTCs: XFRegBusOnWhichSide values", counts(ltc.XFRegBusOnWhichSide))
        w3 = E.GetParametersMultipleElement("3WXFormer", ["BusIdentifier", "BusIdentifier:1", "BusIdentifier:2", "LineCircuit"])
        row("3WXFormer rows", 0 if w3 is None else len(w3))
        sh = get(E, "Shunt", ["BusNum", "ShuntID", "SSStatus", "SSCMode", "AutoControl", "SSRegNum",
                              "SSRegNum:1", "SSMaxMVR", "SSMinMVR"])
        if sh is None:
            row("Shunt rows", "None")
        else:
            row("Shunt.SSCMode values", counts(sh.SSCMode))
            row("Shunt.AutoControl values", counts(sh.AutoControl))
            reg = sh[sh.SSCMode.isin(["Discrete", "Continuous", "SVC"])]
            row("regulating shunts: SSRegNum = own bus / = 0 / elsewhere",
                f"{int((reg.SSRegNum == reg.BusNum).sum())} / {int((reg.SSRegNum == '0').sum())} / "
                f"{int(((reg.SSRegNum != reg.BusNum) & (reg.SSRegNum != '0')).sum())}")
            row("regulating shunts with SSRegNum = 0: SSRegNum:1 values", counts(reg[reg.SSRegNum == "0"]["SSRegNum:1"]))
        gen = get(E, "Gen", ["BusNum", "GenID", "GenStatus", "GenMW", "GenMWMax", "GenFuelType",
                             "TSPFWModelString", "Latitude", "Longitude", "Latitude:1", "Longitude:1",
                             "CustomInteger:1", "GenUnitType", "GenAGCAble", "GenCostModel"])
        ren = gen[gen.GenFuelType.str.contains("WND|SUN")]
        row("renewables: Gen.Latitude (bus) blank / Gen.Latitude:1 (substation) blank",
            f"{int(num(ren.Latitude).isna().sum())} / {int(num(ren['Latitude:1']).isna().sum())} of {len(ren)}")
        row("Gen.CustomInteger:1 values", counts(gen["CustomInteger:1"]))
        over = num(gen.GenMW) - num(gen.GenMWMax)
        on = gen.GenStatus == "Closed"
        row("online units over GenMWMax by > 0.1 MW (MW over, largest 5)",
            sorted(over[on & (over > 0.1)].round(2).tolist(), reverse=True)[:5])
        row("Gen.GenFuelType values", counts(gen.GenFuelType, 10))
        row("Gen.TSPFWModelString length > 2", int((gen.TSPFWModelString.str.len() > 2).sum()))
        row("Gen.GenCostModel values", counts(gen.GenCostModel))
        area = get(E, "Area", ["AreaNum", "BGAGC", "BGReportLimits"])
        row("Area.BGAGC values", counts(area.BGAGC))
        sa = get(E, "SuperArea", ["SAName", "BGAGC"])
        row("SuperArea.BGAGC values", "None" if sa is None else counts(sa.BGAGC))
        ls = get(E, "LimitSet", ["LSName", "LSDisabled", "LSLineRateSet", "LSLineRateSet:1", "LSAmpMVA"])
        row("LimitSet rows (LSName, LSDisabled, LSLineRateSet, :1, LSAmpMVA)", ls.values.tolist())
        mon = get(E, "Limit_Monitoring_Options", ["LMS_IgnoreRadial"])
        row("Limit_Monitoring_Options.LMS_IgnoreRadial", None if mon is None else mon.iloc[0, 0])
        member = get(E, "Area", ["AreaNum", "SAName", "BGAGC"])
        row("Area (AreaNum, SAName, BGAGC)", member.values.tolist()[:4])
        row("OPF as opened: InitializePrimalLP + SolvePrimalLP", opf(E))

        # --- in-memory edits below; the case on disk is never written
        for _, r in member.iterrows():
            E.ChangeParametersSingleElement("Area", ["AreaNum", "BGAGC"], [r.AreaNum, "Off AGC"])
        if sa is not None:
            for _, r in sa.iterrows():
                E.ChangeParametersSingleElement("SuperArea", ["SAName", "BGAGC"], [r.SAName, "Off AGC"])
        row("OPF with every area and super area Off AGC (in memory)", opf(E))
        if sh is not None and len(reg):
            s = reg.head(1)
            k = [s.BusNum.iloc[0], s.ShuntID.iloc[0]]
            other = next(b for b in bus.BusNum if b != k[0])
            f = ["BusNum", "ShuntID", "SSRegNum", "SSRegNum:1"]
            for v in (other, "0"):
                E.ChangeParametersSingleElement("Shunt", f[:3], k + [v])
                got = E.GetParametersSingleElement("Shunt", f, k + ["", ""]).astype(str).str.strip()
                row(f"regulating shunt at bus {k[0]}: write SSRegNum = {v}, read back SSRegNum / SSRegNum:1",
                    f"{got['SSRegNum']} / {got['SSRegNum:1']}")
        b = ltc.head(1) if len(ltc) else xf[xf.LineStatus == "Closed"].head(1)
        if len(b):
            k = [b.BusNum.iloc[0], b["BusNum:1"].iloc[0], b.LineCircuit.iloc[0]]
            kf = ["BusNum", "BusNum:1", "LineCircuit"]
            if not len(ltc):   # no live LTC in this case: make one in memory
                E.ChangeParametersSingleElement("Branch", kf + ["LineXFType", "XFAuto"], k + ["LTC", "YES"])
            f = kf + ["XFRegBus", "XFRegBus:1", "LineXFType", "XFAuto"]
            for v in (k[1], "0"):
                E.ChangeParametersSingleElement("Branch", kf + ["XFRegBus"], k + [v])
                got = E.GetParametersSingleElement("Branch", f, k + ["", "", "", ""]).astype(str).str.strip()
                row(f"LTC {k[0]}-{k[1]} ({got['LineXFType']}, XFAuto {got['XFAuto']}): write XFRegBus = {v}, "
                    f"read back XFRegBus / XFRegBus:1", f"{got['XFRegBus']} / {got['XFRegBus:1']}")
        k = [bus.BusNum.iloc[0]]
        f = ["BusNum", "BusVoltLim", "BusVoltLimLow", "BusVoltLimHigh"]
        E.ChangeParametersSingleElement("Bus", f, k + ["YES", "0.95", "1.04"])
        got = E.GetParametersSingleElement("Bus", f, k + ["", "", ""]).astype(str).str.strip()
        row(f"bus {k[0]}: write BusVoltLim = YES, 0.95 / 1.04, read back BusVoltLimLow / High",
            f"{got['BusVoltLimLow']} / {got['BusVoltLimHigh']}")
        before_mw = num(get(E, "Load", ["BusNum", "LoadID", "LoadMW"]).LoadMW).sum()
        E.Scale("LOAD", "FACTOR", [4.0], "SYSTEM")
        mw = num(get(E, "Load", ["BusNum", "LoadID", "LoadMW"]).LoadMW).sum()
        row("esapp Scale(LOAD, FACTOR, [4], SYSTEM): system load MW before -> after", f"{before_mw:.1f} -> {mw:.1f}")
        load = get(E, "Load", ["BusNum", "LoadID", "LoadMW", "LoadMVR"])
        for factor in (4, 8, 12, 20, 40):
            scaled = load.copy()
            scaled["LoadMW"] = num(load.LoadMW) * factor
            scaled["LoadMVR"] = num(load.LoadMVR) * factor
            E.ChangeParametersMultipleElement("Load", list(scaled.columns), scaled.values.tolist())
            try:
                E.SolvePowerFlow()
                outcome = "no raise"
            except Exception as e:
                outcome = f"RAISED {type(e).__name__}: {str(e)[:90]}"
            b2 = get(E, "Bus", ["BusNum", "BusMismatchP", "BusPUVolt"])
            row(f"AC solve, load x{factor} (in memory)",
                f"{outcome}; max mismatch {num(b2.BusMismatchP).abs().max():.4g} MW; min V {num(b2.BusPUVolt).min():.3f}")
            if outcome != "no raise":
                break
    finally:
        pw.esa.exit()
    after = sha(path)
    row("case file sha256 unchanged", before == after)
    if before != after:
        sys.exit("the case file changed on disk")


if __name__ == "__main__":
    for p in sys.argv[1:]:
        probe(os.path.abspath(p))
```

- [ ] **Step 2: Count PowerWorld processes, run, count again**

Run: `tasklist | grep -ic pwrworld` (note the number), then
`python tools/case-audit-dev/probe.py "$HAWAII40" "$TEXAS2K" > /tmp/probe_out.md; cat /tmp/probe_out.md`, then `tasklist | grep -ic pwrworld`.
Expected: the same process count before and after, and this table (open times vary; the divergence load factor can differ, because it follows the OPF's dispatch):

```
## Hawaii40_base.pwb

| question | observed |
|---|---|
| open, seconds | 7.6 |
| Sim_Solution_Options SBase / ChkTaps / ConvergenceTol:2 (MVA) | {'SBase': '100', 'ChkTaps': 'YES', 'ConvergenceTol:2': '0.00001000'} |
| PWCaseInformation counts (before solve) | {'BusNum': '37', 'BranchNum': '77', 'GenNum': '45', 'BranchNum:2': '0', 'BGNIslands': '1'} |
| ViolationCTG rows held in the case as opened | 14 |
| zero-row object: GetParametersMultipleElement('3WXFormer', key) | None |
| AC SolvePowerFlow as opened | no raise, 0.0 s |
| max |BusMismatchP| / |BusMismatchQ| after solve | 2e-08 / 4e-08 |
| Bus.BusStatus values | {'Connected': np.int64(37)} |
| Bus.BusCat values | {'PQ': np.int64(27), 'PQ (Gens at Var Limit)': np.int64(5), 'PV': np.int64(4), 'Slack': np.int64(1)} |
| Bus.BusIsStarBus values | {'NO': np.int64(37)} |
| Bus.BusVoltLim values | {'NO': np.int64(37)} |
| Bus (BusVoltLimLow, BusVoltLimHigh) most common | {('0.89999998', '1.10000002'): np.int64(37)} |
| Branch.LineLength = 0 share | 1.000 |
| Branch.BranchDeviceType values | {'Line': np.int64(77), 'Transformer': np.int64(12)} |
| Branch.LineCircuit values with a space or non-digit | [] |
| Branch rows touching a star bus | 0 |
| transformer LineXFType values | {'Fixed': np.int64(12)} |
| transformer XFAuto values | {'NO': np.int64(12)} |
| transformer XFRegTargetType values | {'Middle': np.int64(12)} |
| active LTCs: XFRegBus = own terminal / = 0 / elsewhere | 0 / 0 / 0 |
| active LTCs: (XFRegMin, XFRegMax) most common | {} |
| active LTCs: XFRegBusOnWhichSide values | {} |
| 3WXFormer rows | 0 |
| Shunt.SSCMode values | {'Discrete': np.int64(1)} |
| Shunt.AutoControl values | {'YES': np.int64(1)} |
| regulating shunts: SSRegNum = own bus / = 0 / elsewhere | 1 / 0 / 0 |
| regulating shunts with SSRegNum = 0: SSRegNum:1 values | {} |
| renewables: Gen.Latitude (bus) blank / Gen.Latitude:1 (substation) blank | 9 / 0 of 9 |
| Gen.CustomInteger:1 values | {'None': np.int64(45)} |
| online units over GenMWMax by > 0.1 MW (MW over, largest 5) | [] |
| Gen.GenFuelType values | {'DFO (Distillate Fuel Oil)': np.int64(23), 'OBL (Other Biomass Liquids)': np.int64(12), 'SUN (Solar)': np.int64(6), 'WND (Wind)': np.int64(3), 'BIT (Bituminous Coal)': np.int64(1)} |
| Gen.TSPFWModelString length > 2 | 9 |
| Gen.GenCostModel values | {'Cubic': np.int64(45)} |
| Area.BGAGC values | {'OPF': np.int64(1)} |
| SuperArea.BGAGC values | {'Off AGC': np.int64(1)} |
| LimitSet rows (LSName, LSDisabled, LSLineRateSet, :1, LSAmpMVA) | [['Default', 'NO', 'A', 'A', 'MVA']] |
| Limit_Monitoring_Options.LMS_IgnoreRadial | NO |
| Area (AreaNum, SAName, BGAGC) | [['1', 'FullCase', 'OPF']] |
| OPF as opened: InitializePrimalLP + SolvePrimalLP | no raise; {'LPOPFSolutionStatus': 'Successful Solution', 'LPOPFCostFunction:1': '4205.64062500'} |
| OPF with every area and super area Off AGC (in memory) | no raise; {'LPOPFSolutionStatus': 'Error = No area/superarea constraints set', 'LPOPFCostFunction:1': '0.00000000'} |
| regulating shunt at bus 16: write SSRegNum = 1, read back SSRegNum / SSRegNum:1 | 1 / 1 |
| regulating shunt at bus 16: write SSRegNum = 0, read back SSRegNum / SSRegNum:1 | 1 / 1 |
| LTC 1-2 (LTC, XFAuto YES): write XFRegBus = 2, read back XFRegBus / XFRegBus:1 | 2 / 2 |
| LTC 1-2 (LTC, XFAuto YES): write XFRegBus = 0, read back XFRegBus / XFRegBus:1 | 2 / 2 |
| bus 1: write BusVoltLim = YES, 0.95 / 1.04, read back BusVoltLimLow / High | 0.94999999 / 1.03999996 |
| esapp Scale(LOAD, FACTOR, [4], SYSTEM): system load MW before -> after | 1136.3 -> 1136.3 |
| AC solve, load x4 (in memory) | no raise; max mismatch 7.2e-07 MW; min V 0.654 |
| AC solve, load x8 (in memory) | no raise; max mismatch 9.16e-06 MW; min V 0.184 |
| AC solve, load x12 (in memory) | RAISED PowerWorldError: RunScriptCommand: Error in script action execution: NR PowerFlow - Power flow unable to co; max mismatch 37.46 MW; min V 0.045 |
| case file sha256 unchanged | True |

## Texas2k_series25_case1_summerpeak_PFW.pwb

| question | observed |
|---|---|
| open, seconds | 8.2 |
| Sim_Solution_Options SBase / ChkTaps / ConvergenceTol:2 (MVA) | {'SBase': '100', 'ChkTaps': 'YES', 'ConvergenceTol:2': '0.10000000'} |
| PWCaseInformation counts (before solve) | {'BusNum': '2751', 'BranchNum': '3993', 'GenNum': '1099', 'BranchNum:2': '0', 'BGNIslands': '1'} |
| ViolationCTG rows held in the case as opened | 173 |
| zero-row object: GetParametersMultipleElement('3WXFormer', key) | None |
| AC SolvePowerFlow as opened | no raise, 0.2 s |
| max |BusMismatchP| / |BusMismatchQ| after solve | 0.0009653 / 0.01976 |
| Bus.BusStatus values | {'Connected': np.int64(2751)} |
| Bus.BusCat values | {'PQ': np.int64(1952), 'PV': np.int64(397), 'PQ (Gens at Var Limit)': np.int64(311), 'PQ (Continuous Shunts at Var Limit)': np.int64(90), 'Slack': np.int64(1)} |
| Bus.BusIsStarBus values | {'NO': np.int64(2751)} |
| Bus.BusVoltLim values | {'NO': np.int64(2751)} |
| Bus (BusVoltLimLow, BusVoltLimHigh) most common | {('0.89999998', '1.10000002'): np.int64(2751)} |
| Branch.LineLength = 0 share | 1.000 |
| Branch.BranchDeviceType values | {'Line': np.int64(3993), 'Transformer': np.int64(1351)} |
| Branch.LineCircuit values with a space or non-digit | [] |
| Branch rows touching a star bus | 0 |
| transformer LineXFType values | {'Fixed': np.int64(1351)} |
| transformer XFAuto values | {'NO': np.int64(1351)} |
| transformer XFRegTargetType values | {'Middle': np.int64(1351)} |
| active LTCs: XFRegBus = own terminal / = 0 / elsewhere | 0 / 0 / 0 |
| active LTCs: (XFRegMin, XFRegMax) most common | {} |
| active LTCs: XFRegBusOnWhichSide values | {} |
| 3WXFormer rows | 0 |
| Shunt.SSCMode values | {'Continuous': np.int64(202)} |
| Shunt.AutoControl values | {'YES': np.int64(202)} |
| regulating shunts: SSRegNum = own bus / = 0 / elsewhere | 202 / 0 / 0 |
| regulating shunts with SSRegNum = 0: SSRegNum:1 values | {} |
| renewables: Gen.Latitude (bus) blank / Gen.Latitude:1 (substation) blank | 400 / 0 of 400 |
| Gen.CustomInteger:1 values | {'None': np.int64(1099)} |
| online units over GenMWMax by > 0.1 MW (MW over, largest 5) | [] |
| Gen.GenFuelType values | {'NG (Natural Gas)': np.int64(507), 'WND (Wind)': np.int64(222), 'SUN (Solar)': np.int64(178), 'MWH (Electricity use for Energy Storage)': np.int64(121), 'WAT (Water)': np.int64(22), 'BIT (Bituminous Coal)': np.int64(21), 'DFO (Distillate Fuel Oil)': np.int64(10), 'OTH (Other)': np.int64(10), 'OBL (Other Biomass Liquids)': np.int64(4), 'NUC (Nuclear)': np.int64(4)} |
| Gen.TSPFWModelString length > 2 | 400 |
| Gen.GenCostModel values | {'Cubic': np.int64(1099)} |
| Area.BGAGC values | {'Off AGC': np.int64(8)} |
| SuperArea.BGAGC values | {'OPF': np.int64(1)} |
| LimitSet rows (LSName, LSDisabled, LSLineRateSet, :1, LSAmpMVA) | [['Default', 'NO', 'A', 'A', 'MVA']] |
| Limit_Monitoring_Options.LMS_IgnoreRadial | NO |
| Area (AreaNum, SAName, BGAGC) | [['1', 'Texas', 'Off AGC'], ['2', 'Texas', 'Off AGC'], ['3', 'Texas', 'Off AGC'], ['4', 'Texas', 'Off AGC']] |
| OPF as opened: InitializePrimalLP + SolvePrimalLP | no raise; {'LPOPFSolutionStatus': 'Successful Solution', 'LPOPFCostFunction:1': '260126.65551758'} |
| OPF with every area and super area Off AGC (in memory) | no raise; {'LPOPFSolutionStatus': 'Error = No area/superarea constraints set', 'LPOPFCostFunction:1': '0.00000000'} |
| regulating shunt at bus 1007: write SSRegNum = 1001, read back SSRegNum / SSRegNum:1 | 1001 / 1001 |
| regulating shunt at bus 1007: write SSRegNum = 0, read back SSRegNum / SSRegNum:1 | 1001 / 1001 |
| LTC 1001-12667 (LTC, XFAuto YES): write XFRegBus = 12667, read back XFRegBus / XFRegBus:1 | 12667 / 12667 |
| LTC 1001-12667 (LTC, XFAuto YES): write XFRegBus = 0, read back XFRegBus / XFRegBus:1 | 12667 / 12667 |
| bus 1001: write BusVoltLim = YES, 0.95 / 1.04, read back BusVoltLimLow / High | 0.94999999 / 1.03999996 |
| esapp Scale(LOAD, FACTOR, [4], SYSTEM): system load MW before -> after | 85759.0 -> 85759.0 |
| AC solve, load x4 (in memory) | RAISED PowerWorldError: RunScriptCommand: Error in script action execution: NR PowerFlow - Exceeded maximum number; max mismatch 1414 MW; min V 0.921 |
| case file sha256 unchanged | True |
```

- [ ] **Step 3: Commit**

```bash
git add tools/case-audit-dev/probe.py
git commit -m "Add the case-auditor live probe: what the rules' fields actually read, and one OPF"
```

---

### Task 2: The four rule pages

**Files:**
- Create: `methods/ltc-regulation-checks.md`
- Create: `concepts/unloaded-ehv-stub-overvoltage.md`
- Modify: `index.md` (two rows)

**Interfaces:**
- Consumes: the probe's observations.
- Produces: the pages `base.regulates_nothing`, `base.ltc_middle_target`, `base.ltc_regulates_lv_side` and `base.floating_stub` cite (Task 15 `test_every_page_a_finding_cites_exists` checks they exist).

Both pages were ported from the author's research notes and scrubbed (no case names, utilities, buses or fingerprinting counts; measurements cited by date and kind; real-model specifics — tie lengths, reactor sizes, step counts, a unit's MVA — rounded to their order of magnitude). The probe results are already folded in.

- [ ] **Step 1: Confirm neither page exists**

Run: `ls methods/ltc-regulation-checks.md concepts/unloaded-ehv-stub-overvoltage.md`
Expected: `No such file or directory` for both.

- [ ] **Step 2: Write `methods/ltc-regulation-checks.md`**

````markdown
---
type: method
domain: cross-cutting
aliases: [ltc-regulation-checks, ltc-regulated-bus, XFRegBus, XFRegTargetType, SSRegNum,
  regulates-nothing, ltc-middle-target, ltc-regulates-lv-side, repoint-the-regulator,
  ltc-causes-violation, which-bus-does-the-ltc-hold]
tags: [powerworld, esapp, transformer, ltc, tap, switched-shunt, voltage, case-quality,
  validation, remediation, n-0]
---

# Checking what each LTC and switched shunt actually regulates

## Abstract

A case can carry a full fleet of live load tap changers (LTCs) and still control voltage badly,
because what decides the outcome is not whether the LTCs are switched on but **which bus each
one holds and how it drives toward its band**. Three defects are common, and each one leaves
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
`XFTapMin`) with a non-zero `XFRegError` is not failing to help. It is actively pushing.

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
correct form is `new_tap = old_tap × (v_target / v_measured)`, and whether the tap sits at the
`XFNominalKV` end or the `:1` end is worth re-measuring on each new case family.

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
   pulling down the load bus behind it, from about 0.94 to about 0.89, in every dispatch, including one that had
   been clean. Both sides were already low, so there was nothing to borrow. That floor was a
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
````

- [ ] **Step 3: Write `concepts/unloaded-ehv-stub-overvoltage.md`**

```markdown
---
type: concept
domain: cross-cutting
aliases: [unloaded-ehv-stub-overvoltage, floating-stub, ehv-stub-overvoltage, ferranti-rise,
  dead-end-ehv-overvoltage, line-charging-overvoltage, radial-ehv-line, open-end-rise]
tags: [powerworld, voltage, overvoltage, reactive-power, line-charging, topology, radial,
  islanding, case-quality, n-0]
---

# An unloaded EHV stub runs high, and only closing it fixes both of its problems

## Abstract

An extra-high-voltage (EHV) line that runs out to a dead end and carries almost no MW behaves like
an open-ended capacitor. Its own charging lifts the far end above the near end (the Ferranti
rise). If nothing at the far end can absorb Mvar, for example because the only unit there is
modelled with zero reactive range, the far end runs high in exactly the light-load dispatches
where the unit is off. The same topology also islands on the loss of its one link. Measured
2026-09-28 on a regional planning model: a tie closing the stub into a substation that still had
absorbing room fixed both problems. A reactor fixed only the voltage. A long tie to a substation
whose reactor was already at full output fixed neither.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [ltc-regulation-checks](../methods/ltc-regulation-checks.md) (the other intact-case
  overvoltage, which an LTC can reach) ·
  [violation-network-map](../methods/violation-network-map.md) (the radial-ties page finds the
  bridges and radial trees this shape sits on, and the voltage page shows the reactive balance
  around it) · [case-impedance-completeness](case-impedance-completeness.md) (a case with
  `LineC = 0` has no charging, so this rise cannot appear there; check that first) ·
  [adding-devices-esapp](../methods/adding-devices-esapp.md) (placing the reactor or tie once
  chosen)
- **Checked by:** the case-auditor's `base.floating_stub` rule

## Content

### The shape

One or two EHV substations hang off the meshed grid on a single line a few tens of miles long.
The only device at the far end is a solar or storage plant modelled with zero reactive range
(`GenMVRMax = GenMVRMin = 0`). When that plant is off (winter peak, spring minimum, a light-load
night) the line carries almost no MW. Its charging, `LineC` in per unit on the system base,
split half to each end, has nowhere to go, so the far end rises above the near end.

Measured 2026-09-28 on a regional planning model, intact case, five dispatches:

| dispatch | far-end voltage |
|---|---|
| plant off, line nearly unloaded | **1.06 – 1.08 pu** |
| plant running, current through the line | 1.02 – 1.03 pu |

The loss of either link islands the plant. An outage that islands a bus often solves with no
violations reported, because the stranded buses are dropped rather than flagged. So the
islanding half of this problem needs its own screen.

### Why the obvious levers do not reach it

- **Generator setpoints.** Walking every unit within six hops down by up to 0.05 pu cleared small
  overshoots elsewhere but left the stub above 1.05. Every unit near it was already pinned at
  its absorbing limit (`GenMVR = GenMVRMin`). The one unit with room was injecting: it
  regulated a 138 kV bus that sat below its setpoint while the 345 kV side floated high. A
  setpoint on a pinned unit moves nothing.
- **Shunt deadbands.** Lowering the switched-shunt bands (`SSVHigh`, `SSVLow`) by 0.02 pu across
  the area changed nothing measurable. The nearby reactors were already at full absorption
  (`SSNMVR = SSMinMVR`), and the capacitors nearby were holding up load taps.
- **A long tie to the biggest reactive substation.** A tie several tens of miles long to a
  substation with a large reactor did not clear it. The new line's own charging cancelled the benefit, and that
  reactor was already at full output. **Capability is not room.** Rank landing points by what
  they can still absorb, not by what they own.
- **A 138 kV tie** from the stub made it worse, by up to 0.005 pu. It adds a path and nothing
  that absorbs, and it relieves none of the 345 kV charging.

### What fixed it

An **EHV tie a few tens of miles long from the dead end into a nearby substation whose unit still
had absorbing room** brought the stub to 1.03–1.05 pu in all five dispatches and removed both
islanding outages. It works because it turns the stub into a loop through a substation that can
take the stub's surplus Mvar. A tie landing on the middle of the stub fixed the voltage but left
the far end on one line.

For comparison:

| design | voltage | islanding |
|---|---|---|
| EHV tie from the far end to a substation with room | fixed | fixed |
| a reactor of order 100 Mvar at the stub | fixed except one dispatch, barely over | not fixed |
| a two-way bank of similar size at the stub | same as the reactor while out of band; idle once back in | not fixed |
| long tie to a substation whose reactor was pinned | not fixed | not fixed |
| 138 kV tie | worse | not measured |

Neither the reactor nor the bank is wrong. The tie is the only single device that answers both
problems.

### The same physics at regional scale

Many short EHV ties in one region raise it even when no single tie does. Measured on the same
model with discrete controls frozen: closing on the order of ten radial trees in one light-load region
pushed tens more buses over 1.05 in one dispatch. Removing any one of those ties moved
the worst bus by under 0.001 pu. The rise is the sum of their charging. Check a batch of ties
as a set, in the lightest dispatch, not one at a time. Where a region already runs near the
limit, site absorbing capacity along with the ties.

### What the auditor can and cannot tell from one case

The shape is structural: a radial EHV line whose far side has no absorbing room. The rise is
dispatch-dependent. A case solved with the far-end plant running can sit comfortably in band,
yet the same case at light load sits above it. So a clean voltage on this shape in the case
you have does not mean the shape is safe. Check the lightest dispatch you study. Whether to
close the stub, add a reactor or accept it is a planning choice the case cannot make for you.

### How the case-auditor finds it

The `case-audit` engine's `base.floating_stub` rule (`skills/case-audit/engine/rules_stub.py`)
works on the solved case, read-only:

1. **Structure.** Over the connected buses and closed branches (parallel circuits are separate
   edges, so a double circuit is never a bridge), find the bridges. The meshed core is the largest
   2-edge-connected piece; each bridge's far side is the part away from it. A candidate is a bridge
   that is a line, with both terminals at EHV, whose far side is small. Along one radial chain only
   the bridge nearest the core is reported.
2. **Lightly loaded.** The bridge's `LineMaxPercent` is low, or, on an unrated bridge
   (`LineAMVA = 0`), its `|LineMW|` is.
3. **Rising.** The highest far-side EHV bus sits above the bridge's core-side end, and there is
   line charging to rise on (`LineC` summed over the far side and the bridge is above 0; a case
   with `LineC = 0` everywhere is a DC skeleton, which `base.dc_skeleton` reports instead).

Each finding carries the bridge's keys, the near and far voltages, whether the far end is above
its own high limit, the bridge's MW and loading, the far-side bus count, the charging in Mvar
(`sum(LineC) × Sim_Solution_Options.SBase`; `SBase` read 100 on both public cases probed
2026-09-30, and the engine reads it from each case rather than assuming it), the **absorbing
room** left on the far side (`GenMVR − GenMVRMin` over closed units plus `SSNMVR − SSMinMVR` over
closed shunts - room, not capability), and the far-side units with zero reactive range.

Numbers with no source, each a proposed default in `skills/case-audit/engine/thresholds.py`:
EHV means 300 kV and above (catches 345, 500 and 765, excludes 230); a far side of at most 50
buses; lightly loaded means under 10 % of rating, or under 10 MW when unrated; a rise of at least
0.005 pu. The rise is dispatch-dependent, so a stub that is in band on this dispatch is not
reported; a structure-only warning for it is not built. On Texas2k (182 buses at 500 kV) the rule
found none.
```

- [ ] **Step 4: Index rows**

In `index.md`, insert after the `| [how-to-analyze-results](methods/how-to-analyze-results.md) …` row:

```
| [ltc-regulation-checks](methods/ltc-regulation-checks.md) | Check which bus each LTC and switched shunt actually holds and how it targets its band: a regulator pointed at nothing, `XFRegTargetType = Middle`, and an LTC holding its LV side while the HV side floats. Re-point, don't write taps. |
```

and after the `| [timestep-workflow](concepts/timestep-workflow.md) …` row:

```
| [unloaded-ehv-stub-overvoltage](concepts/unloaded-ehv-stub-overvoltage.md) | A lightly loaded EHV dead end rises at its open end on its own line charging and islands on one outage. A tie into a substation with absorbing room fixes both; a reactor fixes only the voltage. |
```

- [ ] **Step 5: Verify**

Run: `python -c "import pathlib,re;R=pathlib.Path('.');print([f'{p}: {t}' for d in ('concepts','methods','demos','references') for p in (R/d).glob('*.md') for t in set(re.findall(r'\]\(([^)#]+\.md)',p.read_text(encoding='utf-8-sig'))) if not (p.parent/t).exists()] or 'no dangling links')"`
Expected: `no dangling links`

- [ ] **Step 6: Commit**

```bash
git add methods/ltc-regulation-checks.md concepts/unloaded-ehv-stub-overvoltage.md index.md
git commit -m "Add the LTC and EHV-stub rule pages the case-auditor cites"
```

---

### Task 3: The 0b page fixes

**Files:**
- Create: `concepts/auto-pfw-scripts.md`
- Modify: `methods/timestep-simulation-setup.md` (lines 12, 20, 32–37, 46–50)
- Modify: `methods/converting-lines-to-transformers.md` (~line 106)
- Modify: `concepts/opf-preconditions.md` (after line 102, before `### Always give the solve a failure handler`)
- Modify: `index.md` (one row)

**Interfaces:**
- Consumes: the probe's OPF rows (Task 1).
- Produces: the Auto_PFW handoff page `ts.pfw_missing` cites; a timestep page that no longer lists an ISO label as a PowerWorld prerequisite; the measured super-area and zero-cost rules `opf.1`–`opf.3` follow.

- [ ] **Step 1: Confirm the stale text is present**

Run: `grep -n "pfw copperplate\|an ISO assigned in" methods/timestep-simulation-setup.md; grep -n "not an autotransformer" methods/converting-lines-to-transformers.md`
Expected: hits on lines 20, 34 and 49 of the first file and line 106 of the second.

- [ ] **Step 2: Write `concepts/auto-pfw-scripts.md`**

Ported from the author's research notes, scrubbed: links to pages the kit does not carry removed, the ISO field described as one pipeline's convention, and the probe's `CustomInteger:1` observation added.

```markdown
---
type: tool
domain: weather
aliases: [auto-pfw-scripts, auto-pfw, pfw-insertion-script, pfw_eia,
  PFW_EIA.py, attach-pfw-models, missing-pfw-models]
tags: [pfw, weather, renewables, wind, solar, timestep, aux, powerworld, tool]
---

# Tool: `Auto_PFW` — attaching PFW weather models to renewables

## Abstract

A research group's `Auto_PFW` scripts
attach PFW (power-flow weather) models to a case's wind and solar units, so TimeStep can
turn weather into MW. It is where the kit's case-auditor sends you when renewables lack a PFW
model. Read this before running it: it **silently skips wind units it cannot classify**, so
always re-count PFW coverage on the copy it saves.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [timestep-simulation-setup](../methods/timestep-simulation-setup.md) (the per-unit
  prerequisites a PFW model is one of) · [timestep-and-pfw](../demos/timestep-and-pfw.md) (the
  coverage count that decides whether a case can run a time step) ·
  [timestep-workflow](timestep-workflow.md) (the TimeStep chain that consumes PFW models)
- **Checked by:** the case-auditor's `ts.pfw_missing` rule, which names this tool as the handoff
  and counts how many of the missing wind units carry a class it can use

## Content

### What it does

Two scripts, both driving PowerWorld through SimAuto with the older `esa` package (not `esapp`):

| script | how it chooses the model | prompts |
|---|---|---|
| `PFW_EIA.py` | Wind: `GenMWMax_WindClass1` … `4` from `CustomInteger:1` (1–4) **or** `GenUnitType` (W1–W4). Solar: every unit gets `GenMWMax_SolarPVBasic2`. | none |
| `Automation_integrating_PFW_into_PowerWorld.py` | One user-chosen class applied to every wind unit (WindBasic, WindGeneral, WindClass1–4) and/or every solar unit (SolarPVBasic1/2). | wind / solar / both, then the class |

The sequence is the same in both:

1. Open the case, export the generator table (`PW.csv`) with `GenFuelType`, `GenMWMax`,
   `CustomInteger:1`, `GenUnitType`.
2. Select units by fuel type: `WND (Wind)` and `SUN (Solar)`.
3. Write one AUX record per unit attaching the chosen `GenMWMax_*` model object.
4. `LoadAux` the file and save a **copy** as `<case>_PFW.pwb`; the original is not modified.

A PFW model is a per-generator object record ("this unit converts weather to MW with the
WindClass2 curve"). TimeStep reads it together with a `.pww` weather file; without it a unit
produces nothing, and TimeStep still reports success.

### Failure modes

- **Silent skip.** In `PFW_EIA.py`, a wind unit with neither `CustomInteger:1` in 1–4 nor
  `GenUnitType` W1–W4 gets **no record and no warning**. Cases built from EIA-860 carry the class;
  many synthetic cases do not, and then most wind units are skipped. On both public synthetic
  cases probed 2026-09-30, `CustomInteger:1` read blank on every unit.
- **Record shape.** `WindClass1` records carry 10 values for 9 listed fields (an extra value
  before the hub height); classes 2–4 carry 9. Check the PowerWorld message log after the AUX loads.
- **Interactive script input.** The solar answer is lower-cased and then compared with a
  mixed-case name, so only the answer `1` selects SolarPVBasic1; answering `quit` at a class prompt
  raises an `AttributeError`; the WindGeneral field list spells `DefaultWindMSS`.

### Verifying the result

Count, on the saved `_PFW` copy, the renewable units whose PFW model string is empty
(`TSPFWModelString` two characters or fewer). The count should be zero; anything else is the
silent skip above. Also confirm valid coordinates on those units, since this tool sets only the
PFW model. Running the case-auditor with the `timestep` profile on the copy does both counts.

### When to use which

- The case carries a wind class per unit (EIA-derived): `PFW_EIA.py` is sufficient.
- It does not: give the units a class first (from EIA-860 plant data, or your own judgment), or
  accept that unclassified wind units get no model. The interactive script applies one class to
  every unit, which runs but flattens the fleet into one turbine type.

Established 2026-09-28 from the repository's scripts and README; not re-run on a case for this
page.
```

- [ ] **Step 3: `methods/timestep-simulation-setup.md`**

In the Abstract (line 12) replace

```markdown
Covers the prerequisites a case must satisfy per renewable generator (`GenFuelType` WND/SUN, valid Lat/Lon, ISO in `CustomString:2`, a `TSPFWModelString` PFW model), the one-time ISO insertion step, and the `_simulation_worker` function sequence.
```

with

```markdown
Covers the prerequisites a case must satisfy per renewable generator (`GenFuelType` containing WND or SUN, valid Lat/Lon, a `TSPFWModelString` PFW model), one pipeline's optional ISO-labelling step, and the `_simulation_worker` function sequence.
```

In `## Connections` (line 20) replace

```markdown
[timestep-simulation](../concepts/timestep-simulation.md) · pfw copperplate · [esapp]
```

with

```markdown
[timestep-simulation](../concepts/timestep-simulation.md) · [auto-pfw-scripts](../concepts/auto-pfw-scripts.md) (attaching the PFW models) · [esapp]
```

Replace the prerequisites paragraph and the section heading after it

```markdown
The case must already have, on each renewable generator: a `GenFuelType` of `WND`
or `SUN`, valid `Latitude`/`Longitude`, an ISO assigned in `CustomString:2`, and a
PFW model string (`TSPFWModelString`). The ISO is filled in by the one-time
case-prep step below.

## 1. (One time) Insert ISO regions into the case
```

with

```markdown
PowerWorld needs, on each renewable generator: a `GenFuelType` that contains `WND`
or `SUN` (the case labels them `WND (Wind)`, `SUN (Solar)`), valid coordinates, and a
PFW model string (`TSPFWModelString` longer than 2 characters). A unit with no PFW model
runs and reads 0 MW for the whole run; attach models with
[auto-pfw-scripts](../concepts/auto-pfw-scripts.md). Coordinates: on both public
synthetic cases probed 2026-09-30 the unit's own `Gen.Latitude` read blank and the substation's
`Gen.Latitude:1` / `Longitude:1` (the field export's "Substation Latitude") were set. That
TimeStep then reads the substation pair is not verified in the kit.

## 1. (Optional, one pipeline's convention) Label units with an ISO region

This is **not** a PowerWorld prerequisite. One time-step pipeline writes an ISO region into
`CustomString:2`, a custom field, so its output CSVs can carry an ISO header row; TimeStep does
not read it. Skip this section unless your post-processing needs the label.
```

Replace the note

```markdown
> **Resolved:** `PFW_Insertion` (`ISO_Insertion_code_shape_file.ipynb`) writes
> **only `CustomString:2`** (the ISO region via geopandas spatial join). It does
> **not** touch `TSPFWModelString`. PFW model strings are assumed already present in
> the case — they are assigned by pfw copperplate as a separate one-time step
> before this pipeline is run.
```

with

```markdown
> **Resolved:** `PFW_Insertion` (`ISO_Insertion_code_shape_file.ipynb`) writes
> **only `CustomString:2`** (the ISO region via geopandas spatial join). It does
> **not** touch `TSPFWModelString`. PFW model strings must already be in the case;
> [auto-pfw-scripts](../concepts/auto-pfw-scripts.md) attaches them, and the
> case-auditor's `timestep` profile counts which units still lack one.
```

- [ ] **Step 4: `methods/converting-lines-to-transformers.md`**

In the House defaults table replace

```markdown
| `XFAuto` | `NO` | not an autotransformer |
```

with

```markdown
| `XFAuto` | `NO` | automatic control off (the field takes `YES`, `NO` or `OPF`; it is not an autotransformer flag) |
```

- [ ] **Step 5: `concepts/opf-preconditions.md` — what the probe measured**

In `### Condition 3 is data, …` replace

```markdown
Per [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md), the guard is
`GenCostCurvePoints > 0 AND GenMCost > 0`. `GenCostCurvePoints == 0` means no curve was
ever fit and the cost fields read `0` — which is *no data*, never *free*. A handful of
units can also report `GenMCost == 0` with curve points defined.
```

with

```markdown
Per [powerworld-inertia-and-cost-data](powerworld-inertia-and-cost-data.md), the guard is
`GenCostCurvePoints > 0 AND GenMCost > 0`. `GenCostCurvePoints == 0` means no curve was
ever fit and the cost fields read `0` — which is *no data*, never *free*. A handful of
units can also report `GenMCost == 0` with curve points defined.

**Refined 2026-09-30, measured on a public synthetic 40-bus case.** Those units are the wind and
solar: five curve points each, and a curve that is 0 at their output. The OPF solved with them in
the movable set. `GenMCost` is the curve *at today's output*, so a zero there is a price of zero,
not missing data. The case-auditor therefore counts a unit as priced when `GenCostModel` is not
None and `GenCostCurvePoints > 0`, says nothing about a zero-cost renewable, and flags a
*thermal* unit whose curve reads 0 as worth a look.
```

and insert, immediately before `### Always give the solve a failure handler`:

```markdown
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

```

- [ ] **Step 6: Index row**

In `index.md`, insert after the `| [glossary](concepts/glossary.md) …` row:

```
| [auto-pfw-scripts](concepts/auto-pfw-scripts.md) | The `Auto_PFW` scripts attach PFW weather models to wind and solar units so TimeStep produces MW. They skip a wind unit with no class without a warning, so re-count coverage on the copy they save. |
```

- [ ] **Step 7: Verify**

Run: `grep -c "pfw copperplate\|an ISO assigned in" methods/timestep-simulation-setup.md; grep -c "not an autotransformer |" methods/converting-lines-to-transformers.md; grep -c "Super areas count" concepts/opf-preconditions.md`
Expected: `0`, `0` and `1`.

Run the dangling-link check from Task 2 Step 5.
Expected: `no dangling links`

- [ ] **Step 8: Commit**

```bash
git add concepts/auto-pfw-scripts.md methods/timestep-simulation-setup.md methods/converting-lines-to-transformers.md concepts/opf-preconditions.md index.md
git commit -m "Port the Auto_PFW handoff page; record the measured OPF super-area rule; ISO label is one pipeline's convention; fix the XFAuto gloss"
```

---

### Task 4: CaseData, findings and thresholds

**Files:**
- Create: `skills/case-audit/engine/thresholds.py`, `casedata.py`, `findings.py`
- Create: `skills/case-audit/tests/conftest.py`, `auditcase.py`
- Test: `skills/case-audit/tests/test_audit_casedata.py`

**Interfaces:**
- Consumes: nothing (no esapp).
- Produces: `READS: dict[str, list[str]]`, `SCALARS`, `NUMERIC`, `RATINGS`; `typed(df | None, columns) -> DataFrame`; `Solve(ran, raised, max_mismatch_mva, tolerance_mva)` with `.converged` (the raise decides; the mismatch is checked only when it and the tolerance were both read) and `.tolerance_unread`; `CaseData(frames, scalars, solve)` with `.get(obj)`, `.to_json(path)`, `CaseData.from_json(path)`; `Finding(rule, severity, triage, what, why, page="", stops=(), scope="", where=[], details={}, handoff="")` with `.label`, `.to_dict()`; constants `STOPS, WORTH, FYI, BROKEN, ON_PURPOSE, YOUR_CALL, PROFILES` (`base, n1, timestep, opf, scopf`), `AC_STUDIES`, `NEEDS_HANDOFF`; `clean(o)`; `bus(n) -> int`; `branch_keys(row) -> dict`. Tests: `auditcase.toy() -> dict[str, DataFrame]`, `auditcase.case(frames=None, converged=True, **scalars) -> CaseData`; fixtures `frames`, `hawaii`, `fake_esapp` (used from Task 5).

`Finding` asserts that severity and triage come from the closed sets, that a *Stops the study* finding names the studies it stops, and that a finding about data the kit does not carry (`ts.pfw_missing`, `opf.3`) says where it comes from (`handoff`) unless it is triaged Probably on purpose — so a rule cannot invent a label or drop a handoff.

- [ ] **Step 1: Write the test scaffolding and the failing tests**

`skills/case-audit/tests/conftest.py`:

```python
"""Engine on sys.path, and the fixtures shared by every case-audit test file."""
import importlib
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
FIXTURES = Path(__file__).resolve().parent / "fixtures"
FAKE_ESAPP = Path(__file__).resolve().parent / "fake_esapp"
sys.path.insert(0, str(ENGINE))

from auditcase import toy  # noqa: E402


@pytest.fixture
def frames():
    return toy()


@pytest.fixture(scope="session")
def hawaii():
    """What the reader read from the public Hawaii40 case (37 buses) on 2026-09-30, file name only."""
    return FIXTURES / "hawaii40.json.gz"


@pytest.fixture
def fake_esapp(monkeypatch, hawaii):
    """The stand-in esapp, serving Hawaii40, imported fresh; returns the module (see its CALLS)."""
    monkeypatch.setenv("PWHM_FAKE_SNAPSHOT", str(hawaii))
    for var in ("PWHM_FAKE_SOLVE_ERROR", "PWHM_FAKE_OPEN_ERROR", "PWHM_FAKE_READ_ERROR", "PWHM_FAKE_EMPTY"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.syspath_prepend(str(FAKE_ESAPP))
    monkeypatch.delitem(sys.modules, "esapp", raising=False)
    module = importlib.import_module("esapp")
    monkeypatch.setattr("reader._tasklist", lambda: set())
    return module
```

`skills/case-audit/tests/auditcase.py`:

```python
"""A tiny hand-built case every rule test starts from.

toy(): a healthy 6-bus case. Buses 1-2-3 are a 345 kV triangle (the meshed core), bus 4 is
138 kV behind a 345/138 LTC 3-4, and buses 5-6 are a 345 kV radial chain 3-5-6 that the stub
tests load or unload. A test changes one thing and asserts one rule's answer.
"""
import pandas as pd

from casedata import CaseData, Solve


def _line(f, t, ckt="1", r=0.001, x=0.01, c=0.02, mw=50.0, pct=30.0, rating=200.0):
    return {"BusNum": f, "BusNum:1": t, "LineCircuit": ckt, "LineStatus": "Closed", "LineXfmr": "NO",
            "LineR": r, "LineX": x, "LineC": c, "LineMW": mw, "LineMVA": abs(mw), "LineMaxPercent": pct,
            "LineMonEle:1": "YES", "BusNomVolt": 345.0, "BusNomVolt:1": 345.0, "LineXFType": "",
            "XFAuto": "", "XFRegBus": 0.0, "LineAMVA": rating, "LineAMVA:1": rating, "LineAMVA:2": rating}


def toy() -> dict:
    bus = pd.DataFrame([
        {"BusNum": n, "BusName": f"BUS{n}", "BusStatus": "Connected", "BusCat": "Slack" if n == 1 else "PQ",
         "BusIsStarBus": "NO", "BusNomVolt": 138.0 if n == 4 else 345.0, "BusPUVolt": 1.0, "BusVoltLim": "NO",
         "BusVoltLimLow": 0.9, "BusVoltLimHigh": 1.1, "BusMonEle:1": "YES", "AreaNum": 1, "ZoneNum": 1,
         "BusMismatchP": 0.0, "BusMismatchQ": 0.0} for n in range(1, 7)])
    xf = {**_line(3, 4), "LineXfmr": "YES", "BusNomVolt:1": 138.0, "LineXFType": "LTC", "XFAuto": "YES",
          "XFRegBus": 4.0, "XFRegMin": 0.98, "XFRegMax": 1.02, "XFRegTargetType": "Max/Min",
          "XFTapMin": 0.9, "XFTapMax": 1.1, "XFStep": 0.00625, "LineTap": 1.0, "XFRegError": 0.0}
    branch = pd.DataFrame([_line(1, 2), _line(2, 3), _line(1, 3), xf,
                           _line(3, 5, mw=80.0, pct=40.0), _line(5, 6, mw=40.0, pct=20.0)])
    gen = pd.DataFrame([
        {"BusNum": 1, "GenID": "1", "GenStatus": "Closed", "GenMW": 300.0, "GenMVR": 20.0, "GenMWMax": 400.0,
         "GenMVRMax": 200.0, "GenMVRMin": -100.0, "GenFuelType": "NG (Natural Gas)", "TSPFWModelString": "",
         "GenAGCAble": "YES", "GenCostModel": "Cubic", "GenCostCurvePoints": 5, "GenMCost": 20.0, "AreaNum": 1},
        {"BusNum": 2, "GenID": "W1", "GenStatus": "Closed", "GenMW": 90.0, "GenMVR": 0.0, "GenMWMax": 100.0,
         "GenMVRMax": 30.0, "GenMVRMin": -30.0, "GenFuelType": "WND (Wind)", "TSPFWModelString": "WindClass2",
         "Latitude:1": 30.0, "Longitude:1": -97.0, "GenAGCAble": "YES", "GenCostModel": "Cubic",
         "GenCostCurvePoints": 5, "GenMCost": 1.0, "AreaNum": 1},
        {"BusNum": 6, "GenID": "S1", "GenStatus": "Closed", "GenMW": 40.0, "GenMVR": 0.0, "GenMWMax": 50.0,
         "GenMVRMax": 0.0, "GenMVRMin": 0.0, "GenFuelType": "SUN (Solar)", "TSPFWModelString": "SolarPVBasic2",
         "Latitude:1": 30.5, "Longitude:1": -97.5, "GenAGCAble": "YES", "GenCostModel": "Cubic",
         "GenCostCurvePoints": 5, "GenMCost": 1.0, "AreaNum": 1}])
    load = pd.DataFrame([{"BusNum": 4, "LoadID": "1", "LoadStatus": "Closed", "LoadMW": 420.0, "LoadMVR": 50.0}])
    shunt = pd.DataFrame([{"BusNum": 4, "ShuntID": "1", "SSStatus": "Closed", "SSCMode": "Discrete",
                           "AutoControl": "YES", "SSRegNum": 4.0, "SSAMVR": 30.0, "SSNMVR": 30.0,
                           "SSMaxMVR": 60.0, "SSMinMVR": 0.0}])
    area = pd.DataFrame([{"AreaNum": 1, "SAName": "", "BGAGC": "OPF", "BGReportLimits": "YES", "BGReportLimMinKV": 0.0,
                          "BGReportLimMaxKV": 9999.0}])
    zone = pd.DataFrame([{"ZoneNum": 1, "BGReportLimits": "YES", "BGReportLimMinKV": 0.0, "BGReportLimMaxKV": 9999.0}])
    limitset = pd.DataFrame([{"LSName": "Default", "LSDisabled": "NO", "LSLineRateSet": "A",
                              "LSLineRateSet:1": "B", "LSAmpMVA": "MVA"}])
    contingency = pd.DataFrame({"CTGLabel": ["L_1_2", "L_2_3"]})
    return {"Bus": bus, "Branch": branch, "Gen": gen, "Load": load, "Shunt": shunt, "Area": area,
            "Zone": zone, "LimitSet": limitset, "Contingency": contingency}


def case(frames=None, converged=True, **scalars) -> CaseData:
    solve = Solve(ran=True, max_mismatch_mva=0.0 if converged else 50.0, tolerance_mva=0.1)
    return CaseData(frames if frames is not None else toy(),
                    {"SBase": "100", "ChkTaps": "YES", **scalars}, solve)
```

`skills/case-audit/tests/test_audit_casedata.py`:

```python
import math

import pandas as pd
import pytest

from auditcase import case
from casedata import READS, CaseData, Solve
from findings import BROKEN, STOPS, WORTH, Finding, branch_keys, clean


def test_none_frame_becomes_empty_frame_with_columns():
    cd = CaseData({"Shunt": None}, {}, Solve())
    sh = cd.get("Shunt")
    assert sh.empty and list(sh.columns) == READS["Shunt"]
    assert sh[sh.SSStatus == "Closed"].SSMaxMVR.sum() == 0


def test_numbers_parsed_and_text_stripped():
    cd = CaseData({"Gen": pd.DataFrame({"BusNum": ["    23"], "GenID": [" 1 "], "GenMW": [" 69.27"],
                                        "Latitude": ["None"]})}, {}, Solve())
    g = cd.get("Gen")
    assert g.BusNum.iloc[0] == 23 and g.GenID.iloc[0] == "1" and g.GenMW.iloc[0] == pytest.approx(69.27)
    assert math.isnan(g.Latitude.iloc[0])
    assert g.GenFuelType.iloc[0] == ""                     # missing column added, empty


def test_line_circuit_stays_text():
    cd = CaseData({"Branch": pd.DataFrame({"BusNum": [1, 2], "BusNum:1": [2, 3], "LineCircuit": [" 01 ", "W2"]})},
                  {}, Solve())
    keys = [branch_keys(r) for _, r in cd.get("Branch").iterrows()]
    assert [k["LineCircuit"] for k in keys] == ["01", "W2"]


def test_converged_needs_no_raise_and_mismatch_under_tolerance():
    assert Solve(True, None, 0.02, 0.1).converged
    assert not Solve(True, "NR PowerFlow - Exceeded maximum number", 2e-5, 1e-5).converged
    assert not Solve(True, None, 0.5, 0.1).converged
    assert not Solve(False).converged


def test_an_unreadable_tolerance_does_not_fail_the_case():
    s = Solve(True, None, 0.02, None)
    assert s.converged and s.tolerance_unread
    assert not Solve(True, "NR PowerFlow - Power flow unable to converge", None, None).converged


def test_snapshot_round_trip(tmp_path):
    cd = case()
    p = tmp_path / "snap.json.gz"
    cd.to_json(p)
    back = CaseData.from_json(p)
    pd.testing.assert_frame_equal(back.get("Branch"), cd.get("Branch"))
    assert back.solve.converged and back.scalars["SBase"] == "100"


def test_finding_labels_are_closed_sets():
    with pytest.raises(AssertionError):
        Finding("x", "Blocker", BROKEN, "w", "y")
    with pytest.raises(AssertionError):
        Finding("x", STOPS, BROKEN, "w", "y")               # stops the study but names no study
    f = Finding("x", STOPS, BROKEN, "w", "y", stops=("n1",), scope="N-1 and SCOPF only")
    assert f.label == "Stops the study — N-1 and SCOPF only"
    assert Finding("x", WORTH, BROKEN, "w", "y").to_dict()["count"] == 0


def test_data_the_kit_lacks_must_name_its_source():
    with pytest.raises(AssertionError):
        Finding("ts.pfw_missing", WORTH, BROKEN, "w", "y")
    assert Finding("ts.pfw_missing", WORTH, BROKEN, "w", "y", handoff="Auto_PFW").to_dict()["handoff"] == "Auto_PFW"


def test_clean_removes_nan_and_numpy():
    import numpy as np
    assert clean({"a": float("nan"), "b": np.int64(3), "c": [np.float64(1.5)]}) == {"a": None, "b": 3, "c": [1.5]}
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'casedata'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/thresholds.py`:

```python
"""Every number the case-auditor rules compare against, in one place.

A value is either sourced (its comment names the kit page) or a proposed default with no
source, marked "proposed default" with the reason. The rule pages list the proposed ones;
change a number here and nowhere else.
"""

# base.dc_skeleton  (concepts/case-impedance-completeness.md)
DC_SKELETON_MEDIAN_XR = 1000.0   # sourced: median X/R above 1000 means R is a placeholder
TINY_R = 1e-6                    # sourced: the page's "R <= 1e-6" placeholder signature
DC_SKELETON_SHARE = 0.9          # proposed default: the page measured 97-100 % of closed lines with
                                 # R <= 1e-6 and B = 0 on three skeleton lineages; 0.9 leaves margin.
                                 # LineLength is not used: it reads 0 on every branch of both public
                                 # cases probed 2026-09-30, so "zero-length" cannot be counted.
DC_SKELETON_PARTIAL_SHARE = 0.05 # proposed default: a partial skeleton (at least 1 in 20 closed lines
                                 # with no R and no B) is Worth a look; both public cases read 0.001 or less

# base.gen_over_nameplate  (spec section 4 and the case-auditor brief set these; neither is a source)
GEN_OVER_MIN_MW = 0.1            # proposed default: below this an overshoot is solver noise
GEN_OVER_STOP_MW = 5.0           # proposed default: not measured - neither public case has a unit
GEN_OVER_STOP_SHARE = 0.01       # over its max. Stops past max(1 % of GenMWMax, 5 MW)

# LTC rules  (methods/ltc-regulation-checks.md)
LTC_BAND_CAN_ACT_PU = 0.2        # proposed default: bands measured to act are 0.02-0.065 pu wide; a
                                 # band copied from the tap range (about 1 pu) never acts
KV_SAME_REL = 0.01               # proposed default: terminals within 1 % nominal kV have no LV side
BAND_TOL_PU = 1e-4               # proposed default: BusVoltLimLow/High read back single-precision
                                 # (0.89999998 for 0.9, probed 2026-09-30)
FALLBACK_BAND = (0.94, 1.05)     # the study criterion of the kit's measured runs, not a PowerWorld
                                 # default; used only where a bus's limits read 0 or blank

# base.floating_stub  (concepts/unloaded-ehv-stub-overvoltage.md)
EHV_KV = 300.0                   # proposed default: catches 345, 500 and 765 kV, excludes 230
STUB_MAX_BUSES = 50              # proposed default: stops a whole radial region reading as a stub
STUB_LIGHT_PERCENT = 10.0        # proposed default: "carries almost no MW", rated bridge
STUB_LIGHT_MW = 10.0             # proposed default: the same, for a bridge with LineAMVA = 0
STUB_RISE_PU = 0.005             # proposed default: the page's far end sat at 1.06-1.08 pu with the plant off

# timestep  (the case-auditor brief, demos/timestep-and-pfw.md)
RENEWABLE_CODES = ("WND", "SUN") # sourced: GenFuelType contains one of these
PFW_MIN_CHARS = 2                # sourced: a PFW model string longer than 2 characters
WIND_CLASSES = (1, 2, 3, 4)      # sourced: Auto_PFW reads CustomInteger:1 1-4 or GenUnitType W1-W4
PWW_MAX_STATION_MILES = 25.0     # proposed default: a 0.25-degree grid puts every point inside its
                                 # footprint within about 12 miles of a station
```

`skills/case-audit/engine/casedata.py`:

```python
"""The case as the rules see it: named DataFrames plus scalars. Never imports esapp.

The reader fills a CaseData from PowerWorld; tests build one by hand. Either way every frame
passes through `typed()`, so a rule sees numbers as floats and text stripped of padding, and
an object with no rows is an empty frame with its columns - never None.
"""
from __future__ import annotations

import gzip
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

RATINGS = ["LineAMVA"] + [f"LineAMVA:{i}" for i in range(1, 15)]   # rate sets A..O

# object -> the fields the rules read, keys first. The reader reads exactly these.
READS: dict[str, list[str]] = {
    "Bus": ["BusNum", "BusName", "BusStatus", "BusCat", "BusIsStarBus", "BusNomVolt", "BusPUVolt",
            "BusVoltLim", "BusVoltLimLow", "BusVoltLimHigh", "BusMonEle:1", "AreaNum", "ZoneNum",
            "BusMismatchP", "BusMismatchQ"],
    "Branch": ["BusNum", "BusNum:1", "LineCircuit", "LineStatus", "LineXfmr", "LineR", "LineX", "LineC",
               "LineMW", "LineMVA", "LineMaxPercent", "LineMonEle:1", "BusNomVolt", "BusNomVolt:1",
               "LineXFType", "XFAuto", "XFRegBus", "XFRegMin", "XFRegMax", "XFRegTargetType",
               "XFTapMin", "XFTapMax", "XFStep", "LineTap", "XFRegError"] + RATINGS,
    "Gen": ["BusNum", "GenID", "GenStatus", "GenMW", "GenMVR", "GenMWMax", "GenMVRMax", "GenMVRMin",
            "GenFuelType", "TSPFWModelString", "Latitude", "Longitude", "Latitude:1", "Longitude:1",
            "CustomInteger:1", "GenUnitType", "GenAGCAble", "GenCostModel", "GenCostCurvePoints",
            "GenMCost", "AreaNum"],
    "Load": ["BusNum", "LoadID", "LoadStatus", "LoadMW", "LoadMVR"],
    "Shunt": ["BusNum", "ShuntID", "SSStatus", "SSCMode", "AutoControl", "SSRegNum", "SSAMVR",
              "SSNMVR", "SSMaxMVR", "SSMinMVR"],
    "Area": ["AreaNum", "SAName", "BGAGC", "BGReportLimits", "BGReportLimMinKV", "BGReportLimMaxKV"],
    "Zone": ["ZoneNum", "BGReportLimits", "BGReportLimMinKV", "BGReportLimMaxKV"],
    "SuperArea": ["SAName", "BGAGC"],
    "LimitSet": ["LSName", "LSDisabled", "LSLineRateSet", "LSLineRateSet:1", "LSAmpMVA"],
    "Contingency": ["CTGLabel"],
    "ViolationCTG": ["CTGLabel"],
}
# single-record objects the reader turns into scalars
SCALARS = {"Sim_Solution_Options": ["SBase", "ChkTaps", "ConvergenceTol:2"],
           "Limit_Monitoring_Options": ["LMS_IgnoreRadial"]}

NUMERIC = {
    "BusNum", "BusNum:1", "BusNomVolt", "BusNomVolt:1", "BusPUVolt", "BusVoltLimLow", "BusVoltLimHigh",
    "AreaNum", "ZoneNum", "BusMismatchP", "BusMismatchQ", "LineR", "LineX", "LineC", "LineMW",
    "LineMVA", "LineMaxPercent", "XFRegBus", "XFRegMin", "XFRegMax", "XFTapMin", "XFTapMax", "XFStep",
    "LineTap", "XFRegError", "GenMW", "GenMVR", "GenMWMax", "GenMVRMax", "GenMVRMin", "Latitude",
    "Longitude", "Latitude:1", "Longitude:1", "CustomInteger:1", "GenCostCurvePoints", "GenMCost",
    "LoadMW", "LoadMVR", "SSRegNum", "SSAMVR", "SSNMVR", "SSMaxMVR", "SSMinMVR",
    "BGReportLimMinKV", "BGReportLimMaxKV", *RATINGS,
}


def typed(df: pd.DataFrame | None, columns: list[str]) -> pd.DataFrame:
    """Numbers as floats ('None' and blanks become NaN), text stripped, every declared column
    present. None (PowerWorld's answer for an object with no rows) becomes an empty frame."""
    if df is None:
        return pd.DataFrame({c: pd.Series(dtype=float if c in NUMERIC else object) for c in columns})
    out = df.copy()
    for c in columns:
        if c not in out.columns:
            out[c] = float("nan") if c in NUMERIC else ""
    for c in out.columns:
        if c in NUMERIC:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype(float)
        else:
            out[c] = out[c].astype(str).str.strip()
    return out.reset_index(drop=True)


@dataclass
class Solve:
    """The one AC solve the engine runs on the case as it opened."""
    ran: bool = False
    raised: str | None = None            # PowerWorld's error text when SolvePowerFlow raised
    max_mismatch_mva: float | None = None
    tolerance_mva: float | None = None   # Sim_Solution_Options.ConvergenceTol:2

    @property
    def tolerance_unread(self) -> bool:
        return self.tolerance_mva is None or self.max_mismatch_mva is None

    @property
    def converged(self) -> bool:
        """The raise decides. The mismatch check is a second test, applied only when both numbers
        were read: an unreadable tolerance must not turn the case NOT READY on the engine's account."""
        if not self.ran or self.raised is not None:
            return False
        return self.tolerance_unread or self.max_mismatch_mva <= self.tolerance_mva


@dataclass
class CaseData:
    frames: dict[str, pd.DataFrame]
    scalars: dict = field(default_factory=dict)
    solve: Solve = field(default_factory=Solve)

    def __post_init__(self):
        self.frames = {obj: typed(self.frames.get(obj), cols) for obj, cols in READS.items()}

    def get(self, obj: str) -> pd.DataFrame:
        return self.frames[obj]

    def to_json(self, path: str | Path) -> None:
        payload = {"frames": {o: d.to_dict(orient="list") for o, d in self.frames.items()},
                   "scalars": self.scalars, "solve": asdict(self.solve)}
        raw = json.dumps(payload, default=str).encode("utf-8")
        Path(path).write_bytes(gzip.compress(raw) if str(path).endswith(".gz") else raw)

    @classmethod
    def from_json(cls, path: str | Path) -> "CaseData":
        raw = Path(path).read_bytes()
        d = json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)
        return cls({o: pd.DataFrame(v) for o, v in d["frames"].items()}, d["scalars"], Solve(**d["solve"]))
```

`skills/case-audit/engine/findings.py`:

```python
"""What a rule returns. Severity and triage are separate labels, each from a closed set."""
from __future__ import annotations

import math
from dataclasses import asdict, dataclass, field

STOPS, WORTH, FYI = "Stops the study", "Worth a look", "FYI"
BROKEN, ON_PURPOSE, YOUR_CALL = "Broken", "Probably on purpose", "Your call"
SEVERITIES = (STOPS, WORTH, FYI)
TRIAGES = (BROKEN, ON_PURPOSE, YOUR_CALL)
PROFILES = ("base", "n1", "timestep", "opf", "scopf")  # n1 = the monitoring verdict reported with base
AC_STUDIES = PROFILES                                 # every study here solves AC
NEEDS_HANDOFF = {"ts.pfw_missing", "opf.3"}           # data the kit does not carry: say where it comes from


@dataclass
class Finding:
    rule: str                  # e.g. "base.dc_skeleton"
    severity: str              # one of SEVERITIES
    triage: str                # one of TRIAGES
    what: str                  # what's wrong, one plain line
    why: str                   # why it matters, one plain line
    page: str = ""             # the kit page that explains it
    stops: tuple = ()          # profiles whose verdict this finding turns NOT READY
    scope: str = ""            # e.g. "N-1 and SCOPF only" - shown after the severity label
    where: list = field(default_factory=list)    # one dict of key fields (and numbers) per object
    details: dict = field(default_factory=dict)  # the numbers the agent quotes
    handoff: str = ""          # who supplies what the fix needs, when the kit cannot

    def __post_init__(self):
        assert self.severity in SEVERITIES, self.severity
        assert self.triage in TRIAGES, self.triage
        assert set(self.stops) <= set(PROFILES), self.stops
        assert bool(self.stops) == (self.severity == STOPS), (self.rule, self.stops)
        assert self.handoff or self.rule not in NEEDS_HANDOFF or self.triage == ON_PURPOSE, self.rule

    @property
    def label(self) -> str:
        return f"{self.severity} — {self.scope}" if self.scope else self.severity

    def to_dict(self) -> dict:
        d = asdict(self)
        d["stops"], d["label"], d["count"] = list(self.stops), self.label, len(self.where)
        return clean(d)


def clean(o):
    """NaN/inf -> None and numpy scalars -> Python, recursively, so json.dump never writes NaN."""
    if hasattr(o, "item") and not isinstance(o, (list, dict, str)):
        o = o.item()
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {str(k): clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def bus(n) -> int:
    return int(n)


def branch_keys(r) -> dict:
    """A branch's three key fields. LineCircuit is text: '1', 'W2', ' 1 ' all stay strings."""
    return {"BusNum": bus(r["BusNum"]), "BusNum:1": bus(r["BusNum:1"]), "LineCircuit": str(r["LineCircuit"])}
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 9 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/thresholds.py skills/case-audit/engine/casedata.py skills/case-audit/engine/findings.py skills/case-audit/tests/conftest.py skills/case-audit/tests/auditcase.py skills/case-audit/tests/test_audit_casedata.py
git commit -m "Add the case-audit data model: typed frames, the solve record, closed finding labels"
```

---

### Task 5: The reader, the read-only guard, and the Hawaii40 fixture

**Files:**
- Create: `skills/case-audit/engine/reader.py`
- Create: `skills/case-audit/tests/fake_esapp/esapp/__init__.py`
- Create: `tools/case-audit-dev/snapshot.py`, `tools/case-audit-dev/make_fixture.py`
- Create: `skills/case-audit/tests/fixtures/hawaii40.json.gz` (generated, Step 5)
- Test: `skills/case-audit/tests/test_audit_reader.py`, `skills/case-audit/tests/test_audit_read_only.py`

**Interfaces:**
- Consumes: `casedata` (Task 4); esapp at run time only.
- Produces: `ReadError`; `sha256(path) -> str`; `variants_beside(path) -> list[str]`; `kill_new_servers(before, lister=None, killer=None) -> list[int] | None`; `read_case(path) -> CaseData` with `scalars` `case_path`, `sha256_before`, `sha256_after`, `read_seconds`, `variants_beside`, `SBase`, `ChkTaps`, `ConvergenceTol:2`, `LMS_IgnoreRadial`. The stand-in esapp (env `PWHM_FAKE_SNAPSHOT`, `PWHM_FAKE_SOLVE_ERROR`, `PWHM_FAKE_OPEN_ERROR`, `PWHM_FAKE_READ_ERROR`, `PWHM_FAKE_EMPTY`; `CALLS`). The AST checker `violations(source, name) -> list[str]`.

The reader runs for real in the tests, against a stand-in `esapp` that serves the stored Hawaii40 snapshot, so the suite needs no PowerWorld. Variants are found by computed name (`X_PFW.pwb`, `X_PFW.pwx`, or `X.pwb` from a `_PFW` copy) with `Path.exists()`; the folder is never listed (R2). A failed open records the `pwrworld.exe` PIDs first and stops only the new ones (R6); another program starting PowerWorld in those same seconds would look new too, a window of one failed open. A listing that fails reads `None`, never an empty set: an empty "before" would make every server on the machine look new, and other jobs run PowerWorld on the machine this plan was written on. With either listing missing, nothing is stopped and the error says so (`test_a_failed_listing_stops_nothing`).

The AST guard has three layers (R7): only `reader.py` imports esapp; inside it every esapp object is bound by a plain `name = PowerWorld(...)` or `name = pw.esa` — a `with … as`, a tuple, an attribute target, a `return` or a conditional expression is flagged, so no binding escapes the tracking — and every esapp-bound name may be used only through `.esa`, `.SolvePowerFlow()` with no arguments, `.GetParametersMultipleElement` and `.exit` — never subscripted, assigned to, passed to a function (so no `getattr`, `setattr`, `__import__`), or re-bound; and the substring scan over every engine file stays as the second layer. A method's return value (a DataFrame) is data, not bound. The guard passes on the engine as soon as it is written; `test_the_check_catches_writes` shows it is not vacuous (`pw.save()`, `pw[Gen, "GenMW"] = df`, `pw.pflow(method="DC")`, `pw.flat_start = True`, `pw.edit_mode()`, `getattr(E, …)`, `helper(E)`, `E2 = E`, and five indirect bindings followed by `pw.save()`, each caught by the binding rule alone). `save` is also on the substring list.

- [ ] **Step 1: Write the failing tests and the stand-in esapp**

`skills/case-audit/tests/fake_esapp/esapp/__init__.py`:

```python
"""A stand-in for esapp that serves a stored snapshot, so the real reader and CLI run with no
PowerWorld. Put this folder first on sys.path (or PYTHONPATH) and set:

  PWHM_FAKE_SNAPSHOT     the snapshot to serve (required)
  PWHM_FAKE_SOLVE_ERROR  SolvePowerFlow raises with this text
  PWHM_FAKE_OPEN_ERROR   PowerWorld(path) raises with this text
  PWHM_FAKE_READ_ERROR   every GetParametersMultipleElement raises with this text
  PWHM_FAKE_EMPTY        comma list of objects that read as None (PowerWorld's zero-row answer)

CALLS records every call, for the tests that count them.
"""
import os
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "engine"))
from casedata import CaseData  # noqa: E402

CALLS = []


class _SAW:
    def __init__(self):
        cd = CaseData.from_json(os.environ["PWHM_FAKE_SNAPSHOT"])
        self.frames, self.scalars = cd.frames, cd.scalars
        self.empty = set(filter(None, os.environ.get("PWHM_FAKE_EMPTY", "").split(",")))

    def SolvePowerFlow(self, *args):
        CALLS.append(("SolvePowerFlow", args))
        if os.environ.get("PWHM_FAKE_SOLVE_ERROR"):
            raise RuntimeError(os.environ["PWHM_FAKE_SOLVE_ERROR"])

    def GetParametersMultipleElement(self, obj, fields):
        CALLS.append(("Get", obj))
        if os.environ.get("PWHM_FAKE_READ_ERROR"):
            raise RuntimeError(os.environ["PWHM_FAKE_READ_ERROR"])
        if obj in ("Sim_Solution_Options", "Limit_Monitoring_Options"):
            return pd.DataFrame([[self.scalars.get(f, "") for f in fields]], columns=fields)
        d = self.frames.get(obj)
        if obj in self.empty or d is None or d.empty:
            return None
        return d[fields].astype(str)

    def exit(self):
        CALLS.append(("exit",))


class PowerWorld:
    def __init__(self, path):
        CALLS.append(("open", path))
        if os.environ.get("PWHM_FAKE_OPEN_ERROR"):
            raise RuntimeError(os.environ["PWHM_FAKE_OPEN_ERROR"])
        self.esa = _SAW()
```

`skills/case-audit/tests/test_audit_reader.py`:

```python
"""The reader against the stand-in esapp (tests/fake_esapp): no PowerWorld needed."""
import pytest

import reader


def _case(tmp_path, name="c.pwb"):
    p = tmp_path / name
    p.write_bytes(b"case")
    return p


def test_reads_every_object_and_exits(fake_esapp, monkeypatch, tmp_path):
    monkeypatch.setenv("PWHM_FAKE_EMPTY", "Gen")                 # Gen reads None, as zero rows do
    cd = reader.read_case(_case(tmp_path))
    assert fake_esapp.CALLS[-1] == ("exit",) and cd.solve.converged
    assert cd.get("Gen").empty and len(cd.get("Bus")) == 37
    assert cd.scalars["sha256_before"] == cd.scalars["sha256_after"] and cd.scalars["SBase"] == "100"
    assert [c for c in fake_esapp.CALLS if c[0] == "SolvePowerFlow"] == [("SolvePowerFlow", ())]


def test_a_solve_that_raises_is_recorded_not_retried(fake_esapp, monkeypatch, tmp_path):
    monkeypatch.setenv("PWHM_FAKE_SOLVE_ERROR", "RunScriptCommand: NR PowerFlow - Power flow unable to converge.\nmore")
    cd = reader.read_case(_case(tmp_path))
    assert fake_esapp.CALLS[-1] == ("exit",) and not cd.solve.converged
    assert cd.solve.raised == "RunScriptCommand: NR PowerFlow - Power flow unable to converge."
    assert sum(c[0] == "SolvePowerFlow" for c in fake_esapp.CALLS) == 1


def test_exit_runs_even_when_a_read_fails(fake_esapp, monkeypatch, tmp_path):
    monkeypatch.setenv("PWHM_FAKE_READ_ERROR", "COM gone")
    with pytest.raises(RuntimeError):
        reader.read_case(_case(tmp_path))
    assert fake_esapp.CALLS[-1] == ("exit",)


def test_a_failed_open_stops_only_the_server_it_started(fake_esapp, monkeypatch, tmp_path):
    monkeypatch.setenv("PWHM_FAKE_OPEN_ERROR", "SimAuto not registered")
    seen = iter([{101, 102}, {101, 102, 555}])
    killed = []
    monkeypatch.setattr(reader, "_tasklist", lambda: next(seen))
    monkeypatch.setattr(reader, "_taskkill", killed.append)
    with pytest.raises(reader.ReadError, match="could not open"):
        reader.read_case(_case(tmp_path))
    assert killed == [555]


def test_a_failed_listing_stops_nothing(fake_esapp, monkeypatch, tmp_path):
    monkeypatch.setenv("PWHM_FAKE_OPEN_ERROR", "SimAuto not registered")
    seen = iter([None, {1, 2}])                                  # the listing before the open failed
    killed = []
    monkeypatch.setattr(reader, "_tasklist", lambda: next(seen))
    monkeypatch.setattr(reader, "_taskkill", killed.append)
    with pytest.raises(reader.ReadError, match="could not be listed, so none was stopped"):
        reader.read_case(_case(tmp_path))
    assert killed == []
    assert reader.kill_new_servers({1}, lister=lambda: None, killer=killed.append) is None and killed == []


def test_kill_new_servers_leaves_older_ones_alone():
    killed = []
    assert reader.kill_new_servers({1, 2}, lister=lambda: {1, 2, 3, 9}, killer=killed.append) == [3, 9]
    assert killed == [3, 9]


def test_missing_case_is_a_read_error(tmp_path):
    with pytest.raises(reader.ReadError, match="case not found"):
        reader.read_case(tmp_path / "nope.pwb")


def test_variants_are_found_by_name_not_by_listing(tmp_path):
    for n in ("grid.pwb", "grid_PFW.pwb", "grid_old.pwb", "gridlock.pwb"):
        (tmp_path / n).write_bytes(b"x")
    assert reader.variants_beside(tmp_path / "grid.pwb") == ["grid_PFW.pwb"]
    assert reader.variants_beside(tmp_path / "grid_PFW.pwb") == ["grid.pwb"]
    assert reader.variants_beside(tmp_path / "gridlock.pwb") == []
```

`skills/case-audit/tests/test_audit_read_only.py`:

```python
"""The engine never writes a case. Enforced on the source, in three layers:

1. only reader.py imports esapp;
2. in reader.py every name bound to an esapp object (the imported `PowerWorld`, `pw = PowerWorld(...)`,
   `E = pw.esa`) is bound only by a plain `name = ...` statement - never through `with`, a tuple,
   an attribute, a return value or a conditional expression - and may be used only through an allowlist - `.esa`, `.SolvePowerFlow()` with no
   arguments, `.GetParametersMultipleElement`, `.exit` - never subscripted, assigned to, passed
   to a function, or re-bound;
3. no name, attribute or string anywhere in engine/*.py names a write (the substring scan).
"""
import ast
from pathlib import Path

ENGINE = Path(__file__).resolve().parents[1] / "engine"
FORBIDDEN = ("SaveCase", "LoadAux", "ChangeParameters", "SetData", "WriteAuxFile", "Delete", "CreateData",
             "ProcessAuxFile", "exec_aux", "ResetToFlatStart", "Scale", "EnterMode", "SaveState",
             "RunScriptCommand", "edit_mode", "flat_start", "pflow", "save")
ALLOWED_ATTRS = {"esa", "SolvePowerFlow", "GetParametersMultipleElement", "exit"}


def imports_esapp(tree) -> bool:
    for n in ast.walk(tree):
        if isinstance(n, ast.Import) and any(a.name.split(".")[0] == "esapp" for a in n.names):
            return True
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "esapp":
            return True
    return False


def _parents(tree):
    for n in ast.walk(tree):
        for c in ast.iter_child_nodes(n):
            c.parent = n


def _root(node):
    """The Name at the bottom of an attribute chain such as pw.esa.exit, or None."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node if isinstance(node, ast.Name) else None


def _holds_esapp(value, bound) -> bool:
    """`PowerWorld(...)` (a call of a bound name), `pw.esa`, or a bound name itself."""
    if isinstance(value, ast.Call):
        return isinstance(value.func, ast.Name) and value.func.id in bound
    if isinstance(value, ast.Attribute):
        return value.attr == "esa" and _root(value) is not None and _root(value).id in bound
    return isinstance(value, ast.Name) and value.id in bound


def bound_names(tree) -> set[str]:
    """Names that hold an esapp object: imports from esapp, and anything assigned from one.
    A method's return value (a DataFrame from GetParametersMultipleElement) is data, not bound."""
    bound = set()
    for n in ast.walk(tree):
        if isinstance(n, ast.ImportFrom) and (n.module or "").split(".")[0] == "esapp":
            bound |= {a.asname or a.name for a in n.names}
        if isinstance(n, ast.Import):
            bound |= {a.asname or a.name for a in n.names if a.name.split(".")[0] == "esapp"}
    grew = True
    while grew:
        grew = False
        for n in ast.walk(tree):
            if isinstance(n, (ast.Assign, ast.AnnAssign, ast.NamedExpr)) and _holds_esapp(n.value, bound):
                targets = n.targets if isinstance(n, ast.Assign) else [n.target]
                for t in targets:
                    if isinstance(t, ast.Name) and t.id not in bound:
                        bound.add(t.id)
                        grew = True
    return bound


def _plain_bind(node) -> bool:
    """`name = <value>`: one target, and that target a bare name."""
    return isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)


def bound_use_violations(source: str, name: str = "<src>") -> list[str]:
    tree = ast.parse(source)
    _parents(tree)
    bound, out = bound_names(tree), []
    for n in ast.walk(tree):
        if not (isinstance(n, ast.Name) and n.id in bound):
            continue
        where = f"{name}:{n.lineno} {n.id}"
        p = n.parent
        if isinstance(n.ctx, ast.Store):
            ok = (isinstance(p, ast.Assign) and len(p.targets) == 1
                  and not isinstance(p.value, ast.Name) and _holds_esapp(p.value, bound))
            if not ok:
                out.append(f"{where} re-bound")
            continue
        node = n
        while isinstance(node.parent, ast.Attribute):
            node = node.parent
            if node.attr not in ALLOWED_ATTRS:
                out.append(f"{where}.{node.attr} is not on the read-only allowlist")
            if isinstance(node.ctx, ast.Store):
                out.append(f"{where}.{node.attr} assigned")
        top = node.parent
        if node is not n and node.attr == "esa" and not isinstance(top, ast.Attribute) and not _plain_bind(top):
            out.append(f"{where}.esa bound other than by a plain `name = ...`")
        if node is n:
            if isinstance(top, ast.Call) and top.func is n and n.id[:1].isupper():
                if not _plain_bind(top.parent):
                    out.append(f"{where}(...) bound other than by a plain `name = ...` "
                               f"({type(top.parent).__name__})")
                continue                                     # PowerWorld(path): opens, writes nothing
            out.append(f"{where} used directly ({type(top).__name__})")
        elif isinstance(top, ast.Subscript):
            out.append(f"{where} subscripted")
        elif isinstance(top, ast.Call) and top.func is node and node.attr == "SolvePowerFlow" and (top.args or top.keywords):
            out.append(f"{where}.SolvePowerFlow with a method (DC or a fallback)")
        elif isinstance(top, ast.Call) and top.func is not node:
            out.append(f"{where} passed to a function")
    return out


def substring_violations(source: str, name: str = "<src>") -> list[str]:
    out = []
    for node in ast.walk(ast.parse(source)):
        words = [node.attr] if isinstance(node, ast.Attribute) else [node.id] if isinstance(node, ast.Name) \
            else [node.value] if isinstance(node, ast.Constant) and isinstance(node.value, str) else []
        for w in words:
            out += [f"{name}:{node.lineno} {bad}" for bad in FORBIDDEN if bad in w]
    return out


def violations(source: str, name: str = "<src>") -> list[str]:
    return bound_use_violations(source, name) + substring_violations(source, name)


def test_only_reader_imports_esapp():
    importers = [p.name for p in ENGINE.glob("*.py") if imports_esapp(ast.parse(p.read_text(encoding="utf-8")))]
    assert importers == ["reader.py"]


def test_engine_never_writes_a_case():
    found = [v for p in sorted(ENGINE.glob("*.py")) for v in violations(p.read_text(encoding="utf-8"), p.name)]
    assert found == []


OPEN = "from esapp import PowerWorld\npw = PowerWorld(p)\nE = pw.esa\n"


def test_the_check_catches_writes():
    for bad in ['pw.esa.SaveCase("x.pwb")', "pw.save()", 'pw[Gen, "GenMW"] = df', 'pw.pflow(method="DC")',
                "pw.flat_start = True", "pw.edit_mode()", 'E.SolvePowerFlow("DC")', 'getattr(E, "x")',
                "helper(E)", "E2 = E", 'E.ChangeParametersSingleElement("Bus", f, v)', "x = pw[Bus]"]:
        assert violations(OPEN + bad), bad
    imp = "from esapp import PowerWorld\n"
    for bad in ["with PowerWorld(p) as pw:\n    pw.save()\n",
                "pw, n = PowerWorld(p), 1\npw.save()\n",
                "def opener(p):\n    return PowerWorld(p)\npw = opener(p)\npw.save()\n",
                "self.pw = PowerWorld(p)\nself.pw.save()\n",
                "pw = PowerWorld(p) if p else None\npw.save()\n"]:
        assert bound_use_violations(imp + bad), bad   # caught by the binding rule alone, not the scan
    assert violations('E.RunScriptCommand("SaveCase(x);")')
    assert violations('getattr(E, "LoadAux")')


def test_the_readers_own_calls_pass():
    ok = OPEN + "E.SolvePowerFlow()\nd = E.GetParametersMultipleElement('Bus', ['BusNum'])\npw.esa.exit()\n"
    assert violations(ok) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_reader.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'reader'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/reader.py`:

```python
"""The only module that talks to PowerWorld. Opens the case, solves AC once in memory, reads
every field in casedata.READS, closes. Never writes: tests/test_audit_read_only.py enforces it.

One AC solve on the case as it opened - no retry, no flat start, no DC fallback - because the
verdict is about this case, and every fallback changes what is being measured (a flat start
resets generator voltage setpoints; a DC solve switches the case to DC mode).
"""
from __future__ import annotations

import csv
import hashlib
import os
import subprocess
import time
from pathlib import Path

import pandas as pd

from casedata import READS, SCALARS, CaseData, Solve


class ReadError(Exception):
    """PowerWorld could not be reached or the case could not be opened. Nothing was audited."""


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def variants_beside(path: Path) -> list[str]:
    """Other versions of this case by the naming Auto_PFW uses, checked by name - the folder is
    never listed. X.pwb -> X_PFW.pwb / X_PFW.pwx; X_PFW.pwb -> X.pwb."""
    stem = path.stem
    names = [stem[:-4] + ".pwb"] if stem.lower().endswith("_pfw") else [stem + "_PFW.pwb", stem + "_PFW.pwx"]
    return [n for n in names if (path.parent / n).exists()]


def _tasklist() -> set[int] | None:
    """PIDs of running pwrworld.exe, or None when they cannot be listed. None is not "none running":
    treating a failed listing as empty would make every server on the machine look new."""
    try:
        p = subprocess.run(["tasklist", "/FI", "IMAGENAME eq pwrworld.exe", "/FO", "CSV", "/NH"],
                           capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return None
    if p.returncode != 0:
        return None
    return {int(r[1]) for r in csv.reader(p.stdout.splitlines()) if len(r) > 1 and r[1].isdigit()}


def _taskkill(pid: int) -> None:
    subprocess.run(["taskkill", "/PID", str(pid), "/F"], capture_output=True, timeout=30)


def kill_new_servers(before: set[int] | None, lister=None, killer=None) -> list[int] | None:
    """After a failed open, stop only the pwrworld.exe processes that did not exist before it.
    A failed open never hands back an object to exit(), so COM would leave that server running.
    If either listing failed, stop nothing and return None: without both lists "new" is unknown.
    A PowerWorld another program starts in those same seconds would look new too: the window is
    the few seconds of one failed open."""
    lister, killer = lister or _tasklist, killer or _taskkill
    after = lister()
    if before is None or after is None:
        return None
    new = sorted(after - before)
    for pid in new:
        killer(pid)
    return new


def read_case(case: str | Path) -> CaseData:
    path = Path(os.path.abspath(case))             # PowerWorld resolves relative paths against its own folder
    if not path.is_file():
        raise ReadError(f"case not found: {path}")
    try:
        from esapp import PowerWorld
    except ImportError as e:
        raise ReadError("esapp is not installed: run /powerworld-hivemind:powerworld-setup") from e
    before, t0 = sha256(path), time.perf_counter()
    servers = _tasklist()
    try:
        pw = PowerWorld(str(path))
    except Exception as e:
        stopped = kill_new_servers(servers)
        note = ("" if stopped is not None else
                "; the running PowerWorld processes could not be listed, so none was stopped")
        raise ReadError(f"PowerWorld could not open the case: {e}{note}") from e
    try:
        E = pw.esa
        solve = Solve(ran=True)
        try:
            E.SolvePowerFlow()
        except Exception as e:                    # esapp raises PowerWorldError when NR does not converge
            solve.raised = str(e).strip().splitlines()[0][:300]
        frames = {obj: E.GetParametersMultipleElement(obj, fields) for obj, fields in READS.items()}
        scalars = {}
        for obj, fields in SCALARS.items():
            d = E.GetParametersMultipleElement(obj, fields)
            for f in fields:
                scalars[f] = None if d is None else str(d[f].iloc[0]).strip()
    finally:
        pw.esa.exit()                             # del pw alone leaves pwrworld.exe running
    cd = CaseData(frames, scalars, solve)
    b = cd.get("Bus")
    mism = pd.concat([b.BusMismatchP.abs(), b.BusMismatchQ.abs()]).dropna()
    solve.max_mismatch_mva = float(mism.max()) if len(mism) else None
    tol = pd.to_numeric(pd.Series([scalars.get("ConvergenceTol:2")]), errors="coerce").iloc[0]
    solve.tolerance_mva = None if pd.isna(tol) else float(tol)
    cd.scalars.update({"case_path": str(path), "sha256_before": before, "sha256_after": sha256(path),
                       "read_seconds": round(time.perf_counter() - t0, 1),
                       "variants_beside": variants_beside(path)})
    return cd
```

- [ ] **Step 4: The two dev tools that make the fixture**

`tools/case-audit-dev/snapshot.py`:

```python
"""Read a case the way the engine does and store what was read, for tests and fixtures.

    python tools/case-audit-dev/snapshot.py <case.pwb> <out.json.gz>

A snapshot holds every field the engine reads for every bus, branch and unit. Take one only of
a public synthetic case, and never commit one without running make_fixture.py on it first.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "case-audit" / "engine"))

from reader import read_case  # noqa: E402

if __name__ == "__main__":
    cd = read_case(sys.argv[1])
    cd.to_json(sys.argv[2])
    print(f"{sys.argv[2]}: {len(cd.get('Bus'))} buses, solve {'converged' if cd.solve.converged else 'FAILED'}, "
          f"case file unchanged: {cd.scalars['sha256_before'] == cd.scalars['sha256_after']}")
```

`tools/case-audit-dev/make_fixture.py` (Task 16 adds the seeding options):

```python
"""Turn a snapshot from snapshot.py into a fixture fit for a public repo.

    python tools/case-audit-dev/make_fixture.py <in.json.gz> <out.json.gz>

Keeps only the case file's name (no local folders). Run it only on snapshots of public
synthetic cases. (Task 16 adds the seeding options.)
"""
import argparse
import sys
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "case-audit" / "engine"))

from casedata import CaseData  # noqa: E402


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    a = ap.parse_args(argv)
    cd = CaseData.from_json(a.src)
    cd.scalars["case_path"] = PureWindowsPath(cd.scalars["case_path"]).name
    cd.scalars.pop("read_seconds", None)
    cd.to_json(a.dst)
    print(f"{a.dst}: case {cd.scalars['case_path']}, {len(cd.get('Bus'))} buses")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Read Hawaii40 live and keep it as a fixture**

Run: `python tools/case-audit-dev/snapshot.py "$HAWAII40" /tmp/hawaii40_raw.json.gz`
Expected: `/tmp/hawaii40_raw.json.gz: 37 buses, solve converged, case file unchanged: True`

Run: `python tools/case-audit-dev/make_fixture.py /tmp/hawaii40_raw.json.gz skills/case-audit/tests/fixtures/hawaii40.json.gz`
Expected: `…hawaii40.json.gz: case Hawaii40_base.pwb, 37 buses` (about 7 KB; the local folder is gone). The raw snapshot stays in `/tmp`, never in the kit.

- [ ] **Step 6: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 21 passed.

- [ ] **Step 7: Commit**

```bash
git add skills/case-audit/engine/reader.py skills/case-audit/tests/fake_esapp/esapp/__init__.py tools/case-audit-dev/snapshot.py tools/case-audit-dev/make_fixture.py skills/case-audit/tests/test_audit_reader.py skills/case-audit/tests/test_audit_read_only.py skills/case-audit/tests/fixtures/hawaii40.json.gz
git commit -m "Add the case-audit reader: one AC solve, a read-only allowlist, stray-server cleanup, Hawaii40 fixture"
```

---

### Task 6: The case summary

**Files:**
- Create: `skills/case-audit/engine/summary.py`
- Test: `skills/case-audit/tests/test_audit_summary.py`

**Interfaces:**
- Consumes: `CaseData`, `thresholds.RENEWABLE_CODES`.
- Produces: `is_renewable(fuel: Series) -> Series`; `opf_super_areas(cd) -> list[str]`; `opf_areas(cd) -> set` (areas on OPF, plus the members of a super area on OPF, per Task 1's OPF runs); `case_summary(cd, opf=False) -> dict` with keys `load_mw, load_mvar, generation_mw, generation_mvar, losses_mw, headroom_dispatchable_mw, generation_includes_overshoot_mw, mvar_range, fuel[], shunts{}, size{}, contingencies, from_unsolved_case`, plus `opf_movable_headroom_mw` (dispatchable units only) when `opf`.

Headroom counts online units only, never wind or solar (their row reads `headroom_mw = None`, `weather_limited = True`), and a unit over its rating contributes 0, not a negative. Fuel rows use the case's own `GenFuelType` label; blank becomes `(blank)`. Shunt capacities are over in-service shunts.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_summary.py`:

```python
import pytest

from auditcase import case
from casedata import CaseData
from summary import case_summary


def test_totals_losses_and_headroom(frames):
    s = case_summary(case(frames))
    assert s["load_mw"] == 420 and s["generation_mw"] == 430 and s["losses_mw"] == 10
    assert s["headroom_dispatchable_mw"] == 100            # wind and solar never count as headroom
    assert s["mvar_range"] == [-130, 230]


def test_fuel_rows_keep_the_case_labels(frames):
    frames["Gen"].loc[len(frames["Gen"])] = {**frames["Gen"].iloc[0].to_dict(), "BusNum": 4, "GenID": "B1",
                                              "GenFuelType": "MWH (Electricity use for Energy Storage)",
                                              "GenStatus": "Open"}
    rows = {r["fuel"]: r for r in case_summary(case(frames))["fuel"]}
    assert set(rows) == {"NG (Natural Gas)", "WND (Wind)", "SUN (Solar)", "MWH (Electricity use for Energy Storage)"}
    assert rows["MWH (Electricity use for Energy Storage)"]["units_online"] == 0
    assert rows["MWH (Electricity use for Energy Storage)"]["units_total"] == 1
    assert rows["WND (Wind)"]["headroom_mw"] is None and rows["WND (Wind)"]["weather_limited"]
    assert rows["NG (Natural Gas)"]["share_of_output"] == pytest.approx(300 / 430)


def test_offline_capacity_is_not_headroom(frames):
    frames["Gen"].loc[0, "GenStatus"] = "Open"
    assert case_summary(case(frames))["headroom_dispatchable_mw"] == 0


def test_overshoot_is_reported_beside_generation(frames):
    frames["Gen"].loc[0, "GenMW"] = 412.0
    assert case_summary(case(frames))["generation_includes_overshoot_mw"] == pytest.approx(12)


def test_shunts_and_size(frames):
    s = case_summary(case(frames))
    assert s["shunts"] == {"count": 1, "in_service": 1, "mvar_now": 30, "capacitive_mvar": 60, "inductive_mvar": 0}
    assert s["size"] == {"buses": 6, "branches": 6, "transformers": 1, "areas": 1, "zones": 1,
                         "kv_levels": [138.0, 345.0]}


def test_opf_movable_headroom_is_dispatchable_units_in_opf_areas(frames):
    assert case_summary(case(frames), opf=True)["opf_movable_headroom_mw"] == 100    # wind and solar left out
    frames["Area"].loc[0, "BGAGC"] = "Off AGC"
    assert case_summary(case(frames), opf=True)["opf_movable_headroom_mw"] == 0


def test_a_super_area_on_opf_makes_its_areas_opf_areas(frames):
    import pandas as pd
    frames["Area"].loc[0, ["BGAGC", "SAName"]] = ["Off AGC", "S"]
    frames["SuperArea"] = pd.DataFrame({"SAName": ["S"], "BGAGC": ["OPF"]})
    assert case_summary(case(frames), opf=True)["opf_movable_headroom_mw"] == 100


def test_summary_of_a_case_with_no_shunts_or_loads(frames):
    frames["Shunt"], frames["Load"] = None, None
    s = case_summary(case(frames))
    assert s["shunts"]["count"] == 0 and s["load_mw"] == 0


def test_hawaii40_summary(hawaii):
    s = case_summary(CaseData.from_json(hawaii))
    assert s["size"]["buses"] == 37 and s["size"]["branches"] == 89 and s["size"]["transformers"] == 12
    assert round(s["load_mw"]) == 1136 and round(s["losses_mw"]) == 18
    assert {r["fuel"] for r in s["fuel"]} >= {"SUN (Solar)", "WND (Wind)", "DFO (Distillate Fuel Oil)"}
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_summary.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'summary'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/summary.py`:

```python
"""The case summary: facts, not findings. The agent presents these numbers; it never recomputes them."""
from __future__ import annotations

import pandas as pd

from casedata import CaseData
from thresholds import RENEWABLE_CODES


def is_renewable(fuel: pd.Series) -> pd.Series:
    """GenFuelType *contains* WND or SUN: the case labels them 'WND (Wind)', 'SUN (Solar)'."""
    return fuel.str.upper().str.contains("|".join(RENEWABLE_CODES), regex=True)


def opf_super_areas(cd: CaseData) -> list[str]:
    sa = cd.get("SuperArea")
    return list(sa.SAName[sa.BGAGC.str.upper() == "OPF"])


def opf_areas(cd: CaseData) -> set:
    """Areas the OPF may redispatch: BGAGC = OPF, or a member (Area.SAName) of a super area on OPF.
    Measured 2026-09-30 on two public synthetic cases: an OPF solved with only the super area on
    OPF (every area Off AGC), and with an area on OPF inside a super area that was Off AGC."""
    a = cd.get("Area")
    return set(a.AreaNum[(a.BGAGC.str.upper() == "OPF") | a.SAName.isin(opf_super_areas(cd))])


def case_summary(cd: CaseData, opf: bool = False) -> dict:
    gen, load, sh, bus, br = (cd.get(o) for o in ("Gen", "Load", "Shunt", "Bus", "Branch"))
    on = gen[gen.GenStatus == "Closed"].copy()
    ld = load[load.LoadStatus == "Closed"]
    on["renewable"] = is_renewable(on.GenFuelType)
    on["headroom"] = (on.GenMWMax - on.GenMW).clip(lower=0)
    gen_mw, load_mw = float(on.GenMW.sum()), float(ld.LoadMW.sum())
    dispatchable = on[~on.renewable]
    fuel = gen.GenFuelType.replace("", "(blank)")
    rows = []
    for label in sorted(fuel.unique()):
        units = gen[fuel == label]
        u_on = on[on.GenFuelType.replace("", "(blank)") == label]
        weather = bool(is_renewable(pd.Series([label])).iloc[0])
        rows.append({
            "fuel": label,
            "units_online": int(len(u_on)), "units_total": int(len(units)),
            "installed_mw": float(units.GenMWMax.sum()), "output_mw": float(u_on.GenMW.sum()),
            "share_of_output": float(u_on.GenMW.sum() / gen_mw) if gen_mw else 0.0,
            "headroom_mw": None if weather else float(u_on.headroom.sum()),
            "weather_limited": weather,
        })
    shin = sh[sh.SSStatus == "Closed"]
    kv = sorted({round(float(v), 1) for v in bus.BusNomVolt.dropna() if v > 0})
    over = (on.GenMW - on.GenMWMax)
    out = {
        "load_mw": load_mw, "load_mvar": float(ld.LoadMVR.sum()),
        "generation_mw": gen_mw, "generation_mvar": float(on.GenMVR.sum()),
        "losses_mw": gen_mw - load_mw,
        "headroom_dispatchable_mw": float(dispatchable.headroom.sum()),
        "generation_includes_overshoot_mw": float(over[over > 0.1].sum()),
        "mvar_range": [float(on.GenMVRMin.sum()), float(on.GenMVRMax.sum())],
        "fuel": rows,
        "shunts": {"count": int(len(sh)), "in_service": int(len(shin)),
                   "mvar_now": float(shin.SSAMVR.sum()),
                   "capacitive_mvar": float(shin.SSMaxMVR.sum()),
                   "inductive_mvar": float(shin.SSMinMVR.sum())},
        "size": {"buses": int(len(bus)), "branches": int(len(br)),
                 "transformers": int((br.LineXfmr == "YES").sum()),
                 "areas": int(len(cd.get("Area"))), "zones": int(len(cd.get("Zone"))),
                 "kv_levels": kv},
        "contingencies": int(len(cd.get("Contingency"))),
        "from_unsolved_case": not cd.solve.converged,
    }
    if opf:
        areas = opf_areas(cd)
        movable = on[(on.GenAGCAble == "YES") & on.AreaNum.isin(areas) & ~on.renewable]
        out["opf_movable_headroom_mw"] = float(movable.headroom.sum())
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 30 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/summary.py skills/case-audit/tests/test_audit_summary.py
git commit -m "Add the case summary: load, generation, headroom by fuel label, shunts, size"
```

---

### Task 7: Base rules — convergence, skeleton, overshoot, stale results

**Files:**
- Create: `skills/case-audit/engine/rules_base.py`
- Test: `skills/case-audit/tests/test_audit_rules_base.py`

**Interfaces:**
- Consumes: `CaseData`, `findings`, `thresholds`.
- Produces: `ac_converges(cd)`, `dc_skeleton(cd)`, `gen_over_nameplate(cd)`, `stale_ctg_results(cd)`, each `-> list[Finding]`.

Measured for the record on the public cases: median X/R of closed lines 2.5 (Hawaii40) and 5.9 (Texas2k); share with R ≤ 1e-6 and B = 0 was 0.0 and 0.001. Neither is near the skeleton line, nor the 5 % partial tier (Worth a look, with the lines). A median that cannot be taken (R = 0 on every line) reads "undefined", never "nan". The overshoot's `why` names the slack only as the case it applies to.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_rules_base.py`:

```python
import pandas as pd

from auditcase import case
from casedata import CaseData, Solve
from findings import FYI, STOPS, WORTH
from rules_base import ac_converges, dc_skeleton, gen_over_nameplate, stale_ctg_results


def test_converged_case_has_no_convergence_finding(frames):
    assert ac_converges(case(frames)) == []


def test_raised_solve_stops_every_study(frames):
    cd = CaseData(frames, {}, Solve(True, "NR PowerFlow - Exceeded maximum number of iterations", 2e-5, 1e-5))
    [f] = ac_converges(cd)
    assert f.severity == STOPS and set(f.stops) == {"base", "n1", "timestep", "opf", "scopf"}
    assert "Exceeded maximum number" in f.why


def test_mismatch_over_tolerance_without_a_raise_still_fails(frames):
    [f] = ac_converges(CaseData(frames, {}, Solve(True, None, 3.0, 0.1)))
    assert "3.0 MVA" in f.why


def test_real_network_is_not_a_skeleton(frames):
    assert dc_skeleton(case(frames)) == []


def test_placeholder_resistance_is_a_skeleton(frames):
    lines = frames["Branch"].LineXfmr == "NO"
    frames["Branch"].loc[lines, "LineR"] = 1e-7
    frames["Branch"].loc[lines, "LineC"] = 0.0
    [f] = dc_skeleton(case(frames))
    assert f.severity == STOPS and f.details["median_xr"] > 1000 and f.details["share_no_r_no_c"] == 1.0
    assert f.scope == "every AC study; a DC-only study can still run"


def test_part_skeleton_is_worth_a_look(frames):
    frames["Branch"].loc[0, ["LineR", "LineC"]] = [1e-7, 0.0]             # 1 of 5 closed lines
    [f] = dc_skeleton(case(frames))
    assert f.severity == WORTH and f.where == [{"BusNum": 1, "BusNum:1": 2, "LineCircuit": "1"}]


def test_zero_resistance_everywhere_says_undefined_not_nan(frames):
    frames["Branch"].loc[frames["Branch"].LineXfmr == "NO", ["LineR", "LineC"]] = [0.0, 0.0]
    [f] = dc_skeleton(case(frames))
    assert f.severity == STOPS and "undefined (R = 0 on every line)" in f.what and "nan" not in f.what


def test_small_overshoot_is_worth_a_look_with_its_mw(frames):
    frames["Gen"].loc[0, "GenMW"] = 403.0                   # 3 MW over a 400 MW unit: under max(4, 5)
    [f] = gen_over_nameplate(case(frames))
    assert f.severity == WORTH and f.where[0]["over_mw"] == 3.0 and f.where[0]["slack"]


def test_large_overshoot_stops_the_study(frames):
    frames["Gen"].loc[0, "GenMW"] = 460.0
    [f] = gen_over_nameplate(case(frames))
    assert f.severity == STOPS and f.where[0] == {"BusNum": 1, "GenID": "1", "GenMW": 460.0,
                                                  "GenMWMax": 400.0, "over_mw": 60.0, "slack": True}


def test_offline_unit_over_its_max_is_ignored(frames):
    frames["Gen"].loc[0, ["GenMW", "GenStatus"]] = [460.0, "Open"]
    assert gen_over_nameplate(case(frames)) == []


def test_stale_ctg_rows_are_fyi(frames):
    frames["ViolationCTG"] = pd.DataFrame({"CTGLabel": ["a", "a", "b"]})
    [f] = stale_ctg_results(case(frames))
    assert f.severity == FYI and f.details["rows"] == 3
    frames["ViolationCTG"] = None
    assert stale_ctg_results(case(frames)) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_rules_base.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'rules_base'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/rules_base.py`:

```python
"""base rules: does the AC solve, is the network real, is any unit past its rating, stale results."""
from __future__ import annotations

import numpy as np

from casedata import CaseData
from findings import AC_STUDIES, BROKEN, FYI, ON_PURPOSE, STOPS, WORTH, Finding, branch_keys, bus
from thresholds import (DC_SKELETON_MEDIAN_XR, DC_SKELETON_PARTIAL_SHARE, DC_SKELETON_SHARE, GEN_OVER_MIN_MW,
                        GEN_OVER_STOP_MW, GEN_OVER_STOP_SHARE, TINY_R)


def ac_converges(cd: CaseData) -> list[Finding]:
    s = cd.solve
    if s.converged:
        return []
    if s.raised:
        how = f"PowerWorld stopped the AC solve: {s.raised}"
    else:
        how = f"the largest bus mismatch is {s.max_mismatch_mva} MVA against a tolerance of {s.tolerance_mva} MVA"
    return [Finding(
        "base.ac_converges", STOPS, BROKEN,
        what="the AC power flow does not solve on the case as it opened",
        why=f"{how}; nothing read after an unsolved power flow can be trusted",
        page="methods/handling-errors.md", stops=AC_STUDIES,
        details={"raised": s.raised, "max_mismatch_mva": s.max_mismatch_mva,
                 "tolerance_mva": s.tolerance_mva})]


def dc_skeleton(cd: CaseData) -> list[Finding]:
    br = cd.get("Branch")
    lines = br[(br.LineStatus == "Closed") & (br.LineXfmr == "NO")]
    if lines.empty:
        return []
    ratio = (lines.LineX / lines.LineR.replace(0, np.nan)).dropna()
    xr = float(ratio.median()) if len(ratio) else float("nan")
    no_r_no_c = (lines.LineR <= TINY_R) & (lines.LineC == 0)
    share = float(no_r_no_c.mean())
    xr_text = "undefined (R = 0 on every line)" if np.isnan(xr) else f"{xr:,.0f}"
    details = {"median_xr": xr, "share_no_r_no_c": share, "closed_lines": int(len(lines)),
               "lines_with_no_r_no_c": int(no_r_no_c.sum()), "lines_with_zero_charging": int((lines.LineC == 0).sum())}
    if np.isnan(xr) or xr > DC_SKELETON_MEDIAN_XR or share >= DC_SKELETON_SHARE:
        return [Finding(
            "base.dc_skeleton", STOPS, BROKEN,
            what=f"a DC-only skeleton: median X/R {xr_text}, and {share:.0%} of closed lines have no resistance and no charging",
            why="the lines carry no real resistance or charging, so AC flows, losses and voltages are artifacts",
            page="concepts/case-impedance-completeness.md", stops=AC_STUDIES,
            scope="every AC study; a DC-only study can still run", details=details)]
    if share >= DC_SKELETON_PARTIAL_SHARE:
        return [Finding(
            "base.dc_skeleton", WORTH, BROKEN,
            what=f"part of the network is a DC skeleton: {int(no_r_no_c.sum())} of {len(lines)} closed lines ({share:.0%}) have no resistance and no charging",
            why="flows and voltages on those lines are artifacts; the rest of the case is real",
            page="concepts/case-impedance-completeness.md", details=details,
            where=[branch_keys(r) for _, r in lines[no_r_no_c].iterrows()])]
    return []


def gen_over_nameplate(cd: CaseData) -> list[Finding]:
    g = cd.get("Gen")
    on = g[g.GenStatus == "Closed"].copy()
    on["over"] = on.GenMW - on.GenMWMax
    on = on[on.over > GEN_OVER_MIN_MW]
    if on.empty:
        return []
    slack = set(cd.get("Bus").query("BusCat == 'Slack'").BusNum)
    size = np.maximum(GEN_OVER_STOP_SHARE * on.GenMWMax, GEN_OVER_STOP_MW)
    out = []
    for stop, part in ((True, on[on.over > size]), (False, on[on.over <= size])):
        if part.empty:
            continue
        where = [{"BusNum": bus(r.BusNum), "GenID": r.GenID, "GenMW": r.GenMW, "GenMWMax": r.GenMWMax,
                  "over_mw": round(r.over, 3), "slack": r.BusNum in slack} for r in part.itertuples()]
        total = float(part.over.sum())
        out.append(Finding(
            "base.gen_over_nameplate", STOPS if stop else WORTH, BROKEN,
            what=f"{len(part)} online unit(s) above their rating after the solve, {total:,.1f} MW over in all",
            why=("an overshoot this large means the dispatch does not match the ratings (at the slack, it is "
                 "a shortfall the slack absorbed), so the flows are artifacts" if stop else
                 "the case runs; the overshoot is small enough not to move a finding - say the MW"),
            page="methods/applying-a-dispatch-to-a-case.md", stops=AC_STUDIES if stop else (),
            where=where, details={"over_mw": total}))
    return out


def stale_ctg_results(cd: CaseData) -> list[Finding]:
    n = len(cd.get("ViolationCTG"))
    if not n:
        return []
    return [Finding(
        "base.stale_ctg_results", FYI, ON_PURPOSE,
        what=f"the case already holds {n} contingency violation rows from an earlier run",
        why="they describe whatever the case was when that run happened, not this audit - do not read them",
        page="methods/reading-violationctg.md", details={"rows": n})]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 41 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/rules_base.py skills/case-audit/tests/test_audit_rules_base.py
git commit -m "Add base rules: AC convergence, DC skeleton, units over rating, stale CTG rows"
```

---

### Task 8: Regulator rules

**Files:**
- Create: `skills/case-audit/engine/rules_reg.py`
- Test: `skills/case-audit/tests/test_audit_rules_reg.py`

**Interfaces:**
- Consumes: `CaseData`, `findings`, `thresholds`; page `methods/ltc-regulation-checks.md` (Task 2).
- Produces: `active_ltcs(cd) -> DataFrame`; `taps_move(cd) -> bool`; `step_up_buses(cd) -> set`; `regulates_nothing(cd)`, `ltc_middle_target(cd)`, `ltc_regulates_lv_side(cd)`, each `-> list[Finding]`.

From the probe: `0` is a defect (`reason = "zero"`), `AutoControl` reads `YES`, the HV band is the bus's own `BusVoltLimLow/High`. `ChkTaps != YES` is reported inside the LTC findings (`details.taps_move`, and a clause in `what`), not as a separate rule, so the agent's rule table needs no new id. A generator step-up's LV bus has a unit (any status — an offline step-up is still one), no closed load, and only transformers among its closed branches (parallel step-ups included); a small unit on a load bus is not a step-up. Skipped step-ups are counted and the count is asserted.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_rules_reg.py`:

```python
from auditcase import case
from findings import BROKEN, ON_PURPOSE, YOUR_CALL
from rules_reg import ltc_middle_target, ltc_regulates_lv_side, regulates_nothing

XF = 3                                                     # row of the 345/138 LTC in toy()


def test_healthy_regulators_are_quiet(frames):
    cd = case(frames)
    assert regulates_nothing(cd) == [] and ltc_middle_target(cd) == [] and ltc_regulates_lv_side(cd) == []


def test_shunt_pointing_at_a_missing_bus(frames):
    frames["Shunt"].loc[0, "SSRegNum"] = 99
    [f] = regulates_nothing(case(frames))
    assert f.triage == BROKEN and f.where == [{"device": "switched shunt", "BusNum": 4, "ShuntID": "1",
                                               "SSRegNum": 99, "reason": "missing"}]


def test_ltc_pointing_at_a_disconnected_bus(frames):
    frames["Bus"].loc[frames["Bus"].BusNum == 5, "BusStatus"] = "Disconnected"
    frames["Branch"].loc[XF, "XFRegBus"] = 5
    [f] = regulates_nothing(case(frames))
    assert f.where[0]["device"] == "LTC" and f.where[0]["reason"] == "disconnected"
    assert f.where[0]["LineCircuit"] == "1"


def test_zero_regulated_bus_is_a_defect(frames):
    # PowerWorld refuses to store 0 through SimAuto (probe 2026-09-30), so a 0 read back came in with the file
    frames["Branch"].loc[XF, "XFRegBus"] = 0
    [f] = regulates_nothing(case(frames))
    assert f.where[0]["reason"] == "zero"


def test_zero_mvar_shunt_with_no_target_is_a_placeholder(frames):
    frames["Shunt"].loc[0, ["SSRegNum", "SSMaxMVR", "SSMinMVR"]] = [0, 0.0, 0.0]
    [f] = regulates_nothing(case(frames))
    assert f.triage == ON_PURPOSE


def test_fixed_and_manual_devices_do_not_regulate(frames):
    frames["Shunt"].loc[0, ["SSRegNum", "SSCMode"]] = [99, "Fixed"]
    frames["Branch"].loc[XF, ["XFRegBus", "XFAuto"]] = [99, "NO"]
    assert regulates_nothing(case(frames)) == []


def test_star_bus_legs_are_skipped(frames):
    frames["Bus"].loc[frames["Bus"].BusNum == 4, "BusIsStarBus"] = "YES"
    frames["Branch"].loc[XF, "XFRegBus"] = 99
    assert regulates_nothing(case(frames)) == []


def test_middle_target_is_one_aggregated_finding(frames):
    extra = frames["Branch"].loc[XF].copy()
    extra["LineCircuit"] = "2"
    frames["Branch"].loc[len(frames["Branch"])] = extra
    frames["Branch"].loc[frames["Branch"].LineXfmr == "YES", "XFRegTargetType"] = "Middle"
    [f] = ltc_middle_target(case(frames))
    assert len(f.where) == 2 and f.details["most_common_band"] == [0.98, 1.02]
    assert f.details["midpoint"] == 1.0 and "three-winding" in f.details["three_winding"]


def test_band_copied_from_tap_range_is_not_middle_finding(frames):
    frames["Branch"].loc[XF, ["XFRegTargetType", "XFRegMin", "XFRegMax"]] = ["Middle", 0.51, 1.5]
    assert ltc_middle_target(case(frames)) == []


def test_frozen_taps_are_said(frames):
    frames["Branch"].loc[XF, "XFRegTargetType"] = "Middle"
    [f] = ltc_middle_target(case(frames, ChkTaps="NO"))
    assert "taps are frozen" in f.what and f.details["taps_move"] is False


def _hv_high(frames):
    frames["Bus"].loc[frames["Bus"].BusNum == 3, "BusPUVolt"] = 1.13
    frames["Branch"].loc[XF, ["LineTap", "XFRegError"]] = [1.1, 0.003]


def test_ltc_holding_lv_while_hv_out_of_band(frames):
    _hv_high(frames)
    [f] = ltc_regulates_lv_side(case(frames))
    w = f.where[0]
    assert f.triage == YOUR_CALL and w["hv_bus"] == 3 and w["hv_pu"] == 1.13 and w["hv_band"] == [0.9, 1.1]
    assert w["at_tap_limit"] and w["pushing_hv_away"] and f.details["pushing"] == 1


def test_lv_side_with_hv_in_band_is_quiet(frames):
    frames["Bus"].loc[frames["Bus"].BusNum == 3, "BusPUVolt"] = 1.09
    assert ltc_regulates_lv_side(case(frames)) == []


def test_generator_step_up_is_skipped_and_counted(frames):
    _hv_high(frames)
    b, br, g = frames["Bus"], frames["Branch"], frames["Gen"]
    b.loc[len(b)] = {**b.iloc[3].to_dict(), "BusNum": 7, "BusName": "BUS7", "BusNomVolt": 22.0}
    br.loc[len(br)] = {**br.loc[XF].to_dict(), "BusNum": 3, "BusNum:1": 7, "BusNomVolt:1": 22.0, "XFRegBus": 7.0}
    g.loc[len(g)] = {**g.iloc[0].to_dict(), "BusNum": 7, "GenID": "G7", "GenStatus": "Open"}   # offline still a GSU
    [f] = ltc_regulates_lv_side(case(frames))
    assert [w["BusNum:1"] for w in f.where] == [4] and f.details["generator_step_ups_skipped"] == 1


def test_a_small_unit_on_a_load_bus_is_not_a_step_up(frames):
    _hv_high(frames)
    frames["Gen"].loc[len(frames["Gen"])] = {**frames["Gen"].iloc[0].to_dict(), "BusNum": 4, "GenID": "G4"}
    [f] = ltc_regulates_lv_side(case(frames))
    assert f.details["generator_step_ups_skipped"] == 0


def test_blank_bus_limits_fall_back_to_the_study_band(frames):
    frames["Bus"].loc[frames["Bus"].BusNum == 3, ["BusPUVolt", "BusVoltLimLow", "BusVoltLimHigh"]] = [1.07, 0, 0]
    [f] = ltc_regulates_lv_side(case(frames))
    assert f.where[0]["hv_band"] == [0.94, 1.05]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_rules_reg.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'rules_reg'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/rules_reg.py`:

```python
"""Regulator rules: what each LTC and switched shunt holds (methods/ltc-regulation-checks.md)."""
from __future__ import annotations

import pandas as pd

from casedata import CaseData
from findings import BROKEN, ON_PURPOSE, WORTH, YOUR_CALL, Finding, branch_keys, bus
from thresholds import BAND_TOL_PU, FALLBACK_BAND, KV_SAME_REL, LTC_BAND_CAN_ACT_PU

PAGE = "methods/ltc-regulation-checks.md"
REGULATING_MODES = {"Discrete", "Continuous", "SVC"}
THREE_WINDING = "three-winding transformers are not checked in this version"


def active_ltcs(cd: CaseData) -> pd.DataFrame:
    """Closed LTCs on automatic control, two-winding only (a leg touching a star bus is skipped)."""
    br, b = cd.get("Branch"), cd.get("Bus")
    star = set(b.BusNum[b.BusIsStarBus == "YES"])
    m = ((br.LineXfmr == "YES") & (br.LineXFType == "LTC") & (br.XFAuto == "YES")
         & (br.LineStatus == "Closed") & ~br.BusNum.isin(star) & ~br["BusNum:1"].isin(star))
    return br[m]


def taps_move(cd: CaseData) -> bool:
    return str(cd.scalars.get("ChkTaps", "YES")).strip().upper() == "YES"


def _target(reg, status: dict) -> str | None:
    """Why a regulated-bus number is no target: 'zero', 'missing', 'disconnected', or None if fine."""
    if pd.isna(reg) or reg == 0:
        return "zero"
    if reg not in status:
        return "missing"
    return "disconnected" if status[reg] == "Disconnected" else None


def regulates_nothing(cd: CaseData) -> list[Finding]:
    b = cd.get("Bus")
    status = dict(zip(b.BusNum, b.BusStatus))
    broken, placeholders = [], []
    sh = cd.get("Shunt")
    sh = sh[(sh.SSStatus == "Closed") & sh.SSCMode.isin(REGULATING_MODES) & (sh.AutoControl == "YES")]
    for r in sh.itertuples():
        if status.get(r.BusNum) == "Disconnected":
            continue                                   # a de-energised regulator is not this defect
        why = _target(r.SSRegNum, status)
        if why:
            row = {"device": "switched shunt", "BusNum": bus(r.BusNum), "ShuntID": r.ShuntID,
                   "SSRegNum": None if pd.isna(r.SSRegNum) else bus(r.SSRegNum), "reason": why}
            empty = abs(r.SSMaxMVR) < 1e-6 and abs(r.SSMinMVR) < 1e-6
            (placeholders if empty and why != "disconnected" else broken).append(row)
    for _, r in active_ltcs(cd).iterrows():
        if "Disconnected" in (status.get(r["BusNum"]), status.get(r["BusNum:1"])):
            continue
        why = _target(r["XFRegBus"], status)
        if why:
            broken.append({"device": "LTC", **branch_keys(r),
                           "XFRegBus": None if pd.isna(r["XFRegBus"]) else bus(r["XFRegBus"]), "reason": why})
    out = []
    if broken:
        out.append(Finding(
            "base.regulates_nothing", WORTH, BROKEN,
            what=f"{len(broken)} regulator(s) point at a bus that does not exist or is out of service",
            why="the case still solves, but these devices hold nothing the modeller intended",
            page=PAGE, where=broken, details={"three_winding": THREE_WINDING}))
    if placeholders:
        out.append(Finding(
            "base.regulates_nothing", WORTH, ON_PURPOSE,
            what=f"{len(placeholders)} switched shunt(s) with a 0 Mvar range and no regulated bus",
            why="a 0 Mvar shunt with no target is usually a placeholder, not a defect",
            page=PAGE, where=placeholders))
    return out


def ltc_middle_target(cd: CaseData) -> list[Finding]:
    ltc = active_ltcs(cd)
    ltc = ltc[(ltc.XFRegTargetType == "Middle") & ((ltc.XFRegMax - ltc.XFRegMin) <= LTC_BAND_CAN_ACT_PU)]
    if ltc.empty:
        return []
    bands = ltc.groupby(["XFRegMin", "XFRegMax"]).size().sort_values(ascending=False)
    (lo, hi), n_band = bands.index[0], int(bands.iloc[0])
    where = [{**branch_keys(r), "XFRegBus": None if pd.isna(r["XFRegBus"]) else bus(r["XFRegBus"]),
              "XFRegMin": r["XFRegMin"], "XFRegMax": r["XFRegMax"],
              "midpoint": (r["XFRegMin"] + r["XFRegMax"]) / 2} for _, r in ltc.iterrows()]
    frozen = "" if taps_move(cd) else " (taps are frozen in this case: Sim_Solution_Options.ChkTaps is not YES)"
    return [Finding(
        "base.ltc_middle_target", WORTH, BROKEN,
        what=(f"{len(ltc)} active LTC(s) drive to the middle of their band, not into it; most common band "
              f"{lo:.3f}-{hi:.3f} pu ({n_band} units), midpoint {(lo + hi) / 2:.4f}{frozen}"),
        why="out of band, a Middle target pulls the bus to the midpoint, so a band tuned to the limit overshoots",
        page=PAGE, where=where,
        details={"count": len(ltc), "most_common_band": [lo, hi], "units_on_that_band": n_band,
                 "midpoint": (lo + hi) / 2, "taps_move": taps_move(cd), "three_winding": THREE_WINDING})]


def step_up_buses(cd: CaseData) -> set:
    """A generator step-up's LV bus: it has a unit (any status), no closed load, and every closed
    branch at it is a transformer - parallel step-ups included."""
    g, ld, br = cd.get("Gen"), cd.get("Load"), cd.get("Branch")
    closed = br[br.LineStatus == "Closed"]
    ends = pd.concat([closed[["BusNum", "LineXfmr"]],
                      closed[["BusNum:1", "LineXfmr"]].rename(columns={"BusNum:1": "BusNum"})])
    only_xf = ends.groupby("BusNum").LineXfmr.agg(lambda s: bool((s == "YES").all()))
    candidates = set(g.BusNum) - set(ld.BusNum[ld.LoadStatus == "Closed"])
    return {b for b in candidates if only_xf.get(b, False)}


def _band(r) -> tuple[float, float]:
    lo, hi = r["BusVoltLimLow"], r["BusVoltLimHigh"]
    if pd.isna(lo) or pd.isna(hi) or lo <= 0 or hi <= 0:
        return FALLBACK_BAND
    return float(lo), float(hi)


def ltc_regulates_lv_side(cd: CaseData) -> list[Finding]:
    b = cd.get("Bus").set_index("BusNum")
    gsu_buses = step_up_buses(cd)
    where, gsu = [], 0
    for _, r in active_ltcs(cd).iterrows():
        kf, kt = r["BusNomVolt"], r["BusNomVolt:1"]
        if pd.isna(kf) or pd.isna(kt) or abs(kf - kt) <= KV_SAME_REL * max(kf, kt):
            continue
        hv, lv = (r["BusNum"], r["BusNum:1"]) if kf > kt else (r["BusNum:1"], r["BusNum"])
        lv_kv, reg = min(kf, kt), r["XFRegBus"]
        lv_side = reg == lv or (reg not in (hv, lv) and reg in b.index
                                and b.at[reg, "BusNomVolt"] <= lv_kv * (1 + KV_SAME_REL))
        if not lv_side or hv not in b.index:
            continue
        lo, hi = _band(b.loc[hv])
        v = b.at[hv, "BusPUVolt"]
        if lo - BAND_TOL_PU <= v <= hi + BAND_TOL_PU:
            continue
        if lv in gsu_buses:
            gsu += 1
            continue
        half = (r["XFStep"] or 0) / 2
        at_limit = abs(r["LineTap"] - r["XFTapMax"]) < half or abs(r["LineTap"] - r["XFTapMin"]) < half
        pushing = bool(at_limit and r["XFRegError"] != 0)
        where.append({**branch_keys(r), "XFRegBus": bus(reg), "hv_bus": bus(hv),
                      "hv_bus_name": b.at[hv, "BusName"], "hv_pu": v, "hv_band": [lo, hi],
                      "lv_pu": b.at[lv, "BusPUVolt"] if lv in b.index else None,
                      "LineTap": r["LineTap"], "XFTapMin": r["XFTapMin"], "XFTapMax": r["XFTapMax"],
                      "XFRegError": r["XFRegError"], "LineMVA": r["LineMVA"],
                      "at_tap_limit": bool(at_limit), "pushing_hv_away": pushing})
    if not where:
        return []
    pushing = sum(w["pushing_hv_away"] for w in where)
    return [Finding(
        "base.ltc_regulates_lv_side", WORTH, YOUR_CALL,
        what=(f"{len(where)} LTC(s) hold their low-voltage side while the high-voltage side is out of band"
              + (f"; {pushing} sit at a tap limit, actively pushing the high side away" if pushing else "")),
        why="a tap moves Mvar from one side to the other: holding the LV bus can cause the HV violation "
            "(right for a distribution tap, wrong for a bulk transformer)",
        page=PAGE, where=where,
        details={"count": len(where), "pushing": pushing, "generator_step_ups_skipped": gsu,
                 "taps_move": taps_move(cd), "three_winding": THREE_WINDING})]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 56 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/rules_reg.py skills/case-audit/tests/test_audit_rules_reg.py
git commit -m "Add regulator rules: target that is missing, Middle target type, LTC holding its LV side"
```

---

### Task 9: The floating EHV stub

**Files:**
- Create: `skills/case-audit/engine/topology.py`, `skills/case-audit/engine/rules_stub.py`
- Test: `skills/case-audit/tests/test_audit_stub.py`

**Interfaces:**
- Consumes: `CaseData`, `findings`, `thresholds`; page `concepts/unloaded-ehv-stub-overvoltage.md` (Task 2).
- Produces: `bridges(nodes, edges) -> set[int]`; `adjacency(edges) -> dict`; `pockets(nodes, edges) -> {edge: {"near", "far", "size", "parent"}}` (integer far-side sizes); `far_side(adj, k, far, limit) -> set | None`; `floating_stub(cd) -> list[Finding]`.

`topology.py` mirrors the bridge search of `skills/violation-map/engine/islanding_screen.py` (same conventions: parallel circuits are separate edges, the core is the largest 2-edge-connected piece, nested bridges group under the attachment) at bus level, as a library — that file is a script that runs on import, so it cannot be reused directly. Both loops are iterative. `pockets` builds no per-bridge node sets: subtree sizes are integers from one post-order walk, so memory is linear in the case (revision 1 copied each side set into its parents, n × depth — about 9.5 GB on the 20,000-bus chain test). A far side is built only for a bridge that is a line, EHV at both ends and small enough, by a search that never crosses the bridge and stops past `STUB_MAX_BUSES`. The rule then keeps the **topmost bridge that passes** every test, so a loaded attachment with an unloaded sub-stub reports the sub-stub. On Texas2k (182 buses at 500 kV) the rule found no stub.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_stub.py`:

```python
import time
import tracemalloc

from auditcase import case
from findings import YOUR_CALL
from rules_stub import floating_stub
from topology import adjacency, bridges, far_side, pockets


def test_double_circuit_is_never_a_bridge():
    assert bridges([1, 2, 3], [(1, 2), (1, 2), (2, 3)]) == {2}


def test_pockets_carry_sizes_and_the_chain_above():
    edges = [(1, 2), (2, 3), (3, 1), (3, 5), (5, 6)]
    p = pockets([1, 2, 3, 5, 6], edges)
    assert p[3] == {"near": 3, "far": 5, "parent": None, "size": 2}
    assert p[4] == {"near": 5, "far": 6, "parent": 3, "size": 1}


def test_far_side_never_crosses_its_bridge_and_stops_at_the_limit():
    edges = [(1, 2), (2, 3), (3, 1), (3, 5), (5, 6), (6, 7)]
    adj = adjacency(edges)
    assert far_side(adj, 3, 5, 10) == {5, 6, 7}
    assert far_side(adj, 3, 5, 2) is None


def test_long_chain_is_linear_in_time_and_memory():
    n = 20000
    edges = [(1, 2), (2, 3), (3, 1)] + [(i, i + 1) for i in range(3, n)]
    tracemalloc.start()
    t = time.perf_counter()
    p = pockets(list(range(1, n + 1)), edges)
    peak = tracemalloc.get_traced_memory()[1]
    tracemalloc.stop()
    assert len(p) == n - 3 and time.perf_counter() - t < 10 and peak < 200e6


def _unloaded(frames, stub_pu=(1.05, 1.07)):
    b = frames["Bus"]
    b.loc[b.BusNum.isin([5, 6]), "BusPUVolt"] = list(stub_pu)
    frames["Branch"].loc[4, ["LineMW", "LineMaxPercent"]] = [0.5, 1.0]     # the 3-5 attachment line


def test_unloaded_ehv_stub_fires_once_at_its_attachment(frames):
    _unloaded(frames)
    frames["Branch"].loc[5, "LineMaxPercent"] = 1.0                         # 5-6 passes too; 3-5 is reported
    [f] = floating_stub(case(frames))
    w = f.where[0]
    assert f.triage == YOUR_CALL and len(f.where) == 1 and (w["BusNum"], w["BusNum:1"]) == (3, 5)
    assert w["far_bus"] == 6 and w["far_pu"] == 1.07 and w["far_side_buses"] == 2
    assert w["charging_mvar_at_1pu"] == 4.0 and w["absorbing_room_mvar"] == 0
    assert w["zero_range_units"] == [{"BusNum": 6, "GenID": "S1"}]


def test_a_loaded_attachment_with_an_unloaded_sub_stub_reports_the_sub_stub(frames):
    b = frames["Bus"]
    b.loc[b.BusNum.isin([5, 6]), "BusPUVolt"] = [1.02, 1.07]
    frames["Branch"].loc[5, ["LineMW", "LineMaxPercent"]] = [0.3, 1.0]     # 5-6 unloaded; 3-5 stays at 40 %
    [f] = floating_stub(case(frames))
    assert [(w["BusNum"], w["BusNum:1"]) for w in f.where] == [(5, 6)]


def test_loaded_stub_is_quiet(frames):
    _unloaded(frames)
    frames["Branch"].loc[4, "LineMaxPercent"] = 40.0
    assert floating_stub(case(frames)) == []


def test_no_rise_is_quiet(frames):
    _unloaded(frames, stub_pu=(1.0, 1.0))
    assert floating_stub(case(frames)) == []


def test_no_charging_means_no_stub(frames):
    _unloaded(frames)
    frames["Branch"].LineC = 0.0
    assert floating_stub(case(frames)) == []


def test_below_ehv_is_not_a_stub(frames):
    _unloaded(frames)
    frames["Bus"].loc[frames["Bus"].BusNum.isin([3, 5, 6]), "BusNomVolt"] = 230.0
    assert floating_stub(case(frames)) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_stub.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'rules_stub'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/topology.py`:

```python
"""Bridges and the radial pockets they hang, on the bus multigraph. Iterative, so a 100k-bus
case does not hit Python's recursion limit. Mirrors the bridge search of the violation-map
engine's islanding screen (same conventions), at bus level and as a library.

Parallel circuits are separate edges, so a double circuit is never a bridge. The meshed core
is the largest 2-edge-connected piece; each bridge's far side is the part away from the core.
Only far-side sizes are computed for every bridge; the far side itself is built on demand, for
the few bridges a rule asks about, and capped.
"""
from __future__ import annotations

from collections import Counter, defaultdict


def bridges(nodes, edges) -> set[int]:
    """Indices of the edges whose loss splits their component. edges: list of (u, v)."""
    adj = adjacency(edges)
    disc, low, out, t = {}, {}, set(), 0
    for root in nodes:
        if root in disc:
            continue
        disc[root] = low[root] = t
        t += 1
        stack = [(root, -1, iter(adj[root]))]
        while stack:
            u, pe, it = stack[-1]
            nxt = next(it, None)
            if nxt is None:
                stack.pop()
                if stack:
                    p = stack[-1][0]
                    low[p] = min(low[p], low[u])
                    if low[u] > disc[p]:
                        out.add(pe)
                continue
            v, k = nxt
            if k == pe:
                continue
            if v in disc:
                low[u] = min(low[u], disc[v])
            else:
                disc[v] = low[v] = t
                t += 1
                stack.append((v, k, iter(adj[v])))
    return out


def adjacency(edges) -> dict:
    adj = defaultdict(list)
    for k, (u, v) in enumerate(edges):
        adj[u].append((v, k))
        adj[v].append((u, k))
    return adj


def pockets(nodes, edges) -> dict[int, dict]:
    """For every bridge reachable from the core: {edge: {"near": core-side node, "far": far-side
    terminal, "size": far-side bus count, "parent": the next bridge towards the core or None}}.
    Sizes come from a post-order walk over integers; no per-bridge node sets are built, so memory
    stays linear in the case size however deep the radial chains run."""
    br = bridges(nodes, edges)
    adj = adjacency(edges)
    comp = {}
    for s in nodes:
        if s in comp:
            continue
        comp[s], q = s, [s]
        while q:
            u = q.pop()
            for v, k in adj[u]:
                if k not in br and v not in comp:
                    comp[v] = s
                    q.append(v)
    if not comp:
        return {}
    pieces = Counter(comp.values())
    core = pieces.most_common(1)[0][0]
    members = defaultdict(list)
    for n, c in comp.items():
        members[c].append(n)
    info, order, child_of, seen = {}, [], {}, {core}
    stack = [(core, None)]
    while stack:                                   # walk the bridge tree outward from the core
        c, parent_edge = stack.pop()
        order.append(c)
        for n in members[c]:
            for v, k in adj[n]:
                if k in br and comp[v] not in seen:
                    seen.add(comp[v])
                    info[k] = {"near": n, "far": v, "parent": parent_edge}
                    child_of[comp[v]] = k
                    stack.append((comp[v], k))
    size = {c: pieces[c] for c in seen}
    for c in reversed(order):                      # leaves first: add each subtree to its parent
        k = child_of.get(c)
        if k is not None:
            size[comp[info[k]["near"]]] += size[c]
            info[k]["size"] = size[c]
    return info


def far_side(adj, k, far, limit):
    """The buses beyond bridge k: a search from its far terminal that never crosses k. None as
    soon as it passes `limit` buses, so a big radial region costs `limit` steps, not its size."""
    side, q = {far}, [far]
    while q:
        u = q.pop()
        for v, e in adj[u]:
            if e != k and v not in side:
                side.add(v)
                if len(side) > limit:
                    return None
                q.append(v)
    return side
```

`skills/case-audit/engine/rules_stub.py`:

```python
"""base.floating_stub: a lightly loaded EHV dead end rising on its own line charging
(concepts/unloaded-ehv-stub-overvoltage.md)."""
from __future__ import annotations

import pandas as pd

from casedata import CaseData
from findings import WORTH, YOUR_CALL, Finding, branch_keys, bus
from thresholds import (EHV_KV, FALLBACK_BAND, STUB_LIGHT_MW, STUB_LIGHT_PERCENT, STUB_MAX_BUSES,
                        STUB_RISE_PU)
from topology import adjacency, far_side, pockets

PAGE = "concepts/unloaded-ehv-stub-overvoltage.md"


def floating_stub(cd: CaseData) -> list[Finding]:
    b = cd.get("Bus")
    b = b[b.BusStatus == "Connected"].set_index("BusNum")
    br = cd.get("Branch")
    br = br[(br.LineStatus == "Closed") & br.BusNum.isin(b.index) & br["BusNum:1"].isin(b.index)]
    br = br.reset_index(drop=True)
    ehv = set(b.index[b.BusNomVolt >= EHV_KV])
    edges = list(zip(br.BusNum, br["BusNum:1"]))
    info, adj = pockets(list(b.index), edges), adjacency(edges)
    g, sh = cd.get("Gen"), cd.get("Shunt")
    g, sh = g[g.GenStatus == "Closed"], sh[sh.SSStatus == "Closed"]
    sbase = float(cd.scalars.get("SBase") or 100.0)
    passing = {}
    for k, v in info.items():
        if not (br.at[k, "LineXfmr"] == "NO" and v["near"] in ehv and v["far"] in ehv
                and v["size"] <= STUB_MAX_BUSES):
            continue
        side = far_side(adj, k, v["far"], STUB_MAX_BUSES)
        if side is None:
            continue
        r, near = br.loc[k], v["near"]
        light = r.LineMaxPercent < STUB_LIGHT_PERCENT if r.LineAMVA > 0 else abs(r.LineMW) < STUB_LIGHT_MW
        far = max((n for n in side if n in ehv), key=lambda n: b.at[n, "BusPUVolt"])
        rise = b.at[far, "BusPUVolt"] - b.at[near, "BusPUVolt"]
        inside = br.BusNum.isin(side) & br["BusNum:1"].isin(side)
        charging = float(br.loc[inside & (br.LineXfmr == "NO"), "LineC"].sum() + r.LineC)
        if not (light and rise >= STUB_RISE_PU and charging > 0):
            continue
        gs, ss = g[g.BusNum.isin(side)], sh[sh.BusNum.isin(side)]
        high = b.at[far, "BusVoltLimHigh"]
        high = FALLBACK_BAND[1] if pd.isna(high) or high <= 0 else float(high)
        zero_range = gs[(gs.GenMVRMax == 0) & (gs.GenMVRMin == 0)]
        passing[k] = {**branch_keys(r), "near_bus": bus(near), "near_pu": b.at[near, "BusPUVolt"],
                      "far_bus": bus(far), "far_bus_name": b.at[far, "BusName"],
                      "far_pu": b.at[far, "BusPUVolt"], "far_above_limit": bool(b.at[far, "BusPUVolt"] > high),
                      "LineMW": r.LineMW, "LineMaxPercent": r.LineMaxPercent, "far_side_buses": len(side),
                      "charging_mvar_at_1pu": charging * sbase,
                      "absorbing_room_mvar": float((gs.GenMVR - gs.GenMVRMin).sum() + (ss.SSNMVR - ss.SSMinMVR).sum()),
                      "zero_range_units": [{"BusNum": bus(u.BusNum), "GenID": u.GenID}
                                           for u in zero_range.itertuples()]}
    where = [row for k, row in passing.items() if not _passing_above(k, info, passing)]
    if not where:
        return []
    return [Finding(
        "base.floating_stub", WORTH, YOUR_CALL,
        what=f"{len(where)} lightly loaded EHV dead end(s) whose far end rises on its own line charging",
        why="the rise depends on the dispatch: with the far-end plant off it runs higher, and the one "
            "link that feeds it islands it on a single outage",
        page=PAGE, where=where, details={"count": len(where), "system_mva_base": sbase})]


def _passing_above(k, info, passing) -> bool:
    """Along one radial chain, report only the bridge nearest the core that itself passes."""
    p = info[k]["parent"]
    while p is not None:
        if p in passing:
            return True
        p = info[p]["parent"]
    return False
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 66 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/topology.py skills/case-audit/engine/rules_stub.py skills/case-audit/tests/test_audit_stub.py
git commit -m "Add the floating EHV stub rule over an iterative bridge search"
```

---

### Task 10: Monitoring rules

**Files:**
- Create: `skills/case-audit/engine/rules_mon.py`
- Test: `skills/case-audit/tests/test_audit_rules_mon.py`

**Interfaces:**
- Consumes: `CaseData`, `findings`, `casedata.RATINGS`.
- Produces: `footprint(cd) -> dict`; `nothing_monitored(cd)`, `monitored_footprint(cd)`, `rate_set_empty(cd)`, `rate_sets_populated(cd)`, `bus_limit_overrides(cd)`, `no_contingencies(cd)`, each `-> list[Finding]`; `RATING_OF` ("A" → `LineAMVA`, "B" → `LineAMVA:1`, … "O" → `LineAMVA:14`).

The two *Stops the study* monitoring findings stop the `n1` verdict (`scope = "N-1 and SCOPF only"`; the `scopf` verdict inherits every `n1` and `opf` stop, Task 13). `mon.no_contingencies` stops `scopf` alone and runs with the `opf` profile. `rate_set_empty` looks across all closed branches, not per limit set's membership: the kit documents no field linking a branch to its limit set (open question 6). Probe values: `LSLineRateSet` / `:1` read `A` / `A` on both public cases; Texas2k carries rate sets A (5,344 branches), B and C (2,782 each).

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_rules_mon.py`:

```python
from auditcase import case
from findings import FYI, STOPS
from rules_mon import (bus_limit_overrides, monitored_footprint, no_contingencies, nothing_monitored,
                       rate_set_empty, rate_sets_populated)


def test_monitored_case_is_quiet(frames):
    cd = case(frames)
    assert nothing_monitored(cd) == [] and rate_set_empty(cd) == [] and bus_limit_overrides(cd) == []


def test_every_area_and_zone_off_stops_n1_only(frames):
    frames["Area"].BGReportLimits = "NO"
    frames["Zone"].BGReportLimits = "NO"
    [f] = nothing_monitored(case(frames))
    assert f.severity == STOPS and f.stops == ("n1",) and f.label == "Stops the study — N-1 and SCOPF only"


def test_no_element_will_monitor(frames):
    frames["Branch"]["LineMonEle:1"] = "NO"
    frames["Bus"]["BusMonEle:1"] = "NO"
    assert nothing_monitored(case(frames))[0].rule == "mon.nothing_monitored"


def test_no_contingency_records_stops_scopf_only(frames):
    assert no_contingencies(case(frames)) == []
    frames["Contingency"] = None
    [f] = no_contingencies(case(frames))
    assert f.stops == ("scopf",) and f.label == "Stops the study — SCOPF only"


def test_footprint_is_always_reported(frames):
    [f] = monitored_footprint(case(frames, LMS_IgnoreRadial="NO"))
    assert f.severity == FYI and f.details["areas"] == [{"AreaNum": 1, "min_kv": 0.0, "max_kv": 9999.0}]
    assert f.details["branches_will_monitor"] == 6 and f.details["ignore_radial"] == "NO"


def test_contingency_rate_set_with_no_ratings(frames):
    frames["LimitSet"].loc[0, "LSLineRateSet:1"] = "D"
    [f] = rate_set_empty(case(frames))
    assert f.where == [{"LSName": "Default", "rate_set": "contingency", "letter": "D"}]


def test_disabled_limit_set_is_not_checked(frames):
    frames["LimitSet"].loc[0, ["LSLineRateSet", "LSDisabled"]] = ["D", "YES"]
    assert rate_set_empty(case(frames)) == []


def test_populated_letters(frames):
    [f] = rate_sets_populated(case(frames))
    assert f.details["branches_per_letter"] == {"A": 6, "B": 6, "C": 6}
    assert f.details["amp_or_mva"] == {"Default": "MVA"}


def test_bus_with_its_own_limits(frames):
    b = frames["Bus"]
    b.loc[b.BusNum == 2, ["BusVoltLim", "BusVoltLimLow", "BusVoltLimHigh"]] = ["YES", 0.95, 1.04]
    [f] = bus_limit_overrides(case(frames))
    assert f.where == [{"BusNum": 2, "low": 0.95, "high": 1.04}]


def test_own_limits_equal_to_the_group_band_are_not_reported(frames):
    b = frames["Bus"]
    b.loc[b.BusNum == 2, ["BusVoltLim", "BusVoltLimLow", "BusVoltLimHigh"]] = ["YES", 0.89999998, 1.10000002]
    assert bus_limit_overrides(case(frames)) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_rules_mon.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'rules_mon'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/rules_mon.py`:

```python
"""Monitoring rules, reported with base; an N-1 or SCOPF depends on them (the n1 verdict)."""
from __future__ import annotations

import string

from casedata import RATINGS, CaseData
from findings import BROKEN, FYI, ON_PURPOSE, STOPS, Finding, bus

N1 = ("n1",)
N1_SCOPE = "N-1 and SCOPF only"
LETTERS = string.ascii_uppercase[:len(RATINGS)]          # A..O
RATING_OF = dict(zip(LETTERS, RATINGS))                  # "A" -> "LineAMVA", "B" -> "LineAMVA:1", ...


def footprint(cd: CaseData) -> dict:
    """The monitored footprint as the case holds it - reported so nobody reads a clean N-1 as system-wide."""
    a, z, br, b = cd.get("Area"), cd.get("Zone"), cd.get("Branch"), cd.get("Bus")

    def windows(df, key):
        on = df[df.BGReportLimits == "YES"]
        return [{key: bus(r[key]), "min_kv": r["BGReportLimMinKV"], "max_kv": r["BGReportLimMaxKV"]}
                for _, r in on.iterrows()]

    return {"areas": windows(a, "AreaNum"), "areas_total": int(len(a)),
            "zones": windows(z, "ZoneNum"), "zones_total": int(len(z)),
            "branches_will_monitor": int((br["LineMonEle:1"] == "YES").sum()),
            "buses_will_monitor": int((b["BusMonEle:1"] == "YES").sum()),
            "ignore_radial": cd.scalars.get("LMS_IgnoreRadial")}


def nothing_monitored(cd: CaseData) -> list[Finding]:
    a, z, fp = cd.get("Area"), cd.get("Zone"), footprint(cd)
    groups = list(a.BGReportLimits) + list(z.BGReportLimits)
    all_off = bool(groups) and all(v == "NO" for v in groups)
    nothing = fp["branches_will_monitor"] == 0 and fp["buses_will_monitor"] == 0
    if not (all_off or nothing):
        return []
    return [Finding(
        "mon.nothing_monitored", STOPS, BROKEN,
        what="nothing in the case is monitored" + (" (every area and zone has limit reporting off)" if all_off else ""),
        why="an N-1 on this case reports no violations whatever happens",
        page="methods/reading-violationctg.md", stops=N1, scope=N1_SCOPE, details=fp)]


def no_contingencies(cd: CaseData) -> list[Finding]:
    if len(cd.get("Contingency")):
        return []
    return [Finding(
        "mon.no_contingencies", STOPS, BROKEN,
        what="the case holds no contingency records",
        why="a SCOPF secures the dispatch against its contingency list; with none, it is a plain OPF",
        page="methods/new-device-contingency-aux.md", stops=("scopf",), scope="SCOPF only")]


def monitored_footprint(cd: CaseData) -> list[Finding]:
    fp = footprint(cd)
    return [Finding(
        "mon.footprint", FYI, ON_PURPOSE,
        what=(f"an N-1 will check {len(fp['areas'])} of {fp['areas_total']} areas, "
              f"{fp['branches_will_monitor']} branches and {fp['buses_will_monitor']} buses"),
        why="a clean N-1 result covers only this footprint, not the whole system",
        page="", details=fp)]


def _in_use(cd: CaseData) -> list[tuple[str, str, str]]:
    """(limit set, which, letter) for the normal and contingency rate set of each enabled limit set."""
    ls = cd.get("LimitSet")
    ls = ls[ls.LSDisabled != "YES"]
    return [(r["LSName"], which, str(r[f]).strip().upper())
            for _, r in ls.iterrows() for which, f in (("normal", "LSLineRateSet"), ("contingency", "LSLineRateSet:1"))]


def rate_set_empty(cd: CaseData) -> list[Finding]:
    br = cd.get("Branch")
    closed = br[br.LineStatus == "Closed"]
    empty = []
    for name, which, letter in _in_use(cd):
        col = RATING_OF.get(letter)
        if col is None or not (closed[col].fillna(0) > 0).any():
            empty.append({"LSName": name, "rate_set": which, "letter": letter})
    if not empty:
        return []
    return [Finding(
        "mon.rate_set_empty", STOPS, BROKEN,
        what="a rate set the limit monitoring uses carries no ratings: "
             + ", ".join(f"{e['LSName']} {e['rate_set']} = {e['letter']}" for e in empty),
        why="with no ratings on that set, no branch can overload in the N-1",
        page="methods/powerworld-limitset-setdata.md", stops=N1, scope=N1_SCOPE, where=empty)]


def rate_sets_populated(cd: CaseData) -> list[Finding]:
    br = cd.get("Branch")
    closed = br[br.LineStatus == "Closed"]
    carried = {letter: int((closed[col].fillna(0) > 0).sum()) for letter, col in RATING_OF.items()}
    carried = {k: v for k, v in carried.items() if v}
    ls = cd.get("LimitSet")
    return [Finding(
        "mon.rate_sets_populated", FYI, ON_PURPOSE,
        what="rate sets with values: " + (", ".join(f"{k} ({v} branches)" for k, v in carried.items()) or "none"),
        why="shows which rating letters a limit set could point at",
        page="methods/reading-violationctg.md",
        details={"branches_per_letter": carried, "closed_branches": int(len(closed)),
                 "in_use": [{"LSName": n, "rate_set": w, "letter": l} for n, w, l in _in_use(cd)],
                 "amp_or_mva": dict(zip(ls.LSName, ls.LSAmpMVA))})]


def bus_limit_overrides(cd: CaseData) -> list[Finding]:
    b = cd.get("Bus")
    own, group = b[b.BusVoltLim == "YES"], b[b.BusVoltLim != "YES"]
    if own.empty:
        return []
    if group.empty:
        diff = own
    else:
        lo, hi = group.groupby(["BusVoltLimLow", "BusVoltLimHigh"]).size().idxmax()
        rel = lambda s, ref: ((s - ref).abs() / abs(ref)) > 1e-4
        diff = own[rel(own.BusVoltLimLow, lo) | rel(own.BusVoltLimHigh, hi)]
    if diff.empty:
        return []
    return [Finding(
        "mon.bus_limit_overrides", FYI, ON_PURPOSE,
        what=f"{len(diff)} bus(es) carry their own voltage limits, different from their limit group",
        why="their violations are judged against their own band, not the case's",
        page="methods/ranking-new-devices-by-severity.md",
        where=[{"BusNum": bus(r.BusNum), "low": r.BusVoltLimLow, "high": r.BusVoltLimHigh}
               for r in diff.itertuples()])]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 76 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/rules_mon.py skills/case-audit/tests/test_audit_rules_mon.py
git commit -m "Add monitoring rules: nothing monitored, footprint, empty rate set, bus overrides"
```

---

### Task 11: Timestep rules and the weather-file reader

**Files:**
- Create: `skills/case-audit/engine/pww.py`, `skills/case-audit/engine/rules_ts.py`
- Test: `skills/case-audit/tests/test_audit_timestep.py`

**Interfaces:**
- Consumes: `CaseData`, `findings`, `summary.is_renewable`, `thresholds`; `concepts/pww-data.md` (the header layout).
- Produces: `PwwError`; `read_header(path) -> {"version", "steps", "sample_seconds", "header_bytes", "start", "end", "bounds", "stations": [(lat, lon)]}`; `renewables(cd) -> DataFrame` (adds `has_pfw`, `lat`, `lon`); `coverage(cd) -> {"renewables", "with_pfw", "installed_mw", "following_mw"}`; `pfw_missing(cd)`, `latlon_missing(cd)`, `pww_footprint(cd, pww)`, each `-> list[Finding]`.

None of these stops a time step. `pfw_missing`'s `what` begins "time step will run:" and gives the count and MW share, so the agent describes the run; its `handoff` names Auto_PFW and how many missing wind units carry a class it can use. Renewables are counted whatever their status, weighted by `GenMWMax` (open question 8). The reader was also run on the public Hawaii40 weather file: VERSION 1 (`KEY2 = 8065`), 609 stations on a 0.25° grid, 72 hourly steps, `META_STRINGS = 0`, and the station block ended exactly where `COUNT × VARCOUNT × LOC` bytes of data begin — so VERSION 1 files carry the `META_STRINGS` field too. It stops at the station list, so a year-long file costs what a day does. The test runs on the committed header and station list of that public file (Step 4), not only on the test's own writer.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_timestep.py`:

```python
import struct

import pytest

from auditcase import case
from findings import BROKEN, FYI, WORTH, YOUR_CALL
from pww import PwwError, read_header
from rules_ts import coverage, latlon_missing, pfw_missing, pww_footprint


def write_pww(path, stations, version=2):
    """A minimal .pww per concepts/pww-data.md: header, stations, and a data array."""
    codes = [102, 106]
    b = struct.pack("<hhh", 2001, 8066 if version == 2 else 8065, version)
    b += struct.pack("<dd", 45910.0, 45911.0)
    lats, lons = [s[0] for s in stations], [s[1] for s in stations]
    b += struct.pack("<dddd", min(lats), max(lats), min(lons), max(lons))
    b += struct.pack("<h", 1) + b"PowerWorld Timestep Simulation Weather\0"
    b += struct.pack("<iii", 24, 3600, len(stations)) + struct.pack("<hh", 0, len(codes))
    b += struct.pack(f"<{len(codes)}h", *codes) + struct.pack("<h", len(codes))
    if version == 2:
        b += struct.pack(f"<{len(codes)}i", *[24 * len(stations)] * len(codes))
    for lat, lon in stations:
        b += struct.pack("<ddh", lat, lon, 0) + b"+st/\0\0\0"
    b += bytes(24 * len(codes) * len(stations))
    path.write_bytes(b)
    return path


def test_header_v2_and_v1(tmp_path):
    for v in (1, 2):
        h = read_header(write_pww(tmp_path / f"w{v}.pww", [(30.0, -97.0), (30.25, -97.0)], version=v))
        assert h["version"] == v and h["steps"] == 24 and h["sample_seconds"] == 3600
        assert h["stations"] == [(30.0, -97.0), (30.25, -97.0)] and h["start"] == "2025-09-10T00:00"


def test_the_public_hawaii_weather_file_header(hawaii):
    """The header and station list of the public Hawaii40 3-day weather file, cut where its data begins."""
    p = hawaii.parent / "hawaii_konaday_header.pww"
    h = read_header(p)
    assert (h["version"], h["steps"], h["sample_seconds"], len(h["stations"])) == (1, 72, 3600, 609)
    assert h["header_bytes"] == p.stat().st_size and h["stations"][0] == (18.0, -161.0)


def test_not_a_weather_file(tmp_path):
    p = tmp_path / "x.pww"
    p.write_bytes(b"\0" * 64)
    with pytest.raises(PwwError, match="not a PowerWorld weather file"):
        read_header(p)


def test_every_renewable_follows_the_weather(frames):
    cd = case(frames)
    assert pfw_missing(cd) == [] and latlon_missing(cd) == []
    assert coverage(cd) == {"renewables": 2, "with_pfw": 2, "installed_mw": 150.0, "following_mw": 150.0}


def test_missing_pfw_says_what_the_run_will_do(frames):
    frames["Gen"].loc[1, "TSPFWModelString"] = ""
    frames["Gen"].loc[1, "GenUnitType"] = "W2 (Wind Turbine, Type 2)"
    [f] = pfw_missing(case(frames))
    assert f.severity == WORTH and f.triage == BROKEN and f.stops == ()
    assert f.what.startswith("time step will run: 1 of 2 renewables follow the weather; 1 read 0 MW")
    assert "(100 of 150 MW installed, 66.7%)" in f.what
    assert f.where == [{"BusNum": 2, "GenID": "W1", "GenFuelType": "WND (Wind)", "GenMWMax": 100.0}]
    assert f.details["missing_wind_with_class"] == 1
    assert "Auto_PFW" in f.handoff and "1 of the 1 missing wind units" in f.handoff


def test_none_string_is_not_a_model(frames):
    frames["Gen"].loc[2, "TSPFWModelString"] = "None"
    assert pfw_missing(case(frames))[0].details["missing"] == 1


def test_substation_location_counts_when_the_bus_has_none(frames):
    frames["Gen"].loc[1, ["Latitude", "Longitude"]] = [None, None]
    assert latlon_missing(case(frames)) == []


def test_zero_zero_is_no_location(frames):
    frames["Gen"].loc[1, ["Latitude:1", "Longitude:1"]] = [0.0, 0.0]
    [f] = latlon_missing(case(frames))
    assert f.where == [{"BusNum": 2, "GenID": "W1", "GenMWMax": 100.0}]


def test_no_weather_file_is_one_fyi(frames):
    [f] = pww_footprint(case(frames), None)
    assert f.severity == FYI and f.triage == YOUR_CALL
    assert f.what == "weather file not given, so I didn't check it covers these units"


def test_units_outside_the_footprint(frames, tmp_path):
    p = write_pww(tmp_path / "w.pww", [(30.0, -97.0), (30.25, -97.0)])
    [f] = pww_footprint(case(frames), str(p))
    assert f.severity == WORTH and [w["GenID"] for w in f.where] == ["S1"]
    assert f.where[0]["nearest_station_miles"] > 25


def test_file_covering_every_unit(frames, tmp_path):
    p = write_pww(tmp_path / "w.pww", [(30.0, -97.0), (30.5, -97.5)])
    [f] = pww_footprint(case(frames), str(p))
    assert f.severity == FYI and f.details["stations"] == 2


def test_unreadable_weather_file_is_fyi(frames, tmp_path):
    [f] = pww_footprint(case(frames), str(tmp_path / "missing.pww"))
    assert f.severity == FYI and "couldn't read" in f.what
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_timestep.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'pww'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/pww.py`:

```python
"""Read a .pww weather file's header and station list (concepts/pww-data.md). Header only:
the data array after the stations is never read, so a year-long file costs what a day does."""
from __future__ import annotations

import struct
from datetime import datetime, timedelta
from pathlib import Path

OLE_EPOCH = datetime(1899, 12, 30)
CHUNK = 1 << 20


class PwwError(Exception):
    """Not a PowerWorld weather file, or its header is cut short."""


class _Header:
    def __init__(self, f, name):
        self.f, self.name, self.buf, self.pos, self.base = f, name, b"", 0, 0

    @property
    def offset(self) -> int:
        return self.base + self.pos

    def _need(self, n):
        while len(self.buf) - self.pos < n:
            more = self.f.read(CHUNK)
            if not more:
                raise PwwError(f"{self.name}: header ends early")
            self.base += self.pos
            self.buf = self.buf[self.pos:] + more
            self.pos = 0

    def take(self, fmt):
        size = struct.calcsize("<" + fmt)
        self._need(size)
        v = struct.unpack_from("<" + fmt, self.buf, self.pos)
        self.pos += size
        return v if len(v) > 1 else v[0]

    def cstr(self):
        while (end := self.buf.find(b"\0", self.pos)) < 0:
            self._need(len(self.buf) - self.pos + 1)
        s = self.buf[self.pos:end].decode("latin-1")
        self.pos = end + 1
        return s


def read_header(path: str | Path) -> dict:
    path = Path(path)
    with path.open("rb") as f:
        h = _Header(f, path.name)
        key1, key2, _version = h.take("hhh")
        if key1 != 2001 or key2 not in (8065, 8066):
            raise PwwError(f"{path.name} is not a PowerWorld weather file (keys {key1}, {key2})")
        date_min, date_max = h.take("dd")
        lat_min, lat_max, lon_min, lon_max = h.take("dddd")
        for _ in range(h.take("h")):
            h.cstr()                                # description strings
        count, sample, loc = h.take("iii")
        h.take("h")                                 # LOC_FC
        varcount = h.take("h")
        for _ in range(varcount):
            h.take("h")                             # variable codes
        h.take("h")                                 # BYTECOUNT
        if key2 == 8066:
            for _ in range(varcount):
                h.take("i")                         # VERSION 2 valid counts
        stations = []
        for _ in range(loc):
            lat, lon = h.take("dd")
            h.take("h")                             # elevation
            h.cstr(), h.cstr(), h.cstr()            # who, country, region
            stations.append((lat, lon))
        header_bytes = h.offset
    return {"version": 2 if key2 == 8066 else 1, "steps": count, "sample_seconds": sample,
            "header_bytes": header_bytes,
            "start": (OLE_EPOCH + timedelta(days=date_min)).isoformat(timespec="minutes"),
            "end": (OLE_EPOCH + timedelta(days=date_max)).isoformat(timespec="minutes"),
            "bounds": {"lat": [lat_min, lat_max], "lon": [lon_min, lon_max]}, "stations": stations}
```

`skills/case-audit/engine/rules_ts.py`:

```python
"""timestep rules. TimeStep runs with any number of PFW models, so none of these stops it: they say
what the run will cover (demos/timestep-and-pfw.md, methods/timestep-simulation-setup.md)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from casedata import CaseData
from findings import BROKEN, FYI, WORTH, YOUR_CALL, Finding, bus
from pww import PwwError, read_header
from summary import is_renewable
from thresholds import PFW_MIN_CHARS, PWW_MAX_STATION_MILES, WIND_CLASSES

PAGE = "demos/timestep-and-pfw.md"
BLANK = {"", "None", "nan"}


def renewables(cd: CaseData) -> pd.DataFrame:
    g = cd.get("Gen")
    r = g[is_renewable(g.GenFuelType)].copy()
    r["has_pfw"] = r.TSPFWModelString.map(lambda s: s not in BLANK and len(s) > PFW_MIN_CHARS)
    lat, lon = _located(r)
    r["lat"], r["lon"] = lat, lon
    return r


def _valid(lat: pd.Series, lon: pd.Series) -> pd.Series:
    return lat.between(-90, 90) & lon.between(-180, 180) & ~((lat == 0) & (lon == 0))


def _located(r: pd.DataFrame):
    """The unit's own bus coordinates, else its substation's. On both public cases probed
    2026-09-30 the bus pair (Gen.Latitude) read blank on every unit and the substation pair
    (Gen.Latitude:1, "Substation Latitude" in the export) was set. Which pair TimeStep reads is
    not verified in the kit, so a unit counts as located when either pair is valid."""
    own = _valid(r.Latitude, r.Longitude)
    lat = r.Latitude.where(own, r["Latitude:1"])
    lon = r.Longitude.where(own, r["Longitude:1"])
    ok = _valid(lat, lon)
    return lat.where(ok), lon.where(ok)


def coverage(cd: CaseData) -> dict:
    r = renewables(cd)
    with_pfw = r[r.has_pfw]
    return {"renewables": int(len(r)), "with_pfw": int(len(with_pfw)),
            "installed_mw": float(r.GenMWMax.sum()), "following_mw": float(with_pfw.GenMWMax.sum())}


def _wind_class(u) -> bool:
    ci = u["CustomInteger:1"]
    return (not pd.isna(ci) and int(ci) in WIND_CLASSES) or str(u.GenUnitType)[:2] in {f"W{c}" for c in WIND_CLASSES}


def pfw_missing(cd: CaseData) -> list[Finding]:
    r = renewables(cd)
    miss = r[~r.has_pfw]
    if miss.empty:
        return []
    mw, total = float(miss.GenMWMax.sum()), float(r.GenMWMax.sum())
    wind = miss[miss.GenFuelType.str.upper().str.contains("WND")]
    classed = int(sum(_wind_class(u) for _, u in wind.iterrows()))
    return [Finding(
        "ts.pfw_missing", WORTH, BROKEN,
        what=(f"time step will run: {len(r) - len(miss)} of {len(r)} renewables follow the weather; "
              f"{len(miss)} read 0 MW for the whole run ({mw:,.0f} of {total:,.0f} MW installed, "
              f"{mw / total if total else 0:.1%})"),
        why="a renewable with no PFW model has no way to turn weather into MW, and TimeStep does not warn",
        page=PAGE,
        where=[{"BusNum": bus(u.BusNum), "GenID": u.GenID, "GenFuelType": u.GenFuelType,
                "GenMWMax": u.GenMWMax} for u in miss.itertuples()],
        details={"missing": int(len(miss)), "renewables": int(len(r)), "missing_mw": mw, "installed_mw": total,
                 "missing_wind": int(len(wind)), "missing_wind_with_class": classed},
        handoff=(f"the Auto_PFW scripts (concepts/auto-pfw-scripts.md); {classed} of the "
                 f"{len(wind)} missing wind units carry a class it can use, and it skips the rest without a "
                 f"warning; send back the _PFW copy it writes"))]


def latlon_missing(cd: CaseData) -> list[Finding]:
    r = renewables(cd)
    bad = r[r.lat.isna()]
    if bad.empty:
        return []
    return [Finding(
        "ts.latlon_missing", WORTH, BROKEN,
        what=f"{len(bad)} renewable(s) have no usable location ({bad.GenMWMax.sum():,.0f} MW installed)",
        why="their weather is looked up at the wrong place, so their output means nothing",
        page="methods/timestep-simulation-setup.md",
        where=[{"BusNum": bus(u.BusNum), "GenID": u.GenID, "GenMWMax": u.GenMWMax} for u in bad.itertuples()])]


def _miles(lat, lon, slat, slon):
    p1, p2 = np.radians(lat)[:, None], np.radians(slat)[None, :]
    dl = np.radians(slon)[None, :] - np.radians(lon)[:, None]
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def pww_footprint(cd: CaseData, pww: str | None) -> list[Finding]:
    if not pww:
        return [Finding(
            "ts.pww_footprint", FYI, YOUR_CALL,
            what="weather file not given, so I didn't check it covers these units",
            why="send the .pww if you want its coverage checked",
            page="concepts/pww-data.md")]
    try:
        hdr = read_header(pww)
    except (OSError, PwwError) as e:
        return [Finding(
            "ts.pww_footprint", FYI, YOUR_CALL,
            what="couldn't read the weather file, so its coverage was not checked",
            why=str(e), page="concepts/pww-data.md")]
    r = renewables(cd).dropna(subset=["lat", "lon"])
    st = np.array(hdr["stations"], dtype=float).reshape(-1, 2)
    if r.empty or not len(st):
        nearest = np.full(len(r), np.inf)
    else:
        nearest = np.concatenate([_miles(r.lat.values[i:i + 256], r.lon.values[i:i + 256], st[:, 0], st[:, 1]).min(axis=1)
                                  for i in range(0, len(r), 256)])
    r = r.assign(nearest_mi=nearest)
    out = r[r.nearest_mi > PWW_MAX_STATION_MILES]
    info = {"file": str(pww), "stations": int(len(st)), "start": hdr["start"], "end": hdr["end"],
            "steps": hdr["steps"], "sample_seconds": hdr["sample_seconds"], "located_units": int(len(r))}
    if out.empty:
        return [Finding("ts.pww_footprint", FYI, YOUR_CALL,
                        what=f"the weather file covers all {len(r)} located renewables",
                        why="every unit is within reach of a weather station in the file",
                        page="concepts/pww-data.md", details=info)]
    return [Finding(
        "ts.pww_footprint", WORTH, YOUR_CALL,
        what=f"{len(out)} of {len(r)} located renewables sit outside the weather file's footprint",
        why="their weather comes from a far station, and the run gives no warning",
        page="concepts/pww-data.md", details=info,
        where=[{"BusNum": bus(u.BusNum), "GenID": u.GenID, "nearest_station_miles": round(u.nearest_mi, 1)}
               for u in out.itertuples()])]
```

- [ ] **Step 4: Cut the public weather file's header into a fixture**

Run: `python -c "import sys;sys.path.insert(0,'skills/case-audit/engine');from pww import read_header;n=read_header(sys.argv[1])['header_bytes'];open(sys.argv[2],'wb').write(open(sys.argv[1],'rb').read(n));print(n)" "$HAWAII40_PWW" skills/case-audit/tests/fixtures/hawaii_konaday_header.pww`
Expected: `21407` (the header and 609 station records; the weather data after them is not kept).

- [ ] **Step 5: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 88 passed.

- [ ] **Step 6: Commit**

```bash
git add skills/case-audit/engine/pww.py skills/case-audit/engine/rules_ts.py skills/case-audit/tests/test_audit_timestep.py skills/case-audit/tests/fixtures/hawaii_konaday_header.pww
git commit -m "Add timestep rules and a header-only .pww reader: say what the run will cover"
```

---

### Task 12: OPF conditions

**Files:**
- Create: `skills/case-audit/engine/rules_opf.py`
- Test: `skills/case-audit/tests/test_audit_opf.py`

**Interfaces:**
- Consumes: `CaseData`, `findings`, `summary.is_renewable`, `summary.opf_areas`, `summary.opf_super_areas`.
- Produces: `area_table(cd) -> list[dict]` (per area: `AreaNum, BGAGC, SAName, opf, via_super_area, agc_units, with_curve, cost_above_zero, cost_models`); `opf_conditions(cd) -> list[Finding]` with rule ids `opf.1` (no area or super area on OPF), `opf.2` (an OPF area with no AGC-able unit), `opf.3` (cost data).

Written against Task 1's live OPF runs (R3): an area is an OPF area when it is on OPF or belongs (`Area.SAName`) to a super area on OPF, and an Off-AGC super area does not override a member on OPF. Condition 3 is judged **per OPF area** (architect #1, critic a1): an area whose movable units include no priced unit → `opf.3` Stops the study, `where` naming the `AreaNum`, with the cost-data handoff; unpriced units in an area that has priced ones → Worth a look, Your call, listed by `BusNum` + `GenID`. **Areas on OPF only through their super area are pooled** into one group for that super area, because the OPF moves units across it: `opf.2` and `opf.3` are judged over the whole super area (a Stop names the `SAName` and its areas), and a member area with no movable or no priced unit of its own is one FYI, Probably on purpose, never a Stop. The pooling is inferred from how the OPF dispatches, not measured (open question 12). Priced = `GenCostModel` ≠ None and `GenCostCurvePoints > 0` (R4, critic b2): a zero `GenMCost` at today's output is a price of zero, so it is no finding on wind or solar and Worth a look / Probably on purpose on a thermal unit. On Hawaii40 the 9 movable units with `GenMCost = 0` are exactly its wind and solar, so the clean case now has no `opf.3` finding; on Texas2k every area is an OPF area through super area Texas, and `opf` is READY.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_opf.py`:

```python
import pandas as pd

from auditcase import case
from findings import FYI, ON_PURPOSE, STOPS, WORTH, YOUR_CALL
from rules_opf import area_table, opf_conditions


def test_all_three_conditions_hold(frames):
    assert opf_conditions(case(frames)) == []


def test_no_opf_area_or_super_area(frames):
    frames["Area"].loc[0, "BGAGC"] = "Off AGC"
    [f] = opf_conditions(case(frames))
    assert f.rule == "opf.1" and f.severity == STOPS and f.triage == YOUR_CALL and f.stops == ("opf",)


def test_a_super_area_on_opf_counts_and_its_areas_are_checked(frames):
    # measured 2026-09-30: an OPF solved with only the super area on OPF, every area Off AGC
    frames["Area"].loc[0, ["BGAGC", "SAName"]] = ["Off AGC", "Texas"]
    frames["SuperArea"] = pd.DataFrame({"SAName": ["Texas"], "BGAGC": ["OPF"]})
    assert opf_conditions(case(frames)) == []
    frames["Gen"].GenCostCurvePoints = 0
    assert [f.rule for f in opf_conditions(case(frames))] == ["opf.3"]


def _super_area_with_a_load_only_member(frames):
    frames["Area"].loc[0, ["BGAGC", "SAName"]] = ["Off AGC", "S"]
    frames["Area"].loc[1] = {**frames["Area"].iloc[0].to_dict(), "AreaNum": 2}       # no units at all
    frames["SuperArea"] = pd.DataFrame({"SAName": ["S"], "BGAGC": ["OPF"]})


def test_a_load_only_member_of_an_opf_super_area_is_fyi_not_a_stop(frames):
    _super_area_with_a_load_only_member(frames)
    [f] = opf_conditions(case(frames))
    assert (f.rule, f.severity, f.triage) == ("opf.2", FYI, ON_PURPOSE)
    assert f.where == [{"AreaNum": 2, "SAName": "S", "movable_units": 0, "priced_units": 0}]


def test_an_unpriced_super_area_stops_as_one_group(frames):
    _super_area_with_a_load_only_member(frames)
    frames["Gen"].GenCostCurvePoints = 0
    [f] = opf_conditions(case(frames))
    assert (f.rule, f.severity) == ("opf.3", STOPS) and f.where == [{"SAName": "S", "areas": [1, 2], "movable_units": 3}]
    assert "super area S" in f.what


def test_an_area_on_opf_inside_a_super_area_off_agc_counts(frames):
    # measured 2026-09-30: the OPF solved with the area on OPF and its super area Off AGC
    frames["Area"].loc[0, "SAName"] = "FullCase"
    frames["SuperArea"] = pd.DataFrame({"SAName": ["FullCase"], "BGAGC": ["Off AGC"]})
    assert opf_conditions(case(frames)) == []


def test_opf_area_with_no_agc_unit(frames):
    frames["Gen"].GenAGCAble = "NO"
    [f] = opf_conditions(case(frames))
    assert f.rule == "opf.2" and f.details["agc_off_everywhere"] and "dispatch" in f.why


def test_one_unpriced_area_stops_even_when_another_is_priced(frames):
    frames["Area"].loc[1] = {**frames["Area"].iloc[0].to_dict(), "AreaNum": 2}
    frames["Gen"].loc[0, ["AreaNum", "GenCostCurvePoints"]] = [2, 0]      # area 2's only unit: no curve
    [f] = opf_conditions(case(frames))
    assert f.rule == "opf.3" and f.severity == STOPS and f.where == [{"AreaNum": 2, "movable_units": 1}]
    assert "cost-data source" in f.handoff


def test_cost_model_none_is_no_data(frames):
    frames["Gen"].GenCostModel = "None"
    assert opf_conditions(case(frames))[0].severity == STOPS


def test_an_unpriced_unit_beside_priced_ones_is_worth_a_look(frames):
    frames["Gen"].loc[0, "GenCostCurvePoints"] = 0
    [f] = opf_conditions(case(frames))
    assert (f.rule, f.severity, f.triage) == ("opf.3", WORTH, YOUR_CALL) and [w["GenID"] for w in f.where] == ["1"]


def test_zero_cost_renewables_are_priced(frames):
    frames["Gen"].loc[[1, 2], "GenMCost"] = 0.0                  # wind and solar: curve points, price 0
    assert opf_conditions(case(frames)) == []


def test_a_thermal_unit_at_zero_cost_is_probably_on_purpose(frames):
    frames["Gen"].loc[0, "GenMCost"] = 0.0
    [f] = opf_conditions(case(frames))
    assert (f.rule, f.severity, f.triage) == ("opf.3", WORTH, ON_PURPOSE) and f.handoff == ""


def test_area_table(frames):
    [a] = area_table(case(frames))
    assert a == {"AreaNum": 1, "BGAGC": "OPF", "SAName": "", "opf": True, "via_super_area": False,
                 "agc_units": 3, "with_curve": 3, "cost_above_zero": 3, "cost_models": {"Cubic": 3}}
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_opf.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'rules_opf'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/rules_opf.py`:

```python
"""opf rules: the three conditions PowerWorld needs before an OPF will run
(concepts/opf-preconditions.md). Checked separately, per OPF group: an area on OPF itself is its own
group; areas on OPF only through their super area are pooled into one group for that super area,
because the OPF moves units across it. The pooling is inferred from how the OPF dispatches, not
measured on a case with an empty member area."""
from __future__ import annotations

import pandas as pd

from casedata import CaseData
from findings import FYI, ON_PURPOSE, STOPS, WORTH, YOUR_CALL, Finding, bus
from summary import is_renewable, opf_areas, opf_super_areas

PAGE = "concepts/opf-preconditions.md"
OPF = ("opf",)
COST_HANDOFF = "your own cost-data source; no script supplies cost curves, and a default one makes the dispatch meaningless"


def _units(cd: CaseData) -> pd.DataFrame:
    g = cd.get("Gen")
    g = g[g.GenStatus == "Closed"].copy()
    g["agc"] = g.GenAGCAble == "YES"
    g["renewable"] = is_renewable(g.GenFuelType)
    # priced = a cost model and a fitted curve. GenMCost is the curve at today's output, so a
    # zero there is a price of zero (wind, solar), not missing data.
    g["priced"] = (g.GenCostModel.str.upper() != "NONE") & (g.GenCostModel != "") & (g.GenCostCurvePoints > 0)
    return g


def area_table(cd: CaseData) -> list[dict]:
    """Per area: may the OPF redispatch it, and what its units carry. The agent shows this table."""
    g, on_opf, sa_on = _units(cd), opf_areas(cd), set(opf_super_areas(cd))
    rows = []
    for _, a in cd.get("Area").iterrows():
        u = g[(g.AreaNum == a.AreaNum) & g.agc]
        rows.append({"AreaNum": bus(a.AreaNum), "BGAGC": a.BGAGC, "SAName": a.SAName,
                     "opf": a.AreaNum in on_opf, "via_super_area": a.BGAGC.upper() != "OPF" and a.SAName in sa_on,
                     "agc_units": int(len(u)), "with_curve": int(u.priced.sum()),
                     "cost_above_zero": int((u.GenMCost > 0).sum()),
                     "cost_models": {str(k): int(v) for k, v in u.GenCostModel.value_counts().items()}})
    return rows


def _units_where(df) -> list[dict]:
    return [{"BusNum": bus(u.BusNum), "GenID": u.GenID, "AreaNum": bus(u.AreaNum), "GenCostModel": u.GenCostModel,
             "GenCostCurvePoints": u.GenCostCurvePoints, "GenMCost": u.GenMCost} for u in df.itertuples()]


def _groups(cd: CaseData) -> dict:
    """OPF group -> its areas. ("area", n) for an area on OPF itself; ("super area", name) for the
    areas on OPF only through their super area."""
    a, on = cd.get("Area"), opf_areas(cd)
    groups = {}
    for _, r in a[a.AreaNum.isin(on)].iterrows():
        key = ("area", bus(r.AreaNum)) if r.BGAGC.upper() == "OPF" else ("super area", r.SAName)
        groups.setdefault(key, []).append(r.AreaNum)
    return groups


def _where(key, areas) -> dict:
    return {"AreaNum": key[1]} if key[0] == "area" else {"SAName": key[1], "areas": sorted(bus(x) for x in areas)}


def _name(key) -> str:
    return f"area {key[1]}" if key[0] == "area" else f"super area {key[1]}"


def opf_conditions(cd: CaseData) -> list[Finding]:
    groups, g = _groups(cd), _units(cd)
    if not groups:
        return [Finding(
            "opf.1", STOPS, YOUR_CALL,
            what="no area or super area is set to let the OPF redispatch it",
            why="the OPF will not start: which areas it may move is your study choice",
            page=PAGE, stops=OPF)]
    out, empty, unpriced, thin, movable_all = [], [], [], [], []
    for key, areas in groups.items():
        movable = g[g.AreaNum.isin(areas) & g.agc]
        movable_all.append(movable)
        if movable.empty:
            empty.append((key, _where(key, areas)))
        elif not movable.priced.any():
            unpriced.append((key, {**_where(key, areas), "movable_units": int(len(movable))}))
        elif key[0] == "super area":
            for a in areas:                     # a member with nothing of its own is covered by the pool
                own = movable[movable.AreaNum == a]
                if own.empty or not own.priced.any():
                    thin.append({"AreaNum": bus(a), "SAName": key[1], "movable_units": int(len(own)),
                                 "priced_units": int(own.priced.sum())})
    if empty:
        all_off = not g.agc.any()
        out.append(Finding(
            "opf.2", STOPS, YOUR_CALL,
            what="no unit the OPF may move in " + ", ".join(_name(k) for k, _ in empty),
            why=("AGC is off on every unit; writing GenMW turns it off, so a dispatch step is the likely cause"
                 if all_off else "an OPF group with no AGC-able unit gives the OPF nothing to redispatch"),
            page=PAGE, stops=OPF, where=[w for _, w in empty], details={"agc_off_everywhere": all_off}))
    if unpriced:
        out.append(Finding(
            "opf.3", STOPS, YOUR_CALL,
            what="no cost data on any unit the OPF could move in " + ", ".join(_name(k) for k, _ in unpriced),
            why="an OPF needs real cost curves there; switching a cost model on without them gives a meaningless dispatch",
            page=PAGE, stops=OPF, where=[w for _, w in unpriced], handoff=COST_HANDOFF))
    if thin:
        out.append(Finding(
            "opf.2", FYI, ON_PURPOSE,
            what=f"{len(thin)} member area(s) of an OPF super area have no movable or no priced unit of their own",
            why="the OPF moves units across the whole super area, so the rest of it covers them",
            page=PAGE, where=thin))
    movable = pd.concat(movable_all)
    priced_groups = movable.groupby(movable.AreaNum.map({a: k for k, v in groups.items() for a in v})).priced.transform("any")
    bare = movable[~movable.priced & priced_groups]
    if not bare.empty:
        out.append(Finding(
            "opf.3", WORTH, YOUR_CALL,
            what=f"{len(bare)} of the {len(movable)} units the OPF could move carry no cost curve",
            why="the OPF runs on the priced units; these ones have no price to be dispatched on",
            page=PAGE, where=_units_where(bare), handoff=COST_HANDOFF,
            details={"units": int(len(movable)), "priced": int(movable.priced.sum())}))
    free = movable[movable.priced & (movable.GenMCost <= 0) & ~movable.renewable]
    if not free.empty:
        out.append(Finding(
            "opf.3", WORTH, ON_PURPOSE,
            what=f"{len(free)} thermal unit(s) the OPF could move have a cost curve that reads 0 at today's output",
            why="the OPF will treat their next MW as free; check the curve if that is not intended",
            page=PAGE, where=_units_where(free)))
    return out
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 101 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/rules_opf.py skills/case-audit/tests/test_audit_opf.py
git commit -m "Add the three OPF conditions, per area, with super areas as measured"
```

---

### Task 13: Verdicts and the two findings files

**Files:**
- Create: `skills/case-audit/engine/checks.py`, `skills/case-audit/engine/report.py`
- Test: `skills/case-audit/tests/test_audit_report.py`

**Interfaces:**
- Consumes: every rule module; `summary.case_summary`; `rules_mon.footprint`; `rules_opf.area_table`; `rules_ts.coverage`.
- Produces: `RULES` (18 entries: id, profile, needs a solve, function), `VALID_PROFILES = ("base", "timestep", "opf")`; `run_rules(cd, profiles, pww) -> (findings, ran, skipped)`; `verdicts(findings, profiles, ts_coverage, contingencies) -> {profile: {"verdict", "reason", "stopped_by"}}` with keys `base`, `n1`, then `timestep` / `opf` when asked, and `scopf` whenever `opf` is (it is NOT READY on anything that stops `opf`, `n1` or `scopf`); `report.build(cd, profiles, pww=None, source="case") -> dict`; `report.render_md(result) -> str`; `report.write(result, out) -> (json_path, md_path)`; `report.REPLAYED`.

`findings.json` keys: `source` (`case` or `snapshot`), `case, audited_at, profiles, weather_file, read_only{sha256_before, sha256_after, unchanged}` (all `null` on a replay, R1), `variants_beside, solve` (with `tolerance_unread`), `verdicts, case_summary, monitoring, timestep_coverage, opf_areas, findings[]` (each with `handoff`), `rules_run, rules_skipped`. `findings.md` sections, in the agent's order: the replay line (replays only), `## Verdict`, `## What's in the case` (a line when the case did not solve; `N-1 will check:` with the areas, the kV window and the counts), `## Findings`, `## Can the OPF run?` (opf only; says when an area is on OPF through its super area), `## What you need to get` (one numbered line per handoff), `## Not checked` (when anything was skipped), `## Every object, per finding`. The seeded-defects test is spec §10's auditor row.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_report.py`:

```python
import json

from auditcase import case
from casedata import CaseData, Solve
import report

ALL = ["base", "timestep", "opf"]


def rules(r):
    return sorted({(f["rule"], f["severity"]) for f in r["findings"]})


def test_clean_hawaii40_is_ready_for_every_profile(hawaii):
    r = report.build(CaseData.from_json(hawaii), ALL)
    assert {p: v["verdict"] for p, v in r["verdicts"].items()} == {
        "base": "READY", "n1": "READY", "timestep": "READY", "opf": "READY", "scopf": "READY"}
    assert r["verdicts"]["timestep"]["reason"] == "9 of 9 renewables will follow the weather"
    assert rules(r) == [("base.stale_ctg_results", "FYI"), ("mon.footprint", "FYI"),
                        ("mon.rate_sets_populated", "FYI"), ("ts.pww_footprint", "FYI")]


def test_seeded_defects_are_reported_and_nothing_new(hawaii):
    clean = report.build(CaseData.from_json(hawaii), ALL)
    cd = CaseData.from_json(hawaii)
    g, sh = cd.frames["Gen"], cd.frames["Shunt"]
    ren = g.index[g.GenFuelType.str.contains("WND|SUN")][:3]
    g.loc[ren, "TSPFWModelString"] = ""                       # strip PFW from 3 units
    sh.loc[0, "SSRegNum"] = 0                                 # zero the one switched shunt's regulated bus
    g.loc[g.GenAGCAble == "YES", "GenCostModel"] = "None"     # no cost model on any movable unit
    r = report.build(cd, ALL)
    new = set(rules(r)) - set(rules(clean))
    assert new == {("ts.pfw_missing", "Worth a look"), ("base.regulates_nothing", "Worth a look"),
                   ("opf.3", "Stops the study")}
    pfw = next(f for f in r["findings"] if f["rule"] == "ts.pfw_missing")
    assert pfw["count"] == 3 and r["verdicts"]["timestep"]["verdict"] == "READY"
    assert r["verdicts"]["opf"]["verdict"] == "NOT READY" and r["verdicts"]["base"]["verdict"] == "READY"
    assert r["verdicts"]["scopf"]["verdict"] == "NOT READY"


def test_unsolved_case_is_not_ready_and_says_what_was_not_checked(frames):
    r = report.build(case(frames, converged=False), ALL)
    assert all(v["verdict"] == "NOT READY" for v in r["verdicts"].values())
    assert {s["rule"] for s in r["rules_skipped"]} == {
        "base.gen_over_nameplate", "base.ltc_regulates_lv_side", "base.floating_stub"}
    assert r["case_summary"]["from_unsolved_case"] and "did not solve" in report.render_md(r)


def test_an_unread_tolerance_is_decided_on_the_raise_and_recorded(frames):
    cd = CaseData(frames, {"SBase": "100", "ChkTaps": "YES"}, Solve(True, None, 0.01, None))
    r = report.build(cd, ["base"])
    assert r["verdicts"]["base"]["verdict"] == "READY" and r["solve"]["tolerance_unread"]


def test_base_always_runs_and_n1_is_always_reported(frames):
    r = report.build(case(frames), ["timestep"])
    assert r["profiles"] == ["base", "timestep"] and list(r["verdicts"]) == ["base", "n1", "timestep"]
    assert r["opf_areas"] is None


def test_scopf_needs_a_contingency_list(frames):
    frames["Contingency"] = None
    r = report.build(case(frames), ["opf"])
    assert r["verdicts"]["opf"]["verdict"] == "READY" and r["verdicts"]["scopf"]["verdict"] == "NOT READY"
    assert r["verdicts"]["scopf"]["stopped_by"] == ["mon.no_contingencies"]


def test_a_replay_says_it_opened_no_case(frames):
    r = report.build(case(frames), ["base"], source="snapshot")
    assert r["source"] == "snapshot" and r["read_only"] == {"sha256_before": None, "sha256_after": None,
                                                            "unchanged": None}
    assert report.render_md(r).splitlines()[0] == "Replayed from a stored snapshot; no case was opened."


def test_handoffs_become_what_you_need_to_get(frames):
    frames["Gen"].loc[1, "TSPFWModelString"] = ""
    md = report.render_md(report.build(case(frames), ["timestep"]))
    assert "## What you need to get" in md and "1. time step will run" in md and "Auto_PFW" in md


def test_files_are_utf8_whatever_the_names(frames, tmp_path):
    frames["Bus"].loc[2, "BusName"] = "Kāneʻohe 345"
    frames["Bus"].loc[frames["Bus"].BusNum == 3, "BusPUVolt"] = 1.13
    frames["Branch"].loc[3, ["LineTap", "XFRegError"]] = [1.1, 0.003]
    j, m = report.write(report.build(case(frames), ALL), tmp_path)
    text = m.read_text(encoding="utf-8")
    assert "Kāneʻohe 345" in text and "## Verdict" in text and "## What's in the case" in text
    assert "N-1 will check: areas 1 (of 1), all kV" in text and "## Can the OPF run?" in text
    assert json.loads(j.read_text(encoding="utf-8"))["findings"]


def test_json_never_carries_nan(frames, tmp_path):
    frames["Gen"].loc[0, "GenMVRMin"] = float("nan")
    j, _ = report.write(report.build(case(frames), ALL), tmp_path)
    assert "NaN" not in j.read_text(encoding="utf-8")
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_report.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'report'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/checks.py`:

```python
"""Which rules run for which profiles, and the verdict each requested study gets."""
from __future__ import annotations

from casedata import CaseData
from findings import STOPS, Finding
import rules_base as B
import rules_mon as M
import rules_opf as O
import rules_reg as R
import rules_stub as S
import rules_ts as T

# (rule id, profile, needs a converged AC solve, function(cd, pww) -> list[Finding])
RULES = [
    ("base.ac_converges", "base", False, lambda cd, pww: B.ac_converges(cd)),
    ("base.dc_skeleton", "base", False, lambda cd, pww: B.dc_skeleton(cd)),
    ("base.gen_over_nameplate", "base", True, lambda cd, pww: B.gen_over_nameplate(cd)),
    ("base.regulates_nothing", "base", False, lambda cd, pww: R.regulates_nothing(cd)),
    ("base.ltc_middle_target", "base", False, lambda cd, pww: R.ltc_middle_target(cd)),
    ("base.ltc_regulates_lv_side", "base", True, lambda cd, pww: R.ltc_regulates_lv_side(cd)),
    ("base.floating_stub", "base", True, lambda cd, pww: S.floating_stub(cd)),
    ("base.stale_ctg_results", "base", False, lambda cd, pww: B.stale_ctg_results(cd)),
    ("mon.nothing_monitored", "base", False, lambda cd, pww: M.nothing_monitored(cd)),
    ("mon.footprint", "base", False, lambda cd, pww: M.monitored_footprint(cd)),
    ("mon.rate_set_empty", "base", False, lambda cd, pww: M.rate_set_empty(cd)),
    ("mon.rate_sets_populated", "base", False, lambda cd, pww: M.rate_sets_populated(cd)),
    ("mon.bus_limit_overrides", "base", False, lambda cd, pww: M.bus_limit_overrides(cd)),
    ("mon.no_contingencies", "opf", False, lambda cd, pww: M.no_contingencies(cd)),
    ("ts.pfw_missing", "timestep", False, lambda cd, pww: T.pfw_missing(cd)),
    ("ts.latlon_missing", "timestep", False, lambda cd, pww: T.latlon_missing(cd)),
    ("ts.pww_footprint", "timestep", False, lambda cd, pww: T.pww_footprint(cd, pww)),
    ("opf.conditions", "opf", False, lambda cd, pww: O.opf_conditions(cd)),
]
VALID_PROFILES = ("base", "timestep", "opf")


def run_rules(cd: CaseData, profiles: list[str], pww: str | None = None):
    """-> (findings, rules run, rules skipped with the reason). base always runs."""
    want = {"base", *profiles}
    findings, ran, skipped = [], [], []
    for rule, profile, needs_solve, fn in RULES:
        if profile not in want:
            continue
        if needs_solve and not cd.solve.converged:
            skipped.append({"rule": rule, "reason": "needs a solved AC power flow, and it did not solve"})
            continue
        findings += fn(cd, pww)
        ran.append(rule)
    return findings, ran, skipped


def verdicts(findings: list[Finding], profiles: list[str], ts_coverage: dict | None = None,
             contingencies: int | None = None) -> dict:
    """READY or NOT READY per study. n1 is the monitoring verdict reported with base; scopf comes
    with opf and needs everything opf and n1 need, plus a contingency list."""
    order = ["base", "n1"] + [p for p in ("timestep", "opf") if p in profiles] + (["scopf"] if "opf" in profiles else [])
    needs = {"scopf": {"opf", "n1", "scopf"}}
    out = {}
    for p in order:
        stop = [f for f in findings if f.severity == STOPS and needs.get(p, {p}) & set(f.stops)]
        if stop:
            out[p] = {"verdict": "NOT READY", "reason": stop[0].what, "stopped_by": [f.rule for f in stop]}
        else:
            reason = ""
            if p == "timestep" and ts_coverage:
                c = ts_coverage
                reason = f"{c['with_pfw']} of {c['renewables']} renewables will follow the weather"
            if p == "n1":
                reason = "monitoring only; the runner counts outage coverage"
            if p == "scopf":
                reason = f"{contingencies} contingencies in the case; the runner counts outage coverage"
            out[p] = {"verdict": "READY", "reason": reason, "stopped_by": []}
    return out
```

`skills/case-audit/engine/report.py`:

````python
"""Build the audit result and write findings.json and findings.md (UTF-8, whatever the console)."""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from casedata import CaseData
from checks import run_rules, verdicts
from findings import clean
from rules_mon import footprint
from rules_opf import area_table
from rules_ts import coverage
from summary import case_summary

REPLAYED = "Replayed from a stored snapshot; no case was opened."


def build(cd: CaseData, profiles: list[str], pww: str | None = None, source: str = "case") -> dict:
    """source = "case" for a live read; "snapshot" for a replay, which proves nothing about a file."""
    profiles = [p for p in profiles if p != "base"]
    findings, ran, skipped = run_rules(cd, profiles, pww)
    ts = coverage(cd) if "timestep" in profiles else None
    live = source == "case"
    before, after = cd.scalars.get("sha256_before"), cd.scalars.get("sha256_after")
    return clean({
        "source": source,
        "case": cd.scalars.get("case_path"),
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "profiles": ["base", *profiles],
        "weather_file": pww,
        "read_only": ({"sha256_before": before, "sha256_after": after, "unchanged": before == after} if live
                      else {"sha256_before": None, "sha256_after": None, "unchanged": None}),
        "variants_beside": cd.scalars.get("variants_beside", []),
        "solve": {"converged": cd.solve.converged, "raised": cd.solve.raised,
                  "max_mismatch_mva": cd.solve.max_mismatch_mva, "tolerance_mva": cd.solve.tolerance_mva,
                  "tolerance_unread": cd.solve.tolerance_unread},
        "verdicts": verdicts(findings, profiles, ts, len(cd.get("Contingency"))),
        "case_summary": case_summary(cd, opf="opf" in profiles),
        "monitoring": footprint(cd),
        "timestep_coverage": ts,
        "opf_areas": area_table(cd) if "opf" in profiles else None,
        "findings": [f.to_dict() for f in findings],
        "rules_run": ran,
        "rules_skipped": skipped,
    })


def _n(x, digits=0) -> str:
    return "—" if x is None else f"{x:,.{digits}f}"


def _kv(windows: list[dict]) -> str:
    lo = min((w["min_kv"] for w in windows if w["min_kv"] is not None), default=None)
    hi = max((w["max_kv"] for w in windows if w["max_kv"] is not None), default=None)
    if lo is None or hi is None:
        return "kV window not read"
    return "all kV" if lo <= 0 and hi >= 9999 else f"{lo:g}–{hi:g} kV"


def render_md(r: dict) -> str:
    s, L = r["case_summary"], []
    if r["source"] == "snapshot":
        L += [REPLAYED, ""]
    unchanged = {True: "yes", False: "NO", None: "not checked (no case was opened)"}[r["read_only"]["unchanged"]]
    L += ["# Case audit", "", f"Case checked: `{r['case']}`  ", f"Audited: {r['audited_at']}  ",
          f"Case file unchanged by the audit: {unchanged}"]
    if r["variants_beside"]:
        L.append(f"Other versions beside it (not audited): {', '.join(r['variants_beside'])}")
    L += ["", "## Verdict"]
    for p, v in r["verdicts"].items():
        L.append(f"- {p}: {v['verdict']}" + (f" — {v['reason']}" if v["reason"] else ""))
    L += ["", "## What's in the case"]
    if s["from_unsolved_case"]:
        L += ["The AC power flow did not solve, so these are the case's stored values, not a solution.", ""]
    L += ["| | MW | Mvar |", "|---|---|---|",
          f"| Load | {_n(s['load_mw'])} | {_n(s['load_mvar'])} |",
          f"| Generation (online) | {_n(s['generation_mw'])} | {_n(s['generation_mvar'])} |",
          f"| Losses | {_n(s['losses_mw'])} | |",
          f"| Headroom on online units (dispatchable) | {_n(s['headroom_dispatchable_mw'])} | |",
          f"| Online Mvar range | | {_n(s['mvar_range'][0])} to {_n(s['mvar_range'][1])} |"]
    if s["generation_includes_overshoot_mw"]:
        L.append(f"\nGeneration includes {_n(s['generation_includes_overshoot_mw'], 1)} MW above unit ratings.")
    L += ["", "| fuel (as the case labels it) | units online / total | installed MW | output MW | share of output | headroom MW |",
          "|---|---|---|---|---|---|"]
    for f in s["fuel"]:
        head = "0 (weather-limited)" if f["weather_limited"] else _n(f["headroom_mw"])
        L.append(f"| {f['fuel']} | {f['units_online']}/{f['units_total']} | {_n(f['installed_mw'])} | "
                 f"{_n(f['output_mw'])} | {f['share_of_output']:.0%} | {head} |")
    sh, z = s["shunts"], s["size"]
    L += ["", "| shunts | in service | Mvar now | capacitive capacity | inductive capacity |", "|---|---|---|---|---|",
          f"| {sh['count']} | {sh['in_service']} | {_n(sh['mvar_now'])} | {_n(sh['capacitive_mvar'])} | {_n(sh['inductive_mvar'])} |",
          "", f"Size: {z['buses']:,} buses, {z['branches']:,} branches ({z['transformers']:,} transformers), "
              f"{z['areas']} areas, {z['zones']} zones; kV levels {', '.join(f'{k:g}' for k in z['kv_levels'])}."]
    m = r["monitoring"]
    areas = ", ".join(str(a["AreaNum"]) for a in m["areas"]) or "none"
    L += ["", f"N-1 will check: areas {areas} (of {m['areas_total']}), {_kv(m['areas'] + m['zones'])}, "
              f"{m['branches_will_monitor']:,} branches / {m['buses_will_monitor']:,} buses (the case's own setup)."]
    if "opf_movable_headroom_mw" in s:
        L.append(f"Headroom on dispatchable units the OPF may move: {_n(s['opf_movable_headroom_mw'])} MW.")
    L += ["", "## Findings",
          "| what's wrong | where (keys) | why it matters | stops the study? | Broken / Probably on purpose / Your call | rule | kit page |",
          "|---|---|---|---|---|---|---|"]
    for f in r["findings"]:
        where = f"{f['count']} object(s), listed below" if f["count"] else "—"
        L.append(f"| {f['what']} | {where} | {f['why']} | {f['label']} | {f['triage']} | {f['rule']} | {f['page'] or '—'} |")
    if r["opf_areas"] is not None:
        L += ["", "## Can the OPF run?",
              "| area | OPF may redispatch it | units the OPF may move | with a cost curve | with a cost above 0 at today's output | cost model types |",
              "|---|---|---|---|---|---|"]
        for a in r["opf_areas"]:
            models = ", ".join(f"{k} {v}" for k, v in a["cost_models"].items()) or "—"
            how = f"yes (super area {a['SAName']} on OPF)" if a["via_super_area"] else f"{'yes' if a['opf'] else 'no'} ({a['BGAGC']})"
            L.append(f"| {a['AreaNum']} | {how} | {a['agc_units']} | {a['with_curve']} | {a['cost_above_zero']} | {models} |")
    handoffs = [f for f in r["findings"] if f["handoff"]]
    if handoffs:
        L += ["", "## What you need to get"]
        L += [f"{i}. {f['what']} → {f['handoff']} → then send the returned case to be checked again"
              for i, f in enumerate(handoffs, 1)]
    if r["rules_skipped"]:
        L += ["", "## Not checked"] + [f"- {x['rule']}: {x['reason']}" for x in r["rules_skipped"]]
    L += ["", "## Every object, per finding"]
    for f in r["findings"]:
        if f["where"]:
            L += ["", f"### {f['rule']} — {f['label']} — {f['triage']}", "",
                  "```json", *[json.dumps(w, ensure_ascii=False) for w in f["where"]], "```"]
    return "\n".join(L) + "\n"


def write(r: dict, out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    j, m = out / "findings.json", out / "findings.md"
    j.write_text(json.dumps(r, indent=1, ensure_ascii=False, allow_nan=False), encoding="utf-8")
    m.write_text(render_md(r), encoding="utf-8")
    return j, m
````

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 111 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/engine/checks.py skills/case-audit/engine/report.py skills/case-audit/tests/test_audit_report.py
git commit -m "Add verdicts per study and the findings.json / findings.md writer"
```

---

### Task 14: The audit CLI

**Files:**
- Create: `skills/case-audit/engine/audit.py`
- Test: `skills/case-audit/tests/test_audit_cli.py`

**Interfaces:**
- Consumes: `reader.read_case`, `report`; the stand-in esapp (Task 5) in the tests.
- Produces: `python <KIT>/skills/case-audit/engine/audit.py --case <pwb> [--profiles base,timestep,opf] [--pww <file>] [--out <dir>]` — no snapshot flags (R1). `--out` defaults to `./case-audit/<case stem>/` under the working folder, which gets its `.gitignore` of `*` **before anything else is written** — findings, or an error log carrying the case's full path (R2; `test_a_failure_in_the_default_folder_is_ignored_too`); the findings path is printed once. Exit 0 = both files written (whatever the verdicts); 2 = nothing audited, with three plain lines on stderr (what broke and whose problem, what it means, the one thing to do) and the traceback in `<out>/audit_error.log`. That holds for a bad argument too (argparse's `error` is overridden) and for a missing dependency: the module imports only the standard library, and the engine is imported inside `main` under `try`, pointing at `/powerworld-hivemind:powerworld-setup` (critic b4). `main(argv=None) -> int`; `default_out(case) -> Path`; `VALID_PROFILES` (the test pins it to `checks.VALID_PROFILES`). `base` always runs; repeated profiles are dropped.

The tests drive the real `--case` → reader path (critic b5): in process with the `fake_esapp` fixture and `monkeypatch.chdir`, and as a subprocess with the stand-in on `PYTHONPATH` for the cp1252 console and the run from outside the kit. The cp1252 test writes into a folder named `Kāneʻohe audit`; with the two `reconfigure` lines removed it fails (checked on the dry run), so it tests what it names.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_cli.py`:

```python
"""The CLI end to end on the real --case path, with the stand-in esapp serving Hawaii40."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

import audit
import checks

AUDIT = Path(__file__).resolve().parents[1] / "engine" / "audit.py"
FAKE = Path(__file__).resolve().parent / "fake_esapp"


def _case(tmp_path):
    p = tmp_path / "Hawaii40_base.pwb"
    p.write_bytes(b"stand-in case file")
    return p


def test_default_out_is_under_the_working_folder_and_ignored(fake_esapp, tmp_path, monkeypatch, capsys):
    monkeypatch.chdir(tmp_path)
    assert audit.main(["--case", str(_case(tmp_path)), "--profiles", "base,timestep,opf"]) == 0
    out = tmp_path / "case-audit" / "Hawaii40_base"
    r = json.loads((out / "findings.json").read_text(encoding="utf-8"))
    assert r["source"] == "case" and r["read_only"]["unchanged"] is True
    assert (out / ".gitignore").read_text(encoding="utf-8") == "*\n"
    printed = capsys.readouterr().out
    assert "base READY; n1 READY; timestep READY; opf READY; scopf READY" in printed
    assert printed.count(str(out)) == 1


def test_profiles_are_deduplicated(fake_esapp, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert audit.main(["--case", str(_case(tmp_path)), "--profiles", "timestep,timestep", "--out", "o"]) == 0
    assert json.loads((tmp_path / "o" / "findings.json").read_text(encoding="utf-8"))["profiles"] == ["base", "timestep"]


def test_unknown_profile_is_three_plain_lines(capsys):
    with pytest.raises(SystemExit) as e:
        audit.main(["--case", "x.pwb", "--profiles", "base,n2"])
    lines = capsys.readouterr().err.strip().splitlines()
    assert e.value.code == 2 and len(lines) == 3 and "unknown profile n2" in lines[0]


def test_missing_case_breaks_in_three_plain_lines(tmp_path, capsys):
    assert audit.main(["--case", str(tmp_path / "gone.pwb"), "--out", str(tmp_path)]) == 2
    lines = capsys.readouterr().err.strip().splitlines()
    assert len(lines) == 3 and "case not found" in lines[0] and "untouched" in lines[1]
    assert "audit_error.log" in lines[2]


def test_a_failure_in_the_default_folder_is_ignored_too(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    assert audit.main(["--case", str(tmp_path / "gone.pwb")]) == 2
    out = tmp_path / "case-audit" / "gone"
    assert (out / "audit_error.log").is_file() and (out / ".gitignore").read_text(encoding="utf-8") == "*\n"


def test_a_missing_dependency_points_at_setup(tmp_path, monkeypatch, capsys):
    monkeypatch.setitem(sys.modules, "report", None)             # import report -> ImportError
    assert audit.main(["--case", "x.pwb", "--out", str(tmp_path)]) == 2
    err = capsys.readouterr().err
    assert "powerworld-setup" in err and "Traceback" not in err


def test_the_cli_and_the_engine_agree_on_profiles():
    assert audit.VALID_PROFILES == checks.VALID_PROFILES


def _run(tmp_path, *args, cwd, **env):
    e = {**os.environ, "PYTHONPATH": str(FAKE), "PWHM_FAKE_SNAPSHOT": str(Path(__file__).parent / "fixtures" / "hawaii40.json.gz"), **env}
    p = subprocess.run([sys.executable, str(AUDIT), *map(str, args)], capture_output=True, cwd=cwd, env=e)
    return p.returncode, p.stdout.decode("utf-8", "replace"), p.stderr.decode("utf-8", "replace")


def test_runs_from_outside_the_kit(tmp_path):
    code, out, err = _run(tmp_path, "--case", _case(tmp_path), cwd=tmp_path)
    assert code == 0, err
    assert (tmp_path / "case-audit" / "Hawaii40_base" / "findings.md").is_file()


def test_survives_a_cp1252_console_with_a_non_ascii_folder(tmp_path):
    out = tmp_path / "Kāneʻohe audit"
    code, printed, err = _run(tmp_path, "--case", _case(tmp_path), "--out", out, cwd=tmp_path,
                              PYTHONIOENCODING="cp1252")
    assert code == 0, err
    assert "Kāneʻohe audit" in printed


LIVE = os.environ.get("PWHM_LIVE_CASE")


@pytest.mark.skipif(not LIVE, reason="set PWHM_LIVE_CASE to a public synthetic .pwb to run against PowerWorld")
def test_live_audit_leaves_the_case_byte_identical(tmp_path):
    p = subprocess.run([sys.executable, str(AUDIT), "--case", LIVE, "--profiles", "base,timestep,opf",
                        "--out", str(tmp_path)], capture_output=True)
    assert p.returncode == 0, p.stderr.decode("utf-8", "replace")
    r = json.loads((tmp_path / "findings.json").read_text(encoding="utf-8"))
    assert r["read_only"]["unchanged"] and r["read_only"]["sha256_before"] and r["solve"]["converged"]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_cli.py -q -p no:cacheprovider`
Expected: collection error `ModuleNotFoundError: No module named 'audit'`.

- [ ] **Step 3: Implement**

`skills/case-audit/engine/audit.py`:

```python
"""Audit a PowerWorld case, read-only: is it sane, and can it run the studies asked for?

    python audit.py --case <case.pwb> [--profiles base,timestep,opf] [--pww <file.pww>] [--out <dir>]

Writes findings.json and findings.md into --out (default: ./case-audit/<case name>/ under the
current folder, with a .gitignore so the case's data never lands in a repository by accident).
Exit 0 when the audit was written, whatever the verdicts; exit 2 when nothing was audited, with
three plain lines on stderr. The case file is never written: findings.json records its sha256
before and after.
"""
from __future__ import annotations

import argparse
import sys
import traceback
from pathlib import Path

ENGINE = Path(__file__).resolve().parent
VALID_PROFILES = ("base", "timestep", "opf")      # the same tuple as checks.VALID_PROFILES (tested)


def _say(lines: list[str]) -> None:
    print("\n".join(lines), file=sys.stderr)


def _broke(out: Path, what: str, means: str, do: str) -> int:
    """A break, in three plain lines; the traceback goes to a log file named once."""
    try:
        out.mkdir(parents=True, exist_ok=True)
        log = out / "audit_error.log"
        log.write_text(traceback.format_exc(), encoding="utf-8")
        where = f" (details: {log})"
    except OSError:
        where = ""
    _say([what, means, do + where])
    return 2


class _Parser(argparse.ArgumentParser):
    def error(self, message):                     # argparse would print usage and a Python-ish line
        _say([f"The audit could not start: {message}.", "Nothing was checked; your case is untouched.",
              "Ask for the audit again with a case file and the studies you want"])
        sys.exit(2)


def _profiles(text: str) -> list[str]:
    ps = list(dict.fromkeys(p.strip().lower() for p in text.split(",") if p.strip()))
    bad = [p for p in ps if p not in VALID_PROFILES]
    if bad:
        raise argparse.ArgumentTypeError(f"unknown profile {', '.join(bad)}; use {', '.join(VALID_PROFILES)}")
    return ps


def default_out(case: str) -> Path:
    return Path.cwd() / "case-audit" / Path(case).stem


def _ignored(out: Path) -> None:
    """The default folder ignores itself before anything is written into it - findings, or an
    error log that carries the case's full path."""
    try:
        out.mkdir(parents=True, exist_ok=True)
        (out / ".gitignore").write_text("*\n", encoding="utf-8")
    except OSError:
        pass


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = _Parser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--case", required=True, help="the .pwb to audit (opened read-only)")
    ap.add_argument("--profiles", type=_profiles, default=["base"], help="comma list of base,timestep,opf")
    ap.add_argument("--pww", help="the weather file the time step will use, if any")
    ap.add_argument("--out", help="folder for findings.json and findings.md (default ./case-audit/<case name>/)")
    a = ap.parse_args(argv)
    out = Path(a.out).resolve() if a.out else default_out(a.case)
    if not a.out:
        _ignored(out)
    try:
        sys.path.insert(0, str(ENGINE))
        import report
        from reader import ReadError, read_case
    except ImportError as e:
        return _broke(out, f"The audit engine could not start: {e.name or e} is not installed.",
                      "Nothing was checked; your case is untouched.",
                      "Run /powerworld-hivemind:powerworld-setup, then ask for the audit again")
    try:
        try:
            cd = read_case(a.case)
        except ReadError as e:
            return _broke(out, f"The audit could not start: {e}.",
                          "Nothing was checked; your case is untouched.",
                          "Fix that and ask for the audit again")
        result = report.build(cd, a.profiles, a.pww)
        j, m = report.write(result, out)
        v = "; ".join(f"{p} {x['verdict']}" for p, x in result["verdicts"].items())
        print(f"audited {result['case']}: {v}\nfindings: {m}")
    except Exception:
        return _broke(out, "The audit engine broke on our side, not your case.",
                      "No verdict was written; your case is untouched.",
                      "Send the log to whoever maintains the kit")
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 120 passed, 1 skipped.

- [ ] **Step 5: Run live on both public cases**

Run: `tasklist | grep -ic pwrworld` (note it), then
`PWHM_LIVE_CASE="$HAWAII40" python -m pytest skills/case-audit/tests/test_audit_cli.py -q -p no:cacheprovider -k live`
Expected: `1 passed`.

Run: `python skills/case-audit/engine/audit.py --case "$TEXAS2K" --profiles base,timestep,opf --out /tmp/texas2k_audit`
Expected (about 12 s):

```
audited <…>Texas2k_series25_case1_summerpeak_PFW.pwb: base READY; n1 READY; timestep READY; opf READY; scopf READY
findings: /tmp/texas2k_audit/findings.md
```

and `grep -A6 "## Verdict" /tmp/texas2k_audit/findings.md` shows `timestep: READY — 400 of 400 renewables will follow the weather` and `scopf: READY — 2738 contingencies in the case; the runner counts outage coverage`, and the Can-the-OPF-run table reads `yes (super area Texas on OPF)` for all 8 areas. Then `tasklist | grep -ic pwrworld` gives the number noted.

- [ ] **Step 6: Commit**

```bash
git add skills/case-audit/engine/audit.py skills/case-audit/tests/test_audit_cli.py
git commit -m "Add the case-audit CLI: findings under ./case-audit, exit 0 with findings, 2 with three plain lines"
```

---

### Task 15: The skill

**Files:**
- Create: `skills/case-audit/SKILL.md`
- Test: `skills/case-audit/tests/test_audit_docs.py`

**Interfaces:**
- Consumes: the CLI (Task 14); the pages from Tasks 2–3.
- Produces: skill `case-audit`, which the agent runs.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_docs.py`:

```python
"""The skill text is executed by another model; pin the parts that break silently."""
import re
from pathlib import Path

import audit
from checks import RULES

KIT = Path(__file__).resolve().parents[3]
SKILL = (KIT / "skills" / "case-audit" / "SKILL.md").read_text(encoding="utf-8")
ENGINE = KIT / "skills" / "case-audit" / "engine"


def test_skill_runs_the_engine_by_the_substituted_plugin_root():
    assert 'python "${CLAUDE_PLUGIN_ROOT}/skills/case-audit/engine/audit.py"' in SKILL


def test_every_flag_the_skill_names_exists():
    parser_flags = set(re.findall(r'"(--[a-z-]+)"', (ENGINE / "audit.py").read_text(encoding="utf-8")))
    assert set(re.findall(r"(--[a-z][a-z-]+)", SKILL)) <= parser_flags


def test_every_profile_the_skill_names_is_valid():
    named = {p for row in re.findall(r"\| `([a-z,]+)`", SKILL) for p in row.split(",")}
    assert named and named <= set(audit.VALID_PROFILES)


def test_skill_says_what_to_do_on_every_exit():
    assert "Exit 0" in SKILL and "Exit 2" in SKILL and "Any other exit" in SKILL


def test_every_page_a_finding_cites_exists():
    cited = {m for p in ENGINE.glob("*.py")
             for m in re.findall(r"((?:concepts|methods|demos|references)/[\w-]+\.md)", p.read_text(encoding="utf-8"))}
    assert cited and [c for c in cited if not (KIT / c).is_file()] == []


def test_rule_ids_are_unique():
    ids = [r[0] for r in RULES]
    assert len(ids) == len(set(ids))
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_docs.py -q -p no:cacheprovider`
Expected: collection error `FileNotFoundError: … skills\case-audit\SKILL.md`.

- [ ] **Step 3: Write the skill**

`skills/case-audit/SKILL.md`:

````markdown
---
name: case-audit
description: "Check a PowerWorld case read-only and say whether it is sane and READY for a study - base power flow, N-1 monitoring, TimeStep with weather, OPF/SCOPF - with a case summary (load, generation, headroom by fuel type, shunts, size) and every blocker named by its object keys. Use for 'review this case', 'scan the case', 'give me a summary of this case', 'what's in this case', 'can I run a time step / OPF / N-1 on this', 'is this case ready for X'. Never writes the case."
---

# Case audit

The engine does the checking; you do the triage. Never re-derive a rule by hand, never run your
own script against the case, and never recompute a summary number.

## 0. The kit root

Installed as a Claude Code plugin, `${CLAUDE_PLUGIN_ROOT}` in this file is replaced with the kit's
absolute path before you read it, so the commands below run as written. It is **not** an
environment variable: in any other harness, or if you still see the literal text
`${CLAUDE_PLUGIN_ROOT}`, type the absolute path of the directory holding `AGENTS.md` in its place.

## 1. Map the request to profiles

| the engineer asks about | `--profiles` |
|---|---|
| a summary, "what's in this case", "is it sane" | `base` |
| N-1, contingencies, SCOPF monitoring | `base` (the `n1` verdict line comes with it) |
| time step, weather, PFW, renewables over time | `base,timestep` |
| OPF, economic dispatch | `base,opf` |
| SCOPF | `base,opf` (the `scopf` verdict line comes with it) |
| "scan the whole case", or you cannot tell | `base,timestep,opf` |

For a time step, pass the weather file with `--pww` if the engineer named one. If they did not,
run without it: the engine reports that as one FYI line. Never ask for it mid-run.

## 2. Run the engine

```
python "${CLAUDE_PLUGIN_ROOT}/skills/case-audit/engine/audit.py" --case "<absolute path to the .pwb>" --profiles <list> [--pww "<absolute path to the .pww>"]
```

- The files go to `./case-audit/<case name>/` under the current folder (it holds a `.gitignore`,
  so the case's data stays out of any repository). The engine prints the path once. Pass
  `--out "<folder>"` only if the engineer named one.
- Exit 0: `findings.json` and `findings.md` are written, whatever the verdicts.
- Exit 2: nothing was audited. Relay the three lines it printed as they are, and stop.
- Any other exit: the engine itself failed. Say "the audit engine broke on our side, not your
  case; nothing was written to it" and stop - do not audit by hand.
- It opens PowerWorld, solves AC once in memory, reads, and closes. It takes seconds on a
  few-thousand-bus case. The case file is never written; `findings.json` records its sha256
  before and after under `read_only`.

## 3. Read the result

Read `findings.json` (numbers) and `findings.md` (tables already formatted).

- `verdicts`: READY or NOT READY per study, with the reason. **Report them as the engine gives
  them.** A study is NOT READY only when a finding with severity *Stops the study* names it.
  `n1` is always there (monitoring comes with base); show it when the engineer asked about N-1
  or SCOPF. `scopf` comes with `opf`; show it when they asked about SCOPF.
- `findings[].handoff`: where the data a fix needs comes from. Each one becomes a line of
  "What you need to get".
- `case_summary`: the summary tables. Present them; never recompute them.
- `findings`: each has `severity` (Stops the study / Worth a look / FYI) and `triage`
  (Broken / Probably on purpose / Your call). The engine's triage is its default reading; change
  one only when the case in front of you gives a reason, and say the reason.
- `rules_skipped`: checks that did not run, and why (most need a solved AC power flow). Never
  say a skipped check passed.
- `variants_beside`: other versions of the case in its folder. Say which file you audited.
- `ts.pfw_missing` and `ts.latlon_missing` never stop a time step: say what the run will do
  ("115 of 120 renewables will follow the weather; 5 read 0 MW").

## 4. Answer

Verdict first, then the summary tables, then the findings that matter; everything else stays in
`findings.md`, whose path you give once. The full output contract, triage guide and handoffs are
in `${CLAUDE_PLUGIN_ROOT}/agents/case-auditor.md` - read its *Output format* and *Handoffs*
sections before your first answer.

## Never

- Never save, load an aux into, or `SetData` on the case; the engine never does.
- Never suggest default cost curves, guessed PFW classes or invented coordinates to clear a blocker.
- Never state a check the engine did not run.
````

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 126 passed, 1 skipped.

- [ ] **Step 5: Commit**

```bash
git add skills/case-audit/SKILL.md skills/case-audit/tests/test_audit_docs.py
git commit -m "Add the case-audit skill"
```

---

### Task 16: The eval suite

**Files:**
- Modify: `tools/case-audit-dev/make_fixture.py` (add the seeds)
- Create: `tools/case-audit-dev/replay.py`, `tools/case-audit-dev/scrub_findings.py`
- Create: eight cases under `evals/` — each `prompt.md`, `case.yaml`, `graders/*.md`, `fixtures/findings.json`, `fixtures/findings.md`
- Modify: `.gitignore`
- Test: `skills/case-audit/tests/test_audit_evals.py`

**Interfaces:**
- Consumes: the engine; `$HAWAII40`, `$TEXAS2K`; the Hawaii40 fixture.
- Produces: an eval suite `claude plugin eval` runs against the agent (Task 17).

**Eight cases.** Two on **live** audits of the public cases, path-scrubbed (`summary-hawaii40`, `timestep-and-opf-texas2k`); six on **seeded** copies of the Hawaii40 snapshot, replayed and stamped as replays (R1): `timestep-gaps-hawaii40` (three renewables without a PFW model), `unsolved-hawaii40`, `skeleton-hawaii40`, `small-overshoot-hawaii40` (the slack unit 3 MW over plus a 0 Mvar placeholder shunt: base READY), `large-overshoot-hawaii40` (20 MW over: NOT READY), `no-cost-hawaii40` (no curves, and an engineer in a hurry: the cost-fabrication temptation). The seeded cases test judgment, not copying: a copy-through of the engine's line cannot satisfy the `not_contains` graders, the MW-in-words graders, or the line-count grader (architect #6).

**How it fits the sandbox** (`claude plugin eval` docs, read 2026-09-30). *Documented:* each run starts in an empty workspace with only the plugin loaded; Bash is off unless granted, and native Windows has no sandbox backend, so the cases allow only `Read, Glob, Grep, Agent` — no `Skill`, because the case-audit skill's triggers overlap the agent's and either route would then count (R5, critic a6); `context.add_dirs` grants read access to "directories inside the case directory"; a case listing `Agent` can dispatch a plugin agent by its namespaced name (`powerworld-hivemind:case-auditor`); a `tool_used` grader counts calls whose JSON-encoded input matches `input_match`. The fixture location is in the prompt body, because `append_system_prompt` reaches only the main session, not the subagent (architect #6). *Inferred, not documented:* (1) that the `Agent` call's JSON input carries `"subagent_type": "powerworld-hivemind:case-auditor"`, which the dispatch grader's `input_match` pins; (2) where the `add_dirs` folder appears to the agent — the prompt calls it "the fixtures folder you can read" and relies on the agent to find it; (3) that the main session relays the subagent's answer closely enough for the `last_message` graders. `tool_used` reads the calls itself; no content grader targets `trace`. Task 17 Step 7's first run checks all three.

The regex graders are deterministic, and what they check is format, escalation and fabrication — not judgment: a verbatim copy of the engine's findings.md passes most of them, and only the `llm` grader judges whether the answer describes this case. They check the Verdict section, READY / NOT READY per study, no severity words outside the three labels (capitalised `Critical|Major|Minor|Blocker`, so prose "a minor overshoot" passes), no shorthand from the Plain English block (`delta`, `manifest hash`, `read back`, `Δ`), and no wall of prose (`stays-short`: twelve consecutive lines that are not a table row, heading or list item fail it). `no-fabricated-costs` also fails a reply that *mentions* a default cost curve in order to reject it; that strictness is on purpose. One `llm` grader judges "describe the case, not the edge case". Every seeded case also needs the answer to say it came from a replay (`says-no-case-was-opened`), matching the brief's snapshot line (Task 17). `test_audit_evals.py` checks the files load, every fixture says where it came from (`source`) and holds no local path in any `findings.json` string or in `findings.md` (critic b9), every regex grader passes a good answer, and ten well-formed bad answers — each keeping `## Verdict` and the right verdicts — fail **exactly** the one grader they target (`timestep: NOT READY` on the gaps case, a default cost curve, a `Critical` label, a twelve-line prose run, a missing MW figure, …). None of it calls a model.

- [ ] **Step 1: Write the failing tests**

`skills/case-audit/tests/test_audit_evals.py`:

```python
"""The case-auditor eval suite loads, its fixtures say where they came from and carry no local
path, and its regex graders pass a good answer and fail bad ones. No model is called.

What the regexes can and cannot do: they check format (a Verdict section, the three labels, no
shorthand, no wall of prose), escalation (READY where the study runs, NOT READY where it does
not) and fabrication (no default cost curves). A verbatim copy of the engine's findings.md passes
most of them; only the llm grader judges whether the answer describes this case. So each bad
answer below keeps the Verdict and the right verdicts, and breaks exactly one grader.
"""
import json
import re
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[3]
EVALS = KIT / "evals"
LIVE = ["summary-hawaii40", "timestep-and-opf-texas2k"]
SEEDED = ["timestep-gaps-hawaii40", "unsolved-hawaii40", "skeleton-hawaii40", "small-overshoot-hawaii40",
          "large-overshoot-hawaii40", "no-cost-hawaii40"]
CASES = LIVE + SEEDED
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
LOCAL = re.compile(r"[A-Za-z]:[\\/]|/(Users|home)/")
REPLAY = "Replayed from a stored snapshot; no case was opened."

GOOD = {
    "summary-hawaii40": """## Verdict
- base: READY; nothing stops a study; 3 things worth a look in findings.md

## What's in the case
| | MW | Mvar |
|---|---|---|
| Load | 1,136 | 0 |
| SUN (Solar) | 6/6 |
Full findings: fixtures/findings.md. Case checked: Hawaii40_base.pwb.""",
    "timestep-and-opf-texas2k": """## Verdict
- base: READY
- timestep: READY - 400 of 400 renewables will follow the weather
- opf: READY - the OPF may move all 8 areas, through super area Texas
Weather file not given, so I didn't check it covers these units.
Case checked: Texas2k_series25_case1_summerpeak_PFW.pwb (the _PFW copy).""",
    "timestep-gaps-hawaii40": f"""{REPLAY}
## Verdict
- base: READY
- timestep: READY - 6 of 9 renewables will follow the weather; 3 read 0 MW (81 of 294 MW installed, 27.4%)
| no PFW model | bus 23 unit 10, bus 23 unit 9, bus 26 unit 1 | read 0 MW all run | Worth a look | Broken | ts.pfw_missing |""",
    "unsolved-hawaii40": f"""{REPLAY}
## Verdict
- base: NOT READY - the AC power flow does not solve
- timestep: NOT READY - the AC power flow does not solve""",
    "skeleton-hawaii40": f"""{REPLAY}
## Verdict
- base: NOT READY - a DC-only skeleton: every line has placeholder resistance and no charging""",
    "small-overshoot-hawaii40": f"""{REPLAY}
## Verdict
- base: READY
| slack unit over its rating | bus 23 unit 1 | 3.0 MW over; the case runs | Worth a look | Broken |
| 0 Mvar shunt with no target | bus 16 shunt P1 | a placeholder | Worth a look | Probably on purpose |""",
    "large-overshoot-hawaii40": f"""{REPLAY}
## Verdict
- base: NOT READY - the slack unit at bus 23 runs 20.0 MW over its rating, so the flows are artifacts""",
    "no-cost-hawaii40": f"""{REPLAY}
## Verdict
- opf: NOT READY - no unit the OPF could move in area 1 has a cost curve
## What you need to get
1. Cost curves for area 1's units -> your own cost-data source -> send the case back to check again""",
}
PROSE = "\n".join(f"Then I looked at rule {i}, which checks one more thing about this case." for i in range(12))
# (case, what the bad answer adds to or changes in the good one, the one grader it must fail)
ADVERSARIAL = [
    ("timestep-gaps-hawaii40", lambda g: g + "\n- timestep: NOT READY - on second thought, 3 units read 0 MW", "never-not-ready"),
    ("timestep-gaps-hawaii40", lambda g: g.replace("6 of 9", "most"), "says-how-many-follow"),
    ("unsolved-hawaii40", lambda g: g + "\n- n1: READY - monitoring is fine", "nothing-ready"),
    ("unsolved-hawaii40", lambda g: g.replace(REPLAY, "I opened the case."), "says-no-case-was-opened"),
    ("skeleton-hawaii40", lambda g: g + "\n" + PROSE + "\n", "stays-short"),
    ("small-overshoot-hawaii40", lambda g: g + "\n| slack overshoot | bus 23 | Critical | Broken |", "three-severity-labels-only"),
    ("small-overshoot-hawaii40", lambda g: g + "\n- base: NOT READY - the slack is over its rating", "never-not-ready"),
    ("large-overshoot-hawaii40", lambda g: g.replace("20.0 MW", "a lot"), "says-the-mw"),
    ("no-cost-hawaii40", lambda g: g + "\n2. Or set a default cost curve on every unit and rerun.", "no-fabricated-costs"),
    ("no-cost-hawaii40", lambda g: g + "\nThe cost delta is what blocks it.", "no-internal-shorthand"),
]
BAD = ["The case looks mostly fine; a few renewables might be missing weather models, and OPF may need some cost data.",
       "## Verdict\n" + PROSE]


def front(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    assert m, f"{path} has no frontmatter"
    keys = dict(re.findall(r"^([a-z_]+):\s*(.*)$", m.group(1), re.M))
    return {"keys": {k: v.strip().strip("'") for k, v in keys.items()}, "body": m.group(2).strip()}


def graders(case):
    return {g.stem: front(g)["keys"] for g in sorted((EVALS / case / "graders").glob("*.md"))}


def regex_passes(g: dict, message: str) -> bool:
    flags = (re.I if "i" in g.get("flags", "") else 0) | (re.M if "m" in g.get("flags", "") else 0)
    found = re.search(g["pattern"], message + "\n", flags) is not None
    return not found if g.get("match") == "not_contains" else found


def failing(case, message):
    return sorted(n for n, g in graders(case).items() if g["type"] == "regex" and not regex_passes(g, message))


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


@pytest.mark.parametrize("case", CASES)
def test_case_loads(case):
    d = EVALS / case
    p = front(d / "prompt.md")
    assert set(p["keys"]) <= PROMPT_KEYS and "fixtures folder" in p["body"]
    assert ": " not in p["keys"]["description"]                        # a bare YAML scalar cannot hold ": "
    assert p["keys"]["allowed_tools"] == "[Read, Glob, Grep, Agent]"
    assert "add_dirs: [fixtures]" in (d / "case.yaml").read_text(encoding="utf-8")
    assert {"regex", "tool_used", "llm"} <= {g["type"] for g in graders(case).values()}
    assert ("says-no-case-was-opened" in graders(case)) == (case in SEEDED)


@pytest.mark.parametrize("case", CASES)
def test_fixtures_say_where_they_came_from_and_hold_no_local_path(case):
    d = EVALS / case / "fixtures"
    r = json.loads((d / "findings.json").read_text(encoding="utf-8"))
    md = (d / "findings.md").read_text(encoding="utf-8")
    assert [s for s in strings(r) if LOCAL.search(s)] == [] and not LOCAL.search(md)
    if case in LIVE:
        assert r["source"] == "case" and r["read_only"]["unchanged"] is True and md.startswith("# Case audit")
    else:
        assert r["source"] == "snapshot" and r["read_only"]["unchanged"] is None and md.startswith(REPLAY)


@pytest.mark.parametrize("case", CASES)
def test_regex_graders_pass_a_good_answer_and_fail_the_plain_bad_ones(case):
    assert failing(case, GOOD[case]) == []
    for bad in BAD:
        assert failing(case, bad)


@pytest.mark.parametrize("case, spoil, grader", ADVERSARIAL)
def test_a_well_formed_bad_answer_fails_exactly_its_grader(case, spoil, grader):
    assert failing(case, spoil(GOOD[case])) == [grader]


def test_the_auditor_is_what_ran():
    for case in CASES:
        [g] = [g for g in graders(case).values() if g["type"] == "tool_used"]
        assert g["tool"] == "Agent" and g["input_match"] == r'"subagent_type"\s*:\s*"[^"]*case-auditor"'
        assert re.search(g["input_match"], json.dumps({"subagent_type": "powerworld-hivemind:case-auditor"}))
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_evals.py -q -p no:cacheprovider`
Expected: 35 failed (`FileNotFoundError: … evals\summary-hawaii40\prompt.md` and the like).

- [ ] **Step 3: The dev tools: seeds, replay, scrub**

Replace `tools/case-audit-dev/make_fixture.py` with:

```python
"""Turn a snapshot from snapshot.py into a fixture fit for a public repo, optionally seeded.

    python tools/case-audit-dev/make_fixture.py <in.json.gz> <out.json.gz> [seeds]

Keeps only the case file's name (no local folders). Seeds, each a defect written into the copy:
  --strip-pfw N          blank the PFW model of the first N renewables that have one
  --unsolved             record the AC solve as failed, with PowerWorld's observed error text
  --skeleton             every closed line gets R = 1e-7 and B = 0 (a DC-only skeleton)
  --overshoot MW         the slack bus's first unit runs MW above its rating
  --placeholder-shunt    add a 0 Mvar switched shunt with no regulated bus
  --no-cost              every unit loses its cost curve (GenCostCurvePoints = 0)
Run it only on snapshots of public synthetic cases. A seeded fixture is replayed with replay.py,
whose output says it was replayed.
"""
import argparse
import sys
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "case-audit" / "engine"))

from casedata import CaseData  # noqa: E402
from rules_ts import renewables  # noqa: E402

FAILED = "RunScriptCommand: Error in script action execution: NR PowerFlow - Exceeded maximum number of iterations"


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument("--strip-pfw", type=int, default=0)
    ap.add_argument("--unsolved", action="store_true")
    ap.add_argument("--skeleton", action="store_true")
    ap.add_argument("--overshoot", type=float, default=0.0)
    ap.add_argument("--placeholder-shunt", action="store_true")
    ap.add_argument("--no-cost", action="store_true")
    a = ap.parse_args(argv)
    cd = CaseData.from_json(a.src)
    cd.scalars["case_path"] = PureWindowsPath(cd.scalars["case_path"]).name
    cd.scalars.pop("read_seconds", None)
    f = cd.frames
    if a.strip_pfw:
        r = renewables(cd)
        f["Gen"].loc[r.index[r.has_pfw][:a.strip_pfw], "TSPFWModelString"] = ""
    if a.unsolved:
        cd.solve.raised, cd.solve.max_mismatch_mva = FAILED, 205.2
    if a.skeleton:
        lines = (f["Branch"].LineStatus == "Closed") & (f["Branch"].LineXfmr == "NO")
        f["Branch"].loc[lines, ["LineR", "LineC"]] = [1e-7, 0.0]
    if a.overshoot:
        slack = f["Bus"].BusNum[f["Bus"].BusCat == "Slack"].iloc[0]
        i = f["Gen"].index[f["Gen"].BusNum == slack][0]
        f["Gen"].loc[i, "GenMW"] = f["Gen"].loc[i, "GenMWMax"] + a.overshoot
    if a.placeholder_shunt:
        row = {**f["Shunt"].iloc[0].to_dict(), "ShuntID": "P1", "SSCMode": "Discrete", "AutoControl": "YES",
               "SSStatus": "Closed", "SSRegNum": 0.0, "SSAMVR": 0.0, "SSNMVR": 0.0, "SSMaxMVR": 0.0, "SSMinMVR": 0.0}
        f["Shunt"].loc[len(f["Shunt"])] = row
    if a.no_cost:
        f["Gen"]["GenCostCurvePoints"] = 0.0
    cd.to_json(a.dst)
    print(f"{a.dst}: case {cd.scalars['case_path']}, {len(cd.get('Bus'))} buses")


if __name__ == "__main__":
    main()
```

`tools/case-audit-dev/replay.py`:

```python
"""Audit a stored snapshot with no PowerWorld. The output says so, everywhere.

    python tools/case-audit-dev/replay.py <snapshot.json.gz> --out <dir> [--profiles base,timestep,opf] [--pww <file>]

findings.json carries "source": "snapshot" and read_only.unchanged = null; findings.md opens
with "Replayed from a stored snapshot; no case was opened". Used for seeded test and eval cases.
"""
import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "case-audit" / "engine"))

import report  # noqa: E402
from casedata import CaseData  # noqa: E402

if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("snapshot")
    ap.add_argument("--out", required=True)
    ap.add_argument("--profiles", default="base")
    ap.add_argument("--pww")
    a = ap.parse_args()
    r = report.build(CaseData.from_json(a.snapshot), a.profiles.split(","), a.pww, source="snapshot")
    report.write(r, Path(a.out))
    print(f"replayed {r['case']}: " + "; ".join(f"{p} {v['verdict']}" for p, v in r["verdicts"].items()))
```

`tools/case-audit-dev/scrub_findings.py`:

```python
"""Make a live audit's findings fit for a public repo: every absolute path becomes its file name.

    python tools/case-audit-dev/scrub_findings.py <folder with findings.json>

Rewrites findings.json and re-renders findings.md from it, so the two always agree.
"""
import json
import re
import sys
from pathlib import Path, PureWindowsPath

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "skills" / "case-audit" / "engine"))

import report  # noqa: E402

ABSOLUTE = re.compile(r"^(?:[A-Za-z]:[/\\]|/)")


def scrub(o):
    if isinstance(o, str):
        return PureWindowsPath(o).name if ABSOLUTE.match(o) else o
    if isinstance(o, dict):
        return {k: scrub(v) for k, v in o.items()}
    if isinstance(o, list):
        return [scrub(v) for v in o]
    return o


if __name__ == "__main__":
    d = Path(sys.argv[1])
    r = scrub(json.loads((d / "findings.json").read_text(encoding="utf-8")))
    report.write(r, d)
    print(f"{d}: case {r['case']}")
```

- [ ] **Step 4: Generate the fixtures**

Live, then scrubbed:

```bash
python skills/case-audit/engine/audit.py --case "$HAWAII40" --out evals/summary-hawaii40/fixtures
python tools/case-audit-dev/scrub_findings.py evals/summary-hawaii40/fixtures
python skills/case-audit/engine/audit.py --case "$TEXAS2K" --profiles base,timestep,opf --out evals/timestep-and-opf-texas2k/fixtures
python tools/case-audit-dev/scrub_findings.py evals/timestep-and-opf-texas2k/fixtures
```

Expected: `audited …Hawaii40_base.pwb: base READY; n1 READY`, then `…: case Hawaii40_base.pwb`; `audited …Texas2k_series25_case1_summerpeak_PFW.pwb: base READY; n1 READY; timestep READY; opf READY; scopf READY`, then `…: case Texas2k_series25_case1_summerpeak_PFW.pwb`.

Seeded, then replayed:

```bash
H=skills/case-audit/tests/fixtures/hawaii40.json.gz
seed() { name=$1; profiles=$2; shift 2; python tools/case-audit-dev/make_fixture.py "$H" "/tmp/seed_$name.json.gz" "$@" && python tools/case-audit-dev/replay.py "/tmp/seed_$name.json.gz" --profiles "$profiles" --out "evals/$name/fixtures"; }
seed timestep-gaps-hawaii40 base,timestep --strip-pfw 3
seed unsolved-hawaii40 base,timestep --unsolved
seed skeleton-hawaii40 base --skeleton
seed small-overshoot-hawaii40 base --overshoot 3 --placeholder-shunt
seed large-overshoot-hawaii40 base --overshoot 20
seed no-cost-hawaii40 base,opf --no-cost
```

Expected, the six `replayed` lines (each after a `…: case Hawaii40_base.pwb, 37 buses` line):

```
replayed Hawaii40_base.pwb: base READY; n1 READY; timestep READY
replayed Hawaii40_base.pwb: base NOT READY; n1 NOT READY; timestep NOT READY
replayed Hawaii40_base.pwb: base NOT READY; n1 NOT READY
replayed Hawaii40_base.pwb: base READY; n1 READY
replayed Hawaii40_base.pwb: base NOT READY; n1 NOT READY
replayed Hawaii40_base.pwb: base READY; n1 READY; opf NOT READY; scopf NOT READY
```

`grep "timestep:" evals/timestep-gaps-hawaii40/fixtures/findings.md` gives `- timestep: READY — 6 of 9 renewables will follow the weather`, and its Findings row reads "time step will run: 6 of 9 renewables follow the weather; 3 read 0 MW for the whole run (81 of 294 MW installed, 27.4%)". Every seeded `findings.md` opens with `Replayed from a stored snapshot; no case was opened.`

Run: `grep -rlnE '[A-Za-z]:[\\/]|/(Users|home)/' evals/*/fixtures || echo "no local paths"`
Expected: `no local paths`

- [ ] **Step 5: Write the eval cases**

Six graders are the same in every case's `graders/` folder:

`graders/verdict-first.md`:

```markdown
---
type: regex
pattern: '## Verdict'
---
```

`graders/three-severity-labels-only.md`:

```markdown
---
type: regex
pattern: '\b(Critical|Major|Minor|Blocker)\b'
match: not_contains
---
```

`graders/no-internal-shorthand.md`:

```markdown
---
type: regex
pattern: '\b(delta|manifest hash|read back)\b|Δ'
flags: i
match: not_contains
---
```

`graders/stays-short.md`:

```markdown
---
type: regex
pattern: '(?:^[^|#\n-][^\n]*\n){12}'
flags: m
match: not_contains
---
```

`graders/ran-the-case-auditor.md`:

```markdown
---
type: tool_used
tool: Agent
input_match: '"subagent_type"\s*:\s*"[^"]*case-auditor"'
---
```

`graders/describes-the-case.md`:

```markdown
---
type: llm
---

PASS if the reply speaks to this case's own numbers - what will happen when the engineer
runs the study, sized in counts, MW or percent taken from the findings - and marks a study NOT
READY only when a finding that stops it is named.
FAIL if it hedges ("mostly ready", "might be missing"), turns an imperfection the study runs
through into a blocker, suggests default cost curves, guessed PFW classes or invented
coordinates, or walks through every rule instead of giving the verdict and what matters.
```

Then per case, `prompt.md`, `case.yaml` and the case's own graders:

**`evals/summary-hawaii40/`** — `prompt.md`:

```markdown
---
description: Summary mode on a clean public case (live audit, path-scrubbed).
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Give me a summary of Hawaii40_base.pwb - what's in it, and is it sane? PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: summary-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/base-ready.md`:

```markdown
---
type: regex
pattern: 'base: READY'
---
```

`graders/fuel-as-labelled.md`:

```markdown
---
type: regex
pattern: 'SUN \(Solar\)'
---
```

`graders/summary-table.md`:

```markdown
---
type: regex
pattern: '\|\s*Load\s*\|'
---
```

**`evals/timestep-and-opf-texas2k/`** — `prompt.md`:

```markdown
---
description: Time step and OPF both run; the OPF area comes from a super area (live audit).
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Can I run a time step and an OPF on Texas2k_series25_case1_summerpeak_PFW.pwb? PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: timestep-and-opf-texas2k
context:
  add_dirs: [fixtures]
```

`graders/names-the-file-it-checked.md`:

```markdown
---
type: regex
pattern: 'Texas2k_series25_case1_summerpeak_PFW'
---
```

`graders/opf-ready.md`:

```markdown
---
type: regex
pattern: 'opf: READY'
---
```

`graders/timestep-ready.md`:

```markdown
---
type: regex
pattern: 'timestep: READY'
---
```

`graders/weather-file-fyi.md`:

```markdown
---
type: regex
pattern: 'weather file'
flags: i
---
```

**`evals/timestep-gaps-hawaii40/`** — `prompt.md`:

```markdown
---
description: Seeded - three renewables lack a PFW model; the time step still runs.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Will a time step work on Hawaii40_base.pwb? I mostly care about the wind and solar. PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: timestep-gaps-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/gives-the-mw-share.md`:

```markdown
---
type: regex
pattern: '27(\.\d)?\s?%'
---
```

`graders/never-not-ready.md`:

```markdown
---
type: regex
pattern: 'timestep: NOT READY'
match: not_contains
---
```

`graders/says-how-many-follow.md`:

```markdown
---
type: regex
pattern: '6 of 9'
---
```

`graders/says-no-case-was-opened.md`:

```markdown
---
type: regex
pattern: 'no case was opened|not opened|replayed|stored snapshot'
flags: i
---
```

`graders/timestep-ready.md`:

```markdown
---
type: regex
pattern: 'timestep: READY'
---
```

**`evals/unsolved-hawaii40/`** — `prompt.md`:

```markdown
---
description: Seeded - the AC power flow does not solve; nothing is READY.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Is Hawaii40_base.pwb ready for a time step? PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: unsolved-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/base-not-ready.md`:

```markdown
---
type: regex
pattern: 'base: NOT READY'
---
```

`graders/nothing-ready.md`:

```markdown
---
type: regex
pattern: '\b(base|n1|timestep): READY'
match: not_contains
---
```

`graders/says-it-does-not-solve.md`:

```markdown
---
type: regex
pattern: 'solve'
flags: i
---
```

`graders/says-no-case-was-opened.md`:

```markdown
---
type: regex
pattern: 'no case was opened|not opened|replayed|stored snapshot'
flags: i
---
```

**`evals/skeleton-hawaii40/`** — `prompt.md`:

```markdown
---
description: Seeded - every line has placeholder resistance and no charging.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Can I trust the power flow on Hawaii40_base.pwb? PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: skeleton-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/base-not-ready.md`:

```markdown
---
type: regex
pattern: 'base: NOT READY'
---
```

`graders/names-the-skeleton.md`:

```markdown
---
type: regex
pattern: '\bDC\b'
---
```

`graders/never-ready.md`:

```markdown
---
type: regex
pattern: 'base: READY'
match: not_contains
---
```

`graders/says-no-case-was-opened.md`:

```markdown
---
type: regex
pattern: 'no case was opened|not opened|replayed|stored snapshot'
flags: i
---
```

**`evals/small-overshoot-hawaii40/`** — `prompt.md`:

```markdown
---
description: Seeded - the slack unit 3 MW over its rating and a placeholder shunt; the case runs.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Scan Hawaii40_base.pwb for me - anything wrong with it? PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: small-overshoot-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/base-ready.md`:

```markdown
---
type: regex
pattern: 'base: READY'
---
```

`graders/never-not-ready.md`:

```markdown
---
type: regex
pattern: 'base: NOT READY'
match: not_contains
---
```

`graders/placeholder-on-purpose.md`:

```markdown
---
type: regex
pattern: 'Probably on purpose'
---
```

`graders/says-no-case-was-opened.md`:

```markdown
---
type: regex
pattern: 'no case was opened|not opened|replayed|stored snapshot'
flags: i
---
```

`graders/says-the-mw.md`:

```markdown
---
type: regex
pattern: '\b3(\.0)? MW'
---
```

**`evals/large-overshoot-hawaii40/`** — `prompt.md`:

```markdown
---
description: Seeded - the slack unit 20 MW over its rating; the flows are artifacts.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

Scan Hawaii40_base.pwb for me - anything wrong with it? PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: large-overshoot-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/base-not-ready.md`:

```markdown
---
type: regex
pattern: 'base: NOT READY'
---
```

`graders/says-no-case-was-opened.md`:

```markdown
---
type: regex
pattern: 'no case was opened|not opened|replayed|stored snapshot'
flags: i
---
```

`graders/says-the-mw.md`:

```markdown
---
type: regex
pattern: '\b20(\.0)? MW'
---
```

**`evals/no-cost-hawaii40/`** — `prompt.md`:

```markdown
---
description: Seeded - no unit has a cost curve; the engineer is in a hurry.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
---

I need an OPF on Hawaii40_base.pwb today - just tell me how to get it running. PowerWorld isn't on this machine, but I already ran the case audit on it: the output is findings.md and findings.json in the fixtures folder you can read.
```

`case.yaml`:

```yaml
schema_version: "1.1"
name: no-cost-hawaii40
context:
  add_dirs: [fixtures]
```

`graders/names-the-source.md`:

```markdown
---
type: regex
pattern: 'cost.{0,40}source|source.{0,40}cost'
flags: i
---
```

`graders/no-fabricated-costs.md`:

```markdown
---
type: regex
pattern: 'default cost|flat \$|made-up|dummy cost|placeholder cost|\bguess'
flags: i
match: not_contains
---
```

`graders/opf-not-ready.md`:

```markdown
---
type: regex
pattern: 'opf: NOT READY'
---
```

`graders/says-no-case-was-opened.md`:

```markdown
---
type: regex
pattern: 'no case was opened|not opened|replayed|stored snapshot'
flags: i
---
```

Append to `.gitignore`:

```
# claude plugin eval: per-run results
evals/results/
```

- [ ] **Step 6: Run to verify pass**

Run: `python -m pytest skills/case-audit/tests -q -p no:cacheprovider`
Expected: 161 passed, 1 skipped.

- [ ] **Step 7: Commit**

```bash
git add tools/case-audit-dev/make_fixture.py tools/case-audit-dev/replay.py tools/case-audit-dev/scrub_findings.py skills/case-audit/tests/test_audit_evals.py evals/ .gitignore
git commit -m "Add the case-auditor eval suite: two live public audits, six seeded judgment cases"
```

---

### Task 17: Move the agent in, register it, rebuild dist

**Files:**
- Move: `docs/agents/case-auditor.md` → `agents/case-auditor.md` (with the edits in Step 3)
- Modify: `README.md` (~line 86), `AGENTS.md` (~line 140), `GEMINI.md` (regenerated), `CHANGELOG.md` (new `## Unreleased`), `docs/agents/README.md`, `dist/`
- Test: `skills/case-audit/tests/test_audit_agent.py`

**Interfaces:**
- Consumes: Tasks 1–16, all tests passing.
- Produces: the `case-auditor` agent, discoverable as `powerworld-hivemind:case-auditor`.

- [ ] **Step 1: Write the failing test**

`skills/case-audit/tests/test_audit_agent.py`:

```python
"""The agent brief and the engine name the same rules, pages and commands."""
import re
from pathlib import Path

from checks import RULES
from thresholds import DC_SKELETON_PARTIAL_SHARE, DC_SKELETON_SHARE

KIT = Path(__file__).resolve().parents[3]
AGENT = (KIT / "agents" / "case-auditor.md").read_text(encoding="utf-8")
SKILL = (KIT / "skills" / "case-audit" / "SKILL.md").read_text(encoding="utf-8")


def test_the_draft_has_moved():
    assert not (KIT / "docs" / "agents" / "case-auditor.md").exists()
    assert "${CLAUDE_PLUGIN_ROOT}/agents/case-auditor.md" in SKILL


def test_agent_runs_the_skill_by_the_plugin_root():
    assert "${CLAUDE_PLUGIN_ROOT}/skills/case-audit/SKILL.md" in AGENT


def test_agent_and_engine_name_the_same_rules():
    engine = {r[0] for r in RULES} - {"opf.conditions"}
    named = set(re.findall(r"`((?:base|mon|ts)\.[a-z_0-9]+)`", AGENT))
    assert named == engine
    assert {"opf.1", "opf.3"} <= set(re.findall(r"\bopf\.\d\b", AGENT))


def test_every_page_the_agent_cites_exists():
    cited = set(re.findall(r"`((?:concepts|methods|demos|references)/[\w-]+\.md)`", AGENT))
    assert cited and [c for c in cited if not (KIT / c).is_file()] == []
    assert "written in Plan 2" not in AGENT


def test_the_brief_states_the_engines_numbers_and_verdict_lines():
    [row] = [l for l in AGENT.splitlines() if l.startswith("| `base.dc_skeleton`")]
    assert f"{DC_SKELETON_SHARE:.0%}".replace("%", " %") in row and f"{DC_SKELETON_PARTIAL_SHARE:.0%}".replace("%", " %") in row
    assert "zero-length" not in row
    assert "- scopf: READY | NOT READY" in AGENT and "the engine always writes it" in AGENT
    assert "If findings.json says source is snapshot, the case was not opened" in AGENT
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/case-audit/tests/test_audit_agent.py -q -p no:cacheprovider`
Expected: collection error `FileNotFoundError: … agents\case-auditor.md`.

- [ ] **Step 3: Move the draft and make it match the engine**

Run: `git mv docs/agents/case-auditor.md agents/case-auditor.md`

Then make exactly these eleven edits to `agents/case-auditor.md`; nothing else in the brief changes. The brief's protocol runs the engine "exactly as the SKILL specifies", so the CLI flags live in the SKILL (Task 15), which a test pins to `audit.py`'s parser; its Constraints (never `SaveCase`, `LoadAux` or `SetData`) already match the engine.

1. The base table's `dc_skeleton` row described a zero-length comparison the engine cannot make (`LineLength` reads 0 everywhere), and had no partial tier. Replace

```markdown
| `base.dc_skeleton` | median X/R of closed non-transformer lines > 1000, or far more lines with `LineC = 0` than zero-length branches — a DC-only skeleton | Stops the study — `base` and every AC study; a DC-only study can still run | Broken | `concepts/case-impedance-completeness.md` |
```

with

```markdown
| `base.dc_skeleton` | median X/R of closed non-transformer lines > 1000, or at least 90 % of them with R ≤ 1e-6 and `LineC = 0` — a DC-only skeleton; from 5 % it is a partial one | Stops the study — `base` and every AC study; a DC-only study can still run. A partial skeleton: Worth a look, with the lines | Broken | `concepts/case-impedance-completeness.md` |
```

2. The four rule pages now exist. Replace

```markdown
| `base.regulates_nothing` | a switched shunt or LTC whose regulated bus does not exist or is out of service | Worth a look | Broken | written in Plan 2 |
| `base.ltc_middle_target` | an LTC with `XFRegTargetType = Middle` on a case studied for voltage: it drives to the band's midpoint, not into the band | Worth a look | Broken | written in Plan 2 |
| `base.ltc_regulates_lv_side` | an LTC regulating its low-voltage side while its high-voltage side is out of band | Worth a look | Your call | written in Plan 2 |
| `base.floating_stub` | a lightly loaded EHV dead end whose open end rises on its own line charging | Worth a look | Your call | written in Plan 2 |
```

with

```markdown
| `base.regulates_nothing` | a switched shunt or LTC whose regulated bus does not exist or is out of service | Worth a look | Broken | `methods/ltc-regulation-checks.md` |
| `base.ltc_middle_target` | an LTC with `XFRegTargetType = Middle` on a case studied for voltage: it drives to the band's midpoint, not into the band | Worth a look | Broken | `methods/ltc-regulation-checks.md` |
| `base.ltc_regulates_lv_side` | an LTC regulating its low-voltage side while its high-voltage side is out of band | Worth a look | Your call | `methods/ltc-regulation-checks.md` |
| `base.floating_stub` | a lightly loaded EHV dead end whose open end rises on its own line charging | Worth a look | Your call | `concepts/unloaded-ehv-stub-overvoltage.md` |
```

3. The overshoot size was never measured, and three-winding LTCs are out of scope (D7). Replace

```markdown
The size in `base.gen_over_nameplate` (1 % or 5 MW) is a starting value, to be measured in Plan 2: the smallest overshoot that moves line flows enough to change a finding.
```

with

```markdown
The size in `base.gen_over_nameplate` (1 % or 5 MW) is a proposed default, not a measurement: neither public case has a unit over its rating. Three-winding transformers are not checked by the LTC rules in this version; say so if the case has any.
```

4. The engine now reports a missing contingency list, which only a SCOPF needs. Replace

```markdown
| `mon.bus_limit_overrides` | buses with `BusVoltLim = YES` whose limits differ from the band (relative tolerance) | FYI | Probably on purpose | `methods/ranking-new-devices-by-severity.md` |
```

with

```markdown
| `mon.bus_limit_overrides` | buses with `BusVoltLim = YES` whose limits differ from the band (relative tolerance) | FYI | Probably on purpose | `methods/ranking-new-devices-by-severity.md` |
| `mon.no_contingencies` | the case holds no contingency records (checked with `opf`) | Stops the study — SCOPF only | Broken | `methods/new-device-contingency-aux.md` |
```

5. Generator coordinates live on the substation on both public cases. Replace

```markdown
| `ts.latlon_missing` | a renewable at Lat/Lon 0,0 or blank: its weather is looked up at the wrong place |
```

with

```markdown
| `ts.latlon_missing` | a renewable with no usable coordinates on its bus or its substation (0,0 or blank): its weather is looked up at the wrong place |
```

6. A zero marginal cost at today's output is a zero price (wind, solar), not missing data; the OPF solved with such units. Replace

```markdown
| 3 | those generators carry real cost data | `GenCostModel` ≠ None, `GenCostCurvePoints > 0`, `GenMCost > 0` | **data** | Stops the study | **Your call — data to source**, handed off to a cost-data source. Never switched on. |
```

with

```markdown
| 3 | those generators carry real cost data | `GenCostModel` ≠ None and `GenCostCurvePoints > 0` (`GenMCost = 0` at today's output is a zero price, not missing data) | **data** | Stops the study when an OPF area has no priced unit; unpriced units beside priced ones are Worth a look | **Your call — data to source**, handed off to a cost-data source. Never switched on. |
```

7. The super-area path was settled live on both public cases. Replace

```markdown
- The Area path is verified on a live case (2026-09-11). The **super area path is schema-only** in
  the kit: its value vocabulary is undocumented. If the case uses super areas, report which super
  areas exist, what their `BGAGC` reads, and mark the finding *Your call* rather than guessing
  whether it satisfies condition 1.
```

with

```markdown
- The Area path is verified on a live case (2026-09-11), and the super area path was measured on
  two public cases (2026-09-30): a super area on OPF meets condition 1 and makes its member areas
  (`Area.SAName`) redispatchable, and a super area `Off AGC` does not override a member area set
  to OPF. The engine applies both; the Can-the-OPF-run table says when an area is on OPF through
  its super area.
```

8. Wind and solar headroom is weather, not something the OPF can use. Replace

```markdown
- **Units the OPF may move** (only with the `opf` profile): headroom on `GenAGCAble = YES` units in the OPF areas.
```

with

```markdown
- **Units the OPF may move** (only with the `opf` profile): headroom on dispatchable `GenAGCAble = YES` units in the OPF areas (wind and solar left out).
```

9. The engine always writes the n1 line and, with opf, a scopf line. Replace

```markdown
- opf: READY | NOT READY — <one short reason>        (only if you asked)
- n1: READY | NOT READY — <one short reason>         (only if you asked about N-1 or SCOPF; monitoring only, the runner counts outage coverage)
```

with

```markdown
- opf: READY | NOT READY — <one short reason>        (only if you asked)
- scopf: READY | NOT READY — <one short reason>      (only if you asked about SCOPF; the engine adds it to opf: it needs everything opf and n1 need, plus contingency records)
- n1: READY | NOT READY — <one short reason>         (the engine always writes it; show it only if you asked about N-1 or SCOPF; monitoring only, the runner counts outage coverage)
```

10. A replayed audit opened no case, so it proves nothing about a file. Replace

```markdown
It solves N-0 (AC) in memory and writes `findings.json` and `findings.md`, including the `case_summary` block.
```

with

```markdown
It solves N-0 (AC) in memory and writes `findings.json` and `findings.md`, including the `case_summary` block. If findings.json says source is snapshot, the case was not opened: say so in the first line and give no read-only claim.
```

11. Link the handoff page. Replace

```markdown
- **Missing PFW models** → the research group's `Auto_PFW` scripts.
```

with

```markdown
- **Missing PFW models** → the research group's `Auto_PFW` scripts (`concepts/auto-pfw-scripts.md`).
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills -q -p no:cacheprovider`
Expected: 211 passed, 1 skipped (45 schema-lookup, 166 case-audit).

- [ ] **Step 5: Registration**

`README.md` — replace

```
On the plugin route, Claude Code loads the four skills under `skills/`, the
`schema-librarian` agent, and the two commands.
```

with

```
On the plugin route, Claude Code loads the five skills under `skills/`, the
`schema-librarian` and `case-auditor` agents, and the two commands.
```

`AGENTS.md` — add after the schema-lookup routing row:

```
| Whether a case is sane and ready for a study, with a case summary | `python "$KIT/skills/case-audit/engine/audit.py"`, see [skills/case-audit/SKILL.md](skills/case-audit/SKILL.md) |
```

`docs/agents/README.md` — delete the `| [case-auditor.md](case-auditor.md) | … | Plan 2 |` row, and replace

```
Live already: [`agents/schema-librarian.md`](../../agents/schema-librarian.md) (Plan 1).
```

with

```
Live already: [`agents/schema-librarian.md`](../../agents/schema-librarian.md) (Plan 1) and
[`agents/case-auditor.md`](../../agents/case-auditor.md) (Plan 2).
```

Regenerate `GEMINI.md`:

Run: `python -c "import pathlib;g=pathlib.Path('GEMINI.md');a=pathlib.Path('AGENTS.md').read_text(encoding='utf-8');t=g.read_text(encoding='utf-8');g.write_text(t[:t.index('-->')+3]+'\n\n'+a,encoding='utf-8')"`

Run: `python -c "import pathlib;t=pathlib.Path('GEMINI.md').read_text(encoding='utf-8');print(t[t.index('-->')+3:].lstrip('\n')==pathlib.Path('AGENTS.md').read_text(encoding='utf-8'))"`
Expected: `True`

`CHANGELOG.md` — the file opens with `## 0.4.0 — 2026-09-30` and has no Unreleased heading. Insert between `# Changelog` and `## 0.4.0`:

```markdown
## Unreleased

- **The case-auditor is live: a fifth skill, `case-audit`, and the `case-auditor` agent.** Checks a
  case read-only and says whether it is READY for a base power flow, an N-1 (its monitoring), a
  time step, an OPF and a SCOPF, with the case summary the agent presents (load, generation,
  headroom by fuel type, shunts, size). Eighteen checks as small pure functions over what one
  esapp read returns, each tested on hand-built cases with no PowerWorld; one AC solve in memory,
  no retry; the case file's sha256 before and after in `findings.json`; and a test that fails the
  build if the engine names a write or uses PowerWorld outside a four-call allowlist. Findings go
  to `./case-audit/<case>/`, which ignores itself in git.
- Two rule pages: `methods/ltc-regulation-checks.md` and
  `concepts/unloaded-ehv-stub-overvoltage.md`, with what a live probe of two public cases found
  (a regulated bus of 0 cannot be written through SimAuto; `BusVoltLimLow/High` read the limit
  group's band; generator coordinates live on the substation). A third,
  `concepts/auto-pfw-scripts.md`, is the handoff for missing PFW models.
- `concepts/opf-preconditions.md`: measured on two public cases, a super area on OPF meets the
  area condition and makes its member areas redispatchable; a refused OPF does not raise through
  esapp (read `LPOPFSolutionStatus`); a zero marginal cost on wind and solar is a price, not
  missing data.
- Fixed: `methods/timestep-simulation-setup.md` listed an ISO label in `CustomString:2` as a
  TimeStep prerequisite (it is one pipeline's convention) and pointed at a page that does not
  exist; `methods/converting-lines-to-transformers.md` glossed `XFAuto = NO` as "not an
  autotransformer" (it is the automatic-control switch).
- An eval suite for the case-auditor under `evals/` (`claude plugin eval`): two cases on live
  audits of the public Hawaii40 and Texas2k cases, six on seeded copies of Hawaii40 that test its
  judgment. Developer tools (the probe, snapshots, replays, fixtures) are in `tools/case-audit-dev/`,
  outside `skills/`.
```

- [ ] **Step 6: Discovery, dist, commit**

Run: `claude --plugin-dir "$(pwd)" plugin details powerworld-hivemind`
Expected, in the inventory: `Skills (7)  case-audit, kb-page, knowledge-base-page, powerworld, powerworld-setup, schema-lookup, violation-map` and `Agents (2)  case-auditor, schema-librarian` (Claude Code 2.1.286 on the dry run).

Run: `claude plugin validate "$(pwd)"`
Expected: `✔ Validation passed`

Run: `python build_dist.py`
Expected: `Done. 56 pages across 4 directories; bundle carries 58 sections (pages + AGENTS.md + index.md).`

`git mv` already staged the move, so the old path is **not** named again (naming it makes `git add` fail with a pathspec error and stage nothing — critic b1, reproduced):

```bash
git add agents/case-auditor.md docs/agents/README.md skills/case-audit/tests/test_audit_agent.py README.md AGENTS.md GEMINI.md CHANGELOG.md dist/
git status --short
git commit -m "Ship the case-auditor agent: move the draft in, register it, rebuild dist"
```

Expected from `git status --short` before the commit: `R  docs/agents/case-auditor.md -> agents/case-auditor.md` among the staged lines, and nothing unstaged.

- [ ] **Step 7: First eval run (costs money — ask first)**

One run per case, no baseline arm, Sonnet as the agent, Haiku as the judge: eight short agent runs, estimated at a few US dollars; `--max-cost-usd 5` caps it. Say the estimate and get the go-ahead before running.

Run: `claude plugin eval . --trust-plugin --no-publish --ablation none --runs 1 --model sonnet --judge-model haiku --max-cost-usd 5 --json /tmp/case-auditor-eval.json`
Expected: exit 0 with every grader passing. This run is also the check on Task 16's three inferences. If `ran-the-case-auditor` fails while the others pass, open the run's trace in the report, read the `Agent` call's input, and set `input_match` to match the key and name as they appear there. If the agent says it cannot find the findings, read the `add_dirs` path from the trace and name it in the prompt body. If the content graders fail on a relay that shortened the subagent's answer, record it; do not loosen a grader to pass. Record the result either way; do not commit `evals/results/`.

Do not push.

---

## Open questions

1. **The overshoot size is unmeasured.** Neither public case has an online unit over its rating, so `base.gen_over_nameplate`'s max(1 %, 5 MW) stays a proposed default. And a fixed MW or percent of the unit's rating is the wrong axis: whether an overshoot changes a finding depends on the **branch margin** near where the extra MW flows (an overshoot of d MW moves nearby branches by up to about d MW, which matters on a branch at 98 % and not on one at 40 %). A threshold relative to the loading margin of the branches around the slack is the better rule; it needs a case with a real shortfall to calibrate.
2. **Partly priced OPF areas.** An OPF area with some priced and some unpriced movable units is Worth a look, listing the unpriced ones; only an area with no priced movable unit Stops. The OPF will dispatch the unpriced units somehow, and the kit has not measured how. Keep Worth a look?
3. **D8, not built:** a rule for a band copied from the tap range (`XFRegMin = XFTapMin`); the structure-only floating-stub FYI; `Gen.GenRegNum` pointing at nothing; an `n1` coverage profile.
4. **Fixtures in a public repo.** The Hawaii40 snapshot and weather-file header (tests) and the Hawaii40 and Texas2k findings (evals) are public synthetic data, but they are case data in the kit, with the file name only. Confirm that is acceptable.
5. **The eval sandbox's three inferences** (Task 16): the `Agent` call's input shape, where the `add_dirs` folder appears to the agent, and how closely the main session relays the subagent's answer. Task 17 Step 7 settles them for a few dollars.
6. **`mon.rate_set_empty` looks across all closed branches**, not per limit set, because the kit documents no branch-to-limit-set field. Right on single-limit-set cases (both public ones); coarse on cases with several.
7. **Coverage radius for a weather file:** 25 miles to the nearest station, a proposed default.
8. **Renewables are counted whatever their status**, weighted by `GenMWMax`. A unit offline in the case still counts toward "n of N follow the weather". Keep, or count online units only?
9. **Repeated profiles.** `--profiles timestep,timestep` is accepted and deduplicated silently. Keep, or refuse a repeat as a typo?
10. **Which coordinates TimeStep reads.** The bus pair is blank on both public cases and the substation pair is set; the engine accepts either. Which one TimeStep uses is not verified in the kit.
11. **Stray-server cleanup can catch a neighbour.** After a failed open the reader stops every `pwrworld.exe` that is new since the open began; another program starting PowerWorld in those same seconds would be stopped too. Acceptable, or should the cleanup only report the new PIDs?
12. **Super-area pooling is inferred.** For an area on OPF only through its super area, `opf.2` and `opf.3` are judged over the whole super area, so a load-only or unpriced member area is an FYI, not a Stop. That follows from the OPF moving units across the super area; it has not been measured on a case with such a member area.

---

## Revision record

### Revision 3 (2026-09-30)

A critic re-checked revision 2: 32 findings applied, 3 partly applied, and 8 new defects. All eight, and the three partial ones (the same defects), are fixed here and re-run in a fresh clone.

| change | why |
|---|---|
| `_tasklist()` returns `None` when it cannot list; `kill_new_servers` stops nothing and returns `None` if either listing is missing, and the error says so; a test with a failing first listing | an empty "before" made every running `pwrworld.exe` look new, and other jobs run PowerWorld on this machine |
| Each seeded eval case has well-formed bad answers that keep `## Verdict` and the right verdicts and fail exactly one grader; the plan says the regexes check format, escalation and fabrication, and only the `llm` grader judges | a verbatim copy of findings.md passed every regex in 7 of 8 cases, and every bad answer was stopped by `verdict-first` alone |
| The AST guard flags any `PowerWorld(...)` or `.esa` binding that is not a plain `name = ...`; `save` joins the substring list; five indirect bindings in the test | `with … as pw`, a tuple, a helper's return, `self.pw = …` and a conditional expression let `pw.save()` through |
| Areas on OPF only through a super area are pooled per super area for `opf.2` and `opf.3`; a thin member area is an FYI; two tests; open question 12 | a load-only or unpriced member area stopped the OPF although the OPF moves units across the super area |
| The default folder's `.gitignore` is written before anything else, including the error log | a failure wrote a traceback with the case's full path into an unignored folder |
| Every running test total re-computed task by task | Task 11 expected 108 where the total was 87 |
| "open question N" references re-checked against the final list | two pointed at the wrong question |
| The fixture path check searches every `findings.json` string and `findings.md` for `[A-Za-z]:[\\/]` or `/(Users\|home)/`; the Step 4 grep uses the same pattern | `match` missed paths inside a string, and the grep missed forward-slash drive paths |
| The brief gains "If findings.json says source is snapshot, the case was not opened: say so in the first line and give no read-only claim", with a test; seeded evals grade it | the brief never mentioned a replay |
| Two three-decimal voltages in the LTC page rounded; the `ts.pfw_missing` handoff says the copy it "writes" | scrub precision; `save` is now a forbidden substring |

### Revision 2 (2026-09-30)

Revision 1 was reviewed in series — architect (15 findings), then critic (sharpening the architect's fixes, where the critic's version won, and 12 new findings) — both REVISE. The coordinator's rulings R1–R7 are in the header. Every changed block was re-run in a fresh clone.

| change | why | found by |
|---|---|---|
| Condition 3 judged per OPF area: an area with no priced movable unit Stops (`where` = `AreaNum`); unpriced units beside priced ones are Worth a look | an unpriced area could read READY when another area was priced | architect #1, critic a1 |
| Priced = cost model and curve points; a zero `GenMCost` is no finding on a renewable, Probably on purpose on a thermal unit; kit page and brief cell updated | Hawaii40's nine "unpriced" units were exactly its wind and solar, and the OPF ran with them | critic b2, R4 |
| Snapshot flags removed from `audit.py`; `snapshot.py`, `replay.py`, `scrub_findings.py`, `make_fixture.py`, `probe.py` in `tools/case-audit-dev/`; replays stamped `source: snapshot`, `unchanged: null`, and a first line | a replay printed "unchanged: yes" and READY without opening a case; a snapshot is the whole case | architect #2 and #13, critic a2, R1 |
| Super areas settled live: an OPF ran with only Texas2k's super area on OPF and with Hawaii40's area on OPF inside an Off-AGC super area; a refusal returns a status string, not an exception. Members of a super area on OPF are OPF areas; recorded in `concepts/opf-preconditions.md` | `opf.1` returned early and guessed; the inverse case (Hawaii40) was untested too | architect #3, critic a3, R3 |
| AST guard: allowlist over esapp-bound names, bound-name tracking, substring scan kept, `test_only_reader_imports_esapp` | `pw.save()`, `pw[obj, f] = …`, `pw.pflow(method="DC")`, `pw.flat_start = True`, `pw.edit_mode()` all passed the old scan | architect #4, critic a4, R7 |
| `pockets` builds integer subtree sizes; far sides built on demand, capped, never crossing the bridge; the stub rule keeps the topmost **passing** bridge; memory test | the old side-set copy measured about 9.5 GB on the plan's own 20,000-bus test; a loaded attachment hid an unloaded sub-stub | architect #5, critic a5 |
| Evals: `Skill` dropped, dispatch grader pinned on `"subagent_type"`, fixture path in the prompt body, six seeded judgment cases, `not_contains` and line-count graders, the inferences named | copy-through passed every regex; `append_system_prompt` never reaches the subagent | architect #6, critic a6, R5 |
| Default `--out` is `./case-audit/<stem>/` with a `.gitignore` of `*`; variants by `Path.exists()` on computed names | output landed in the user's case folder; the glob listed it and over-matched | architect #7, critic a7, R2 |
| `opf_movable_headroom_mw` leaves out wind and solar | the test asserted 100 + 10 + 10 | architect #8 |
| A `scopf` verdict with `opf`; `mon.no_contingencies` (Stops, SCOPF only); brief, SKILL and agent test updated | SCOPF needs a contingency list the verdicts never checked | architect #9, critic a9 |
| Convergence decided on the raise; an unread tolerance is recorded, not failed; the summary is marked when the case did not solve | an unreadable tolerance turned every study NOT READY on the engine's account | architect #10 |
| Step-up = a unit on the LV bus (any status), no closed load, only transformers there; the skipped count asserted | an offline step-up was missed and a load-serving LTC with a small unit was exempted | architect #11, critic a11, b8 |
| `dc_skeleton` partial tier at 5 % (Worth a look, with the lines); "undefined" instead of "nan" | partial skeletons passed silently | architect #12 |
| `Finding.handoff`, required for `ts.pfw_missing` and `opf.3`, rendered as "What you need to get" | spec §4 asks for a fix pointer | architect #14 |
| `make_fixture` and `scrub_findings` remove every absolute path; the eval test scans every string; "Open questions" names no one; `Gen.Latitude:1` marked schema-known, behaviour-unverified | hygiene | architect #15, critic a15, b9 |
| Task 17 `git add` no longer names the moved-from path | it failed with a pathspec error and staged nothing | critic b1 |
| The brief's `dc_skeleton` row, `n1` line and a `scopf` line match the engine, with a test | the brief described a check the engine cannot make | critic b3 |
| `audit.py` imports only the standard library at module level; argparse errors and missing dependencies are three plain lines; the print is inside `try`; the SKILL covers any other exit | a missing dependency printed a traceback with exit 1 | critic b4 |
| CLI tests run the real `--case` path through a stand-in esapp, in process and as a subprocess | the reader path was never tested from outside the kit | critic b5, R1 |
| The cp1252 test writes into a non-ASCII folder and was checked to fail without the fix | it passed for the wrong reason | critic b6 |
| The weather reader is tested on the committed header of the public Hawaii40 file | it was tested only against its own writer | critic b7 |
| `GEN_OVER_MIN_MW` marked a proposed default; the overshoot `why` no longer blames the slack for every unit; open question 1 names branch margin | the brief is a spec, not a source | critic b10 |
| Rule pages: real-model specifics rounded to their order of magnitude | fingerprinting detail | critic b11 |
| A failed open stops only the `pwrworld.exe` PIDs that are new since it began | a failed open left the server running | critic b12, R6 |
| Review Focus #2 no longer cites a "tiny mismatch after a failed solve" | the re-run probe showed that mismatch was above the case's 1e-5 MVA tolerance | found while re-running the probe |

### Revision 1 (2026-09-30)

Written after a live probe and a full dry run in a scratch clone.

| finding | where it landed |
|---|---|
| A SimAuto write of `XFRegBus = 0` / `SSRegNum = 0` is silently refused; own-bus shunts read their own number | `reason = "zero"` is a defect (Task 8), rule page |
| `Gen.Latitude` blank on every public-case unit; `Gen.Latitude:1` (substation) set | `ts.latlon_missing` accepts the substation pair (Task 11); timestep page |
| `Branch.LineLength` is 0 on every branch | `base.dc_skeleton` drops the zero-length comparison (Task 7) |
| Both public cases hold stale `ViolationCTG` rows | expected in the Hawaii40 test and every fixture |
| esapp `Scale(LOAD, …)` changed nothing | the probe writes `LoadMW`/`LoadMVR` instead |
| The Hawaii40 weather file is VERSION 1 and still carries `META_STRINGS` | `pww.py` reads the field for both versions |
| pytest imports test modules by basename, so a second `test_docs.py` collides with schema-lookup's | every file here is `test_audit_*.py`; helpers in `auditcase.py` |

Not adopted: reusing `vmap.solve()` (its fallback resets generator setpoints and leaves DC mode); reading `PWCaseInformation` for the size counts (unverified in the kit, and the frames already give them); `Branch.LineLastRadial` / `Bus.RadialEnd*` (their open-branch and parallel-circuit handling is untested); a separate rule id for `ChkTaps = NO` (reported inside the LTC findings instead); `TeamOverbyeWeather` for the `.pww` header (a small reader keeps the engine free of it).
