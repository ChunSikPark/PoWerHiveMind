---
type: method
domain: tooling
topic: scripting
aliases: [demos-index, demos, demo-index, examples, worked-examples]
tags: [demo, index, examples, prompts, getting-started]
---

# Demos: what to say, and what happens

## Abstract

Worked runs on the public synthetic Synth40 case (37 buses, 89 branches, 45 generators).
Every number on these pages came from a real run, including the failures, which were left
in on purpose. Start with the one-line prompts below. You should not have to know which
page covers what.

## Connections

- **Up:** [Home](../index.md)
- **Across:** [handling-errors](../methods/handling-errors.md) · [preflight-powerworld](../methods/preflight-powerworld.md) · [esapp-overview](../methods/esapp-overview.md)

## Content

### Just say this

You do not need to name a function, a field, or a file. Say the thing you want:

| Say this | The agent will |
|---|---|
| *"Is PowerWorld working on this machine?"* | Run the 5-check preflight and tell you what is missing |
| *"Open my case and summarize it."* | Load it, solve, report buses/branches/generators and voltage range |
| *"Which branches are most heavily loaded?"* | AC solve, rank by percent of rating |
| *"Anything overloaded?"* | Solve and check limits, base case and N-1 |
| *"Run a DC power flow instead."* | Switch solver mode and re-solve |
| *"If line 27–29 trips, where does the flow go?"* | LODF, sentinel values filtered |
| *"How sensitive are the lines to a transfer from bus 23 to bus 26?"* | PTDF |
| *"Add a line between bus 27 and bus 31 and tell me if it helps N-1."* | Create it, verify it was really created, re-run N-1, compare |
| *"Run N-1 on everything."* | Auto-insert contingencies, solve, report violations |
| *"Build me a contingency file for the five most loaded lines."* | Generate an `.aux` and load it |
| *"Get February 2021 weather for Texas."* | Download a cropped `.pww` |
| *"How much wind and solar would these units produce?"* | Set up and run a TimeStep simulation |
| *"Run N-1, work out what's wrong, and tell me what to build to fix it."*  | Diagnose the cause, test candidate reinforcements, rank them, and say which to reject |
| *"Compare my 2016 and 2024 cases and tell me what the plan builds."* | Diff both, guard against renumbering artifacts, classify NEW / RETIRED / UPGRADED |
| *"Do the new devices in this plan cause violations?"* | Build a contingency set for just those devices, solve, and attribute correctly |
| *"Can this case run a weather study?"* | Check whether its renewable units carry PFW models |
| *"Save the case."* | Write it out, after asking where, since that is destructive |

If a prompt fails, that is a defect worth reporting. The routing is
[AGENTS.md](../AGENTS.md)'s job, not yours.

### The demos

| Demo | Shows |
|---|---|
| [comparing-planning-cases](comparing-planning-cases.md) | **Multi-case.** 2016 vs 2024: 691 new branches, 199 new generators, and a scoping trap that makes the naive answer 87% wrong |
| [violation-remediation](violation-remediation.md) | **The full study.** 12 violations diagnosed to one cause, five reinforcements tested and ranked, two of which make things worse |
| [adding-a-device](adding-a-device.md) | **Read this one.** Three attempts that succeeded and did nothing, then the fix. The silent-failure problem in full |
| [power-flow-and-sensitivities](power-flow-and-sensitivities.md) | AC, DC, LODF, PTDF, with the `1e8` sentinel and a two-step error recovery |
| [contingency-and-aux](contingency-and-aux.md) | N-1 from scratch, and generating a filter + contingency `.aux` automatically |
| [timestep-and-pfw](timestep-and-pfw.md) | Weather to megawatts: PFW models, TimeStep, and reading the output |
| [aux-file-cookbook](aux-file-cookbook.md) | Claude in one window, Simulator in the other. Four recipes in order: turn the channel on, prove it with a four-line script, inventory a case, then take a bus out and measure it. Start here if you are working through files rather than Python. |

### Queries versus studies

The first few prompts above are queries: one number, one answer. The rest are studies:
*diagnose the cause, propose a fix, apply it, re-verify, and report what you rejected.*

Studies are what this kit is for. A voltage readout needs no knowledge base. Knowing that
reinforcing the most loaded branch can make N-1 **worse**, and having measured it, does.

### Measuring whether this actually works — in progress

The traversal protocol claims a fresh agent needs three to five pages for a typical task.
**That is a design target, not yet a measured result.** To check it:

1. Start a fresh session with no prior PowerWorld context, in a clean clone.
2. Give it one prompt from the table above.
3. Count the pages it opens before it writes code.

**Pass is fewer than 8 of 41.** Reading 25 means the router's traversal instructions are
too weak and belong in the next revision. That is a defect in this knowledge base, not in
the agent.

If you run it, open an issue on the repository with the page count and the prompt you
used, pass or fail. A failure here is more useful than a pass.

### What every demo assumes

Preflight passed. If it did not, nothing here runs — see [preflight-powerworld](../methods/preflight-powerworld.md).

### The case used

```
Synth40.pwb
  37 buses, 89 branches, 45 generators, 27 loads
  1154.7 MW generation vs 1136.3 MW load
  voltage 0.9749 - 1.0034 pu, Sbase 100 MVA
  base case: 0 overloads
  N-1: 12 violations across 89 auto-inserted contingencies
```

It was chosen because it is small enough that a wrong answer is visibly wrong. It is
synthetic, so nothing here is sensitive.

### Two habits these demos are trying to teach

**Assert the effect, not the absence of an error.** PowerWorld will accept a malformed
request, report success, and do nothing. Count before, count after, assert the delta.

**Say what you did not do.** None of these demos saved the case. Every one of them says
so. An analysis that quietly wrote to disk is worse than one that quietly did not.
