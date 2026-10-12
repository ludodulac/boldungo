"""Strict assembly entry point: do not issue a notice for unchecked geometry.

Only canonical rectangular bricks/plates on a ground plane are supported.
This deliberately refuses legacy visual models rather than silently passing.
"""
from .physical_placement_gate import Placement, PhysicalPlacementGate
from .assembly import generate_assembly_plan

def generate_physically_screened_assembly_plan(model):
    gate = PhysicalPlacementGate()
    # Support ordering: ground first, then ascending z; a supported piece
    # can only depend on parts already placed below it.
    for part in sorted(model.parts, key=lambda p: (p.z_plates, p.placement_id)):
        if part.width_studs is not None or part.length_studs is not None or part.height_plates is not None:
            # Explicit dimensions may be legitimate, but cannot override the
            # canonical catalog's dimensions without verification.
            definition = gate_dimension(part)
            if (part.width_studs not in (None, definition[0]) or
                part.length_studs not in (None, definition[1]) or
                part.height_plates not in (None, definition[2])):
                raise ValueError(f"NONCANONICAL_DIMENSIONS:{part.placement_id}")
        try:
            gate.add(Placement(part.part_id, part.x_studs, part.y_studs,
                               part.z_plates, part.rotation_quarter_turns))
        except (ValueError, TypeError) as exc:
            raise ValueError(f"PHYSICAL_GATE_FAIL:{part.placement_id}:{exc}") from exc
    plan = generate_assembly_plan(model)
    # Replay the actual notice order, not just a sorted spatial model.
    ordered = PhysicalPlacementGate()
    parts_by_id = {part.placement_id: part for part in model.parts}
    for step in plan.steps:
        for placement_id in step.placement_ids:
            part = parts_by_id[placement_id]
            try:
                ordered.add(Placement(part.part_id, part.x_studs, part.y_studs,
                                      part.z_plates, part.rotation_quarter_turns))
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"UNBUILDABLE_NOTICE_STEP:{step.step_id}:{placement_id}:{exc}"
                ) from exc
    return plan

def gate_dimension(part):
    return Placement(part.part_id, 0, 0, 0, part.rotation_quarter_turns).dimensions()
