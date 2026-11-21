# Screw Size Chart

Static site (plain HTML, CSS, JS, JSON). Deploy as a Cloudflare Workers static-assets project: push to GitHub, create a Worker from Git, no build command. `wrangler.jsonc` drives everything. `_redirects` holds the 301 rules.

## Structure (after the 18 Nov 2026 consolidation: 34 indexable URLs)

Per language (English at the root, then `/es/`, `/pt/`, `/de/`, `/fr/`, `/ja/`), 5 pages:

| Page | Holds |
|---|---|
| `/` | home, lookup tool |
| `/screw-size-chart` | inch master page: how to choose a chart (`#choosing-a-chart`), machine screws, wood screws, machine vs wood, UNC vs UNF (sections `#machine-screws`, `#wood-screws`, `#machine-vs-wood`, `#unc-vs-unf`) |
| `/metric-screw-size-chart` | metric chart + how to read a thread callout (`#thread-callout`) |
| `/drill-bit-to-screw-size` | drill finder and charts + pilot holes (`#pilot-holes`) + tap drills (`#tap-drill`) |
| `/blog/how-to-measure-a-screw-size` | guide (kept on its own URL) |

English-only utility pages: `/sources-and-method`, `/about`, `/contact`, `/privacy`. The translated privacy pages exist for visitors but are `noindex, follow` and are not in the sitemap or hreflang. The old filterable explorer on `/screw-size-chart` was removed on purpose (its content lived in JavaScript); the lookup on the home page and the finder on the drill page remain. Old URLs (wood chart, machine chart, the other guides, `/blog`, `/ja/about|contact|sources-and-method`) are 301s in `_redirects`.

## Diagrams, PDF and printing

- **Six diagrams** (inline SVG, no image files) sit where they explain something a table cannot: how to measure a screw (guide), how to read `M8 × 1.25 – 30` (metric page) and `#8-32 × 1` (inch page), clearance vs tapped vs pilot hole (drill page), wood vs machine screw and coarse vs fine thread (inch page). The picture holds only numbers and the two screw names; the explanation is a numbered list in HTML under it, so it is translated, searchable and screen-reader friendly. They follow the light and dark theme. Source: `tools/add_enhancements.py` (safe to re-run; it replaces what it added). Not added on purpose: head-style galleries, stock imagery and decorative graphics, because they would not help anyone choose a drill bit.
- **`screw-size-chart-printable.pdf`**: 3 pages (inch machine, wood, metric) built from `data/*.json` by `tools/build_pdf.py` (needs `pip install reportlab`). Rebuild it whenever the data changes. It is English only and linked from the three chart pages in every language.
- **Print styles** in `style.css` hide menus and tool widgets so a chart page prints cleanly.
- The lookup tool's source line and the wood pilot-hole note are translated through `window.I18N` (keys are the English strings plus `wood-assumption-template`), so non-English results are no longer half English.
- `.github/workflows/check.yml` runs both checkers on every push.

## Before every commit

1. `python3 tools/validate.py` (data) and `python3 tools/check_site.py` (site) must both pass.
2. If the data changed: `python3 tools/build_pdf.py`. If you add, remove or change pages: `python3 tools/build_sitemap.py --lastmod YYYY-MM-DD`, then run the checks again.

`tools/check_site.py` checks links and anchors, redirects (no chains, no linking to redirected URLs), canonicals, hreflang (reciprocal and equal to the sitemap), sitemap = indexable pages, the noindex list, unique titles and descriptions, one `<h1>` per page, valid JSON-LD without stray backslashes, table row counts in the HTML, the six diagrams (valid SVG, numbered markers match the legend) and the PDF links, minimum prose depth, decimal separators and the approved drill terms (`tools/glossary.json`).

`tools/merge_pages.py` was the one-off script that did the consolidation. It refuses to run again.

## Rules that keep the site healthy

- Every table a page needs must be in the HTML, not loaded by JavaScript. The lookup and finder tools add to the page; they are not where content lives.
- Add a new page only if it is clearly different from the others, and put it in the sitemap through `build_sitemap.py`. Prefer adding a section to an existing page.
- Redirect targets never include `#anchors`. Link to anchors from pages, not from `_redirects`.
- Decimal separators: pt, de and fr use a comma (`dec` in each page's `I18N`); en, es and ja use a point. Spanish keeps the point because 86% of the Spanish-page impressions in the first month came from Mexico, which uses it. Standard names such as ASME B18.2.8 keep their points.

## Languages

English, Spanish, Portuguese, German, French and Japanese, with a crawlable switcher and `hreflang` for all six plus `x-default` on the five core pages. Every translation is machine-assisted and still needs native review: a mistranslated drill term sends someone to the wrong hole. Terms to review: Spanish "agujero de paso" / "broca para roscar"; Portuguese "furo de passagem" / "broca para rosca"; German "Durchgangsloch" / "Kernlochbohrer"; French "trou de passage" / "foret de taraudage"; Japanese 通し穴 / タップ下穴径.

## Before launching ads

- Replace `https://screwchart.com` and `contact@screwchart.com` if the domain or address changes.
- Add a Google-certified consent banner: Analytics currently denies tracking by default for the EU/UK/EEA and there is no banner to grant it.
- No ad code is included.
