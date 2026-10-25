# BOLDÜNGO — S-1 — ossature LEGO porteuse expérimentale (mission close)

**UNE construction, pas une maison ni un nouveau toit : 20 véritables pièces LEGO**, versionnées sur la branche expérimentale et PR #932 DRAFT. `main`, LEGO2, GUIDED-004 canonique, PR #929/#930/#931 et tous les prototypes A/R/B intacts ; aucune fusion.

## FAIT VÉRIFIÉ

**Notice officielle UNIQUE** : LEGO Creator **31009 Small Cottage**, Booklet 1, `6038244.pdf`, https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf . Pages imprimées étudiées avec leurs dessins : **5, étape 2** (base et premiers éléments), **14, étape 9** (briques de murs sur tenons), **25, étape 19** (empilement structurel), **43–44, étapes 33–34** (longues pièces horizontales de couronnement sur murs).

**Distinction décisive :** l'ossature S-1 s'**inspire** de cette méthode. La notice NE décrit PAS exactement notre module : l'original emploie une baseplate **3811 (32×32)**, tandis que **S-1 choisit une vraie plaque officielle `91405` (16×16)**. Les quatre piles `3003`, les deux poutres `3006` et les cinq plaques de plancher `3832` sont **des placements EXPÉRIMENTAUX**, pas des pas officiels de 31009. Ce principe de poutre/plancher n'est pas revendiqué comme montage officiel documenté à ces pages.

### Modèle réel et nomenclature

| Rôle | LDraw | Quantité |
|---|---|---:|
| Base LEGO 16×16 | `91405.dat` | 1 |
| Quatre colonnes, trois cours chacune | `3003.dat` (brick 2×2) | 12 |
| Deux poutres traversantes 2×10 | `3006.dat` | 2 |
| Cinq plaques de plancher 2×10 | `3832.dat` | 5 |
| **Total** | | **20** |

**Montage proposé** : (1) poser base ; (2) monter 4 poteaux, cours 1 ; (3) cours 2 et cours 3 ; (4) placer deux traverses 3006, chaque poutre portant sur deux poteaux ; (5) poser les cinq plaques 3832 sur les deux traverses. Fichier `MONTAGE.json` : les 20 pièces ordonnées individuellement, direction verticale uniquement **PROPOSÉE**. Pas d'insertion continue démontrée.

**Schéma d'appui** (graphe d'emboîtement, valable pour chacune des cinq plaques) :

```text
3832   3832   3832   3832   3832     PLANCHER
  \      |      |      |      /
     3006               3006         DEUX POUTRES
      /  \               /  \
    3003  3003         3003  3003     QUATRE COLONNES (3 cours chacune)
      |      |           |      |
  ================ 91405 ============ BASE LEGO
```

Les routes exactes de toutes les plaques à la base sont dans `CHEMIN-D-APPUI.json`. **Le graphe nominal compte 20 pièces en une composante et 26 liens d'appui parent→enfant** : 4 base→poteaux, 8 superpositions 3003, 4 poteaux→poutres et 10 poutres→planches. Chacun présente précisément quatre positions de tenon communes ; **0 mauvais alignement nominal**. Le test négatif décale volontairement une poutre d'un tenon : seuls deux plots coïncident, raccord **REJETÉ**. Un niveau vertical invalide est également rejeté.

### Vraies connexions / vrais maillages LDraw (version épinglée)

L'outil `lego_geometry_engine` existant a chargé les vrais DAT officiels depuis le miroir épinglé `pybricks/ldraw@c43ed06a128a10ed65675166bf42eb6fd608b9b0`. Les **26 couples** ont été soumis au calcul de **connecteurs** (positions tenons / anti-studs réels inférées par le moteur depuis le DAT), sans exception. **26/26** possèdent au moins un ensemble compatible de connecteurs à la position finale.

Les maillages complets ont été comparés **sur un représentant de chacune des quatre classes d'interface seulement** :

| Interface de pièces | Maillage testé | Connecteurs explicites |
|---|---|---|
| `3003 → 91405` poteau sur base | **CONTACT** | 4 |
| `3003 → 3003` cours empilés | **CONTACT** | 4 |
| `3006 → 3003` poutre sur poteau | **CONTACT** | 4 |
| `3832 → 3006` plancher sur poutre | **COLLISION** | alignement des quatre plots reconnu |

**Ne pas requalifier automatiquement la COLLISION** de la dernière interface en CONTACT, même si une plaque LEGO et une brique 2×10 sont usuellement combinables. Les détails des triangles intriqués, cavités et tolérances de l'emboîtement ne sont **pas démontrés** avec l'audit borné ; cet indicateur peut provenir d'un emboîtement normal ou d'une interférence réelle. Il est donc **INDETERMINE**, non pas « physiquement impossible », et non pas « validé ».

