# LEGO2-081 — Intégrité de l'importation LDraw des pièces 3005 et 30363

## Objectif ciblé

La mission 080 observait **16 arêtes non appariées** pour la brique
**3005**, et **192** pour chacune des deux pentes **30363**. Le problème
n'est ni un besoin de nouvelles pièces ni une invitation à ajouter des
surfaces inventées : il faut séparer (1) le traitement des sources par
l'importateur et (2) la géométrie **effectivement décrite** par LDraw.

Les fichiers source de la bibliothèque officielle épinglée utilisés
depuis 066 sont :
- `parts/3005.dat`, `parts/s/3005s01.dat` et leurs primitives ;
- `parts/30363.dat`, `parts/s/30363s01.dat` et leurs primitives.

Un constat direct : la sous-pièce `30363s01.dat` contient
**`0 BFC CERTIFY CW`**. Le moteur traitait avant 081 cette orientation
comme `CCW`, et omettait la correction de winding lors de l'emploi
de matrices de sous-pièces inversées (déterminant négatif). C'est un
**défaut réel d'interprétation des faces**, sans perte automatique de
triangles. La brique 3005 et la sous-pièce 30363 font également appel
à `BFC INVERTNEXT` pour signaler les surfaces à inverser.

### Correction du moteur existant

`LDrawLibrary._expand` reconnaît maintenant les commandes
`BFC CERTIFY CW/CCW`, leurs changements de winding, `INVERTNEXT`,
et la réflexion géométrique des références type 1. Les inversions
s'accumulent au fil de l'arbre de sous-pièces, sans reclasser les faces
ou ajouter de nouveaux triangles.

La correction suit la spécification LDraw.org
**Back Face Culling (BFC) Language Extension** :
https://www.ldraw.org/article/415.html

L'importateur ne réalise **aucune opération de bouchage de trous**.

### Une seule vérification reproductible de l'origine des ouvertures

`scripts/check_ldraw_source_integrity_081.py` examine seulement 3005
et 30363. Il reconstruit **indépendamment** le nombre de faces
référencées par les lignes LDraw `3` et `4` (un quad vaut deux
triangles), en suivant récursivement les sous-pièces. Il compare ce
nombre aux triangles effectivement chargés par le moteur, compte les
fichiers CW et les commandes INVERTNEXT, puis vérifie la fermeture
de la surface triangulée avec le contrôle existant de la mission 080.

Une égalité des nombres de triangles **écarte une perte globale de
faces LDraw 3/4 pendant l'import** ; elle ne constitue **pas** une preuve
de maillage fermé. Les primitives LDraw comme `box4t.dat` (quatre
faces adjacentes) et `box5.dat` (cinq faces) peuvent représenter des
**surfaces partielles par conception** ; un parent peut les compléter
avec d'autres faces. Certaines coutures non jointes ou raccords en T
peuvent rester malgré l'importation de toutes les faces documentées.

L'étape 081 **ne prétend pas** démontrer des trous dans la matière
physique LEGO à partir d'arêtes ouvertes d'un maillage de rendu.

En cas de correction de winding, les **trois paires originales de
collisions** sont recalculées, et rien d'autre, sans refaire les
localisations de 079 ni les diagnostics globaux.

## Preuve chiffrée CI (workflow spécialisé #39591860050)

La vérification officielle, limitée à 3005 et 30363, **a réussi** :

| Pièce | Triangles exacts attendus depuis les lignes source 3/4 | Triangles réellement importés | Arêtes toujours non jointes après la correction BFC |
|---|---:|---:|---:|
| 3005 | 76 | 76 | **16** |
| 30363 | 700 | 700 | **192** |

La sous-pièce du 30363 contient **un fichier CW** et la fermeture de
ses dépendances comporte **13 commandes BFC INVERTNEXT**. Le 3005 comporte
**une** commande INVERTNEXT. La correction traite ces règles de winding
et aucune face LDraw 3/4 n'est perdue à l'importation. Le nombre d'arêtes
ouvertes ne change **pas** : l'origine des limites de fermeture est donc
dans la **description/tessellation LDraw non étanche dans sa forme
actuelle**, et non dans une omission de triangles pendant l'expansion.

Il ne faut toutefois pas assimiler ces arêtes non appariées à des trous
de plastique : raccords en T et primitives à faces volontairement
partielles peuvent ne pas donner un maillage étanche dans le moteur,
même avec toutes les surfaces importées. Le script d'import n'effectue
aucune soudure, remaillage ni bouchage.

Les **trois contrôles de collisions existants**, seuls réexécutés après
la correction, renvoient encore `COLLISION` pour **chacune des deux
orientations**. Les six verdicts matériels restent **UNKNOWN**.

**Conclusion 081 : une erreur d'orientation BFC était avérée et a été
corrigée ; elle n'était pas responsable de la perte des 16/192 arêtes.
Le blocage volumique est celui d'une représentation de surface non
étanche même lorsque toutes les faces officielles ont été comptées.
Pas de nouvelle série d'audits.**

### Décision et suite physique indispensable

- Si toutes les faces source sont présentes, mais les coques restent
  ouvertes, la **limitation provient de la représentation des
  surfaces triangulées** plutôt que d'une face type 3/4 perdue par le
  moteur. Ne pas refermer automatiquement ces surfaces : leur couture
  physique et le rôle de chaque surface nécessitent des preuves.
- Si des faces source sont absentes, la CI doit échouer et la cause
  d'importation doit être corrigée avant tout verdict.
- Pour démontrer l'impossibilité ou la validité d'un assemblage réel,
  il faudrait une **géométrie volumique étanche et fiable** des zones
  de contact (idéalement une CAO/tessellation de fabrication ou une
  vérification réelle des pièces 3005 et 30363), avec tolérances,
  emboîtements autorisés et zones de déformation identifiées.

**GUIDED-004 : 1 890 pièces inchangées.** Aucune toiture,
pente ou structure modifiée. La stabilité mécanique reste
`NOT_CERTIFIED`.
