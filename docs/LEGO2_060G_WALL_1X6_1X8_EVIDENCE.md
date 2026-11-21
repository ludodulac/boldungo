# LEGO2-060G — BRICK_1X6 ↔ BRICK_1X8 : preuve nominale ciblée

## Provenance de la véritable maison

- GUIDED-004 : `artifacts/lego2-guided-004/brick-model.json` régénéré à partir
  de `scripts/export_guided004_lego.py`, **1 890 pièces inchangées**.
- Référence 060F : export GitHub Actions #39111261074, HEAD
  `75e8cf918d5648b07881b20a4f4ab8a1a3c8c733`.
- Périmètre direct de `connectors.py` : 1 590 contacts verticaux candidats,
  dont 1 032 VALID, 558 UNKNOWN et 0 INVALID avant 060G.
- Famille choisie : 162 UNKNOWN, dont 83 BRICK_1X6 sous BRICK_1X8 et
  79 BRICK_1X8 sous BRICK_1X6 (162 contacts « wall » ↔ « wall »).
- Les 162 contacts observés ont la **même** orientation aux deux niveaux :
  77 cas (rotation 0/0), 85 cas (rotation 1/1). Empreinte transverse :
  exactement une colonne. Chevauchement longitudinal : 1 à 6 tenons.

## Sources géométriques LDraw officielles

Fichiers analysés, sans copier les fichiers LDraw dans le dépôt :

- https://library.ldraw.org/library/official/parts/3009.dat
- https://library.ldraw.org/library/official/parts/s/3009s01.dat
- https://library.ldraw.org/library/official/parts/3008.dat
- https://library.ldraw.org/library/official/parts/s/3008s01.dat
- https://library.ldraw.org/library/official/p/stug3-1x7.dat
- https://library.ldraw.org/library/official/p/stug-1x8.dat
- https://library.ldraw.org/library/official/p/stud.dat
- https://library.ldraw.org/library/official/p/stud3.dat

Référence de géométrie nominale : une unité LDraw (LDU). Les deux briques
ont une largeur totale de 20 LDU et une hauteur de corps de 24 LDU.

- BRICK_1X6 : tenons supérieurs centrés à **±10, ±30, ±50 LDU** sur
  l'axe long ; cinq `stud3` internes centrés à **−40, −20, 0, 20, 40 LDU**.
  Demi-largeur intérieure de la cavité : **6 LDU** ; demi-longueur
  intérieure : **56 LDU**.
- BRICK_1X8 : tenons supérieurs à **±10, ±30, ±50, ±70 LDU** ;
  sept `stud3` à **−60, −40, −20, 0, 20, 40, 60 LDU**.
  Cavité intérieure : demi-largeur **6 LDU**, demi-longueur **76 LDU**.
- `stud.dat` : rayon extérieur **6 LDU**, hauteur **4 LDU**.
  `stud3.dat` : rayon **4 LDU**, inclus dans les sous-pièces avec
  un facteur 5 selon l'axe vertical de l'élément inférieur.
- Les tenons des deux pièces sont sur une grille de 20 LDU. Dans une
  connexion horizontale parallèle sur la grille, un tenon inférieur
  recouvert est à 10 LDU des centres `stud3` internes les plus proches :
  **6 + 4 = 10**, contact tangentiel nominal sans interpenetration.
  Le dégagement vis-à-vis des parois intérieure transversales est de
  **6 − 6 = 0 LDU**, et le dégagement minimal aux extrémités
  **(10n−4) − (10n−10) − 6 = 0 LDU**.
- L'ouverture intérieure de la brique supérieure accueille donc
  géométriquement chaque tenon inférieur recouvert par l'empreinte,
  dans les orientations et empilements **strictement examinés**.

Ces égalités démontrent une compatibilité de géométrie **nominale au modèle
LDraw**, **pas** une réserve de tolérance positive, une force de serrage,
la résistance de la liaison ni la faisabilité de l'insertion.

## Configuration reconnue dans `connectors.py`

La règle 060G retourne VALID uniquement pour des catégories `brick`,
la paire exacte {BRICK_1X6, BRICK_1X8}, les plans verticaux en contact,
aucune collision solide, des orientations communes 0/0 ou 1/1, des
axes longs parallèles et des lignes transversales confondues, avec 1 à 6
colonnes de tenons effectivement communes.

Toutes les autres familles, les orientations 2/3, les croisements d'axes
et les catégories sémantiques différentes restent **hors de cette preuve**.
`connectors.py` conserve leurs états antérieurs, dont UNKNOWN.

## Effet mesuré sur les contacts stricts de GUIDED-004

| Indicateur | 060F | 060G |
|---|---:|---:|
| Contacts admissibles (périmètre strict) | 1 590 | 1 590 |
| VALID | 1 032 | **1 194** |
| UNKNOWN | 558 | **396** |
| INVALID | 0 | **0** |
| Contacts de cette paire restant UNKNOWN | 162 | **0** |
| Pièces supérieures candidates sans au moins un VALID | 277 | **187** |

**90 pièces supérieures** obtiennent au moins un contact VALID qui leur
manquait auparavant. Ce décompte est fondé sur les 905 pièces supérieures
ayant au moins une interface candidate dans le périmètre 060F ; il ne constitue
**pas** une vérification de connectivité globale ou d'ordre d'assemblage.

## Périmètre explicitement hors certification

La maison garde `NOT_CERTIFIED` : les modèles de connexion nominale ne
prouvent pas la force de clutch, le flambement, la stabilité, la résistance
des murs, l'accessibilité, les trajectoires d'insertion ni la constructibilité
complète. Les 420 pièces hors catalogue orthogonal et les 523 pièces aux
catégories sémantiques non admises par le validateur restent exclues du
décompte strict ; les variantes 059M/059N restent expérimentales.

Les règles de `GEOMETRY_ONLY` / `CONNECTOR_EVIDENCE_STRICT` de 060B/060C
ne sont pas modifiées ; une connexion UNKNOWN n'est jamais promue par
le chemin strict sans sa propre preuve.
