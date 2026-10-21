"""base rules: does the AC solve, is the network real, is any unit past its rating, is load or generation
stranded on a dead bus, stale results."""
from __future__ import annotations

import numpy as np

from casedata import CaseData
from findings import AC_STUDIES, BROKEN, FYI, ON_PURPOSE, STOPS, WORTH, Finding, branch_keys, bus
from summary import _total, dead_buses, dead_injections
from thresholds import (DC_SKELETON_MEDIAN_XR, DC_SKELETON_PARTIAL_SHARE, DC_SKELETON_SHARE, DEAD_BUS_STOP_MW,
                        GEN_OVER_MIN_MW, GEN_OVER_STOP_MW, GEN_OVER_STOP_SHARE, TINY_R)


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
                 "the case runs; the overshoot is small enough not to move a finding"),
            page="methods/applying-a-dispatch-to-a-case.md", stops=AC_STUDIES if stop else (),
            where=where, details={"over_mw": total}))
    return out


def _multiplied(d, setpoint: str) -> str:
    """How the load MW was reached: '1,533 MW setpoint × 1.305 zone multiplier'."""
    if not d.multiplier_applied.any():
        return f"{setpoint} setpoint; area and zone multipliers not read, not applied"
    on = d[d.multiplier_applied & (d.loads > 0)]
    pairs = set(zip(on.area_mult, on.zone_mult))
    if len(pairs) == 1:
        [(a, z)] = pairs
        factors = " × ".join(f"{m:g} {name}" for m, name in ((a, "area"), (z, "zone")) if m != 1)
        how = f"{setpoint} setpoint × {factors} multiplier" if factors else f"{setpoint} setpoint, multipliers 1"
    else:
        how = f"{setpoint} setpoint × each load's area and zone multipliers"
    return how if d.multiplier_applied.all() else how + "; some multipliers not read, those loads at setpoint"


def dead_bus_injection(cd: CaseData) -> list[Finding]:
    """In-service load or generation on a bus outside every viable island. The solver converges on the
    live network without it and reports nothing, so a closed status alone passes a case that dropped
    a load. A dead bus with nothing attached is common and harmless: only counted."""
    d = dead_injections(cd)
    if d.empty:
        return []
    b = cd.get("Bus").set_index("BusNum")
    load, setpoint, gen = _total(d.load_mw), _total(d.load_setpoint_mw), _total(d.gen_mw)
    applied = bool(d.multiplier_applied.all())
    stop = not (load + gen <= DEAD_BUS_STOP_MW)             # after multipliers; an unread setpoint counts as material
    mw = lambda x: "an unread amount" if np.isnan(x) else f"{x:,.0f} MW"
    dead = len(dead_buses(cd))
    return [Finding(
        "base.dead_bus_injection", STOPS if stop else WORTH, BROKEN,
        what=f"{len(d)} disconnected bus(es) carry in-service load or generation the solution leaves out: "
             f"{mw(load)} of load ({_multiplied(d, mw(setpoint))}) and {mw(gen)} of generation at its setpoint",
        why=("the main island solves without them and reports no error, so every result describes a case "
             "short of that load and generation" if stop else
             "small enough not to move a finding, but the solution still leaves it out"),
        page="methods/violation-network-map.md", stops=AC_STUDIES if stop else (),
        where=[{"BusNum": bus(r.BusNum), "BusName": b.at[r.BusNum, "BusName"], "BusNomVolt": b.at[r.BusNum, "BusNomVolt"],
                "AreaNum": b.at[r.BusNum, "AreaNum"], "load_mw": r.load_mw, "load_setpoint_mw": r.load_setpoint_mw,
                "multiplier_applied": r.multiplier_applied, "gen_mw": r.gen_mw} for r in d.itertuples()],
        details={"load_mw": None if np.isnan(load) else load, "gen_mw": None if np.isnan(gen) else gen,
                 "load_setpoint_mw": None if np.isnan(setpoint) else setpoint, "multiplier_applied": applied,
                 "dead_buses": dead, "dead_buses_with_nothing_attached": dead - len(d)})]


def stale_ctg_results(cd: CaseData) -> list[Finding]:
    n = len(cd.get("ViolationCTG"))
    if not n:
        return []
    return [Finding(
        "base.stale_ctg_results", FYI, ON_PURPOSE,
        what=f"the case already holds {n} contingency violation rows from an earlier run",
        why="they describe whatever the case was when that run happened, not this audit - do not read them",
        page="methods/reading-violationctg.md", details={"rows": n})]
