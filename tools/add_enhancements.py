#!/usr/bin/env python3
"""Adds the diagrams, the PDF download links and their CSS. Safe to re-run: it replaces what it added before.

  python3 tools/add_enhancements.py

Diagrams (inline SVG, no external files, no text except numbers and two screw names):
  measure          guide        how to measure a screw (major diameter, length of flat head vs other heads)
  callout-metric   metric chart how to read M8 x 1.25 - 30
  callout-inch     inch chart   how to read #8-32 x 1
  holes            drill page   clearance hole vs tapped hole vs pilot hole
  machine-vs-wood  inch chart   wood screw next to machine screw
  coarse-fine      inch chart   UNC next to UNF, with the pitch marked
Each figure's explanation is plain HTML (a numbered list under the picture), so it is translated, searchable and accessible.
"""
import os
import re
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
os.chdir(ROOT)
LANGS = ["en", "es", "pt", "de", "fr", "ja"]
COMMA = {"pt", "de", "fr"}  # languages that write 1,25 instead of 1.25


def fp(l, name):
    return f"{name}.html" if l == "en" else f"{l}/{name}.html"


def rd(p):
    with open(p, encoding="utf-8") as f:
        return f.read()


def wr(p, s):
    with open(p, "w", encoding="utf-8", newline="\n") as f:
        f.write(s)


def d(l, s):  # decimal separator
    return s.replace(".", ",") if l in COMMA else s


# ------------------------------------------------------------------ SVG pieces
def marker(x, y, n):
    return f'<g class="mk"><circle cx="{x}" cy="{y}" r="10"/><text x="{x}" y="{y + 4.5}" text-anchor="middle">{n}</text></g>'


def threads(x0, x1, cy, r, step, slant):
    return '<path class="thr" d="' + "".join(f"M{x},{cy + r} l{slant},{-2 * r} " for x in range(x0, x1, step)) + '"/>'


def dim_h(x0, x1, y, ext_from=None):
    s = f'<path class="dim" d="M{x0},{y} H{x1} M{x0},{y - 6} V{y + 6} M{x1},{y - 6} V{y + 6}"/>'
    if ext_from is not None:
        s += f'<path class="ext" d="M{x0},{ext_from} V{y - 6} M{x1},{ext_from} V{y - 6}"/>'
    return s


def svg_measure(l, names):
    a, b, r = 64, 156, 12
    return (
        f'<path class="body" d="M30,{a - 19} L56,{a - r} H380 L400,{a} L380,{a + r} H56 L30,{a + 19} Z"/>'
        f'<path class="body" d="M30,{a - 19} L56,{a - r} V{a + r} L30,{a + 19} Z"/>'
        + threads(62, 376, a, r, 11, 7)
        + f'<path class="ext" d="M200,{a - r} H240 M200,{a + r} H240"/>'
        + f'<path class="dim" d="M236,{a - r} V{a + r} M230,{a - r} H242 M230,{a + r} H242"/>'
        + f'<path class="ext" d="M236,{a - r - 2} V{a - 17}"/>' + marker(236, a - 27, 1)
        + dim_h(30, 400, a + 34, a + 20) + marker(215, a + 34, 2)
        + f'<rect class="body" x="30" y="{b - 19}" width="22" height="38" rx="9"/>'
        f'<path class="body" d="M52,{b - r} H380 L400,{b} L380,{b + r} H52 Z"/>'
        + threads(58, 376, b, r, 11, 7)
        + dim_h(52, 400, b + 34, b + 20) + marker(226, b + 34, 3)
    ), "0 0 420 214"


def svg_callout(l, names, parts, marks, unders):
    out = ""
    for x, t in parts:
        out += f'<text class="big" x="{x}" y="78" text-anchor="middle">{t}</text>'
    for n, (x, w) in enumerate(unders, 1):
        out += f'<path class="ul" d="M{x - w / 2},90 H{x + w / 2}"/><path class="ext" d="M{x},32 V54"/>' + marker(x, 22, n)
    return out, "0 0 400 110"


