# BOLDÜNGO — M040 : huit pentes, deux véritables rangées LEGO (provisoire avant contrôle final)

Base M036 HEAD initial : `296ad4b489d89141c479467cfcc5e397e7b66443`. Fichier B3 d'origine : blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`, 1 904 pièces inchangées. M036 six pièces conservées rigoureusement dans les nouveaux sous-assemblages.

## Premier essai de 2 rangées : collision dans les pièces de support, pas entre pentes
Le run de contrôle [M040 GitHub Actions #43859979725](https://github.com/ludodulac/boldungo/actions/runs/43859979725) a testé deux options de 11 pièces :
- **CROSS** (pentes 002–005 et 025–028, murs 699/715 + pignon 001) : **18** snaps LDCad, **23 CONTACT**, **31 SEPARATED**, **1 COLLISION moteur** sur 55 paires : **`wall-000699` ↔ `gable-000001`**, bien qu'ils aient 4 correspondances ordinaires de tenons. Ce contact est suspendu : pas de validation mécanique, aucun retrait de ce pignon du modèle réel.
- **LONG** (8 pentes 002–009, murs 699/715/714) : **17** snaps LDCad, **19 CONTACT**, **36 SEPARATED**, **0 COLLISION moteur** sur 55 paires. Une bande étroite alternative, 11 pièces.

**NOUVELLE PROPOSITION M040 — CROSS_BARE** : conserver les mêmes **deux rangées** de pentes 002–005 et 025–028, mais **ne pas inclure `gable-000001` dans le module expérimental**. Conserver exactement les **deux vrais éléments de murs M036**, `wall-000699` et `wall-000715` : **8 pentes + 2 supports = 10 pièces**. Les 4 pentes de la rangée supérieure possèdent chacune 2 matches nominaux sur les tenons de la pente inférieure ; soit **17 snaps LDCad** au total (9 M036 + 8 nouvelles). Les **45 paires** du nouveau sous-ensemble sont soumises au contrôle dédié `verify_m040.py` avant toute conclusion. Le problème de la jonction `wall-000699` / `gable-000001`, toujours existante dans la maison B3, demeure un **obstacle externe** à l'intégration complète.

## Livrables et limites
- `TOITURE-040-RETENUE-2-RANGEES-8-PENTES.ldr` et `APERCU-040-RETENUE-2-RANGEES.svg` : dix lignes LDraw copiées de B3 et projection géométrique.
- `TOITURE-040-ESSAI-2-RANGEES-8-PENTES.ldr` : variant à 11 pièces **non retenu** (1 signal COLLISION sur la jonction support/pignon).
- `TOITURE-040-REPLI-BANDE-8-PENTES.ldr` : alternative prudemment vérifiée.
- `BOM-040.json`, `verify_m040.py`, run ciblé et artefact : matrices, noms originaux, tests M032, LDCad M031 et maillages triangulés véritables.

**Ordre seulement plausible** : les deux murs existants, puis les quatre pentes de rive dans l'ordre 002→005, puis les quatre pentes de rangée suivante dans l'ordre 025→028. Ne constitue PAS une simulation d'insertion réelle, ni une preuve de stabilité, ni un raccord complet aux fondations. Aucun changement de B3, du moteur ou des autres missions.
