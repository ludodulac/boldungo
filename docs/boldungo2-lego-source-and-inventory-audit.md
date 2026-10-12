# BOLDÜNGO LEGO2 — source-of-truth and inventory audit (2026-10-12)

## Verified sources
- Drive `01 — MÉMOIRE VIVANTE — BOLDÜNGO LEGO2`: latest user-confirmed front width **9.30 m**, South approximately **8.20 m**, stair **7 + landing + 9**, north sidewalk **continuous slope**.
- Drive `00 — Vérité guidée des façades` is older and states **10.0 m**. **Superseded by 9.30 m.** Do not copy the obsolete measurement.
- Earlier visual exports 015–019 are **NOT physically buildable/certified**. The 019 catalog-only audit found 2262 part IDs outside the project's limited orthogonal catalog, 582 canonical IDs with noncanonical geometry, 8 matching geometries. An ID absent from this internal catalog is **not proof that LEGO never manufactured the part**.
- Existing production contracts: `brick_model.py`, `catalog.py`, `assembly.py`, BOM/instruction pipeline. Reuse them; no parallel house pipeline.
- The 12-part opening wall and 17-part solid wall are **engineering fixtures only**, not house facade modules and not a verified shopping list.

## Distinguish three different inventories
1. **Canonical engine catalog:** IDs known to the software, not a list of every genuine LEGO part.
2. **Model BOM:** pieces required by a particular design, not proof they can be purchased.
3. **Owned/available physical stock:** quantities, colors, condition and supplier identifiers actually held or confirmed available. **Not yet verified from the available records.** Never assume that the engine catalog or the fixture BOM is the user's stock.

Before selecting pieces for the house, reconcile each part against real supplier/LEGO/BrickLink identifiers, color availability, dimensions and the confirmed owned-stock ledger, if any. Unknown stock must be marked UNKNOWN, not zero and not available.

## Physical LEGO design standards reviewed
Official BrickLink Studio / Designer Program documentation:
- https://www.bricklink.com/v3/designer-program/guidelines.page?guideline=6
- https://studiohelp.bricklink.com/hc/en-us/articles/6501498505111-Stability-check
- https://studiohelp.bricklink.com/hc/en-us/articles/6481651047319-Connect

Connections are **not** equivalent to collision-free AABBs. Studio Connect does not check collisions. Stability checks are conservative; strength and insertion may still need physical testing. Bridging seams and overlapping bricks matter. A single stud contact is not sufficient evidence of structural reliability.

## Stop/go gates
1. Architectural truth: the latest neutral topology, photo evidence, and **HUMAN PASS** of actual house geometry before any house-specific LEGO conversion. Unknown roof angle stays UNKNOWN.
2. Catalog: verified real parts and dimensions, not merely strings matching a regex.
3. Geometry: exact solids + connector compatibility + collision checks, including angled roof and sloping sidewalk.
4. Assembly: connection graph, support, insertion order/path and stability; disconnected ground islands fail.
5. Outputs: only after all gates may the project issue a **certified** notice, purchase BOM, or promise physical buildability.

The experimental orthogonal preflight checks only a subset of these gates. Its output must never be labeled FULL PHYSICAL PASS.

## Architectural constraints that must survive conversion
- EAST front, WEST rear, NORTH right, SOUTH left.
- South from EAST to WEST: wood terrace → concrete platform → exterior stair; the stair upper flight rises toward EAST.
- Concrete platform is elevated with **open void underneath**, not solid.
- Wood terrace has diagonal return, railings, Y bracing; deep recessed double door.
- North sidewalk and curb climb continuously, **never staircase**.
- Zinc gabled roof; actual pitch unknown. Only house-owned chimneys.
- The separate lavoir is not to be artificially attached to the building.

## Scope / next evidence
No confirmed owned-stock quantities or full BrickLink part-number mapping have been identified in the sources reviewed here. Locate the authoritative inventory file before making an availability claim. Do not auto-merge unvalidated geometry into the existing viewer or benchmark pipeline.
