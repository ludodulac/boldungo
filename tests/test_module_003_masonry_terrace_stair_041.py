from __future__ import annotations

import json
from pathlib import Path

from brickhouse.bricks.bom import BillOfMaterials
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.orthogonal_geometry import OrthogonalBounds, orthogonal_bounds, orthogonal_collisions
from brickhouse.bricks.piece_capabilities import (
    PieceCapabilityStage,
    create_current_engine_capability_registry,
    validate_model_part_capabilities,
)
from brickhouse.bricks.support_chain import analyze_standard_brick_support_chain

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "frontend" / "module-001-plus-module-002-roof-export.json"
MODULE = ROOT / "frontend" / "module-003-masonry-terrace-stair-export.json"
COMBINED = ROOT / "frontend" / "module-001-plus-module-002-plus-module-003-export.json"
MASTER = ROOT / "data" / "processed" / "piece_types_master.csv"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def model_and_parts() -> tuple[dict, BrickModel, list]:
    module = load(MODULE)
    model = BrickModel.model_validate(module["brick_model"])
    return module, model, model.parts


def cells_for(model: BrickModel) -> set[tuple[int, int, int]]:
    cells: set[tuple[int, int, int]] = set()
    for part in model.parts:
        bounds = orthogonal_bounds(part)
        if bounds is None:
            continue
        for x in range(bounds.x0, bounds.x1):
            for y in range(bounds.y0, bounds.y1):
                for z in range(bounds.z0, bounds.z1):
                    cells.add((x, y, z))
    return cells


def parts_with(fragment: str, parts: list) -> list:
    return [part for part in parts if fragment in part.placement_id]


def visible_orthogonal_bounds(part) -> OrthogonalBounds | None:
    """Geometric bounds for an orthogonal visible shape regardless of support domain.

    orthogonal_bounds() deliberately excludes facade_detail because that helper
    belongs to structural collision/support auditing. 052 parapet alignment is
    a visible-envelope requirement, so derive the same physical footprint from
    the canonical orthogonal part definition without reclassifying the part.
    """
    definition = standard_orthogonal_definitions().get(part.part_id)
    if definition is None:
        return None
    width, length = definition.footprint(part.rotation_quarter_turns)
    return OrthogonalBounds(
        placement_id=part.placement_id,
        x0=part.x_studs,
        x1=part.x_studs + width,
        y0=part.y_studs,
        y1=part.y_studs + length,
        z0=part.z_plates,
        z1=part.z_plates + definition.height_plates,
    )


def test_051_scope_source_unchanged_and_confidence_separated() -> None:
    module = load(MODULE)
    combined = load(COMBINED)
    source = load(SOURCE)

    assert module["metadata"]["mission"] == "BOLDUNGO-057-PARAPET-PROFILE-CANONIZE-AND-APPLY"
    assert module["metadata"]["structure_type"] == "WALLS_PLUS_PLATFORM_AROUND_MAJOR_VOID_AND_TWO_RUN_STAIR"

    confidence = module["metadata"]["subsystem_confidence"]
    assert confidence == {
        "ENVELOPE": "HIGH",
        "MAJOR_VOID": "HIGH",
        "CIRCULATION": "HIGH",
        "INTERFACES": "MEDIUM",
        "METRICS": "LOW",
    }
    assert "confidence" not in module["metadata"]

    source_parts = source["brick_model"]["parts"]
    combined_source = combined["brick_model"]["parts"][: len(source_parts)]
    shift = combined["metadata"]["source_bundle_translation"]
    assert shift["y_studs"] == 0
    assert shift["z_plates"] == 0
    for original, translated in zip(source_parts, combined_source):
        expected = dict(original)
        expected["x_studs"] += shift["x_studs"]
        assert translated == expected

    assert combined["metadata"]["module_001_plus_002_piece_count"] == len(source_parts)
    assert combined["metadata"]["module_003_piece_count"] == module["bom"]["total_parts"]
    assert combined["metadata"]["combined_piece_count"] == (
        len(source_parts) + module["bom"]["total_parts"]
    )


