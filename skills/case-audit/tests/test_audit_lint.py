import json
import time

import pytest

import checks
import report
from auditcase import case, toy
from casedata import BLOCK_MVAR, BLOCK_STEPS, NUMERIC, READS, CaseData
from findings import FYI, WORTH
from rules_lint import (GEN_LIMITS, bus_names, gen_below_min, gen_limits, islands, missing_ratings, negative_x,
                        nominal_kv, shunt_band_inverted, shunt_steps)

ALL = [shunt_steps, shunt_band_inverted, gen_below_min, gen_limits, negative_x, missing_ratings,
       bus_names, islands, nominal_kv]
LINT = [r for r, p, _, _ in checks.RULES if p == "lint"]
KEYS = {"BusNum", "BusNum:1", "LineCircuit", "GenID", "ShuntID", "island"}
SLOTS = [*BLOCK_STEPS[1:], *BLOCK_MVAR[1:]]


def S(skipped):
    return {s["rule"]: s["reason"] for s in skipped}


def _fields(reason):
    return set(reason.split("field(s) ", 1)[1].split(" not read", 1)[0].split(", "))


def _verdict(findings, rule):
    rows = [f.to_dict() if hasattr(f, "to_dict") else f for f in findings]
    return sorted((f["severity"], f["triage"], f["what"], f["why"],
                   json.dumps(f["details"], sort_keys=True, default=str),
                   tuple(tuple(sorted((k, str(v)) for k, v in row.items() if k in KEYS))
                         for row in f["where"])) for f in rows if f["rule"] == rule)


def _lint_only(monkeypatch, cd):
    monkeypatch.setattr(checks, "RULES", [t for t in checks.RULES if t[1] == "lint"])
    return checks.run_rules(cd, ["lint"])


def _lintable(frames):
    """The toy with the fields only lint reads: unit minimums and the shunt's blocks and band."""
    frames["Gen"]["GenMWMin"] = 0.0
    sh = frames["Shunt"]
    for c in SLOTS:
        sh[c] = float("nan")                                       # the live shape: every slot returned, none used
    sh[["SSBlockNumSteps", "SSBlockMVarPerStep", "SSVLow", "SSVHigh"]] = [4.0, 15.0, 0.98, 1.02]
    sh["SSNMVR"] = 30.0                                            # 2 of 4 steps of 15
    return frames


def _defective(frames):
    f = _lintable(frames)
    f["Shunt"][["SSNMVR", "SSVHigh"]] = [20.0, 0.5]
    f["Gen"].loc[0, "GenMWMin"] = 350.0
    f["Gen"].loc[1, "GenMVRMax"] = float("nan")
    f["Load"].loc[len(f["Load"])] = {"BusNum": 5, "LoadID": "1", "LoadStatus": "Closed",
                                      "LoadMW": 10.0, "LoadMVR": 0.0}
    f["Branch"].loc[0, "LineX"] = -0.01
    f["Branch"].loc[1, "LineAMVA"] = 0.0
    f["Branch"].loc[2, "LineAMVA:1"] = 0.0
    f["Branch"].loc[[4, 5], "LineStatus"] = "Open"
    f["Bus"].loc[2, "BusName"] = ""
    f["Bus"].loc[0, "BusNomVolt"] = 345.1234
    f["Shunt"].loc[len(f["Shunt"])] = {"BusNum": 4, "ShuntID": "2", "SSStatus": "Closed", "SSCMode": "Discrete",
                                       "SSNMVR": 5.0, "SSVLow": 0.98, "SSVHigh": 1.02,
                                       "SSBlockNumSteps": 1.0, "SSBlockMVarPerStep": 15.0,
                                       "SSBlockNumSteps:1": 1.0, "SSBlockMVarPerStep:1": -10.0}
    return f


def test_the_defective_toy_fires_every_lint_rule(frames):
    r = report.build(case(_defective(frames)), ["lint"])
    assert not any(rule.startswith("lint.") for rule in S(r["rules_skipped"]))
    assert all(_verdict(r["findings"], rule) for rule in LINT)
    assert len(_verdict(r["findings"], "lint.missing_ratings")) == 2
    assert len(_verdict(r["findings"], "lint.islands")) == 2
    [x] = [f for f in r["findings"] if f["rule"] == "lint.shunt_steps"]
    assert [w["ShuntID"] for w in x["where"]] == ["1"]


