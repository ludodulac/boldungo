# BOLDÜNGO — MAISON COMPLÈTE-1 — premier audit global (4 novembre 2026)

**Objectif accordé par Ludo :** partir de la maison B-3 existante de 1 904 vraies références LEGO et identifier les zones prioritaires à corriger avant toute notice. **Aucune pièce déplacée ; modèle original inchangé ; PR #931 toujours DRAFT.**

## Périmètre réellement exécuté

- Source : `missions/B3/generated/GUIDED004-B3-1904.ldr`, HEAD source `3c8c5f19f5d7c5ee6d81383bbd24dc3ea38a8003`.
- Lecture des **1 904 placements uniques** et de leurs références LDraw.
- Graphe provisoire d'emboîtements **verticaux nominaux** pour les 1496 briques et plaques orthogonales : empreintes de tenons sur grille, rotations cardinales, niveaux de briques (24 LDU) et plaques (8 LDU).
- Les **408 pentes 30363 sont expressément exclues de ce graphe** : ce contrôle ne peut pas prouver leur fixation ou leur insertion.
- Reproductibilité : `node scripts/audit_guided004_b3_fullhouse.mjs`. Résultat détaillé : `missions/MAISON_COMPLETE1/DIAGNOSTIC-NOMINAL.json`.

## Mesures de ce premier passage

| Indicateur | Mesure |
|---|---:|
| Pièces LEGO réelles dans le modèle | 1904 |
| Briques et plaques orthogonales contrôlées sur grille | 1496 |
| Pentes 30363 laissées sans validation d'assemblage | 408 |
| Interfaces verticales nominales trouvées | 2211 |
| Centres de tenons alignés sur ces interfaces | 7148 |
| Groupes du graphe nominal, hors pentes | 55 |
| Pièces sans emboîtement vertical inférieur trouvé par **ce** contrôle | 96 |
| Dont au niveau inférieur local (à traiter comme pieds potentiels) | 35 |
| Dont plus haut que ce premier niveau | 61 |

⚠️ **Ne pas interpréter ces chiffres comme 55 sous-assemblages réellement libres ou 96 pièces flottantes.** Ce graphe simplifié ne vérifie ni les maillages LDraw, ni les contacts latéraux, ni les autres familles de connexions LEGO. Les 26 composantes du contrôle historique B-3 utilisent un autre périmètre/mode de calcul : chiffres **non interchangeables**.

Principaux groupes NOMINAUX observés (hors pentes) :
- **1144 pièces** : murs, fenêtres et pignons du volume principal (graphe de tenons du contrôle).
- **181 pièces** : ensemble terrasse béton/escalier et raccords expérimentaux.
- **50 pièces** : cheminée métallique et pièces associées.
- La terrasse bois et plusieurs garde-corps restent distribués dans des groupes nominaux différents.

Le précédent bilan B-3 dans `missions/B3/RESULTATS-FINAUX-B1-B2-B3.md` donne un autre contrôle : **45 absences d'appui orthogonal immédiat, 26 composantes de graphe et 408 pentes non certifiées**. Les deux audits doivent être rapprochés **par identifiant de pièce et par définition de la règle** avant de modifier une seule brique.

## Blocages confirmés versus hypothèses

**Confirmé par anciens tests B-3 :** chaîne planche → poteau bois → pont 3001 → poteau béton **incomplètement démontrée**, deux interfaces avec signal COLLISION de maillage, absence de certification des 408 pentes, aucune insertion continue ni stabilité réelle certifiée.

**Confirmé par le nouveau relevé nominal :** toutes les 1 904 références sont présentes et uniques ; la majeure partie des murs/fenêtres/pignons appartient à un même groupe nominal ; 61 briques/plaques au-dessus du premier niveau méritent un examen précis de leurs liaisons (dont joints de faîtage, terrasses, éléments de cheminée). Ce n'est **pas** une preuve de déconnexion physique.

**Non fait :** maillage 3D exhaustif de 1 904 pièces, analyse d'ordre d'assemblage sans collision, mesures de forces/rigidité, essai LEGO réel, notice certifiée.

## Séquence de réparation proposée — une seule maison

1. **Toiture, avant toute nouvelle extension :** relier réellement les 408 pentes au volume principal en utilisant des vraies pièces et interfaces compatibles ; auditer les joints de faîtage `EXPERIMENT-088-JOINT...` et vérifier insertion/collisions sur le modèle complet. Ne pas réutiliser artificiellement la solution TOITURE-7 sur un autre modèle sans correspondance géométrique.
2. **Ensembles extérieurs :** relier et stabiliser terrasses, escalier, garde-corps et cheminées ; accepter des modules séparés sur base LEGO si une construction modulaire est volontaire et stable, ne pas inventer des poutres de bâtiment.
3. **Intégration globale :** vérifier toutes les interfaces nouvellement modifiées au vrai maillage, les collisions, la connexion ou le support du modèle retenu et un ordre d'assemblage praticable.
4. **Seulement après :** produire la notice et faire un essai humain avec vraies briques ; la simulation ne suffit pas à promettre la résistance.

**Verdict : DIAGNOSTIC INITIAL FAIT ; MAISON COMPLÈTE ASSEMBLABLE PAS ENCORE DÉMONTRÉE.** Pas de modification géométrique, pas de fusion, pas de publication.
