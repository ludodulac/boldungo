# BOLDÜNGO — Nouvelle maison entière visible dans la visionneuse 3D

Nouvelle entrée « **Nouvelle maison LEGO — 1 792 pièces** » dans `frontend/viewer.html` et carte correspondante en accueil `frontend/index.html` sur la branche PR #939 DRAFT.

**Il s'agit bien d'une version complète convertie automatiquement à partir de la vraie maison LEGO MAISON_COMPLETE2, pas du modèle visuel 2 852 éléments ni de la maquette partielle 356.** Les 1 792 placements, identifiants, références, matrices et coordonnées LDraw sont conservés. Contrôle à la génération : 1 496 originaux hors toit, 296 nouveaux LEGO de toit, BOM cohérente, coordonnées en grille entière, contrôle `wall-000001` et `wall-000719`.

L'adresse de prévisualisation correspond au viewer HTML existant avec `?bundle=./data/guided004-maison-complete-1792-brickhouse.json`. Les commandes « Vue perspective / Avant / Arrière / Gauche / Droite » et le zoom/orbite restent disponibles sur la page.

**Important :** prototype expérimental. La forme du toit reste en escalier et non fidèle à l'angle photographié. Des trous restent autour des cheminées. Vrais maillages, ordre d'insertion et solidité physique pas encore validés. La production et les autres modèles ne sont pas modifiés.

Script de régénération depuis le LDraw source : `node scripts/convert_b3_roof_to_brickhouse_viewer.mjs [source] [output]`.

Aucun merge, aucun déploiement GitHub Pages. Des prévisualisations CDN de branche peuvent être utilisées en tant que **prévisualisations externes non officielles**, pas une publication de production.
