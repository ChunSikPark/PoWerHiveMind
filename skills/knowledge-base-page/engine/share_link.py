"""Build the pre-filled GitHub issue that shares a scrubbed page with the maintainer.

    python share_link.py --page <scrubbed copy> --title "New page: methods/foo.md" --note-file <note.md>

The issue carries two labels: the kind (--label, default new-page) and the page's topic,
read from its `topic:` line (--topic overrides). Writes the full issue body to
<scrubbed copy>.issue.md, prints the link, and lists anything left in the text that still
looks like case data. Opens nothing, sends nothing.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from urllib.parse import quote, urlencode

REPO = "https://github.com/ChunSikPark/PoWerHiveMind/issues/new"
LIMIT = 8000  # past roughly this, browsers and GitHub refuse the link
TITLES = ("New page: ", "Page update: ")
KINDS = ("new-page", "page-defect", "missing-page")
TOPICS = ("power-flow", "contingency", "timestep", "design", "case-audit", "scripting", "agents")
TOO_LONG = ("**Page text:** too long for a link. Paste the full page below this line, "
            "from the `.issue.md` file the assistant named.\n")

# simple: catches the mechanical leaks only; bus numbers and names need a human read
LEFTOVERS = {
    "case file name": re.compile(r"\b[\w.-]+\.(?:pwb|pwd|raw|epc|dyr)\b", re.I),
    "personal folder path": re.compile(
        r"[a-z]:[\\/](?:users|documents and settings)[\\/][^\\/\s`]+|/(?:home|Users)/[^/\s`]+", re.I),
    "email address": re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
}
PUBLIC_GRIDS = re.compile(r"texas2k|synth2k|activsg|hawaii40|ieee\s?\d+", re.I)


def issue_body(note: str, page: str) -> str:
    """The note, then the page as raw markdown in a fence longer than any inside it."""
    longest = max((len(m) for m in re.findall(r"`+", page)), default=0)
    fence = "`" * max(3, longest + 1)
    return f"{note.strip()}\n\n{fence}markdown\n{page.rstrip()}\n{fence}\n"


def issue_url(title: str, body: str, labels: str = "new-page") -> str:
    return REPO + "?" + urlencode({"title": title, "body": body, "labels": labels}, quote_via=quote)


def topic_of(page: str) -> str | None:
    """The `topic:` value from the page's frontmatter, or None."""
    m = re.match(r"﻿?---\r?\n(.*?)\r?\n---", page, re.S)
    t = re.search(r"^topic:\s*(\S+)\s*$", m.group(1), re.M) if m else None
    return t.group(1) if t else None


def build(title: str, note: str, page: str, label: str = "new-page",
          topic: str | None = None) -> tuple[str, str, bool]:
    """Return (link, full body, whether the full body fits in the link)."""
    if not title.startswith(TITLES):
        raise ValueError(f"title must start with {' or '.join(repr(t) for t in TITLES)}: {title!r}")
    if label not in KINDS:
        raise ValueError(f"label must be one of {', '.join(KINDS)}: {label!r}")
    topic = topic or topic_of(page)
    if topic not in TOPICS:
        raise ValueError(f"the page needs a topic: line with one of {', '.join(TOPICS)} (or pass --topic): {topic!r}")
    labels = f"{label},{topic}"
    body = issue_body(note, page)
    url = issue_url(title, body, labels)
    if len(url) <= LIMIT:
        return url, body, True
    url = issue_url(title, f"{note.strip()}\n\n{TOO_LONG}", labels)
    if len(url) > LIMIT:
        raise ValueError("the note alone is too long for a link; cut it to a few lines")
    return url, body, False


def leftovers(text: str) -> list[str]:
    """Lines that still look like case data. A list to read, not a verdict."""
    hits = []
    for n, line in enumerate(text.splitlines(), 1):
        for kind, pat in LEFTOVERS.items():
            hits += [f"line {n}: {kind}: {m}" for m in pat.findall(line) if not PUBLIC_GRIDS.search(m)]
    return hits


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--page", required=True, type=Path, help="the scrubbed copy of the page")
    ap.add_argument("--title", required=True, help='"New page: <folder>/<slug>.md" or "Page update: ..."')
    ap.add_argument("--note-file", required=True, type=Path, help="what the page is, why, its index.md row")
    ap.add_argument("--label", default="new-page", choices=KINDS, help="the kind of report")
    ap.add_argument("--topic", choices=TOPICS, help="overrides the page's topic: line")
    a = ap.parse_args(argv)

    page = a.page.read_text(encoding="utf-8-sig")
    note = a.note_file.read_text(encoding="utf-8-sig")
    try:
        url, body, fits = build(a.title, note, page, a.label, a.topic)
    except ValueError as e:
        print(f"error: {e}", file=sys.stderr)
        return 2
    out = a.page.with_name(a.page.name + ".issue.md")
    out.write_text(body, encoding="utf-8")

    print(f"issue body: {out}")
    if fits:
        print(f"link ({len(url)} chars, carries the whole page):\n{url}")
    else:
        print(f"link ({len(url)} chars, note only - the page is too long for a link; "
              f"the user pastes {out.name} into the issue):\n{url}")
    hits = [f"note {h}" for h in leftovers(note)] + [f"page {h}" for h in leftovers(page)]
    print("still looks like case data - read before sharing:" if hits else "no leftover case file names, personal paths or emails found")
    for h in hits:
        print(f"  {h}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
