# BOLDÜNGO — MISSION OUVERTURES 046 (modèle visuel 019)

**Base HEAD :** `cd1b4ad71dd877317d709f60a3a205de39e5d440` — PR #943 en DRAFT. La correction porte exclusivement sur les pièces portant `opening_id` : `right_glass_blocks`, `front_glazed_door`, `left_french_door`. Les **2 811 autres placements**, y compris les pignons et la terrasse bois, sont byte-pour-byte inchangés lorsqu'on les sérialise ; test sentinelle dans `audit_046.mjs`.

## A — Briques de verre côté droit
- Conserve les 30 cases existantes (6 × 5, confirmé dans la scène GUIDED004), repositionnées sur la grille : **y 23…28**, **z 9, 12, 15, 18, 21** en trois plaques par rang.
- Ajoute un appui inférieur `BRICK_1X6` de **z6 à z9**, et un linteau supérieur `BRICK_1X6` de **z24 à z27**, dans l'ouverture uniquement.
- Corrige le rendu des cellules **sur cette ouverture uniquement** : briques translucides 0,70 stud de profondeur, 0,96 stud de largeur le long de la façade, joints visuels fins de 0,04 stud. Le corps de verre est donc continu verticalement contre ses deux assises : pas de jour de 0,6 plaque entre rangs.

## B — Porte-fenêtre façade avant
- Le haut existant `BRICK_10X1` de **z24 à z25** laissait **2 plaques vides** avant la maçonnerie, qui commence à z27.
- Remplacement local par **deux vraies briques normalisées dans le corpus**, `BRICK_6X1` (x45…51) + `BRICK_4X1` (x51…55), toutes deux de **z24 à z27**. Les jambages existants sont raccourcis de z25 à z24 pour rejoindre proprement le nouveau linteau.

## C — Porte vitrée côté terrasse
- Le plan vitré `PANE_1X7X8` historique était un proxy de visualisation rendu comme une petite lame de **0,12 stud** le long de la façade (mauvaise orientation du volume dans la visionneuse).
- Correction ciblée du rendu : **vraie face visuelle translucide étendue le long des 7 tenons de l'ouverture**, épaisseur virtuelle 0,12, toujours en retrait dans l'embrasure ; profondeur de retrait maintenue, ni terrasse ni murs déplacés.
- Pour une lecture de **deux vantaux**, ajoute deux jambages intérieurs et un montant central formés de **24 vrais volumes de briques 1 × 1** (`BRICK_1X1`, 3 colonnes de 8 briques). Ces briques sont des références déjà présentes. Les liaisons mécaniques entre ces briques et le vitrage proxy ne sont **pas** certifiées.

## Vérifications et limites
- `audit_046.mjs` : 3 zones, 30 cellules A, 2 assises A, 2 briques B, 24 briques C, nomenclature recalculée, sentinelle des 2 811 placements non ciblés. `node --check frontend/viewer.js`.
- **Réussite visuelle géométrique, pas certification LEGO** : les `PANE_*` et `BRICK_1X1X8` historiques du modèle **019** sont des **proxies de prévisualisation**, pas des composants LDraw manufacturables démontrés. Aucun moteur physique, conversion du modèle B3, aucune collision maillage ou insertion complète n'est certifiée. Pour une notice d'assemblage réel, remplacer ces proxies par des ensembles éprouvés du catalogue (par exemple 60592/60601, 60593/60602) après nouvelle mesure des huisseries.
- `APERCU-046.svg` est une **coupe orthographique schématique**, non une capture WebGL validée sur appareils.

**Statut : les 3 ouvertures sont corrigées dans la prévisualisation 019 et séparément auditables. La maison B3 originale, pignons, charpente, terrasse bois et autres équipes restent intacts. Ne pas fusionner ni publier.**
