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
