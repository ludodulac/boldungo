"""Mission 085: portable 24-step + 30-part LDraw exports, never a certificate."""
from pathlib import Path
import json

import pytest
from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.ridge_trial_ldraw_export_085 import (
    write_experimental_ldr_files,
    _ldraw_reference,
)
from brickhouse.bricks.ridge_technique_candidates_083 import _orthogonal_transverse_spine
from brickhouse.bricks.geometry_adapter import brick_model_part_to_instance


def _type1_lines(path):
    return [line for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith("1 ")]


def _parse_type1(line):
    fields = line.split()
    assert len(fields) == 15
    assert fields[0] == "1"
    return fields[1], tuple(float(x) for x in fields[2:14]), fields[14]


def test_complete_30_piece_preview_and_frame_24_steps(tmp_path, ldraw_root_085):
    library = LDrawLibrary(ldraw_root_085)
    result = write_experimental_ldr_files(tmp_path, library)
    frame = tmp_path / "frame-24-steps.ldr"
    preview = tmp_path / "roof-30-positions-NOT-CERTIFIED.ldr"
    assert frame.is_file() and preview.is_file()
    a, b = _type1_lines(frame), _type1_lines(preview)
    assert len(a) == 24 and len(b) == 30
    assert b[:24] == a
    assert len([x for x in frame.read_text().splitlines() if x == "0 STEP"]) == 24
    assert len([x for x in preview.read_text().splitlines() if x == "0 STEP"]) == 30
    assert all(_parse_type1(line)[0] == "16" for line in a)
    assert all(_parse_type1(line)[0] == "14" for line in b[24:])
    assert "NOT_CERTIFIED" in frame.read_text()
    assert "UNVERIFIED" in preview.read_text()
    assert result["physical_certification"] == "NOT_CERTIFIED"
    assert result["frame_assembly_screen"] == "READY_FOR_USER_FRAME_ASSEMBLY_TRIAL"
    assert result["roof_attachment"].startswith("REJECTED")


def test_visual_transforms_are_exactly_geometry_adapter_matrices(tmp_path, ldraw_root_085):
    library = LDrawLibrary(ldraw_root_085)
    report = write_experimental_ldr_files(tmp_path, library)
    model, _, _, _ = _orthogonal_transverse_spine()
    parts = {part.placement_id: part for part in model.parts}
    all_lines = _type1_lines(tmp_path / report["preview_file"])
    ids = report["frame_steps"] + report["roof_test_parts"]
    assert len(ids) == len(all_lines) == 30
    for pid, line in zip(ids, all_lines):
        _, vals, dat_name = _parse_type1(line)
        instance = brick_model_part_to_instance(parts[pid], library)
        matrix = instance.transform.matrix
        expected = tuple(
            [matrix[row][3] for row in range(3)] +
            [matrix[row][col] for row in range(3) for col in range(3)]
        )
        assert vals == pytest.approx(expected, abs=1e-6)
        assert dat_name.endswith(".dat")


def test_exact_bom_and_immutable_canonical_independent_export(tmp_path, ldraw_root_085):
    r = write_experimental_ldr_files(tmp_path, LDrawLibrary(ldraw_root_085))
    assert r["bill_of_materials"] == {"3005": 18, "3008": 6, "30363": 6}
    assert r["frame_part_count"] == 24
    assert r["unapproved_roof_part_count"] == 6
    assert r["part_count"] == 30
    assert sum(r["bill_of_materials"].values()) == 30
    assert json.loads((tmp_path / "manifest.json").read_text()) == r


@pytest.fixture(scope="module")
def ldraw_root_085():
    """CI downloads a 3-part dependency closure from a PINNED public mirror.

    Unit tests intentionally do not hit the network: the orchestrated CI sets
    LDRAW_TEST_ROOT_085, while local testing can supply its own official library.
    """
    import os
    location = os.environ.get("LDRAW_TEST_ROOT_085")
    if not location:
        pytest.skip("official pinned mini LDraw library not supplied")
    root = Path(location)
    if not all(any((root / folder / (p + ".dat")).is_file()
                   for folder in ("parts", "p"))
               for p in ("3005", "3008", "30363")):
        pytest.skip("required verified LDraw parts not present in external library")
    return root
