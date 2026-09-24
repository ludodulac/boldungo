import json
from pathlib import Path

import pytest
from pydantic import ValidationError

from brickhouse.vision.multiview import (
    ArchitecturalEvidenceRef,
    ArchitecturalSubassembly,
    ArchitecturalSubassemblyKind,
    AssemblyConnection,
    ConstructiveApproximation,
    RecognizableArchitecturalFragmentGate,
)

ROOT = Path(__file__).resolve().parents[1]
PIVOT = ROOT / "frontend" / "architectural-assembly-pivot-805.json"
WORLD_803 = ROOT / "frontend" / "minimal-surviving-world-803.json"
HTML_803 = ROOT / "frontend" / "minimal-surviving-world-803.html"


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def test_805_persists_human_rejection_without_rewriting_803_world_evidence():
    pivot = load(PIVOT)
    old = load(WORLD_803)
    rejection = pivot["human_rejection_803"]
    assert rejection["HUMAN_VISUAL_VALIDATION"] == "REJECTED"
    assert rejection["world_evidence_mutated"] is False
    assert HTML_803.exists()
    assert old["WORLD_EVIDENCE"]["observations"]
    assert "OBJECT_GRAPH_ALONE_INSUFFICIENT_FOR_RECOGNIZABLE_RECONSTRUCTION" in rejection["lessons"]
    assert "DISPLAY_LAYOUT_MUST_NOT_SUBSTITUTE_FOR_SPATIAL_MODEL" in rejection["lessons"]


def test_805_truth_classes_are_explicit_and_constructive_approximation_is_revisable():
    pivot = load(PIVOT)
    assert set(pivot["truth_model"]) >= {"OBSERVED_ARCHITECTURAL_EVIDENCE", "CONSTRUCTIVE_APPROXIMATION"}
    approx = ConstructiveApproximation(
        approximation_id="approx-depth",
        description="temporary depth",
        source_unknowns=["depth"],
    )
    evidence = ArchitecturalEvidenceRef(
        observation_ref="obs_p1_front_wall",
        photo_index=1,
        statement="visible wall",
    )
    assembly = ArchitecturalSubassembly(
        assembly_id="house",
        kind=ArchitecturalSubassemblyKind.HOUSE,
        observed_evidence=[evidence],
        unknown_shape_information=["depth"],
        constructive_approximations=[approx],
    )
    assert approx.truth_class == "CONSTRUCTIVE_APPROXIMATION"
    assert approx.revisable is True
    assert evidence.truth_class == "OBSERVED_ARCHITECTURAL_EVIDENCE"
    assert assembly.unknown_shape_information == ["depth"]


def test_805_approximation_cannot_masquerade_as_observation():
    with pytest.raises(ValidationError):
        ArchitecturalSubassembly(
            assembly_id="house",
            kind="HOUSE",
            observed_evidence=[ArchitecturalEvidenceRef(
                observation_ref="same-id", photo_index=1, statement="visible"
            )],
            constructive_approximations=[ConstructiveApproximation(
                approximation_id="same-id", description="invented closure", source_unknowns=["closure"]
            )],
        )


def test_805_connections_require_evidence_and_unknown_connections_stay_unknown():
    pivot = load(PIVOT)
    assert pivot["unknown_connections"]
    assert all(x["state"] == "UNKNOWN_CONNECTION" for x in pivot["unknown_connections"])
    for connection in pivot["supported_connections"]:
        parsed = AssemblyConnection(**connection)
        assert parsed.evidence_refs
    assert not any(
        x["subject_assembly_ref"] == "stair_assembly" and x["object_assembly_ref"] == "terrace_assembly"
        for x in pivot["supported_connections"]
    )


def test_805_never_promotes_display_layout_or_historical_hardcodes_to_evidence():
    pivot = load(PIVOT)
    evidence_blob = json.dumps(pivot["assemblies"] + pivot["supported_connections"])
    assert "DISPLAY_LAYOUT_ONLY" not in evidence_blob
    assert '"x": 0.08' not in evidence_blob
    assert "hardcoded" not in evidence_blob.lower()
    assert "obs_p2_stair" not in evidence_blob
    assert "obs_p2_box_volume" not in evidence_blob


def test_805_recognizable_architectural_fragment_gate_is_blocked():
    pivot = load(PIVOT)
    gate = RecognizableArchitecturalFragmentGate(
        status=pivot["gate"]["status"],
        blockers=pivot["gate"]["blockers"],
    )
    assert gate.status == "BLOCKED"
    assert pivot["gate"]["requirements"]["supported_structural_interassembly_connection"] == "MISSING"
    assert len(gate.blockers) == 3


def test_805_has_minimal_architectural_subassembly_kinds_and_preserves_unknowns():
    pivot = load(PIVOT)
    kinds = {x["kind"] for x in pivot["assemblies"]}
    assert {"HOUSE", "TERRACE", "STAIR", "ROOF"}.issubset(kinds)
    assert pivot["opening_assemblies"]["observed"]
    assert all(x["UNKNOWN_SHAPE_INFORMATION"] for x in pivot["assemblies"])
