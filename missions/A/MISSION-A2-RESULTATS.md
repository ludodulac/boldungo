# 🧱 BOLDÜNGO — MISSION A-2 — un premier micro-toit réel, validation stricte encore incomplète

**Statut : CONSTRUCTION EXPÉRIMENTALE, NON CERTIFIÉE, NE PAS FUSIONNER.**
Branche `feat/lego2-mission-a-stacked-slope-test`, PR #929 DRAFT. `main`, la branche LEGO2 et GUIDED-004 1 890 pièces restent hors modification. **La mission B générale / GUIDED-004 expérimental n'est PAS commencée.**

## FAIT VÉRIFIÉ — reconstruction LDraw

Nouvel assemblage tiré des **deux rangées internes j=1 et j=2 de A1**, en largeur de référence 20 tenons et en bande y=2..3, sans construire la maison entière. Les deux pans utilisent les quatre vrais `30363.dat`. Ils sont portés par quatre piles de vrais `3003.dat` 2×2 (18 briques en tout, têtes de pannes incluses) sur une vraie baseplate `3811.dat`.

Les deux seuls faîtages candidats comparés :

| Contrôle | Candidat conservé 3023b (initial) | Candidat retenu pour poursuite 3022 |
| --- | ---: | ---: |
| Pièces | 25 | **24** |
| Pièces de toiture (pans + faîtage) | 6 | **5** |
| Détail du faîtage | 2 plaques `3023b` 1×2 | **1 plaque `3022` 2×2** |
| Paires de maillages **entre pièces du toit** examinées | 8 | 5 |
| `COLLISION` trouvées entre pièces du toit | **2** | **0** |
| `COLLISION` à la position finale entre les pièces du module **hors baseplate** | **2** | **0** |
| Pièces sans appui dans le graphe nominal corrigé | 0 | 0 |
| Composantes du graphe nominal | 1 | 1 |
| Interfaces pièce de toiture→porteur avec `CONTACT` + coordonnées de tube/tenons compatibles | 6 | **5** |
| Directions d'insertion échantillonnées présentant une collision avant les 4 derniers LDU | 0 | 0 |
| Insertions continues démontrées | **NON** | **NON** |
| Pièces de toiture avec **connexion positive complète certifiée** | 0 | 0 |
| Pièces de toiture sans preuve de connexion positive complète | **6** | **5** |

La vérification à l'état final fait intervenir toutes les paires de pièces **non-baseplate** : 253 paires pour le candidat 3022, 276 pour le candidat 3023b, par rejet exact sur AABB de vrais triangles puis appel à `check_collision` si nécessaire. Les rapports des groupes de pièces du toit comportent 5 ou 8 relations distinctes ; ils ne doivent pas être présentés comme la totalité des paires du module.

**Périmètre exclu de l'exhaustivité du maillage final :** les contacts de l'énorme baseplate `3811` avec les quatre premières briques `3003`. Leur ancrage est documenté par le pas de grille et le catalogue, mais leur test de maillage complet n'a pas été effectué.

### Collision initiale de `30363` contre `3023b` : cause du signal logiciel

Avec les DAT publics LDraw, le moteur retourne deux `COLLISION` entre le pan intérieur droit et les deux petites plaques :

- `right-j2-30363 ↔ ridge-3023b-y2`
- `right-j2-30363 ↔ ridge-3023b-y3`

La recherche de **croisements internes stricts de triangles** avec la routine existante `_tri_intersection_kind` n'en retrouve **aucun**. Le `COLLISION` est produit par le test de **contenance ponctuelle** `_point_in_mesh` appliqué au premier sommet de la plaque dans le maillage de la pente droite :

- Y2 : sommet `(-150, -144, 0)` LDU déclaré « dans » le pan droit.
- Y3 : sommet `(-130, -144, 0)` LDU déclaré « dans » le pan droit.
- Pour les deux : premier sommet du pan droit testé dans la plaque = `False` ; premier sommet de la plaque testé dans le pan droit = `True`.

Ces sommets se trouvent au niveau de l'interface du faîtage `Y=-144 LDU` ; la procédure ne distingue pas encore de manière probante une surface au bord, une cavité recevant un tenon ou un **vrai chevauchement volumique**. **Il serait incorrect de reclassifier la `COLLISION` d'origine en `CONTACT` sans preuve supplémentaire.** Le micro-module ne la masque pas : il **change réellement de pièce**, vers `3022.dat`.

### Nouvelle pièce au faîtage : 3022 2×2

La vraie référence officielle `3022.dat` contient un **`stud4.dat` central en dessous**, une géométrie `box5.dat` et quatre `stud.dat` supérieurs. Elle couvre sur le petit module **les deux tenons de chaque pan**, en grille x=9/10 et y=2/3. Le centre de son tube est exactement sur la frontière entre les quatre cellules (x=10, y=3), au plan d'appui Z=18 plaques (Y=-144 LDU).

La sous-pièce `s/30363s01.dat` contient réellement des `stud4a.dat`/`stud4s.dat` aux positions locales (X=0, Z=-10/-30/-50). Les quatre `30363` du module sont disposées au-dessus de leurs piliers `3003` avec les tenons répartis autour d'une de ces positions de tube. Ces correspondances **de coordonnées et de maillages en position finale** donnent cinq interfaces toiture→appui `CONTACT` et cinq centres de tubes géométriquement alignés, mais pas encore un modèle de friction ni une preuve continue d'insertion/clutch.

