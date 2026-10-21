"""Shared helpers for the violation-map engine: config, case access, and small geometry.

Every script in this folder takes the config path as its first argument, or reads it from
the VMAP_CONFIG environment variable. All outputs land in the config's `out_dir`, resolved
relative to the config file, so one config is one study and nothing is written next to the
engine itself.
"""
import json
import math
import os
import sys
from pathlib import Path

import pandas as pd

num = lambda s: pd.to_numeric(s, errors="coerce")

DEFAULTS = {
    "title": "Violation map",
    "out_dir": "vmap_out",
    "band": {"lo": 0.94, "hi": 1.05, "post_lo": 0.90, "post_hi": 1.10},
    "min_net_kv": 69,
    "exclude_bus_prefixes": ["GSU_", "STR_", "TERT_"],
    "hops": 5,
    "radial": {"min_kv": 138, "reach_mi": 60, "reach_max_mi": 90,
               "exclude_landing_name_parts": ["LargeLoad", "DataCenter", "Data_Center", "DC_"]},
    "thermal": {"over": 100, "near": 90, "outages": "case+area"},
}


def thermal_band(pct, th):
    """'over' at or above th['over'] % of the rating in use, 'near' from th['near'] up to it, else 'ok'.
    template.html's tBand() is the same rule; test_thermal.py holds the two together."""
    if pct is None or pct != pct:
        return "ok"
    return "over" if pct >= th["over"] else "near" if pct >= th["near"] else "ok"


def load_config(argv=None):
    """Return (cfg, out_dir). The config path is argv[1] or $VMAP_CONFIG."""
    argv = sys.argv if argv is None else argv
    path = argv[1] if len(argv) > 1 and argv[1].endswith(".json") else os.environ.get("VMAP_CONFIG")
    if not path:
        sys.exit("usage: python <script>.py <config.json> [...]   (or set VMAP_CONFIG)")
    path = Path(path).resolve()
    cfg = json.load(open(path, encoding="utf-8"))
    for k, v in DEFAULTS.items():
        if isinstance(v, dict):
            cfg[k] = {**v, **cfg.get(k, {})}
        else:
            cfg.setdefault(k, v)
    for s in cfg["scenarios"]:
        s.setdefault("label", s["key"])
        s.setdefault("short", s["label"][:6])
    for st in cfg["states"]:
        st.setdefault("label", st["key"])
        missing = [s["key"] for s in cfg["scenarios"] if s["key"] not in st["cases"]]
        if missing:
            sys.exit(f"state {st['key']!r} has no case for scenario(s) {missing}")
    out = (path.parent / cfg["out_dir"]).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return cfg, out


def args(argv=None):
    """Positional arguments after the config path."""
    argv = sys.argv if argv is None else argv
    return [a for a in argv[1:] if not a.endswith(".json")]


def scenario_keys(cfg):
    return [s["key"] for s in cfg["scenarios"]]


def case_path(cfg, scenario, state=None):
    """Absolute case path. `state` defaults to the first (base) state."""
    st = next(s for s in cfg["states"] if s["key"] == (state or cfg["states"][0]["key"]))
    p = os.path.abspath(st["cases"][scenario])            # PowerWorld resolves relative paths
    if not os.path.exists(p):                             # against its own directory, not ours
        sys.exit(f"case not found: {p}")
    return p


def open_case(path):
    """Open and solve a case. Pair every call with close_case() in a finally block."""
    from esapp import PowerWorld
    pw = PowerWorld(path)
    try:
        pw.esa.SolvePowerFlow()
    except Exception:
        close_case(pw)                  # the caller never gets pw, so its finally cannot exit it
        raise
    return pw


def close_case(pw):
    """esa.exit() releases the Simulator process. `del pw` alone leaves one running per open."""
    try:
        pw.esa.exit()
    except Exception:
        pass


def solve(E):
    """Solve; on failure retry once from a flat start seeded by a DC solve. Returns True if solved."""
    try:
        E.SolvePowerFlow()
        return True
    except Exception:
        try:
            E.ResetToFlatStart()
            E.SolvePowerFlow("DC")
            E.SolvePowerFlow()
            return True
        except Exception:
            return False


def set_branch(E, f, t, ckt, status):
    """Open or close one branch by its full key, trying both bus orders."""
    keys = ["BusNum", "BusNum:1", "LineCircuit", "LineStatus"]
    for a, b in ((f, t), (t, f)):
        try:
            E.ChangeParametersSingleElement("Branch", keys, [a, b, str(ckt), status])
            got = E.GetParametersSingleElement("Branch", keys, [a, b, str(ckt), ""])
            if str(got["LineStatus"]).strip().lower() == status.lower():    # assert the effect
                return True
        except Exception:
            continue
    return False


def frame(E, obj, fields, numeric):
    d = E.GetParametersMultipleElement(obj, fields)
    for c in d.columns:
        d[c] = num(d[c]) if c in numeric else d[c].astype(str).str.strip()
    return d


def kv_class(kv):
    return 765 if kv >= 700 else 345 if kv >= 300 else 138 if kv >= 100 else 69


def net_bus(cfg):
    """Network bus test: at or above min_net_kv and not a step-up, star-point or tertiary bus."""
    lo, pre = cfg["min_net_kv"], tuple(cfg["exclude_bus_prefixes"])
    return lambda b: b["kv"] >= lo and not b["name"].startswith(pre)


def miles(lat1, lon1, lat2, lon2):
    p1, p2, dl = map(math.radians, (lat1, lat2, lon2 - lon1))
    h = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 3958.8 * 2 * math.asin(math.sqrt(h))


def place_star_buses(topo):
    """Three-winding star buses carry no substation: put each in the substation its windings reach."""
    B = {b["num"]: b for b in topo["buses"]}
    for br in topo["branches"]:
        if br["w"]:
            f, t = B[br["f"]], B[br["t"]]
            if f["sub"] is None and t["sub"] is not None:
                f["sub"] = t["sub"]
            if t["sub"] is None and f["sub"] is not None:
                t["sub"] = f["sub"]
    return B


def clean(o):
    """NaN/inf -> None, recursively. One NaN in the page data makes JSON.parse throw and the page blank."""
    if isinstance(o, float):
        return o if math.isfinite(o) else None
    if isinstance(o, dict):
        return {k: clean(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [clean(v) for v in o]
    return o


def dump(path, obj):
    json.dump(clean(obj), open(path, "w", encoding="utf-8"), separators=(",", ":"), allow_nan=False)


def inject(template, data, out_path):
    """Write the page: the template with its /*__DATA__*/ slot replaced by the data JSON."""
    html = template.read_text(encoding="utf-8").replace(
        "/*__DATA__*/", json.dumps(clean(data), separators=(",", ":"), allow_nan=False).replace("</", "<\\/"))
    out_path.write_text(html, encoding="utf-8")
    return len(html)
