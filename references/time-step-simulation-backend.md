---
type: reference
domain: cross-cutting
topic: timestep
aliases: [timestep-backend, time-step-simulation-backend]
tags: [timestep, powerworld, esapp, simauto, backend, reference]
---

# Reference: time-step-simulation backend

> ⚠️ **TimeStep ≠ Transient Stability.** This is PowerWorld's **TimeStep** weather
> feature (quasi-static `.pww` weather → hourly MW), driven by the low-level `esapp`
> `TimeStep*` script commands. It is **NOT** a transient-stability/dynamics study and
> does **NOT** use esapp's `pw.ts_solve` / `TSWatch` / `ContingencyBuilder` API (see the
> "TS" warning on [esapp](../concepts/esapp.md)). The "TS" in the `TSPFWModelString` field means *TimeStep*,
> not Transient Stability. Do not import or call any transient-stability function here.

## Abstract

Code-reconstruction reference for a timestep simulation pipeline: the worker function's PowerWorld call sequence (weather load → generator selection → field-save wrapper → run → export), `_GEN_PARAM` field list, `process_results` CSV post-processing with 8 header rows skipped, and both series and parallel orchestration variants. Covers every SimAuto command, required wrapper (`TIMESTEPSaveSelectedModifyStart`/`Finish`), and gotcha in enough detail to regenerate working simulation code from scratch. Read this in full only when writing or regenerating code for a timestep simulation; for the gist, use [timestep-simulation](../concepts/timestep-simulation.md).

## Connections

- **Up:** [timestep-simulation](../concepts/timestep-simulation.md) + [Home](../index.md)
- **Across:** [pww-data](../concepts/pww-data.md), [copper-plate](../concepts/copper-plate.md), [timestep-simulation](../concepts/timestep-simulation.md), [timestep-simulation-setup](../methods/timestep-simulation-setup.md)

## Content

> **Library note — prefer `esapp` over `esa`.** The original pipeline imports the standalone `esa` (Easy SimAuto) package. For new or regenerated code, prefer **`esapp` (ESA++)**. It wraps the **same** PowerWorld SimAuto server and exposes each of those SCRIPT commands as a typed named method (`pw.esa.TimeStepDoRun()`), which is what you should call (see [esapp-script-command-wrappers](../concepts/esapp-script-command-wrappers.md)). Swap esa's data helpers (`GetParametersMultipleElement`, `change_parameters_multiple_element_df`, `get_key_field_list`) for esapp's bracket interface (`pw[Type, fields]`, `pw[Type] = df`, `Type.keys()`). See [esapp-overview](../methods/esapp-overview.md). (Library choice only — unrelated to the TimeStep-vs-Transient-Stability distinction.)

Given a plain prompt ("run the renewable sim on the Synth2k case"), an agent reads this
page and writes working code. Everything here is verified against the pipeline's source.

The engine is two functions in one module: `timestep_worker(...)` (drives PowerWorld) and
`process_results(...)` (post-processes the CSV). The CLI entry script and the parallel
variant's entry script are CLI, grouping and I/O around them. The time math lives in
`time_utils.py`. **The parallel variant's engine module is byte-identical to the series
one**; only the entry-script orchestration differs.

---

## 0. Imports & environment (get these wrong and nothing runs)

- **`from esapp import PowerWorld`**, not the standalone `esa` (see the library note
  above). `pw.esa` is esapp's raw SimAuto handle; call each SCRIPT command below through its
  typed named method, not a hand-written script string. The bracket interface replaces esa's
  `GetParametersMultipleElement` / `change_parameters_multiple_element_df`.
- The import is **lazy**, done *inside* the worker function rather than at module top,
  so importing the engine module never requires PowerWorld to be installed. Keep it lazy
  if you regenerate this.
- **Windows-only.** esapp drives PowerWorld Simulator through SimAuto (COM). No
  PowerWorld → no run.
- `numpy` is imported at module top with `# noqa: F401` "for parity with downstream
  tooling"; the engine module does not use it. `pandas` is used.
