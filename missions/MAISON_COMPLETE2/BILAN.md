# BOLDÜNGO — MAISON COMPLÈTE-2 — TOIT LEGO RECONSTRUIT (PROTOTYPE)

**Réalisé sur la maison B-3 réelle de 1 904 pièces, PR #931 DRAFT.**

✅ Un **nouveau fichier de maison entière** existe : `GUIDED004-B3-STEPPED-ROOF.ldr`, soit **1792 vrais placements LEGO LDraw**. Les 1496 placements originaux hors toiture sont conservés à l'identique (murs, fenêtres, escalier, terrasses, les 44 pièces de pignon et 60 éléments de cheminée). Le fichier B-3 de départ, ses 408 pentes et `main` ne sont pas modifiés.

**Construction :** remplacement des 408 anciennes pentes 30363 sans raccordements de tenons par **296 vraies briques** 1×N et 2×N, disposées en sept rangées ascendantes de chaque côté, reliées par un faîtage de briques. Un pavage automatique découpe les pièces près des cheminées sans les traverser.

### Résultats géométriques mesurés

| Vérification nominale | Résultat |
|---|---:|
| Maison variante, pièces complètes | **1792** |
| Anciennes pièces hors toit conservées | **1496** |
| Anciennes pentes retirées uniquement de la variante | 408 |
| Nouvelles briques de couverture | **296** |
| Nouvelles briques ayant ≥2 positions de tenons mates sous elles, menant à un mur original | **296 / 296** |
| Briques de rive directement reliées à un mur | **40** |
| Briques de faîtage reliant les deux versants | **20 / 21** |
| Collisions de volumes **parallélépipédiques nominaux** nouvelles/anciennes et nouvelles/nouvelles | **0 / 0** |
| Cellules non couvertes, notamment autour des cheminées | **172 / 3600** |

**Ce résultat est un véritable changement du fichier LEGO**, pas un nouveau bilan d'étude. Le toit est maintenant relié au volume des murs par des chaînes de tenons nominales sur chaque nouvelle pièce. Les ouvertures proches des cheminées sont volontaires pour éviter les intersections avec les volumes existants.

⚠️ Ce n'est **pas encore** une maison dont la robustesse physique serait certifiée : le contrôle utilise des dimensions géométriques nominales, pas le maillage triangle complet de chaque pièce. Il ne prouve ni l'insertion continue sans obstruction, ni les efforts mécaniques, ni la tenue des assemblages, ni les raccords extérieurs hérités de B-3. La nouvelle toiture est **en escaliers**, conservant l'allure générale de double versant mais pas la surface inclinée lisse d'origine. La nomenclature est destinée au prototypage, pas à l'achat.

### Livrables et reproduction

- `GUIDED004-B3-STEPPED-ROOF.ldr` — maison complète avec toiture nouvelle, ouvrable dans les logiciels LDraw.
- `RESULTAT.json` — compteurs, couverture et endroits non remplis.
- `BOM.json` — inventaire réel des références LEGO.
- `ORDRE-TOIT-PROPOSE.json` — rangées de pose proposées, NON certifiées.
- `scripts/build_guided004_b3_stepped_roof.mjs` — constructeur reproductible, ne modifiant jamais l'original.

```bash
node scripts/build_guided004_b3_stepped_roof.mjs \
  missions/B3/generated/GUIDED004-B3-1904.ldr \
  artifacts/maison-complete2
```

**Prochaine opération utile :** visualiser le vrai fichier LDraw, contrôler les maillages et l'ordre d'insertion, puis traiter les raccordements de terrasse. On ne relance pas 369 micro-missions.

**Aucun déploiement ni fusion ; le travail reste dans PR #931 DRAFT.**
