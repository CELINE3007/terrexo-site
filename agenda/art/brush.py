# -*- coding: utf-8 -*-
"""Boite a outils de dessin : trait tremble, aplats texturés, ombres douces.

Tout est fait pour garder la main : les traits ne sont jamais parfaitement
droits, les aplats ne sont jamais parfaitement plats.
"""
import math
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter

INK = (36, 31, 29)


# --- Geometrie ------------------------------------------------------------
def lerp(a, b, t):
    return a + (b - a) * t


def bezier(p0, c0, c1, p1, n=40):
    pts = []
    for i in range(n + 1):
        t = i / n
        u = 1 - t
        x = (u ** 3 * p0[0] + 3 * u * u * t * c0[0] + 3 * u * t * t * c1[0]
             + t ** 3 * p1[0])
        y = (u ** 3 * p0[1] + 3 * u * u * t * c0[1] + 3 * u * t * t * c1[1]
             + t ** 3 * p1[1])
        pts.append((x, y))
    return pts


def densify(pts, step=14):
    """Reechantillonne un chemin pour pouvoir le trembler regulierement."""
    out = []
    for a, b in zip(pts, pts[1:]):
        d = math.hypot(b[0] - a[0], b[1] - a[1])
        n = max(int(d / step), 1)
        for i in range(n):
            out.append((lerp(a[0], b[0], i / n), lerp(a[1], b[1], i / n)))
    out.append(pts[-1])
    return out


def wobble(pts, amp=2.2, wave=0.035, seed=None):
    """Le tremble de la main : une petite onde lente + du bruit fin."""
    rng = random.Random(seed)
    phase = rng.uniform(0, 6.28)
    out, drift = [], 0.0
    for i, (x, y) in enumerate(pts):
        drift = drift * 0.82 + rng.uniform(-1, 1) * amp * 0.5
        s = math.sin(i * wave * 6.28 + phase) * amp
        out.append((x + s + drift, y + math.cos(i * wave * 5.1 + phase) * amp
                    + drift * 0.6))
    return out


def hand(pts, amp=2.2, seed=None, closed=False, step=14):
    p = list(pts) + ([pts[0]] if closed else [])
    return wobble(densify(p, step), amp=amp, seed=seed)


# --- Traits ---------------------------------------------------------------
def ink_stroke(layer, pts, width=7, color=INK, passes=2, seed=0, alpha=255,
               taper=0.42):
    """Un trait d'encre : l'epaisseur respire le long du trace, comme un feutre.

    C'est ce qui separe un dessin fait main d'un contour vectoriel.
    """
    d = ImageDraw.Draw(layer, "RGBA")
    rng = random.Random(seed)
    n = len(pts)
    if n < 2:
        return
    for k in range(passes):
        base = width * (1.0 - 0.24 * k)
        a = int(alpha * (1.0 if k == 0 else 0.5))
        ox, oy = (rng.uniform(-1, 1) * width * 0.09,
                  rng.uniform(-1, 1) * width * 0.09)
        f1, ph1 = rng.uniform(1.4, 2.6), rng.uniform(0, 6.28)
        f2, ph2 = rng.uniform(4.0, 7.0), rng.uniform(0, 6.28)
        for i in range(n - 1):
            t = i / (n - 1)
            m = (1.0 - taper * 0.5
                 + taper * 0.32 * math.sin(t * 6.283 * f1 + ph1)
                 + taper * 0.18 * math.sin(t * 6.283 * f2 + ph2))
            w = max(base * m, 1.0)
            x0, y0 = pts[i][0] + ox, pts[i][1] + oy
            x1, y1 = pts[i + 1][0] + ox, pts[i + 1][1] + oy
            d.line([(x0, y0), (x1, y1)], fill=color + (a,), width=int(round(w)))
            r = w / 2.0
            d.ellipse([x0 - r, y0 - r, x0 + r, y0 + r], fill=color + (a,))
        xe, ye = pts[-1][0] + ox, pts[-1][1] + oy
        r = base / 2.0
        d.ellipse([xe - r, ye - r, xe + r, ye + r], fill=color + (a,))


