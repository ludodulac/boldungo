# BOLDÜNGO — Mission 037 : premier support raccordable au mur B3

**Base M033 :** `69c7b5e792199056490539af185368eb5b23b5c0`. Le vrai modèle `missions/B3/generated/GUIDED004-B3-1904.ldr` reste intact (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`, 1 904 pièces, dont 408 pentes 30363).

## Nouveau support
Une seule **vraie brique LEGO 3004.dat**, position `(440,-792,50)`, est ajoutée dans un fichier LDraw **local indépendant**. Les cinq autres pièces du fichier sont copiées aux positions exactes B3. Le support est relié **nominalement** au pignon `gable-000001`, lui-même lié au mur `wall-000699`. La pente `roof-000048` reçoit deux tenons sur deux sites femelles LDCad M031.

**Connexions :** 4 tenons mur→pignon, 2 tenons pignon→nouvelle 3004, 2 correspondances mâle/femelle nouvelle 3004→30363, profondeurs 8 et 14 LDU ; centres `(430,-792,50)` et `(450,-792,50)`. La pente B3 est conservée exactement, sans réorientation de l'architecture à deux pans ≈22°.

## Blocages existants et contrôles
`roof-000025` occupe la zone à gauche, bord à x=420 ; `gable-000006` occupe celle à droite, début x=460. La brique nouvelle occupe exactement le couloir x=420..460, z=40..60, y=-792..-768 : **0 recouvrement positif des boîtes principales** contre les 1 904 pièces B3. Les positions déplacées x−20, x+20, y−24 sont refusées par collision avec `roof-000025`, `gable-000006`, `roof-000048` respectivement. `wall-000704` et `gable-000005` ont également été localisés, sans y ajouter de pièces.

**Limite :** contrôle d'enveloppes des corps nominaux, pas de collision des maillages triangulés ni de profondeur des tenons ; aucun trajet d'insertion ou tenue mécanique ne sont prouvés. Les surfaces de la nouvelle pièce touchent d'autres volumes : un montage sans déplacer la toiture **peut rester impossible**. Ce sous-assemblage n'est pas une charpente complète ou certifiée.

## Livrables
- `M037-GUIDED004-APPUI-LOCAL.ldr` : 5 pièces B3 intactes + 1 brique nouvelle.
- `APERCU-037.svg` : coupe locale avec mur, pignon, voisinage du toit.
- `CONTROLES-037.json` : connexions, origines, blocages et tests négatifs.
- `audit_037.mjs` : contrôles reproductibles de l'emplacement depuis la racine du dépôt.

**Étape suivante :** validation ciblée au maillage de la paire 3004/30363, puis contrôle d'une trajectoire d'insertion sans modifier B3. Ne pas fusionner tant que ces preuves sont absentes.
