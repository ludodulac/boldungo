# BOLDÜNGO — TOITURE-5, toiture vers le pied du mur

Cette mission étend **sans déplacement** le module TOITURE-4
(5 pentes officielles LEGO 30363) à une **unique colonne continue
de 31 briques originales B-3 3008**, de `wall-000009` (Y=-24)
à `wall-000707` (Y=-744).

Le module présente **43 pièces distinctes** : les 13 de TOITURE-4,
plus 30 éléments de mur originaux situés en dessous. Aucune nouvelle
pièce LEGO n'est nécessaire pour le raccord au pied du mur.

**Données et tests** :

- `MODULE-TOIT-AU-PIED.ldr` : 43 placements LDraw, toutes les positions
  sources inchangées.
- `VIEWER-43.json` : 43 étapes d'assemblage avec la visionneuse
  BOLDÜNGO existante (rendu schématique).
- `CHAIN-PROOF.json` : preuves par maillages officiels LDraw des
  **30 nouvelles interfaces** briques 3008, connecteurs, collisions,
  insertion analytique continue, parcours des 5 pièces de toiture
  jusqu'à `wall-000009`.
- `COLLISIONS.json` et `INSERTION.json` : vérifications des voisins
  et ordre des étapes.
- `EXTENSION.json` : les dix autres 30363 de la zone, deuxième
  support indépendant : aucun PASS inventé.
- `RESULTAT.json`, `BOM.json`, `PROVENANCE.json` : rapports mesurés.
- `toiture5-mobile.png` : capture mobile si le test Chromium aboutit.

**Attention** : le pied de la dernière rangée est à Y=-24, ce qui
correspond à un corps LEGO se terminant à Y=0. **Il n'y a aucune
plaque de fondation à Y=0 dans B-3.** La continuité de la chaîne
vers cette face ne constitue pas une connexion à une fondation.
La tenue mécanique, la résistance au basculement et un deuxième
appui indépendant sont toujours **NON DÉMONTRÉS**.

Aucune modification de B-3, MAISON-4, modèle 019 ni de la visionneuse
publique. Aucun merge. Aucun réaudit TOITURE-1 à TOITURE-4.

Lien de prévisualisation sur un serveur local de cette branche :
`frontend/viewer.html?bundle=../missions/TOITURE5/VIEWER-43.json`.
