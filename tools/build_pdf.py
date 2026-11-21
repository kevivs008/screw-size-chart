#!/usr/bin/env python3
"""Builds screw-size-chart-printable.pdf (US Letter, 3 pages) from data/*.json. Re-run whenever the data changes.

  pip install reportlab      (only needed to rebuild; the site itself needs nothing)
  python3 tools/build_pdf.py
"""
import json
import os

from reportlab import rl_config

rl_config.invariant = 1  # same input -> same bytes, so git diffs stay clean
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
OUT = os.path.join(ROOT, "screw-size-chart-printable.pdf")


def load(n):
    with open(os.path.join(ROOT, "data", n + ".json"), encoding="utf-8") as f:
        return json.load(f)


imp, met, wood = load("imperial-machine-screws"), load("metric-machine-screws"), load("wood-screws")
VERIFIED = imp["meta"]["lastVerified"]


def n(x, dp):  # number without trailing zeros
    s = f"{x:.{dp}f}"
    return s.rstrip("0").rstrip(".") if "." in s else s


H1 = ParagraphStyle("h1", fontName="Helvetica-Bold", fontSize=17, leading=20, spaceAfter=2)
SUB = ParagraphStyle("sub", fontName="Helvetica", fontSize=9, leading=12, textColor=colors.HexColor("#5c554d"), spaceAfter=8)
NOTE = ParagraphStyle("note", fontName="Helvetica", fontSize=8, leading=10.5, textColor=colors.HexColor("#333333"), spaceBefore=6)
ACCENT = colors.HexColor("#a1541a")


def table(header, rows, widths):
    t = Table([header] + rows, colWidths=[w * inch for w in widths], repeatRows=1)
    t.setStyle(TableStyle([
        ("FONT", (0, 0), (-1, 0), "Helvetica-Bold", 7.6), ("FONT", (0, 1), (-1, -1), "Helvetica", 8.4),
        ("FONT", (0, 1), (0, -1), "Helvetica-Bold", 8.4),
        ("BACKGROUND", (0, 0), (-1, 0), ACCENT), ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f7ede1")]),
        ("LINEBELOW", (0, -1), (-1, -1), 0.6, ACCENT), ("TOPPADDING", (0, 0), (-1, -1), 3.4), ("BOTTOMPADDING", (0, 0), (-1, -1), 3.4),
    ]))
    return t


def page_imperial():
    rows = []
    for r in imp["rows"]:
        u, f, c = r["unc"], r["unf"], r["clearance"]
        rows.append([r["label"], n(r["majorDiameterIn"], 4), n(r["majorDiameterMm"], 3),
                     str(u["tpi"]) if u else "-", u["tapDrill"] if u else "-", str(f["tpi"]) if f else "-", f["tapDrill"] if f else "-",
                     c["close"]["drill"], c["normal"]["drill"], c["loose"]["drill"]])
    hdr = ["Size", "Major dia\n(in)", "Major dia\n(mm)", "UNC\nTPI", "UNC tap\ndrill", "UNF\nTPI", "UNF tap\ndrill", "Clearance\nclose", "Clearance\nnormal", "Clearance\nloose"]
    return [Paragraph("Inch machine screws (UNC and UNF)", H1),
            Paragraph("Sizes #0 to 1 inch. Tap drills are for a 75% thread. Clearance drills are for close, normal and loose fits.", SUB),
            table(hdr, rows, [0.55, 0.72, 0.72, 0.5, 0.72, 0.5, 0.72, 0.82, 0.82, 0.82]),
            Paragraph("Sources: ASME B1.1 (diameter, threads per inch), 75% tap-drill chart (tap drills), ASME B18.2.8 (clearance holes). A dash means no standard thread in that series.", NOTE)]