- `sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))` is done so
  `from time_utils import convert_to_utc` resolves regardless of CWD.

```python
import os, sys, shutil, struct, tempfile
import numpy as np   # noqa: F401
import pandas as pd
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from time_utils import convert_to_utc
# ... inside the worker:
from esapp import PowerWorld       # lazy, only when actually simulating
from esapp.components import Gen
```

---

## 1. `_GEN_PARAM` — the generator field list (reconstructed)

These extra fields are appended to the case's key fields and pulled from every
generator. Reconstructed from the pipeline's engine module:

```python
_GEN_PARAM = [
    'Latitude', 'Longitude', 'GenUnitType', 'GenFuelType',
    'ZoneName', 'AreaName', 'TSPFWModelString', 'GenMWMax',
    'Selected', 'CustomString:1', 'CustomString:2',
]
```

Why each field is pulled:

| Field | Used for |
|---|---|
| `Latitude`, `Longitude` | output header rows (rows 7 & 8); also fed to the ISO-assignment step (a geopandas spatial join) to assign ISO region |
| `GenUnitType` | pulled for completeness; not used downstream in the engine module |
| `GenFuelType` | **the renewable selector** — `.str.contains('WND\|SUN')` picks wind/solar; also splits solar (`SUN`) vs wind (`WND`) |
| `ZoneName` | output header "State" row (label maps `ZoneName` → "State") |
| `AreaName` | output header "Utility" row (label maps `AreaName` → "Utility") |
| `TSPFWModelString` | output header "PV / Wind Types" row — the unit's PFW model string |
| `GenMWMax` | output header "Gen Max MW" row |
| `Selected` | toggled to `'YES'` for renewables, then used to drive `TimeDomainSelected` |
| `CustomString:1` | pulled but not used in the engine module |
| `CustomString:2` | output header "ISO" row (label maps `CustomString:2` → "ISO"); populated by the ISO-assignment step's spatial join |

Key fields come from `Gen.keys()` (typically `BusNum`, `GenID`)
and are **prepended**, so the resulting `gen` DataFrame has columns
`[<key fields>] + _GEN_PARAM`.

> ⚠️ **This prepend is required.** Later the code pushes `gen` back with
> `pw[Gen] = gen` twice, to set `Selected` and
> `TimeDomainSelected`. PowerWorld matches each row to a generator by its key fields, so
> if `BusNum`/`GenID` weren't in the DataFrame the write would **silently do nothing** and
> no generators would be selected. Always keep the key columns in any DataFrame you write
> back. (Same rule on the esapp bracket path — see [esapp](../concepts/esapp.md).)

---

## 2. `timestep_worker` — the FULL backend sequence, IN ORDER

Signature: `timestep_worker(case_path, pww_list, result_csv) -> gen (DataFrame)`.
Returns the generator metadata DataFrame (the caller needs it for `process_results`).
Reconstructed from the pipeline's worker function:

