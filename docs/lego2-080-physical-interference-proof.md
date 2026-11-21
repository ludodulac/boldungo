# LEGO2-080 — Une collision triangulaire occupe-t-elle réellement la matière ?

## Périmètre : les trois collisions déjà localisées en 079

Aucun calcul des 24 témoins triangulaires de la mission 079 n'est répété.
Les trois couples et leurs positions existantes, issus des missions 076–079,
sont repris exactement : **3005 ↔ 30363 négatif**, **3005 ↔ 30363
positif**, **30363 négatif ↔ 30363 positif**. Les deux orientations
restent celles de 079 ; la tuile de faîtage ne change pas.

La bibliothèque LDraw est téléchargée par le système existant
(`scripts/download_ldraw_probe_066.py`) à la **révision épinglée**,
uniquement pour les quatre pièces 3005, 26603, 30363 et 87079 et leurs
dépendances. Elle est conservée dans `/tmp` du runner, pas dans GitHub.

## Nouvelle preuve de volume (et ses limites)

La fonction `inspect_solid_shell` examine chaque maillage réel, **sans
reparcourir les croisements entre les deux pièces**. Elle vérifie si
chaque arête triangulaire possède exactement deux faces adjacentes
d'orientations opposées, sans dégénérescence ni volume signé nul.

Cette condition de **surface fermée et orientée** est nécessaire avant
d'utiliser des rayons pour déduire un intérieur et un extérieur. Une
géométrie LDraw présentant des ouvertures, des raccords T, des faces
internes, des maillages doubles ou des coutures inconsistantes ne doit
**jamais** être traitée naïvement comme un volume de plastique plein.

Si les deux maillages satisfont ce contrôle, un petit réseau borné de
points situés dans leur intersection de boîtes englobantes est testé
avec trois directions de rayons. Un éventuel point dans les deux
intérieurs est **une preuve géométrique locale uniquement**, non une
preuve de matière LEGO rigide incompatible. Un résultat négatif du
réseau limité ne signifie pas que les solides ne s'interpénètrent pas.

Le véritable embrayage LEGO exige aussi de connaître **l'identité des
surfaces** (tenon, tube, paroi, corps de pente), les déformations
autorisées, les jeux et la trajectoire d'assemblage. Ces informations
ne sont pas codées dans les maillages triangulés du moteur utilisé.
L'absence de connecteurs officiels reconnus en 079 n'est pas la preuve
qu'aucun montage LEGO n'est physiquement possible.

## Résultat des vrais maillages LDraw — CI spécialisée #39574318401

Le contrôle de volume a été **exécuté avec succès**, sans refaire les
24 localisations de la mission 079. Les fichiers LDraw officiels épinglés
présentent les anomalies de fermeture suivantes, dans **les deux orientations** :

| Pièce | Nombre d'arêtes de maillage à une seule face | Conclusion sur la coque |
|---|---:|---|
| Potelet **3005** | **16** | Pas de coque orientée fermée démontrée |
| Chacun des deux versants **30363** | **192** | Pas de coque orientée fermée démontrée |

Ces comptes concernent des arêtes de **triangles LDraw**, et **ne
signifient pas nécessairement des trous physiques dans les briques**.
Les écarts peuvent venir d'ouvertures réelles, de coutures de primitives,
de raccords en T ou d'une représentation de surface non-manifold à
examiner. La fermeture requise pour prouver l'appartenance intérieure
d'un point n'a **pas** été démontrée.

| Collision | État de preuve d'occupation commune de matière | Verdict |
|---|---|---|
| Potelet 3005 ↔ versant gauche 30363 | **UNKNOWN** : 16 et 192 arêtes ouvertes dans les maillages | **UNKNOWN** |
| Potelet 3005 ↔ versant droit 30363 | **UNKNOWN** : 16 et 192 arêtes ouvertes dans les maillages | **UNKNOWN** |
| Versant gauche ↔ versant droit | **UNKNOWN** : 192 arêtes ouvertes sur chacun | **UNKNOWN** |

Cela constitue une **limite de preuve identifiée et vérifiée**, pas une
nouvelle répétition de la détection des collisions. Un croisement de
surfaces triangulées est toujours établi par 079, mais l'occupation
simultanée de volumes fermés de matière LEGO **n'est pas prouvable avec
ces maillages bruts**. Il manque aussi l'origine des faces (tenon,
tube, paroi) et les règles précises d'interférence/serrage physique.

Le test logiciel reste prudent : aucun verdict `INVALID` n'est
inventé faute de preuve volumique robuste, aucun `VALID` n'est
attribué faute de preuve de connexion mécanique.

### Règle de verdict

- **VALID**, réservé à une connexion matériellement documentée,
  jamais attribué sur la seule base de triangles ou rayons.
- **INVALID**, réservé à une occupation contradictoire de matière
  **non assimilable à un emboîtement LEGO autorisé**, avec provenance
  des surfaces et tolérances suffisamment prouvées.
- **UNKNOWN**, dès que la fermeture du maillage, l'occupation intérieure
  ou la distinction paroi/tenon/tube reste incertaine.

Le rapport `artifacts/lego2-080/material-interference-three-pairs.json`
enregistre par paire **le nombre d'arêtes ouvertes, les arêtes
non-manifold, les défauts d'orientation, l'état de preuve d'un volume,
les éventuels témoins intérieurs et le verdict physique justifié**.

Le workflow `lego2-080-ridge-material-review.yml` vérifie les trois
couples avec des maillages LDraw réels et archive uniquement ce JSON.
Des tests synthétiques sur des volumes fermés, ouverts et mal orientés
valident la séparation entre **preuve géométrique** et **certificat LEGO**.

**GUIDED-004 : 1 890 pièces intactes. Aucun versant, faîtage, pente
ou appui modifié. Main et PR #881 inchangées.**

**État général : NOT_CERTIFIED.**
