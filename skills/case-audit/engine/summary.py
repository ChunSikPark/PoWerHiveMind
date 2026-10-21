"""The case summary: facts, not findings. The agent presents these numbers; it never recomputes them."""
from __future__ import annotations

import pandas as pd

from casedata import CaseData
from thresholds import GEN_OVER_MIN_MW, RENEWABLE_CODES


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


def _total(mw: pd.Series) -> float:
    """The sum, or NaN when any value was not read: an unread setpoint is not 0 MW."""
    return float(mw.sum()) if mw.notna().all() else float("nan")


def dead_buses(cd: CaseData) -> set:
    """Buses outside every viable island: BusStatus Disconnected, PowerWorld's topology answer, set
    before any solve."""
    b = cd.get("Bus")
    return set(b.BusNum[b.BusStatus == "Disconnected"])


def dead_injections(cd: CaseData) -> pd.DataFrame:
    """In-service load and generation on dead buses, one row per bus. A dead bus is not solved, so its
    LoadMW / GenMW say nothing: generation is GenMWSetPoint, and load is the setpoint (LoadSMW +
    LoadIMW + LoadZMW) times its area and zone multipliers (LoadMultiplier, LoadMultiplier:2), the
    load the scenario means. Where a multiplier was not read the load stays at its setpoint and
    multiplier_applied is False: never a silent 1.0. area_mult / zone_mult are the bus's first load's."""
    ld, g, dead = cd.get("Load"), cd.get("Gen"), dead_buses(cd)
    ld = ld[(ld.LoadStatus == "Closed") & ld.BusNum.isin(dead)]
    g = g[(g.GenStatus == "Closed") & g.BusNum.isin(dead)]
    setpoint = ld[["LoadSMW", "LoadIMW", "LoadZMW"]].sum(axis=1, min_count=1)
    # assumed, not measured: the two compound, as each "scales all the real power load" in its area / zone
    mult = ld.LoadMultiplier * ld["LoadMultiplier:2"]
    load_mw = setpoint.where(mult.isna(), setpoint * mult)
    rows = []
    for n in sorted(set(ld.BusNum) | set(g.BusNum)):
        on, first = ld.BusNum == n, ld[ld.BusNum == n].head(1)
        rows.append({"BusNum": n, "load_mw": _total(load_mw[on]), "load_setpoint_mw": _total(setpoint[on]),
                     "multiplier_applied": bool(mult[on].notna().all()), "loads": int(on.sum()),
                     "area_mult": first.LoadMultiplier.sum(min_count=1),
                     "zone_mult": first["LoadMultiplier:2"].sum(min_count=1),
                     "gen_mw": _total(g.GenMWSetPoint[g.BusNum == n])})
    return pd.DataFrame(rows, columns=["BusNum", "load_mw", "load_setpoint_mw", "multiplier_applied", "loads",
                                       "area_mult", "zone_mult", "gen_mw"])


def case_summary(cd: CaseData, opf: bool = False) -> dict:
    gen, load, sh, bus, br = (cd.get(o) for o in ("Gen", "Load", "Shunt", "Bus", "Branch"))
    dead = dead_buses(cd)                                    # reported apart: none of it is in the solution
    on = gen[(gen.GenStatus == "Closed") & ~gen.BusNum.isin(dead)].copy()
    ld = load[(load.LoadStatus == "Closed") & ~load.BusNum.isin(dead)]
    stranded = dead_injections(cd)
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
        "load_mw_dead_buses": _total(stranded.load_mw), "generation_mw_dead_buses": _total(stranded.gen_mw),
        "load_mw_dead_buses_multiplier_applied": bool(stranded.multiplier_applied.all()),
        "losses_mw": gen_mw - load_mw,
        "headroom_dispatchable_mw": float(dispatchable.headroom.sum()),
        "generation_includes_overshoot_mw": float(over[over > GEN_OVER_MIN_MW].sum()),
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
