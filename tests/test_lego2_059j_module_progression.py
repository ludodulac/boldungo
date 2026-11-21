"""Check the 059J staged geometry on the freshly regenerated REAL export.

Passing does not certify the physical assembly or mechanical strength.
"""
import json
from pathlib import Path

import pytest

from scripts.assembly_terrace_059j import analyze

EXPORT = Path("artifacts/lego2-guided-004/brick-model.json")
PREFIX = "scene-platform:south-timber-deck-main:"


@pytest.mark.parametrize("variant,expected_module", [("B",8),("C",9)])
def test_059j_plate_joined_in_hand_then_59_original_finishes(variant,expected_module):
    model = json.loads(EXPORT.read_text(encoding="utf-8"))
    report = analyze(model, variant)
    assert report["official_parts"] == 1890
    assert report["terrace_original_scope"] == 105
    assert report["handheld_module_size"] == expected_module
    assert report["fixed_count"] == 39
    assert report["official_module_pieces"] == 7
    assert report["plate_attached_to_board1"]["status"] == "VALID"
    assert report["plate_attached_to_board1"]["stud_contacts"] == 2
    assert report["plate_receives_board2"]["status"] == "VALID"
    assert report["plate_receives_board2"]["stud_contacts"] == 1
    assert report["module_internal_valid_connected"]
    assert report["module_valid_docking_anchors"]
    assert report["rigid_module_install"]["verdict"] == "GEOMETRY_PASS"
    assert report["later_counts"] == {
        "GEOMETRY_PASS":59, "BLOCKED":0, "UNKNOWN":0, "NOT_TESTED":0
    }
    # Hidden cross-bonds must be placed before board2, not after:
    # placing board2 immediately first would obstruct 029:01.
    board2 = report["board2_step"]
    assert board2["piece"] == PREFIX + "board:00002"
    assert board2["number"] > 1
    assert board2["verdict"] == "GEOMETRY_PASS"
    assert report["staged_rectangular_geometry_demonstrated"]
    assert report["physical_buildability"] == "NOT_CERTIFIED"
