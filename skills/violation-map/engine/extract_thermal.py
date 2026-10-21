"""Branch loading for the thermal view: nothing out, and after every outage. Read-only: nothing is saved.

    python extract_thermal.py <config.json>             -> thermal_<state>_<scenario>.json for every state x scenario
    python extract_thermal.py <config.json> <st> <sc>   -> just that one

Needs topo.json (extract.py topo): loadings are kept for the drawn branches only.

The outage list is the case's own contingencies plus, by default, one outage for every in-service
drawn branch at or above min_net_kv that the case's list does not already open on its own
(`thermal.outages`: "case+area" | "case"). A shipped list is usually built for one area
and before the study's new devices existed, so without the area outages a new line is never tripped.

Each outage is applied with CTGApply, solved, read, and undone with CTGRestoreReference plus a
re-solve; every undo is fingerprinted against the base loadings and the run stops if it drifts.
Loading is the higher end's MVA over the rating in use: the normal rating with nothing out
(LineMaxPercent), the contingency rating after an outage (LineLimMVA:1). Afterwards CTGSolveAll
runs on the same list: every ViolationCTG thermal row must agree with the per-outage loading,
and every per-outage overload on a monitored branch must have a ViolationCTG row, so the two paths
check each other both ways.
"""
import json

import vmap

cfg, OUT = vmap.load_config()
A = vmap.args()
TH = cfg["thermal"]
frame = vmap.frame
TOL = 1.0                        # percentage points allowed between the two paths
KEEP_DELTA = 0.5                 # an outage stores a branch only if it moved this much, or sits near the band
KEYS = ["BusNum", "BusNum:1", "LineCircuit"]
POST = KEYS + ["LineStatus", "LineMW", "LineMVA", "LineMVA:1", "LineLimMVA:1"]
if TH["outages"] not in ("case+area", "case"):
    raise SystemExit(f'thermal.outages is {TH["outages"]!r}; use "case+area" (default) or "case"')


def bkey(f, t, c):
    return f"{int(f)}-{int(t)}-{c}"


def post_rows(E, idx):
    """Per drawn branch after an outage: [mw, mva, pct] against the contingency rating, None when open."""
    d = frame(E, "Branch", POST, ["BusNum", "BusNum:1", "LineMW", "LineMVA", "LineMVA:1", "LineLimMVA:1"])
    out = {}
    for r in d.itertuples(index=False):
        i = idx.get(bkey(r[0], r[1], r[2]))
        if i is None:
            continue
        if r[3] != "Closed":
            out[i] = None
            continue
        mva, lim = max(r[5], r[6]), r[7]
        out[i] = [round(r[4], 1), round(mva, 1), round(mva / lim * 100, 1) if lim and lim > 0 else None]
    return out


def fingerprint(E, idx):
    d = frame(E, "Branch", KEYS + ["LineMaxPercent"], ["BusNum", "BusNum:1", "LineMaxPercent"])
    return {idx[k]: p for k, p in zip((bkey(a, b, c) for a, b, c in zip(d.BusNum, d["BusNum:1"], d.LineCircuit)), d.LineMaxPercent)
            if k in idx}


