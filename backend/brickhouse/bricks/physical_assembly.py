"""Two explicit assembly preflights sharing catalog, geometry and notice-order checks.

Physical remains strict 060B: documented VALID connectors only.
Geometric is non-certifying: connector evidence NOT checked.
Neither mode proves clutch strength, stability or actual insertability.
"""
from .physical_placement_gate import (
    Placement, PhysicalPlacementGate, GeometricPlacementGate,
    verify_connected, verify_geometrically_connected,
)
from .assembly import generate_assembly_plan


def generate_physically_screened_assembly_plan(model):
    """Strict 060B path: refuse UNKNOWN connector support before producing a notice."""
    return _screen_assembly(model, PhysicalPlacementGate, verify_connected, "PHYSICAL")


def generate_geometrically_screened_assembly_plan(model):
    """Non-certifying orthogonal geometry/notice-order check; connectors NOT checked."""
    return _screen_assembly(
        model, GeometricPlacementGate, verify_geometrically_connected, "GEOMETRIC"
    )


def _screen_assembly(model, gate_type, connected_check, label):
    gate = gate_type()
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
            raise ValueError(f"{label}_GATE_FAIL:{part.placement_id}:{exc}") from exc
    try:
        connected_check(gate.accepted)
    except ValueError as exc:
        raise ValueError(f"{label}_GATE_FAIL:{exc}") from exc
    plan = generate_assembly_plan(model)
    # Replay the actual notice order, not just a sorted spatial model.
    ordered = gate_type()
    parts_by_id = {part.placement_id: part for part in model.parts}
    scheduled_ids = [pid for step in plan.steps for pid in step.placement_ids]
    if len(scheduled_ids) != len(set(scheduled_ids)):
        raise ValueError(f"DUPLICATE_{label}_NOTICE_PART")
    if set(scheduled_ids) != set(parts_by_id):
        raise ValueError(f"{label}_NOTICE_COVERAGE_MISMATCH")
    for step in plan.steps:
        # Within one instruction step, place lower supporting bricks first.
        for placement_id in sorted(step.placement_ids, key=lambda pid: (parts_by_id[pid].z_plates, pid)):
            part = parts_by_id[placement_id]
            try:
                ordered.add(Placement(part.part_id, part.x_studs, part.y_studs,
                                      part.z_plates, part.rotation_quarter_turns))
            except (ValueError, TypeError) as exc:
                raise ValueError(
                    f"UNBUILDABLE_NOTICE_STEP:{step.step_id}:{placement_id}:{exc}"
                ) from exc
    if len(ordered.accepted) != len(model.parts):
        raise ValueError(f"INCOMPLETE_{label}_NOTICE")
    connected_check(ordered.accepted)
    return plan

def gate_dimension(part):
    return Placement(part.part_id, 0, 0, 0, part.rotation_quarter_turns).dimensions()
