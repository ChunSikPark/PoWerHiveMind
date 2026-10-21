import pytest

from auditcase import case
from casedata import CaseData
from summary import case_summary


def test_totals_losses_and_headroom(frames):
    s = case_summary(case(frames))
    assert s["load_mw"] == 420 and s["generation_mw"] == 430 and s["losses_mw"] == 10
    assert s["headroom_dispatchable_mw"] == 100            # wind and solar never count as headroom
    assert s["mvar_range"] == [-130, 230]


def test_fuel_rows_keep_the_case_labels(frames):
    frames["Gen"].loc[len(frames["Gen"])] = {**frames["Gen"].iloc[0].to_dict(), "BusNum": 4, "GenID": "B1",
                                              "GenFuelType": "MWH (Electricity use for Energy Storage)",
                                              "GenStatus": "Open"}
    rows = {r["fuel"]: r for r in case_summary(case(frames))["fuel"]}
    assert set(rows) == {"NG (Natural Gas)", "WND (Wind)", "SUN (Solar)", "MWH (Electricity use for Energy Storage)"}
    assert rows["MWH (Electricity use for Energy Storage)"]["units_online"] == 0
    assert rows["MWH (Electricity use for Energy Storage)"]["units_total"] == 1
    assert rows["WND (Wind)"]["headroom_mw"] is None and rows["WND (Wind)"]["weather_limited"]
    assert rows["NG (Natural Gas)"]["share_of_output"] == pytest.approx(300 / 430)


def test_offline_capacity_is_not_headroom(frames):
    frames["Gen"].loc[0, "GenStatus"] = "Open"
    assert case_summary(case(frames))["headroom_dispatchable_mw"] == 0


def test_overshoot_is_reported_beside_generation(frames):
    frames["Gen"].loc[0, "GenMW"] = 412.0
    assert case_summary(case(frames))["generation_includes_overshoot_mw"] == pytest.approx(12)


def test_shunts_and_size(frames):
    s = case_summary(case(frames))
    assert s["shunts"] == {"count": 1, "in_service": 1, "mvar_now": 30, "capacitive_mvar": 60, "inductive_mvar": 0}
    assert s["size"] == {"buses": 6, "branches": 6, "transformers": 1, "areas": 1, "zones": 1,
                         "kv_levels": [138.0, 345.0]}


def test_opf_movable_headroom_is_dispatchable_units_in_opf_areas(frames):
    assert case_summary(case(frames), opf=True)["opf_movable_headroom_mw"] == 100    # wind and solar left out
    frames["Area"].loc[0, "BGAGC"] = "Off AGC"
    assert case_summary(case(frames), opf=True)["opf_movable_headroom_mw"] == 0


def test_a_super_area_on_opf_makes_its_areas_opf_areas(frames):
    import pandas as pd
    frames["Area"].loc[0, ["BGAGC", "SAName"]] = ["Off AGC", "S"]
    frames["SuperArea"] = pd.DataFrame({"SAName": ["S"], "BGAGC": ["OPF"]})
    assert case_summary(case(frames), opf=True)["opf_movable_headroom_mw"] == 100


def test_summary_of_a_case_with_no_shunts_or_loads(frames):
    frames["Shunt"], frames["Load"] = None, None
    s = case_summary(case(frames))
    assert s["shunts"]["count"] == 0 and s["load_mw"] == 0


def test_hawaii40_summary(hawaii):
    s = case_summary(CaseData.from_json(hawaii))
    assert s["size"]["buses"] == 37 and s["size"]["branches"] == 89 and s["size"]["transformers"] == 12
    assert round(s["load_mw"]) == 1136 and round(s["losses_mw"]) == 18
    assert {r["fuel"] for r in s["fuel"]} >= {"SUN (Solar)", "WND (Wind)", "DFO (Distillate Fuel Oil)"}


def test_the_overshoot_floor_is_the_rules_threshold(frames, monkeypatch):
    import summary
    frames["Gen"].loc[0, "GenMW"] = 400.05                   # 0.05 MW over: noise at the default floor
    assert case_summary(case(frames))["generation_includes_overshoot_mw"] == 0
    monkeypatch.setattr(summary, "GEN_OVER_MIN_MW", 0.01)
    assert case_summary(case(frames))["generation_includes_overshoot_mw"] == pytest.approx(0.05)


def test_load_on_disconnected_buses_is_reported_beside_the_solved_total(frames):
    import report
    from auditcase import add_dead_bus
    add_dead_bus(frames, 7, load_mw=766.0, gen_mw=100.0)
    frames["Load"].loc[frames["Load"].BusNum == 7, "LoadMW"] = 766.0     # even if LoadMW kept the setpoint
    s = case_summary(case(frames))
    assert s["load_mw"] == 420 and s["load_mw_dead_buses"] == 766
    assert s["generation_mw"] == 430 and s["generation_mw_dead_buses"] == 100
    md = report.render_md(report.build(case(frames), []))
    assert ("| Load | 420 solved + 766 on disconnected buses, not served (setpoint; area and zone multipliers "
            "not read) | 50 |") in md
    assert "| Generation (online) | 430 solved + 100 on disconnected buses, not served | 20 |" in md


def test_dead_bus_load_in_the_summary_is_after_its_multipliers(frames):
    import report
    from auditcase import add_dead_bus
    add_dead_bus(frames, 7, load_mw=766.28, area_mult=1.0, zone_mult=1.305)
    s = case_summary(case(frames))
    assert s["load_mw_dead_buses"] == pytest.approx(1000, abs=0.1) and s["load_mw_dead_buses_multiplier_applied"]
    assert "| Load | 420 solved + 1,000 on disconnected buses, not served | 50 |" in report.render_md(report.build(case(frames), []))


def test_no_dead_bus_load_leaves_the_summary_rows_alone(frames):
    import report
    s = case_summary(case(frames))
    assert s["load_mw_dead_buses"] == 0 and s["generation_mw_dead_buses"] == 0
    assert "| Load | 420 | 50 |" in report.render_md(report.build(case(frames), []))
