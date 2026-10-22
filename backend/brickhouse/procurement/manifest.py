"""Generate exact supplier-independent order manifests from BrickModel + BagPlan."""

from __future__ import annotations

from collections import Counter

from brickhouse.bricks.bags import BagPlan
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.brick_model import BrickModel

from .models import BagOrderManifest, CanonicalOrderPackage, OrderLine


def _order_lines(counter: Counter[tuple[str, str, str | None]]) -> list[OrderLine]:
    return [
        OrderLine(
            part_id=part_id,
            category=category,
            semantic_color=semantic_color,
            quantity=quantity,
        )
        for (part_id, category, semantic_color), quantity in sorted(
            counter.items(),
            key=lambda item: (item[0][1], item[0][0], item[0][2] or ""),
        )
    ]


def generate_canonical_order_package(
    model: BrickModel,
    bag_plan: BagPlan,
) -> CanonicalOrderPackage:
    """Conserve every generated part exactly once in both order and bag views.

    This is intentionally supplier-independent. A later resolver may attach
    supplier part/color identifiers and produce vendor-specific documents, but
    it must not change quantities or BagPlan membership.
    """

    if (model.building_id, model.volume_id) != (bag_plan.building_id, bag_plan.volume_id):
        raise ValueError("BrickModel and BagPlan must describe the same building volume")

    parts_by_id = {part.placement_id: part for part in model.parts}
    model_ids = set(parts_by_id)
    bag_ids = {
        placement_id
        for bag in bag_plan.bags
        for placement_id in bag.placement_ids
    }
    if bag_ids != model_ids:
        missing = sorted(model_ids - bag_ids)
        unknown = sorted(bag_ids - model_ids)
        raise ValueError(
            "BagPlan must conserve BrickModel placements exactly; "
            f"missing={missing}, unknown={unknown}"
        )
    if bag_plan.total_parts != len(model.parts):
        raise ValueError("BagPlan total_parts does not match BrickModel part count")

    bom = generate_bom(model)
    order_lines = [
        OrderLine(
            part_id=line.part_id,
            category=line.category,
            semantic_color=line.semantic_color,
            quantity=line.quantity,
        )
        for line in bom.lines
    ]

    bags: list[BagOrderManifest] = []
    for bag in bag_plan.bags:
        counter: Counter[tuple[str, str, str | None]] = Counter()
        for placement_id in bag.placement_ids:
            part = parts_by_id[placement_id]
            counter[(part.part_id, part.category, part.semantic_color)] += 1
        bags.append(
            BagOrderManifest(
                bag_number=bag.bag_number,
                phases=bag.phases,
                assembly_step_ids=bag.assembly_step_ids,
                total_parts=len(bag.placement_ids),
                lines=_order_lines(counter),
            )
        )

    return CanonicalOrderPackage(
        building_id=model.building_id,
        volume_id=model.volume_id,
        total_parts=bom.total_parts,
        unique_part_types=bom.unique_part_types,
        total_bags=bag_plan.total_bags,
        order_lines=order_lines,
        bags=bags,
    )


def generate_canonical_order_package_from_bundle(bundle) -> CanonicalOrderPackage:
    """Create a procurement package directly from a finished BrickExportBundle.

    The bundle must already contain the canonical BagPlan produced by the normal
    instruction/export pipeline. Procurement never invents or regroups bags here.
    """
    if bundle.bag_plan is None:
        raise ValueError("BrickExportBundle has no BagPlan; procurement package cannot be generated")
    return generate_canonical_order_package(bundle.brick_model, bundle.bag_plan)