def shape_mask(size, pts, blur=0.6):
    m = Image.new("L", size, 0)
    ImageDraw.Draw(m).polygon(pts, fill=255)
    return m.filter(ImageFilter.GaussianBlur(blur)) if blur else m


# --- Aplats ---------------------------------------------------------------
def streaks(size, color, light=0.16, angle="v", seed=0, grain=10):
    """Un aplat qui garde la trace du crayon : stries douces + grain."""
    w, h = size
    im = Image.new("RGB", size, color)
    d = ImageDraw.Draw(im, "RGBA")
    rng = random.Random(seed)
    up = tuple(min(int(c + (255 - c) * light), 255) for c in color)
    dn = tuple(int(c * (1 - light * 0.55)) for c in color)
    n = max(w // 9, 8) if angle == "v" else max(h // 9, 8)
    for i in range(n):
        a = rng.randint(14, 46)
        col = up if rng.random() < 0.62 else dn
        if angle == "v":
            x = rng.uniform(0, w)
            d.line([(x, -h * 0.1), (x + rng.uniform(-w * 0.05, w * 0.05), h * 1.1)],
                   fill=col + (a,), width=rng.randint(int(w * 0.03) + 2, int(w * 0.11) + 4))
        else:
            y = rng.uniform(0, h)
            d.line([(-w * 0.1, y), (w * 1.1, y + rng.uniform(-h * 0.05, h * 0.05))],
                   fill=col + (a,), width=rng.randint(int(h * 0.03) + 2, int(h * 0.11) + 4))
    im = im.filter(ImageFilter.GaussianBlur(max(w, h) * 0.012 + 1))
    if grain:
        noise = Image.effect_noise(size, grain).convert("L").point(
            lambda v: 128 + (v - 128) * 0.35)
        im = ImageChops.overlay(im, Image.merge("RGB", (noise, noise, noise)))
    return im


def paint(canvas, pts, color, light=0.16, angle="v", seed=0, blur=0.8):
    """Remplit une forme avec un aplat texture."""
    mask = shape_mask(canvas.size, pts, blur=blur)
    canvas.paste(streaks(canvas.size, color, light=light, angle=angle, seed=seed),
                 (0, 0), mask)
    return mask


def soft_shadow(canvas, mask, offset=(10, 14), blur=26, alpha=52,
                color=(120, 96, 86)):
    """Une seule ombre portee, toujours dans le meme sens : ca pose les objets."""
    sh = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    sh.paste(color + (alpha,), (0, 0), mask.filter(ImageFilter.GaussianBlur(blur)))
    canvas.alpha_composite(sh.transform(
        canvas.size, Image.AFFINE, (1, 0, -offset[0], 0, 1, -offset[1])))


# --- Fond -----------------------------------------------------------------
def paper(size, base=(247, 240, 230), warm=(240, 226, 209), grain=14,
          vignette=0.10, seed=3):
    """Papier creme : legere variation de teinte, grain, vignetage discret."""
    w, h = size
    im = Image.new("RGB", size, base)
    top = Image.new("RGB", size, warm)
    g = Image.linear_gradient("L").resize(size)
    im = Image.composite(top, im, g.point(lambda v: int(v * 0.55)))
    noise = Image.effect_noise(size, grain).convert("L").point(
        lambda v: 128 + (v - 128) * 0.5)
    im = ImageChops.overlay(im, Image.merge("RGB", (noise, noise, noise)))
    if vignette:
        v = Image.new("L", size, 0)
        ImageDraw.Draw(v).ellipse([-w * 0.25, -h * 0.18, w * 1.25, h * 1.18], fill=255)
        v = v.filter(ImageFilter.GaussianBlur(min(w, h) * 0.12))
        dark = Image.new("RGB", size, (198, 182, 164))
        im = Image.composite(im, Image.blend(im, dark, vignette), v)
    return im.convert("RGBA")
