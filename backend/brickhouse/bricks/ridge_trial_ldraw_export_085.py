"""LEGO2-085: view the actual 30-piece experimental kit in LDraw-compatible 3D.

Convert the existing mission-083 BrickModel placements using the verified
BrickHouse geometry adapter, not another handwritten coordinate transform.
The 24-STEP frame is distinct from the six slope POSITION HYPOTHESES.

Requires an official/pinned LDraw library for placement definitions. The
export includes only references (e.g. 3005.dat), never the library's geometry.
Not a physics simulation, a physical mounting instruction, or a certified roof.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import json
from typing import Sequence

from lego_geometry_engine import LDrawLibrary

from .brick_model import BrickModelPart
from .geometry_adapter import (
    CANONICAL_LDRAW_PARTS,
    brick_model_part_to_instance,
)
from .ridge_technique_candidates_083 import _orthogonal_transverse_spine
from .ridge_trial_assembly_084 import review_ridge_trial_assembly_084


def _number(v: float) -> str:
    n = round(float(v), 7)
    if abs(n) < 1e-7:
        n = 0
    return str(int(n)) if n == int(n) else f"{n:.7f}".rstrip("0").rstrip(".")


def _ldraw_reference(part: BrickModelPart, library: LDrawLibrary, *,
                     experimental_roof: bool = False) -> str:
    """Return an LDraw Type-1 reference with a verified physical transform.

    Colour 16 = inherit/default. Colour 14 = visibly highlighted hypothetical
    roof position. Neither colour is a validated inventory colour.
    """
    inst = brick_model_part_to_instance(part, library)
    matrix = inst.transform.matrix
    axes = [matrix[row][col] for row in range(3) for col in range(3)]
    pos = [matrix[i][3] for i in range(3)]
    definition = CANONICAL_LDRAW_PARTS[part.part_id]
    values = [
        "1", "14" if experimental_roof else "16",
        *(_number(value) for value in pos),
        *(_number(value) for value in axes),
        f"{definition.ldraw_id}.dat",
    ]
    if len(values) != 15:
        raise AssertionError("LDraw Type 1 requires 14 tokens plus referenced DAT")
    return " ".join(values)


def write_experimental_ldr_files(output_dir: str | Path, library: LDrawLibrary) -> dict:
    """Export step-based frame and visual 30-part *hypothesis*, non-mutating."""
    model, _, frame_ids, slope_ids = _orthogonal_transverse_spine()
    original = model.model_dump_json()
    review = review_ridge_trial_assembly_084()
    if review["frame_trial_status"] != "READY_FOR_USER_FRAME_ASSEMBLY_TRIAL":
        raise ValueError("FRAME_SEQUENCE_NOT_APPROVED_FOR_PHYSICAL_EXPERIMENT")
    if review["physical_certification"] != "NOT_CERTIFIED":
        raise AssertionError("experiment cannot be treated as certified")
    step_ids = [step["placement_id"] for step in review["steps"]]
    if step_ids != frame_ids or set(step_ids) & set(slope_ids):
        raise AssertionError("frame and slope evidence sets diverged")
    parts = {part.placement_id: part for part in model.parts}
    frame_lines = [
        "0 BOLDUNGO LEGO2-085 FRAME (24 PIECES, 24 STEPS)",
        "0 !LEGO2_NOT_CERTIFIED: NOMINAL FRAME ONLY; PHYSICAL STABILITY NOT PROVEN",
        "0 !LEGO2_NOT_CERTIFIED: 6 SLOPE PIECES ARE NOT PRESENT IN THIS FILE",
        "0 !LEGO2_SOURCE: BrickModel 083 + geometry_adapter; LDraw part references only",
    ]
    for number, pid in enumerate(step_ids, 1):
        part = parts[pid]
        frame_lines.extend([
            f"0 !LEGO2_FRAME_STEP {number:02d} {pid}",
            _ldraw_reference(part, library),
            "0 STEP",
        ])
    hypothetical_lines = [
        "0 BOLDUNGO LEGO2-085 PREVIEW (30 PIECES, NOT_CERTIFIED)",
        "0 !LEGO2_NOT_CERTIFIED: THIS IS NOT A PHYSICAL CONSTRUCTION NOTICE",
        "0 !LEGO2_NOT_CERTIFIED: YELLOW SLOPE POSES = UNVERIFIED EXPERIMENTAL HYPOTHESES",
        "0 !LEGO2_SOURCE: BrickModel 083 + geometry_adapter; LDraw part references only",
        *frame_lines[4:],
        "0 !LEGO2_UNVERIFIED_ROOF_POSES_BEGIN — DO NOT FORCE THESE CONNECTIONS",
    ]
    for pid in slope_ids:
        hypothetical_lines.extend([
            f"0 !LEGO2_UNVERIFIED_30363_MATING {pid}",
            _ldraw_reference(parts[pid], library, experimental_roof=True),
            "0 STEP",
        ])
    hypothetical_lines.extend([
        "0 !LEGO2_UNVERIFIED_ROOF_POSES_END — MECHANICAL FIT NOT PROVEN",
        "0 !LEGO2_PHYSICAL_CERTIFICATION NOT_CERTIFIED",
    ])
    counts = Counter(CANONICAL_LDRAW_PARTS[p.part_id].ldraw_id
                     for p in model.parts)
    if (len(step_ids), len(slope_ids), len(model.parts)) != (24, 6, 30):
        raise AssertionError("83/84 physical kit count changed")
    if counts != {"3005": 18, "3008": 6, "30363": 6}:
        raise AssertionError("83/84 physical kit BOM changed")

    folder = Path(output_dir)
    folder.mkdir(parents=True, exist_ok=True)
    frame_file = folder / "frame-24-steps.ldr"
    preview_file = folder / "roof-30-positions-NOT-CERTIFIED.ldr"
    frame_file.write_text("\n".join(frame_lines) + "\n", encoding="utf-8")
    preview_file.write_text("\n".join(hypothetical_lines) + "\n", encoding="utf-8")
    manifest = {
        "source_building_id": model.building_id,
        "part_count": 30,
        "frame_part_count": 24,
        "unapproved_roof_part_count": 6,
        "frame_steps": step_ids,
        "roof_test_parts": slope_ids,
        "bill_of_materials": dict(sorted(counts.items())),
        "frame_file": frame_file.name,
        "preview_file": preview_file.name,
        "frame_nominal_interfaces": review["frame_nominal_joint_count"],
        "frame_assembly_screen": review["frame_trial_status"],
        "roof_attachment": review["roof_attach_status"],
        "physical_certification": "NOT_CERTIFIED",
        "note": (
            "LDraw is a visual reference model only. Yellow slopes are "
            "unvalidated positions; use only after manual no-force test. "
            "Frame itself is not structurally strength certified."
        ),
    }
    (folder / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    if model.model_dump_json() != original:
        raise AssertionError("experiment model mutated during export")
    return manifest
