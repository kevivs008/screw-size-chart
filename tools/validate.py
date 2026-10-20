#!/usr/bin/env python3
"""Re-check the four datasets before commit. Exit non-zero on any failure."""
import json, os, sys
D = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
load = lambda n: json.load(open(os.path.join(D, n + ".json")))
imp, met, wood, drills = (load(n) for n in ("imperial-machine-screws", "metric-machine-screws", "wood-screws", "drill-bits"))
errs = []
def bad(m): errs.append(m)

for name, ds in (("imperial", imp), ("metric", met), ("wood", wood)):
    if not ds.get("meta", {}).get("lastVerified"): bad(f"{name}: meta.lastVerified missing")
for ds, n in ((imp, 20), (met, 17), (wood, 11)):
    if len(ds["rows"]) != n: bad(f"expected {n} rows, got {len(ds['rows'])}")

def need(row, fields, typ):
    for f in fields:
        if f not in row: bad(f"{row.get('label')}: missing {f}")
        elif typ.get(f) and row[f] is not None and not isinstance(row[f], typ[f]): bad(f"{row.get('label')}: {f} wrong type")
    if not row.get("source"): bad(f"{row.get('label')}: no source")
num = (int, float)
for r in imp["rows"]:
    need(r, ["label", "series", "majorDiameterIn", "majorDiameterMm", "unc", "unf", "clearance", "source"], {"majorDiameterIn": num, "majorDiameterMm": num})
    if not (r["unc"] or r["unf"]): bad(f"{r['label']}: no thread series")
for r in met["rows"]:
    need(r, ["label", "coarsePitch", "finePitches", "majorDiameterMm", "majorDiameterIn", "tapDrillCoarse", "clearance", "source"], {"coarsePitch": num, "majorDiameterMm": num, "tapDrillCoarse": num})
    if set(r["clearance"]) != {"fine", "medium", "coarse"}: bad(f"{r['label']}: clearance keys")
for r in wood["rows"]:
    need(r, ["label", "gauge", "majorDiameterIn", "pilotSoftwood", "pilotHardwood", "clearance", "assumption", "source"], {"majorDiameterIn": num})
    if abs(r["majorDiameterIn"] - (0.060 + 0.013 * r["gauge"])) > 0.0006: bad(f"{r['label']}: wood diameter formula")
for r in imp["rows"]:
    if r["series"] == "number" and abs(r["majorDiameterIn"] - (0.060 + 0.013 * int(r["label"][1:]))) > 0.0006: bad(f"{r['label']}: D=0.060+0.013n fails")

I = {r["label"]: r for r in imp["rows"]}; M = {r["label"]: r for r in met["rows"]}; W = {r["label"]: r for r in wood["rows"]}
def chk(c, m):
    if not c: bad("spot value failed: " + m)
chk(I["#8"]["majorDiameterIn"] == 0.164, "#8 = 0.164"); chk(I["#10"]["majorDiameterIn"] == 0.190, "#10 = 0.190")
chk(M["M6"]["coarsePitch"] == 1.0, "M6 pitch 1.0"); chk(M["M8"]["coarsePitch"] == 1.25, "M8 pitch 1.25")
chk(I["#8"]["unc"]["tapDrill"] == "#29", "#8-32 tap #29"); chk(I["1/4"]["unc"]["tapDrill"] == "#7", "1/4-20 tap #7")
chk(I["#8"]["clearance"]["close"]["drill"] == "#18", "#8 close #18"); chk(M["M8"]["clearance"]["medium"] == 9.0, "M8 medium 9.0")

# every drill a row names must exist in the drill tables
lab = {s: {d["label"] for d in drills[s]} for s in ("number", "letter", "fractional", "metric")}
allin = set().union(lab["number"], lab["letter"], lab["fractional"])
mm = [d["mm"] for d in drills["metric"]]
def inch_ok(x, who):
    if x not in allin: bad(f"{who}: drill '{x}' not in drill tables")
def mm_ok(x, who):
    if not any(abs(x - m) < 1e-9 for m in mm): bad(f"{who}: metric drill {x} mm not in drill tables")
for r in imp["rows"]:
    for k in ("unc", "unf"):
        if r[k]: inch_ok(r[k]["tapDrill"], r["label"])
    for k, v in r["clearance"].items(): inch_ok(v["drill"], r["label"])
for r in met["rows"]:
    mm_ok(r["tapDrillCoarse"], r["label"])
    for f in r["finePitches"]: mm_ok(f["tapDrill"], r["label"])
    for v in r["clearance"].values(): mm_ok(v, r["label"])
for r in wood["rows"]:
    for k in ("pilotSoftwood", "pilotHardwood", "clearance"): inch_ok(r[k], r["label"])

if errs:
    print("\n".join("FAIL " + e for e in errs)); sys.exit(1)
print("OK: data validated (20 / 17 / 11 rows, drills cross-checked)")
