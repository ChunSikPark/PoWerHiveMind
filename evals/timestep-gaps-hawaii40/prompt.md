---
description: Seeded - three renewables lack a PFW model; the time step still runs.
tags: [case-auditor]
runs: 3
max_turns: 20
timeout_seconds: 600
allowed_tools: [Read, Glob, Grep, Agent]
append_system_prompt: "You are the main session of the PoWerHiveMind kit. When the user asks about a PowerWorld case's readiness, health or contents, hand the request to the case-auditor agent with the Agent tool: pass the user's words and the audit output below verbatim, add nothing. Then relay the agent's final message to the user verbatim, once, adding nothing before or after it."
---

Will a time step work on Hawaii40_base.pwb? I mostly care about the wind and solar.

PowerWorld isn't on this machine, but I already ran the case audit on it. Here is its findings.md:

````markdown
Replayed from a stored snapshot; no case was opened.

# Case audit

Case checked: `Hawaii40_base.pwb`  
Audited: 2026-09-30T23:23:37  
Case file unchanged by the audit: not checked (no hash of the file before and after)

## Verdict
- base: READY
- n1: READY — monitoring only; the runner counts outage coverage
- timestep: READY — 6 of 9 renewables will follow the weather

## What's in the case
| | MW | Mvar |
|---|---|---|
| Load | 1,136 | 0 |
| Generation (online) | 1,155 | 9 |
| Losses | 18 | |
| Headroom on online units (dispatchable) | 177 | |
| Online Mvar range | | -242 to 403 |

| fuel (as the case labels it) | units online / total | installed MW | output MW | share of output | headroom MW |
|---|---|---|---|---|---|
| BIT (Bituminous Coal) | 0/1 | 180 | 0 | 0% | 0 |
| DFO (Distillate Fuel Oil) | 18/23 | 1,405 | 738 | 64% | 165 |
| OBL (Other Biomass Liquids) | 12/12 | 146 | 135 | 12% | 12 |
| SUN (Solar) | 6/6 | 167 | 156 | 13% | 0 (weather-limited) |
| WND (Wind) | 3/3 | 127 | 127 | 11% | 0 (weather-limited) |

| shunts | in service | Mvar now | capacitive capacity | inductive capacity |
|---|---|---|---|---|
| 1 | 1 | 31 | 32 | 0 |

Size: 37 buses, 89 branches (12 transformers), 1 areas, 1 zones; kV levels 69, 138.

N-1 will check: areas 1 (of 1), all kV, 89 branches / 37 buses (the case's own setup).

## Findings
| what's wrong | where (keys) | why it matters | stops the study? | Broken / Probably on purpose / Your call | rule | kit page |
|---|---|---|---|---|---|---|
| the case already holds 14 contingency violation rows from an earlier run | — | they describe whatever the case was when that run happened, not this audit - do not read them | FYI | Probably on purpose | base.stale_ctg_results | methods/reading-violationctg.md |
| an N-1 will check 1 of 1 areas, 89 branches and 37 buses | — | a clean N-1 result covers only this footprint, not the whole system | FYI | Probably on purpose | mon.footprint | field export (schema-only) |
| rate sets with values: A (89 branches), B (89 branches), C (89 branches) | — | shows which rating letters a limit set could point at | FYI | Probably on purpose | mon.rate_sets_populated | methods/reading-violationctg.md |
| time step will run: 6 of 9 renewables follow the weather; 3 read 0 MW for the whole run (81 of 294 MW installed, 27.4%) | 3 object(s), listed below | a renewable with no PFW model has no way to turn weather into MW, and TimeStep does not warn | Worth a look | Broken | ts.pfw_missing | demos/timestep-and-pfw.md |
| weather file not given, so I didn't check it covers these units | — | send the .pww if you want its coverage checked | FYI | Your call | ts.pww_footprint | concepts/pww-data.md |

## What you need to get
1. time step will run: 6 of 9 renewables follow the weather; 3 read 0 MW for the whole run (81 of 294 MW installed, 27.4%) → the Auto_PFW scripts (concepts/auto-pfw-scripts.md); 0 of the 0 missing wind units carry a class it can use, and it skips the rest without a warning; send back the _PFW copy it writes → then send the returned case to be checked again

## Every object, per finding

### ts.pfw_missing — Worth a look — Broken

```json
{"BusNum": 23, "GenID": "10", "GenFuelType": "SUN (Solar)", "GenMWMax": 45.90000212}
{"BusNum": 23, "GenID": "9", "GenFuelType": "SUN (Solar)", "GenMWMax": 14.69999999}
{"BusNum": 26, "GenID": "1", "GenFuelType": "SUN (Solar)", "GenMWMax": 20.0000003}
```
````
