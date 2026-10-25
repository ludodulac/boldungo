# BOLDÜNGO — R-2 — résultat concret / état de preuve

## FAIT VÉRIFIÉ
Sous-ensemble du toit LEGO Creator 31009, livret 1, notice publique LEGO 6038244.pdf, **25 opérations numérotées**, sur les pages imprimées **47 à 68**.

Fichier LDraw 3D : `missions/R2/31009-ROOF-R2-OFFICIAL-STEP-RECONSTRUCTION.ldr`.
Nomenclature : `missions/R2/BOM.json`.
Correspondance pièce et étapes : `missions/R2/OFFICIAL-STEPS-ORDER.json` et `31009-ROOF-STEP-PLACEMENTS.tsv`.
Aperçu 3D schématique : `missions/R2/R2-APERCU-ISOMETRIQUE.svg`.

**80 pièces, dont 29 pièces de toiture inclinées :** 6×4445, 10×3037, 4×3038, 5×3039, 4×3046. Les **51 autres** incluent supports 3001/3002/3003/3004/3005/3009/3010/3023/32001/32028/3622/3659/3832, fenêtres 60592/60601, accessoires, et cheminée (dont **1×3022**). La plaque 3022 du fichier d'origine **n'est pas artificiellement utilisée comme faîtage** : elle appartient à la cheminée LEGO représentée à l'étape 24.

**Provenance exacte :**
- Notice officielle LEGO, source de l'ordre et des illustrations : https://www.lego.com/cdn/product-assets/product.bi.core.pdf/6038244.pdf .
- Placement 3D numérisé **non officiel** : modèle communautaire de l'auteur « LTRON », fichier `data/train/building377.mpd` à l'empreinte GitHub `31c2222a4b007298e9e53b429562957c78972017` dans `willsaliba/M3_Model`. Le source porte le titre `31009 - Small Cottage - Small Cottage.mpd`. Les **80 lignes** contiguës d'index 149 à 228 sont conservées sans réorienter ni ajouter aucune pièce. La correspondance aux 25 étapes LEGO a été structurée par la succession des pièces et contrôlée sur les dessins/page.
- **La coïncidence de placement exacte de chaque pièce du modèle communautaire avec la notice LEGO n'est PAS prouvée pixel par pixel.** Ne pas qualifier ce fichier de CAD certifié LEGO.

Pages corrigées depuis la notice (une page pouvant contenir deux étapes) :
`1:47,2:47,3:48,4:49,5:49,6:50,7:51,8:51,9:52,10:52,11:53,12:54,13:55,14:56,15:57,16:58,17:59,18:60,19:61,20:62,21:63,22:64,23:65,24:66–67,25:68`.

**Test spécialisé GitHub #40187888177 : SUCCESS, 4 passed in 0.10s.**
Extraits bruts :
```text
R2_PARTS 80 SLOPED 29 STEPS 25
R2_OFFICIAL_STEP_COUNTS [2,2,2,3,2,6,2,1,2,2,4,6,4,4,4,4,2,2,4,2,4,3,3,5,5]
R2_ORIGIN_SOURCE_3D COMMUNITY_LTRON_NOT_LEGO
R2_NO_FAKE_RIDGE_PILLARS PASS
R2_LDRAW_EXACTLY_REPRODUCED
R2_EXACT_BOM_AND_25_OFFICIAL_STEP_COUNTS_PASS
```

Commandes :
```bash
python -m pytest -q tests/bricks/test_official_roof_r2.py
python scripts/reconstruct_official_31009_r2.py --output artifacts/lego2-r2-official-31009
cmp missions/R2/31009-ROOF-R2-OFFICIAL-STEP-RECONSTRUCTION.ldr artifacts/lego2-r2-official-31009/31009-ROOF-R2-OFFICIAL-STEP-RECONSTRUCTION.ldr
```

**Périmètre géométrique non établi :** contrôle triangulaire exhaustif des 80 pièces NON EXÉCUTÉ ; nombre de collisions physiques NON DÉMONTRÉ ; nombre de composantes réellement connectées NON DÉMONTRÉ ; chaque chemin d'appui aux fondations NON DÉMONTRÉ ; trajectoires d'insertion de notre export communautaire NON DÉMONTRÉES. Les 80 vrais placements et les groupes d'étapes sont vérifiés, pas l'ensemble des interactions géométriques. Une notice LEGO documente les montages du set original ; pas une certification mécanique indépendante de notre reconstruction numérique.

## HYPOTHÈSE
Comparé à R-1, le sous-ensemble suit beaucoup plus fidèlement la **structure originale** : 80 pièces dont 29 pentes officielles, sur des plaques `32001`/`3832` et des briques LEGO rouges ; aucune baseplate 3811 ni quatre piliers 3007 imaginés pour R-1 ; le faîtage avec lucarne utilise des pentes `3046` et le 3022 présent sert à la cheminée. À l'inverse R-1 était une petite recette simplifiée à 41 pièces, 8 de toiture dont 4 longues pentes, plus aisée à généraliser mais moins fidèle.

Le modèle R-2 est **plus fidèle en famille de pièces, quantités et ordre documenté**, mais **plus complexe** ; il n'est pas automatiquement meilleur comme recette générique.

## RECOMMANDATION
Ne pas prolonger R-2 en série de nouveaux systèmes de collision. Conserver ici le **vrai modèle LDraw 80 pièces**, visible via l'aperçu schématique SVG, et sa provenance. R-3 (uniquement après décision de Grand-père) devra extraire le **motif répété minimal de supports/2 pans** de ces étapes, avec un contrôle géométrique borné et une recette dimensionnable, sans altérer la pente 45° vers les 22° de GUIDED-004 ni toucher cette dernière.

Aucune fusion ; `main`, la branche LEGO2 principale, la PR A #929, GUIDED-004 et les livrables R-1 sont préservés.
