# Mission A — étude des pièces et des trois maquettes 30363

État : **EXPÉRIMENTAL, NON CERTIFIÉ, NON FUSIONNÉ**. Aucune modification de main, de GUIDED-004 ou des archives 088–099.

## État réellement vérifié au départ (2026-10-24)

- Le dépôt `ludodulac/lego-app` a pour nom canonique GitHub `ludodulac/boldungo`.
- `main` : `b82f94cc2e7ad2d8d613d5eb0d610fb42cdf7fc9` ; `feat/lego2-existing-house-021` : `3cb6b897f29b6e44e312cd46220903ed6f9e363a`.
- Mission 098, PR #927 fusionnée dans LEGO2 ; deux supports muraux fixes réels, **32 tenons centraux non soutenus** sur la grande maison, **0 panneau verrouillé par deux appuis**.
- Mission 099, PR #928 toujours DRAFT : quatre plaques 3024 sur le pignon ; leur écart sous le rail incliné à 22° reste non nul et **0 chemin N4 de toit fixé**, malgré les vues et CI vertes.
- `support_chain.py` ne couvre que les briques murales orthogonales et cadres validés ; la vérification expérimentale des `roof_support` et `roof_tile` nécessite un contrôle distinct, que le présent banc d'essai NE présente pas comme une certification.

## Étape zéro — fichier LDraw officiel

Références à vérifier et conserver lors de l'audit :

- `https://library.ldraw.org/library/official/parts/30363.dat` — `0 Slope Brick 18 4 x 2`. Géométrie extérieure inclinée reliant approximativement (Y=0,Z=-10) à (Y=20,Z=-70) ; angle de la **facette** = `atan(20/60)=18.43494882°`. La pièce appelle la sous-pièce `s/30363s01.dat`.
- `https://sources.debian.org/src/ldraw-parts/2003%2Bds-1/parts/s/30363s01.dat/` — copie publiée de la sous-pièce LDraw ; deux vrais tenons SUPÉRIEURS centrés en coordonnées locales (X=±10,Y=0,Z=0). En dessous se trouvent les tubes/constructions `stud4a`, ainsi que des sous-géométries aux Z=-10, -30 et -50 ; coque à Y=24 local. Ce sont des **indices géométriques de connectabilité**, pas une courbe de résistance ou une preuve automatique de mate sur toute l'empreinte.
- La référence `3037.dat` (pente 45°, 2×4) existe dans `lego_geometry_engine/tests/fixtures/ldraw/parts/3037.dat`. Vérifier aussi `60477.dat` (18°, 4×1), `5404.dat` (petite pente), `3039.dat` (45°, 2×2) avant de généraliser une autre famille.
- Briqueterie ordinaire, purlins et support du prototype : `3003.dat` (2×2), `3007.dat` (2×8), `2456.dat` (2×6), `3001.dat` (2×4), `3008.dat` (1×8), `3009.dat` (1×6), `3010.dat` (1×4), `3622.dat` (1×3), `3004.dat` (1×2), `3005.dat` (1×1), `3023b.dat` (plate 1×2), `3811.dat` (baseplate 32×32).

**Garde-fou géométrique :** le calcul expérimental relie des stud-centres à des empreintes/cavités nominales. Il n'a pas encore aplati/vérifié toutes les sous-pièces DAT avec leurs opérations booléennes de maillage, leurs tolérances, les intersections fines des tenons ni l'insertion depuis chaque trajectoire de montage. L'étiquette `supported_roof_to_baseplate_nominal` n'autorise donc aucun achat, assemblage final ou certitude mécanique.

## Recette générique proposée, limitée à la famille 30363

Entrées du code : `width`, `length`, `pitch`, `overhang`, `wall_courses`. La grille actuelle est bornée à **20 ou 26 tenons de largeur** et une longueur paire entre 20 et 30 ; toute autre géométrie risquant de casser l'interface centrale est rejetée, PAS corrigée silencieusement. Le débord non nul est volontairement rejeté avant preuve de porte-à-faux et d'insertion : **ce paramètre est déclaré, mais la fonctionnalité n'est pas encore achevée**.

1. Couronnes murales orthogonales sur tenons de baseplate et deux vrais pignons montés rang après rang.
2. Colonnes indépendantes de briques 3003 2×2 appuyées sur la baseplate, alignées aux positions des poutres. Longueur de poutre **au plus 8 tenons** (3007/2456/3001/3003), pas de portée libre de 20–30 tenons.
3. Pour chaque pan : rangs de vraies pièces 30363 le long de la longueur par blocs de 2, chaque nouveau rang avance de 3 tenons et monte de 3 plaques ; le rang suivant recouvre nominalement un tenon haut du précédent.
4. Au centre, les deux rangs finaux présentent deux lignes contiguës de vrais tenons supérieurs ; des plaques 3023b 1×2 les relient nominalement. Elles sont posées après les rangs.
5. Génération de LDraw, BOM, graphe d'appui nominal, collisions de boîtes orthogonales (ne remplace pas un audit des surfaces inclinées) et ordre de montage **proposé**.

