# BOLDÜNGO — MISSION 025 — VÉRIFICATION MATÉRIELLE DU FAÎTAGE

**Verdict : C — INDÉTERMINÉ.** Une seule paire étudiée, aucune pièce déplacée, aucun moteur modifié.

## Sources et exécution

- Modèle de référence inchangé : `missions/B3/generated/GUIDED004-B3-1904.ldr` ; 1 904 pièces, dont 408 pentes `30363.dat`.
- Exécution **SUCCESS** du seul job ciblé M025 : https://github.com/ludodulac/boldungo/actions/runs/42688279915
- Bibliothèque authentique `pybricks/ldraw` épinglée à `c43ed06a128a10ed65675166bf42eb6fd608b9b0` ; **16 fichiers** téléchargés temporairement dans GitHub Actions, aucun ajouté au dépôt.
- Maillage de chaque `30363.dat` : **700 triangles**. Le suivi des sources produit également exactement **700 entrées**, alignées avec l'ordre du moteur.
- Paires : `roof-000185` (830, −960, 20) LDU, matrice `[0,0,1; 0,1,0; −1,0,0]` et `roof-000392` (790, −960, 20) LDU, matrice `[0,0,−1; 0,1,0; 1,0,0]`.

## 1. Provenance des quatre témoins M024 — vérifiée, pas présumée

Les **quatre croisements de triangles** (M024) ont été reproduits à l'identique avec `lego_geometry_engine.core._tri_intersection_kind` ; leur provenance a été retracée dans l'ordre d'aplatissement du moteur `LDrawLibrary`, sans nouveau moteur physique.

| Témoin | Face de `roof-000185` | Face de `roof-000392` |
|---|---|---|
| A#0 / B#601 | `p/4-4cyli.dat:18` | `p/box2-7.dat:19` |
| A#0 / B#698 | `p/4-4cyli.dat:18` | `parts/30363.dat:17` |
| A#1 / B#601 | `p/4-4cyli.dat:18` | `p/box2-7.dat:19` |
| A#2 / B#601 | `p/4-4cyli.dat:20` | `p/box2-7.dat:19` |

**Chaîne source de la première pente :** `parts/30363.dat:16` → `parts/s/30363s01.dat:18` → `p/stud4a.dat:21` → `p/4-4cyli.dat:18/20`. Il s'agit d'une **surface cylindrique de la primitive de tenon `stud4a`**, pas d'une preuve d'un choc entre deux masses pleines.

**Chaîne source de la deuxième pente :** `parts/30363.dat:16` → `parts/s/30363s01.dat:60` → `p/box2-7.dat:19` pour trois témoins ; le quatrième atteint directement le **quadrilatère principal de `parts/30363.dat:17`**.

**Nature observée :** au moins une surface de la primitive de tenon de la pente A est traversée par des triangles de la primitive `box2-7` ou de la face quadrilatérale de la pente B. Le fait que `box2-7` représente une boîte dans les fichiers LDraw **ne prouve pas**, à lui seul, une pénétration interdite de deux *corps rigides* complets. Les tenons, vides, tolérances d'emboîtement et faces physiques ne sont pas documentés de manière suffisante pour statuer sur le joint.

## 2. Contrôle volumique 080 — réellement exécuté

Réutilisation **sans aucune modification** de `backend/brickhouse/bricks/ridge_material_volume_080.py` :
`inspect_solid_shell`, `inspect_shared_interior`, `decide_physical_interference`.

| Propriété | Pente A | Pente B |
|---|---:|---:|
| Triangles | 700 | 700 |
| Arêtes uniques | 1 146 | 1 146 |
| **Arêtes de bord ouvertes** | **192** | **192** |
| Arêtes non-manifold | 0 | 0 |
| **Arêtes à orientations incohérentes** | **76** | **76** |
| Faces dégénérées | 0 | 0 |
| `watertight_oriented_shell_gate` | **UNKNOWN** | **UNKNOWN** |

- `inspect_shared_interior` : `UNKNOWN_UNCLOSED_OR_UNORIENTED_LDRAW_SURFACE`.
- Échantillons intérieurs testés : **0**. **Aucun témoin fiable de volume matériel partagé** ne pouvait être tiré d'un maillage qui ne satisfait pas le contrôle de fermeture et d'orientation.
- `decide_physical_interference` : `UNKNOWN` / `OPEN_LDRAW_SHELL_PREVENTS_MATERIAL_OCCUPANCY_PROOF`.
- Connecteurs `30363` reconnus entre les deux pièces : **0**. Cela ne prouve ni absence de connexion réelle ni emboîtement admissible.

**Important :** une intersection de surfaces est avérée, mais sa qualification comme *interférence matérielle interdite* est **NON DÉMONTRÉE**. Un verdict B (emboîtement admissible) serait tout aussi injustifié.

## 3. Les 23 jonctions répétées

L'inspection des **408 enregistrements de pentes dans le fichier B3** a retrouvé **23 paires** avec exactement :
- l'écart de translation **(−40, 0, 0) LDU** ;
- la même matrice `[0,0,1; 0,1,0; −1,0,0]` pour la première pente ;
- la même matrice opposée `[0,0,−1; 0,1,0; 1,0,0]` pour la deuxième.

Les **23 transformations relatives sont identiques**, et pas seulement leur distance. Cette identité ne constitue **pas** une preuve de connexion, insertion ou stabilité ; seule la paire `roof-000185 / roof-000392` a été analysée volumiquement ici.

## 4. Décision et correction de principe

**C — INDÉTERMINÉ.** Les croisements concernent notamment une surface de tenon, une primitive de boîte et une face externe de pente. Le contrôle 080 refuse à juste titre de traiter les maillages LDraw incomplets/incohérents comme des volumes de matière fermés.

**Aucune correction du faîtage n'est justifiable à ce stade :** ne déplacer ni supprimer aucune pente. Une décision sur la constructibilité demanderait une géométrie de matière fermée et fiable, l'identification des zones tenon/logement et des tolérances d'ajustement, puis un contrôle de la trajectoire d'insertion et de la stabilité.

### Preuve numérique intégrale

Artefact GitHub Actions `BOLDUNGO-M025-FAITAGE-MATERIAL-PROOF-NOT-CERTIFIED` sur https://github.com/ludodulac/boldungo/actions/runs/42688279915, contenant `PREUVES-FAITAGE-M025.json` (**4 témoins complets**, chaînes source et données des surfaces 3D, métriques 080, **23 paires et matrices**), ainsi que le rapport Markdown émis automatiquement.

**Aucun modèle, aucune pièce LEGO, aucune pente, aucun mur, aucun pignon, aucune photographie, aucune règle physique et aucun site public modifiés.**
