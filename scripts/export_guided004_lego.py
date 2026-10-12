"""Execute the existing BrickHouse pipeline against the actual GUIDED-004 house.

This is a reproducible export/inventory job, not a mechanical certificate.
"""
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.bom import generate_bom
from brickhouse.bricks.assembly import generate_assembly_plan
from brickhouse.bricks.instructions import generate_instruction_plan
from brickhouse.bricks.bags import generate_bag_plan
from scripts.repair_guided004_overlaps import repair_orthogonal_overlaps
from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene import ArchitecturalScene

SOURCE = Path("frontend/data/boldungo2-guided-004-real-scene.json")
OUTPUT = Path("artifacts/lego2-guided-004")
ORTHOGONAL = standard_orthogonal_definitions()


def generate():
    scene = ArchitecturalScene.model_validate_json(SOURCE.read_text(encoding="utf-8"))
    bundle = run_partial_scene_pipeline(scene, front_width_studs=48)
    original_model = bundle.brick_model
    model, repair = repair_orthogonal_overlaps(original_model)
    plan = generate_assembly_plan(model)
    bundle = bundle.model_copy(update={
        'brick_model': model, 'bom': generate_bom(model), 'assembly_plan': plan,
        'instruction_plan': generate_instruction_plan(plan),
        'bag_plan': generate_bag_plan(plan),
    })
    parts = model.parts
    if not parts:
        raise AssertionError("EMPTY_BRICKMODEL")
    if bundle.bom.total_parts != len(parts):
        raise AssertionError("BOM_COUNT_MISMATCH")
    ids = [p.placement_id for p in parts]
    if len(ids) != len(set(ids)):
        raise AssertionError("DUPLICATE_PLACEMENTS")
    if bundle.assembly_plan:
        ordered = [pid for step in bundle.assembly_plan.steps for pid in step.placement_ids]
        if len(ordered) != len(parts) or set(ordered) != set(ids):
            raise AssertionError("NOTICE_PART_COVERAGE_MISMATCH")

    references = Counter(p.part_id for p in parts)
    categories = Counter(p.category for p in parts)
    components = Counter(p.component for p in parts)
    unresolved = []
    for part in parts:
        definition = ORTHOGONAL.get(part.part_id)
        if definition is None:
            unresolved.append({"placement_id": part.placement_id, "part_id": part.part_id,
                               "category": part.category, "reason": "NOT_IN_ORTHOGONAL_PHYSICAL_GATE_CATALOG"})
        elif part.category in ("brick", "plate"):
            width, length = definition.footprint(part.rotation_quarter_turns)
            if (part.width_studs is not None and part.width_studs != width) or (
                part.length_studs is not None and part.length_studs != length
            ) or (part.height_plates is not None and part.height_plates != definition.height_plates):
                raise AssertionError("CATALOG_DIMENSION_MISMATCH:" + part.placement_id)

    issues = [issue.model_dump(mode="json") for issue in bundle.fidelity_issues]
    opening_ids = {p.opening_id for p in parts if p.opening_id}
    omissions = [issue for issue in issues if "omitt" in issue.get("code", "").lower()
                 or "omitt" in issue.get("message", "").lower()]
    inventory = {
        "source_scene": str(SOURCE),
        "orthogonal_repair": repair,
        "building_id": model.building_id,
        "total_bricks": len(parts),
        "unique_part_references": len(references),
        "references": dict(sorted(references.items())),
        "categories": dict(sorted(categories.items())),
        "components": dict(sorted(components.items())),
        "wall_bricks": components["wall"],
        "floor_bricks": sum("floor" in p.placement_id.lower() for p in parts),
        "roof_bricks": components["roof"] + components["roof_support"],
        "stair_bricks": sum(p.placement_id.startswith("scene-stair:") for p in parts),
        "terrace_bricks": sum(p.placement_id.startswith("scene-platform:") for p in parts),
        "other_bricks": len(parts) - components["wall"] - components["roof"] - components["roof_support"],
        "source_openings": [o.id for o in scene.openings],
        "openings_with_parts": sorted(opening_ids),
        "opening_count_in_scene": len(scene.openings),
        "omitted_components": omissions,
        "fidelity_issue_count": len(issues),
        "physical_gate_unsupported_parts": unresolved,
        "mechanical_certification": "NOT_CERTIFIED",
    }
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / "viewer-export.json").write_text(bundle.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    (OUTPUT / "brick-model.json").write_text(model.model_dump_json(indent=2, exclude_none=True), encoding="utf-8")
    (OUTPUT / "inventory.json").write_text(json.dumps(inventory, indent=2, ensure_ascii=False), encoding="utf-8")
    (OUTPUT / "validation.json").write_text(json.dumps({
        "schema_validated": True, "orthogonal_repair": repair, "bom_count_matches": True,
        "placement_ids_unique": True, "notice_coverage_checked": bool(bundle.assembly_plan),
        "catalog_dimensions_checked_where_available": True,
        "collisions": "NOT_CERTIFIED", "supports": "NOT_CERTIFIED",
        "connections": "NOT_CERTIFIED", "vertical_insertion": "NOT_CERTIFIED",
        "viewer_browser": "NOT_TESTED",
        "fidelity_issues": issues,
    }, indent=2, ensure_ascii=False), encoding="utf-8")
    print("GUIDED004_REAL_CONVERSION=" + json.dumps(inventory, ensure_ascii=False, sort_keys=True))
    return inventory


if __name__ == "__main__":
    generate()
