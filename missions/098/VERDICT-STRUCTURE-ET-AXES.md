# 🧱 BOLDÜNGO 098 — preuves de la construction expérimentale et verdict

Statut : **PAS DE FUSION AUTOMATIQUE**. La PR #927 doit être relue par GRAND-PÈRE.
Nouvelle branche directement depuis LEGO2 `7851ec4377879fface4eadd001cb42340a177479`, indépendamment de la PR #926 de 097.

## 1. Vraies sources LDraw, non interprétation des seuls noms

Le test `technic_official_axes_098.py` contient cinq références **type 1** recopiées depuis les vrais DAT publics suivants :

- `parts/32278.dat` : `beamhole.dat` à x=0, y=0, z=20 ; primitive Y conservé → axe de trou **local Y** dans la pièce.
- `parts/32524.dat` : `beamhole.dat` à z=20, matrice inversant Y → axe de trou **local −Y** (équivalent géométriquement à Y, pas X).
- `parts/32017.dat` : `beamhol2.dat` à z=20 → axe de trou **local Y**.
- `parts/2780.dat` : `confric5.dat` primitif longitudinal **Y**, sa matrice de placement en pièce transforme ce Y primitif en **local X de la broche**.
- `parts/6558.dat` : `confric5.dat` subpart de même transform, **local X de la broche**, malgré sa longueur nominale 3L.

Sources directes du miroir public LDraw (fichiers réels, pas une hypothèse) :

- https://raw.githubusercontent.com/pybricks/ldraw/master/parts/32278.dat
- https://raw.githubusercontent.com/pybricks/ldraw/master/parts/32524.dat
- https://raw.githubusercontent.com/pybricks/ldraw/master/parts/32017.dat
- https://raw.githubusercontent.com/pybricks/ldraw/master/parts/2780.dat
- https://raw.githubusercontent.com/pybricks/ldraw/master/parts/6558.dat
- https://raw.githubusercontent.com/pybricks/ldraw/master/p/confric5.dat

**Constat** : la matrice originale de `technic_triangle_095.py` met les trous sur le mauvais axe. L'intention de 097 de les corriger a bien identifié Y pour les poutres, mais sa correction qui utilise **Z pour les broches 2780 et 6558** est physiquement incorrecte dans leur DAT. Ne pas fusionner les hypothèses physiques 097 sans corriger ceci.

Le moteur 098 corrige mathématiquement toutes les rotations LDraw des poutres et broches **dans un LDraw DIAGNOSTIQUE 095/096 distinct**, y compris `096-F6-brace-7-hole`, sans modifier les archives. Les tests **font échouer les anciennes matrices**. Aligner des axes ne prouve pas l'insertion de la collerette ou la solidité.

Deuxième anomalie héritée de 095 : les `3004/3700` de remplacement de l'ancien couronnement 093 étaient dessinées au monde Y=−93×8 (niveau **dessous** de la brique). La vraie face supérieure de la brique de z=93..96 doit être Y=−96×8, soit **24 LDU plus haut**. Le module fixe 098 corrige ce placement **dans sa seule variante** et contrôle le dessous de la plaque 3020 sous Y=−96×8. Ne pas présenter les connexions à cette ancienne retile 095 comme déjà valides.

## 2. Nouveau support fixe de toiture

L'architecture principale n'hérite **ni du 097 ni des fermes Technic 095–096** ; elle utilise la fondation 093/094 et conserve la couverture à deux panneaux réels inclinés exactement à **22°**, les fenêtres et façades, et le faîtage comme expérimental.

Le moteur cherche deux colonnes réelles de tenons appartenant à un mur fondé sous CHAQUE rive. Il refait seulement deux blocs de couronnement de la nouvelle variante, avec `3004` ordinaires et vraies `3007` de 2×8. Les plaques de chaperon originales et leurs charnières restent identiques. Les pièces `3007` reposent sur les **mêmes véritables tenons du mur**, pas sur un contact visuel.

Lorsque la distance entre rives est **courte (≤ 40 studs)**, une vraie traverse de briques 2×8 est assemblée, avec une plaque `3020` 2×4 à cheval sur chaque joint entre briques. Ces interfaces sont de vrais clutches top stud→anti-stud sur grille LEGO standard.

Lorsque le span est **long (> 40 studs)**, et notamment sur la maison réelle GUIDED-004, **la longue traverse est refusée**. Un système de **DEUX petites poutres de couronnement 3007, chacune appuyée par deux colonnes de tenons sur son mur** est construit. L'espace central reste explicitement **NON SOUTENU**, aucun pont fictif. Le produit doit trouver une vraie seconde assise pour le toit (pignon, murs porteurs intérieurs, contreventements, réduction de portée) avant l'approbation.

La charnière fixe l'angle du dessin mais conserve un degré de liberté physique, de sorte que **ZÉRO panneau de toiture a deux appuis indépendants complètement prouvés**. **ZÉRO chemin N4 intégral et stable toiture→murs**. L'écran des collages n'est pas une certification N6.

## 3. Contrôles et livrables

La CI spécialisée reconstruit la maquette historique **1890**, les variantes 088/090/091, et produit :

- `BOLDUNGO-098-WALL-FIXED-TIE-AND-22DEG-ROOF.ldr` : maison complète simplifiée.
- `BRICKMODEL-098-FIXED-WALL-FOUNDATION.json` : nouvelle assise séparée des archives.
- `SOUS-ASSEMBLAGE-098-POUTRE-FIXE-ET-CHARNIERE.ldr` : vrais murs, appuis et panneau avec charnière.
- `BOM-098-FULL-EXACT.json` : nomenclature exacte, quantité couleur non attribuée, ne pas commander.
- `EVIDENCE-098-WALL-TIE-AND-BLOCKERS.json` : preuves de tenons, portées, appuis, trous et blocages.
- `AUDIT-098-OFFICIAL-LDRAW-AXES.json` et `AUDIT-098-CORRECTED-095-096-TECHNIC-AXES.ldr` : orientations corrigées des anciennes pièces, y compris F6.
- `NOTICE-098-SUPPORT-FIXE-ET-STOP.md` : ordre réel jusqu'au STOP structurel.
- `views/*.svg` : sept perspectives techniques du vrai modèle (pas de photos artificielles).

La deuxième maison de test, à largeur plus courte, utilise bien une **vraie traverse fixée entre deux murs avec ses plaques de recouvrement 3020**. Une maison sans deux colonnes de studs bien appuyés doit être refusée. Les modèles historiques ne sont ni écrasés ni fusionnés.

## 4. Décision à GRAND-PÈRE

Cette mission construit un soutien de couronnement **vraiment attaché aux murs**, mais **le verrouillage mécanique de la couverture à 22° n'est pas résolu**. Le modèle ne doit pas être vendu comme maquette entièrement assemblable.

**Suite recommandée** : choisir une assise non articulée **au faîtage et/ou sous la pente** sur des murs existants, ou alléger structurellement le toit et utiliser des appuis gables réels ; mesurer la portée du panneau. Ne pas réintroduire de fermes Technic flottantes. En cas de large portée sans supports, **changer le principe de charpente**, pas ajouter des faux raccords.

LDraw et 2D/3D geometrie N1/N2 ne certifient ni le N5 montage complet ni N6 résistance.