def test_051_circulation_has_two_runs_turn_landing_and_reaches_house_level() -> None:
    module, model, parts = model_and_parts()
    lower = parts_with("stair-lower-tread", parts)
    upper = parts_with("stair-upper-tread", parts)
    landing = parts_with("stair-landing-", parts)
    landing_surface = [
        part for part in landing
        if "support" not in part.placement_id and "rail" not in part.placement_id
    ]

    assert lower
    assert upper
    assert landing_surface

    lower_bounds = [orthogonal_bounds(part) for part in lower]
    upper_bounds = [orthogonal_bounds(part) for part in upper]
    landing_bounds = [orthogonal_bounds(part) for part in landing_surface]
    assert all(bound is not None for bound in [*lower_bounds, *upper_bounds, *landing_bounds])

    lower_x = [part.x_studs for part in lower]
    lower_y = [part.y_studs for part in lower]
    lower_tops = [part.z_plates + 1 for part in lower]
    assert lower_x == sorted(lower_x)
    assert len(set(lower_y)) == 1
    assert lower_tops == sorted(lower_tops)
    assert lower_tops[-1] == module["metadata"]["level_model"]["intermediate_turn_level_z"]

    upper_x = [part.x_studs for part in upper]
    upper_y = [part.y_studs for part in upper]
    upper_tops = [part.z_plates + 1 for part in upper]
    assert len(set(upper_x)) == 1
    assert upper_y == sorted(upper_y, reverse=True)
    assert upper_tops == sorted(upper_tops)
    assert upper_tops[0] > lower_tops[-1]
    assert upper_tops[-1] == module["metadata"]["level_model"]["upper_masonry_platform_z"]

    # The lower run changes direction into the upper run through the landing.
    last_lower = max(lower_bounds, key=lambda bound: bound.x1)
    turn_x0 = min(bound.x0 for bound in landing_bounds)
    turn_y0 = min(bound.y0 for bound in landing_bounds)
    first_upper = max(upper_bounds, key=lambda bound: bound.y0)
    assert last_lower.x1 == turn_x0
    assert max(last_lower.y0, turn_y0) < min(
        last_lower.y1, max(bound.y1 for bound in landing_bounds)
    )
    assert first_upper.y1 == turn_y0
    assert max(first_upper.x0, turn_x0) < min(
        first_upper.x1, max(bound.x1 for bound in landing_bounds)
    )

    # Derive the real host visible wall plane from MODULE001 geometry in the
    # combined bundle; do not assume X24 in the semantic check.
    combined = load(COMBINED)
    source_count = combined["metadata"]["module_001_plus_002_piece_count"]
    source_parts = combined["brick_model"]["parts"][:source_count]
    definitions = standard_orthogonal_definitions()
    host_left = [
        part for part in source_parts
        if part["component"] == "wall"
        and part.get("facade") == "left"
        and part["part_id"] in definitions
    ]
    assert host_left
    host_plane = min(part["x_studs"] for part in host_left)

    final_upper = min(
        (orthogonal_bounds(part) for part in upper),
        key=lambda bound: bound.y0,
    )
    assert final_upper.x1 == host_plane
    assert final_upper.z1 == module["metadata"]["level_model"]["upper_masonry_platform_z"]

    assert module["metadata"]["circulation_path"] == [
        "GROUND_Z0",
        "STAIR_RUN_01_TO_Z24",
        "TURN_LANDING_Z24",
        "DIRECTION_CHANGE",
        "STAIR_RUN_02_TO_Z49",
        "HOUSE_LEVEL_Z49",
    ]


def test_051_major_void_is_real_ground_open_negative_space_with_ceiling() -> None:
    module, model, _ = model_and_parts()
    solid = cells_for(model)
    void = module["metadata"]["geometry"]["void_01"]
    x0, x1 = void["x"]
    y0, y1 = void["y"]
    z0, z1 = void["z"]

    assert void["classification"] == "MAJOR_ARCHITECTURAL_VOID"
    assert z0 == module["metadata"]["level_model"]["ground_low_level_z"]
    assert void["open_to_ground"] is True
    assert void["upper_boundary_z"] == z1

    # The entire declared VOID_01 volume is physically unoccupied, not tagged
    # as empty while hidden solids remain behind it.
    for x in range(x0, x1):
        for y in range(y0, y1):
            for z in range(z0, z1):
                assert (x, y, z) not in solid

    # The upper platform is the real geometric ceiling of the void.
    for x in range(x0, x1):
        for y in range(y0, y1):
            assert (x, y, z1) in solid

    # Ground remains open throughout the void footprint.
    for x in range(x0, x1):
        for y in range(y0, y1):
            assert (x, y, z0) not in solid

    # Multiple full-height faces are open below the ceiling. This distinguishes
    # the negative space from a small local window punched into a solid block.
    face_open = {
        "x_high": all(
            (x1, y, z) not in solid
            for y in range(y0, y1)
            for z in range(z0, z1)
        ),
        "y_low": all(
            (x, y0 - 1, z) not in solid
            for x in range(x0, x1)
            for z in range(z0, z1)
        ),
        "y_high": all(
            (x, y1, z) not in solid
            for x in range(x0, x1)
            for z in range(z0, z1)
        ),
    }
    assert sum(face_open.values()) >= 2

    envelope = module["metadata"]["geometry"]["upper_system_envelope"]
    envelope_width = envelope["x"][1] - envelope["x"][0]
    envelope_depth = envelope["y"][1] - envelope["y"][0]
    envelope_height = envelope["z"][1] - envelope["z"][0]
    assert (x1 - x0) / envelope_width >= 0.40
    assert (y1 - y0) / envelope_depth >= 0.75
    assert (z1 - z0) / envelope_height >= 0.90


