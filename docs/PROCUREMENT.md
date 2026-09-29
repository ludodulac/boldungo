# Procurement and packed-order foundation

## Goal

Turn a finished BrickHouse construction into an exact procurement package without
making the geometric engine depend on LEGO, BrickLink, GoBricks, or any other
supplier.

The first rule is conservation:

> Every placement in the canonical `BrickModel` must appear exactly once in the
> global order manifest and exactly once in a numbered bag.

A supplier exporter may translate identifiers. It must never silently change a
quantity, omit a part, or move a part to another bag.

## Existing upstream contracts

BrickHouse already has the three inputs needed for this work:

1. `BrickModel` — one canonical placement per physical part.
2. `BillOfMaterials` — exact global aggregation of part ID, category, semantic
   color, and quantity.
3. `BagPlan` — deterministic numbered bags derived from assembly order.

`backend/brickhouse/procurement/` joins these contracts into a
`CanonicalOrderPackage`.

## CanonicalOrderPackage v0.1

The package contains:

- building and volume identity;
- total part count;
- global order lines;
- contiguous bags 1..N;
- each bag's construction phases;
- assembly-step IDs assigned to that bag;
- exact part/color quantities for that bag.

The generator rejects a package if the BagPlan does not reference exactly the
same placement IDs as the BrickModel.

## Important boundary

v0.1 is **not supplier-ready yet**.

`supplier_state = canonical_only` means the quantities and bags are exact, but
supplier part IDs and supplier color IDs have not been resolved.

This boundary is intentional. BrickHouse engine IDs such as `BRICK_2X4` remain
the source of truth for construction. Supplier identifiers are attached later.

## Next layer: verified supplier resolution

A future crosswalk must resolve, for each order line:

- canonical BrickHouse `part_id`;
- canonical/physical color selected for purchase;
- Rebrickable/LDraw identifiers used as neutral catalog bridges where useful;
- BrickLink item/color identifiers;
- LEGO Pick a Brick design/element identifiers where available;
- GoBricks / compatible-supplier SKU and color identifiers where available;
- equivalence status for alternate molds;
- validation status and provenance.

No mapping should be treated as orderable until the part **and color** have both
been verified.

## Intended user outputs

Once supplier resolution exists, the same canonical package can produce:

- a human-readable master picking list;
- a supplier-specific upload file or order-request document;
- a missing/unresolved-parts report that must be empty before declaring the order
  complete;
- one packing sheet per bag;
- bag labels such as `Sac 1 / N`, `Sac 2 / N`, etc.;
- a final reconciliation sheet proving that the sum of all packed bags equals
  the complete construction BOM.

This supports two operating modes:

1. **User orders parts** — Boldüngo gives the exact files/documents to submit to
   the chosen supplier(s).
2. **Prepared kit** — a supplier or packer receives the master order plus the bag
   manifests and returns a complete kit already split into numbered bags.

## Non-interference rule

Procurement is downstream of BrickModel, BOM, AssemblyPlan, and BagPlan. It must
not change Survey, Scene, photo reasoning, geometry, placement, or instruction
ordering merely to improve availability or price.
