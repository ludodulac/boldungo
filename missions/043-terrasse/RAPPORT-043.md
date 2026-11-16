# 🧱 BOLDÜNGO — CONSTRUCTION 4 / M043 TERRASSE

**HEAD d'entrée vérifié :** `6bd708b8a04a444ff3d4bddb07a60f581d4ff9ea`, branche `feat/boldungo-parallel-035-terrasse`; PR #944 reste **DRAFT**. Sources B3 (**1 904 pièces**) et M035 (**171**) et M039 (**164**) sont archivées inchangées.

## 12 paires signalées : classification, pas de suppression silencieuse

Les 12 paires du fichier `missions/039-terrasse/AUDIT-039.json` sont de **véritables superpositions AABB dans la variante M039 recomposée avec les éléments de la maison non remplacés**, et non des faux positifs dus à la comparaison avec l'ancien bois non déposé. Deux paires concernent le béton présent même dans l'isolat M039 ; dix concernent murs ou raccords préservés dans B3 et absents du seul fichier isolé. Aucune des 12 ne doit être ignorée.

Le nouveau prototype conserve le principe certain du propriétaire : **le bois est plus bas que le béton**. Niveaux top béton `-288 LDU` et bois `-264 LDU`, marche de `24 LDU` **uniquement hypothétique**, pas une mesure. LDraw vertical croît vers le bas.

## Correction matérielle dans la copie (pas B3)

- **7 pièces de garde-corps** sont repositionnées localement : trois lisses, quatre montants ; toutes leurs coordonnées avant/après figurent dans `AUDIT-043.json`.
- Les **4 anciennes lames superposées** du retour bois (`board:00001/00003/00005/00007`) sont **recalepinées en 3 bandes 3007 de 2×8**, côte à côte : x=[90,250] LDU, z=[720,760], [760,800], [800,840] LDU. L'ancienne `board:00007` disparaît **de cette copie uniquement**, mais sa fonction de surface est reprise par le nouveau calepinage. La portion encastrée à tort dans `wall-000248` n'est plus dessinée en bois. **Cette emprise nouvelle, les lisses et les positions de montants nécessitent validation photo/métrique.**
- Aucune pièce des murs, du béton, de l'escalier, du toit, du moteur partagé ou des raccords `guided004-031` retenus n'est modifiée. La maquette est **recomposée en entier** depuis la source B3, en retirant de la copie uniquement l'ancien bois déjà déplacé par M039 et l'ancien pontage expérimental B3 incompatible avec la marche.
- **Y Technic M039 conservé à l'identique : 16 nouvelles pièces**, dont deux poutres inclinées 32524, trois broches 6558, trois briques à trou 3700, huit contacts nominaux des parties orthogonales et trois sites de trous coaxiaux selon les axes M098. Les 7 projections sur les anciennes planches restent **ambiguës** et ne démontrent pas de fixation indépendante.

## Collisions, dans les limites de l'algorithme utilisé

| Périmètre | M039 | M043 | Verdict |
|---|---:|---:|---|
| Paires signalées dans AUDIT-039 | 12 | **0** | **12 corrigées** |
| Bois déplacé vs toutes les pièces B3 conservées (orthogonal) | 12 | **0** | **0 ignorée** |
| Superpositions internes AABB du prototype isolé | 78 | **70** | 70 restent |
| Superpositions AABB dans la maison recomposée | 223 | **205** | **18 de moins, 0 nouvelle** |
| Source B3 historique (référence seule) | 230 | — | Déjà en conflit |
 
**Les 205 paires AABB restantes sont conservées dans le rapport : elles empêchent de conclure à une maquette physiquement assemblable.** Aucun maillage complet des 408 pentes 30363, des deux poutres 32524 ni des trois broches 6558, aucun jeu d'emboîtement, aucune trajectoire d'insertion ni descente de charges n'est certifié. Une absence de **nouvelles** collisions AABB ne suffit pas à prouver une absence de collisions physiques.

## Fichiers

- `PROTO-043-TERRASSE-Y-RECALE.ldr` : terrasse isolée **163 pièces** (46 béton + 101 bois/reprises + 16 Y).
- `GUIDED004-B3-EXPERIMENTAL-M043.ldr` : modèle maison complète **1 912 pièces**, variante **non officielle**, sans modifier B3.
- `BOM-043.json` : nomenclature exacte de l'isolat et de la maison entière.
- `AUDIT-043.json` : 12 paires traitées, positions avant/après, niveaux, limites et résultats globaux.
- `APERCU-043.svg` : vue du palier, du Y et du retour recalepiné.
- `VERIFIER-043.py` : tests reproductibles, comparant B3 / M039 / M043 et les axes M098, sans toucher au moteur.
- `.github/workflows/boldungo-terrasse-043.yml` : CI ciblée propre à cette branche.

**Décision : la M043 règle les 12 conflits spécifiquement signalés par M039, sans en créer d'autres au périmètre orthogonal ; 205 AABB subsistent dans la maison complète, stabilité et fidélité photographique restent NON CERTIFIÉES. Ne pas fusionner.**
