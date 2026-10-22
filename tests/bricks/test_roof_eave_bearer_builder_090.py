"""LEGO2-090: eave modules must be connected and never invent physical clutch."""
from brickhouse.bricks.brick_model import BrickModel, BrickModelPart
from brickhouse.bricks.roof_eave_bearer_builder_090 import design_roof_eave_bearers_090


def wall(pid, x, y, z, turn=0, facade="front"):
    return BrickModelPart(placement_id=pid, part_id="BRICK_1X8", category="brick",
                          component="wall", facade=facade, x_studs=x, y_studs=y,
                          z_plates=z, rotation_quarter_turns=turn)


def slope(pid, x, y, z, side):
    return BrickModelPart(placement_id=pid, part_id="BRICK_SLOPED_18_4X2",
                          category="roof_tile", component="roof",
                          roof_side=side, x_studs=x, y_studs=y, z_plates=z,
                          rotation_quarter_turns=0)


def house(parts):
    return BrickModel(building_id="OTHER-HOUSE", volume_id="shell",
                      width_studs=80, depth_studs=25, height_plates=15, parts=parts)


def corner(left=True):
    x = 16 if left else 63
    front = 16 if left else 56
    original = [
        wall("front-lower", front, 2, 0, 1),
        wall("side-lower", x, 3, 0, 0, "left" if left else "right"),
        wall("front-upper", front, 2, 3, 1),
        wall("side-upper", x, 3, 3, 0, "left" if left else "right"),
        slope("first", 14 if left else 63, 0, 6,
              "negative" if left else "positive"),
    ]
    return house(original)


def test_front_left_eave_is_wall_bonded_and_no_source_mutation():
    source = corner(True)
    before = source.model_dump_json()
    report, new = design_roof_eave_bearers_090(source)
    assert source.model_dump_json() == before
    assert report["bracket_count"] == 1
    assert report["root_ids_with_new_nominal_path"] == ["first"]
    assert report["after"]["unreached"] == 0
    assert len(report["accepted_eave_brackets"][0]["grounded_lower_stud_cells"]) >= 3
    assert len(report["accepted_eave_brackets"][0]["grounded_lower_ids"]) == 2
    assert report["physical_certification"] == "NOT_CERTIFIED"
    assert report["roof_cavity_connections_mechanically_proven"] == 0
    assert len(new.parts) != len(source.parts)


def test_other_house_positive_roof_orientation_eave_module():
    result, experiment = design_roof_eave_bearers_090(corner(False))
    assert result["bracket_count"] == 1
    assert result["root_ids_with_new_nominal_path"] == ["first"]
    assert experiment.building_id.endswith("-EXPERIMENTAL-090")


def test_missing_grounded_cross_wall_cannot_fake_cantilever():
    m = corner(True)
    m.parts = [p for p in m.parts if p.placement_id != "side-lower"]
    report, exp = design_roof_eave_bearers_090(m)
    assert report["bracket_count"] == 0
    assert report["after"]["unreached"] == report["before"]["unreached"]
    assert report["unresolved_root_designs"][0]["reason"] == "INSUFFICIENT_INTERLOCKED_WALL_ANCHORS"
    assert len(exp.parts) == len(m.parts)


def test_internal_roof_has_no_unsafe_automatic_beam():
    m = corner(True)
    m.parts += [slope("inner", 26, 8, 12, "negative")]
    result, _ = design_roof_eave_bearers_090(m)
    assert any(r["roof_id"] == "inner" for r in result["unresolved_root_designs"])


def test_catalog_geometry_no_bogus_parts_or_replacements():
    m = corner(True)
    r, exp = design_roof_eave_bearers_090(m)
    from brickhouse.bricks.catalog import standard_orthogonal_definitions
    d = standard_orthogonal_definitions()
    added = [x for x in exp.parts if x.placement_id.startswith("EXPERIMENT-090")]
    assert added and all(p.part_id in d for p in added)
    assert r["bom_additions"] and r["bom_removals"]
    assert all(b["color"] == "UNSPECIFIED_BY_BRICKMODEL" for b in r["bom_additions"])
    assert {p.placement_id for p in exp.parts if p.component == "roof"} == {"first"}


def test_translated_house_coordinates_not_guided004_special_case():
    source = corner(True)
    shifted = []
    for p in source.parts:
        shifted.append(p.model_copy(update={
            "x_studs": p.x_studs + 11,
            "y_studs": p.y_studs + 6,
        }))
    foreign = house(shifted)
    result, candidate = design_roof_eave_bearers_090(foreign)
    assert result["bracket_count"] == 1
    assert result["after"]["unreached"] == 0
    assert next(p for p in candidate.parts if p.placement_id == "EXPERIMENT-090-EAVE-first").x_studs == 27


def test_beam_replaces_colliding_wall_solids_without_stacked_bricks():
    from brickhouse.bricks.catalog import standard_orthogonal_definitions
    from brickhouse.bricks.roof_eave_bearer_builder_090 import _cells
    r, experiment = design_roof_eave_bearers_090(corner(True))
    beam = next(p for p in experiment.parts
                if p.placement_id == "EXPERIMENT-090-EAVE-first")
    d = standard_orthogonal_definitions()
    for other in experiment.parts:
        if other.placement_id == beam.placement_id or other.part_id not in d:
            continue
        if other.z_plates < beam.z_plates + 3 and (
                other.z_plates + d[other.part_id].height_plates > beam.z_plates):
            assert not (_cells(beam) & _cells(other)), other.placement_id
