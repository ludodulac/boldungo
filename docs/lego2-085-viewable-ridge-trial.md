# LEGO2-085 — Visualiser le prototype LEGO dans un véritable éditeur LDraw

## Livrable concret

Une fois le pipeline GitHub CI **vert**, télécharger l'artefact **`LEGO2-085-LDraw-viewer-30-pieces-24-steps`**, qui contient uniquement des références de pièces LDraw et non les fichiers officiels redistribués.

- **`frame-24-steps.ldr`** — l'ossature de l'essai B : **24 pièces LEGO**, **24 étapes LDraw**. Ouvrir dans un éditeur compatible LDraw/BrickLink Studio. Revoir sous différents angles **avant** le montage physique. Les étapes correspondent **exactement** à celles du rapport LEGO2-084, sans remplacer le contrôle physique.
- **`roof-30-positions-NOT-CERTIFIED.ldr`** — même ossature plus **six pièces 30363** de couverture, **en jaune d'avertissement**, à des positions **expérimentales non validées**. **Ce fichier n'est pas une notice de construction** : ne jamais supposer que les six pentes sont réellement connectées ou installables.
- **`manifest.json`** — nomenclature exacte : **18× 3005, 6× 3008, 6× 30363** ; 24 éléments d'ossature et 6 pentes non validées ; toutes les identités de placements.

Les transformations sont calculées **exclusivement** par `brickhouse.bricks.geometry_adapter.brick_model_part_to_instance` et des définitions LDraw épinglées. Ce travail ne change aucun mur, toit, position, pente, quantité ou scène du projet original.

**Couleurs de la vue 3D :** le 16 LDraw des pièces de l'ossature et le jaune 14 des pentes sont des **codes de prévisualisation**, non des disponibilités commerciales ou des couleurs obligatoires.

## Utilisation

1. Ouvrir la PR dédiée et son workflow `LEGO2-085 physical trial Studio/LDraw preview`.
2. Télécharger l'artefact ZIP depuis **Actions → ce workflow → Artifacts** et l'extraire.
3. Ouvrir **`frame-24-steps.ldr`** dans un visualiseur LDraw (ou Studio).
4. Faire défiler **les 24 étapes** de l'ossature, en respectant l'ordre.
5. Ouvrir le second fichier **uniquement comme hypothèse visuelle** pour les pentes.
6. Si l'utilisateur possède les briques, monter les 24 étapes **sans forcer**, et relever stabilité, possibilités d'emboîtement, photos des jonctions.
7. Tester séparément le montage **sans forcer** des 30363 ; si elles ne s'accrochent pas aux pièces support et ne relient pas les pans, **conclure que le prototype B échoue comme solution de faîtage**, malgré sa bonne charpente nominale.

## Limites

Les contrôles informatiques constituent un **filtre de conception**, pas une preuve d'assemblage. Même le châssis de 24 pièces n'a pas été démontré stable sur une table : les potelets 1×1 sont étroits, l'ensemble exige un essai physique, et une plaque de base **non incluse dans le mini-kit** pourrait être nécessaire pour éviter le basculement. Le code ne prétend pas que cette plaque est fournie. Ne pas faire passer un succès de lecture d'un modèle LDraw pour une certification de stabilité.

**S'il faut plus de deux missions pour résoudre l'emboîtement spécifique de ces six pentes, abandonner la configuration expérimentale et sélectionner une technique alternative documentée plutôt que reprendre les audits 075–081.**

**GUIDED-004 : 1 890 pièces intouchées ; PR principale #881 et `main` inchangées ; `NOT_CERTIFIED`.**
