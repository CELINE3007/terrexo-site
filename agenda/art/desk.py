# -*- coding: utf-8 -*-
"""L'illustration « bureau » : livres, pot a crayons, carnet, rouge a levres.

Redessine au trait, dans l'esprit du croquis d'origine mais avec une palette
resserree, un trait d'epaisseur variable et une ombre unique.

    python3 art/desk.py --palette girly --out inserts/art/desk-girly.png
"""
import argparse
import math
import os
import sys

from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from brush import (INK, bezier, hand, ink_stroke, paint, paper, shape_mask,  # noqa
                   soft_shadow)

HERE = os.path.dirname(os.path.abspath(__file__))
FONT_DIR = os.path.join(os.path.dirname(HERE), "fonts")

PALETTES = {
    "girly": {
        "paper": ((250, 243, 236), (245, 230, 221)),
        "a": (243, 200, 210),      # rose poudre
        "b": (220, 207, 238),      # lilas
        "c": (207, 226, 238),      # bleu glacier
        "d": (251, 242, 230),      # creme
        "accent": (214, 67, 107),  # fuchsia
        "gold": (201, 162, 39),
        "ink": INK,
    },
    "automne": {
        "paper": ((245, 236, 221), (236, 220, 197)),
        "a": (217, 138, 99),       # terracotta
        "b": (227, 183, 120),      # ocre
        "c": (169, 116, 79),       # brun chaud
        "d": (243, 229, 208),      # creme
        "accent": (180, 82, 58),
        "gold": (176, 138, 62),
        "ink": (48, 38, 32),
    },
}


def font(name, size):
    return ImageFont.truetype(os.path.join(FONT_DIR, name), int(size))


# --- Objets ---------------------------------------------------------------
def book(cv, P, x0, x1, ytop, ground, color, tilt=0.0, seed=1, lw=9,
         pages="right"):
    """Un livre debout, legerement penche, avec sa tranche de pages."""
    dx = (ground - ytop) * tilt
    body = [(x0, ground), (x1, ground), (x1 + dx, ytop), (x0 + dx, ytop)]
    pts = hand(body, amp=lw * 0.28, seed=seed, closed=True, step=lw * 2.2)
    m = paint(cv, pts, color, light=0.20, angle="v", seed=seed)
    soft_shadow(cv, m, offset=(int(lw * 1.4), int(lw * 1.7)), blur=int(lw * 3),
                alpha=46)
    paint(cv, pts, color, light=0.20, angle="v", seed=seed)
    # tranche de pages, plus claire, du cote choisi
    t = (x1 - x0) * 0.17
    if pages == "right":
        edge = [(x1 - t, ground), (x1, ground), (x1 + dx, ytop), (x1 - t + dx, ytop)]
    else:
        edge = [(x0, ground), (x0 + t, ground), (x0 + t + dx, ytop), (x0 + dx, ytop)]
    paint(cv, hand(edge, amp=lw * 0.2, seed=seed + 7, closed=True, step=lw * 2),
          P["d"], light=0.10, angle="h", seed=seed + 3)
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed)
    ink_stroke(cv, hand([edge[0], edge[3]], amp=lw * 0.2, seed=seed + 11,
                        step=lw * 2), width=max(lw - 3, 2), color=P["ink"],
               seed=seed + 2, alpha=170)
    return (x0 + dx, ytop, x1 + dx, ground)


def spine_text(cv, P, box, text, fnt, color=None, size_ratio=0.72):
    """Un mot ecrit a la verticale sur la tranche d'un livre."""
    x0, ytop, x1, ground = box
    w = int(x1 - x0)
    size = w * size_ratio
    f = font(fnt, size)
    tmp = Image.new("RGBA", (int((ground - ytop) * 0.95), int(size * 1.6)),
                    (0, 0, 0, 0))
    d = ImageDraw.Draw(tmp)
    d.text((0, 0), text, font=f, fill=(color or P["ink"]) + (255,))
    bbox = tmp.getbbox()
    if bbox:
        tmp = tmp.crop(bbox)
    tmp = tmp.rotate(-90, expand=True, resample=Image.BICUBIC)
    cx = int((x0 + x1) / 2 - tmp.width / 2)
    cy = int(ytop + (ground - ytop) * 0.5 - tmp.height / 2)
    cv.alpha_composite(tmp, (cx, cy))


