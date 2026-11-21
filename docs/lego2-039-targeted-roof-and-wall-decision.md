# BOLDUNGO-LEGO2-039 — targeted construction decision

## Evidence boundary (2026-10-13)

- LEGO 21188 and 60366: official LEGO instruction landing pages exist; their inventories include part 30363. **No verified step number or supporting part** was established in this investigation.
- Eiffleman's Space Shuttle Mobile Launch Platform, *MLP-instructions-1.pdf*, 46 pages, https://bricksin.space/wp-content/uploads/2022/06/MLP-instructions-1.pdf: inventory lists **13 × 30363**, dark stone gray. Inspected page indices 12 and 28; neither demonstrates placement of 30363. No step-specific connection certified.
- No verified 30363 underside support geometry is available from those inspected pages. Previous experiments 036/037 are NOT mechanical certificates.

## Roof decision: retain architecture and defer unsupported structural assertion

**A — Preserve existing 30363 coverage:** retain 408 × 30363 and existing 11 × TILE_2X4 + 1 × TILE_2X2. Add a load-bearing standard-stud substructure ONLY after its studs and 30363 underside sockets are proven to mate; don't mark roof physically buildable on axis alignment alone. The visible silhouette is unchanged if all supports fit under existing slopes. This is a proposed method, not a verified assembly.

**B — Alternative documented standard LEGO interface:** use 3020 (2×4 plates), 3001 (2×4 bricks), and 3022 (2×2 plates) to create a stepped, stud-connected roof surface. Each new layer is placed on the studs of the preceding layer, a standard LEGO connection. This is a mechanically conventional *principle*, not a complete replacement layout: a stepped exterior would visibly differ from the current 18-degree continuous slopes. **Do not switch to this design without supervisor approval of the silhouette.**

## Independent area of GUIDED-004: front wall, below lower-left window

The real scene `frontend/data/boldungo2-guided-004-real-scene.json` describes:
- main front width **9.30 m**;
- front lower-left window offset **1.35 m**, width **1.05 m**, vertical offset **0.75 m**.

A *candidate* for standard stud-to-tube brick bonding is the uninterrupted front-wall strip **from 0 to 1.35 m** horizontally, below the lower-left window. These are scene-space meters, NOT a LEGO stud grid. Before adding bricks, the actual brick grid and neighboring openings must be read from the generated model, and an overlap/connectivity test must be run. No bricks have been added by this mission; do not call this a completed improvement.

## Construction gate

1. Extract actual generated bricks in this front-wall strip (not just the architectural source JSON).
2. Check 3001/3020/3022 stud overlap and occupancy at actual brick-grid coordinates.
3. Add only verified non-overlapping, connected bricks without moving any existing brick or changing the scene envelope.
4. Run tests, CI and compare scene/BOM before claiming improvement.

**Status: PARTIAL.** This record documents a targeted investigation and explicit choice; it is not a physical stability test or an integrated structural modification.
