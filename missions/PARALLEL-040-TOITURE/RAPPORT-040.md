# GRAND-PÈRE BOLDÜNGO — M040 : agrandir la toiture à huit pentes

## Base et fidélité
Branche `feat/boldungo-parallel-032-toiture` à partir du HEAD M036 `296ad4b489d89141c479467cfcc5e397e7b66443` ; PR #942 conserve son statut DRAFT.
Fichier original `missions/B3/generated/GUIDED004-B3-1904.ldr` : Git blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`, **1 904 pièces non modifiées**.
Chaque ligne LDraw du nouveau sous-ensemble est la **ligne originale exacte** correspondante. Les six pièces de M036 sont préservées sans déplacement.

## Deux propositions matérielles documentées — décider après le test maillage réel

**ESSAI CROISÉ (souhaité)** : `TOITURE-040-ESSAI-2-RANGEES-8-PENTES.ldr` : pentes 002–005 et 025–028 ; appuis existants `wall-000699`, `wall-000715` et `gable-000001`, 11 pièces (8 pentes, 3 supports). Les calculs du M032 prévoient **18** coïncidences LDCad : 9 dans l'ancien sous-ensemble, **8 pente–pente** nouvelles et **1 pente–pignon** nouvelle. Le pignon est aligné au-dessus de `wall-000699` par des grilles de tenons standards. Les anciennes analyses M023/M024 avertissent toutefois de possibles **signaux de collision** entre les pentes de rangées décalées en hauteur. Une coïncidence LDCad ne les absout pas.

**REPLI LONGITUDINAL (si signaux de collision croisés)** : `TOITURE-040-REPLI-BANDE-8-PENTES.ldr` : 002–009 ; supports `wall-000699`, `wall-000715`, `wall-000714`, toujours 11 pièces. **17** coïncidences LDCad (9 d'origine + 8 nouvelles) d'après M032. Cet agrandissement prolonge la longueur de la bande, sans ajouter une seconde rangée de pente.

## Protocole de décision conservateur
`verify_m040.py` relit M036 et B3, **relance M032**, confronte les sites calculés à `RELEVE-408.json`, vérifie `find_connections` avec les 8 réceptions 30363 de la vraie ShadowLibrary M031, puis **`check_collision` sur les 55 paires de chaque variante (110 paires, dont 40 nouvelles par variante)** à partir des maillages officiels LDraw épinglés. Le workflow `.github/workflows/lego2-m040-toiture.yml` téléchargera uniquement les sources tierces dans le runner. Si le moteur retourne des `COLLISION` sur l'essai croisé, le modèle de repli n'est retenu que s'il ne comporte aucun signal de collision ; sinon conserver M036.

Le journal `M040-RESULTATS-MAILLAGES.json` de l'artefact GitHub fournit la décision réellement mesurée. **`CONTACT` ne certifie pas une insertion. `COLLISION` reste un signal géométrique à qualifier, pas automatiquement une pénétration interdite.** L'ordre plausible est support de mur → éventuel pignon → pentes de rive → pentes supérieures (ou pentes 002–009 pour le repli). Il n'existe pour l'instant aucune trajectoire d'insertion continue ou preuve de stabilité sous charge.

## Nomenclature et visuels
Chaque option : 8 × `30363.dat` (couleur 1) et 3 × `3008.dat` (couleur 19). Les deux aperçus SVG sont des projections techniques **des transformations originales**, non des photographies ou des preuves d'assemblage. Aucune pièce extérieure à la maison n'a été inventée.

**STOP mécanique** : ne pas intégrer ce prototype dans le modèle original ou présenter le rampant comme supportant une charge avant qualification des collisions, ordre physique de pose, appuis jusqu'aux fondations, faîtage.