def heart(cv, P, cx, cy, r, color, lw=5, seed=5):
    pts = []
    for i in range(41):
        t = math.pi * 2 * i / 40
        x = 16 * math.sin(t) ** 3
        y = -(13 * math.cos(t) - 5 * math.cos(2 * t) - 2 * math.cos(3 * t)
              - math.cos(4 * t))
        pts.append((cx + x * r / 16, cy + y * r / 13))
    pts = hand(pts, amp=lw * 0.18, seed=seed, step=lw * 1.6)
    paint(cv, pts, color, light=0.14, seed=seed)
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed, passes=1)


def bow(cv, P, cx, cy, w, color, lw=6, seed=9, dots=True):
    """Un noeud : deux boucles bien rondes, un petit centre, deux rubans."""
    h = w * 0.74
    left = (bezier((cx - w * 0.10, cy - h * 0.06),
                   (cx - w * 0.62, cy - h * 0.66), (cx - w * 0.78, cy - h * 0.10),
                   (cx - w * 0.46, cy + h * 0.16), 26)
            + bezier((cx - w * 0.46, cy + h * 0.16),
                     (cx - w * 0.30, cy + h * 0.34), (cx - w * 0.20, cy + h * 0.22),
                     (cx - w * 0.10, cy + h * 0.06), 18))
    right = [(2 * cx - x, y) for x, y in left]
    tail1 = [(cx - w * 0.06, cy + h * 0.06), (cx - w * 0.34, cy + h * 0.86),
             (cx - w * 0.14, cy + h * 0.92), (cx + w * 0.01, cy + h * 0.18)]
    tail2 = [(cx + w * 0.06, cy + h * 0.06), (cx + w * 0.36, cy + h * 0.82),
             (cx + w * 0.16, cy + h * 0.92), (cx - w * 0.01, cy + h * 0.18)]
    for i, shape in enumerate((tail1, tail2, left, right)):
        pts = hand(shape, amp=lw * 0.20, seed=seed + i, closed=True, step=lw * 1.5)
        paint(cv, pts, color, light=0.20, seed=seed + i)
        ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed + i, passes=1)
    knot = [(cx - w * 0.09, cy - h * 0.13), (cx + w * 0.09, cy - h * 0.13),
            (cx + w * 0.11, cy + h * 0.13), (cx - w * 0.11, cy + h * 0.13)]
    pts = hand(knot, amp=lw * 0.18, seed=seed + 20, closed=True, step=lw * 1.2)
    paint(cv, pts, color, light=0.08, seed=seed + 20)
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed + 21, passes=1)
    if dots:
        d = ImageDraw.Draw(cv, "RGBA")
        import random
        rng = random.Random(seed)
        for _ in range(30):
            a = rng.uniform(0, 6.28)
            rr = rng.uniform(0.12, 0.58) * w
            px, py = cx + math.cos(a) * rr, cy + math.sin(a) * rr * 0.80
            s_ = w * 0.020
            d.ellipse([px - s_, py - s_, px + s_, py + s_],
                      fill=P["accent"] + (185,))


