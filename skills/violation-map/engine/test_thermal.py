"""The thermal colour thresholds, checked in both places they live: vmap.thermal_band (Python, used
for the counts the engine prints) and tBand in template.html (the colour on the page).

    python test_thermal.py          (node on PATH checks the page's rule too; without it that half is skipped, and says so)
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import vmap

HERE = Path(__file__).parent
# (pct, thresholds, expected): red at or above `over`, orange from `near` up to it, grey below and for no value
CASES = [(100.0, (100, 90), "over"), (275.4, (100, 90), "over"), (99.99, (100, 90), "near"), (90.0, (100, 90), "near"),
         (89.99, (100, 90), "ok"), (0.0, (100, 90), "ok"), (None, (100, 90), "ok"), (float("nan"), (100, 90), "ok"),
         (95.0, (95, 80), "over"), (80.0, (95, 80), "near"), (79.9, (95, 80), "ok")]


def test_python():
    for pct, (over, near), want in CASES:
        got = vmap.thermal_band(pct, {"over": over, "near": near})
        assert got == want, f"thermal_band({pct}, over={over}, near={near}) = {got!r}, want {want!r}"


def test_page():
    node = shutil.which("node")
    if not node:
        print("SKIPPED page check: node not on PATH")
        return
    src = (HERE / "template.html").read_text(encoding="utf-8")
    m = re.search(r"^const tBand = .*?;\s*(//.*)?$", src, re.M)
    assert m, "tBand not found in template.html -- the page's threshold rule moved; update this test"
    cases = [[None if p is None or p != p else p, o, n, w] for p, (o, n), w in CASES]
    js = (f"{m.group(0)}\nlet TH; const bad = [];\nfor (const [p, o, n, w] of {json.dumps(cases)}) "
          "{ TH = {over: o, near: n}; const g = tBand(p); if (g !== w) bad.push([p, o, n, g, w]); }\n"
          "if (bad.length) { console.log(JSON.stringify(bad)); process.exit(1); }")
    r = subprocess.run([node, "-e", js], capture_output=True, text=True)
    assert r.returncode == 0, f"template tBand disagrees: {r.stdout or r.stderr}"


if __name__ == "__main__":
    test_python()
    test_page()
    print("thermal thresholds: ok")