def test_051_void_and_stair_share_one_architectural_system() -> None:
    module, model, parts = model_and_parts()
    void = module["metadata"]["geometry"]["void_01"]
    platform = module["metadata"]["geometry"]["upper_platform"]
    upper = parts_with("stair-upper-tread", parts)
    final_upper = min(
        (orthogonal_bounds(part) for part in upper),
        key=lambda bound: bound.y0,
    )

    # VOID_01 is directly under the same upper platform reached by RUN_02.
    assert void["z"][1] == platform["walking_top_z"] - 1
    assert final_upper.z1 == platform["walking_top_z"]
    assert final_upper.y0 == platform["y"][1]
    assert max(final_upper.x0, platform["x"][0]) < min(
        final_upper.x1, platform["x"][1]
    )

    # The historical "block + local opening" pieces are gone from the rebuild.
    forbidden_fragments = (
        "main-house-wall",
        "lower-false-opening-closure",
        "rear-wall",
        "rear-lintel",
        "opening-lintel",
    )
    assert not any(
        any(fragment in part.placement_id for fragment in forbidden_fragments)
        for part in model.parts
    )


def test_051_human_validated_position_and_railing_are_preserved() -> None:
    module, model, parts = model_and_parts()
    preserved = module["metadata"]["preserved_human_constraints"]
    assert preserved["rearward_position"] == {
        "status": "PRESERVED",
        "translation_y_studs": 10,
    }
    assert preserved["stair_house_proximity"] == {
        "status": "PRESERVED",
        "translation_x_studs": 9,
    }

    geometry = module["metadata"]["geometry"]
    lower_bounds = [orthogonal_bounds(part) for part in parts_with("stair-lower-tread", parts)]
    upper_bounds = [orthogonal_bounds(part) for part in parts_with("stair-upper-tread", parts)]
    platform_bounds = [orthogonal_bounds(part) for part in parts_with("upper-platform", parts)]
    assert min(bound.x0 for bound in lower_bounds) == geometry["stair_run_01"]["x"][0]
    assert max(bound.x1 for bound in lower_bounds) == geometry["stair_run_01"]["x"][1]
    assert min(bound.y0 for bound in platform_bounds) == geometry["upper_platform"]["y"][0]
    assert max(bound.y1 for bound in platform_bounds) == geometry["upper_platform"]["y"][1]
    assert min(bound.x0 for bound in upper_bounds) == geometry["stair_run_02"]["x"][0]
    assert max(bound.x1 for bound in upper_bounds) == geometry["stair_run_02"]["x"][1]

    guard = parts_with("platform-edge-fall-protection", parts)
    assert guard
    guard_cells: set[tuple[int, int, int]] = set()
    for part in guard:
        bounds = orthogonal_bounds(part)
        assert bounds is not None
        for x in range(bounds.x0, bounds.x1):
            for y in range(bounds.y0, bounds.y1):
                for z in range(bounds.z0, bounds.z1):
                    guard_cells.add((x, y, z))

    target = preserved["platform_edge_protection_044"]
    assert target["status"] == "HUMAN_PASS_PRESERVED"
    for x in range(*target["rear_edge_x"]):
        for z in range(*target["z"]):
            assert (x, target["y"], z) in guard_cells
    assert not any(
        x >= target["stair_arrival_open_x"][0]
        for x, _y, _z in guard_cells
    )


