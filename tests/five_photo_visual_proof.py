"""Build the five-photo visual witness without promoting LEGO conventions to Scene truth."""
from __future__ import annotations
import json
from pathlib import Path
from brickhouse.bricks.export import export_bundle_json
from brickhouse.partial_scene_pipeline import run_partial_scene_pipeline
from brickhouse.scene import ArchitecturalScene

ROOT=Path(__file__).resolve().parents[1]
SCENE=ROOT/"frontend/benchmarks/real-house-5/five-photo-scene-candidate-v0.2.json"
OUTPUT=ROOT/"frontend/sample-export.json"
MANIFEST=ROOT/"frontend/benchmarks/real-house-5/five-photo-materialization-v0.1.json"

def main():
    scene=ArchitecturalScene.model_validate_json(SCENE.read_text())
    # LEGO-only convention: the architectural Scene intentionally keeps numeric
    # roof pitch unknown. A moderate 28° is used solely to make the already-proven
    # gable topology visible in this witness.
    roof=scene.roofs[0].model_copy(update={"pitch_degrees":28.0})
    materialized=scene.model_copy(update={"roofs":[roof]})
    bundle=run_partial_scene_pipeline(materialized,front_width_studs=48,optimize_scale=False)
    OUTPUT.write_text(export_bundle_json(bundle)+"\n")
    MANIFEST.write_text(json.dumps({
        "status":"VISUAL_MATERIALIZATION_ONLY",
        "architectural_scene":str(SCENE.relative_to(ROOT)),
        "lego_conventions":{
            "roof_pitch_degrees":28.0,
            "meaning":"rendering convention only; real numeric roof pitch remains UNKNOWN",
            "scene_generated_default_geometry":"volume/platform/chimney/stair proxy coordinates exist only to produce the first visual witness and are not measurements"
        },
        "preserved_unknowns":["real roof pitch","exact stair run count","exact step count","exact deck support inventory and coordinates","real opening depths","real landing dimensions"],
    },indent=2)+"\n")
    print(f"Generated {len(bundle.brick_model.parts)} parts")
if __name__=="__main__":
    main()
