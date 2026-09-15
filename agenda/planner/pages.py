# -*- coding: utf-8 -*-
"""Gabarits de pages. Chaque fonction dessine une page complete."""
import datetime as dt

from reportlab.lib.units import mm

from . import calendars as cal

DOT = 1.05 * mm


class Ctx:
    """Contexte de generation : annee, langue, debut de semaine, regions."""

    def __init__(self, year, L, week_start="mon", regions=("FR", "BE")):
        self.year = year
        self.L = L
        self.week_start = week_start
        self.regions = regions
        self.order = cal.weekday_order(week_start)
        self.initials = [L["weekday_initials"][i] for i in self.order]

    def month_weeks(self, month, year=None):
        return cal.month_matrix(year or self.year, month, self.week_start)

    def dayname(self, date):
        return self.L["weekdays"][date.weekday()]

    def monthname(self, m):
        return self.L["months_accent"][m - 1]


# --------------------------------------------------------------------------
# Pages d'ouverture
# --------------------------------------------------------------------------
def cover(sh, ctx, side="right"):
    sh.begin(side, brand_mark=False)
    t, L = sh.theme, ctx.L
    y = sh.y1 - 42 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, str(ctx.year), size=30, align="c", tracking=9)
    y -= 9 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, L["intro_title"], font=t.serif_it, size=10.5,
            color=t.soft, align="c")
    y -= 14 * mm
    inner = sh.w * 0.80
    y = sh.paragraph(sh.x0 + (sh.w - inner) / 2, y, L["intro_body"], inner,
                     size=8.4, align="c")
    y -= 6 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, L["intro_sign"], font=t.serif_it, size=10,
            align="c")
    if sh.brand:
        sh.text((sh.x0 + sh.x1) / 2, sh.y0 + 8 * mm, sh.brand.upper(), font=t.sans,
                size=5.4, color=t.hair, align="c", tracking=2.4)
    sh.finish()


def quote(sh, ctx, line1, line2, line3="", side="right"):
    """Page citation, facon separateur."""
    sh.begin(side, brand_mark=False)
    t = sh.theme
    cx, y = (sh.x0 + sh.x1) / 2, sh.H * 0.60
    sh.text(cx, y, line1.upper(), size=15, align="c", tracking=3)
    sh.text(cx, y - 9 * mm, line2, font=t.serif_it, size=15, align="c")
    if line3:
        sh.text(cx, y - 18 * mm, line3.upper(), size=15, align="c", tracking=3)
    sh.text(cx, sh.y0 + 6 * mm, (sh.brand or "").upper(), font=t.sans, size=5.4,
            color=t.hair, align="c", tracking=2)
    sh.finish()


def year_at_glance(sh, ctx, side="right"):
    sh.begin(side)
    L = ctx.L
    y = sh.header(L["yearly_planner"], right=str(ctx.year))
    cols, gap = 3, 5 * mm
    cw = (sh.w - gap * (cols - 1)) / cols
    row_h = (y - sh.y0) / 4.0
    for m in range(1, 13):
        r, c = divmod(m - 1, cols)
        x = sh.x0 + c * (cw + gap)
        weeks = ctx.month_weeks(m)
        rh = (row_h - 14 * mm) / 6.0
        sh.mini_month(x, y - r * row_h, cw, ctx.year, m, weeks, ctx.initials,
                      title=L["months"][m - 1], day_size=5.2, row_h=rh)
    sh.finish()


