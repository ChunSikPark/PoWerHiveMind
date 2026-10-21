"""Assemble the voltage page from topo.json + state_*.json (+ design_meas_*.json when present). Offline.

    python build.py <config.json>        -> <out_dir>/voltage_map.html
"""
import json
from pathlib import Path

import vmap

cfg, OUT = vmap.load_config()
HERE = Path(__file__).parent
SCES = vmap.scenario_keys(cfg)
SETS = [s["key"] for s in cfg["states"]]
BAND = cfg["band"]

T = json.load(open(OUT / "topo.json"))
H = T["max_hops"]
keep = {int(s) for a in T["areas"].values() for s, h in a["hop"].items() if h <= H}
subs = [s for s in T["subs"] if s["id"] in keep]
buses = [b for b in T["buses"] if b["sub"] in keep]
bset = {b["num"] for b in buses}
branches = [b for b in T["branches"] if b["sf"] in keep and b["st"] in keep]
gens = [g for g in T["gens"] if g["bus"] in bset]
shunts = [h for h in T["shunts"] if h["bus"] in bset]
areas = {k: dict(title=a["title"], roots=a["roots"], default_hops=min(H, int(cfg["areas"][k].get("default_hops", H))),
                 hop={s: h for s, h in a["hop"].items() if h <= H}) for k, a in T["areas"].items()}

states = {}
for w in SETS:
    for sc in SCES:
        d = json.load(open(OUT / f"state_{w}_{sc}.json"))
        states[f"{w}|{sc}"] = dict(
            v=[d["v"].get(str(b["num"])) for b in buses],
            br=[d["br"].get(f"{b['f']}-{b['t']}-{b['ckt']}") for b in branches],
            gen=[d["gen"].get(f"{g['bus']}-{g['id']}") for g in gens],
            sh=[d["sh"].get(f"{h['bus']}-{h['id']}") for h in shunts],
            load=[d["load"].get(str(b["num"])) for b in buses])
        miss = sum(x is None for x in states[f"{w}|{sc}"]["br"])
        assert miss == 0, f"{w} {sc}: {miss} branches have no state -- the cases do not share a topology, or the keys drifted"

data = dict(title=cfg["title"], max_hops=H, band=BAND, min_net_kv=cfg["min_net_kv"], exclude_prefixes=cfg["exclude_bus_prefixes"],
            scenarios=cfg["scenarios"], sets=[dict(key=s["key"], label=s["label"]) for s in cfg["states"]],
            areas=areas, subs=subs, buses=buses, branches=branches, gens=gens, shunts=shunts, states=states)

