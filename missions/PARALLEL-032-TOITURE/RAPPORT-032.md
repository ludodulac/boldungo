# BOLDÜNGO — M032 — recensement de 408 pentes 30363

Base immuable : `0f5bfe1836598f7050089c54a415123f06d33945`. Toutes les transformations sont lues dans `missions/B3/generated/GUIDED004-B3-1904.ldr` (**1 904 instances, 408 pentes**). Le relevé détaillé de **chaque pente et de ses 8 logements** est dans `RELEVE-408.json`. Aucune pièce de B3 déplacée.

## Résultat calculé (census de coordonnées, pas test de maillage)

| Mesure | Résultat |
|---|---:|
| Pentes inspectées / identifiants uniques | 408 / 408 |
| Couples nominaux logement/tenon (y compris pentes voisines) | **832** |
| Couples entre deux pentes 30363 | **720** |
| Couples pente / tenon de brique ou plaque rectangulaire | **112** |
| Pentes avec au moins une correspondance à une brique/plaquette ordinaire | **60** |
| Pentes sans aucune correspondance | **4** |

Les quatre pentes sans match sont `roof-000001`, `roof-000023`, `roof-000208`, `roof-000230`. La distribution des pentes selon les correspondances est `{"0":4,"1":1,"2":385,"3":16,"5":1,"8":1}`. Types hôtes des 112 correspondances ordinaires : `{"3008.dat":93,"30363.dat":720,"3004.dat":4,"3009.dat":2,"3007.dat":2,"3010.dat":2,"3002.dat":6,"3622.dat":3}` (voir détails JSON). Pour `roof-000048`, trois coïncidences : une avec `gable-000006` (3004, femelle profondeur 20) et deux avec `roof-000025` (profondeur 4). La correspondance 3004 déjà vérifiée par M031 reste située à **(470, −792, 50)** LDU.

### Portée de la preuve

Les huit logements femelles et leurs profondeurs 20/14/8/4 LDU viennent des méta-données authentiques LDCad M031. Les deux tenons de pente viennent de M026. Pour les 17 références rectangulaires courantes, ce recensement projette les grilles de tenons nominaux et suppose leur plan supérieur **Y local = 0**, règle reproduite par le moteur pour les pièces classiques ; **ce passage n'a pas chargé ni exécuté le moteur 3D avec la bibliothèque externe complète**, sauf preuve déjà obtenue en M031 pour la paire `3004`. Les 832 sont donc des **coïncidences nominales candidates** et ne doivent pas être annoncées comme 832 interfaces physiques certifiées. Les couples comptent des sites, pas des pièces supportées indépendamment.

**Collisions non résolues :** M023 avait signalé **209** événements moteur sur la toiture, dont **207 entre pentes** et **2 pente/pignon**. M024 a établi **4 paires de triangles qui se croisent** sur un exemple de faîtage ; les autres catégories restent indéterminées. Le présent recensement ne réexécute **aucun** contrôle de triangle, ne requalifie **aucun** de ces avertissements, et n'affirme donc **zéro collision**. Aucun des 832 snaps ne doit servir à effacer un `COLLISION`.

**Prototype réel :** `PAIR-ROOF48-GABLE6.ldr` contient exactement les deux pièces originales et leurs placements B3, une pente 30363 et une brique 3004. Un tenon est aligné avec une réception LDCad documentée ; **le deuxième tenon 3004 reste libre**, et le montage n'est ni autorisé à la vente ni certifié pour l'insertion, la tenue, ou les collisions.

### Contrôles

- Calcul exécuté sur la version GitHub de B3 avec entiers LDU ; assertions : **1 904 pièces, 408 identifiants de pentes uniques, 832 coïncidences, 112 coïncidences ordinaires, 4 pentes sans match** : PASS (audit déterministe en session).
- `audit_032.py` reproduit le calcul sans bibliothèque externe ; **son exécution en GitHub Actions ou dans un environnement Python n'a pas été effectuée ici**.
- Test sur les **maillages LDraw complets** et insertion continue : **NON EXÉCUTÉ**.
- Références de licence externes : LDCadShadowLibrary `9b1131fb...` CC BY-SA 4.0, attribution Roland Melkert et contributeurs ; aucun fichier tiers recopié.

**Décision :** avancer sur une simulation d'insertion et sur les signaux de collision M023/M024 avant d'affirmer un assemblage physique de la couverture.
