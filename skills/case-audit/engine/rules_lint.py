"""Lint rules: data defects that let a case solve while being wrong (methods/case-data-lint.md).

None needs a solve and none stops a study; each says what is wrong and where, by object keys.
A field the source lacked, or that reads blank on every row (NaN for a number, empty for text), was not
read (an older snapshot, or a field this PowerWorld lacks), so a rule that depends on it returns nothing
rather than flag every object; a switched-shunt block slot after the first is the exception, blank meaning unused.
REQUIRES lists the fields each rule cannot run without, PARTIAL the fields one half needs,
and run_rules reports a rule under rules_skipped naming the ones it could not read.
"""
from __future__ import annotations

import pandas as pd

import math

from casedata import BLOCK_MVAR, BLOCK_STEPS, NUMERIC, CaseData
from findings import BROKEN, FYI, WORTH, YOUR_CALL, Finding, branch_keys, bus
from rules_mon import RATING_OF, _in_use
from rules_reg import REGULATING_MODES
from thresholds import (GEN_LIMIT_PLACEHOLDER, GEN_UNDER_MIN_MW, KV_DECIMALS, SHUNT_BAND_TOL_PU,
                        SHUNT_MAX_COMBOS, SHUNT_STEP_TOL_MVAR, ZBR_X_PU)
from topology import adjacency

PAGE = "methods/case-data-lint.md"
BLANK = {"", "nan", "None"}
GEN_LIMITS = ["GenMWMax", "GenMWMin", "GenMVRMax", "GenMVRMin"]
SLOTS = [*BLOCK_STEPS[1:], *BLOCK_MVAR[1:]]   # block slots after the first: blank means unused, only an absent column is unread
# every field a rule reads, keys first; T2 is the check.
REQUIRES = {
    "lint.shunt_steps": [("Shunt", ["BusNum", "ShuntID", "SSCMode", "SSNMVR", BLOCK_STEPS[0], BLOCK_MVAR[0]])],
    "lint.shunt_band_inverted": [("Shunt", ["BusNum", "ShuntID", "SSCMode", "SSVHigh", "SSVLow"])],
    "lint.gen_below_min": [("Gen", ["BusNum", "GenID", "GenStatus", "GenMW", "GenMWMin"])],
    "lint.gen_limits": [("Gen", ["BusNum", "GenID"])],
    "lint.negative_x": [("Branch", ["BusNum", "BusNum:1", "LineCircuit", "LineStatus", "LineX"]),
                        ("Bus", ["BusNum", "BusIsStarBus"])],
    "lint.missing_ratings": [("Branch", ["BusNum", "BusNum:1", "LineCircuit", "LineStatus",
                                       "LineR", "LineX", "LineAMVA"])],
    "lint.bus_names": [("Bus", ["BusNum", "BusName"])],
    "lint.islands": [("Bus", ["BusNum", "BusStatus"]), ("Branch", ["BusNum", "BusNum:1", "LineStatus"])],
    "lint.nominal_kv": [("Bus", ["BusNum", "BusNomVolt"])],
}
PARTIAL = {
    "lint.missing_ratings": ("the rating B/C half was", [("Branch", ["LineAMVA:1", "LineAMVA:2"]),
                                                 ("LimitSet", ["LSDisabled", "LSLineRateSet:1"])]),
    "lint.islands": ("the slack count was", [("Bus", ["BusCat"]), ("Gen", ["BusNum", "GenStatus", "GenMW"]),
                                       ("Load", ["BusNum", "LoadStatus", "LoadMW"])]),
}


def _unread(df: pd.DataFrame, *cols: str) -> bool:
    """True when any of `cols` was not in the source, or reads blank on every row (NaN for a number column,
    ''/'nan'/'None' for text); a block slot after the first counts only when absent, since blank means no shunt uses it."""
    missing = set(df.attrs.get("unread", ()))
    return len(df) > 0 and any(
        c in missing or (c not in SLOTS and (df[c].isna().all() if c in NUMERIC else df[c].isin(BLANK).all()))
        for c in cols)


def unread_fields(cd: CaseData, rule: str) -> list[str]:
    missing = [c for obj, cols in REQUIRES[rule] for c in cols if _unread(cd.get(obj), c)]
    if not missing and rule == "lint.gen_limits" and all(_unread(cd.get("Gen"), c) for c in GEN_LIMITS):
        return GEN_LIMITS
    if not missing and rule == "lint.shunt_steps":
        return [c for c in SLOTS if _unread(cd.get("Shunt"), c)]
    return missing