def test_051_no_solid_collision_all_required_solids_supported_and_parts_approved() -> None:
    module, model, _ = model_and_parts()
    bill = BillOfMaterials.model_validate(module["bom"])
    assert bill.total_parts == len(model.parts)
    assert len({part.placement_id for part in model.parts}) == len(model.parts)

    registry = create_current_engine_capability_registry(MASTER)
    validate_model_part_capabilities(model, registry)
    assert orthogonal_collisions(model) == []

    support = analyze_standard_brick_support_chain(model)
    assert support.valid
    assert not support.unsupported_placement_ids
    assert not support.unsupported_connector_ids

    for line in bill.lines:
        assert registry.get(line.part_id).stage >= PieceCapabilityStage.PLACEMENT_APPROVED


def test_051_normalized_decomposition_and_interfaces_are_explicit() -> None:
    module = load(MODULE)
    normalized = module["metadata"]["normalized_decomposition"]
    assert set(normalized) == {
        "STAIR_RUN_01",
        "TURN_LANDING",
        "STAIR_RUN_02",
        "UPPER_ARRIVAL",
        "PARAPETS",
        "VOID_01",
        "VOID_BOUNDARIES",
        "UPPER_SOLIDS",
        "HOUSE_INTERFACE",
        "TIMBER_TERRACE_INTERFACE",
    }
    assert normalized["VOID_01"]["open_to_ground"] is True
    assert normalized["UPPER_SOLIDS"]["not_a_solid_block"] is True
    assert normalized["VOID_BOUNDARIES"]["x_high"] == "OPEN"
    assert normalized["VOID_BOUNDARIES"]["y_low"] == "OPEN"
    assert normalized["STAIR_RUN_01"]["orientation"] != normalized["STAIR_RUN_02"]["orientation"]
    assert normalized["HOUSE_INTERFACE"]["detail"] == "FINAL_LEGO_CONNECTION_DEFERRED"
    assert normalized["TIMBER_TERRACE_INTERFACE"]["detail"] == "PLAN_SPAN_UNRESOLVED_REFINABLE"



def test_052_stair_runs_have_solid_masonry_mass_and_void_remains_unoccupied() -> None:
    module, model, parts = model_and_parts()
    void = module["metadata"]["geometry"]["void_01"]

    def occupied_by(fragment: str) -> set[tuple[int, int, int]]:
        occupied: set[tuple[int, int, int]] = set()
        for part in parts_with(fragment, parts):
            bounds = orthogonal_bounds(part)
            assert bounds is not None
            for x in range(bounds.x0, bounds.x1):
                for y in range(bounds.y0, bounds.y1):
                    for z in range(bounds.z0, bounds.z1):
                        occupied.add((x, y, z))
        return occupied

    # STAIR_RUNS_HAVE_SOLID_MASONRY_MASS:
    # every cell directly below every preserved tread is masonry down to ground.
    for tread_fragment, mass_fragment in (
        ("stair-lower-tread", "stair-lower-solid-mass"),
        ("stair-upper-tread", "stair-upper-solid-mass"),
    ):
        mass = occupied_by(mass_fragment)
        treads = parts_with(tread_fragment, parts)
        assert treads
        for tread in treads:
            bounds = orthogonal_bounds(tread)
            assert bounds is not None
            for x in range(bounds.x0, bounds.x1):
                for y in range(bounds.y0, bounds.y1):
                    for z in range(0, bounds.z0):
                        assert (x, y, z) in mass

    # MAJOR_VOID_REMAINS_UNOCCUPIED: the stair fill is physically separate
    # from the established first-class architectural void.
    solid = cells_for(model)
    for x in range(*void["x"]):
        for y in range(*void["y"]):
            for z in range(*void["z"]):
                assert (x, y, z) not in solid


