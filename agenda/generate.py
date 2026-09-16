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
# Sections, dans l'ordre du produit fini
# --------------------------------------------------------------------------
def sec_impression(sh, ctx, o):
    """Fiche d'impression : elle accompagne la vente, elle n'est pas reliee."""
    P.printing_guide(sh, ctx)


def sec_ouverture(sh, ctx, o):
    P.cover(sh, ctx)


def sec_vue_ensemble(sh, ctx, o):
    P.divider(sh, ctx, 1)
    P.year_at_glance(sh, ctx)
    if o.preset != "semainier":
        P.year_overview(sh, ctx, 1)
        P.year_overview(sh, ctx, 7)
    P.key_dates(sh, ctx)


def sec_objectifs(sh, ctx, o):
    P.divider(sh, ctx, 2)
    P.bucketlist(sh, ctx)
    P.yearly_goals(sh, ctx)
    if o.preset == "complet":
        P.life_in_review(sh, ctx)
    for q in (1, 2, 3, 4):
        P.quarterly_goals(sh, ctx, q)
        if o.preset == "complet":
            P.quarterly_review(sh, ctx, q)
    if o.quotes:
        L = ctx.L
        if L["code"] == "fr":
            P.quote(sh, ctx, "Une année se construit", "une ligne", "à la fois")
        else:
            P.quote(sh, ctx, "A year is built", "one line", "at a time")


def weeks_by_month(ctx):
    """Chaque semaine est rangee dans le mois ou elle commence."""
    buckets = {m: [] for m in range(1, 13)}
    for monday in cal.year_weeks(ctx.year, ctx.week_start):
        if monday.year < ctx.year:
            m = 1                       # la semaine a cheval sur l'an passe
        elif monday.year > ctx.year:
            m = 12
        else:
            m = monday.month
        buckets[m].append(monday)
    return buckets


def sec_pages_datees(sh, ctx, o):
    P.divider(sh, ctx, 3)
    buckets = weeks_by_month(ctx)
    for m in o.months:
        P.month_cover(sh, ctx, m)
        if o.budget_month:
            # au verso de la page de garde : budget du mois, puis page libre.
            # Les deux vont de pair : le rythme des doubles pages reste juste.
            P.budget(sh, ctx, month=m)
            P.notes(sh, ctx, dotted=True)
        P.month_spread(sh, ctx, m, split=o.split)
        for monday in buckets[m]:
            if o.layout == "vertical":
                P.week_spread_vertical(sh, ctx, monday, split=o.split)
            else:
                P.week_spread(sh, ctx, monday, layout=o.layout, split=o.split)
        if o.preset != "semainier":
            P.month_review(sh, ctx, m)


def sec_bonus(sh, ctx, o):
    P.divider(sh, ctx, 4)
    P.recurring_tasks(sh, ctx)
    P.master_list(sh, ctx)
    if o.preset == "complet":
        for q in range(4):
            P.gifts(sh, ctx, [q * 3 + 1, q * 3 + 2, q * 3 + 3])
    P.year_in_review(sh, ctx)
    if o.preset == "complet":
        for start in (1, 5, 9):
            P.next_year_dates(sh, ctx, [start, start + 1, start + 2, start + 3])
    for name, fn in EXTRA_PAGES:
        for _ in range(o.extras.get(name, 0)):
            fn(sh, ctx)
    for i in range(o.notes):
        P.notes(sh, ctx, dotted=(i % 2 == 1))


# Pages supplementaires, activables a la demande (--extras)
EXTRA_PAGES = [
    ("budget", lambda sh, ctx: P.budget(sh, ctx)),
    ("menus", lambda sh, ctx: P.meals(sh, ctx)),
    ("lecture", lambda sh, ctx: P.reading(sh, ctx)),
    ("contacts", lambda sh, ctx: P.contacts(sh, ctx)),
]
EXTRA_DEFAULTS = {"budget": 1, "menus": 4, "lecture": 2, "contacts": 2}

PRESET_SECTIONS = {
    "semainier": ["impression", "ouverture", "vue-ensemble", "pages-datees"],
}

