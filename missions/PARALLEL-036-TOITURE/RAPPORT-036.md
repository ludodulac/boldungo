# 🧱 BOLDÜNGO — MISSION 036 — première tranche de toiture réelle

Base M032 : `af22f6be74a1069e32e4c0f693cf2e7f0e595b47` (PR #942, rester en DRAFT). Source originale B3 inchangée, blob `288c60fde76918128d8b955f78ebfa9afc2dfe8e`. Ce dossier **n'ajoute aucune pièce** à la maison de 1 904 éléments.

## Assemblage géométriquement fidèle, restreint à six pièces

Quatre pentes contiguës : `roof-000002`, `roof-000003`, `roof-000004`, `roof-000005`, toutes `30363.dat`. Deux vrais membres de mur existants : `wall-000699`, `wall-000715`, tous deux `3008.dat`. Les six lignes LDraw `1 ...` de `TOITURE-036-4-PENTES-6-PIECES.ldr` sont **recopiées sans modification** de B3. Le support `wall-000699` possède **2** points de jonction nominaux avec `roof-000002`. Le support `wall-000715` possède **7** points avec les quatre pentes (1+2+2+2).

## Interfaces : 9 nominales, 23 logements inférieurs non engagés

Les **32** réceptions de la bibliothèque *LDCadShadowLibrary* M031 (8 pour chaque pente) sont contrôlées ; **9** coïncident avec des tenons d'origine des deux 3008 et respectent l'axe de connexion, d'après le relevé M032. Ces correspondances constituent des **snap nominaux** et ne démontrent aucune résistance sous charge. Tous les détails des 9 sites et les six matrices sont dans `RELEVE-036.json`.

## Préfiltre de collision séparé

Sur les **15 paires de pièces** du mini-ensemble : **5** boîtes englobantes se chevauchent (corps de tenons inclus), **4** se touchent sur leur frontière, **6** sont séparées. Les **5 chevauchements ne sont pas des collisions de matière certifiées** et peuvent être l'emboîtement attendu ; cependant aucune de ces interfaces n'est blanchie arbitrairement. Leur contrôle par triangle et maillage véritable doit être confirmé par le job ciblé GitHub Actions `BOLDUNGO M036 toiture`, dont le script `verify_m036.py` relance **directement `audit_032.py`**, le moteur existant `find_connections` sur la vraie bibliothèque externe M031, puis `check_collision` sur les **15** paires. L'existence du job ne prouve pas son succès : consulter les journaux et l'artefact `RESULTATS-036-ENGINE.json`.

## Fichiers

- `TOITURE-036-4-PENTES-6-PIECES.ldr` : vrai petit sous-ensemble, **6 références réelles** et positions B3 exactes ; pas de nouvelles fixations.
- `APERCU-036.svg` : projection schématique des positions LDraw, non rendu de maillage.
- `BOM-036.json` : 4×30363 + 2×3008 ; quantités expérimentales, **pas une commande d'achat**.
- `RELEVE-036.json` et `verify_m036.py` : preuves, contrôles reproductibles.

## Bloqueurs (STOP)

Les supports proviennent des murs existants mais leur **chaîne structurelle complète jusqu'au sol** n'est pas démontrée dans ce module limité. La toiture à deux pans de la maison, l'insertion séquentielle, l'absence d'interférence matérielle et la tenue mécanique ne sont **pas certifiées**. La couverture historique en pentes 30363 présente des surfaces étagées et n'est pas validée comme un toit parfaitement plan de 22°.
