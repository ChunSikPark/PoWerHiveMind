---
description: Seeded - the slack unit 3 MW over its rating and a placeholder shunt; the case runs.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
append_system_prompt: "You are the main session of the PoWerHiveMind kit. When the user asks about a PowerWorld case's readiness, health or contents, hand the request to the case-auditor agent with the Agent tool: pass the user's words and the audit output below verbatim, add nothing. Then relay the agent's final message to the user verbatim, once, adding nothing before or after it."
---

Scan Hawaii40_base.pwb for me - anything wrong with it?

PowerWorld isn't on this machine, but I already ran the case audit on it. Here is its findings.md:

````markdown
Replayed from a stored snapshot; no case was opened.

# Case audit

Case checked: `Hawaii40_base.pwb`  
Audited: 2026-09-30T23:23:44  
Case file unchanged by the audit: not checked (no hash of the file before and after)

## Verdict
- base: READY
- n1: READY — monitoring only; the runner counts outage coverage

## What's in the case
| | MW | Mvar |
|---|---|---|
| Load | 1,136 | 0 |
| Generation (online) | 1,166 | 9 |
| Losses | 30 | |
| Headroom on online units (dispatchable) | 168 | |
| Online Mvar range | | -242 to 403 |

Generation includes 3.0 MW above unit ratings.

| fuel (as the case labels it) | units online / total | installed MW | output MW | share of output | headroom MW |
|---|---|---|---|---|---|
| BIT (Bituminous Coal) | 0/1 | 180 | 0 | 0% | 0 |
| DFO (Distillate Fuel Oil) | 18/23 | 1,405 | 749 | 64% | 156 |
| OBL (Other Biomass Liquids) | 12/12 | 146 | 135 | 12% | 12 |
| SUN (Solar) | 6/6 | 167 | 156 | 13% | 0 (weather-limited) |
| WND (Wind) | 3/3 | 127 | 127 | 11% | 0 (weather-limited) |

| shunts | in service | Mvar now | capacitive capacity | inductive capacity |
|---|---|---|---|---|
| 2 | 2 | 31 | 32 | 0 |

Size: 37 buses, 89 branches (12 transformers), 1 areas, 1 zones; kV levels 69, 138.

N-1 will check: areas 1 (of 1), all kV, 89 branches / 37 buses (the case's own setup).

## Findings
| what's wrong | where (keys) | why it matters | stops the study? | Broken / Probably on purpose / Your call | rule | kit page |
|---|---|---|---|---|---|---|
| 1 online unit(s) above their rating after the solve, 3.0 MW over in all | 1 object(s), listed below | the case runs; the overshoot is small enough not to move a finding | Worth a look | Broken | base.gen_over_nameplate | methods/applying-a-dispatch-to-a-case.md |
| 1 switched shunt(s) with a 0 Mvar range and no regulated bus | 1 object(s), listed below | a 0 Mvar shunt with no target is usually a placeholder, not a defect | Worth a look | Probably on purpose | base.regulates_nothing | methods/ltc-regulation-checks.md |
| the case already holds 14 contingency violation rows from an earlier run | — | they describe whatever the case was when that run happened, not this audit - do not read them | FYI | Probably on purpose | base.stale_ctg_results | methods/reading-violationctg.md |
| an N-1 will check 1 of 1 areas, 89 branches and 37 buses | — | a clean N-1 result covers only this footprint, not the whole system | FYI | Probably on purpose | mon.footprint | field export (schema-only) |
| rate sets with values: A (89 branches), B (89 branches), C (89 branches) | — | shows which rating letters a limit set could point at | FYI | Probably on purpose | mon.rate_sets_populated | methods/reading-violationctg.md |

## Every object, per finding

### base.gen_over_nameplate — Worth a look — Broken

```json
{"BusNum": 23, "GenID": "1", "GenMW": 80.80000567, "GenMWMax": 77.80000567, "over_mw": 3.0, "slack": true}
```

### base.regulates_nothing — Worth a look — Probably on purpose

```json
{"device": "switched shunt", "BusNum": 16, "ShuntID": "P1", "SSRegNum": 0, "reason": "zero"}
```
````
