"""Write reproducible human-readable build steps and machine-readable trial report.

Usage:
  python scripts/prepare_ridge_trial_084.py --output-dir artifacts/lego2-084

No canonical house mutation. No claim of physical LEGO stability.
"""
from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from brickhouse.bricks.ridge_trial_assembly_084 import review_ridge_trial_assembly_084


def render_trial_sheet(report: dict) -> str:
    parts = Counter(step["part_id"] for step in report["steps"])
    parts.update(piece["part_id"] for piece in report["roof_pieces"])
    translations = {
        "BRICK_1X1": ("3005", "Brique 1×1"),
        "BRICK_1X8": ("3008", "Brique 1×8"),
        "BRICK_SLOPED_18_4X2": ("30363", "Pente 18° 2×4"),
    }
    lines = [
        "# BOLDÜNGO — ESSAI DE FAÎTAGE LEGO (30 PIÈCES)",
        "",
        "**ATTENTION — expérience, PAS une notice de maison validée.** "
        "La stabilité, le serrage des pièces et la liaison des deux pans sont "
        "**non démontrés**. N'appliquez aucune force pour emboîter les pentes.",
        "",
        "## Inventaire du kit",
        "",
        "| Référence LEGO | Pièce | Quantité |",
        "|---|---|---:|",
    ]
    for part_id, amount in sorted(parts.items()):
        num, label = translations[part_id]
        lines.append(f"| {num} | {label} | {amount} |")
    lines.extend(["| | **TOTAL** | **30** |", "",
                  "## Comment lire les coordonnées",
                  "",
                  "X et Y = rangées de tenons, Z = hauteur en plaques "
                  "(1 brique ordinaire = 3 plaques). "
                  "Rotation 0 = longueur selon Y ; rotation 1 = longueur selon X.",
                  "",
                  "## Essai de l'ossature (24 étapes individuelles)",
                  "",
                  "Respecter l'ordre. Monter sur une surface plane, "
                  "sans colle ni effort excessif. Arrêter si une pile bascule.",
                  ""])
    for step in report["steps"]:
        p = step["position"]
        part_id = step["part_id"]
        num, label = translations[part_id]
        support = (
            "poser au niveau de base Z=0, stabilité non démontrée"
            if step["on_structural_ground_datum"] else
            "appui nominal sur " + ", ".join(
                x["from"] for x in step["documented_prior_supports"])
        )
        lines.append(
            f"{step['step']}. **{num} — {label}** "
            f"`{step['placement_id']}` : "
            f"X={p['x_studs']}, Y={p['y_studs']}, "
            f"Z={p['z_plates']}, rotation={p['rotation_quarter_turns']}. "
            f"Prévu : {support}.")
    lines.extend(["", "## Six pièces de toiture — NE PAS LES FIXER D'OFFICE",
                  "",
                  "Les positions suivantes sont **des hypothèses à comparer**, "
                  "pas une preuve d'emboîtement ni un ordre de montage autorisé.",
                  ""])
    for piece in report["roof_pieces"]:
        lines.append(
            f"- **30363**, `{piece['placement_id']}` : "
            f"X={piece['x_studs']}, Y={piece['y_studs']}, "
            f"Z={piece['z_plates']}, rotation={piece['rotation_quarter_turns']}. "
            "**Connexion inconnue : tenir séparée ; tester manuellement "
            "uniquement sans contrainte.**"
        )
    lines.extend(["", "## Observations à noter",
                  ""] + [
                      f"- [ ] {question}" for question in report["physical_observation_questions"]
                  ] + [
                      "", "Si un test échoue, arrêter, noter la pièce et "
                      "la position concernées, photographier (si possible) "
                      "sans forcer, puis transmettre le résultat.",
                      "",
                      "**Verdict informatique :** "
                      + report["frame_trial_status"],
                      "",
                      "**Faîtage complet : NON VALIDÉ — NOT_CERTIFIED.**",
                      "",
                  ])
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-dir", type=Path,
                        default=Path("artifacts/lego2-084"))
    args = parser.parse_args()
    r = review_ridge_trial_assembly_084()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    (args.output_dir / "assembly-replay.json").write_text(
        json.dumps(r, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (args.output_dir / "ESSAI-30-PIECES.md").write_text(
        render_trial_sheet(r), encoding="utf-8")
    print("LEGO2_084_STEP_COUNT=", r["step_count"])
    print("LEGO2_084_REPLAY=", r["frame_trial_status"])
    print("LEGO2_084_SLOPE_ATTACH=", r["roof_attach_status"])
    print("LEGO2_084_CERTIFICATION=", r["physical_certification"])


if __name__ == "__main__":
    main()
