# 🧱 BOLDÜNGO — MISSION B-2 — RACCORDER DES ÉLÉMENTS DE GUIDED-004

**Mission 2/3 du chantier B. B-2 terminée ; B-3 NON commencée.**
Branche **`feat/lego2-b1-guided004-full-house-experiment`**, PR [#931](https://github.com/ludodulac/boldungo/pull/931) **DRAFT**. **Aucune fusion, ni changement de `main`, LEGO2, GUIDED-004 canonique 1 890, Scene, PR #929/#930 ou source B-1 1 901.**

## FAIT VÉRIFIÉ — maison B-2 intégralement générée, quatre pièces réellement ajoutées

B-1 a été régénérée dans un dossier ISOLÉ par le script B-1 existant, sans modifier ses fichiers originaux ; ses 1 901 placements ont ensuite été recopiés **à l'identique**. Un raccordement de terrasse déjà exploré expérimentalement dans l'ancien **059M** est désormais intégré à **UNE MAISON COMPLÈTE DE 1 905 PIÈCES**, suivant une recette qui **lit les dimensions et emprises dans le modèle**, et rejette la topologie incompatible. Ni le toit, ni les deux cheminées, ni les murs n'ont été déplacés.

### Construction concrète

Les 30 planches/pièces de plancher du module de terrasse en bois formaient auparavant des composantes de **[29, 1]** : la planche **`scene-platform:south-timber-deck-main:board:00033`** était isolée dans ce sous-assemblage (bien qu'elle puisse toucher d'autres pièces hors de celui-ci).

Les nouvelles pièces sont :
- **`EXPERIMENT-B2-DECK-SEAM-1`** et **`EXPERIMENT-B2-DECK-SEAM-2`** : deux vraies plaques LEGO **`PLATE_1X3` → LDraw `3623`**, disposées SOUS l'interface entre la planche **`board:00027` (2×3)** et **`board:00033` (1×3)**. Chacune porte **2 studs sous la 2×3 et 1 stud sous la 1×3**. Coordonnées réellement produites : `(11,34,35,r1)` et `(11,35,35,r1)` sur **ce modèle** ; **elles ne sont pas codées en dur dans le générateur**.
- **`EXPERIMENT-B2-DECK-BRACE-1`** et **`EXPERIMENT-B2-DECK-BRACE-2`** : deux vraies briques LEGO **`BRICK_1X8` → LDraw `3008`**, sous les planches principales, avec **6 cellules de tenon nominales** réparties sur quatre planches pour chaque traverse. Coordonnées constatées `(6,19,33,r1)` et `(6,22,33,r1)`. Leurs chaînes propres jusqu'aux fondations ne sont **PAS démontrées**.

**Résultat local mesuré :** le plancher de terrasse à 30 éléments passe de **[29,1]** à **[34]**, soit une composante unique avec les quatre pièces ajoutées. La planche auparavant isolée est réunie au module par **deux vraies plaques**. Ce résultat est le **graphe nominal d'emboîtement du sous-ensemble**, il n'établit pas encore une résistance, une trajectoire continue d'insertion, ni une liaison complète aux fondations.

### Contrôles de géométrie positifs et négatifs

Le contrôle numérique limité reprend les sections de véritables tenons/cavités étudiées en **059M**, mais dérive cette fois les centres des empreintes du modèle. Deux plaques × (2×3 + 1×3) → **4 interfaces nominales**, **6 cellules de tenons** dont les profondeurs/espaces sur les sections contrôlées sont géométriquement compatibles avec les paramètres LDraw. Le cas volontairement faux, **plaque déplacée d'un tenon**, est **rejeté** ; une plaque à mauvais niveau vertical l'est également.

**Vérification supplémentaire au moteur maillage officiel épinglé**, en échantillon :
| Paire LDraw réellement contrôlée | Relation triangulée | Connexions explicites reconnues par le moteur |
|---|---|---:|
| Première plaque `3623` → planche `3002` | **CONTACT** | **2** |
| Première plaque `3623` → planche `3622` | **CONTACT** | **1** |
| Un seul faîtage historique `3002` → `30363`, pan 1 | **CONTACT** | **0** |
| Le même faîtage `3002` → `30363`, pan 2 | **CONTACT** | **0** |

**0 signal COLLISION dans ces QUATRE paires**, pas dans le modèle entier. La seconde plaque est validée en coupe et en alignement, mais **pas échantillonnée aux maillages**. Le faîtage échantillonné reste **NON DÉMONTRÉ** malgré les deux `CONTACT` : le moteur ne reconnaît **aucune connexion explicite** pour les deux paires `30363`. Aucune insertion continue n'a été prouvée. **`CONTACT` seul n'est pas une preuve d'emboîtement normal.**

### Inventaire explicite des 42 premiers appuis

Identifiants individuels conservés en `generated/ALL-42-B1-CLASSIFIED.json`.

| Statut de classification | Nombre B-1 | Lecture |
|---|---:|---|
| **A**, appui vertical immédiat non identifié pour les deux cheminées | **4** | Aucun support direct orthogonal prouvé ; attaches alternatives possibles restent inconnues. |
| **A**, une planche de terrasse sans liaison inférieure reconnue | **1** | **Raccordée localement en B-2** aux autres planches, au moyen de deux plaques ; sa chaîne vers les fondations demeure à démontrer. |
| **B**, 12 plaques de liaison sous les plateformes | **12** | Leur tenue peut dépendre d'attaches tenon/cavité orientées vers des éléments du dessus, mal représentées par un contrôle « supporter dessous » ; **pas prouvées** pour toutes. |
| **B ou D**, 23 anciennes jonctions expérimentales 088 du faîtage | **23** | Leur support réel concerne les surfaces inclinées `30363` exclues du contrôle orthogonal. **Un motif représentatif contrôlé aux maillages, sans preuve positive d'engagement.** |
| **D**, deux éléments orthogonaux de plateforme additionnels | **2** | Connexion toujours indéterminée. |
| **C**, impossibilité géométrique positivement établie parmi les 42 | **0** | Aucune incompatibilité physique généralisée démontrée. |
| **TOTAL** | **42** | Les catégories B/D ne sont PAS des preuves que la pièce flotte. |

### Avant / après — périmètres inchangés

| Mesure | B-1 | B-2 |
|---|---:|---:|
| **Pièces modèle entier** | **1 901** | **1 905** |
| Pièces ajoutées / retirées / déplacées | — | **+4 / 0 / 0** |
| Pièces réutilisées à emplacement identique | 1 901 | **1 901** |
| Pièces sans **appui immédiat reconnu par audit orthogonal** | **42** | **45** |
| Composantes connexes **orthogonales globales** | **26** | **26** |
| Collisions détectées en **voxels orthogonaux** | **0** | **0** |
| Composantes **du plancher bois seul** | **[29,1]** | **[34] (quatre pièces ajoutées)** |
| Connexions de plaque/planches contrôlées sur vrais maillages LDraw | 0 | **2 paires, 3 connecteurs explicites** |
| Autres liaisons plaque/planches étudiées par coupes géométriques | 0 | **2 autres paires ; pas de maillage complet** |
| Éléments inclinés `30363` non certifiés mécaniquement | **408** | **408** |
| Pas de preuve complète de chemin d'appui mécanique sur **l'ensemble** | **1 901** | **1 905** |
| Étapes d'assemblage **PROPOSÉES, non certifiées** | **271** | **272** |
| Collisions LDraw de la maison entière | **INCONNUES** | **INCONNUES** |

**Pourquoi 42 → 45 ?** L'auditeur vérifie essentiellement un appui *immédiatement au-dessous*, dans un ordre propre à son code. Une planche auparavant sans appui inférieur nominal est maintenant reliée aux plaques par ses cavités, tandis que quatre pièces de renfort ajoutées sous le plancher ont elles-mêmes besoin de démonstrations de tenue/assise que ce contrôle ne voit pas. **B-2 ne masque jamais ce compteur défavorable.** Nous n'affirmons **ni réduction globale** du nombre de composantes, **ni augmentation certifiée de la résistance mécanique**. Le progrès **vérifié** est la suppression de l'isolation locale de la planche de terrasse via une vraie interface de pièce LEGO.

### Fichiers durables GitHub (PAS uniquement artefact temporaire)

Répertoire : **`missions/B2/generated/`** sur la branche de PR #931 :
1. `GUIDED004-B2-1905-FULL-HOUSE.ldr` — **1 905 placements LDraw, maison entière** ;
2. `GUIDED004-B2-FULL-HOUSE-ISOMETRIC.svg` — 5 715 faces isométriques **SCHÉMATIQUES**, **PAS rendu maillage exact** ;
3. `B2-CORRECTED-DECK-JOINTS.svg` — zoom sur le raccordement ajouté, schématique ;
4. `BOM-B2.json` — BOM 1 905 : +2 `3008`, +2 `3623`, zéro autre delta, pas de commande autorisée ;
5. `ORDER-B2-NOT-CERTIFIED.json` — 272 étapes avec étape de prémontage terrasse signalée non démontrée ;
6. `BEFORE-AFTER-B1-B2.json` — chiffres, vrais IDs et dimensions constatées, preuves des coupes, SHA256 ;
7. `ALL-42-B1-CLASSIFIED.json` et `MESH-4-INTERFACE-SAMPLE.json` — preuves exactement bornées.

**Code ajouté :** `scripts/build_guided004_connections_b2.py`, `scripts/check_b2_mesh_sample.py`, `tests/bricks/test_guided004_connections_b2.py`, `.github/workflows/lego2-b2-connections.yml`.

### Commandes réelles de CI

```bash
python -m pip install -e .
python -m pip install -e ./lego_geometry_engine
python -m pip install pytest
python -m pytest -q tests/bricks/test_guided004_connections_b2.py

python scripts/download_ldraw_probe_066.py /tmp/ldraw-b2 \
  --max-files 240 --parts 30363 3002 3622 3623 3008 3007

python scripts/build_guided004_connections_b2.py \
  --ldraw-root /tmp/ldraw-b2 --output artifacts/lego2-b2

python scripts/check_b2_mesh_sample.py \
  --ldraw-root /tmp/ldraw-b2 \
  --model artifacts/lego2-b2/EXPERIMENTAL-1905-FULL-HOUSE/BRICKMODEL-B2-1905.json \
  --output artifacts/lego2-b2/EXPERIMENTAL-1905-FULL-HOUSE/MESH-4-INTERFACE-SAMPLE.json
```

**CI ciblée RÉUSSIE :** [Actions run #40211795317](https://github.com/ludodulac/boldungo/actions/runs/40211795317), sur HEAD code `f3c431413f383b0cbf1808c7182adea779e0a8c4`. L'Action a versionné les sept fichiers produits en **nouveau commit** sur la **même branche DRAFT**, avec `contents:write` seulement sur branche PR, **sans toucher `main` ni LEGO2**. Le commit automatique ne change pas la logique testée, uniquement les fichiers de sortie.

```text
5 passed in 1.53s
B2_HOUSE {"from_count":1901,"to_count":1905,"added":4,
 "removed":0,"moved":0,
 "b1_orthogonal_unsupported":42,"b2_orthogonal_unsupported":45,
 "b1_orthogonal_components":26,"b2_orthogonal_components":26,
 "b1_orthogonal_collision_cells":0,"b2_orthogonal_collision_cells":0,
 "b1_unverified_slopes":408,"b2_unverified_slopes":408,
 "assembly_step_count_before":271,"assembly_step_count_after":272}
B2_FLOOR_REJOIN {"b1_floor_components":[29,1],
 "b2_floor_components":[34],"nominal_plate_host_interfaces":4,
 "b1_orphan_board":"scene-platform:south-timber-deck-main:board:00033",
 "neighbor":"scene-platform:south-timber-deck-main:board:00027"}
B2_MESH_PAIR deck_2x3_plate CONTACT EXPLICIT_CONNECTORS 2
B2_MESH_PAIR deck_1x3_plate CONTACT EXPLICIT_CONNECTORS 1
B2_MESH_PAIR ridge_30363_left CONTACT EXPLICIT_CONNECTORS 0
B2_MESH_PAIR ridge_30363_right CONTACT EXPLICIT_CONNECTORS 0
B2_MESH_SUMMARY {"checked_distinct_pairs":4,
 "interference_signals_in_sample":0,"sampled_not_exhaustive":true,
 "all_real_insertions_proven":"NO","roof_fully_verified":"NO"}
B2_1905_TRUE_LDRAW_LINES_PASS
B2_B1_ALL_1901_POSITIONS_UNCHANGED_PASS
```

Les spécialisées **B-1** et **B-2** sur le code `f3c431...` sont **SUCCESS**. La **CI générale de ce SHA** était toujours `in_progress` au dernier contrôle. Sur le **commit de fichiers générés**, GitHub renvoie `action_required` (pas une preuve de succès ni une erreur de test exécuté). La CI principale de B-1 avant le travail B-2 était **SUCCESS**.

## HYPOTHÈSE — constructibilité globale toujours partielle

La couture avec deux plaques 3623 fournit des emboîtements **géométriquement identifiables** entre les planches, avec trois connecteurs explicites effectivement retournés pour la première plaque par le moteur et sans interférence dans les deux couples de maillages examinés. **Ce gain local justifie la nouvelle maison expérimentale.**

En revanche, les renforts sous le plancher et les pièces existantes ne disposent pas tous d'une chaîne d'appui aux fondations démontrée. Aucune séquence d'insertion continue de ces pièces n'est vérifiée. Les deux cheminées restent structurellement mal reliées, et les 23 jonctions de toiture ne deviennent pas « validées » parce qu'un motif présente CONTACT. **Le modèle complet ne peut pas encore recevoir une notice de construction fiable ni une certification mécanique.**

## RECOMMANDATION — B-2 terminée / B-3 réservée à Grand-père

**Conserver le modèle B-2 de 1 905 pièces et sa preuve de liaison de terrasse**, sans promouvoir les pièces ni déplacer la Scene. **Ne pas prétendre avoir résolu les 42 problèmes initiaux globalement** : un seulement a obtenu une correction géométrique locale constructive, et le nombre orthogonal est même passé de 42 à 45 avec quatre nouvelles pièces.

Pour le **dernier choix de mission B-3**, recommander à Grand-père de privilégier une **chaîne de support réelle de la terrasse** (assise des traverses) **ou l'une des cheminées**, où le passage à une connexion menant réellement aux fondations apporterait plus de progrès qu'une nouvelle série de micro-diagnostics du faîtage. Ne pas commencer B-3 sans son verdict.

**Dossier fermé pour B-2 :** 0 fusion, 0 dépense, aucun test physique demandé à Ludo. Les données de la maison 1890 et de la Scene restent inchangées.
