"""Real, bounded proposal for the FIRST two-sided LEGO slope joining trial.

Machine-only evidence does not replace a physical engagement trial.
Only export BUILD instructions for a candidate that passes the known
shared-stud-alignment and opposing-slope LDraw interference screens.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

from lego_geometry_engine import LDrawLibrary

from brickhouse.bricks.roof_joint_module_087 import (
    choose_bounded_two_slope_trial_087, propose_two_slope_bridge_087,
)
from brickhouse.bricks.ridge_trial_ldraw_export_085 import _ldraw_reference


def write_mini_ridge_trial_087(output: Path, library: LDrawLibrary) -> dict:
    output.mkdir(parents=True, exist_ok=True)
    overview = choose_bounded_two_slope_trial_087(library)
    (output / "candidate-decisions.json").write_text(
        json.dumps(overview, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    recommended = overview["recommended_experiment_id"]
    if recommended is None:
        (output / "AUCUN-MONTAGE-APPROUVE.txt").write_text(
            "AUCUN CANDIDAT N'A PASSE LES CONTROLES NUMERIQUES LOCAUX.\n"
            "NE PAS commander de pieces pour ce faîtage.\n"
            "Lire candidate-decisions.json et changer de technique.\n",
            encoding="utf-8",
        )
        return overview

    row = next(x for x in overview["candidates"] if x["building_id"] == recommended)
    candidate = propose_two_slope_bridge_087(
        seam_gap_studs=row["seam_gap_studs"],
        roof_rotation=row["roof_rotation"])
    if candidate.status != "NOMINAL_TWO_SIDED_STUD_ALIGNMENT_PHYSICAL_CLUTCH_UNTESTED":
        raise AssertionError("rejected layout incorrectly promoted")
    parts = candidate.model.parts
    ldr_lines = [
        "0 BOLDUNGO LEGO2-087 3-PIECE SHARED TWO-SLOPE ROOF BRIDGE",
        "0 !NOT_CERTIFIED: NOMINAL STUD ALIGNMENT ONLY; PHYSICAL FIT NOT PROVEN",
        "0 !NOT_CERTIFIED: NO STRUCTURAL SUPPORT TO WALL OR CLUTCH TEST",
        "0 !LDraw_REFERENCE_ONLY: parts not embedded",
    ]
    for n, p in enumerate(parts, 1):
        ldr_lines.extend([
            f"0 !TRIAL_STEP {n} {p.placement_id}",
            _ldraw_reference(p, library, experimental_roof=p.roof_side is not None),
            "0 STEP",
        ])
    (output / "essai-faitage-3-pieces-NOT-CERTIFIED.ldr").write_text(
        "\n".join(ldr_lines) + "\n", encoding="utf-8")
    cap_id = "3003" if row["seam_gap_studs"] == 0 else "3002"
    guide = [
        "# BOLDÜNGO — Test manuel de jonction de DEUX versants",
        "",
        "## Seulement TROIS pièces",
        "",
        "- 2 × pente LEGO 18° 4×2, référence **30363**.",
        f"- 1 × brique LEGO {'2×2' if cap_id == '3003' else '2×3'}, référence **{cap_id}**.",
        "",
        "**ATTENTION : montage à tester à la main, ne représente PAS "
        "une toiture stable ou une notice de maison.**",
        "",
        "## Test physique ciblé",
        "",
        "1. Tenir les deux pentes 30363 côte à côte, les hauts orientés vers la jonction.",
        "2. Aligner les quatre tenons apparents : deux tenons de chaque pente, "
        "aux quatre emplacements prévus sous la brique centrale.",
        f"3. Descendre doucement la brique **{cap_id}** sur les deux paires de tenons.",
        "4. **Ne jamais forcer ni tordre** les éléments. Si la brique ne s'emboîte pas "
        "simultanément sur les deux versants, l'essai est un ÉCHEC.",
        "5. Vérifier si la brique maintient les DEUX pentes ensemble "
        "(et non une pente seulement).",
        "6. Soulever légèrement l'ensemble à la main, sans solliciter fortement "
        "le montage. Observer si le contact tient sans appui des mains. "
        "Ne jamais en déduire une tenue sous charges.",
        "7. Démonter sans forcer.",
        "",
        "## Réponse à fournir après l'essai",
        "",
        "- Emboîtement simultané des deux côtés : OUI / NON.",
        "- Effort excessif ou pièce forcée : OUI / NON.",
        "- Tenue des deux pentes à la brique centrale : OUI / NON.",
        "- Démontage sans dommage : OUI / NON.",
        "- Photo dessus et dessous de la jonction si possible.",
        "",
        "**Si l'essai échoue : rejeter la technique, ne pas lancer de nouveaux audits "
        "de maillages 075–081.**",
        "",
        "**Géométrie et rigidité de la maison de 1 890 pièces : NOT_CERTIFIED.**",
        "",
    ]
    (output / "ESSAI-3-PIECES.md").write_text(
        "\n".join(guide), encoding="utf-8")
    return overview


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ldraw-root", type=Path,
                        default=Path(os.environ["LDRAW_ROOT"])
                        if "LDRAW_ROOT" in os.environ else None)
    parser.add_argument("--output-dir", type=Path,
                        default=Path("artifacts/lego2-087/physical-mini-ridge"))
    args = parser.parse_args()
    if args.ldraw_root is None or not args.ldraw_root.is_dir():
        parser.error("Please specify a real --ldraw-root directory")
    decision = write_mini_ridge_trial_087(args.output_dir, LDrawLibrary(args.ldraw_root))
    print("LEGO2_087_CANDIDATES=", decision["candidates_tested"])
    print("LEGO2_087_RECOMMENDATION=", decision["recommendation"])
    print("LEGO2_087_RECOMMENDED_ID=", decision["recommended_experiment_id"])
    print("LEGO2_087_MECHANICAL=NOT_CERTIFIED")


if __name__ == "__main__":
    main()