def year_overview(sh, ctx, first_month=1, side="right"):
    """Grille verticale : 6 mois en colonnes, 31 jours en lignes."""
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.header(L["yearly_overview"] if first_month == 1 else " ",
                  right=str(ctx.year), rule=False)
    top = y + 2 * mm
    n_days, cols = 31, 6
    lab_w = 5.5 * mm
    cw = (sh.w - lab_w) / cols
    row_h = (top - sh.y0 - 6 * mm) / (n_days + 1)
    sh.rule(sh.x0, top, sh.w, color=t.ink, lw=t.lw_frame)
    for c in range(cols):
        m = first_month + c
        x = sh.x0 + lab_w + c * cw
        sh.text(x + cw / 2, top - row_h * 0.72, L["months"][m - 1], size=6.6,
                align="c", tracking=1.2)
    sh.rule(sh.x0, top - row_h, sh.w, color=t.rule)
    for d in range(1, n_days + 1):
        yy = top - row_h * (d + 1)
        sh.text(sh.x0 + lab_w - 1.4 * mm, yy + row_h * 0.30, str(d), font=t.sans,
                size=4.8, color=t.soft, align="r")
        sh.rule(sh.x0, yy, sh.w, color=t.hair)
        for c in range(cols):
            m = first_month + c
            x = sh.x0 + lab_w + c * cw
            try:
                date = dt.date(ctx.year, m, d)
            except ValueError:
                sh.box(x, yy, cw, row_h, fill=t.wash, color=t.wash)
                continue
            sh.text(x + 1.2 * mm, yy + row_h * 0.30, ctx.L["weekday_initials"][date.weekday()],
                    font=t.sans, size=4.4,
                    color=t.rule if date.weekday() < 5 else t.soft)
    for c in range(cols + 1):
        sh.vrule(sh.x0 + lab_w + c * cw, top - row_h * (n_days + 1), row_h * (n_days + 1),
                 color=t.hair)
    sh.finish()