def svg_metric(l, names):
    p = d(l, "1.25")
    return svg_callout(l, names, [(58, "M"), (108, "8"), (150, "×"), (212, p), (272, "–"), (330, "30")], None,
                       [(58, 26), (108, 26), (212, 88), (330, 46)])


def svg_inch(l, names):
    return svg_callout(l, names, [(115, "#8"), (157, "-"), (199, "32"), (253, "×"), (297, "1")], None,
                       [(115, 46), (199, 46), (297, 26)])


def panel(x0, cx, title, wood):
    top = (f'<rect class="plate" x="{x0 + 10}" y="78" width="{cx - 12 - (x0 + 10)}" height="40"/>'
           f'<rect class="plate" x="{cx + 12}" y="78" width="{x0 + 180 - (cx + 12)}" height="40"/>')
    hw = 3.5 if wood else 6.5
    bot = (f'<path class="plate" d="M{x0 + 10},118 H{cx - hw} V190 H{cx + hw} V118 H{x0 + 180} V208 H{x0 + 10} Z"/>')
    if wood:
        bot += "".join(f'<path class="grain" d="M{x0 + 14},{y} H{cx - 12} M{cx + 12},{y} H{x0 + 176}"/>' for y in (136, 158, 180))
        shank = (f'<path class="body" d="M{cx - 6},74 V118 L{cx - 8},120 V132 L{cx},150 L{cx + 8},132 V120 L{cx + 6},118 V74 Z"/>')
    else:
        bot += "".join(f'<path class="thr" d="M{cx - hw},{y} l-4,3 M{cx + hw},{y} l4,3"/>' for y in range(154, 190, 7))
        shank = f'<path class="body" d="M{cx - 8},74 V148 H{cx + 8} V74 Z"/>'
        shank += f'<path class="thr" d="' + "".join(f"M{cx - 8},{y + 3} L{cx + 8},{y - 3} " for y in range(124, 148, 7)) + '"/>'
    head = f'<rect class="body" x="{cx - 22}" y="58" width="44" height="16" rx="5"/>'
    lead = (f'<path class="ext" d="M{cx - 40},50 L{cx - 12},96"/>' + marker(cx - 46, 42, 1)
            + f'<path class="ext" d="M{cx + 40},226 L{cx + 5},176"/>' + marker(cx + 46, 232, 3 if wood else 2))
    return (f'<text class="ttl" x="{cx}" y="18" text-anchor="middle">{title}</text>' + top + bot + shank + head + lead)


def svg_holes(l, names):
    return panel(10, 105, names["machine"], False) + panel(220, 315, names["wood"], True), "0 0 420 250"


def svg_vs(l, names):
    a, b = 58, 150
    wood = (f'<text class="ttl" x="30" y="20">{names["wood"]}</text>'
            f'<path class="body" d="M30,{a - 15} L52,{a - 6} H130 V{a - 9} H370 L404,{a} L370,{a + 9} H130 V{a + 6} H52 L30,{a + 15} Z"/>'
            + threads(136, 366, a, 9, 16, 8)
            + f'<path class="ext" d="M396,{a - 14} L398,{a - 4}"/>' + marker(392, a - 26, 1)
            + f'<path class="ext" d="M250,{a - 16} V{a - 11}"/>' + marker(250, a - 26, 2))
    mach = (f'<text class="ttl" x="30" y="112">{names["machine"]}</text>'
            f'<rect class="body" x="30" y="{b - 16}" width="22" height="32" rx="8"/>'
            f'<path class="body" d="M52,{b - 8} H388 L394,{b - 3} V{b + 3} L388,{b + 8} H52 Z"/>'
            + threads(56, 386, b, 8, 6, 3)
            + f'<path class="ext" d="M230,{b - 16} V{b - 10}"/>' + marker(230, b - 26, 3)
            + f'<path class="ext" d="M392,{b - 16} V{b - 5}"/>' + marker(392, b - 26, 4))
    return wood + mach, "0 0 420 180"


