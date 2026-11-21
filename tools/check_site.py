#!/usr/bin/env python3
"""Site-wide checks. Must pass before every commit:  python3 tools/validate.py && python3 tools/check_site.py"""
import json, os, re, sys, html as H, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)
BASE = "https://screwchart.com"
LANGS = ["en", "es", "pt", "de", "fr", "ja"]
DEC_LANGS = ["pt", "de", "fr"]  # comma languages; en, es and ja use a point
errs = []


def has_backslash(o):
    if isinstance(o, dict):
        return any(has_backslash(v) for v in o.values())
    if isinstance(o, list):
        return any(has_backslash(v) for v in o)
    return isinstance(o, str) and "\\" in o


def bad(m):
    errs.append(m)


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


files = []
for r, _, fs in os.walk("."):
    if r.startswith("./.git") or r.startswith("./node_modules"):
        continue
    for f in fs:
        if f.endswith(".html"):
            files.append(os.path.relpath(os.path.join(r, f), "."))
files.sort()
H_ = {f: read(f) for f in files}


def lang_of(f):
    p = f.split("/")
    return p[0] if len(p) > 1 and p[0] in LANGS else "en"


def slug_of(f):
    p = f.split("/")
    s = "/".join(p[1:]) if lang_of(f) != "en" or (len(p) > 1 and p[0] in LANGS) else f
    return s[:-5]


def pub(f):
    l, s = lang_of(f), slug_of(f)
    pre = "" if l == "en" else "/" + l
    if s == "index":
        return pre + "/"
    return pre + "/" + s


def is_noindex(h):
    return bool(re.search(r'<meta name="robots"[^>]*noindex', h))


indexable = [f for f in files if f != "404.html" and not is_noindex(H_[f])]
noindex = sorted(f for f in files if f == "404.html" or is_noindex(H_[f]))

# 1. noindex set
want = sorted(["404.html"] + [f"{l}/privacy.html" for l in LANGS if l != "en"])
if noindex != want:
    bad(f"noindex pages differ: {noindex} != {want}")

# 2. sitemap == indexable pages
sm = read("sitemap.xml")
sm_urls = re.findall(r"<loc>(.*?)</loc>", sm)
want_urls = sorted(BASE + pub(f) for f in indexable)
if sorted(sm_urls) != want_urls:
    bad(f"sitemap lists {len(sm_urls)} URLs, indexable pages are {len(want_urls)}; run tools/build_sitemap.py")
if sm.count("<lastmod>") != len(sm_urls):
    bad("sitemap: every URL needs <lastmod>")

# 3. redirects
redir = {}
for line in read("_redirects").splitlines():
    if line.strip() and not line.startswith("#"):
        parts = line.split()
        if len(parts) != 3 or parts[2] != "301":
            bad(f"_redirects: bad line {line!r}")
            continue
        redir[parts[0]] = parts[1]


def to_file(path):
    base = path.split("#")[0].split("?")[0]
    if base == "/":
        return "index.html"
    if base.endswith("/"):
        return base.strip("/") + "/index.html"
    c = base.strip("/") + ".html"
    if os.path.exists(c):
        return c
    return base.strip("/") if os.path.isfile(base.strip("/")) else None


for s, d in redir.items():
    if to_file(s) is not None:
        bad(f"_redirects: source still exists as a file: {s}")
    if "#" in d:
        bad(f"_redirects: no #fragment allowed in target: {s} -> {d}")
    if to_file(d) is None:
        bad(f"_redirects: target missing: {s} -> {d}")
    if d in redir:
        bad(f"_redirects: redirect chain {s} -> {d} -> {redir[d]}")
if len(redir) < 60:
    bad(f"_redirects has only {len(redir)} rules (expected at least 63)")