def key_dates(sh, ctx, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.header(L["important_dates"], right=str(ctx.year))
    colw = sh.w / 2 - 4 * mm
    for i, code in enumerate(ctx.regions[:2]):
        x = sh.x0 + i * (colw + 8 * mm)
        sh.label(x + colw / 2, y, L["countries"][i], size=6.6, align="c",
                 color=t.ink, tracking=2)
        sh.rule(x, y - 2.6 * mm, colw, color=t.rule)
        yy = y - 8 * mm
        items = cal.region_dates(code, ctx.year)
        step = min(5.9 * mm, (yy - sh.y0) / max(len(items), 1))
        for date, label, is_off in items:
            sh.text(x, yy, "%d %s" % (date.day, L["months_short"][date.month - 1]),
                    font=t.serif_it, size=6.2, color=t.soft)
            sh.text(x + 15 * mm, yy, label,
                    font=t.serif_bd if is_off else t.serif, size=6.4)
            yy -= step
    sh.finish()


# --------------------------------------------------------------------------
# Objectifs et bilans
# --------------------------------------------------------------------------
def yearly_goals(sh, ctx, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.header(L["yearly_goals"], right=str(ctx.year))
    sh.text((sh.x0 + sh.x1) / 2, y, L["yearly_goals_hint"], font=t.serif_it,
            size=7, color=t.soft, align="c")
    y -= 10 * mm
    step = (y - sh.y0) / 7.0
    for i in range(7):
        yy = y - step * i
        sh.text(sh.x0, yy + 1.4 * mm, "%d." % (i + 1), font=t.serif_it, size=8.4,
                color=t.soft)
        sh.rule(sh.x0 + 6 * mm, yy, sh.w - 6 * mm)
        sh.rule(sh.x0 + 6 * mm, yy - step * 0.42, sh.w - 6 * mm - 7 * mm, color=t.hair)
        sh.box(sh.x1 - 3.2 * mm, yy - step * 0.42 - 0.6 * mm, 3.2 * mm, 3.2 * mm)
    sh.finish()


def quarterly_goals(sh, ctx, q, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    months = "%s - %s" % (L["months"][q * 3 - 3], L["months"][q * 3 - 1])
    y = sh.banner(L["quarterly_goals"], sub="%s  ·  %s" % (months.upper(), L["quarters"][q - 1]))
    y -= 4 * mm
    step = (y - sh.y0) / 7.0
    for i in range(7):
        yy = y - step * i
        sh.text(sh.x0, yy + 1.4 * mm, "%d." % (i + 1), font=t.serif_it, size=8.4,
                color=t.soft)
        sh.rule(sh.x0 + 6 * mm, yy, sh.w - 6 * mm)
        sh.rule(sh.x0 + 6 * mm, yy - step * 0.45, sh.w - 13 * mm, color=t.hair)
        sh.box(sh.x1 - 3.2 * mm, yy - step * 0.45 - 0.6 * mm, 3.2 * mm, 3.2 * mm)
    sh.finish()


def quarterly_review(sh, ctx, q, side="left"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["quarterly_review"], sub=L["quarters"][q - 1])
    prompts = [(L["q_grateful"], 2), (L["q_goals_done"], 2),
               (L["q_align"], 2), (L["q_better"], 2)]
    for label, n in prompts:
        sh.text((sh.x0 + sh.x1) / 2, y, label, font=t.serif_it, size=7.4,
                color=t.soft, align="c")
        y = sh.lines(sh.x0, y - 6 * mm, sh.w, n, gap=6.6 * mm) - 9 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, L["q_actions"], font=t.serif_it, size=7.4,
            color=t.soft, align="c")
    y -= 6.5 * mm
    n = max(int((y - sh.y0) / (6.6 * mm)), 1)
    sh.lines(sh.x0, y, sh.w, n, gap=6.6 * mm, bullet="circle")
    sh.finish()


def bucketlist(sh, ctx, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.header(L["bucketlist"], right=str(ctx.year))
    blocks = [L["bucket_more"], L["bucket_less"], L["bucket_places"],
              L["bucket_new"], L["bucket_projects"], L["bucket_buys"]]
    colw = sh.w / 2 - 4 * mm
    block_h = (y - sh.y0) / 3.0
    for i, title in enumerate(blocks):
        r, c = divmod(i, 2)
        x = sh.x0 + c * (colw + 8 * mm)
        yy = y - r * block_h
        sh.text(x + colw / 2, yy, title, font=t.serif_it, size=7.6, align="c")
        sh.rule(x + colw * 0.22, yy - 2.2 * mm, colw * 0.56, color=t.rule)
        n = max(int((block_h - 12 * mm) / (6.4 * mm)), 1)
        sh.lines(x, yy - 9 * mm, colw, n, gap=6.4 * mm)
    sh.finish()


# --------------------------------------------------------------------------
# Mensuel
# --------------------------------------------------------------------------
def month_cover(sh, ctx, m, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.y1 - 12 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, ctx.monthname(m).upper(), size=20, align="c",
            tracking=6)
    y -= 12 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, L["intentions"], font=t.serif_it, size=7.6,
            color=t.soft, align="c")
    y = sh.lines(sh.x0, y - 7 * mm, sh.w, 2, gap=7 * mm) - 12 * mm

    sh.label((sh.x0 + sh.x1) / 2, y, L["top_three"], size=6.6, color=t.ink,
             align="c", tracking=2.4)
    y -= 7 * mm
    y = sh.lines(sh.x0, y, sh.w, 3, gap=7 * mm, bullet="number") - 12 * mm

    sh.label((sh.x0 + sh.x1) / 2, y, L["important_tasks"], size=6.6, color=t.ink,
             align="c", tracking=2.4)
    y -= 7 * mm
    colw = sh.w / 2 - 3 * mm
    rows = 6
    for c in range(2):
        sh.lines(sh.x0 + c * (colw + 6 * mm), y, colw, rows, gap=6.4 * mm,
                 bullet="square")
    y -= 6.4 * mm * (rows - 1) + 13 * mm

    sh.label((sh.x0 + sh.x1) / 2, y, L["monthly_habits"], size=6.6, color=t.ink,
             align="c", tracking=2.4)
    y -= 5.5 * mm
    ndays = (dt.date(ctx.year + (m == 12), m % 12 + 1, 1) - dt.timedelta(days=1)).day
    lab_w = sh.w * 0.42
    cw = (sh.w - lab_w) / ndays
    for d in range(1, ndays + 1):
        sh.text(sh.x0 + lab_w + cw * (d - 0.5), y, str(d), font=t.sans, size=3.6,
                color=t.soft, align="c")
    y -= 1.6 * mm
    rows = max(int((y - sh.y0) / (4.4 * mm)), 4)
    h = rows * 4.4 * mm
    sh.grid(sh.x0 + lab_w, y - h, sh.w - lab_w, h, ndays, rows)
    for r in range(rows):
        sh.rule(sh.x0, y - 4.4 * mm * (r + 1) + 0.0, lab_w - 1.5 * mm, color=t.hair)
    sh.finish()


def month_spread(sh, ctx, m, split=4):
    """Double page calendrier : jours 1..n a gauche, fin de semaine + notes a droite."""
    t, L = sh.theme, ctx.L
    weeks = ctx.month_weeks(m)
    names = [L["weekdays"][i] for i in ctx.order]

    # --- page de gauche
    sh.begin("left")
    y = sh.y1
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    sh.text(sh.x0, y - 7.5 * mm, ctx.monthname(m).upper(), size=11, tracking=3)
    y -= 12 * mm
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    cw = sh.w / split
    for i in range(split):
        sh.text(sh.x0 + cw * (i + 0.5), y - 5 * mm, names[i], font=t.serif_it,
                size=6.8, color=t.soft, align="c")
    y -= 8.5 * mm
    _month_cells(sh, ctx, weeks, range(0, split), sh.x0, y, cw, len(weeks))
    sh.finish()

    # --- page de droite
    sh.begin("right")
    y = sh.y1
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    sh.text(sh.x1, y - 7.5 * mm, str(ctx.year), size=11, align="r", tracking=3)
    y -= 12 * mm
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    rest = 7 - split
    notes_w = sh.w * 0.28
    cw = (sh.w - notes_w) / rest
    for i in range(rest):
        sh.text(sh.x0 + cw * (i + 0.5), y - 5 * mm, names[split + i], font=t.serif_it,
                size=6.8, color=t.soft, align="c")
    sh.label(sh.x0 + (sh.w - notes_w) + notes_w / 2, y - 5 * mm, L["notes"],
             size=6.2, align="c", tracking=2)
    y -= 8.5 * mm
    _month_cells(sh, ctx, weeks, range(split, 7), sh.x0, y, cw, len(weeks))
    nx = sh.x0 + (sh.w - notes_w)
    h = y - sh.y0
    sh.vrule(nx, sh.y0, h, color=t.hair)
    gap = 7.4 * mm
    n = int(h / gap)
    top = y - gap
    sh.lines(nx + 3 * mm, top, notes_w - 3 * mm, min(n, 10), gap=gap, bullet="circle")
    if n > 10:
        sh.lines(nx + 3 * mm, top - gap * 10, notes_w - 3 * mm, n - 10, gap=gap)
    sh.finish()


def _month_cells(sh, ctx, weeks, idx_range, x, y, cw, nweeks):
    t = sh.theme
    h = (y - sh.y0) / nweeks
    for r, week in enumerate(weeks):
        for k, i in enumerate(idx_range):
            day = week[i]   # month_matrix renvoie deja les jours en ordre d'affichage
            cx, cy = x + cw * k, y - h * (r + 1)
            sh.box(cx + 0.8 * mm, cy + 0.8 * mm, cw - 1.6 * mm, h - 1.6 * mm,
                   color=t.hair, dash=(0.6, 1.2))
            if day:
                sh.text(cx + 2.4 * mm, cy + h - 4.6 * mm, str(day.day), font=t.sans,
                        size=5.4, color=t.soft)


def recurring_tasks(sh, ctx, side="right"):
    """Tableau des taches / factures recurrentes, coche mois par mois."""
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["monthly_tasks"], sub=str(ctx.year))
    y -= 2 * mm
    lab_w = sh.w * 0.52
    cw = (sh.w - lab_w) / 12.0
    sh.text(sh.x0, y, L["task_or_bill"], font=t.serif_it, size=7, color=t.soft)
    for i in range(12):
        sh.text(sh.x0 + lab_w + cw * (i + 0.5), y, L["months_short"][i][0],
                font=t.sans, size=5, color=t.soft, align="c")
    y -= 3 * mm
    sh.rule(sh.x0, y, sh.w, color=t.rule)
    y -= 6 * mm
    rows = int((y - sh.y0) / (6.4 * mm)) + 1
    for r in range(rows):
        yy = y - 6.4 * mm * r
        sh.rule(sh.x0, yy, lab_w - 3 * mm, color=t.hair)
        for i in range(12):
            sh.circle_mark(sh.x0 + lab_w + cw * (i + 0.5), yy + 1.5 * mm, DOT)
    sh.finish()


def month_review(sh, ctx, m, side="left"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["monthly_review"], sub=ctx.monthname(m))
    y -= 3 * mm
    sh.text((sh.x0 + sh.x1) / 2, y, L["wins"], font=t.serif_it, size=7.6,
            color=t.soft, align="c")
    y -= 6 * mm
    n = 5
    gap = 2.4 * mm
    bw = (sh.w - gap * (n - 1)) / n
    bh = bw * 1.15
    for i in range(n):
        sh.box(sh.x0 + i * (bw + gap), y - bh, bw, bh, color=t.hair,
               dash=(0.7, 1.4), fill=t.wash)
    y -= bh + 12 * mm

    sh.text((sh.x0 + sh.x1) / 2, y, L["gratitude"], font=t.serif_it, size=7.6,
            color=t.soft, align="c")
    y = sh.lines(sh.x0, y - 6.5 * mm, sh.w, 4, gap=6.6 * mm, dash=(0.7, 1.4)) - 13 * mm

    colw = sh.w / 2 - 3 * mm
    box_h = y - sh.y0
    for i, label in enumerate([L["to_work_on"], L["next_month"]]):
        x = sh.x0 + i * (colw + 6 * mm)
        sh.box(x, sh.y0, colw, box_h, color=t.hair, fill=t.wash)
        sh.text(x + colw / 2, y - 6 * mm, label, font=t.serif_it, size=7.4,
                color=t.soft, align="c")
    sh.finish()


# --------------------------------------------------------------------------
# Hebdomadaire
# --------------------------------------------------------------------------
def week_spread(sh, ctx, monday, layout="horizontal", split=4):
    days = [monday + dt.timedelta(days=i) for i in range(7)]
    t, L = sh.theme, ctx.L
    span = _week_label(ctx, days)

    # --- gauche : 4 premiers jours
    sh.begin("left")
    y = sh.y1
    sh.text(sh.x0, y - 6 * mm, str(days[3].year), size=9.5, tracking=2.5)
    sh.text(sh.x1, y - 6 * mm, span, font=t.serif_it, size=7.4, color=t.soft, align="r")
    y -= 9.5 * mm
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    _day_blocks(sh, ctx, days[:split], y, (y - sh.y0) / split, layout)
    sh.finish()

    # --- droite : fin de semaine + mini calendrier + liste
    sh.begin("right")
    y = sh.y1
    sh.text(sh.x1, y - 6 * mm, "%s %d" % (L["week"], cal.iso_week(days[3])),
            font=t.serif_it, size=7.4, color=t.soft, align="r")
    sh.text(sh.x0, y - 6 * mm, ctx.monthname(days[3].month).upper(), size=9.5,
            tracking=2.5)
    y -= 9.5 * mm
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    rest = 7 - split
    bottom_h = 48 * mm
    block_h = (y - sh.y0 - bottom_h) / rest
    _day_blocks(sh, ctx, days[split:], y, block_h, layout)

    by = sh.y0 + bottom_h - 4 * mm
    mini_w = sh.w * 0.44
    m = days[3].month
    sh.mini_month(sh.x0, by, mini_w, days[3].year, m,
                  ctx.month_weeks(m, days[3].year), ctx.initials,
                  title="%s %d" % (ctx.monthname(m), days[3].year),
                  title_size=6.4, day_size=4.6, row_h=4.8 * mm, highlight=set(days))
    lx = sh.x0 + mini_w + 6 * mm
    lw_ = sh.x1 - lx
    n = int((by - sh.y0) / (6.0 * mm)) + 1
    sh.lines(lx, by - 3 * mm, lw_, n, gap=6.0 * mm, bullet="circle")
    sh.finish()


def _week_label(ctx, days):
    L = ctx.L
    a, b = days[0], days[6]
    if a.month == b.month:
        return "%d - %d %s %d" % (a.day, b.day, ctx.monthname(a.month), b.year)
    if a.year == b.year:
        return "%d %s - %d %s %d" % (a.day, ctx.monthname(a.month), b.day,
                                     ctx.monthname(b.month), b.year)
    return "%d %s %d - %d %s %d" % (a.day, ctx.monthname(a.month), a.year,
                                    b.day, ctx.monthname(b.month), b.year)


def _day_blocks(sh, ctx, days, y, block_h, layout):
    t = sh.theme
    for i, day in enumerate(days):
        top = y - block_h * i
        name = ctx.dayname(day).upper()
        sh.label(sh.x0, top - 5 * mm, name, size=6.4, color=t.ink, tracking=1.8)
        nw = sh.c.stringWidth(name, t.sans, 6.4) + 1.8 * len(name)
        sh.text(sh.x0 + nw + 5 * mm, top - 5 * mm, str(day.day), font=t.serif_it,
                size=7.4, color=t.soft)
        sh.rule(sh.x0, top - 6.8 * mm, sh.w, color=t.rule)
        if layout == "vertical":
            n = max(int((block_h - 10 * mm) / (5.6 * mm)), 1)
            sh.lines(sh.x0, top - 12.4 * mm, sh.w, n, gap=5.6 * mm, color=t.hair,
                     dash=(0.7, 1.5))
        else:
            n = max(int((block_h - 10 * mm) / (6.2 * mm)), 1)
            sh.lines(sh.x0, top - 13 * mm, sh.w, n, gap=6.2 * mm, color=t.hair)


# --------------------------------------------------------------------------
# Pages complementaires
# --------------------------------------------------------------------------
def master_list(sh, ctx, side="right"):
    sh.begin(side)
    L = ctx.L
    y = sh.header(L["master_list"])
    colw = sh.w / 2 - 4 * mm
    n = int((y - sh.y0) / (6.4 * mm)) + 1
    for c in range(2):
        sh.lines(sh.x0 + c * (colw + 8 * mm), y, colw, n, gap=6.4 * mm,
                 bullet="circle")
    sh.finish()


def notes(sh, ctx, side="right", dotted=False):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["notes"])
    y -= 2 * mm
    sh.text(sh.x0, y, L["topic"] + " :", font=t.serif_it, size=7, color=t.soft)
    sh.rule(sh.x0 + 18 * mm, y - 0.5 * mm, sh.w - 18 * mm, color=t.hair)
    y -= 9 * mm
    n = int((y - sh.y0) / (6.6 * mm)) + 1
    sh.lines(sh.x0, y, sh.w, n, gap=6.6 * mm,
             dash=(0.7, 1.6) if dotted else None)
    sh.finish()


