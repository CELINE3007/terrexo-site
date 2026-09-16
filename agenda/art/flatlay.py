# -*- coding: utf-8 -*-
"""Page decor « vanity » : objets graphiques au trait epais, facon illustration mode.

Registre volontairement different du croquis au crayon : contours noirs
appuyes, aplats francs, contraste fort, collage papier.

    python3 art/flatlay.py --palette girly --out inserts/art/vanity-girly.png
"""
import argparse
import math
import os
import random
import sys

from PIL import Image, ImageDraw, ImageFilter, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brush import (bezier, hand, ink_stroke, paint, paper, shape_mask,  # noqa
                   soft_shadow, streaks)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(os.path.dirname(HERE), "fonts")

PALETTES = {
    "girly": {
        "paper": ((214, 190, 172), (203, 176, 158)),   # greige chaud
        "panel": (242, 210, 210),                      # blush
        "panel2": (249, 233, 228),
        "noir": (26, 22, 21),
        "rose": (233, 165, 175),
        "rose_v": (206, 110, 130),
        "or": (198, 160, 92),
        "creme": (250, 244, 236),
        "ink": (22, 19, 18),
    },
    "automne": {
        "paper": ((208, 186, 158), (193, 168, 139)),
        "panel": (226, 190, 158),
        "panel2": (241, 223, 200),
        "noir": (34, 26, 22),
        "rose": (199, 120, 82),
        "rose_v": (160, 74, 52),
        "or": (182, 140, 70),
        "creme": (247, 238, 224),
        "ink": (30, 24, 20),
    },
}


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), int(size))


def bold(cv, pts, fill, P, lw, seed=0, shadow=True, light=0.10, angle="v",
         shine=None):
    """Une forme pleine, cernee d'un trait noir epais. La base du style."""
    m = shape_mask(cv.size, pts, blur=0.7)
    if shadow:
        soft_shadow(cv, m, offset=(int(lw * 1.1), int(lw * 1.3)),
                    blur=int(lw * 2.6), alpha=58, color=(92, 70, 62))
    paint(cv, pts, fill, light=light, angle=angle, seed=seed)
    if shine:
        sh = Image.new("RGBA", cv.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(sh, "RGBA")
        d.line(shine[0], fill=shine[1] + (shine[2],), width=int(lw * 1.6))
        cv.alpha_composite(Image.composite(
            sh.filter(ImageFilter.GaussianBlur(lw * 0.5)),
            Image.new("RGBA", cv.size, (0, 0, 0, 0)), m))
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed, passes=1, taper=0.16)
    return m


def curve(*pts, n=26):
    """Raccourci : suite de beziers passant par des points de controle donnes."""
    out = []
    for i in range(0, len(pts) - 3, 3):
        out += bezier(pts[i], pts[i + 1], pts[i + 2], pts[i + 3], n)
    return out


# --- Objets ---------------------------------------------------------------
def camellia(cv, P, cx, cy, r, lw, seed=3, color=None):
    """La fleur graphique : trois couronnes de petales en goutte, coeur spirale."""
    color = color or P["noir"]

    def petal(a, reach, wide):
        """Un petale oriente vers l'angle a."""
        ux, uy = math.cos(a), math.sin(a)
        vx, vy = -uy, ux
        base = (cx + ux * reach * 0.16, cy + uy * reach * 0.16)
        tip = (cx + ux * reach, cy + uy * reach)
        return (bezier(base,
                       (base[0] + vx * wide, base[1] + vy * wide),
                       (tip[0] + vx * wide * 0.62, tip[1] + vy * wide * 0.62),
                       tip, 20)
                + bezier(tip,
                         (tip[0] - vx * wide * 0.62, tip[1] - vy * wide * 0.62),
                         (base[0] - vx * wide, base[1] - vy * wide),
                         base, 20))

    rings = ((1.00, 8, 0.00, 0.42), (0.70, 7, 0.44, 0.34), (0.44, 5, 0.95, 0.26))
    for ri, (scale, n, phase, wide) in enumerate(rings):
        for i in range(n):
            a = 6.283 * i / n + phase
            pts = hand(petal(a, r * scale, r * wide * scale),
                       amp=lw * 0.09, seed=seed + ri * 10 + i, step=lw * 1.2)
            paint(cv, pts, color, light=0.12 + ri * 0.10, seed=seed + ri * 5 + i)
            ink_stroke(cv, pts, width=lw * 0.8, color=P["ink"],
                       seed=seed + ri * 3 + i, passes=1, taper=0.14)
    spiral = []
    for k in range(60):
        t = k / 59
        spiral.append((cx + math.cos(t * 8.0) * r * 0.22 * (1 - t * 0.9),
                       cy + math.sin(t * 8.0) * r * 0.20 * (1 - t * 0.9)))
    ink_stroke(cv, spiral, width=lw * 0.7, color=P["ink"], seed=seed + 99,
               passes=1, taper=0.2)


