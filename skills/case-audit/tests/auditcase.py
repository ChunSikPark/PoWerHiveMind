"""A tiny hand-built case every rule test starts from.

toy(): a healthy 6-bus case. Buses 1-2-3 are a 345 kV triangle (the meshed core), bus 4 is
138 kV behind a 345/138 LTC 3-4, and buses 5-6 are a 345 kV radial chain 3-5-6 that the stub
tests load or unload. A test changes one thing and asserts one rule's answer.
"""
import pandas as pd

from casedata import CaseData, Solve


def _line(f, t, ckt="1", r=0.001, x=0.01, c=0.02, mw=50.0, pct=30.0, rating=200.0):
    return {"BusNum": f, "BusNum:1": t, "LineCircuit": ckt, "LineStatus": "Closed", "LineXfmr": "NO",
            "LineR": r, "LineX": x, "LineC": c, "LineMW": mw, "LineMVA": abs(mw), "LineMaxPercent": pct,
            "LineMonEle:1": "YES", "BusNomVolt": 345.0, "BusNomVolt:1": 345.0, "LineXFType": "",
            "XFAuto": "", "XFRegBus": 0.0, "LineAMVA": rating, "LineAMVA:1": rating, "LineAMVA:2": rating}


def toy() -> dict:
    bus = pd.DataFrame([
        {"BusNum": n, "BusName": f"BUS{n}", "BusStatus": "Connected", "BusCat": "Slack" if n == 1 else "PQ",
         "BusIsStarBus": "NO", "BusNomVolt": 138.0 if n == 4 else 345.0, "BusPUVolt": 1.0, "BusVoltLim": "NO",
         "BusVoltLimLow": 0.9, "BusVoltLimHigh": 1.1, "BusMonEle:1": "YES", "AreaNum": 1, "ZoneNum": 1,
         "BusMismatchP": 0.0, "BusMismatchQ": 0.0} for n in range(1, 7)])
    xf = {**_line(3, 4), "LineXfmr": "YES", "BusNomVolt:1": 138.0, "LineXFType": "LTC", "XFAuto": "YES",
          "XFRegBus": 4.0, "XFRegMin": 0.98, "XFRegMax": 1.02, "XFRegTargetType": "Max/Min",
          "XFTapMin": 0.9, "XFTapMax": 1.1, "XFStep": 0.00625, "LineTap": 1.0, "XFRegError": 0.0}
    branch = pd.DataFrame([_line(1, 2), _line(2, 3), _line(1, 3), xf,
                           _line(3, 5, mw=80.0, pct=40.0), _line(5, 6, mw=40.0, pct=20.0)])
    gen = pd.DataFrame([
        {"BusNum": 1, "GenID": "1", "GenStatus": "Closed", "GenMW": 300.0, "GenMVR": 20.0, "GenMWMax": 400.0,
         "GenMVRMax": 200.0, "GenMVRMin": -100.0, "GenFuelType": "NG (Natural Gas)", "TSPFWModelString": "",
         "GenAGCAble": "YES", "GenCostModel": "Cubic", "GenCostCurvePoints": 5, "GenMCost": 20.0, "AreaNum": 1},
        {"BusNum": 2, "GenID": "W1", "GenStatus": "Closed", "GenMW": 90.0, "GenMVR": 0.0, "GenMWMax": 100.0,
         "GenMVRMax": 30.0, "GenMVRMin": -30.0, "GenFuelType": "WND (Wind)", "TSPFWModelString": "WindClass2",
         "Latitude:1": 30.0, "Longitude:1": -97.0, "GenAGCAble": "YES", "GenCostModel": "Cubic",
         "GenCostCurvePoints": 5, "GenMCost": 1.0, "AreaNum": 1},
        {"BusNum": 6, "GenID": "S1", "GenStatus": "Closed", "GenMW": 40.0, "GenMVR": 0.0, "GenMWMax": 50.0,
         "GenMVRMax": 0.0, "GenMVRMin": 0.0, "GenFuelType": "SUN (Solar)", "TSPFWModelString": "SolarPVBasic2",
         "Latitude:1": 30.5, "Longitude:1": -97.5, "GenAGCAble": "YES", "GenCostModel": "Cubic",
         "GenCostCurvePoints": 5, "GenMCost": 1.0, "AreaNum": 1}])
    load = pd.DataFrame([{"BusNum": 4, "LoadID": "1", "LoadStatus": "Closed", "LoadMW": 420.0, "LoadMVR": 50.0}])
    shunt = pd.DataFrame([{"BusNum": 4, "ShuntID": "1", "SSStatus": "Closed", "SSCMode": "Discrete",
                           "AutoControl": "YES", "SSRegNum": 4.0, "SSAMVR": 30.0, "SSNMVR": 30.0,
                           "SSMaxMVR": 60.0, "SSMinMVR": 0.0}])
    area = pd.DataFrame([{"AreaNum": 1, "SAName": "", "BGAGC": "OPF", "BGReportLimits": "YES", "BGReportLimMinKV": 0.0,
                          "BGReportLimMaxKV": 9999.0}])
    zone = pd.DataFrame([{"ZoneNum": 1, "BGReportLimits": "YES", "BGReportLimMinKV": 0.0, "BGReportLimMaxKV": 9999.0}])
    limitset = pd.DataFrame([{"LSName": "Default", "LSDisabled": "NO", "LSLineRateSet": "A",
                              "LSLineRateSet:1": "B", "LSAmpMVA": "MVA"}])
    contingency = pd.DataFrame({"CTGLabel": ["L_1_2", "L_2_3"]})
    return {"Bus": bus, "Branch": branch, "Gen": gen, "Load": load, "Shunt": shunt, "Area": area,
            "Zone": zone, "LimitSet": limitset, "Contingency": contingency}


def add_dead_bus(frames, n, load_mw=None, gen_mw=None, kv=230.0, area_mult=None, zone_mult=None):
    """A bus with no branches, as PowerWorld reads it: Disconnected at 0 pu, LoadMW and GenMW 0,
    the setpoint only in LoadSMW and GenMWSetPoint. Optionally one in-service load (with its area and
    zone multipliers, left unread when None) and one unit."""
    def add(obj, row):
        frames[obj] = pd.concat([frames[obj], pd.DataFrame([row])], ignore_index=True)
    add("Bus", {**frames["Bus"].iloc[1].to_dict(), "BusNum": n, "BusName": f"NEW{n}",
                "BusStatus": "Disconnected", "BusPUVolt": 0.0, "BusNomVolt": kv})
    if load_mw is not None:
        mult = {"LoadMultiplier": area_mult, "LoadMultiplier:2": zone_mult}
        add("Load", {"BusNum": n, "LoadID": "1", "LoadStatus": "Closed", "LoadMW": 0.0, "LoadMVR": 0.0,
                     "LoadSMW": load_mw, **{k: v for k, v in mult.items() if v is not None}})
    if gen_mw is not None:
        add("Gen", {**frames["Gen"].iloc[0].to_dict(), "BusNum": n, "GenID": "N1", "GenMW": 0.0, "GenMVR": 0.0,
                    "GenMWSetPoint": gen_mw})
    return frames


def case(frames=None, converged=True, **scalars) -> CaseData:
    solve = Solve(ran=True, max_mismatch_mva=0.0 if converged else 50.0, tolerance_mva=0.1)
    return CaseData(frames if frames is not None else toy(),
                    {"SBase": "100", "ChkTaps": "YES", **scalars}, solve)
