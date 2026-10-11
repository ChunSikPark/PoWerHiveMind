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


def test_not_checked_reaches_the_cli_files(fake_esapp, tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    out = tmp_path / "o"
    assert audit.main(["--case", str(_case(tmp_path)), "--profiles", "base,lint", "--out", str(out)]) == 0
    r = json.loads((out / "findings.json").read_text(encoding="utf-8"))
    assert {"lint.shunt_steps", "lint.shunt_band_inverted", "lint.gen_below_min"} <= {
        s["rule"] for s in r["rules_skipped"]}
    assert "## Not checked" in (out / "findings.md").read_text(encoding="utf-8")


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


def test_a_rule_that_raises_is_three_lines_and_a_full_chained_log(fake_esapp, tmp_path, monkeypatch, capsys):
    import report

    def boom(*a, **k):
        try:
            raise RuntimeError("the solve crashed")
        except RuntimeError:
            raise ValueError("exit() raised its own error")      # original survives as __context__

    monkeypatch.setattr(report, "build", boom)
    assert audit.main(["--case", str(_case(tmp_path)), "--out", str(tmp_path / "o")]) == 2
    err = capsys.readouterr().err
    assert len(err.strip().splitlines()) == 3 and "Traceback" not in err and "ValueError" not in err
    log = (tmp_path / "o" / "audit_error.log").read_text(encoding="utf-8")
    assert "the solve crashed" in log and "exit() raised its own error" in log and "During handling" in log


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
