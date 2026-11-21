#!/usr/bin/env python3
"""ONE-OFF consolidation (18 Nov 2026): 86 indexable URLs -> 34, no content removed.

Run once from a clean checkout:  python3 tools/merge_pages.py
It refuses to run twice (the old pages are deleted on the first run).
FIRST PASS ONLY: text restored afterwards (hub "Choosing the right chart", per-section "Last updated" lines),
shorter hub meta descriptions, the date fixes, Spanish back to a decimal point and the About page change were applied by hand, so do not use this to regenerate pages.

What it does, for each of the 6 languages:
  /screw-size-chart         <- machine chart + wood chart + machine-vs-wood + UNC-vs-UNF (as sections)
  /metric-screw-size-chart  <- + how to read a metric thread callout
  /drill-bit-to-screw-size  <- + pilot holes in hardwood + tap drill sizes
  /blog/how-to-measure-a-screw-size  stays (fixed breadcrumb data)
then deletes the old pages, rewrites every internal link, rebuilds the menus,
makes the Japanese utility pages follow the other languages, localises decimal
separators (pt/es/de/fr) and appends the 301 rules to _redirects.
"""
import html as H
import json
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)
LANGS = ["en", "es", "pt", "de", "fr", "ja"]
DEC = {"pt": ",", "de": ",", "fr": ","}  # decimal separator per language (ja and en keep ".")

if not os.path.exists("wood-screw-size-chart.html"):
    sys.exit("Already merged (wood-screw-size-chart.html is gone). Nothing to do.")


def pre(l):
    return "" if l == "en" else "/" + l


def fp(l, name):
    return f"{name}.html" if l == "en" else f"{l}/{name}.html"


def pub(l, name):
    if name == "index":
        return "/" if l == "en" else f"/{l}/"
    return f"{pre(l)}/{name}"