def cup(cv, P, x0, x1, ytop, ybot, seed=31, lw=9):
    """Le pot a crayons raye, avec son noeud."""
    inset = (x1 - x0) * 0.09
    body = [(x0 + inset, ybot), (x1 - inset, ybot), (x1, ytop), (x0, ytop)]
    pts = hand(body, amp=lw * 0.26, seed=seed, closed=True, step=lw * 2)
    m = shape_mask(cv.size, pts)
    soft_shadow(cv, m, offset=(int(lw * 1.6), int(lw * 1.8)), blur=int(lw * 3.4),
                alpha=50)
    paint(cv, pts, P["d"], light=0.12, angle="h", seed=seed)
    # rayures horizontales, tenues par le masque du pot
    stripes = Image.new("RGBA", cv.size, (0, 0, 0, 0))
    ds = ImageDraw.Draw(stripes, "RGBA")
    h = ybot - ytop
    n = 9
    for i in range(n):
        y = ytop + h * (0.14 + 0.093 * i)
        th = h * (0.030 if i % 2 else 0.052)
        band = hand([(x0 - 20, y), (x1 + 20, y)], amp=lw * 0.2, seed=seed + i,
                    step=lw * 2)
        ds.line(band, fill=P["a"] + (215 if i % 2 == 0 else 150,), width=int(th))
    cv.alpha_composite(Image.composite(stripes,
                                       Image.new("RGBA", cv.size, (0, 0, 0, 0)), m))
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed + 1)
    # ellipse d'ouverture
    rim = []
    rx, ry = (x1 - x0) / 2, (ybot - ytop) * 0.055
    cx, cy = (x0 + x1) / 2, ytop
    for i in range(49):
        t = 6.283 * i / 48
        rim.append((cx + math.cos(t) * rx, cy + math.sin(t) * ry))
    rim = hand(rim, amp=lw * 0.18, seed=seed + 4, step=lw * 1.6)
    paint(cv, rim, P["d"], light=0.08, seed=seed + 5)
    ink_stroke(cv, rim, width=max(lw - 2, 3), color=P["ink"], seed=seed + 6)
    bow(cv, P, cx, ytop + (ybot - ytop) * 0.33, (x1 - x0) * 0.52, P["d"],
        lw=lw - 3, seed=seed + 8)


def pencil(cv, P, x0, y0, x1, y1, color, lw=6, seed=51, tip=True):
    """Un crayon : corps allonge, pointe coupee."""
    ang = math.atan2(y1 - y0, x1 - x0)
    nx, ny = -math.sin(ang), math.cos(ang)
    w = lw * 1.9
    tipx, tipy = x1 - math.cos(ang) * lw * 3.0, y1 - math.sin(ang) * lw * 3.0
    body = [(x0 + nx * w, y0 + ny * w), (tipx + nx * w, tipy + ny * w),
            (tipx - nx * w, tipy - ny * w), (x0 - nx * w, y0 - ny * w)]
    pts = hand(body, amp=lw * 0.2, seed=seed, closed=True, step=lw * 1.6)
    m = shape_mask(cv.size, pts)
    soft_shadow(cv, m, offset=(int(lw), int(lw * 1.2)), blur=int(lw * 2.4), alpha=40)
    paint(cv, pts, color, light=0.18, seed=seed)
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed + 1, passes=1)
    if tip:
        cone = [(tipx + nx * w, tipy + ny * w), (x1, y1), (tipx - nx * w, tipy - ny * w)]
        cpts = hand(cone, amp=lw * 0.18, seed=seed + 2, closed=True, step=lw * 1.4)
        paint(cv, cpts, P["d"], light=0.10, seed=seed + 3)
        ink_stroke(cv, cpts, width=lw, color=P["ink"], seed=seed + 4, passes=1)


def lipstick(cv, P, cx, ybot, w, h, seed=71, lw=7):
    """Le rouge a levres : etui clair, baton biseaute."""
    case = [(cx - w / 2, ybot), (cx + w / 2, ybot), (cx + w / 2, ybot - h * 0.55),
            (cx - w / 2, ybot - h * 0.55)]
    pts = hand(case, amp=lw * 0.22, seed=seed, closed=True, step=lw * 1.8)
    m = shape_mask(cv.size, pts)
    soft_shadow(cv, m, offset=(int(lw), int(lw * 1.3)), blur=int(lw * 2.6), alpha=44)
    paint(cv, pts, P["a"], light=0.16, seed=seed)
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed + 1, passes=1)
    stick = [(cx - w * 0.36, ybot - h * 0.55), (cx + w * 0.36, ybot - h * 0.55),
             (cx + w * 0.36, ybot - h * 0.86), (cx + w * 0.02, ybot - h),
             (cx - w * 0.36, ybot - h * 0.90)]
    spts = hand(stick, amp=lw * 0.2, seed=seed + 5, closed=True, step=lw * 1.6)
    paint(cv, spts, P["accent"], light=0.22, seed=seed + 6)
    ink_stroke(cv, spts, width=lw, color=P["ink"], seed=seed + 7, passes=1)


