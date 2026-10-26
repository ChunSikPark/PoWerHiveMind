---
type: method
domain: tooling
topic: scripting
aliases: [preflight, preflight-powerworld, powerworld-check, simauto-check, license-check]
tags: [powerworld, simauto, esapp, setup, troubleshooting, preflight]
---

# Method: Preflight — is PowerWorld actually usable here?

## Abstract

Run this before writing any analysis code. It takes about five seconds and answers one
question: can this machine drive PowerWorld from Python at all? Five checks, each with
the exact error you get when it fails and what that error means. Skipping this is why an agent writes two hundred lines
of a study and then discovers on the last line that SimAuto was never licensed.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [esapp-overview](esapp-overview.md) · [powerworld-simauto](../concepts/powerworld-simauto.md) · [esapp](../concepts/esapp.md)
- **Next:** [esapp-overview](esapp-overview.md) once every check passes

## Content

> **Agents: run this first.** Do not write analysis code before the preflight passes.
> A failure here is a fact about the machine, not a bug in your code, and no amount of
> rewriting the analysis will fix it. Report which check failed and stop.

### The preflight script

Paste this and run it. It prints a line per check and stops at the first failure.

**Run it with plain `python`, never `python -I`.** Isolated mode hides the user
site-packages, which is where `pip install --user` puts esapp, so check 3 reports esapp
missing when it is installed. In a 2026-10-20 validation run two agents hit exactly that and
then ran `pip install` on a shared machine unasked. If esapp really is missing, tell the user
to run `/powerhivemind:powerworld-setup` (it installs esapp, TeamOverbyeWeather,
pywin32 and openpyxl). **Never pip-install on your own.**

Checks 1-4 are about the **machine** and need no case file; check 5 opens **your case**.
Call `preflight_machine()` on its own when you do not have a case yet (during setup, say),
and `preflight(case_path)` when you do.

```python
"""PowerWorld preflight. Run before writing any analysis code."""

import sys
from pathlib import Path

CASE = r"C:\path\to\your_case.pwb"   # <- change this


def preflight_machine() -> bool:
    """Checks 1-4: can this machine drive PowerWorld? No case file needed."""
    # 1. Platform. SimAuto is a Windows COM server; there is no Linux or macOS path.
    if not sys.platform.startswith("win"):
        print(f"FAIL 1/5  platform is {sys.platform!r}, SimAuto requires Windows")
        return False
    print("ok   1/5  platform is Windows")

    # 2. pywin32, the COM bridge esapp calls through.
    try:
        import win32com.client  # noqa: F401
    except ImportError:
        print(f"FAIL 2/5  pywin32 not importable from {sys.executable}")
        print("          ask the user to run /powerhivemind:powerworld-setup")
        return False
    print("ok   2/5  pywin32 importable")

    # 3. esapp itself.
    try:
        from esapp import PowerWorld  # noqa: F401
    except ImportError:
        print(f"FAIL 3/5  esapp not importable from {sys.executable} (not under python -I?)")
        print("          ask the user to run /powerhivemind:powerworld-setup")
        return False
    print("ok   3/5  esapp importable")

    # 4. The SimAuto COM server. This is where an unlicensed add-on shows up.
    #    Also record the build date, so the version is on file before any analysis.
    try:
        import win32com.client
        from datetime import date, timedelta

        sa = win32com.client.Dispatch("pwrworld.SimulatorAuto")
        try:
            # RequestBuildDate is a Delphi serial date: days since 1899-12-30
            build = date(1899, 12, 30) + timedelta(days=int(sa.RequestBuildDate))
            version = f", build {build.isoformat()}"
        except Exception:  # noqa: BLE001 - version is useful, not required
            version = ", build unknown"
    except Exception as exc:  # noqa: BLE001 - the message is the diagnosis
        print(f"FAIL 4/5  cannot start SimAuto: {exc}")
        print("          see the failure table: this is usually 'not installed'")
        print("          or 'installed but the SimAuto add-on is not licensed'")
        return False
    print(f"ok   4/5  SimAuto COM server responds{version}")
    return True


def preflight_case(case_path: str) -> bool:
    """Check 5: this particular case opens. Run preflight_machine() first."""
    # 5. The case itself opens.
    if not Path(case_path).is_file():
        print(f"FAIL 5/5  case not found: {case_path}")
        return False
    try:
        from esapp import PowerWorld

        pw = PowerWorld(case_path)
        info = pw.summary()
    except Exception as exc:  # noqa: BLE001
        print(f"FAIL 5/5  case will not open: {exc}")
        return False
    print(f"ok   5/5  case opens: {info['n_bus']} buses, {info['n_gen']} generators")
    return True


def preflight(case_path: str) -> bool:
    """All five checks, stopping at the first failure."""
    return preflight_machine() and preflight_case(case_path)


if __name__ == "__main__":
    ok = preflight(CASE)
    print("\nPREFLIGHT PASSED" if ok else "\nPREFLIGHT FAILED - fix the above before continuing")
    raise SystemExit(0 if ok else 1)
```

