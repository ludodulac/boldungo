# LEGO2-082 — Première décision « connecteurs avant placement »

## Pourquoi ce changement

Les missions 075–080 ont mis en évidence un problème de méthode : on place un assemblage de faîtage, puis on inspecte à répétition ses collisions. La mission 082 ajoute un **filtre de conception conservateur avant implantation** ; elle ne recommence pas l'audit volumique des trois collisions. Le sujet 081/PR #909 sur les maillages reste indépendant.

## Code utilisable

`brickhouse.bricks.connector_first_design_082.describe_interfaces(part)` retourne un profil **typé** :
- `TOP_STUD` pour la grille orthogonale nominale, ou, pour **30363**, exactement deux tenons exposés selon la conversion des primitives LDraw déjà revue dans `lego30363_mechanics_034.top_studs`. Les orientations/positions ne sont **pas** recalculées par une nouvelle formule.
- `TUBE_AXIS` pour les **deux axes sous 26603** identifiés par `ridge_tile_upper_interface_073`. Un axe de tube est une frontière de cellules, **pas** un troisième tenon ni la preuve d'un serrage.
- `UNDERSIDE_ENVELOPE` et `BEARING_PROJECTION` pour la projection des pièces orthogonales ; ce sont des **enveloppes**, jamais un emboîtement, un support porteur ou un maillage de matière validé.
- `CLIP` est un type prévu, mais **aucun connecteur clip n'est autorisé** sans géométrie et technique validées.

Chaque site possède sa position en **studs et plaques**, sa direction, une direction d'insertion **candidate**, une preuve et une provenance. Une direction candidate ne certifie pas une trajectoire continue. Les connecteurs des pentes autres que la famille 18°, les sous-faces 30363 et l'accroche mécanique 26603 restent **non approuvés**.

`screen_connector_first_candidate(parts, required_connections)` applique **avant placement** :
1. Rejet des **volumes de tenons superposés** sur une même cellule XYZ, avec identification des propriétaires.
2. Consultation exclusive du contrôle existant `connectors.validate_connection` pour chaque paire **explicitement demandée**. Seul `VALID` au sens restreint du contrôleur ouvre la porte à une étude supérieure ; `INVALID` ou `UNKNOWN` donnent une **décision de conception REJECTED**, pas une nouvelle enquête.
3. Rejet s'il n'existe aucun plan de connexions.
4. Limite explicite de 50 pièces et 100 paires pour garder des expériences bornées.

Le statut `ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS` signifie **géométrie nominale de connexion revue uniquement**. Il ne signifie **jamais** « construction valide ». La géométrie du corps hors connecteurs, les chaînes de charges, les séquences continues d'insertion et la rigidité restent des barrières séparées avant toute décision physique.

## Décision concrète

| Montage expérimental | Décision du filtre |
|---|---|
| 3005 (1×1) sous 3002 (2×3), cellule alignée | `ELIGIBLE_FOR_FURTHER_DESIGN_CHECKS` (connexion nominale existante) |
| Deux tenons de pièces distinctes au même XYZ | `REJECTED_DUPLICATE_STUD_MATERIAL` |
| 3002 sous 26603 | `REJECTED_UNDOCUMENTED_INTERFACE` (la mission 073 ne certifie pas l'accroche) |
| 3005 sous 30363 | `REJECTED_UNDOCUMENTED_INTERFACE` |
| Pente 33° sans connecteurs documentés | Pas de connexion de conception approuvée |

Ces cas **ne changent aucune pièce canonique**. Le GUIDED-004 de 1 890 pièces reste `NOT_CERTIFIED`.

## Suite — décision et borne anti-tunnel

Le prochain lot **expérimental, sans changement du modèle canonique**, doit proposer trois **techniques de charpente distinctes** en réutilisant ce filtre : (1) versants sur fermes indépendantes, (2) liaison par plaques/relais documentés, (3) sous-assemblages de versants installés séparément puis réunis. Chaque option doit produire un schéma de connexions, les blocages explicites, une séquence et un mini-BOM ; celles sans interfaces approuvées sont **écartées**, pas « à auditer de nouveau ». Le choix d'une option pour **environ 30 pièces à tester physiquement** exige une nomenclature vérifiée, sans inventer de résultats de tenue mécanique.

**Aucune réparation de maillage, aucune fusion vers `main`, aucun changement du GUIDED-004.**
