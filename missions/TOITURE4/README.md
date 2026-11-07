# TOITURE-4 : 5 pentes 30363 raccordées au pignon de B-3

Solution EXPÉRIMENTALE **dans la PR #941** : préserve les cinq
`roof-000336`–`roof-000340`, leur poutre TOITURE-3 originale
expérimentale `3006`, et cinq placements B-3 de mur et pignon.
Deux **véritables** pièces LEGO supplémentaires sont introduites
**seulement dans la variante**, sans modification des modèles originaux :

- `3622.dat`, brique 1×3 en `(970,-864,870)`, raccordée au
  pignon existant `gable-000039` ;
- `3006.dat`, brique 2×10 en `(960,-840,760)`, support
  transversal de liaison, en-dessous de la poutre TOITURE-3 et
  vers la brique 3622, montée par dessous.

**Chemin de connecteurs attendu :**
`roof-000338` ... cinq pentes → `3006 TOITURE-3`
→ `3006 TOITURE-4` → `3622 TOITURE-4`
→ `gable-000039` → `gable-000035` → `gable-000031`
→ `gable-000026` → `wall-000707`.

Ces murs et pignons conservent **à l'identique** leurs positions dans
`missions/TOITURE3/B3-ORIGINAL-READONLY.ldr`. Le raccordement
à la base de l'édifice et la résistance mécanique ne sont **pas** certifiés.

**Fichiers**
- `MODULE-VARIANTE-PIGNON.ldr` — 13 pièces LDraw réelles, dont deux nouvelles.
- `PROVENANCE.json` — coordonnées / ID exact des 10 éléments
  sources B-3 ; transformations expérimentales.
- `BOM.json` — 5 pentes, 5 briques 3008, 2 briques 3006,
  1 brique 3622.
- `CONNEXIONS.json`, `COLLISIONS.json`, `INSERTION.json`,
  `RESULTAT.json` — **mesures ciblées** sur les nouveaux
  raccordements et leurs voisins (les acquis TOITURE-3 sont conservés).
- `VIEWER-12.json` — sous-modèle expérimental de 13 pièces,
  visualisation **schématique** dans la visionneuse existante ;
  `toiture4-mobile.png` après contrôle Chromium.

Prévisualisation locale sur serveur desservant la racine de cette
branche :
`frontend/viewer.html?bundle=../missions/TOITURE4/VIEWER-12.json`.

**Ne pas confondre** : fixation géométrique par les tenons ≠
résistance à la flexion d'une poutre longue ≠ charpente stable
≠ continuité jusqu'aux fondations.
