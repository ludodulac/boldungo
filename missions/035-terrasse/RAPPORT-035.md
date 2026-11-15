# BOLDÜNGO — Mission 035 / CONSTRUCTION 4 : TERRASSE

**État : PROTOTYPE LEGO EXPÉRIMENTAL, DRAFT — AUCUNE CERTIFICATION DE STABILITÉ.**

## Origine et limites

- Base figée : `0f5bfe1836598f7050089c54a415123f06d33945`, fichier intégral de la **vraie maison** `missions/B3/generated/GUIDED004-B3-1904.ldr` (**1 904 éléments**, dont **408 pentes 30363**). Le fichier original n'est pas modifié.
- Modèle d'architecture de référence : `frontend/data/boldungo2-guided-004-real-scene.json`. Son palier maçonné est décrit par **2,20 × 2,65 m**, sa terrasse bois principale par **2,15 × 3,75 m**, le retour par **1,45 × 1,20 m** ; ce sont des données de cette version, non des dimensions nouvellement relevées.
- Photographies documentées : vues du côté Sud, poteaux et contreventements visibles, et palier blanc, notamment `frontend/benchmarks/real-house-5/benchmark-3plus1/analyst-input/photos/LEFT_001.jpg` et `LEFT_002.jpg`. **La forme géométrique exacte du Y et ses points d'attache ne sont pas mesurés**.
- **Alerte de fidélité** : le journal `owner-spatial-topology-survey-facts-v0.1.json` confirme une marche unique et un plateau **bois plus bas que le béton**. Les niveaux des pièces B3 (`-312` LDU bois contre `-264` LDU béton, axe vertical LDraw dirigé vers le bas) paraissent dans l'autre sens. Aucune correction du modèle source n'est faite ici ; résolution nécessaire avant intégration finale.

## Pièces et construction proposées

LDraw livré : [PROTO-035-GUIDED004-Y.ldr](PROTO-035-GUIDED004-Y.ldr). Il reprend **sans réécriture de ligne de pièce** les **150 pièces des plateformes** et les **5 pièces expérimentales B2/B3** déjà présentes dans GUIDED004, puis ajoute un **Y en gradins** de **16 pièces LEGO réelles** : une 3001 (brique 2×4) de base, huit 3005 (briques 1×1) pour le fût, et sept 3004 (briques 1×2) pour la ramification. Les bras ne sont **pas des poutres en diagonale** : le Y est une interprétation en tenons, un premier essai de construction réalisable avec des références connues. Les couleurs restent indicatives.

Implantation **proposée seulement**, dans le repère LDraw de la maison : pied `(200,0,560)` LDU, sommet du fût sous la terrasse à `(200,-216,550)`, bras terminés `(160,-288,550)` et `(240,-288,550)`. Les deux terminaisons ont respectivement un recouvrement nominal de **2 tenons** avec les vrais planchers `board:00014` et `board:00026` déjà présents (briques 3007). Ce Y ajouté n'est **ni relevé par mesure photographique**, ni validé comme emplacement définitif.

## Vérifications réelles et non-vérifications

Le contrôle a utilisé la géométrie nominale AABB des pièces droites : coordonnées exactes de la maison, 20 LDU par tenon, 24 LDU par brique et 8 LDU par plaque.

| Contrôle | Résultat |
|---|---|
| Source intégrale conservée | 1 904 pièces source, aucune ligne réécrite |
| Terrasse recopiée dans le prototype | 155 pièces existantes |
| Nouveau Y | 16 pièces : 1 base + 8 fût + 7 branches |
| Nouveaux recouvrements AABB avec la maison | **0**, sur les pièces droites du catalogue |
| Nouveaux recouvrements internes au Y | **0** |
| Paires de faces avec tenons nominaux du Y | **15**, réseau connecté (centres de tenons coïncidents) |
| Interfaces nominales Y/plancher | **2**, planches `00014` et `00026` |
| Test de stabilité, tenue, assemblage manuel | **NON RÉALISÉ / NON CERTIFIÉ** |

Les pièces inclinées 30363 sont très au-dessus de cette zone et ne font pas l'objet d'un calcul maillé ; **aucune preuve d'absence globale de collisions de la maison n'est revendiquée**. Les tenons et logements sont des interfaces nominales géométriques ; aucune mesure d'emboîtement, test de résistance, maintien latéral, ancrage au terrain en pente ou corridor d'insertion n'a été effectué. L'appui au sol est une hypothèse. Le contreventement diagonal réel reste à résoudre avec des pièces articulées et connexions LDraw documentées.

Le script de vérification est [VERIFIER-035.py](VERIFIER-035.py), à exécuter depuis la racine du dépôt avec `python missions/035-terrasse/VERIFIER-035.py`. Son test ne revendique **que** le modèle AABB et les recouvrements de faces de tenons.

## Livrables

- [LDraw](PROTO-035-GUIDED004-Y.ldr) : véritable sélection de la terrasse B3 + Y construit séparément.
- [Nomenclature exacte](BOM-035.json) : référence et quantité par groupe, toutes les 171 pièces.
- [Audit reproductible](AUDIT-035.json) : coordonnées, collisions et interfaces constatées.
- [Aperçu SVG](APERCU-035.svg) : projections de la géométrie, **non photographies**.
- [Contrôles Python](VERIFIER-035.py).

## Décision à Grand-père BOLDÜNGO

**Prototype géométrique livré ; réalisation mécanique et fidélité architecturale du Y : BLOQUÉES.** Étape suivante : relever sur les photos les positions et angles du véritable support Y, corriger la relation de niveau bois/béton dans un **autre** chantier autorisé, puis chercher des charnières/axes officiels pour des bras diagonaux sans fabriquer des fixations fictives. Ni fusion, ni déploiement, ni modification du moteur.