@pytest.mark.parametrize("obj, col", [(o, c) for o, cs in READS.items() for c in cs if o in toy()])
def test_every_unread_lint_field_is_declared(monkeypatch, obj, col):
    control, _, _ = _lint_only(monkeypatch, case(_defective(toy())))
    for variant in ("drop", "nan", "blank"):
        f = _defective(toy())
        if variant == "drop":
            if col not in f[obj].columns:
                continue
            f[obj] = f[obj].drop(columns=[col])
        elif variant == "nan":
            if col not in NUMERIC or col in SLOTS:
                continue
            f[obj][col] = float("nan")
        else:
            if col in NUMERIC:
                continue
            f[obj][col] = ""
        findings, _, skipped = _lint_only(monkeypatch, case(f))
        skipped = S(skipped)
        for rule in LINT:
            assert (_verdict(findings, rule) == _verdict(control, rule)
                    or (rule in skipped and col in _fields(skipped[rule]))), (obj, col, variant, rule)


def test_shunt_steps_needs_the_nominal_mvar(frames):
    f = _defective(frames)
    f["Shunt"] = f["Shunt"].drop(columns=["SSNMVR"])
    for _ in range(2):
        r = report.build(case(f), ["lint"])
        assert "lint.shunt_steps" not in r["rules_run"]
        assert S(r["rules_skipped"])["lint.shunt_steps"] == "field(s) SSNMVR not read"
        assert shunt_steps(case(f)) == []
        f["Shunt"]["SSNMVR"] = float("nan")


@pytest.mark.parametrize("col", ["SSBlockNumSteps:1", "SSBlockMVarPerStep:1"])
def test_a_missing_later_block_is_not_read(frames, col):
    f = _defective(frames)
    r0 = report.build(case(f), ["lint"])
    assert "lint.shunt_steps" in r0["rules_run"] and "lint.shunt_steps" not in S(r0["rules_skipped"])
    f["Shunt"] = f["Shunt"].drop(columns=[col])
    r = report.build(case(f), ["lint"])
    assert "lint.shunt_steps" not in r["rules_run"]
    assert S(r["rules_skipped"])["lint.shunt_steps"] == f"field(s) {col} not read"
    assert not [x for x in r["findings"] if x["rule"] == "lint.shunt_steps"]
    assert shunt_steps(case(f)) == []


def test_a_blank_unused_block_slot_is_data(frames):
    f = _defective(frames)
    f["Shunt"][SLOTS] = float("nan")
    r = report.build(case(f), ["lint"])
    assert "lint.shunt_steps" in r["rules_run"] and "lint.shunt_steps" not in S(r["rules_skipped"])
    [x] = [y for y in r["findings"] if y["rule"] == "lint.shunt_steps"]
    assert [w["ShuntID"] for w in x["where"]] == ["1", "2"] and "between steps" in x["what"]