### What each failure actually means

| Error you see | What is wrong | Fix |
|---|---|---|
| `platform is 'linux'` / `'darwin'` | SimAuto is a Windows COM server. There is no port | Use Windows. The weather half of this kit still works — see [teamoverbyeweather-client](teamoverbyeweather-client.md) |
| `ModuleNotFoundError: No module named 'win32com'` | pywin32 is not installed | Ask the user to run `/powerhivemind:powerworld-setup`; do not pip-install yourself |
| `ModuleNotFoundError: No module named 'esapp'` | esapp is not installed, you are in the wrong interpreter, or you ran under `python -I` | Rerun without `-I` and check `sys.executable`. If it is still missing, ask the user to run `/powerhivemind:powerworld-setup`; do not pip-install yourself |
| `com_error: (-2147221005, 'Invalid class string', ...)` | SimAuto is not registered. Usually PowerWorld Simulator is not installed at all | Install Simulator. If it *is* installed, run it once as administrator so it registers its COM server |
| `com_error: (-2147221164, 'Class not registered', ...)` | Same as above, or a 32/64-bit mismatch between Python and Simulator | Match the bitness. A 32-bit Simulator will not serve a 64-bit Python |
| A COM error mentioning **licence**, **not authorized**, or **add-on** | Simulator is installed and licensed, but the **SimAuto add-on is a separate licence** and yours does not include it | This cannot be fixed in code. Talk to whoever administers your PowerWorld licence |
| SimAuto starts but a feature errors | Possibly a version difference | Check the build date against [version-requirements](../concepts/version-requirements.md) before assuming a page is wrong |
| `PowerWorldPrerequisiteError` | **Not** a version or licence problem. The case lacks a prerequisite state | e.g. clearing TimeStep results that do not exist yet. Do the prerequisite step first |
| `case not found` | Path typo, or a relative path resolving somewhere unexpected | Use an absolute path. Always |
| Case opens but `n_bus` is 0 | The file opened but is not a valid case | Confirm the `.pwb` is not corrupt; try opening it in Simulator directly |

### The licence check, specifically

**PowerWorld Simulator and the SimAuto add-on are licensed separately.** A machine can
have a fully valid, fully working Simulator installation and still be unable to run a
single line of this kit, because automation is a different SKU. Simulator's own GUI works
fine and gives no hint of this.

The symptom is that check 4 fails while Simulator itself launches normally. If you can
open your case by double-clicking it but `Dispatch("pwrworld.SimulatorAuto")` raises,
that is the licence, not your code.

### Record the version before you analyse anything

Check 4 prints the Simulator build date. Put it in your report. Field availability and
script-action behaviour both shift between releases, and they shift silently, so when a
result later looks wrong, check the build date first.

`RequestBuildDate` is a Delphi serial date (days since 1899-12-30), not a version number.
For the full version string and what this kit was verified against, see
[version-requirements](../concepts/version-requirements.md).

### Quick version

If you only want the one-line answer:

```python
import win32com.client
win32com.client.Dispatch("pwrworld.SimulatorAuto")   # raises if PowerWorld automation is unavailable
```

If that line runs without raising, everything downstream in this kit is available to
you. If it raises, nothing is.

### What preflight does not tell you

It confirms you can *drive* PowerWorld. It says nothing about whether the case is
suitable for the study you have in mind: whether it solves, whether it has the
generators or weather models you need, whether its limits are configured. Those are
questions for the analysis itself, starting at [esapp-overview](esapp-overview.md).
