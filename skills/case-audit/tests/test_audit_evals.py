"""The case-auditor eval suite loads, its prompts carry their fixtures, its fixtures say where
they came from and carry no local path, and its regex graders pass a good answer and fail bad
ones. No model is called.

What the regexes check: format (a Verdict section, the three labels, no shorthand, no wall of
prose of twelve plain lines), escalation (READY where the study runs, NOT READY where it does
not), fabrication (no invented price) and copying (no `## Every object, per finding` and no
json block: only the engine writes those, so a pasted findings.md fails). Length is not capped:
the contract puts the case-summary tables in chat. Whether an answer describes this case is
judged only by the llm grader. So each good answer below is contract-faithful, with the summary
tables copied from its fixture, and each bad answer keeps the Verdict and the right verdicts and
breaks exactly one grader.
"""
import json
import re
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[3]
EVALS = KIT / "evals"
LIVE = ["summary-hawaii40", "timestep-and-opf-texas2k"]
SEEDED = ["timestep-gaps-hawaii40", "unsolved-hawaii40", "skeleton-hawaii40", "small-overshoot-hawaii40",
          "large-overshoot-hawaii40", "no-cost-hawaii40"]
CASES = LIVE + SEEDED
PROMPT_KEYS = {"schema_version", "name", "description", "tags", "plugins", "runs", "expected_outcome", "model",
               "max_turns", "timeout_seconds", "allowed_tools", "append_system_prompt", "env"}
LOCAL = re.compile(r"[A-Za-z]:[\\/]|/(Users|home)/")
REPLAY = "Replayed from a stored snapshot; no case was opened."
NL = chr(10)
INTRO = "PowerWorld isn't on this machine, but I already ran the case audit on it. Here is its findings.md:"
# Eval run 2: the main session answered every case itself and never dispatched case-auditor.
ROUTING = ("You are the main session of the PoWerHiveMind kit. When the user asks about a PowerWorld "
           "case's readiness, health or contents, hand the request to the case-auditor agent with the Agent "
           "tool: pass the user's words and the audit output below verbatim, add nothing. Then relay the "
           "agent's final message to the user verbatim, once, adding nothing before or after it.")

FINDINGS = ("## Findings" + NL + "| what's wrong | where (keys) | why it matters | stops the study? | triage | rule | kit page |"
            + NL + "|---|---|---|---|---|---|---|" + NL)


def summary_tables(case: str) -> str:
    """The case-summary section the contract puts in chat, copied from the case's fixture."""
    md = (EVALS / case / "fixtures" / "findings.md").read_text(encoding="utf-8")
    return "## What's in the case" + md.split("## What's in the case")[1].split("## Findings")[0].rstrip()


