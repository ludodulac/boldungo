# 🧱 BOLDÜNGO — CHANTIER R-3, BILAN FINAL R-1 / R-2 / R-3

**Décision proposée à Grand-père/Ludo : CONTINUER LA RECETTE COMME MODULE EXPÉRIMENTAL ISOLÉ, NE PAS L'INTÉGRER EN PRODUCTION AVANT LEVÉE DES BLOQUANTS.** Le chantier R-1/R-2/R-3 est désormais terminé : aucune R-4, aucune B, aucune modification GUIDED-004, main, LEGO2 ou PR #929.

## FAIT VÉRIFIÉ — deux sorties concrètes, un seul générateur

Programme : `scripts/generate_roof_recipe_r3.py`, fonction `recipe(width_studs, length_studs, pitch_degrees, overhang_studs)` et CLI `export`.

**Périmètre explicite :** largeur **8 tenons seulement** ; longueurs multiples de 8, comprises entre **8 et 32 tenons** ; pente **45°** seulement ; débord **0 tenon** seulement. Toute largeur, longueur, pente ou débord non compatible lève `ValueError` (tests dédiés). Aucun paramètre de GUIDED-004, aucune cote de la maison réelle.

| | Prototype 1 | Prototype 2 |
|---|---:|---:|
| Dimensions demandées (tenons) | **8 × 8** | **8 × 16** |
| Total pièces | **22** | **46** |
| Pièces de toiture (4445 + 3022) | **8** | **16** |
| Pentes 4445 45° | 4 | 8 |
| Faîtages 3022 (adaptation) | 4 | 8 |
| Supports 3001 2×4 | 12 | 24 |
| Plaques transversales 3832 | 2 | 4 |
| Plaques de jonction 3023 (adaptation entre modules) | 0 | 2 |
| Composantes **NOMINALES** du graphe | **1** | **1** |
| Liens parent→enfant **NOMINAUX** | **28** | **60** |
| Pièces sans parent nominal injustifié | **0** | **0** |
| Chaînes jusqu'à une baseplate/maison réelle certifiées | **NON** | **NON** |
| Insertions continues certifiées | **NON** | **NON** |
| Résistance mécanique physique certifiée | **NON** | **NON** |

**Livrables immuables sur la branche expérimentale** (`missions/R3/`) :

- `roof-8x8/ROOF-R3.ldr` et `roof-8x16/ROOF-R3.ldr` — véritables placements LDraw, 22 et 46 pièces ;
- chaque sous-dossier : `BOM.json`, `ORDER.json`, `EVIDENCE.json`, `ISOMETRIC-SCHEMATIC.svg` ;
- vues SVG **isométriques simplifiées**, **PAS** un rendu exact des triangles officiels ; fichiers LDraw pour la vraie géométrie ;
- `scripts/render_roof_r3_preview.py` — production déterministe des deux aperçus ;
- `scripts/audit_roof_recipe_r3.py` — vérifications mesurées des catégories distinctes de raccords via le moteur LDraw existant, et voisinages de pentes ; les répétitions sont comptées sans être prétendues toutes auditées ;
- `tests/bricks/test_generic_roof_r3.py` — valeurs acceptées/refusées, un seul composant nominal, deux tailles, exactitude des exports, et cas négatif avec pente décalée d'un tenon.

### Petit motif et lien exact à la notice

Notice LEGO **31009**, livret 1, `6038244.pdf`, pages imprimées 47–68 ; coordonnées numériques étudiées dans R-2 issues du CAD communautaire LTRON, **pas officiel**.

