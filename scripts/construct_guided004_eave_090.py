"""LEGO2-090 full-house experimental eave bracket construction (read-only inputs)."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from brickhouse.bricks.brick_model import BrickModel
from brickhouse.bricks.roof_eave_bearer_builder_090 import design_roof_eave_bearers_090


def construct(canonical_path: Path, earlier_experiment_path: Path, output: Path):
    before = {p: hashlib.sha256(p.read_bytes()).hexdigest()
              for p in (canonical_path, earlier_experiment_path)}
    canonical = BrickModel.model_validate_json(canonical_path.read_bytes())
    previous = BrickModel.model_validate_json(earlier_experiment_path.read_bytes())
    if len(canonical.parts) != 1890 or len(previous.parts) != 1901:
        raise ValueError("INVALID_1890_CANONICAL_OR_1901_EXPERIMENT")
    if not previous.building_id.endswith("-EXPERIMENTAL-RIDGE-088"):
        raise ValueError("UNKNOWN_EXPERIMENTAL_INPUT")
    result, candidate = design_roof_eave_bearers_090(previous)
    from collections import Counter
    old_roof = Counter(p.model_dump_json() for p in previous.parts if p.component == "roof")
    new_roof = Counter(p.model_dump_json() for p in candidate.parts if p.component == "roof")
    if new_roof != old_roof:
        raise AssertionError("ROOF_POSITIONS_CHANGED")
    if any(hashlib.sha256(p.read_bytes()).hexdigest() != h for p, h in before.items()):
        raise AssertionError("SOURCE_FILE_MUTATED")
    report = {"canonical_sha256": before[canonical_path],
              "previous_sha256": before[earlier_experiment_path],
              "canonical_parts": len(canonical.parts),
              "previous_experimental_parts": len(previous.parts),
              "user_physical_test_requested": False,
              **result}
    output.mkdir(parents=True, exist_ok=True)
    (output / "GUIDED-004-EXPERIMENTAL-090-NOT-CERTIFIED.json").write_text(
        candidate.model_dump_json(indent=2) + "\n", encoding="utf-8")
    (output / "eave-assembly-090.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    doc = [
        "# BOLDÜNGO 090 — Ossature d'avant-toit expérimentale",
        "",
        "ATTENTION : NON CERTIFIÉ PHYSIQUEMENT. Pas de notice définitive ni d'achat.",
        "",
        "| Indicateur | Avant | Après |",
        "|---|---:|---:|",
        f"| Pentes nominalement reliées aux murs | {report['before']['nominal']} | {report['after']['nominal']} |",
        f"| Pentes sans chemin nominal | {report['before']['unreached']} | {report['after']['unreached']} |",
        f"| Racines non supportées | {len(report['roots_initially_missing'])} | {len(report['unresolved_root_designs'])} |",
        f"| Modules d'ancrage | 0 | {report['bracket_count']} |",
        f"| Pièces du modèle expérimental | {report['source_parts']} | {report['experimental_parts']} |",
        "",
        "## Séquence provisoire",
        "1. Monter les murs et les pièces de mur jusqu'au cours inférieur aux attaches.",
        "2. Remplacer localement les briques de couronnement sélectionnées par les nouvelles briques croisées et briques de remplissage.",
        "3. Contrôler les connexions standard tenon/anti-tenon des appuis de mur.",
        "4. Insérer les pentes depuis l'extérieur uniquement après confirmation des interfaces 30363 (non démontrée).",
        "5. Poursuivre les rangées hautes et n'insérer les faîtages que si les chemins mécaniques sont confirmés.",
        "",
        "## Réserves bloquantes",
        "- La cavité sous 30363 n'est PAS une liaison documentée par essai d'assemblage et de serrage.",
        "- L'absence de collision avec toutes les façades non orthogonales et les trajectoires d'insertion reste non prouvée.",
        "- Charge, fléchissement, rigidité, couleur des pièces et résistance globale restent non prouvés.",
        "- Toute zone intérieure qui ne dispose pas d'ancrages documentés demeure NON résolue.",
        "- Les positions des 408 pentes et le modèle 1890 restent intacts.",
        "",
        "## Nomenclature précise des modifications",
        "Voir eave-assembly-090.json (positions exactes, identifiants, quantités).",
        "Coloris = UNSPECIFIED_BY_BRICKMODEL, donc aucune liste d'achat validée.",
        "",
    ]
    (output / "PLAN-OSSATURE-090.md").write_text("\n".join(doc), encoding="utf-8")
    print("LEGO2_090_BEAMS", report["bracket_count"])
    print("LEGO2_090_ROOF_BEFORE", report["before"])
    print("LEGO2_090_ROOF_AFTER", report["after"])
    print("LEGO2_090_PARTS", report["experimental_parts"])
    print("LEGO2_090_BLOCKERS", report["unresolved_root_designs"])
    return report


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--canonical", type=Path, default=Path("artifacts/lego2-guided-004/brick-model.json"))
    ap.add_argument("--previous", type=Path, default=Path("artifacts/lego2-088-guided004-EXPERIMENTAL/GUIDED-004-EXPERIMENTAL-NOT-CERTIFIED.json"))
    ap.add_argument("--output", type=Path, default=Path("artifacts/lego2-090"))
    args = ap.parse_args()
    construct(args.canonical, args.previous, args.output)
