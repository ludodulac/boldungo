# 🧱 BOLDÜNGO — M040 : première portion réelle de rampant à DEUX RANGÉES

**Statut mesuré : prototype géométrique validé par le moteur ciblé ; pas de certification physique.**
**Branche M032/M036, PR #942 DRAFT.** HEAD de départ M036 `296ad4b489d89141c479467cfcc5e397e7b66443`. Maison B3 `missions/B3/generated/GUIDED004-B3-1904.ldr`, Git blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`, **1 904 pièces intégralement inchangées**.

## Choix final — ESSAI « CROSS_BARE » RETENU

**`TOITURE-040-RETENUE-2-RANGEES-8-PENTES.ldr`** construit le mini-rampant indépendant suivant, directement depuis les placements et matrices d'origine :
- **Huit pentes `30363.dat`** : rangée initiale `roof-000002`, `roof-000003`, `roof-000004`, `roof-000005` ; nouvelle rangée de `roof-000025`, `roof-000026`, `roof-000027`, `roof-000028`.
- **Deux pièces porteuses de mur `3008.dat`** : `wall-000699` et `wall-000715`. Les **six pièces M036 précédentes** (4 pentes + 2 murs) sont reprises **à l'identique**. **Total : 10 pièces**, dont aucune nouvelle référence ou pose inventée.
- **17 connexions nominales LDCad** reconnues directement par le moteur M031, soit les **9 déjà présentes M036** et **8 nouvelles** (2 accrochages individuels `roof-000025 → roof-000002`, `026 → 003`, `027 → 004`, `028 → 005`). Aucun de ces matches n'établit une stabilité structurelle.
- **45 couples de maillages LDraw officiels réellement vérifiés : 22 `CONTACT`, 23 `SEPARATED`, 0 `COLLISION`** renvoyé par le moteur **pour ce module seulement**. Parmi les 30 couples nouveaux : 13 `CONTACT`, 17 `SEPARATED`. Un CONTACT est une relation informatique, pas une épreuve d'insertion sous charge.

Le meilleur ordre de montage proposé, **non validé par simulation d'insertion**, est : appuis 699/715 déjà en place → pentes 002 à 005, rangée inférieure → pentes 025 à 028, nouvelle rangée. Les deux membres de mur sont des **pièces existantes** et les nouvelles pentes s'accrochent **nominalement** à celles de la première rangée. La chaîne complète de charge jusqu'au sol, l'insertion réelle de chaque pièce et la solidité de la toiture restent **inconnues**.

## Variante avec pignon — signal bloquant conservé

La proposition initiale `TOITURE-040-ESSAI-2-RANGEES-8-PENTES.ldr` (8 pentes + 3 supports, **11 pièces**, 18 snaps) inclut `gable-000001`, pièce **réellement présente** dans la maison B3. Elle a produit **23 `CONTACT`, 31 `SEPARATED`, 1 `COLLISION` moteur** (55 paires). Le signal concerne précisément **`wall-000699` ↔ `gable-000001`**, malgré quatre correspondances standards de tenons. Il n'est pas permis de considérer cette collision validée ou de supprimer/déplacer le pignon dans le modèle original. Ce **conflit de voisinage, toujours présent dans la maison entière**, doit être résolu avant toute intégration du mini-rampant.

Le modèle retenu **n'intègre pas** ce pignon dans le sous-assemblage isolé ; ce choix permet de tester la continuité entre les deux rangées, **mais ne répare pas la maison B3**. L'absence de signal de collision dans le petit sous-ensemble ne garantit donc pas l'absence de collision lors du raccord à la maison entière.

## Repli conservé

`TOITURE-040-REPLI-BANDE-8-PENTES.ldr` (pentes 002 à 009 + murs 699,715,714 ; 11 pièces) : **17 snaps**, **19 `CONTACT`, 36 `SEPARATED`, 0 `COLLISION`** sur 55 paires. C'est une extension longitudinale d'une seule bande, **non retenue** puisqu'une véritable portion de deux rangées a passé les contrôles ciblés sans collision moteur.

## Tests ciblés réellement exécutés

Run GitHub Actions **[43860733891](https://github.com/ludodulac/boldungo/actions/runs/43860733891)** : **SUCCESS**. Artefact `BOLDUNGO-M040-TOITURE-8-PENTES-NON-CERTIFIE` / **[14222619336](https://github.com/ludodulac/boldungo/actions/runs/43860733891/artifacts/14222619336)**. Contrôles :
- Reproduction effective de l'audit historique M032 : **1 904 pièces, 408 pentes, 832 connexions nominales** : **PASS**.
- Six placements M036 inchangés et 10 lignes du sous-assemblage identiques à leur entrée B3 : **PASS**.
- Huit réceptions femelles authentiques `30363` lues depuis les shadow files de **LDCadShadowLibrary@9b1131fb...**, avec profondeur 20/14/8/4, et comparées aux données indépendantes de `RELEVE-408.json` : **PASS**.
- Maillage officiel `30363.dat` et `3008.dat` (sous-dépendances incluses, pybricks/ldraw@`c43ed06...`), 3 variantes, **155 paires de maillages** analysées en tout : **PASS**. Sources externes téléchargées dans les runners, non recopiées dans le dépôt.
- Aucun changement de la maison B3, des moteurs partagés, de l'interface ni des branches des autres équipes. **Aucune fusion ni déploiement.**

## Fichiers

`TOITURE-040-RETENUE-2-RANGEES-8-PENTES.ldr` et `APERCU-040-RETENUE-2-RANGEES.svg` : réalisation retenue, 2 rangées. `BOM-040.json` : 8 × 30363 + 2 × 3008. `verify_m040.py` : source d'audit reproductible. Deux autres fichiers LDraw + aperçus : essais et alternatives conservés comme témoins techniques.

**STOP de certification** : absence de collision moteur sur les 10 pièces ≠ absence de pénétration matérielle interdite, insertion séquentielle possible, capacité portante, vérification de tous les voisins B3, ou solidité réelle. La prochaine mission doit qualifier le conflit `gable-000001` / `wall-000699` sans modifier la géométrie de la maison.
