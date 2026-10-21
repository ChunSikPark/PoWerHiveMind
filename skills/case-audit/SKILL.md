---
name: case-audit
description: "Check a PowerWorld case read-only and say whether it is sane and READY for a study - base power flow, N-1 monitoring, TimeStep with weather, OPF/SCOPF - with a case summary (load, generation, headroom by fuel type, shunts, size) and every blocker named by its object keys, plus a data lint (shunt steps, unit limits, ratings, islands, names, kV). Use for 'review this case', 'scan the case', 'what's wrong with this case', 'check the case for issues', 'give me a summary of this case', 'what's in this case', 'can I run a time step / OPF / N-1 on this', 'is this case ready for X'. Never writes the case."
topic: agents
---

# Case audit

The engine does the checking; you do the triage. Never re-derive a rule by hand, never run your
own script against the case, and never recompute a summary number.

## 0. The kit root

Installed as a Claude Code plugin, `${CLAUDE_PLUGIN_ROOT}` in this file is replaced with the kit's
absolute path before you read it, so the commands below run as written. It is **not** an
environment variable: in any other harness, or if you still see the literal text
`${CLAUDE_PLUGIN_ROOT}`, type the absolute path of the directory holding `AGENTS.md` in its place.

## 1. Map the request to profiles

| the engineer asks about | `--profiles` |
|---|---|
| a summary, "what's in this case", "is it sane" | `base` |
| N-1, contingencies, SCOPF monitoring | `base` (the `n1` verdict line comes with it) |
| "is this case N-1 clean": what breaks when the outages are solved | out of scope: the audit checks N-1 monitoring and does not solve contingencies. Use the powerworld skill |
| time step, weather, PFW, renewables over time | `base,timestep` |
| OPF, economic dispatch | `base,opf` |
| SCOPF | `base,opf` (the `scopf` verdict line comes with it) |
| data problems: "what's wrong with this case", "check it for issues", "is the data clean" | `base,lint` |
| "scan the whole case", or you cannot tell | `base,timestep,opf,lint` |

For a time step, pass the weather file with `--pww` if the engineer named one. If they did not,
run without it: the engine reports that as one FYI line. Never ask for it mid-run.

## 2. Run the engine

```
python "${CLAUDE_PLUGIN_ROOT}/skills/case-audit/engine/audit.py" --case "<absolute path to the .pwb>" --profiles <list> [--pww "<absolute path to the .pww>"]
```

- The files go to `./case-audit/<case name>/` under the current folder (it holds a `.gitignore`,
  so the case's data stays out of any repository). The engine prints the path once. Pass
  `--out "<folder>"` only if the engineer named one.
- Exit 0: `findings.json` and `findings.md` are written, whatever the verdicts.
- Exit 2: nothing was audited. Relay the three lines it printed as they are, and stop.
- Any other exit: the engine itself failed. Say "the audit engine broke on our side, not your
  case; nothing was written to it" and stop - do not audit by hand.
- It opens PowerWorld, solves AC once in memory, reads, and closes. It takes seconds on a
  few-thousand-bus case. The case file is never written; `findings.json` records its sha256
  before and after under `read_only`.

## 3. Read the result

Read `findings.json` (numbers) and `findings.md` (tables already formatted).

- `verdicts`: READY or NOT READY per study, with the reason. **Report them as the engine gives
  them.** A study is NOT READY only when a finding with severity *Stops the study* names it.
  `n1` is always there (monitoring comes with base); show it when the engineer asked about N-1
  or SCOPF. `scopf` comes with `opf`; show it when they asked about SCOPF.
- `findings[].handoff`: where the data a fix needs comes from. Each one becomes a line of
  "What you need to get".
- `case_summary`: the summary tables. Present them; never recompute them.
- `findings`: each has `severity` (Stops the study / Worth a look / FYI) and `triage`
  (Broken / Probably on purpose / Your call). The engine's triage is its default reading; change
  one only when the case in front of you gives a reason, and say the reason.
- `rules_skipped`: checks that did not run, and why (most need a solved AC power flow). Never
  say a skipped check passed. A lint rule is here when the case or snapshot did not carry a field
  it reads; a rule that ran in part is in both lists.
- `variants_beside`: other versions of the case in its folder. Say which file you audited.
- `ts.pfw_missing` and `ts.latlon_missing` never stop a time step: say what the run will do
  ("115 of 120 renewables will follow the weather; 5 read 0 MW").

## 4. Answer

Verdict first, then the summary tables, then the findings that matter; everything else stays in
`findings.md`, whose path you give once. The full output contract, triage guide and handoffs are
in `${CLAUDE_PLUGIN_ROOT}/agents/case-auditor.md` - read its *Output format* and *Handoffs*
sections before your first answer.

When `lint` ran, every lint finding is a Findings row with its count and up to 3 object keys, and
every `rules_skipped` entry is a `not checked` line.

## Never

- Never save, load an aux into, or `SetData` on the case; the engine never does.
- Never suggest default cost curves, guessed PFW classes or invented coordinates to clear a blocker.
- Never state a check the engine did not run.
