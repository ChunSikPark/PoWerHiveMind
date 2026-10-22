---
name: knowledge-base-page
description: Write something up as a page in this knowledge base, or edit a page already here. Use when the user wants to record, save, document, write up or keep what they just worked out - a PowerWorld behaviour, a procedure that worked, a failure mode, a gotcha - so it is not lost when the session ends. Also use when asked to add a page, fix a page, or check whether the pages still hang together (missing index rows, links pointing nowhere), or to share a page with everyone else who uses this kit ("send it in", "share it", "get it to everyone").
topic: agents
---

# Writing a page into this knowledge base

This repo is a knowledge base you are expected to **grow**, not just read. A
session that worked something out and left it in the chat has thrown it away.

The schema below was derived by measuring the pages this repo already ships,
and nearly every one of them follows it. **The pages are authoritative.** If this file and the pages ever disagree, read a
few pages and follow those; then fix this file.

## Before you write: does a page already cover it?

`grep` the four content folders on both the plain-English phrasing and the
likely identifier, several terms at once:

```bash
grep -rn -i "shunt\|Shunt\|GenMVRMax" concepts/ methods/ references/ demos/
```

Read a candidate's `## Abstract` first. It is written to tell you whether the
page is the right one. If it covers the ground, **edit that page instead of
adding a second one.** Two pages on one topic is the failure this base exists
to avoid.

## Where the page goes

| The thing you are recording | Folder | `type:` |
|---|---|---|
| What a thing *is* — a model, a concept, a failure mode | `concepts/` | `concept` |
| How to *do* a thing — a procedure that worked | `methods/` | `method` |
| A code/API surface reconstructed in detail | `references/` | `reference` |
| A worked run with real output, failures left in | `demos/` | `method` (aux-file-cookbook is a `reference`) |
| A package or tool's interface | `concepts/` | `tool` |
| A dataset's shape and quirks | `concepts/` | `dataset` |

## The page shape

Copy this. Every field is required.

```markdown
---
type: concept
domain: tooling
topic: contingency
aliases: [the-slug, a-synonym, what-someone-would-search]
tags: [esapp, powerworld, contingency]
---

# Title In Sentence Case

## Abstract
One paragraph, written so a reader can decide from it alone whether to open the
rest. State the answer here, not a promise of the answer.

## Connections
- **Up:** [Home](../index.md)
- **Used in:** [some-method](../methods/some-method.md)
- **Across:** [a-concept](../concepts/a-concept.md)

## Content

### The actual material
```

**`type:`** is one of `concept`, `method`, `reference`, `tool`, `dataset`.
**`domain:`** is one of `tooling`, `cross-cutting`, `weather`, `synthetic-grid`.
Use one of these. If your page genuinely needs a new value, **say so explicitly**
rather than bending the page to fit or quietly inventing one: adding a value is a
decision about the whole base, not about your page.

**`topic:`** is exactly one of these seven slugs. It puts the page under its heading in
`index.md`'s *Browse by topic* section (add the page's line there too) and becomes the second
label on a shared page's issue:

| slug | covers |
|---|---|
| `power-flow` | solving, convergence, DC/AC, dispatch, OPF |
| `contingency` | building sets, solving, reading violations, ranking, remediation of N-1 results |
| `timestep` | PWW, PFW models, hourly runs and results |
| `design` | adding devices, reviewing and comparing designs, sizing, base-case remediation |
| `case-audit` | case sanity, lint, multipliers, islanded load, impedance completeness |
| `scripting` | esapp, SimAuto, aux files, SCRIPT commands, saving, glossary, version requirements, preflight |
| `agents` | `agents/*.md` and `skills/*/SKILL.md` |

Pick the one a reader would be doing when they need the page. Folders stay as they are; the
topic is a label, not a location.

**`aliases:`** and **`tags:`** are `[bracketed, lists]`. They may wrap across
lines. These are what `grep` finds later, so write the phrasings a future
reader would actually type, not a restatement of the title.

## Links are the point

A page with no outbound links is **refused**: it is unreachable and will never
be found again. Links are relative markdown, not wikilinks:

```markdown
[copper-plate](../concepts/copper-plate.md)     <- correct
[[copper-plate]]                                 <- not used in this repo
```

Every link target must exist on disk; a typo or a renamed page is a refusal.
Two or more links passes; one gets a warning.

## Bookkeeping: add the index.md row

`index.md` is the catalog. A new page adds **exactly one** row, in the table
for its folder, in the existing style:

```markdown
| [your-page](concepts/your-page.md) | One line on what it covers and when to open it. |
```

Then add one line under the page's topic heading in *Browse by topic*, at the
end of `index.md`:

```markdown
- [your-page](concepts/your-page.md): the one-line hook.
```

A page with no row warns rather than refusing, because two pages already ship
without one. Add it anyway.

## Check the corpus when you have finished

There is no checker to run; the shape above is the whole schema. Three
questions can only be answered across all the pages at once. Run these from
the repo root when you have added or renamed pages:

```bash
# pages with no row in index.md
python -c "import pathlib;R=pathlib.Path('.');i=(R/'index.md').read_text(encoding='utf-8-sig');print([f'{d}/{p.name}' for d in ('concepts','methods','demos','references') for p in (R/d).glob('*.md') if f'{d}/{p.name}' not in i and p.stem not in i] or 'all pages indexed')"

# links that point at a file that does not exist
python -c "import pathlib,re;R=pathlib.Path('.');print([f'{p}: {t}' for d in ('concepts','methods','demos','references') for p in (R/d).glob('*.md') for t in set(re.findall(r'\]\(([^)#]+\.md)',p.read_text(encoding='utf-8-sig'))) if not (p.parent/t).exists()] or 'no dangling links')"

# page names in ## Connections that were never written as links
python -c "import pathlib,re;R=pathlib.Path('.');L=re.compile(r'\[[^]]*\]\([^)\s]*\)');S=re.compile(r'^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$');B=lambda t:[s for s in [re.split(r'\s+[\u2014\u2013-]\s+|\s*\(',x.replace('\x00',' ').strip(),maxsplit=1)[0].strip('*_[] ') for x in re.split(r'[\u00b7\n,;]',re.sub(r'\*\*[^*]+?:\*\*',' \u00b7 ',L.sub(' \x00 ',t.split('## Connections')[1].split(chr(10)+'## ')[0])))] if S.match(s)] if '## Connections' in t else [];print([f'{p}: {n}' for d in ('concepts','methods','demos','references') for p in (R/d).glob('*.md') for n in B(p.read_text(encoding='utf-8-sig'))] or 'no bare page names')"
```

Paste what they print. The first two must come back clean before you say you
are done.

The third is a signal to read, not a gate. It looks for a page name written as
bare text where a link belongs, which the dangling-link check cannot see: with
no `[](...)` around it there is nothing to resolve. The port that seeded the
manual pages lost 19 cross-references exactly this way, and every check passed.
Ordinary hyphenated English standing alone in a
segment takes the same shape, so `no-op` and `per-solve` are expected hits.
Read each one and decide: a page name gets written as a link or deleted, a word
stays.

## Share it — only when the user says yes

The page now exists on this one machine. Everyone else's kit gets it only when
the maintainer merges it, and most users cannot open a pull request. So the
route is a pre-filled GitHub issue: you scrub the page, build the link, the
user reads it and clicks submit, the maintainer merges, and the next kit update
carries the page to everyone.

This is the same channel as [Filing a defect against this knowledge
base](../../AGENTS.md) in `AGENTS.md`, with its own title and label. The rules
there hold here too: **offer, never file on your own; show the exact text
first; say the tracker is public.**

**1. Ask.** Once the checks above are clean, ask one plain question: *"Want to
share this page so everyone using PowerWorldHiveMind gets it? I'd strip the case details
first and show you exactly what would go out."* No answer, or no, ends it.

**2. Scrub a copy, not the page.** The user's page may keep their case details;
the shared text may not. The cases this kit drives are often CEII or otherwise
restricted. Write the scrubbed copy to the system temp folder (never inside
`concepts/`, `methods/`, `demos/` or `references/`, where it would count as a
page). Remove or generalize:

- case file names and paths, and any private folder path
- bus numbers and bus names, substation, utility, area, zone and owner names:
  write `a 345 kV bus`, `an area`, `<area A>`
- device identifiers (`GenID`, circuit IDs, contingency labels from the case)
- parameter values read out of the real case
- counts that fingerprint a case (an exact branch or contingency count): give a
  ratio or an order of magnitude instead
- names of people

Keep the mechanism, the rule, the failure mode, the code pattern and the field
names (`GenMVRMax` is the API, not the case). Cite a measurement by date and
Simulator build date, never by case: *"measured 2026-10-12, Simulator build
2026-08-01, on a regional planning model."* Public synthetic grids such as Texas2k
(ACTIVSg2000), Hawaii40 and the IEEE test cases may stay named with their
numbers; they are the preferred worked example. If a point can only be shown on
a real case, keep the point and drop the demonstration.

**3. Build the link.** Write a short note file: one line on what the page
covers, why it matters (what went wrong without it), and the `index.md` row you
added. Then:

```bash
python "${CLAUDE_PLUGIN_ROOT}/skills/knowledge-base-page/engine/share_link.py" --page "<scrubbed copy>" --title "New page: methods/<slug>.md" --note-file "<note>"
```

Use `Page update: <folder>/<slug>.md` for an edit to a page that already
exists. Installed as a Claude Code plugin, `${CLAUDE_PLUGIN_ROOT}` is replaced
with the kit's absolute path; anywhere else, type the absolute path of the
directory holding `AGENTS.md` in its place. The issue carries **two labels**:
the kind (`new-page` by default; `page-defect` or `missing-page` with `--label`) and the
page's topic slug, which the script reads from the copy's `topic:` line
(`--topic <slug>` overrides it; a copy with no valid topic is refused). The
script percent-encodes the title, body and both labels, writes the full issue body to
`<scrubbed copy>.issue.md`, and prints the link. If the page would push the
link past about 8,000 characters (where it stops opening), the link carries
the note only and the user pastes the `.issue.md` text into the issue body
themselves; tell them which file. It also lists anything still shaped like case
data: case file names, personal folder paths, email addresses. Read every hit.
A placeholder such as `out.pwb` is fine; a real case name means the scrub
missed it, so fix the copy and run it again. It cannot see bus numbers or
utility names, so that part of the scrub is still yours.

**4. Show, then hand over.** Give the user, in this order:

1. one line: *"The issue tracker is public. Anyone can read what you submit."*
2. what you removed or changed, as a short list (`bus 12345 → a 345 kV bus`)
3. the final text (the `.issue.md` file)
4. the link, to open, review and submit themselves

Let them edit the text or decline. A shared page is never worth leaking a case.

If `gh` is installed and signed in (`gh auth status`), offer it instead of the
link, still only after they approve the exact text:

```bash
gh issue create --repo ChunSikPark/PowerWorldHiveMind --title "New page: methods/<slug>.md" --label new-page --label <topic> --body-file "<scrubbed copy>.issue.md"
```

`--body-file` has no 8,000-character limit. If `gh` refuses because a label
does not exist on the repo, run it again without that `--label`.
