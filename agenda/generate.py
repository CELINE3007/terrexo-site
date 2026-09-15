# -*- coding: utf-8 -*-
"""Generateur d'inserts d'agenda prets a imprimer (A5 par defaut).

Exemples :
    python3 generate.py                          # 2027, FR, semaine au lundi
    python3 generate.py --year 2027 --lang both --week-start both
    python3 generate.py --sections hebdo --layout vertical
    python3 generate.py --size a4 --brand "Autre Marque"

Les fichiers sont ecrits dans export/<annee>/<langue>/.
"""
import argparse
import os
import sys

from reportlab.lib.units import mm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from planner import calendars as cal  # noqa: E402
from planner import pages as P  # noqa: E402
from planner.draw import Sheet  # noqa: E402
from planner.lang import LANGS  # noqa: E402
from planner.theme import Theme  # noqa: E402

from reportlab.pdfbase import pdfmetrics  # noqa: E402
from reportlab.pdfbase.ttfonts import TTFont  # noqa: E402

REGIONS_BY_LANG = {"fr": ("FR", "BE"), "en": ("UK", "US")}


# --------------------------------------------------------------------------
# Sections
# --------------------------------------------------------------------------
def sec_impression(sh, ctx, o):
    P.printing_guide(sh, ctx)


def sec_couverture(sh, ctx, o):
    P.cover(sh, ctx)
    if o.quotes:
        L = ctx.L
        if L["code"] == "fr":
            P.quote(sh, ctx, "Une année se construit", "une ligne", "à la fois")
        else:
            P.quote(sh, ctx, "A year is built", "one line", "at a time")


def sec_annuel(sh, ctx, o):
    P.year_at_glance(sh, ctx)
    P.year_overview(sh, ctx, 1, side="left")
    P.year_overview(sh, ctx, 7, side="right")
    P.key_dates(sh, ctx)
    P.yearly_goals(sh, ctx)
    P.bucketlist(sh, ctx)


def sec_trimestriel(sh, ctx, o):
    for q in (1, 2, 3, 4):
        P.quarterly_goals(sh, ctx, q, side="right")
        P.quarterly_review(sh, ctx, q, side="left")


def sec_mensuel(sh, ctx, o):
    for m in o.months:
        P.month_cover(sh, ctx, m, side="right")
        P.month_spread(sh, ctx, m, split=o.split)
        P.month_review(sh, ctx, m, side="left")


def sec_hebdo(sh, ctx, o):
    weeks = cal.year_weeks(ctx.year, ctx.week_start)
    for monday in weeks:
        if o.layout == "vertical":
            P.week_spread_vertical(sh, ctx, monday, split=o.split)
        else:
            P.week_spread(sh, ctx, monday, layout=o.layout, split=o.split)


def sec_extras(sh, ctx, o):
    P.recurring_tasks(sh, ctx)
    P.master_list(sh, ctx)
    for q in range(4):
        P.gifts(sh, ctx, [q * 3 + 1, q * 3 + 2, q * 3 + 3],
                side="right" if q % 2 == 0 else "left")
    P.year_in_review(sh, ctx)
    P.life_in_review(sh, ctx)
    for start in (1, 5, 9):
        P.next_year_dates(sh, ctx, [start, start + 1, start + 2, start + 3],
                          side="right" if start != 5 else "left")
    for i in range(o.notes):
        P.notes(sh, ctx, side="right" if i % 2 == 0 else "left",
                dotted=(i % 2 == 1))


SECTIONS = [
    ("impression", sec_impression),
    ("couverture", sec_couverture),
    ("annuel", sec_annuel),
    ("trimestriel", sec_trimestriel),
    ("mensuel", sec_mensuel),
    ("hebdo", sec_hebdo),
    ("extras", sec_extras),
]
SECTION_NAMES = [n for n, _ in SECTIONS]


# --------------------------------------------------------------------------
# Fabrication des fichiers
# --------------------------------------------------------------------------
def make_theme(o):
    """Theme par defaut, complete par les polices .ttf eventuellement fournies."""
    th = Theme()
    for opt, attrs in (("font_serif", ("serif",)),
                       ("font_serif_italic", ("serif_it",)),
                       ("font_serif_bold", ("serif_bd",)),
                       ("font_sans", ("sans",)),
                       ("font_sans_bold", ("sans_bd",))):
        path = getattr(o, opt)
        if not path:
            continue
        name = os.path.splitext(os.path.basename(path))[0]
        pdfmetrics.registerFont(TTFont(name, path))
        for a in attrs:
            setattr(th, a, name)
    # replis : si seule la police serif est fournie, elle sert aussi aux variantes
    if o.font_serif and not o.font_serif_italic:
        th.serif_it = th.serif
    if o.font_serif and not o.font_serif_bold:
        th.serif_bd = th.serif
    if o.font_sans and not o.font_sans_bold:
        th.sans_bd = th.sans
    return th