def heel(cv, P, x, ybase, length, lw, seed=11, flip=False, body=None, sole=None):
    """Un escarpin de profil. `length` = longueur du soulier, pas sa hauteur."""
    body = body or P["noir"]
    sole = sole or P["rose"]
    s_ = length / 100.0

    def T(px, py):
        return (x + (-px if flip else px) * s_, ybase - py * s_)

    # talon aiguille, dessine en premier : il passe derriere le corps
    spike = (curve(T(47, 16), T(45, 10), T(43, 4), T(42, 0), n=12)
             + curve(T(42, 0), T(38, 0), T(36, 1), T(37, 3), n=6)
             + curve(T(37, 3), T(39, 8), T(41, 13), T(42, 19), n=12))
    bold(cv, hand(spike, amp=lw * 0.06, seed=seed + 9, closed=True, step=lw * 1.0),
         body, P, lw * 0.8, seed=seed + 9, light=0.26)

    # corps du soulier
    upper = (curve(T(98, 11), T(80, 4), T(64, 5), T(50, 13), n=18)    # semelle
             + curve(T(50, 13), T(45, 18), T(42, 26), T(40, 34), n=14)  # cambrure
             + curve(T(40, 34), T(38, 42), T(40, 50), T(46, 52), n=12)  # contrefort
             + curve(T(46, 52), T(56, 43), T(66, 31), T(76, 21), n=16)  # ouverture
             + curve(T(76, 21), T(86, 16), T(93, 12), T(98, 11), n=12))  # empeigne
    pts = hand(upper, amp=lw * 0.07, seed=seed, closed=True, step=lw * 1.2)
    bold(cv, pts, body, P, lw, seed=seed, light=0.13,
         shine=([T(54, 17), T(68, 20), T(82, 18)], (255, 255, 255), 50))

    # semelle claire
    solep = (curve(T(98, 11), T(80, 4), T(64, 5), T(50, 13), n=16)
             + curve(T(50, 13), T(64, 0), T(80, -1), T(98, 6), n=16))
    sp = hand(solep, amp=lw * 0.05, seed=seed + 5, closed=True, step=lw * 1.0)
    paint(cv, sp, sole, light=0.14, seed=seed + 6)
    ink_stroke(cv, sp, width=lw * 0.7, color=P["ink"], seed=seed + 7, passes=1,
               taper=0.12)

    # doublure de l'ouverture
    op = curve(T(47, 50), T(57, 41), T(66, 30), T(75, 22), n=16)
    ink_stroke(cv, hand(op, amp=lw * 0.05, seed=seed + 13, step=lw * 1.0),
               width=lw * 0.55, color=P["rose"], seed=seed + 14, passes=1, taper=0.2)


def lipstick(cv, P, cx, ybase, w, h, lw, seed=21):
    """Rouge a levres : etui noir, bague doree, baton biseaute."""
    case = [(cx - w / 2, ybase), (cx + w / 2, ybase),
            (cx + w / 2, ybase - h * 0.52), (cx - w / 2, ybase - h * 0.52)]
    bold(cv, hand(case, amp=lw * 0.08, seed=seed, closed=True, step=lw * 1.4),
         P["noir"], P, lw, seed=seed, light=0.14,
         shine=([(cx - w * 0.22, ybase - h * 0.06), (cx - w * 0.22, ybase - h * 0.46)],
                (255, 255, 255), 40))
    ring = [(cx - w * 0.52, ybase - h * 0.52), (cx + w * 0.52, ybase - h * 0.52),
            (cx + w * 0.52, ybase - h * 0.60), (cx - w * 0.52, ybase - h * 0.60)]
    bold(cv, hand(ring, amp=lw * 0.06, seed=seed + 3, closed=True, step=lw * 1.2),
         P["or"], P, lw * 0.9, seed=seed + 3, shadow=False, light=0.30)
    tube = [(cx - w * 0.42, ybase - h * 0.60), (cx + w * 0.42, ybase - h * 0.60),
            (cx + w * 0.42, ybase - h * 0.76), (cx - w * 0.42, ybase - h * 0.76)]
    bold(cv, hand(tube, amp=lw * 0.06, seed=seed + 5, closed=True, step=lw * 1.2),
         P["noir"], P, lw * 0.9, seed=seed + 5, shadow=False, light=0.16)
    stick = [(cx - w * 0.38, ybase - h * 0.76), (cx + w * 0.38, ybase - h * 0.76),
             (cx + w * 0.38, ybase - h * 0.92), (cx - w * 0.06, ybase - h),
             (cx - w * 0.38, ybase - h * 0.94)]
    bold(cv, hand(stick, amp=lw * 0.07, seed=seed + 7, closed=True, step=lw * 1.2),
         P["rose_v"], P, lw * 0.9, seed=seed + 7, shadow=False, light=0.24)