def partial_skips(cd: CaseData, rule: str) -> list[dict]:
    if rule == "lint.gen_limits":
        missing = [c for c in GEN_LIMITS if _unread(cd.get("Gen"), c)]
        if len(missing) == len(GEN_LIMITS):
            return []
        half = "those limits were"
    elif rule in PARTIAL:
        half, fields = PARTIAL[rule]
        missing = [c for obj, cols in fields for c in cols if _unread(cd.get(obj), c)]
    else:
        return []
    return [{"rule": rule, "reason": f"field(s) {', '.join(missing)} not read; {half} not checked"}] if missing else []


def _reachable(blocks, limit):
    """Every Mvar total whole steps of the blocks can make; None when the combinations would pass
    `limit`, checked before they are built. Rounded to 1e-6 only to merge equal totals, so the
    error stays far below SHUNT_STEP_TOL_MVAR however many blocks there are."""
    reach = {0.0}
    for n, q in blocks:
        if len(reach) * (int(n) + 1) > limit:
            return None
        reach = {round(t + k * q, 6) for t in reach for k in range(int(n) + 1)}
    return reach


def shunt_steps(cd: CaseData) -> list[Finding]:
    sh = cd.get("Shunt")
    if sh.empty or _unread(sh, "SSCMode", *BLOCK_STEPS, *BLOCK_MVAR):
        return []
    beyond, between, skipped = [], [], []
    for _, r in sh[sh.SSCMode == "Discrete"].iterrows():
        blocks = [(r[n], r[q]) for n, q in zip(BLOCK_STEPS, BLOCK_MVAR)
                  if math.isfinite(r[n]) and math.isfinite(r[q]) and r[n] > 0 and r[q] != 0]
        if not blocks or pd.isna(r.SSNMVR):
            continue                       # no blocks: PowerWorld has nothing to step through to check against
        top = sum(n * q for n, q in blocks if q > 0)
        bottom = sum(n * q for n, q in blocks if q < 0)
        row = {"BusNum": bus(r.BusNum), "ShuntID": r.ShuntID, "SSStatus": r.SSStatus, "SSNMVR": r.SSNMVR,
               "blocks": ", ".join(f"{int(n)} x {q:g}" for n, q in blocks),
               "block_max_mvar": round(top, 3), "block_min_mvar": round(bottom, 3)}
        if r.SSNMVR > top + SHUNT_STEP_TOL_MVAR or r.SSNMVR < bottom - SHUNT_STEP_TOL_MVAR:
            beyond.append(row)
            continue
        reach = _reachable(blocks, SHUNT_MAX_COMBOS)
        if reach is None:
            skipped.append(row)
        elif min(abs(r.SSNMVR - t) for t in reach) > SHUNT_STEP_TOL_MVAR:
            between.append(row)
    out = []
    if skipped:
        out.append(Finding(
            "lint.shunt_steps", FYI, YOUR_CALL,
            what=f"{len(skipped)} discrete shunt(s) not checked for whole steps: too many step combinations",
            why="silence on these is not a pass; check their settings against their blocks by hand",
            page=PAGE, where=skipped))
    if beyond:
        out.append(Finding(
            "lint.shunt_steps", WORTH, BROKEN,
            what=f"{len(beyond)} discrete shunt(s) set beyond what their blocks can switch in",
            why="the nominal Mvar is more than every step together; the blocks or the setting are wrong",
            page=PAGE, where=beyond))
    if between:
        out.append(Finding(
            "lint.shunt_steps", WORTH, BROKEN,
            what=f"{len(between)} discrete shunt(s) set between steps: the nominal Mvar is no whole number of steps",
            why="a discrete shunt can only sit on a step, so the solve starts from a setting the device cannot hold",
            page=PAGE, where=between))
    return out


def shunt_band_inverted(cd: CaseData) -> list[Finding]:
    sh = cd.get("Shunt")
    if sh.empty or _unread(sh, "SSCMode", "SSVHigh", "SSVLow"):
        return []
    bad = sh[sh.SSCMode.isin(REGULATING_MODES) & (sh.SSVHigh < sh.SSVLow - SHUNT_BAND_TOL_PU)]
    if bad.empty:
        return []
    return [Finding(
        "lint.shunt_band_inverted", WORTH, BROKEN,
        what=f"{len(bad)} regulating shunt(s) with a high voltage limit below the low one",
        why="the band is empty, so the shunt cannot regulate in the solve; the real device would",
        page=PAGE, where=[{"BusNum": bus(r.BusNum), "ShuntID": r.ShuntID, "SSCMode": r.SSCMode,
                           "SSVLow": r.SSVLow, "SSVHigh": r.SSVHigh} for r in bad.itertuples()])]


