# 🧱 BOLDÜNGO — S-3 — premier petit étage LEGO (dernière mission du cycle)

## FAIT VÉRIFIÉ

**Un modèle expérimental unique de 47 vraies pièces LEGO est généré et conservé dans la PR #932 DRAFT.** Il part directement des **20 pièces S-1 inchangées** et ajoute 27 pièces : **20 briques 3003** (deux murs parallèles composés chacun de 5 briques sur 2 niveaux), **2 poutres 3006** porteuses et **5 plaques 3832** formant le plancher supérieur. **Aucune toiture, terrasse, cheminée ou donnée GUIDED-004** n'est concernée.

**Nomenclature totale :** 1×91405 (base), 32×3003 (poteaux + murs), 4×3006 (poutres), 10×3832 (deux planchers). 47 pièces, 47 lignes LDraw type 1.

**Documents permanents :** `missions/S3/generated/S3-PETIT-ETAGE-47-PIECES.ldr`, `S3-VUE-3D-SCHEMATIQUE.svg` (visualisation isométrique de volumes, **pas** vrai rendu maillage LDraw), `S3-NOMENCLATURE.json`, `S3-ORDRE-MONTAGE.json` (47 opérations proposées), `S3-CHEMINS-APPUI.json`, `S3-CONTROLES-CONNEXIONS.json`. Génération reproductible par `scripts/build_upper_floor_s3.py`. Anciens fichiers S-1 et S-2 strictement préservés.

**Nouveaux assemblages, audit exclusivement ciblé :** **40/40** nouvelles liaisons parent→enfant disposent de **4 positions de tenons communes** et sont reconnues par `find_connections` sur les pièces LDraw officielles. Un échantillon géométrique par type de raccordement (sur les **nouvelles** connexions seulement) donne :

| Type de liaison | Relation maillage représentative | Connecteurs moteurs |
|---|---|---|
| 3003 (mur) → 3832 (ancien plancher) | CONTACT | reconnus |
| 3003 (mur) → 3003 (empilement mur) | CONTACT | reconnus |
| 3006 (poutre supérieure) → 3003 (mur) | CONTACT | reconnus |
| 3832 (nouveau plancher) → 3006 (poutre supérieure) | **COLLISION brute** | reconnus |

La dernière alerte est **la même classe d'interface déjà étudiée et expliquée en S-2** : collision signalée par le repli `point_in_mesh` malgré des axes de tenons/cavités et une profondeur statique compatibles. Les **10 nouveaux** raccords supérieur 3832/3006 partagent le même placement relatif que les dix étudiés en S-2, mais leur balayage complet triangulé et leurs insertions continues **ne sont pas réexécutés ni prétendus démontrés**. `COLLISION` brute est conservée comme telle dans l'audit de S-3.

**0 superposition interdite des volumes orthogonaux de corps (AABB)** dans les 47 pièces. Ce contrôle **n'est pas** un audit exhaustif des véritables triangles pour toutes les paires : nombre de collisions maillage du modèle entier **INCONNU**.

**Chemins d'appui :** les cinq nouvelles plaques supérieures disposent chacune d'un chemin **nominal de dix pièces** jusqu'à la base 91405 : nouveau plancher → nouvelle poutre → 2 cours de mur → ancien plancher → ancienne poutre → 3 cours de poteau → base. Les 20 pièces S-1 déjà validées statiquement sont réutilisées **sans nouveaux diagnostics** et la preuve S-2 de leurs liaisons 3832/3006 est référencée. Tous les nouveaux raccords disposent d'alignements de connecteurs vérifiés au niveau statique, mais **les insertions continues, les répétitions des maillages et la résistance mécanique ne sont PAS certifiées**.

**Tests et commandes réelles :**
```bash
python -m pytest -q tests/bricks/test_first_storey_s3.py
python scripts/download_ldraw_probe_066.py /tmp/s3-ldraw --max-files 150 --parts 91405 3003 3006 3832
python scripts/build_upper_floor_s3.py --ldraw-root /tmp/s3-ldraw --output artifacts/s3-first-storey
```

**CI spécialisée sur le code S-3** : [#40356634931 — SUCCESS](https://github.com/ludodulac/boldungo/actions/runs/40356634931), commit `443363fa91f7be1c5561d72037d3447aaa8c81cb`. Sortie brute :

```text
7 passed in 0.06s
S3_MESH_REPRESENTATIVE 3003_TO_3832 CONTACT
S3_MESH_REPRESENTATIVE 3003_TO_3003 CONTACT
S3_MESH_REPRESENTATIVE 3006_TO_3003 CONTACT
S3_MESH_REPRESENTATIVE 3832_TO_3006 COLLISION
S3_SUMMARY {"total_pieces":47,"new_pieces":27,"new_support_edges":40,
 "new_edges_with_four_real_stud_centres":40,
 "new_edges_with_engine_recognized_connectors":40,
 "new_body_AABB_overlaps":0,
 "mesh_representative_classes":4,
 "mesh_representative_COLLISION_classes":1,
 "full_path_47_piece_continuous_insertions_proven":false,
 "physical_stability_certified":false}
S3_20_S1_ORIGINAL_PLACEMENTS_PRESERVED_PASS
S3_40_NEW_GENUINE_CONNECTOR_LOCATIONS_PASS
S3_5_UPPER_FLOOR_TO_BASE_NOMINAL_PATHS_PASS
```

Le **mauvais raccordement** testé (poutre décalée d'un tenon) est rejeté : 2 tenons au lieu de 4 ; mauvaise hauteur d'appui également rejetée. **CI S-2 du commit testé : SUCCESS.** CI S-1 et générale étaient encore `in_progress` au dernier pointage ; après archivage automatique des modèles le HEAD de la PR évolue vers un commit d'artefacts marqué `action_required` par GitHub (ni succès ni échec de tests exécutés). Ne pas inférer un CI vert non vérifié pour un HEAD différent.

## HYPOTHÈSE

**Oui : un premier étage LEGO est géométriquement cohérent au niveau des emplacements, des tenons et des chaînes de connexions statiques.** Les deux murs opposés reposent sur le premier plancher, portent les nouvelles poutres et un deuxième plancher complet ; le prototype conserve exactement l'ossature S-1. Cette architecture peut servir de motif pour des maisons de dimensions variées **après** adaptation explicite des longueurs/poteaux, sans prétendre que les autres dimensions sont déjà prises en charge.

L'alerte triangulée brute 3832/3006 reste déclarée ; S-2 fournit sa preuve d'une compatibilité **statique** (pas trajectoire ou charge). Les différences d'échelle et les stabilités latérales des deux murs parallèles restent à examiner avant une vraie maison.

## RECOMMANDATION

**CONSERVER ET CONTINUER CONDITIONNELLEMENT**, uniquement comme motif expérimental de deux murs porteurs et de plancher supérieur. Le résultat prioritaire est un **vrai LDraw visible de 47 pièces**, pas un diagnostic. **Ne pas déclarer constructibilité physique certifiée ni préparer une notice définitive.**

S-3 ferme le cycle S. **Aucune S-4 ni autre mission commencée**, PR #932 DRAFT non fusionnée, `main`, branche LEGO2 principale, GUIDED-004, S-1/S-2, PR #929/#930/#931 inchangés. Décision finale Grand-père et Ludo.
