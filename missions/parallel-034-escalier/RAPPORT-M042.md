# 🧱 BOLDÜNGO — M042 / CONSTRUCTION 3 — raccord nominal escalier ↔ plateforme béton

## Sources immuables / règle d'isolation
- Maison B3 source authentique : `missions/B3/generated/GUIDED004-B3-1904.ldr` (1904 pièces).
- M038 : `missions/parallel-034-escalier/ESCALIER-M038-IMPLANTATION.ldr` (1126 pièces), 7+9 marches, largeur 5,5 tenons ~1,10 m.
- M034 conservée pour comparaison (485 pièces). Aucune pièce originale supprimée, déplacée, écrasée ou masquée. Moteur, toiture et terrasse non édités.
- Photo-guidage : réemploie l'audit antérieur et M038, sans **nouvelle mesure photographique** en M042.

## Constat exact dans B3 et M038
- Pièce béton d'interface : `scene-platform:south-concrete-platform:deck:00289`, **2456.dat**, centre **(220, -288, 280) LDU**, rotation 90°; deux tenons supérieurs utilisés à x=170, z=270 et 290 (y=-288).
- Arrivée haute M038 : deux pièces de chapeau `M038-01001 high cap` et `M038-01005 high cap`, sur z=350 et 370, avec deux tenons par chapeau à x=160 et x=180 (niveau y=-264).
- Écart entre les niveaux d'appui : **24 LDU (hauteur d'une brique)** ; vide horizontal entre les surfaces au même x entre **z=300 et 340 LDU** (40 LDU).

## Adaptateur neuf, 7 pièces seulement
- **2× `3794b.dat`** (jumpers 1×2 à tenon central) en **(170,-272,350)** et **(170,-272,370)**, rotation 90° : deux logements par jumper épousent les deux tenons des chapeaux M038 ; leur tenon central décale l'axe de x=160/180 à **x=170**.
- **4× `3024.dat`** (plaques 1×1) en deux piles au-dessus des jumpers, niveaux y=-280, -288, aux z=350/370.
- **1× `3666.dat`** (plaque 1×6), centre **(170,-296,320)**, direction z, venant reposer sur les deux sommets de piles et les deux tenons du béton originel ; aucune coupure/remplacement du deck.
- Références LDraw standard et authentiques : `3794b` est documentée officiellement comme jumper avec *1 centre stud* ; `3666` comme plate 1×6.
- Pièces non déplacées : la variante fusionnée contient **3037 type-1** = 1904 B3 + 1126 M038 + 7 adaptateur. La variante `ADAPTATEUR-M042-7-PIECES.ldr` ne contient que l'ajout.

## Connecteurs et collisions effectivement contrôlés
| Contrôle | Résultat |
|---|---|
| Tenons béton B3 → logements plaque-pont | **2 sites**, 1 liaison pièce-pièce `2456 → 3666` |
| Tenons 2 chapeaux M038 → logements 2 jumpers | **4 sites**, 2 liaisons |
| Tenons jumpers → piles → plaque-pont | **6 liaisons** distinctes, un seul composant |
| Collision de boîtes solides, nouvel adaptateur ↔ lui-même | **0** |
| Collision de boîtes solides, nouvel adaptateur ↔ B3 | **0** sur 1496 pièces orthogonales |
| Collision de boîtes solides, nouvel adaptateur ↔ M038 | **0** sur 1126 pièces |
| Alternative x=190 | **REJETÉE** : 11 paires de recouvrement de boîtes avec les renforts existants (dont `EXPERIMENT-B2-DECK-BRACE-1/2` et `hidden-cross-bond-029:04` en zone bois) |
| Pentes B3 | 408 pièces 30363 non maillées, éloignées de l'interface en plan |
| Tests ciblés | **22/22 PASS**, contrôles positifs, non-régression, obstacle injecté, source incomplète rejetée. Exécutés dans l'environnement JS d'évaluation; **pas de run GitHub Actions revendiqué**. |

**Portée scientifique** : les points de connexion sont calculés selon les positions nominales de tenons et logements des pièces officielles. Les boîtes sont un précontrôle conservateur d'intersection des corps orthogonaux, **pas** une résolution complète du maillage des tenons et cavités. Les logements ne sont pas lus dans un fichier shadow LDCad pour cette mission. La résistance, le serrage, la rigidité, l'ordre d'insertion, l'intégration réaliste du parapet et le relevé géométrique complet restent **NON CERTIFIÉS**.

## Livrables
- `build-stair-m042.mjs` + `test-stair-m042.mjs`, exécutables avec Node depuis le dépôt.
- `ADAPTATEUR-M042-7-PIECES.ldr` : ajout local uniquement.
- `GUIDED004-B3-ESCALIER-M042-EXPERIMENTAL.ldr` : variante complète indépendante, source incluse intégralement et sans altération.
- `APERCU-M042-LIAISON.svg` : plan comparant façade Sud, béton, bois, M038 et adaptateur.
- `NOMENCLATURE-M042.md` et `CONTROLES-M042.json` : inventaire et métriques vérifiables.
- `TESTS-M042.json` : exécution des contrôles ciblés.

**Décision :** premier raccord *nominal* obtenu entre B3 et M038, sans collision de boîtes concernant les 7 nouvelles pièces. Ne pas présenter comme un assemblage stable ou immédiatement réalisable. Ne pas fusionner ni publier ; PR #945 DRAFT.