@pytest.mark.parametrize("rule, obj, col, half", [
    ("lint.shunt_steps", "Shunt", "ShuntID", "whole"),
    ("lint.shunt_steps", "Shunt", "SSCMode", "whole"),
    ("lint.shunt_band_inverted", "Shunt", "ShuntID", "whole"),
    ("lint.shunt_band_inverted", "Shunt", "SSCMode", "whole"),
    ("lint.gen_below_min", "Gen", "GenID", "whole"),
    ("lint.gen_below_min", "Gen", "GenStatus", "whole"),
    ("lint.gen_limits", "Gen", "GenID", "whole"),
    ("lint.negative_x", "Branch", "LineCircuit", "whole"),
    ("lint.negative_x", "Branch", "LineStatus", "whole"),
    ("lint.negative_x", "Bus", "BusIsStarBus", "whole"),
    ("lint.missing_ratings", "Branch", "LineCircuit", "whole"),
    ("lint.missing_ratings", "Branch", "LineStatus", "whole"),
    ("lint.missing_ratings", "LimitSet", "LSDisabled", "partial"),
    ("lint.missing_ratings", "LimitSet", "LSLineRateSet:1", "partial"),
    ("lint.bus_names", "Bus", "BusName", "whole"),
    ("lint.islands", "Bus", "BusStatus", "whole"),
    ("lint.islands", "Branch", "LineStatus", "whole"),
    ("lint.islands", "Bus", "BusCat", "partial"),
    ("lint.islands", "Gen", "GenStatus", "partial"),
    ("lint.islands", "Load", "LoadStatus", "partial"),
])
def test_a_text_field_blank_on_every_row_is_not_read(frames, rule, obj, col, half):
    f = _defective(frames)
    f[obj][col] = ""
    r = report.build(case(f), ["lint"])
    skipped = S(r["rules_skipped"])
    found = [x for x in r["findings"] if x["rule"] == rule]
    assert rule in skipped and col in _fields(skipped[rule])
    assert (rule in r["rules_run"]) == (half == "partial")
    if half == "whole":
        assert skipped[rule] == f"field(s) {col} not read" and found == []
    elif rule == "lint.missing_ratings":
        assert len(found) == 1 and "no rating A" in found[0]["what"]
        assert skipped[rule] == f"field(s) {col} not read; the rating B/C half was not checked"
    else:
        assert len(found) == 1 and found[0]["what"].startswith("2 energized island(s)")
        assert skipped[rule] == f"field(s) {col} not read; the slack count was not checked"


@pytest.mark.parametrize("col", ["LSLineRateSet:1", "LSDisabled"])
def test_missing_ratings_without_the_n1_rate_set_drops_the_bc_half(frames, col):
    f = _defective(frames)
    r0 = report.build(case(f), ["lint"])
    found = [x for x in r0["findings"] if x["rule"] == "lint.missing_ratings"]
    assert len(found) == 2
    [bc] = [x for x in found if "no B or C" in x["what"]]
    assert bc["severity"] == WORTH and bc["triage"] == "Broken"
    assert bc["details"]["contingency_sets_hit"] == ["B"]
    f["LimitSet"] = f["LimitSet"].drop(columns=[col])
    r = report.build(case(f), ["lint"])
    assert "lint.missing_ratings" in r["rules_run"]
    assert S(r["rules_skipped"])["lint.missing_ratings"] == (
        f"field(s) {col} not read; the rating B/C half was not checked")
    [a] = [x for x in r["findings"] if x["rule"] == "lint.missing_ratings"]
    assert "no rating A" in a["what"] and a["severity"] == WORTH and a["triage"] == "Broken"


@pytest.mark.parametrize("obj, col", [
    ("Bus", "BusCat"), ("Gen", "BusNum"), ("Gen", "GenStatus"), ("Gen", "GenMW"),
    ("Load", "BusNum"), ("Load", "LoadStatus"), ("Load", "LoadMW"),
])
def test_islands_slack_half_needs_its_fields(frames, obj, col):
    f = _defective(frames)
    r0 = report.build(case(f), ["lint"])
    found = [x for x in r0["findings"] if x["rule"] == "lint.islands"]
    assert len(found) == 2 and found[1]["what"].startswith("2 island(s) carrying")
    f[obj] = f[obj].drop(columns=[col])
    r = report.build(case(f), ["lint"])
    assert "lint.islands" in r["rules_run"]
    assert S(r["rules_skipped"])["lint.islands"] == (
        f"field(s) {col} not read; the slack count was not checked")
    [island] = [x for x in r["findings"] if x["rule"] == "lint.islands"]
    assert island["what"].startswith("2 energized island(s)")