def gen_below_min(cd: CaseData) -> list[Finding]:
    g = cd.get("Gen")
    if g.empty or _unread(g, "GenStatus", "GenMW", "GenMWMin"):
        return []
    on = g[(g.GenStatus == "Closed") & (g.GenMW < g.GenMWMin - GEN_UNDER_MIN_MW)]
    if on.empty:
        return []
    slack = set(cd.get("Bus").query("BusCat == 'Slack'").BusNum)
    return [Finding(
        "lint.gen_below_min", WORTH, BROKEN,
        what=f"{len(on)} online unit(s) dispatched below their minimum output, "
             f"{float((on.GenMWMin - on.GenMW).sum()):,.1f} MW under in all",
        why="a unit that is on cannot run below its minimum; it should be off or dispatched at least to it",
        page=PAGE, where=[{"BusNum": bus(r.BusNum), "GenID": r.GenID, "GenMW": r.GenMW, "GenMWMin": r.GenMWMin,
                           "GenFuelType": r.GenFuelType, "slack": r.BusNum in slack} for r in on.itertuples()])]


def gen_limits(cd: CaseData) -> list[Finding]:
    g = cd.get("Gen")
    if g.empty:
        return []
    cols = [c for c in GEN_LIMITS if not _unread(g, c)]
    where = []
    for _, r in g.iterrows():
        problems = [f"{c} missing" for c in cols if pd.isna(r[c])]
        problems += [f"{c} placeholder" for c in cols if pd.notna(r[c]) and abs(r[c]) >= GEN_LIMIT_PLACEHOLDER]
        if "GenMWMin" in cols and r.GenMWMax < r.GenMWMin:
            problems.append("GenMWMax below GenMWMin")
        if r.GenMVRMax < r.GenMVRMin:
            problems.append("GenMVRMax below GenMVRMin")
        if problems:
            where.append({"BusNum": bus(r.BusNum), "GenID": r.GenID, "GenStatus": r.GenStatus,
                          **{c: r[c] for c in cols}, "problems": problems})
    if not where:
        return []
    return [Finding(
        "lint.gen_limits", WORTH, BROKEN,
        what=f"{len(where)} unit(s) with a missing, placeholder or inverted MW or Mvar limit",
        why="the solve and any dispatch read these limits as real; a placeholder means no limit at all",
        page=PAGE, where=where)]


def negative_x(cd: CaseData) -> list[Finding]:
    br, b = cd.get("Branch"), cd.get("Bus")
    if _unread(br, "LineStatus", "LineX") or _unread(b, "BusIsStarBus"):
        return []
    star = set(b.BusNum[b.BusIsStarBus == "YES"])
    neg = br[(br.LineStatus == "Closed") & (br.LineX < 0) & ~br.BusNum.isin(star) & ~br["BusNum:1"].isin(star)]
    if neg.empty:
        return []                          # a star leg's negative X is the three-winding equivalent, not a defect
    return [Finding(
        "lint.negative_x", WORTH, YOUR_CALL,
        what=f"{len(neg)} closed branch(es) with negative series reactance",
        why="real for series compensation; anywhere else it is a sign error that reverses the branch's flow share",
        page=PAGE, where=[{**branch_keys(r), "LineXfmr": r["LineXfmr"], "LineR": r["LineR"], "LineX": r["LineX"]}
                          for _, r in neg.iterrows()])]


def missing_ratings(cd: CaseData) -> list[Finding]:
    br = cd.get("Branch")
    if _unread(br, "LineStatus", "LineR", "LineX", "LineAMVA"):
        return []
    closed = br[br.LineStatus == "Closed"]
    jumper = (closed.LineR.fillna(0) == 0) & (closed.LineX.abs() <= ZBR_X_PU)
    real = closed[~jumper]
    a = real.LineAMVA.fillna(0)
    out = []
    no_a = real[a <= 0]
    if len(no_a):
        out.append(Finding(
            "lint.missing_ratings", WORTH, BROKEN,
            what=f"{len(no_a)} closed branch(es) with no rating A (0 MVA), jumpers left out",
            why="a 0 rating is never monitored, so no study can show these branches overloaded",
            page=PAGE, where=[{**branch_keys(r), "LineXfmr": r["LineXfmr"]} for _, r in no_a.iterrows()]))
    rated = real[a > 0]
    b0, c0 = rated["LineAMVA:1"].fillna(0) <= 0, rated["LineAMVA:2"].fillna(0) <= 0
    only_a = rated[b0 | c0]
    if len(only_a) and not partial_skips(cd, "lint.missing_ratings"):
        used = {letter for _, which, letter in _in_use(cd) if which == "contingency"}
        hit = sorted(l for l in used & {"B", "C"} if (only_a[RATING_OF[l]].fillna(0) <= 0).any())
        out.append(Finding(
            "lint.missing_ratings", WORTH if hit else FYI, BROKEN if hit else YOUR_CALL,
            what=f"{len(only_a)} rated branch(es) carry rating A but no B or C ({int(b0.sum())} without B, "
                 f"{int(c0.sum())} without C)",
            why=(f"the N-1 checks rate set {', '.join(hit)}, so these branches go unmonitored after an outage"
                 if hit else "no limit set uses B or C for the N-1 today, so this is data to fill, not a blind spot yet"),
            page=PAGE, where=[{**branch_keys(r), "LineAMVA": r["LineAMVA"], "LineAMVA:1": r["LineAMVA:1"],
                               "LineAMVA:2": r["LineAMVA:2"]} for _, r in only_a.iterrows()],
            details={"without_b": int(b0.sum()), "without_c": int(c0.sum()), "contingency_sets_hit": hit}))
    return out


