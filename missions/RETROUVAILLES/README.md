# RETROUVAILLES — GUIDED-004 house, no rebuilding or merging

## Chosen visual reference
**[Existing 019 JSON](../../frontend/data/boldungo2-lego-house-019.json)**: 2,852 *visual model parts*, 930 wall segments, 104 gable elements, 13 roof elements (12 slopes, 1 ridge), lower stair 7 and upper stair 9 plus landing, 2 timber decks and concrete platform, columns, rails, openings, gutters, chimney and terrain. Contains 1,549 terrain/base elements and 2,262 non-canonical catalog IDs; geometry for many shapes is visually approximate/fictitious. DO NOT market as 2,852 verified physical LEGO bricks or as buildable. This retains detailed prior architectural **appearance** with a visually approximate roof; documented Scene roof pitch ~22° is inferred, not experimentally proven by model.

## Compared existing alternatives (NO mixing)
- GUIDED-004 canonical pipeline **1,890** placements: physical part catalog, 408 official `30363` slopes approximating 21.8° overall; roof, openings, stairs, terraced supports and platforms conserved, but many physical connections not certified.
- PR #931 B-1/B-2/B-3: most developed real-LEGO variant **B-3 1,904 pieces**, source `missions/B3/generated/GUIDED004-B3-1904.ldr`. 408 official inclined roof pieces; supports/terraces improved; 45 orthogonal parts without recognized immediate bearing, 26 graph components, 10/12 chain link checks recognized on one interface. Not mechanically certified, not a richer visual architectural composition than JSON 019.
- PR #937 **356** exact positions of limited RDC; no roof, stairs, terraces or west face. Export `frontend/data/guided004-maison4-356-brickhouse.json`.

**These models do not share a guaranteed compatible coordinate scale. NEVER append geometry from one to another.**

## Simple reuse of existing software
Existing `frontend/viewer.html` + `frontend/viewer.js` unchanged except **two link labels/buttons**; homepage `frontend/index.html` gets two buttons for model selection. Direct local/same-origin links:
- `viewer.html?bundle=./data/boldungo2-lego-house-019.json` — **Voir ma maison complète** (2,852 visual components, full visible house).
- `viewer.html?bundle=./data/guided004-maison4-356-brickhouse.json` — **Construction LEGO — 356 pièces**.

On unmerged branch, only code prepared, production unchanged. On the live viewer, if the 019 data is deployed on same origin, it can be loaded by direct URL; otherwise download existing 019 JSON via GitHub and use the existing **Ouvrir un export JSON**. A real Chromium desktop+touch Android simulated test is in `tests/frontend/test_retrouvailles_019_browser.py`.

**No manufacturing certification. No new architecture or engine. No Scene or main changes.**
