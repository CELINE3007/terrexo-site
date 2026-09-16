# -*- coding: utf-8 -*-
"""Inserts A5 a plastifier (dashboards) : votre dessin, mis en page pour la vente.

    python3 inserts.py                                  # la serie de demonstration
    python3 inserts.py --art mon-dessin.png --layout arche --palette automne \
        --title "Automne" --sub "chocolat chaud & carnet"

Chaque insert sort en PDF A5 avec 3 mm de fond perdu et des traits de coupe :
c'est ce que demandent les imprimeurs, et c'est ce qui evite le liseré blanc
apres plastification.
"""
import argparse
import os

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas as pdfcanvas

from PIL import Image, ImageChops, ImageDraw, ImageFilter

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(HERE, "fonts")

TRIM = (148 * mm, 210 * mm)          # A5
BLEED = 3 * mm                        # fond perdu
SAFE = 8 * mm                         # zone de securite (rien d'important au-dela)

FONTS = {
    "serif": "CormorantGaramond-Regular.ttf",
    "serif_it": "CormorantGaramond-Italic.ttf",
    "serif_lt": "CormorantGaramond-Light.ttf",
    "sans": "Jost-Regular.ttf",
    "script": "Italianno-Regular.ttf",      # titres calligraphies
    "hand": "Caveat-Medium.ttf",            # ecriture au feutre
}


def register_fonts():
    names = {}
    for role, fn in FONTS.items():
        name = "Ins-" + role
        pdfmetrics.registerFont(TTFont(name, os.path.join(FONT_DIR, fn)))
        names[role] = name
    return names


# --- Palettes -------------------------------------------------------------
PALETTES = {
    "girly": {
        "bg": "#F7E4DC", "panel": "#FFFBF8", "ink": "#4A3540",
        "accent": "#D98BA0", "soft": "#9C7C88", "line": "#E7C6CC",
    },
    "automne": {
        "bg": "#EFE1CD", "panel": "#FDF8F0", "ink": "#4A3B32",
        "accent": "#BE6A46", "soft": "#8A7358", "line": "#D8C2A4",
    },
    "creme": {
        "bg": "#F4F1EA", "panel": "#FFFFFF", "ink": "#3A3A34",
        "accent": "#A8A38C", "soft": "#7C7A70", "line": "#DEDACE",
    },
}


def col(p, key):
    return HexColor(PALETTES[p][key])


# --- Preparation de l'image ----------------------------------------------
def fit_cover(im, box_px):
    """Redimensionne et recadre au centre pour remplir la boite."""
    bw, bh = box_px
    scale = max(bw / im.width, bh / im.height)
    im = im.resize((max(int(im.width * scale), bw), max(int(im.height * scale), bh)),
                   Image.LANCZOS)
    left = (im.width - bw) // 2
    top = (im.height - bh) // 2
    return im.crop((left, top, left + bw, top + bh))


def fit_contain(im, box_px):
    """Redimensionne sans rien couper ; le fond de page comble le reste."""
    bw, bh = box_px
    scale = min(bw / im.width, bh / im.height)
    im = im.resize((int(im.width * scale), int(im.height * scale)), Image.LANCZOS)
    out = Image.new("RGBA", box_px, (0, 0, 0, 0))
    out.paste(im, ((bw - im.width) // 2, (bh - im.height) // 2))
    return out


def arch_mask(size, feather=2):
    """Masque en arche : rectangle surmonte d'un demi-cercle."""
    w, h = size
    m = Image.new("L", size, 0)
    d = ImageDraw.Draw(m)
    r = w // 2
    d.ellipse([0, 0, w, 2 * r], fill=255)
    d.rectangle([0, r, w, h], fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather)) if feather else m


def rounded_mask(size, radius_px, feather=1):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, size[0] - 1, size[1] - 1],
                                        radius=radius_px, fill=255)
    return m.filter(ImageFilter.GaussianBlur(feather)) if feather else m


def prepare_art(path, box_mm, shape="rect", radius_mm=0, dpi=300, fit="cover"):
    """Ouvre le dessin, l'ajuste a la boite et lui applique sa forme.

    fit="cover" remplit la boite quitte a recadrer ; fit="contain" garde tout
    le dessin (utile quand il y a une signature ou un detail pres du bord).
    """
    box_px = (int(box_mm[0] / mm / 25.4 * dpi), int(box_mm[1] / mm / 25.4 * dpi))
    src = Image.open(path).convert("RGB")
    im = (fit_contain(src, box_px) if fit == "contain"
          else fit_cover(src, box_px).convert("RGBA"))
    shape_mask = None
    if shape == "arche":
        shape_mask = arch_mask(box_px)
    elif shape == "arrondi":
        shape_mask = rounded_mask(box_px, int(radius_mm / 25.4 * dpi))
    if shape_mask is not None:
        # on combine avec la transparence deja presente (marges du mode contain)
        im.putalpha(ImageChops.multiply(im.getchannel("A"), shape_mask))
    return im