def bus_names(cd: CaseData) -> list[Finding]:
    b = cd.get("Bus")
    if _unread(b, "BusName"):
        return []
    blank = b[b.BusName.isin(BLANK)]
    if blank.empty:
        return []
    return [Finding(
        "lint.bus_names", WORTH, BROKEN,
        what=f"{len(blank)} bus(es) with no name",
        why="a bus found by name, in an aux file or a report, cannot be found",
        page=PAGE, where=[{"BusNum": bus(n)} for n in blank.BusNum])]


def _islands(cd: CaseData) -> list[set]:
    b, br = cd.get("Bus"), cd.get("Branch")
    live = set(b.BusNum[b.BusStatus != "Disconnected"])
    br = br[(br.LineStatus == "Closed") & br.BusNum.isin(live) & br["BusNum:1"].isin(live)]
    adj = adjacency(list(zip(br.BusNum, br["BusNum:1"])))
    seen, out = set(), []
    for s in live:
        if s in seen:
            continue
        part, q = {s}, [s]
        while q:
            for v, _ in adj[q.pop()]:
                if v not in part:
                    part.add(v)
                    q.append(v)
        seen |= part
        out.append(part)
    return sorted(out, key=len, reverse=True)


def islands(cd: CaseData) -> list[Finding]:
    if _unread(cd.get("Bus"), "BusStatus") or _unread(cd.get("Branch"), "LineStatus", "BusNum:1"):
        return []
    parts = _islands(cd)
    if not parts:
        return []
    b, ld, g = cd.get("Bus"), cd.get("Load"), cd.get("Gen")
    slack = set(b.BusNum[b.BusCat == "Slack"])
    ld, g = ld[ld.LoadStatus == "Closed"], g[g.GenStatus == "Closed"]
    rows = [{"island": i, "buses": len(p), "lowest_bus": bus(min(p)), "slack_buses": sorted(bus(s) for s in p & slack),
             "load_mw": round(float(ld[ld.BusNum.isin(p)].LoadMW.sum()), 1),
             "gen_mw": round(float(g[g.BusNum.isin(p)].GenMW.sum()), 1)} for i, p in enumerate(parts)]
    out = []
    if len(rows) > 1:
        extra = rows[1:]
        out.append(Finding(
            "lint.islands", WORTH, YOUR_CALL,
            what=f"{len(extra)} energized island(s) apart from the main one, {sum(r['buses'] for r in extra)} bus(es) in all",
            why="an island the model meant to be connected solves on its own, or not at all, and hides what it feeds",
            page=PAGE, where=extra))
    odd = [r for r in rows if len(r["slack_buses"]) != 1 and (r["load_mw"] or r["gen_mw"] or r["island"] == 0)]
    if odd and not partial_skips(cd, "lint.islands"):
        out.append(Finding(
            "lint.islands", WORTH, YOUR_CALL,
            what=f"{len(odd)} island(s) carrying load or generation with no slack bus or more than one",
            why="each island needs exactly one angle reference; none means it cannot solve, two means two references fight",
            page=PAGE, where=odd))
    return out


def nominal_kv(cd: CaseData) -> list[Finding]:
    b = cd.get("Bus")
    if _unread(b, "BusNomVolt"):
        return []
    kv = b.BusNomVolt
    bad = b[kv.isna() | (kv <= 0) | ((kv - kv.round(KV_DECIMALS)).abs() > 1e-4)]
    if bad.empty:
        return []
    values = bad.BusNomVolt.value_counts(dropna=False).head(10)
    return [Finding(
        "lint.nominal_kv", WORTH, YOUR_CALL,
        what=f"{len(bad)} bus(es) with a nominal kV that is missing or not a round number "
             f"(more than {KV_DECIMALS} decimals)",
        why="filters and reports that select by kV level miss these buses, and per-unit values rest on that base",
        page=PAGE, where=[{"BusNum": bus(r.BusNum), "BusNomVolt": r.BusNomVolt} for r in bad.itertuples()],
        details={"most_common": [{"kv": None if pd.isna(k) else float(k), "buses": int(n)} for k, n in values.items()]})]
