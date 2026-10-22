"""Write data.json for the site: the kit's link graph, and real searches run over the kit.

Graph: every page the repo's Obsidian graph shows (see .obsidian/graph.json), the links between
them, and the date each page was added. Dates come from git, so the checkout needs full history
(fetch-depth: 0).

Searches: each question in SEARCHES is run the way AGENTS.md tells an agent to search, over the
four content folders, and the ranking, hit counts and Abstracts are the kit's own at build time.

    python site/build_data.py <out.json>
"""
import json
import posixpath
import re
import subprocess
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKIP = ("skills/", "commands/", "dist/", "assets/", "evals/", "docs/superpowers/", "site/", ".github/", ".obsidian/")
LINK = re.compile(r"\]\(([^)\s#]+\.md)(?:#[^)]*)?\)")
GROUPS = {"concepts", "methods", "references", "demos"}
CONTENT = ["concepts", "methods", "demos", "references"]

# One entry per demo question. `plain` and `ident` are the two vocabularies AGENTS.md says to
# search together. `expect` is the page the hand-written `answer` comes from; if the ranking ever
# stops landing there, the answer is left out rather than shown against the wrong page.
SEARCHES = [
    {"id": "save", "q": "I saved the case and no file showed up. What happened?",
     "plain": ["save the case", "no file", "silently"], "ident": ["SaveCase"],
     "expect": "methods/save-powerworld-case.md",
     "answer": "The SimAuto <code>SaveCase</code> call reports success and writes nothing. Save with the "
               "script command instead: <code>pw.esa.RunScriptCommand('SaveCase(\"out.pwb\", PWB);')</code>. "
               "Exactly two parameters. A third one fails with <i>Invalid number of parameters</i>."},
    {"id": "outage", "q": "Which outage caused which overload?",
     "plain": ["overload", "contingency"], "ident": ["ViolationCTG", "CTGSolveAll"],
     "expect": "methods/reading-violationctg.md",
     "answer": "Solve with <code>CTGSolveAll</code>, then read <code>ViolationCTG</code> with an explicit field "
               "list. Each row carries its <code>CTGLabel</code>, so you know which outage did it. Don't filter "
               "on <code>AreaNum</code>: it reads 0 on a tie-line and drops every cross-area violation."},
    {"id": "zero", "q": "TimeStep ran fine, but my solar reads 0 MW. Why?",
     "plain": ["zero output", "0 MW"], "ident": ["TimeStep", "PFW"],
     "expect": "demos/timestep-and-pfw.md",
     "answer": "Your solar units most likely carry no PFW model, so TimeStep has nothing to drive them with "
               "and still reports success. Count which renewables have a PFW model before you run. On the "
               "demo case it was 9 of 45."},
]


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, check=True).stdout


def body_of(text):
    return text.split("\n---", 2)[-1] if text.startswith("---") else text


def title_of(text, stem):
    m = re.search(r"^# (.+)$", body_of(text), re.M)
    return m.group(1).strip() if m else stem.replace("-", " ")


def section(text, name):
    m = re.search(rf"^## {name}\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    return m.group(1).strip() if m else ""


def plain(md, limit=460):
    """First paragraph of a markdown block as plain text, cut at a sentence near `limit`."""
    para = md.split("\n\n")[0].replace("\n", " ")
    para = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", para)
    para = re.sub(r"\*\*|__|`", "", para)
    if len(para) <= limit:
        return para
    cut = para.rfind(". ", 0, limit)
    return para[: cut + 1] if cut > 0 else para[:limit] + "…"


def graph():
    pages = sorted(p for p in git("ls-files", "*.md").splitlines() if "/" in p and not p.startswith(SKIP))
    known = set(pages)
    nodes, links = [], set()
    for p in pages:
        text = (ROOT / p).read_text(encoding="utf-8")
        added = git("log", "--diff-filter=A", "--follow", "--format=%as", "--", p).split()
        top = p.split("/")[0]
        front = text.split("\n---", 1)[0] if text.startswith("---") else ""
        topic = re.search(r"^topic:\s*(\S+)", front, re.M)
        nodes.append({"id": p, "title": title_of(text, Path(p).stem),
                      "group": top if top in GROUPS else "agents",
                      # the page's `topic:` field, the same one index.md's "Browse by topic" groups on
                      "topic": topic.group(1) if topic else "agents",
                      "added": added[-1] if added else date.today().isoformat()})
        for target in LINK.findall(text):
            t = posixpath.normpath(posixpath.join(posixpath.dirname(p), target))
            if t in known and t != p:
                links.add(tuple(sorted((p, t))))
    return nodes, [list(l) for l in sorted(links)]


def search(s):
    terms = s["plain"] + s["ident"]
    pages = {f"{d}/{p.name}": p.read_text(encoding="utf-8") for d in CONTENT for p in sorted((ROOT / d).glob("*.md"))}
    rows = []
    for rel, text in pages.items():
        lines = text.lower().splitlines()
        hits = [sum(t.lower() in ln for ln in lines) for t in terms]  # matching lines per term, like rg -ic
        if any(hits):
            rows.append({"page": rel, "title": title_of(text, Path(rel).stem), "hits": hits,
                         "terms": sum(1 for h in hits if h)})
    rows.sort(key=lambda r: (-r["terms"], -sum(r["hits"]), r["page"]))
    top = rows[0]["page"]
    out = {k: s[k] for k in ("id", "q", "plain", "ident")}
    out.update(hit_pages=len(rows), rank=rows[:5],
               top={"page": top, "abstract": plain(section(pages[top], "Abstract"))})
    if top == s["expect"]:
        out["answer"] = {"page": top, "html": s["answer"]}
    else:
        print(f"warning: search '{s['id']}' now lands on {top}, not {s['expect']}; answer left out", file=sys.stderr)
    return out


def main(out):
    nodes, links = graph()
    searches = [search(s) for s in SEARCHES]
    Path(out).write_text(json.dumps({"generated": date.today().isoformat(), "nodes": nodes,
                                     "links": links, "searches": searches}, indent=1), encoding="utf-8")
    print(f"{len(nodes)} pages, {len(links)} links, {len(searches)} searches -> {out}")


if __name__ == "__main__":
    main(sys.argv[1])