def build(path, builders, ctx, o, title):
    sh = Sheet(path, size=o.size, theme=make_theme(o), brand=o.brand,
               guides=o.guides, title=title)
    for fn in builders:
        fn(sh, ctx, o)
    n = sh.save()
    print("  %-52s %3d pages" % (os.path.basename(path), n))
    return n


def run(o):
    langs = ["fr", "en"] if o.lang == "both" else [o.lang]
    starts = ["mon", "sun"] if o.week_start == "both" else [o.week_start]
    layouts = ["horizontal", "vertical"] if o.layout == "both" else [o.layout]
    wanted = SECTION_NAMES if "tout" in o.sections else o.sections
    total = 0

    for lang in langs:
        L = LANGS[lang]
        for ws in starts:
            ctx = P.Ctx(o.year, L, week_start=ws, regions=REGIONS_BY_LANG[lang])
            for layout in layouts:
                o.layout = layout
                ws_label = {"mon": "lundi", "sun": "dimanche"}[ws] if lang == "fr" \
                    else {"mon": "monday", "sun": "sunday"}[ws]
                base = os.path.join(o.out, str(o.year), lang.upper())
                os.makedirs(base, exist_ok=True)
                tag = "%s_%s_%s_%s" % (o.size.upper(), o.year, lang.upper(), ws_label)
                print("\n> %s  (%s, %s)" % (tag, layout, L["code"]))

                parts = [(n, f) for n, f in SECTIONS if n in wanted]
                if o.separate:
                    for name, fn in parts:
                        i = SECTION_NAMES.index(name)
                        suffix = "-" + layout if name == "hebdo" else ""
                        fname = "%02d_%s_%s%s.pdf" % (i + 1, name, tag, suffix)
                        total += build(os.path.join(base, fname), [fn], ctx, o,
                                       "%s %s" % (name, o.year))
                if o.combined:
                    fname = "AGENDA-COMPLET_%s_%s.pdf" % (tag, layout)
                    total += build(os.path.join(base, fname),
                                   [f for _, f in parts], ctx, o,
                                   "%s %s" % (L["cover_sub"].format(year=o.year), lang))
    print("\n%d pages generees dans %s/" % (total, o.out))


def parse_months(value):
    if value in (None, "", "all", "tout"):
        return list(range(1, 13))
    out = []
    for chunk in value.split(","):
        if "-" in chunk:
            a, b = chunk.split("-")
            out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(chunk))
    return out


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--year", type=int, default=2027, help="annee de l'agenda")
    p.add_argument("--lang", choices=["fr", "en", "both"], default="fr")
    p.add_argument("--week-start", choices=["mon", "sun", "both"], default="mon",
                   dest="week_start", help="premier jour de la semaine")
    p.add_argument("--layout", choices=["horizontal", "vertical", "both"],
                   default="horizontal", help="style des semaines")
    p.add_argument("--size", choices=["a5", "a4", "personal", "half-letter"],
                   default="a5")
    p.add_argument("--sections", default="tout",
                   help="liste separee par des virgules : " + ", ".join(SECTION_NAMES))
    p.add_argument("--months", default="all", help="ex. 1,2,3 ou 1-6")
    p.add_argument("--notes", type=int, default=6, help="nombre de pages de notes")
    p.add_argument("--split", type=int, default=4,
                   help="jours sur la page de gauche (4 = lun-jeu)")
    p.add_argument("--brand", default="MY LINE PLANNER",
                   help="marque imprimee en filigrane (\"\" pour aucune)")
    p.add_argument("--font-serif", dest="font_serif", default="",
                   help="chemin d'une police .ttf pour les titres")
    p.add_argument("--font-serif-italic", dest="font_serif_italic", default="")
    p.add_argument("--font-serif-bold", dest="font_serif_bold", default="")
    p.add_argument("--font-sans", dest="font_sans", default="",
                   help="chemin d'une police .ttf pour les petites capitales")
    p.add_argument("--font-sans-bold", dest="font_sans_bold", default="")
    p.add_argument("--guides", action="store_true",
                   help="reperes de perforation 6 anneaux")
    p.add_argument("--no-quotes", action="store_false", dest="quotes")
    p.add_argument("--no-combined", action="store_false", dest="combined",
                   help="ne pas generer le PDF complet")
    p.add_argument("--no-separate", action="store_false", dest="separate",
                   help="ne pas generer un PDF par section")
    p.add_argument("--out", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "export"))
    o = p.parse_args(argv)
    o.sections = [s.strip() for s in o.sections.split(",")]
    o.months = parse_months(o.months)
    bad = [s for s in o.sections if s not in SECTION_NAMES + ["tout"]]
    if bad:
        p.error("section inconnue : %s" % ", ".join(bad))
    run(o)


if __name__ == "__main__":
    main()
