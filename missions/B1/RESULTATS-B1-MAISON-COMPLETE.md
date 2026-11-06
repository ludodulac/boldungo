# 🧱 BOLDÜNGO — MISSION B-1 — MAISON GUIDED-004 EXPÉRIMENTALE COMPLÈTE

**Résultat réel :** une maison complète de **1 901 vraies positions de pièces LDraw** produite en CI à partir de la scène GUIDED-004, en préservant entièrement le modèle canonique **1 890 pièces**. Modèle 1901 issu **exclusivement** de la variante existante `088` qui recompose les tuiles de faîtage ; **aucune nouvelle famille de pente** n'a été substituée. PR **#931**, DRAFT, non fusionnée ; base LEGO2.

**Source de vérité :** `frontend/data/boldungo2-guided-004-real-scene.json`, SHA-256 `752c407f3e087e18f71e4e298a152a87f30011692affff0d210b65933a1ae98e`.

## FAIT VÉRIFIÉ

Le nouveau script `scripts/build_guided004_full_house_b1.py` réutilise **sans les modifier** :
- `scripts/export_guided004_lego.py` : régénération 1890 **dans un dossier temporaire B-1 distinct**, pas dans le chemin canonique ;
- `scripts/construct_guided004_roof_088.py` : **1901** pièces via remplacement de **12** anciennes tuiles plates de faîtage par **23** briques de liaison expérimentales ;
- `brickhouse.bricks.geometry_adapter` : identités de pièces, transformation 3D en LDraw de **1901/1901** positions, y compris **408** pentes authentiques `30363` orientées selon les vraies géométries officielles téléchargées à version épinglée ; **0 pièce omise** de ce BrickModel ;
- `generate_bom`, `generate_assembly_plan`, `audit_physical_model` préexistants.

Les **1878 pièces d'origine hors tuiles de faîtage** sont identiques **au placement près**. Toutes les géométries de murs, ouvertures, terrasses, escaliers et cheminées déjà modélisées par l'export canonique restent conservées dans cette copie. Les ouvertures sont modélisées comme réservations/vides : **ceci ne prouve pas des cadres, vitres ou portes fonctionnelles**, puisque le BOM original ne contient pas les références LDraw de vitrage/portes à ce stade.

| Métrique | Résultat B-1 |
|---|---:|
| Source canonique inchangée | **1890 pièces** |
| Copie expérimentale | **1901 pièces** |
| Différence nette | **+11** (`-12` tuiles anciennes, `+23` nouvelles liaisons) |
| Pentes 18° (`30363`), progression globale proche 21,8° | **408, inchangées** |
| LDraw type-1 exportés | **1901/1901** |
| Références LDraw distinctes | **17** |
| Étapes de montage **PROPOSÉES**, dont 1 supplémentaire explicitement expérimentale | **271** |
| Pièces sans appui immédiat dans l'audit orthogonal | **42** |
| Composantes **orthogonales** par contact nominal tenon/grille (toiture inclinée exclue) | **26** |
| Collisions **en cellules voxels orthogonaux** détectées | **0** |
| Pentes de toiture dont les vrais accouplements restent non démontrés | **408** |
| Pièces ne disposant pas d'une **chaîne complète mécaniquement démontrée** | **1901 / 1901** (preuve complète indisponible, pas démonstration que toutes sont flottantes) |
| Composantes de toute la maison selon attaches réelles tenon/tube | **NON ÉTABLIES** |
| Collisions sur tous les maillages officiels incluant la toiture | **NON EXAMINÉES exhaustivement** |
| Insertion continue de l'ensemble | **NON DÉMONTRÉE** |
| Résistance mécanique | **NON CERTIFIÉE** |

**Attention** : zéro collision *voxel orthogonale* ne veut absolument pas dire zéro collision physique globale. Le nombre **26** concerne **1493** pièces orthogonales et **exclut les 408 pentes** de toiture, il **n'est PAS** le nombre de composantes de la maison physique totale. Les **42** pièces sans appui immediate sont le résultat du même audit orthogonal, non de la vraie simulation physique de toute la maison.

**Rendu :** `GUIDED004-B1-FULL-HOUSE-ISOMETRIC.svg` contient **5703 faces dessinées depuis les vraies coordonnées** ; c'est une **isométrie schématique des volumes**, PAS un rendu fidèle des vrais maillages LDraw. Le fichier `.ldr` contient quant à lui toutes les **1901 vraies références et transformations officielles**. Les fichiers complets, nomenclature, contrôles et notice proposée sont dans l'artefact Actions, pas dans un commit d'assets volumineux ; le générateur et les tests sont bien versionnés GitHub.

### Livrables de l'artefact Actions B-1

