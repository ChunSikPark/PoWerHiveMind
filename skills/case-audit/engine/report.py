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

ALL_KV_CEILING = 9999  # a report-limits window whose max kV is at or above this has no upper limit (cases store 9999)
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
        "case": Path(p).name if (p := cd.scalars.get("case_path")) else None,  # basename only: no local paths in the files
        "audited_at": datetime.now().isoformat(timespec="seconds"),
        "profiles": ["base", *profiles],
        "weather_file": Path(pww).name if pww else None,
        "read_only": ({"sha256_before": before, "sha256_after": after, "unchanged": before == after if (before is not None and after is not None) else None} if live
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
    return "all kV" if lo <= 0 and hi >= ALL_KV_CEILING else f"{lo:g}–{hi:g} kV"


def _mw(solved, dead, applied=True) -> str:
    """Solved MW, with what sits on disconnected buses beside it, so a total is never silently partial."""
    if dead == 0:
        return _n(solved)
    note = "" if applied else " (setpoint; area and zone multipliers not read)"
    return f"{_n(solved)} solved + {_n(dead)} on disconnected buses, not served{note}"


def render_md(r: dict) -> str:
    s, L = r["case_summary"], []
    if r["source"] == "snapshot":
        L += [REPLAYED, ""]
    unchanged = {True: "yes", False: "NO", None: "not checked (no hash of the file before and after)"}[r["read_only"]["unchanged"]]
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
          f"| Load | {_mw(s['load_mw'], s['load_mw_dead_buses'], s['load_mw_dead_buses_multiplier_applied'])} | {_n(s['load_mvar'])} |",
          f"| Generation (online) | {_mw(s['generation_mw'], s['generation_mw_dead_buses'])} | {_n(s['generation_mvar'])} |",
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
              "| area | OPF may redispatch it | units the OPF may move | with cost data | with a cost above 0 at today's output | cost model types |",
              "|---|---|---|---|---|---|"]
        for a in r["opf_areas"]:
            models = ", ".join(f"{k} {v}" for k, v in a["cost_models"].items()) or "—"
            how = f"yes (super area {a['SAName']} on OPF)" if a["via_super_area"] else f"{'yes' if a['opf'] else 'no'} ({a['BGAGC']})"
            L.append(f"| {a['AreaNum']} | {how} | {a['agc_units']} | {a['with_cost_data']} | {a['cost_above_zero']} | {models} |")
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