def svg_cf(l, names):
    def strip(base, pitch, n, h, label, ly):
        pts, x = [f"M40,{base + 18}", f"L40,{base}"], 40.0
        for _ in range(n):
            pts += [f"L{x + pitch / 2:.1f},{base - h}", f"L{x + pitch:.1f},{base}"]
            x += pitch
        pts += [f"L{x:.1f},{base + 18}", "Z"]
        return (f'<path class="body" d="{" ".join(pts)}"/><text class="ttl" x="{(40 + x) / 2:.0f}" y="{ly}" text-anchor="middle">{label}</text>')
    s = strip(70, 56, 6, 26, "UNC", 84) + strip(150, 33.6, 10, 18, "UNF", 164)
    s += dim_h(68, 124, 34) + marker(96, 34, 3) + dim_h(56.8, 90.4, 122)
    s += marker(18, 63, 1) + marker(18, 151, 2)
    return s, "0 0 420 190"


FIGS = {
    "measure": svg_measure, "callout-metric": svg_metric, "callout-inch": svg_inch,
    "holes": svg_holes, "machine-vs-wood": svg_vs, "coarse-fine": svg_cf,
}

NAMES = {
    "en": dict(wood="Wood screw", machine="Machine screw"),
    "es": dict(wood="Tornillo para madera", machine="Tornillo de máquina"),
    "pt": dict(wood="Parafuso para madeira", machine="Parafuso de máquina"),
    "de": dict(wood="Holzschraube", machine="Maschinenschraube"),
    "fr": dict(wood="Vis à bois", machine="Vis à métaux"),
    "ja": dict(wood="木ねじ", machine="小ねじ"),
}