**CI spécialisée : [run #40200030268 — SUCCESS](https://github.com/ludodulac/boldungo/actions/runs/40200030268)**. Artefact direct : [BOLDUNGO-B1-GUIDED004-1901-FULL-HOUSE-EXPERIMENTAL-NOT-CERTIFIED](https://github.com/ludodulac/boldungo/actions/runs/40200030268/artifacts/12602045320), 30 jours de conservation.

Dans le ZIP :
- `EXPERIMENTAL-1901-FULL-HOUSE/GUIDED004-B1-FULL-HOUSE-22DEG.ldr` — vrai modèle complet ;
- `.../GUIDED004-B1-FULL-HOUSE-ISOMETRIC.svg` — vue 3D isométrique schématique ;
- `.../BRICKMODEL-EXPERIMENTAL-1901.json` — structure de toutes les pièces ;
- `.../BOM.json` — nomenclature exacte, commande de pièces interdite ;
- `.../ASSEMBLY-ORDER-NOT-CERTIFIED.json` — plan 271 étapes, 23 nouveaux joints explicitement `NOT_DEMONSTRATED` ;
- `.../CONNECTIONS-AND-COLLISIONS.json` — audit orthogonal borné et limites ;
- `.../COMPARISON-WITH-1890-CANONICAL.json` — SHA-256, invariants de la maison et deltas ;
- `READONLY-CANONICAL-1890-REGEN/brick-model.json`, `inventory.json`, `validation.json`, `viewer-export.json` — originaux de comparaison régénérés isolément, non écrits dans le dossier canonique ;
- `REUSED-088-RIDGE-CANDIDATE/CONSTRUCTION-DECISION-088.json` et différences de faîtage originales.

### Commandes réellement exécutées par GitHub Actions

```bash
python -m pip install -e .
python -m pip install -e ./lego_geometry_engine
python -m pip install pytest
python -m pytest -q tests/bricks/test_guided004_full_house_b1.py

python scripts/download_ldraw_probe_066.py /tmp/lego2-b1-real-30363 --max-files 150 --parts 30363

python scripts/build_guided004_full_house_b1.py \
  --ldraw-root /tmp/lego2-b1-real-30363 \
  --output artifacts/lego2-b1-guided004
```

Sorties brutes pertinentes, CI #40200030268 :

```text
7 passed in 1.56s
B1_NONRIDGE_OLD_IDS_UNCHANGED 1878 NEW_EXPERIMENTAL_RIDGE_JOINTS 23
B1_FULL_HOUSE {
 "assembly_steps":271,"canonical":1890,"experimental":1901,
 "fully_proven_load_paths":0,"mapped_ldraw":1901,"unmapped":0,
 "orthogonal_connected_components":26,"orthogonal_unsupported":42,
 "orthogonal_voxel_collision_cells":0,"roof_slopes":408,
 "roof_unverified":408,"svg_faces":5703,"no_full_support_proof":1901
}
B1_ALL_SOURCE_BYTES_UNCHANGED YES
B1_FULL_1901_REAL_LDRAW_PARTS_PASS
B1_ALL_NON_RIDGE_ARCHITECTURE_IDENTICAL_PASS
B1_408_SLOPE_PARTS_PRESERVED_NO_45DEG_PASS
B1_1890_SOURCE_ISOLATED_AND_HASHED_PASS
```

## HYPOTHÈSE — ce que la copie démontre et ne démontre pas

Nous avons effectivement **une maison complète visible et exportable**, pas une simple toiture isolée. Le placement des **408** pentes 30363 reste issu des données de GUIDED-004 avec progression proche de **21,8°**, sans substitution aux briques 45° de R-3.

Le faîtage 088 créé **23 nouveaux joints** là où la maison 1890 possédait **12 anciennes tuiles de sommet** ; **la vraie compatibilité géométrique tenon/cavité de la toiture complète n'est pas démontrée**. L'assemblage peut notamment échouer mécaniquement au sommet, sur les appuis de pente, à la terrasse et à la jonction des deux cheminées. Ce sont des **inconnus**, pas des impossibilités physiques démontrées.

Les 42 manques d'appui direct auditables avec briques orthogonales, les 26 composantes orthogonales et les deux cheminées précédemment isolées demandent de vrais choix de construction avant certification. **Les ouvertures sont des vides fidèles à la modélisation existante, mais le modèle ne prétend pas avoir déjà des véritables blocs de vitrage ou menuiseries**.

La recette R-3 (45°) **n'a PAS été appliquée** à cette maison : elle trahirait la pente de la Scene. Le travail A (~21,8° de progression 30363) reste une **référence d'audit** dont la constructibilité n'est pas automatiquement transférée à 408 pièces.

## RECOMMANDATION — clôture B-1, sans démarrer B-2

**CONTINUER sous contrôle de Grand-père/Ludo, exclusivement dans la PR #931 DRAFT.** La première priorité n'est plus de générer une image, mais de **résoudre les déconnexions réellement identifiées sur la copie 1901**, en commençant par la toiture/faîtage et les chaînes de support, **puis les cheminées et la terrasse**, sans altérer la scène. Une éventuelle B-2 relève d'une décision future ; B-1 ne l'entame pas.

**Protections :** `main`, branche LEGO2, PR #929/#930, GUIDED-004 canonique 1890 et anciens modules intacts. Aucune fusion, aucune dépense, aucun test physique demandé à Ludo. La mécanique de la maison est explicitement `NOT_CERTIFIED`.
