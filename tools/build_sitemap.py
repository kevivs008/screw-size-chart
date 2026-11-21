#!/usr/bin/env python3
"""Regenerate sitemap.xml from the real files. Usage: python3 tools/build_sitemap.py [--lastmod YYYY-MM-DD]

A page is listed only if it is indexable (no noindex) and is not the 404 page.
hreflang alternates are listed only between indexable language versions of the same page.
Run it (with the deploy date) before every commit that adds, removes or changes pages.
"""
import datetime, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)
BASE = "https://screwchart.com"
LANGS = ["en", "es", "pt", "de", "fr", "ja"]
ORDER = ["index", "screw-size-chart", "metric-screw-size-chart", "drill-bit-to-screw-size",
         "blog/how-to-measure-a-screw-size", "sources-and-method", "about", "contact", "privacy"]
lastmod = datetime.date.today().isoformat()
if "--lastmod" in sys.argv:
    lastmod = sys.argv[sys.argv.index("--lastmod") + 1]


def fp(l, s):
    return f"{s}.html" if l == "en" else f"{l}/{s}.html"


def url(l, s):
    if s == "index":
        return BASE + ("/" if l == "en" else f"/{l}/")
    return BASE + ("" if l == "en" else f"/{l}") + "/" + s


def indexable(path):
    if not os.path.exists(path) or path == "404.html":
        return False
    return not re.search(r'<meta name="robots"[^>]*noindex', open(path, encoding="utf-8").read())


out = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">']
n = 0
for s in ORDER:
    here = [l for l in LANGS if indexable(fp(l, s))]
    for l in here:
        alts = ""
        if len(here) > 1:
            alts = "".join(f'<xhtml:link rel="alternate" hreflang="{c}" href="{url(c, s)}"/>' for c in here)
            if "en" in here:
                alts += f'<xhtml:link rel="alternate" hreflang="x-default" href="{url("en", s)}"/>'
        out.append(f"<url><loc>{url(l, s)}</loc><lastmod>{lastmod}</lastmod>{alts}</url>")
        n += 1
out.append("</urlset>")
open("sitemap.xml", "w", encoding="utf-8", newline="\n").write("\n".join(out) + "\n")
print(f"sitemap.xml written: {n} URLs, lastmod {lastmod}")
