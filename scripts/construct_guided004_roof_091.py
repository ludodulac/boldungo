"""LEGO2-091: reproducible whole-house replacement roof from preserved variants."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.roof_studdeck_designer_091 import design_standard_stud_roof_091


def export_091(canonical: Path, previous_088: Path, previous_090: Path, dest: Path):
    files = (canonical, previous_088, previous_090)
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    models = [BrickModel.model_validate_json(p.read_bytes()) for p in files]
    if [len(x.parts) for x in models] != [1890, 1901, 1909]:
        raise ValueError("091_REQUIRES_UNMODIFIED_1890_1901_1909_MODELS")
    if not models[2].building_id.endswith("-EXPERIMENTAL-090"):
        raise ValueError("091_REQUIRES_090_PRIOR_EXPERIMENT")
    report, trial = design_standard_stud_roof_091(models[2])
    if any(hashlib.sha256(p.read_bytes()).hexdigest() != hashes[str(p)] for p in files):
        raise AssertionError("SOURCE_MODEL_BYTES_CHANGED")
    old_nonroof = sorted(
        p.model_dump_json() for p in models[2].parts if
        p.component == "wall" or p.component == "facade_detail")
    new_nonroof = sorted(
        p.model_dump_json() for p in trial.parts if
        p.component == "wall" or p.component == "facade_detail")
    if old_nonroof != new_nonroof:
        raise AssertionError("SOURCE_ARCHITECTURE_OR_MASONRY_CHANGED")
    total = {**report, "source_hashes": hashes,
             "canonical_count": 1890, "variant088_count": 1901,
             "variant090_count": 1909, "source_nonroof_unchanged": True,
             "user_requested_physical_test": False}
    dest.mkdir(parents=True, exist_ok=True)
    (dest / "GUIDED-004-EXPERIMENTAL-STUDDED-ROOF-091-NOT-CERTIFIED.json").write_text(
        trial.model_dump_json(indent=2)+"\n", encoding="utf-8")
    (dest / "STUDDED-ROOF-091-COMPLETE-EVIDENCE.json").write_text(
        json.dumps(total, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    text = [
        "# BOLDÜNGO — 091 — Construction expérimentale de toiture à tenons",
        "",
        "**EXPERIMENTAL / NOT_CERTIFIED — aucune notice d'achat ni garantie mécanique.**",
        "L'interface 30363 est retirée du nouveau toit, faute de preuve suffisante ;",
        "toit alternatif entièrement construit en briques et plaques à tenons classiques.",
        "",
        f"- Pièces de la nouvelle variante : {len(trial.parts)}.",
        f"- Anciennes pentes 30363 remplacées : {report['replaced_slopes']}.",
        f"- Pièces de faîtage 088 retirées : {report['removed_prior_caps']}.",
        f"- Briques de toiture à tenons standard : {report['deck_bricks']}.",
        f"- Plaques de faîtage : {report['ridge_plate_count']}.",
        f"- Pentes reconstruites directement sur des interfaces de compression : {report['direct_compression_connected_roof_bricks']}.",
        f"- Pentes reconstruites reliées uniquement par tirant supérieur : {report['roof_bricks_tied_only_no_compression_certification']}.",
        f"- Briques de toiture avec chaîne dans le graphe de tenons : {report['roof_bricks_connected_in_standard_stud_graph']}.",
        f"- Briques hors de ce graphe : {len(report['roof_bricks_not_connected_to_walls'])}.",
        f"- Paires d'interfaces tenon/anti-tenon standard identifiées : {report['stud_interface_pairs_documented_type']}.",
        f"- Cellules de tenons engagées nominalement : {report['stud_interface_cells_documented_type']}.",
        f"- Pente moyenne d'escalier : {report['stepped_deck_pitch_degrees']}° ;",
        f"  référence architecturale : 22° ; écart : {report['pitch_difference_degrees']}°.",
        "",
        "## Ordre de préassemblage (conditionnel)",
        "1. Préserver la maçonnerie porteuse et les couronnements 090.",
        "2. Assembler les nouvelles briques de toiture de l'avant-toit vers le sommet.",
        "3. Préassembler les modules de tirants transversaux à deux couches",
        "   entre deux parties de toiture déjà reliées aux murs.",
        "4. Ne jamais charger ces tirants avant preuve de leur résistance en flexion.",
        "5. Fermer le sommet avec les plaques de jonction de deux versants.",
        "6. Contrôler la géométrie extérieure en escalier (pas de finition lisse).",
        "",
        "## Portes de validation fermées",
        "- Clutch local et résistance des tirants en traction/flexion : NOT_PROVEN.",
        "- Dégagement de tous les objets architecturaux non orthogonaux : NOT_VERIFIED.",
        "- Insertion des préassemblages dans la maison complète : NOT_VERIFIED.",
        "- Pente moyenne ≠ aspect lisse du toit réel ; revue de fidélité requise.",
        "- Aucun niveau N6 n'est revendiqué, aucun test physique exigé maintenant.",
        "- Le JSON joint contient chaque modification BOM, placement, connecteur",
        "  nominal et son origine.",
    ]
    (dest / "PLAN-OSSATURE-TOITURE-091.md").write_text(
        "\n".join(text)+"\n", encoding="utf-8")
    print("LEGO2_091_SOURCE_MODELS", [len(m.parts) for m in models])
    for k in ["experiment_parts", "replaced_slopes", "removed_prior_caps",
              "roof_bricks_connected_in_standard_stud_graph",
              "roof_bricks_tied_only_no_compression_certification",
              "stud_interface_pairs_documented_type", "stud_interface_cells_documented_type"]:
        print("LEGO2_091_"+k.upper(), report[k])
    print("LEGO2_091_REMAINING", report["roof_bricks_not_connected_to_walls"])
    print("LEGO2_091_GATE", report["physical_certification"])
    return total


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path, default=Path("artifacts/lego2-guided-004/brick-model.json"))
    parser.add_argument("--previous-088", type=Path, default=Path("artifacts/lego2-088-guided004-EXPERIMENTAL/GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json"))
    parser.add_argument("--previous-090", type=Path, default=Path("artifacts/lego2-090/GUIDED-004-EXPERIMENTAL-090-NOT-CERTIFIED.json"))
    parser.add_argument("--output", type=Path, default=Path("artifacts/lego2-091"))
    args = parser.parse_args()
    export_091(args.canonical, args.previous_088, args.previous_090, args.output)
