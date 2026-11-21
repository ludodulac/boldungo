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

## Résultats réels — six collisions localisées

Le workflow spécialisé GitHub #39491345200 est **SUCCESS**. Les trois
collisions déjà constatées en 078 ont été reproduites pour les deux
orientations avec les **vraies surfaces LDraw** du même miroir épinglé.

Chaque zone ci-dessous correspond à l'**enveloppe des 24 premiers
témoins de croisement strict de triangles** (non à l'intégralité du
volume d'intersection). Les coordonnées sont celles de la maquette :
XY en tenons, H en plaques.

| Orientation | Paire de pièces | Zone XY (tenons) ; H (plaques) | Nature démontrée | Verdict |
|---|---|---|---|---|
| 0 · faîtage 26603 | 1×1 ↔ versant gauche | X 40–41 ; Y 0–1 ; H **117–120** | Croisement des surfaces du corps supérieur du potelet / proximité du plan de tenon et du versant | **UNKNOWN** |
| 0 · faîtage 26603 | 1×1 ↔ versant droit | X 40–41 ; Y 0,2–1 ; H **117–120** | Même type de croisement, autre pente | **UNKNOWN** |
| 0 · faîtage 26603 | versant gauche ↔ droit | X 41–41,3 ; Y 0,7–1,212 ; H **117,5–119,167** | Croisement des surfaces des deux versants vers leur bord supérieur de faîtage | **UNKNOWN** |
| 1 · faîtage 87079 | 1×1 ↔ versant gauche | X 14–15 ; Y 3–4 ; H **93–96** | Corps supérieur potelet / surface du versant | **UNKNOWN** |
| 1 · faîtage 87079 | 1×1 ↔ versant droit | X 14–15 ; Y 3–4 ; H **93–96** | Corps supérieur potelet / surface du versant | **UNKNOWN** |
| 1 · faîtage 87079 | versant gauche ↔ droit | X 14,788–15,3 ; Y 5–5,3 ; H **93,5–95,167** | Croisement des surfaces des deux versants près de l'arête de faîtage | **UNKNOWN** |

**Preuve commune** : 24 croisements stricts de triangles enregistrés par
paire, sur les triangles géométriques LDraw réels. Le moteur ne renvoie
**aucun connecteur documenté (`find_connections=0`)** sur ces trois
paires, dans chacune des deux orientations. Les positions connues des
tenons supérieurs ne sont pas identiques entre potelet et versants.
Aucun indice ne permet donc de requalifier une de ces collisions en
« emboîtement LEGO normal » **VALID**.

Mais ces informations ne prouvent pas non plus **INVALID** au sens de
« montage physiquement impossible » : les faces triangulées ne disent
pas à quel sous-composant elles appartiennent (tenon, tube, paroi,
volume incliné) et les interférences d'assemblage voulues ne sont pas
modélisées par une loi de déformation. Une enveloppe de triangles croisés
n'est PAS une preuve d'intersection rigide non détachable.

Le rapport source contient, pour chacun des six couples, les témoins
LDU, leurs coordonnées, les limites d'échantillonnage, le test des
connecteurs, le verdict et le caractère `NOT_CERTIFIED`.

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
