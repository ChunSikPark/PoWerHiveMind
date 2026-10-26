---
description: Time step and OPF both run; the OPF area comes from a super area (live audit).
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
append_system_prompt: "You are the main session of the PoWerHiveMind kit. When the user asks about a PowerWorld case's readiness, health or contents, hand the request to the case-auditor agent with the Agent tool: pass the user's words and the audit output below verbatim, add nothing. Then relay the agent's final message to the user verbatim, once, adding nothing before or after it."
---

Can I run a time step and an OPF on Texas2k_series25_case1_summerpeak_PFW.pwb?

PowerWorld isn't on this machine, but I already ran the case audit on it. Here is its findings.md:

````markdown
# Case audit

Case checked: `Texas2k_series25_case1_summerpeak_PFW.pwb`  
Audited: 2026-09-30T23:42:07  
Case file unchanged by the audit: yes

## Verdict
- base: READY
- n1: READY — monitoring only; the runner counts outage coverage
- timestep: READY — 400 of 400 renewables will follow the weather
- opf: READY
- scopf: READY — 2738 contingencies in the case; the runner counts outage coverage

## What's in the case
| | MW | Mvar |
|---|---|---|
| Load | 85,759 | 21,616 |
| Generation (online) | 90,185 | 11,898 |
| Losses | 4,426 | |
| Headroom on online units (dispatchable) | 17,771 | |
| Online Mvar range | | -10,031 to 29,628 |

| fuel (as the case labels it) | units online / total | installed MW | output MW | share of output | headroom MW |
|---|---|---|---|---|---|
| BIT (Bituminous Coal) | 18/21 | 13,538 | 4,145 | 5% | 7,543 |
| DFO (Distillate Fuel Oil) | 8/10 | 514 | 170 | 0% | 236 |
| MWH (Electricity use for Energy Storage) | 66/121 | 14,277 | 7,305 | 8% | 0 |
| NG (Natural Gas) | 305/507 | 58,088 | 19,751 | 22% | 9,413 |
| NUC (Nuclear) | 4/4 | 4,980 | 4,400 | 5% | 580 |
| OBL (Other Biomass Liquids) | 3/4 | 160 | 142 | 0% | 0 |
| OTH (Other) | 8/10 | 228 | 138 | 0% | 0 |
| SUN (Solar) | 128/178 | 32,313 | 21,120 | 23% | 0 (weather-limited) |
| WAT (Water) | 19/22 | 553 | 480 | 1% | 0 |
| WND (Wind) | 177/222 | 41,832 | 32,534 | 36% | 0 (weather-limited) |

| shunts | in service | Mvar now | capacitive capacity | inductive capacity |
|---|---|---|---|---|
| 202 | 202 | 29,166 | 41,120 | -425 |

Size: 2,751 buses, 5,344 branches (1,351 transformers), 8 areas, 1 zones; kV levels 13.2, 13.8, 18, 20, 22, 24, 115, 161, 230, 500.

