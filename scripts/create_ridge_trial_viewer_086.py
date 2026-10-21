"""Create an OFFLINE, ONE-FILE mobile 3D schematic of the 30-piece physical trial.

No external imports, network, plugins or GitHub Pages deployment required:
open `prototype-30-pieces.html` on a phone or computer. This is a simplified
shape viewer, NOT an LDraw solid mesh or mechanical certification.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.catalog import standard_orthogonal_definitions
from brickhouse.bricks.roof import create_m0_roof_catalog
from brickhouse.bricks.ridge_technique_candidates_083 import (
    LDRAW_IDENTITIES, _orthogonal_transverse_spine,
)
from brickhouse.bricks.ridge_trial_assembly_084 import review_ridge_trial_assembly_084

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = REPO_ROOT / "frontend/experiments/ridge-trial-086.template.html"
LABELS = {
    "BRICK_1X1": "Brique 1×1",
    "BRICK_1X8": "Brique 1×8",
    "BRICK_SLOPED_18_4X2": "Pente LEGO 18° (2×4)",
}


def build_viewer_payload() -> dict:
    model, required, frame_ids, roof_ids = _orthogonal_transverse_spine()
    before = model.model_dump_json()
    replay = review_ridge_trial_assembly_084()
    standard = standard_orthogonal_definitions()
    roof = create_m0_roof_catalog()
    if (replay["frame_trial_status"] != "READY_FOR_USER_FRAME_ASSEMBLY_TRIAL"
            or replay["physical_certification"] != "NOT_CERTIFIED"):
        raise AssertionError("Frame nominal review does not authorize even an experiment")
    if [step["placement_id"] for step in replay["steps"]] != frame_ids:
        raise AssertionError("084 sequence disagrees with 083 experimental frame")
    by_id = {p.placement_id: p for p in model.parts}
    if len(by_id) != 30 or len(frame_ids) != 24 or len(roof_ids) != 6:
        raise AssertionError("Experimental 30-piece kit changed unexpectedly")
    pieces = []
    for part in model.parts:
        definition = standard.get(part.part_id)
        if definition is None:
            definition = roof.get(part.part_id)
            w, d = definition.width_studs, definition.length_studs
            if part.rotation_quarter_turns % 2:
                w, d = d, w
        else:
            w, d = definition.footprint(part.rotation_quarter_turns)
        pieces.append({
            "id": part.placement_id,
            "part_id": part.part_id,
            "type": "roof" if part.roof_side else "frame",
            "side": part.roof_side,
            "x": part.x_studs,
            "y": part.y_studs,
            "z_plates": part.z_plates,
            "w": w, "d": d, "h": definition.height_plates * .4,
            "rotation": part.rotation_quarter_turns,
            "connector_status": ("REJECTED_UNDOCUMENTED_ROOF_ATTACHMENT"
                                 if part.placement_id in roof_ids
                                 else "DOCUMENTED_NOMINAL_ONLY"),
        })
    # Frame steps encode the exact already verified nominal order.
    steps = []
    for item in replay["steps"]:
        steps.append({
            "id": item["placement_id"],
            "on_ground": item["on_structural_ground_datum"],
            "supports": [s["from"] for s in item["documented_prior_supports"]],
            "insertion_screen": item["insertion_screen"],
        })
    quantities = Counter(part.part_id for part in model.parts)
    bom = [
        {"engine_id": pid, "ldraw_id": LDRAW_IDENTITIES[pid],
         "label": LABELS[pid], "quantity": quantities[pid]}
        for pid in sorted(quantities)
    ]
    if {p["ldraw_id"]: p["quantity"] for p in bom} != {
        "3005": 18, "3008": 6, "30363": 6,
    }:
        raise AssertionError("The known physical test kit's BOM changed")
    if sum(row["quantity"] for row in bom) != 30:
        raise AssertionError("Physical BOM count mismatch")
    if before != model.model_dump_json():
        raise AssertionError("Canonical or experimental model mutated")
    return {
        "experiment": "LEGO2-086-mobile-offline",
        "origin": "LEGO2-083-and-084-only",
        "physical_certification": "NOT_CERTIFIED",
        "view_geometry": "SIMPLIFIED_VISUAL_ENVELOPES_NOT_LDRAW_MESHES",
        "frame_connectors": "NOMINAL_ONLY_26_EDGES",
        "roof_attach": "REJECTED_UNDOCUMENTED",
        "parts": pieces,
        "steps": steps,
        "roof_parts": roof_ids,
        "bom": bom,
        "guided004_modified": False,
    }


def render_offline_viewer(template: str, data: dict) -> str:
    sentinel = "__TRIAL_DATA_JSON__"
    if template.count(sentinel) != 1:
        raise ValueError("Missing or duplicate viewer data insertion point")
    safe = json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":")).replace("</", "<\\/")
    output = template.replace(sentinel, safe)
    if sentinel in output:
        raise AssertionError("Viewer template not fully rendered")
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path(
        "artifacts/lego2-086/prototype-30-pieces.html"))
    args = parser.parse_args()
    payload = build_viewer_payload()
    html = render_offline_viewer(TEMPLATE.read_text(encoding="utf-8"), payload)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(html, encoding="utf-8")
    (args.output.parent / "prototype-data.json").write_text(
        json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print("LEGO2_086_OFFLINE_HTML=" + str(args.output))
    print("LEGO2_086_PARTS=" + str(len(payload["parts"])))
    print("LEGO2_086_FRAME_STEPS=" + str(len(payload["steps"])))
    print("LEGO2_086_ROOF_HYPOTHESES=" + str(len(payload["roof_parts"])))
    print("LEGO2_086_PHYSICAL_CERTIFICATION=NOT_CERTIFIED")


if __name__ == "__main__":
    main()
