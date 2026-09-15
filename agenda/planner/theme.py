"""Palette, typographie et geometrie des pages A5.

Tout ce qui touche a l'apparence se regle ici : changez ces valeurs pour
obtenir un rendu different sans toucher au reste du code.
"""
from dataclasses import dataclass, field

from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm

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

    # Polices (polices de base PDF : aucune installation requise)
    serif: str = "Times-Roman"
    serif_it: str = "Times-Italic"
    serif_bd: str = "Times-Bold"
    sans: str = "Helvetica"
    sans_bd: str = "Helvetica-Bold"

    # Marges (mm)
    margin_ring: float = 16.0   # cote perforations
    margin_out: float = 9.0     # cote exterieur
    margin_top: float = 11.0
    margin_bottom: float = 10.0

    # Epaisseurs
    lw_rule: float = 0.5
    lw_hair: float = 0.3
    lw_frame: float = 0.7

    # Interlignes d'ecriture (mm)
    line_gap: float = 7.0