```python
def timestep_worker(case_path, pww_list, result_csv):
    from esapp import PowerWorld                     # lazy import
    from esapp.components import Gen, Timepoint
    tmp_case = None
    try:
        # (a) temp-copy the case so parallel runs never fight over the .pwb lock
        tmp_fd, tmp_case = tempfile.mkstemp(suffix='.PWB')
        os.close(tmp_fd)
        shutil.copy2(case_path, tmp_case)

        # (b) open the temp case
        pw = PowerWorld(tmp_case)

        # (c) pull generator metadata (key fields + _GEN_PARAM)
        gen_param = list(Gen.keys()) + _GEN_PARAM
        gen = pw[Gen, gen_param]

        # (d) load weather file(s): first = Load, rest = Append. The project calls plain
        # TimeStepLoadPWW here, which fails on every file on Simulator 25 (builds dated
        # 2026-09-20 and 2026-09-25; suspected glitch 2026-10-20-timestep-loadpww-plain). Load the file's full span with the Range form instead.
        d0, d1 = struct.unpack_from("<dd", open(pww_list[0], "rb").read(22), 6)  # OLE days, UTC
        t0, t1 = [(pd.Timestamp("1899-12-30") + pd.Timedelta(days=d)).round("h") for d in (d0, d1)]
        pw.esa.TimeStepLoadPWWRange(pww_list[0], f"{t0:%Y-%m-%dT%H:%M:%SZ}",
                                    f"{t1:%Y-%m-%dT%H:%M:%SZ}", "Weather Only")
        for pww in pww_list[1:]:
            pw.esa.TimeStepAppendPWW(pww, "Weather Only")
        assert len(pw[Timepoint, ["TimeDomainDateTimeUTC"]]) > 0, "weather load gave no timepoints"

        # (e) EDIT mode: mark renewables Selected = YES, push back
        pw.esa.EnterMode("EDIT")
        gen.loc[gen['GenFuelType'].str.contains('WND|SUN', na=False), 'Selected'] = 'YES'
        pw[Gen] = gen
        pw.esa.EnterMode("RUN")

        # (f) declare which fields to save — MUST be wrapped (see callout below)
        pw.esa.TIMESTEPSaveSelectedModifyStart()
        gen.loc[gen['Selected'] == 'YES', 'TimeDomainSelected'] = 'YES'
        pw[Gen] = gen
        pw.esa.TimeStepSaveFieldsSet(
            "GEN",
            ["BGGenMWFuelTypeGeneric:10", "BGGenMWFuelTypeGeneric:12"],
            "SELECTED",
        )
        pw.esa.TIMESTEPSaveSelectedModifyFinish()

        # (g) run + export
        pw.esa.TimeStepDoRun()
        pw.esa.TimeStepSaveResultsByTypeCSV("gen", result_csv)
        pw.esa.CloseCase()
        return gen
    finally:
        # (h) always delete the temp case
        if tmp_case and os.path.exists(tmp_case):
            try:
                os.remove(tmp_case)
            except OSError:
                pass
```

Step-by-step, every SimAuto call / SAW method in execution order:

1. `tempfile.mkstemp(suffix='.PWB')` → `os.close(fd)` → `shutil.copy2(case_path, tmp_case)` — work on a private temp copy, never the original `.pwb`.
2. `pw = PowerWorld(tmp_case)` — open the case.
3. `gen_param = list(Gen.keys()) + _GEN_PARAM`
4. `gen = pw[Gen, gen_param]` — DataFrame of all gens.
5. `pw.esa.TimeStepLoadPWWRange(pww0, t0, t1, "Weather Only")` — load the first weather file over
   its full span, read from the file header. Plain `TimeStepLoadPWW` fails on Simulator 25 builds
   dated 2026-09-20 and 2026-09-25 (suspected PowerWorld issue, not yet confirmed: glitch `2026-10-20-timestep-loadpww-plain`); assert the case now has timepoints.
6. for each remaining pww: `pw.esa.TimeStepAppendPWW(pww, "Weather Only")` — append.
7. `pw.esa.EnterMode("EDIT")`
8. set `gen['Selected'] = 'YES'` where `GenFuelType` contains `WND|SUN`.
9. `pw[Gen] = gen` — push selection into the case.
10. `pw.esa.EnterMode("RUN")`
11. **`pw.esa.TIMESTEPSaveSelectedModifyStart()`** ← opens the save-field edit transaction.
12. set `gen['TimeDomainSelected'] = 'YES'` where `Selected == 'YES'`.
13. `pw[Gen] = gen` — push `TimeDomainSelected`.
14. `pw.esa.TimeStepSaveFieldsSet("GEN", ["BGGenMWFuelTypeGeneric:10", "BGGenMWFuelTypeGeneric:12"], "SELECTED")` — choose the two MW-by-fuel-type fields to save for selected gens.
15. **`pw.esa.TIMESTEPSaveSelectedModifyFinish()`** ← closes the transaction.
16. `pw.esa.TimeStepDoRun()` — run the time-step simulation.
17. `pw.esa.TimeStepSaveResultsByTypeCSV("gen", result_csv)` — export gen results to CSV.
18. `pw.esa.CloseCase()`.
19. `finally:` delete `tmp_case`.

