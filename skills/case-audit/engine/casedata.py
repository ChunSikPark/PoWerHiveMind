"""The case as the rules see it: named DataFrames plus scalars. Never imports esapp.

The reader fills a CaseData from PowerWorld; tests build one by hand. Either way every frame
passes through `typed()`, so a rule sees numbers as floats and text stripped of padding, and
an object with no rows is an empty frame with its columns - never None.
"""
from __future__ import annotations

import gzip
import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

import pandas as pd

RATINGS = ["LineAMVA"] + [f"LineAMVA:{i}" for i in range(1, 15)]   # rate sets A..O
_BLOCK = ["", *(f":{i}" for i in range(1, 10))]                      # switched-shunt blocks 1..10
BLOCK_STEPS = [f"SSBlockNumSteps{s}" for s in _BLOCK]
BLOCK_MVAR = [f"SSBlockMVarPerStep{s}" for s in _BLOCK]

# object -> the fields the rules read, keys first. The reader reads exactly these.
READS: dict[str, list[str]] = {
    "Bus": ["BusNum", "BusName", "BusStatus", "BusCat", "BusIsStarBus", "BusNomVolt", "BusPUVolt",
            "BusVoltLim", "BusVoltLimLow", "BusVoltLimHigh", "BusMonEle:1", "AreaNum", "ZoneNum",
            "BusMismatchP", "BusMismatchQ"],
    "Branch": ["BusNum", "BusNum:1", "LineCircuit", "LineStatus", "LineXfmr", "LineR", "LineX", "LineC",
               "LineMW", "LineMVA", "LineMaxPercent", "LineMonEle:1", "BusNomVolt", "BusNomVolt:1",
               "LineXFType", "XFAuto", "XFRegBus", "XFRegMin", "XFRegMax", "XFRegTargetType",
               "XFTapMin", "XFTapMax", "XFStep", "LineTap", "XFRegError"] + RATINGS,
    "Gen": ["BusNum", "GenID", "GenStatus", "GenMW", "GenMVR", "GenMWMax", "GenMVRMax", "GenMVRMin",
            "GenFuelType", "TSPFWModelString", "Latitude", "Longitude", "Latitude:1", "Longitude:1",
            "CustomInteger:1", "GenUnitType", "GenAGCAble", "GenCostModel", "GenCostCurvePoints",
            "GenMCost", "AreaNum", "GenMWMin"],
    "Load": ["BusNum", "LoadID", "LoadStatus", "LoadMW", "LoadMVR"],
    "Shunt": ["BusNum", "ShuntID", "SSStatus", "SSCMode", "AutoControl", "SSRegNum", "SSAMVR",
              "SSNMVR", "SSMaxMVR", "SSMinMVR", "SSVHigh", "SSVLow", *BLOCK_STEPS, *BLOCK_MVAR],
    "Area": ["AreaNum", "SAName", "BGAGC", "BGReportLimits", "BGReportLimMinKV", "BGReportLimMaxKV"],
    "Zone": ["ZoneNum", "BGReportLimits", "BGReportLimMinKV", "BGReportLimMaxKV"],
    "SuperArea": ["SAName", "BGAGC"],
    "LimitSet": ["LSName", "LSDisabled", "LSLineRateSet", "LSLineRateSet:1", "LSAmpMVA"],
    "Contingency": ["CTGLabel"],
    "ViolationCTG": ["CTGLabel"],
}
# single-record objects the reader turns into scalars
SCALARS = {"Sim_Solution_Options": ["SBase", "ChkTaps", "ConvergenceTol:2"],
           "Limit_Monitoring_Options": ["LMS_IgnoreRadial"]}

NUMERIC = {
    "BusNum", "BusNum:1", "BusNomVolt", "BusNomVolt:1", "BusPUVolt", "BusVoltLimLow", "BusVoltLimHigh",
    "AreaNum", "ZoneNum", "BusMismatchP", "BusMismatchQ", "LineR", "LineX", "LineC", "LineMW",
    "LineMVA", "LineMaxPercent", "XFRegBus", "XFRegMin", "XFRegMax", "XFTapMin", "XFTapMax", "XFStep",
    "LineTap", "XFRegError", "GenMW", "GenMVR", "GenMWMax", "GenMVRMax", "GenMVRMin", "Latitude",
    "Longitude", "Latitude:1", "Longitude:1", "CustomInteger:1", "GenCostCurvePoints", "GenMCost",
    "LoadMW", "LoadMVR", "SSRegNum", "SSAMVR", "SSNMVR", "SSMaxMVR", "SSMinMVR",
    "BGReportLimMinKV", "BGReportLimMaxKV", *RATINGS, "GenMWMin", "SSVHigh", "SSVLow",
    *BLOCK_STEPS, *BLOCK_MVAR,
}


def typed(df: pd.DataFrame | None, columns: list[str]) -> pd.DataFrame:
    """Numbers as floats ('None' and blanks become NaN), text stripped, every declared column
    present. None (PowerWorld's answer for an object with no rows) becomes an empty frame.
    The declared columns the source lacked are listed in `attrs["unread"]`."""
    if df is None:
        return pd.DataFrame({c: pd.Series(dtype=float if c in NUMERIC else object) for c in columns})
    out = df.copy()
    unread = [c for c in columns if c not in out.columns]
    for c in unread:
        out[c] = float("nan") if c in NUMERIC else ""
    for c in out.columns:
        if c in NUMERIC:
            out[c] = pd.to_numeric(out[c], errors="coerce").astype(float)
        else:
            out[c] = out[c].astype(str).str.strip()
    out = out.reset_index(drop=True)
    out.attrs["unread"] = unread
    return out


@dataclass
class Solve:
    """The one AC solve the engine runs on the case as it opened."""
    ran: bool = False
    raised: str | None = None            # PowerWorld's error text when SolvePowerFlow raised
    max_mismatch_mva: float | None = None
    tolerance_mva: float | None = None   # Sim_Solution_Options.ConvergenceTol:2

    @property
    def tolerance_unread(self) -> bool:
        return self.tolerance_mva is None or self.max_mismatch_mva is None

    @property
    def converged(self) -> bool:
        """The raise decides. The mismatch check is a second test, applied only when both numbers
        were read: an unreadable tolerance must not turn the case NOT READY on the engine's account."""
        if not self.ran or self.raised is not None:
            return False
        return self.tolerance_unread or self.max_mismatch_mva <= self.tolerance_mva


@dataclass
class CaseData:
    frames: dict[str, pd.DataFrame]
    scalars: dict = field(default_factory=dict)
    solve: Solve = field(default_factory=Solve)

    def __post_init__(self):
        self.frames = {obj: typed(self.frames.get(obj), cols) for obj, cols in READS.items()}

    def get(self, obj: str) -> pd.DataFrame:
        return self.frames[obj]

    def to_json(self, path: str | Path) -> None:
        # unread columns are left out, so typed() marks them unread again on load
        payload = {"frames": {o: d.drop(columns=d.attrs.get("unread", [])).to_dict(orient="list")
                              for o, d in self.frames.items()},
                   "scalars": self.scalars, "solve": asdict(self.solve)}
        raw = json.dumps(payload, default=str).encode("utf-8")
        Path(path).write_bytes(gzip.compress(raw) if str(path).endswith(".gz") else raw)

    @classmethod
    def from_json(cls, path: str | Path) -> "CaseData":
        raw = Path(path).read_bytes()
        d = json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)
        return cls({o: pd.DataFrame(v) for o, v in d["frames"].items()}, d["scalars"], Solve(**d["solve"]))