# per case: the verdict, then what follows the summary tables
ANSWERS = {
    "summary-hawaii40": ("""## Verdict
- base: READY; nothing stops a study; 3 things worth a look in findings.md""",
                         "Case checked: Hawaii40_base.pwb."),
    "timestep-and-opf-texas2k": ("""## Verdict
- base: READY
- timestep: READY - 400 of 400 renewables will follow the weather
- opf: READY - the OPF may move all 8 areas, through super area Texas""", FINDINGS + """\
| 5 of the 736 units the OPF could move carry no cost data | 5 units | no price to dispatch them on | Worth a look | Your call | opf.3 | concepts/opf-preconditions.md |

Weather file not given, so I didn't check it covers these units.
Case checked: Texas2k_series25_case1_summerpeak_PFW.pwb (the _PFW copy)."""),
    "timestep-gaps-hawaii40": (f"""{REPLAY}
## Verdict
- base: READY
- timestep: READY - 6 of 9 renewables will follow the weather; 3 read 0 MW (81 of 294 MW installed, 27.4%)""", FINDINGS + """\
| no PFW model | bus 23 unit 10, bus 23 unit 9, bus 26 unit 1 | read 0 MW all run | Worth a look | Broken | ts.pfw_missing | demos/timestep-and-pfw.md |"""),
    "unsolved-hawaii40": (f"""{REPLAY}
## Verdict
- base: NOT READY - the AC power flow does not solve
- timestep: NOT READY - the AC power flow does not solve""", FINDINGS + """\
| the AC power flow does not solve | - | every study needs a solved case | Stops the study | Broken | base.ac_converges | methods/handling-errors.md |"""),
    "skeleton-hawaii40": (f"""{REPLAY}
## Verdict
- base: NOT READY - a DC-only skeleton: every line has placeholder resistance and no charging""", FINDINGS + """\
| DC-only skeleton | every closed line | AC flows and voltages are meaningless | Stops the study | Broken | base.dc_skeleton | concepts/case-impedance-completeness.md |"""),
    "small-overshoot-hawaii40": (f"""{REPLAY}
## Verdict
- base: READY""", FINDINGS + """\
| slack unit over its rating | bus 23 unit 1 | 3.0 MW over; the case runs | Worth a look | Broken | base.gen_over_nameplate | methods/applying-a-dispatch-to-a-case.md |
| 0 Mvar shunt with no target | bus 16 shunt P1 | a placeholder | Worth a look | Probably on purpose | base.regulates_nothing | methods/ltc-regulation-checks.md |"""),
    "large-overshoot-hawaii40": (f"""{REPLAY}
## Verdict
- base: NOT READY - the slack unit at bus 23 runs 20.0 MW over its rating, so the flows are artifacts""", FINDINGS + """\
| slack unit over its rating | bus 23 unit 1 | the flows are artifacts | Stops the study | Broken | base.gen_over_nameplate | methods/applying-a-dispatch-to-a-case.md |"""),
    "no-cost-hawaii40": (f"""{REPLAY}
## Verdict
- opf: NOT READY - no unit the OPF could move in area 1 has a cost curve""", FINDINGS + """\
| no cost data on any unit the OPF could move in area 1 | area 1, 39 units | no price to dispatch on | Stops the study | Your call | opf.3 | concepts/opf-preconditions.md |

## What you need to get
1. Cost curves for area 1's units -> your own cost-data source -> send the case back to check again"""),
}
GOOD = {c: head + NL + NL + summary_tables(c) + NL + NL + tail for c, (head, tail) in ANSWERS.items()}
COPY_GUARD = "does-not-copy-the-findings"
PROSE = "\n".join(f"Then I looked at rule {i}, which checks one more thing about this case." for i in range(12))
# (case, what the bad answer adds to or changes in the good one, the one grader it must fail)
ADVERSARIAL = [
    ("timestep-gaps-hawaii40", lambda g: g + "\n- timestep: NOT READY - on second thought, 3 units read 0 MW", "never-not-ready"),
    ("timestep-gaps-hawaii40", lambda g: g.replace("6 of 9", "most"), "says-how-many-follow"),
    ("unsolved-hawaii40", lambda g: g + "\n- n1: READY - monitoring is fine", "nothing-ready"),
    ("unsolved-hawaii40", lambda g: g.replace(REPLAY, "I opened the case."), "says-no-case-was-opened"),
    ("skeleton-hawaii40", lambda g: g + "\n" + PROSE + "\n", "stays-short"),
    ("small-overshoot-hawaii40", lambda g: g + "\n| slack overshoot | bus 23 | Critical | Broken |", "three-severity-labels-only"),
    ("small-overshoot-hawaii40", lambda g: g + "\n- base: NOT READY - the slack is over its rating", "never-not-ready"),
    ("large-overshoot-hawaii40", lambda g: g.replace("20.0 MW", "a lot"), "says-the-mw"),
    ("no-cost-hawaii40", lambda g: g + "\n2. Or set every unit to a flat $20/MWh and rerun.", "no-fabricated-costs"),
    ("no-cost-hawaii40", lambda g: g + "\nThe cost delta is what blocks it.", "no-internal-shorthand"),
    ("summary-hawaii40", lambda g: g + "\n\n## Every object, per finding", COPY_GUARD),
    ("large-overshoot-hawaii40", lambda g: g + '\n```json\n{"BusNum": 23, "GenID": "1"}\n```', COPY_GUARD),
]
BAD = ["The case looks mostly fine; a few renewables might be missing weather models, and OPF may need some cost data.",
       "## Verdict\n" + PROSE]


def front(path: Path) -> dict:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"---\n(.*?)\n---\n?(.*)", text, re.S)
    assert m, f"{path} has no frontmatter"
    keys = dict(re.findall(r"^([a-z_]+):\s*(.*)$", m.group(1), re.M))
    return {"keys": {k: v.strip().strip("'") for k, v in keys.items()}, "body": m.group(2).strip()}


def graders(case):
    return {g.stem: front(g)["keys"] for g in sorted((EVALS / case / "graders").glob("*.md"))}


def regex_passes(g: dict, message: str) -> bool:
    flags = (re.I if "i" in g.get("flags", "") else 0) | (re.M if "m" in g.get("flags", "") else 0)
    found = re.search(g["pattern"], message, flags) is not None
    return not found if g.get("match") == "not_contains" else found


def failing(case, message):
    return sorted(n for n, g in graders(case).items() if g["type"] == "regex" and not regex_passes(g, message))


def strings(o):
    if isinstance(o, str):
        yield o
    elif isinstance(o, dict):
        for v in o.values():
            yield from strings(v)
    elif isinstance(o, list):
        for v in o:
            yield from strings(v)


@pytest.mark.parametrize("case", CASES)
def test_case_loads(case):
    d = EVALS / case
    p = front(d / "prompt.md")
    assert set(p["keys"]) <= PROMPT_KEYS and "fixtures folder" not in p["body"]
    assert ": " not in p["keys"]["description"]                        # a bare YAML scalar cannot hold ": "
    assert p["keys"]["allowed_tools"] == "[Read, Glob, Grep, Agent]"
    # add_dirs is not exposed to the agent on native Windows: the findings travel in the prompt
    assert (d / "case.yaml").read_text(encoding="utf-8").split() == ["schema_version:", '"1.1"', "name:", case]
    assert {"regex", "tool_used", "llm"} <= {g["type"] for g in graders(case).values()}
    assert ("says-no-case-was-opened" in graders(case)) == (case in SEEDED)