### ⚠️ REQUIRED wrapper — do not drop it

```
TIMESTEPSaveSelectedModifyStart;
   ... set TimeDomainSelected = YES + TimeStepSaveFieldsSet(...) ...
TIMESTEPSaveSelectedModifyFinish;
```

The `TimeStepSaveFieldsSet` + `TimeDomainSelected` changes **MUST** be bracketed by
`TIMESTEPSaveSelectedModifyStart;` … `TIMESTEPSaveSelectedModifyFinish;`. Without this
wrapper the field-save selection **silently fails**: the sim runs and the CSV is
written, but the per-generator MW columns you wanted are missing or empty. There is no
error. If you regenerate this code, keep the Start/Finish pair around steps 11–15 exactly.

### Field codes `BGGenMWFuelTypeGeneric:10` / `:12`

These are the two PowerWorld TimeStep result fields saved per selected generator:
"generator MW by generic fuel type", indices `10` and `12`. Downstream
`process_results` splits output columns by the literal substrings `'solar'` and
`'wind'` in the exported CSV column names, so the two indices correspond to the solar
and wind MW outputs.
> **UNVERIFIED:** needs confirmation -- which of `:10` / `:12` is solar vs wind in the PowerWorld fuel-type
> generic enumeration (code only relies on the column-name token, not the index).

### `pww_list` semantics

`pww_list[0]` → `TimeStepLoadPWWRange` over its full span; every subsequent entry → `TimeStepAppendPWW`. Both
use the `"Weather Only"` mode argument. In practice the callers pass **one PWW per
worker call** (`[pww]`) and concatenate the resulting CSVs in pandas afterward. The
Append branch exists, but the production paths feed single-file lists and stitch
quarters at the DataFrame level (see §4).

---

## 3. `process_results(gen, df)` — CSV → (solar_df, wind_df)

Signature: `process_results(gen, df) -> (solar_df, wind_df)`. `gen` is the DataFrame
returned by the worker; `df` is the raw exported CSV read back via `pd.read_csv`.
Reconstructed from the pipeline's `process_results` function.

### 3a. Time conversion first
`result = convert_to_utc(df)` — replaces the first column (Excel-serial timestamps,
which PowerWorld writes in UTC but the code treats as CST) with ISO-8601 strings marked
UTC that run 7 h early in summer (see §6).

### 3b. The 8 metadata header rows
Eight rows are prepended above the time-series. `row_names` are the row labels;
`labels` are the `gen` columns each row pulls its values from (positional zip):

```python
row_names = ['ISO', 'PV / Wind', 'PV / Wind Types', 'Gen Max MW', 'State', 'Utility',
             'Latitude', 'Longitude']
labels    = ['CustomString:2', 'GenFuelType', 'TSPFWModelString',
             'GenMWMax', 'ZoneName', 'AreaName', 'Latitude', 'Longitude']
```

| Header row | Source `gen` column |
|---|---|
| ISO | `CustomString:2` |
| PV / Wind | `GenFuelType` |
| PV / Wind Types | `TSPFWModelString` |
| Gen Max MW | `GenMWMax` |
| State | `ZoneName` |
| Utility | `AreaName` |
| Latitude | `Latitude` |
| Longitude | `Longitude` |

### 3c. `(BusNum, GenID)` meta_lookup
An O(1) dict over only the renewable rows, keyed by `(int(BusNum), str(GenID))`:

```python
ren_mask = gen['GenFuelType'].str.contains('WND|SUN', na=False)
meta_lookup = {
    (int(row['BusNum']), str(row['GenID'])): row
    for _, row in gen[ren_mask].iterrows()
}
```

### 3d. Header build — per-column branch logic
Walk every column of `result` once:

- column == `'DateTimeUTCExcelFormat'` → each header row gets its own label (the row name itself) in this column.
- column contains `'Gen'` → parse `parts = col.split(' ')`; `busnum = int(parts[2].replace("'", ""))`, `genid = parts[3].replace("'", "")`. On `IndexError`/`ValueError` → fill `'N/A'`. Otherwise look up `meta_lookup[(busnum, genid)]` and fill each header row from its mapped label (`'N/A'` if not found).
- any other column → fill `''` (empty) for all header rows.

The column-name shape PowerWorld emits is therefore like `... Gen '<BusNum>' '<GenID>' ...` (quoted bus and id at `parts[2]`/`parts[3]`), with `'solar'`/`'wind'` somewhere in the name. Header rows are assembled into `header_df` and `pd.concat([header_df, result], ignore_index=True)` → `result_1`.

### 3e. Solar / wind split by token matching
```python
PV_gen = gen[gen['GenFuelType'].str.contains('SUN', na=False)]
WT_gen = gen[gen['GenFuelType'].str.contains('WND', na=False)]

solar_tokens = {f"'{int(r['BusNum'])}' '{r['GenID']}'" for _, r in PV_gen.iterrows()}
wind_tokens  = {f"'{int(r['BusNum'])}' '{r['GenID']}'" for _, r in WT_gen.iterrows()}

solar_columns = ['DateTimeUTCExcelFormat'] + [
    c for c in result_1.columns
    if 'solar' in c.lower() and any(tok in c for tok in solar_tokens)]
wind_columns = ['DateTimeUTCExcelFormat'] + [
    c for c in result_1.columns
    if 'wind' in c.lower() and any(tok in c for tok in wind_tokens)]

return result_1[solar_columns], result_1[wind_columns]
```

A column lands in the solar output iff its name contains `'solar'` (case-insensitive)
**AND** contains a `'<BusNum>' '<GenID>'` token of a `SUN` generator; symmetric for
wind/`WND`. The timestamp column `DateTimeUTCExcelFormat` is always kept first in both.
Both returned frames carry the 8 header rows on top.

---

## 4. The pipeline's CLI entry script (series) — grouping, run loop, output naming

- CLI args (`parse_args`): `--case` (required), mutually-exclusive **required** group
  `--pww FILE...` xor `--pww-dir DIR`, plus `--year YYYY` (int, filters `--pww-dir`),
  `--output-dir`, `--yes/-y` (skip the `input()` confirm prompt).
- Default output: `Results/` next to the entry script (`os.path.join(_script_dir, "Results")`).
- **Grouping (`_group_files`)**: for each file, `re.search(r"(\d{4})_Q\d", name)`.
  Matches (quarter files like `NorthAmerica2025_Q1.pww`) are grouped by **year** so all
  4 quarters run as one logical run (`groups[year] = [...]`). Non-matches (e.g. forecast
  files) become individual runs keyed by their filename stem. With `--pww-dir`, only
  `.pww` files are listed and `year_filter=args.year` drops other years.
