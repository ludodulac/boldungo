# VISIONNEUSE-1 — GUIDED-004, MAISON-4, 356 placements

LDraw source **immutable**: `missions/MAISON4/generated/MAISON4-MURS-RDC-COMPLETS.ldr` at `f3c596aa03a5159953ad548bc5c6d4a8cdb6066c`.

Existing BrickHouse viewer: `frontend/viewer.html`, `frontend/viewer.js`. No new rendering engine.

Exact lossless adapter output: `frontend/data/guided004-maison4-356-brickhouse.json`. It preserves **all 356 original physical LDraw references**, colors, original XYZ coordinates and 3×3 orientation matrices in each placement; BrickHouse grid placement is derived by the inverse of `backend/brickhouse/bricks/geometry_adapter.py`: 20 LDU/stud, 8 LDU/plate, rotation `(3+turn)%4`. Nominal dimensions are mapped from verified canonical LDraw part mappings, including existing experimental baseplate 3811 and supports. No invented, moved or dropped physical pieces.

A transparent colored LDraw 3005 *proxy* is displayed as a solid colored 1×1 brick, **not** as fabricated manufactured glazing. Prior experimental baseplate at plate -1 preserved: viewer-only bundle, not promised as Pydantic-valid production BrickModel.

**Important architectural gap**: facade OUEST/back lacks any canonical wall parts; it must remain visibly open. SUD/left and NORD/right source coverage complete. Physical insertion, strength, mechanical certification NOT PROVEN.

When deployed to same-origin frontend, the existing viewer can open:
`viewer.html?bundle=./data/guided004-maison4-356-brickhouse.json`
or click the added simple link “Voir notre maison LEGO — 356 pièces” in `viewer.html`.

**While DRAFT only (no production deployment)**: download the JSON via GitHub repository and use **Ouvrir un export JSON** in the **already deployed** existing viewer. Its built-in import, drag-to-orbit, touch pinch/zoom, and front/back/left/right buttons need no modification.

Targeted browser proof: `tests/frontend/test_maison4_356_real_browser.py` in a single PR GitHub Action with Chromium screenshots. No modification to main, canonical Scene or former PR.