### Ordre de montage et directions

Les **24 pièces** sont ordonnées dans le `ORDER.json` CI, ainsi que dans `A2-MODULE-3022-NOTICE-PARTIELLE.md` sur la branche.

Baseplate → piliers 3003 par couches → quatre couronnements 3003 → rangée 30363 j=1 gauche/droite → rangée j=2 gauche/droite → plaque 3022 de faîtage.

Pour chacune des **23 pièces non-baseplate**, huit positions verticales de la trajectoire (48, 32, 24, 16, 8, 4, 2, 0 LDU avant position finale) sont calculées, comparées au maillage des pièces déjà installées. **0 collision avant les 4 derniers LDU**. La nouvelle variante n'a donné **aucune collision de maillage même en position finale** entre ces pièces. **Une telle discrétisation ne prouve PAS la continuité des trajectoires** entre les échantillons, ni la compatibilité mécanique réelle des connexions ; elles restent `NON DÉMONTRÉES`.

### Sources et commandes réellement exécutées en CI

La bibliothèque officielle est téléchargée **seulement** dans le runner, via le miroir épinglé `c43ed06a128a10ed65675166bf42eb6fd608b9b0`.

```bash
python -m pytest -q tests/bricks/test_stacked_roofs_a.py tests/bricks/test_small_roof_a2.py
python scripts/experiment_stacked_roofs_a.py --output artifacts/lego2-mission-a
python scripts/download_ldraw_probe_066.py /tmp/mission-a-ldraw --max-files 240 --parts 30363 3007 3003 3023b 3008 3811 3022
python scripts/probe_stacked_roof_mesh_a.py --ldraw-root /tmp/mission-a-ldraw --output artifacts/lego2-mission-a/LDraw-REAL-MESH-SIX-PAIRS.json
python scripts/verify_small_roof_a2.py --ldraw-root /tmp/mission-a-ldraw --output artifacts/lego2-a2-small-module
cmp missions/A/A2-MODULE-3022-PROPOSE.ldr artifacts/lego2-a2-small-module/3022/SMALL-ROOF-A2.ldr
```

Une CI spécialisée sur la version avant la dernière correction d'ID a fourni **14 tests PASS** (run #40105025308), un fichier LDraw et deux JSON d'audit sans erreurs d'exécution ; la CI générale et spécialisée du HEAD final doivent être vérifiées distinctement. La correction d'identité `baseplate` aligne ensuite la racine du graphe nominal avec le contrat **déjà existant** de `_audit`, dont les données précédentes comptaient à tort tous les éléments comme non reliés en partant du nom `module-base-3811`.

### Livrables branchés

- `missions/A/A2-MODULE-3022-PROPOSE.ldr` — 24 vrais placements, commis **sur la branche**, contrôlés par `cmp` contre la version régénérée en CI.
- `missions/A/A2-MODULE-3022-BOM.json` — **24 pièces** : 18×3003, 4×30363, 1×3022, 1×3811.
- `missions/A/A2-MODULE-3022-NOTICE-PARTIELLE.md` — ordre clair, garde-fous.
- `scripts/construct_small_roof_a2.py` et `scripts/verify_small_roof_a2.py` — variantes et audit existants réutilisés.
- `tests/bricks/test_small_roof_a2.py` — contrôle des familles, pièces, rangées, conservations et de la racine nominale.
- Artefacts CI des deux candidats : LDraw, nomenclatures, `ORDER.json`, `REAL-LDRAW-ROOF-AND-INSERTION.json`, `COMPARE-CANDIDATES.json`.

## HYPOTHÈSE

Le faîtage `3022` et les quatre `30363` constituent un candidat **géométriquement compatible à la position finale** sur les interfaces étudiées et non bloqué dans les positions de descente échantillonnées. Les rangées restent individuellement reprises sur des supports 3003 : **aucun cliquetage direct `30363→30363` n'est présumé** à partir de leur simple recouvrement.

L'interprétation de la collision du candidat `3023b` comme défaut de test de contenance sur une surface coplanaire reste une **HYPOTHÈSE**, pas un fait physique validé.

## RECOMMANDATION

**NE PAS encore promouvoir le résultat à A1 complète.** Un assemblage géométrique entièrement démontré nécessiterait : analyse de l'insertion **continue**, classification exacte de la compatibilité d'emboîtement avec le tube et chaque tenon officiel, contrôle de l'accrochage de la baseplate `3811` ainsi que l'audit de toutes les interfaces de la maison étendue. Aucune de ces preuves ne peut être remplacée par le graphe nominal.

La mission A-3 est la **dernière possible** : privilégier un contrôle mécanique/géométrique de l'interface minimale `30363↔3003↔3022` et de l'insertion, sans nouveau système complexe. Si le contrôle échoue, proposer **CHANGER D'APPROCHE**, en conservant cette version 24 pièces et ses preuves. Ne demander aucun test physique à Ludo.

**Décision A-2 : MICRO-MODULE CONSTRUIT NUMÉRIQUEMENT ; zéro collision statique détectée hors baseplate en variante 3022 ; N5 et N6 NON DÉMONTRÉS.**
