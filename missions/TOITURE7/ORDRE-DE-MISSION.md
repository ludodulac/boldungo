# 🧱 BOLDÜNGO — MISSION TOITURE-7 — deuxième appui supérieur, SANS collisions

**Propriétaire : Ludo. Pilotage : Grand-père. Exécution : CONSTRUCTION.**  
**Dépôt** : `ludodulac/boldungo` — **PR #941 DRAFT**.  
**HEAD vérifié avant création** : `f462f4868278f9d7a1256526f223b5a16f5279e1`.

## But, en une phrase

À partir des **75 pièces retenues de TOITURE-6**, obtenir une **deuxième liaison démontrée** entre le support des **5 pentes `roof-000336`…`340`** et le **deuxième mur** (`wall-000719`), en évitant toute collision avec la toiture originale B-3.

**Ne pas reconstruire TOITURE-1…6** ; ne pas ajouter d'autres pentes avant la deuxième liaison.

## Référence immuable : le modèle RETENU, pas l'expérience échouée

- Point de départ : `missions/TOITURE6/MODULE-RETENU-75.ldr` ; `VIEWER-RETENU-75.json`.
- 43 pièces TOITURE-5 + 31 pièces deuxième mur original + 1 baseplate officielle `3811.dat`.
- `FONDATION.json` : deux pieds muraux, `wall-000009` et `wall-000021`, sont nominalement raccordés à `3811`. C'est une **base locale**, pas une fondation complète ni ancrage au terrain.
- `DEUXIEME-APPUI.json` : 30/30 joints de la colonne `wall-000021` → `wall-000719` vérifiés.
- **Ne pas réintroduire les quatre `TOITURE6-BRIDGE-{A,B,C,D}-3006`** : collisions confirmées respectivement avec `roof-000292`, `roof-000269`, `roof-000246`, `roof-000223`.
- **Ne pas compter `roof-000315`** parmi les pièces assemblables : son insertion est non démontrée (tenon en [1050,-840,610] ; possible interaction avec `roof-000338`).

Les 75 pièces sont la version **conservée géométriquement**, mais la vue spécifique 75 n'a **pas encore eu un essai Chromium indépendant**. Ne pas utiliser la capture de la variante échouée de 80 pièces comme validation du modèle 75.

## Étape 1 — recherche courte et déterminante : une pente existante déjà au-dessus du mur Est

Avant de dessiner toute nouvelle longue poutre, vérifier le contact **`roof-000223` ↔ `wall-000719`** dans B-3.

Ces deux pièces sont toutes deux originales, sans déplacement :

- `roof-000223` : `30363.dat`, (1270, -768, 620), orientation B-3 d'origine.
- `wall-000719` : `3008.dat`, (1270, -744, 620), orientation B-3 d'origine.

**Hypothèse non certifiée :** les centres de cavités candidates de 30363 sont au plan Y=-744, exactement au plan des tenons supérieurs de `wall-000719`. Vérifier précisément à partir des **triangles officiels**, de la géométrie sous la pente, des connecteurs ET de l'insertion continue. Tester les collisions avec les voisins pertinents.

- Si PASS, le mur Est possède une interface toiture potentiellement exploitable, mais **cela ne relie pas encore notre groupe de cinq pentes au deuxième mur**.
- Si FAIL/NON DÉMONTRÉ, expliquer le premier défaut de géométrie et ne pas fabriquer de faux raccord.

## Étape 2 — remplacer le tracé des quatre poutres qui traverse les pentes

Vérifier la possibilité de créer une structure **sous** les faces de toiture plutôt qu'à l'intérieur des pentes :

- Du support existant `TOITURE3-VARIANT-3006-ROW336-340` (960,-864,620) vers le **mur Est** via des éléments porteurs LEGO officiels, **sans occuper les volumes des pentes** `roof-000292`, `269`, `246`, `223`.
- Une hypothèse de route peut partir de la liaison `roof-000223`–`wall-000719` si elle est validée, puis s'appuyer sur une petite structure sous les rangées intermédiaires. Les pentes voisines qui ne sont pas validées ne sont pas des *connecteurs automatiquement acceptés*.
- Favoriser une jonction à la **face inférieure** / aux plans de tenons des poutres au lieu d'installer une longue brique 3006 au même niveau que les corps de toiture.
- Tester les connecteurs réels, les insertions **en ordre constructible**, les collisions avec les 75 pièces retenues et les voisins B-3, puis l'existence de **deux chemins de graphe distincts avant la baseplate**.
- Ne pas modifier les positions du groupe de 5 pentes, des deux murs, de la fondation 3811 ni des placements originaux B-3.

**Priorité** : une vraie deuxième liaison plutôt que rajouter des pièces au toit. Limiter à **deux variantes locales motivées** (pas de recherche combinatoire ouverte, pas de prototypes sans fin). Si impossible, conserver strictement les 75 pièces et livrer la première contrainte géométrique précise.

## Étape 3 — vérifier les deux chemins de façon indépendante

La première chaîne connue est :
`roof-000338` → `TOITURE3-VARIANT-3006-ROW336-340` → `TOITURE4-VARIANT-3006-BRIDGE-TO-GABLE` → `TOITURE4-VARIANT-3622-GABLE-CONNECTOR` → pignon → `wall-000707` → `wall-000009` → baseplate.

Le nouveau chemin doit passer par **`wall-000719`** → `wall-000021` → baseplate, sans utiliser le mur `wall-000707` ni la cheminée pour ce chemin ; les 2 chemins ont le droit de partager les 5 pentes ou le support commun et la baseplate, mais ils doivent avoir **deux routes d'appuis distinctes vers les deux murs**.

Deux graphes de tenons ≠ deux appuis *mécaniquement suffisants* ; résistance à la flexion, stabilité et effort réel restent NON DÉMONTRÉS.

## Livrables

Créer `missions/TOITURE7/` :
- `MODULE-RETENU.ldr` à partir du 75 + **seulement des pièces supplémentaires vérifiées** ;
- `PROVENANCE.json`, `BOM.json` ;
- `ROOF223-WALL719.json` : résultat du premier test avec coordonnées/connecteurs/collisions ;
- `DEUX-CHEMINS.json` : preuves nominatives des deux trajets ;
- `COLLISIONS.json`, `INSERTION.json`, `RESULTAT.json` ;
- export pour la visionneuse **existante** et vraie capture Chromium **du module retenu** (pas de la variante échouée).

**Rapport final demandé :** pièces conservées, pièces ajoutées, cinq pentes maintenues, première collision restante (ou absence), connexion `roof223↔wall719` PASS/FAIL/NON DÉMONTRÉ, deuxième chemin complet PASS/FAIL/NON DÉMONTRÉ, insertion PASS/FAIL/NON DÉMONTRÉ, mobile PASS/FAIL, statuts distincts pour mécanique et fondation complète.

Une campagne CI ciblée **après les tests locaux**, au maximum une campagne corrective si problème technique prouvé. Ne pas relancer CI-1…6. La PR reste **DRAFT**, sans merge ni déploiement. B-3 / MAISON-4 / 019 restent intacts.

**STOP après livraison factuelle ; ne pas annoncer TOITURE-8 automatiquement.**