Les références choisies existent dans la séquence originale : `3832` support (étape 2/page 47), `4445` pentes longues (étapes 4,10,13,18,23), `3001` briques structurelles (étape 12/page 54), `3023` plaque (étape 6/page 50), `3022` plaque (étape 24/page 66, **dans la cheminée d'origine**).

**AUCUN assemblage R-3 ne doit être qualifié de sous-ensemble identique à la notice officielle.** La position, les deux lits de briques `3001`, la jonction entre modules et le faîtage `3022` sont de nouvelles **ADAPTATIONS R-3**. Le `3022` est ici utilisé comme faîtage bien qu'il servît à la cheminée dans R-2. R-1 avait déjà testé cette forme de faîtage sur des pentes 4445 ; ce choix est motivé par la collision avec le candidat `3023` de la première itération R-3 et NON par une fausse attribution à LEGO.

### Évolution guidée par la réalité de la géométrie

La première itération R-3 utilisait 8 plaques `3023` pour la crête d'un module de 8 tenons, et un pont `3832` enterré. L'audit réel a renvoyé :
- **8 `COLLISION` au faîtage** sur 8×8 (entre `3023` et le pan droit `4445`) ;
- **9 `COLLISION` sur 8×16**, dont l'assemblage de pont `3832`.

Les journaux **ne masquent pas** ces collisions en `CONTACT`. Le modèle de sortie définitif est corrigé : une plaque `3022` sur deux rangs longitudinaux pour la crête, et deux petites plaques `3023` à l'extérieur des appuis pour la liaison entre modules. Les 22/46 pièces produites sont cette **deuxième itération**. Leur nombre de collisions du dernier audit doit être confirmé dans la CI correspondante ; aucune preuve intégrale ne peut être annoncée par anticipation.

### Commandes de reconstruction

```bash
python -m pytest -q tests/bricks/test_generic_roof_r3.py

python scripts/generate_roof_recipe_r3.py --width-studs 8 --length-studs 8 --pitch-degrees 45 --overhang-studs 0 --output artifacts/lego2-r3/roof-8x8
python scripts/generate_roof_recipe_r3.py --width-studs 8 --length-studs 16 --pitch-degrees 45 --overhang-studs 0 --output artifacts/lego2-r3/roof-8x16

python scripts/render_roof_r3_preview.py --width-studs 8 --length-studs 8 --output artifacts/lego2-r3/roof-8x8/ISOMETRIC-SCHEMATIC.svg
python scripts/render_roof_r3_preview.py --width-studs 8 --length-studs 16 --output artifacts/lego2-r3/roof-8x16/ISOMETRIC-SCHEMATIC.svg

python scripts/download_ldraw_probe_066.py /tmp/lego2-r3-ldraw --max-files 240 --parts 4445 3001 3832 3023 3022
python scripts/audit_roof_recipe_r3.py --ldraw-root /tmp/lego2-r3-ldraw --length-studs 8 --output artifacts/lego2-r3/roof-8x8/GEOMETRY.json
python scripts/audit_roof_recipe_r3.py --ldraw-root /tmp/lego2-r3-ldraw --length-studs 16 --output artifacts/lego2-r3/roof-8x16/GEOMETRY.json
```

Les vérifications GitHub Actions en CI spécialisée `LEGO2 R-3 generic 45deg roof two real models` conservent les journaux de vérification des vrais maillages et l'artefact des deux constructions. La **CI générale** doit être rapportée séparément et un `SUCCESS` antérieur n'est jamais imputé au nouveau HEAD sans confirmation.

## HYPOTHÈSE — comparaison des méthodes

| Critère | A (24 pièces de test) | R-1 (41 pièces) | R-2 (80 pièces) | R-3 (22 / 46 pièces) |
|---|---|---|---|---|
| Pente | brique 30363 ~18°, progression globale ~21,8° | 45° | 45° | 45° |
| Principe | rangs 30363, piliers indépendants, faîtage 3022 | 4445, pannes 3007, piliers 3003, 3022 | authentiques rangs/supports du LEGO 31009, avec lucarne et cheminée | 3832 transversal, 3001 empilées, 4445, faîtage 3022, jonction 3023 |
| Appuis statiques démontrés | 23/23 au micro-module A-3 | 8/8 pièces toiture statiquement contrôlées | 0 support complet démontré par nos validateurs | géométries LDraw **partielles**, voir audit spécialisé du HEAD |
| Appuis nominaux sans chemin | 0 | 0 | non établi en 3D sur toutes pièces | 0 / 0 dans les graphes |
| Connexions non démontrées | cinq insertions continues de toiture | chaînes vers baseplate non certifiées | très nombreuses, non exhaustivement auditées | aucune chaîne physique entière ni insertion certifiée |
| Paramétrable | sur modèle A expérimental | longueur 8/16 déjà possible mais support inventé | NON : 80 pièces figées | **OUI** : largeur 8 fixée, longueur 8..32 par pas 8 |
| Proximité à la notice LEGO | aucune | palette et principe 45° inspirés | **maximum pour la séquence documentée**, CAD communautaire | pièces/motif empruntés, **placements nouveaux** |
| Limite bloquante | insertion des 5 toitures non démontrée | structure spécifique, 45° | structure compliquée, pas de recette dimensionnelle | portée fixée à 8, 22° interdit, jonction/insertion réelle à valider |

Le vrai principe LEGO 31009 sert d'autorité **sur les pièces et les séquences de son propre set**, mais une adaptation paramétrique ne peut pas hériter automatiquement de sa constructibilité. Le meilleur **point de départ logiciel** à 45° est donc R-3 (recette paramétrique avec validation stricte des valeurs), **et pas** R-2 (historique de fidélité), ni A (seule famille proche des ~22° du bâtiment cible). Ceci n'est **pas** une validation du montage complet R-3.

## RECOMMANDATION — FIN DU CHANTIER R, décision proposée

**CONTINUER uniquement comme proposition de composant de générateur EXPÉRIMENTAL** : préserver les deux modèles et la recette sur PR #930 **DRAFT**, sans fusion, et ne pas l'utiliser sur les maisons GUIDED tant que les connexions structurales, l'absence de collision sur l'ensemble et les trajectoires nécessaires ne sont pas prouvées.

Priorité réelle prochaine : unifier la couche de validateur/contrat constructible entre ce candidat 45° et les besoins réels de GUIDED-004 **sans changer ses vérités architecturales** ; avant intégration, résoudre toute collision révélée dans les deux modèles. **La maison GUIDED-004 reste proche de 22°, donc cette recette 45° est inapplicable telle quelle.**

Aucune mission R-4, aucune mission B engagée. Décision d'intégration : Grand-père et Ludo seulement.

## Protections

Branche expérimentale `feat/lego2-r1-official-31009-roof` / PR #930 **DRAFT**. `main`, branche LEGO2 principale, 1 890 pièces GUIDED-004, PR #929 et anciens fichiers R-1/R-2 intacts. Pas de fusion, pas de dépense, aucun essai physique demandé à Ludo.