# 4. links + anchors
ids = {f: set(re.findall(r'\sid="([^"]+)"', h)) for f, h in H_.items()}
for f, h in H_.items():
    cur = pub(f)
    for m in re.finditer(r'(?:href|src)="(/[^"#?]*)(#[^"]*)?"', h):
        path, frag = m.group(1), (m.group(2) or "")[1:]
        if path in redir:
            bad(f"{f}: links to redirected URL {path}")
            continue
        t = to_file(path)
        if t is None:
            bad(f"{f}: broken link {path}")
        elif frag and t.endswith(".html") and frag not in ids.get(t, set()):
            bad(f"{f}: missing anchor #{frag} on {path}")
    for m in re.finditer(r'href="#([^"]+)"', h):
        if m.group(1) not in ids[f]:
            bad(f"{f}: in-page link #{m.group(1)} has no target")

# 5. per-page basics
titles, metas = collections.defaultdict(list), collections.defaultdict(list)
for f in indexable:
    h = H_[f]
    url = BASE + pub(f)
    c = re.search(r'<link rel="canonical" href="([^"]+)"', h)
    if not c or c.group(1) != url:
        bad(f"{f}: canonical {c.group(1) if c else None} != {url}")
    if len(re.findall(r"<h1[ >]", h)) != 1:
        bad(f"{f}: needs exactly one <h1>")
    all_ids = re.findall(r'\sid="([^"]+)"', h)
    if len(all_ids) != len(set(all_ids)):
        bad(f"{f}: duplicate id attributes")
    t = re.search(r"<title>(.*?)</title>", h, re.S)
    d = re.search(r'<meta name="description" content="([^"]*)"', h)
    if not t or not d:
        bad(f"{f}: missing title or description")
    else:
        titles[(lang_of(f), t.group(1))].append(f)
        metas[(lang_of(f), d.group(1))].append(f)
    for m in re.finditer(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            j = json.loads(m.group(1))
        except Exception as e:
            bad(f"{f}: JSON-LD invalid ({e})")
            continue
        if has_backslash(j):
            bad(f"{f}: stray backslash in JSON-LD text")
        if j.get("@type") == "BreadcrumbList":
            for i in j["itemListElement"]:
                if "<" in i["name"]:
                    bad(f"{f}: HTML inside breadcrumb name")
for k, v in list(titles.items()) + list(metas.items()):
    if len(v) > 1:
        bad(f"duplicate title/description {k[1][:50]!r}: {v}")

# 6. hreflang reciprocity and agreement with the sitemap
alts = {}
for f in indexable:
    alts[f] = dict(re.findall(r'<link rel="alternate" hreflang="([^"]+)" href="([^"]+)"', H_[f]))
by_url = {BASE + pub(f): f for f in indexable}
for f, a in alts.items():
    if not a:
        continue
    if a.get(lang_of(f)) != BASE + pub(f):
        bad(f"{f}: hreflang does not list itself")
    for code, u in a.items():
        if code == "x-default":
            continue
        g = by_url.get(u)
        if g is None:
            bad(f"{f}: hreflang {code} points at a non-indexable or missing page {u}")
        elif alts[g].get(lang_of(f)) != BASE + pub(f):
            bad(f"{f}: hreflang {code} is not reciprocal")
    sm_block = re.search(r"<url><loc>%s</loc>(.*?)</url>" % re.escape(BASE + pub(f)), sm)
    sm_alts = dict(re.findall(r'hreflang="([^"]+)" href="([^"]+)"', sm_block.group(1))) if sm_block else {}
    if sm_alts != a:
        bad(f"{f}: hreflang in the page differs from the sitemap")

# 7. merged pages: anchors, tables, depth
NEED = {"screw-size-chart": ["choosing-a-chart", "machine-screws", "wood-screws", "machine-vs-wood", "unc-vs-unf"],
        "metric-screw-size-chart": ["thread-callout"], "drill-bit-to-screw-size": ["pilot-holes", "tap-drill"]}
ROWS = {"screw-size-chart": {"machine": 20, "wood": 11}, "metric-screw-size-chart": {"metric": 17}}


def table_rows(h, tid):
    m = re.search(r'<table id="%s">.*?<tbody>(.*?)</tbody>' % tid, h, re.S)
    return len(re.findall(r"<tr>", m.group(1))) if m else -1


def prose_words(h):
    m = re.search(r'<main><div class="wrap">(.*?)</div></main>', h, re.S)
    t = re.sub(r"<script.*?</script>|<style.*?</style>|<table.*?</table>", " ", m.group(1), flags=re.S)
    return len(H.unescape(re.sub(r"<[^>]+>", " ", t)).split())


MIN = {"screw-size-chart": 1500, "metric-screw-size-chart": 800, "drill-bit-to-screw-size": 1200,
       "blog/how-to-measure-a-screw-size": 700}
for l in LANGS:
    for s, need in NEED.items():
        f = f"{s}.html" if l == "en" else f"{l}/{s}.html"
        for i in need:
            if i not in ids.get(f, set()):
                bad(f"{f}: missing section id {i}")
    for s, rows in ROWS.items():
        f = f"{s}.html" if l == "en" else f"{l}/{s}.html"
        for tid, n in rows.items():
            if table_rows(H_[f], tid) != n:
                bad(f"{f}: table #{tid} should have {n} rows in the HTML (found {table_rows(H_[f], tid)})")
    for sid, page in (("machine-vs-wood", "screw-size-chart"), ("unc-vs-unf", "screw-size-chart"), ("thread-callout", "metric-screw-size-chart"), ("pilot-holes", "drill-bit-to-screw-size"), ("tap-drill", "drill-bit-to-screw-size")):
        f = f"{page}.html" if l == "en" else f"{l}/{page}.html"
        m = re.search(r'<section id="%s">.*?</section>' % sid, H_[f], re.S)
        if not m or "<time datetime=" not in m.group(0):
            bad(f"{f}: section #{sid} lost its 'Last updated' line")
    f = "screw-size-chart.html" if l == "en" else f"{l}/screw-size-chart.html"
    dm = re.search(r'<meta name="description" content="([^"]*)"', H_[f])
    if l != "ja" and dm and len(H.unescape(dm.group(1))) > 165:
        bad(f"{f}: meta description is {len(dm.group(1))} characters (max 165)")
    if l != "ja":
        for s, n in MIN.items():
            f = f"{s}.html" if l == "en" else f"{l}/{s}.html"
            w = prose_words(H_[f])
            if w < n:
                bad(f"{f}: only {w} prose words (minimum {n})")

# 8. decimals in pt/es/de/fr visible text
for f in files:
    if lang_of(f) in DEC_LANGS:
        h = H_[f]
        parts = re.split(r"(<script.*?</script>|<style.*?</style>|<!--.*?-->|<[^>]+>)", h, flags=re.S)
        for p in parts:
            if p.startswith("<"):
                continue
            q = re.sub(r"\bB\d+(?:\.\d+)+\b", "", p)
            m = re.search(r".{12}(?<=\d)\.(?=\d).{6}", q)
            if m:
                bad(f"{f}: decimal point in visible text: {m.group(0)!r}")
                break

# 8b. en, es, ja must not use a decimal comma in visible text
for f in files:
    if lang_of(f) in ("en", "es", "ja"):
        for p in re.split(r"(<script.*?</script>|<style.*?</style>|<!--.*?-->|<[^>]+>)", H_[f], flags=re.S):
            if not p.startswith("<"):
                m = re.search(r".{12}(?<=\d),(?=\d).{6}", p)
                if m:
                    bad(f"{f}: decimal comma in visible text: {m.group(0)!r}")
                    break

# 9. glossary
G = json.load(open("tools/glossary.json", encoding="utf-8"))
for l, terms in G.items():
    if l.startswith("_"):
        continue
    f1 = H_[f"{l}/drill-bit-to-screw-size.html"] + H_[f"{l}/screw-size-chart.html"]
    for t in terms:
        if t not in f1:
            bad(f"glossary: {l} pages no longer contain the approved term {t!r}")

# 10. nothing may reference the removed pages
GONE = ["wood-screw-size-chart", "machine-screw-size-chart", "machine-screw-vs-wood-screw", "unc-vs-unf-threads",
        "how-to-read-a-metric-thread-callout", "pilot-hole-basics-hardwood", "tap-drill-sizes-explained"]
for f in files + ["app.js", "sitemap.xml", "robots.txt"]:
    txt = read(f)
    for g in GONE:
        if g in txt:
            bad(f"{f}: still mentions removed page {g}")
for g in ["wood-screw-size-chart", "machine-screw-size-chart", "blog"]:
    for l in LANGS:
        p = f"{l}/{g}.html" if l != "en" else f"{g}.html"
        if os.path.exists(p):
            bad(f"{p}: should have been deleted")

# 11. diagrams (inline SVG with a numbered legend) and the printable PDF
import xml.etree.ElementTree as ET
FIG = {"measure": ("blog/how-to-measure-a-screw-size", 3), "callout-metric": ("metric-screw-size-chart", 4),
       "callout-inch": ("screw-size-chart", 3), "holes": ("drill-bit-to-screw-size", 3),
       "machine-vs-wood": ("screw-size-chart", 4), "coarse-fine": ("screw-size-chart", 3)}
for l in LANGS:
    for fid, (page, n_items) in FIG.items():
        f = f"{page}.html" if l == "en" else f"{l}/{page}.html"
        m = re.search(r'<figure class="diagram" id="fig-%s">(.*?)</figure>' % fid, H_[f], re.S)
        if not m:
            bad(f"{f}: figure {fid} is missing (run tools/add_enhancements.py)")
            continue
        svg = re.search(r"<svg .*?</svg>", m.group(1), re.S)
        if not svg:
            bad(f"{f}: figure {fid} has no <svg>")
            continue
        try:
            ET.fromstring(svg.group(0).replace("<svg ", '<svg xmlns="http://www.w3.org/2000/svg" ', 1))
        except ET.ParseError as e:
            bad(f"{f}: figure {fid} is not valid SVG ({e})")
        if 'role="img"' not in svg.group(0) or "<title" not in svg.group(0):
            bad(f"{f}: figure {fid} needs role=img and a <title>")
        if re.search(r'(href|src)="https?:', svg.group(0)):
            bad(f"{f}: figure {fid} loads an external resource")
        marks = set(re.findall(r'<g class="mk">.*?<text[^>]*>(\d)</text>', svg.group(0)))
        if marks != {str(i) for i in range(1, n_items + 1)} or m.group(1).count("<li>") != n_items:
            bad(f"{f}: figure {fid} must have markers 1-{n_items} and exactly {n_items} legend items (found markers {sorted(marks)})")
PDF_NAME = "screw-size-chart-printable.pdf"
if not os.path.isfile(PDF_NAME) or open(PDF_NAME, "rb").read(5) != b"%PDF-":
    bad(f"{PDF_NAME} is missing or not a PDF (run tools/build_pdf.py)")
elif os.path.getsize(PDF_NAME) > 300_000:
    bad(f"{PDF_NAME} is unexpectedly large")
for l in LANGS:
    for page in ("screw-size-chart", "metric-screw-size-chart", "drill-bit-to-screw-size"):
        f = f"{page}.html" if l == "en" else f"{l}/{page}.html"
        if f'<p class="dl"><a href="/{PDF_NAME}">' not in H_[f]:
            bad(f"{f}: missing the PDF download link")
# the lookup tool's translated notes must exist on every non-English page that loads it
for f in files:
    if lang_of(f) != "en" and "window.I18N={" in H_[f]:
        for key in ("wood-assumption-template", "ASME B1.1 (diameter, TPI)", "ISO 261 / ISO 262 (diameter, pitch)", "Manufacturer wood-screw pilot-hole guidance"):
            if key not in H_[f]:
                bad(f"{f}: no translation for the tool note {key!r}")

if errs:
    print("\n".join("FAIL " + e for e in errs))
    print(f"\n{len(errs)} problem(s)")
    sys.exit(1)
print(f"OK: {len(files)} HTML files, {len(indexable)} indexable pages, {len(redir)} redirects, sitemap and hreflang consistent")