# caption + numbered explanation, per figure and language. {p}=1.25 and {g}=0.164 get the language's decimal separator.
TXT = {
    "measure": {
        "en": ("How to measure a screw: major diameter and length", [
            "Major diameter: across the thread crests, measured with a caliper.",
            "Length of a flat (countersunk) head screw: the whole screw, from the top of the head to the tip.",
            "Length with any other head: from under the head to the tip."]),
        "es": ("Cómo medir un tornillo: diámetro exterior y longitud", [
            "Diámetro exterior: de cresta a cresta de la rosca, medido con un calibre.",
            "Longitud de un tornillo de cabeza plana (avellanada): todo el tornillo, desde la parte superior de la cabeza hasta la punta.",
            "Longitud con cualquier otra cabeza: desde debajo de la cabeza hasta la punta."]),
        "pt": ("Como medir um parafuso: diâmetro externo e comprimento", [
            "Diâmetro externo: de crista a crista da rosca, medido com um paquímetro.",
            "Comprimento de um parafuso de cabeça chata (escareada): o parafuso inteiro, do topo da cabeça até a ponta.",
            "Comprimento com qualquer outra cabeça: de baixo da cabeça até a ponta."]),
        "de": ("Schraube messen: Außendurchmesser und Länge", [
            "Außendurchmesser: über die Gewindespitzen gemessen, mit der Schieblehre.",
            "Länge einer Senkkopfschraube: die ganze Schraube, von der Oberseite des Kopfes bis zur Spitze.",
            "Länge bei allen anderen Kopfformen: von unter dem Kopf bis zur Spitze."]),
        "fr": ("Mesurer une vis : diamètre extérieur et longueur", [
            "Diamètre extérieur : d'un sommet de filet à l'autre, mesuré au pied à coulisse.",
            "Longueur d'une vis à tête fraisée : toute la vis, du dessus de la tête à la pointe.",
            "Longueur avec toute autre tête : de sous la tête à la pointe."]),
        "ja": ("ねじの測り方:外径と長さ", [
            "外径:ねじ山の頂から頂までを、ノギスで測ります。",
            "皿頭ねじの長さ:頭の上面から先端までの全長です。",
            "それ以外の頭の形の長さ:頭の下から先端までです。"]),
    },
    "callout-metric": {
        "en": ("Reading a metric size: M8 × {p} – 30", [
            "M: metric thread.", "8: major diameter in millimetres.",
            "{p}: thread pitch in millimetres (the distance between crests).", "30: length in millimetres."]),
        "es": ("Cómo leer una medida métrica: M8 × {p} – 30", [
            "M: rosca métrica.", "8: diámetro exterior en milímetros.",
            "{p}: paso de rosca en milímetros (la distancia entre crestas).", "30: longitud en milímetros."]),
        "pt": ("Como ler uma medida métrica: M8 × {p} – 30", [
            "M: rosca métrica.", "8: diâmetro externo em milímetros.",
            "{p}: passo da rosca em milímetros (a distância entre cristas).", "30: comprimento em milímetros."]),
        "de": ("So liest man eine metrische Größe: M8 × {p} – 30", [
            "M: metrisches Gewinde.", "8: Außendurchmesser in Millimetern.",
            "{p}: Gewindesteigung in Millimetern (der Abstand zwischen den Gewindespitzen).", "30: Länge in Millimetern."]),
        "fr": ("Lire une taille métrique : M8 × {p} – 30", [
            "M : filetage métrique.", "8 : diamètre extérieur en millimètres.",
            "{p} : pas du filetage en millimètres (la distance entre deux sommets).", "30 : longueur en millimètres."]),
        "ja": ("メートルねじの表記の読み方:M8 × {p} – 30", [
            "M:メートルねじ。", "8:外径(ミリメートル)。",
            "{p}:ピッチ(ミリメートル。ねじ山の頂の間隔)。", "30:長さ(ミリメートル)。"]),
    },
    "callout-inch": {
        "en": ("Reading an inch machine screw size: #8-32 × 1", [
            "#8: size number (the major diameter is {g} in).", "32: threads per inch (TPI).", "1: length in inches."]),
        "es": ("Cómo leer la medida de un tornillo de máquina en pulgadas: #8-32 × 1", [
            "#8: número de tamaño (el diámetro exterior es {g} pulg.).", "32: hilos por pulgada (TPI).", "1: longitud en pulgadas."]),
        "pt": ("Como ler a medida de um parafuso de máquina em polegadas: #8-32 × 1", [
            "#8: número do tamanho (o diâmetro externo é {g} pol.).", "32: filetes por polegada (TPI).", "1: comprimento em polegadas."]),
        "de": ("So liest man die Größe einer Maschinenschraube in Zoll: #8-32 × 1", [
            "#8: Größennummer (der Außendurchmesser beträgt {g} Zoll).", "32: Gänge pro Zoll (TPI).", "1: Länge in Zoll."]),
        "fr": ("Lire la taille d'une vis à métaux en pouces : #8-32 × 1", [
            "#8 : numéro de taille (le diamètre extérieur est de {g} pouce).", "32 : filets par pouce (TPI).", "1 : longueur en pouces."]),
        "ja": ("インチの小ねじの表記の読み方:#8-32 × 1", [
            "#8:サイズ番号(外径は{g}インチ)。", "32:1インチあたりの山数(TPI)。", "1:長さ(インチ)。"]),
    },
    "holes": {
        "en": ("The three kinds of hole", [
            "Clearance hole: the screw passes through freely, so the parts clamp together.",
            "Tapped hole: drilled to the tap drill size, then threaded with a tap.",
            "Pilot hole: smaller than the thread, so the wood screw cuts its own thread."]),
        "es": ("Los tres tipos de agujero", [
            "Agujero de paso: el tornillo pasa sin apretar, así las piezas quedan unidas.",
            "Agujero roscado: se taladra con la broca para roscar y luego se rosca con un macho.",
            "Agujero piloto: más estrecho que la rosca, para que el tornillo para madera abra su propia rosca."]),
        "pt": ("Os três tipos de furo", [
            "Furo de passagem: o parafuso passa folgado, e assim as peças ficam unidas.",
            "Furo roscado: feito com a broca para rosca e depois roscado com um macho.",
            "Furo piloto: mais estreito que a rosca, para o parafuso para madeira abrir a própria rosca."]),
        "de": ("Die drei Arten von Löchern", [
            "Durchgangsloch: Die Schraube geht frei hindurch, so werden die Teile zusammengezogen.",
            "Gewindebohrung: mit dem Kernlochbohrer gebohrt und dann mit einem Gewindebohrer geschnitten.",
            "Vorbohrung: kleiner als das Gewinde, damit die Holzschraube ihr Gewinde selbst schneidet."]),
        "fr": ("Les trois types de trou", [
            "Trou de passage : la vis le traverse librement, ce qui serre les pièces ensemble.",
            "Trou taraudé : percé avec le foret de taraudage, puis fileté avec un taraud.",
            "Avant-trou : plus étroit que le filet, pour que la vis à bois taille son propre filetage."]),
        "ja": ("3種類の穴", [
            "通し穴:ねじが自由に通り、部品を締め付けられます。",
            "タップ穴:タップ下穴径でドリルし、タップでねじ山を切ります。",
            "下穴:ねじ山より細く、木ねじが自分でねじ山を切ります。"]),
    },
    "machine-vs-wood": {
        "en": ("A wood screw and a machine screw compared", [
            "Tapered point that cuts into the wood.",
            "Deep, widely spaced thread, often with a smooth shank under the head.",
            "Straight shank with a fine, even thread.",
            "Blunt end that threads into a nut or a tapped hole."]),
        "es": ("Un tornillo para madera y un tornillo de máquina, comparados", [
            "Punta cónica que se clava en la madera.",
            "Rosca profunda y muy espaciada, a menudo con una parte lisa bajo la cabeza.",
            "Caña recta con rosca fina y uniforme.",
            "Extremo romo que se enrosca en una tuerca o en un agujero roscado."]),
        "pt": ("Um parafuso para madeira e um parafuso de máquina, comparados", [
            "Ponta cônica que penetra na madeira.",
            "Rosca profunda e bem espaçada, muitas vezes com uma parte lisa sob a cabeça.",
            "Corpo reto com rosca fina e uniforme.",
            "Ponta romba que rosqueia em uma porca ou em um furo roscado."]),
        "de": ("Holzschraube und Maschinenschraube im Vergleich", [
            "Konische Spitze, die sich ins Holz schneidet.",
            "Tiefes Gewinde mit großem Abstand, oft mit glattem Schaft unter dem Kopf.",
            "Gerader Schaft mit feinem, gleichmäßigem Gewinde.",
            "Stumpfes Ende, das in eine Mutter oder Gewindebohrung geschraubt wird."]),
        "fr": ("Une vis à bois et une vis à métaux comparées", [
            "Pointe conique qui s'enfonce dans le bois.",
            "Filet profond et très espacé, souvent avec une partie lisse sous la tête.",
            "Tige droite avec un filet fin et régulier.",
            "Extrémité plate qui se visse dans un écrou ou un trou taraudé."]),
        "ja": ("木ねじと小ねじの比較", [
            "木に食い込む先細りの先端。",
            "ねじ山が深く間隔が広い。頭の下にねじ山のない部分があることも多い。",
            "まっすぐな軸に細かく均一なねじ山。",
            "ナットやタップ穴にねじ込む平らな先端。"]),
    },
    "coarse-fine": {
        "en": ("Coarse (UNC) and fine (UNF) threads compared (schematic)", [
            "UNC (coarse): fewer threads per inch, deeper thread.",
            "UNF (fine): more threads per inch, shallower thread.",
            "P: pitch, the distance between two crests (1 ÷ TPI)."]),
        "es": ("Roscas gruesa (UNC) y fina (UNF), comparadas (esquema)", [
            "UNC (gruesa): menos hilos por pulgada y rosca más profunda.",
            "UNF (fina): más hilos por pulgada y rosca menos profunda.",
            "P: paso, la distancia entre dos crestas (1 ÷ TPI)."]),
        "pt": ("Roscas grossa (UNC) e fina (UNF), comparadas (esquema)", [
            "UNC (grossa): menos filetes por polegada e rosca mais profunda.",
            "UNF (fina): mais filetes por polegada e rosca mais rasa.",
            "P: passo, a distância entre duas cristas (1 ÷ TPI)."]),
        "de": ("Regelgewinde (UNC) und Feingewinde (UNF) im Vergleich (Schema)", [
            "UNC (Regelgewinde): weniger Gänge pro Zoll, tieferes Gewinde.",
            "UNF (Feingewinde): mehr Gänge pro Zoll, flacheres Gewinde.",
            "P: Steigung, der Abstand zwischen zwei Gewindespitzen (1 ÷ TPI)."]),
        "fr": ("Filetages à pas gros (UNC) et à pas fin (UNF) comparés (schéma)", [
            "UNC (pas gros) : moins de filets par pouce, filet plus profond.",
            "UNF (pas fin) : plus de filets par pouce, filet moins profond.",
            "P : pas, la distance entre deux sommets (1 ÷ TPI)."]),
        "ja": ("並目(UNC)と細目(UNF)の比較(模式図)", [
            "UNC(並目):1インチあたりの山数が少なく、ねじ山が深い。",
            "UNF(細目):1インチあたりの山数が多く、ねじ山が浅い。",
            "P:ピッチ。ねじ山の頂の間隔(1 ÷ TPI)。"]),
    },
}

