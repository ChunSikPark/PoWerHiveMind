# The website (site/)

Source for https://chunsikpark.github.io/PoWerHiveMind/. Maintainer notes only: this
file is not published (the Pages workflow copies an explicit file list) and not in the
plugin build.

## Each page has one job

| Page | Job |
|---|---|
| `index.html` | Decide whether to install. One scroll, no hidden panels. |
| `install.html` | Get it running. The only install instructions on the site. |
| `validation.html` | The benchmark: the 30 tasks, plus "Earlier tests" (`#earlier`). |
| `demo-design.html` | The one recorded run, replayed on the map. |
| `demo-has-page.html`, `demo-new-page.html` | Illustrated walkthroughs of how the agent searches. |

## Main page order (set 2026-10-22)

Hero → page graph → How it finds the answer (`#demo`, two walkthrough cards) → It runs
the whole study (`#work`, recorded run first) → Does it help? (`#proof`) → How your AI
talks to PowerWorld (`#talk`) → Install card (`#get`) → Add to it (`#add`).

The reason is the reader's path: how big the kit is, how the agent searches it, what it
does, proof it works, then install. The graph sits under the hero because it is the only
at-a-glance sign of size, and it only grows once it scrolls into view, so at the bottom
most readers never saw it. The walkthroughs follow it because they animate that same graph.
They are kept to two cards so proof still starts under 4 screens down on desktop
(measured 2026-10-22); the "30 of 30" line in the hero already links to the benchmark.

- **No hidden or hash-routed panels.** The old ones were unreachable, because nothing
  linked to them. Every section is a normal section with an id.
- **Don't re-add the cuts:** the agent-team panel (mostly "planned" roles, which made the
  proof read like marketing), the search-demo panel (it repeated the walkthroughs) and the
  embedded walkthrough iframe (40% of the page height).
- Old hashes forward through `MOVED` in `index.html`'s script. Add an entry there when a
  section moves.

## Every page shares one nav

Demo · Benchmark · Install · Contribute · Changelog · GitHub, with `aria-current="page"` on
the current page. Change all six pages together. It is "Benchmark", never "Validation".
Each demo page ends with an Install link, so no page is a dead end.

## Check and ship

- Serve `site/` locally with `python -m http.server`. A 404 on `data.json` is expected:
  CI builds it with `build_data.py`, so the page graph stays hidden locally.
- A new page must also be added to the `cp` line in `.github/workflows/pages.yml`, or it
  never deploys.
- A push to `main` deploys in about 30 seconds.