def perfume(cv, P, cx, ybot, w, h, color, seed=121, lw=8):
    """Un flacon : corps arrondi, col, bouchon et poire de vaporisateur."""
    bw = w / 2
    top = ybot - h
    body = (bezier((cx - bw, ybot), (cx - bw * 1.14, ybot - h * 0.42),
                   (cx - bw * 1.02, top + h * 0.14), (cx - bw * 0.46, top), 22)
            + bezier((cx - bw * 0.46, top), (cx - bw * 0.16, top - h * 0.04),
                     (cx + bw * 0.16, top - h * 0.04), (cx + bw * 0.46, top), 12)
            + bezier((cx + bw * 0.46, top), (cx + bw * 1.02, top + h * 0.14),
                     (cx + bw * 1.14, ybot - h * 0.42), (cx + bw, ybot), 22))
    pts = hand(body, amp=lw * 0.22, seed=seed, closed=True, step=lw * 1.8)
    m = shape_mask(cv.size, pts)
    soft_shadow(cv, m, offset=(int(lw * 1.5), int(lw * 1.7)), blur=int(lw * 3.2),
                alpha=48)
    paint(cv, pts, color, light=0.22, angle="v", seed=seed)
    ink_stroke(cv, pts, width=lw, color=P["ink"], seed=seed + 1)
    # col + bouchon
    neck = [(cx - bw * 0.22, top + h * 0.01), (cx + bw * 0.22, top + h * 0.01),
            (cx + bw * 0.20, top - h * 0.10), (cx - bw * 0.20, top - h * 0.10)]
    npts = hand(neck, amp=lw * 0.18, seed=seed + 4, closed=True, step=lw * 1.4)
    paint(cv, npts, P["d"], light=0.10, seed=seed + 5)
    ink_stroke(cv, npts, width=lw - 1, color=P["ink"], seed=seed + 6, passes=1)
    cap = [(cx - bw * 0.40, top - h * 0.10), (cx + bw * 0.40, top - h * 0.10),
           (cx + bw * 0.34, top - h * 0.30), (cx - bw * 0.34, top - h * 0.30)]
    cpts = hand(cap, amp=lw * 0.18, seed=seed + 7, closed=True, step=lw * 1.4)
    paint(cv, cpts, P["gold"], light=0.26, seed=seed + 8)
    ink_stroke(cv, cpts, width=lw - 1, color=P["ink"], seed=seed + 9, passes=1)
    # poire du vaporisateur, a droite
    bx, by, br = cx + bw * 1.02, top - h * 0.10, w * 0.26
    bulb = [(bx + math.cos(6.283 * k / 28) * br,
             by + math.sin(6.283 * k / 28) * br * 0.86) for k in range(29)]
    bpts = hand(bulb, amp=lw * 0.16, seed=seed + 10, step=lw * 1.3)
    paint(cv, bpts, P["a"], light=0.24, seed=seed + 11)
    ink_stroke(cv, bpts, width=lw - 2, color=P["ink"], seed=seed + 12, passes=1)
    tube = bezier((cx + bw * 0.36, top - h * 0.24), (cx + bw * 0.70, top - h * 0.26),
                  (bx - br * 0.7, by - br * 1.0), (bx - br * 0.78, by - br * 0.25), 18)
    ink_stroke(cv, hand(tube, amp=lw * 0.14, seed=seed + 13, step=lw * 1.2),
               width=max(lw - 4, 2), color=P["ink"], seed=seed + 14, passes=1)


def rot(p, c, a):
    s, co = math.sin(a), math.cos(a)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * co - y * s, c[1] + x * s + y * co)


