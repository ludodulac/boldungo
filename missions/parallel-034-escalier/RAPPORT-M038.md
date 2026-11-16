# BOLDÜNGO — Mission 038 — Construction 3 : escalier expérimental réel

## Référence et provenance
- Départ de M034 : `20fc51c988e1f478fecadd4d32c2a19ce378e332` ; **ancien fichier M034 inchangé** (485 pièces).
- Maison B3 d'origine : `missions/B3/generated/GUIDED004-B3-1904.ldr`, 1 904 pièces (408 pentes).
- Photos directement lues : **IMG_20261007_092854**, **IMG_20261007_092818**, **IMG_20261007_092901**, **IMG_20260919_170032** ; documents `ANALYSE-PHOTOS-109.md`, `ESCALIER-L-TOPOLOGIE-V1.md`.
- Observation photo : volée supérieure le long du mur Sud avec parapet du côté cour ; retournement après un palier et volée basse vers la cour entre murs pleins. Arrivée haute sur le béton, distincte de la terrasse bois. Le débord arrière qualitatif est attesté dans l'audit mais sa **distance est inconnue**.
- Attribution 7 marches en bas, 9 en haut : **hypothèse M034 conservée** ; photos et relevés historiques confirment 7+9, sans métrique permettant de certifier l'attribution.

## Variante indépendante M038
- `ESCALIER-M038-IMPLANTATION.ldr` : **1126 pièces LEGO** en cinq références officielles dont le véritable jumper **3794b.dat**, dont le tenon supérieur central permet un décalage de **un demi-tenon**.
- Structure interne **5 tenons**, dessus décalé d'un demi-tenon : enveloppe transverse **5,5 tenons = 1,10 m** à l'échelle nominale (objectif largeur déclarée ~1,12 m ; écart **−2 cm, −1,8 %**). Ce n'est **pas** une mesure nouvelle, et libre passage/largeur hors-tout ne sont pas distingués.
- Plan placé à côté du véritable contour B3 : volée haute `z=340..700 LDU`, palier `z=700..800 LDU`, volée basse vers le Sud, plus proche du béton que M034. Extrémité béton de la scène B3 : `z_max=400 LDU`; la projection peut se chevaucher mais **aucune connexion par tenon à la plateforme n'est démontrée**. Les pièces actuelles du mur Sud ont elles-mêmes une projection plus large que le plan de mur idéalisé. Aucune fixation n'est ajoutée.
- Les hauteurs des 7 marches basses utilisent une graduation temporaire non uniforme pour garder des jumpers soutenus ; le giron nominal 0,40 m et les hauteurs de marche restent **des hypothèses**. Les parapets réels et le vide sous plateforme ne sont pas reproduits par cette variante en plaques.
- **Débord arrière : NON RÉSOLU.** L'audit photo suggère un retournement au-delà du mur Ouest, alors que placer ce sous-assemblage seulement 20 LDU plus à l'Ouest de la variante testée provoquerait **16 paires de collisions de boîtes** avec le support bois existant de B3. Il serait trompeur de déplacer l'escalier à travers ce poteau sans revoir l'implantation des modules ; terrasse et moteur sont laissés intacts.

## Vérifications
- Dans le prototype : zéro superposition de boîtes orthogonales solides.
- Contre les **1 496 pièces orthogonales B3** : zéro superposition de boîtes. **408 pentes 30363 non maillées** : cela n'est pas une garantie de collision zéro sur des maillages complets.
- Graphe nominal : **1 composant**, zéro pièce sans appui nominal ; correspondances tenon/logement **2887 sites**, dont les tenons centraux 3794b. *Simple contact par boîte ≠ liaison LEGO* ; seule la grille de connecteurs est utilisée pour le graphe, mais sans essai d'insertion ni serrage mécanique.
- **13/13 contrôles JS ciblés réussis**, avec mutations de collision et de source manquante rejetées ; `test-stair-m038.mjs` est reproductible via `node missions/parallel-034-escalier/test-stair-m038.mjs`. Pas de campagne GitHub Actions revendiquée.
- `APERCU-M038-MAISON.svg` montre les formes projetées du mur Sud, les éléments existants de béton/bois et les trois segments du prototype en plan. Ce n'est pas une photographie de maquette LEGO ni une validation de construction physique.

## Décision
**Progrès ciblé accepté au niveau maquette expérimentale**, **intégration physique et fidélité métrique complète NON CERTIFIÉES**. Étape suivante uniquement si demandé : contraindre l'implantation à partir d'un plan de dessus et des côtes réelles du débord, puis concevoir les parapets et l'interface LEGO au béton sans entrer dans le volume de la terrasse B3. Ne pas fusionner la PR DRAFT.