SECTIONS = [
    ("impression", sec_impression),
    ("ouverture", sec_ouverture),
    ("vue-ensemble", sec_vue_ensemble),
    ("objectifs", sec_objectifs),
    ("pages-datees", sec_pages_datees),
    ("bonus", sec_bonus),
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


def build_charte(o, ctx):
    """Fiche de marque, en A4, hors agenda."""
    path = os.path.join(o.out, "CHARTE-MARQUE_%s.pdf" % o.brand.title().replace(" ", "-"))
    sh = Sheet(path, size="a4", theme=make_theme(o), brand=o.brand,
               title="Charte %s" % o.brand.title())
    P.brand_specimen(sh, ctx, brand=o.brand)
    n = sh.save()
    print("  %-52s %3d page" % (os.path.basename(path), n))
    return n


def run(o):
    langs = ["fr", "en"] if o.lang == "both" else [o.lang]
    starts = ["mon", "sun"] if o.week_start == "both" else [o.week_start]
    layouts = ["horizontal", "vertical"] if o.layout == "both" else [o.layout]
    wanted = SECTION_NAMES if "tout" in o.sections else o.sections
    wanted = [n for n in wanted if n in PRESET_SECTIONS.get(o.preset, SECTION_NAMES)]
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
                tag = "%s_%s_%s_%s_%s" % (o.size.upper(), o.year, lang.upper(),
                                          ws_label, layout)
                print("\n> %s (%s)" % (tag, o.preset))

                parts = [(n, f) for n, f in SECTIONS if n in wanted]
                if o.separate:
                    for name, fn in parts:
                        i = SECTION_NAMES.index(name)
                        fname = "%d_%s_%s.pdf" % (i, name, tag)
                        total += build(os.path.join(base, fname), [fn], ctx, o,
                                       "%s %s" % (name, o.year))
                if o.combined:
                    fiche = [f for n, f in parts if n == "impression"]
                    corps = [f for n, f in parts if n != "impression"]
                    if fiche and not o.separate:
                        total += build(os.path.join(base, "FICHE-IMPRESSION_%s.pdf" % tag),
                                       fiche, ctx, o, "Impression")
                    if corps:
                        fname = "AGENDA-COMPLET_%s.pdf" % tag
                        total += build(os.path.join(base, fname), corps, ctx, o,
                                       "%s %s" % (L["cover_sub"].format(year=o.year),
                                                  lang))
    if o.charte and o.brand:
        print("\n> Marque")
        ctx = P.Ctx(o.year, LANGS[langs[0]], week_start=starts[0],
                    regions=REGIONS_BY_LANG[langs[0]])
        total += build_charte(o, ctx)
    print("\n%d pages generees dans %s/" % (total, o.out))


def parse_extras(value):
    """--extras tout | budget,menus | budget=2,menus=6"""
    if not value:
        return {}
    if value.strip() in ("tout", "all"):
        return dict(EXTRA_DEFAULTS)
    out = {}
    for chunk in value.split(","):
        name, _, count = chunk.partition("=")
        name = name.strip()
        if name not in EXTRA_DEFAULTS:
            raise SystemExit("page supplementaire inconnue : %s (choix : %s)"
                             % (name, ", ".join(EXTRA_DEFAULTS)))
        out[name] = int(count) if count else EXTRA_DEFAULTS[name]
    return out


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
    p.add_argument("--preset", choices=["complet", "essentiel", "semainier"],
                   default="complet",
                   help="complet = toutes les pages ; essentiel = sans les bilans "
                        "trimestriels, cadeaux et dates n+1 ; semainier = mois et "
                        "semaines seulement")
    p.add_argument("--pack", action="store_true",
                   help="genere toutes les variantes (FR/EN, lundi/dimanche, "
                        "horizontal/vertical) et les PDF par section")
    p.add_argument("--extras", default="",
                   help="pages supplementaires : budget, menus, lecture, contacts "
                        "(ex. --extras tout ou --extras budget=2,menus=6)")
    p.add_argument("--budget-par-mois", action="store_true", dest="budget_month",
                   help="un budget + une page libre au debut de chaque mois")
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
    p.add_argument("--no-charte", action="store_false", dest="charte",
                   help="ne pas generer la fiche de charte typographique")
    p.add_argument("--no-combined", action="store_false", dest="combined",
                   help="ne pas generer le PDF complet")
    p.add_argument("--separate", action="store_true",
                   help="generer aussi un PDF par section")
    p.add_argument("--out", default=os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "export"))
    o = p.parse_args(argv)
    if o.pack:
        o.lang, o.week_start, o.layout, o.separate = "both", "both", "both", True
    if o.preset in ("essentiel", "semainier"):
        o.notes = min(o.notes, 2)
    o.sections = [s.strip() for s in o.sections.split(",")]
    o.months = parse_months(o.months)
    o.extras = parse_extras(o.extras)
    bad = [s for s in o.sections if s not in SECTION_NAMES + ["tout"]]
    if bad:
        p.error("section inconnue : %s" % ", ".join(bad))
    run(o)


if __name__ == "__main__":
    main()