def notebook(cv, P, cx, cy, w, h, angle=-0.09, seed=91, lw=9, line1="", line2="",
             script="Caveat-Medium.ttf"):
    """Le carnet a spirale, pose a plat, avec son mot ecrit a la main."""
    c = (cx, cy)
    corners = [(cx - w / 2, cy - h / 2), (cx + w / 2, cy - h / 2),
               (cx + w / 2, cy + h / 2), (cx - w / 2, cy + h / 2)]
    corners = [rot(p, c, angle) for p in corners]
    # tranche des pages, legerement decalee vers le bas
    pages = [(x, y + lw * 2.2) for x, y in corners]
    ppts = hand(pages, amp=lw * 0.22, seed=seed, closed=True, step=lw * 2)
    m = shape_mask(cv.size, ppts)
    soft_shadow(cv, m, offset=(int(lw * 1.8), int(lw * 2)), blur=int(lw * 3.6),
                alpha=52)
    paint(cv, ppts, P["d"], light=0.10, angle="h", seed=seed + 1)
    ink_stroke(cv, ppts, width=lw - 2, color=P["ink"], seed=seed + 2, passes=1)
    cpts = hand(corners, amp=lw * 0.24, seed=seed + 3, closed=True, step=lw * 2)
    paint(cv, cpts, P["a"], light=0.20, angle="h", seed=seed + 4)
    ink_stroke(cv, cpts, width=lw, color=P["ink"], seed=seed + 5)
    # spirale le long du bord gauche
    top_l, bot_l = corners[0], corners[3]
    n = 13
    for i in range(n):
        t = (i + 0.5) / n
        px = top_l[0] + (bot_l[0] - top_l[0]) * t
        py = top_l[1] + (bot_l[1] - top_l[1]) * t
        r = lw * 1.5
        ring = []
        for k in range(29):
            a = 6.283 * k / 28
            ring.append((px + math.cos(a) * r * 1.5 - lw * 0.2,
                         py + math.sin(a) * r * 0.55))
        ink_stroke(cv, hand(ring, amp=lw * 0.16, seed=seed + 10 + i, step=lw * 1.2),
                   width=max(lw - 4, 3), color=P["ink"], seed=seed + 20 + i, passes=1)
    # le mot manuscrit
    if line1 or line2:
        size = w * 0.115
        layer = Image.new("RGBA", (int(w * 1.2), int(h * 0.9)), (0, 0, 0, 0))
        d = ImageDraw.Draw(layer)
        f = font(script, size)
        d.text((w * 0.12, 0), line1, font=f, fill=P["gold"] + (255,))
        d.text((w * 0.20, size * 1.05), line2, font=f, fill=P["gold"] + (255,))
        layer = layer.rotate(-math.degrees(angle), expand=True, resample=Image.BICUBIC)
        cv.alpha_composite(layer, (int(cx - w * 0.40), int(cy - h * 0.34)))


def signature(cv, P, x, y, text, size, fnt="Italianno-Regular.ttf", color=None):
    layer = Image.new("RGBA", (int(size * len(text) * 0.75) + 40, int(size * 1.8)),
                      (0, 0, 0, 0))
    ImageDraw.Draw(layer).text((10, 0), text, font=font(fnt, size),
                               fill=(color or P["ink"]) + (255,))
    bbox = layer.getbbox()
    if bbox:
        layer = layer.crop(bbox)
    cv.alpha_composite(layer, (int(x), int(y)))
    return layer.size