@pytest.mark.parametrize("obj, col, rules", [
    ("Bus", "BusNum", {"negative_x", "bus_names", "islands", "nominal_kv"}),
    ("Branch", "BusNum", {"negative_x", "missing_ratings", "islands"}),
    ("Branch", "BusNum:1", {"negative_x", "missing_ratings", "islands"}),
    ("Branch", "LineCircuit", {"negative_x", "missing_ratings"}),
    ("Gen", "BusNum", {"gen_below_min", "gen_limits"}),
    ("Gen", "GenID", {"gen_below_min", "gen_limits"}),
    ("Shunt", "BusNum", {"shunt_steps", "shunt_band_inverted"}),
    ("Shunt", "ShuntID", {"shunt_steps", "shunt_band_inverted"}),
])
def test_a_missing_key_is_not_read_and_never_raises(frames, obj, col, rules):
    f = _defective(frames)
    f[obj] = f[obj].drop(columns=[col])
    for _ in range(2 if col in NUMERIC else 1):
        r = report.build(case(f), ["lint"])
        for rule in rules:
            rule = f"lint.{rule}"
            assert rule not in r["rules_run"]
            assert S(r["rules_skipped"])[rule] == f"field(s) {col} not read"
        f[obj][col] = float("nan")


def test_an_object_with_no_rows_skips_no_lint_rule(frames):
    f = _lintable(frames)
    f["Shunt"] = f["Shunt"].iloc[0:0]
    r = report.build(case(f), ["lint"])
    for rule in ("lint.shunt_steps", "lint.shunt_band_inverted"):
        assert rule in r["rules_run"] and rule not in S(r["rules_skipped"])
    assert not any(x["rule"].startswith("lint.") for x in r["findings"])


def test_healthy_toy_has_no_lint_finding(frames):
    cd = case(_lintable(frames))
    assert [f for rule in ALL for f in rule(cd)] == []


def test_unread_fields_flag_nothing(frames):
    cd = case(frames)                                              # no GenMWMin, no blocks, no band
    assert shunt_steps(cd) == [] and shunt_band_inverted(cd) == [] and gen_below_min(cd) == []


@pytest.mark.parametrize("rule, obj, col, seed", [
    (shunt_steps, "Shunt", "SSCMode", lambda f: f["Shunt"].__setitem__("SSNMVR", 20.0)),
    (shunt_band_inverted, "Shunt", "SSVLow", lambda f: f["Shunt"].__setitem__("SSVHigh", 0.5)),
    (gen_below_min, "Gen", "GenMW", lambda f: f["Gen"].__setitem__("GenMWMin", 1e4)),
    (negative_x, "Bus", "BusIsStarBus", lambda f: f["Branch"].__setitem__("LineX", -0.01)),
    (missing_ratings, "Branch", "LineAMVA", None),
    (missing_ratings, "Branch", "LineAMVA:1", None),
    (bus_names, "Bus", "BusName", None),
    (islands, "Branch", "LineStatus", None),
    (islands, "Bus", "BusCat", None),
    (nominal_kv, "Bus", "BusNomVolt", None),
])
def test_a_field_that_was_not_read_flags_nothing(frames, rule, obj, col, seed):
    f = _lintable(frames)
    if seed:
        seed(f)                                                    # a defect the rule would otherwise report
    f[obj] = f[obj].drop(columns=[col])
    assert rule(case(f)) == []
    if col in NUMERIC:                                             # read, but NaN on every row: still unread
        f[obj][col] = float("nan")
        assert rule(case(f)) == []


@pytest.mark.parametrize("rule, seed", [
    (shunt_steps, lambda f: f["Shunt"].__setitem__("SSNMVR", 20.0)),
    (shunt_band_inverted, lambda f: f["Shunt"].__setitem__("SSVHigh", 0.5)),
    (gen_below_min, lambda f: f["Gen"].__setitem__("GenMWMin", 1e4)),
    (negative_x, lambda f: f["Branch"].__setitem__("LineX", -0.01)),
])
def test_the_seeded_defects_fire_when_the_field_is_read(frames, rule, seed):
    f = _lintable(frames)
    seed(f)
    assert rule(case(f)) != []


def test_many_blocks_with_three_decimal_steps_do_not_drift(frames):
    f = _lintable(frames)
    sh = f["Shunt"]
    for n, q in zip(BLOCK_STEPS[:6], BLOCK_MVAR[:6]):
        sh[[n, q]] = [1.0, 14.375]
    sh["SSNMVR"] = 86.25                                           # all six blocks in
    assert shunt_steps(case(f)) == []


