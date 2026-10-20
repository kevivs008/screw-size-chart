# Screw Size Chart

Static site (plain HTML, CSS, JS, JSON). Deploy as a Cloudflare Workers static-assets project: push to GitHub, create a Worker from Git, no build command. `wrangler.jsonc` drives everything.

Before launch:
- Replace `https://screwchart.com` (canonicals, sitemap, robots.txt, JSON-LD) and `contact@screwchart.com` (contact page) with the real domain and address.
- Run `python3 tools/validate.py`; it must pass before every commit.
- Languages: English (root), Spanish `/es/`, Portuguese `/pt/`, German `/de/`, French `/fr/` and Japanese `/ja/` are all built, with a crawlable switcher and `hreflang` for all six plus `x-default`. Every translation is machine-assisted and needs native review before launch: a mistranslated drill term sends someone to the wrong hole. Numbers and sizes are identical in every language (checked by script). Terms to review: Spanish "agujero de paso" / "broca para roscar"; Portuguese "furo de passagem" / "broca para rosca"; German "Durchgangsloch" / "Kernlochbohrer"; French "trou de passage" / "foret de taraudage"; Japanese 通し穴 / タップ下穴径.
- Content pages carry 185-390 words of original prose in every language (guides on reading sizes, UNC vs UNF, pilot vs clearance holes), translated alongside the English. Extend toward 300-600 words per page before applying to AdSense; some pages are still under that. No ad code is included.