def gifts(sh, ctx, months, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["gifts"])
    y -= 1 * mm
    block_h = (y - sh.y0) / len(months)
    for k, m in enumerate(months):
        top = y - block_h * k
        sh.text((sh.x0 + sh.x1) / 2, top - 4.5 * mm, L["months"][m - 1].upper(),
                size=7, align="c", tracking=2.4)
        hy = top - 9 * mm
        c1, c2, c3 = sh.x0, sh.x0 + sh.w * 0.16, sh.x0 + sh.w * 0.44
        c4, c5 = sh.x1 - 18 * mm, sh.x1 - 8 * mm
        sh.text(c1, hy, L["gift_date"], font=t.serif_it, size=5.6, color=t.soft)
        sh.text(c2, hy, L["gift_person"], font=t.serif_it, size=5.6, color=t.soft)
        sh.text(c3, hy, L["gift_idea"], font=t.serif_it, size=5.6, color=t.soft)
        sh.text(c4, hy, L["gift_bought"], font=t.serif_it, size=5.6, color=t.soft, align="c")
        sh.text(c5, hy, L["gift_sent"], font=t.serif_it, size=5.6, color=t.soft, align="c")
        rows = max(int((block_h - 16 * mm) / (5.8 * mm)), 1)
        for r in range(rows):
            yy = hy - 5.0 * mm - 5.8 * mm * r
            sh.rule(c1, yy, c4 - c1 - 4 * mm, color=t.hair)
            sh.circle_mark(c4, yy + 0.9 * mm, DOT)
            sh.circle_mark(c5, yy + 0.9 * mm, DOT)
    sh.finish()


