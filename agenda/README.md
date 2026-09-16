# My Line Planner — générateur d'inserts A5

Un script Python fabrique l'agenda complet, prêt à imprimer, en PDF vectoriel.
Deux fichiers sortent par défaut : l'agenda et la fiche d'impression à joindre
à la vente. Tout se régénère en quelques secondes pour une autre année, une
autre langue ou un autre format.

---

## 1. Installation (une fois, sur le MacBook)

Double-cliquez **`build.command`** dans le Finder : il installe ce qu'il faut,
génère le pack et ouvre le dossier `export/`. (Au premier lancement, macOS peut
demander : clic droit → Ouvrir.)

En Terminal, si vous préférez :

```bash
cd ~/chemin/vers/terrexo-site/agenda
python3 -m pip install --user reportlab
python3 generate.py
```

## 2. Ce qui est généré

```
export/
├── CHARTE-MARQUE_My-Line-Planner.pdf          la charte typo de la marque
└── 2027/FR/
    ├── AGENDA-COMPLET_A5_2027_FR_lundi_horizontal.pdf   195 pages
    └── FICHE-IMPRESSION_A5_2027_FR_lundi_horizontal.pdf   1 page
```

Ajoutez `--separate` pour obtenir en plus un PDF par section, et `--pack` pour
générer toutes les variantes (FR/EN × lundi/dimanche × horizontal/vertical).

## 3. La structure de l'agenda

Le produit est organisé en quatre sections, chacune ouverte par un intercalaire.
Les pages alternent automatiquement gauche / droite : chaque double page tombe
juste, et une page blanche est insérée quand il en faut une.

| | Contenu | Pages |
|---|---|---|
| **Ouverture** | page d'accueil de l'année | 2 |
| **Section 1 · Vue d'ensemble** | année en un coup d'œil, vue annuelle (2 p.), dates importantes | 5 |
| **Section 2 · Objectifs** | envies de l'année, objectifs annuels, où j'en suis, 4 × (objectifs + bilan de trimestre), page citation | 13 |
| **Section 3 · Pages datées** | pour chaque mois : page de garde et habitudes, double page calendrier, les semaines du mois, bilan du mois | 160 |
| **Section 4 · Bonus** | tâches récurrentes, liste maîtresse, cadeaux, bilan de l'année, dates 2028, notes | 15 |

Chaque semaine est rangée dans le mois où elle commence, comme dans un agenda
relié : on ouvre janvier, on trouve son calendrier puis ses semaines, et le
bilan du mois avant de passer à février.

### Trois volumes au choix

| `--preset` | Pages | Ce qui change |
|---|---|---|
| `complet` (défaut) | 195 | tout |
| `essentiel` | 178 | sans bilans de trimestre, cadeaux, dates 2028, « où j'en suis » |
| `semainier` | 161 | mois et semaines seulement, plus la vue annuelle |

## 4. Les options

| Option | Effet |
|---|---|
| `--year 2028` | année de l'agenda (Pâques et jours fériés recalculés) |
| `--lang fr / en / both` | langue des pages |
| `--week-start mon / sun / both` | semaine au lundi ou au dimanche |
| `--layout horizontal / vertical / both` | semaines en blocs ou en colonnes |
| `--size a5 / a4 / personal / half-letter` | format de page |
| `--preset complet / essentiel / semainier` | volume de l'agenda |
| `--sections vue-ensemble,pages-datees` | ne régénérer qu'une partie |
| `--months 1-6` | limiter les mois |
| `--notes 10` | nombre de pages de notes |
| `--brand "My Line Planner"` | marque en filigrane (`--brand ""` pour l'enlever) |
| `--guides` | repères de perforation 6 anneaux (à retirer de la version vendue) |
| `--split 3` | 3 jours sur la page de gauche au lieu de 4 |
| `--separate` / `--pack` | PDF par section / toutes les variantes |
| `--no-charte` | ne pas régénérer la charte de marque |

## 5. La marque

**Logotype et titres : Cormorant Garamond.** Une garalde contemporaine, très
fine, dessinée pour les grands corps : elle donne le côté « papeterie haut de
gamme » sans copier personne. Le logotype s'écrit en **Light, capitales,
interlettrage 0,34 em**.

**Intitulés : Jost.** Une linéale géométrique discrète, pour les petites
capitales (LES TROIS PRIORITÉS, NOTES, HABITUDES) : elle apporte la respiration
moderne qui équilibre le serif.

**Chiffres.** Cormorant écrit ses chiffres en style ancien (elzévirien). Dans les
calendriers, le générateur bascule automatiquement sur une variante à chiffres
alignés, plus lisible sur une grille.

Les deux polices sont sous licence **SIL Open Font License 1.1** : usage
commercial libre, y compris pour un produit vendu. Les fichiers sont dans
`agenda/fonts/`, les licences à côté.

**Pour les réutiliser ailleurs** (visuels Etsy, Canva, Word, Instagram) :
double-cliquez les `.ttf` du dossier `fonts/` pour les installer sur le Mac ;
dans Canva, Marque → Polices → Importer une police. Gardez toujours le même
couple Cormorant Garamond / Jost : c'est ce qui fera reconnaître vos produits
d'une année sur l'autre.

La fiche `CHARTE-MARQUE_My-Line-Planner.pdf` reprend tout cela sur une page A4 :
logotype, échelle typographique, couleurs avec leurs codes hexadécimaux.

## 6. Personnaliser

- **`planner/theme.py`** — couleurs, marges, épaisseurs de filets, interlignes,
  polices, échelle du serif.
- **`planner/lang.py`** — tous les textes FR / EN, y compris les intitulés des
  sections et les questions des bilans.
- **`planner/pages.py`** — les gabarits. Une page = une fonction, construite avec
  les briques de `planner/draw.py` (`header`, `lines`, `mini_month`, `box`…).
  Pour ajouter une page : copiez la fonction la plus proche, renommez-la,
  ajoutez-la à sa section dans `generate.py`.

## 7. Sur iPad

Les PDF s'ouvrent dans GoodNotes, Notability ou Noteshelf : importez, écrivez au
stylet. C'est la façon la plus rapide de relire une maquette avant de la mettre
en vente. Pour une version « digitale » vendue à part, générez en `--size a4`.

## 8. Avant de vendre

1. Imprimez une semaine, un mois et une page annuelle sur papier, et vérifiez
   les dates d'un mois au hasard.
2. Composez le pack : l'agenda complet, la fiche d'impression, et vos conditions
   d'usage (usage personnel, pas de revente du fichier).
3. Faites vos propres photos de présentation : les visuels d'une autre boutique
   sont protégés, les grilles de calendrier ne le sont pas.
4. Les textes livrés ici sont originaux. Si vous les réécrivez, gardez-les
   originaux : c'est la partie réellement protégeable d'un agenda.

## 9. Structure du dossier

```
agenda/
├── build.command          double-clic sur Mac : installe, génère, ouvre export/
├── generate.py            ligne de commande, sections et assemblage
├── requirements.txt
├── fonts/                 Cormorant Garamond + Jost (OFL) et leurs licences
├── export/                les PDF produits (non versionnés)
└── planner/
    ├── theme.py           couleurs, marges, polices
    ├── lang.py            tous les textes FR / EN
    ├── calendars.py       semaines, grilles mensuelles, jours fériés calculés
    ├── draw.py            briques de dessin
    └── pages.py           gabarits de pages
```
