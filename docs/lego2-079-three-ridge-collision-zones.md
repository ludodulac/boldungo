# LEGO2-079 — Nature des trois collisions du faîtage

## Portée et preuve

Cette mission conserve **exactement** les positions étudiées aux missions
076–078 : potelet LEGO **3005**, deux versants LEGO **30363**, et
couvre-faîtage **26603** ou **87079** suivant l'orientation.
**Aucune pièce de GUIDED-004 (1 890 pièces) n'est modifiée.**

La mission 078 a déjà établi trois relations de maillage `COLLISION` :
potelet–versant négatif, potelet–versant positif et versant–versant.

Le nouveau script `scripts/diagnose_ridge_collision_surfaces_079.py`
ne recherche pas de solution alternative. Il récupère l'exacte bibliothèque
LDraw épinglée par le téléchargeur existant 066/078 : **3005, 26603, 30363,
87079 et leurs seules dépendances**, temporairement dans `/tmp`.
Les fichiers `.dat` ne sont pas ajoutés dans GitHub.

Pour chacune des trois paires, le script :
- reconstruit les deux maillages dans les mêmes coordonnées que la mission 078 ;
- reconfirme `COLLISION` avec `check_collision` ;
- parcourt les triangles avec le moteur existant `_tri_intersection_kind`,
  enregistrant au maximum 24 **témoins de croisement strict de surfaces**
  et la zone XYZ associée en LDraw (LDU) et en coordonnées de la maquette ;
- rapporte la présence ou l'absence de connecteurs **effectivement
  documentés dans le moteur** et les cellules de tenons officielles
  recouvrantes si elles sont connues ;
- distingue une zone proche du tenon supérieur du potelet
  d'une zone impliquant son corps, avec une incertitude explicite.

### Limite de classification

Les triangles LDraw aplatis ne conservent pas systématiquement la
**provenance de chaque face** (tenon, tube, jupe, pente ou paroi).
Le contrôle des connecteurs du moteur n'est pas un certificat de
serrage, et un contact/croisement triangulaire isolé ne prouve pas
à lui seul une interférence rigide empêchant l'assemblage.

En conséquence, **une collision de triangle n'est pas reclassée
automatiquement en connexion valide**, ni en impossibilité matérielle.
Le verdict final reste `UNKNOWN` lorsque les preuves de provenance
géométrique et d'emboîtement sont insuffisantes.

### Résultats et témoins reproductibles

Le workflow GitHub
`.github/workflows/lego2-079-ridge-collision-surfaces.yml`
génère le rapport JSON
`artifacts/lego2-079/ridge-three-collision-zones.json`
sous l'artifact `lego2-079-three-ridge-collision-zones`.
Ce rapport contient un tableau pour les **deux orientations** et les
**trois intersections**, avec les limites de calcul consignées.

Un résultat technique de localisation n'autorise **aucune correction de
structure**. Les deux versants, leur pente, l'appui et la tuile
demeurent inchangés. La stabilité et la résistance restent
**NOT_CERTIFIED**.
