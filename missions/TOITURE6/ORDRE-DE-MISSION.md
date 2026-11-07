# 🧱 BOLDÜNGO — TOITURE-6 — fondation locale et deuxième appui

**Propriétaire : Ludo. Exécutant : CONSTRUCTION. Pilotage : Grand-père.**  
**Dépôt :** `ludodulac/boldungo` — **PR #941 DRAFT**.  
**Point de départ vérifié :** `4bba30c06baaa61742b103286c514fbb8c6a44cb`.

## Objectif prioritaire

Transformer le module TOITURE-5 de **43 véritables pièces LEGO** en un assemblage :
1. fixé géométriquement à une **fondation LEGO locale identifiable** ;
2. possédant **deux chemins de connexion distincts** depuis le toit vers deux colonnes murales indépendantes de la cheminée.

La stabilité, la rigidité, le flambement, la résistance à la flexion, l'ancrage au sol et les forces de friction ne peuvent PAS être certifiés par une simple chaîne de tenons.

## Acquis intangibles

- TOITURE-5 : 5 vraies pentes `30363.dat`, une chaîne jusqu'à `wall-000009`, 31 niveaux et 30 joints PASS.
- Module de 43 pièces : collisions contrôlées, insertion et visionneuse mobile PASS dans le périmètre établi.
- **Ne pas revalider TOITURE-1 à 5** ni modifier les placements originaux de B-3 (1 904 pièces), MAISON-4 (356), maison architecturale 019.
- La PR reste DRAFT ; **aucune fusion ni déploiement**.

## Étape A — fondation LEGO locale

B-3 ne contient aucune pièce à Y=0. Tester dans un modèle expérimental *séparé* une vraie baseplate `3811.dat` à **(960, 0, 760)**, orientation identité, sous la rangée `wall-000009` (880,-24,870). C'est une **hypothèse de placement**, pas un PASS. Les centres de tenons peuvent coïncider à cette grille ; il faut le calculer sur les maillages officiels.

1. Vérifier la géométrie LDraw réelle et la reconnaissance des connecteurs avec `wall-000009`.
2. Vérifier collisions avec toutes les pièces originales B-3 suffisamment proches, y compris les rangées du niveau inférieur.
3. Vérifier l'insertion continue de la première rangée sur la base, avec tests négatifs (décalage d'un demi-tenon, superposition de matière).
4. Indiquer explicitement que cette baseplate est **locale** : ne pas la qualifier de fondation complète de la maison ou de fixation au terrain.
5. Si l'emplacement proposé ne convient pas, essayer au maximum **un autre placement justifié**, sans déplacer les 43 pièces acquises.

## Étape B — second chemin toiture → mur

Rechercher une liaison autre que `wall-000707`, en priorité vers **`wall-000719`** (1270,-744,620), mur latéral de B-3. Sa rangée inférieure est **`wall-000021`** (1270,-24,620). L'existence d'une chaîne entre ces extrémités n'est PAS encore démontrée.

- Examiner les briques originales de la colonne latérale, niveau par niveau, jusqu'à la base.
- Partir du support de la rangée toiture : `TOITURE3-VARIANT-3006-ROW336-340` (960,-864,620).
- Proposer une **liaison locale réelle** avec un minimum de pièces LEGO officielles ; tester les connecteurs, la géométrie LDraw et les insertions continues, pas seulement les centres.
- Vérifier les voisins B-3 : notamment les autres pentes 30363 dans la zone X=1030…1270, Z autour de 620 ; elles se trouvent à différentes hauteurs et sont susceptibles d'interférer avec une nouvelle poutre.
- Ne jamais déclarer « second appui indépendant » si les deux chemins passent finalement par le **même mur** sans liaison distincte, ou si la nouvelle pièce flotte.
- Si la liaison à `wall-000719` est impossible, documenter **le premier obstacle exact** et examiner une seconde route localisée, sans relancer un audit général.

## Étape C — extension toiture (conditionnelle)

Si A et B sont démontrés, étudier l'ajout des deux rangées voisines de cinq pièces chacune : `roof-000313` à `317`, et `roof-000359` à `363`, sans changer leurs positions B-3. Leur plan de cavités diffère : Y=-840 et Y=-888, contre Y=-864 pour la rangée déjà soutenue. Elles ne peuvent pas simplement être ajoutées à la même poutre.

Privilégier des supports communs correctement raccordés ; ne pas viser 15/15 en sacrifiant la validité. **Ne pas ouvrir une autre série de petits prototypes**.

## Livrables obligatoires

Sous `missions/TOITURE6/` :
- `MODULE-VARIANTE.ldr` : uniquement de vraies pièces LEGO et provenance documentée ;
- `FONDATION.json` : position, maillages, connecteurs, insertion, limites ;
- `DEUXIEME-APPUI.json` : les deux chemins nominatifs, joints et tests ;
- `COLLISIONS.json`, `INSERTION.json`, `BOM.json`, `RESULTAT.json` ;
- visualisation du module via **visionneuse BOLDÜNGO existante** (pas de nouvelle interface).

Rapport chiffré : baseplate PASS/FAIL/NON DÉMONTRÉ ; raccordement à wall-000009 ; chaîne seconde colonne X/30 ; deuxième appui PASS/FAIL/NON DÉMONTRÉ ; pièces de toiture reliées X/15 ; nouveaux éléments ; collisions ; insertion ; mobile ; limites mécaniques.

## Exécution et STOP

Commencer par le calcul géométrique local en tests ciblés, puis **une campagne CI spécialisée finale**, au maximum **une correction justifiée** après échec. Ne jamais inventer un PASS. Si aucun second appui réel n'est démontré, conserver la fondation locale validée le cas échéant et signaler le blocage exact.

**Aucune fusion, aucune publication. Ne pas modifier les originaux.**