def test_052_run_parapet_aligns_with_landing_and_break_remains_local() -> None:
    _module, _model, parts = model_and_parts()

    run_house = parts_with("stair-upper-parapet-house-body", parts)
    landing = parts_with("stair-first-landing-rail", parts)
    transition = parts_with("stair-landing-parapet-local-transition", parts)
    assert run_house and landing and transition

    run_bounds = [visible_orthogonal_bounds(part) for part in run_house]
    landing_bounds = [visible_orthogonal_bounds(part) for part in landing]
    transition_bounds = [visible_orthogonal_bounds(part) for part in transition]
    assert all(bound is not None for bound in [*run_bounds, *landing_bounds, *transition_bounds])

    # RUN_PARAPET_ALIGNS_WITH_LANDING_PARAPET:
    # derive the landing's longitudinal rail from its one-stud X thickness.
    longitudinal = [
        bound for bound in landing_bounds
        if (bound.x1 - bound.x0) == 1 and (bound.y1 - bound.y0) > 1
    ]
    assert longitudinal
    landing_x = {bound.x0 for bound in longitudinal}
    run_x = {bound.x0 for bound in run_bounds}
    assert len(landing_x) == 1
    assert run_x == landing_x

    # LANDING_PARAPET_BREAK_REMAINS_LOCAL:
    # the raised correction occupies only the two cells nearest RUN_02 and
    # leaves a non-zero but <=2-plate break to the nearest run parapet top.
    transition_y0 = min(bound.y0 for bound in transition_bounds)
    transition_y1 = max(bound.y1 for bound in transition_bounds)
    assert transition_y1 - transition_y0 <= 2

    transition_top = max(bound.z1 for bound in transition_bounds)
    nearest_run_y = max(bound.y0 for bound in run_bounds)
    nearest_run_top = max(
        bound.z1 for bound in run_bounds
        if bound.y0 == nearest_run_y
    )
    break_plates = abs(nearest_run_top - transition_top)
    assert 1 <= break_plates <= 2


def test_052_stair_wall_terminates_and_house_remains_deep_boundary() -> None:
    module, model, parts = model_and_parts()
    combined = load(COMBINED)
    refinement = module["metadata"]["human_refinement_052"]["stair_wall_termination"]
    void = module["metadata"]["geometry"]["void_01"]

    sidewall = parts_with("void-entry-sidewall", parts)
    assert sidewall
    side_bounds = [orthogonal_bounds(part) for part in sidewall]
    assert all(bound is not None for bound in side_bounds)

    side_y0 = min(bound.y0 for bound in side_bounds)
    side_y1 = max(bound.y1 for bound in side_bounds)
    assert [side_y0, side_y1] == refinement["sidewall_y"]
    assert side_y0 > void["y"][0]

    # STAIR_WALL_TERMINATES_AT_MAJOR_VOID + MAJOR_VOID_DEPTH_NOT_BLOCKED_BY_STAIR_WALL:
    # below the ceiling-carrier zone, the former long X-low corridor wall is
    # absent throughout the deep portion of VOID_01.
    solid = cells_for(model)
    deep_y0, deep_y1 = refinement["deep_open_region_y"]
    side_x = refinement["sidewall_x"]
    carrier_bottom_z = min(
        orthogonal_bounds(part).z0
        for part in parts_with("void-ceiling-carrier", parts)
    )
    for y in range(deep_y0, deep_y1):
        for z in range(void["z"][0], carrier_bottom_z):
            assert (side_x, y, z) not in solid

    # HOUSE_WALL_REMAINS_DEEP_BOUNDARY:
    # derive the real host wall plane from MODULE001/002 source geometry and
    # require substantial longitudinal coverage beside the newly opened depth.
    source_count = combined["metadata"]["module_001_plus_002_piece_count"]
    combined_model = BrickModel.model_validate(combined["brick_model"])
    source_parts = combined_model.parts[:source_count]
    host_left = [
        part for part in source_parts
        if part.component == "wall" and part.facade == "left"
    ]
    assert host_left
    host_bounds = [orthogonal_bounds(part) for part in host_left]
    host_bounds = [bound for bound in host_bounds if bound is not None]
    host_plane = min(bound.x0 for bound in host_bounds)
    assert host_plane == module["metadata"]["interfaces"]["TO_HOUSE"]["plane_x"]

    deep_y = set(range(deep_y0, deep_y1))
    host_y_coverage: set[int] = set()
    for bound in host_bounds:
        if bound.x0 <= host_plane < bound.x1 and bound.z0 < void["z"][1]:
            host_y_coverage.update(range(bound.y0, bound.y1))
    covered = deep_y.intersection(host_y_coverage)
    assert covered
    assert len(covered) / len(deep_y) >= 0.5


def test_052_interior_recess_remains_explicitly_not_observable() -> None:
    module = load(MODULE)
    recess = module["metadata"]["human_refinement_052"]["interior_recess"]
    assert recess["status"] == "NOT_OBSERVABLE_FROM_CURRENT_PHOTOS"
    assert recess["geometry_added"] is False
    assert recess["required_future_evidence"] == "PHOTO_FROM_OR_TOWARD_INTERIOR_OF_PASSAGE"