DL = {
    "en": "Printable PDF of the inch, wood and metric charts (English)",
    "es": "PDF imprimible de las tablas en pulgadas, para madera y métrica (en inglés)",
    "pt": "PDF para imprimir das tabelas em polegadas, para madeira e métrica (em inglês)",
    "de": "Druckbares PDF der Tabellen für Zoll, Holz und metrisch (auf Englisch)",
    "fr": "PDF imprimable des tableaux en pouces, pour le bois et métriques (en anglais)",
    "ja": "インチ・木ねじ・メートルねじの一覧表を印刷用PDFで(英語)",
}
PDF = "/screw-size-chart-printable.pdf"

# where each figure goes: (page, anchor) ; anchor kinds: ("section", id) -> after its first paragraph,
# ("h2", n) -> after the first paragraph following the n-th <h2>, ("before", html) -> right before that html
PLACE = {
    "measure": ("blog/how-to-measure-a-screw-size", ("h2", 2)),
    "callout-inch": ("screw-size-chart", ("section", "machine-screws")),
    "machine-vs-wood": ("screw-size-chart", ("section", "machine-vs-wood")),
    "coarse-fine": ("screw-size-chart", ("section", "unc-vs-unf")),
    "callout-metric": ("metric-screw-size-chart", ("section", "thread-callout")),
    "holes": ("drill-bit-to-screw-size", ("before", '<h2 id="drill-charts">')),
}