def test_a_placeholder_step_count_is_skipped_not_enumerated(frames):
    f = _lintable(frames)
    f["Shunt"][["SSBlockNumSteps", "SSBlockMVarPerStep", "SSNMVR"]] = [1e8, 0.01, 0.005]
    t = time.perf_counter()
    [x] = shunt_steps(case(f))
    assert time.perf_counter() - t < 1.0
    assert x.severity == FYI and "not checked" in x.what and x.where[0]["ShuntID"] == "1"


def test_an_unread_field_stays_unread_through_a_snapshot(frames, tmp_path):
    f = _lintable(frames)
    f["Bus"] = f["Bus"].drop(columns=["BusName"])
    case(f).to_json(tmp_path / "s.json")
    assert bus_names(CaseData.from_json(tmp_path / "s.json")) == []


def test_shunt_beyond_its_blocks(frames):
    f = _lintable(frames)
    f["Shunt"][["SSBlockNumSteps", "SSBlockMVarPerStep", "SSNMVR"]] = [4.0, 8.2, 41.0]
    [x] = shunt_steps(case(f))
    assert "beyond" in x.what and x.where[0]["block_max_mvar"] == 32.8 and x.where[0]["ShuntID"] == "1"


def test_shunt_between_steps(frames):
    f = _lintable(frames)
    f["Shunt"]["SSNMVR"] = 20.0                                    # steps of 15: 0, 15, 30, 45, 60
    [x] = shunt_steps(case(f))
    assert "between steps" in x.what


def test_shunt_on_a_mix_of_blocks_is_fine(frames):
    f = _lintable(frames)
    sh = f["Shunt"]
    sh[["SSBlockNumSteps:1", "SSBlockMVarPerStep:1"]] = [2.0, -10.0]   # a reactor block as well
    sh["SSNMVR"] = 5.0                                                 # 15 - 10
    assert shunt_steps(case(f)) == []


def test_continuous_shunt_is_not_stepped(frames):
    f = _lintable(frames)
    f["Shunt"][["SSCMode", "SSNMVR"]] = ["Continuous", 20.0]
    assert shunt_steps(case(f)) == []


def test_inverted_shunt_band(frames):
    f = _lintable(frames)
    f["Shunt"][["SSVLow", "SSVHigh"]] = [1.05, 0.95]
    [x] = shunt_band_inverted(case(f))
    assert x.severity == WORTH and x.where[0]["SSVHigh"] == 0.95


def test_online_unit_below_minimum(frames):
    f = _lintable(frames)
    f["Gen"].loc[1, "GenMWMin"] = 95.0                             # wind unit at 90 MW
    [x] = gen_below_min(case(f))
    assert x.where == [{"BusNum": 2, "GenID": "W1", "GenMW": 90.0, "GenMWMin": 95.0,
                        "GenFuelType": "WND (Wind)", "slack": False}]


def test_offline_unit_below_minimum_is_fine(frames):
    f = _lintable(frames)
    f["Gen"].loc[1, ["GenMWMin", "GenStatus"]] = [95.0, "Open"]
    assert gen_below_min(case(f)) == []


def test_missing_placeholder_and_inverted_limits(frames):
    f = _lintable(frames)
    g = f["Gen"]
    g.loc[0, "GenMVRMax"] = float("nan")
    g.loc[1, "GenMVRMax"] = 9999.0
    g.loc[2, ["GenMWMax", "GenMWMin"]] = [10.0, 20.0]
    [x] = gen_limits(case(f))
    assert [w["problems"] for w in x.where] == [["GenMVRMax missing"], ["GenMVRMax placeholder"],
                                                ["GenMWMax below GenMWMin"]]


