"""Audit a PowerWorld case, read-only: is it sane, and can it run the studies asked for?

    python audit.py --case <case.pwb> [--profiles base,timestep,opf,lint] [--pww <file.pww>] [--out <dir>]

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
VALID_PROFILES = ("base", "timestep", "opf", "lint")  # the same tuple as checks.VALID_PROFILES (tested)


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
    ap.add_argument("--profiles", type=_profiles, default=["base"], help="comma list of base,timestep,opf,lint")
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
                      "Run /powerhivemind:powerworld-setup, then ask for the audit again")
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