def figure(l, fid):
    inner, vb = FIGS[fid](l, NAMES[l])
    cap, items = TXT[fid][l]
    fill = lambda s: s.replace("{p}", d(l, "1.25")).replace("{g}", d(l, "0.164"))
    cap = fill(cap)
    sub = fill
    lis = "".join(f"<li>{sub(t)}</li>" for t in items)
    return (f'<figure class="diagram" id="fig-{fid}"><svg class="dg" viewBox="{vb}" role="img" aria-labelledby="fig-{fid}-t">'
            f'<title id="fig-{fid}-t">{cap}</title>{inner}</svg>'
            f"<figcaption><b>{cap}</b><ol>{lis}</ol></figcaption></figure>\n")


def insert(h, fid, html, anchor):
    h = re.sub(r'<figure class="diagram" id="fig-%s">.*?</figure>\n?' % re.escape(fid), "", h, flags=re.S)
    kind, a = anchor
    if kind == "before":
        i = h.index(a)
        return h[:i] + html + h[i:]
    if kind == "section":
        i = h.index(f'<section id="{a}">')
    else:  # n-th h2
        i = [m.start() for m in re.finditer(r"<h2[ >]", h)][a - 1]
    j = h.index("</p>", i) + 4
    return h[:j] + "\n" + html.rstrip("\n") + h[j:]


