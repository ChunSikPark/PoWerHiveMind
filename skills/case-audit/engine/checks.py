"""Which rules run for which profiles, and the verdict each requested study gets."""
from __future__ import annotations

from casedata import CaseData
from findings import STOPS, Finding
import rules_base as B
import rules_lint as L
import rules_mon as M
import rules_opf as O
import rules_reg as R
import rules_stub as S
import rules_ts as T

# (rule id, profile, needs a converged AC solve, function(cd, pww) -> list[Finding])
RULES = [
    ("base.ac_converges", "base", False, lambda cd, pww: B.ac_converges(cd)),
    ("base.dc_skeleton", "base", False, lambda cd, pww: B.dc_skeleton(cd)),
    ("base.gen_over_nameplate", "base", True, lambda cd, pww: B.gen_over_nameplate(cd)),
    ("base.regulates_nothing", "base", False, lambda cd, pww: R.regulates_nothing(cd)),
    ("base.ltc_middle_target", "base", False, lambda cd, pww: R.ltc_middle_target(cd)),
    ("base.ltc_regulates_lv_side", "base", True, lambda cd, pww: R.ltc_regulates_lv_side(cd)),
    ("base.floating_stub", "base", True, lambda cd, pww: S.floating_stub(cd)),
    ("base.stale_ctg_results", "base", False, lambda cd, pww: B.stale_ctg_results(cd)),
    ("mon.nothing_monitored", "base", False, lambda cd, pww: M.nothing_monitored(cd)),
    ("mon.footprint", "base", False, lambda cd, pww: M.monitored_footprint(cd)),
    ("mon.rate_set_empty", "base", False, lambda cd, pww: M.rate_set_empty(cd)),
    ("mon.rate_sets_populated", "base", False, lambda cd, pww: M.rate_sets_populated(cd)),
    ("mon.bus_limit_overrides", "base", False, lambda cd, pww: M.bus_limit_overrides(cd)),
    ("mon.no_contingencies", "opf", False, lambda cd, pww: M.no_contingencies(cd)),
    ("ts.pfw_missing", "timestep", False, lambda cd, pww: T.pfw_missing(cd)),
    ("ts.latlon_missing", "timestep", False, lambda cd, pww: T.latlon_missing(cd)),
    ("ts.pww_footprint", "timestep", False, lambda cd, pww: T.pww_footprint(cd, pww)),
    # also emits opf.preview (Worth a look, never stops anything) when no area is on OPF
    ("opf.conditions", "opf", False, lambda cd, pww: O.opf_conditions(cd)),
    # lint: data defects; never stops a study (methods/case-data-lint.md)
    ("lint.shunt_steps", "lint", False, lambda cd, pww: L.shunt_steps(cd)),
    ("lint.shunt_band_inverted", "lint", False, lambda cd, pww: L.shunt_band_inverted(cd)),
    ("lint.gen_below_min", "lint", False, lambda cd, pww: L.gen_below_min(cd)),
    ("lint.gen_limits", "lint", False, lambda cd, pww: L.gen_limits(cd)),
    ("lint.negative_x", "lint", False, lambda cd, pww: L.negative_x(cd)),
    ("lint.missing_ratings", "lint", False, lambda cd, pww: L.missing_ratings(cd)),
    ("lint.bus_names", "lint", False, lambda cd, pww: L.bus_names(cd)),
    ("lint.islands", "lint", False, lambda cd, pww: L.islands(cd)),
    ("lint.nominal_kv", "lint", False, lambda cd, pww: L.nominal_kv(cd)),
]
VALID_PROFILES = ("base", "timestep", "opf", "lint")


def run_rules(cd: CaseData, profiles: list[str], pww: str | None = None):
    """-> (findings, rules run, rules skipped with the reason). base always runs."""
    want = {"base", *profiles}
    findings, ran, skipped = [], [], []
    for rule, profile, needs_solve, fn in RULES:
        if profile not in want:
            continue
        if needs_solve and not cd.solve.converged:
            skipped.append({"rule": rule, "reason": "needs a solved AC power flow, and it did not solve"})
            continue
        if profile == "lint":
            missing = L.unread_fields(cd, rule)
            if missing:
                skipped.append({"rule": rule, "reason": f"field(s) {', '.join(missing)} not read"})
                continue
        findings += fn(cd, pww)
        if profile == "lint":
            skipped += L.partial_skips(cd, rule)
        ran.append(rule)
    return findings, ran, skipped


def verdicts(findings: list[Finding], profiles: list[str], ts_coverage: dict | None = None,
             contingencies: int | None = None) -> dict:
    """READY or NOT READY per study. n1 is the monitoring verdict reported with base; scopf comes
    with opf and needs everything opf and n1 need, plus a contingency list. Only a finding whose
    `stops` names the study counts, so a Worth-a-look finding such as opf.preview never moves one."""
    order = ["base", "n1"] + [p for p in ("timestep", "opf") if p in profiles] + (["scopf"] if "opf" in profiles else [])
    needs = {"scopf": {"opf", "n1", "scopf"}}
    out = {}
    for p in order:
        stop = [f for f in findings if f.severity == STOPS and needs.get(p, {p}) & set(f.stops)]
        if stop:
            out[p] = {"verdict": "NOT READY", "reason": stop[0].what, "stopped_by": [f.rule for f in stop]}
        else:
            reason = ""
            if p == "timestep" and ts_coverage:
                c = ts_coverage
                reason = f"{c['with_pfw']} of {c['renewables']} renewables will follow the weather"
            if p == "n1":
                reason = "monitoring only; the runner counts outage coverage"
            if p == "scopf":
                reason = f"{contingencies} contingencies in the case; the runner counts outage coverage"
            out[p] = {"verdict": "READY", "reason": reason, "stopped_by": []}
    return out
