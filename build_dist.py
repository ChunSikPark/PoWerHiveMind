#!/usr/bin/env python3
"""Rebuild dist/ from the source pages.

dist/ had no build script and drifted: at 2026-09-10 the bundles were missing three
pages entirely and still carried esapp 0.1.x behaviour that the source pages had
already corrected. Run this after editing any page.

    python build_dist.py

Output (byte-for-byte the shape the previous hand-built bundles used):
  dist/powerworld-hivemind-bundle.md      AGENTS + index + all four directories
  dist/powerworld-hivemind-<dir>.md       one per directory, basenames only
  dist/powerworld-hivemind-skill.zip      powerworld/ skill tree
"""

import io
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIST = ROOT / "dist"
DIRS = ["demos", "methods", "concepts", "references"]

BUNDLE_HEADER = """# PoWerHiveMind - complete knowledge bundle

Single-file bundle of the PoWerHiveMind knowledge base for chat tools that
cannot clone a repository. Source: https://github.com/ChunSikPark/PoWerHiveMind

NOTE: a chat interface cannot open your .pwb, run Python, or reach SimAuto. Use
this to have it WRITE code that you then run yourself.

---
"""

SEP = "\n\n\n---\n\n"


def read(p: Path) -> str:
    return io.open(p, encoding="utf-8").read().rstrip("\n")


def pages(d: str):
    return sorted((ROOT / d).glob("*.md"), key=lambda p: p.name)


def section(label: str, body: str) -> str:
    return f"# ==== {label} ====\n\n{body}"


def write(path: Path, text: str) -> None:
    io.open(path, "w", encoding="utf-8", newline="\n").write(text)
    print(f"  {path.relative_to(ROOT)}  ({len(text):,} bytes)")


def build_bundle() -> int:
    parts = [section("AGENTS.md", read(ROOT / "AGENTS.md")),
             section("index.md", read(ROOT / "index.md"))]
    for d in DIRS:
        for p in pages(d):
            parts.append(section(f"{d}/{p.name}", read(p)))
    write(DIST / "powerworld-hivemind-bundle.md",
          BUNDLE_HEADER + "\n" + SEP.join(parts) + "\n\n\n---\n")
    return len(parts)


def build_dir_bundle(d: str) -> int:
    parts = [section(p.name, read(p)) for p in pages(d)]
    write(DIST / f"powerworld-hivemind-{d}.md",
          f"# PoWerHiveMind - {d.upper()}\n\n" + SEP.join(parts) + "\n\n\n---\n")
    return len(parts)


def build_skill_zip() -> int:
    src = ROOT / "skills" / "powerworld"
    out = DIST / "powerworld-hivemind-skill.zip"
    entries = []
    with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
        skill_md = src / "SKILL.md"
        if skill_md.exists():
            z.write(skill_md, "powerworld/SKILL.md")
            entries.append("powerworld/SKILL.md")
        for name in ("AGENTS.md", "index.md"):
            z.write(ROOT / name, f"powerworld/{name}")
            entries.append(f"powerworld/{name}")
        for d in DIRS:
            for p in pages(d):
                arc = f"powerworld/{d}/{p.name}"
                z.write(p, arc)
                entries.append(arc)
    print(f"  {out.relative_to(ROOT)}  ({len(entries)} entries)")
    return len(entries)


if __name__ == "__main__":
    DIST.mkdir(exist_ok=True)
    print("Rebuilding dist/ ...")
    n = build_bundle()
    for d in DIRS:
        build_dir_bundle(d)
    build_skill_zip()
    total = sum(len(pages(d)) for d in DIRS)
    print(f"Done. {total} pages across {len(DIRS)} directories; "
          f"bundle carries {n} sections (pages + AGENTS.md + index.md).")