def main():
    n = 0
    for l in LANGS:
        for fid, (page, anchor) in PLACE.items():
            f = fp(l, page)
            h = insert(rd(f), fid, figure(l, fid), anchor)
            wr(f, h)
            n += 1
        # PDF link, before the "On this page" box of the three chart pages
        for page in ("screw-size-chart", "metric-screw-size-chart", "drill-bit-to-screw-size"):
            f = fp(l, page)
            h = re.sub(r'<p class="dl">.*?</p>\n?', "", rd(f), flags=re.S)
            h = h.replace('<div class="toc">', f'<p class="dl"><a href="{PDF}">{DL[l]}</a></p>\n<div class="toc">', 1)
            wr(f, h)
    # CSS (replaced between markers)
    css = rd("style.css")
    css = re.sub(r"\n?/\* diagrams:start \*/.*?/\* diagrams:end \*/\n?", "\n", css, flags=re.S)
    css = css.rstrip("\n") + "\n" + CSS + "\n"
    wr("style.css", css)
    print(f"figures placed: {n}; css updated")


CSS = """/* diagrams:start */
figure.diagram{margin:1.3em 0;padding:12px 14px;border:1px solid var(--rule-2);border-radius:10px;background:var(--surface)}
figure.diagram svg{display:block;width:100%;height:auto;max-width:460px;margin:0 auto}
figure.diagram figcaption{margin-top:10px;font-size:.92rem;color:var(--ink-2)}
figure.diagram figcaption b{display:block;color:var(--ink);margin-bottom:4px}
figure.diagram ol{margin:.3em 0 0;padding-left:1.4em}figure.diagram li{margin:.2em 0}
.dg{font-family:"Arial Narrow",Arial,sans-serif}
.dg text{fill:var(--ink);font-size:13px}.dg .ttl{font-weight:bold}
.dg .big{font:600 34px ui-monospace,"SF Mono",Consolas,monospace;fill:var(--ink)}
.dg .body{fill:var(--accent-soft);stroke:var(--ink);stroke-width:1.6;stroke-linejoin:round}
.dg .plate{fill:var(--rule);stroke:var(--ink-2);stroke-width:1.4}
.dg .grain{fill:none;stroke:var(--rule-2);stroke-width:1.2}
.dg .thr{fill:none;stroke:var(--ink-2);stroke-width:1.3}
.dg .dim{fill:none;stroke:var(--accent);stroke-width:1.6}
.dg .ext{fill:none;stroke:var(--ink-3);stroke-width:1;stroke-dasharray:3 3}
.dg .ul{stroke:var(--accent);stroke-width:2.5}
.dg .mk circle{fill:var(--accent)}.dg .mk text{fill:var(--bg);font-weight:bold}
p.dl{margin:.6em 0}p.dl a{font-weight:bold}
@media print{header.site,footer,.toc,.dl,.lang,form,.chips,.copy,button{display:none!important}body{background:#fff;color:#000;font-size:11pt}a{color:#000;text-decoration:none}table{font-size:9pt}tr,figure.diagram{break-inside:avoid}h2,h3{break-after:avoid}}
/* diagrams:end */"""

if __name__ == "__main__":
    main()