def year_in_review(sh, ctx, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["year_in_review"], sub=str(ctx.year))
    prompts = [L["q_grateful"], L["q_flourished"], L["q_improve"],
               L["q_learned"], L["q_nextyear"]]
    per = (y - sh.y0) / len(prompts)
    for i, p in enumerate(prompts):
        top = y - per * i
        sh.text((sh.x0 + sh.x1) / 2, top - 4 * mm, p, font=t.serif_it, size=7.2,
                color=t.soft, align="c")
        n = max(int((per - 11 * mm) / (6.8 * mm)), 1)
        sh.lines(sh.x0, top - 10 * mm, sh.w, n, gap=6.8 * mm)
    sh.finish()


def life_in_review(sh, ctx, side="right"):
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.banner(L["life_in_review"])
    y = sh.paragraph(sh.x0, y - 1 * mm, L["life_note"], sh.w, size=6.6,
                     font=t.serif_it, color=t.soft) - 2 * mm
    areas = L["life_areas"]
    colw = sh.w / 2 - 3 * mm
    rows = (len(areas) + 1) // 2
    bh = (y - sh.y0) / rows
    for i, area in enumerate(areas):
        r, c = divmod(i, 2)
        x, top = sh.x0 + c * (colw + 6 * mm), y - bh * r
        sh.box(x, top - bh + 2 * mm, colw, bh - 2 * mm, color=t.hair)
        # le libelle se retrecit si besoin pour ne jamais toucher les pastilles
        avail = colw - 6 * mm - 24 * mm
        size = 6.0
        while size > 4.4 and sh.c.stringWidth(area.upper(), t.sans, size) + \
                1.4 * len(area) > avail:
            size -= 0.2
        sh.label(x + 3 * mm, top - 6 * mm, area, size=size, color=t.ink, tracking=1.4)
        for k in range(5):
            sh.circle_mark(x + colw - 4 * mm - k * 4 * mm, top - 5.2 * mm, DOT + 0.2 * mm)
        n = max(int((bh - 15 * mm) / (6.0 * mm)), 1)
        sh.lines(x + 3 * mm, top - 11.5 * mm, colw - 6 * mm, n, gap=6.0 * mm,
                 dash=(0.7, 1.5))
    sh.finish()


