"""081: precise BFC import correction + fail-closed source face accounting."""
from pathlib import Path
import pytest
from lego_geometry_engine import LDrawLibrary

from scripts.check_ldraw_source_integrity_081 import (
    PARTS, check_two_source_parts, tally_ldraw_source,
)


def _make(tmp_path, name, src):
    p = tmp_path / "parts" / name
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(src, encoding="utf-8")
    return p


TRIANGLE = "3 16 0 0 0 2 0 0 0 2 0\n"
IDENTITY = "1 16 0 0 0 1 0 0 0 1 0 0 0 1 "
MIRROR_X = "1 16 0 0 0 -1 0 0 0 1 0 0 0 1 "


def test_certify_cw_reverses_direct_polygon_winding(tmp_path):
    _make(tmp_path, "cw.dat", "0 BFC CERTIFY CW\n" + TRIANGLE)
    mesh = LDrawLibrary(tmp_path).load_part("cw")
    assert mesh.triangles == (((0.,0.,0.), (0.,2.,0.), (2.,0.,0.)),)


def test_subpart_cw_is_local_not_inherited_from_parent(tmp_path):
    _make(tmp_path, "s/cw.dat", "0 BFC CERTIFY CW\n" + TRIANGLE)
    _make(tmp_path, "s/ccw.dat", "0 BFC CERTIFY CCW\n" + TRIANGLE)
    _make(tmp_path, "both.dat",
          "0 BFC CERTIFY CCW\n"
          + IDENTITY + "s\\cw.dat\n"
          + "1 16 10 0 0 1 0 0 0 1 0 0 0 1 s\\ccw.dat\n")
    faces = LDrawLibrary(tmp_path).load_part("both").triangles
    assert faces[0] == ((0., 0., 0.), (0., 2., 0.), (2., 0., 0.))
    assert faces[1] == ((10., 0., 0.), (12., 0., 0.), (10., 2., 0.))


def test_invertnext_flips_only_next_subfile_not_future_one(tmp_path):
    _make(tmp_path, "child.dat", "0 BFC CERTIFY CCW\n" + TRIANGLE)
    _make(tmp_path, "assembly.dat",
          "0 BFC CERTIFY CCW\n0 BFC INVERTNEXT\n"
          + IDENTITY + "child.dat\n"
          + "1 16 10 0 0 1 0 0 0 1 0 0 0 1 child.dat\n")
    faces = LDrawLibrary(tmp_path).load_part("assembly").triangles
    assert faces[0] == ((0.,0.,0.), (0.,2.,0.), (2.,0.,0.))
    assert faces[1] == ((10.,0.,0.), (12.,0.,0.), (10.,2.,0.))


def test_mirrored_reference_adjusts_outward_winding(tmp_path):
    _make(tmp_path, "child.dat", "0 BFC CERTIFY CCW\n" + TRIANGLE)
    _make(tmp_path, "mirror.dat", "0 BFC CERTIFY CCW\n" + MIRROR_X + "child.dat\n")
    faces = LDrawLibrary(tmp_path).load_part("mirror").triangles
    assert faces[0] == ((0.,0.,0.), (0.,2.,0.), (-2.,0.,0.))


def test_invertnext_and_negative_determinant_cancel(tmp_path):
    _make(tmp_path, "child.dat", "0 BFC CERTIFY CCW\n" + TRIANGLE)
    _make(tmp_path, "mirror.dat",
          "0 BFC CERTIFY CCW\n0 BFC INVERTNEXT\n" + MIRROR_X + "child.dat\n")
    faces = LDrawLibrary(tmp_path).load_part("mirror").triangles
    assert faces[0] == ((0.,0.,0.), (-2.,0.,0.), (0.,2.,0.))


def test_importer_matches_exact_number_of_raw_triangles_and_quads(tmp_path):
    _make(tmp_path, "s/sub.dat", "0 BFC CERTIFY CW\n" + TRIANGLE)
    _make(tmp_path, "main.dat", "0 BFC CERTIFY CCW\n"
          + IDENTITY + "s\\sub.dat\n"
          + "4 16 0 0 0 1 0 0 1 1 0 0 1 0\n"
          + "2 24 0 0 0 1 1 0\n")
    tally = tally_ldraw_source(LDrawLibrary(tmp_path), "main")
    assert tally["source_triangle_equivalent"] == 3
    assert tally["imported_triangle_count"] == 3
    assert tally["type3_type4_surfaces_accounted_for"] is True
    assert tally["source_counts"]["line_segments_not_surfaces"] == 1
    assert tally["source_counts"]["certify_cw_files"] == 1


def test_missing_source_does_not_silently_assume_watertight(tmp_path):
    report = check_two_source_parts(tmp_path)
    assert report["source_faces_all_accounted_for"] is False
    assert report["blockers"]
    assert report["physical_certification"] == "NOT_CERTIFIED"


def test_scope_exactly_existing_two_parts_only():
    assert PARTS == ("3005", "30363")