N-1 will check: areas 1, 2, 3, 4, 5, 6, 7, 8 (of 8), all kV, 5,344 branches / 2,751 buses (the case's own setup).
Headroom on dispatchable units the OPF may move: 17,771 MW.

## Findings
| what's wrong | where (keys) | why it matters | stops the study? | Broken / Probably on purpose / Your call | rule | kit page |
|---|---|---|---|---|---|---|
| the case already holds 173 contingency violation rows from an earlier run | — | they describe whatever the case was when that run happened, not this audit - do not read them | FYI | Probably on purpose | base.stale_ctg_results | methods/reading-violationctg.md |
| an N-1 will check 8 of 8 areas, 5344 branches and 2751 buses | — | a clean N-1 result covers only this footprint, not the whole system | FYI | Probably on purpose | mon.footprint | field export (schema-only) |
| rate sets with values: A (5344 branches), B (2782 branches), C (2782 branches) | — | shows which rating letters a limit set could point at | FYI | Probably on purpose | mon.rate_sets_populated | methods/reading-violationctg.md |
| weather file not given, so I didn't check it covers these units | — | send the .pww if you want its coverage checked | FYI | Your call | ts.pww_footprint | concepts/pww-data.md |
| 5 of the 736 units the OPF could move carry no cost data | 5 object(s), listed below | the OPF runs on the priced units; these ones have no price to be dispatched on | Worth a look | Your call | opf.3 | concepts/opf-preconditions.md |
| 95 thermal unit(s) the OPF could move have a cost curve that reads 0 at today's output | 95 object(s), listed below | the OPF will treat their next MW as free; check the curve if that is not intended | Worth a look | Probably on purpose | opf.3 | concepts/opf-preconditions.md |

## Can the OPF run?
| area | OPF may redispatch it | units the OPF may move | with cost data | with a cost above 0 at today's output | cost model types |
|---|---|---|---|---|---|
| 1 | yes (super area Texas on OPF) | 116 | 115 | 28 | Cubic 116 |
| 2 | yes (super area Texas on OPF) | 86 | 85 | 13 | Cubic 86 |
| 3 | yes (super area Texas on OPF) | 76 | 75 | 8 | Cubic 76 |
| 4 | yes (super area Texas on OPF) | 122 | 120 | 42 | Cubic 122 |
| 5 | yes (super area Texas on OPF) | 62 | 62 | 30 | Cubic 62 |
| 6 | yes (super area Texas on OPF) | 88 | 88 | 63 | Cubic 88 |
| 7 | yes (super area Texas on OPF) | 146 | 146 | 126 | Cubic 146 |
| 8 | yes (super area Texas on OPF) | 40 | 40 | 25 | Cubic 40 |

## What you need to get
1. 5 of the 736 units the OPF could move carry no cost data → your own cost-data source; no script supplies cost curves, and a default one makes the dispatch meaningless → then send the returned case to be checked again

## Every object, per finding

### opf.3 — Worth a look — Your call

```json
{"BusNum": 2019, "GenID": "1", "AreaNum": 2, "GenCostModel": "Cubic", "GenCostCurvePoints": 0.0, "GenMCost": 0.0}
{"BusNum": 4153, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 0.0, "GenMCost": 0.0}
{"BusNum": 12821, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 0.0, "GenMCost": 0.0}
{"BusNum": 13143, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 0.0, "GenMCost": 0.0}
{"BusNum": 13391, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 0.0, "GenMCost": 0.0}
```

### opf.3 — Worth a look — Probably on purpose

```json
{"BusNum": 1033, "GenID": "BA", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 1090, "GenID": "2", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 2063, "GenID": "1", "AreaNum": 2, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 2063, "GenID": "2", "AreaNum": 2, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 3014, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 3106, "GenID": "2", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 3120, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4007, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4045, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4046, "GenID": "2", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4047, "GenID": "3", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4065, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4067, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4068, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4069, "GenID": "3", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4090, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4100, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4100, "GenID": "2", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4102, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 4111, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 5290, "GenID": "1", "AreaNum": 5, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 5290, "GenID": "2", "AreaNum": 5, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6027, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6082, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6083, "GenID": "2", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6116, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6137, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6137, "GenID": "3", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6168, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6213, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 6214, "GenID": "2", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 7086, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 7312, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 8099, "GenID": "1", "AreaNum": 8, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 8141, "GenID": "1", "AreaNum": 8, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12589, "GenID": "1", "AreaNum": 5, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12594, "GenID": "BA", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12641, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12658, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12662, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12666, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12680, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12711, "GenID": "1", "AreaNum": 5, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12720, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12759, "GenID": "1", "AreaNum": 8, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12782, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12786, "GenID": "1", "AreaNum": 2, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12881, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12944, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12969, "GenID": "1", "AreaNum": 8, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 12993, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13028, "GenID": "BA", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13086, "GenID": "1", "AreaNum": 2, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13088, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13090, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13094, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13128, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13182, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13219, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13221, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13223, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13225, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13227, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13229, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13231, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13233, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13298, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13303, "GenID": "BA", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13305, "GenID": "BA", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13307, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13323, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13324, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13327, "GenID": "NF", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13332, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13336, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13338, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13340, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13344, "GenID": "1", "AreaNum": 6, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13345, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13386, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13389, "GenID": "BA", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13391, "GenID": "2", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13393, "GenID": "1", "AreaNum": 8, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13393, "GenID": "2", "AreaNum": 8, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13397, "GenID": "2", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13398, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13403, "GenID": "1", "AreaNum": 3, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13407, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13407, "GenID": "2", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13408, "GenID": "1", "AreaNum": 7, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13412, "GenID": "1", "AreaNum": 2, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13415, "GenID": "1", "AreaNum": 1, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13425, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13427, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
{"BusNum": 13428, "GenID": "1", "AreaNum": 4, "GenCostModel": "Cubic", "GenCostCurvePoints": 5.0, "GenMCost": 0.0}
```
````