Le principal progrès expérimental est d'utiliser directement les tenons horizontaux et les tubes de la famille inclinée plutôt que d'essayer de verrouiller une grande plaque rigide articulée à 22°. Le basculement/mise en place réelle de chaque rang, les efforts et le comportement du faîtage restent à démontrer.

## Pente et fidélité

- **Facette réelle 30363 :** 18,43495°.
- **Montée de rang :** 3 plaques / 3 tenons = 24/60 LDU ; angle moyen des marches = 21,80141°.
- Par rapport à 22° : écart de pente moyenne ≈ -0,19859°, sous réserve que les rangs forment le profil nominal et qu'il n'y ait ni collision ni déformation.
- Par rapport à 18° : +3,80141° pour le profil global des rangs. Une demande 18° ne sort donc pas à 18° global. La recette explicite **requested_pitch_degrees** et **course_step_pitch_degrees** ; elle ne promet pas une pente continue homogène.
- Pour une demi-largeur de 10 tenons : différence verticale géométrique théorique entre 22° et 18° = `10*20*(tan(22°)-tan(18°))` LDU ≈ **15,8 LDU**, soit ≈ **1,98 plaque**. Il ne s'agit pas d'une correction du modèle GUIDED-004.

## Trois expériences concrètes

- **A1** : 20×20 tenons, 3 rangées de murs, demande 18° (exprès pour mesurer le compromis 18°/21,8°).
- **A2** : 26×24 tenons, 4 rangées de murs, demande 22°.
- **A3** : 26×28 tenons, 5 rangées de murs, demande 22°.

Fichiers générés dans chaque sous-dossier : `A?-REAL-PARTS-EXPERIMENT.ldr`, `A?-EVIDENCE.json`, `A?-BOM.json`, `A?-ASSEMBLY-ORDER.md`, plus `COMPARE-THREE-HOUSES.json`. Les quantités sont exclusivement lues dans les fichiers de CI après exécution ; **ne jamais les inventer**.

## Modules antérieurs : candidats à évaluer pour archivage, NON supprimés

Si la nouvelle voie obtient une preuve supérieure, reconsidérer notamment :

- Chaîne de faîtage par correctifs locaux : `ridge_bridge_planner_065.py`, `ridge_proposal_3d_066.py`, `ridge_seam_offsets_067.py`, `ridge_full_length_audit_068.py`, `ridge_structural_posts_070.py`, `ridge_anchor_path_071.py`, `ridge_cap_adapter_072.py`, `ridge_tile_upper_interface_073.py`, `ridge_clutch_verifier_074.py`, `ridge_two_slope_joint_075.py`, `ridge_central_post_076.py`, `ridge_four_piece_assembly_077.py`, `ridge_material_volume_080.py`, `ridge_technique_candidates_083.py`, `ridge_trial_assembly_084.py`, `ridge_trial_ldraw_export_085.py`.
- Dépendances de la couverture panneaux/fermes : `roof_eave_shift_069.py`, `roof_host_mesh_064.py`, `roof_joint_module_087.py`, `roof_connectivity_compiler_089.py`, `roof_eave_bearer_builder_090.py`, `roof_studdeck_designer_091.py`, `roof_collision_093.py`, `roof_technic_transfer_096.py`.

**À préserver explicitement :** `support_chain.py`, validateurs existants, `roof_mesh_preflight.py`, `roof_raster_fidelity.py`, `roof_skin_support.py`, `roof_ridge_diagnostics.py` et la famille `roof.py` tant que leurs usages actuels ne sont pas remplacés avec tests. Une liste de candidats n'est pas une recommandation de suppression.

## Portes de sortie — 3 missions maximum

Le banc d'essai A relève au mieux de preuves nominales N1/N2, pas de N4/N5/N6. Avant qu'il puisse servir pour des notices d'assemblage validées, demander à la mission suivante une **preuve LDraw exhaustive et une simulation d'insertion** sur un petit module, sans faire manipuler de LEGO à Ludo. Si cette preuve réfute le placement (pièces s'interpénètrent ou boîtes trop approximatives), **CHANGER D'APPROCHE** vers une autre référence testée ; ne pas masquer l'échec derrière davantage de diagnostics. Trois missions maximum, décision finale à Ludo.