# --- Mise en page ---------------------------------------------------------
class Insert:
    def __init__(self, path, palette="girly", bleed=BLEED, marks=True,
                 brand="MY LINE PLANNER"):
        self.p = palette
        self.bleed = bleed
        self.marks = marks
        self.brand = brand
        self.f = register_fonts()
        w, h = TRIM[0] + 2 * bleed, TRIM[1] + 2 * bleed
        self.c = pdfcanvas.Canvas(path, pagesize=(w, h))
        self.W, self.H = w, h
        self.ox, self.oy = bleed, bleed          # origine du format fini

    # coordonnees exprimees dans le format fini (0,0 = coin bas gauche apres coupe)
    def X(self, x_mm):
        return self.ox + x_mm * mm

    def Y(self, y_mm):
        return self.oy + y_mm * mm

    def background(self, key="bg"):
        self.c.setFillColor(col(self.p, key))
        self.c.rect(0, 0, self.W, self.H, stroke=0, fill=1)

    def art(self, img, x_mm, y_mm, w_mm, h_mm):
        self.c.drawImage(ImageReader(img), self.X(x_mm), self.Y(y_mm),
                         w_mm * mm, h_mm * mm, mask="auto")

    def text(self, x_mm, y_mm, s, font="serif", size=12, color="ink",
             align="c", tracking=0):
        c = self.c
        c.saveState()
        c.setFont(self.f[font], size)
        c.setFillColor(col(self.p, color) if isinstance(color, str) else color)
        x = self.X(x_mm)
        if align == "c":
            c.drawCentredString(x + tracking / 2, self.Y(y_mm), s, charSpace=tracking)
        elif align == "r":
            w = c.stringWidth(s, self.f[font], size) + tracking * max(len(s) - 1, 0)
            c.drawString(x - w, self.Y(y_mm), s, charSpace=tracking)
        else:
            c.drawString(x, self.Y(y_mm), s, charSpace=tracking)
        c.restoreState()

    def rule(self, x_mm, y_mm, w_mm, color="line", lw=0.6):
        c = self.c
        c.saveState()
        c.setStrokeColor(col(self.p, color))
        c.setLineWidth(lw)
        c.line(self.X(x_mm), self.Y(y_mm), self.X(x_mm + w_mm), self.Y(y_mm))
        c.restoreState()

    def frame(self, x_mm, y_mm, w_mm, h_mm, color="line", lw=0.8, radius=0):
        c = self.c
        c.saveState()
        c.setStrokeColor(col(self.p, color))
        c.setLineWidth(lw)
        if radius:
            c.roundRect(self.X(x_mm), self.Y(y_mm), w_mm * mm, h_mm * mm,
                        radius * mm, stroke=1, fill=0)
        else:
            c.rect(self.X(x_mm), self.Y(y_mm), w_mm * mm, h_mm * mm, stroke=1, fill=0)
        c.restoreState()

    def band(self, y_mm, h_mm, key="panel", alpha=0.92):
        c = self.c
        c.saveState()
        c.setFillColor(col(self.p, key))
        c.setFillAlpha(alpha)
        c.rect(0, self.Y(y_mm), self.W, h_mm * mm, stroke=0, fill=1)
        c.restoreState()

    def wordmark(self, y_mm=11, size=7, color="soft"):
        if self.brand:
            self.text(74, y_mm, self.brand.upper(), font="serif_lt", size=size,
                      color=color, align="c", tracking=size * 0.34)

    def crop_marks(self):
        """Traits de coupe : ou l'imprimeur (ou votre massicot) doit couper."""
        if not self.marks:
            return
        c = self.c
        c.saveState()
        c.setStrokeColor(HexColor("#666666"))
        c.setLineWidth(0.3)
        b, L = self.bleed, 4 * mm
        for x in (b, self.W - b):
            c.line(x, 0, x, b - 1 * mm)
            c.line(x, self.H, x, self.H - b + 1 * mm)
        for y in (b, self.H - b):
            c.line(0, y, b - 1 * mm, y)
            c.line(self.W, y, self.W - b + 1 * mm, y)
        c.restoreState()

    def save(self):
        self.crop_marks()
        self.c.showPage()
        self.c.save()


# --- Les quatre mises en page --------------------------------------------
def layout_arche(ins, art_path, title, sub):
    ins.background("bg")
    x, w = 18, 112
    y, h = 44, 148
    if art_path:
        img = prepare_art(art_path, (w * mm, h * mm), shape="arche")
        ins.art(img, x, y, w, h)
    else:
        c = ins.c
        c.saveState()
        c.setFillColor(col(ins.p, "panel"))
        c.circle(ins.X(x + w / 2), ins.Y(y + h - w / 2), w / 2 * mm, stroke=0, fill=1)
        c.rect(ins.X(x), ins.Y(y), w * mm, (h - w / 2) * mm, stroke=0, fill=1)
        c.restoreState()
        ins.text(74, y + h * 0.55, title, font="script", size=54, color="accent")
        title = ""
    if title:
        ins.text(74, 28, title, font="script", size=46, color="ink")
    if sub:
        ins.text(74, 20, sub, font="sans", size=7.5, color="soft", tracking=2.2)
    ins.wordmark()