def test_negative_reactance_but_not_on_a_star_leg(frames):
    f = _lintable(frames)
    f["Branch"].loc[0, "LineX"] = -0.01                            # 1-2
    f["Branch"].loc[4, "LineX"] = -0.01                            # 3-5, then make 5 a star bus
    f["Bus"].loc[f["Bus"].BusNum == 5, "BusIsStarBus"] = "YES"
    [x] = negative_x(case(f))
    assert [(w["BusNum"], w["BusNum:1"]) for w in x.where] == [(1, 2)]


def test_branch_with_no_rating_but_not_a_jumper(frames):
    f = _lintable(frames)
    br = f["Branch"]
    br.loc[0, "LineAMVA"] = 0.0
    br.loc[1, ["LineAMVA", "LineR", "LineX"]] = [0.0, 0.0, 1e-4]    # a jumper: no rating expected
    [x] = missing_ratings(case(f))
    assert "no rating A" in x.what and [(w["BusNum"], w["BusNum:1"]) for w in x.where] == [(1, 2)]


def test_used_emergency_rating_stays_broken(frames):
    f = _lintable(frames)
    f["Branch"].loc[2, "LineAMVA:1"] = 0.0                         # limit set uses B for contingencies
    [x] = missing_ratings(case(f))
    assert x.severity == WORTH and x.triage == "Broken"
    assert x.details["contingency_sets_hit"] == ["B"] and x.details["without_b"] == 1


def test_unused_emergency_rating_is_your_call(frames):
    f = _lintable(frames)
    f["Branch"]["LineAMVA:2"] = 0.0                                # C is empty, and the N-1 uses B
    [x] = missing_ratings(case(f))
    assert x.severity == FYI and x.triage == "Your call"
    assert x.details["contingency_sets_hit"] == [] and x.details["without_c"] == 6


def test_blank_bus_name(frames):
    f = _lintable(frames)
    f["Bus"].loc[2, "BusName"] = ""
    [x] = bus_names(case(f))
    assert x.where == [{"BusNum": 3}]


def test_an_island_with_generation_and_no_slack(frames):
    f = _lintable(frames)
    f["Branch"].loc[4, "LineStatus"] = "Open"                      # 3-5: buses 5-6 and the solar unit split off
    found = islands(case(f))
    assert [x.what.split(" ")[0] for x in found] == ["1", "1"]
    assert found[0].where[0]["buses"] == 2 and found[0].where[0]["gen_mw"] == 40.0
    assert found[1].where[0]["slack_buses"] == []


def test_two_slacks_in_one_island(frames):
    f = _lintable(frames)
    f["Bus"].loc[1, "BusCat"] = "Slack"
    [x] = islands(case(f))
    assert x.where[0]["slack_buses"] == [1, 2]


def test_nominal_kv_that_is_not_round(frames):
    f = _lintable(frames)
    f["Bus"].loc[0, "BusNomVolt"] = 345.1234
    f["Bus"].loc[1, "BusNomVolt"] = 4.16                           # a real kV with two decimals
    [x] = nominal_kv(case(f))
    assert x.where == [{"BusNum": 1, "BusNomVolt": 345.1234}]


def test_lint_never_stops_a_study_and_replays_on_hawaii(hawaii):
    r = report.build(CaseData.from_json(hawaii), ["lint"])
    assert all(v["verdict"] == "READY" or not any(s.startswith("lint.") for s in v["stopped_by"])
               for v in r["verdicts"].values())
    assert {x for x in r["rules_run"] if x.startswith("lint.")} == {
        "lint.gen_limits",
        "lint.negative_x", "lint.missing_ratings", "lint.bus_names", "lint.islands", "lint.nominal_kv"}
    assert all(not f["stops"] for f in r["findings"] if f["rule"].startswith("lint."))


def test_unread_lint_fields_are_reported_as_not_run(hawaii):
    r = report.build(CaseData.from_json(hawaii), ["lint"])
    skipped = {s["rule"]: s["reason"] for s in r["rules_skipped"]}
    rules = {"lint.shunt_steps", "lint.shunt_band_inverted", "lint.gen_below_min"}
    assert rules <= set(skipped)
    assert not rules & set(r["rules_run"])
    assert "GenMWMin" in skipped["lint.gen_below_min"]
    assert "SSVHigh" in skipped["lint.shunt_band_inverted"]
    assert skipped["lint.shunt_steps"] == "field(s) SSBlockNumSteps, SSBlockMVarPerStep not read"


