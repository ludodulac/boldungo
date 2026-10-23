"""LEGO2-094: full-house structural candidate with genuine LDraw transforms.

Does not assert a physically closed truss, a watertight ridge, or rated hinges.
All additions, deletions, support graph and missing proofs are explicitly
serialized for review by GRAND-PÈRE BOLDÜNGO.
"""
from __future__ import annotations
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.triangular_frame_ridge_094 import build_094,LOCAL_PARTS
from brickhouse.bricks.geometry_adapter import CANONICAL_LDRAW_PARTS
from brickhouse.bricks.articulated_roof_093 import PARTS
from construct_guided004_hinged_roof_093 import save_ldraw,draw_views
PARTS.update(LOCAL_PARTS)


def main(source:Path,output:Path,pitch=22.):
    sha=hashlib.sha256(source.read_bytes()).hexdigest()
    original=BrickModel.model_validate_json(source.read_bytes())
    if len(original.parts)!=1936:
        raise ValueError("REQUIRES_REAL_091_1936_PART_FOUNDATION")
    experiment=build_094(original,pitch=pitch)
    if hashlib.sha256(source.read_bytes()).hexdigest()!=sha:
        raise AssertionError("HISTORIC_MODEL_MUTATED")
    foundation=experiment["foundation"]
    parts=experiment["articulated_parts"]
    r=experiment["report"]
    output.mkdir(parents=True,exist_ok=True)
    (output/"COMPOSITE-BRICKMODEL-094-ORTHOGONAL-SOURCE.json").write_text(
        foundation.model_dump_json(indent=2)+"\n",encoding="utf8")
    ldraw=save_ldraw(foundation,parts,output/"GUIDED004-ROOF-094-REAL-LEGO.ldr")
    views=draw_views(foundation,parts,output/"views")
    # Only relabel the SVG title, never draw fictitious material or shift any
    # placement: every actual 3D corner still comes from the 094 LDraw model.
    for svg in (output/"views").glob("*.svg"):
        raw=svg.read_text(encoding="utf8")
        svg.write_text(raw.replace("BOLDUNGO 093", "BOLDUNGO 094"),
                       encoding="utf8")
    if views!=7:raise AssertionError("EXPECTED_REAL_MODEL_VIEWS")
    report={**r,**ldraw,"source_091_sha256":sha,
        "full_house_LDraw_part_count":ldraw["ldraw_mapped_brick_model_part_count"]+len(parts),
        "views":views,"source_093_composite_count":2812,
        "user_physical_test_requested":False}
    if report["full_house_LDraw_part_count"]!=r["composite_total"]:
        raise AssertionError("COMPOSITE_PART_COUNT_MISMATCH")
    (output/"FRAME-094-PROOF-AND-BLOCKERS.json").write_text(
        json.dumps({"report":report,"assembly_parts":parts,"connections":experiment["links"],
                    "hinge_axes":experiment["hinge_axes"]},ensure_ascii=False,indent=2)+"\n",
        encoding="utf8")
    before=Counter()
    for pid in original.parts:
        if pid.placement_id.startswith("EXPERIMENT-091-"):
            before[CANONICAL_LDRAW_PARTS[pid.part_id].ldraw_id]+=1
    actual=Counter(p["ldraw_id"] for p in parts)
    bom={
        "not_certified":True,"new_composite_total":report["composite_total"],
        "source_093_total":2812,
        "net_delta_vs093":report["parts_delta_vs093"],
        "actual_articulated_LDraw_quantities":dict(sorted(actual.items())),
        "added_vs_093":report["part_id_additions"],
        "removed_vs_093":report["part_id_removals"],
        "colors":"UNSPECIFIED_NOT_READY_FOR_PURCHASE",
        "individual_positions_in":"FRAME-094-PROOF-AND-BLOCKERS.json",
        "source_091_original_roof_removed_only_in_composite":dict(sorted(before.items())),
    }
    (output/"BOM-094.json").write_text(json.dumps(bom,indent=2)+"\n",encoding="utf8")
    doc=[
        "# LEGO2-094 — vraie toiture à 22°, A-frames et faîtage séparé",
        "",
        "EXPERIMENTAL — NOT_CERTIFIED — AUCUNE NOTICE FINALE.",
        f"Modèle composite : {report['composite_total']} éléments (093 = 2812).",
        f"Fermes transversales TRIANGULÉES DANS LE DESSIN : {r['frame_count']}.",
        "ATTENTION : assemblages des sommets non réalisés par interfaces documentées",
        "dans le graphe. Les triangles ne sont pas certifiés fermés mécaniquement.",
        "Liaisons charnières : types complémentaires 3/2 doigts, coaxialité établie",
        "géométriquement ; maillages, rotation sous charge et tenue NOT_VERIFIED.",
        "Faîtage : deux extrémités de pans raccourcies + panne faîtière séparée",
        "et couverture horizontale ; engagement des capots et dégagement",
        "à l'insertion non établi ; ne pas forcer les panneaux.",
        "Séquence proposée : (1) murs / couronnement existant,",
        "(2) préassembler les longerons de tie beams sur zones portantes,",
        "(3) installer les montants centraux et contreventements inclinés",
        "SEULEMENT si liaisons de sommet et aux appuis sont établies,",
        "(4) assembler la panne faîtière séparément,",
        "(5) assembler les panneaux 093 avec tuiles terminales raccourcies,",
        "(6) articuler et soulever les panneaux, vérifier l'accès,",
        "(7) installer les couvre-faîtages SANS forcer les jonctions.",
        "GATES FERMÉES : insertion complète, véritables maillages des doigts",
        "de charnières, étanchéité du faîtage, efforts des fermes en flexion,",
        "efforts de poussée sur murs, N4/N5/N6.",
    ]
    (output/"SEQUENCE-094-BLOCKED.md").write_text("\n".join(doc)+"\n",encoding="utf8")
    print("LEGO2_094_MODEL_TOTAL",report["composite_total"])
    print("LEGO2_094_FRAMES",report["frame_count"])
    print("LEGO2_094_RIDGE",report["ridge_shape_solution"])
    print("LEGO2_094_HINGES",report["hinge_count"])
    print("LEGO2_094_DOCUMENTED_LOAD_RATED_PATHS",report["actual_load_rated_roof_paths"])
    print("LEGO2_094_NOT_CERTIFIED",report["N6"])
    return report


if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--pitch",type=float,default=22.)
    ap.add_argument("--truss-step",type=int,default=4)
    a=ap.parse_args()
    main(a.source,a.output,a.pitch)
