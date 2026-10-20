# LEGO2-078 — Vérification géométrique réelle LDraw, 4 pièces

## Périmètre strict

Reprise **sans modification de montage** de la mission 077 :
potelet `3005` (1×1), faîtage `26603` (2×3) ou `87079` (2×4),
et deux pentes `30363` dans leurs positions canoniques respectives.

La bibliothèque réduite commise dans `lego_geometry_engine/tests/fixtures/ldraw`
ne contient que le 3005, et ne saurait démontrer les collisions du faîtage.

## Reproductibilité, sans bibliothèque dans GitHub

La CI `lego2-078-real-four-piece-ldraw.yml` réutilise
`scripts/download_ldraw_probe_066.py`. Une option `--parts` permet
de ne récupérer **que les quatre racines 3005, 26603, 30363, 87079
et leurs références LDraw transitives**, depuis le miroir public LDraw
à la révision **c43ed06a128a10ed65675166bf42eb6fd608b9b0**.
Limite explicite : 240 fichiers. Téléchargement seulement dans
`/tmp/lego2-078-ldraw`, aucun `.dat` ajouté au dépôt.

Le runner recharge les quatre définitions et vérifie qu'elles produisent
des triangles réellement triangulés. Toute référence manquante est
signalée par `FileNotFoundError` ; aucun maillage n'est fabriqué pour
combler une dépendance absente.

Le script `scripts/probe_ridge_full_ldraw_078.py` construit deux
architectures tests de la mission 077, appelle son contrôleur inchangé,
et vérifie sur chacune :

- les **six** interactions entre les quatre placements simultanés ;
- les positions d'insertion de la tuile à `+3, +2, +1, 0` plaques,
  avec les trois autres pièces conservées dans leurs positions initiales ;
- le signalement de toute collision `COLLISION`, contact `CONTACT`
  ou séparation `SEPARATED` LDraw ;
- la non-mutation du modèle, le statut **NOT_CERTIFIED** et les
  pièces officielles effectivement chargées.

Les preuves reproductibles sont archivées par la CI sous le nom
`lego2-078-real-four-piece-mesh-report`. Si la fermeture LDraw ne
peut pas être obtenue, la CI échoue et le blocage est documenté :
cela **ne valide pas** une absence de collision.

## Résultat réel vérifié sur la CI #39488668480

La CI sur `cdeb837d0d4559ed68bf81f7f2b5d6329052026f` a réellement
téléchargé **27 fichiers** LDraw, transitive incluses, depuis le miroir
épinglé. Les quatre pièces se sont chargées avec surfaces triangulées :

| Pièce | Triangles |
|---|---:|
| 3005 (potelet 1×1) | 76 |
| 26603 (tuile 2×3) | 236 |
| 30363 (versant) | 700 |
| 87079 (tuile 2×4) | 332 |

Sur **chacune des deux orientations**, les six paires simultanées ont
été évaluées avec de vraies surfaces LDraw (aucune géométrie manquante).
Le résultat précis a été **identique pour les deux orientations** :

| Couple de pièces | Relation LDraw |
|---|---|
| 1×1 / couvre-faîtage | CONTACT |
| 1×1 / versant négatif | **COLLISION** |
| 1×1 / versant positif | **COLLISION** |
| couvre-faîtage / versant négatif | CONTACT |
| couvre-faîtage / versant positif | CONTACT |
| versant négatif / versant positif | **COLLISION** |

Les quatre positions de l'insertion discrète du couvre-faîtage ont
également été calculées pour les trois pièces immobiles : *complétude
des maillages vérifiée* ; cela ne démontre PAS un chemin d'assemblage
continu. **Les collisions impliquant le potelet et les deux versants,
ainsi que la collision entre les versants, sont le blocage réel qui
doit être examiné avec les volumes de tenons/tubes.**

La méthode de maillage ne reconnaît pas automatiquement l'interférence
légale d'un tenon dans une cavité LEGO. Pour cette raison, le résultat
est **REVIEW_REQUIRED**, et non une conclusion mécanique INVALID ni VALID.
Aucun correctif non démontré n'est ajouté et aucun versant n'est déplacé.

## Distinction des verdicts

- **VALID sur une vérification précise** : les six paires disposent
  de résultats de triangulation réelle, et non des résultats UNKNOWN.
  Il s'agit d'un **contrôle géométrique exécuté**, pas d'un certificat
  de connexion LEGO.
- **INVALID sur une géométrie** : conflit de position matériellement
  démontré. Le moteur `_pair` ne fournit qu'un `COLLISION`
  exigeant encore une analyse de tenons/tubes pour distinguer
  interférence volontaire de traversée impossible.
- **UNKNOWN sur la mécanique** : force de serrage, emboîtement
  simultané à trois points, insertion continue et ordre de montage
  des pentes, déformation des pièces, rigidité et fondations.

Les tests ordinaires ne prétendent pas contenir les pièces officielles.
La CI à téléchargement borné fournit le contrôle 3D exigé.

**Aucune modification du modèle GUIDED-004 (1 890 pièces) ;
toiture, pente, appuis, `main` et PR #881 inchangés.
Certification : NOT_CERTIFIED.**