# --- Scene ----------------------------------------------------------------
def compose(palette="girly", brand="My Line Planner", width=1748, height=2480,
            ss=2, script_line=("chasing", "daylight")):
    P = PALETTES[palette]
    W, H = width * ss, height * ss
    cv = paper((W, H), base=P["paper"][0], warm=P["paper"][1])
    lw = 9 * ss * (width / 1748.0)

    ground = H * 0.792
    # --- les livres, du fond vers l'avant
    specs = [  # (x0, x1, ytop, couleur, inclinaison, pages)
        (0.098, 0.212, 0.196, P["b"], 0.034, "right"),
        (0.206, 0.300, 0.286, P["c"], 0.020, "right"),
        (0.296, 0.372, 0.150, P["d"], -0.012, "left"),
        (0.368, 0.508, 0.128, P["a"], 0.006, "right"),
        (0.502, 0.606, 0.232, P["d"], -0.016, "left"),
        (0.600, 0.752, 0.176, P["b"], -0.030, "left"),
    ]
    boxes = []
    for i, (a, b, t, colr, tilt, pages) in enumerate(specs):
        boxes.append(book(cv, P, W * a, W * b, H * t, ground, colr, tilt=tilt,
                          seed=10 + i * 7, lw=lw, pages=pages))
    # le nom de la marque sur la plus large tranche
    spine_text(cv, P, boxes[3], brand.upper(), "CormorantGaramond-Light.ttf",
               color=P["ink"], size_ratio=0.32)
    heart(cv, P, W * 0.252, H * 0.352, W * 0.032, P["a"], lw=lw * 0.6, seed=77)
    bow(cv, P, W * 0.676, H * 0.268, W * 0.082, P["d"], lw=lw * 0.55, seed=83,
        dots=False)

    # --- le flacon, qui tient la droite
    perfume(cv, P, W * 0.848, ground, W * 0.172, H * 0.268, P["a"], seed=121,
            lw=lw * 0.9)

    # --- le pot a crayons et ce qu'il contient
    pencil(cv, P, W * 0.190, H * 0.600, W * 0.232, H * 0.300, P["b"], lw=lw * 0.62,
           seed=55)
    pencil(cv, P, W * 0.268, H * 0.600, W * 0.300, H * 0.346, P["accent"],
           lw=lw * 0.55, seed=61)
    pencil(cv, P, W * 0.320, H * 0.600, W * 0.346, H * 0.392, P["c"], lw=lw * 0.5,
           seed=67)
    cup(cv, P, W * 0.108, W * 0.358, H * 0.548, H * 0.822, seed=31, lw=lw)

    # --- le carnet, au premier plan
    notebook(cv, P, W * 0.600, H * 0.800, W * 0.560, H * 0.242, angle=-0.075,
             seed=91, lw=lw, line1=script_line[0], line2=script_line[1])
    bow(cv, P, W * 0.408, H * 0.845, W * 0.070, P["d"], lw=lw * 0.5, seed=131,
        dots=False)
    pencil(cv, P, W * 0.470, H * 0.902, W * 0.768, H * 0.832, P["a"], lw=lw * 0.55,
           seed=101)

    # --- les petits objets
    lipstick(cv, P, W * 0.128, H * 0.912, W * 0.072, H * 0.098, seed=71,
             lw=lw * 0.75)
    heart(cv, P, W * 0.828, H * 0.722, W * 0.024, P["accent"], lw=lw * 0.5, seed=111)

    # --- la signature de la marque
    signature(cv, P, W * 0.565, H * 0.936, brand, size=H * 0.046, color=P["ink"])

    return cv.resize((width, height), Image.LANCZOS).convert("RGB")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--palette", choices=sorted(PALETTES), default="girly")
    p.add_argument("--brand", default="My Line Planner")
    p.add_argument("--line1", default="chasing")
    p.add_argument("--line2", default="daylight")
    p.add_argument("--width", type=int, default=1748)   # A5 a 300 dpi
    p.add_argument("--height", type=int, default=2480)
    p.add_argument("--ss", type=int, default=2, help="suréchantillonnage")
    p.add_argument("--out", default="")
    o = p.parse_args(argv)
    out = o.out or os.path.join(os.path.dirname(HERE), "inserts", "art",
                                "desk-%s.png" % o.palette)
    os.makedirs(os.path.dirname(out), exist_ok=True)
    im = compose(o.palette, o.brand, o.width, o.height, o.ss, (o.line1, o.line2))
    im.save(out, dpi=(300, 300))
    print(out, im.size)


if __name__ == "__main__":
    main()