def next_year_dates(sh, ctx, months, side="right"):
    """Colonnes de jours pour les rendez-vous deja pris l'annee suivante."""
    sh.begin(side)
    t, L = sh.theme, ctx.L
    nyear = ctx.year + 1
    y = sh.header(L["diary_dates"].format(year=nyear), right=None or "")
    cols = len(months)
    cw = sh.w / cols
    row_h = (y - sh.y0) / 32.0
    for c, m in enumerate(months):
        x = sh.x0 + cw * c
        sh.text(x + cw / 2, y - 3 * mm, L["months"][m - 1], font=t.serif_it,
                size=7, align="c")
        for d in range(1, 32):
            yy = y - 8 * mm - row_h * (d - 1)
            try:
                date = dt.date(nyear, m, d)
                init = L["weekday_initials"][date.weekday()]
            except ValueError:
                continue
            sh.text(x, yy + 1 * mm, str(d), font=t.sans, size=4.4, color=t.soft)
            sh.text(x + 4 * mm, yy + 1 * mm, init, font=t.sans, size=4.0, color=t.hair)
            sh.rule(x + 7 * mm, yy, cw - 10 * mm, color=t.hair)
    sh.finish()


def week_spread_vertical(sh, ctx, monday, split=4):
    """Version verticale : les jours en colonnes, facon 'vertical weekly'."""
    days = [monday + dt.timedelta(days=i) for i in range(7)]
    t, L = sh.theme, ctx.L
    span = _week_label(ctx, days)

    sh.begin("left")
    y = sh.y1
    sh.text(sh.x0, y - 6 * mm, str(ctx.year), size=9.5, tracking=2.5)
    sh.text(sh.x1, y - 6 * mm, span, font=t.serif_it, size=7.4, color=t.soft, align="r")
    y -= 9.5 * mm
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    _week_columns(sh, ctx, days[:split], sh.x0, y, sh.w / split)
    sh.finish()

    sh.begin("right")
    y = sh.y1
    sh.text(sh.x0, y - 6 * mm, ctx.monthname(days[3].month).upper(), size=9.5, tracking=2.5)
    sh.text(sh.x1, y - 6 * mm, "%s %d" % (L["week"], cal.iso_week(days[3])),
            font=t.serif_it, size=7.4, color=t.soft, align="r")
    y -= 9.5 * mm
    sh.rule(sh.x0, y, sh.w, color=t.ink, lw=t.lw_frame)
    rest = 7 - split
    notes_w = sh.w * 0.26
    cw = (sh.w - notes_w) / rest
    _week_columns(sh, ctx, days[split:], sh.x0, y, cw)
    nx = sh.x0 + cw * rest
    sh.vrule(nx, sh.y0, y - sh.y0, color=t.hair)
    sh.label(nx + notes_w / 2, y - 5 * mm, L["notes"], size=6, align="c", tracking=2)
    m = days[3].month
    mini_h = sh.mini_month(nx + 2.5 * mm, sh.y0 + 34 * mm, notes_w - 5 * mm, ctx.year, m,
                           ctx.month_weeks(m, days[3].year), ctx.initials,
                           day_size=4.0, row_h=4.4 * mm, highlight=set(days))
    n = max(int((y - 9 * mm - (sh.y0 + 36 * mm)) / (6.6 * mm)), 1)
    top = y - 10 * mm
    sh.lines(nx + 2.5 * mm, top, notes_w - 5 * mm, min(n, 12), gap=6.6 * mm,
             bullet="circle")
    if n > 12:
        sh.lines(nx + 2.5 * mm, top - 6.6 * mm * 12, notes_w - 5 * mm, n - 12,
                 gap=6.6 * mm)
    sh.finish()


