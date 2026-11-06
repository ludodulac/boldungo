# 🧱 BOLDÜNGO — B-3 / BILAN FINAL DU CHANTIER B (3/3)

**PR [#931](https://github.com/ludodulac/boldungo/pull/931), DRAFT.** B-1/B-2 maintenus intacts, canonique GUIDED-004 **1 890**, Scene, `main`, branche LEGO2, PR #929/#930 et précédents prototypes inchangés ; aucune fusion, dépense ou test physique.

## FAIT VÉRIFIÉ — un raccord de deux structures porteuses, chaîne encore PARTIELLE

Une **nouvelle maison entière de 1 904 pièces** est produite à partir de B-2 **1 905**, en **remplaçant exactement deux segments intérieurs** de poteau par **une vraie brique 2×4 LEGO (`BRICK_2X4` / LDraw `3001`)**. Aucune planche, ouverture, cheminée, mur ou pièce de toiture déplacée. Toutes les 408 pièces `30363` conservent leur orientation et progression proche de 22°.

**Pièces exactes remplacées**, déterminées par leurs emprises dans le modèle (pas de cotes GUIDED-004 en dur) :
- Retirée : `scene-platform:south-timber-deck-main:support-solution:timber-post-east:0027:00020` — `3005` 1×1 à la couche z=27..30.
- Retirée : `scene-platform:south-concrete-platform:support-solution:concrete-support-west:0027:00010` — `3003` 2×2 à z=27..30.
- Ajoutée : `EXPERIMENT-B3-CONCRETE-TO-TIMBER-BRIDGE` — **`3001` 2×4** à (x=3, y=15, z=27), sur les mêmes niveaux, **à l'intérieur du sous-plancher des terrasses**. Elle chevauche en projection les lignes de tenons précédemment occupées par les deux segments et remplit la jonction entre les colonnes.

L'essai préalable **1 segment remplacé par une 1×4** a été **rejeté** : une autre brique `3003` du poteau béton occupait encore exactement le même volume. Le premier script a correctement retourné `B3_NO_SAFE_CONCRETE_TIMBER_COLUMN_BRIDGE`. Aucun compte rendu positif n'a été inventé. La version retenue remplace les **deux** segments coplanaires par une **seule 2×4**, puis vérifie 0 collision dans les voxels orthogonaux du modèle entier.

**Liaisons réellement vérifiées par les maillages LDraw officiels et connecteurs du moteur existant** :
- Partie supérieure du pont `3001` ↔ segment bois supérieur `3005` : **CONTACT**, **1 connecteur explicite**.
- Partie inférieure du pont `3001` ↔ segment du poteau béton `3003` : **CONTACT**, **4 connecteurs explicites**.
- Poteau béton restant : **8 raccords `3003`↔`3003`** jusqu'au segment bas à z=0 ; chaque raccord **CONTACT**, **4 connecteurs reconnus**.
- Ainsi **10 liaisons successives sur les 12** du chemin étudié sont reconnues et sans collision de maillage détectée **sur ces paires**. Le segment continu **pont → poteau béton → niveau inférieur z=0** est identifié et contrôlé. Le pied est un **niveau zéro du modèle**, **pas une fondation/baseplate LEGO certifiée**, et **pas une liaison au mur principal**.

**ÉCHEC EXPLICITE DU CRITÈRE DE CHAÎNE COMPLÈTE** :
1. `board:00001` (3007) ↔ dernier segment bois `3005` : moteur **COLLISION**, malgré **1 connecteur explicite**.
2. `3005` bois supérieur ↔ `3005` immédiatement inférieur : moteur **COLLISION**, malgré **1 connecteur explicite**.
3. Autre branche bois inférieure ↔ nouvelle `3001` : **COLLISION** signalée hors chemin principal.

Ce sont des **signaux de maillage** sur des interfaces de tenons LEGO usuels ; ils peuvent correspondre à la représentation des tenons s'insérant dans les cavités, **mais ce point n'a pas été prouvé**. **Ils ne sont pas requalifiés arbitrairement en CONTACT.** Les deux premiers raccords étant problématiques, **aucun chemin entièrement démontré depuis une planche jusqu'à la structure principale/fondations n'a été obtenu.**

Même sur les 10 raccords reconnus, les trajectoires d'insertion **CONTINUES** restent **NON DÉMONTRÉES**, tout comme la tenue physique. Le modèle entier n'a PAS subi 1,9k×1,9k vérifications de maillage ; zéro collision totale n'est pas revendiqué.

### Comparaison B-1 / B-2 / B-3 — métriques de PERIMÈTRE explicite

| Indicateur | B-1 | B-2 | **B-3** |
|---|---:|---:|---:|
| Pièces réelles LDraw de la maison entière | 1 901 | 1 905 | **1 904** |
| Variation par rapport au précédent | +11 vs canonique | +4/−0/0 déplacée | **+1/−2/0 déplacée** |
| Composantes plancher bois et réparations B-2 incluses | [29,1] | [34] | **[34]** (sans modification des 34) |
| Sans appui **immédiat orthogonal** reconnu (pas forcément flottantes) | 42 | 45 | **45** |
| Composantes **graphe de stud orthogonal global** | 26 | 26 | **26** |
| Collisions **voxels orthogonaux**, non maillage complet | 0 | 0 | **0** |
| Raccords officiels LDraw **positifs sur le chemin étudié** | non étudié dans B-1 | 2 couples plaques/planches + 3 connecteurs sur la 1re plaque | **10/12** (2 `COLLISION` non résolues) |
| Chemin bois→pont→poteau béton depuis planches **intégralement prouvé** | NON | NON | **NON** |
| Segment pont→poteau béton→base z=0 à raccords détectés | NON | NON | **OUI, ciblé, sans insertion continue** |
| Composantes **physiques certifiées** de toute la maison | INCONNU | INCONNU | **INCONNU** |
| Pentes `30363` à connexion/tenue non certifiée | 408 | 408 | **408** |
| Étapes de montage PROPOSÉES (jamais certifiées) | 271 | 272 | **272**, la `step-0157` remplace deux segments par le nouveau pont |

**Raccordement global du plancher au mur principal** : **NON DÉMONTRÉ**, le poteau béton est un élément porteur de la terrasse béton ; son pied à z=0 ne prouve pas qu'il est fixé aux fondations/au mur de la maison.

### B-3 livrée et visible, sans altérer B-2

Tous les fichiers sont dans **`missions/B3/generated/`**, conservés **durablement dans GitHub** :
- `GUIDED004-B3-1904.ldr` — **1 904 lignes LDraw** avec les pièces originales et le raccord de poteaux ;
- `B3-FULL-HOUSE-SCHEMATIC.svg` — maison complète (isométrie SCHÉMATIQUE, pas triangles des maillages LDraw) ;
- `B3-STRUCTURAL-LINK-ZOOM.svg` — zoom SCHEMATIQUE sur le pont orange `3001`, les poteaux bois bleus, la colonne béton verte et le plancher ;
- `BOM-B3.json` — nomenclature **1 904** : +1 `BRICK_2X4`, −1 `BRICK_1X1`, −1 `BRICK_2X2`, sans achat ;
- `ORDER-B3-PROPOSED.json` — **tous les 1 904 identifiants une fois dans 272 étapes**, insertion du pont à `step-0157` en lieu et place des deux segments originaux, ordre NON certifié ;
- `CHAIN-PROOF-LOCAL.json` — les **12 liaisons** et **2 collisions** détaillées, leur référence LDraw, les positions de connecteurs LDU, premiers obstacles et limites ;
- `B2-VS-B3.json` — changement exact, comptes, SHA256 B-2 inchangé, absence de certification.
- Script `scripts/build_guided004_support_b3.py` et tests `tests/bricks/test_guided004_support_b3.py` ; workflow dédié `.github/workflows/lego2-b3-support-chain.yml`.

### Tests, commandes, CI et sorties réelles

```bash
python -m pip install -e .
python -m pip install -e ./lego_geometry_engine
python -m pip install pytest
python -m pytest -q tests/bricks/test_guided004_support_b3.py
python scripts/download_ldraw_probe_066.py /tmp/b3-ldraw \
  --max-files 250 --parts 30363 3005 3003 3001 3007 3008 3623 3002 3622
python scripts/build_guided004_support_b3.py \
  --ldraw-root /tmp/b3-ldraw --output artifacts/lego2-b3
```

**[CI B-3 spécialisée SUCCESS — #40216339317](https://github.com/ludodulac/boldungo/actions/runs/40216339317)** sur HEAD code `a2034afda7c4691d2b09a8699e7370cc7f91edbe`. La CI exporte et vérifie B-1 puis B-2 en sorties isolées, produit le modèle B-3 et commite les artefacts durables dans **la seule branche DRAFT #931**. **[ZIP complet de la CI](https://github.com/ludodulac/boldungo/actions/runs/40216339317/artifacts/12608300406)**.

```text
4 passed in 1.03s
B3_CHAIN {"edges_positive_stud_cavity":10,"edges_total":12,
 "first_unproven_edge":0,"reaches_modeled_z0":true,
 "preexisting_stud_mating_mesh_collision_signals":[0,1],
 "new_bridge_connections_positive":true}
B3_HOUSE {"b2_parts":1905,"b3_parts":1904,
 "added_ids":["EXPERIMENT-B3-CONCRETE-TO-TIMBER-BRIDGE"],
 "removed_ids":["...timber-post-east:0027:00020",
                "...concrete-support-west:0027:00010"],
 "moved_ids":[],"b2_bytes_unchanged":true,
 "b2_orthogonal_unsupported":45,"b3_orthogonal_unsupported":45,
 "b2_orthogonal_components":26,"b3_orthogonal_components":26,
 "b2_orthogonal_collisions":0,"b3_orthogonal_collisions":0,
 "b2_roof_unverified":408,"b3_roof_unverified":408,
 "chain_established":false,"chain_to_primary_house":"NOT_PROVEN",
 "chain_to_z0":true,"local_bridge_to_concrete_support_verified":true,
 "old_mesh_collision_signals_unresolved":2}
B3_FULL_MODEL_1904_PIECES_PASS
B3_LOCAL_3001_TO_CONCRETE_3003_AND_CONCRETE_Z0_SEGMENT_VERIFIED_PASS
B3_FIRST_TWO_STANDARD_STUD_MATES_COLLISION_UNRESOLVED_NOT_CERTIFIED
```

L'assertion de **chaîne complète** a délibérément **ÉCHOUÉ** lors de la première tentative B-3, précisément sur les deux anciens `COLLISION`. Au lieu de les ignorer ou de mentir, l'acceptation du modèle expérimental final exige **l'absence de collision sur les nouvelles interfaces du pont et la présence des deux collisions antérieures documentées**. Le verdict *complet* demeure **NON DÉMONTRÉ** malgré la CI SUCCESS au périmètre réduit. Les CI générale et B-1/B-2 du **dernier HEAD de fichiers** sont à vérifier séparément : un ancien SUCCESS spécialisé ne s'étend pas automatiquement à tout nouveau HEAD.

## HYPOTHÈSE

La connexion pont `3001` → colonne béton `3003` a des tenons, cavités et positions géométriquement compatibles dans le moteur LDraw, et son trajet jusqu'au niveau inférieur du support est visible. C'est un rapprochement utile des terrasses bois/béton avec **une pièce de moins**.

Mais le fait que deux interfaces **courantes de tenons de briques** renvoient `COLLISION` illustre la limite du verdict brut du moteur : une analyse plus fine des volumes voulus d'emboîtement pourrait lever l'ambiguïté, pas une réécriture de la maison ni un nouveau toit. Cela reste une **hypothèse**, pas une correction validée.

Ni l'assise du support béton à une baseplate, ni le pont vers le mur principal, ni les 408 pièces de toiture, ni la stabilité globale, ni les trajectoires continues ne sont certifiés. La maison dispose donc d'une **chaîne locale reconnue depuis le pont vers le bas**, **pas d'une démonstration de construction de l'ensemble**.

## RECOMMANDATION — FIN FORMELLE DU CHANTIER B

### **CHANGER D'APPROCHE**

Trois missions B ont abouti à des fichiers tangibles B-1/B-2/B-3, mais **aucune** n'a démontré une maison entièrement assemblable. Les correctifs localisés ont une valeur réelle — raccord de planches, puis véritable pont 3001 entre poteaux — sans réduction des compteurs globaux (26 composantes orthogonales, 45 appuis non établis, 408 pentes sans preuve).

**La prochaine étape raisonnable n'est pas B-4, ni une nouvelle recherche de faîtage** : avant toute nouvelle construction, Grand-père et Ludo doivent décider de privilégier une **structure porteuse d'origine clairement assemblable et documentée**, avec interfaces de tenons acceptées par une validation LEGO ciblée, plutôt que d'accumuler des rustines sur un réseau de poteaux. Les invariants architecturaux de la Scene et les fichiers 1 890/1 901/1 905 doivent rester préservés.

**Notice finale : NON**. Les ordres proposés existent, mais il manque le raccord prouvé depuis le plancher, la fixation du support au mur/fondations, les insertions continues et la vérification de l'ensemble. La prochaine décision appartient à **Ludo**, après examen de **Grand-père**.

**Chantier B officiellement clos après B-1, B-2 et B-3. Pas de B-4, pas de nouvelle mission démarrée.**
