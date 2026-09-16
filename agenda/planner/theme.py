"""Palette, typographie et geometrie des pages A5.

Tout ce qui touche a l'apparence se regle ici : changez ces valeurs pour
obtenir un rendu different sans toucher au reste du code.
"""
import os
from dataclasses import dataclass, field

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

# --- Polices de la marque -------------------------------------------------
# Cormorant Garamond (titres, wordmark) + Jost (petites capitales), toutes
# deux sous licence SIL OFL : usage commercial libre, y compris pour un
# produit vendu. Les fichiers sont dans agenda/fonts/.
FONT_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                        "fonts")
BUNDLED = {
    "serif": ("MyLine-Serif", "CormorantGaramond-Regular.ttf", "Times-Roman"),
    "serif_it": ("MyLine-SerifItalic", "CormorantGaramond-Italic.ttf", "Times-Italic"),
    "serif_bd": ("MyLine-SerifBold", "CormorantGaramond-SemiBold.ttf", "Times-Bold"),
    "serif_lt": ("MyLine-SerifLight", "CormorantGaramond-Light.ttf", "Times-Roman"),
    "serif_num": ("MyLine-SerifNum", "CormorantGaramond-Lining.ttf", "Times-Roman"),
    "serif_num_it": ("MyLine-SerifNumIt", "CormorantGaramond-LiningItalic.ttf",
                     "Times-Italic"),
    "sans": ("MyLine-Sans", "Jost-Regular.ttf", "Helvetica"),
    "sans_bd": ("MyLine-SansMedium", "Jost-Medium.ttf", "Helvetica-Bold"),
}


def register_brand_fonts():
    """Enregistre les polices de la marque ; repli sur les polices PDF de base."""
    resolved = {}
    for role, (name, filename, fallback) in BUNDLED.items():
        path = os.path.join(FONT_DIR, filename)
        try:
            pdfmetrics.registerFont(TTFont(name, path))
            resolved[role] = name
        except Exception:
            resolved[role] = fallback
    return resolved


FONTS = register_brand_fonts()

# --- Format de page -------------------------------------------------------
PAGE_SIZES = {
    "a5": (148 * mm, 210 * mm),
    "a4": (210 * mm, 297 * mm),
    "personal": (95 * mm, 171 * mm),
    "half-letter": (139.7 * mm, 215.9 * mm),
}

# Positions indicatives des 6 perforations A5 (depuis le haut, en mm).
RING_HOLES_A5 = (25.5, 44.5, 95.5, 114.5, 165.5, 184.5)


@dataclass
class Theme:
    # Couleurs
    ink: object = field(default_factory=lambda: HexColor("#1A1A1A"))
    soft: object = field(default_factory=lambda: HexColor("#5C5C5C"))
    rule: object = field(default_factory=lambda: HexColor("#9E9E9E"))
    hair: object = field(default_factory=lambda: HexColor("#CFCFCF"))
    wash: object = field(default_factory=lambda: HexColor("#F2F2F2"))

    # Polices de la marque (voir register_brand_fonts ci-dessus)
    serif: str = FONTS["serif"]
    serif_it: str = FONTS["serif_it"]
    serif_bd: str = FONTS["serif_bd"]
    serif_lt: str = FONTS["serif_lt"]
    # variantes a chiffres alignes, pour les calendriers et les quantiemes
    serif_num: str = FONTS["serif_num"]
    serif_num_it: str = FONTS["serif_num_it"]
    sans: str = FONTS["sans"]
    sans_bd: str = FONTS["sans_bd"]

    @property
    def serif_fonts(self):
        return (self.serif, self.serif_it, self.serif_bd, self.serif_lt,
                self.serif_num, self.serif_num_it)

    # Marges (mm)
    margin_ring: float = 16.0   # cote perforations
    margin_out: float = 9.0     # cote exterieur
    margin_top: float = 11.0
    margin_bottom: float = 10.0

    # Cormorant a un oeil plus petit que les polices PDF de base : on compense
    # d'un coup, au lieu de retoucher chaque taille.
    serif_scale: float = 1.15

    # Epaisseurs
    lw_rule: float = 0.5
    lw_hair: float = 0.3
    lw_frame: float = 0.7

    # Interlignes d'ecriture (mm)
    line_gap: float = 7.0
