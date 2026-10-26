# 🧱 BOLDÜNGO — S-2 — UNE interface, UN verdict, aucun modèle modifié

**Mission S-2 close.** Vérification ciblée de **`3832.dat` (plaque de plancher) ↔ `3006.dat` (poutre)** sur S-1. Ossature de **20 pièces conservée exactement**, sans aucun changement de pièce, orientation ou règle globale du moteur, sans seconde architecture ni S-3.

## FAIT VÉRIFIÉ

### Verdict de l'interface : **COMPATIBLE à la position statique des véritables connecteurs LEGO**

**Pourquoi le détecteur indiquait COLLISION :** sa fonction `check_collision` enchaîne (1) les intersections réelles de triangles puis (2) un test de `_point_in_mesh` par **parité d'un rayon sur une surface LDraw comportant des cavités et sous-primitives ouvertes**. Pour la paire S-1 **aucun croisement intérieur de triangles** n'a été découvert malgré l'analyse de tous leurs triangles ; cependant le point témoin de la plaque a été classé « intérieur de la poutre » par le repli `_point_in_mesh`. Les deux boîtes englobantes complètes ne sont pas contenues l'une dans l'autre. **L'unique `COLLISION` signalée provient ici du repli de parité des rayons, et non d'un croisement démontré de matières.**

Les données réelles des sous-pièces officielles LDraw :
- `3832.dat` : `20` tenons supérieurs (`stud.dat`) et **9 tubes ouverts inférieurs `stud4.dat`** ; 2 × 10 en coordonnées locales LDraw, axe long X ; orientation 90° sur S-1 ;
- `3006.dat` : `20` tenons supérieurs `stud.dat`, 2 × 10, axe long X ;
- sur la paire représentative, **4 vrais axes de tenons** correspondent à 4 cavités du dessous, pas seulement à quatre connecteurs inférés d'une description ;
- la poutre est en appui sous la plaque sur le plan **Y = −96 LDU** ; sommet du tenon **Y = −100** et plafond de cavité de la plaque **Y = −100** ; **engagement nominal de 4 LDU** ;
- rayons officiels : tenon **6 LDU**, tube inférieur extérieur **8 LDU**, écart diagonal des axes **√200 = 14,1421356 LDU** ; donc **jeu radial idéal ≈ +0,142136 LDU**, strictement positif pour la configuration étudiée.

**IMPORTANT :** la petite marge est issue de **géométrie idéalisée LDraw**, pas d'une tolérance mécanique ou d'une garantie de tenue. La conclusion **COMPATIBLE** concerne le positionnement et l'emboîtement statique de cette interface, pas le modèle entier ou la force d'adhérence.

### Contrôle négatif : une vraie interférence est bien détectée

Une configuration **volontairement fausse** abaisse la plaque de **4 LDU**, de sorte que les matières du plateau et de la poutre se pénètrent. Le moteur retourne également `COLLISION`, **mais cette fois son propre détecteur trouve un vrai croisement intérieur de triangles**, indices **[866,885]**, avec leurs coordonnées enregistrées dans `PAIR-3832-3006-PROOFS.json`. L'examen ne classe donc **pas toutes les collisions comme licites** ; rien n'a été ajouté au moteur pour masquer le cas négatif.

### Les DIX interfaces de l'ossature S-1 ont été réexaminées

Chaque plaque de plancher 3832 touche les **deux** poutres 3006, soit **5 × 2 = 10** raccordements. Le code S-2 lit de nouveau les positions des véritables `stud.dat`/`stud4.dat` officiels et calcule la coïncidence d'axes, le plan et le jeu de chaque paire :

| Mesure / portée | Résultat |
|---|---:|
| Interfaces de plancher / poutre examinées sur vraies positions officielles de tenons et tubes | **10 / 10** |
| Interfaces possédant 4 axes de tenons correctement alignés | **10 / 10** |
| Interfaces avec profondeur nominale 4 LDU et jeu tube/tenon positif | **10 / 10** |
| Paire représentative scrutée exhaustivement triangle par triangle | **1 / 10** |
| Vraies interférences entre matières découvertes sur la paire représentative S-1 | **0** |
| Test volontairement incompatible avec croisement réel de triangles | **1 (rejeté)** |
| Modifications apportées aux 20 pièces de S-1 | **0** |
| Changement global du détecteur de collision | **0** |

Les **neuf autres paires** ont été examinées par les **connecteurs réels et calculs locaux des corps**, **pas** par une recherche exhaustive de chaque triangle. Elles ne doivent pas être présentées comme neuf audits triangulés complets.

### Chaîne plancher → base

