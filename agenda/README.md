# Générateur d'agenda A5 (inserts à imprimer)

Un seul script Python produit tout le jeu d'inserts d'un agenda : couverture,
pages annuelles, trimestrielles, mensuelles, 52/53 doubles pages hebdomadaires
et pages complémentaires — en français et en anglais, semaine au lundi ou au
dimanche, format A5 (ou A4, Personal, Half-Letter).

Les PDF sont **vectoriels** : texte net à l'impression, poids léger
(~350 Ko pour 187 pages), et regénérables en 5 secondes pour une autre année.

---

## 1. Installation (une seule fois, sur le MacBook)

Ouvrez le Terminal et lancez :

```bash
cd ~/chemin/vers/terrexo-site/agenda
python3 -m pip install --user reportlab
```

Vous pouvez aussi double-cliquer sur **`build.command`** dans le Finder : il
installe ce qu'il faut, génère le pack complet et ouvre le dossier `export/`.
(Au premier lancement, macOS peut demander : clic droit → Ouvrir.)

## 2. Générer

```bash
python3 generate.py                      # 2027, FR, semaine au lundi, hebdo horizontal
python3 generate.py --year 2028          # une autre année : tout se recalcule
python3 generate.py --lang both --week-start both --layout both   # le pack complet
```

Les fichiers arrivent dans `export/<année>/<langue>/` :

| Fichier | Contenu |
|---|---|
| `AGENDA-COMPLET_A5_2027_FR_lundi_horizontal.pdf` | l'agenda entier, 187 pages |
| `01_impression_…` | la fiche « Impression & montage » à joindre à la vente |
| `02_couverture_…` | page d'ouverture + page citation |
| `03_annuel_…` | année en un coup d'œil, vue annuelle, dates importantes, objectifs, envies |
| `04_trimestriel_…` | objectifs et bilan des 4 trimestres |
| `05_mensuel_…` | par mois : page de garde + habitudes, double page calendrier, bilan |
| `06_hebdo_…` | les 52/53 doubles pages de semaine |
| `07_extras_…` | tâches récurrentes, liste maîtresse, cadeaux, bilans, dates de l'année suivante, notes |

## 3. Les options utiles

| Option | Effet |
|---|---|
| `--year 2028` | année de l'agenda (jours fériés et Pâques recalculés) |
| `--lang fr / en / both` | langue des pages |
| `--week-start mon / sun / both` | semaine au lundi ou au dimanche |
| `--layout horizontal / vertical / both` | semaines en blocs horizontaux ou en colonnes |
| `--size a5 / a4 / personal / half-letter` | format de page |
| `--sections hebdo,mensuel` | ne régénérer qu'une partie |
| `--months 1-6` | limiter les mois générés |
| `--notes 10` | nombre de pages de notes |
| `--brand "Ma Marque"` | votre nom, imprimé en tout petit dans la marge |
| `--guides` | repères de perforation 6 anneaux (à ne pas laisser sur la version vendue) |
| `--split 3` | 3 jours sur la page de gauche au lieu de 4 |
| `--font-serif Fichier.ttf` | votre propre police (voir plus bas) |
| `--no-separate` / `--no-combined` | ne produire que le PDF complet, ou que les PDF par section |

Exemple, un pack complet signé, sans repères de perforation :

```bash
python3 generate.py --year 2027 --lang both --week-start both --layout both \
  --brand "TERREXO"
```

## 4. Personnaliser (c'est là que se fait la différence)

Trois fichiers, trois niveaux :

- **`planner/theme.py`** — couleurs, épaisseurs de filets, marges, interlignes,
  polices. Changez `line_gap` et tout l'agenda respire différemment ;
  changez `margin_ring` si votre perforatrice mord plus large.
- **`planner/lang.py`** — **tous** les textes (titres, questions des bilans,
  texte d'ouverture). Reformulez-les : c'est ce qui rend le produit vôtre.
- **`planner/pages.py`** — les gabarits eux-mêmes. Chaque page est une petite
  fonction (`month_cover`, `week_spread`, `bucketlist`…) qui n'utilise que les
  briques de `planner/draw.py` (`header`, `lines`, `mini_month`, `box`…).
  Pour créer une page, copiez la fonction la plus proche, renommez-la et
  ajoutez-la à la section voulue dans `generate.py`.

### Utiliser une vraie police de titrage

Les polices par défaut sont celles intégrées au format PDF (aucune licence à
gérer). Pour un rendu plus haut de gamme, téléchargez une police libre de droits
**avec licence commerciale** (Google Fonts : EB Garamond, Cormorant Garamond,
Playfair Display, Jost, Karla…) puis :

```bash
python3 generate.py \
  --font-serif ~/Downloads/EBGaramond-Regular.ttf \
  --font-serif-italic ~/Downloads/EBGaramond-Italic.ttf \
  --font-sans ~/Downloads/Jost-Regular.ttf
```

Vérifiez toujours la licence de la police : « free for commercial use » est
indispensable pour un produit vendu.

## 5. Sur iPad

Les PDF s'ouvrent tels quels dans GoodNotes, Notability ou Noteshelf : importez
le fichier, écrivez dessus au stylet. C'est aussi la façon la plus rapide de
relire vos maquettes avant de les mettre en vente. Pour préparer une version
« digitale » vendue séparément, générez avec `--size a4` (surface d'écriture
plus grande à l'écran).

## 6. Préparer la mise en vente

Ce que contient un pack téléchargeable cohérent :

1. le PDF complet (la version la plus vendue) ;
2. les PDF par section, pour qui ne veut réimprimer qu'une partie ;
3. la fiche « Impression & montage » (section `impression`) ;
4. vos conditions d'usage (usage personnel, pas de revente du fichier).

Quelques points de vigilance :

- **Originalité.** Les grilles de calendrier ne sont pas protégeables, mais les
  textes, les formulations des questions, les visuels de présentation et le nom
  du produit le sont. Les textes livrés ici sont originaux : gardez-les ou
  réécrivez-les, mais ne recopiez pas ceux d'une boutique existante. Faites de
  même pour vos photos de présentation : produisez vos propres maquettes.
- **Vérification.** Avant publication, imprimez une semaine, un mois et une page
  annuelle sur papier, et vérifiez les dates d'un mois au hasard.
- **Traçabilité.** `--brand` imprime discrètement votre nom sur chaque page.

## 7. Structure du dossier

```
agenda/
├── build.command          double-clic sur Mac : installe, génère, ouvre export/
├── generate.py            ligne de commande et assemblage des sections
├── requirements.txt
├── export/                les PDF produits (non versionnés)
└── planner/
    ├── theme.py           couleurs, marges, polices
    ├── lang.py            tous les textes FR / EN
    ├── calendars.py       semaines, grilles mensuelles, jours fériés calculés
    ├── draw.py            briques de dessin (titres, filets, lignes, mini-calendriers)
    └── pages.py           les gabarits de pages
```