def _week_columns(sh, ctx, days, x, y, cw):
    t = sh.theme
    h = y - sh.y0
    for i, day in enumerate(days):
        cx = x + cw * i
        sh.label(cx + 2 * mm, y - 5 * mm, ctx.dayname(day)[:3], size=6, color=t.ink,
                 tracking=1.4)
        sh.text(cx + cw - 2 * mm, y - 5 * mm, str(day.day), font=t.serif_it, size=7,
                color=t.soft, align="r")
        sh.rule(cx + 1.5 * mm, y - 7.5 * mm, cw - 3 * mm, color=t.rule)
        if i:
            sh.vrule(cx, sh.y0, h, color=t.hair)
        n = int((y - 12 * mm - sh.y0) / (6.0 * mm))
        sh.lines(cx + 1.5 * mm, y - 13 * mm, cw - 3 * mm, n, gap=6.0 * mm,
                 color=t.hair, dash=(0.7, 1.5))


def printing_guide(sh, ctx, side="right"):
    """Fiche d'impression a joindre au fichier vendu."""
    sh.begin(side)
    t, L = sh.theme, ctx.L
    y = sh.header(L["print_title"], right="")
    y = sh.paragraph(sh.x0, y - 2 * mm, L["print_intro"], sh.w, size=8,
                     font=t.serif_it, color=t.soft) - 4 * mm
    for title, body in L["print_steps"]:
        sh.label(sh.x0, y, title, size=6.4, color=t.ink, tracking=1.8)
        y = sh.paragraph(sh.x0, y - 5 * mm, body, sh.w, size=7.6) - 3 * mm
    sh.rule(sh.x0, y - 2 * mm, sh.w, color=t.hair)
    sh.paragraph(sh.x0, y - 8 * mm, L["print_footer"], sh.w, size=6.8,
                 font=t.serif_it, color=t.soft)
    sh.finish()