# ---- thermal view (optional): thermal_<state>_<scenario>.json from extract_thermal.py, re-indexed to the page's branches
TF = {(w, sc): OUT / f"thermal_{w}_{sc}.json" for w in SETS for sc in SCES}
if all(p.exists() for p in TF.values()):
    TH = cfg["thermal"]
    page_i = {(b["f"], b["t"], b["ckt"]): i for i, b in enumerate(branches)}
    to_page = [page_i.get((b["f"], b["t"], b["ckt"])) for b in T["branches"]]     # topo index -> page index (None: geometry ring)
    BN = {b["num"]: b for b in T["buses"]}
    SN = {s["id"]: s["name"] for s in T["subs"]}
    where = lambda bus: SN.get(BN[bus]["sub"], str(bus)) if bus in BN else f"bus {bus}"

    def outage_name(o):
        parts = []
        for e in o["elements"]:
            if e["kind"] == "branch":
                parts.append(f"{where(e['f'])} – {where(e['t'])} #{e['ckt']}")
            elif e["kind"] == "gen":
                parts.append(f"generator at {where(e['bus'])} #{e['id']}")
            else:
                parts.append(e.get("obj", e["kind"]))
        return "Lose " + " + ".join(parts) if parts else o["label"]

    th_states = {}
    for (w, sc), p in TF.items():
        d = json.load(open(p, encoding="utf-8"))
        assert d.get("keys") == [f"{b['f']}-{b['t']}-{b['ckt']}" for b in T["branches"]], \
            f"{p.name} was extracted against a different topo.json -- re-run extract_thermal.py"
        base_p, worst_p = [None] * len(branches), [None] * len(branches)
        for ti, pi in enumerate(to_page):
            if pi is not None:
                base_p[pi], worst_p[pi] = d["base"][ti], d["worst"][ti]
        post_p = [{str(to_page[int(k)]): v for k, v in s.items() if to_page[int(k)] is not None} for s in d["post"]]
        outs = []
        for o in d["outages"]:
            opens = [e for e in o["elements"] if e["action"].upper() == "OPEN"]     # only an OPEN element is drawn as out
            trip = [page_i[k] for e in opens if e["kind"] == "branch"
                    for k in ((e["f"], e["t"], e["ckt"]), (e["t"], e["f"], e["ckt"])) if k in page_i]
            gens_out = [e["bus"] for e in opens if e["kind"] == "gen"]
            outs.append(dict(label=o["label"], name=outage_name(o), added=o["added"], solved=o["solved"],
                             lost_mw=o["lost_mw"], trip=trip, gens=gens_out))
        # found by the run but on a branch past the drawn hops: named on the page, never silently dropped
        outside = sorted(([x[0], f"{where(b['f'])} – {where(b['t'])} #{b['ckt']}", outs[x[1]]["name"]]
                          for b, x, pi in zip(T["branches"], d["worst"], to_page)
                          if pi is None and x and vmap.thermal_band(x[0], TH) != "ok"), reverse=True)
        th_states[f"{w}|{sc}"] = dict(base=base_p, worst=worst_p, post=post_p, outages=outs, rate_sets=d["rate_sets"],
                                      keep_delta=d["keep_delta"], check=d["check"], outside=outside)
        n_over = sum(1 for x in worst_p if x and vmap.thermal_band(x[0], TH) == "over")
        n_near = sum(1 for x in worst_p if x and vmap.thermal_band(x[0], TH) == "near")
        print(f"thermal {w} {sc}: {len(outs)} outages; worst case per line on the page: {n_over} overloaded, {n_near} near")
    data["thermal"] = dict(over=TH["over"], near=TH["near"], states=th_states)
elif any(p.exists() for p in TF.values()):
    print("thermal_*.json missing for some state x scenario -- page built without the thermal view")


def watch_excess(o, post):
    """How far the watched buses sit outside their band (<= 0 is inside), or None."""
    if not o or not o.get("solved") or o.get("watch") is None:
        return None
    hi, lo = (BAND["post_hi"], BAND["post_lo"]) if post else (BAND["hi"], BAND["lo"])
    return max(o["watch"] - hi, lo - o["watch_min"])


