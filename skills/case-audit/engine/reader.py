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


def _is_powerworld_error(e: Exception) -> bool:
    """esapp's PowerWorldError or a subclass: the solve failed, which is the case's answer. Matched by
    class name down the MRO so reader.py needs no second esapp name, which the read-only guard would
    have to allow. Anything else (COM failure, a bug) is the engine's break and propagates."""
    return any(c.__name__ == "PowerWorldError" for c in type(e).__mro__)


def read_case(case: str | Path) -> CaseData:
    path = Path(os.path.abspath(case))             # PowerWorld resolves relative paths against its own folder
    if not path.is_file():
        raise ReadError(f"case not found: {path}")
    try:
        from esapp import PowerWorld
    except ImportError as e:
        raise ReadError("esapp is not installed: run /powerhivemind:powerworld-setup") from e
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
        except Exception as e:
            if not _is_powerworld_error(e):       # an engine break, not the case's fault
                raise
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
