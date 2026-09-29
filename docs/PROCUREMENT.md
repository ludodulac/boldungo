# Procurement and packed-order foundation

## Goal

Turn a finished BrickHouse construction into an exact procurement package without
making the geometric engine depend on LEGO, BrickLink, GoBricks, or any other
supplier.

The governing rule is conservation:

> Every placement in the canonical `BrickModel` must appear exactly once in the
> global order manifest and exactly once in a numbered bag.

A supplier exporter may translate identifiers and colors. It must never silently
change a quantity, omit a part, replace a part with an unverified equivalent, or
move a part to another bag.

## Upstream contracts reused unchanged

Procurement is downstream of existing product artifacts:

1. `BrickModel` — one canonical placement per physical part.
2. `BillOfMaterials` — global aggregation of part ID, category, semantic color,
   and quantity.
3. `AssemblyPlan` — construction ordering.
4. `BagPlan` — deterministic numbered bags derived from that ordering.
5. `BrickExportBundle` — already carries BrickModel, BOM, BagPlan and appearance.

`generate_canonical_order_package_from_bundle()` can therefore start directly
from a finished export bundle. Procurement does not create or regroup bags.

## CanonicalOrderPackage v0.1

The package contains:

- building and volume identity;
- total part count;
- global order lines;
- contiguous bags 1..N;
- each bag's construction phases;
- assembly-step IDs assigned to that bag;
- exact part/color quantities for that bag.

The package rejects:

- a BagPlan that omits a BrickModel placement;
- a BagPlan that references an unknown placement;
- non-contiguous bag numbering;
- a total quantity mismatch;
- a bag composition that differs from the global order even when the overall
  number of pieces happens to be the same.

This last check prevents a false pass such as replacing 100 required bricks A
with 100 bricks B.

## Verified part crosswalk

`data/procurement/part_crosswalk.csv` currently covers every piece promoted to
`PLACEMENT_APPROVED` by the current engine: 35 engine IDs.

The first bridge uses BrickLink catalog item numbers because they are suitable
for Wanted List XML and are also useful to compatible-brick import tools.

The crosswalk includes the current standard bricks, standard plates, supported
roof slopes, ridge tiles, and validated frame/pane window assemblies.

Mapping presence is not the same as stock availability.

## Verified purchase-color vocabulary

`data/procurement/color_crosswalk.csv` contains a first canonical physical
color vocabulary with verified BrickLink color IDs and LEGO color identities.

Architectural descriptions such as "warm stone" or "slightly darker beige" are
not silently converted to one of these colors. A purchase color must be selected
explicitly or by a future evidence-backed color policy.

## Fail-closed readiness gate

An order line is not supplier-ready until all three conditions are true:

1. **Part identity resolved** — the engine part ID has a verified external
   catalog identity.
2. **Purchase color resolved** — an explicit canonical physical color has been
   chosen.
3. **Part/color availability verified** — that exact part is known to be
   obtainable in that exact color for the intended procurement route.

A known part plus a known color is deliberately insufficient. This prevents
Boldüngo from producing a supposedly complete order containing a physically
nonexistent part/color combination.

## BrickLink documents

`backend/brickhouse/procurement/bricklink.py` generates:

- one master BrickLink Wanted List XML for the entire construction;
- one BrickLink Wanted List XML per numbered bag.

The adapter emits the required Wanted List fields:

- `ITEMTYPE=P`;
- `ITEMID`;
- `COLOR`;
- `MINQTY`.

Canonical lines that intentionally select the same physical part/color are
aggregated while preserving the total quantity.

Generation is blocked unless the readiness gate is completely clear.

## Kit-packer documents

`backend/brickhouse/procurement/packing.py` generates a human-readable document
set from the same supplier-ready package:

- one master picking CSV with Boldüngo ID, BrickLink item number, physical color,
  BrickLink color ID/name and quantity;
- one picking CSV per existing BagPlan bag;
- one printable text label per bag, e.g. `Sac 2/6`, including piece count and
  construction phase(s);
- one reconciliation CSV containing, for every physical part/color pair:
  required quantity, packed quantity and difference.

The generator refuses to return a kit document set unless every reconciliation
difference is exactly zero. The total of all bag sheets must also equal the
master part count.

## Intended user package

The finished procurement feature can therefore build toward a downloadable
folder containing:

- master human-readable picking list;
- supplier-specific upload/order file;
- unresolved/missing report, which must be empty before "ready to order";
- one packing sheet per bag;
- one supplier file per bag when useful;
- labels such as `Sac 1 / N`, `Sac 2 / N`, etc.;
- reconciliation sheet proving all bags sum exactly to the complete BOM.

Two operating modes are supported by the architecture:

1. **User orders parts** — Boldüngo gives the exact files/documents to submit to
   one or more suppliers.
2. **Prepared kit** — a supplier/packer receives the master order plus bag
   manifests and returns a complete kit already split into numbered bags.

## Compatible-brick route

Wobrick currently documents a Studio CSV import requiring:

- `BLItemNo`;
- `LdrawId`;
- `BLColorId`;
- `Qty`.

The current crosswalk already owns the BrickLink side. A later tranche must add
verified LDraw identities before generating this CSV; no guessed LDraw ID should
be emitted merely because it often resembles a BrickLink number.

GoBricks/Brickwith or another compatible supplier remains an adapter downstream
of the same canonical package.

## Remaining work

The next bounded tasks are:

1. preserve/resolve physical colors from existing Survey/Scene/Building
   appearance data without inventing colors;
2. implement a part/color availability registry or live verifier;
3. add verified LDraw identities for Wobrick-compatible CSV export;
4. package the generated strings as named downloadable files/ZIP in the product;
5. later add supplier price/stock comparison without allowing availability or
   price to mutate construction geometry.

## Non-interference rule

Procurement is downstream of BrickModel, BOM, AssemblyPlan, InstructionPlan and
BagPlan. It must not change Survey, Scene, photo reasoning, geometry, placement,
or construction order merely to improve supplier availability or price.


## Wobrick / compatible-brick export

The verified part crosswalk now stores a separate `ldraw_id` rather than
assuming BrickLink and LDraw numbers are identical. This matters for real current
parts: for example BrickLink `3068` maps to LDraw `3068b`, BrickLink `3040`
maps to `3040b`, BrickLink `3023` maps to `3023b`, and BrickLink window
glass `60603` maps to LDraw `86210`.

The color crosswalk also stores LDraw color IDs and GoBricks color numbers using
Wobrick's published cross-system color chart.

`backend/brickhouse/procurement/wobrick.py` generates the documented Studio CSV
columns:

- `BLItemNo`;
- `LdrawId`;
- `BLColorId`;
- `LDrawColorId`;
- `Qty`.

It produces one master CSV and one CSV per existing numbered bag. Generation
requires availability evidence whose route is explicitly `wobrick`; BrickLink
evidence cannot authorize a Wobrick document.

This creates a safe upload document but does not claim current stock. A separate
live-availability check is still required before Boldüngo can promise that a
single supplier can fulfill every line at that moment.