- **Run loop**: for each `(key, pww_list)`:
  - `is_historical = bool(re.search(r"\d{4}_Q\d", basename(pww_list[0])))`.
  - `out_stem = f"Historical_{key}"` if historical else `key` (forecast stems already
    start with `Forecast_`, so don't double-prefix).
  - Outputs: `{out_stem}_solar.csv`, `{out_stem}_wind.csv` in `output_dir`.
  - **Resume-safe skip**: if BOTH solar and wind CSVs already exist → skip (delete to re-run).
  - Runs each pww **one at a time** via `timestep_worker(args.case, [pww], q_csv)`
    into `_raw_<qname>.csv`, reads each back with `pd.read_csv`, removes the temp csv,
    `pd.concat(dfs, ignore_index=True)`, then `process_results(gen, df)` → write
    `solar_path` / `wind_path`. `gen` from the last quarter is reused (identical per case).
  - Wrapped in try/except → prints error + `traceback.print_exc()`, continues to next group.

---

## 5. The parallel variant's entry script

Same engine; only orchestration differs. What can produce a wrong or failed run:

- **Cap `--workers` at what the PowerWorld licence and RAM allow.** Each worker drives its
  own SimAuto instance against its own temp copy of the case. The temp copy in the worker
  function is what makes concurrency safe.
- **Workers must stay top-level and import the engine inside the child.** Windows spawn
  needs them picklable, and the parent must never load PowerWorld.
- **Incomplete years are skipped silently** — only years with all four quarters become
  groups, and a group with any failed sim skips assembly.
- **Resume-safe:** a group whose solar *and* wind CSVs both exist is skipped, so a rerun
  after a partial failure does not redo finished work.

## 6. `time_utils.py` — time math

> **Correction:** the conversion below is wrong. PowerWorld writes column 0 in **UTC**
> (measured 2026-10-20 on build 2026-09-25: it matched `Timepoint.TimeDomainDateTimeUTC` row for
> row), but the code treats it as CST and shifts it the wrong way. Labels run 7 h early in summer
> and 6 h early in winter (7 h measured 2026-10-14 against `TimeDomainDateTimeUTC`). Re-label from
> `Timepoint.TimeDomainDateTimeUTC` before joining on time; see [how-to-analyze-results](../methods/how-to-analyze-results.md).
> The text below describes what the code does, not what is right.

Two facts that change an answer:

- **The conversion applies a DST step, not a fixed offset.** The code reads column 0 as
  Excel-serial CST, subtracts 6 h, and takes one more hour off inside US DST (second Sunday in
  March 02:00 → first Sunday in November 02:00) before rounding to the hour. A summer label is
  therefore 7 h earlier than the true UTC hour, and a winter label 6 h earlier.
- **`interpolate_to_hourly` exists but is NOT called** in the current run path. It fills
  3-hour forecast gaps; assuming it ran is how a gapped forecast series gets read as hourly.

## 7. Gotchas checklist (regenerate-safe)

- ✅ `from esapp import PowerWorld`: **esapp, not the standalone `esa`**. Same SimAuto
  underneath; do not mix the two in one script.
- ✅ **Windows + PowerWorld only** (SimAuto/COM).
- ✅ **Temp-copy the case** (`mkstemp('.PWB')` + `shutil.copy2`) and run against the
  copy; delete in `finally`. This is what makes parallel runs lock-safe.
- ✅ **`TIMESTEPSaveSelectedModifyStart;` … `TIMESTEPSaveSelectedModifyFinish;`** must
  wrap the `TimeStepSaveFieldsSet` + `TimeDomainSelected` edits, or saved fields
  silently come back empty.
- ✅ Selection is two-stage: `Selected='YES'` (EDIT mode) for renewables, then
  `TimeDomainSelected='YES'` (inside the Save-Modify wrapper) for those same gens.
- ✅ `EnterMode(EDIT)` before pushing `Selected`; `EnterMode(RUN)` before the
  Save-Modify wrapper and the run.
- ✅ Renewable selector everywhere: `GenFuelType.str.contains('WND|SUN', na=False)`;
  solar = `SUN`, wind = `WND`.
- ✅ **Resume-safe skip**: a run is skipped iff BOTH its solar and wind CSVs exist.
- ✅ **Historical grouping** keys off `re.search(r"(\d{4})_Q\d", name)` — quarter files
  group by year and are named `Historical_{year}_{solar,wind}.csv`; anything else runs
  individually under its stem. Keep `_group_files` and the `is_historical` check in sync.
- ✅ Confirmation prompt via `input()` unless `--yes/-y`; parallel adds `--workers`.
- ✅ Parallel workers must stay **top-level / picklable** and import the engine module inside
  the child process (Windows spawn).

---

## Related

- Hub: [Home](../index.md)
- Concept/how-to: [timestep-simulation](../concepts/timestep-simulation.md) · [timestep-simulation-setup](../methods/timestep-simulation-setup.md)
- Inputs: [pww-data](../concepts/pww-data.md) · PFW context: [copper-plate](../concepts/copper-plate.md) · ISO prep: the ISO-assignment step (a geopandas spatial join)
