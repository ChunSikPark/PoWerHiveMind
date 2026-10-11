"""The agent brief and the engine name the same rules, pages and commands."""
import re
from pathlib import Path

from checks import RULES
from thresholds import DC_SKELETON_PARTIAL_SHARE, DC_SKELETON_SHARE

KIT = Path(__file__).resolve().parents[3]
AGENT = (KIT / "agents" / "case-auditor.md").read_text(encoding="utf-8")
SKILL = (KIT / "skills" / "case-audit" / "SKILL.md").read_text(encoding="utf-8")


def test_the_draft_has_moved():
    assert not (KIT / "docs" / "agents" / "case-auditor.md").exists()
    assert "${CLAUDE_PLUGIN_ROOT}/agents/case-auditor.md" in SKILL


def test_agent_runs_the_skill_by_the_plugin_root():
    assert "${CLAUDE_PLUGIN_ROOT}/skills/case-audit/SKILL.md" in AGENT


def test_agent_and_engine_name_the_same_rules():
    # opf.conditions is a bundle: the engine reports it as opf.1 to opf.3, plus opf.preview.
    engine = ({r[0] for r in RULES} - {"opf.conditions"}) | {"opf.preview"}
    named = set(re.findall(r"`((?:base|mon|ts|lint)\.[a-z_0-9]+|opf\.preview)`", AGENT))
    assert named == engine
    assert {"opf.1", "opf.3"} <= set(re.findall(r"\bopf\.\d\b", AGENT))


def test_every_page_the_agent_cites_exists():
    cited = set(re.findall(r"`((?:concepts|methods|demos|references)/[\w-]+\.md)`", AGENT))
    assert cited and [c for c in cited if not (KIT / c).is_file()] == []
    assert "written in Plan 2" not in AGENT


def test_the_brief_states_the_engines_numbers_and_verdict_lines():
    [row] = [l for l in AGENT.splitlines() if l.startswith("| `base.dc_skeleton`")]
    assert f"{DC_SKELETON_SHARE:.0%}".replace("%", " %") in row and f"{DC_SKELETON_PARTIAL_SHARE:.0%}".replace("%", " %") in row
    assert "zero-length" not in row
    assert "- scopf: READY | NOT READY" in AGENT and "the engine always writes it" in AGENT
    assert "If findings.json says source is snapshot, the case was not opened" in AGENT


def test_the_brief_shows_the_engines_opf_table_header():
    src = (KIT / "skills" / "case-audit" / "engine" / "report.py").read_text(encoding="utf-8")
    header = re.search(r'"(\| area \| OPF may redispatch it[^"]*)"', src).group(1)
    assert "| with cost data |" in header and header in AGENT


def test_the_worked_example_shows_what_the_engine_writes_with_no_opf_area_and_no_cost_data():
    import report
    from auditcase import case, toy
    f = toy()
    f["Area"]["BGAGC"] = "Off AGC"
    f["Gen"]["GenCostModel"] = "None"
    r = report.build(case(f), ["opf"])
    example = AGENT.split("## Examples")[1].split("**Bad:**")[0]
    assert f"- opf: NOT READY — {r['verdicts']['opf']['reason']}" in example
    rows = {m[0]: m for m in re.findall(r"\| (Stops the study|Worth a look) \| (Your call) \| (opf\.\w+) \|", example)}
    engine = {x["rule"]: x for x in r["findings"] if x["rule"].startswith("opf")}
    assert {m[2] for m in rows.values()} == set(engine)
    for sev, triage, rule in rows.values():
        assert (sev, triage) == (engine[rule]["severity"], engine[rule]["triage"])


def test_the_footprint_row_claims_only_what_the_engine_reports():
    [row] = [l for l in AGENT.splitlines() if l.startswith("| `mon.footprint`")]
    assert "element overrides (" not in row and "already reflect any element overrides" in row


def test_contracts_require_keyed_lint_rows_and_not_checked_lines():
    agent = " ".join(AGENT.split())
    skill = " ".join(SKILL.split())
    method = " ".join((KIT / "methods" / "case-data-lint.md").read_text(encoding="utf-8").split())
    assert ("Every finding that stops the study, and every lint finding when `lint` ran, names its rule id, "
            "the object's key fields (e.g. `BusNum`+`GenID`), a one-line why, and the kit page that explains it.") in agent
    assert "appears in both `rules_run` and `rules_skipped`" in agent
    assert "not checked: <rule>, <reason>" in agent
    [row] = [l for l in AGENT.splitlines() if l.startswith("| `lint.missing_ratings`")]
    assert "Your call when nothing uses it" in row
    assert "Never infer a shared cause" in agent and "usually share one cause" not in agent
    assert "one Findings row per lint finding with its count from findings.json and the keys of up to 3 objects" in agent
    assert "what's wrong with this case" in AGENT.split("---")[1]
    assert "a rule that ran in part is in both lists" in skill
    assert "every lint finding is a Findings row" in skill
    assert "triaged Your call" in method
    assert "listed as run and as not checked for that half" in method
