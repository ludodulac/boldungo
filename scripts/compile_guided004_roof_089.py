"""Produce an actual 408-slope roof assembly DEPENDENCY plan from GUIDED-004.

Outputs are a conservative stud-geometry graph, not a mechanical build notice.
The original 1890 parts and experimental 1901 parts are read-only inputs.
No request to the user to physically assemble prototype pieces.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.roof_connectivity_compiler_089 import (
    compile_roof_connections_089,
)


def export_real_assembly_dependency_plan(
    original_path: Path, experimental_path: Path, output_dir: Path,
) -> dict:
    originals = original_path.read_bytes()
    experiments = experimental_path.read_bytes()
    source_hash = hashlib.sha256(originals).hexdigest()
    experimental_hash = hashlib.sha256(experiments).hexdigest()
    original = BrickModel.model_validate_json(originals)
    proposed = BrickModel.model_validate_json(experiments)
    if len(original.parts) != 1890:
        raise ValueError("REAL_GUIDED004_CANONICAL_PIECE_COUNT_NOT_1890")
    if proposed.building_id != original.building_id + "-EXPERIMENTAL-RIDGE-088":
        raise ValueError("UNRECOGNIZED_088_EXPERIMENTAL_SOURCE")
    if len(proposed.parts) != 1901:
        raise ValueError("EXPECTED_1901_PART_COMPLETE_RIDGE_EXPERIMENT")
    before_original, before_experiment = (
        original.model_dump_json(), proposed.model_dump_json())
    canonical = compile_roof_connections_089(original)
    experimental = compile_roof_connections_089(proposed)
    if (len(original.parts) != 1890 or len(proposed.parts) != 1901
            or original.model_dump_json() != before_original
            or proposed.model_dump_json() != before_experiment
            or hashlib.sha256(original_path.read_bytes()).hexdigest() != source_hash
            or hashlib.sha256(experimental_path.read_bytes()).hexdigest() != experimental_hash):
        raise AssertionError("SOME_CANONICAL_OR_EXPERIMENTAL_SOURCE_WAS_MUTATED")
    if canonical["roof_slope_parts"] != 408 or experimental["roof_slope_parts"] != 408:
        raise AssertionError("Original roof slopes count changed unexpectedly")
    result = {
        "scope": "REAL_1890_PIECE_HOUSE_AND_1901_PIECE_RIDGE_EXPERIMENT",
        "canonical_sha256": source_hash,
        "experimental_sha256": experimental_hash,
        "canonical_part_count": 1890,
        "experimental_part_count": 1901,
        "canonical_roof": canonical,
        "experimental_roof": experimental,
        "new_bom_parts": 0,
        "changes_to_any_source": 0,
        "full_house_certificate": "DENIED_NOT_CERTIFIED",
        "user_physical_trial_requested": False,
        "decision": (
            "DESIGN_ALTERNATIVE_FOR_UNREACHED_ROOF_COURSES"
            if experimental["roof_slope_still_without_grounded_nominal_path"]
            else "NOMINAL_PATHS_FOUND_BUT_REAL_CLUTCH_UNCERTIFIED"
        ),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "whole-house-roof-dependencies.json").write_text(
        json.dumps(result, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    summary = [
        "# BOLDÜNGO 089 — cheminements vers les murs, maison entière",
        "",
        "**Ce document n'est PAS une notice certifiée.** "
        "Les connexions étudiées sont des hypothèses de géométrie nominale.",
        "",
        "| Indicateur | Maison originale | Copie expérimentale 088 |",
        "|---|---:|---:|",
        f"| Pièces totales | {len(original.parts)} | {len(proposed.parts)} |",
        f"| Pentes 30363 | {canonical['roof_slope_parts']} | {experimental['roof_slope_parts']} |",
        f"| Pentes avec chemin nominal d'au moins deux tenons jusqu'aux murs | "
        f"{canonical['roof_slope_grounded_nominal']} | {experimental['roof_slope_grounded_nominal']} |",
        f"| Pentes sans ce chemin nominal | "
        f"{canonical['roof_slope_still_without_grounded_nominal_path']} | "
        f"{experimental['roof_slope_still_without_grounded_nominal_path']} |",
        f"| Raccords de faîtage 3002/3003 analysés | "
        f"{len(canonical['ridge_caps'])} | {len(experimental['ridge_caps'])} |",
        "",
        "## Ordonnancement structurel",
        "",
        "Le manifeste JSON contient les dépendances entre les vraies 408 pentes "
        "et une liste ordonnée uniquement des pentes ayant une voie nominale "
        "vers les murs. Il ne les déclare pas posables ni physiquement stables.",
        "",
        "## Limites non contournables",
        "",
        "- Le contrôle prouve la position nominale de tenons dans des zones "
        "géométriquement compatibles avec la cavité 30363. Il ne prouve pas "
        "l'emboîtement, sa force, le frottement, ni la stabilité de la toiture.",
        "- Pour l'extrémité interne Z=-60 de la cavité, la règle est une "
        "HYPOTHÈSE GÉOMÉTRIQUE basée sur le dessin LDraw : pas une "
        "liaison mécanique validée.",
        "- Les 362 pentes hors jonction centrale mentionnées en 088 sont "
        "principalement des rangées de toiture inférieures. Ce nombre "
        "n'implique PAS que toutes ces pentes soient sans appuis aux murs.",
        "- Il reste à concevoir et sélectionner une liaison de pente et une "
        "ossature qui satisfait les règles physiques avant toute notice finale.",
        "- Aucun test physique n'est demandé à l'utilisateur.",
        "",
        "**GUIDED-004 canonique : 1 890 pièces intactes. "
        "Statut mécanique : NOT_CERTIFIED.**",
        "",
    ]
    (output_dir / "PLAN-TOITURE-089.md").write_text(
        "\n".join(summary), encoding="utf-8",
    )
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--canonical", type=Path,
                        default=Path("artifacts/lego2-guided-004/brick-model.json"))
    parser.add_argument("--experimental", type=Path,
                        default=Path("artifacts/lego2-088-guided004-EXPERIMENTAL/GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json"))
    parser.add_argument("--output-dir", type=Path,
                        default=Path("artifacts/lego2-089"))
    args = parser.parse_args()
    r = export_real_assembly_dependency_plan(
        args.canonical, args.experimental, args.output_dir)
    print("LEGO2_089_SOURCE_PARTS=",r["canonical_part_count"])
    print("LEGO2_089_EXPERIMENTAL_PARTS=",r["experimental_part_count"])
    for kind in ("canonical_roof","experimental_roof"):
        report=r[kind]
        print(f"LEGO2_089_{kind}_GROUNDED_NOMINAL={report['roof_slope_grounded_nominal']}")
        print(f"LEGO2_089_{kind}_UNREACHED={report['roof_slope_still_without_grounded_nominal_path']}")
        print(f"LEGO2_089_{kind}_CAP_STATUS={report['ridge_cap_status_counts']}")
    print("LEGO2_089_CONSTRUCTION=",r["full_house_certificate"])


if __name__=="__main__":
    main()