def read(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


MAIN_RE = re.compile(r'(<main><div class="wrap">)(.*?)(</div></main>)', re.S)


def inner_of(h):
    return MAIN_RE.search(h).group(2)


def split_inner(inner):
    m = re.match(r'<h1>(.*?)</h1>\s*(<p class="lede">.*?</p>)?\s*(.*)$', inner, re.S)
    return m.group(1), (m.group(2) or ""), m.group(3)


def demote(s):
    for k in (5, 4, 3, 2):
        s = re.sub(rf"<h{k}(\s|>)", lambda m, k=k: f"<h{k + 1}{m.group(1)}", s)
        s = s.replace(f"</h{k}>", f"</h{k + 1}>")
    return s


def strip_last_updated(s):
    return re.sub(r'\s*<p>[^<]*<time datetime="[^"]*">[^<]*</time></p>\s*$', "", s)


def strip_tags(s):
    return H.unescape(re.sub(r"<[^>]+>", "", s)).strip()


def section(sec_id, title, lede, body):
    return f'<section id="{sec_id}"><h2>{title}</h2>{lede}{demote(body)}</section>'


def toc(label, entries):
    li = "".join(f'<li><a href="#{i}">{t}</a></li>' for i, t in entries)
    return f'<div class="toc"><b>{label}</b><ul>{li}</ul></div>'


# ---------------------------------------------------------------- new strings
JUMP = {"en": "On this page", "es": "En esta página", "pt": "Nesta página", "de": "Auf dieser Seite",
        "fr": "Sur cette page", "ja": "このページの内容"}
HOWTO = {"en": "How to measure", "es": "Cómo medir", "pt": "Como medir", "de": "Schraube messen",
         "fr": "Mesurer une vis", "ja": "測り方"}
HUB = {
    "en": dict(
        title="Screw Size Chart (Inch): Machine and Wood Screw Sizes",
        meta="Inch screw size chart: diameters, threads per inch, tap drills and wood screw pilot holes, plus machine vs wood screws and UNC vs UNF threads.",
        h1="Screw size chart (inch)",
        lede="Machine and wood screws in inch sizes, kept apart because they use different threads and holes.",
        intro='Metric screws have their own <a href="{P}/metric-screw-size-chart">metric screw size chart</a>. Not sure what you have? Start with <a href="{P}/blog/how-to-measure-a-screw-size">how to measure a screw size</a>.'),
    "es": dict(
        title="Tabla de tornillos (pulgadas): máquina y madera",
        meta="Tabla de tornillos en pulgadas con diámetro, hilos por pulgada (UNC y UNF), broca para roscar y agujero piloto para madera, y la diferencia entre tornillos de máquina y para madera.",
        h1="Tabla de tornillos en pulgadas",
        lede="Tornillos de máquina y para madera en pulgadas, separados porque usan roscas y agujeros distintos.",
        intro='Los tornillos métricos tienen su propia <a href="{P}/metric-screw-size-chart">tabla de tornillos métricos</a>. ¿No sabes qué tornillo tienes? Empieza por <a href="{P}/blog/how-to-measure-a-screw-size">cómo medir el tamaño de un tornillo</a>.'),
    "pt": dict(
        title="Tabela de parafusos (polegadas): máquina e madeira",
        meta="Tabela de parafusos em polegadas com diâmetro, filetes por polegada (UNC e UNF), broca para rosca e furo piloto para madeira, e a diferença entre parafusos de máquina e para madeira.",
        h1="Tabela de parafusos em polegadas",
        lede="Parafusos de máquina e para madeira em polegadas, separados porque usam roscas e furos diferentes.",
        intro='Os parafusos métricos têm a própria <a href="{P}/metric-screw-size-chart">tabela de parafusos métricos</a>. Não sabe qual parafuso você tem? Comece por <a href="{P}/blog/how-to-measure-a-screw-size">como medir o tamanho de um parafuso</a>.'),
    "de": dict(
        title="Schraubentabelle (Zoll): Maschinen- und Holzschrauben",
        meta="Schraubentabelle in Zoll mit Durchmesser, Gängen pro Zoll (UNC und UNF), Kernlochbohrer und Vorbohrung für Holzschrauben sowie dem Unterschied zwischen Maschinen- und Holzschrauben.",
        h1="Schraubentabelle in Zoll",
        lede="Maschinen- und Holzschrauben in Zoll, getrennt geführt, weil sie unterschiedliche Gewinde und Löcher haben.",
        intro='Metrische Schrauben haben eine eigene <a href="{P}/metric-screw-size-chart">Tabelle metrischer Schrauben</a>. Nicht sicher, welche Schraube Sie haben? Beginnen Sie mit <a href="{P}/blog/how-to-measure-a-screw-size">Schraubengröße messen</a>.'),
    "fr": dict(
        title="Tableau des vis (pouces) : vis à métaux et à bois",
        meta="Tableau des vis en pouces avec diamètre, filets par pouce (UNC et UNF), foret de taraudage et avant-trou pour le bois, et la différence entre vis à métaux et vis à bois.",
        h1="Tableau des vis en pouces",
        lede="Vis à métaux et à bois en pouces, séparées parce qu'elles ont des filetages et des trous différents.",
        intro='Les vis métriques ont leur propre <a href="{P}/metric-screw-size-chart">tableau des vis métriques</a>. Vous ne savez pas quelle vis vous avez ? Commencez par <a href="{P}/blog/how-to-measure-a-screw-size">comment mesurer la taille d’une vis</a>.'),
    "ja": dict(
        title="ねじ一覧表(インチ):小ねじと木ねじ",
        meta="インチの小ねじと木ねじの一覧表。直径、インチあたりの山数(UNC・UNF)、タップ下穴径、木ねじの下穴を掲載し、小ねじと木ねじの違いや UNC と UNF の違いも解説。",
        h1="ねじサイズ一覧表(インチ)",
        lede="インチ規格の小ねじと木ねじを、ねじ山と穴が異なるため分けて掲載しています。",
        intro='メートルねじは別ページの<a href="{P}/metric-screw-size-chart">メートルねじ表</a>をご覧ください。手元のねじが分からない場合は、まず<a href="{P}/blog/how-to-measure-a-screw-size">ねじのサイズの測り方</a>をご覧ください。'),
}

# ---------------------------------------------------------------- read everything first
SRC = {}
for l in LANGS:
    for name in ["index", "screw-size-chart", "machine-screw-size-chart", "wood-screw-size-chart",
                 "metric-screw-size-chart", "drill-bit-to-screw-size", "blog/machine-screw-vs-wood-screw",
                 "blog/unc-vs-unf-threads", "blog/how-to-read-a-metric-thread-callout",
                 "blog/pilot-hole-basics-hardwood", "blog/tap-drill-sizes-explained"]:
        SRC[(l, name)] = read(fp(l, name))

NAVLAB = {}
for l in LANGS:
    labs = re.findall(r"<a href=\"[^\"]+\"[^>]*>([^<]+)</a>",
                      re.search(r'<nav aria-label="Main">.*?</nav>', SRC[(l, "index")], re.S).group(0))
    NAVLAB[l] = dict(home=labs[0], chart=labs[1], metric=labs[2], drill=labs[5])


def art(l, slug):
    t, lede, body = split_inner(inner_of(SRC[(l, "blog/" + slug)]))
    return t, strip_last_updated(body)


def set_main(h, inner):
    return MAIN_RE.sub(lambda m: m.group(1) + inner + m.group(3), h, count=1)


# ---------------------------------------------------------------- build merged pages
for l in LANGS:
    P = pre(l)
    # ---- hub
    mt, mlede, mrest = split_inner(inner_of(SRC[(l, "machine-screw-size-chart")]))
    wt, wlede, wrest = split_inner(inner_of(SRC[(l, "wood-screw-size-chart")]))
    vt, vbody = art(l, "machine-screw-vs-wood-screw")
    ut, ubody = art(l, "unc-vs-unf-threads")
    S = HUB[l]
    entries = [("machine-screws", mt), ("wood-screws", wt), ("machine-vs-wood", vt), ("unc-vs-unf", ut)]
    inner = (f'<h1>{S["h1"]}</h1><p class="lede">{S["lede"]}</p>\n<p>{S["intro"].format(P=P)}</p>\n'
             + toc(JUMP[l], entries) + "\n"
             + section("machine-screws", mt, mlede, mrest) + "\n"
             + section("wood-screws", wt, wlede, wrest) + "\n"
             + section("machine-vs-wood", vt, "", vbody) + "\n"
             + section("unc-vs-unf", ut, "", ubody))
    h = set_main(SRC[(l, "screw-size-chart")], inner)
    h = re.sub(r"<title>.*?</title>", lambda m: f"<title>{S['title']}</title>", h, count=1)
    h = re.sub(r'(<meta name="description" content=")[^"]*(")', lambda m: m.group(1) + S["meta"] + m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:title" content=")[^"]*(")', lambda m: m.group(1) + S["title"] + m.group(2), h, count=1)
    h = re.sub(r'(<meta property="og:description" content=")[^"]*(")', lambda m: m.group(1) + S["meta"] + m.group(2), h, count=1)
    h = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "WebApplication".*?</script>', "", h, flags=re.S)
    write(fp(l, "screw-size-chart"), h)

    # ---- metric
    h = SRC[(l, "metric-screw-size-chart")]
    t, lede, rest = split_inner(inner_of(h))
    ct, cbody = art(l, "how-to-read-a-metric-thread-callout")
    inner = (f"<h1>{t}</h1>{lede}\n" + toc(JUMP[l], [("metric", t), ("thread-callout", ct)]) + "\n" + rest
             + "\n" + section("thread-callout", ct, "", cbody))
    write(fp(l, "metric-screw-size-chart"), set_main(h, inner))

    # ---- drill
    h = SRC[(l, "drill-bit-to-screw-size")]
    t, lede, rest = split_inner(inner_of(h))
    m = re.search(r"<h2>([^<]*)</h2><details>", rest)
    charts_title = m.group(1)
    rest = rest.replace(m.group(0), f'<h2 id="drill-charts">{charts_title}</h2><details>', 1)
    pt_, pbody = art(l, "pilot-hole-basics-hardwood")
    tt, tbody = art(l, "tap-drill-sizes-explained")
    inner = (f"<h1>{t}</h1>{lede}\n"
             + toc(JUMP[l], [("drill-charts", charts_title), ("pilot-holes", pt_), ("tap-drill", tt)]) + "\n" + rest
             + "\n" + section("pilot-holes", pt_, "", pbody) + "\n" + section("tap-drill", tt, "", tbody))
    write(fp(l, "drill-bit-to-screw-size"), set_main(h, inner))

# ---------------------------------------------------------------- delete merged-away pages
OLD = ["wood-screw-size-chart", "machine-screw-size-chart", "blog",
       "blog/machine-screw-vs-wood-screw", "blog/unc-vs-unf-threads",
       "blog/how-to-read-a-metric-thread-callout", "blog/pilot-hole-basics-hardwood",
       "blog/tap-drill-sizes-explained"]
deleted = 0
for l in LANGS:
    for n in OLD:
        os.remove(fp(l, n))
        deleted += 1
for n in ("about", "contact", "sources-and-method"):
    os.remove(fp("ja", n))
    deleted += 1
print("deleted files:", deleted)


# ---------------------------------------------------------------- global pass
def linkmap(l):
    P = pre(l)
    m = {
        f"{P}/wood-screw-size-chart": f"{P}/screw-size-chart#wood-screws",
        f"{P}/machine-screw-size-chart": f"{P}/screw-size-chart#machine-screws",
        f"{P}/blog/machine-screw-vs-wood-screw": f"{P}/screw-size-chart#machine-vs-wood",
        f"{P}/blog/unc-vs-unf-threads": f"{P}/screw-size-chart#unc-vs-unf",
        f"{P}/blog/how-to-read-a-metric-thread-callout": f"{P}/metric-screw-size-chart#thread-callout",
        f"{P}/blog/pilot-hole-basics-hardwood": f"{P}/drill-bit-to-screw-size#pilot-holes",
        f"{P}/blog/tap-drill-sizes-explained": f"{P}/drill-bit-to-screw-size#tap-drill",
        f"{P}/blog": f"{P}/blog/how-to-measure-a-screw-size",
    }
    if l == "ja":
        m.update({"/ja/about": "/about", "/ja/contact": "/contact", "/ja/sources-and-method": "/sources-and-method"})
    return m


def page_path(f):
    if f == "index.html":
        return "/"
    if f.endswith("/index.html"):
        return "/" + f[: -len("index.html")]
    return "/" + f[:-5]


def lang_of(f):
    return f.split("/")[0] if f.split("/")[0] in LANGS and "/" in f else "en"


def rewrite_links(h, l, cur):
    lm = linkmap(l)

    def sub(m):
        path, frag = m.group(1), m.group(2) or ""
        if path in lm and not frag:
            new = lm[path]
            base, _, fr = new.partition("#")
            if base == cur and fr:
                return f'href="#{fr}"'
            return f'href="{new}"'
        return m.group(0)

    return re.sub(r'href="(/[^"#?]*)(#[^"]*)?"', sub, h)


def nav_html(l, cur):
    items = [(pub(l, "index"), NAVLAB[l]["home"]), (pub(l, "screw-size-chart"), NAVLAB[l]["chart"]),
             (pub(l, "metric-screw-size-chart"), NAVLAB[l]["metric"]),
             (pub(l, "drill-bit-to-screw-size"), NAVLAB[l]["drill"]),
             (pub(l, "blog/how-to-measure-a-screw-size"), HOWTO[l])]
    a = "".join(f'<a href="{u}"' + (' aria-current="page"' if u == cur else "") + f">{t}</a>" for u, t in items)
    return f'<nav aria-label="Main">{a}</nav>'


NAMES = [("en", "English"), ("es", "Español"), ("pt", "Português"), ("de", "Deutsch"), ("fr", "Français"), ("ja", "日本語")]


def switcher_ul(cur_lang, target):
    li = "".join(
        f'<li><a href="{target(c)}" hreflang="{c}" lang="{c}"' + (' aria-current="true"' if c == cur_lang else "") + f">{n}</a></li>"
        for c, n in NAMES)
    return f"<ul>{li}</ul>"


def localize(s, sep):
    def text(t):
        t = re.sub(r"\b(B\d+(?:\.\d+)+)\b", lambda m: m.group(1).replace(".", "\x01"), t)
        t = re.sub(r"(?<=\d)\.(?=\d)", sep, t)
        return t.replace("\x01", ".")

    parts = re.split(r"(<script.*?</script>|<style.*?</style>|<!--.*?-->|<[^>]+>)", s, flags=re.S)
    out = []
    for p in parts:
        if p.startswith("<"):
            if re.match(r'<meta (name="description"|property="og:(title|description)")', p):
                p = re.sub(r'(content=")([^"]*)(")', lambda m: m.group(1) + text(m.group(2)) + m.group(3), p)
            out.append(p)
        else:
            out.append(text(p))
    return "".join(out)


ALL = []
for root, _, files in os.walk("."):
    if root.startswith("./.git") or root.startswith("./node_modules"):
        continue
    for f in files:
        if f.endswith(".html"):
            ALL.append(os.path.relpath(os.path.join(root, f), "."))
ALL.sort()

for f in ALL:
    l = lang_of(f)
    h = read(f)
    cur = page_path(f)
    h = rewrite_links(h, l, cur)
    h = re.sub(r'<nav aria-label="Main">.*?</nav>', lambda m: nav_html(l, cur), h, count=1, flags=re.S)
    write(f, h)

# ---- utility pages: English-only (about, contact, sources, privacy) + translated privacy pages
UTIL_EN = ["about.html", "contact.html", "sources-and-method.html", "privacy.html"]
for f in UTIL_EN:
    h = read(f)
    h = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">', "", h)
    if f != "privacy.html":
        h = re.sub(r"<ul>.*?</ul>", lambda m: switcher_ul("en", lambda c: pub(c, "index")), h,
                   count=1, flags=re.S) if re.search(r'<nav class="lang"', h) else h
    write(f, h)
h = read("ja/privacy.html")
h = re.sub(r'<link rel="alternate" hreflang="[^"]+" href="[^"]+">', "", h)
if 'name="robots"' not in h:
    h = h.replace('<link rel="canonical"', '<meta name="robots" content="noindex, follow"><link rel="canonical"', 1)
write("ja/privacy.html", h)
# ja footers now point at the English utility pages (done by linkmap); the ja switcher on utility pages is gone.

# ---- guide pages: valid breadcrumb data (no HTML inside names, no "Blog" level)
for l in LANGS:
    f = fp(l, "blog/how-to-measure-a-screw-size")
    h = read(f)

    def fix_ld(m):
        d = json.loads(m.group(1))
        if d.get("@type") == "BreadcrumbList":
            items = [i for i in d["itemListElement"] if not i["item"].rstrip("/").endswith("/blog")]
            for n, i in enumerate(items, 1):
                i["position"] = n
                i["name"] = strip_tags(i["name"])
            d["itemListElement"] = items
        return '<script type="application/ld+json">' + json.dumps(d, ensure_ascii=False) + "</script>"

    h = re.sub(r'<script type="application/ld\+json">(.*?)</script>', fix_ld, h, flags=re.S)
    write(f, h)

# ---- decimal separators (visible text, title, meta description) for pt/es/de/fr
for f in ALL:
    if not os.path.exists(f):
        continue
    l = lang_of(f)
    if l in DEC:
        h = read(f)
        h = localize(h, DEC[l])
        if "window.I18N={" in h and '"dec"' not in h:
            h = h.replace("window.I18N={", 'window.I18N={"dec": "%s", ' % DEC[l], 1)
        write(f, h)

# ---------------------------------------------------------------- redirects
rules = ["", "# Consolidation (18 Nov 2026): merged pages. 301 so old URLs, links and Google's records land on the new page."]
tgt = [("wood-screw-size-chart", "screw-size-chart"), ("machine-screw-size-chart", "screw-size-chart"),
       ("blog/machine-screw-vs-wood-screw", "screw-size-chart"), ("blog/unc-vs-unf-threads", "screw-size-chart"),
       ("blog/how-to-read-a-metric-thread-callout", "metric-screw-size-chart"),
       ("blog/pilot-hole-basics-hardwood", "drill-bit-to-screw-size"),
       ("blog/tap-drill-sizes-explained", "drill-bit-to-screw-size"),
       ("blog", "blog/how-to-measure-a-screw-size")]
for l in LANGS:
    for old, new in tgt:
        rules.append(f"{pre(l)}/{old}  {pre(l)}/{new}  301")
for n in ("about", "contact", "sources-and-method"):
    rules.append(f"/ja/{n}  /{n}  301")
with open("_redirects", "a", encoding="utf-8", newline="\n") as f:
    f.write("\n".join(rules) + "\n")
print("redirect rules added:", len(rules) - 2)
print("done")