def page_wood():
    rows = []
    for r in wood["rows"]:
        rows.append([r["label"], n(r["majorDiameterIn"], 3), n(r["majorDiameterMm"], 2),
                     f'{r["pilotSoftwood"]}  ({n(r["pilotSoftwoodIn"], 4)})', f'{r["pilotHardwood"]}  ({n(r["pilotHardwoodIn"], 4)})',
                     f'{r["clearance"]}  ({n(r["clearanceIn"], 4)})'])
    hdr = ["Size", "Major dia\n(in)", "Major dia\n(mm)", "Pilot hole, softwood\n(drill in)", "Pilot hole, hardwood\n(drill in)", "Clearance hole\n(drill in)"]
    return [Paragraph("Wood screws (gauge #2 to #14)", H1),
            Paragraph("Drill sizes are in fractions of an inch with the decimal equivalent in brackets.", SUB),
            table(hdr, rows, [0.6, 0.85, 0.85, 1.55, 1.55, 1.3]),
            Paragraph("Guidance only. Published charts disagree, and the right pilot size depends on the wood species and its hardness. "
                      "Drill a test hole in a scrap of your board first. Source: manufacturer wood-screw pilot-hole guidance.", NOTE)]


def page_metric():
    rows = []
    for r in met["rows"]:
        c = r["clearance"]
        fine = "  /  ".join(f'{n(x["pitch"], 3)} ({n(x["tapDrill"], 2)})' for x in r["finePitches"]) if r["finePitches"] else "-"
        rows.append([r["label"], n(r["majorDiameterMm"], 2), n(r["majorDiameterIn"], 3), n(r["coarsePitch"], 3), fine,
                     n(r["tapDrillCoarse"], 2), n(c["fine"], 2), n(c["medium"], 2), n(c["coarse"], 2)])
    hdr = ["Size", "Major dia\n(mm)", "Major dia\n(in)", "Coarse\npitch (mm)", "Fine pitch (tap drill)\n(mm)", "Tap drill,\ncoarse (mm)", "Clearance\nfine (mm)", "Clearance\nmedium (mm)", "Clearance\ncoarse (mm)"]
    return [Paragraph("Metric machine screws (M1.6 to M24)", H1),
            Paragraph("Coarse pitch is the standard thread; fine pitches are listed with their tap drill in brackets. Tap drill = diameter minus pitch.", SUB),
            table(hdr, rows, [0.5, 0.7, 0.7, 0.75, 1.5, 0.8, 0.72, 0.85, 0.78]),
            Paragraph("Sources: ISO 261 / ISO 262 (diameter, pitch), tap drill = d - P, clearance holes per ISO 273 (fine H12 / medium H13 / coarse H14).", NOTE)]


def footer(c, doc):
    c.saveState()
    c.setFont("Helvetica", 7.5)
    c.setFillColor(colors.HexColor("#555555"))
    c.drawString(0.6 * inch, 0.55 * inch, f"screwchart.com   |   Reference only, not an engineering specification. Test on scrap before drilling.   |   Data verified {VERIFIED}")
    c.drawRightString(letter[0] - 0.6 * inch, 0.55 * inch, f"Page {doc.page} of 3")
    c.setStrokeColor(ACCENT)
    c.setLineWidth(1.4)
    c.line(0.6 * inch, letter[1] - 0.45 * inch, letter[0] - 0.6 * inch, letter[1] - 0.45 * inch)
    c.restoreState()


doc = SimpleDocTemplate(OUT, pagesize=letter, leftMargin=0.6 * inch, rightMargin=0.6 * inch, topMargin=0.7 * inch, bottomMargin=0.8 * inch,
                        title="Screw size charts: inch, wood and metric", author="screwchart.com", subject="Screw sizes, tap drills, clearance and pilot holes")
story = page_imperial() + [PageBreak()] + page_wood() + [PageBreak()] + page_metric()
doc.build(story, onFirstPage=footer, onLaterPages=footer)
print("wrote", OUT, os.path.getsize(OUT), "bytes")