def layout_cadre(ins, art_path, title, sub, fit="contain"):
    ins.background("bg")
    x, w = 19, 110
    y, h = 54, 126
    ins.text(74, 190, (sub or "").upper(), font="sans", size=7, color="soft",
             tracking=3)
    if art_path:
        img = prepare_art(art_path, (w * mm, h * mm), shape="arrondi", radius_mm=3,
                          fit=fit)
        ins.art(img, x, y, w, h)
    ins.frame(x - 3, y - 3, w + 6, h + 6, color="line", lw=0.7, radius=3)
    ins.text(74, 36, title, font="script", size=44, color="ink")
    ins.rule(60, 30, 28, color="line")
    ins.wordmark()


def layout_pleine(ins, art_path, title, sub):
    if art_path:
        img = prepare_art(art_path, (ins.W, ins.H))
        ins.c.drawImage(ImageReader(img), 0, 0, ins.W, ins.H, mask="auto")
    else:
        ins.background("bg")
    ins.band(0, 34, "panel", alpha=0.94)
    ins.text(74, 20, title, font="script", size=42, color="ink")
    if sub:
        ins.text(74, 13, sub, font="sans", size=6.8, color="soft", tracking=2.4)
    ins.wordmark(y_mm=6, size=6)


def layout_citation(ins, art_path, title, sub):
    ins.background("bg")
    ins.frame(10, 10, 128, 190, color="line", lw=0.8)
    lines = [l for l in (title or "").split("|")]
    y = 140
    for i, line in enumerate(lines):
        big = i == 1 and len(lines) == 3
        ins.text(74, y, line.strip(), font="script" if big else "serif_lt",
                 size=52 if big else 19, color="accent" if big else "ink",
                 tracking=0 if big else 2.4)
        y -= 20 if big else 15
    ins.rule(64, y - 2, 20, color="line")
    if sub:
        ins.text(74, y - 14, sub, font="hand", size=15, color="soft")
    ins.wordmark()


def layout_nue(ins, art_path, title, sub):
    """Le dessin seul, a fond perdu : c'est la mise en page des dashboards."""
    if art_path:
        img = prepare_art(art_path, (ins.W, ins.H))
        ins.c.drawImage(ImageReader(img), 0, 0, ins.W, ins.H, mask="auto")
    else:
        ins.background("bg")


LAYOUTS = {"nue": layout_nue, "arche": layout_arche, "cadre": layout_cadre,
           "pleine": layout_pleine, "citation": layout_citation}


def make(path, layout, palette, art, title, sub, brand, marks=True, bleed=BLEED):
    ins = Insert(path, palette=palette, brand=brand, marks=marks, bleed=bleed)
    LAYOUTS[layout](ins, art, title, sub)
    ins.save()
    print("  %s" % os.path.basename(path))


DEMO = [
    ("01_girly_arche", "arche", "girly", True, "Douce journée", "PRENDS TON TEMPS"),
    ("02_girly_cadre", "cadre", "girly", True, "Mon carnet", "ROUTINE DU MATIN"),
    ("03_girly_pleine", "pleine", "girly", True, "Belle semaine", "MY LINE PLANNER"),
    ("04_automne_arche", "arche", "automne", False, "Automne", "SAISON DOUCE"),
    ("05_automne_citation", "citation", "automne", False,
     "UNE ANNÉE SE CONSTRUIT|une ligne|À LA FOIS", "octobre, enfin"),
    ("06_creme_citation", "citation", "creme", False,
     "FAIS-EN|ta saison|PRÉFÉRÉE", "un jour après l'autre"),
]


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--art", default="", help="votre dessin (.png ou .jpg, 300 dpi)")
    p.add_argument("--layout", choices=sorted(LAYOUTS), default="")
    p.add_argument("--palette", choices=sorted(PALETTES), default="girly")
    p.add_argument("--title", default="Douce journée")
    p.add_argument("--sub", default="")
    p.add_argument("--brand", default="MY LINE PLANNER")
    p.add_argument("--name", default="insert")
    p.add_argument("--no-marks", action="store_false", dest="marks",
                   help="sans traits de coupe ni fond perdu")
    p.add_argument("--out", default=os.path.join(HERE, "export", "inserts"))
    o = p.parse_args(argv)
    os.makedirs(o.out, exist_ok=True)
    bleed = BLEED if o.marks else 0

    if o.layout:
        make(os.path.join(o.out, "%s.pdf" % o.name), o.layout, o.palette,
             o.art or None, o.title, o.sub, o.brand, o.marks, bleed)
        return
    print("Serie de demonstration :")
    for name, layout, palette, needs_art, title, sub in DEMO:
        art = o.art if (needs_art and o.art) else None
        make(os.path.join(o.out, "%s.pdf" % name), layout, palette, art,
             title, sub, o.brand, o.marks, bleed)


if __name__ == "__main__":
    main()
