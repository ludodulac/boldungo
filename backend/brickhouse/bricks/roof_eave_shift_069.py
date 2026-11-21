"""Check one whole-roof-side shift against existing eave wall anchors.

This tests a narrowly defined alternative to the 068 failure: shift ALL
courses together, preserving the selected slope family's course advance.
A roof eave still needs to meet its ACTUAL wall-top stud columns.

Pure nominal evidence. No brick moves, no mesh/clutch/strength certificate.
"""
from __future__ import annotations

from .catalog import standard_orthogonal_definitions
from .roof import create_m0_roof_catalog


def assess_whole_side_shift(model, *, side="positive", shift_studs=3):
    if side not in ("negative", "positive"):
        raise ValueError("side must be negative or positive")
    if not isinstance(shift_studs, int) or shift_studs == 0 or abs(shift_studs) > 8:
        raise ValueError("shift_studs must be a nonzero integer within 8 studs")

    catalog = create_m0_roof_catalog()
    slope = [p for p in model.parts if p.component == "roof"
             and p.roof_side == side]
    if not slope:
        return {"building_id": model.building_id, "status": "NO_SLOPE_ON_SIDE",
                "model_mutated": False, "physical_certification": "NOT_CERTIFIED"}

    axes = {p.rotation_quarter_turns % 2 for p in slope}
    if len(axes) != 1:
        return {"building_id": model.building_id, "status": "UNKNOWN_MIXED_SLOPE_AXES",
                "model_mutated": False, "physical_certification": "NOT_CERTIFIED"}
    shift_axis = "x" if next(iter(axes)) == 0 else "y"
    bottom_z = min(p.z_plates for p in slope)
    eaves = sorted([p for p in slope if p.z_plates == bottom_z],
                   key=lambda p: p.placement_id)
    ortho = standard_orthogonal_definitions()
    wall_tops = set()
    unrecognized_top_parts = []
    for part in model.parts:
        if part.component not in ("wall", "roof_support"):
            continue
        definition = ortho.get(part.part_id)
        if definition is None:
            unrecognized_top_parts.append(part.placement_id)
            continue
        if part.z_plates + definition.height_plates != bottom_z:
            continue
        width, depth = definition.footprint(part.rotation_quarter_turns)
        wall_tops.update(
            (part.x_studs + x, part.y_studs + y)
            for x in range(width) for y in range(depth)
        )

    original_supported = []
    shifted_supported = []
    unknown_footprints = []
    for p in eaves:
        try:
            definition = catalog.get(p.part_id)
        except KeyError:
            unknown_footprints.append(p.placement_id)
            continue
        w, d = definition.width_studs, definition.length_studs
        if p.rotation_quarter_turns % 2:
            w, d = d, w
        footprint = {(p.x_studs + x, p.y_studs + y)
                     for x in range(w) for y in range(d)}
        offset = ((shift_studs, 0) if shift_axis == "x"
                  else (0, shift_studs))
        before = bool(footprint & wall_tops)
        after = bool({(x + offset[0], y + offset[1])
                      for x, y in footprint} & wall_tops)
        if before:
            original_supported.append(p.placement_id)
        if after:
            shifted_supported.append(p.placement_id)
    lost = sorted(set(original_supported) - set(shifted_supported))
    gained = sorted(set(shifted_supported) - set(original_supported))
    if unknown_footprints or unrecognized_top_parts:
        status = "UNKNOWN_UNREVIEWED_EAVE_GEOMETRY"
    elif not original_supported:
        status = "UNKNOWN_NO_DOCUMENTED_ORIGINAL_EAVE_ANCHORS"
    elif lost:
        status = "REJECTED_LOST_EAVE_ANCHORS"
    else:
        status = "EAVE_PROJECTION_PRESERVED_ONLY"
    return {
        "building_id": model.building_id,
        "side": side,
        "shift_axis": shift_axis,
        "shift_studs": shift_studs,
        "first_eave_z_plates": bottom_z,
        "eave_parts_total": len(eaves),
        "original_supported_eave_parts": len(original_supported),
        "shifted_supported_eave_parts": len(shifted_supported),
        "originally_supported_now_unsupported": lost,
        "originally_unsupported_now_supported": gained,
        "unknown_eave_footprints": unknown_footprints,
        "unrecognized_host_count": len(unrecognized_top_parts),
        "status": status,
        "model_mutated": False,
        "physical_certification": "NOT_CERTIFIED",
        "limitation": "Only nominal wall-top footprint contacts. Never proves physical clutch, loads, exterior silhouette or legal insertion.",
    }