def flacon(cv, P, cx, ybase, w, h, lw, seed=31):
    """Flacon losange, bouchon noir : la silhouette parfum du style."""
    body = curve((cx, ybase), (cx + w * 0.62, ybase - h * 0.10),
                 (cx + w * 0.52, ybase - h * 0.48), (cx, ybase - h * 0.62), n=22) + \
        curve((cx, ybase - h * 0.62), (cx - w * 0.52, ybase - h * 0.48),
              (cx - w * 0.62, ybase - h * 0.10), (cx, ybase), n=22)
    bold(cv, hand(body, amp=lw * 0.08, seed=seed, closed=True, step=lw * 1.4),
         P["noir"], P, lw, seed=seed, light=0.16,
         shine=([(cx - w * 0.26, ybase - h * 0.14), (cx - w * 0.34, ybase - h * 0.38)],
                (255, 255, 255), 46))
    neck = [(cx - w * 0.13, ybase - h * 0.60), (cx + w * 0.13, ybase - h * 0.60),
            (cx + w * 0.11, ybase - h * 0.74), (cx - w * 0.11, ybase - h * 0.74)]
    bold(cv, hand(neck, amp=lw * 0.06, seed=seed + 3, closed=True, step=lw * 1.2),
         P["or"], P, lw * 0.85, seed=seed + 3, shadow=False, light=0.30)
    cap = curve((cx - w * 0.22, ybase - h * 0.74), (cx - w * 0.24, ybase - h * 0.92),
                (cx - w * 0.14, ybase - h * 1.0), (cx, ybase - h * 1.0), n=16) + \
        curve((cx, ybase - h * 1.0), (cx + w * 0.14, ybase - h * 1.0),
              (cx + w * 0.24, ybase - h * 0.92), (cx + w * 0.22, ybase - h * 0.74), n=16)
    bold(cv, hand(cap, amp=lw * 0.06, seed=seed + 5, closed=True, step=lw * 1.2),
         P["noir"], P, lw * 0.9, seed=seed + 5, shadow=False, light=0.18)


def brush_tool(cv, P, x0, y0, x1, y1, lw, seed=41, handle=None):
    """Pinceau de maquillage : manche, virole doree, touffe poudrée."""
    handle = handle or P["noir"]
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang), math.cos(ang)
    L = math.hypot(x1 - x0, y1 - y0)
    w = L * 0.055

    def at(t, off=0.0):
        return (x0 + (x1 - x0) * t + nx * off, y0 + (y1 - y0) * t + ny * off)

    body = [at(0.0, w * 0.75), at(0.62, w), at(0.62, -w), at(0.0, -w * 0.75)]
    bold(cv, hand(body, amp=lw * 0.07, seed=seed, closed=True, step=lw * 1.3),
         handle, P, lw, seed=seed, light=0.20)
    fer = [at(0.62, w), at(0.74, w), at(0.74, -w), at(0.62, -w)]
    bold(cv, hand(fer, amp=lw * 0.05, seed=seed + 3, closed=True, step=lw * 1.1),
         P["or"], P, lw * 0.85, seed=seed + 3, shadow=False, light=0.32)
    tuft = curve(at(0.74, w), at(0.86, w * 1.5), at(0.97, w * 1.2), at(1.0, 0), n=18) + \
        curve(at(1.0, 0), at(0.97, -w * 1.2), at(0.86, -w * 1.5), at(0.74, -w), n=18)
    bold(cv, hand(tuft, amp=lw * 0.08, seed=seed + 5, closed=True, step=lw * 1.2),
         P["rose"], P, lw * 0.9, seed=seed + 5, shadow=False, light=0.26)


