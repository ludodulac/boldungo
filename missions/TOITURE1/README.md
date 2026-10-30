# TOITURE-1 — premier raccord original B-3

**Trois pièces de B-3, strictement inchangées** : deux supports 3622 de
cheminée et la pente LEGO 30363 (roof-000338), sans variante ni ajout.

- `MODULE-B3-ORIGINAL.ldr` — lignes officielles originales.
- `PROVENANCE.json` — refs, commits, lignes sources exactes.
- `BOM.json` — nomenclature originale, 2×3622 + 1×30363.
- `CONNEXIONS.json`, `COLLISIONS.json`, `INSERTION.json`,
  `RESULTAT.json` — preuves géométriques mesurées par le test ciblé.
- `VIEWER-3.json` — export de présentation (proxy visuel seulement), trois
  étapes dans **la visionneuse existante** ; les transformations LDraw exactes
  sont conservées dans les métadonnées des pièces.
- `roof-mobile.png` — capture réelle Chromium, si le test réussit.

Lancer le test géométrique avec les primitives téléchargées par
`scripts/download_ldraw_probe_066.py`, puis ouvrir
`frontend/viewer.html?bundle=../missions/TOITURE1/VIEWER-3.json`
sur un serveur local desservant la racine du dépôt.

**Ne pas extrapoler** : le raccord au pied de la cheminée, la connexion
complète de la toiture, les propriétés mécaniques, l'étanchéité et le jeu
plastique LEGO ne sont pas certifiés. Les 408 pièces B-3, les 356 placements
publiés et le modèle architectural 019 restent inchangés.
