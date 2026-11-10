# BOLDÜNGO — MISSION 024 — DIAGNOSTIC DES INTERSECTIONS DE TOITURE

**État : contrôle ciblé réellement exécuté, 3/3 paires. Verdict physique des trois cas : INDETERMINE.**
Exécution unique : https://github.com/ludodulac/boldungo/actions/runs/42530188204
Source inchangée : `missions/B3/generated/GUIDED004-B3-1904.ldr` (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`).
Bibliothèque réelle : `pybricks/ldraw` à la révision `c43ed06a128a10ed65675166bf42eb6fd608b9b0` : **23 fichiers téléchargés** pour les deux familles 30363 et 3010 et leurs dépendances.
Moteur réutilisé : `LDrawLibrary`, `check_collision`, `find_connections` et la fonction existante `_tri_intersection_kind`; aucun moteur nouveau.

## 1. Vérification du rapport global M023

Artefact global : https://github.com/ludodulac/boldungo/actions/runs/42526253312
- 1 904 paires candidates effectivement examinées sur 1 904 ; 408 pentes sur 408 intégralement couvertes au niveau des paires candidates.
- **209 résultats `COLLISION`** du moteur : **207 toiture/toiture**, **2 toiture/pignon**.
- Parmi les 207 : **184** paires avec translation ordonnée (+60,+24,0) LDU, **23** avec (-40,0,0) LDU.
- **1 695 contacts** sans connecteur compatible reconnu ; aucun emboîtement admissible démontré.
- Aucune paire candidate oubliée. `COLLISION` signifie *signal à analyser*, pas preuve à lui seul d'une pénétration matérielle interdite.

## 2. Trois cas : géométries, surfaces, interprétation

### A — `roof-000252` / `roof-000229` (184 configurations analogues)

- `roof-000252`, `30363.dat` : origine (1210,-792,860) LDU.
- `roof-000229`, `30363.dat` : origine (1270,-768,860) LDU.
- **Orientation identique** des deux pièces : rotations LDraw `[0,0,-1 ; 0,1,0 ; 1,0,0]`. Écart ordonné (+60,+24,0) LDU.
- Boîtes réelles des maillages : A [(1200,-796,840)–(1280,-768,880)] et B [(1260,-772,840)–(1340,-744,880)]. Leur recouvrement est un **indice spatial seulement**.
- Moteur : **`COLLISION`** ; **0 témoin** trouvé de triangles *non coplanaires* se traversant ; **0 connecteur** reconnu.
- Le moteur traite aussi les points considérés « à l'intérieur » d'un maillage ; en l'absence de témoin de surfaces croisées et de provenance des faces solides, cette indication ne prouve pas une traversée matérielle réelle.
- **Verdict physique : C — INDETERMINE.** Cause probable : juxtaposition longitudinale répétée de pentes décalées verticalement d'une hauteur de brique, avec contact ou recouvrement nominal à examiner. Ni emboîtement admissible ni pénétration interdite démontrés.
- Correction de principe, **non autorisée à ce stade** : qualifier la zone de contact et la géométrie intérieure réelle de la pente, avant toute décision sur les rangées.

### B — `roof-000185` / `roof-000392` (23 configurations analogues)

- `roof-000185`, `30363.dat` : origine (830,-960,20) LDU ; rotation `[0,0,1 ; 0,1,0 ; -1,0,0]`.
- `roof-000392`, `30363.dat` : origine (790,-960,20) LDU ; rotation `[0,0,-1 ; 0,1,0 ; 1,0,0]`.
- **Orientation opposée**, même altitude ; écart (-40,0,0) LDU. Boîtes A [(760,-964,0)–(840,-936,40)] et B [(780,-964,0)–(860,-936,40)].
- Moteur : **`COLLISION`**, et cette fois **4 couples de triangles réellement croisés**, non coplanaires, identifiés par le détecteur existant ; **0 connecteur** reconnu.
- Exemple de témoin exact : triangle A n°0 aux sommets (820,-953.333,14), (822.2962,-936.001,14.4566), (822.2962,-953.333,14.4566) ; triangle B n°601 aux sommets (800,-956,36), (848,-940,4), (800,-956,4). Normales unitaires : A (0.195032,0,-0.980797), B (-0.316228,0.948683,0). Les **quatre témoins complets** figurent dans l'artefact JSON M024.
- **Verdict physique : C — INDETERMINE, risque de collision plus sérieux.** Contrairement à A, une intersection effective des *surfaces triangulées* est constatée. Il faut encore qualifier les triangles comme corps plein, tenon ou logement et tester un raccord LEGO admissible avant de prononcer une pénétration interdite. Cause probable : rapprochement frontal des deux rampants opposés au faîtage.
- Correction de principe, **non autorisée à ce stade** : inspecter le raccord exact du faîtage et les volumes de matière/liaisons sans inventer de nouvelle pente.

### C — `roof-000183` / `gable-000044` (l'une des 2 jonctions pignon signalées)

- `roof-000183`, `30363.dat` : origine (770,-936,860) LDU ; rotation `[0,0,1 ; 0,1,0 ; -1,0,0]`.
- `gable-000044`, `3010.dat` (brique 1×4) : origine (800,-912,870) LDU ; rotation identité.
- Écart (+30,+24,+10) LDU. Boîtes A [(700,-940,840)–(780,-912,880)] et B [(760,-916,860)–(840,-888,880)].
- Moteur : **`COLLISION`**, **0 témoin** de triangles non coplanaires se traversant ; A possède 0 connecteur inféré, B en possède 8, **0 connecteur compatible entre eux**.
- L'absence de témoin direct malgré le verdict `COLLISION` indique qu'une vérification du test « point dans maillage » et de la surface exacte de la jonction est indispensable. La boîte englobante ne prouve pas le chevauchement matériel.
- **Verdict physique : C — INDETERMINE.** Cause probable : zone de jonction entre couverture inclinée et dessus du pignon, sans preuve d'un joint accepté ni d'un corps solide traversé.
- Correction de principe, **non autorisée à ce stade** : confirmer les surfaces et le détail architectural de l'appui ; ne déplacer ni toit ni pignon à partir de ce seul indicateur.

## 3. Pourquoi les connecteurs `30363.dat` ne sont pas reconnus

La pièce réelle porte la description `Slope Brick 18  4 x  2` (18°). Le moteur `lego_geometry_engine/src/lego_geometry_engine/library.py` infère les connecteurs à partir de motifs `Brick N x M` ou `Plate N x M` avec leurs faces canoniques. Ce motif ne s'applique pas à la pente `Slope Brick 18 4 x 2` : la bibliothèque rapporte **0 connecteur pour `30363.dat` (700 triangles)**, contre **8 pour `3010.dat` (364 triangles)**.
Ainsi, **0 connexion reconnue ne signifie pas absence de connexion réelle**, et ne permet pas non plus de considérer une intersection comme admissible.

## 4. Portée des répétitions et limites

- Les positions et rotations répétées suggèrent que les 184 cas A et 23 cas B sont générés par deux configurations de toiture systématiques. Le diagnostic d'un **seul représentant** de chaque classe n'établit toutefois pas l'identité physique de toutes les paires ni leur caractère constructible.
- Le rapport global contient **2** jonctions toiture/pignon ; **une seule** a été détaillée ici.
- Le moteur `check_collision` comporte une recherche d'intersections de triangles **et** un test de point dans le maillage. Pour A/C, le résultat `COLLISION` ne s'accompagne d'aucun témoin de surfaces non coplanaires croisées dans la vérification ciblée. Cela reste **à valider géométriquement**, sans désactiver aucun contrôle.
- **Aucun des 209 cas n'est certifié « collision matérielle interdite » ou « emboîtement admissible ».** La preuve de connexion, l'insertion et la stabilité ne sont **PAS ÉTABLIES**.
- Aucun élément du modèle B3, du moteur, des pignons, des terrasses ou des photographies n'a été modifié.

## Artefacts de preuve
- Exécution M024 : https://github.com/ludodulac/boldungo/actions/runs/42530188204
- Artefact `BOLDUNGO-M024-THREE-ROOF-INTERFACES-NOT-CERTIFIED` : rapport Markdown détaillé + `DIAGNOSTIC-TRIANGLES-M024.json` avec les quatre témoins de surfaces.