def pearls(cv, P, pts, r, lw, seed=51):
    """Un rang de perles : ponctuation douce entre deux objets."""
    d = ImageDraw.Draw(cv, "RGBA")
    for i, (px, py) in enumerate(pts):
        d.ellipse([px - r, py - r, px + r, py + r], fill=P["creme"] + (255,),
                  outline=P["ink"] + (255,), width=max(int(lw * 0.45), 2))
        d.ellipse([px - r * 0.42, py - r * 0.48, px - r * 0.02, py - r * 0.08],
                  fill=(255, 255, 255, 150))


def coffee(cv, P, cx, ybase, w, h, lw, seed=91):
    """Le gobelet a emporter : corps creme, manchon et couvercle noirs."""
    body = [(cx - w * 0.40, ybase), (cx + w * 0.40, ybase),
            (cx + w * 0.50, ybase - h * 0.80), (cx - w * 0.50, ybase - h * 0.80)]
    bold(cv, hand(body, amp=lw * 0.07, seed=seed, closed=True, step=lw * 1.3),
         P["creme"], P, lw, seed=seed, light=0.10,
         shine=([(cx - w * 0.28, ybase - h * 0.10),
                 (cx - w * 0.33, ybase - h * 0.66)], (255, 255, 255), 60))
    sleeve = [(cx - w * 0.455, ybase - h * 0.26), (cx + w * 0.455, ybase - h * 0.26),
              (cx + w * 0.475, ybase - h * 0.54), (cx - w * 0.475, ybase - h * 0.54)]
    bold(cv, hand(sleeve, amp=lw * 0.05, seed=seed + 3, closed=True, step=lw * 1.1),
         P["noir"], P, lw * 0.9, seed=seed + 3, shadow=False, light=0.18)
    lid = [(cx - w * 0.54, ybase - h * 0.80), (cx + w * 0.54, ybase - h * 0.80),
           (cx + w * 0.50, ybase - h * 0.95), (cx - w * 0.50, ybase - h * 0.95)]
    bold(cv, hand(lid, amp=lw * 0.05, seed=seed + 5, closed=True, step=lw * 1.1),
         P["noir"], P, lw * 0.9, seed=seed + 5, shadow=False, light=0.20)
    top = [(cx - w * 0.44, ybase - h * 0.95), (cx + w * 0.44, ybase - h * 0.95),
           (cx + w * 0.40, ybase - h * 1.03), (cx - w * 0.40, ybase - h * 1.03)]
    bold(cv, hand(top, amp=lw * 0.05, seed=seed + 7, closed=True, step=lw * 1.1),
         P["noir"], P, lw * 0.85, seed=seed + 7, shadow=False, light=0.26)


# --- Collage --------------------------------------------------------------
def torn_paper(cv, P, x0, y0, w, h, seed=61, color=None, angle=0.0, text=True):
    """Un morceau de page arrachee, avec du faux texte imprime."""
    rng = random.Random(seed)
    top = [(x0 + w * i / 14, y0 + rng.uniform(-h * 0.012, h * 0.012)) for i in range(15)]
    bot = [(x0 + w - w * i / 14, y0 + h + rng.uniform(-h * 0.03, h * 0.03))
           for i in range(15)]
    pts = top + [(x0 + w, y0 + h * 0.5)] + bot
    layer = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    m = shape_mask(cv.size, pts, blur=1.2)
    layer.paste(streaks(cv.size, color or P["creme"], light=0.06, seed=seed), (0, 0), m)
    if text:
        t = Image.new("RGBA", cv.size, (0, 0, 0, 0))
        dt = ImageDraw.Draw(t)
        f = font("CormorantGaramond-Regular.ttf", h * 0.085)
        words = ("matin lumière carnet douceur saison lignes encre papier "
                 "heures thé velours tendre soie jardin pages ").split()
        yy = y0 + h * 0.12
        while yy < y0 + h * 0.86:
            line = " ".join(rng.choice(words) for _ in range(7))
            dt.text((x0 + w * 0.05, yy), line, font=f, fill=P["ink"] + (130,))
            yy += h * 0.125
        layer.alpha_composite(Image.composite(
            t, Image.new("RGBA", cv.size, (0, 0, 0, 0)), m))
    soft_shadow(cv, m, offset=(6, 8), blur=18, alpha=40, color=(120, 96, 84))
    if angle:
        layer = layer.rotate(angle, resample=Image.BICUBIC,
                             center=(x0 + w / 2, y0 + h / 2))
    cv.alpha_composite(layer)


