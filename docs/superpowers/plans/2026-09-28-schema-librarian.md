# Schema-librarian (Plan 1 of 4) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship the kit's first agent — a read-only "reference desk" that answers "which PowerWorld object, field or command?" and shows what the kit's curated pages say about it — plus the stale-page fixes the later agents build on.

**Architecture:** A pure-Python lookup engine over the Simulator 25 field export (openpyxl, gzip-JSON cache, no PowerWorld needed); a hub reader that returns the curated study-options page's rows **verbatim** rather than scoring them; and a CLI. A skill (`skills/schema-lookup/SKILL.md`) carries the procedure so every harness can use it; a thin Claude Code agent (`agents/schema-librarian.md`) runs that skill in a fresh context on a cheap model.

**Tech Stack:** Python 3.11+, openpyxl, pytest. No esapp, no PowerWorld.

**Spec:** `docs/superpowers/specs/2026-09-28-power-system-agents-design.md` (§3 team, §7 schema-librarian, §10 librarian test row, §11 build order steps 0–1, §13 open questions).

**Revision 2 (2026-09-28)** — rewritten after a serial architect → critic review. What changed and why is recorded at the end. Every code block below was run from a scratch copy of the kit before it was written here: **37 tests, 37 passed**.

**Plans 2–4** (case-auditor, study-runner, fix-reviewer) are written after this plan ships.

## Global Constraints

