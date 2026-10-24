# BOLDÜNGO — R-1 : CONSTRUCTION ET PREMIÈRE PREUVE BORNEE

**Mission : R-1, première des trois au maximum.**
**Statut : CONSTRUCTION EFFECTIVE, NOTICE LEGO OFFICIELLE RETROUVÉE ; RÉALISABILITÉ TOTALE NON CERTIFIÉE.**
**PR expérimentale : #930 DRAFT**, branche `feat/lego2-r1-official-31009-roof`, base `feat/lego2-existing-house-021`. PR A #929 conservée sans modification, `main`/branche LEGO2/GUIDED-004 intacts.

## FAIT VÉRIFIÉ

**Référence principale :** LEGO Creator **#31009 Small Cottage / La petite maison**, livret **1/3**, notice officielle **6038244.pdf**, consultation réelle des diagrammes pages **47 à 68** (étapes 1–25). Les deux pans et la disposition progressive de vraies briques inclinées 45° sont visibles pages 49, 53, 55, 60, 63 et 65 ; supports en briques et plaques visibles pages 47–48, 51, 57 et 61. La notice précise son ordre de montage, elle ne présente pas une certification de notre adaptation.

**Pièces officielles :** le set emploie des longues pentes **`4445` (45°, 2×8)**, avec des petites variantes **`3037`, `3038`, `3039`** référencées dans l'inventaire du set. Notre modèle utilise `4445` comme famille de toiture et des supports nouveaux en `3007/3003`, 4 plaques de faîtage `3022` et 1 baseplate `3811`.

**Livrables effectifs sur GitHub :**
- `R1-31009-EXPERIMENT.ldr` — 41 placements authentiques LDraw (modèle 3D).
- `BOM.json` — 41 pièces, exactement 28 × 3003, 4 × 3007, 4 × 4445, 4 × 3022, 1 × 3811.
- `ORDER.json` — 41 placements ordonnés : base → piliers → pannes → rangée basse → rangée haute → faîtage. **L'ordre expérimental n'est pas celui du set !**
- `NOTICE-SOURCE-ET-CONSTRUCTION.md` — pages exactes, références et différences.
- `scripts/experiment_official_roof_r1.py` — recette 8 tenons de portée, `--length-studs 8|16` pour répéter le motif longitudinal sans se servir d'une mesure de GUIDED-004.
- `scripts/probe_official_roof_r1.py` — contrôle borné au maillage LDraw officiel, aucun outil géométrique général ajouté.
- `tests/bricks/test_official_roof_r1.py` — deux longueurs 8/16, exactitude BOM/ordre, valeurs rejetées et décalage volontaire de pente de 1 tenon rejeté.

### Résultats du vrai contrôle LDraw de R-1

Source : `pybricks/ldraw` épinglé au commit `c43ed06a128a10ed65675166bf42eb6fd608b9b0`, fichiers DAT officiels non commis.

Un `4445.dat` officiel contient **7 tubes creux `stud4a.dat`**, dont les centres ont été comparés par transformations 3D exactes aux **7 trous de la grille** des deux rangées de 8 tenons du support `3007.dat`.

**4/4 appuis de pentes `4445→3007` vérifiés en projection réelle, profondeur d'insertion des tenons : 4,0 LDU.**

Le moteur de collision existant donne :
- 4 liaisons `4445→3007` : `CONTACT`.
- 8 liaisons de quatre plaques `3022` vers deux pans supérieurs : `CONTACT`.
- 2 jonctions entre les rangs `4445` successifs (gauche/droite) : `CONTACT`.
- **0 COLLISION** détectée sur ces **14 paires effectivement examinées**.

Le rapport n'annonce pas « zéro collision sur 41 pièces » : les **820 paires possibles** ne sont PAS toutes évaluées, notamment empilements de piliers, baseplate et trajets d'insertion.

**Graphe NOMINAL :** 41 pièces, 8 de toiture, 48 liens de support, 0 pièce sans chemin d'appui **nominal**, 1 composante nominale.

**Connexions démontrées à la position finale : 8/8 pièces de toiture.** Les quatre 4445 possèdent chacune 7 alignements de tubes sur pannes 3007 (profondeur 4 LDU). Les quatre faîtages 3022 possèdent chacun quatre tenons provenant des deux versants aux positions (±10,±10) LDU dans leur tube central (profondeur 4 LDU). Les 12 interfaces de soutien du toit donnent `CONTACT` au maillage officiel, et les deux jonctions de rangs donnent `CONTACT`. **Aucune de ces vérifications statiques n'est une preuve d'insertion continue.** Tous les appuis des piliers et pannes sur fondations ne sont documentés que par le graphe nominal, ils ne doivent PAS être qualifiés de certifiés.

**Pièces sans appui démontré selon le critère strict :** 0 sans appui NOMINAL ; **0 élément de toiture sans interface statique locale vérifiée**, mais les **32 éléments structurels hors fondation** n'ont pas encore une chaîne de preuves réelles complète. Un nombre de « pièces sans chaîne géométrique complète démontrée » ne peut donc pas être annoncé 0 ; **40/40 pièces autres que la baseplate restent sans chaîne de la pièce jusqu'aux fondations intégralement certifiée**, car aucun pilier n'a encore une chaîne réelle complète validée.