def washi(cv, P, x0, y0, w, h, angle, color, seed=71, alpha=205):
    """Un bout de masking tape, pour l'esprit collage."""
    layer = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(layer, "RGBA")
    d.rectangle([x0, y0, x0 + w, y0 + h], fill=color + (alpha,))
    for i in range(int(w // max(h * 0.5, 4))):
        x = x0 + i * h * 0.5
        d.line([(x, y0), (x + h * 0.3, y0 + h)], fill=(255, 255, 255, 40),
               width=max(int(h * 0.12), 2))
    layer = layer.rotate(angle, resample=Image.BICUBIC,
                         center=(x0 + w / 2, y0 + h / 2))
    cv.alpha_composite(layer)


def panel(cv, P, x0, y0, x1, y1, color, seed=81, radius=0.0):
    pts = [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
    pts = hand(pts, amp=(x1 - x0) * 0.004, seed=seed, closed=True,
               step=(x1 - x0) * 0.03)
    m = shape_mask(cv.size, pts, blur=1.4)
    soft_shadow(cv, m, offset=(10, 12), blur=26, alpha=42, color=(110, 88, 78))
    paint(cv, pts, color, light=0.07, angle="v", seed=seed)


def script(cv, P, x, y, text, size, fnt="Italianno-Regular.ttf", color=None,
           angle=0.0):
    layer = Image.new("RGBA", (int(size * len(text) * 0.8) + 60, int(size * 2)),
                      (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((20, 0), text, font=font(fnt, size),
                               fill=(color or P["ink"]) + (255,))
    bbox = layer.getbbox()
    if bbox:
        layer = layer.crop(bbox)
    if angle:
        layer = layer.rotate(angle, expand=True, resample=Image.BICUBIC)
    cv.alpha_composite(layer, (int(x), int(y)))
    return layer.size


# --- Scene ----------------------------------------------------------------
def compose(palette="girly", brand="My Line Planner", width=1748, height=2480,
            ss=2, word="just a little"):
    P = PALETTES[palette]
    W, H = width * ss, height * ss
    cv = paper((W, H), base=P["paper"][0], warm=P["paper"][1], grain=16,
               vignette=0.14)
    lw = 17.0 * ss * (width / 1748.0)          # trait epais, assume

    panel(cv, P, W * 0.075, H * 0.075, W * 0.925, H * 0.905, P["panel"], seed=81)
    torn_paper(cv, P, W * 0.10, H * 0.105, W * 0.48, H * 0.110, seed=61, angle=-1.2)
    washi(cv, P, W * 0.115, H * 0.848, W * 0.24, H * 0.026, 2.0, P["creme"],
          alpha=175)

    camellia(cv, P, W * 0.790, H * 0.190, W * 0.150, lw * 0.8, seed=3)
    # la paire d'escarpins, tous deux dans le meme sens, l'un devant l'autre
    heel(cv, P, W * 0.140, H * 0.455, W * 0.255, lw, seed=11)
    heel(cv, P, W * 0.215, H * 0.500, W * 0.255, lw, seed=17)
    flacon(cv, P, W * 0.735, H * 0.540, W * 0.205, H * 0.165, lw, seed=31)
    pearls(cv, P, [(W * (0.500 + 0.028 * i), H * (0.585 + 0.010 * math.sin(i * 1.2)))
                   for i in range(7)], W * 0.018, lw, seed=51)
    coffee(cv, P, W * 0.225, H * 0.800, W * 0.180, H * 0.200, lw, seed=91)
    lipstick(cv, P, W * 0.455, H * 0.760, W * 0.098, H * 0.150, lw, seed=21)
    brush_tool(cv, P, W * 0.570, H * 0.845, W * 0.870, H * 0.700, lw, seed=41)

    script(cv, P, W * 0.115, H * 0.560, word, H * 0.050, color=P["ink"], angle=3)
    script(cv, P, W * 0.545, H * 0.872, brand, H * 0.040,
           fnt="CormorantGaramond-Light.ttf", color=P["ink"])
    return cv.resize((width, height), Image.LANCZOS).convert("RGB")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--palette", choices=sorted(PALETTES), default="girly")
    p.add_argument("--brand", default="My Line Planner")
    p.add_argument("--word", default="just a little")
    p.add_argument("--width", type=int, default=1748)
    p.add_argument("--height", type=int, default=2480)
    p.add_argument("--ss", type=int, default=2)
    p.add_argument("--out", default="")
    o = p.parse_args(argv)
    out = o.out or os.path.join(os.path.dirname(HERE), "inserts", "art",
                                "vanity-%s.png" % o.palette)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    compose(o.palette, o.brand, o.width, o.height, o.ss, o.word).save(
        out, dpi=(300, 300))
    print(out)


if __name__ == "__main__":
    main()