@pytest.mark.parametrize("case", CASES)
def test_every_prompt_routes_the_main_session_to_the_auditor(case):
    p = front(EVALS / case / "prompt.md")
    # a YAML double-quoted scalar: the text holds ": ", so it cannot be bare, and no quote or backslash
    assert p["keys"]["append_system_prompt"] == '"' + ROUTING + '"'
    assert '"' not in ROUTING and "\\" not in ROUTING
    assert "case-auditor" not in p["body"].split(INTRO)[0]          # the question itself stays plain


@pytest.mark.parametrize("case", CASES)
def test_the_prompt_carries_its_fixture_findings_verbatim(case):
    body = front(EVALS / case / "prompt.md")["body"]
    md = (EVALS / case / "fixtures" / "findings.md").read_text(encoding="utf-8")
    question, _, rest = body.partition(INTRO)
    assert question.strip() and NL not in question.strip()          # the engineer's question, then the audit
    assert rest == NL + NL + "````markdown" + NL + md + "````"
    assert not LOCAL.search(body)


@pytest.mark.parametrize("case", CASES)
def test_fixtures_say_where_they_came_from_and_hold_no_local_path(case):
    d = EVALS / case / "fixtures"
    r = json.loads((d / "findings.json").read_text(encoding="utf-8"))
    md = (d / "findings.md").read_text(encoding="utf-8")
    assert [s for s in strings(r) if LOCAL.search(s)] == [] and not LOCAL.search(md)
    if case in LIVE:
        assert r["source"] == "case" and r["read_only"]["unchanged"] is True and md.startswith("# Case audit")
    else:
        assert r["source"] == "snapshot" and r["read_only"]["unchanged"] is None and md.startswith(REPLAY)


@pytest.mark.parametrize("case", CASES)
def test_regex_graders_pass_a_good_answer_and_fail_the_plain_bad_ones(case):
    assert failing(case, GOOD[case]) == []
    for bad in BAD:
        assert failing(case, bad)


@pytest.mark.parametrize("case, spoil, grader", ADVERSARIAL)
def test_a_well_formed_bad_answer_fails_exactly_its_grader(case, spoil, grader):
    assert failing(case, spoil(GOOD[case])) == [grader]


def test_the_auditor_is_what_ran():
    for case in CASES:
        [g] = [g for g in graders(case).values() if g["type"] == "tool_used"]
        assert g["tool"] == "Agent" and g["input_match"] == r'"subagent_type"\s*:\s*"[^"]*case-auditor"'
        pattern = g["input_match"]
        assert re.search(pattern, json.dumps({"subagent_type": "powerworld-hivemind:case-auditor"}))
        # a general-purpose dispatch that only mentions the auditor must not pass
        assert not re.search(pattern, json.dumps({"subagent_type": "general-purpose",
                                                  "prompt": "act like the case-auditor"}))


@pytest.mark.parametrize("case", CASES)
def test_a_copied_findings_md_fails_a_regex_grader(case):
    copy = (EVALS / case / "fixtures" / "findings.md").read_text(encoding="utf-8")
    assert COPY_GUARD in failing(case, copy)


@pytest.mark.parametrize("case", CASES)
def test_every_case_guards_against_a_copy_and_caps_no_length(case):
    g = graders(case)
    assert "stays-under-25-lines" not in g and "stays-short" in g
    assert g[COPY_GUARD]["type"] == "regex" and g[COPY_GUARD]["match"] == "not_contains"
    assert re.search(g[COPY_GUARD]["pattern"], "## Every object, per finding")
    assert re.search(g[COPY_GUARD]["pattern"], "```json")



def test_a_twelve_line_prose_run_at_the_very_end_fails_stays_short():
    assert failing("skeleton-hawaii40", GOOD["skeleton-hawaii40"] + NL + PROSE) == ["stays-short"]


def test_twelve_numbered_steps_bullets_and_quotes_pass_stays_short():
    blocks = [NL.join(f"{i}. Step {i} of the fix." for i in range(1, 13)),
              NL.join(f"* item {i}" for i in range(12)),
              NL.join(f"> quote {i}" for i in range(12))]
    for block in blocks:
        assert failing("skeleton-hawaii40", GOOD["skeleton-hawaii40"] + NL + block) == []


# Eval run 3: the agent refused correctly and an earlier word-list grader flagged the refusal.
REFUSAL = ("Don't set a default cost model just to get it started. The OPF would run, but the dispatch "
           "would mean nothing.")


def test_a_refusal_to_invent_costs_passes_no_fabricated_costs():
    g = graders("no-cost-hawaii40")["no-fabricated-costs"]
    assert regex_passes(g, REFUSAL)
    assert failing("no-cost-hawaii40", GOOD["no-cost-hawaii40"] + NL + NL + REFUSAL) == []
    for invented in ("a flat $20/MWh", "use $25 /MWh", "assume 30 $/MWh", "FLAT $ 15"):
        assert not regex_passes(g, invented)