def _tread_top(part) -> int:
    bounds = orthogonal_bounds(part)
    assert bounds is not None
    return bounds.z1


def _distinct_risers(parts: list, base_level: int) -> list[int]:
    tops = sorted({_tread_top(part) for part in parts})
    assert tops
    return [tops[0] - base_level, *[b - a for a, b in zip(tops, tops[1:])]]


def _giron_spans_by_top(parts: list, axis: str) -> list[int]:
    grouped: dict[int, list] = {}
    for part in parts:
        grouped.setdefault(_tread_top(part), []).append(orthogonal_bounds(part))
    spans: list[int] = []
    for bounds in grouped.values():
        assert all(bound is not None for bound in bounds)
        if axis == "x":
            spans.append(max(bound.x1 for bound in bounds) - min(bound.x0 for bound in bounds))
        else:
            spans.append(max(bound.y1 for bound in bounds) - min(bound.y0 for bound in bounds))
    return sorted(spans)


def test_054_upper_run_step_module_matches_observed_stair_family() -> None:
    module, _model, parts = model_and_parts()
    lower = parts_with("stair-lower-tread", parts)
    upper = parts_with("stair-upper-tread", parts)
    assert lower and upper

    levels = module["metadata"]["level_model"]
    lower_risers = _distinct_risers(lower, levels["ground_low_level_z"])
    upper_risers = _distinct_risers(upper, levels["intermediate_turn_level_z"])

    # UPPER_RUN_STEP_MODULE_MATCHES_OBSERVED_STAIR_FAMILY:
    # the hidden run uses risers of the same order as the observed run,
    # without claiming an exact photographic tread count.
    assert min(upper_risers) >= min(lower_risers)
    assert max(upper_risers) <= max(lower_risers)
    assert len(set(_tread_top(part) for part in upper)) <= (
        len(set(_tread_top(part) for part in lower)) + 1
    )

    lower_girons = _giron_spans_by_top(lower, "x")
    upper_girons = _giron_spans_by_top(upper, "y")
    lower_median = lower_girons[len(lower_girons) // 2]
    upper_median = upper_girons[len(upper_girons) // 2]
    assert 0.5 <= upper_median / lower_median <= 2.5

    # UPPER_RUN_DOES_NOT_USE_UNJUSTIFIED_MICRO_STEPS:
    # no hidden riser is smaller than the smallest directly observed family riser.
    assert min(upper_risers) >= min(lower_risers)


def test_054_no_unobserved_void_under_stair_and_platform_void_distinct() -> None:
    module, model, parts = model_and_parts()
    solid = cells_for(model)

    # NO_UNOBSERVED_VOID_UNDER_STAIR:
    # every cell beneath the preserved lower-run treads and turn landing
    # is masonry down to the ground datum.
    lower = parts_with("stair-lower-tread", parts)
    landing = [
        part for part in parts_with("stair-landing-", parts)
        if "support" not in part.placement_id
        and "rail" not in part.placement_id
        and "transition" not in part.placement_id
        and "solid-mass" not in part.placement_id
    ]
    assert lower and landing
    for surface in [*lower, *landing]:
        bounds = orthogonal_bounds(surface)
        assert bounds is not None
        for x in range(bounds.x0, bounds.x1):
            for y in range(bounds.y0, bounds.y1):
                for z in range(module["metadata"]["level_model"]["ground_low_level_z"], bounds.z0):
                    assert (x, y, z) in solid

    # PLATFORM_VOID_REMAINS_DISTINCT_FROM_STAIR_MASS +
    # MAJOR_PLATFORM_VOID_PRESERVED.
    void = module["metadata"]["geometry"]["void_01"]
    assert void["classification"] == "MAJOR_ARCHITECTURAL_VOID"
    for x in range(*void["x"]):
        for y in range(*void["y"]):
            for z in range(*void["z"]):
                assert (x, y, z) not in solid

    stair_mass = [
        *parts_with("stair-lower-solid-mass", parts),
        *parts_with("stair-landing-solid-mass", parts),
        *parts_with("stair-upper-solid-mass", parts),
    ]
    assert stair_mass
    for part in stair_mass:
        bounds = orthogonal_bounds(part)
        assert bounds is not None
        overlaps_void = (
            max(bounds.x0, void["x"][0]) < min(bounds.x1, void["x"][1])
            and max(bounds.y0, void["y"][0]) < min(bounds.y1, void["y"][1])
            and max(bounds.z0, void["z"][0]) < min(bounds.z1, void["z"][1])
        )
        assert not overlaps_void


def test_054_platform_face_coplanar_across_floor_boundary() -> None:
    module, model, parts = model_and_parts()
    solid = cells_for(model)
    platform = module["metadata"]["geometry"]["upper_platform"]

    carriers = parts_with("void-ceiling-carrier", parts)
    assert carriers
    carrier_bounds = [orthogonal_bounds(part) for part in carriers]
    assert all(bound is not None for bound in carrier_bounds)
    floor_boundary_z = min(bound.z0 for bound in carrier_bounds)

    outer_plane_x = platform["x"][0]
    platform_top_z = platform["walking_top_z"]

    # MASONRY_PLATFORM_FACE_IS_COPLANAR_ACROSS_FLOOR_BOUNDARY:
    # the actual occupied exterior plane stays present continuously through
    # the constructive floor boundary.
    for y in range(*platform["y"]):
        for z in range(floor_boundary_z, platform_top_z):
            assert (outer_plane_x, y, z) in solid

    # FLOOR_BOUNDARY_DOES_NOT_IMPLY_DEPTH_CHANGE:
    # the minimum exterior X at the boundary is the same immediately below,
    # through, and immediately above the carrier datum.
    probe_z = [floor_boundary_z - 1, floor_boundary_z, platform_top_z - 1]
    for y in range(*platform["y"]):
        minima = []
        for z in probe_z:
            xs = [x for x, yy, zz in solid if yy == y and zz == z]
            assert xs
            minima.append(min(xs))
        assert minima == [outer_plane_x, outer_plane_x, outer_plane_x]

def test_055_stair_parapet_has_no_unintended_large_gap_at_landing_junction() -> None:
    _module, _model, parts = model_and_parts()

    run_house = parts_with("stair-upper-parapet-house-body", parts)
    landing = parts_with("stair-first-landing-rail", parts)
    transition = parts_with("stair-landing-parapet-local-transition", parts)
    bridge = parts_with("stair-landing-parapet-gap-bridge", parts)
    assert run_house and landing and transition

    run_bounds = [visible_orthogonal_bounds(part) for part in run_house]
    landing_bounds = [visible_orthogonal_bounds(part) for part in landing]
    transition_bounds = [visible_orthogonal_bounds(part) for part in transition]
    bridge_bounds = [visible_orthogonal_bounds(part) for part in bridge]
    all_bounds = [*run_bounds, *landing_bounds, *transition_bounds, *bridge_bounds]
    assert all(bound is not None for bound in all_bounds)

    # Derive the junction from the actual geometry rather than checking for a
    # named replacement piece. The house-side RUN_02 parapet and the landing's
    # longitudinal rail must occupy one common X plane with no empty Y column
    # through their substantial shared vertical band.
    longitudinal = [
        bound for bound in landing_bounds
        if (bound.x1 - bound.x0) == 1 and (bound.y1 - bound.y0) > 1
    ]
    assert longitudinal

    run_x = {bound.x0 for bound in run_bounds}
    landing_x = {bound.x0 for bound in longitudinal}
    assert len(run_x) == 1
    assert run_x == landing_x
    plane_x = next(iter(run_x))

    nearest_run_y = max(bound.y0 for bound in run_bounds)
    nearest_landing_y = min(bound.y0 for bound in longitudinal)
    assert nearest_landing_y > nearest_run_y

    run_endpoint = [bound for bound in run_bounds if bound.y0 == nearest_run_y]
    landing_endpoint = [
        bound for bound in [*longitudinal, *transition_bounds]
        if bound.y0 == nearest_landing_y
    ]
    assert run_endpoint and landing_endpoint

    common_bottom = max(
        min(bound.z0 for bound in run_endpoint),
        min(bound.z0 for bound in landing_endpoint),
    )
    common_top = min(
        max(bound.z1 for bound in run_endpoint),
        max(bound.z1 for bound in landing_endpoint),
    )
    assert common_top - common_bottom >= 9

    protected_cells: set[tuple[int, int, int]] = set()
    for bound in [*run_bounds, *longitudinal, *transition_bounds, *bridge_bounds]:
        if not (bound.x0 <= plane_x < bound.x1):
            continue
        for y in range(bound.y0, bound.y1):
            for z in range(bound.z0, bound.z1):
                protected_cells.add((plane_x, y, z))

    # STAIR_PARAPET_HAS_NO_UNINTENDED_LARGE_GAP_AT_LANDING_JUNCTION
    for y in range(nearest_run_y, nearest_landing_y + 1):
        for z in range(common_bottom, common_top):
            assert (plane_x, y, z) in protected_cells

def _upper_profile_top_by_y(bounds: list[OrthogonalBounds], plane_x: int) -> dict[int, int]:
    tops: dict[int, int] = {}
    for bound in bounds:
        if not (bound.x0 <= plane_x < bound.x1):
            continue
        for y in range(bound.y0, bound.y1):
            tops[y] = max(tops.get(y, bound.z1), bound.z1)
    return tops


def test_057_architectural_upper_profile_continues_across_slope_to_horizontal_transition() -> None:
    _module, _model, parts = model_and_parts()

    run_house = parts_with("stair-upper-parapet-house-body", parts)
    landing = parts_with("stair-first-landing-rail", parts)
    bridge = parts_with("stair-landing-parapet-gap-bridge", parts)
    transition = parts_with("stair-landing-parapet-local-transition", parts)
    continuation = parts_with("stair-landing-parapet-profile-continuation", parts)
    assert run_house and landing and bridge and transition and continuation

    run_bounds = [visible_orthogonal_bounds(part) for part in run_house]
    landing_bounds = [visible_orthogonal_bounds(part) for part in landing]
    bridge_bounds = [visible_orthogonal_bounds(part) for part in bridge]
    transition_bounds = [visible_orthogonal_bounds(part) for part in transition]
    continuation_bounds = [visible_orthogonal_bounds(part) for part in continuation]
    all_bounds = [
        *run_bounds,
        *landing_bounds,
        *bridge_bounds,
        *transition_bounds,
        *continuation_bounds,
    ]
    assert all(bound is not None for bound in all_bounds)

    longitudinal = [
        bound for bound in landing_bounds
        if (bound.x1 - bound.x0) == 1 and (bound.y1 - bound.y0) > 1
    ]
    assert longitudinal

    run_x = {bound.x0 for bound in run_bounds}
    landing_x = {bound.x0 for bound in longitudinal}
    assert len(run_x) == 1
    assert run_x == landing_x
    plane_x = next(iter(run_x))

    # The run itself must carry an ascending upper profile toward the upper
    # level. This is a profile property, not a mass-connectivity assertion.
    run_profile = _upper_profile_top_by_y(run_bounds, plane_x)
    assert run_profile
    nearest_run_y = max(run_profile)
    run_from_landing_upward = [
        run_profile[y] for y in sorted(run_profile, reverse=True)
    ]
    assert len(set(run_from_landing_upward)) >= 3
    assert all(
        next_top >= top
        for top, next_top in zip(
            run_from_landing_upward,
            run_from_landing_upward[1:],
        )
    )

    # The established landing parapet is horizontal. Its visible top must
    # remain one horizontal profile from the 055 bridge through the complete
    # longitudinal landing segment; a 39 -> 36 -> 33 taper would fail here
    # even though the masonry remains materially connected.
    landing_profile = _upper_profile_top_by_y(
        [*longitudinal, *bridge_bounds, *transition_bounds, *continuation_bounds],
        plane_x,
    )
    horizontal_y0 = min(bound.y0 for bound in bridge_bounds)
    horizontal_y1 = max(bound.y1 for bound in longitudinal)
    horizontal_tops = [
        landing_profile[y] for y in range(horizontal_y0, horizontal_y1)
    ]
    assert len(horizontal_tops) >= 3
    assert len(set(horizontal_tops)) == 1
    horizontal_top = horizontal_tops[0]

    # ARCHITECTURAL_UPPER_PROFILE_CONTINUES_ACROSS_SLOPE_TO_HORIZONTAL_TRANSITION:
    # the slope endpoint and horizontal continuation meet within the engine's
    # one-plate constructive quantization, without inventing a photographic
    # metric or permitting a local profile notch.
    run_endpoint_top = run_profile[nearest_run_y]
    plate_quantization = standard_orthogonal_definitions()["PLATE_1X1"].height_plates
    assert horizontal_top <= run_endpoint_top
    assert run_endpoint_top - horizontal_top <= plate_quantization