def test_a_half_run_rule_is_in_both_lists(hawaii):
    r = report.build(CaseData.from_json(hawaii), ["lint"])
    skipped = {s["rule"]: s["reason"] for s in r["rules_skipped"]}
    assert "lint.gen_limits" in r["rules_run"] and "lint.gen_limits" in skipped
    assert skipped["lint.gen_limits"] == "field(s) GenMWMin not read; those limits were not checked"
    rules = {"lint.negative_x", "lint.missing_ratings", "lint.bus_names", "lint.islands", "lint.nominal_kv"}
    assert rules <= set(r["rules_run"])
    assert not rules & set(skipped)


@pytest.mark.parametrize("rule, obj, col, half", [
    ("lint.shunt_steps", "Shunt", "SSCMode", "whole"),
    ("lint.shunt_steps", "Shunt", "SSBlockMVarPerStep", "whole"),
    ("lint.shunt_band_inverted", "Shunt", "SSVLow", "whole"),
    ("lint.gen_below_min", "Gen", "GenMWMin", "whole"),
    ("lint.gen_limits", "Gen", "GenMWMin", "partial"),
    ("lint.gen_limits", "Gen", "GenMVRMax", "partial"),
    ("lint.negative_x", "Bus", "BusIsStarBus", "whole"),
    ("lint.missing_ratings", "Branch", "LineAMVA", "whole"),
    ("lint.missing_ratings", "Branch", "LineAMVA:1", "partial"),
    ("lint.bus_names", "Bus", "BusName", "whole"),
    ("lint.islands", "Bus", "BusStatus", "whole"),
    ("lint.islands", "Bus", "BusCat", "partial"),
    ("lint.nominal_kv", "Bus", "BusNomVolt", "whole"),
    ("lint.shunt_steps", "Shunt", "SSNMVR", "whole"),
    ("lint.missing_ratings", "LimitSet", "LSLineRateSet:1", "partial"),
    ("lint.missing_ratings", "LimitSet", "LSDisabled", "partial"),
    ("lint.islands", "Load", "LoadMW", "partial"),
    ("lint.islands", "Gen", "GenStatus", "partial"),
    ("lint.gen_limits", "Gen", "GenID", "whole"),
    ("lint.negative_x", "Branch", "LineCircuit", "whole"),
])
def test_dropping_a_field_lands_the_rule_in_not_checked(frames, rule, obj, col, half):
    f = _lintable(frames)
    f[obj] = f[obj].drop(columns=[col])
    for _ in range(2 if col in NUMERIC else 1):
        r = report.build(case(f), ["lint"])
        skipped = {s["rule"]: s["reason"] for s in r["rules_skipped"]}
        assert rule in skipped and col in skipped[rule]
        assert (rule in r["rules_run"]) == (half == "partial")
        f[obj][col] = float("nan")


def test_all_unread_generator_limits_are_not_run(frames):
    f = _lintable(frames)
    f["Gen"] = f["Gen"].drop(columns=GEN_LIMITS)
    r = report.build(case(f), ["lint"])
    skipped = {s["rule"]: s["reason"] for s in r["rules_skipped"]}
    assert skipped["lint.gen_limits"] == f"field(s) {', '.join(GEN_LIMITS)} not read"
    assert "lint.gen_limits" not in r["rules_run"]


def test_a_fully_read_toy_skips_no_lint_rule(frames):
    r = report.build(case(_lintable(frames)), ["lint"])
    assert not any(s["rule"].startswith("lint.") for s in r["rules_skipped"])
    assert {r for r in r["rules_run"] if r.startswith("lint.")} == {f"lint.{fn.__name__}" for fn in ALL}


def test_not_checked_reaches_the_markdown(hawaii):
    md = report.render_md(report.build(CaseData.from_json(hawaii), ["lint"]))
    assert "## Not checked" in md
    assert "- lint.gen_below_min:" in md and "- lint.gen_limits:" in md
