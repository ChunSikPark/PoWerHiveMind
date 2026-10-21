import pandas as pd
import pytest

from auditcase import case
from casedata import CaseData, Solve
from findings import FYI, STOPS, WORTH
from rules_base import ac_converges, dc_skeleton, gen_over_nameplate, stale_ctg_results


def test_converged_case_has_no_convergence_finding(frames):
    assert ac_converges(case(frames)) == []


def test_raised_solve_stops_every_study(frames):
    cd = CaseData(frames, {}, Solve(True, "NR PowerFlow - Exceeded maximum number of iterations", 2e-5, 1e-5))
    [f] = ac_converges(cd)
    assert f.severity == STOPS and set(f.stops) == {"base", "n1", "timestep", "opf", "scopf"}
    assert "Exceeded maximum number" in f.why


def test_mismatch_over_tolerance_without_a_raise_still_fails(frames):
    [f] = ac_converges(CaseData(frames, {}, Solve(True, None, 3.0, 0.1)))
    assert "3.0 MVA" in f.why


def test_real_network_is_not_a_skeleton(frames):
    assert dc_skeleton(case(frames)) == []


def test_placeholder_resistance_is_a_skeleton(frames):
    lines = frames["Branch"].LineXfmr == "NO"
    frames["Branch"].loc[lines, "LineR"] = 1e-7
    frames["Branch"].loc[lines, "LineC"] = 0.0
    [f] = dc_skeleton(case(frames))
    assert f.severity == STOPS and f.details["median_xr"] > 1000 and f.details["share_no_r_no_c"] == 1.0
    assert f.scope == "every AC study; a DC-only study can still run"


def test_part_skeleton_is_worth_a_look(frames):
    frames["Branch"].loc[0, ["LineR", "LineC"]] = [1e-7, 0.0]             # 1 of 5 closed lines
    [f] = dc_skeleton(case(frames))
    assert f.severity == WORTH and f.where == [{"BusNum": 1, "BusNum:1": 2, "LineCircuit": "1"}]


def test_zero_resistance_everywhere_says_undefined_not_nan(frames):
    frames["Branch"].loc[frames["Branch"].LineXfmr == "NO", ["LineR", "LineC"]] = [0.0, 0.0]
    [f] = dc_skeleton(case(frames))
    assert f.severity == STOPS and "undefined (R = 0 on every line)" in f.what and "nan" not in f.what


def test_small_overshoot_is_worth_a_look_with_its_mw(frames):
    frames["Gen"].loc[0, "GenMW"] = 403.0                   # 3 MW over a 400 MW unit: under max(4, 5)
    [f] = gen_over_nameplate(case(frames))
    assert f.severity == WORTH and f.where[0]["over_mw"] == 3.0 and f.where[0]["slack"]
    assert "say the MW" not in f.why                         # an instruction to the agent, not why it matters


def test_large_overshoot_stops_the_study(frames):
    frames["Gen"].loc[0, "GenMW"] = 460.0
    [f] = gen_over_nameplate(case(frames))
    assert f.severity == STOPS and f.where[0] == {"BusNum": 1, "GenID": "1", "GenMW": 460.0,
                                                  "GenMWMax": 400.0, "over_mw": 60.0, "slack": True}


def test_offline_unit_over_its_max_is_ignored(frames):
    frames["Gen"].loc[0, ["GenMW", "GenStatus"]] = [460.0, "Open"]
    assert gen_over_nameplate(case(frames)) == []


def test_stale_ctg_rows_are_fyi(frames):
    frames["ViolationCTG"] = pd.DataFrame({"CTGLabel": ["a", "a", "b"]})
    [f] = stale_ctg_results(case(frames))
    assert f.severity == FYI and f.details["rows"] == 3
    frames["ViolationCTG"] = None
    assert stale_ctg_results(case(frames)) == []


def test_load_on_a_disconnected_bus_stops_every_study(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    add_dead_bus(frames, 7, load_mw=766.0)
    add_dead_bus(frames, 8, load_mw=766.0)
    [f] = dead_bus_injection(case(frames))
    assert f.severity == STOPS and set(f.stops) == {"base", "n1", "timestep", "opf", "scopf"}
    assert f.where[0] == {"BusNum": 7, "BusName": "NEW7", "BusNomVolt": 230.0, "AreaNum": 1, "load_mw": 766.0,
                          "load_setpoint_mw": 766.0, "multiplier_applied": False, "gen_mw": 0.0}
    assert f.details["load_mw"] == 1532 and f.details["gen_mw"] == 0 and "1,532 MW" in f.what
    assert "area and zone multipliers not read, not applied" in f.what   # never a silent 1.0


def test_stranded_load_is_reported_after_its_multipliers(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    for n in (7, 8):
        add_dead_bus(frames, n, load_mw=766.28, area_mult=1.0, zone_mult=1.305)
    [f] = dead_bus_injection(case(frames))
    assert f.details["load_mw"] == pytest.approx(2000, abs=0.1)
    assert f.details["load_setpoint_mw"] == pytest.approx(1532.56) and f.details["multiplier_applied"]
    assert "2,000 MW of load (1,533 MW setpoint × 1.305 zone multiplier)" in f.what
    assert f.where[0]["load_mw"] == pytest.approx(1000, abs=0.1) and f.where[0]["load_setpoint_mw"] == 766.28


def test_the_stop_size_is_on_the_load_after_its_multipliers(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    [f] = dead_bus_injection(case(add_dead_bus(frames, 7, load_mw=8.0, area_mult=1.0, zone_mult=1.5)))
    assert f.severity == STOPS and f.details["load_mw"] == 12


def test_generation_on_a_disconnected_bus_is_counted_at_its_setpoint(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    [f] = dead_bus_injection(case(add_dead_bus(frames, 7, gen_mw=150.0)))
    assert f.severity == STOPS and f.where[0]["gen_mw"] == 150 and f.details["gen_mw"] == 150


def test_a_small_stranded_load_is_worth_a_look_and_stops_nothing(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    [f] = dead_bus_injection(case(add_dead_bus(frames, 7, load_mw=2.0)))
    assert f.severity == WORTH and f.stops == ()


def test_an_unread_setpoint_is_not_taken_as_zero(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    add_dead_bus(frames, 7, load_mw=766.0)
    frames["Load"] = frames["Load"].drop(columns="LoadSMW")
    [f] = dead_bus_injection(case(frames))
    assert f.severity == STOPS and f.details["load_mw"] is None and "nan" not in f.what


def test_an_empty_dead_bus_is_not_flagged(frames):
    from auditcase import add_dead_bus
    from rules_base import dead_bus_injection
    add_dead_bus(frames, 7)                                 # nothing attached: common and harmless
    add_dead_bus(frames, 8, load_mw=766.0)
    frames["Load"].loc[frames["Load"].BusNum == 8, "LoadStatus"] = "Open"
    assert dead_bus_injection(case(frames)) == []


def test_the_verdicts_say_not_ready_when_load_is_stranded(frames):
    import report
    from auditcase import add_dead_bus
    r = report.build(case(add_dead_bus(frames, 7, load_mw=766.0)), [])
    assert r["verdicts"]["base"]["verdict"] == "NOT READY" and r["verdicts"]["n1"]["verdict"] == "NOT READY"
    assert r["verdicts"]["base"]["stopped_by"] == ["base.dead_bus_injection"]