- Everything ships inside the kit and is self-contained: no imports from any private research repository.
- Tests use public data only; the field export is PowerWorld schema, not case data.
- The librarian never opens or writes a case, never states a field name absent from the export, and never condenses the hub's claims into a confidence level — it shows the hub's rows verbatim.
- The agent's "read-only" is enforced by its prompt only: it holds `Bash`. The skill and agent files say so.
- Every role is a skill plus an engine first; the agent file is a thin wrapper that runs the skill.
- Commit messages carry no AI attribution lines.
- Never `cd` inside a compound shell command; run everything from the repository root.
- **Do not push** until the redistribution decision (spec §13: may a CC-BY-4.0 kit ship PowerWorld's field export and a digest of its aux-file-format document) is recorded in the spec. Local commits are fine.

## Review Focus

1. **Windows console encoding.** Descriptions contain non-ASCII (`≥` in `Substation.NERCCIP14AggWeight`); a default cp1252 console crashes on print. Expect clean UTF-8. → Task 6 `test_cli_survives_cp1252_console`.
2. **Run from outside the kit.** Under a plugin install the user's cwd is their project, not the kit. Expect the CLI to work from any directory. → Task 6 `test_cli_runs_from_outside_the_kit`; Task 7 SKILL uses an absolute kit root.
3. **A field name shared by many objects** (`GenMW` on Gen, Area, Contingency…). Expect no row about another object to be presented as being about this one. → Task 5 `test_no_exact_claim_for_same_name_on_another_object`, `test_other_objects_dotted_row_is_not_returned`.
4. **A preference with no matching field** ("SCOPF inner loop"). Expect the real alternative to surface, and spelling neighbours labelled as not substitutes. → Task 5 `test_passages_answer_the_inner_loop_question`, Task 6 `test_absent_field_exit_1_points_at_the_real_answer`.
5. **Environment damage**: openpyxl missing, a corrupt cache, a read-only install directory, a replaced export. Expect a clear message or a transparent rebuild, never a traceback or stale fields. → Task 2 `test_missing_openpyxl_is_a_schema_error`, `test_corrupt_cache_falls_back_to_export`, `test_unwritable_cache_dir_still_answers`, `test_cache_rebuilt_when_export_changes`.

---

## File Structure

| file | responsibility |
|---|---|
| `concepts/parallel-contingency-solve.md` (modify) | gain the rule to `.exit()` instances you own |
| `methods/reading-violationctg.md` (modify) | islanding: invisible to `ViolationCTG`, visible through three other checks |
| `concepts/lodf.md` (modify) | stop calling islanding silent in PowerWorld overall |
| `commands/powerworld-setup.md` (modify) | install openpyxl |
| `skills/schema-lookup/engine/schema.py` | load the export (cached); resolve objects; keys, required, find field, search |
| `skills/schema-lookup/engine/hub.py` | the hub page's rows and passages about a field, verbatim |
| `skills/schema-lookup/engine/lookup.py` | CLI: `object`, `field`, `search` |
| `skills/schema-lookup/tests/conftest.py` | engine on `sys.path`; session-scoped fields |
| `skills/schema-lookup/tests/test_schema.py` | loader, cache, lookups, search |
| `skills/schema-lookup/tests/test_hub.py` | hub rows and passages against the real hub page |
| `skills/schema-lookup/tests/test_lookup_cli.py` | CLI end to end via subprocess |
| `skills/schema-lookup/SKILL.md` | the procedure any harness follows |
| `agents/schema-librarian.md` | Claude Code agent: runs the skill, haiku |
| `.gitignore` (modify) | ignore `skills/*/engine/.cache/` |
| `README.md`, `AGENTS.md`, `GEMINI.md`, `CHANGELOG.md` (modify) | registration |

---

### Task 1: Fix the stale pages

**Files:**
- Modify: `concepts/parallel-contingency-solve.md` (~line 34, ~line 72)
- Modify: `methods/reading-violationctg.md` (~line 236, ~line 252, ~line 261)
- Modify: `concepts/lodf.md` (~line 91)

**Interfaces:**
- Consumes: nothing.
- Produces: page text Plan 3 (study-runner) cites for worker cleanup and island detection.

- [ ] **Step 1: Confirm the stale statements are present**

Run: `grep -n "so that's a non-issue\|never call" concepts/parallel-contingency-solve.md; grep -n "not detectable\|will not give it to you\|So the correct pairing is" methods/reading-violationctg.md; grep -n "reports CLEAN" concepts/lodf.md`
Expected: hits in all three files.

- [ ] **Step 2: `concepts/parallel-contingency-solve.md`**

In `## Connections` (~line 34) replace

```markdown
  instances concurrently, the real rule is just "never call `.exit()`")
```

with

```markdown
  instances concurrently; the rule is never `.exit()` a shared instance, always `.exit()` one you own)
```

Insert this paragraph immediately after the paragraph ending `process lifetime, so that's a non-issue.`:

```markdown
**The rule cuts the other way for an instance you own and reopen in a loop.** A worker that opens a
fresh case per candidate — the pattern a measurement harness uses so no tap or shunt state carries
between candidates — must call `.exit()` on **its own** instance before the next open. Dropping the
Python reference (`del pw`) does not release the COM server: measured 2026-09-28, each open left one
`pwrworld.exe` of ~1 GB running, and a run of four workers reached sixteen stray servers in a few
minutes, starving the other sweep on the machine. So: never `.exit()` a shared instance; always
`.exit()` one you opened and are done with. Killing the Python process eventually frees them too, but
only once COM notices the client is gone.
```

- [ ] **Step 3: `methods/reading-violationctg.md`**

Replace the heading

```markdown
### Islanding is not detectable from `CTGSolveAll`
```

with

```markdown
### Islanding: invisible to `ViolationCTG`, visible through three other checks
```

In the paragraph starting `If you need islanding detection` (~line 252), replace

```markdown
If you need islanding detection, `CTGSolveAll` alone will not give it to you — **but
```

with

```markdown
If you need islanding detection, `ViolationCTG` alone will not give it to you — **and
```

Replace the two lines

```markdown
**So the correct pairing is: `CTGSolveAll` for the violations, the LODF denominator for the
islanding list.** Neither one covers the other.
```

with

```markdown
**Correction (2026-09-24, completed 2026-09-28): islanding *is* visible after `CTGSolveAll` —
through three checks that each catch a different set, and no single one catches all.**

- **`Contingency.LoadMW` / `GenMW`** hold the load and generation cut off by each outage and are
  non-zero only on islanding outages — these are islands PowerWorld **drops**. Checked against a
  direct `CTGApply` plus re-solve of every outage on a public 40-bus synthetic case (93 of 93
  agreed). A generation-only pocket reads `LoadMW = 0`; catch it through `GenMW`.
- **`CTG_Options.Include`** (concise `IslandViolations`) = YES, with `BGLoadMW` and
  `IslandTotalBus` as minimum-size filters and `Sim_Solution_Options.EvalSolutionIsland` = YES as
  its prerequisite, reports *Island Solved* rows for self-sustaining pockets PowerWorld keeps
  **energized** — exactly the ones where `LoadMW` / `GenMW` read 0.
- **`DetermineBranchesThatCreateIslands`** (script) is the structural check: it finds both kinds
  plus 0-MW pockets whose generation is offline.

Measured 2026-09-28 on a regional synthetic planning model. Gate an island check on MW only when
the stranded pocket carries MW. The LODF denominator above remains the solve-free screen.
`ViolationCTG` alone still ranks every one of these outages harmless — read the island checks
alongside it.
```

- [ ] **Step 4: `concepts/lodf.md`**

Replace

```markdown
PowerWorld CTG sweep, islanded buses read 0 and get skipped, so stranding a 138 kV pocket
**reports CLEAN**. A free connectivity check turns that silent failure into an explicit list.
```

with

```markdown
PowerWorld CTG sweep, islanded buses read 0 and get skipped, so stranding a 138 kV pocket
**reports CLEAN in `ViolationCTG`**. PowerWorld does record it elsewhere — `Contingency.LoadMW` /
`GenMW` and the *Island Solved* rows of `CTG_Options.Include`, see
[reading-violationctg](../methods/reading-violationctg.md) — but only for whoever reads those. A
free connectivity check turns it into an explicit list before any solve.
```

- [ ] **Step 5: Verify**

Run: `grep -c "not detectable\|So the correct pairing is" methods/reading-violationctg.md`
Expected: `0`

Run: `python -c "import pathlib,re;R=pathlib.Path('.');print([f'{p}: {t}' for d in ('concepts','methods','demos','references') for p in (R/d).glob('*.md') for t in set(re.findall(r'\]\(([^)#]+\.md)',p.read_text(encoding='utf-8-sig'))) if not (p.parent/t).exists()] or 'no dangling links')"`
Expected: `no dangling links`

- [ ] **Step 6: Rebuild dist and commit**

```bash
python build_dist.py
git add concepts/parallel-contingency-solve.md methods/reading-violationctg.md concepts/lodf.md dist/
git commit -m "Sync stale pages: exit owned instances, islanding is detectable outside ViolationCTG"
```

---

### Task 2: Field loader with a safe cache

**Files:**
- Create: `skills/schema-lookup/engine/schema.py`
- Create: `skills/schema-lookup/tests/conftest.py`
- Create: `skills/schema-lookup/tests/test_schema.py`
- Modify: `.gitignore`
- Modify: `commands/powerworld-setup.md` (step 2)

**Interfaces:**
- Consumes: `references/powerworld-object-fields-v25.xlsx`, sheet `ObjectFields`: column 0 Object Type (set only on an object's header row), 2 Key/Required marker, 3 Variable Name, 4 Concise, 5 Type, 6 Description, 7 Available Field List, 8 Enterable. Enterable values in the v25 export: blank (read-only), `Yes`, `Yes/Always`, `AUX/Paste`, `Depends: …`, `Edit Mode Only`, `???`.
- Produces: `Field` dataclass (`object, variable, concise, type, description, dialog_path, enterable, marker`; properties `key_index: int | None`, `is_required: bool`, `writable: str` ∈ `yes | aux-only | edit-mode | depends | read-only | unknown`); `SchemaError`; `load_fields(xlsx=DEFAULT_XLSX) -> dict[str, list[Field]]`; constants `KIT_ROOT`, `DEFAULT_XLSX`, `CACHE_DIR`; test hooks `_MEMO`, `_read_xlsx`, `_cache_path`.

Key markers are kept raw. The digit is the primary-key position; letters such as the `B` in `*2B*` are **undocumented** (the hub lists them as a gap), so nothing decodes them.

- [ ] **Step 1: Write conftest and the failing tests**

`skills/schema-lookup/tests/conftest.py`:

```python
import sys
from pathlib import Path

import pytest

ENGINE = Path(__file__).resolve().parents[1] / "engine"
sys.path.insert(0, str(ENGINE))


@pytest.fixture(scope="session")
def fields():
    import schema
    return schema.load_fields()
```

`skills/schema-lookup/tests/test_schema.py`:

```python
import os
import re
import shutil

import pytest

import schema


# ---- Task 2: loader and cache

def test_export_loads_all_objects(fields):
    assert len(fields) > 1000
    assert "Shunt" in fields and "CTG_Options" in fields


def test_field_record_shape(fields):
    by_var = {f.variable: f for f in fields["Sim_Solution_Options"]}
    f = by_var["DCPFMode"]
    assert f.concise == "DCApprox"
    assert f.writable == "yes"
    assert f.dialog_path.startswith("DC Approximation")


def test_key_and_required_markers(fields):
    by_var = {f.variable: f for f in fields["Shunt"]}
    assert by_var["BusNum"].key_index == 1
    assert by_var["ShuntID"].key_index == 2
    assert by_var["ShuntID"].marker.startswith("*2")
    assert by_var["SSCMode"].is_required
    assert by_var["BusName_NomVolt"].key_index is None


def test_writable_categories(fields):
    seen = {f.writable for fs in fields.values() for f in fs}
    assert {"yes", "aux-only", "depends", "read-only"} <= seen
    by_var = {f.variable: f for f in fields["Contingency"]}
    assert by_var["CTGSolutionOptions"].writable == "aux-only"


def test_missing_export_names_the_path(tmp_path):
    with pytest.raises(schema.SchemaError, match="nope.xlsx"):
        schema.load_fields(tmp_path / "nope.xlsx")


def test_missing_openpyxl_is_a_schema_error(tmp_path, monkeypatch):
    import builtins
    real_import = builtins.__import__

    def no_openpyxl(name, *a, **k):
        if name == "openpyxl":
            raise ImportError("no openpyxl")
        return real_import(name, *a, **k)

    monkeypatch.setattr(builtins, "__import__", no_openpyxl)
    with pytest.raises(schema.SchemaError, match="pip install openpyxl"):
        schema._read_xlsx(tmp_path / "any.xlsx")


def test_cache_rebuilt_when_export_changes(tmp_path, monkeypatch):
    src = tmp_path / "fields.xlsx"
    shutil.copy(schema.DEFAULT_XLSX, src)
    monkeypatch.setattr(schema, "CACHE_DIR", tmp_path / "cache")
    schema._MEMO.clear()

    first = schema.load_fields(src)
    assert list((tmp_path / "cache").glob("v*.json.gz")), "cache file not written"

    schema._MEMO.clear()
    monkeypatch.setattr(schema, "_read_xlsx", lambda p: pytest.fail("cache not used"))
    assert schema.load_fields(src).keys() == first.keys()

    st = src.stat()
    os.utime(src, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))
    schema._MEMO.clear()
    calls = []
    monkeypatch.setattr(schema, "_read_xlsx", lambda p: calls.append(p) or {"X": []})
    assert schema.load_fields(src) == {"X": []}
    assert calls, "changed export was served from the stale cache"


def test_corrupt_cache_falls_back_to_export(tmp_path, monkeypatch):
    src = tmp_path / "fields.xlsx"
    src.write_bytes(b"placeholder")
    monkeypatch.setattr(schema, "CACHE_DIR", tmp_path / "cache")
    schema._MEMO.clear()
    cache = schema._cache_path(src, src.stat())
    cache.parent.mkdir()
    cache.write_bytes(b"not gzip")
    monkeypatch.setattr(schema, "_read_xlsx", lambda p: {"Y": []})
    assert schema.load_fields(src) == {"Y": []}


def test_unwritable_cache_dir_still_answers(tmp_path, monkeypatch):
    src = tmp_path / "fields.xlsx"
    src.write_bytes(b"placeholder")
    blocker = tmp_path / "cache"
    blocker.write_text("a file where the cache directory should be")
    monkeypatch.setattr(schema, "CACHE_DIR", blocker)
    schema._MEMO.clear()
    monkeypatch.setattr(schema, "_read_xlsx", lambda p: {"Z": []})
    assert schema.load_fields(src) == {"Z": []}
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/schema-lookup/tests/test_schema.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'schema'`.

- [ ] **Step 3: Implement**

`skills/schema-lookup/engine/schema.py` (the `difflib` import is used from Task 3 on):

```python
"""Field lookup over PowerWorld's case-object field export (no PowerWorld needed)."""
from __future__ import annotations

import difflib
import gzip
import json
import os
import re
from dataclasses import asdict, dataclass
from pathlib import Path

KIT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_XLSX = KIT_ROOT / "references" / "powerworld-object-fields-v25.xlsx"
CACHE_DIR = Path(__file__).resolve().parent / ".cache"
_CACHE_VERSION = 1
_MEMO: dict[tuple, dict] = {}


class SchemaError(Exception):
    """The export is missing or unreadable, or a lookup cannot be answered."""


@dataclass(frozen=True)
class Field:
    object: str
    variable: str
    concise: str
    type: str
    description: str
    dialog_path: str
    enterable: str  # the export's raw Enterable cell; "" means read-only
    marker: str     # the export's raw Key/Required cell; "" if none

    @property
    def key_index(self) -> int | None:
        m = re.match(r"\*(\d)", self.marker)
        return int(m.group(1)) if m else None

    @property
    def is_required(self) -> bool:
        return "**" in self.marker

    @property
    def writable(self) -> str:
        """yes | aux-only | edit-mode | depends | read-only | unknown."""
        e = self.enterable
        if e in ("Yes", "Yes/Always"):
            return "yes"
        if e == "AUX/Paste":
            return "aux-only"
        if e == "Edit Mode Only":
            return "edit-mode"
        if e.startswith("Depends"):
            return "depends"
        if e == "":
            return "read-only"
        return "unknown"


def _s(v) -> str:
    if v is None:
        return ""
    return re.sub(r"\s+", " ", str(v)).strip().replace("�", "...")


def _read_xlsx(path: Path) -> dict[str, list[Field]]:
    try:
        import openpyxl
    except ImportError as e:
        raise SchemaError(
            "openpyxl is needed to read the field export: python -m pip install openpyxl"
        ) from e
    wb = openpyxl.load_workbook(path, read_only=True)
    objs: dict[str, list[Field]] = {}
    cur = None
    for row in wb.worksheets[0].iter_rows(min_row=2, values_only=True):
        r = tuple(row) + (None,) * (9 - len(row))
        if r[0]:
            cur = _s(r[0])
            objs[cur] = []
        elif r[3] and cur:
            objs[cur].append(Field(
                object=cur, variable=_s(r[3]), concise=_s(r[4]), type=_s(r[5]),
                description=_s(r[6]), dialog_path=_s(r[7]), enterable=_s(r[8]), marker=_s(r[2]),
            ))
    wb.close()
    return objs


def _cache_path(xlsx: Path, st: os.stat_result) -> Path:
    return CACHE_DIR / f"v{_CACHE_VERSION}-{xlsx.stem}-{st.st_size}-{st.st_mtime_ns}.json.gz"


def _read_cache(cache: Path) -> dict[str, list[Field]] | None:
    try:
        raw = json.loads(gzip.decompress(cache.read_bytes()))
        return {o: [Field(**f) for f in fs] for o, fs in raw.items()}
    except (OSError, ValueError, EOFError, TypeError, AttributeError):
        return None


def _write_cache(cache: Path, objs: dict[str, list[Field]]) -> None:
    """Best effort: a read-only install simply runs without a cache."""
    try:
        cache.parent.mkdir(parents=True, exist_ok=True)
        tmp = cache.with_name(f"{cache.name}.{os.getpid()}.tmp")
        payload = {o: [asdict(f) for f in fs] for o, fs in objs.items()}
        tmp.write_bytes(gzip.compress(json.dumps(payload).encode("utf-8")))
        os.replace(tmp, cache)
    except OSError:
        pass


def load_fields(xlsx: Path | str = DEFAULT_XLSX) -> dict[str, list[Field]]:
    """All objects and their fields, cached on disk by the export's size and mtime."""
    xlsx = Path(xlsx)
    if not xlsx.is_file():
        raise SchemaError(
            f"Field export not found: {xlsx}. The kit ships it as "
            f"references/powerworld-object-fields-v25.xlsx; pass --xlsx to use another export."
        )
    st = xlsx.stat()
    key = (str(xlsx.resolve()), st.st_size, st.st_mtime_ns)
    if key in _MEMO:
        return _MEMO[key]
    cache = _cache_path(xlsx, st)
    objs = _read_cache(cache) if cache.is_file() else None
    if objs is None:
        objs = _read_xlsx(xlsx)
        _write_cache(cache, objs)
    _MEMO[key] = objs
    return objs
```

Append to `.gitignore`:

```
# schema-lookup engine: rebuilt from the field export on first use
skills/*/engine/.cache/
```

In `commands/powerworld-setup.md` step 2, change the install line to

```bash
python -m pip install --upgrade esapp TeamOverbyeWeather pywin32 openpyxl
```

and add under it, after the `pywin32` bullet:

```markdown
- `openpyxl` reads the PowerWorld field export behind the `schema-lookup` skill.
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/schema-lookup/tests/test_schema.py -v`
Expected: 9 passed. The first run reads the xlsx (tens of seconds); later runs hit the cache.

- [ ] **Step 5: Commit**

```bash
git add skills/schema-lookup/engine/schema.py skills/schema-lookup/tests/conftest.py skills/schema-lookup/tests/test_schema.py .gitignore commands/powerworld-setup.md
git commit -m "Add the schema-lookup field loader with a versioned, atomic cache"
```

---

### Task 3: Object and field lookups

**Files:**
- Modify: `skills/schema-lookup/engine/schema.py` (append)
- Modify: `skills/schema-lookup/tests/test_schema.py` (append)

**Interfaces:**
- Consumes: `load_fields`, `Field`, `SchemaError` (Task 2).
- Produces: `UnknownObject(SchemaError)` with `.name`, `.suggestions: list[str]`; `resolve_object(name, fields=None) -> str`; `object_fields(name, fields=None) -> list[Field]`; `keys(name, fields=None) -> list[Field]` (key order); `required(name, fields=None) -> list[Field]`; `normalize_field_name(name) -> str`; `find_field(obj, name, fields=None) -> Field | None`; `close_field_names(obj, name, fields=None) -> list[str]` (spelling neighbours only); `split_words(name) -> list[str]`.

- [ ] **Step 1: Write the failing tests** (append to `test_schema.py`)

```python
# ---- Task 3: lookups

def test_shunt_keys_required_and_area_fields(fields):
    assert [f.variable for f in schema.keys("Shunt", fields)] == ["BusNum", "ShuntID"]
    req = {f.variable for f in schema.required("Shunt", fields)}
    assert {"SSCMode", "SSNMVR", "SSStatus"} <= req
    own = schema.find_field("Shunt", "AreaNum", fields)
    bus = schema.find_field("Shunt", "AreaNum:1", fields)
    assert own.writable == "yes" and "of Shunt" in own.dialog_path
    assert bus.writable == "read-only" and "of Bus" in bus.dialog_path


def test_resolve_object_case_insensitive(fields):
    assert schema.resolve_object("ctg_options", fields) == "CTG_Options"


def test_unknown_object_suggests(fields):
    with pytest.raises(schema.UnknownObject) as e:
        schema.resolve_object("Shunts", fields)
    assert "Shunt" in e.value.suggestions
    assert "Shunt" in str(e.value)


def test_find_field_colon_python_and_concise_forms(fields):
    a = schema.find_field("Sim_Solution_Options", "MaxItr:1", fields)
    b = schema.find_field("Sim_Solution_Options", "MaxItr__1", fields)
    c = schema.find_field("Sim_Solution_Options", "MaxItrVoltLoop", fields)
    assert a is not None and a == b == c
    assert a.variable == "MaxItr:1"


def test_concise_name_is_the_same_field(fields):
    assert schema.find_field("Sim_Solution_Options", "DCApprox", fields).variable == "DCPFMode"


def test_absent_field_returns_none(fields):
    assert schema.find_field("OPF_Options", "SCOPFMaxInnerLoopItr", fields) is None


def test_split_words():
    assert schema.split_words("SCOPFMaxInnerLoopItr") == ["scopf", "max", "inner", "loop", "itr"]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/schema-lookup/tests/test_schema.py -v`
Expected: the 7 new tests FAIL with `AttributeError: module 'schema' has no attribute …`.

- [ ] **Step 3: Implement** (append to `schema.py`)

```python
class UnknownObject(SchemaError):
    def __init__(self, name: str, suggestions: list[str]):
        self.name = name
        self.suggestions = suggestions
        hint = f" Did you mean: {', '.join(suggestions)}?" if suggestions else ""
        super().__init__(f"No object type {name!r} in the field export.{hint}")


def resolve_object(name: str, fields: dict | None = None) -> str:
    fields = fields if fields is not None else load_fields()
    if name in fields:
        return name
    lower = {o.lower(): o for o in fields}
    if name.lower() in lower:
        return lower[name.lower()]
    near = difflib.get_close_matches(name.lower(), list(lower), n=3, cutoff=0.6)
    raise UnknownObject(name, [lower[n] for n in near])


def object_fields(name: str, fields: dict | None = None) -> list[Field]:
    fields = fields if fields is not None else load_fields()
    return fields[resolve_object(name, fields)]


def keys(name: str, fields: dict | None = None) -> list[Field]:
    return sorted((f for f in object_fields(name, fields) if f.key_index), key=lambda f: f.key_index)


def required(name: str, fields: dict | None = None) -> list[Field]:
    return [f for f in object_fields(name, fields) if f.is_required]


def normalize_field_name(name: str) -> str:
    """Accept the Python attribute spelling: MaxItr__1 -> MaxItr:1."""
    return re.sub(r"__(\d+)$", r":\1", name.strip())


def find_field(obj: str, name: str, fields: dict | None = None) -> Field | None:
    """Match on variable name first, then concise name, case-insensitively."""
    want = normalize_field_name(name).lower()
    fs = object_fields(obj, fields)
    for f in fs:
        if f.variable.lower() == want:
            return f
    for f in fs:
        if f.concise and f.concise.lower() == want:
            return f
    return None


def close_field_names(obj: str, name: str, fields: dict | None = None) -> list[str]:
    """Spelling neighbours only — not substitutes for the field that was asked for."""
    names = [f.variable for f in object_fields(obj, fields)]
    return difflib.get_close_matches(normalize_field_name(name), names, n=3, cutoff=0.6)


def split_words(name: str) -> list[str]:
    """SCOPFMaxInnerLoopItr -> ['scopf', 'max', 'inner', 'loop', 'itr']."""
    parts = re.findall(r"[A-Z]+(?=[A-Z][a-z])|[A-Z]?[a-z]+|[A-Z]+|\d+", name)
    return [p.lower() for p in parts]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/schema-lookup/tests/test_schema.py -v`
Expected: 16 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/schema-lookup/engine/schema.py skills/schema-lookup/tests/test_schema.py
git commit -m "Add object and field lookups: keys, required, concise and colon names"
```

---

### Task 4: Search across the export

**Files:**
- Modify: `skills/schema-lookup/engine/schema.py` (append)
- Modify: `skills/schema-lookup/tests/test_schema.py` (append)

**Interfaces:**
- Consumes: `load_fields`, `object_fields`, `Field`.
- Produces: `search(query, obj=None, limit=20, fields=None) -> list[Field]`, ranked by query terms matched anywhere, then terms matched in the names, then object and variable name.

- [ ] **Step 1: Write the failing tests** (append)

```python
# ---- Task 4: search

def test_search_finds_island_reporting(fields):
    top = [f.variable for f in schema.search("island violations", obj="CTG_Options", fields=fields)[:3]]
    assert "Include" in top


def test_search_across_all_objects_respects_limit(fields):
    assert len(schema.search("voltage", limit=7, fields=fields)) == 7
    assert len({f.object for f in schema.search("voltage", limit=50, fields=fields)}) > 1


def test_search_empty_query_returns_nothing(fields):
    assert schema.search("  ", fields=fields) == []
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/schema-lookup/tests/test_schema.py -v`
Expected: 3 new tests FAIL with `AttributeError: module 'schema' has no attribute 'search'`.

- [ ] **Step 3: Implement** (append to `schema.py`)

```python
def search(query: str, obj: str | None = None, limit: int = 20,
           fields: dict | None = None) -> list[Field]:
    terms = [t for t in re.split(r"\W+", query.lower()) if t]
    if not terms:
        return []
    fields = fields if fields is not None else load_fields()
    pool = object_fields(obj, fields) if obj else [f for fs in fields.values() for f in fs]
    scored = []
    for f in pool:
        names = f"{f.variable} {f.concise}".lower()
        text = f"{names} {f.dialog_path} {f.description}".lower()
        hits = sum(t in text for t in terms)
        if hits:
            scored.append((-hits, -sum(t in names for t in terms), f.object, f.variable, f))
    scored.sort(key=lambda s: s[:4])
    return [s[4] for s in scored[:limit]]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/schema-lookup/tests/test_schema.py -v`
Expected: 19 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/schema-lookup/engine/schema.py skills/schema-lookup/tests/test_schema.py
git commit -m "Add ranked search across the field export"
```

---

### Task 5: What the hub says, verbatim

**Files:**
- Create: `skills/schema-lookup/engine/hub.py`
- Create: `skills/schema-lookup/tests/test_hub.py`

**Interfaces:**
- Consumes: `find_field`, `KIT_ROOT` (schema); `references/powerworld-study-options.md`.
- Produces: `HubRow` dataclass (`section`, `text`, `tag`, `match` ∈ `exact | name`); `hub_rows(obj, field_name, fields=None, hub=HUB) -> list[HubRow]` (exact first); `hub_passages(words, hub=HUB, limit=3) -> list[str]`.

Why verbatim: the hub's tags rate a **row's claim** — a recipe, a trap, a decoy — not a field. Turning them into a per-field level tagged `CTG_ReportMonitoredAreas` "verified" from the row that calls it a decoy (found in review). Rows are returned as written; `match` says whether the row names `Object.Field` (`exact`) or only the bare field name (`name`, which may concern another object). A tag exists only for tables whose header's last cell is `tag`.

- [ ] **Step 1: Write the failing tests**

`skills/schema-lookup/tests/test_hub.py`:

```python
import schema
from hub import hub_passages, hub_rows


def test_exact_row_for_dotted_field(fields):
    rows = hub_rows("Area", "BGAGC", fields)
    assert rows and rows[0].match == "exact"
    assert any(r.tag.startswith("V") for r in rows)


def test_untagged_table_rows_carry_no_tag(fields):
    glance = [r for r in hub_rows("Area", "BGAGC", fields) if r.section == "Every study at a glance"]
    assert glance and all(r.tag == "" for r in glance)


def test_other_objects_dotted_row_is_not_returned(fields):
    rows = hub_rows("SuperArea", "BGAGC", fields)
    assert [r.tag[:1] for r in rows] == ["S"]


def test_decoy_text_reaches_the_reader(fields):
    rows = hub_rows("CTG_Options", "CTG_ReportMonitoredAreas", fields)
    assert any("decoy" in r.text for r in rows)


def test_no_exact_claim_for_same_name_on_another_object(fields):
    for obj, fld in [("Contingency", "GenMW"), ("Load", "GenCostCurvePoints"), ("Gen", "BusPUVolt")]:
        assert schema.find_field(obj, fld, fields) is not None, (obj, fld)
        assert not [r for r in hub_rows(obj, fld, fields) if r.match == "exact"], (obj, fld)


def test_field_absent_from_hub_returns_nothing(fields):
    assert hub_rows("Substation", "NERCCIP14AggWeight", fields) == []


def test_field_absent_from_export_returns_nothing(fields):
    assert hub_rows("OPF_Options", "SCOPFMaxInnerLoopItr", fields) == []


def test_passages_answer_the_inner_loop_question():
    top = hub_passages(schema.split_words("SCOPFMaxInnerLoopItr"))
    assert top and "OPF_MaxLPIterations" in top[0]
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/schema-lookup/tests/test_hub.py -v`
Expected: collection error `ModuleNotFoundError: No module named 'hub'`.

- [ ] **Step 3: Implement**

`skills/schema-lookup/engine/hub.py`:

```python
"""What the curated study-options page says about a field — verbatim, never summarised.

The hub's tags rate a row's claim (a recipe, a trap, a decoy), not a field, so this module
returns the rows themselves and leaves the reading to whoever asked.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from schema import KIT_ROOT, find_field

HUB = KIT_ROOT / "references" / "powerworld-study-options.md"


@dataclass(frozen=True)
class HubRow:
    section: str  # nearest heading above the row
    text: str     # the row's cells joined with " | ", tag excluded
    tag: str      # the row's tag cell verbatim, "" when its table has no tag column
    match: str    # "exact": the row names Object.Field; "name": only the bare field name


def _tokens(text: str) -> list[str]:
    """Backticked names, reduced to their first word before any '='."""
    out = []
    for t in re.findall(r"`([^`]+)`", text):
        words = t.split()
        if words:
            out.append(words[0].split("=")[0])
    return out


def _cells(line: str) -> list[str]:
    return [c.strip() for c in re.split(r"(?<!\\)\|", line)[1:-1]]


def _table_rows(hub: Path):
    """(section, body cells, tag) per data row. Only a table whose header ends in 'tag' has tags."""
    section, header, prev_table = "", None, False
    for line in hub.read_text(encoding="utf-8").splitlines():
        is_table = line.startswith("|")
        if line.startswith("#"):
            section = line.lstrip("#").strip()
        elif is_table and not prev_table:
            header = _cells(line)
        elif is_table and not re.match(r"^\|[\s|:-]+\|$", line):
            cells = _cells(line)
            if header and header[-1].lower() == "tag":
                yield section, cells[:-1], cells[-1]
            else:
                yield section, cells, ""
        prev_table = is_table


def hub_rows(obj: str, field_name: str, fields: dict | None = None, hub: Path = HUB) -> list[HubRow]:
    """Hub table rows that name this field: exact Object.Field matches first."""
    f = find_field(obj, field_name, fields)
    if f is None:
        return []
    names = {n for n in (f.variable, f.concise) if n}
    found = []
    for section, cells, tag in _table_rows(hub):
        body = " | ".join(cells)
        match = ""
        for tok in _tokens(body):
            if "." in tok:
                o, fld = tok.split(".", 1)
                if o.lower() == f.object.lower() and fld in names:
                    match = "exact"
                    break
            elif tok in names:
                match = "name"
        if match:
            found.append(HubRow(section, body, tag, match))
    return sorted(found, key=lambda r: r.match != "exact")


def hub_passages(words: list[str], hub: Path = HUB, limit: int = 3) -> list[str]:
    """Paragraphs and table rows mentioning at least two of `words`, most matches first."""
    words = [w.lower() for w in words if len(w) >= 3]
    blocks, para = [], []
    for line in hub.read_text(encoding="utf-8").splitlines():
        if line.startswith("|"):
            blocks.append(line)
        elif line.strip() and not line.startswith("#"):
            para.append(line.strip())
            continue
        if para:
            blocks.append(" ".join(para))
            para = []
    if para:
        blocks.append(" ".join(para))
    scored = [(sum(w in b.lower() for w in set(words)), i, b) for i, b in enumerate(blocks)]
    scored = [s for s in scored if s[0] >= 2]
    scored.sort(key=lambda s: (-s[0], s[1]))
    return [s[2] for s in scored[:limit]]
```

- [ ] **Step 4: Run to verify pass**

Run: `python -m pytest skills/schema-lookup/tests/test_hub.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/schema-lookup/engine/hub.py skills/schema-lookup/tests/test_hub.py
git commit -m "Add the hub reader: study-options rows and passages, verbatim"
```

---

### Task 6: The lookup CLI

**Files:**
- Create: `skills/schema-lookup/engine/lookup.py`
- Create: `skills/schema-lookup/tests/test_lookup_cli.py`

**Interfaces:**
- Consumes: `schema`, `hub`.
- Produces: `python <KIT>/skills/schema-lookup/engine/lookup.py [--xlsx PATH] object <Obj> | field <Obj> <Field> | search <query> [--object Obj] [--limit N]`. Exit 0 = answered; 1 = field not in the export (spelling neighbours plus hub passages printed); 2 = unknown object, missing export or missing openpyxl. `main(argv=None) -> int`. Plan 3 calls this CLI rather than importing the engine, so the name `schema` never meets the PyPI package of the same name.

- [ ] **Step 1: Write the failing tests**

`skills/schema-lookup/tests/test_lookup_cli.py`:

```python
import os
import subprocess
import sys
from pathlib import Path

LOOKUP = Path(__file__).resolve().parents[1] / "engine" / "lookup.py"


def run(*args, env_extra=None, cwd=None):
    env = {**os.environ, **(env_extra or {})}
    p = subprocess.run([sys.executable, str(LOOKUP), *args], capture_output=True, env=env, cwd=cwd)
    return p.returncode, p.stdout.decode("utf-8"), p.stderr.decode("utf-8", "replace")


def test_object_lists_keys_required_and_writability():
    code, out, _ = run("object", "Shunt")
    assert code == 0
    assert "keys (in order): BusNum, ShuntID" in out
    assert "SSCMode" in out and "SSNMVR" in out and "SSStatus" in out
    assert "read-only" in out


def test_field_prints_concise_marker_and_hub_rows():
    code, out, _ = run("field", "CTG_Options", "IslandViolations")
    assert code == 0
    assert "CTG_Options.Include  (concise: IslandViolations)" in out
    assert "[exact]" in out and "tag D, fires live" in out


def test_field_shows_decoy_verbatim():
    code, out, _ = run("field", "CTG_Options", "CTG_ReportMonitoredAreas")
    assert code == 0 and "decoy" in out


def test_field_not_on_hub_says_so():
    code, out, _ = run("field", "Substation", "NERCCIP14AggWeight")
    assert code == 0 and "field export only" in out


def test_absent_field_exit_1_points_at_the_real_answer():
    code, out, _ = run("field", "OPF_Options", "SCOPFMaxInnerLoopItr")
    assert code == 1
    assert "not substitutes" in out
    assert "OPF_MaxLPIterations" in out


def test_unknown_object_exit_2():
    code, _, err = run("object", "Shunts")
    assert code == 2 and "Did you mean" in err


def test_search_prints_one_line_per_hit():
    code, out, _ = run("search", "island violations", "--object", "CTG_Options", "--limit", "3")
    assert code == 0
    assert len([l for l in out.splitlines() if l.startswith("- ")]) == 3


def test_cli_missing_export_exit_2(tmp_path):
    code, _, err = run("--xlsx", str(tmp_path / "gone.xlsx"), "object", "Shunt")
    assert code == 2 and "gone.xlsx" in err


def test_cli_survives_cp1252_console():
    code, out, _ = run("field", "Substation", "NERCCIP14AggWeight", env_extra={"PYTHONIOENCODING": "cp1252"})
    assert code == 0
    assert "≥" in out


def test_cli_runs_from_outside_the_kit(tmp_path):
    code, out, _ = run("object", "Shunt", cwd=tmp_path)
    assert code == 0 and "BusNum" in out
```

- [ ] **Step 2: Run to verify failure**

Run: `python -m pytest skills/schema-lookup/tests/test_lookup_cli.py -v`
Expected: all 10 FAIL (`can't open file … lookup.py`).

- [ ] **Step 3: Implement**

`skills/schema-lookup/engine/lookup.py`:

```python
"""Which PowerWorld object, field or command — from the field export and the study-options hub.

    python lookup.py object Shunt
    python lookup.py field CTG_Options Include
    python lookup.py search "island violations" --object CTG_Options --limit 5
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import schema  # noqa: E402
from hub import hub_passages, hub_rows  # noqa: E402

WRITABLE = ("yes", "aux-only", "edit-mode", "depends", "read-only", "unknown")


def _role(f: schema.Field) -> str:
    if f.key_index:
        return f"key {f.key_index}"
    if f.is_required:
        return "required to create"
    return "-"


def show_object(name: str, fields: dict) -> str:
    obj = schema.resolve_object(name, fields)
    fs = fields[obj]
    count = Counter(f.writable for f in fs)
    return "\n".join([
        f"## {obj}  ({len(fs)} fields)",
        f"keys (in order): {', '.join(f.variable for f in schema.keys(obj, fields)) or 'none (single-record object)'}",
        f"required to create: {', '.join(f.variable for f in schema.required(obj, fields)) or 'none'}",
        "writable: " + "   ".join(f"{w} {count[w]}" for w in WRITABLE if count[w]),
    ])


def show_field(obj: str, name: str, fields: dict) -> tuple[int, str]:
    obj = schema.resolve_object(obj, fields)
    f = schema.find_field(obj, name, fields)
    if f is None:
        near = schema.close_field_names(obj, name, fields)
        lines = [
            f"{obj} has no field {name!r} in the field export.",
            f"spelling neighbours (not substitutes): {', '.join(near) or 'none'}",
        ]
        passages = hub_passages(schema.split_words(schema.normalize_field_name(name)))
        if passages:
            lines.append("the study-options hub on these words:")
            lines += [f"  > {p}" for p in passages]
        return 1, "\n".join(lines)
    concise = f"  (concise: {f.concise})" if f.concise and f.concise != f.variable else ""
    lines = [
        f"{obj}.{f.variable}{concise}",
        f"type: {f.type}   writable: {f.writable} ({f.enterable or 'blank'})   "
        f"role: {_role(f)}   marker: {f.marker or '-'}",
        f"dialog: {f.dialog_path}",
        f"description: {f.description}",
    ]
    rows = hub_rows(obj, f.variable, fields)
    if rows:
        lines.append("hub rows (verbatim; 'name' rows may concern another object):")
        lines += [f"  [{r.match}] {r.section} :: {r.text} :: tag {r.tag}" for r in rows]
    else:
        lines.append("hub: not mentioned - field export only, behaviour not tested here")
    return 0, "\n".join(lines)


def show_search(query: str, obj: str | None, limit: int, fields: dict) -> str:
    hits = schema.search(query, obj=obj, limit=limit, fields=fields)
    if not hits:
        return f"no field matches {query!r}"
    lines = []
    for f in hits:
        concise = f" ({f.concise})" if f.concise and f.concise != f.variable else ""
        lines.append(f"- {f.object}.{f.variable}{concise} [{f.writable}] - {f.dialog_path}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--xlsx", default=str(schema.DEFAULT_XLSX), help="field export to read")
    sub = ap.add_subparsers(dest="cmd", required=True)
    o = sub.add_parser("object")
    o.add_argument("name")
    fl = sub.add_parser("field")
    fl.add_argument("object")
    fl.add_argument("name")
    s = sub.add_parser("search")
    s.add_argument("query")
    s.add_argument("--object")
    s.add_argument("--limit", type=int, default=20)
    a = ap.parse_args(argv)
    try:
        fields = schema.load_fields(a.xlsx)
        if a.cmd == "object":
            print(show_object(a.name, fields))
            return 0
        if a.cmd == "field":
            code, text = show_field(a.object, a.name, fields)
            print(text)
            return code
        print(show_search(a.query, a.object, a.limit, fields))
        return 0
    except schema.SchemaError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 4: Run the whole suite**

Run: `python -m pytest skills/schema-lookup/tests -v`
Expected: 37 passed.

- [ ] **Step 5: Commit**

```bash
git add skills/schema-lookup/engine/lookup.py skills/schema-lookup/tests/test_lookup_cli.py
git commit -m "Add the schema-lookup CLI: object, field and search"
```

---

### Task 7: Confirm plugin agents load, then write the skill and agent

**Files:**
- Create: `skills/schema-lookup/SKILL.md`
- Create: `agents/schema-librarian.md`

**Interfaces:**
- Consumes: the CLI (Task 6); `references/powerworld-study-options.md`, `references/powerworld-study-commands.md`.
- Produces: skill `schema-lookup` and agent `schema-librarian`, which Plan 3's configure phase calls.

- [ ] **Step 1: Write the agent file**

`agents/schema-librarian.md`:

```markdown
---
name: schema-librarian
description: "PowerWorld reference desk. Answers which object, field or SCRIPT command to use, and shows what the kit's study pages say about it, from the kit's field export. Use for 'which field do I set for…', 'what does a shunt/area/contingency need', 'is there an option for…'. Never opens a case."
tools: Bash, Read, Grep, Glob
model: haiku
---

You are the schema librarian for the PoWerHiveMind kit.

Read `skills/schema-lookup/SKILL.md` under the kit root and follow it exactly; it is the whole
procedure and says how to find the kit root.

You hold Bash, so "read-only" is your rule to keep, not a sandbox: run only the lookup CLI and
read-only file commands. Never run anything that opens PowerWorld or writes a file.

Return only the answer block the skill defines — no search logs, no tool dumps. One block per
field asked about. If the export has no such field, say so and show what the tool printed.
```

- [ ] **Step 2: Confirm Claude Code discovers plugin agents (spec §13) — before anything claims it**

This needs a human in Claude Code. The published marketplace points at GitHub, which lags this working tree, so load the **local** tree:

1. Start Claude Code with this working tree as a plugin: `claude --plugin-dir <path-to-your-clone>` (check the flag name in `claude --help`; if absent, add the working tree as a local marketplace with `/plugin marketplace add <path-to-your-clone>` and install from it).
2. Run `/agents`. Expected: `schema-librarian` listed under `powerhivemind`.

If it is **not** listed, stop and report: Plans 2–4 assume `agents/` loads, and the spec's layout changes first. Record the result and the Claude Code version for the Task 8 commit message.

- [ ] **Step 3: Write the skill**

`skills/schema-lookup/SKILL.md`:

````markdown
---
name: schema-lookup
description: "Answer which PowerWorld object, field or SCRIPT command to use, and show what the kit's study pages say about it. Use when the user asks which field holds something, what the key or required fields of an object are, how to set an option (iterations, island reporting, SCOPF loops, DC mode), what a field or concise name means, or whether a field exists at all - e.g. 'which parameter do I set for...', 'what fields does a shunt need', 'is there a setting for...'."
---

# Schema lookup

Answer from the kit's own sources, never from memory. PowerWorld has about 1,000 object types
and 100,000 fields; a guessed field name fails silently.

## 0. Resolve the kit root once

`KIT` is `${CLAUDE_PLUGIN_ROOT}` when the kit is installed as a Claude Code plugin; anywhere else
it is the directory holding `AGENTS.md`. Resolve it to an absolute path first. Every command below
uses `"$KIT/..."`; a bare `skills/...` path runs against the user's working directory and fails.

## 1. Look it up

```
python "$KIT/skills/schema-lookup/engine/lookup.py" object <Object>
python "$KIT/skills/schema-lookup/engine/lookup.py" field <Object> <Field>
python "$KIT/skills/schema-lookup/engine/lookup.py" search "<words>" [--object <Object>] [--limit 10]
```

- Don't know the object? `search` without `--object`, then `object` on the best hit.
- A field may be given by variable name (`DCPFMode`), concise name (`DCApprox`) or Python
  spelling (`MaxItr__1`); all resolve to one field.
- Exit 2 with "pip install openpyxl": tell the user to run it (or `/powerhivemind:powerworld-setup`).

## 2. Read what the tool printed about the hub

`field` prints the rows of `references/powerworld-study-options.md` that name the field, verbatim:

- `[exact]` rows name `Object.Field` — they are about this field.
- `[name]` rows only mention the bare name and **may concern another object**. Read the row before
  using it.
- The row's words decide the answer. A row that says **decoy** or **trap** overrides everything else;
  the tag (`V` verified on a live case, `D` documented, `S` schema only) rates the row's claim.
- No hub rows: say "field export only — PowerWorld describes it; its behaviour is untested here".

For exact SCRIPT syntax and defaults, read `$KIT/references/powerworld-study-commands.md`,
including its "Surprises" section before recommending any command.

## 3. When the field does not exist

Exit 1. The tool prints **spelling neighbours — not substitutes** — and the hub passages that match
the words of the request. Offer a real alternative only if a hub passage names it (e.g. "no SCOPF
inner loop; the per-LP limit is `OPF_MaxLPIterations`"). Never present a spelling neighbour as the
answer.

## 4. Answer in this shape

```
<Object>.<Field>  (concise: …)      type · writable · role (key 1 / required / -)
what it does: <one line, from the description>
how to set it: SetData(<Object>, [<Field>], [<value>]);   — then read it back
the kit says: <the hub row, quoted, with its tag> | field export only
```

For "what do I need to create an X": the keys in order and the required fields.

## Never

- Never open, solve or write a case; never run anything but this CLI and read-only commands.
- Never state a field that the tool did not return.
- Never summarise a hub row into a confidence word; quote it.
````

- [ ] **Step 4: Verify the skill's commands from outside the kit**

Run (from the repository root, pointing the tool at an absolute path as the skill does):
`python "$(pwd)/skills/schema-lookup/engine/lookup.py" field CTG_Options IslandViolations`
Expected: `CTG_Options.Include  (concise: IslandViolations)` and a line containing `[exact]` and `tag D, fires live`.

Run: `python -m pytest skills/schema-lookup/tests -v`
Expected: 37 passed (includes `test_cli_runs_from_outside_the_kit`).

- [ ] **Step 5: Commit**

```bash
git add skills/schema-lookup/SKILL.md agents/schema-librarian.md
git commit -m "Add the schema-lookup skill and schema-librarian agent"
```

---

### Task 8: Registration

**Files:**
- Modify: `README.md` (~line 134), `AGENTS.md` (~line 140), `GEMINI.md` (regenerated), `CHANGELOG.md` (`## Unreleased`)

**Interfaces:**
- Consumes: Tasks 1–7.
- Produces: the kit's user-facing docs list the new skill and agent.

- [ ] **Step 1: README**

Replace

```
Code loads `skills/powerworld/SKILL.md`, `skills/knowledge-base-page/SKILL.md` and
`skills/violation-map/SKILL.md`, and
```

with

```
Code loads `skills/powerworld/SKILL.md`, `skills/knowledge-base-page/SKILL.md`,
`skills/violation-map/SKILL.md` and `skills/schema-lookup/SKILL.md`, registers the
`schema-librarian` agent from `agents/`, and
```

- [ ] **Step 2: AGENTS.md routing row**

Add after the `violation-map` row:

```
| Which object, field or command to use, and what the kit says about it | `python "$KIT/skills/schema-lookup/engine/lookup.py"`, see [skills/schema-lookup/SKILL.md](skills/schema-lookup/SKILL.md) |
```

- [ ] **Step 3: Regenerate GEMINI.md**

GEMINI.md is a header comment followed by a verbatim copy of AGENTS.md, and it is already several commits behind (it lacks the `$KIT` path fix and two routing rows). Regenerate it:

Run: `python -c "import pathlib;g=pathlib.Path('GEMINI.md');a=pathlib.Path('AGENTS.md').read_text(encoding='utf-8');t=g.read_text(encoding='utf-8');g.write_text(t[:t.index('-->')+3]+'\n\n'+a,encoding='utf-8')"`

Run: `python -c "import pathlib;t=pathlib.Path('GEMINI.md').read_text(encoding='utf-8');print(t[t.index('-->')+3:].lstrip('\n')==pathlib.Path('AGENTS.md').read_text(encoding='utf-8'))"`
Expected: `True`

- [ ] **Step 4: CHANGELOG**

Add as the first bullet under `## Unreleased`:

```markdown
- **A fourth skill, `schema-lookup`, and the kit's first agent, `schema-librarian`.** Answers which
  PowerWorld object, field or SCRIPT command to use from the Simulator 25 field export
  (`references/powerworld-object-fields-v25.xlsx`), and prints what
  `references/powerworld-study-options.md` says about the field verbatim — including rows that
  call a field a decoy or a trap. Key fields, required fields, writability, concise and colon
  names, and a ranked search across ~100,000 fields; no PowerWorld needed. `powerworld-setup` now
  installs `openpyxl`. Also fixed: two pages still said islanding is undetectable after
  `CTGSolveAll`, and the parallel-contingency page lacked the rule to `.exit()` instances you own.
```

- [ ] **Step 5: Verify, rebuild dist, commit**

Run: `python -m pytest skills/schema-lookup/tests -q`
Expected: 37 passed.

```bash
python build_dist.py
git add README.md AGENTS.md GEMINI.md CHANGELOG.md dist/
git commit -m "Register the schema-lookup skill and schema-librarian agent

Plugin agent discovery (Task 7 Step 2): <listed | not listed>, Claude Code <version>."
```

Do not push: see Global Constraints.

---

## Revision record

Revision 1 was reviewed in series — architect, then critic with the architect's findings. Adopted:

| change | from |
|---|---|
| Confidence levels replaced by verbatim hub rows (`hub.py`), with negative tests; a level mapping tagged a decoy "verified" | architect #1, critic C1 |
| Absent field: spelling neighbours labelled "not substitutes" plus hub passages, so "SCOPF inner loop" surfaces `OPF_MaxLPIterations` | architect #8, critic C2 |
| Alternate-key decoding dropped; raw marker printed (letters are undocumented) | architect #3, critic C3 |
| Skill commands use an absolute kit root; CLI test from outside the kit | architect #4, critic C4 |
| Task 1 also retitles the islanding heading, fixes the line-252 sentence, and fixes `concepts/lodf.md` | architect #6, critic C5 |
| openpyxl added to setup; missing openpyxl is a clean error | architect #5, critic C6 |
| Versioned, atomic cache; corrupt cache and read-only install fall back to the export | architect #9, critic C7 |
| Writability from the real value set (7 categories), `show_object` counts all of them | architect #10, critic C8 |
| Agent discovery checked on a local plugin load, before any doc claims it | architect #11, critic C9 |
| CHANGELOG entry; GEMINI.md regenerated | architect #11, critic C10 |
| Redistribution decision gates the push, not the build | architect #7, critic C11 |

Rejected: shipping a prebuilt cache (git resets mtime, so it would never hit, and it is a second copy of the export); a parser for key-marker letters; a hub row-count contract test (made unnecessary by verbatim rows); `field --json` before Plan 3 needs it.

Found while dry-running revision 2: the hub's "every study at a glance" table has commands, not tags, in its last column; `hub.py` reads a tag only when the table header's last cell is `tag` (`test_untagged_table_rows_carry_no_tag`).
