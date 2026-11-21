"""Mission 011: conservative actual-LDraw collision regression on 10 existing placements.

No change to the model or geometry engine. Official LDraw library required for
the exact ten-piece check; no silent substitution of bounding boxes for meshes.
A skipped test is NOT a construction certificate.
"""
from __future__ import annotations

import os
from pathlib import Path

import pytest

from lego_geometry_engine import (
    LDrawLibrary, Transform, Relation, analyze_assembly,
    assess_pair, check_collision, find_connections, instance_from_dict, instantiate,
)

REPO = Path(__file__).resolve().parents[2]
MODULE = REPO / "missions" / "VALIDATION1" / "EST-SUD-10.ldr"
FIXTURE = Path(__file__).parent / "fixtures" / "ldraw"


def _model_records():
    """Only the ten type-1 references: annotations retain original instance IDs."""
    records = []
    identifier = None
    for line in MODULE.read_text(encoding="utf-8").splitlines():
        if line.startswith("0 // "):
            tokens = line.split()
            identifier = tokens[3] if len(tokens) > 3 else None
        if not line.startswith("1 "):
            continue
        fields = line.split()
        assert len(fields) == 15, f"Malformed LDraw placement: {line}"
        assert identifier, f"Missing original identity: {line}"
        records.append({
            "instance_id": identifier,
            "part_id": fields[14],
            "color": int(fields[1]),
            "transform": [float(v) for v in fields[2:14]],
        })
        identifier = None
    return records


def test_validation1_ten_no_forbidden_material_overlap():
    root = os.environ.get("LDRAW_ROOT")
    if not root:
        pytest.skip("Official complete LDraw library absent: module NOT DEMONSTRATED")
    library = LDrawLibrary(root)  # fail explicitly if any real part geometry is missing
    raw = _model_records()
    assert len(raw) == 10
    assert len({r["instance_id"] for r in raw}) == 10
    parts = [instance_from_dict(record, library) for record in raw]
    report = analyze_assembly(parts)
    assert not report.collisions, f"Forbidden intersections: {report.collisions}"
    assert not report.indeterminate_pairs, (
        f"Unproved intersections must NOT pass: {report.indeterminate_pairs}"
    )
    # Validity of whole physical assembly is deliberately NOT asserted.


def test_injected_real_brick_solid_overlap_is_forbidden():
    library = LDrawLibrary(FIXTURE)
    brick = library.load_part("3005.dat")
    a = instantiate(brick, "brick-a")
    b = instantiate(brick, "brick-b", Transform.translation(0, -22, 0))
    assert check_collision(a, b) is Relation.COLLISION
    outcome = assess_pair(a, b)
    assert outcome.verdict == "FORBIDDEN_COLLISION", outcome


def test_real_stud_cavity_connection_passes_nominal_geometry():
    library = LDrawLibrary(FIXTURE)
    brick = library.load_part("3005.dat")
    a = instantiate(brick, "brick-a")
    b = instantiate(brick, "brick-b", Transform.translation(0, -24, 0))
    assert find_connections(a, b), "Real studs must align to real anti-studs"
    assert check_collision(a, b) is Relation.CONTACT
    outcome = assess_pair(a, b)
    assert outcome.verdict == "COMPATIBLE_MATING", outcome
    # Nominal compatibility is not physical stability or continuous insertion.
