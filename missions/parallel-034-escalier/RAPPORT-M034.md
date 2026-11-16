# GRAND-PÈRE BOLDÜNGO — M034 : escalier extérieur (CONSTRUCTION 3)

**État : prototype LEGO réel en pièces standards, précontrôles nominaux réussis, intégration architecturale et stabilité NON CERTIFIÉES.**

## Mandat et provenance
- Branche indépendante : `feat/boldungo-parallel-034-escalier`.
- Départ exact : `0f5bfe1836598f7050089c54a415123f06d33945`.
- **Maison de référence réellement lue** : `missions/B3/generated/GUIDED004-B3-1904.ldr` ; **1 904 pièces**, dont **408 pentes 30363**. Le canonique, ses ouvertures, le toit, la terrasse, le moteur et les PR des autres équipes sont intacts.
- Lecture des documents d'audit photographique : `missions/ARCHITECTURE-REFERENCE-ESCALIER-L/ANALYSE-PHOTOS-109.md` et `ESCALIER-L-TOPOLOGIE-V1.md`. **Les photographies originales n'ont pas été réexaminées directement dans cette mission** ; leur interprétation provient de l'audit archivé.
- Cible qualitative : **escalier extérieur en L**, le long de la façade Sud, continuant vers l'Ouest au-delà de l'arrière, virage à gauche en DESCENTE vers le Sud et la cour ; palier, deux volées, liaison haute au béton et non au platelage bois.

## Ce qui est effectivement construit
- `ESCALIER-M034-PROTOTYPE.ldr` : **485 pièces LEGO réelles**, `3022.dat` (2×2), `3020.dat` (2×4) et `3795.dat` (2×6), chaque référence attestée au catalogue LDraw officiel.
- **7 marches de volée basse** et **9 marches de volée haute**, palier 6×6 tenons. Attribution 7/bas + 9/haut = **hypothèse de travail** : les anciens documents photographiques confirmaient 7+9 sans confirmer rigoureusement leur attribution.
- Noyau expérimental plein, assemblé par couches de plaques à joints décalés dans les deux directions ; il n'est pas la plateforme réelle ni le vide sous celle-ci. Les parapets réels ne sont pas modélisés à cette étape.
- **6 tenons de largeur**, soit **1,20 m dans l'échelle nominale GUIDED004 de 100 LDU/m**, contre **1,12 m déclarés** (+**7.14 %**). Profondeur de marche supposée **0,40 m** ; contremarche supposée **0,16 m** ; niveau d'accès supérieur **2,72 m**. Ce sont des choix de prototype, **pas des mesures nouvelles du bâtiment**.
- L'escalier démonstrateur va de z=6,0 à 10,8 m dans le repère du modèle, dépassant le plan arrière documentaire vers z=8,20 m. Le débord obtenu de 2,60 m n'est **pas mesuré sur les photographies**. Son bord côté bâtiment est à x=0 dans le LDraw ; le mur de la scène B3 est environ à x=300 LDU : **le prototype reste délibérément déporté et non raccordé au mur**, car les interfaces de la véritable plateforme restent contradictoires.
- Le fichier LDraw ne contient **que les pièces neuves du prototype**. Il n'efface ni ne remplace les anciennes marches présentes dans B3.

## Résultats calculés (précontrôle reproductible)
| Test | Résultat | Limitation |
| --- | --- | --- |
| Source GUIDED004-B3 | **PASS** : 1 904 pièces, 408 pentes | Source non modifiée |
| Références LEGO et nomenclature | **PASS** : 485 plaques, 3 références | Disponibilité de stock non vérifiée |
| Dimensions/7+9 | **PASS géométrique** : 6 tenons, 7+9, palier en L | Giron/hauteur/implantation *inférés* |
| Collision des volumes orthogonaux nouveaux | **PASS : zéro cellule occupée deux fois** | Contrôle boîtes sans maillage de tenons |
| Appuis sous plaques | **PASS nominal : 0 sans support** | Ne mesure pas la charge |
| Graphe d'emboîtements | **PASS nominal : 1 composant**, 957 liens pièce-à-pièce, 3828 positions tenon/logement sur grille | Ni extraction de connecteurs LDCad ni mesure de serrage |
| Conflit nouveau prototype / maison B3 | **PASS préliminaire : 0 recoupement AABB** avec 1496 pièces orthogonales d'origine | Les 408 pentes n'ont pas été maillées ; leur emprise est séparée dans ce repère |
| Assemblage au béton et au mur | **NON DÉMONTRÉ** | Position expérimentale volontairement déportée |
| Insertion, rigidité, descente de charges | **NON TESTÉS / NON CERTIFIÉS** | Essai physique ou calcul indépendant requis |

**Attention : le fait que le graphe nominal soit connexe ne prouve pas qu'on puisse introduire toutes les plaques, que le serrage soit suffisant ou que l'escalier puisse porter une charge.** Les plaques supérieures restent à tenons visibles, sans finition carrelage ni garde-corps.

## Fichiers
- `build-stair.mjs` : génération reproductible sans dépendances, y compris contrôle contre le fichier canonique lu seul ; exécuter depuis le dépôt : `node missions/parallel-034-escalier/build-stair.mjs`.
- `ESCALIER-M034-PROTOTYPE.ldr` : sous-assemblage autonome ouvrable dans un logiciel LDraw.
- `NOMENCLATURE-M034.md` : décompte des plaques.
- `APERCU-M034.svg` : plan et profils métriques schématiques (ce n'est **pas** une capture de rendu LDraw).
- `CONTROLES-M034.json` : compteurs mesurés et limites explicites.

## Étape avant intégration
Reprendre les **cotes réelles** du palier, les hauteurs, le giron et le débord Ouest à partir des photos et/ou d'un relevé ; choisir une position sans interférence avec la vraie plateforme béton, la terrasse bois et les vieilles marches de B3. Concevoir ensuite les parapets et des **appuis démontables avec connecteurs authentifiés par la bibliothèque LDraw/LDCad** ; contrôler les surfaces solides exactes et le montage, puis seulement envisager l'intégration. **Aucune modification du modèle source ni fusion dans cette PR DRAFT.**
