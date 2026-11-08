# BOLDÜNGO — Mission 024 : diagnostic des intersections de toiture

**Rapport initial — le contrôle ciblé des témoins de surfaces est en attente d'exécution sur GitHub Actions.**

## Éléments vérifiés dans le rapport global M023

- Modèle : `missions/B3/generated/GUIDED004-B3-1904.ldr` (blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`).
- 1 904 placements et 408 pentes `30363.dat`.
- 1 904 / 1 904 paires spatiales contrôlées, 408 / 408 pentes couvertes.
- 209 intersections de maillages : 207 toiture/toiture (184 cas au delta LDraw (60,24,0), 23 cas (-40,0,0)), et 2 toiture/pignon ; 1 695 contacts sans connexion démontrée.
- Aucun de ces 209 croisements de maillages n'est **déjà prouvé** physiquement interdit ou admissible.

## Les trois paires représentatives

| Cas | A | B | Statut physique initial |
|---|---|---|---|
| A | `roof-000252` `30363.dat` (1210,-792,860) | `roof-000229` `30363.dat` (1270,-768,860) | **INDETERMINE** |
| B | `roof-000185` `30363.dat` (830,-960,20) | `roof-000392` `30363.dat` (790,-960,20) | **INDETERMINE** |
| C | `roof-000183` `30363.dat` (770,-936,860) | `gable-000044` `3010.dat` (800,-912,870) | **INDETERMINE** |

La pièce `30363.dat` est décrite dans la bibliothèque épinglée comme `Slope Brick 18 4 x 2`. Le détecteur de connecteurs existant ne sait inférer que les descriptions des briques et plaques classiques ; il n'identifie pas les connexions spécifiques à cette pente.

Les éventuels témoins de triangles réels seront publiés dans le **rapport d'artefact GitHub Actions**, avec un JSON détaillé. Aucune modification du modèle B3 n'est prévue.