**Insertion continue :** NON DÉMONTRÉE dans notre adaptation, y compris en présence d'une vraie notice LEGO de référence. **Résistance mécanique/physique :** NON DÉMONTRÉE.

### Différences importantes avec LEGO 31009

- Le set officiel comprend la maison entière, une lucarne et une toiture plus détaillée avec plusieurs longueurs `4445/3037/3038/3039`.
- R-1 ne reproduit que le principe de *briques inclinées à 45° en plusieurs rangées, sur briques/plaques*, sans lucarne et avec deux pans de deux rangs.
- Les 28 piliers, quatre pannes et les quatre plaques de faîtage du petit module sont des choix expérimentaux propres à R-1, **non extraits à l'identique de la notice**.
- La hauteur d'un rang est décalée de **3 plaques** par rapport au précédent, la couverture est à gradins ; la continuité de pente parfaite n'est pas prouvée et n'est pas revendiquée.

### Commandes réelles de GitHub Actions

```bash
python -m pip install pytest
python -m pip install -e ./lego_geometry_engine
python -m pytest -q tests/bricks/test_official_roof_r1.py
python scripts/experiment_official_roof_r1.py --length-studs 8 --output artifacts/lego2-r1-official-roof
cmp missions/R1/R1-31009-EXPERIMENT.ldr artifacts/lego2-r1-official-roof/R1-31009-EXPERIMENT.ldr
cmp missions/R1/BOM.json artifacts/lego2-r1-official-roof/BOM.json
cmp missions/R1/ORDER.json artifacts/lego2-r1-official-roof/ORDER.json
python scripts/download_ldraw_probe_066.py /tmp/lego2-r1-ldraw --max-files 240 --parts 4445 3007 3003 3022 3811
python scripts/probe_official_roof_r1.py --ldraw-root /tmp/lego2-r1-ldraw --output artifacts/lego2-r1-official-roof/REAL-LDRAW-GEOMETRY.json
```

**Journaux bruts utiles d'un run spécialisé réussi (#40124195501, avant le dernier changement de tests) :**

```text
8 passed in 0.08s
R1_BUILT {"total_parts":41,"roof_parts":8,"nominal_unsupported_count":0,"nominal_components":1}
R1_COMMITTED_MODEL_BOM_ORDER_EQUALS_GENERATED
R1_PRIMITIVE_4445_TO_3007 left-c0-b0-roof centres True depth_ldu 4.0
R1_PRIMITIVE_4445_TO_3007 right-c0-b0-roof centres True depth_ldu 4.0
R1_PRIMITIVE_4445_TO_3007 left-c1-b0-roof centres True depth_ldu 4.0
R1_PRIMITIVE_4445_TO_3007 right-c1-b0-roof centres True depth_ldu 4.0
R1_MESH_MATE (4 x slope-to-purlin) CONTACT
R1_MESH_MATE (8 x ridge-to-upper-slope) CONTACT
R1_PRIMITIVE_3022_RIDGE (4 x) centres True depths [4.0, 4.0, 4.0, 4.0]
R1_ADJACENT_COURSES (2 x) CONTACT
R1_GEOMETRY_SUMMARY {
  "mesh_collisions_detected_in_checked_pairs":0,
  "roof_supporting_mesh_pairs_checked":12,
  "adjacent_course_mesh_pairs_checked":2,
  "nominal_support_edges":48,
  "real_4445_to_3007_primitive_mates_aligned":4,
  "real_3022_to_opposing_4445_four_stud_mates_aligned":4,
  "all_eight_roof_parts_have_verified_static_mating_geometry":true,
  "all_model_mesh_pairs_checked":false,
  "full_insertion_proven":false,
  "physical_strength_proven":false
}
R1_PROVENANCE_GUARDS_PASS 31009 PIECES 41 N6_NOT_CERTIFIED
```

Les tests rajoutent depuis un rejet explicite d'une pente volontairement décalée. Le statut du dernier HEAD / CI doit être revérifié à la fin de la conversation.

## HYPOTHÈSE

Les vraies pentes `4445` et le montage par rangs figurant dans une notice LEGO sont une bonne base de recette reproductible ; cependant **notre nouvelle structure 3007/3003/3022 n'est pas le montage précis de cette notice**. Le nombre de paires contrôlées est ciblé, et la méthode ne peut être directement déclarée constructible sur une maison réelle.

## RECOMMANDATION

**CONTINUER seulement sur une base officielle**, dans les missions R-2/R-3 si Grand-père le juge utile : privilégier le **soubassement / faîtage exactement documenté par LEGO #31009**, afin de réduire l'écart avec la notice, plutôt que développer de nouveaux vérificateurs d'insertion pour des assemblages originaux. Conserver R-1 et les preuves, sans fusion et sans transfert vers GUIDED-004. Une priorité serait de simplifier davantage les piliers et d'adopter la plateforme support originale avant toute généralisation.

**R-1 termine avec un fichier concret de 41 pièces ; ce n'est pas une preuve complète de solidité ou de montage. A-1/A-2/A-3 restent clos, aucune R-2 ou B commencée.**
