"""Rule-driven construction of an EXPERIMENTAL ridge across real GUIDED-004.

Existing source: the canonical exporter (do not reimplement it).
Never write back to the input file, the scene, main, or the canonical model.
Do NOT publish a "build-ready" notice while actual bonds remain unverified.

Usage:
  python scripts/construct_guided004_roof_088.py \
    --source artifacts/lego2-guided-004/brick-model.json \
    --output-dir artifacts/lego2-088-guided004-EXPERIMENTAL
"""
from __future__ import annotations

import argparse
import hashlib
import json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.house_roof_rule_builder_088 import (
    construct_rule_based_roof_experiment_088,
)


def construct_to_files(source: Path, output_dir: Path) -> dict:
    if not source.is_file():
        raise FileNotFoundError(
            f"Real house canonical export is missing: {source}; "
            "run the EXISTING scripts/export_guided004_lego.py first")
    original_bytes = source.read_bytes()
    original_sha = hashlib.sha256(original_bytes).hexdigest()
    original = BrickModel.model_validate_json(original_bytes)
    if len(original.parts) != 1890:
        raise ValueError(
            f"GUIDED-004 canonical expected 1890 pieces; actual={len(original.parts)}. "
            "Stop; never silently change the canonical count.")
    report, model = construct_rule_based_roof_experiment_088(original)
    if original.model_dump_json() != BrickModel.model_validate_json(original_bytes).model_dump_json():
        raise AssertionError("Original house changed in memory")
    if hashlib.sha256(source.read_bytes()).hexdigest() != original_sha:
        raise AssertionError("Canonical house file changed while constructing")
    report["source_sha256"] = original_sha
    report["canonical_piece_count_confirmed"] = 1890
    report["canonical_file_unchanged"] = True
    report["user_physical_test_required_for_this_mission"] = False
    report["approved_house_notice_emitted"] = False
    report["approved_house_parts_order_emitted"] = False
    report["house_assembly_permission"] = "DENIED_BY_FAIL_CLOSED_RULES"
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "CONSTRUCTION-DECISION-088.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8")
    if model is not None:
        (output_dir / "GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json").write_text(
            model.model_dump_json(indent=2) + "\n", encoding="utf-8")
        counter_original = Counter(p.part_id for p in original.parts)
        counter_candidate = Counter(p.part_id for p in model.parts)
        delta = {
            part: counter_candidate[part] - counter_original[part]
            for part in sorted(counter_original.keys() | counter_candidate.keys())
            if counter_candidate[part] != counter_original[part]
        }
    else:
        delta = {}
    (output_dir / "EXPERIMENTAL-BOM-DELTA.json").write_text(
        json.dumps({
            "part_count_original": 1890,
            "part_count_experiment": len(model.parts) if model is not None else None,
            "net_delta_by_canonical_part_id": delta,
            "approval": "DENIED_NOT_CERTIFIED",
            "not_a_procurement_instruction": True,
            "not_a_building_notice": True,
        }, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8")
    (output_dir / "LIRE-AVANT-CONSTRUCTION.txt").write_text(
        "BOLDUNGO LEGO2-088 - TRAVAIL D'INGENIERIE SUR GUIDED-004\n"
        "L'original de 1 890 pieces n'a pas ete modifie.\n"
        "Le fichier experimental, s'il existe, est un plan alternatif NON VALIDE.\n"
        "Aucune notice finale ne doit etre diffusee comme constructible.\n"
        "Des liaisons LEGO et une descente de charge de toiture restent non prouvees.\n"
        "Aucun test physique personnel n'est demande pour cette mission.\n"
        "Pour poursuivre: corriger les liaisons automatiquement, ou changer "
        "de technique de toiture, sans declarer la maison certifiee.\n",
        encoding="utf-8",
    )
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--source",type=Path,default=Path(
        "artifacts/lego2-guided-004/brick-model.json"))
    parser.add_argument("--output-dir",type=Path,default=Path(
        "artifacts/lego2-088-guided004-EXPERIMENTAL"))
    args=parser.parse_args()
    report=construct_to_files(args.source,args.output_dir)
    print("LEGO2_088_REAL_GUIDED004_COUNT=",report["canonical_piece_count_confirmed"])
    print("LEGO2_088_RIDGE_CANDIDATES=",report["candidate_pairs_screened"])
    print("LEGO2_088_EXPERIMENTAL_CAPS=",report["candidate_caps_proposed"])
    print("LEGO2_088_ROOF_SLOPES_NOT_CONNECTED=",report["roof_slope_parts_not_yet_joined"])
    print("LEGO2_088_DECISION=",report["decision"])
    print("LEGO2_088_CONSTRUCTION=",report["construction_status"])
    print("LEGO2_088_PHYSICAL_CERTIFICATION=",report["physical_certification"])


if __name__=="__main__":
    main()
