# M033 — Charpente : premier prototype LEGO tangible

**Base :** `0f5bfe1836598f7050089c54a415123f06d33945`. Recherche lue : `missions/095/CATALOGUE-PIECES-REELLES.md`, `missions/098/VERDICT-STRUCTURE-ET-AXES.md`, `fixed_wall_roof_support_098.py`. M098 refuse à raison le pont transversal de plus de 40 tenons pour la vraie maison ; la rotation des pièces Technic 095/096 a connu un défaut d'axe. **Nous n'avons pas repris les fausses fermes aériennes.**

## Prototype construit

`CHARPENTE-APPUI-EXPERIMENTAL.ldr` contient **six pièces authentiques**, quatre briques `3003.dat` (deux colonnes 2×2 de deux rangs), une vraie traverse `3007.dat` (2×8), et la pente `30363.dat` du corpus. Deux appuis sous le 3007 sont clairement visibles. Les 4 interfaces brique/brique ou brique/traverse possèdent des recouvrements de grilles de tenons (4 studs chacune), et **8 sites LDCad femelles** de 30363 coïncident exactement avec 8 tenons du 3007, à des profondeurs 20/14/8/4 LDU. Tous les calculs et chaque pièce sont décrits dans `CONTROLES-033.json`.

**Contrôles calculés pendant cette passe :** 5 pièces rectangulaires sans intersection de leurs corps géométriques simplifiés ; 4 interfaces de grille démontrables ; 8 coïncidences nominales sur la pente ; un composant relié pour les 5 briques rectangulaires. Le **maillage réel 30363 et les frottements ne sont PAS vérifiés** ; la différence entre connexion nominale et tenue est maintenue.

## Installation dans la maison originale : STOP

Ce **gabarit de 8 tenons** n'a pas été inséré dans la maison B3. Les murs d'origine `wall-000699` et `wall-000704` présentent des appuis réels, mais les positions supérieures proposées sont déjà occupées par `gable-000001` et `gable-000005` (et d'autres pièces au voisinage). L'intégration telle quelle y provoquerait des intersections ; aucune suppression ou translation des 1 904 pièces n'est autorisée. Une charpente de pleine portée, ses deux pentes extérieures à **22°**, sa seconde assise et le blocage mécanique ne sont **pas démontrés**.

**Statut : PROTOTYPE RÉEL DE CONNECTEURS, PAS CHARPENTE DE MAISON VALIDÉE.** Ce premier assemblage prouve une méthode de liaison d'appuis et de poutre sans poutre flottante, mais ne prétend pas résoudre la structure de la maison. Aucun moteur, modèle original, workflow ou autre mission modifié.