DZ = cfg.get("designs")
mf = [OUT / f"design_meas_{sc}.json" for sc in SCES]
if DZ and all(p.exists() for p in mf):
    idx = {b["num"]: i for i, b in enumerate(buses)}
    B = {b["num"]: b for b in T["buses"]}
    S = {s["id"]: s for s in T["subs"]}
    brk = {(b["f"], b["t"], b["ckt"]): b for b in T["branches"]}
    cands = [dict(name="As built", short="As built", kind="none")]
    for c in DZ["candidates"]:
        d = dict(name=c["name"], kind=c["kind"], short=c.get("short", c["name"]))
        if c["kind"] == "line":
            f, t = B.get(c["from_bus"]), B.get(c["to_bus"])
            tm = brk.get((c["template"][0], c["template"][1], str(c["template"][2])))
            d.update(from_bus=c["from_bus"], to_bus=c["to_bus"], fid=f and f["sub"], tid=t and t["sub"], kv=f and f["kv"],
                     mi=c.get("miles") or (round(vmap.miles(S[f["sub"]]["lat"], S[f["sub"]]["lon"], S[t["sub"]]["lat"], S[t["sub"]]["lon"]), 1)
                                           if f and t else None),
                     tmpl_name=f"{S[tm['sf']]['name']} – {S[tm['st']]['name']}" if tm else f"{c['template'][0]}–{c['template'][1]}",
                     tmpl_mi=tm and tm["mi"], tmpl_rate=tm and tm["rate"])
        elif c["kind"] == "shunt":
            d.update(bus=c["bus"], mvar=c["mvar"])
        cands.append(d)
    ar = T["areas"][DZ["area"]]
    area_subs = {int(s) for s, h in ar["hop"].items() if h <= H}
    area_nums = [b["num"] for b in T["buses"] if b["sub"] in area_subs]   # the order measure_designs.py writes in
    res = {}
    for sc, p in zip(SCES, mf):
        R = json.load(open(p, encoding="utf-8"))["results"]
        assert [r["name"] for r in R] == [d["name"] for d in cands], f"{sc}: candidate list drifted -- re-run measure_designs.py"
        for r in R:
            if "error" in r:
                continue
            r["v"] = {k: [r[k]["v"].get(str(n)) for n in area_nums] for k in ["n0"] + [o["key"] for o in DZ.get("outages", [])]
                      if isinstance(r.get(k), dict) and "v" in r[k]}
            for k in list(r):
                if isinstance(r[k], dict):
                    r[k].pop("v", None)
        res[sc] = R
    OK = [o["key"] for o in DZ.get("outages", [])]

    def agg(di):
        rs = [res[sc][di] for sc in SCES]
        if any("error" in r for r in rs):
            return None
        n0 = [watch_excess(r["n0"], False) for r in rs]
        post = [watch_excess(r.get(k), True) for r in rs for k in OK]
        return dict(bad=sum(1 for x in n0 if x is None or x > 0), worst=max((x for x in n0 if x is not None), default=9.0),
                    post_bad=sum(1 for x in post if x is None or x > 0),
                    isl=sum(1 for r in rs for k in OK if (r.get(k) or {}).get("islanded")),
                    nout=sum(r["n0"].get("n_out") or 0 for r in rs if r["n0"].get("solved")))
    base = agg(0)
    nsc, npost = len(SCES), len(SCES) * len(OK)
    rank = []
    for di in range(1, len(cands)):
        a = agg(di)
        if a is None:
            continue
        vs = ("clears the watched buses" if a["bad"] == 0 and a["post_bad"] == 0 else
              "worse" if a["worst"] > base["worst"] + 1e-4 else
              "reduces" if a["worst"] < base["worst"] - 0.005 else "no change")
        verdict = vs if not (base["isl"] or a["isl"]) else vs + " · " + (
            "fixes islanding" if a["isl"] == 0 else "partly fixes islanding" if a["isl"] < base["isl"] else "islanding not fixed")
        cls = ("good" if vs.startswith("clears") and a["isl"] == 0 else
               "bad" if vs in ("worse", "no change") else "part")
        note = (f"{DZ.get('watch_label', 'watched buses')} out of band at N-0 in {a['bad']}/{nsc} dispatches (as built {base['bad']}/{nsc})"
                + (f" · after an outage {a['post_bad']}/{npost} (as built {base['post_bad']}/{npost}) · islanding in {a['isl']}/{npost}"
                   f" (as built {base['isl']}/{npost})" if OK else "")
                + f" · whole area: {a['nout']} bus-dispatches out of band (as built {base['nout']})")
        rank.append(dict(di=di, verdict=verdict, cls=cls, note=note, key=(a["bad"] + a["post_bad"], a["isl"], a["worst"], a["nout"])))
    rank.sort(key=lambda r: r.pop("key"))
    watch = [int(x) for x in DZ.get("watch_buses", cfg["areas"][DZ["area"]]["seeds"])]
    data["designs"] = dict(area=DZ["area"], watch_label=DZ.get("watch_label", "watched buses"), outages=DZ.get("outages", []),
                           candidates=cands, res=res, rank=rank, area_idx=[idx[n] for n in area_nums],
                           focus_subs=sorted({B[n]["sub"] for n in watch if n in B}))
    print("designs ranked:", [(cands[r["di"]]["short"], r["verdict"]) for r in rank])
elif DZ:
    print("designs block present but design_meas_*.json missing for some scenario -- page built without the designs panel")

page = OUT / ("thermal_map.html" if "thermal" in data else "voltage_map.html")   # a thermal page opens on thermal, voltage one switch away
size = vmap.inject(HERE / "template.html", data, page)
print(f"{len(subs)} subs, {len(buses)} buses, {len(branches)} branches, {len(gens)} gens, {len(shunts)} shunts; "
      f"{size / 1e6:.1f} MB -> {page}")
