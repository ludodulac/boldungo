# 🧱 BOLDÜNGO — MAISON-1 : VRAI ANGLE EST–SUD DU RDC DE GUIDED-004

**Mission MAISON-1 terminée : UNE construction localisée, pas de MAISON-2.** PR [#933](https://github.com/ludodulac/boldungo/pull/933) **DRAFT**, nouvelle branche `feat/lego2-maison1-guided004-southeast-corner`, base S-3 déjà validée, aucune fusion ni modification des PR #929–932, `main`, LEGO2, GUIDED-004 canonique ni Scene.

## FAIT VÉRIFIÉ

**Le fragment n'est pas inventé.** Il provient de la Scene originale `frontend/data/boldungo2-guided-004-real-scene.json` (SHA-256 `752c407f3e087e18f71e4e298a152a87f30011692affff0d210b65933a1ae98e`) : façade EST/avant, façade SUD/gauche, **petite fenêtre de RDC `east-rdc-window-left`**, façade originale de **9,30 m**, profondeur SUD **8,20 m**. Échelle effective du générateur canonique : **48/9,30 = 5,16129 tenons/mètre**. La découpe occupe dans les coordonnées canoniques **x=16..36 (20 tenons ≈3,875 m)** et **y=2..22 (20 tenons ≈3,875 m)** ; les pièces source ont été sélectionnées sans déplacer leurs coordonnées, sur un sous-ensemble de ce domaine. Premier niveau de la Scene nominalement **2,4 m** (hauteur totale inférée), tandis que le nouveau plancher expérimental termine au niveau **43 plaques ≈2,517 m**. **Ce léger écart (~0,117 m) est explicite et ne modifie pas la Scene.** Une dalle de base 32×32 est expérimentale et peut dépasser la découpe ; elle n'est pas une fondation observée.

**Maison construite numériquement : 126 véritables lignes de placement LDraw.**
- **91 placements sources préservés** : **29 briques du mur EST, 32 briques du mur SUD**, et **30 BRICK_1X1 proxy de la petite fenêtre EST au RDC**. La fenêtre suit les positions existantes ; ces 30 briques **ne sont ni une véritable fenêtre LEGO ni un vitrage conforme**.
- **35 pièces expérimentales ajoutées** : **1 plaque-base 3811 32×32**, **26 briques 3003 en deux poteaux de 13 cours**, **2 poutres 3006**, **5 plaques de plancher 3832**, **1 plaque 3022** raccordant les deux façades au coin. **Aucun remplacement architectural**, aucun changement des ouvertures/hauteurs/orientation de la Scene. On n'installe aucun toit, cheminée ni terrasse.
- Nomenclature globale : `3003:26, 3004:6, 3005:33, 3006:2, 3008:34, 3009:13, 3022:1, 3622:4, 3710:1, 3811:1, 3832:5` → **126 pièces** (liste définitive dans `MAISON1-NOMENCLATURE.json`).
- Le fragment réellement extrait peut être resitué dans la maison entière grâce au SVG **`MAISON1-LOCALISATION-DANS-SCENE.svg`** : la fenêtre de façade originale est marquée en bleu, découpe en vert. Il s'agit d'une **vue de plan**, indépendante de l'aperçu 3D volumétrique.

### Construction et raccordements ciblés

Deux sections de murs perpendiculaires proviennent directement du modèle existant. Un **seul 3022 (2×2)** à leur sommet établit **2 alignements de tenons sur le mur EST + 1 sur le mur SUD**. Chaque poutre 3006 relie **le mur EST (2 connecteurs)** à **un poteau arrière de soutien (4 connecteurs)**. Cinq plaques 3832 reposent sur les deux poutres : **10 interfaces** de plancher de 4 connecteurs chacune. Les 26 briques de poteaux sont empilées sur 13 cours, chaque empilement reconnu par le moteur ; **les deux liaisons poteau→base 3811 sont le premier obstacle réel**.

**42 nouvelles liaisons parent→enfant positionnées**, dont **40** avec des connecteurs explicites reconnus par le moteur LDraw, **2 sans reconnaissance positive** :
```text
M1-POST-0-COURSE-0 -> M1-EXPERIMENTAL-BASE-3811 (4 centres nominaux / 0 connecteur moteur)
M1-POST-1-COURSE-0 -> M1-EXPERIMENTAL-BASE-3811 (4 centres nominaux / 0 connecteur moteur)
```
Ces deux liaisons sont **NON DÉMONTRÉES** : la classe 3003/3811 donne `CONTACT` au maillage représentatif, mais pas de vrai connecteur moteur identifié. Une absence de connecteur détecté ne prouve pas une impossibilité physique.

**Six familles distinctes de interfaces auditées sur UN représentant chacune** : `3003/3811 CONTACT`, `3003/3003 CONTACT`, `3006/3008 CONTACT`, `3006/3003 CONTACT`, `3832/3006 CONTACT`, `3022/3008 CONTACT`. **Zéro collision signalée dans ces six échantillons**. **Zéro chevauchement interdit** dans le contrôle orthogonal des volumes des 126 pièces. **Pas** de contrôle exhaustif sur toutes paires de triangles et toutes répétitions.

**Chemins d'appui** : plaque de plancher → poutre 3006 (connecteur reconnu) → poteau arrière 3003 (connecteur reconnu) → 12 empilements (connecteurs reconnus) → **base 3811 : NON DÉMONTRÉE**. Il existe aussi le chemin de la poutre à la façade EST, mais la vérification complète de la structure ancienne et de ses appuis historiques n'a pas été recommencée. **Les murs EST et SUD sont reliés localement par la plaque de coin, mais pas mécaniquement certifiés sur toute leur hauteur.**

**Ordre** : briques d'origine suivant niveaux, base S-3 expérimentale, poteaux de 13 cours, liaison de coin, deux poutres, cinq panneaux : le fichier `MAISON1-ORDRE-PROPOSE.json` conserve toutes les opérations ; **insertion continue et résistance physique NON DÉMONTRÉES**.

### Fichiers permanents GitHub

Tous dans `missions/MAISON1/generated/` :
- `MAISON1-EST-SUD-FRAGMENT.ldr` — **126 vraies positions LDraw** ;
- `MAISON1-VUE-3D-SCHEMATIQUE.svg` — perspective **SCHÉMATIQUE**, pas maillage rendu ;
- `MAISON1-LOCALISATION-DANS-SCENE.svg` — comparaison à la position réelle dans la Scene ;
- `MAISON1-NOMENCLATURE.json`, `MAISON1-PROVENANCE.json`, `MAISON1-ORDRE-PROPOSE.json`, `MAISON1-CONTROLES-NOUVEAUX-RACCORDS.json`, `MAISON1-RESULTATS.json`.

Générateur reproductible : `scripts/build_guided004_corner_maison1.py`. CI `.github/workflows/lego2-maison1-real-scene.yml`. Tests `tests/bricks/test_guided004_corner_maison1.py`.

### Commandes et sorties brutes

```bash
python -m pytest -q tests/bricks/test_guided004_corner_maison1.py
python scripts/download_ldraw_probe_066.py /tmp/maison1-ldraw \
  --max-files 250 --parts 3811 3003 3006 3832 3022 3005 3004 3008 3009 3010 3622
python scripts/build_guided004_corner_maison1.py \
  --ldraw-root /tmp/maison1-ldraw --output artifacts/lego2-maison1
```

**CI ciblée spécialisée** [GitHub Actions #40365985644 — SUCCESS](https://github.com/ludodulac/boldungo/actions/runs/40365985644) sur HEAD générateur `2930fc6a73a618cf183deb014dd1a60a31ac7367`.

```text
4 passed in 0.90s
MAISON1_MESH_CLASS ('3003', '3811') CONTACT
MAISON1_MESH_CLASS ('3003', '3003') CONTACT
MAISON1_MESH_CLASS ('3006', '3008') CONTACT
MAISON1_MESH_CLASS ('3006', '3003') CONTACT
MAISON1_MESH_CLASS ('3832', '3006') CONTACT
MAISON1_MESH_CLASS ('3022', '3008') CONTACT
MAISON1_NEW_LINKS 42 CONNECTORS 40 MESH_CLASS_COUNT 6
MAISON1_MODEL {"parts":126,"source_parts":91,"new_parts":35,
  "front_wall_count":29,"south_wall_count":32,
  "original_window_proxy_count":30,"new_orthogonal_body_collisions":0,
  "new_connections":42,"new_connections_with_actual_connector":40,
  "mesh_sample_collision_signals":0,
  "complete_assembly":"NOT_PROVEN","mechanical_strength":"NOT_PROVEN"}
MAISON1_REAL_FRONT_AND_SOUTH_WALLS_WITH_30_WINDOW_PROXY_PIECES_PASS
MAISON1_SCENE_9_3_BY_8_2_AND_ORIGINAL_1890_UNCHANGED_PASS
MAISON1_FULL_FRAGMENT_LDRAW_AND_BOM_PASS
```

Deux premières tentatives de CI ont échoué dans le générateur (seuil de candidats trop strict, puis échappement de retour ligne dans la même correction) ; la seule correction de sélection sémantique a été terminée et vérifiée. La CI spéciale du **code validé** est SUCCESS. Le commit automatique qui ajoute les fichiers générés est **`212d0261a2b2096610c0df7f90c0559ccf646cef`** ; GitHub marque ses nouveaux contrôles `action_required` faute d'exécution : ils ne sont pas annoncés SUCCESS. La CI générale du SHA source était encore **in_progress** au dernier contrôle.

## HYPOTHÈSE

C'est le **premier vrai fragment d'une façade de la maison de Ludo**, pas une ossature imaginaire. Les 61 briques de murs proviennent des vraies positions de GUIDED-004, les 30 proxies de fenêtre du vrai identifiant d'ouverture ; le plancher, l'assise 3811, la liaison d'angle et les poteaux sont des **adaptations constructives explicites**. La structure a un parcours de connecteurs démontré depuis le plancher jusqu'à l'avant-dernier raccord, mais **les deux pieds sur la base** et la véritable menuiserie restent non démontrés. Le plancher situé à environ **2,52 m** reste une **approximation (+0,12 m)** par rapport au nominal de niveau 2,40 m dérivé de la hauteur inférée ; il ne doit pas être caché ni propagé à GUIDED-004 sans accord.

## RECOMMANDATION — STOP APRÈS MAISON-1

**CONSERVER LE FRAGMENT, sans fusion.** Il montre une vraie convergence avec la Scene et fournit une recette de localisation de murs/ouvertures respectant la source. Son obstacle géométrique prioritaire est précisément l'interface des **deux pieds de poteaux avec la base 3811**, que l'outil ne reconnaît pas malgré le CONTACT maillage ; la dalle de plancher et sa cote architecturale devront également être validées avant l'extension. **Pas de MAISON-2 ouverte** : Grand-père et Ludo décident de la suite, sans achat ni essai physique.
