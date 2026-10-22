# PowerWorldHiveMind

<p align="center">
  <img src="assets/juiced.jpg" alt="A juiced-up pixel-art agent with glowing red eyes" width="220">
</p>

<p align="center"><strong>Your agent on PowerWorldHiveMind.</strong> Version 0.5.1</p>

<p align="center"><a href="https://chunsikpark.github.io/PowerWorldHiveMind/"><strong>Open the site</strong></a>: pick a topic, read only that part, and watch the knowledge graph grow.</p>

### Tired of babysitting your coding agent?

Tired of explaining, again, that `SaveCase` silently does nothing and that a filtered
write changes nothing at all?

**PowerWorldHiveMind juices up your agent.** Drop it in, and your assistant stops guessing
at PowerWorld and starts knowing it, including the failures that never raise an exception
and quietly hand you a wrong answer. You give it a case, it gives you the analysis, and you
stop having to be the documentation.

**22 of 23 right, against 13 for the same assistant searching the web, marked blind.**
[See the benchmark](BENCHMARK.md).

## Install

Paste this sentence into Claude Code (desktop app or CLI):

```
Install the PowerWorld knowledge base: git clone https://github.com/ChunSikPark/PowerWorldHiveMind ~/.claude/skills/powerworld-hivemind
```

Then run `/reload-plugins`, then `/powerworld-hivemind:powerworld-setup`. The setup installs
the Python packages and checks that this machine can drive PowerWorld, SimAuto licence
included.

When a newer version is published, Claude tells you at the start of a session and offers to
update. To check, the kit reads one version number from GitHub at most once a day and changes
nothing on your machine. Set `PWHM_NO_UPDATE_CHECK=1` to turn it off. If you use Claude Code
in a terminal, setup also offers a PWHM status line showing the kit's version, the model, your
usage limits and how full the context is. It asks first, and if you already have a status line
it keeps yours and adds only the `[PWHM#<version>]` tag.

**Check it worked:** ask what `pw.esa.SaveCase("out.pwb")` does. "Silently writes no file"
means the kit loaded.

- **Codex:** `codex plugin marketplace add ChunSikPark/PowerWorldHiveMind`, then install
  **powerworld-hivemind** from `/plugins`. Not yet tested on a released Codex build.
- **Anything else:** clone the repo, `pip install esapp TeamOverbyeWeather`, start your agent
  in the folder, and tell it `Read AGENTS.md and run the preflight.`
- **Never used Claude Code or Python?** [GETTING-STARTED.md](GETTING-STARTED.md) takes you
  from nothing in six steps, about fifteen minutes.

You need Windows, PowerWorld Simulator, and the SimAuto add-on, which is licensed
separately. The agent can also drive Simulator through `.aux` files dropped in a watched
folder, and read PowerWorld's own message log for each one:
[methods/aux-file-mode.md](methods/aux-file-mode.md).

## What's new in 0.5

- **Validated on 30 real study requests.** A fresh agent, given only the request and the case,
  solved 30 of 30 against an answer key written before the run. v0.4 solved 20.
  [See every request and answer](https://chunsikpark.github.io/PowerWorldHiveMind/validation.html).
- **It knows when to stop.** Seven rules in [AGENTS.md](AGENTS.md#scope-the-work-before-you-start):
  answer, then offer; estimate before a long study; one working design first; audit and ask on
  a vague request; out of scope means stop. Most v0.4 misses were the agent working past the
  answer, not missing knowledge.
- **case-audit catches stranded load.** Load on a disconnected bus now stops a study (before,
  2 GW of islanded load audited as READY), and a `lint` profile checks nine kinds of bad data.
- **Overloads on the map.** `violation-map` gains a thermal view and uses the case's own voltage
  limits.
- **Eleven new pages**, mostly on fixing violations in large cases: base-case and N-1
  remediation, a non-converging contingency, reviewing a design, radial-by-N-1 pockets, the
  zone load multiplier trap, and more. [Browse them by topic](index.md#browse-by-topic).
- **Share what you learn.** After writing a page, the agent can scrub a copy and hand you a
  pre-filled GitHub issue to submit.

Full list in [CHANGELOG.md](CHANGELOG.md).

## Where to go next

| You want | Read |
|---|---|
| The whole kit, by topic | [index.md](index.md) |
| Worked runs on a 37-bus case, failures included | [demos/start-here.md](demos/start-here.md) |
| How it scored against web search | [BENCHMARK.md](BENCHMARK.md) |
| The agent team and its rules | [docs/agents/README.md](docs/agents/README.md) |
| To file what you worked out as a new page | say *"write that up as a page"*, or [skills/knowledge-base-page/SKILL.md](skills/knowledge-base-page/SKILL.md) |
| To see the pages as a graph offline | open the folder as an [Obsidian](https://obsidian.md) vault and press Ctrl/Cmd+G |
| You are an agent | [AGENTS.md](AGENTS.md) |

<details>
<summary>Which instruction file each agent loads</summary>

On the plugin route, Claude Code loads the five skills under `skills/`, the
`schema-librarian` and `case-auditor` agents, and the two commands. It does not load `CLAUDE.md` or `AGENTS.md`
from a plugin; `skills/powerworld/SKILL.md` carries the rules and points at the pages.

On the manual route:

| Your agent | Loads | Shipped as |
|---|---|---|
| Codex, Cursor, GitHub Copilot, Windsurf | `AGENTS.md` | the file itself |
| Claude Code | `CLAUDE.md` | a one-line `@AGENTS.md` import |
| Gemini CLI | `GEMINI.md` | a generated copy of `AGENTS.md` |

`GEMINI.md` is generated, so edit `AGENTS.md` instead. Checked against each vendor's docs on
2026-09-09, not smoke-tested on each client.

</details>

## Credits and contributing

Built on [`esapp` (ESA++)](https://github.com/lukelowry/ESApp), the Apache-2.0 PowerWorld
SimAuto wrapper from Texas A&M, and
[`TeamOverbyeWeather`](https://pypi.org/project/TeamOverbyeWeather/). A bug in the package
goes to [esapp](https://github.com/lukelowry/ESApp). A page here that is wrong or missing
goes in an issue here, naming the page. Every page exists because someone lost time to the
thing it documents.

PowerWorld Simulator is commercial software of PowerWorld Corporation. This is an
independent knowledge base and is not affiliated with or endorsed by them.