- S-1 demeure une structure **20 pièces, 26 liaisons nominales, 5 chemins nominaux** vers la base.
- Les **16 autres liaisons** (poteau-base, poteau-poteau et poutre-poteau) avaient des connecteurs reconnus par le moteur, avec **trois types représentatifs en CONTACT** ; toutes leurs répétitions n'avaient **pas** été auditées exhaustivement au maillage.
- Les **10 liaisons plancher-poutre** sont maintenant **compatibles par lecture des vrais axes/cavités de la géométrie LDraw**. La collision apparente de leur classe est expliquée.
- **Les 26 interfaces n'ont toujours pas reçu chacune un contrôle exhaustif de tous les triangles ni une preuve d'insertion continue.** Nous pouvons donc décrire une **chaîne statique de connecteurs compatibles à chaque étage**, mais pas certifier toute l'ossature « assemblable » au sens de trajectoire continue et solidité démontrée.

### Commandes et CI exactes

```bash
python -m pip install -e ./lego_geometry_engine
python -m pip install pytest
python -m pytest -q tests/bricks/test_probe_s2_floor_beam.py
python scripts/download_ldraw_probe_066.py /tmp/s2-official --max-files 100 --parts 3832 3006
python scripts/probe_s2_floor_beam.py --ldraw-root /tmp/s2-official --output artifacts/s2/S2-PAIR-3832-3006.json
```

**CI spécialisée S-2 #40341882555 : SUCCESS**, commit code `08138415130bea26029bcbdf10b714ca239d40cf`, tests **4 passed in 0.12s**. [Journaux et artifact source réel](https://github.com/ludodulac/boldungo/actions/runs/40341882555), [ZIP preuve primaire](https://github.com/ludodulac/boldungo/actions/runs/40341882555/artifacts/12660365222). Les premiers runs de travail S-2 ont pu échouer à cause de tests restés attachés au verdict provisoire `NON_RESOLU`; **ne pas les appeler SUCCESS**.

```text
4 passed in 0.12s
S2_RAW:
 mesh_relation_at_S1_position: COLLISION
 original_mesh_collision_comes_from_containment_fallback_not_triangle_crossing: true
 original_mesh_inside_ray_vertex_plate_to_beam: true
 actual_horizontal_stud_to_cavity_axis_matches: 4
 nominal_stud_insertion_depth_LDU: 4.0
 min_tube_stud_radial_clearance_LDU: 0.142135623730951
 negative_wrong_depth_has_actual_triangles_crossing: true
 all_ten_actual_stud_cavity_alignments_compatible: true
 bounded_static_geometric_verdict: COMPATIBLE
S2_WITNESS:
 triangle_intersection_found: false
 checked_overlap_pairs: 1058
S2_BAD_WITNESS:
 collision_type: NON_COPLANAR_TRIANGLE_INTERSECTION
 first_triangle_indices: [866,885]
S2_ONE_REAL_MESH_PAIR_AND_NEGATIVE_CASE_DOCUMENTED
```

Le **modèle S-1 original, son LDraw, ses dix tests S-1, son BOM et son aperçu restent intégralement inchangés**, PR #932 demeure DRAFT. Pour la CI générale du **commit final de documentation**, rapporter son état réellement consulté ; ne pas déduire `SUCCESS` d'un run antérieur.

## HYPOTHÈSE

La méthode standard base → poteaux → poutres → plancher est suffisamment cohérente au niveau des connecteurs géométriques statiques pour mériter d'être **retenue comme prototype isolé**, et l'alerte précédente de maillage S-1 n'est **pas** la preuve d'une incompatibilité réelle entre une plaque 3832 et une brique 3006. Ce motif est réutilisable en dimensions adaptées ; la **résistance réelle des 20 pièces**, les tolérances de friction, les contraintes d'échelle et la possibilité de chaque mouvement d'insertion ne sont toujours pas démontrées.

## RECOMMANDATION — ARRÊT S-2

**CONSERVER S-1 SANS CORRECTION MATÉRIELLE.** Le cas de la plaque et de la poutre possède une explication triangulée localisée et un test négatif qui empêche de blanchir toute collision. Aucune modification des règles générales du détecteur n'a été nécessaire.

**Réponse explicite :** nous avons une **chaîne statique de connecteurs géométriquement compatibles** depuis les cinq plaques vers la base, sur les interfaces représentatives et dix raccords recontrôlés sur vrais axes. Nous ne disposons **pas d'une certification exhaustive de l'assemblage entier** (maillages des répétitions, mouvements continus, résistance). Une notice finale, une commande de pièces ou une intégration à GUIDED-004 serait donc prématurée.

**AUCUNE mission S-3 commencée.** Grand-père et Ludo choisissent la suite.
