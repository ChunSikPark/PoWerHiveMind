"""timestep rules. TimeStep runs with any number of PFW models, so none of these stops it: they say
what the run will cover (demos/timestep-and-pfw.md, methods/timestep-simulation-setup.md)."""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from casedata import CaseData
from findings import BROKEN, FYI, WORTH, YOUR_CALL, Finding, bus
from pww import PwwError, read_header
from summary import is_renewable
from thresholds import PFW_MIN_CHARS, PWW_MAX_STATION_MILES, WIND_CLASSES

PAGE = "demos/timestep-and-pfw.md"
BLANK = {"", "None", "nan"}


def renewables(cd: CaseData) -> pd.DataFrame:
    g = cd.get("Gen")
    r = g[is_renewable(g.GenFuelType)].copy()
    r["has_pfw"] = r.TSPFWModelString.map(lambda s: s not in BLANK and len(s) > PFW_MIN_CHARS)
    lat, lon = _located(r)
    r["lat"], r["lon"] = lat, lon
    return r


def _valid(lat: pd.Series, lon: pd.Series) -> pd.Series:
    return lat.between(-90, 90) & lon.between(-180, 180) & ~((lat == 0) & (lon == 0))


def _located(r: pd.DataFrame):
    """The unit's own bus coordinates, else its substation's. On both public cases probed
    2026-09-30 the bus pair (Gen.Latitude) read blank on every unit and the substation pair
    (Gen.Latitude:1, "Substation Latitude" in the export) was set. Which pair TimeStep reads is
    not verified in the kit, so a unit counts as located when either pair is valid."""
    own = _valid(r.Latitude, r.Longitude)
    lat = r.Latitude.where(own, r["Latitude:1"])
    lon = r.Longitude.where(own, r["Longitude:1"])
    ok = _valid(lat, lon)
    return lat.where(ok), lon.where(ok)


def coverage(cd: CaseData) -> dict:
    r = renewables(cd)
    with_pfw = r[r.has_pfw]
    return {"renewables": int(len(r)), "with_pfw": int(len(with_pfw)),
            "installed_mw": float(r.GenMWMax.sum()), "following_mw": float(with_pfw.GenMWMax.sum())}


def _wind_class(u) -> bool:
    ci = u["CustomInteger:1"]
    return (not pd.isna(ci) and int(ci) in WIND_CLASSES) or str(u.GenUnitType)[:2] in {f"W{c}" for c in WIND_CLASSES}


def pfw_missing(cd: CaseData) -> list[Finding]:
    r = renewables(cd)
    miss = r[~r.has_pfw]
    if miss.empty:
        return []
    mw, total = float(miss.GenMWMax.sum()), float(r.GenMWMax.sum())
    wind = miss[miss.GenFuelType.str.upper().str.contains("WND")]
    classed = int(sum(_wind_class(u) for _, u in wind.iterrows()))
    return [Finding(
        "ts.pfw_missing", WORTH, BROKEN,
        what=(f"time step will run: {len(r) - len(miss)} of {len(r)} renewables follow the weather; "
              f"{len(miss)} read 0 MW for the whole run ({mw:,.0f} of {total:,.0f} MW installed, "
              f"{mw / total if total else 0:.1%})"),
        why="a renewable with no PFW model has no way to turn weather into MW, and TimeStep does not warn",
        page=PAGE,
        where=[{"BusNum": bus(u.BusNum), "GenID": u.GenID, "GenFuelType": u.GenFuelType,
                "GenMWMax": u.GenMWMax} for u in miss.itertuples()],
        details={"missing": int(len(miss)), "renewables": int(len(r)), "missing_mw": mw, "installed_mw": total,
                 "missing_wind": int(len(wind)), "missing_wind_with_class": classed},
        handoff=(f"the Auto_PFW scripts (concepts/auto-pfw-scripts.md); {classed} of the "
                 f"{len(wind)} missing wind units carry a class it can use, and it skips the rest without a "
                 f"warning; send back the _PFW copy it writes"))]


def latlon_missing(cd: CaseData) -> list[Finding]:
    r = renewables(cd)
    bad = r[r.lat.isna()]
    if bad.empty:
        return []
    return [Finding(
        "ts.latlon_missing", WORTH, BROKEN,
        what=f"{len(bad)} renewable(s) have no usable location ({bad.GenMWMax.sum():,.0f} MW installed)",
        why="their weather is looked up at the wrong place, so their output means nothing",
        page="methods/timestep-simulation-setup.md",
        where=[{"BusNum": bus(u.BusNum), "GenID": u.GenID, "GenMWMax": u.GenMWMax} for u in bad.itertuples()])]


def _miles(lat, lon, slat, slon):
    p1, p2 = np.radians(lat)[:, None], np.radians(slat)[None, :]
    dl = np.radians(slon)[None, :] - np.radians(lon)[:, None]
    h = np.sin((p2 - p1) / 2) ** 2 + np.cos(p1) * np.cos(p2) * np.sin(dl / 2) ** 2
    return 3958.8 * 2 * np.arcsin(np.sqrt(np.clip(h, 0, 1)))


def pww_footprint(cd: CaseData, pww: str | None) -> list[Finding]:
    if not pww:
        return [Finding(
            "ts.pww_footprint", FYI, YOUR_CALL,
            what="weather file not given, so I didn't check it covers these units",
            why="send the .pww if you want its coverage checked",
            page="concepts/pww-data.md")]
    try:
        hdr = read_header(pww)
    except (OSError, PwwError) as e:
        return [Finding(
            "ts.pww_footprint", FYI, YOUR_CALL,
            what="couldn't read the weather file, so its coverage was not checked",
            why=(e.strerror or type(e).__name__) + f": {Path(pww).name}" if isinstance(e, OSError) else str(e), page="concepts/pww-data.md")]
    r = renewables(cd).dropna(subset=["lat", "lon"])
    st = np.array(hdr["stations"], dtype=float).reshape(-1, 2)
    if r.empty or not len(st):
        nearest = np.full(len(r), np.inf)
    else:
        nearest = np.concatenate([_miles(r.lat.values[i:i + 256], r.lon.values[i:i + 256], st[:, 0], st[:, 1]).min(axis=1)
                                  for i in range(0, len(r), 256)])
    r = r.assign(nearest_mi=nearest)
    out = r[r.nearest_mi > PWW_MAX_STATION_MILES]
    info = {"file": Path(pww).name, "stations": int(len(st)), "start": hdr["start"], "end": hdr["end"],
            "steps": hdr["steps"], "sample_seconds": hdr["sample_seconds"], "located_units": int(len(r))}
    if out.empty:
        return [Finding("ts.pww_footprint", FYI, YOUR_CALL,
                        what=f"the weather file covers all {len(r)} located renewables",
                        why="every unit is within reach of a weather station in the file",
                        page="concepts/pww-data.md", details=info)]
    return [Finding(
        "ts.pww_footprint", WORTH, YOUR_CALL,
        what=f"{len(out)} of {len(r)} located renewables sit outside the weather file's footprint",
        why="their weather comes from a far station, and the run gives no warning",
        page="concepts/pww-data.md", details=info,
        where=[{"BusNum": bus(u.BusNum), "GenID": u.GenID, "nearest_station_miles": round(u.nearest_mi, 1)}
               for u in out.itertuples()])]
