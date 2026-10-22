"""LEGO2-092: regenerate original and prior versions, construct and export actual new house."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.roof_girder_skin_092 import design_braced_skin_092


def build(paths, dest):
    sha={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    sources=[BrickModel.model_validate_json(p.read_bytes()) for p in paths]
    assert [len(p.parts) for p in sources]==[1890,1901,1909,1936]
    old=sources[-1]
    report,variant=design_braced_skin_092(old)
    if any(hashlib.sha256(p.read_bytes()).hexdigest()!=sha[str(p)] for p in paths):
        raise AssertionError("PRIOR_VARIANTS_MUTATED")
    old_base={p.placement_id:p.model_dump_json() for p in old.parts
              if p.component in ("wall","facade_detail")}
    new_base={p.placement_id:p.model_dump_json() for p in variant.parts
              if p.component in ("wall","facade_detail")}
    if old_base!=new_base:
        raise AssertionError("ARCHITECTURAL_BASE_MUTATED")
    summary={**report, "source_count":[len(m.parts) for m in sources],
             "source_sha256":sha, "prior_architecture_preserved":True,
             "no_physical_test_requested":True}
    dest.mkdir(parents=True,exist_ok=True)
    (dest/"GUIDED-004-EXPERIMENTAL-092-NOT-CERTIFIED.json").write_text(
        variant.model_dump_json(indent=2)+"\n", encoding="utf-8")
    (dest/"CHARPENTE-TOITURE-092-EVIDENCES.json").write_text(
        json.dumps(summary,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    lines=["# BOLDÜNGO — 092 — Charpente et couverture expérimentales",
            "",
            "IMPORTANT: ce bâtiment LEGO reste NOT_CERTIFIED.",
            f"Source 091 : {len(old.parts)} pièces ; expérimental 092 : {len(variant.parts)} pièces.",
            f"Poutre BRICK_2X8 : {summary['transverse_girder_span_studs'] if 'transverse_girder_span_studs' in summary else summary['girder_span_studs']} tenons.",
            f"Plaques de peau 1-plate : {summary['skin_plate_count']}.",
            f"Modules de toiture à gradins raffinés : {summary['skin_improved_deck_bricks']}/{summary['skin_target_standard_deck_bricks']}.",
            f"Entrées bloquées par obstacles : {len(summary['skin_skipped_deck_bricks'])}.",
            f"Pente moyenne conservée : {summary['roof_mean_pitch_degrees']}° ; écart 22° : {summary['pitch_error_degrees']}°.",
            "La peau n'est PAS un zinc incliné lisse : la marche maximale locale descend de 3 à 1 plaque dans les zones acceptées.",
            "La poutre est connectée à deux ancrages via leurs tenons, mais sa capacité de flexion et la traction des racines ne sont PAS établies.",
            "Dix modules de toiture restent dépendants de cette liaison non dimensionnée.",
            "Vérification d'insertion complète, collisions avec décors non orthogonaux et N6 : REFUSÉES.",
            "", "## Ordre conditionnel"]
    lines+=["%s. %s"%(i+1,x) for i,x in enumerate(summary["assembly_sequence"])]
    (dest/"PLAN-DE-MONTAGE-092-BLOQUE.md").write_text("\n".join(lines)+"\n",encoding="utf-8")
    print("LEGO2_092_MODEL_COUNTS",summary["source_count"],"->",summary["experimental_parts"])
    for k in ["skin_improved_deck_bricks","skin_plate_count",
              "connectors_standard_type_new_interfaces","new_stud_interface_cells",
              "remaining_unproven_tension_dependent_roof_ids_count"]:
        print("LEGO2_092_"+k.upper(),summary[k])
    print("LEGO2_092_PHYSICAL_CERTIFICATION",summary["physical_certification"])
    return summary

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--canonical",type=Path,required=True)
    parser.add_argument("--v088",type=Path,required=True)
    parser.add_argument("--v090",type=Path,required=True)
    parser.add_argument("--v091",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    a=parser.parse_args()
    build([a.canonical,a.v088,a.v090,a.v091],a.output)