**Statuts clairement différenciés** :
- **26/26** : coïncidence exacte de centres et connecteurs reconnus par le moteur LDraw (ce n'est pas une preuve physique) ;
- **3/4 classes** : vrais maillages représentatifs en `CONTACT` et connecteurs reconnus ; les répétitions n'ont **pas été** auditées individuellement ;
- **1/4 classe**, qui correspond à **10 interfaces nominales** de poutre/plancher : collision triangulée en exemple → **NON DÉMONTRÉES** ;
- **16/26 liens** ont un alignement de connecteurs et une classe échantillonnée en CONTACT, **pas 16 validations individuelles complètes** ;
- **0/5 chemins complets** sont prouvés jusqu'à la base au sens rigoureux retenu : chaque plaque passe par au moins une interface `3832/3006` non levée ;
- composante connexe physique validée, profondeur de maintien dans les tubes, insertions continues et résistance mécanique : **NON DÉMONTRÉES** ;
- collision **observée : 1 classe sur 4 représentatives** ; nombre de collisions sur l'ensemble du module : **INCONNU**, examen exhaustif non réalisé.

LDraw entier `missions/S1/generated/S1-OSSATURE.ldr`. Vue isométrique `OSSATURE-VUE-3D-SCHEMATIQUE.svg` **SCHÉMATIQUE**, pas rendu des triangles réels. Nomenclature `NOMENCLATURE.json`, ordre `MONTAGE.json`, graphe `CHEMIN-D-APPUI.json`, preuves pour **chaque lien** `PREUVES-GEOMETRIE.json`, source `PROVENANCE.json`. Ces sept fichiers sont **durablement commités dans la branche DRAFT** ; ils ne dépendent pas d'un ZIP temporaire.

### Tests et commandes réellement exécutés

```bash
python -m pip install pytest
python -m pip install -e ./lego_geometry_engine
python -m pytest -q tests/bricks/test_documented_frame_s1.py
python scripts/download_ldraw_probe_066.py /tmp/s1-official --max-files 200 --parts 91405 3003 3006 3832
python scripts/build_documented_frame_s1.py --ldraw-root /tmp/s1-official --output artifacts/s1-frame
```

**CI spécialisée sur commit source `77c2180ee90c68b4dc0b1ae20d6f456d3793bf79`** : [GitHub Actions #40229131927 — SUCCESS](https://github.com/ludodulac/boldungo/actions/runs/40229131927). Log brut :

```text
10 passed in 0.11s
S1_MESH_MATE 3003_to_91405 CONTACT
S1_MESH_MATE 3003_to_3003 CONTACT
S1_MESH_MATE 3006_to_3003 CONTACT
S1_MESH_MATE 3832_to_3006 COLLISION
S1_SUMMARY {"pieces":20,"edges_planned":26,"nominal_wrong_pairs":0,
  "connector_aligned_edges":26,"sampled_mesh_class_count":4,
  "connector_plus_sample_contact_edges":16,
  "not_confirmed_under_bounded_rule":10,
  "sampled_mesh_collision_classes":["3832_to_3006"],
  "entire_chain_of_mesh_contact_verified":false,
  "insertion_proven":false,"strength_certified":false}
S1_20_GENUINE_OFFICIAL_LDRAW_PARTS_AND_BOM_PASS
S1_26_EXACT_NOMINAL_FOUR_STUD_ALIGNMENTS_PASS
S1_ALL_FIVE_FLOOR_TO_BASE_GRAPH_PATHS_PASS
S1_NOT_A_CERTIFICATION_PASS
```

Le premier run #40228902453 a échoué sur un **terminateur JSON `\\n` encodé littéralement**, corrigé sans changer aucune des 20 pièces ; les sorties réelles et les 10 tests ont alors réussi. Le workflow sur un nouveau commit de rapport ne remplace pas automatiquement la preuve du commit source validé : vérifier ses CI séparément.

## HYPOTHÈSE

Le schéma base 91405 → poteaux 3003 → poutres 3006 est reproductible et prometteur ; son motif se répète sans aucune dimension propre à la maison de Ludo. **Mais le raccord de plancher `3832/3006` doit rester NON DÉMONTRÉ**, faute d'une classification sûre de la collision interne au couple. Les autres classes n'ont été examinées aux maillages que sur un représentant, donc aucune certification de toute la construction.

La notice de 31009 apporte un précédent réel au **principe base/murs empilés/couronnement**, pas au plancher S-1 lui-même. Ni une vérification statique ni ce précédent ne démontrent la résistance ou la construction de S-1.

## RECOMMANDATION — ARRÊT S-1, décision Grand-père / Ludo

**CONSERVER L'OSSATURE comme EXPÉRIENCE CONTRÔLÉE, mais NE PAS prétendre le principe validé entièrement.** Nous avons 20 vraies pièces, un modèle visible, le graphe et les connecteurs vérifiés, et une **seule classe bloquante** précisément identifiée au plancher ; nous n'avons pas une chaîne complète certifiée et aucune notice fiable n'est justifiée.

Recommandation principale : **poursuivre CONDITIONNELLEMENT l'idée d'une ossature LEGO standard**, mais ne rien généraliser à GUIDED-004 avant qu'une interface plancher/poutre et les insertions pertinentes soient réellement démontrées. Une approche fondée sur des sous-ensembles officiels de plancher réellement documentés serait préférable à des réparations successives.

**Aucune S-2 commencée.** Décision finale à Grand-père et Ludo ; préserver tous les travaux antérieurs sans fusion.
