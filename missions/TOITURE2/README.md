# TOITURE-2 — variante unique, connecteur 3002 sous la toiture 30363

Hypothèse de Grand-père testée sans toucher à B-3 : remplace **dans ce fragment
uniquement** la 3622 supérieure originale (950,-864,630) par une véritable
3002 (960,-864,630) d'orientation identique. Conserve **à l'octet près**
les deux autres lignes B-3 (3622 inférieure + 30363 de roof-000338).

Nomenclature : 1× 3622, 1× 3002, 1× 30363 ; **1 référence substituée,
0 pièce ajoutée au nombre total**. Les 408 briques de toiture, le modèle
architectural 019 et les 356 pièces publiées ne changent pas.

`MODULE-VARIANTE-3002.ldr` contient les lignes LEGO réelles.
`PROVENANCE.json` et `COMPARAISON.json` consignent ce qui change
*uniquement dans la variante*.
`CONNEXIONS.json`, `COLLISIONS.json`, `INSERTION.json`,
`RESULTAT.json` donnent les mesures effectives du moteur LDraw et
des trajectoires continues.
`VIEWER-3.json` permet de parcourir **trois étapes dans la visionneuse existante**.

Lien de prévisualisation après serveur de cette branche à la racine du
dépôt : `frontend/viewer.html?bundle=../missions/TOITURE2/VIEWER-3.json`.
Le rendu reste un **proxy visuel** ; la vérification utilise les
triangles LDraw de la bibliothèque épinglée, non les cubes WebGL.

La validation d'un support **local** ne prouve pas le chemin de charge vers
les fondations de B-3 ni l'absence de collisions avec les 1901 autres
placements non sélectionnés. Les tolérances mécaniques réelles, forces de
clipsage et contraintes structurelles restent NON DÉMONTRÉES.
