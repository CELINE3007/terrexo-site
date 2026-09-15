# -*- coding: utf-8 -*-
"""Primitives de dessin : titres, filets, lignes d'ecriture, mini-calendriers.

Les pages (pages.py) n'utilisent que ces briques : en modifier une change
le style partout d'un coup.
"""
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas as pdfcanvas

from .theme import PAGE_SIZES, RING_HOLES_A5, Theme


class Sheet:
    """Une feuille PDF, consciente du cote ou se trouvent les anneaux."""

    def __init__(self, path, size="a5", theme=None, brand="", guides=False, title=""):
        self.theme = theme or Theme()
        self.W, self.H = PAGE_SIZES[size]
        self.size = size
        self.brand = brand
        self.guides = guides
        self.c = pdfcanvas.Canvas(path, pagesize=(self.W, self.H))
        self.c.setTitle(title or "Planner")
        self.side = "right"
        self.pages = 0

    # -- cycle de vie ------------------------------------------------------
    def begin(self, side="right", brand_mark=True):
        """brand_mark=False : page sans la marque verticale (couverture, citation)."""
        t = self.theme
        self.side = side
        self._mark = brand_mark
        if side == "right":
            self.x0, self.x1 = t.margin_ring * mm, self.W - t.margin_out * mm
        else:
            self.x0, self.x1 = t.margin_out * mm, self.W - t.margin_ring * mm
        self.y1 = self.H - t.margin_top * mm
        self.y0 = t.margin_bottom * mm
        return self

    @property
    def w(self):
        return self.x1 - self.x0

    def finish(self):
        self._brand_mark()
        if self.guides:
            self._ring_guides()
        self.c.showPage()
        self.pages += 1

    def save(self):
        self.c.save()
        return self.pages

    def _brand_mark(self):
        if not self.brand or not getattr(self, "_mark", True):
            return
        t, c = self.theme, self.c
        c.saveState()
        c.setFillColor(t.hair)
        gutter = t.margin_ring * mm
        if self.side == "right":
            x, angle = gutter * 0.42, 90
        else:
            x, angle = self.W - gutter * 0.42, 90
        c.translate(x, self.H / 2)
        c.rotate(angle)
        c.setFont(t.sans, 4.2)
        c.drawCentredString(0, 0, self.brand.upper(), charSpace=1.2)
        c.restoreState()

    def _ring_guides(self):
        if self.size != "a5":
            return
        c, t = self.c, self.theme
        c.saveState()
        c.setStrokeColor(t.hair)
        c.setLineWidth(0.3)
        x = (t.margin_ring * mm) * 0.42 if self.side == "right" else self.W - (t.margin_ring * mm) * 0.42
        for hy in RING_HOLES_A5:
            c.circle(x, self.H - hy * mm, 1.7 * mm, stroke=1, fill=0)
        c.restoreState()

    # -- texte -------------------------------------------------------------
    def text(self, x, y, s, font=None, size=9, color=None, align="l", tracking=0):
        t, c = self.theme, self.c
        font = font or t.serif
        c.saveState()
        c.setFont(font, size)
        c.setFillColor(color or t.ink)
        if align == "c":
            c.drawCentredString(x, y, s, charSpace=tracking)
        elif align == "r":
            width = c.stringWidth(s, font, size) + tracking * max(len(s) - 1, 0)
            c.drawString(x - width, y, s, charSpace=tracking)
        else:
            c.drawString(x, y, s, charSpace=tracking)
        c.restoreState()
        return y

    def label(self, x, y, s, size=6.2, align="l", color=None, tracking=1.4, font=None):
        """Petite capitale espacee, pour les intitules de rubrique."""
        return self.text(x, y, s.upper(), font=font or self.theme.sans,
                         size=size, color=color or self.theme.soft,
                         align=align, tracking=tracking)

    def paragraph(self, x, y, s, width, size=8.5, leading=None, font=None,
                  color=None, align="l"):
        """Paragraphe simple avec retour a la ligne (respecte les \\n\\n)."""
        t, c = self.theme, self.c
        font = font or t.serif
        leading = leading or size * 1.55
        for block in s.split("\n\n"):
            words, line = block.split(), ""
            for word in words:
                trial = (line + " " + word).strip()
                if c.stringWidth(trial, font, size) <= width:
                    line = trial
                else:
                    self._prow(x, y, line, width, font, size, color, align)
                    y -= leading
                    line = word
            if line:
                self._prow(x, y, line, width, font, size, color, align)
                y -= leading
            y -= leading * 0.45
        return y

    def _prow(self, x, y, line, width, font, size, color, align):
        if align == "c":
            self.text(x + width / 2, y, line, font=font, size=size, color=color, align="c")
        else:
            self.text(x, y, line, font=font, size=size, color=color)

    # -- filets et cadres --------------------------------------------------
    def rule(self, x, y, w, color=None, lw=None, dash=None):
        t, c = self.theme, self.c
        c.saveState()
        c.setStrokeColor(color or t.rule)
        c.setLineWidth(lw or t.lw_rule)
        if dash:
            c.setDash(dash)
        c.line(x, y, x + w, y)
        c.restoreState()

    def vrule(self, x, y, h, color=None, lw=None, dash=None):
        t, c = self.theme, self.c
        c.saveState()
        c.setStrokeColor(color or t.hair)
        c.setLineWidth(lw or t.lw_hair)
        if dash:
            c.setDash(dash)
        c.line(x, y, x, y + h)
        c.restoreState()

    def box(self, x, y, w, h, color=None, lw=None, dash=None, fill=None, radius=None):
        t, c = self.theme, self.c
        c.saveState()
        c.setStrokeColor(color or t.hair)
        c.setLineWidth(lw or t.lw_hair)
        if dash:
            c.setDash(dash)
        if fill is not None:
            c.setFillColor(fill)
        if radius:
            c.roundRect(x, y, w, h, radius, stroke=1, fill=1 if fill is not None else 0)
        else:
            c.rect(x, y, w, h, stroke=1, fill=1 if fill is not None else 0)
        c.restoreState()

    # -- en-tetes ----------------------------------------------------------
    def header(self, title, right="", size=17, rule=True, tracking=1.6,
               italic_right=True, y=None, font=None):
        """Titre de page : filet, titre centre en serif espace."""
        t = self.theme
        y = self.y1 if y is None else y
        base = y - size * 0.95
        self.text((self.x0 + self.x1) / 2, base, title, font=font or t.serif,
                  size=size, align="c", tracking=tracking)
        if right:
            self.text(self.x1, base, right,
                      font=t.serif_it if italic_right else t.serif, size=8.5,
                      color=t.soft, align="r")
        if rule:
            self.rule(self.x0, base - 3.4 * mm, self.w, color=t.ink, lw=t.lw_frame)
        return base - 7.5 * mm

    def banner(self, title, sub="", h=12 * mm, y=None, align="l"):
        """Bandeau encadre facon 'MONTHLY TASKS' des pages modeles."""
        t = self.theme
        y = self.y1 if y is None else y
        top = y
        self.rule(self.x0, top, self.w, color=t.ink, lw=t.lw_frame)
        self.rule(self.x0, top - h, self.w, color=t.ink, lw=t.lw_frame)
        cx = (self.x0 + self.x1) / 2 if align == "c" else self.x0 + self.w / 2
        self.text(cx, top - h * 0.62, title.upper(), size=11, align="c", tracking=2.6)
        if sub:
            self.text(cx, top - h - 4.6 * mm, sub, font=t.serif_it, size=7.6,
                      color=t.soft, align="c")
            return top - h - 9 * mm
        return top - h - 4 * mm

    # -- lignes d'ecriture -------------------------------------------------
    def lines(self, x, y, w, n, gap=None, color=None, lw=None, dash=None,
              bullet=None, bullet_gap=2.6 * mm):
        """n lignes d'ecriture partant de y (vers le bas). Retourne le y final."""
        t = self.theme
        gap = (gap or t.line_gap * mm)
        for i in range(n):
            yy = y - gap * i
            if bullet == "circle":
                self.circle_mark(x + 1.1 * mm, yy + 1.5 * mm, 1.1 * mm)
                self.rule(x + bullet_gap + 1.4 * mm, yy, w - bullet_gap - 1.4 * mm,
                          color=color or t.hair, lw=lw, dash=dash)
            elif bullet == "square":
                self.box(x, yy + 0.3 * mm, 2.2 * mm, 2.2 * mm)
                self.rule(x + bullet_gap + 1.2 * mm, yy, w - bullet_gap - 1.2 * mm,
                          color=color or t.hair, lw=lw, dash=dash)
            elif bullet == "number":
                self.text(x, yy + 1.2 * mm, "%d." % (i + 1), font=t.serif_it, size=8,
                          color=t.soft)
                self.rule(x + 6 * mm, yy, w - 6 * mm, color=color or t.hair, lw=lw, dash=dash)
            else:
                self.rule(x, yy, w, color=color or t.hair, lw=lw, dash=dash)
        return y - gap * (n - 1)

    def circle_mark(self, cx, cy, r, color=None, lw=None):
        t, c = self.theme, self.c
        c.saveState()
        c.setStrokeColor(color or t.rule)
        c.setLineWidth(lw or t.lw_hair)
        c.circle(cx, cy, r, stroke=1, fill=0)
        c.restoreState()

    def fits(self, y, need):
        return y - need >= self.y0

    def field(self, x, y, w, label, size=6.2, gap=3.2 * mm):
        """Intitule discret + ligne a remplir."""
        self.label(x, y + gap, label, size=size)
        self.rule(x, y, w)
        return y

    # -- grilles -----------------------------------------------------------
    def grid(self, x, y, w, h, cols, rows, color=None, lw=None):
        """Grille reguliere (coin bas-gauche en x, y)."""
        t = self.theme
        color = color or t.hair
        cw, rh = w / cols, h / rows
        for i in range(cols + 1):
            self.vrule(x + cw * i, y, h, color=color, lw=lw)
        for j in range(rows + 1):
            self.rule(x, y + rh * j, w, color=color, lw=lw or t.lw_hair)
        return cw, rh

    def mini_month(self, x, y, w, year, month, weeks, initials, title=None,
                   title_size=7.4, day_size=5.4, highlight=None, row_h=None):
        """Mini calendrier (coin haut-gauche en x, y). Retourne la hauteur."""
        t = self.theme
        top = y
        if title:
            self.text(x + w / 2, top - title_size, title.upper(), size=title_size,
                      align="c", tracking=1.5)
            top -= title_size + 3.2 * mm
        cw = w / 7.0
        for i, ini in enumerate(initials):
            self.text(x + cw * (i + 0.5), top - day_size, ini, font=t.sans,
                      size=day_size, color=t.soft, align="c")
        top -= day_size + 1.6 * mm
        self.rule(x, top + 0.6 * mm, w, color=t.hair)
        rh = row_h or (day_size + 2.6 * mm)
        for r, week in enumerate(weeks):
            for i, day in enumerate(week):
                if day is None:
                    continue
                cx, cy = x + cw * (i + 0.5), top - rh * r - day_size
                if highlight and day in highlight:
                    self.c.saveState()
                    self.c.setFillColor(t.wash)
                    self.c.circle(cx, cy + day_size * 0.35, day_size * 0.95, stroke=0, fill=1)
                    self.c.restoreState()
                self.text(cx, cy, str(day.day), size=day_size + 0.6, align="c")
        return (y - (top - rh * len(weeks))) + 1 * mm