def run(which, sce):
    T = json.load(open(OUT / "topo.json"))
    BR = T["branches"]
    idx = {bkey(b["f"], b["t"], b["ckt"]): i for i, b in enumerate(BR)}
    kv = {b["num"]: b["kv"] for b in T["buses"]}
    pw = vmap.open_case(vmap.case_path(cfg, sce, which))
    try:
        E = pw.esa
        ls = frame(E, "LimitSet", ["LSName", "LSAmpMVA", "LSLineRateSet", "LSLineRateSet:1", "LSDisabled", "LSLinePercent"], ["LSLinePercent"])
        amp = ls[(ls.LSDisabled != "YES") & (ls.LSAmpMVA != "MVA")]
        if len(amp):
            raise SystemExit(f"limit set(s) {list(amp.LSName)} rate branches in amps; the thermal view reads MVA "
                             "ratings only and would mis-score them. Not built for amp ratings yet.")
        rates = sorted(set(ls.LSLineRateSet) | set(ls["LSLineRateSet:1"]))
        report_pct = float(ls[ls.LSDisabled != "YES"].LSLinePercent.max())   # ViolationCTG reports only above this

        # ---- nothing out, solved in AC -- the case may have been saved with other options
        E.SetData("Sim_Solution_Options", ["DCApprox"], ["NO"])
        E.SolvePowerFlow()
        d = frame(E, "Branch", KEYS + ["LineStatus", "LineMW", "LineMVA", "LineMVA:1", "LineMaxPercent", "LineLimMVA", "LineLimMVA:1", "LineMonEle:1"],
                  ["BusNum", "BusNum:1", "LineMW", "LineMVA", "LineMVA:1", "LineMaxPercent", "LineLimMVA", "LineLimMVA:1"])
        base, found, monitored = [None] * len(BR), set(), set()   # base row: [mw, mva, % of normal rating, normal rating, contingency rating]
        for r in d.itertuples(index=False):
            i = idx.get(bkey(r[0], r[1], r[2]))
            if i is not None:
                found.add(i)
                if r[10] == "YES":                # the effective monitoring flag, after area and kV filters
                    monitored.add(i)
                if r[3] == "Closed":
                    base[i] = [round(r[4], 1), round(max(r[5], r[6]), 1), round(r[7], 1), round(r[8], 1), round(r[9], 1)]
        assert len(found) == len(BR), f"{len(BR) - len(found)} drawn branches are not in this case -- re-run extract.py topo"

        # ---- the outage list: the case's own, plus the drawn branches it does not open
        ctg = frame(E, "Contingency", ["CTGLabel", "CTGSkip"], [])
        el = frame(E, "ContingencyElement", ["CTGLabel", "Object", "Action"], [])
        case_labels = [l for l, s in zip(ctg.CTGLabel, ctg.CTGSkip) if s != "YES"]
        # a branch counts as covered only by a case outage that runs and opens that branch alone; one inside
        # a skipped or multi-element contingency still gets its own single outage
        n_el, runs = el.CTGLabel.value_counts(), set(case_labels)
        opened = set()
        for lab, o, act in zip(el.CTGLabel, el.Object, el.Action):
            p = o.split()
            if lab in runs and n_el[lab] == 1 and act.upper() == "OPEN" and p[0] == "BRANCH" and len(p) >= 4:
                opened.add((min(int(p[1]), int(p[2])), max(int(p[1]), int(p[2])), p[3]))
        added = []
        drawn = {int(s) for a in T["areas"].values() for s, h in a["hop"].items() if h <= T["max_hops"]}   # not the geometry ring
        if TH["outages"] == "case+area":
            for i, b in enumerate(BR):
                k = (min(b["f"], b["t"]), max(b["f"], b["t"]), b["ckt"])
                if b["sf"] not in drawn or b["st"] not in drawn:
                    continue
                if base[i] and not b["w"] and min(kv[b["f"]], kv[b["t"]]) >= cfg["min_net_kv"] and k not in opened:
                    added.append((f"VMAP_{b['f']}_{b['t']}_{b['ckt']}", b["f"], b["t"], b["ckt"]))
        if added:
            aux = (OUT / f"area_outages_{which}_{sce}.aux").resolve()       # LoadAux resolves a relative path against pwrworld.exe
            with open(aux, "w", encoding="utf-8") as fh:
                fh.write("Contingency (CTGLabel,CTGSkip)\n{\n")
                for lab, f, t, c in added:            # the action string must be quoted, or only the first record loads
                    fh.write(f'"{lab}" "NO"\n   <SUBDATA CTGElement>\n     "BRANCH {f} {t} {c} OPEN" "" CHECK 0 NO\n   </SUBDATA>\n')
                fh.write("}\n")
            E.RunScriptCommand("EnterMode(EDIT);")
            E.RunScriptCommand(f'LoadAux("{aux.as_posix()}", NO);')
            E.RunScriptCommand("EnterMode(RUN);")
            el = frame(E, "ContingencyElement", ["CTGLabel", "Object", "Action"], [])
            got = el[el.CTGLabel.isin({a[0] for a in added})]
            assert len(got) == len(added) and set(got.CTGLabel) == {a[0] for a in added}, \
                f"wrote {len(added)} area outages, {len(got)} elements loaded -- the aux did not load as written"
        labels = case_labels + [a[0] for a in added]
        if not labels:
            raise SystemExit("no outages to run: the case has no contingencies and no drawn branch qualified")
        elements, want = {}, set(labels)
        for r in el.itertuples(index=False):
            if r.CTGLabel in want:
                p = r.Object.split()
                e = (dict(kind="branch", f=int(p[1]), t=int(p[2]), ckt=p[3]) if p[0] == "BRANCH" else
                     dict(kind="gen", bus=int(p[1]), id=p[2]) if p[0] == "GEN" else dict(kind=p[0].lower(), obj=r.Object))
                e["action"] = r.Action
                elements.setdefault(r.CTGLabel, []).append(e)

        # ---- every outage, one at a time, each undone and fingerprinted
        E.SolvePowerFlow()
        E.CTGSetAsReference()
        fp0 = fingerprint(E, idx)
        moved = [i for i, b in enumerate(base) if b and fp0.get(i) == fp0.get(i) and abs(b[2] - fp0[i]) > 0.1]
        assert not moved, f"{len(moved)} base loadings changed between two solves of the same case -- the base is not settled"
        post, solved = [], []
        for n, lab in enumerate(labels):
            try:
                E.CTGApply(lab)
                ok = vmap.solve(E)
            except Exception:
                ok = False
            rows = post_rows(E, idx) if ok else {}
            E.CTGRestoreReference()
            E.SolvePowerFlow()                    # the restore puts inputs back; the solve puts the flows back
            fp = fingerprint(E, idx)
            drift = max((abs(fp[i] - fp0[i]) for i in fp0 if fp0[i] == fp0[i] and fp.get(i) == fp.get(i)), default=0)
            if drift > 0.01:
                raise SystemExit(f"after undoing {lab!r} the base loadings moved {drift:.3f} points -- the undo did not restore the case")
            post.append(rows)
            solved.append(ok)
            if (n + 1) % 50 == 0:
                print(f"  {which} {sce}: {n + 1}/{len(labels)} outages")

        # ---- the second path: CTGSolveAll + ViolationCTG, which must agree on every thermal row we draw
        E.SetData("CTG_Options", ["CTG_CalculationMethod"], ["AC"])
        got = E.GetParametersSingleElement("CTG_Options", ["CTG_CalculationMethod"], [""])["CTG_CalculationMethod"]
        assert str(got).strip().upper() == "AC", f"CTG_CalculationMethod reads {got!r}, not AC"
        E.CTGClearAllResults()                    # results persist in the .pwb; clear before every solve
        E.CTGSolveAll()
        cs = frame(E, "Contingency", ["CTGLabel", "CTGSolved", "LoadMW"], ["LoadMW"]).set_index("CTGLabel")
        vf = ["CTGLabel", "LimViolCat", "LimViolPct", "LimViolValue", "LimViolLimit", "BusNum", "BusNum:1", "LineCircuit"]
        vc = frame(E, "ViolationCTG", vf, ["LimViolPct", "LimViolValue", "LimViolLimit"])
    finally:
        vmap.close_case(pw)

    stale = set(vc.CTGLabel) - set(labels)
    assert not stale, f"ViolationCTG has rows for {len(stale)} label(s) that were not solved -- stale results"
    th = vc[vc.LimViolCat.isin(["Branch MVA", "Branch Amp"])]
    li = {l: n for n, l in enumerate(labels)}
    bad, checked, seen = [], 0, set()
    for r in th.itertuples(index=False):
        i = idx.get(bkey(r.BusNum, r._6, r.LineCircuit)) if r.BusNum and r._6 else None
        if i is None:
            i = idx.get(bkey(r._6, r.BusNum, r.LineCircuit)) if r.BusNum and r._6 else None
        if i is None:
            continue
        n = li[r.CTGLabel]
        mine = post[n].get(i)
        ours = mine[2] if mine else None         # None: our solve of this outage failed, or the branch read open
        checked += 1
        seen.add((n, i))
        if ours is None or abs(ours - r.LimViolPct) > TOL:
            bad.append((r.CTGLabel, BR[i]["f"], BR[i]["t"], BR[i]["ckt"], r.LimViolPct, ours if solved[n] else "our solve failed"))
    # the other way round: an overload we found on a monitored branch must be one PowerWorld reported
    unmonitored = []
    for n, rows in enumerate(post):
        for i, v in rows.items():
            if v and v[2] is not None and v[2] >= report_pct + TOL and (n, i) not in seen:
                if i in monitored:
                    bad.append((labels[n], BR[i]["f"], BR[i]["t"], BR[i]["ckt"], "no ViolationCTG row", v[2]))
                else:
                    unmonitored.append([labels[n], BR[i]["f"], BR[i]["t"], BR[i]["ckt"], v[2]])
    if bad:
        for b in bad[:12]:
            print("  disagree:", b)
        raise SystemExit(f"{len(bad)} thermal results disagree between the per-outage loading and ViolationCTG ({checked} rows "
                         f"compared, tolerance {TOL} points) -- the two paths solved different cases; do not trust either")
    for u in unmonitored:
        print(f"  not monitored by the case, so PowerWorld did not report it: {u[1]}-{u[2]} #{u[3]} at {u[4]:.1f}% after {u[0]}")
    split = [l for n, l in enumerate(labels) if bool(solved[n]) != (str(cs.CTGSolved.get(l, "")).strip() == "YES")]
    for l in split:
        print(f"  solved by one path only: {l} (ours {'yes' if solved[li[l]] else 'no'})")

    # ---- worst post-outage loading per branch, and the outage behind it
    worst = [None] * len(BR)
    for n, rows in enumerate(post):
        if not solved[n]:
            continue
        for i, v in rows.items():
            if v and v[2] is not None and (worst[i] is None or v[2] > worst[i][0]):
                worst[i] = [v[2], n, v[0], v[1]]
    sparse = []                                   # the page falls back to the base value for a branch an outage did not store
    for n, rows in enumerate(post):
        keep = {}
        for i, v in rows.items():
            b = base[i]
            if v is None or b is None:
                if (v is None) != (b is None):
                    keep[i] = v
                continue
            bpct = round(b[1] / b[4] * 100, 1) if b[4] else b[2]
            if v[2] is None or abs(v[2] - bpct) >= KEEP_DELTA or v[2] >= TH["near"] - 1:
                keep[i] = v
        sparse.append(keep)
    # LoadMW is the load an outage cuts off. PowerWorld leaves it blank for zero: measured 2026-10-21, blank on
    # every outage of a run whose GenMW column carried numbers on the outages that lost generation
    lost = lambda x: 0.0 if x is None or x != x else round(float(x), 1)
    outs = [dict(label=l, added=l.startswith("VMAP_"), elements=elements.get(l, []), solved=bool(solved[n]),
                 ctg_solved=str(cs.CTGSolved.get(l, "")).strip() == "YES",
                 lost_mw=lost(cs.LoadMW.get(l)))
            for n, l in enumerate(labels)]
    res = dict(scenario=sce, set=which, rate_sets=rates, near=TH["near"], over=TH["over"], keep_delta=KEEP_DELTA,
               base=base, outages=outs, post=[{str(i): v for i, v in s.items()} for s in sparse], worst=worst,
               keys=list(idx), check=dict(violationctg_rows=checked, case_outages=len(case_labels), area_outages=len(added),
                                          unmonitored=unmonitored, solved_by_one_path=split))
    vmap.dump(OUT / f"thermal_{which}_{sce}.json", res)
    over = sum(1 for w in worst if w and vmap.thermal_band(w[0], TH) == "over")
    near = sum(1 for w in worst if w and vmap.thermal_band(w[0], TH) == "near")
    print(f"{which} {sce}: {len(labels)} outages ({len(case_labels)} from the case, {len(added)} added for the drawn area), "
          f"{sum(1 for s in solved if not s)} unsolved; worst case per line: {over} overloaded, {near} at "
          f"{TH['near']:g}-{TH['over']:g}%; {checked} ViolationCTG thermal rows agree within {TOL} points")
    top = sorted((w[0], i, w[1]) for i, w in enumerate(worst) if w)[::-1][:5]
    for p, i, n in top:
        print(f"  {BR[i]['f']}-{BR[i]['t']} #{BR[i]['ckt']}: {p:.1f}% after {labels[n]}")


if A and len(A) >= 2:
    run(A[0], A[1])
elif A:
    raise SystemExit(__doc__)
else:
    for st in cfg["states"]:
        for sc in vmap.scenario_keys(cfg):
            run(st["key"], sc)
